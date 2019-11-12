import uuid
import pandas as pd

from server.common.database import Database
from server.models.stock.config import SYMBOLS, COLLECTION, START_DATE, END_DATE
from server.models.stock.utils import TiingoDailyReader


class Stocks(object):
    # Stocks class creates portfolio instances for auth stock using stocks in Stock class
    def __init__(self, _id=None):
        self.tickers = SYMBOLS
        self._id = uuid.uuid4().hex if _id is None else _id
        self.tiingo_reader = TiingoDailyReader()
        self.tiingo_reader.initialize()

    def update_database(self):
        eod_prices = self.tiingo_reader.getEndOfDayPrices()
        print(Database)
        print(Database.DATABASE)
        eod_prices.to_sql(COLLECTION, con=Database.DATABASE.engine, if_exists="replace", index=True)

    @classmethod
    def get_all(self):  # Retrieves all stock records
        return pd.read_sql('select "symbol","date", "adjClose","adjVolume" from "{}" ;'.format(COLLECTION),
                           Database.DATABASE.engine)

    @classmethod
    def get_by_id(self, id):  # Retrieves portfolio from MongoDB by its unique id
        return pd.read_sql(
            """SELECT "symbol","date", "adjClose", "adjVolume" FROM "{}" WHERE "symbol" LIKE '{}'; """.format(
                COLLECTION, id),
            Database.DATABASE.engine)
