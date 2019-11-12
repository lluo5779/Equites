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

from server.common.schemas import FactorModel, EodPrices, UserPortfolio, User

db.DATABASE.create_all()

# from server.models.portfolio.portfolio import Portfolio

# p = Portfolio('test1')

s = Stocks()
# TO-DO: Remove update as update should be triggered by third party software
s.update_database()
