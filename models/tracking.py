from sqlalchemy import Column, Integer, String, Index
from sqlalchemy.sql.sqltypes import Boolean, DateTime, Float
from common.db import Base


class Tracking(Base):
    __tablename__ = "tracking"
    id = Column("id", Integer, primary_key=True)
    ticker = Column(String(10))
    date = Column(DateTime(timezone=True))
    stop_loss = Column(Float)
    buy_lower_bound = Column(Float)
    buy_higher_bound = Column(Float)
    should_long = Column(Boolean)
