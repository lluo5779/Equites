from flask import Blueprint, request, session, redirect, url_for, render_template
from flask_login import login_required, current_user
from server.models.auth.schema import User
# import server.models.users.errors as UserErrors
# import server.models.users.decorators as user_decorators
from server.common.database import Database
from server.models.portfolio.portfolio import Portfolio
from server.models.portfolio.bt import back_test
from server.models.stock.stock import Stocks
from server.models.portfolio.config import COLLECTION, START_DATE, END_DATE, SYMBOLS
from server.models.portfolio.bt import back_test
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np

import flask
from plotly.graph_objs import Scatter, Pie, Layout
from datetime import datetime
from io import BytesIO
from flask import Blueprint
import urllib
import base64
import plotly.offline

trackSpecialCase = Blueprint("", __name__)
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


# @login_required
def optiondecision():
    return render_template('OptionDecision.jinja2', title='optiondecision')


# @login_required
def track():
    if len(request.query_string) == 0:
        weightings = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        return render_template('Option1.jinja2', tickers=s.tickers, weightings=weightings)
    else:
        # do this after you extract the starting and ending dates ...
        args = list(request.args.values())

        tickers = args[::2]
        values = [float(x) for x in args[1::2]]
        weights = [x / sum(values) for x in values]
        portfolio = dict(zip(tickers, weights))
        #start_date = (datetime.now() - relativedelta(years=6)).strftime("%Y-%m-%d")
        start_date = args[-1]

        values, success, msg = back_test(portfolio, start_date, dollars=sum(values))
        port_values = values.sum(axis=1)

        minValue = round(min(port_values), 2)
        maxValue = round(max(port_values), 2)
        vol = round((np.std(port_values.pct_change()) * 252 ** 0.5)*100, 1)
        stats = [maxValue, minValue, vol]

        plot_data = plotly.graph_objs.Scatter(x=list(port_values.index), y=port_values, mode='lines')

        plot = plotly.offline.plot({"data": plot_data},
                                   output_type='div',
                                   include_plotlyjs=False,
                                   show_link=False,
                                   config={"displayModeBar": False})

        return render_template('Option1Results.jinja2', tickers=tickers, weightings=values, plot=plot, stats=stats)

@trackSpecialCase.route('/track2', methods=["GET", "POST"])
def track2():
    if len(request.query_string) == 0:
        weightings = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        return render_template('Option2.jinja2', tickers=s.tickers, weightings=weightings, stats=stats)
    else:
        #save option type 2 to database
        tickers = ["AAPL", "SPY", "TLT"]
        weightings = [.1,.1,.1]
        fig = plotly.graph_objs.Figure(data=[plotly.graph_objs.Pie(labels=tickers, values=weightings, hole=.3)])

        plot = plotly.offline.plot({"data": fig},
                                   output_type='div',
                                   include_plotlyjs=False,
                                   show_link=False,
                                   config={"displayModeBar": False})

        return render_template('Option2.jinja2', tickers=tickers, weightings=weightings, plot=plot)

# @login_required
def option2():
    weightings = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    timeHorizon = 50
    return render_template('Option2.jinja2', tickers=s.tickers, weightings=weightings, timeHorizon=timeHorizon)


# @login_required
def option3parent():
    return render_template('Option3Parent.jinja2', title='optiondecision')


# @login_required
def option3childa():
    return render_template('Option3ChildA.jinja2', title='optiondecision')


# @login_required
def option3childb():
    return render_template('Option3ChildB.jinja2', title='optiondecision')


# @login_required
def option3childc():
    print("request.query_string: ", len(request.query_string))
    if len(request.query_string) == 0:
        return render_template('Option3ChildC.jinja2')
    else:
        p = Portfolio(current_user.username)  # Initializes portfolio object for user.
        budget = float(request.args.get('investmentGoal'))
        cardinality = [1] * 7 + [0] * (len(SYMBOLS) - 7)
        if request.args.get('riskAppetite') == "High":
            risk_tolerance = [((1, 10), (0, 0.10), cardinality, 'SHARPE'),
                              ((5, 5), (0, 0.20), cardinality, 'SHARPE'),
                              ((10, 1), (-0.05, 0.50), cardinality, 'SHARPE')]
        else:
            risk_tolerance = [((1, 10), (0, 0.10), cardinality, 'SHARPE'),
                              ((5, 5), (0, 0.20), cardinality, 'SHARPE'),
                              ((10, 1), (-0.05, 0.50), cardinality, 'SHARPE')]
        weights = p.run_optimization(risk_tolerance)
        p.update_portfolios(budget=budget)

        return render_template('portfolio.jinja2', title='Sign In', weightings=weights, risk=p.get_portfolio_cvar(),
                               expectedReturn=p.get_portfolio_return(), expectedVol=p.get_portfolio_volatility())


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


#@login_required
def portfolioview():
    # initial user input
    # try:
    username = current_user.username
    print('username: ', username)
    p = Portfolio(username)

    if (len(request.query_string) != 0):
        weightings = []

        for sym in SYMBOLS:
            weightings.append(request.args.get(sym).strip('%'))

        print(weightings)
        expectedReturn = 0.1
        expectedVol = 0.1
        risk = 'High'
    else:
        weightings = [p.x1, p.x2]
        budget = p.budget
        print(weightings)
        expectedReturn = p.get_portfolio_return()
        expectedVol = p.get_portfolio_volatility()
        risk = p.get_portfolio_cvar()

    return render_template('portfolio.jinja2', title='Sign In', weightings=weightings, risk=risk,
                           expectedReturn=expectedReturn, expectedVol=expectedVol)
    # except:
    #     return render_template('OptionDecision.jinja2')


def portfoliosnapshot():
    username = current_user.username
    print('username: ', username)
    p = Portfolio(username)

    all_past_p = p.get_past_portfolios(get_all=True)
    print(">>> all_past_p: ", all_past_p)
    print(p)

    # list of lists, portfolio values for past year or since inception for each portfolio
    portfolioInitialValue = [val for val in all_past_p[2]]

    start_date = (datetime.now() - relativedelta(months=6)).strftime("%Y-%m-%d")
    histValues = [back_test(portfolio.to_dict(), start_date)[0].sum(axis=1) * portfolioInitialValue[index] for
                  index, portfolio in
                  all_past_p[0].iterrows()]  # [[100, 110, 120, 115, 118], [50, 60]]
    # initial portfolio value (wont be in list above if port is > 1yr old)
    returnSinceInception = []
    for i in range(len(histValues)):
        temp = round(((histValues[i][-1] / portfolioInitialValue[i]) - 1) * 100, 2)
        returnSinceInception.append(temp)
    return render_template('portfoliosnapshot.jinja2', title='optiondecision',
                           returnSinceInception=returnSinceInception, histValues=histValues)


def portfoliodashboard():
    # list of portfolio values for past year or since inception of specific portfolio
    # histValues = [100, 110, 120, 115, 118]
    username = current_user.username
    print('username: ', username)
    p = Portfolio(username)

    all_past_p = p.get_past_portfolios(get_all=True)
    print(">>> all_past_p: ", all_past_p)

    # list of lists, portfolio values for past year or since inception for each portfolio
    portfolioInitialValue = [val for val in all_past_p[2]]

    start_date = (datetime.now() - relativedelta(months=6)).strftime("%Y-%m-%d")
    histValues = [back_test(portfolio.to_dict(), start_date)[0].sum(axis=1) * portfolioInitialValue[index] for
                  index, portfolio in
                  all_past_p[0].iterrows()]  # [[100, 110, 120, 115, 118], [50, 60]]

    all_past_p = p.get_past_portfolios(get_all=True)
    print(">>> all_past_p: ", all_past_p)
    print(p)

    print(">>> current_user: ", current_user.is_authenticated)

    # initial portfolio value (wont be in list above if port is > 1yr old)
    returnSinceInception = []
    for i in range(len(histValues)):
        temp = round(((histValues[i][-1] / portfolioInitialValue[i]) - 1) * 100, 2)
        returnSinceInception.append(temp)
    # portfolio composition
    weightings = [.1, -.1, .1, .1]
    short = []
    long = []
    for i in range(len(weightings)):
        if weightings[i] < 0:
            short.append(weightings[i])
        if weightings[i] > 0:
            long.append(weightings[i])

    expectedReturn = .1
    expectedVol = .12
    risk = 'high'

    # regime? bull/bear

    return render_template('portfoliodashboard.jinja2', title='optiondecision',
                           returnSinceInception=returnSinceInception, histValues=histValues, weightings=weightings,
                           short=short, long=long, expectedReturn=expectedReturn, expectedVol=expectedVol, risk=risk)


#@login_required
def editportfolio():
    #pull most recent questionaire data if portfolioName==""
    #if portfolio is option 1
    weightings = [0]
    return render_template('Option1.jinja2', title='Sign In', weightings=weightings)

    #if portfolio is option 2
    #return render_template('Option2.jinja2', title='Sign In', weightings=weightings, timeHorizon=timeHorizon)

def saveportfolio():
    return render_template("home.jinja2")


'''Option 3'''
#@login_required
def option3Parent():
    return render_template('Option3Parent.jinja2', title='optiondecision')

def option3Purchase():
    timeHorizon = 2019
    investmentGoal = 0
    riskAppetite = "Medium"
    return render_template('Option3Purchase.jinja2', title='optiondecision', timeHorizon=timeHorizon, investmentGoal=investmentGoal, riskAppetite=riskAppetite)

def option3PurchaseA():
    return render_template('Option3PurchaseA.jinja2')

def option3PurchaseB():
    return render_template('Option3PurchaseB.jinja2')

def option3PurchaseC():
    return render_template('Option3PurchaseC.jinja2')

def option3Retirement():
    timeHorizon = 2019
    investmentGoal = 0
    riskAppetite = "Medium"
    return render_template('Option3Retirement.jinja2', title='optiondecision', timeHorizon=timeHorizon, investmentGoal=investmentGoal, riskAppetite=riskAppetite)

def option3RetirementA():
    return render_template('Option3RetirementA.jinja2', title='optiondecision')

def option3RetirementB():
    return render_template('Option3RetirementB.jinja2', title='optiondecision')

def option3RetirementC():
    return render_template('Option3RetirementC.jinja2', title='optiondecision')

def option3Wealth():
    initialInvestment = 0
    riskAppetite = "Medium"
    return render_template('Option3Wealth.jinja2', title='optiondecision', initialInvestment=initialInvestment, riskAppetite=riskAppetite)

def option3WealthA():
    return render_template('Option3WealthA.jinja2', title='optiondecision')

def option3WealthB():
    return render_template('Option3WealthB.jinja2', title='optiondecision')

def build():
    return render_template('Build.jinja2')


