import time

import pandas as pd

from server.models.portfolio.tiingo import get_data
from datetime import datetime
from dateutil.relativedelta import relativedelta


## *********************************************************************************************************************
# INPUTS
# - ::string:: starting date; REQUIRED
# - ::string:: ending date; OPTIONAL, defaults to present day
# - ::dictionary:: {keys: ::string:: tickers, values: ::float:: weights}
# - ::float:: starting investment amount; OPTIONAL, defaults to 1

# OUTPUTS
# - ::dataframe:: portfolio value over backtest period
# - ::boolean:: success
# - ::string:: status

# ERROR CATCHING
# - error 1: portfolio weights sum to less than one
# - resolution 1: keep weights and pad the remaining amount with cash, returning 1% per year or daily rd = (1.01)^(1/250) - 1

# - error 2: portfolio weights sum to more than one
# - resolution 2: compute the portfolio and raise a warning ... assume the leverage is being funded elsewhere

# - error 3: unable to find an asset
# - resolution 3: cannot compute, return an error with the unknown assets

# - error 4: new issuances
# - resolution 4: if not all assets have prices over the backtest period, truncate to the earliest date with data

## *********************************************************************************************************************

# portfolio = {'AAPL': 0.25, 'MSFT': 0.10, 'JPM': 0.25, 'NTIOF': 0.40}
# start_date = (datetime.now() - relativedelta(years=6)).strftime("%Y-%m-%d")

def back_test(portfolio, start_date, end_date=None, dollars=None, tore=False):

    if end_date is None: end_date = datetime.now().strftime("%Y-%m-%d")
    if dollars is None: dollars = 1

    prices = get_data(portfolio.keys(), 'adjClose', start_date, end_date, save=False, fail_safe=True, tore=tore)

    if prices is None:
        msg = "ERROR: could not retrieve pricing data for one or more of the assets given."
        print("\n\n{}".format(msg))

        return None, False, msg

    msg = "SUCCESS: retrieved pricing data all assets given."
    # print("\n\n{}".format(msg))
    # print(prices.tail(10))

    # check if any prices are missing ... if so drop the row
    if prices.isnull().values.any():
        msg += "\nWARNING: there are %f missing price entries ... truncating to a common base."

        prices.dropna(inplace=True)

    # check if the portfolio's budget is under utilized
    budget = sum(portfolio.values())
    portfolio['CASH'] = 1 - budget

    if budget != 1:
        msg += "\nWARNING: adding a CASH position since the budget of the portfolio was under-utilized."
    else:
        msg += "\nSUCCESS: budget is fully utilized."

    # get the number of shares
    shares = dollars * pd.Series(portfolio) / prices.iloc[0]

    # calculate portfolio value per share ... to recover portfolio value per day, do value.sum(axis=1)
    value = prices * shares

    return value, True, msg
