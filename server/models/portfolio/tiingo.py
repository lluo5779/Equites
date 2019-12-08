import os
import time
import requests
import datetime
import pandas as pd
from server.models.portfolio.config import SYMBOLS
from server.models.stock.stock import fetchEodPrices

TIINGO_KEY = '6d2d79e31c7c1b6bae9be7e8986b4a5fe3ce5111'
TIINGO_EOD = 'https://api.tiingo.com/tiingo/daily/%s/prices?startDate=%s&endDate=%s'


def get_data(tickers, data_point, start_date, end_date, save=True, fail_safe=True, tore=False):
    data = pd.DataFrame()
    start = time.time()

    try:
        if tore:
            for ticker in tickers:
                ticker = ticker.upper()
                data[ticker] = tiingo(ticker, start_date, end_date)[data_point]  # Series with date as index and prices as values
        else:
            preset_prices = fetchEodPrices()
            data[preset_prices.columns] = preset_prices

    except Exception as e:
        if fail_safe:
            data = pd.read_csv(os.getcwd() + r'/server/models/portfolio/data/%s.csv' % data_point, index_col=0)
            data.index = pd.to_datetime(data.index)
            return data
        else:
            return None

    data.index = pd.to_datetime(data.index, utc=True)

    if save:
        data.to_csv(os.getcwd() + r'/data/%s.csv' % data_point)

    return data.dropna()


def tiingo(ticker, start_date, end_date):
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Token %s' % TIINGO_KEY}

    response = requests.get(TIINGO_EOD % (ticker, start_date, end_date),
                            headers=headers).json()

    # print('tiingo response: ', response)
    data = pd.DataFrame(response)

    return data.set_index('date')
