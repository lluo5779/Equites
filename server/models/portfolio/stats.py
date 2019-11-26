import numpy as np

from scipy.stats import norm


def ret(mu, x):
    print(mu)
    print(x)

    return float(mu.T.dot(x).values)



def vol(cov, x):
    print(cov)
    print(x)
    try:
        return float(np.sqrt(x.T.dot(cov).dot(x)).values)
    except:
        return float(np.sqrt(x.T.dot(cov).dot(x)))


def var(mu, cov, alpha, x):
    print(mu)
    print(cov)
    print(x)
    try:
        return float(-mu.T.dot(x).values - norm.ppf(alpha) * np.sqrt(x.T.dot(cov).dot(x)).values)
    except:
        return float(-mu.T.dot(x).values - norm.ppf(alpha) * np.sqrt(x.T.dot(cov).dot(x)))


def cvar(mu, cov, alpha, x):
    try:
        return float(-mu.T.dot(x).values - norm.pdf(norm.ppf(alpha)) / alpha * np.sqrt(x.T.dot(cov).dot(x)).values)
    except:
        return float(-mu.T.dot(x).values - norm.pdf(norm.ppf(alpha)) / alpha * np.sqrt(x.T.dot(cov).dot(x)))


