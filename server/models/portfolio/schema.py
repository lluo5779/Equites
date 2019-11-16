from server import db


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
