import json
from sqlalchemy import Column, Integer, String, Index, inspect
from sqlalchemy.sql.sqltypes import Boolean, DateTime, Float
from common.db import Base


class SellOption(Base):
    __tablename__ = "sell_option"
    id = Column("id", Integer, primary_key=True)
    ticker = Column(String(10))
    expired_date = Column(DateTime(timezone=True))
    credit = Column(Float)
    sold_date = Column(DateTime(timezone=True))
    gain = Column(Float)
    strike = Column(Float)
    price = Column(Float)

    def _asdict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}
