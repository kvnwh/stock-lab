from robinhood_api import robinhoodapi
import json
import urllib.parse
import decimal
import matplotlib.pyplot as plotter

class Holding():
  pass

class RhProcess:
  h = None
  def __init__(self):
    self.h = robinhoodapi.RobinhoodApi()

  def run(self):
    rh = self.h
    portfolio = rh.portfolios()
    currentStockTotalValue = portfolio['market_value']
    positions = rh.positions()['results']
    instruments = []
    holdings = []
    for position in positions:
      holding = Holding()
      holding.instrument = position['instrument']
      holding.quantity = position['quantity']
      holding.average_price = position['average_buy_price']
      instruments.append(holding.instrument)
      holdings.append(holding)

    separator = ','
    stocks = rh.portfolio_pie(urllib.parse.quote(separator.join(instruments)))['results']
    for stock in stocks:
      found = next((h for h in holdings if h.instrument == stock['instrument']), None)
      if found is not None:
        found.last_trade_price = stock['last_trade_price']
        found.symbol = stock['symbol']
        found.value = decimal.Decimal(found.quantity) * decimal.Decimal(found.last_trade_price)
        found.percentage = round(found.value/decimal.Decimal(currentStockTotalValue) * 100, 2)
        print(f'{found.symbol}: {found.last_trade_price} x {found.quantity} = {round(found.value, 2)} ({found.percentage}%)' )

    
    labels = []
    shares = []
    explodes = []
    for holding in holdings:
      labels.append(f'{holding.symbol} - {holding.percentage}%')
      shares.append(holding.value)
      # if (holding.percentage < 5):
      #   explodes.append(0.8)
      # else:
      #   explodes.append(0.0)

    # figureObject, axesObject = plotter.subplots()
    # patches, texts = plt.pie(y, colors=colors, startangle=90, radius=1.2)

    # plotter.ion()
    patches, texts = plotter.pie(shares,
      # labels=labels,
      # explode=explodes,
      startangle=90,
      radius=1.2)

    patches, labels, dummy =  zip(*sorted(zip(patches, labels, shares),
                                              key=lambda x: x[2],
                                              reverse=True))

    plotter.legend(patches, labels, loc='best', bbox_to_anchor=(-0.1, 1.), fontsize=7)
    # axesObject.axis('equal')
    plotter.show()

process = RhProcess()
process.run()