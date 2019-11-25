from datetime import date, timedelta

COLLECTION = 'prices'                                       # MongoDB collection
SYMBOLS = ['ITOT', 'DIA', 'SPY', 'XLG', 'AIA', 'GXC', 'XLY', 'XLE', 'XLF', 'XLV', 'XLI', 'XLB', 'XLK', 'XLU', 'ICLN', 'CGW', 'WOOD', 'IYR']

SAMPLE_FREQUENCY = 'monthly'
START_DATE = (date.today() - timedelta(days=6*365)).isoformat()
END_DATE = date.today().isoformat()
RISK_PROFILE_INDICES = [32, 39, 60]                             # Gamma values corresponding to risk appetites
RISK_LABELS = ['high', 'medium','low']                          # Different portfolio risk levels
RISK_APP_DICT = dict(zip(RISK_LABELS, RISK_PROFILE_INDICES))    # Dict tying gamma values to risk levels
TIINGO_TOKEN = frozenset({"2e64578d69892c20fab750efe3ae9ed176f7c1af"})

