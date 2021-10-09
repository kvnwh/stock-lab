# To extract and parse fundamental data from finviz website
import requests
from bs4 import BeautifulSoup as bs

metric = ["Price", "EPS next 5Y", "Beta", "Shs Outstand", "EPS (ttm)"]


def fundamental_metric(soup, metric):
    # the table which stores the data in Finviz has html table attribute class of 'snapshot-td2'
    return soup.find(text=metric).find_next(class_="snapshot-td2").text


def get_finviz_data(ticker):
    try:
        url = "http://finviz.com/quote.ashx?t=" + ticker.lower()
        print(f"fin_viz url for {ticker}: {url}")
        result = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0"
            },
        ).content
        soup = bs(result, "html.parser")
        dict_finviz = {}
        for m in metric:
            dict_finviz[m] = fundamental_metric(soup, m)
        for key, value in dict_finviz.items():
            # replace percentages
            if value[-1] == "%":
                dict_finviz[key] = value[:-1]
                dict_finviz[key] = float(dict_finviz[key])
            # billion
            if value[-1] == "B":
                dict_finviz[key] = value[:-1]
                dict_finviz[key] = float(dict_finviz[key]) * 1000000000
            # million
            if value[-1] == "M":
                dict_finviz[key] = value[:-1]
                dict_finviz[key] = float(dict_finviz[key]) * 1000000
            try:
                dict_finviz[key] = float(dict_finviz[key])
            except:
                pass
    except Exception as e:
        print(e)
        print("Not successful parsing " + ticker + " data.")
    return dict_finviz


def get_discount_rate(beta):
    if isinstance(beta, float):
        beta = beta
    elif not beta.isnumeric():  # in case of `-`
        beta = 1
    print(f"beta: {beta}")
    discount_rate = 7
    if beta < 0.80:
        discount_rate = 5
    elif beta >= 0.80 and beta < 1:
        discount_rate = 6
    elif beta >= 1 and beta < 1.1:
        discount_rate = 6.5
    elif beta >= 1.1 and beta < 1.2:
        discount_rate = 7
    elif beta >= 1.2 and beta < 1.3:
        discount_rate = 7.5
    elif beta >= 1.3 and beta < 1.4:
        discount_rate = 8
    elif beta >= 1.4 and beta < 1.6:
        discount_rate = 8.5
    elif beta >= 1.61:
        discount_rate = 9
    return discount_rate
