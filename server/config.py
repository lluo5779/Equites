username = "postgres"
password = "louisluo"
databaseName= "factorModel"

import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from initialize import *
from dataGetter import getSth
basedir = os.path.abspath(os.path.dirname(__file__))

sql_url = "postgresql://{}:{}@localhost/{}".format(username, password, databaseName)
print('This is sql url: ', sql_url)
# Configure the SqlAlchemy part of the app instance
app.config["SQLALCHEMY_ECHO"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = sql_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Create the SqlAlchemy db instance
db = SQLAlchemy(app)

# Initialize Marshmallow
ma = Marshmallow(app)


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