from flask import Flask, render_template
import connexion
import os

from server.common import database as d
from server.models.stock.stock import Stocks

basedir = os.path.abspath(os.path.dirname(__file__))
connex_app = connexion.FlaskApp(__name__, specification_dir=basedir)
app = connex_app.app

db = d.Database()
db.initialize(app)

# from server.common.schemas import FactorModel, EodPrices, UserPortfolio, User
from server.models.auth.schema import User
# from server.models.stock.schema import EodPrices
# from server.models.factors.schema import FactorModel
# from server.models.portfolio.schema import UserPortfolio
db.DATABASE.create_all()


from server.models.portfolio.populate_tables import get_params_for_optimization

params = get_params_for_optimization()

for name, df in params.items():
    df.to_sql(name, con=db.DATABASE.engine, if_exists="replace", index=True)
