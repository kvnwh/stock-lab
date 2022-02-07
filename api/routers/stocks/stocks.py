import datetime
from typing import List
import numpy as np
import pandas as pd
import dateutil
import pytz

import yfinance as yf
from yfinance import ticker
from common.db import get_session
from common.logging import logger
from flask import Blueprint, jsonify, request, render_template
from models.sell_option import SellOption
from models.tracking import Tracking
from robinhood_api.robinhoodapi import RobinhoodApi
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