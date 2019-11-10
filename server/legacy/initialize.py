import connexion
import os

from flask_login import LoginManager

basedir = os.path.abspath(os.path.dirname(__file__))
connex_app = connexion.FlaskApp(__name__, specification_dir=basedir)
app = connex_app.app

login_manager = LoginManager()
