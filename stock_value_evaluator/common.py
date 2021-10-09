import pandas as pd
import matplotlib.pyplot as plt


def calculate_intrinsic_value(
    cash_flow,
    total_debt,
    cash_and_ST_investments,
    EPS_growth_5Y,
    EPS_growth_6Y_to_10Y,
    EPS_growth_11Y_to_20Y,
    shares_outstanding,
    discount_rate,
    ticker,
):
    _cash_flow = cash_flow
    # Convert all percentages to decmials
    EPS_growth_5Y_d = EPS_growth_5Y / 100
    EPS_growth_6Y_to_10Y_d = EPS_growth_6Y_to_10Y / 100
    EPS_growth_11Y_to_20Y_d = EPS_growth_11Y_to_20Y / 100
    discount_rate_d = discount_rate / 100
    print("Discounted Cash Flows\n")

    # Lists of projected cash flows from year 1 to year 20
    cash_flow_list = []
    cash_flow_discounted_list = []
    year_list = []

    def print_year_rate(range, eps):
        for year in range:
            year_list.append(year)
            nonlocal _cash_flow
            _cash_flow *= 1 + eps
            cash_flow_list.append(_cash_flow)
            cash_flow_discounted = _cash_flow / ((1 + discount_rate_d) ** year)
            cash_flow_discounted_list.append(cash_flow_discounted)
            print(
                f'Year {year}: {"${:,.2f}".format(cash_flow_discounted)}'
            )  ## Print out the projected discounted cash flows

    # Years 1 to 5
    print_year_rate(range(1, 6), EPS_growth_5Y_d)
    # Years 6 to 10
    print_year_rate(range(6, 11), EPS_growth_6Y_to_10Y_d)
    # Years 11 to 20
    print_year_rate(range(11, 21), EPS_growth_11Y_to_20Y_d)

    intrinsic_value = (
        sum(cash_flow_discounted_list) - total_debt + cash_and_ST_investments
    ) / shares_outstanding
    df = pd.DataFrame.from_dict(
        {
            "Year": year_list,
            "Cash Flow": cash_flow_list,
            "Discounted Cash Flow": cash_flow_discounted_list,
        }
    )
    df.index = df.Year
    df.plot(kind="bar", title=f"Projected Cash Flows of {ticker}")

    return intrinsic_value
