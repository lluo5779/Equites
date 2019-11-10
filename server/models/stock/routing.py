from flask import Blueprint, render_template, request, redirect, url_for, json

from server.common.database import Database
from server.models.stock.stock import Stocks

# import server.models.users.decorators as user_decorators
s = Stocks()

def index():  # Views list of available/stored stocks
    stocks = s.get_all()
    return render_template('stock/stock_index.jinja2', stocks=stocks)


def stock_page(stock_ticker):  # Renders unique stock page
    print('This is stock page: ', stock_ticker)
    stock = s.get_by_id(stock_ticker)
    print("stock obj: ", stock)
    return render_template('stock/stock.jinja2', tables=[stock.to_html(classes='data', header="true")])
