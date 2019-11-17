import os
import time

import pandas as pd
import pandas_datareader.data as web
import numpy as np
import datetime


def fama_french(start_date, end_date, save):
    start = time.time()

    if datetime.strptime(start_date, "%Y-%m-%d") <= datetime.strptime('2014-11-05', "%Y-%m-%d"):
        factors = pd.read_csv(os.getcwd() + r'/data/ff_factors.csv', index_col=0)

        print("\n\nWARNING: start date is beyond what's stored in the online database ... retrieved old data")
    else:
        try:
            factors = web.DataReader('F-F_Research_Data_5_Factors_2x3_daily', 'famafrench')[0]

            print("\n\nSUCCESS: captured new fama french data ...")
        except:
            factors = pd.read_csv(os.getcwd() + r'/data/ff_factors.csv', index_col=0)

            print("\n\nERROR: failed to retrieve new fama french data ... retrieved old data")

    print('finished retrieving fama french data in %f seconds.\n' % (time.time() - start))

    factors.rename(columns={'Mkt-RF': 'MKT'}, inplace=True)

    factors.replace(-99.99, np.nan)
    factors.replace(-999, np.nan)

    factors = factors / 100
    factors = factors.loc[start_date:end_date, :].iloc[1:]
    factors.index = pd.to_datetime(factors.index)

    if save:
        factors.to_csv(os.getcwd() + r'/data/factors.csv')

    return factors


