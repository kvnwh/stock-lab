from robinhood_api import robinhoodapi
import json
import urllib.parse
import decimal

class Bitcoin():
    def __init__(self, **kwargs):
        self.__dict__ = kwargs
   

class BitcoinTracker:
    rh = None
    def __init__(self):
        self.rh = robinhoodapi.RobinhoodApi()

    def get_price(self):
        h = self.rh
        bitcoin = h.get_bit_coin()
        return decimal.Decimal(bitcoin['mark_price'])
