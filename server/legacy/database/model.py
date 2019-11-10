from datetime import datetime
from config import db, ma
from flask_login import UserMixin


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


class EodPrices(db.Model):
    date = db.Column(db.String(80))
    symbol = db.Column(db.String(80))
    close = db.Column(db.Float(), unique=True)
    high = db.Column(db.Float(), unique=True)
    low = db.Column(db.Float(), unique=True)
    open = db.Column(db.Float(), unique=True)
    volume = db.Column(db.BigInt(), unique=True)
    adjClose = db.Column(db.Float(), unique=True)
    adjHigh = db.Column(db.Float(), unique=True)
    adjLow = db.Column(db.Float(), unique=True)
    adjVolume = db.Column(db.BigInt(), unique=True)
    divCash = db.Column(db.Float(), unique=True)
    splitFactor = db.Column(db.Float(), unique=True)

    def __init__(self, date, symbol, close, high, low, open, volume, adjClose, adjHigh, adjLow, adjVolume, divCash,
                 splitFactor):
        self.date = date
        self.symbol = symbol
        self.close = close
        self.high = high
        self.low = low
        self.open = open
        self.volume = volume
        self.adjClose = adjClose
        self.adjHigh = adjHigh
        self.adjLow = adjLow
        self.adjVolume = adjVolume
        self.divCash = divCash
        self.splitFactor = splitFactor

    def __repr(self):
        return '<date %r>' % self.date

    # UserPortfolio
class UserPortfolio(db.Model):
    username = db.Column(db.String(80), primary_key=True)
    user_email = db.Column(db.String(80))
    risk_appetite = db.Column(db.String(80))
    _id = db.Column(db.String(80))
    tickers = db.Column(db.String(80)) #TO-DO: serialize list
    weights = db.Column(db.String(80))

    def __init__(self, username, user_email, risk_appetite, _id, tickers, weights):
        self.username = username
        self.user_email = user_email
        self.risk_appetite = risk_appetite
        self._id = _id
        self.tickers = tickers  # TO-DO: serialize list
        self.weights = weights