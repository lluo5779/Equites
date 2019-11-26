from server import db
from server.models.portfolio.config import SYMBOLS
from datetime import datetime


class UserPortfolio(db.DATABASE.Model):
    username = db.DATABASE.Column(db.DATABASE.String(80))
    uuid = db.DATABASE.Column(db.DATABASE.String(80), primary_key=True)
    active = db.DATABASE.Column(db.DATABASE.String(10))
    period = db.DATABASE.Column(db.DATABASE.Float())
    portfolio_type = db.DATABASE.Column(db.DATABASE.String(80))
    portfolio_name = db.DATABASE.Column(db.DATABASE.String(80), unique=True)
    ITOT = db.DATABASE.Column(db.DATABASE.Float())
    DIA = db.DATABASE.Column(db.DATABASE.Float())
    SPY = db.DATABASE.Column(db.DATABASE.Float())
    XLG = db.DATABASE.Column(db.DATABASE.Float())
    AIA = db.DATABASE.Column(db.DATABASE.Float())
    GXC = db.DATABASE.Column(db.DATABASE.Float())
    XLY = db.DATABASE.Column(db.DATABASE.Float())
    XLE = db.DATABASE.Column(db.DATABASE.Float())
    XLF = db.DATABASE.Column(db.DATABASE.Float())
    XLV = db.DATABASE.Column(db.DATABASE.Float())
    XLI = db.DATABASE.Column(db.DATABASE.Float())
    XLB = db.DATABASE.Column(db.DATABASE.Float())
    XLK = db.DATABASE.Column(db.DATABASE.Float())
    XLU = db.DATABASE.Column(db.DATABASE.Float())
    ICLN = db.DATABASE.Column(db.DATABASE.Float())
    CGW = db.DATABASE.Column(db.DATABASE.Float())
    WOOD = db.DATABASE.Column(db.DATABASE.Float())
    IYR = db.DATABASE.Column(db.DATABASE.Float())

    ITOT2 = db.DATABASE.Column(db.DATABASE.Float())
    DIA2 = db.DATABASE.Column(db.DATABASE.Float())
    SPY2 = db.DATABASE.Column(db.DATABASE.Float())
    XLG2 = db.DATABASE.Column(db.DATABASE.Float())
    AIA2 = db.DATABASE.Column(db.DATABASE.Float())
    GXC2 = db.DATABASE.Column(db.DATABASE.Float())
    XLY2 = db.DATABASE.Column(db.DATABASE.Float())
    XLE2 = db.DATABASE.Column(db.DATABASE.Float())
    XLF2 = db.DATABASE.Column(db.DATABASE.Float())
    XLV2 = db.DATABASE.Column(db.DATABASE.Float())
    XLI2 = db.DATABASE.Column(db.DATABASE.Float())
    XLB2 = db.DATABASE.Column(db.DATABASE.Float())
    XLK2 = db.DATABASE.Column(db.DATABASE.Float())
    XLU2 = db.DATABASE.Column(db.DATABASE.Float())
    ICLN2 = db.DATABASE.Column(db.DATABASE.Float())
    CGW2 = db.DATABASE.Column(db.DATABASE.Float())
    WOOD2 = db.DATABASE.Column(db.DATABASE.Float())
    IYR2 = db.DATABASE.Column(db.DATABASE.Float())

    print(">>> datetime.utcnow", datetime.utcnow())
    timestamp = db.DATABASE.Column(db.DATABASE.DateTime, index=True, default=datetime.utcnow)
    preferences = db.DATABASE.relationship('user_preferences', backref='author', lazy='dynamic')


    def __init__(self, username, portfolio_name, uuid, active, timestamp, portfolio_type, ITOT, DIA, SPY, XLG, AIA, GXC, XLY, XLE, XLF, XLV, XLI, XLB, XLK, XLU,
                 ICLN, CGW, WOOD, IYR, ITOT2, DIA2, SPY2, XLG2, AIA2, GXC2, XLY2, XLE2, XLF2, XLV2, XLI2, XLB2, XLK2,
                 XLU2, ICLN2, CGW2, WOOD2, IYR2, preferences):
        self.username = username
        self.uuid = uuid
        # self.period = period
        self.active = active
        self.timestamp = timestamp
        self.portfolio_type = portfolio_type

        self.portfolio_name = portfolio_name

        self.ITOT = ITOT
        self.DIA = DIA
        self.SPY = SPY
        self.XLG = XLG
        self.AIA = AIA
        self.GXC = GXC
        self.XLY = XLY
        self.XLE = XLE
        self.XLF = XLF
        self.XLV = XLV
        self.XLI = XLI
        self.XLB = XLB
        self.XLK = XLK
        self.XLU = XLU
        self.ICLN = ICLN
        self.CGW = CGW
        self.WOOD = WOOD
        self.IYR = IYR

        self.ITOT2 = ITOT2
        self.DIA2 = DIA2
        self.SPY2 = SPY2
        self.XLG2 = XLG2
        self.AIA2 = AIA2
        self.GXC2 = GXC2
        self.XLY2 = XLY2
        self.XLE2 = XLE2
        self.XLF2 = XLF2
        self.XLV2 = XLV2
        self.XLI2 = XLI2
        self.XLB2 = XLB2
        self.XLK2 = XLK2
        self.XLU2 = XLU2
        self.ICLN2 = ICLN2
        self.CGW2 = CGW2
        self.WOOD2 = WOOD2
        self.IYR2 = IYR2


    def __repr(self):
        return '<Portfolio for auth %s>' % self.username
