from datetime import datetime
from config import db, ma
#
#
# class Person(db.Model):
#     __tablename__ = "person"
#     person_id = db.Column(db.Integer, primary_key=True)
#     lname = db.Column(db.String(32))
#     fname = db.Column(db.String(32))
#     timestamp = db.Column(
#         db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
#     )
#
#
# class PersonSchema(ma.ModelSchema):
#     class Meta:
#         model = Person
#         sqla_session = db.session



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)

    def __init__(self, username, email):
        self.username = username
        self.email = email

    def __repr__(self):
        return '<User %r>' % self.username

class FactorModel(db.Model):
    date = db.Column(db.String(80), primary_key=True)
    symbol = db.Column(db.String(80), unique=True)
    mkt_rf = db.Column(db.Float(), unique=True)
    smb = db.Column(db.Float(), unique=True)
    hml = db.Column(db.Float(), unique=True)
    rf = db.Column(db.Float(), unique=True)

    def __init__(self, date, symbol, mkt_rf, smb, hml, rf):
        self.date = date
        self.symbol = symbol
        self.mkt_rf = mkt_rf
        self.smb = smb
        self.hml = hml
        self.rf = rf

    def __repr(self):
        return '<date %r>' % self.date