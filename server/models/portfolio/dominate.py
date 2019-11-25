import os

import pandas as pd

from datetime import datetime
from scipy.stats.mstats import gmean
from dateutil.relativedelta import relativedelta

from server.models.portfolio.bt import back_test
from server.models.portfolio.prepare import prepare
from server.models.portfolio.rs import business_days
from server.models.portfolio.optimize import optimize
from server.models.portfolio.config import SYMBOLS


def dominate(portfolio, mu, cov, cost, prices, risk_tolerance, single_period=False):
    """By Default, always multi-period"""

    # start date for the based portfolio to be determined ... always assign to past 6 months (ie rebalance the period)
    start_date = (datetime.now() - relativedelta(months=6)).strftime("%Y-%m-%d")

    # get the number of days in the backtest period ... to determine target returns and variances later
    days = business_days(start_date, datetime.now().strftime("%Y-%m-%d"))

    # call backtest to get the value of the portfolio
    portfolio_value = back_test(portfolio, start_date, end_date=None, dollars=None)[0].sum(axis=1)

    print(">>> portfolio_value: ", portfolio_value)

    # calculate portfolio returns
    portfolio_returns = (portfolio_value / portfolio_value.shift(1) - 1).dropna()

    print(">>> portfolio_returns: ", portfolio_returns)

    # assign the target return and variance
    target_returns = (gmean(portfolio_returns + 1, axis=0) - 1) * days
    target_variance = portfolio_returns.var() * days

    mu_p2 = mu[0] if single_period else mu[1]
    cov_p2 = cov[0] if single_period else cov[1]

    soln, agg_soln = optimize(mu=(mu[0], mu_p2),
                              sigma=(cov[0], cov_p2),
                              alpha=(0.05, 0.10),
                              return_target=(target_returns, target_returns),
                              costs=cost,
                              prices=prices,
                              gamma=risk_tolerance[2])

    return soln, agg_soln


if __name__ == "__main__":

    ## *********************************************************************************************************************
    #  INPUTS
    ## *********************************************************************************************************************
    mu, cov, cost, prices = prepare()

    # base portfolio ... comes as an input
    portfolio = {'SPY': 0.25, 'MSFT': 0.10, 'JPM': 0.25, 'NTIOF': 0.40}

    # our tracked assets
    tickers = SYMBOLS #list(pd.read_csv(os.getcwd() + r'/data/tickers.csv')['Tickers'])

    # the number of assets
    N = len(tickers)

    # user choose which assets (from the 18 we follow) should be included.
    cardinality = [1] * 7 + [0] * (N - 7)
    risk_tolerance = [((1, 10), (0, 0.10), cardinality, 'SHARPE'),
                      ((5, 5), (0, 0.20), cardinality, 'SHARPE'),
                      ((10, 1), (-0.05, 0.50), cardinality, 'SHARPE')]

    # user chooses if they want to do 2 period optimization or not ... choosing whether they want the portfolio to just be buy and hold
    single_period = False

    soln, agg_soln = dominate(portfolio, mu, cov, cost, prices, risk_tolerance, single_period)

    x1 = pd.DataFrame(soln.x[:N])
    x2 = pd.DataFrame(soln.x[N:])

    print('\n\n********************************************************************')
    print('\tperiod one results')
    print('********************************************************************\n')
    print(x1)

    print('\n\n********************************************************************')
    print('\tperiod two results')
    print('********************************************************************\n')
    print(x2)
