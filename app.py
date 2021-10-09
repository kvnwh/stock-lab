from flask import Flask, json, jsonify
from flask.wrappers import Response
import yfinance as yf

app = Flask(__name__)


@app.route("/<ticker>")
def hello_world(ticker):
    goog = yf.Ticker(ticker)
    return Response(json.dumps(goog.info), mimetype="application/json")
