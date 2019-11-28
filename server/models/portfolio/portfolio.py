import uuid
from datetime import datetime

from server.common.database import Database
from server.models.stock.stock import Stocks
from server.models.portfolio.config import COLLECTION, START_DATE, END_DATE, SYMBOLS
import pandas as pd
from server.models.portfolio.optimize import optimize
from server.models.portfolio.stats import *
from flask_login import current_user


class Portfolio(object):
    # Portfolio class creates portfolio instances for auth portfolios using stocks in Stock class

    def __init__(self, username, _id=None, generate_new=False):
        self.username = username
        # portfolio = self.get_params()
        # self.user_email = info['user_email'] if user_email is None else user_email
        # self.risk_appetite = info['risk_appetite'] if risk_appetite is None else risk_appetite
        # self.tickers = info['tickers'] if tickers is None else tickers
        # self.weights = info['weights'] if weights is None else weights
        # self._id = uuid.uuid4().hex if _id is None else _id

        self._id = _id
        self.mu_bl1 = None
        self.mu_bl2 = None
        self.cov_bl1 = None
        self.cov_bl2 = None
        self.cost = None
        self.prices = None

        p = self.get_portfolio(_id=_id) if not generate_new else [None, None]
        self.x1 = p[0]
        self.x2 = p[1]

        self.fetch_parameters()

    def __repr__(self):
        return "<Portfolio for auth {}>".format(self.username)

    def get_portfolio(self, _id):
        query = """select * from {} where "uuid" like '{}';""".format(COLLECTION, _id)
        df = pd.read_sql(query, con=Database.DATABASE.engine)

        p1 = df[SYMBOLS]
        p2 = df[[c + "2" for c in SYMBOLS]]
        p2.columns = SYMBOLS

        self.budget = df['budget']

        if p2.isnull().all().all():
            p2 = p1

        return [p1.T, p2.T]

    def fetch_parameters(self):
        self.mu_bl1 = self.fetch_parameter('mu_bl1')#.T
        self.mu_bl2 = self.fetch_parameter('mu_bl2')#.T
        self.cov_bl1 = self.fetch_parameter('cov_bl1')#.T
        self.cov_bl2 = self.fetch_parameter('cov_bl2')#.T
        self.cost = self.fetch_parameter('cost')
        self.prices = self.fetch_parameter('prices')

    def fetch_parameter(self, param):
        df = pd.read_sql(
            """select * from "{}";""".format(param),
            Database.DATABASE.engine)

        return df.set_index(df.columns[0], drop=True)


    def run_optimization(self, risk_tolerance, alpha=(0.05, 0.10), return_target=0.05):
        print("self.cost: ", self.cost)

        safe_soln, target_soln = optimize(mu=(self.mu_bl1.values.ravel(), self.mu_bl2.values.ravel()),
                                          sigma=(self.cov_bl1.values, self.cov_bl2.values),
                                          alpha=alpha,
                                          return_target=(return_target, return_target),
                                          costs=self.cost.T,
                                          prices=self.prices.iloc[-2, :].values if self.prices.iloc[-1,:].isnull().values.any() else self.prices.iloc[-1,:].values,
                                          gamma=risk_tolerance)
        soln = safe_soln if target_soln is None else target_soln

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

    def make_new_portfolios(self, budget, portfolio_type, portfolio_name):

        x1 = self.x1.transpose(copy=True)
        x1['username'] = self.username
        x1 = x1.set_index('username', drop=True)
        # df_1.to_sql(COLLECTION, con=Database.DATABASE.engine, if_exists="append", index=True)

        x2 = self.x2.transpose(copy=True)
        x2['username'] = self.username
        x2 = x2.set_index('username', drop=True)

        x1 = x1.merge(x2, on="username", suffixes=("", "2"), how="inner")
        x1['timestamp'] = datetime.utcnow()
        x1['budget'] = budget
        x1['portfolio_type'] = portfolio_type
        x1['portfolio_name'] = portfolio_name
        x1['uuid'] = self._id
        x1['active'] = 'Y'

        # x1 = x1.set_index('uuid', drop=True)
        print('WHY NO WORK: ', x1.columns)
        print('Saving the following to database {}: '.format(COLLECTION), x1)
        x1.to_sql(COLLECTION, con=Database.DATABASE.engine, if_exists="append", index=True)

    def update_existing_portfolio(self, uuid, new_values={}):
        portfolio_df = pd.read_sql('select * from {}'.format(COLLECTION), con=Database.DATABASE.engine, index_col='uuid')
        print('before: ', portfolio_df)

        portfolio_df.loc[uuid, list(new_values.keys())] = list(new_values.values())
        print('after: ', portfolio_df)
        portfolio_df.to_sql(COLLECTION, con=Database.DATABASE.engine, if_exists="replace", index=True)

def get_past_portfolios(username, get_all=False):
    try:
        query = """select * from "{}" where "username" like '{}' and "active" like '{}' order by "timestamp" asc;""".format(
            COLLECTION, username, "Y")
        df = pd.read_sql(query,
                         Database.DATABASE.engine, index_col='uuid')

        print(">>> query df: ", df)
        if not get_all:
            df = df.iloc[0]
        p1 = df[SYMBOLS]
        p2 = df[[c + "2" for c in SYMBOLS]]
        p2.columns = SYMBOLS

        if p2.isnull().all().all():
            p2 = p1

        print("period 1: ", p1)
        print("period 2: ", p2)
        return [p1, p2, df]
    except:
        print("Error in fetching past portfolio from database {}".format(COLLECTION))
        p1, p2 = None, None
        return [None, None, None]

def getOptionTypeFromName(portfolioName):
    df= pd.read_sql(
        """select "portfolio_type" from {} where "portfolio_name" like '{}';""".format(COLLECTION, portfolioName), con=Database.DATABASE.engine)
    if len(df) == 0:
        print(df)
        return None

    return df.to_numpy()[0][0]



    # def get_portfolio_uuids(self):
    #     try:
    #         tickers = '"' + '","'.join(SYMBOLS) + '"'
    #         query = """select "uuid" from "{}" where "username" like '{}' and "active" like '{}';""".format(COLLECTION,
    #                                                                                                         self.username,
    #                                                                                                         'Y')
    #
    #         return pd.read_sql(query,
    #                            Database.DATABASE.engine)
    #
    #     except:
    #         print("FAILED to read portfolio uuid {}. ".format(uuid))
    #         return None
    #
    # def get_past_portfolios(self, get_all=False):
    #     try:
    #         query = """select * from "{}" where "username" like '{}' and "active" like '{}' order by "timestamp" asc;""".format(
    #             COLLECTION, self.username, "Y")
    #         df = pd.read_sql(query,
    #                          Database.DATABASE.engine)
    #
    #         print(">>> query df: ", df)
    #         if not get_all:
    #             df = df.iloc[0]
    #         p1 = df[SYMBOLS]
    #         p2 = df[[c + "2" for c in SYMBOLS]]
    #         p2.columns = SYMBOLS
    #         budget = df['budget']
    #
    #         if p2.isnull().all().all():
    #             p2 = p1
    #
    #         print("period 1: ", p1)
    #         print("period 2: ", p2)
    #
    #     except:
    #         print("Error in fetching past portfolio from database {}".format(COLLECTION))
    #         p1, p2, budget = None, None, None
    #     return [p1, p2, budget]
    #
    # def get_valid_portfolio_uuids_for_user(self):
    #     query = """select "timestamp" from "{}" where "username" like '{}' and "active" like '{}';""".format(
    #         COLLECTION, self.username, "Y")
    #
    #     return pd.read_sql(query,
    #                        Database.DATABASE.engine)
    #
    # def get_specific_portfolio(self, created_timestamp):
    #     query = """select * from "{}" where "username" like '{}' and "active" like '{}' and "timestamp" like '{}';""".format(
    #         COLLECTION, self.username, "Y", created_timestamp)
    #     df = pd.read_sql(query,
    #                      Database.DATABASE.engine)
    #
    #     p1 = df[SYMBOLS]
    #     p2 = df[[c + "2" for c in SYMBOLS]]
    #     p2.columns = SYMBOLS
    #     budget = df['budget']
    #
    #     if p2.isnull().all().all():
    #         p2 = p1
    #
    #     return [p1, p2, budget]
    #
    # def get_params(self):
    #     '''Lecacy code'''
    #     try:
    #         return pd.read_sql(
    #             """select "email","date", "_id" from "{}" where "username" like '{}';""".format(
    #                 COLLECTION, self.username),
    #             Database.DATABASE.engine)
    #     except:
    #         print('User is not in database')
    #         return {
    #             'username': self.username,
    #             'user_email': None,
    #             'risk_appetite': None,
    #             'tickers': None,
    #             'weights': None,
    #             '_id': None
    #         }


def getUuidFromPortfolioName(portfolio_name):
    query = """select uuid from {} where "portfolio_name" like '{}';""".format(COLLECTION, portfolio_name)
    id = pd.read_sql(query, con=Database.DATABASE.engine)
    print('id: ', id)
    if len(id) != 0:
        print(id.values[0][0])
        return id.values[0][0]
    else:
        return None
    pass
