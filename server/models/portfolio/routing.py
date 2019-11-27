import uuid

from flask import Blueprint, request, session, redirect, url_for, render_template
from flask_login import login_required, current_user
from server.models.auth.schema import User
# import server.models.users.errors as UserErrors
# import server.models.users.decorators as user_decorators
from server.common.database import Database
from server.models.portfolio.rs import business_days
from server.models.portfolio.risk import risk_prefs
from server.models.portfolio.portfolio import Portfolio, getUuidFromPortfolioName, get_past_portfolios, \
    getOptionTypeFromName
from server.models.portfolio.bt import back_test
from server.models.stock.stock import Stocks
from server.models.portfolio.config import COLLECTION, START_DATE, END_DATE, SYMBOLS
from server.models.portfolio.bt import back_test
from server.models.user_preferences.user_preferences import fetch_latest_questionnaire_from_type, \
    fetch_questionnaire_from_uuid_and_type, update_new_questionnaire, initialize_new_questionnaire
import urllib
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
            port_values.rename(columns={'Unnamed: 0': 'value'}, inplace=True)
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

            return render_template('Option1Results.jinja2', display=True, tickers=tickers, weightings=values, plot=plot,
                                   pie=pie, stats=stats)

        else:
            # TODO: ERROR CATCHING
            pass


@trackSpecialCase.route('/track2', methods=["GET", "POST"])
def track2():
    """
        Display option 2 portfolio with 2 states
        Input:
            Header:
                numEntries <optional>
                ticker_0, weight_0
                ticker_1, weight_1
                ...
        Output:
            Template
            Params:
               tickers=tickers, weightings=weightings, plot=plot

        Accessed from:
            main page
            option2 upon submission
    """

    if len(request.query_string) == 0:
        weightings = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        return render_template('Option2.jinja2', tickers=s.tickers, weightings=weightings, stats=stats)
    else:

        # save option type 2 to database
        num_entries = request.headers.get('numEntries')
        if num_entries == None:
            querys = request.query_string.split('ticker_')
            num_entries = 0
            for query in querys:
                try:
                    num = int(query[0])
                    num_entries = max(num, num_entries)
                except:
                    continue

        tickers = [request.headers.get('ticker_' + str(i)) for i in range(num_entries)]  # ["AAPL", "SPY", "TLT"]
        weightings = [request.headers.get('weight_' + str(i)) for i in range(num_entries)]

        fig = plotly.graph_objs.Figure(data=[plotly.graph_objs.Pie(labels=tickers, values=weightings, hole=.3)])

        plot = plotly.offline.plot({"data": fig},
                                   output_type='div',
                                   include_plotlyjs=False,
                                   show_link=False,
                                   config={"displayModeBar": False})

        return render_template('Option2.jinja2', tickers=tickers, weightings=weightings, plot=plot)


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
        horizon, aversion, l = 10, 1, 5

        p = Portfolio(current_user.username)
        alpha, multipliers, exposures, cardinality = risk_prefs(horizon, aversion, return_target, l, p.mu_bl1, p.mu_bl2,
                                                                p.cov_bl1)

        # assign the risk tolerances
        risk_tolerance = (multipliers, exposures, cardinality, 'SHARPE')

        weights = p.run_optimization(alpha, return_target, risk_tolerance)[0]
        weights = weights.loc[weights['weight'] != 0]

        fig = plotly.graph_objs.Figure(
            data=[plotly.graph_objs.Pie(labels=weights.index, values=weights['weight'], hole=.1)])
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


#
# # @login_required
# def option3childc():
#     print("request.query_string: ", len(request.query_string))
#     if len(request.query_string) == 0:
#         return render_template('Option3ChildC.jinja2')
#     else:
#         p = Portfolio(current_user.username)  # Initializes portfolio object for user.
#         budget = float(request.args.get('investmentGoal'))
#         cardinality = [1] * 7 + [0] * (len(SYMBOLS) - 7)
#         if request.args.get('riskAppetite') == "High":
#             risk_tolerance = [((1, 10), (0, 0.10), cardinality, 'SHARPE'),
#                               ((5, 5), (0, 0.20), cardinality, 'SHARPE'),
#                               ((10, 1), (-0.05, 0.50), cardinality, 'SHARPE')]
#         else:
#             risk_tolerance = [((1, 10), (0, 0.10), cardinality, 'SHARPE'),
#                               ((5, 5), (0, 0.20), cardinality, 'SHARPE'),
#                               ((10, 1), (-0.05, 0.50), cardinality, 'SHARPE')]
#         weights = p.run_optimization(risk_tolerance)
#         p.make_new_portfolios(budget=budget, portfolio_type='option3childc')
#
#         return render_template('portfolio.jinja2', title='Sign In', weightings=weights, risk=p.get_portfolio_cvar(),
#                                expectedReturn=p.get_portfolio_return(), expectedVol=p.get_portfolio_volatility())
#

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

op_to_q_map = {
    'retirement': ['initialInvestment', 'retirementAmount', 'retirementDate', 'riskAppetite'],
    'purchase': ['initialInvestment', 'purchaseAmount', 'purchaseDate', 'riskAppetite'],
    'wealth': ['initialInvestment', 'riskAppetite']
}


def getCardinalityFromQuestionnaire(questionnaire):
    # TO-DO: NEED TO CHANGE TO LIVE INFO
    questionnaire['cardinality'] = [1] * 7 + [0] * (len(SYMBOLS) - 7)
    return questionnaire['cardinality']


def getRiskToleranceFromQuestionnaire(questionnaire):
    cardinality = getCardinalityFromQuestionnaire(questionnaire)

    if questionnaire['riskAppetite'] == 'High':
        return [((1, 10), (0, 0.10), cardinality, 'SHARPE'),
                ((5, 5), (0, 0.20), cardinality, 'SHARPE'),
                ((10, 1), (-0.05, 0.50), cardinality, 'SHARPE')]
    else:
        return [((1, 10), (0, 0.10), cardinality, 'SHARPE'),
                ((5, 5), (0, 0.20), cardinality, 'SHARPE'),
                ((10, 1), (-0.05, 0.50), cardinality, 'SHARPE')]


# @login_required
def portfolioview():
    """
        Display tentative portfolio
        Input:
            portfolioName <for editing known portfolio; None if finishing new questionnaire>
            option_type
        Output:
            Template
            Params:
                title='Sign In', weightings=weightings, risk=risk,
               expectedRet=expectedReturn, expectedVol=expectedVol, histValues=histValues, long=None,
               short=None, portfolioName=portfolio_name

        Accessed from:
            options questionnaires upon save
            # edit button from portfoliodashboard
    """

    # Updating questionnaire data
    portfolio_name = request.headers.get('portfolioName')
    if 'purchaseAmount' in request.query_string.decode("utf-8"):
        option_type = 'purchase'
    elif 'retirementAmount' in request.query_string.decode("utf-8"):
        option_type = 'retirement'
    elif 'initialInvestment' in request.query_string.decode("utf-8"):
        option_type = 'wealth'
    else:
        print(request.query_string.decode("utf-8"))
        raise ValueError('Bad query parameters. No such option type.')

    questionnaire = {}
    is_new_portfolio = False

    for question in op_to_q_map[option_type]:
        if 'Date' in question:
            raw_dates = request.args.get(question).split('/')
            questionnaire[question] = datetime(int(raw_dates[1]), int(raw_dates[0]), 1)
        else:
            questionnaire[question] = request.args.get(question)

    print("questionnaire: ", questionnaire)

    _id = getUuidFromPortfolioName(portfolio_name)
    # need to check if request no uuid, will create uuid
    if _id is None:
        _id = uuid.uuid4()
        is_new_portfolio = True
        # initialize_new_questionnaire(questionnaire, option_type, uuid=_id)
    # else:
    #     update_new_questionnaire(questionnaire, option_type, uuid=_id)

    # Updating the portfolio data
    p = Portfolio(current_user.username, _id=_id, generate_new=is_new_portfolio)

    if is_new_portfolio:
        p.run_optimization(risk_tolerance=getRiskToleranceFromQuestionnaire(questionnaire=questionnaire))

    weightings = [p.x1, p.x2]
    expectedReturn = p.get_portfolio_return()
    expectedVol = p.get_portfolio_volatility()
    risk = p.get_portfolio_cvar()
    start_date = (datetime.now() - relativedelta(months=6)).strftime("%Y-%m-%d")

    histValues = back_test(p.x1.to_dict()[list(p.x1.to_dict().keys())[0]], start_date)[0].sum(axis=1) \
                 * float(questionnaire['initialInvestment'])
    # if is_new_portfolio:
    #     p.make_new_portfolios(questionnaire['investmentGoal'], option_type, 'r5')
    # else:
    #     print(p.x1.to_dict())
    #     p.update_existing_portfolio(_id, p.x1.to_dict()[list(p.x1.to_dict().keys())[0]])
    print('FINISHED')

    return render_template('portfolioview.jinja2', title='Sign In', weightings=weightings, risk=risk,
                           expectedRet=expectedReturn, expectedVol=expectedVol, histValues=histValues, long=None,
                           short=None, portfolioName=portfolio_name, questionnaire=questionnaire)
    # except:
    #     return render_template('OptionDecision.jinja2')


def portfoliosnapshot():
    """
        Displays all user portfolio
        Input:
            None
        Output:
            Template
            Params:
                title='optiondecision',
                returnSinceInception=returnSinceInception,
                histValues=histValues,
                portfolioNames=portfolioNames

        Accessed from:
            menu
            portfolioview upon save
    """
    username = current_user.username

    all_past_p = get_past_portfolios(username=username, get_all=True)
    print(">>> all_past_p: ", all_past_p)

    portfolioNames = all_past_p[2]['portfolio_name']
    print('>>>> portfolioNames: ', portfolioNames)

    portfolioInitialValue = all_past_p[2]['budget'].tolist()
    print('>>>> portfolioInitialValue: ', portfolioInitialValue)

    start_date = (datetime.now() - relativedelta(months=6)).strftime("%Y-%m-%d")
    histValues = [back_test(portfolio.to_dict(), start_date)[0].sum(axis=1) * portfolioInitialValue[index] for
                  index, portfolio in
                  all_past_p[0].iterrows()]  # [[100, 110, 120, 115, 118], [50, 60]]
    print('>>>> histValues: ', histValues)

    # initial portfolio value (wont be in list above if port is > 1yr old)
    returnSinceInception = []
    for i in range(len(histValues)):
        temp = round(((histValues[i][-1] / portfolioInitialValue[i]) - 1) * 100, 2)
        returnSinceInception.append(temp)
    print('>>>> returnSinceInception: ', returnSinceInception)

    return render_template('portfoliosnapshot.jinja2', title='optiondecision',
                           returnSinceInception=returnSinceInception, histValues=histValues,
                           portfolioNames=portfolioNames)


def portfoliodashboard():
    """
    Displays a dashboard of the portfolio based on portfolio name

    Input:
        Header: portfolioName
    Output:
        Template
        Params:
            title='optiondecision',
            returnSinceInception=returnSinceInception
            histValues=histValues
            weightings=weightings
            short=short
            long=long
            expectedReturn=expectedReturn
            expectedVol=expectedVol
            risk=risk

    Accessed from:
        portfoliosnapshot
    """

    portfolio_name = request.headers.get('portfolioName')
    username = 'test1'#current_user.username
    print('username: ', username)

    _id = getUuidFromPortfolioName(portfolio_name)
    p = Portfolio(username=username, _id=_id, generate_new=False)

    start_date = (datetime.now() - relativedelta(months=6)).strftime("%Y-%m-%d")
    print('p.x1.to_dict()[list(p.x1.to_dict().keys())[0]]: ', p.x1.to_dict()[list(p.x1.to_dict().keys())[0]])
    histValues = back_test(p.x1.to_dict()[list(p.x1.to_dict().keys())[0]], start_date)[0].sum(axis=1)
    print('port hist: ', histValues)

    returnSinceInception = histValues.apply(lambda x: round((x - 1) * 100, 2))

    portfolioInitialValue = p.budget
    histValues = histValues.apply(lambda x: x * portfolioInitialValue)
    print('port hist: ', histValues)

    # initial portfolio value (wont be in list above if port is > 1yr old)
    # for i in range(len(histValues)):
    #     temp = round(((histValues[i][-1] / portfolioInitialValue) - 1) * 100, 2)
    #     returnSinceInception.append(temp)
    # portfolio composition

    weightings = p.x1.to_numpy().flatten()
    tickers = p.x1.columns

    print(weightings)
    short = []
    long = []
    for i in range(len(weightings)):
        if weightings[i] < 0:
            short.append(weightings[i])
        if weightings[i] > 0:
            long.append(weightings[i])

    expectedReturn = p.get_portfolio_return()
    expectedVol = p.get_portfolio_volatility()

    option_type = getOptionTypeFromName(portfolio_name)
    questionnaire = fetch_questionnaire_from_uuid_and_type(uuid=_id, option_type=option_type)

    risk = questionnaire['riskAppetite']

    # regime? bull/bear

    return render_template('portfoliodashboard.jinja2', title='optiondecision',
                           returnSinceInception=returnSinceInception, histValues=histValues, weightings=weightings,
                           short=short, long=long, expectedReturn=expectedReturn, expectedVol=expectedVol, risk=risk, tickers=tickers)


# @login_required
def editportfolio():
    # pull most recent questionaire data if portfolioName==""
    # if portfolio is option 1

    portfolio_name = request.headers.get('portfolioName')

    option_type = getOptionTypeFromName(portfolio_name)
    questionnaire = fetch_latest_questionnaire_from_type(option_type=option_type)

    if portfolio_name is None:
        if 'purchaseAmount' in request.query_string.decode("utf-8"):
            option_type = 'purchase'
        elif 'retirementAmount' in request.query_string.decode("utf-8"):
            option_type = 'retirement'
        elif 'initialInvestment' in request.query_string.decode("utf-8"):
            option_type = 'wealth'
        else:
            raise ValueError('Bad query parameters. No such option type.')

        for question in op_to_q_map[option_type]:
            questionnaire[question] = request.args.get(question)

        print("questionnaire: ", questionnaire)

    return render_template('Build.jinja2', title='Sign In', questionnaire=questionnaire)

    # if portfolio is option 2
    # return render_template('Option2.jinja2', title='Sign In', weightings=weightings, timeHorizon=timeHorizon)


def saveportfolio():
    # Updating questionnaire data
    portfolio_name = request.headers.get('portfolioName')
    option_type = request.headers.get("optionType")
    questionnaire = {}
    is_new_portfolio = False

    if option_type not in op_to_q_map:
        print(option_type)
        raise ValueError("Bad option type. Something went terribly wrong.")

    for question in op_to_q_map[option_type]:
        questionnaire[question] = request.headers.get(question)

    print("questionnaire: ", questionnaire)

    _id = getUuidFromPortfolioName(portfolio_name)
    # need to check if request no uuid, will create uuid
    if _id is None:
        _id = uuid.uuid4()
        is_new_portfolio = True
        initialize_new_questionnaire(questionnaire, option_type, uuid=_id)
    else:
        update_new_questionnaire(questionnaire, option_type, uuid=_id)

    # Updating the portfolio data
    p = Portfolio(current_user.username, _id=_id, generate_new=is_new_portfolio)

    p.run_optimization(risk_tolerance=getRiskToleranceFromQuestionnaire(questionnaire=questionnaire))

    if is_new_portfolio:
        p.make_new_portfolios(questionnaire['investmentGoal'], option_type, portfolio_name)
    else:
        print(p.x1.to_dict())
        p.update_existing_portfolio(_id, p.x1.to_dict()[list(p.x1.to_dict().keys())[0]])
    print('FINISHED')
    return redirect(url_for('/.server_models_portfolio_routing_portfoliosnapshot'))


'''Option 3'''


# @login_required
def option3Parent():
    return render_template('Option3Parent.jinja2', title='optiondecision')


def option3Purchase():
    _id = request.args.get('uuid')
    if _id == None:
        timeHorizon = 2019
        investmentGoal = 0
        riskAppetite = "Medium"
    else:
        questionnaire = fetch_questionnaire_from_uuid_and_type(uuid=_id, option_type='purchase')
        timeHorizon = questionnaire['timeHorizon']
        investmentGoal = questionnaire['timeHorizon']
        riskAppetite = questionnaire['timeHorizon']

    # TODO: WHAT DOES THIS PAGE NEED?

    return render_template('Purchase.jinja2', title='optiondecision')


def option3PurchaseA():
    return render_template('Option3PurchaseA.jinja2')


def option3PurchaseB():
    return render_template('Option3PurchaseB.jinja2')


def option3PurchaseC():
    return render_template('Option3PurchaseC.jinja2')


def option3Retirement():
    _id = request.args.get('uuid')
    if _id == None:
        timeHorizon = 2019
        investmentGoal = 0
        riskAppetite = "Medium"
    else:
        questionnaire = fetch_questionnaire_from_uuid_and_type(uuid=_id, option_type='retirement')
        timeHorizon = questionnaire['timeHorizon']
        investmentGoal = questionnaire['timeHorizon']
        riskAppetite = questionnaire['timeHorizon']

    return render_template('Retirement.jinja2', title='optiondecision', timeHorizon=timeHorizon,
                           investmentGoal=investmentGoal, riskAppetite=riskAppetite)


def option3RetirementA():
    return render_template('Option3RetirementA.jinja2', title='optiondecision')


def option3RetirementB():
    return render_template('Option3RetirementB.jinja2', title='optiondecision')


def option3RetirementC():
    return render_template('Option3RetirementC.jinja2', title='optiondecision')


def option3Wealth():
    _id = request.args.get('uuid')
    if _id == None:
        timeHorizon = 2019
        investmentGoal = 0
        riskAppetite = "Medium"
    else:
        questionnaire = fetch_questionnaire_from_uuid_and_type(uuid=_id, option_type='wealth')
        investmentGoal = questionnaire['timeHorizon']
        riskAppetite = questionnaire['timeHorizon']

    return render_template('Wealth.jinja2', title='optiondecision', initialInvestment=initialInvestment,
                           riskAppetite=riskAppetite)


def option3WealthA():
    return render_template('Option3WealthA.jinja2', title='optiondecision')


def option3WealthB():
    return render_template('Option3WealthB.jinja2', title='optiondecision')


def build():
    portfolio_name = request.headers.get('portfolioName')
    _id = getUuidFromPortfolioName(portfolio_name)

    if portfolio_name == None:
        questionnaire = None
    else:
        option_type = getOptionTypeFromName(portfolio_name)
        questionnaire = fetch_questionnaire_from_uuid_and_type(uuid=_id, option_type=option_type)

    return render_template('Build.jinja2', questionnaire=questionnaire)
