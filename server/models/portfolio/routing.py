from flask import Blueprint, request, session, redirect, url_for, render_template
from flask_login import login_required, current_user
from server.models.auth.schema import User
# import server.models.users.errors as UserErrors
# import server.models.users.decorators as user_decorators
from server.common.database import Database
from server.models.portfolio.portfolio import Portfolio
from server.models.stock.stock import Stocks
from server.models.portfolio.config import COLLECTION, START_DATE, END_DATE, SYMBOLS

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


@login_required
def optiondecision():
    return render_template('OptionDecision.jinja2', title='optiondecision')


@login_required
def option1():
    return render_template('Option1.jinja2', tickers=s.tickers)


@login_required
def option2():
    return render_template('Option2.jinja2', tickers=s.tickers)


@login_required
def option3parent():
    return render_template('Option3Parent.jinja2', title='optiondecision')


@login_required
def option3childa():
    return render_template('Option3ChildA.jinja2', title='optiondecision')


@login_required
def option3childb():
    return render_template('Option3ChildB.jinja2', title='optiondecision')


@login_required
def option3childc():
    print("request.query_string: ", len(request.query_string))
    if len(request.query_string) == 0:
        return render_template('Option3ChildC.jinja2')
    else:
        p = Portfolio('test1')
        if request.args.get('riskAppetite') == "High":
            weights = p.run_optimization([((1, 10), (0, 0.50)),
                                          ((5, 5), (0, 0.50)),
                                          ((10, 1), (-0.05, 0.50))])
        else:
            weights = p.run_optimization([((1, 10), (0, 0.10)),
                                          ((5, 5), (0, 0.20)),
                                          ((10, 1), (-0.05, 0.30))])
        p.update_portfolios()

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


@login_required
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
        print(weightings)
        expectedReturn = p.get_portfolio_return()
        expectedVol = p.get_portfolio_volatility()
        risk = p.get_portfolio_cvar()

    return render_template('portfolio.jinja2', title='Sign In', weightings=weightings, risk=risk,
                           expectedReturn=expectedReturn, expectedVol=expectedVol)

    # except:
    #     return render_template('OptionDecision.jinja2')

def portfoliosnapshot():
    #list of lists, portfolio values for past year or since inception for each portfolio
    histValues = [[100,110,120,115,118],[50,60]]
    #initial portfolio value (wont be in list above if port is > 1yr old)
    portfolioInitialValue = [100,50]
    returnSinceInception = []
    for i in range(len(histValues)):
        temp = round(((histValues[i][-1] / portfolioInitialValue[i])-1)*100, 2)
        returnSinceInception.append(temp)
    return render_template('portfoliosnapshot.jinja2', title='optiondecision', returnSinceInception=returnSinceInception, histValues=histValues)


def portfoliodashboard():
    #list of portfolio values for past year or since inception of specific portfolio
    histValues = [100,110,120,115,118]

    print(">>> current_user: ", current_user.is_authenticated)

    #initial portfolio value (wont be in list above if port is > 1yr old)
    portfolioInitialValue = 100
    returnSinceInception = round((histValues[-1] / portfolioInitialValue-1)*100, 2)

    #portfolio composition
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

    #regime? bull/bear

    return render_template('portfoliodashboard.jinja2', title='optiondecision', returnSinceInception=returnSinceInception, histValues=histValues,weightings=weightings, short=short, long=long, expectedReturn=expectedReturn, expectedVol=expectedVol, risk=risk)