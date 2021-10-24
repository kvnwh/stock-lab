from flask_sqlalchemy import SQLAlchemy

postgres_url = "postgresql://stock:aSecret@localhost:50052/stock"

db = SQLAlchemy()


class Base(db.Model):
    __abstract__ = True


def get_session():
    return db.session
