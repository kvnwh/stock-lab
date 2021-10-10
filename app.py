from flask import Flask, json
from flask.wrappers import Response
import yfinance as yf

from stock_value_evaluator.evaluate import evaluate

app = Flask(__name__)


@app.route("/info/<ticker>")
def get_company_info(ticker):
    company = yf.Ticker(ticker)
    return Response(json.dumps(company.info), mimetype="application/json")


@app.route("/value/<ticker>")
def get_stock_value(ticker):
    value = evaluate(ticker, show_plot=False)
    return Response(json.dumps(value), mimetype="application/json")
