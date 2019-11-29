from datetime import date, timedelta

COLLECTION = 'user_portfolio'                                       # MongoDB collection
SYMBOLS = ['ITOT', 'DIA', 'SPY', 'XLG', 'AIA', 'GXC', 'XLY', 'XLE', 'XLF', 'XLV', 'XLI', 'XLB', 'XLK', 'XLU', 'ICLN', 'CGW', 'WOOD', 'IYR', 'F', 'DIS', 'MCD', 'KO', 'PEP', 'JPM', 'AAPL', 'PFE', 'JNJ', 'ED', 'F2', 'DIS2', 'MCD2', 'KO2', 'PEP2', 'JPM2', 'AAPL2', 'PFE2', 'JNJ2', 'ED2']

START_DATE = (date.today() - timedelta(days=10*365)).isoformat()
END_DATE = date.today().isoformat()
RISK_PROFILE_INDICES = [32, 39, 60]                             # Gamma values corresponding to risk appetites
RISK_LABELS = ['high', 'medium','low']                          # Different portfolio risk levels
RISK_APP_DICT = dict(zip(RISK_LABELS, RISK_PROFILE_INDICES))    # Dict tying gamma values to risk levels

