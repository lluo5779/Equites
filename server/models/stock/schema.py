from server import db


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
