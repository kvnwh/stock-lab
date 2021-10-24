from datetime import datetime

import yfinance as yf
from common.db import get_session
from common.logging import logger
from flask import Blueprint, jsonify, request
from models.tracking import Tracking
from stock_value_evaluator.evaluate import evaluate

stocks = Blueprint("stocks", __name__)


@stocks.route("/stocks/<ticker>/info")
def get_company_info(ticker):
    company = yf.Ticker(ticker)
    return jsonify(company.info), 200


@stocks.route("/stocks/<ticker>/evaluation")
def get_stock_value(ticker):
    value = evaluate(ticker, show_plot=False)
    return jsonify(value), 200


@stocks.route("/stocks/tracking", methods=["POST"])
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
