import numpy as np

from scipy.stats import norm


def ret(mu, x):
    return float(mu.T.dot(x).values)


def vol(cov, x):
    return float(np.sqrt(x.T.dot(cov).dot(x)))


def var(mu, cov, alpha, x):
    return float(-mu.T.dot(x) - norm.ppf(alpha) * np.sqrt(x.T.dot(cov).dot(x)))


def cvar(mu, cov, alpha, x):
    return float(-mu.T.dot(x) - norm.pdf(norm.ppf(alpha)) / alpha * np.sqrt(x.T.dot(cov).dot(x)))
