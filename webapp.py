import waitress
import os

from stock_value_evaluator.api.app import app
from common.db import db


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    waitress.serve(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "3000")),
        expose_tracebacks=True,
        connection_limit=os.getenv("CONNECTION_LIMIT", "100"),
        threads=os.getenv("THREADS", "4"),
    )

# run waitress-serve --port=8111 webapp:app
