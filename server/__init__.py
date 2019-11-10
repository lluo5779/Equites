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
    db.initialize(app)

    app.config['SECRET_KEY'] = SECRET_KEY

    connex_app.add_api('swagger.yaml', base_path='/')

    from server.models.auth.routing import auth_mold
    app.register_blueprint(auth_mold, url_prefix="/auth")

    # Initialize Database before running any other command
    # @app.before_first_request
    # def init_db():
    #

    return connex_app
