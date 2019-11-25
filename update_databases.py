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

from server.models.auth.schema import User
from server.models.portfolio.schema import UserPortfolio
db.DATABASE.create_all()


from server.models.portfolio.populate_tables import get_params_for_optimization

# Key parameters used in the optimization procedure. Particular values selected to faciliate swiftness of response.
params = get_params_for_optimization()

for name, df in params.items():
    df.to_sql(name, con=db.DATABASE.engine, if_exists="replace", index=True)

