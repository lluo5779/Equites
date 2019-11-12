import requests
from pandas_datareader import tiingo
from datetime import date, timedelta
from server.models.stock.config import SYMBOLS, START_DATE, END_DATE, TIINGO_TOKEN


class TiingoDailyReader(object):
    reader = None

    @staticmethod
    def initialize(symbols=SYMBOLS, start=START_DATE, end=END_DATE, api_key=list(TIINGO_TOKEN)[0]):
        print("Initializing Tiingo reader for {} stocks with start {} and end {}".format(len(symbols), start, end))
        TiingoDailyReader.reader = tiingo.TiingoDailyReader(
            symbols, start=start, end=end, api_key=api_key
        )

    @staticmethod
    def getEndOfDayPrices():
        return TiingoDailyReader.reader.read()
