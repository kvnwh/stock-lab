# To extract and parse fundamental data from finviz website
import re

import requests
from bs4 import BeautifulSoup as bs

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0"
}
ONE_MIL = 1000000


def get_value(soup: bs, text: str):
    return soup.find(text=text).find_next("td").text


def convert_to_dollar(amount: str):
    # if not amount.isnumeric():
    #   print(f'found non-numeric value: {amount}, default to 0')
    #   return 0
    symbol = 1
    if amount.startswith("("):
        symbol = -1
    new_amount = re.sub("[(,)]", "", amount)

    dollar = float(new_amount) * symbol * ONE_MIL
    # print(f'convert {amount} to {"${:,.2f}".format(dollar)}')
    return dollar


def get_cashFlow_ttm(soup: bs):
    q1 = soup.find(text="Free Cash Flow").find_next("td")
    q1CashFlow = convert_to_dollar(q1.text)
    q2 = q1.find_next("td")
    q2CashFlow = convert_to_dollar(q2.text)
    q3 = q2.find_next("td")
    q3CashFlow = convert_to_dollar(q3.text)
    q4 = q3.find_next("td")
    q4CashFlow = convert_to_dollar(q4.text)
    ttmCashFlow = q1CashFlow + q2CashFlow + q3CashFlow + q4CashFlow
    return ttmCashFlow


def get_wsj_data(ticker: str):
    baseUrl = f"https://www.wsj.com/market-data/quotes/{ticker}/financials/quarter"
    try:
        quarter_cash_flow_url = f"{baseUrl}/cash-flow"
        print(f"quarter_cash_flow_url: {quarter_cash_flow_url}")
        quarter_cash_flow_result = requests.get(
            quarter_cash_flow_url, headers=headers
        ).content
        quarter_cash_flow_soup = bs(quarter_cash_flow_result, "html.parser")

        cashflow = get_cashFlow_ttm(quarter_cash_flow_soup)
        # print(f'TTM Free cash flow: {"${:,.2f}".format(cashflow)}')

        quarter_balance_sheet_url = f"{baseUrl}/balance-sheet"
        print(f"balance_sheet_url: {quarter_balance_sheet_url}")
        quarter_balance_sheet_result = requests.get(
            quarter_balance_sheet_url, headers=headers
        ).content
        quarter_balance_sheet_soup = bs(quarter_balance_sheet_result, "html.parser")
        longTermDebt = convert_to_dollar(
            get_value(quarter_balance_sheet_soup, "Long-Term Debt")
        )
        shortTermDebt = convert_to_dollar(
            get_value(quarter_balance_sheet_soup, "Short Term Debt")
        )
        cashAndShortTermInvestments = convert_to_dollar(
            get_value(quarter_balance_sheet_soup, "Cash & Short Term Investments")
        )
        # print(f'LT debt: {"${:,.2f}".format(longTermDebt)}')
        # print(f'ST debt: {"${:,.2f}".format(shortTermDebt)}')
        totalDebt = longTermDebt + shortTermDebt
        # print(f'total debt: {"${:,.2f}".format(totalDebt)}')
        # print(f'cashAndShortTermInvestments: {"${:,.2f}".format(cashAndShortTermInvestments)}')

        res = {
            "totalDebt": totalDebt,
            "freeCashFlow": cashflow,
            "cashAndShortTermInvestments": cashAndShortTermInvestments,
        }
        return res
    except Exception as e:
        print(e)
        print("Not successful parsing " + ticker + " data.")
    return None
