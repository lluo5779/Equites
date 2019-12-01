import uuid

from flask import Blueprint, request, session, redirect, url_for, render_template
from flask_login import login_required, current_user
from server.models.auth.schema import User
# import server.models.users.errors as UserErrors
# import server.models.users.decorators as user_decorators
from server.common.database import Database
from server.models.portfolio.rs import business_days
from server.models.portfolio.risk import risk_prefs
from server.models.portfolio.portfolio import Portfolio, getUuidFromPortfolioName, get_past_portfolios, getOptionTypeFromName
from server.models.stock.stock import Stocks
from server.models.portfolio.config import COLLECTION, START_DATE, END_DATE, SYMBOLS
from server.models.portfolio.bt import back_test
from server.models.user_preferences.user_preferences import fetch_latest_questionnaire_from_type, fetch_questionnaire_from_uuid_and_type, update_new_questionnaire, initialize_new_questionnaire
import urllib
from datetime import datetime
from scipy.stats.mstats import gmean
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np

from server.models.portfolio.stats import *
import flask
from plotly.graph_objs import Scatter, Pie, Layout
import plotly.graph_objects as go
from datetime import datetime
from io import BytesIO
from flask import Blueprint
import urllib
import base64
import plotly.offline

from server.models.user_preferences.user_preferences import fetch_latest_questionnaire_from_type, fetch_questionnaire_from_uuid_and_type, update_new_questionnaire, initialize_new_questionnaire, fetch_all_questionnaires
from server.models.portfolio.tiingo import get_data
from server.models.portfolio.bt import back_test
from server.models.stock.stock import Stocks, fetchEodPrices

trackSpecialCase = Blueprint("", __name__)
s = Stocks()


# @login_required
def track():
    if len(request.query_string) == 0:
        return render_template('Option1.jinja2',
                               display=False,
                               error=False)
    else:
        error = False
        success = True

        try:
            args = list(request.args.values())

            start_date = args[0]
            end_date = args[1]

            # rolling days assignment
            bt_days = business_days(start_date, end_date)
            rolling = 100 if bt_days > 1000 else max(int(bt_days/10), 1)

            portfolio_data = args[2:]

            tickers = portfolio_data[::2]
            values = [abs(float(x)) for x in portfolio_data[1::2]]
            weights = [(x / sum(values)) for x in values]
            portfolio = dict(zip(tickers, weights))

            values, success, msg = back_test(portfolio, start_date, end_date=None, dollars=sum(values), tore=True)
        except:
            succcess, error = False, True

        if success:
            port_values = values.sum(axis=1)
            port_values.rename(columns={'Unnamed: 0': 'value'}, inplace=True)

            # PORTFOLIO HOLDINGS
            pie = plotly.offline.plot({"data": [Pie(labels=tickers, values=weights, hole=.1)]},
                                      output_type='div',
                                      include_plotlyjs=False,
                                      show_link=False,
                                      config={"displayModeBar": False})

            # CUMULATIVE RETURNS
            plot_data = plotly.graph_objs.Scatter(x=list(port_values.index), y=port_values, mode='lines', line = dict(color = '#3B4F66'))
            plot = plotly.offline.plot({"data": plot_data},
                                       output_type='div',
                                       include_plotlyjs=False,
                                       show_link=False,
                                       config={"displayModeBar": False})

            # calculate returns from the portfolio
            port_returns = (port_values / port_values.shift(1) - 1).dropna()

            # ROLLING VOLATILITY
            vols = rolling_volatility(port_returns, rolling).dropna()
            vols_plot_data = plotly.graph_objs.Scatter(x=list(port_values.index), y=vols, mode='lines', line = dict(color = '#3B4F66'))
            vols_plot = plotly.offline.plot({"data": vols_plot_data},
                                       output_type='div',
                                       include_plotlyjs=False,
                                       show_link=False,
                                       config={"displayModeBar": False})

            # ROLLING SHARPE
            sharpe = rolling_sharpe(port_returns, rolling).dropna()
            sharpe_plot_data = plotly.graph_objs.Scatter(x=list(port_values.index), y=sharpe, mode='lines', line = dict(color = '#3B4F66'))
            sharpe_plot = plotly.offline.plot({"data": sharpe_plot_data},
                                       output_type='div',
                                       include_plotlyjs=False,
                                       show_link=False,
                                       config={"displayModeBar": False})

            # detailed statistics
            underwater = drawdown_underwater(port_returns)

            underwater_data = plotly.graph_objs.Scatter(x=list(port_values.index), y=underwater, mode='lines', line = dict(color = '#3B4F66'))
            underwater_plot = plotly.offline.plot({"data": underwater_data},
                                              output_type='div',
                                              include_plotlyjs=False,
                                              show_link=False,
                                              config={"displayModeBar": False})

            # DRAWDOWN
            drawdown = drawdown_table(port_returns)
            drawdown_fig = go.Figure(data=[go.Table(header=dict(values=list(drawdown.columns),
                                                                align='left'),
                                                    cells=dict(values=[drawdown["Net drawdown in %"],
                                                                       drawdown["Peak date"],
                                                                       drawdown["Valley date"],
                                                                       drawdown["Recovery date"],
                                                                       drawdown["Duration"]], align='center'))])
            drawdown = plotly.offline.plot({"data": drawdown_fig},
                                           output_type='div',
                                           include_plotlyjs=False,
                                           show_link=False,
                                           config={"displayModeBar": False})


            total_returns = round((port_values[-1] / port_values[0] - 1) * 100)
            min_value = round(min(port_values), 2)
            max_value = round(max(port_values), 2)
            stats = [total_returns, min_value, max_value]


            return render_template('Option1.jinja2',
                                   display=True,
                                   error=False,
                                   tickers=tickers,
                                   weightings=values,
                                   pie=pie,
                                   plot=plot,
                                   vols_plot=vols_plot,
                                   sharpe_plot=sharpe_plot,
                                   underwater=underwater_plot,
                                   drawdown=drawdown,
                                   stats=stats,
                                   rolling=rolling)

        else:
            return render_template('Option1.jinja2', display=False, error=True)


@login_required
def enhance():
    if len(request.query_string) == 0:
        return render_template('Option2.jinja2',
                               display=False,
                               error=False)
    else:
        success = True

        try:
            args = list(request.args.values())

            cardinal = int(args[0])

            portfolio_data = args[1:]

            tickers = portfolio_data[::2]
            values = [abs(float(x)) for x in portfolio_data[1::2]]

            budget = sum(values)
            weights = [x / budget for x in values]
            portfolio = dict(zip(tickers, weights))

            # always assign to past 6 months (ie rebalance the period)
            start_date = (datetime.now() - relativedelta(months=6)).strftime("%Y-%m-%d")

            # get the number of days in the backtest period ... to determine target returns and variances later
            days = business_days(start_date, datetime.now().strftime("%Y-%m-%d"))

            # call backtest to get the value of the portfolio
            values, success, msg = back_test(portfolio, start_date, end_date=None, dollars=sum(values), tore=True)
        except:
            success, error = False, True

        if success:
            portfolio_value = values.sum(axis=1)

            # calculate portfolio returns
            portfolio_returns = (portfolio_value / portfolio_value.shift(1) - 1).dropna()

            # assign the target return and variance
            return_target = float(gmean(portfolio_returns + 1, axis=0) - 1) * days

            # set the other parameters for a generalized maximization
            horizon, aversion, l = 10, 1, 5

            # make the portfolio
            p = Portfolio(current_user.username, generate_new=True)
            alpha, multipliers, exposures, cardinality = risk_prefs(horizon, aversion, cardinal, return_target, l,
                                                                    p.mu_bl1, p.mu_bl2, p.cov_bl1)

            # assign the risk tolerances, specifying a SHARPE optimization
            risk_tolerance = (multipliers, exposures, cardinality, 'SHARPE')

            # get the weights
            weights = p.run_optimization(risk_tolerance=risk_tolerance,
                                         alpha=alpha,
                                         return_target=return_target,
                                         budget=budget)[0]

            # hacky solution lol
            enhanced_values = back_test(weights.to_dict()['weight'], start_date, end_date=None, dollars=budget, tore=False)[0].sum(axis=1)[-(len(portfolio_value)+1):]
            back_returns = (enhanced_values / enhanced_values.shift(1) - 1).dropna()
            enhanced_values = cum_returns(back_returns, budget)

            expected_returns = float(p.mu_bl1.T.dot(weights).iloc[0])

            ## COMPARE PORTFOLIO RETURNS OVER THE PAST MONTHS
            returns_data = []

            benchmark = plotly.graph_objs.Scatter(x=list(portfolio_value.index),
                                                  y=portfolio_value,
                                                  mode='lines',
                                                  name='benchmark',
                                                  line=dict(color='#A7E66E'))

            returns_data.append(benchmark)

            enhanced = plotly.graph_objs.Scatter(x=list(enhanced_values.index),
                                                 y=enhanced_values,
                                                 mode='lines',
                                                 name='enhanced',
                                                 line=dict(color='#3B4F66'))

            returns_data.append(enhanced)

            plot = plotly.offline.plot({"data": returns_data},
                                       output_type='div',
                                       include_plotlyjs=False,
                                       show_link=False,
                                       config={"displayModeBar": False})

            # COMPARE PORTFOLIO SHARPE RATIO
            sharpe_data = []

            portfolio_returns = (portfolio_value / portfolio_value.shift(1) - 1).dropna()
            enhanced_returns = (enhanced_values / enhanced_values.shift(1) - 1).dropna()

            benchmark_sharpe = rolling_sharpe(portfolio_returns, 10).dropna()
            benchmark_sharpe_plot_data = plotly.graph_objs.Scatter(x=list(benchmark_sharpe.index),
                                                                   y=benchmark_sharpe,
                                                                   mode='lines',
                                                                   name='benchmark',
                                                                   line=dict(color='#A7E66E'))

            sharpe_data.append(benchmark_sharpe_plot_data)

            enhanced_sharpe = rolling_sharpe(enhanced_returns, 10).dropna()
            enhanced_sharpe_plot_data = plotly.graph_objs.Scatter(x=list(enhanced_sharpe.index),
                                                                  y=enhanced_sharpe,
                                                                  mode='lines',
                                                                  name='enhanced',
                                                                  line=dict(color='#3B4F66'))

            sharpe_data.append(enhanced_sharpe_plot_data)

            sharpe_plot = plotly.offline.plot({"data": sharpe_data},
                                              output_type='div',
                                              include_plotlyjs=False,
                                              show_link=False,
                                              config={"displayModeBar": False})

            # round the weights to a nice number for display
            weights = weights.round(2).loc[weights['weight'] != 0]

            # make the pie graph of recommended weights
            fig = plotly.graph_objs.Figure(
                data=[plotly.graph_objs.Pie(labels=weights.index, values=weights['weight'], hole=.1)])
            pie = plotly.offline.plot({"data": fig},
                                      output_type='div',
                                      include_plotlyjs=False,
                                      show_link=False,
                                      config={"displayModeBar": False})

            return render_template('Option2.jinja2',
                                   display=True,
                                   error=(not success),
                                   cardinal=cardinal,
                                   pie=pie,
                                   plot=plot,
                                   sharpe_plot=sharpe_plot)
        else:
            return render_template('Option2.jinja2', display=False, error=(not success))


# @login_required
def option2():
    weightings = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    timeHorizon = 50
    return render_template('Option2.jinja2', tickers=s.tickers, weightings=weightings, timeHorizon=timeHorizon)


op_to_q_map = {
    'Retirement': ['initialInvestment', 'retirementAmount', 'retirementDate', 'riskAppetite'],
    'Purchase': ['initialInvestment', 'purchaseAmount', 'purchaseDate', 'riskAppetite'],
    'Wealth': ['initialInvestment', 'riskAppetite']
}


def populateQuestionnaire(questionnaire, option_type):
    info = ['retirementAmount', 'retirementDate', 'purchaseAmount', 'purchaseDate']

    if type(questionnaire) == pd.DataFrame or type(questionnaire) == pd.Series:
        questionnaire = questionnaire.T.to_dict()[questionnaire.index.values[0]]

    print(questionnaire)
    for key in info:
        if key not in questionnaire.keys():
            questionnaire[key] = ""
        # elif 'Date' in key:
        #
        #     raw_dates = questionnaire[key]
        #     print(type(raw_dates))
        #     if type(raw_dates.to_pydatetime()) == datetime:
        #         raw_dates = raw_dates.to_pydatetime().strftime("%m/%Y")
        #     if '-' in raw_dates:
        #         separator = '-'
        #         raw_dates = raw_dates.split(separator)
        #         year = int(raw_dates[0])
        #         month = int(raw_dates[1])
        #     else:
        #         separator = '/'
        #         raw_dates = raw_dates.split(separator)
        #         month = int(raw_dates[0])
        #         year = int(raw_dates[1])
        #     questionnaire[key] = str(month) + '/' + str(year)

    questionnaire["optionType"] = option_type

    return questionnaire


def getCardinalityFromQuestionnaire(questionnaire):
    # TO-DO: NEED TO CHANGE TO LIVE INFO
    questionnaire['cardinality'] = [1] * 7 + [0] * (len(SYMBOLS) - 7)
    return questionnaire['cardinality']


def getRiskToleranceFromQuestionnaire(questionnaire):
    cardinality = getCardinalityFromQuestionnaire(questionnaire)

    if questionnaire['riskAppetite'] == 'High Risk':
        return ((1, 10), (0, 0.10), cardinality, 'SHARPE')
    else:
        return ((1, 10), (0, 0.10), cardinality, 'SHARPE')


# @login_required
def portfolioview():

    # Updating questionnaire data
    portfolio_name = request.args.get('portfolioName')
    if 'purchaseAmount' in request.query_string.decode("utf-8"):
        option_type = 'Purchase'
    elif 'retirementAmount' in request.query_string.decode("utf-8"):
        option_type = 'Retirement'
    elif 'initialInvestment' in request.query_string.decode("utf-8"):
        option_type = 'Wealth'
    else:
        print(request.query_string.decode("utf-8"))
        raise ValueError('Bad query parameters. No such option type.')

    questionnaire = {}
    is_new_portfolio = False

    for question in op_to_q_map[option_type]:
        if 'Date' in question:
            raw_dates = str(request.args.get(question))
            print('raw_dates', raw_dates)
            if '-' in raw_dates:
                separator = '-'
                raw_dates = raw_dates.split(separator)
                year = int(raw_dates[0])
                month = int(raw_dates[1])
            else:
                separator = '/'
                raw_dates = raw_dates.split(separator)
                month = int(raw_dates[0])
                year = int(raw_dates[1])
            questionnaire[question] = datetime(year, month, 1)
        elif 'riskAppetite' in question:
            if float(request.args.get(question)) <= 5:
                questionnaire[question] = "Low Risk"
            elif float(request.args.get(question)) <= 15:
                questionnaire[question] = "Med Risk"
            else:
                questionnaire[question] = "High Risk"
        else:
            questionnaire[question] = request.args.get(question)

    print("questionnaire \n{}\n\n".format(questionnaire))

    # populate rest of questionnaire with ""
    questionnaire = populateQuestionnaire(questionnaire, option_type)

    _id = getUuidFromPortfolioName(portfolio_name)
    # need to check if request no uuid, will create uuid
    if _id is None:
        _id = uuid.uuid4()
        is_new_portfolio = True
        # initialize_new_questionnaire(questionnaire, option_type, uuid=_id)
    # else:
    #     update_new_questionnaire(questionnaire, option_type, uuid=_id)

    # Updating the portfolio data
    # TODO: current_user.username
    p = Portfolio('test1', _id=_id, generate_new=is_new_portfolio)

    if is_new_portfolio:
        p.run_optimization(risk_tolerance=getRiskToleranceFromQuestionnaire(questionnaire=questionnaire))

    weightings = [p.x1, p.x2]
    expectedReturn = p.get_portfolio_return()
    expectedVol = p.get_portfolio_volatility()
    risk = p.get_portfolio_cvar()
    start_date = (datetime.now() - relativedelta(months=6)).strftime("%Y-%m-%d")

    print(p.x1.to_dict())
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

    username = current_user.username
    df_to_display = fetch_all_questionnaires(username)
    latest_prices = fetchEodPrices(get_latest=True)[SYMBOLS]
    all_past_p = get_past_portfolios(username=username, get_all=True)
    initial_weights = all_past_p[0][SYMBOLS]

    investment_target = df_to_display['target']

    holding_names = [x + "_holdings" for x in SYMBOLS]
    latest_holdings = all_past_p[2][holding_names]
    df_to_display['percentCompleted'] = np.nan
    df_to_display['targetAmount'] = np.nan
    df_to_display['start_date'] = np.nan
    for _id, portfolio in latest_holdings.iterrows():
        # iterating over each portfolio
        if investment_target.loc[_id] == "":
            # if wealth portfolio
            continue
        portfolio.index = SYMBOLS
        start_date = all_past_p[2].loc[_id, 'timestamp'].to_pydatetime()
        portfolio_value = latest_prices.mul(portfolio).sum(axis=1)
        current_return = portfolio_value/investment_target.loc[_id]
        df_to_display['start_date'] = start_date.strftime("%Y-%m")

        df_to_display['targetAmount']= investment_target.loc[_id]
        df_to_display.loc[_id, 'percentCompleted'] = current_return.values[0]

    return render_template('portfoliosnapshot.jinja2', title='optiondecision', budget=df_to_display['budget'],
                           portfolioNames=df_to_display['portfolioName'], targetAmount=df_to_display['targetAmount'], percentCompleted=df_to_display['percentCompleted'],
                           startDates=df_to_display['start_date'], endDates=df_to_display['end_date'])

        # start_date = pd.to_datetime(all_past_p[2]['timestamp'], unit='s', utc=True)
        # df_to_display['start_date'] = start_date

    # all_past_p = get_past_portfolios(username=username, get_all=True)
    # print(">>> all_past_p: ", all_past_p)
    #
    # portfolioNames = all_past_p[2]['portfolio_name']
    # print('>>>> portfolioNames: ', portfolioNames)
    #
    # portfolioInitialValue = all_past_p[2]['budget']
    # print('>>>> portfolioInitialValue: ', portfolioInitialValue)
    #
    # start_date = (datetime.now() - relativedelta(months=6)).strftime("%Y-%m-%d")
    # print(all_past_p[0])
    #
    # histValues = []
    # counter = 0
    # for index, portfolio in all_past_p[0].iterrows():
    #     portfolio_returns = back_test(portfolio.to_dict(), start_date)[0].sum(axis=1)
    #     print(portfolio_returns)
    #     print(portfolioInitialValue[index])
    #     histValues.append(portfolio_returns.apply(lambda x: x * portfolioInitialValue[index]).tolist())
    #     counter += 1
    #
    # print('>>>> histValues: ', histValues)
    #
    # # initial portfolio value (wont be in list above if port is > 1yr old)
    # returnSinceInception = []
    # percentCompleted = []
    # for i in range(len(histValues)):
    #     temp = round(((histValues[i][-1] / portfolioInitialValue[i]) - 1) * 100, 2)
    #     returnSinceInception.append(temp)
    #     percentCompleted.append(1)
    # print('>>>> returnSinceInception: ', returnSinceInception)
    #
    # targetAmount = 200
    #
    # timeTilCompletion = 200#targetDate - today
    #
    # return render_template('portfoliosnapshot.jinja2', title='optiondecision',
    #                        returnSinceInception=returnSinceInception, histValues=histValues,
    #                        portfolioNames=portfolioNames, targetAmount=targetAmount, percentCompleted=percentCompleted,
    #                        timeTilCompletion=timeTilCompletion)


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

    portfolio_name = request.args.get('portfolioName')
    username = 'test1'  # current_user.username
    print('username: ', username)

    _id = getUuidFromPortfolioName(portfolio_name)
    if _id is None:
        return redirect(url_for('/.server_models_portfolio_routing_portfoliosnapshot'))
    p = Portfolio(username=username, _id=_id, generate_new=False)

    start_date = (datetime.now() - relativedelta(months=6)).strftime("%Y-%m-%d")
    print('p.x1.to_dict(): ', p.x1.to_dict())
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
    # populate rest of questionnaire with ""
    questionnaire = populateQuestionnaire(questionnaire, option_type)
    print(">>> questionnaire: ", questionnaire)

    # regime? bull/bear
    if 'purchase' in option_type.lower():
        targetAmount = questionnaire['purchaseAmount']
        percentCompleted = histValues.iloc[-1].values[0] / float(targetAmount)
        timeTilCompletion = questionnaire['purchaseDate'] - datetime.utcnow()
    elif 'retirement' in option_type.lower():
        targetAmount = questionnaire['retirementAmount']
        percentCompleted = histValues.iloc[-1].values[0] / float(targetAmount)
        timeTilCompletion = questionnaire['retirementDate'] - datetime.utcnow()
    else:
        targetAmount = None
        percentCompleted = None
        timeTilCompletion = None

    # timeTilCompletion = targetDate - today

    return render_template('portfoliodashboard.jinja2', title='optiondecision',
                           returnSinceInception=returnSinceInception, histValues=histValues, weightings=weightings,
                           short=short, long=long, expectedReturn=expectedReturn, expectedVol=expectedVol, risk=risk,
                           tickers=tickers, questionnaire=questionnaire, targetAmount=targetAmount,
                           percentCompleted=percentCompleted, timeTilCompletion=timeTilCompletion)


# @login_required
def editportfolio():
    # pull most recent questionnaire data if portfolioName==""
    # if portfolio is option 1

    portfolio_name = request.headers.get('portfolioName')

    option_type = getOptionTypeFromName(portfolio_name)
    questionnaire = fetch_latest_questionnaire_from_type(option_type=option_type)

    if portfolio_name is None:
        if 'purchaseAmount' in request.query_string.decode("utf-8"):
            option_type = 'Purchase'
        elif 'retirementAmount' in request.query_string.decode("utf-8"):
            option_type = 'Retirement'
        elif 'initialInvestment' in request.query_string.decode("utf-8"):
            option_type = 'Wealth'
        else:
            raise ValueError('Bad query parameters. No such option type.')

        for question in op_to_q_map[option_type]:
            questionnaire[question] = request.args.get(question)

        print("questionnaire: ", questionnaire)

    # populate rest of questionnaire with ""
    questionnaire = populateQuestionnaire(questionnaire, option_type)

    #     'Retirement': ['initialInvestment', 'retirementAmount', 'retirementDate', 'riskAppetite'],
    #     'Purchase': ['initialInvestment', 'purchaseAmount', 'purchaseDate', 'riskAppetite'],
    #     'Wealth': ['initialInvestment', 'riskAppetite']
    #
    # }
    date_key = ''
    if questionnaire['retirementDate'] != '':
        date_key = 'retirementDate'
    elif questionnaire['purchaseDate'] != '':
        date_key = 'purchaseDate'

    if date_key != '' and len(questionnaire[date_key]) >= 8:  # "MM/YYYY"
        raw_date = questionnaire[date_key].split('-')
        month = '0' + raw_date[1] if len(raw_date[1]) == 1 else raw_date[1]
        questionnaire[date_key] = month + '/' + raw_date[0]

    return render_template('Build.jinja2', title='Sign In', questionnaire=questionnaire)


def saveportfolio():
    username = current_user.username

    # Updating questionnaire data
    portfolio_name = request.args.get('portfolioName')
    option_type = request.args.get("optionType")
    questionnaire = {}
    is_new_portfolio = False

    if option_type not in op_to_q_map:
        print(option_type)
        raise ValueError("Bad option type. Something went terribly wrong.")

    for question in op_to_q_map[option_type]:
        if 'Date' in question:
            print(request.args.get(question))
            raw_dates = request.args.get(question).split('-')
            questionnaire[question] = datetime(int(raw_dates[0]), int(raw_dates[1]), 1)
        else:
            questionnaire[question] = request.args.get(question)

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
    p = Portfolio(username, _id=_id, generate_new=is_new_portfolio)

    risk_prefs(horizon, aversion, cardinal, return_target, l, mu_bl1, mu_bl2, cov_bl1)



    p.run_optimization(risk_tolerance=getRiskToleranceFromQuestionnaire(questionnaire=questionnaire))

    if is_new_portfolio:
        p.make_new_portfolios(questionnaire['initialInvestment'], option_type, portfolio_name)
    else:
        print(p.x1.to_dict())
        p.update_existing_portfolio(_id, p.x1.to_dict()[list(p.x1.to_dict().keys())[0]])
    print('FINISHED')
    return redirect(url_for('/.server_models_portfolio_routing_portfoliosnapshot'))


@login_required
def build():
    '''
    portfolio_name = request.headers.get('portfolioName')
    _id = getUuidFromPortfolioName(portfolio_name)
    if portfolio_name == None:
        questionnaire = None
    else:
        option_type = getOptionTypeFromName(portfolio_name)
        questionnaire = fetch_questionnaire_from_uuid_and_type(uuid=_id, option_type=option_type)
    return render_template('Build.jinja2', questionnaire=questionnaire)
    '''

    questionnaire = {'initialInvestment': "", 'retirementAmount': "", 'retirementDate': "", 'purchaseAmount': "",
                     'purchaseDate': "", 'riskAppetite': "", 'option': ""}

    return render_template('Build.jinja2', questionnaire=questionnaire)
