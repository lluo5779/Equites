import os
import time

import pandas as pd
import pandas_datareader.data as web

from datetime import datetime
from regime_switch_model.rshmm import *

BASEPATH = "/server/models/portfolio/"


## *********************************************************************************************************************
#  helper functions
## *********************************************************************************************************************


def fama_french(start_date, end_date, save):
    start = time.time()

    if datetime.strptime(start_date, "%Y-%m-%d") <= datetime.strptime('2014-11-05', "%Y-%m-%d"):
        factors = pd.read_csv(os.getcwd() + BASEPATH + r'/data/ff_factors.csv', index_col=0)

        print("\n\nWARNING: start date is beyond what's stored in the online database ... retrieved old data")
    else:
        try:
            factors = web.DataReader('F-F_Research_Data_5_Factors_2x3_daily', 'famafrench')[0]

            print("\n\nSUCCESS: captured new fama french data ...")
        except:
            factors = pd.read_csv(os.getcwd() + BASEPATH + r'/data/ff_factors.csv', index_col=0)

            print("\n\nERROR: failed to retrieve new fama french data ... retrieved old data")

    print('finished retrieving fama french data in %f seconds.\n' % (time.time() - start))

    factors.rename(columns={'Mkt-RF': 'MKT'}, inplace=True)

    factors.replace(-99.99, np.nan)
    factors.replace(-999, np.nan)

    factors = factors / 100
    factors = factors.loc[start_date:end_date, :].iloc[1:]
    factors.index = pd.to_datetime(factors.index)

    if save:
        factors.to_csv(os.getcwd() + BASEPATH + r'/data/factors.csv')

    return factors


def business_days(start_date, end_date):
    return len(pd.bdate_range(start_date, end_date))


## *********************************************************************************************************************
#  regime switching model
## *********************************************************************************************************************


def regime_switch(R, F, tickers, save=True):
    start = time.time()

    try:
        model = HMMRS(n_components=2)
        model.fit(R, F)

        transmat = pd.DataFrame(model.transmat_)
        loading_one = pd.DataFrame(model.loadingmat_[0], index=tickers,
                                   columns=['INT', 'MKT', 'SMB', 'HML', 'RMW', 'CMA'])
        loading_two = pd.DataFrame(model.loadingmat_[1], index=tickers,
                                   columns=['INT', 'MKT', 'SMB', 'HML', 'RMW', 'CMA'])
        cov_one = pd.DataFrame(model.covmat_[0], index=tickers, columns=tickers)
        cov_two = pd.DataFrame(model.covmat_[1], index=tickers, columns=tickers)

        print("\n\nSUCCESS: fitted the regime switching factor model")

        if save:
            transmat.to_csv(os.getcwd() + BASEPATH + r'/data/transition_matrix.csv')
            loading_one.to_csv(os.getcwd() + BASEPATH + r'/data/loadings_one.csv')
            loading_two.to_csv(os.getcwd() + BASEPATH + r'/data/loadings_two.csv')
            cov_one.to_csv(os.getcwd() + BASEPATH + r'/data/cov_one.csv')
            cov_two.to_csv(os.getcwd() + BASEPATH + r'/data/cov_two.csv')

    except:
        transmat = pd.read_csv(os.getcwd() + BASEPATH + r'/data/transition_matrix.csv', index_col=0)
        loading_one = pd.read_csv(os.getcwd() + BASEPATH + r'/data/loadings_one.csv', index_col=0)
        loading_two = pd.read_csv(os.getcwd() + BASEPATH + r'/data/loadings_two.csv', index_col=0)
        cov_one = pd.read_csv(os.getcwd() + BASEPATH + r'/data/cov_one.csv', index_col=0)
        cov_two = pd.read_csv(os.getcwd() + BASEPATH + r'/data/cov_two.csv', index_col=0)

        print("\n\nERROR: failed to fit the regime switching factor model ... retrieving prior calibration")

    print('finished fitting the regime switching factor model in %f seconds.\n' % (time.time() - start))

    return transmat, (loading_one, loading_two), (cov_one, cov_two)


def current_regime(R, F, loadings, baseline):
    rss = [None] * 2

    for i in range(2):
        rss[i] = np.sum((R[:-baseline] - F[:-baseline].dot(loadings[i].values.T)) ** 2)

    return rss.index(min(rss))


def expected_returns(F, transmat, loadings, regime):
    f = F.mean(axis=0)
    mu = 0

    for n in range(2):
        mu = mu + transmat.values[regime][n] * (f.dot(loadings[n].values.T))

    return mu


def covariance(R, F, transmat, loadings, covariances, regime):
    # hard coded because yes

    cov = np.empty((len(R[1]), len(R[1])))
    f = F.mean(axis=0)

    D0 = pd.DataFrame(R - F.dot(loadings[0].values.T)).cov().values
    V0 = loadings[0].values.dot(pd.DataFrame(F).cov().values).dot(loadings[0].values.T)
    m0 = f.dot(loadings[0].values.T)

    D1 = pd.DataFrame(R - F.dot(loadings[1].values.T)).cov().values
    V1 = loadings[1].values.dot(pd.DataFrame(F).cov().values).dot(loadings[1].values.T)
    m1 = f.dot(loadings[1].values.T)

    cov = transmat.values[regime][0] * (V0 + D0 + (1 - transmat.values[regime][0]) * np.outer(m0, m0)) \
          + transmat.values[regime][1] * (V1 + D1 + (1 - transmat.values[regime][1]) * np.outer(m1, m1)) \
          - transmat.values[regime][0] * transmat.values[regime][1] * (np.outer(m0, m1) + np.outer(m1, m0))

    return cov
