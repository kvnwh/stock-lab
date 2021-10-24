import os
from common.db import db, postgres_url
from flask import Flask

from .routers.stocks.stocks import stocks


def make_app():
    app = Flask(__name__)
    app.debug = True
    app.config["SQLALCHEMY_DATABASE_URI"] = postgres_url
    db.init_app(app)
    return app


app = make_app()

app.register_blueprint(stocks)
