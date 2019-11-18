import uuid
from server.common.database import Database
from server.models.stock.stock import Stocks
from server.models.portfolio.config import COLLECTION, START_DATE, END_DATE, SYMBOLS
import pandas as pd
from server.models.portfolio.optimize import optimize
from server.models.portfolio.stats import *


class Portfolio(object):
    # Portfolio class creates portfolio instances for auth portfolios using stocks in Stock class

    def __init__(self, username, user_email=None, risk_appetite=None, tickers=None, weights=None, _id=None):
        self.username = username
        # portfolio = self.get_params()
        # self.user_email = info['user_email'] if user_email is None else user_email
        # self.risk_appetite = info['risk_appetite'] if risk_appetite is None else risk_appetite
        # self.tickers = info['tickers'] if tickers is None else tickers
        # self.weights = info['weights'] if weights is None else weights
        # self._id = uuid.uuid4().hex if _id is None else _id

        self.mu_bl1 = None
        self.mu_bl2 = None
        self.cov_bl1 = None
        self.cov_bl2 = None
        self.cost = None
        self.prices = None

        self.x1 = None

    def __repr__(self):
        return "<Portfolio for auth {}>".format(self.username)

    def get_past_portfolios(self):
        try:
            query = '"' + '","'.join(SYMBOLS) + '"'
            p1 = pd.read_sql(
                """select {} from "{}" where "username" like '{}';""".format(
                    query, "p1_returns", self.username),
                Database.DATABASE.engine)

            p1 = p1.iloc[-1]  # Get the most recent entry

            p2 = pd.read_sql(
                """select {} from "{}" where "username" like '{}';""".format(
                    query, "p2_returns", self.username),
                Database.DATABASE.engine)
            p2 = p2.iloc[-1]
        except:
            p1, p2 = None, None
        return [p1, p2]

    def get_params(self):
        '''Lecacy code'''
        try:
            return pd.read_sql(
                """select "email","date", "_id" from "{}" where "username" like '{}';""".format(
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

    def fetch_parameters(self):
        self.mu_bl1 = self.fetch_parameter('mu_bl1')
        self.mu_bl2 = self.fetch_parameter('mu_bl2')
        self.cov_bl1 = self.fetch_parameter('cov_bl1')
        self.cov_bl2 = self.fetch_parameter('cov_bl2')
        self.cost = self.fetch_parameter('cost')
        self.prices = self.fetch_parameter('prices')

    def fetch_parameter(self, param):
        df = pd.read_sql(
            """select * from "{}";""".format(param),
            Database.DATABASE.engine)

        return df.set_index(df.columns[0], drop=True)

    def run_optimization(self, risk_tolerance, start_date=START_DATE, end_date=END_DATE, samples=100):
        risk_tolerance = [((1, 10), (0, 0.10)),
                          ((5, 5), (0, 0.20)),
                          ((10, 1), (-0.05, 0.30))]

        self.fetch_parameters()

        soln = optimize(mu=(self.mu_bl1.values.ravel(), self.mu_bl2.values.ravel()),
                        sigma=(self.cov_bl1.values, self.cov_bl2.values),
                        alpha=(0.05, 0.10),
                        return_target=(0.05, 0.05),
                        costs=self.cost,
                        prices=self.prices.iloc[-2, :].values if self.prices.iloc[-1,
                                                                 :].isnull().values.any() else self.prices.iloc[-1,
                                                                                               :].values,
                        gamma=risk_tolerance[2])

        self.x1 = pd.DataFrame(soln.x[:int(len(self.mu_bl1))], index=self.mu_bl1.index, columns=['weight'])
        self.x2 = pd.DataFrame(soln.x[int(len(self.mu_bl2)):], index=self.mu_bl2.index, columns=['weight'])

        return [self.x1, self.x2]

    def get_portfolio_return(self, x1=None, mu_bl2=None):
        if x1 is None:
            x1 = self.x1
        if mu_bl2 is None:
            mu_bl2 = self.mu_bl2
        return ret(mu_bl2, x1) * 100

    def get_portfolio_volatility(self, x1=None, cov_bl2=None):
        if x1 is None:
            x1 = self.x1
        if cov_bl2 is None:
            cov_bl2 = self.cov_bl2
        return vol(cov_bl2, x1) * 100

    def get_portfolio_var(self, x1=None, mu_bl2=None, cov_bl2=None):
        if x1 is None:
            x1 = self.x1
        if mu_bl2 is None:
            mu_bl2 = self.mu_bl2
        if cov_bl2 is None:
            cov_bl2 = self.cov_bl2
        return var(mu_bl2, cov_bl2, 0.05, x1)

    def get_portfolio_cvar(self, x1=None, mu_bl2=None, cov_bl2=None):
        if x1 is None:
            x1 = self.x1
        if mu_bl2 is None:
            mu_bl2 = self.mu_bl2
        if cov_bl2 is None:
            cov_bl2 = self.cov_bl2
        return cvar(mu_bl2, cov_bl2, 0.05, x1)

    def plot_comparison(self, risk_data, ret_data, gamma_vals, risk_data_minVar, ret_data_minVar, std, mu):
        pass

    def update_portfolios(self):
        df_1 = self.x1.transpose(copy=True)
        df_1['username'] = self.username
        df_1 = df_1.set_index('username', drop=True)
        df_1.to_sql("p1_returns", con=Database.DATABASE.engine, if_exists="append", index=True)

        df_1 = self.x2.transpose(copy=True)
        df_1['username'] = self.username
        df_1 = df_1.set_index('username', drop=True)
        df_1.to_sql("p2_returns", con=Database.DATABASE.engine, if_exists="append", index=True)
