from datetime import date, timedelta

COLLECTION = 'user_portfolio'                                       # MongoDB collection
SYMBOLS = ['IVV', 'SPDW', 'SPEM', # Market-cap Equity
           'SPYD', 'SPFF', 'VTEB', 'SPXB', # Income Solutions
           'XLC','XLY','XLE','XLF','XLV','XLI','XLB','XLRE','XLK','XLU', # Sector Solutions
           'SNPE','SPYX','ICLN','CGW','GRNB'# Thematic
           ]
START_DATE = (date.today() - timedelta(days=6*365)).isoformat()
END_DATE = date.today().isoformat()
RISK_PROFILE_INDICES = [32, 39, 60]                             # Gamma values corresponding to risk appetites
RISK_LABELS = ['high', 'medium','low']                          # Different portfolio risk levels
RISK_APP_DICT = dict(zip(RISK_LABELS, RISK_PROFILE_INDICES))    # Dict tying gamma values to risk levels

