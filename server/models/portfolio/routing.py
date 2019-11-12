from flask import Blueprint, request, session, redirect, url_for, render_template

from server.models.users.user import User
import server.models.users.errors as UserErrors
import server.models.users.decorators as user_decorators
from server.common.database import Database
from server.models.portfolio.portfolio import Portfolio

from io import BytesIO
import urllib
import base64

@user_decorators.requires_login
def get_portfolio_page(portfolio_id):   # Renders unique portfolio page
    return render_template('/portfolios/portfolio.jinja2')

@user_decorators.requires_login
def change_risk(username):         # Views form to change portfolio's associated risk aversion parameter
    port = Portfolio.get_by_id(username)
    if request.method == "POST":
        risk_appetite = request.form['risk_appetite']
        port.risk_appetite = risk_appetite
        port.update_portfolio()
        img = BytesIO()
        img.seek(0)
        plot_data = base64.b64encode(img.read()).decode()
        return render_template('/portfolios/optimal_portfolio.jinja2', portfolio = port, plot_url=plot_data)

    return render_template('/portfolios/edit_portfolio.jinja2',portfolio = port)

@user_decorators.requires_login
def create_portfolio():            # Views form to create portfolio associated with active/ loggedin auth
    if request.method == "POST":
        risk_appetite = request.form['risk_appetite']
        port = Portfolio(session['email'], risk_appetite= risk_appetite)
        port.update_portfolio()
        fig = port.runMVO()
        img = BytesIO()
        fig.savefig(img)
        img.seek(0)
        plot_data = base64.b64encode(img.read()).decode()
        return render_template('/portfolios/optimal_portfolio.jinja2', portfolio=port, plot_url=plot_data)

    return render_template('/portfolios/new_portfolio.jinja2')
