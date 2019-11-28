from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

class Database(object):
    username = "postgres"
    password = ""
    URI = "postgresql://{}:{}@localhost/".format(username, password)
    DATABASE = None


    @staticmethod
    def initialize(app):       # Initializes Database (Mongodb must be already running on system)
        app.config["SQLALCHEMY_ECHO"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = Database.URI
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        Database.DATABASE = SQLAlchemy(app)
        Database.ma = Marshmallow(app)

    @staticmethod
    def insert(collection, data):       # Inserts new record in db.collection (data must be in JSON)
        Database.DATABASE[collection].insert(data)

    @staticmethod
    def find(collection, query):        # Returns all records from db.collection matching query
        return Database.DATABASE[collection].find(query)        # query must be in JSON

    @staticmethod
    def find_one(collection, query):    # Returns fist record from db.collection matching query
        return Database.DATABASE[collection].find_one(query)    # query must be in JSON

    @staticmethod
    def update(collection, query, data):    # Modifies record matching query in db.collection
        # (upsert = true): creates a new record when no record matches the query criteria
        Database.DATABASE[collection].update(query,data,upsert = True)

    @staticmethod
    def remove(collection, query):      # Deletes record from db.collecion
        Database.DATABASE[collection].remove(query)
