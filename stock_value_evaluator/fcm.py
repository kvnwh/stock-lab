# Importing required modules
import configparser

import matplotlib.pyplot as plt
import pandas as pd

# Settings to produce nice plots in a Jupyter notebook
plt.style.use("ggplot")  # ('fivethirtyeight')
plt.rcParams["figure.figsize"] = [12, 7]

import json

# For parsing financial statements data from financialmodelingprep api
from urllib.request import urlopen


def get_jsonparsed_data(url):
    print(f"url: {url}")
    response = urlopen(url)
    data = response.read().decode("utf-8")
    return json.loads(data)


# Financialmodelingprep api url
base_url = "https://financialmodelingprep.com/api/v3/"
config = configparser.ConfigParser()
config.read("env.config")
apiKey = config["secrets"]["fcm_api_key"]


def get_fcm_data(ticker, quarterly=True, show_plot: bool = False):
    quarterlycashFlow = None
    if quarterly:
        # quarterly not supported in free tier!!!
        quarterlycashFlow = get_jsonparsed_data(
            base_url
            + "cash-flow-statement/"
            + ticker
            + "?period=quarter"
            + "&apikey="
            + apiKey
        )
        q_cash_flow_statement = (
            pd.DataFrame(quarterlycashFlow)
            .set_index("date")
            .iloc[:4]
            .apply(pd.to_numeric, errors="coerce")
        )  # extract for last 4 quarters
        q_cash_flow_statement.iloc[:, 4:].head()
        # q_cash_flow_statement.to_html('temp.html')

    # anual cash flow
    anualCashFlow = get_jsonparsed_data(
        base_url + "cash-flow-statement/" + ticker + "?apikey=" + apiKey
    )
    anual_cash_flow_statement = (
        pd.DataFrame(anualCashFlow)
        .set_index("date")
        .apply(pd.to_numeric, errors="coerce")
    )
    anual_cash_flow_statement.iloc[:, 4:].head()

    # merge cash flows from quarters to anual
    anual_cash_flow_statement = anual_cash_flow_statement[::-1]
    if quarterly:
        ttm_cash_flow_statement = (
            q_cash_flow_statement.sum()
        )  # sum up last 4 quarters to get TTM cash flow
        anual_cash_flow_statement = anual_cash_flow_statement.append(
            ttm_cash_flow_statement.rename("TTM")
        )

    anual_cash_flow_statement = anual_cash_flow_statement.drop(["netIncome"], axis=1)

    final_cash_flow_statement = anual_cash_flow_statement[
        ::-1
    ]  # reverse list to show most recent ones first
    final_cash_flow_statement.iloc[:, 4:].head()

    if show_plot:
        final_cash_flow_statement[["freeCashFlow"]].iloc[::-1].iloc[-15:].plot(
            kind="bar", title=ticker + " Cash Flows"
        )

    balance_sheet_url = (
        base_url + "balance-sheet-statement/" + ticker + "?apikey=" + apiKey
    )
    if quarterly:
        balance_sheet_url += "&period=quarter"
    balanceSheet = get_jsonparsed_data(balance_sheet_url)
    # anualBalanceSheet = get_jsonparsed_data(base_url+'balance-sheet-statement/' + ticker + '?apikey=' + apiKey)
    balance_statement = (
        pd.DataFrame(balanceSheet)
        .set_index("date")
        .apply(pd.to_numeric, errors="coerce")
    )
    balance_statement.iloc[:, 4:].head()

    cash_flow = final_cash_flow_statement.iloc[0]["freeCashFlow"]
    total_debt = balance_statement.iloc[0]["totalDebt"]
    cash_and_ST_investments = balance_statement.iloc[0]["cashAndShortTermInvestments"]

    res = {
        "totalDebt": total_debt,
        "freeCashFlow": cash_flow,
        "cashAndShortTermInvestments": cash_and_ST_investments,
    }
    # plt.show()
    return res
