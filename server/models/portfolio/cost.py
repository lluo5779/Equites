import time

import numpy as np

from server.models.stock.tiingo import get_data

TIINGO_ENDPOINTS = {'eod': 'https://api.tiingo.com/tiingo/daily/%s/prices?startDate=%s&endDate=%s',
                    'spreads': 'https://api.tiingo.com/iex/%s'}

def costs(tickers, cov, prices, start_date, end_date, alpha):

    start = time.time()

    volumes = get_data(tickers, 'volume', start_date, end_date, save=True).mean()

    print('finished calculating cost coefficients in %f seconds.\n\n' % (time.time() - start))

    return 0.05/100 * (1 - volumes / volumes.sum()).mul(prices) + alpha * np.diag(cov) / (prices.mul(np.sqrt(volumes)))








