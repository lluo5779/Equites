import time

import numpy as np

from scipy.stats import norm, chi2
from scipy.optimize import minimize


def portfolio_value(weights, prices):
    return float(weights.values.T.dot(prices.values))


def optimize(mu, sigma, alpha, return_target, costs, prices, gamma):

    start = time.time()

    # the number of assets
    N = len(sigma[0])

    # the initial guess is an equally weighted portfolio
    x0 = np.ones(2*N) / (2*N)

    # augment prices to forecast stock value leading up to the next rebalancing
    print(prices)
    print(mu[0])
    prices = np.multiply(prices, 1 + mu[0])

    # exposure constraints
    bounds = [gamma[1]] * 2 *  N

    # budget constraints
    budget_1p = {'type': 'ineq',
                 'fun': budget_p1,
                 'args': (1, )}

    budget_1n = {'type': 'ineq',
                 'fun': budget_p1,
                 'args': (-1, )}

    # budget constraints
    budget_2p = {'type': 'ineq',
                 'fun': budget_p2,
                 'args': (1, )}

    budget_2n = {'type': 'ineq',
                 'fun': budget_p2,
                 'args': (-1, )}

    # return constraints
    ret_1 = {'type': 'ineq',
           'fun': return_p1,
           'args': (mu[0], return_target[0], )}

    ret_2 = {'type': 'ineq',
            'fun': return_p2,
            'args': (mu[1], return_target[1],)}

    soln = minimize(objective, x0,
                    args=(mu, sigma, gamma[0], alpha, costs, prices),
                    #jac=jaco,
                    method='SLSQP',
                    bounds=bounds,
                    constraints=[budget_1p, budget_1n, budget_2p, budget_2n, ret_1, ret_2])

    if soln.success:
        print("SUCCESS: optimized the Mean-CVaR Tradeoff and met the return goals")
    else:
        print("WARNING: the return targets are too aggressive for the risk tolerance level ... \n")

        # return constraints
        ret_1 = {'type': 'ineq',
                 'fun': return_p1,
                 'args': (mu[0], 0,)}

        ret_2 = {'type': 'ineq',
                 'fun': return_p2,
                 'args': (mu[1], 0,)}

        soln = minimize(objective, x0,
                        args=(mu, sigma, gamma[0], alpha, costs, prices),
                        # jac=jaco,
                        method='SLSQP',
                        bounds=bounds,
                        constraints=[budget_1, budget_2, ret_1, ret_2])

        print("The portfolio is the closest to the target returns ...")

    print('finished optimization in %f seconds.\n\n' % (time.time() - start))

    return soln


def jaco(x, mu, sigma, gamma, alpha, costs, prices):
    psi = norm.pdf(norm.ppf(alpha)) / alpha

    return -1 * (2 * mu - gamma[0] * psi / (np.sqrt(x.T.dot(sigma).dot(x))) * sigma.dot(x))


def objective(x, mu, sigma, gamma, alpha, costs, prices):
    # period one and period two weights
    x1 = x[:int(len(x)/2)]
    x2 = x[int(len(x)/2):]

    psi = norm.pdf(norm.ppf(alpha[0])) / alpha[0]
    p1 = 2 * mu[0].T.dot(x1) - gamma[0] * psi * np.sqrt(x1.T.dot(sigma[0]).dot(x1))

    psi = norm.pdf(norm.ppf(alpha[1])) / alpha[1]
    p2 = 2 * mu[1].T.dot(x2) - gamma[0] * psi * np.sqrt(x2.T.dot(sigma[1]).dot(x2))

    # transaction costs
    print(x1)
    print(x2)
    print(costs)
    t = costs.transpose().dot(np.multiply((x2 - x1), np.multiply(x1, prices)))

    return -1 * (p1 + p2 - gamma[1] * t) / 1000


def budget_p1(x, lev):
    return np.sum(x[:int(len(x)/2)]) - lev


def budget_p2(x, lev):
    return np.sum(x[int(len(x)/2):]) - lev


def return_p1(x, mu, return_target):
    return mu.T.dot(x[:int(len(x)/2)]) - return_target


def return_p2(x, mu, return_target):
    return mu.T.dot(x[int(len(x)/2):]) - return_target
