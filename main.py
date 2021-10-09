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
    interval = 15
    span = 60
    maxSize = 60
    currentTime = 0
    coinsInMin.append(
        Bitcoin(price=round(prevPrice, 3), time=datetime.now(), change=0.0)
    )
    while 1:
        price = btcTracker.get_price()
        change = (price - prevPrice) / prevPrice
        prevPrice = price
        now = datetime.now()
        coin = Bitcoin(price=round(price, 3), time=now, change=round(change * 100, 3))
        print(f'{coin.time.strftime("%H:%M:%S")}: {coin.price} change: {coin.change}%')
        coins.append(coin)
        currentTime += interval
        if currentTime >= span:
            lastMinPrice = coinsInMin[-1].price
            minChange = (price - lastMinPrice) / lastMinPrice
            print(
                f'MIN change!!! {coinsInMin[-1].time.strftime("%H:%M:%S")}: {coinsInMin[-1].price} change: {coinsInMin[-1].change}%'
            )
            currentTime = 0
            if len(coinsInMin) >= maxSize:
                writeToFile()
                coins.clear()
                coinsInMin.clear()
            coinsInMin.append(
                Bitcoin(
                    price=round(price, 3), time=now, change=round(minChange * 100, 3)
                )
            )
        time.sleep(interval)


def writeToFile():
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

    data = {"time": ticks, "price": prices, "change": changes}
    csvFile = pd.DataFrame(data, columns=["time", "price", "change"])
    csvFile.to_csv(
        f'./data/bitcoin_{datetime.now().strftime("%y_%m_%d_%H_%M_%S")}.csv',
        index=False,
    )
    data = {"time": ticksM, "price": pricesM, "change": changesM}
    csvFile2 = pd.DataFrame(data, columns=["time", "price", "change"])
    csvFile2.to_csv(
        f'./data/bitcoin_{datetime.now().strftime("%y_%m_%d_%H_%M_%S")}_M.csv',
        index=False,
    )


if __name__ == "__main__":
    try:
        main_loop()
    except (KeyboardInterrupt, ConnectionResetError):
        writeToFile()
        print("Exiting by user request.")
        sys.exit(0)
