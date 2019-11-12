username = "postgres"
password = "louisluo"
databaseName = "factorModel"

import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from initialize import basedir, connex_app, app, login_manager
from dataGetter import getSth

basedir = os.path.abspath(os.path.dirname(__file__))

sql_url = "postgresql://{}:{}@localhost/".format(username, password)
print('This is sql url: ', sql_url)
# Configure the SqlAlchemy part of the app instance
app.config["SQLALCHEMY_ECHO"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = sql_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Create the SqlAlchemy db instance
# engine = SQLAlchemy.create_engine(sql_url, {})
db = SQLAlchemy(app)

# Initialize Marshmallow
ma = Marshmallow(app)

login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

## Routing ##
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    form = LoginForm()
    if form.validate_on_submit():
        # Login and validate the auth.
        # auth should be an instance of your `User` class
        login_user(user)

        flask.flash('Logged in successfully.')

        next = flask.request.args.get('next')
        # is_safe_url should check if the url is safe for redirects.
        # See http://flask.pocoo.org/snippets/62/ for an example.
        if not is_safe_url(next):
            return flask.abort(400)

        return flask.redirect(next or flask.url_for('index'))
    return flask.render_template('login.html', form=form)

@app.route("/settings")
@login_required
def settings():
    pass

@app.route("/logout")
@login_required
def logout():
    logout_user()
    #return redirect(somewhere)


## API Routing ##
@app.route('/')
def index():
    print("basedir: ", basedir)
    df = getSth(db)
    return render_template("index.html", tables=[df.to_html(classes='data')], titles=df.columns.values)


@app.route('/books')
def renderBooks():
    print('>>>>>> THIS IS RENDERING BOOKS <<<<<<<<<<<')
    return render_template("index.html")


if __name__ == "__main__":
    app.run()
