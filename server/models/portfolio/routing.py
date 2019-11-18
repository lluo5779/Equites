from flask import Blueprint, request, session, redirect, url_for, render_template

from server.models.auth.schema import User
# import server.models.users.errors as UserErrors
# import server.models.users.decorators as user_decorators
from server.common.database import Database
from server.models.portfolio.portfolio import Portfolio
from server.models.stock.stock import Stocks

from io import BytesIO
import urllib
import base64

s = Stocks()


# @user_decorators.requires_login
def get_portfolio_page(portfolio_id):  # Renders unique portfolio page
    return render_template('/portfolios/portfolio.jinja2')


# @user_decorators.requires_login
def change_risk(username):  # Views form to change portfolio's associated risk aversion parameter
    port = Portfolio.get_by_id(username)
    if request.method == "POST":
        risk_appetite = request.form['risk_appetite']
        port.risk_appetite = risk_appetite
        port.update_portfolio()
        img = BytesIO()
        img.seek(0)
        plot_data = base64.b64encode(img.read()).decode()
        return render_template('/portfolios/optimal_portfolio.jinja2', portfolio=port, plot_url=plot_data)

    return render_template('/portfolios/edit_portfolio.jinja2', portfolio=port)


# @user_decorators.requires_login
def create_portfolio():  # Views form to create portfolio associated with active/ loggedin auth
    if request.method == "POST":
        risk_appetite = request.form['risk_appetite']
        port = Portfolio(session['email'], risk_appetite=risk_appetite)
        port.update_portfolio()
        fig = port.runMVO()
        img = BytesIO()
        fig.savefig(img)
        img.seek(0)
        plot_data = base64.b64encode(img.read()).decode()
        return render_template('/portfolios/optimal_portfolio.jinja2', portfolio=port, plot_url=plot_data)

    return render_template('/portfolios/new_portfolio.jinja2')


def optiondecision():
    return render_template('OptionDecision.jinja2', title='optiondecision')


def option1():
    return render_template('Option1.jinja2', tickers=s.tickers)


def option2():
    return render_template('Option2.jinja2', tickers=s.tickers)


def option3parent():
    return render_template('Option3Parent.jinja2', title='optiondecision')


def option3childa():
    return render_template('Option3ChildA.jinja2', title='optiondecision')


def option3childb():
    return render_template('Option3ChildB.jinja2', title='optiondecision')


def option3childc():
    return render_template('Option3ChildC.jinja2')


'''
def portfoliio():
    weightings = [0.6,0.4,0,0,0,0,0,0,0,0,0,0,0]
    #initial user input
    histPortValue = [1000,990,1050,1100]
    histVol = 0.12
    expectedReturn = 0.1
    expectedVol = 0.1
    risk = 'High'
    return render_template('portfolio.jinja2', title='Sign In', weightings=weightings, risk=risk,histPortValue=histPortValue,histVOL=histVol, expectedReturn=expectedReturn,expectedVol=expectedVol)
'''


def portfolioview():
    weightings = [0.6, 0.4]
    # initial user input
    expectedReturn = 0.1
    expectedVol = 0.1
    risk = 'High'
    return render_template('portfolio.jinja2', title='Sign In', weightings=weightings, risk=risk,
                           expectedReturn=expectedReturn, expectedVol=expectedVol)
