from server import db
from datetime import datetime


class Option2Questionnaire(db.DATABASE.Model):
    uuid = db.DATABASE.Column(db.DATABASE.String(80), primary_key=True)
    timestamp = db.DATABASE.Column(db.DATABASE.DateTime, index=True, default=datetime.utcnow)
    option_type = db.DATABASE.Column(db.DATABASE.String(80))
    initialInvestment = db.DATABASE.Column(db.DATABASE.Float())
    riskAppetite = db.DATABASE.Column(db.DATABASE.String(80))
    startDate = db.DATABASE.Column(db.DATABASE.DateTime)
    endDate = db.DATABASE.Column(db.DATABASE.DateTime)

    def __init__(self, uuid, timestamp, option_type, initialInvestment, riskAppetite, startDate, endDate):
        self.uuid = uuid
        self.timestamp = timestamp
        self.option_type = option_type
        self.initialInvestment = initialInvestment
        self.riskAppetite = riskAppetite
        self.startDate = startDate
        self.endDate = endDate

    def __repr(self):
        return '<date %r>' % self.date


class WealthQuestionnaire(db.DATABASE.Model):
    uuid = db.DATABASE.Column(db.DATABASE.String(80), primary_key=True)
    timestamp = db.DATABASE.Column(db.DATABASE.DateTime, index=True, default=datetime.utcnow)
    option_type = db.DATABASE.Column(db.DATABASE.String(80))
    initialInvestment = db.DATABASE.Column(db.DATABASE.Float())
    riskAppetite = db.DATABASE.Column(db.DATABASE.String(80))

    def __init__(self, uuid, timestamp, option_type, initialInvestment, riskAppetite):
        self.uuid = uuid
        self.timestamp = timestamp
        self.option_type = option_type
        self.initialInvestment = initialInvestment
        self.riskAppetite = riskAppetite

    def __repr(self):
        return '<date %r>' % self.date


class PurchaseQuestionnaire(db.DATABASE.Model):
    uuid = db.DATABASE.Column(db.DATABASE.String(80), primary_key=True)
    timestamp = db.DATABASE.Column(db.DATABASE.DateTime, index=True, default=datetime.utcnow)
    option_type = db.DATABASE.Column(db.DATABASE.String(80))
    initialInvestment = db.DATABASE.Column(db.DATABASE.Float())
    purchaseAmount = db.DATABASE.Column(db.DATABASE.Float())
    riskAppetite = db.DATABASE.Column(db.DATABASE.String(80))
    purchaseDate = db.DATABASE.Column(db.DATABASE.DateTime)

    def __init__(self, uuid, timestamp, option_type, initialInvestment, purchaseAmount, riskAppetite, purchaseDate):
        self.uuid = uuid
        self.timestamp = timestamp
        self.option_type = option_type
        self.purchaseAmount = purchaseAmount
        self.initialInvestment = initialInvestment
        self.riskAppetite = riskAppetite
        self.purchaseDate = purchaseDate

    def __repr(self):
        return '<date %r>' % self.date


class RetirementQuestionnaire(db.DATABASE.Model):
    uuid = db.DATABASE.Column(db.DATABASE.String(80), primary_key=True)
    timestamp = db.DATABASE.Column(db.DATABASE.DateTime, index=True, default=datetime.utcnow)
    initialInvestment = db.DATABASE.Column(db.DATABASE.Float())
    option_type = db.DATABASE.Column(db.DATABASE.String(80))
    retirementAmount = db.DATABASE.Column(db.DATABASE.Float())
    riskAppetite = db.DATABASE.Column(db.DATABASE.String(80))
    retirementDate = db.DATABASE.Column(db.DATABASE.DateTime)

    def __init__(self, uuid, timestamp, option_type, initialInvestment, retirementAmount, riskAppetite, retirementDate):
        self.uuid = uuid
        self.timestamp = timestamp
        self.option_type = option_type
        self.retirementAmount = retirementAmount
        self.initialInvestment = initialInvestment
        self.riskAppetite = riskAppetite
        self.retirementDate = retirementDate

    def __repr(self):
        return '<date %r>' % self.date
