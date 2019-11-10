import uuid
from server.common.database import Database
from server.models.stock.stock import Stocks
from server.models.portfolio.config import COLLECTION, START_DATE, END_DATE
import pandas as pd


class Portfolio(object):
    # Portfolio class creates portfolio instances for auth portfolios using stocks in Stock class

    def __init__(self, username, user_email=None, risk_appetite=None, tickers=None, weights=None, _id=None):
        self.username = username
        info = self.get_params()
        self.user_email = info['user_email'] if user_email is None else user_email
        self.risk_appetite = info['risk_appetite'] if risk_appetite is None else risk_appetite
        self.tickers = info['tickers'] if tickers is None else tickers
        self.weights = info['weights'] if weights is None else weights
        self._id = uuid.uuid4().hex if _id is None else _id

    def __repr__(self):
        return "<Portfolio for auth {}>".format(self.username)

    def get_params(self):
        try:
            return pd.read_sql(
                """select "email","date", "risk_appetite", "tickers", "weights", "_id" from "{}" where "username" like '{}';""".format(
                    COLLECTION, self.username),
                Database.DATABASE.engine)
        except:
            print('User is not in database')
            return {
                'username': self.username,
                'user_email': None,
                'risk_appetite': None,
                'tickers': None,
                'weights': None,
                '_id': None
            }

    def runMVO(self, start_date=START_DATE, end_date=END_DATE, samples=100):
        return

    def plot_comparison(self, risk_data, ret_data, gamma_vals, risk_data_minVar, ret_data_minVar, std, mu):
        return

    def update_portfolio(self):
        d = {
            'username': self.username,
            'user_email': self.user_email,
            'risk_appetite': self.risk_appetite,
            'tickers': self.tickers,
            'weights': self.weights,
            '_id': self._id
        }
        print(d)
        print(d.keys())
        print(d.values())
        names = ", ".join(list(d.keys()))

        vals = "'" + "','".join([str(i) for i in list(d.values())]) + "'"
        statement = """INSERT INTO {} ({}) VALUES ({});""".format(COLLECTION, names, vals)
        print(statement)
        Database.DATABASE.engine.execute(statement)
