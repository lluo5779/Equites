import uuid
import pandas as pd

from server.common.database import Database
from server.models.stock.config import SYMBOLS, COLLECTION, START_DATE, END_DATE
from server.models.stock.utils import TiingoDailyReader
from server.models.stock.tiingo import get_data

import datetime


def fetchEodPrices(fromtimeon=None, timestamp=None, get_latest=False):
    query = """select * from {}""".format(COLLECTION)
    if get_latest:
        query = query + """ order by date desc limit 1"""  # select * from prices order by date desc limit 1

    if fromtimeon is not None:
        query = query + """ where date between '{}' and '{}' order by date desc limit 1;""".format(
            fromtimeon.strftime('%Y-%m-%d'),
            datetime.datetime.utcnow().strftime('%Y-%m-%d'))

    if timestamp is not None:
        query = query + """ where date between '{}' and '{}' order by date desc limit 1;""".format(
            (timestamp - datetime.timedelta(days=5)).strftime('%Y-%m-%d'),
            (timestamp + datetime.timedelta(hours=1)).strftime('%Y-%m-%d'))

    df = pd.read_sql(query, con=Database.DATABASE.engine, index_col='date')

    return df


class Stocks(object):
    # Stocks class creates portfolio instances for auth stock using stocks in Stock class
    def __init__(self, _id=None):
        self.tickers = SYMBOLS
        self._id = uuid.uuid4().hex if _id is None else _id
        self.tiingo_reader = TiingoDailyReader()
        self.tiingo_reader.initialize()

    def update_database(self):
        eod_prices = get_data(SYMBOLS, 'adjClose', start_date, end_date, save=True)
        eod_prices.to_sql(COLLECTION, con=Database.DATABASE.engine, if_exists="replace", index=True)

    @classmethod
    def get_all(self):  # Retrieves all stock records
        return pd.read_sql('select * from "{}" ;'.format(COLLECTION),
                           Database.DATABASE.engine)

    @classmethod
    def get_by_id(self, id):  # Retrieves portfolio from MongoDB by its unique id
        return pd.read_sql(
            """SELECT "symbol","date", "adjClose", "adjVolume" FROM "{}" WHERE "symbol" LIKE '{}'; """.format(
                COLLECTION, id),
            Database.DATABASE.engine)
