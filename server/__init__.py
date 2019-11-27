from flask import Flask, render_template
import connexion
import os
from server.common.database import Database
from flask_login import LoginManager

db = Database()
login_manager = LoginManager()
SECRET_KEY = 'SECRETKEY'


def create_app():
    basedir = os.path.abspath(os.path.dirname(__file__))
    connex_app = connexion.FlaskApp(__name__, specification_dir=basedir)
    app = connex_app.app

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    db.initialize(app)

    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['EXPLAIN_TEMPLATE_LOADING'] = True
    #app.config['DEBUG'] = True

    connex_app.add_api('swagger.yaml', base_path='/')

    from server.models.auth.routing import auth_mold
    from server.models.portfolio.routing import trackSpecialCase
    app.register_blueprint(auth_mold, url_prefix="/auth")
    app.register_blueprint(trackSpecialCase, url_prefix="")
    # Initialize Database before running any other command
    # @app.before_first_request
    # def init_db():
    #

    return connex_app
