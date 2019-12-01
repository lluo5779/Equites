import time

import numpy as np
import pandas as pd

from scipy.stats import norm, chi2
from scipy.optimize import minimize

from server.models.portfolio.config import SYMBOLS


def portfolio_value(no_shares, prices):
    return float(no_shares.T.dot(prices))


def make_constraint(type, func, args):
    return {'type': type, 'fun': func, 'args': args}


def optimize(mu, sigma, alpha, return_target, costs, prices, gamma, budget=1):

    # print("\n\nPERIOD ONE RETURNS {}".format(mu[0]))
    # print("\n\nPERIOD TWO RETURNS {}".format(mu[1]))
    #
    # print("\n\nPERIOD ONE COV {}".format(sigma[1]))
    # print("\n\nPERIOD TWO COV {}".format(sigma[1]))

    start = time.time()

    # the number of assets
    N = len(sigma[0])

    # the initial guess is an equally weighted portfolio
    x0 = np.ones(2*N) / (2*N)

    # augment prices to forecast stock value leading up to the next rebalancing
    prices = np.multiply(prices, 1 + mu[0])

    # exposure constraints
    bounds = []

    for cardinal in gamma[2]:
        bounds += [tuple(cardinal * x for x in gamma[1])]

    bounds *= 2

    # period one constraints
    budget1 = make_constraint('eq', budget_p1, (1, ))
    target1 = make_constraint('ineq', return_p1, (mu[0], return_target[0], ))

    # period two contraints
    budget2 = make_constraint('eq', budget_p2, (1, ))
    target2 = make_constraint('ineq', return_p2, (mu[1], return_target[1], ))

    soln = minimize(objective, x0,
                    args=(mu, sigma, gamma[0], alpha, costs, prices, gamma[3], budget),
                    method='SLSQP',
                    bounds=bounds,
                    constraints=[budget1, budget2, target1, target2])

    if not soln.success:
        # print("\n\nWARNING: the return targets are too aggressive for the risk tolerance level ...")

        # SAFE SOLUTION ... just try to get a positive return
        target1 = make_constraint('ineq', return_p1, (mu[0], 0,))
        target2 = make_constraint('ineq', return_p2, (mu[1], 0,))

        soln = minimize(objective, x0,
                        args=(mu, sigma, gamma[0], alpha, costs, prices, gamma[3], budget),
                        method='SLSQP',
                        bounds=bounds,
                        constraints=[budget1, budget2, target1, target2])

        # print("The safe portfolio is the closest to the target returns while respecting the risk exposure tolerance... \n")
        #
        # print('finished optimization in %f seconds.\n\n' % (time.time() - start))

        holdings = [ticker + "_holdings" for ticker in SYMBOLS]
        shares = budget * np.divide(soln.x[:int(len(mu[0]))], np.divide(prices, 1 + mu[0]))
        shares = pd.DataFrame(shares, index=holdings, columns=['shares'])

        print("\n\n{}".format(shares))

        return soln, shares


def objective(x, mu, sigma, gamma, alpha, costs, prices, risk_func, budget):
    # period one and period two weights
    x1 = x[:int(len(x)/2)]
    x2 = x[int(len(x)/2):]

    if risk_func == "MCVAR":
        psi = norm.pdf(norm.ppf(alpha[0])) / alpha[0]
        p1 = 2 * mu[0].T.dot(x1) - gamma[0] * psi * np.sqrt(x1.T.dot(sigma[0]).dot(x1))

        psi = norm.pdf(norm.ppf(alpha[1])) / alpha[1]
        p2 = 2 * mu[1].T.dot(x2) - gamma[0] * psi * np.sqrt(x2.T.dot(sigma[1]).dot(x2))

    elif risk_func == "SHARPE":
        p1 = mu[0].T.dot(x1) / np.sqrt(x1.T.dot(sigma[0]).dot(x1))
        p2 = mu[1].T.dot(x2) / np.sqrt(x2.T.dot(sigma[1]).dot(x2))

    shares_1 = budget * np.divide(x1, prices)
    shares_2 = shares_1 * x2

    t = costs.dot(np.sqrt(abs(shares_2 - shares_1)))

    return -1 * (p1 + p2 - gamma[1]*t)


def budget_p1(x, lev):
    return np.sum(x[:int(len(x)/2)]) - lev


def budget_p2(x, lev):
    return np.sum(x[int(len(x)/2):]) - lev


def return_p1(x, mu, return_target):
    return mu.T.dot(x[:int(len(x)/2)]) - return_target


def return_p2(x, mu, return_target):
    return mu.T.dot(x[int(len(x)/2):]) - return_target
