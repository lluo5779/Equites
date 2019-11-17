from server.common.database import Database
from server import db
#from server.models.auth.user import User

class FactorModel(db.DATABASE.Model):
    date = db.DATABASE.Column(db.DATABASE.String(80), primary_key=True)
    symbol = db.DATABASE.Column(db.DATABASE.String(80), unique=True)
    mkt_rf = db.DATABASE.Column(db.DATABASE.Float(), unique=True)
    smb = db.DATABASE.Column(db.DATABASE.Float(), unique=True)
    hml = db.DATABASE.Column(db.DATABASE.Float(), unique=True)
    rf = db.DATABASE.Column(db.DATABASE.Float(), unique=True)

    def __init__(self, date, symbol, mkt_rf, smb, hml, rf):
        self.date = date
        self.symbol = symbol
        self.mkt_rf = mkt_rf
        self.smb = smb
        self.hml = hml
        self.rf = rf

    def __repr(self):
        return '<date %r>' % self.date


class EodPrices(db.DATABASE.Model):
    date = db.DATABASE.Column(db.DATABASE.String(80))
    symbol = db.DATABASE.Column(db.DATABASE.String(80), primary_key=True)
    close = db.DATABASE.Column(db.DATABASE.Float(), unique=True)
    high = db.DATABASE.Column(db.DATABASE.Float(), unique=True)
    low = db.DATABASE.Column(db.DATABASE.Float(), unique=True)
    open = db.DATABASE.Column(db.DATABASE.Float(), unique=True)
    volume = db.DATABASE.Column(db.DATABASE.Float(), unique=True)
    adjClose = db.DATABASE.Column(db.DATABASE.Float(), unique=True)
    adjHigh = db.DATABASE.Column(db.DATABASE.Float(), unique=True)
    adjLow = db.DATABASE.Column(db.DATABASE.Float(), unique=True)
    adjVolume = db.DATABASE.Column(db.DATABASE.Float(), unique=True)
    divCash = db.DATABASE.Column(db.DATABASE.Float(), unique=True)
    splitFactor = db.DATABASE.Column(db.DATABASE.Float(), unique=True)

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


class UserPortfolio(db.DATABASE.Model):
    username = db.DATABASE.Column(db.DATABASE.String(80), primary_key=True)
    user_email = db.DATABASE.Column(db.DATABASE.String(80))
    risk_appetite = db.DATABASE.Column(db.DATABASE.String(80))
    _id = db.DATABASE.Column(db.DATABASE.String(80))
    tickers = db.DATABASE.Column(db.DATABASE.String(80))  # TO-DO: serialize list
    weights = db.DATABASE.Column(db.DATABASE.String(80))

    def __init__(self, username, user_email, risk_appetite, _id, tickers, weights):
        self.username = username
        self.user_email = user_email
        self.risk_appetite = risk_appetite
        self._id = _id
        self.tickers = tickers  # TO-DO: serialize list
        self.weights = weights

    def __repr(self):
        return '<Portfolio for auth %s>' % self.username


