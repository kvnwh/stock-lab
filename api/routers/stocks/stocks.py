import datetime
from typing import List
import numpy as np
import pandas as pd
import dateutil
import pytz
import time

import yfinance as yf
from yfinance import ticker
from common.db import get_session
from common.logging import logger
from flask import Blueprint, jsonify, request, render_template
from models.sell_option import SellOption
from models.tracking import Tracking
from robinhood_api.robinhoodapi import RobinhoodApi
from robinhood_api import endpoints
from stock_value_evaluator.evaluate import evaluate

stocks = Blueprint(
    "stocks",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/stocks",
)


@stocks.route("/")
def default_page():
    return render_template("index.html")

_OPP_CACHE = {"ts": 0.0, "watchlists": None}


def _float(x):
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _days_between(a, b):
    return max(0, (b.date() - a.date()).days)


def _pick_expirations(expiration_dates, target_dtes):
    """Pick expirations closest to each target DTE from an iterable of YYYY-MM-DD."""
    now = datetime.datetime.now(datetime.timezone.utc)
    parsed = []
    for d in expiration_dates or []:
        try:
            dt = datetime.datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
        except Exception:
            continue
        parsed.append((d, _days_between(now, dt), dt))

    if not parsed:
        return []

    out = []
    used = set()
    for target in target_dtes:
        best = None
        for d, dte, dt in parsed:
            if d in used:
                continue
            if best is None or abs(dte - target) < abs(best[1] - target):
                best = (d, dte, dt)
        if best:
            used.add(best[0])
            out.append(best)
    return out


def _annualized_put_yield(premium, strike, dte_days):
    if premium is None or strike is None or dte_days <= 0:
        return None
    if strike <= 0:
        return None
    return (premium / strike) * (365.0 / dte_days)


def _distance_to_strike_pct(underlying, strike):
    if underlying is None or strike is None or underlying <= 0:
        return None
    return (underlying - strike) / underlying


def _spread_pct(bid, ask):
    if bid is None or ask is None:
        return None
    mid = (bid + ask) / 2.0
    if mid <= 0:
        return None
    return (ask - bid) / mid


def _score_csp(ann_yield, dist_pct, spread_pct):
    """
    Higher is better. Penalize wide spreads and strikes too close to spot.
    This is intentionally simple and interpretable.
    """
    if ann_yield is None or dist_pct is None:
        return None
    sp_penalty = 0.0 if spread_pct is None else min(1.5, spread_pct * 2.0)
    # Prefer a bit of cushion; 5% cushion is a decent default.
    cushion_bonus = min(0.08, max(0.0, dist_pct - 0.03))
    return (ann_yield * 100.0) + (cushion_bonus * 100.0) - (sp_penalty * 10.0)


def _get_watchlists_cached(api: RobinhoodApi, ttl_s=60.0):
    now = time.time()
    if _OPP_CACHE["watchlists"] is not None and (now - _OPP_CACHE["ts"]) < ttl_s:
        return _OPP_CACHE["watchlists"]
    wls = api.get_watchlists()
    _OPP_CACHE["watchlists"] = wls
    _OPP_CACHE["ts"] = now
    return wls


@stocks.route("/opportunities/watchlists")
def opportunities_watchlists():
    api = RobinhoodApi()
    try:
        logger.info("opportunities_watchlists: fetching watchlists from Robinhood")
        wls = _get_watchlists_cached(api)
        logger.info(f"opportunities_watchlists: ok count={len(wls)}")
    except Exception as e:
        # Surface the failure to the UI; common causes are expired tokens or blocked network/DNS.
        logger.exception("opportunities_watchlists: failed")
        return jsonify({"error": str(e), "hint": "Check network/DNS and env.config auth/refresh tokens."}), 502
    return jsonify([{"name": w.get("name"), "url": w.get("url")} for w in wls]), 200


@stocks.route("/opportunities")
def opportunities_page():
    return render_template("opportunities.html")


@stocks.route("/opportunities.json")
def opportunities_json():
    strategy = (request.args.get("strategy") or "csp").lower()
    watchlist = request.args.get("watchlist")
    max_tickers = int(request.args.get("max_tickers") or "40")
    target_dte = int(request.args.get("target_dte") or "30")

    if strategy not in {"csp"}:
        return jsonify({"error": "unsupported strategy"}), 400

    api = RobinhoodApi()
    symbols = api.get_watchlist_symbols(watchlist)
    symbols = symbols[:max_tickers]

    rows = []
    now = datetime.datetime.now(datetime.timezone.utc)
    for sym in symbols:
        try:
            q = api.quote_data(sym)
            underlying = _float(q.get("last_trade_price") or q.get("last_extended_hours_trade_price") or q.get("previous_close"))
        except Exception:
            continue
        if underlying is None:
            continue

        # Fetch chain to get expirations.
        try:
            instrument_id = api.get_url(q["instrument"])["id"]
            chains = api.get_url(endpoints.chain(instrument_id))
            chain = (chains.get("results") or [None])[0] or {}
            expiration_dates = chain.get("expiration_dates") or []
        except Exception:
            expiration_dates = []

        picks = _pick_expirations(expiration_dates, [target_dte, max(7, target_dte - 14)])
        for exp_str, dte, exp_dt in picks:
            if dte <= 0:
                continue

            try:
                puts = api.get_options(sym, exp_str, "put")
            except Exception:
                continue

            # Strike targeting: start around 90% spot, sample a few around it.
            target_strike = underlying * 0.90
            candidates = []
            for c in puts:
                strike = _float(c.get("strike_price"))
                if strike is None:
                    continue
                if strike > underlying * 0.985:
                    continue
                if strike < underlying * 0.70:
                    continue
                candidates.append((abs(strike - target_strike), c))
            candidates.sort(key=lambda t: t[0])
            candidates = [c for _, c in candidates[:8]]

            md_map = {}
            try:
                md_map = api.get_option_marketdata_map([c.get("url") for c in candidates if c.get("url")])
            except Exception:
                md_map = {}

            for c in candidates:
                md = md_map.get(c.get("url")) or {}
                mark = _float(md.get("adjusted_mark_price") or md.get("mark_price"))
                bid = _float(md.get("bid_price"))
                ask = _float(md.get("ask_price"))
                strike = _float(c.get("strike_price"))
                if mark is None or strike is None:
                    continue

                ann = _annualized_put_yield(mark, strike, dte)
                dist = _distance_to_strike_pct(underlying, strike)
                spr = _spread_pct(bid, ask)
                score = _score_csp(ann, dist, spr)
                if score is None:
                    continue

                rows.append(
                    {
                        "ticker": sym,
                        "underlying": underlying,
                        "expiry": exp_str,
                        "dte": dte,
                        "strike": strike,
                        "premium": mark,
                        "bid": bid,
                        "ask": ask,
                        "spreadPct": spr,
                        "distToStrikePct": dist,
                        "annYield": ann,
                        "score": score,
                        "url": c.get("url"),
                    }
                )

    rows.sort(key=lambda r: r["score"], reverse=True)
    return jsonify({"strategy": strategy, "watchlist": watchlist, "candidates": rows[:200]}), 200


@stocks.route("/<ticker>/info")
def get_company_info(ticker):
    company = yf.Ticker(ticker)
    return jsonify(company.info), 200


@stocks.route("/<ticker>/evaluation")
def get_stock_value(ticker):
    value = evaluate(ticker, show_plot=False)
    return jsonify(value), 200


@stocks.route("/tracking", methods=["POST"])
def add_tracking():
    payload = dict(request.json)
    logger.info(payload)
    tracking = Tracking(
        ticker=payload.get("ticker"),
        date=datetime.datetime.strptime(payload["date"], "%Y-%m-%d"),
        stop_loss=payload.get("stop_loss"),
        buy_lower_bound=payload.get("buy_lower_bound"),
        buy_higher_bound=payload.get("buy_higher_bound"),
        should_long=payload.get("should_long"),
    )
    session = get_session()
    session.add(tracking)
    session.commit()

    return jsonify(payload), 200


@stocks.route("/trackings", methods=["GET"])
def get_trackings():
    trackings = Tracking.query.all()
    res = []
    for t in trackings:
        res.append(t._asdict())
    return jsonify(res), 200


@stocks.route("/options_gain", methods=["POST"])
def add_sold_options():
    payload = dict(request.json)
    logger.info(payload)
    option = SellOption(
        ticker=payload.get("ticker"),
        expired_date=datetime.datetime.strptime(payload["expired_date"], "%Y-%m-%d"),
        sold_date=datetime.datetime.strptime(payload["sold_date"], "%Y-%m-%d"),
        credit=payload.get("credit"),
        strike=payload.get("strike"),
        price=payload.get("price"),
    )
    if payload.get("gain") is None:
        option.gain = option.credit

    session = get_session()
    session.add(option)
    session.commit()

    return jsonify(option._asdict()), 200


@stocks.route("/options_gain", methods=["GET"])
def get_sold_options():
    res = _get_options(dict(request.args))
    return jsonify(res), 200

@stocks.route("/options_gain/view")
def get_oo():
    res = _get_options()
    return render_template("options.html", total=res["credit"], options=res["options"])


def _get_options(args = {}):
    query = SellOption.query
    if args.get("ticker") is not None:
        query = query.filter(SellOption.ticker == args.get("ticker"))
    if args.get("from_date") is not None:
        query = query.filter(SellOption.sold_date >= args.get("from_date"))
    if args.get("direction") is not None:
        condition = (
            SellOption.strike < SellOption.price
            if args.get("direction") == "PUT"
            else SellOption.strike > SellOption.price
        )
        query = query.filter(condition)
    arr: List[SellOption] = query.all()
    res = []
    credit = 0
    for r in arr:
        credit += r.credit
        margin = abs(r.strike - r.price) / r.price
        # include enddate => +1
        day_range = abs(np.busday_count(r.expired_date.date(), r.sold_date.date())) + 1 
        # print(f'{r.sold_date.date()} - {r.expired_date.date()}: {day_range}')
        res.append(
            {
                **r._asdict(),
                "direction": "PUT" if r.strike < r.price else "CALL",
                "margin": "{:.2%}".format(margin),
                "credit_per_percentage_point_per_day": r.credit / (margin * 100) / day_range ,
                # "day_range": day_range,
            }
        )
    res.sort(key=lambda r: r.get("sold_date"))
    return {"credit": credit, "options": res}

@stocks.route("/options")
def get_options():
    args = dict(request.args)
    start_date = args.get("start_date")
    ticker = args.get("ticker")
    api = RobinhoodApi()
    # owned = api.options_owned()
    orders = api.get_option_orders()
    res = []
    amount = 0
    map = {}
    for o in orders:
        if start_date:
            date = pytz.UTC.localize(datetime.datetime.strptime(start_date,"%Y-%m-%d"))

            option_opened_date = dateutil.parser.parse(o["updated_at"])
            if option_opened_date < date:
                continue
        
        if ticker:
            if ticker.lower() !=  o["chain_symbol"].lower():
                continue
        
        # next_day = dateutil.parser.parse(o["updated_at"]) + datetime.timedelta(days=1)
        # date_portion = o["updated_at"].split("T")[0]
        # history = yf.Ticker(o["chain_symbol"]).history(start=date_portion, end=next_day.date().strftime('%Y-%m-%d'), interval="1m")
        order = {
            "ticker": o["chain_symbol"],
            "strike": o["legs"][0]["strike_price"],
            "premium": o["processed_premium"],
            "direction": o["direction"],
            "quantity": o["processed_quantity"],
            "expiration_date": o["legs"][0]["expiration_date"],
            "sold_date": o["updated_at"],
            "opening_strategy": o["opening_strategy"],
            "closing_strategy": o["closing_strategy"],
        }
        
        money_flow = float(order["premium"]) if order["direction"] == "credit" else (-1 * float(order["premium"]))
        amount = amount + money_flow

        if (o["chain_symbol"] not in map):
            map[o["chain_symbol"]] = 0
        map[o["chain_symbol"]] = map[o["chain_symbol"]] + money_flow
        res.append(order)
    # return jsonify({
    #     "earnings": amount,
    #     "data": res
    # }), 200
    return render_template("robinhood_options.html", total=amount, options=res, earnings=map)
