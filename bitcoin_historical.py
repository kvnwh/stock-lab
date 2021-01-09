from robinhood_api import robinhoodapi
import decimal
import dateutil.parser

class PricePoint():
  pass

rh = robinhoodapi.RobinhoodApi()

history = rh.get_bit_coin_history()
points = history['data_points']
first = True
prevHigh = float('inf')
prevClose = float('inf')
prevOpen = float('inf')
for point in points:
  p = PricePoint()
  p.open = decimal.Decimal(point['open_price'])
  p.close = decimal.Decimal(point['close_price'])
  p.high = decimal.Decimal(point['high_price'])
  p.low = decimal.Decimal(point['low_price'])
  p.time = dateutil.parser.parse(point['begins_at'])
  if (prevOpen < prevClose): # prev was green
    if (p.open < p.close and p.open > prevOpen and p.close > prevClose): # green going up
      print(f'continue up time: {p.time.astimezone().strftime("%y-%m-%d %H:%M:%S")} open:{p.open} close:{p.close} high:{p.high} low:{p.low} prevClose:{prevClose}')
  elif (prevOpen > prevClose): # prev was red
    if (p.open < p.close and p.open <= prevClose and p.close >= (prevOpen + prevClose)/2):
      print(f'turning up time: {p.time.astimezone().strftime("%y-%m-%d %H:%M:%S")} open:{p.open} close:{p.close} high:{p.high} low:{p.low} prevClose:{prevClose}')
  # prevHigh = p.high
  prevClose = p.close
  prevOpen = p.open