import sys
import time
from bitcoin import BitcoinTracker
from datetime import datetime
from bitcoin import Bitcoin
import pandas as pd
from pathlib import Path

coins = []
coinsInMin = []
def main_loop():
    btcTracker = BitcoinTracker()
    prevPrice = btcTracker.get_price()
    count = 1
    interval = 15
    currentTime = 0
    coinsInMin.append(Bitcoin(price=round(prevPrice, 3), time = datetime.now(), change = 0.))
    while 1:
        # do your stuff...
        price = btcTracker.get_price()
        change = (price - prevPrice)/prevPrice
        prevPrice = price
        now = datetime.now()
        coin = Bitcoin(price=round(price, 3), time = now, change = round(change * 100, 3))
        print(f'{coin.time.strftime("%H:%M:%S")}: {coin.price} change: {coin.change}%')
        coins.append(coin)
        # print(f'slepp...{count}')
        # count += 1
        currentTime += interval
        if (currentTime >= 60):
            lastMinPrice = coinsInMin[-1].price
            minChange = (price - lastMinPrice)/lastMinPrice
            coinsInMin.append(Bitcoin(price=round(price, 3), time = now, change = round(minChange * 100, 3)))
            print(f'MIN change!!! {coinsInMin[-1].time.strftime("%H:%M:%S")}: {coinsInMin[-1].price} change: {coinsInMin[-1].change}%')
            currentTime = 0
        time.sleep(interval)

if __name__ == '__main__':
    try:
        main_loop()
    except (KeyboardInterrupt, ConnectionResetError):
        ticks = []
        prices = []
        changes = []
        ticksM = []
        pricesM = []
        changesM = []
        for coin in coins:
            ticks.append(coin.time.strftime("%H:%M:%S"))
            prices.append(coin.price)
            changes.append(coin.change)
        for coin in coinsInMin:
            ticksM.append(coin.time.strftime("%H:%M:%S"))
            pricesM.append(coin.price)
            changesM.append(coin.change)
        
        data = {
            'time': ticks,
            'price': prices,
            'change': changes
        }
        csvFile = pd.DataFrame(data, columns= ['time', 'price', 'change'])
        csvFile.to_csv(f'./data/bitcoin_{datetime.now().strftime("%y_%m_%d_%H_%M_%S")}.csv', index=False)
        data = {
            'time': ticksM,
            'price': pricesM,
            'change': changesM
        }
        csvFile2 = pd.DataFrame(data, columns= ['time', 'price', 'change'])
        csvFile2.to_csv(f'./data/bitcoin_{datetime.now().strftime("%y_%m_%d_%H_%M_%S")}_M.csv', index=False)
        
        # lvl = json.dumps(coins)
        # print (f'length: {len(coins)}')
        # print(lvl)
        print ('Exiting by user request.')
        sys.exit(0)