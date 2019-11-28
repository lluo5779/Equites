import os
import pandas as pd

from datetime import datetime
from scipy.stats.mstats import gmean
from dateutil.relativedelta import relativedelta

from server.models.portfolio.sent_analysis import SentimentAnalysis, predict
from server.models.portfolio.stats import *
from server.models.portfolio.cost import costs
from server.models.stock.tiingo import get_data
from server.models.factors.fama import fama_french
from server.models.portfolio.risk import risk_prefs
from server.models.portfolio.optimize import optimize
from server.models.portfolio.bl import bl, get_mkt_cap
from server.models.portfolio.rs import regime_switch, current_regime, business_days, expected_returns, covariance

from server.models.portfolio.config import SYMBOLS

BASEPATH = "/server/models/portfolio/"
## *********************************************************************************************************************
# parameters
## *********************************************************************************************************************

tickers = SYMBOLS
N = len(tickers)

end_date = datetime.now().strftime("%Y-%m-%d")
start_date = (datetime.strptime(end_date, "%Y-%m-%d") - relativedelta(years=6)).strftime("%Y-%m-%d")

# target rebalance date ... based on calendar days ... need to adjust for trading days
rebalance_date = (datetime.strptime(end_date, "%Y-%m-%d") + relativedelta(months=6, days=1)).strftime("%Y-%m-%d")
rebalance_date = datetime.strftime(pd.bdate_range(end_date, rebalance_date)[-1], "%Y-%m-%d")

np.set_printoptions(precision=4)


## *********************************************************************************************************************
#  pull the factors and asset prices
## *********************************************************************************************************************

print('\n\n********************************************************************')
print('\tretrieving asset prices')
print('********************************************************************')

prices = get_data(tickers, 'adjClose', start_date, end_date, save=True, fail_safe=True) #Stored
print(prices.tail(10))

print('\n\n********************************************************************')
print('\tretrieving factor data')
print('********************************************************************')

factors = fama_french(start_date, end_date, save=True)
print(factors.tail(10))


print('\n\n********************************************************************')
print('risk adjusted returns')
print('********************************************************************')

returns = (prices / prices.shift(1) - 1).dropna()[:len(factors)] #Stored
R = (returns.values - factors['RF'].values[:, None])  #Stored
print(pd.DataFrame(R, index=factors.index, columns=prices.columns).tail(10))


## *********************************************************************************************************************
#  factor model
## *********************************************************************************************************************

factors.drop('RF', axis=1, inplace=True)
F = np.hstack((np.atleast_2d(np.ones(factors.shape[0])).T, factors))

print('\n\n********************************************************************')
print('\tfitting the factor model')
print('********************************************************************')

transmat, loadings, covarainces = regime_switch(R, F, tickers) #Stored

#transmat - dataframe?
#loadings - np array
#cov

print('\n\ntransition matrix')
print(transmat)

for i in range(2):
    print('\n\nregime %d' % (i + 1))

    print('\nfactor loadings matrix')
    print(loadings[i])

    print("\ncovariance matrix")
    print(covarainces[i])

# see what regime best fits the most recent data (# days = baseline)
baseline = 30
regime = current_regime(R, F, loadings, baseline)
print('\nbased on the last %d trading days, the best fitted regime is %d' % (baseline, regime))


## *********************************************************************************************************************
#  expeceted mean and variances from the factor model
## *********************************************************************************************************************

print('\n\n********************************************************************')
print('\tcalculating period one estimates')
print('********************************************************************')

# get the number of days until the next scheduled rebalance
days = business_days((datetime.strptime(end_date, "%Y-%m-%d") + relativedelta(days=1)).strftime("%Y-%m-%d"), rebalance_date)

# get the estimate returns and covariances from the factor model
mu_rsfm = pd.DataFrame(days * expected_returns(F, transmat, loadings, regime), index=tickers, columns=['returns'])
cov_rsfm = pd.DataFrame(days * covariance(R, F, transmat, loadings, covarainces, regime), index=tickers, columns=tickers)

# write estimates to a csv file
mu_rsfm.to_csv(os.getcwd() + BASEPATH + r'/data/mu_rsfm.csv')
cov_rsfm.to_csv(os.getcwd() +BASEPATH +  r'/data/cov_rsfm.csv')

print('\nexpected returns from the factor model')
print(mu_rsfm)

print('\nexpected covariance from the factor model')
print(cov_rsfm)




## *********************************************************************************************************************
#  black litterman for period one returns
## *********************************************************************************************************************

mktcap = get_mkt_cap(tickers, save=True) #Stored Daily

print("\nmarket cap data")
print(mktcap)

# calculate the market coefficient
l = (gmean(factors.iloc[-days:,:]['MKT'] + 1,axis=0) - 1)/factors.iloc[-days:,:]['MKT'].var() #Stored

mu_bl1, cov_bl1 = bl(tickers=tickers,
                     l=l, tau=1,
                     mktcap=mktcap,
                     Sigma=returns.iloc[-days:,:].cov().values * days,
                     P=np.identity(len(tickers)),
                     Omega=np.diag(np.diag(cov_rsfm)),
                     q=mu_rsfm.values,
                     adjust=False) #Stored

print('\nperiod one returns')
print(mu_bl1)

print('\nperiod one covariances')
print(cov_bl1)


## *********************************************************************************************************************
#  AIDAN ML ... pass along a new returns dataframe, mu_ml, with the same format as mu_rsfm
## *********************************************************************************************************************

print('\n\n********************************************************************')
print('\tcalculating period two estimates')
print('********************************************************************')

# temp mu_ml
mu_ml = predict()


## *********************************************************************************************************************
#  black litterman for period two returns
## *********************************************************************************************************************

mu_bl2, cov_bl2 = bl(tickers=tickers,
                     l=l, tau=1,
                     mktcap=mktcap,
                     Sigma=returns.iloc[-days:,:].cov().values * days,
                     P=np.identity(len(tickers)),
                     Omega=np.diag(np.diag(cov_rsfm)),
                     q=mu_ml.values,
                     adjust=True) #Stored inputs to optimization

print('\nperiod two returns')
print(mu_bl2)

print('\nperiod two covariances')
print(cov_bl2)


## *********************************************************************************************************************
#  calculate transaction cost coefficients
## *********************************************************************************************************************

print('\n\n********************************************************************')
print('\tcalculating cost coefficients')
print('********************************************************************')

cost = costs(tickers=tickers,
             cov=cov_rsfm,
             prices=prices.iloc[-2, :] if prices.iloc[-1, :].isnull().values.any() else prices.iloc[-1, :],
             start_date=(datetime.strptime(end_date, "%Y-%m-%d") - relativedelta(years=1)).strftime("%Y-%m-%d"),
             end_date=end_date,
             alpha=5) #Stored

print('\ncost coefficients')
print(cost)


## *********************************************************************************************************************
#  risk preferences
## *********************************************************************************************************************

# in years
horizon = 10

# target goal amount in dollars
target_dollars, initial_dollars = 1300, 1250

# low 1, medium 2, high = 3
aversion = 3

return_target = (target_dollars / initial_dollars) ** (1 / (2 * horizon)) - 1

alpha, multipliers, exposures, cardinality = risk_prefs(horizon, aversion, initial_dollars, target_dollars, l, mu_bl1, mu_bl2, cov_bl1)

# assign the risk tolerances
risk_tolerance = (multipliers, exposures, cardinality, 'MCVAR')


## *********************************************************************************************************************
#  optimization
## *********************************************************************************************************************

print('\n\n********************************************************************')
print('\toptimization')
print('********************************************************************')

soln, agg_soln = optimize(mu = (mu_bl1.values.ravel(), mu_bl2.values.ravel()),
                          sigma = (cov_bl1.values, cov_bl2.values),
                          alpha = (alpha, alpha * 1.02),
                          return_target = (return_target, return_target),
                          costs = cost,
                          prices = prices.iloc[-2, :].values if prices.iloc[-1, :].isnull().values.any() else prices.iloc[-1, :].values,
                          gamma = risk_tolerance)

x1 = pd.DataFrame(soln.x[:int(len(mu_bl1))], index=mu_bl1.index, columns=['weight'])
x2 = pd.DataFrame(soln.x[int(len(mu_bl2)):], index=mu_bl2.index, columns=['weight'])


print('\n\n********************************************************************')
print('\tperiod one results')
print('********************************************************************\n')

print(x1)

print("\nportfolio return: %f" % (ret(mu_bl1, x1) * 100))
print("portfolio volatility: %f" % (vol(cov_bl1, x1) * 100))
print("portfolio var%f: %f" % (1-0.05, var(mu_bl1, cov_bl1, 0.05, x1)))
print("portfolio cvar%f: %f" % (1-0.05, cvar(mu_bl1, cov_bl1, 0.05, x1)))


print('\n\n********************************************************************')
print('\tperiod two results')
print('********************************************************************\n')

print(x2)

print("\nportfolio return: %f" % (ret(mu_bl2, x1) * 100))
print("portfolio volatility: %f" % (vol(cov_bl2, x1) * 100))
print("portfolio var%f: %f" % (1-0.05, var(mu_bl2, cov_bl2, 0.05, x1)))
print("portfolio cvar%f: %f" % (1-0.05, cvar(mu_bl2, cov_bl2, 0.05, x1)))