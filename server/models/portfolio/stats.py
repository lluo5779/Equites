import numpy as np

from scipy.stats import norm


def ret(mu, x):
    return float(mu.T.dot(x).values)


def vol(cov, x):
    return float(np.sqrt(x.T.dot(cov).dot(x)).values)


def var(mu, cov, alpha, x):
    return float(-mu.T.dot(x).values - norm.ppf(alpha) * np.sqrt(x.T.dot(cov).dot(x)).values)


def cvar(mu, cov, alpha, x):
    return float(-mu.T.dot(x).values - norm.pdf(norm.ppf(alpha)) / alpha * np.sqrt(x.T.dot(cov).dot(x)).values)


