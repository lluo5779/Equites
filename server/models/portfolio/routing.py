import uuid
import ast
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

from server.models.portfolio.stats import *
import flask
from plotly.graph_objs import Scatter, Pie, Layout
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta

from io import BytesIO
from flask import Blueprint
import urllib
import base64
import plotly.offline

from server.models.user_preferences.user_preferences import fetch_latest_questionnaire_from_type, \
    fetch_questionnaire_from_uuid_and_type, update_new_questionnaire, initialize_new_questionnaire, \
    fetch_all_questionnaires
from server.models.portfolio.tiingo import get_data
from server.models.portfolio.bt import back_test
from server.models.stock.stock import Stocks, fetchEodPrices

trackSpecialCase = Blueprint("", __name__)
s = Stocks()


@login_required
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
            rolling = 100 if bt_days > 1000 else max(int(bt_days / 10), 1)

            portfolio_data = args[2:]

            tickers = portfolio_data[::2]
            values = [abs(float(x)) for x in portfolio_data[1::2]]
            weights = [(x / sum(values)) for x in values]
            portfolio = dict(zip(tickers, weights))

            values, success, msg = back_test(portfolio, start_date, end_date=None, dollars=sum(values), tore=True)
        except:
            succcess, error = False, True

        if success:
            try:
                port_values = values.sum(axis=1)
                port_values.rename(columns={'Unnamed: 0': 'value'}, inplace=True)

                # PORTFOLIO HOLDINGS
                pie = plotly.offline.plot({"data": [Pie(labels=tickers, values=weights, hole=.1)]},
                                          output_type='div',
                                          include_plotlyjs=False,
                                          show_link=False,
                                          config={"displayModeBar": False})

                # CUMULATIVE RETURNS
                plot_data = plotly.graph_objs.Scatter(x=list(port_values.index), y=port_values, mode='lines',
                                                      line=dict(color='#3B4F66'))
                plot = plotly.offline.plot({"data": plot_data},
                                           output_type='div',
                                           include_plotlyjs=False,
                                           show_link=False,
                                           config={"displayModeBar": False})

                # calculate returns from the portfolio
                port_returns = (port_values / port_values.shift(1) - 1).dropna()

                # ROLLING VOLATILITY
                vols = rolling_volatility(port_returns, rolling).dropna()
                vols_plot_data = plotly.graph_objs.Scatter(x=list(port_values.index), y=vols, mode='lines',
                                                           line=dict(color='#3B4F66'))
                vols_plot = plotly.offline.plot({"data": vols_plot_data},
                                                output_type='div',
                                                include_plotlyjs=False,
                                                show_link=False,
                                                config={"displayModeBar": False})

                # ROLLING SHARPE
                sharpe = rolling_sharpe(port_returns, rolling).dropna()
                sharpe_plot_data = plotly.graph_objs.Scatter(x=list(port_values.index), y=sharpe, mode='lines',
                                                             line=dict(color='#3B4F66'))
                sharpe_plot = plotly.offline.plot({"data": sharpe_plot_data},
                                                  output_type='div',
                                                  include_plotlyjs=False,
                                                  show_link=False,
                                                  config={"displayModeBar": False})

                # detailed statistics
                underwater = drawdown_underwater(port_returns)

                underwater_data = plotly.graph_objs.Scatter(x=list(port_values.index), y=underwater, mode='lines',
                                                            line=dict(color='#3B4F66'))
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
            except:
                return render_template('Option1.jinja2', display=False, error=True)
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
            try:
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
                enhanced_values = \
                    back_test(weights.to_dict()['weight'], start_date, end_date=None, dollars=budget, tore=True)[0].sum(
                        axis=1)[-(len(portfolio_value) + 1):]
                back_returns = (enhanced_values / enhanced_values.shift(1) - 1).dropna()
                enhanced_values = cum_returns(back_returns, budget)

                expected_returns = float(p.mu_bl1.T.dot(weights).iloc[0])

                ## COMPARE PORTFOLIO RETURNS OVER THE: PAST MONTHS
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
            except:
                return render_template('Option2.jinja2', display=False, error=(not success))
        else:
            return render_template('Option2.jinja2', display=False, error=(not success))


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

    questionnaire["optionType"] = option_type

    return questionnaire


@login_required
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
                try:
                    month = int(raw_dates[1])
                except:
                    month = 1
            else:
                separator = '/'
                raw_dates = raw_dates.split(separator)
                year = int(raw_dates[0])
                try:
                    month = int(raw_dates[1])
                except:
                    month = 1
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

    if _id is None:  # If the id is not present in the database, consider this a new portfolio and generate new UUID
        _id = uuid.uuid4()
        is_new_portfolio = True

    # Updating the portfolio data
    p = Portfolio(current_user.username, _id=_id, generate_new=is_new_portfolio)

    # Initialize parameters used to determine risk preferences.
    if option_type == "Wealth":
        horizon, return_target = 10, 0.15
    elif option_type == "Retirement":
        horizon = relativedelta(questionnaire["retirementDate"], datetime.today()).years
        horizon = 1 if horizon == 0 else horizon
        total_target = float(questionnaire["retirementAmount"]) / float(questionnaire["initialInvestment"])
        return_target = total_target / (2 * horizon)
    else:
        horizon = relativedelta(questionnaire["purchaseDate"], datetime.today()).years
        horizon = 1 if horizon == 0 else horizon
        total_target = float(questionnaire["purchaseAmount"]) / float(questionnaire["initialInvestment"])
        return_target = total_target / (2 * horizon)

    aversion = 1 if questionnaire['riskAppetite'] == 'High Risk' else (
        2 if questionnaire['riskAppetite'] == 'Med Risk' else 3)

    # Determine parameters to the model based on user input
    alpha, multipliers, exposures, cardinality = risk_prefs(horizon,
                                                            aversion,
                                                            cardinal=15,
                                                            return_target=return_target,
                                                            l=5,
                                                            mu_bl1=p.mu_bl1,
                                                            mu_bl2=p.mu_bl2,
                                                            cov_bl1=p.cov_bl1)

    # assign the risk tolerances, specifying a SHARPE optimization
    risk_tolerance = (multipliers, exposures, cardinality, 'MCVAR')

    # Optimize the portfolio based on risk tolerances
    p.run_optimization(risk_tolerance=risk_tolerance,
                       alpha=alpha,
                       return_target=return_target,
                       budget=float(questionnaire["initialInvestment"]))

    # backtest over the previous 6 months
    values = back_test(p.x1.to_dict()['weight'],
                       start_date=None,
                       end_date=None,
                       dollars=float(questionnaire["initialInvestment"]),
                       tore=True)[0].sum(axis=1)[-132:]

    back_returns = (values / values.shift(1) - 1).dropna()
    port_values = cum_returns(back_returns, float(questionnaire["initialInvestment"]))

    # PORTFOLIO HOLDINGS
    pie_weights = p.x1.loc[p.x1['weight'] != 0]
    pie = plotly.offline.plot({"data": [Pie(labels=pie_weights.index, values=pie_weights['weight'].round(2), hole=.1)]},
                              output_type='div',
                              include_plotlyjs=False,
                              show_link=False,
                              config={"displayModeBar": False})

    # CUMULATIVE RETURNS
    plot_data = plotly.graph_objs.Scatter(x=list(port_values.index), y=port_values, mode='lines',
                                          line=dict(color='#3B4F66'))
    plot = plotly.offline.plot({"data": plot_data},
                               output_type='div',
                               include_plotlyjs=False,
                               show_link=False,
                               config={"displayModeBar": False})

    # calculate returns from the portfolio
    port_returns = (port_values / port_values.shift(1) - 1).dropna()

    # ROLLING VOLATILITY
    vols = rolling_volatility(port_returns, 10).dropna()
    vols_plot_data = plotly.graph_objs.Scatter(x=list(port_values.index), y=vols, mode='lines',
                                               line=dict(color='#3B4F66'))
    vols_plot = plotly.offline.plot({"data": vols_plot_data},
                                    output_type='div',
                                    include_plotlyjs=False,
                                    show_link=False,
                                    config={"displayModeBar": False})

    # ROLLING SHARPE
    sharpe = rolling_sharpe(port_returns, 10).dropna()
    sharpe_plot_data = plotly.graph_objs.Scatter(x=list(port_values.index), y=sharpe, mode='lines',
                                                 line=dict(color='#3B4F66'))
    sharpe_plot = plotly.offline.plot({"data": sharpe_plot_data},
                                      output_type='div',
                                      include_plotlyjs=False,
                                      show_link=False,
                                      config={"displayModeBar": False})

    # detailed statistics
    underwater = drawdown_underwater(port_returns)
    underwater_data = plotly.graph_objs.Scatter(x=list(port_values.index), y=underwater, mode='lines',
                                                line=dict(color='#3B4F66'))
    underwater_plot = plotly.offline.plot({"data": underwater_data},
                                          output_type='div',
                                          include_plotlyjs=False,
                                          show_link=False,
                                          config={"displayModeBar": False})

    total_returns = round((port_values[-1] / port_values[0] - 1) * 100)
    min_value = round(min(port_values), 2)
    max_value = round(max(port_values), 2)
    stats = [total_returns, min_value, max_value]

    weightings = [p.x1, p.x2]
    num_shares = p.num_shares.T

    start_date = (datetime.now() - relativedelta(months=6)).strftime("%Y-%m-%d")

    histValues = back_test(p.x1.to_dict()[list(p.x1.to_dict().keys())[0]], start_date)[0].sum(axis=1) \
                 * float(questionnaire['initialInvestment'])

    return render_template('portfolioview.jinja2', title='Sign In', weightings_1=weightings[0],
                           weightings_2=weightings[1], histValues=histValues, long=None,
                           short=None, portfolioName=portfolio_name, questionnaire=questionnaire, num_shares=num_shares,
                           pie=pie, plot=plot, vols_plot=vols_plot, sharpe_plot=sharpe_plot,
                           underwater_plot=underwater_plot, stats=stats)


@login_required
def portfoliosnapshot():
    """
        Displays all user portfolio
        Input:
            None
        Output:
            portfoliosnapshot.jinja2
        Accessed from:
            menu
            portfolioview upon save
    """

    username = current_user.username

    # Fetches all questionnaires and portfolios for a given user
    df_to_display = fetch_all_questionnaires(username)
    latest_prices = fetchEodPrices(get_latest=True)[SYMBOLS]
    all_past_p = get_past_portfolios(username=username, get_all=True)
    initial_weights = all_past_p[0][SYMBOLS]

    investment_target = df_to_display['target']

    holding_names = [x + "_holdings" for x in SYMBOLS]
    latest_holdings = all_past_p[2][holding_names]
    df_to_display['percentCompleted'] = ""
    df_to_display['targetAmount'] = ""
    df_to_display['start_date'] = ""
    df_to_display['returns'] = 0

    for _id, portfolio in latest_holdings.iterrows():  # iterating over each portfolio to obtain portfolio value and format start date
        portfolio.index = SYMBOLS
        start_date = all_past_p[2].loc[_id, 'timestamp'].to_pydatetime()
        portfolio_value = latest_prices.dot(portfolio)
        df_to_display.loc[_id, 'start_date'] = start_date.strftime("%Y-%m")

        if investment_target.loc[_id] == "":
            # wealth portfolio does not have a target. Hence, we skip calculations for the wealth portfolio
            continue

        try:
            current_return = portfolio_value / investment_target.loc[_id]
        except:
            current_return = portfolio_value * 0

        df_to_display.loc[_id, 'returns'] = round(current_return.values[0], 2)
        df_to_display.loc[_id, 'end_date'] = df_to_display.loc[_id, 'end_date'].strftime("%Y-%m")

        df_to_display.loc[_id, 'targetAmount'] = round(float(investment_target.loc[_id]), 2)
        df_to_display.loc[_id, 'percentCompleted'] = str(round(current_return.values[0], 2)) + "%"

    return render_template('portfoliosnapshot.jinja2', title='optiondecision',
                           purchase=df_to_display[df_to_display['optionType'] == "purchase"],
                           retirement=df_to_display[df_to_display['optionType'] == "retirement"],
                           wealth=df_to_display[df_to_display['optionType'] == "wealth"])


@login_required
def portfoliodashboard():
    """
    Displays a detailed dashboard of the portfolio based on portfolio name
    Input:
        Params: portfolioName
    Output:
        portfoliodashboard.jinja2
    Accessed from:
        portfoliosnapshot
    """

    portfolio_name = request.args.get('portfolioName')
    username = current_user.username

    _id = getUuidFromPortfolioName(portfolio_name)

    if _id is None:
        # if this page is accessed without any known portfolio ids, redirect back to portfolio snapshot
        return redirect(url_for('/.server_models_portfolio_routing_portfoliosnapshot'))

    p = Portfolio(username=username, _id=_id, generate_new=False)

    df_to_display = fetch_all_questionnaires(username).loc[_id]
    latest_prices = fetchEodPrices(get_latest=True)[SYMBOLS]

    investment_target = df_to_display['target']

    holding_names = [x + "_holdings" for x in SYMBOLS]
    num_shares = p.num_shares.T
    num_shares.columns = SYMBOLS
    portfolio_value = latest_prices.values[0] * num_shares.values[0]

    weightings = p.num_shares.to_numpy().flatten()
    values = portfolio_value
    values = pd.DataFrame(values, columns=['value'], index=SYMBOLS)
    values.loc['CASH', ] = (1 - p.x1.sum()).values

    tickers = list(p.x1.columns)

    option_type = getOptionTypeFromName(portfolio_name)
    questionnaire = fetch_questionnaire_from_uuid_and_type(uuid=_id, option_type=option_type)

    error = False
    success = True
    show_plots = True

    pie_weights = p.x1.round(2).loc[p.x1.iloc[:, 0] != 0]

    # PORTFOLIO HOLDINGS
    pie = plotly.offline.plot({"data": [Pie(labels=pie_weights.index, values=pie_weights.iloc[:, 0], hole=.1)]},
                              output_type='div',
                              include_plotlyjs=False,
                              show_link=False,
                              config={"displayModeBar": False})

    try:

        inception_date = pd.to_datetime(str(questionnaire['timestamp'].values[0])).strftime("%Y-%m-%d")

        if datetime.now().date() == datetime.strptime(inception_date, "%Y-%m-%d").date():
            return render_template('portfoliodashboard.jinja2',
                                   display=True,
                                   error=False,
                                   show_plots=False,
                                   pie=pie,
                                   questionnaire=questionnaire,
                                   option=option_type,
                                   portfolioName=portfolio_name)

        # rolling days assignment
        six_month = datetime.utcnow() - relativedelta(months=6)

        start_date = pd.to_datetime(str(questionnaire['timestamp'].values[0]))
        bt_days = business_days(start_date, datetime.utcnow())
        rolling = 100 if bt_days > 1000 else max(int(bt_days / 10), 1)


        p_values, success, msg = back_test(p.x1.to_dict()[0],
                                         start_date.strftime("%Y-%m-%d"),
                                         end_date=None,
                                         dollars=float(values.sum()),
                                         tore=True)
    except:
        print("\n\n\n FAILURE ... I AM GOING TO DIE NOW")
        succcess, error = False, True

    if success:

        port_values = p_values.sum(axis=1)
        port_values.rename(columns={'Unnamed: 0': 'value'}, inplace=True)

        # CUMULATIVE RETURNS
        plot_data = plotly.graph_objs.Scatter(x=list(port_values.index), y=port_values, mode='lines',
                                              line=dict(color='#3B4F66'))
        plot = plotly.offline.plot({"data": plot_data},
                                   output_type='div',
                                   include_plotlyjs=False,
                                   show_link=False,
                                   config={"displayModeBar": False})

        # calculate returns from the portfolio
        port_returns = (port_values / port_values.shift(1) - 1).dropna()

        # ROLLING VOLATILITY
        vols = rolling_volatility(port_returns, rolling).dropna()
        vols_plot_data = plotly.graph_objs.Scatter(x=list(port_values.index), y=vols, mode='lines',
                                                   line=dict(color='#3B4F66'))
        vols_plot = plotly.offline.plot({"data": vols_plot_data},
                                        output_type='div',
                                        include_plotlyjs=False,
                                        show_link=False,
                                        config={"displayModeBar": False})

        # ROLLING SHARPE
        sharpe = rolling_sharpe(port_returns, rolling).dropna()
        sharpe_plot_data = plotly.graph_objs.Scatter(x=list(port_values.index), y=sharpe, mode='lines',
                                                     line=dict(color='#3B4F66'))
        sharpe_plot = plotly.offline.plot({"data": sharpe_plot_data},
                                          output_type='div',
                                          include_plotlyjs=False,
                                          show_link=False,
                                          config={"displayModeBar": False})

        # detailed statistics
        underwater = drawdown_underwater(port_returns)

        underwater_data = plotly.graph_objs.Scatter(x=list(port_values.index), y=underwater, mode='lines',
                                                    line=dict(color='#3B4F66'))
        underwater_plot = plotly.offline.plot({"data": underwater_data},
                                              output_type='div',
                                              include_plotlyjs=False,
                                              show_link=False,
                                              config={"displayModeBar": False})

        total_returns = round((port_values[-1] / port_values[0] - 1) * 100)
        min_value = round(min(port_values), 2)
        max_value = round(max(port_values), 2)
        stats = [total_returns, min_value, max_value]

        return render_template('portfoliodashboard.jinja2',
                               display=True,
                               error=False,
                               show_plots=True,
                               tickers=tickers,
                               weightings=values,
                               pie=pie,
                               plot=plot,
                               vols_plot=vols_plot,
                               sharpe_plot=sharpe_plot,
                               underwater=underwater_plot,
                               stats=stats,
                               rolling=rolling,
                               questionnaire=questionnaire,
                               option=option_type,
                               portfolioName=portfolio_name)

    else:
        return render_template('portfoliodashboard.jinja2', display=False, error=True)


@login_required
def editportfolio():
    """
        Pulls the most recent questionnaire data for input portfolioName""
        Input:
            Params: portfolioName
        Output:
            build.jinja2
        Accessed from:
            portfolioview
    """

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

    # populate rest of questionnaire with empty strings. This is done so that all front-end survey options can be populated
    questionnaire = populateQuestionnaire(questionnaire, option_type)

    date_key = ''
    if questionnaire['retirementDate'] != '':
        date_key = 'retirementDate'
    elif questionnaire['purchaseDate'] != '':
        date_key = 'purchaseDate'

    if date_key != '' and len(questionnaire[date_key]) >= 8:
        raw_date = questionnaire[date_key].split('-')
        month = '0' + raw_date[1] if len(raw_date[1]) == 1 else raw_date[1]
        questionnaire[date_key] = month + '/' + raw_date[0]

    return render_template('Build.jinja2', title='Sign In', questionnaire=questionnaire)


@login_required
def saveportfolio():
    """
        Saves both the portfolio and questionnaire into database.
        Input:
            Params: portfolioName
        Output:
            build.jinja2
        Accessed from:
            portfolioview
    """
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
            try:
                questionnaire[question] = datetime(int(raw_dates[0]), int(raw_dates[1]), 1)
            except:
                questionnaire[question] = datetime(int(raw_dates[0]), 1, 1)
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

    if option_type == "Wealth":
        horizon, return_target = 10, 0.15
    elif option_type == "Retirement":
        horizon = relativedelta(questionnaire["retirementDate"], datetime.today()).years
        horizon = 1 if horizon == 0 else horizon
        total_target = float(questionnaire["retirementAmount"]) / float(questionnaire["initialInvestment"])
        return_target = total_target / (2 * horizon)
    else:
        horizon = relativedelta(questionnaire["purchaseDate"], datetime.today()).years
        horizon = 1 if horizon == 0 else horizon
        total_target = float(questionnaire["purchaseAmount"]) / float(questionnaire["initialInvestment"])
        return_target = total_target / (2 * horizon)

    aversion = 1 if questionnaire['riskAppetite'] == 'High Risk' else (
        2 if questionnaire['riskAppetite'] == 'Med Risk' else 3)

    alpha, multipliers, exposures, cardinality = risk_prefs(horizon,
                                                            aversion,
                                                            cardinal=15,
                                                            return_target=return_target,
                                                            l=5,
                                                            mu_bl1=p.mu_bl1,
                                                            mu_bl2=p.mu_bl2,
                                                            cov_bl1=p.cov_bl1)

    # assign the risk tolerances, specifying a SHARPE optimization
    risk_tolerance = (multipliers, exposures, cardinality, 'MCVAR')

    p.run_optimization(risk_tolerance=risk_tolerance,
                       alpha=alpha,
                       return_target=return_target,
                       budget=float(questionnaire["initialInvestment"]))

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
