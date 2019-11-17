from server import db

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
