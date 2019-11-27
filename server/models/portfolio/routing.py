from flask import Blueprint, request, session, redirect, url_for, render_template
from flask_login import login_required, current_user
from server.models.auth.schema import User
# import server.models.users.errors as UserErrors
# import server.models.users.decorators as user_decorators
from server.common.database import Database
from server.models.portfolio.portfolio import Portfolio
from server.models.stock.stock import Stocks
from server.models.portfolio.config import COLLECTION, START_DATE, END_DATE, SYMBOLS
from server.models.portfolio.bt import back_test
from server.models.portfolio.rs import business_days
from server.models.portfolio.risk import risk_prefs
from datetime import datetime
from scipy.stats.mstats import gmean
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



@login_required
def track():
    if len(request.query_string) == 0:
        return render_template('Option1.jinja2', display=False)
    else:
        args = list(request.args.values())

        start_date = args[0]
        end_date = args[1]

        portfolio_data = args[2:]

        tickers = portfolio_data[::2]
        values = [abs(float(x)) for x in portfolio_data[1::2]]
        weights = [x / sum(values) for x in values]
        portfolio = dict(zip(tickers, weights))

        values, success, msg = back_test(portfolio, start_date, end_date, dollars=sum(values))

        if success:
            port_values = values.sum(axis=1)
            port_values.rename( columns={'Unnamed: 0':'value'}, inplace=True )
            port_returns = (port_values / port_values.shift(1) - 1).dropna()
            
            total_returns = round((port_values[-1] / port_values[0] - 1) * 100)
            
            min_value = round(min(port_values), 2)
            max_value = round(max(port_values), 2)

            stats = [total_returns, min_value, max_value]

            plot_data = plotly.graph_objs.Scatter(x=list(port_values.index), y=port_values, mode='lines')

            plot = plotly.offline.plot({"data": plot_data},
                                       output_type='div',
                                       include_plotlyjs=False,
                                       show_link=False,
                                       config={"displayModeBar": False})

            # show the pie graph of the portfolio
            pie = plotly.offline.plot({"data": [Pie(labels=tickers, values=weights, hole=.1)]},
                                   output_type='div',
                                   include_plotlyjs=False,
                                   show_link=False,
                                   config={"displayModeBar": False})

            return render_template('Option1Results.jinja2', display=True, tickers=tickers, weightings=values, plot=plot, pie=pie, stats=stats)

        else: 
            # TODO: ERROR CATCHING
            pass

@login_required
def enhance():
    if len(request.query_string) == 0:
        return render_template('Option2.jinja2', display=False)
    else:
        args = list(request.args.values())

        tickers = args[::2]
        values = [abs(float(x)) for x in args[1::2]]
        weights = [x / sum(values) for x in values]
        portfolio = dict(zip(tickers, weights))

        # always assign to past 6 months (ie rebalance the period)
        start_date = (datetime.now() - relativedelta(months=6)).strftime("%Y-%m-%d")

        # get the number of days in the backtest period ... to determine target returns and variances later
        days = business_days(start_date, datetime.now().strftime("%Y-%m-%d"))

        # call backtest to get the value of the portfolio
        portfolio_value = back_test(portfolio, start_date, end_date=None, dollars=None)[0].sum(axis=1)

        # calculate portfolio returns
        portfolio_returns = (portfolio_value / portfolio_value.shift(1) - 1).dropna()

        # assign the target return and variance
        return_target = float(gmean(portfolio_returns + 1, axis=0) - 1) * days

        # set the other parameters for a generalized maximization
        horizon, aversion, l= 10, 1, 5

        p = Portfolio(current_user.username)
        alpha, multipliers, exposures, cardinality = risk_prefs(horizon, aversion, return_target, l, p.mu_bl1, p.mu_bl2, p.cov_bl1)

        # assign the risk tolerances
        risk_tolerance = (multipliers, exposures, cardinality, 'SHARPE')

        weights = p.run_optimization(alpha, return_target, risk_tolerance)[0]
        weights = weights.loc[weights['weight'] != 0]

        fig = plotly.graph_objs.Figure(data=[plotly.graph_objs.Pie(labels=weights.index, values=weights['weight'], hole=.1)])
        pie = plotly.offline.plot({"data": fig},
                                   output_type='div',
                                   include_plotlyjs=False,
                                   show_link=False,
                                   config={"displayModeBar": False})

        return render_template('Option2.jinja2', pie=pie, display=True)

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


