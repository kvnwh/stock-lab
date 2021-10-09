# Importing required modules
import numpy as np

from common import calculate_intrinsic_value
from fin_viz import get_finviz_data, get_discount_rate
from fcm import get_fcm_data
from wsj import get_wsj_data


def evaluate(ticker: str):
    partial_data = get_wsj_data(ticker)
    if partial_data == None:
        print("something wrong with quarterly data, trying anual data")
        partial_data = get_fcm_data(ticker, False)  # get using fcm api
    print(partial_data)
    cash_flow = partial_data["freeCashFlow"]
    total_debt = partial_data["totalDebt"]
    cash_and_ST_investments = partial_data["cashAndShortTermInvestments"]

    finviz_data = get_finviz_data(ticker)
    print(finviz_data)

    discount_rate = get_discount_rate(finviz_data["Beta"])

    EPS_growth_5Y = finviz_data["EPS next 5Y"]
    EPS_growth_6Y_to_10Y = EPS_growth_5Y * (
        4 / 5
    )  # Half the previous growth rate, conservative estimate
    EPS_growth_11Y_to_20Y = np.minimum(
        EPS_growth_6Y_to_10Y, 4
    )  # Slightly higher than long term inflation rate, conservative estimate

    shares_outstanding = finviz_data["Shs Outstand"]

    print("Free Cash Flow: ", "${:,.2f}".format(cash_flow))
    print("Total Debt: ", "${:,.2f}".format(total_debt))
    print(
        "Cash and Short Term Investments: ", "${:,.2f}".format(cash_and_ST_investments)
    )

    print("EPS Growth 5Y: ", EPS_growth_5Y)
    print("EPS Growth 6Y to 10Y: ", EPS_growth_6Y_to_10Y)
    print("EPS Growth 11Y to 20Y: ", EPS_growth_11Y_to_20Y)

    print(f"Discount Rate: {discount_rate}%")
    print("Shares Outstanding: ", shares_outstanding)

    intrinsic_value = calculate_intrinsic_value(
        cash_flow,
        total_debt,
        cash_and_ST_investments,
        EPS_growth_5Y,
        EPS_growth_6Y_to_10Y,
        EPS_growth_11Y_to_20Y,
        shares_outstanding,
        discount_rate,
        ticker,
    )
    current_price = finviz_data["Price"]
    margin_of_safety = (1 - current_price / intrinsic_value) * 100
    print("Intrinsic Value: ", intrinsic_value)
    print("Current Price: ", current_price)
    print("Margin of Safety: ", margin_of_safety)

    return {
        "intrinsicValue": intrinsic_value,
        "currentPrice": current_price,
        "marginOfSafety": margin_of_safety,
    }