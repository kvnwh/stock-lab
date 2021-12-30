from datetime import datetime
from typing import List

import yfinance as yf
from yfinance import ticker
from common.db import get_session
from common.logging import logger
from flask import Blueprint, jsonify, request, render_template
from models.sell_option import SellOption
from models.tracking import Tracking
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
        date=datetime.strptime(payload["date"], "%Y-%m-%d"),
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
        expired_date=datetime.strptime(payload["expired_date"], "%Y-%m-%d"),
        sold_date=datetime.strptime(payload["sold_date"], "%Y-%m-%d"),
        credit=payload.get("credit"),
    )
    if payload.get("gain") is None:
        option.gain = option.credit

    session = get_session()
    session.add(option)
    session.commit()

    return jsonify(option._asdict()), 200


@stocks.route("/options_gain", methods=["GET"])
def get_sold_options():
    args = dict(request.args)
    logger.info(args)
    filter = {}
    query = SellOption.query
    if args.get("ticker") is not None:
        query = query.filter(SellOption.ticker == args.get("ticker"))
    arr: List[SellOption] = query.all()
    res = []
    credit = 0
    for r in arr:
        credit += r.credit
        res.append(r._asdict())
    res.sort(key=lambda r: r.get("sold_date"))
    return jsonify({"credit": credit, "options": res}), 200
