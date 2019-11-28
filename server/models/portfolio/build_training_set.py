import pandas as pd 
import numpy as np 
from datetime import datetime
from scipy.stats.mstats import gmean
from dateutil.relativedelta import relativedelta
import os

from server.models.portfolio.stats import *
from server.models.portfolio.cost import costs
from server.models.portfolio.tiingo import get_data
from server.models.portfolio.optimize import optimize
from server.models.portfolio.bl import bl, get_mkt_cap
from server.models.portfolio.rs import fama_french, regime_switch, current_regime, business_days, expected_returns, covariance

tickers = list(pd.read_csv(os.getcwd() + r'/data/tickers.csv')['Tickers'])

def run_optimization(end_date, start_date, prices, factors):
	rebalance_date = (datetime.strptime(end_date, "%Y-%m-%d") + relativedelta(months=6, days=1)).strftime("%Y-%m-%d")
	rebalance_date = datetime.strftime(pd.bdate_range(end_date, rebalance_date)[-1], "%Y-%m-%d")
	#prices = get_data(tickers, 'adjClose', start_date, end_date, save=False)
	print(prices.shape)
	#factors = fama_french(start_date, end_date, save=False)
	print(factors.shape)
	returns = (prices / prices.shift(1) - 1).dropna()[:len(factors)]
	R = returns.values
	
	## *********************************************************************************************************************
	#  factor model
	## *********************************************************************************************************************

	factors.drop('RF', axis=1, inplace=True)
	F = np.hstack((np.atleast_2d(np.ones(factors.shape[0])).T, factors))
	transmat, loadings, covarainces = regime_switch(R, F, tickers)
	baseline = 30
	regime = current_regime(R, F, loadings, baseline)


	# get the number of days until the next scheduled rebalance
	days = business_days((datetime.strptime(end_date, "%Y-%m-%d") + relativedelta(days=1)).strftime("%Y-%m-%d"), rebalance_date)

	# get the estimate returns and covariances from the factor model
	mu_rsfm = pd.DataFrame(days * expected_returns(F, transmat, loadings, regime), index=tickers, columns=['returns'])
	cov_rsfm = pd.DataFrame(days * covariance(R, F, transmat, loadings, covarainces, regime), index=tickers, columns=tickers)

	# write estimates to a csv file
	mu_rsfm.to_csv(os.getcwd() + r'/data/mu_rsfm.csv')
	cov_rsfm.to_csv(os.getcwd() + r'/data/cov_rsfm.csv')
	mktcap = get_mkt_cap(tickers, save=True)

	# calculate the market coefficient
	l = (gmean(factors.iloc[-days:,:]['MKT'] + 1,axis=0) - 1)/factors.iloc[-days:,:]['MKT'].var()

	mu_bl1, cov_bl1 = bl(tickers=tickers,
	                     l=l, tau=1,
	                     mktcap=mktcap,
	                     Sigma=returns.iloc[-days:,:].cov().values * days,
	                     P=np.identity(len(tickers)),
	                     Omega=np.diag(np.diag(cov_rsfm)),
	                     q=mu_rsfm.values,
	                     adjust=False)

	mu_ml = mu_bl1.mul(pd.DataFrame(1 + np.random.uniform(-0.05, 0.1, len(tickers)), index=mu_bl1.index, columns=mu_bl1.columns))

	mu_bl2, cov_bl2 = bl(tickers=tickers,
	                     l=l, tau=1,
	                     mktcap=mktcap,
	                     Sigma=returns.iloc[-days:,:].cov().values * days,
	                     P=np.identity(len(tickers)),
	                     Omega=np.diag(np.diag(cov_rsfm)),
	                     q=mu_ml.values,
	                     adjust=True)

	cost = costs(tickers=tickers,
	             cov=cov_rsfm,
	             prices=prices.iloc[-2, :] if prices.iloc[-1, :].isnull().values.any() else prices.iloc[-1, :],
	             start_date=(datetime.strptime(end_date, "%Y-%m-%d") - relativedelta(years=1)).strftime("%Y-%m-%d"),
	             end_date=end_date,
	             alpha=5)

	risk_tolerance = [((1, 10), (0, 0.10)),
                  ((5, 5), (0, 0.20)),
                  ((10, 1), (-0.05, 0.30))]

	soln = optimize(mu = (mu_bl1.values.ravel(), mu_bl2.values.ravel()),
	                sigma = (cov_bl1.values, cov_bl2.values),
	                alpha = (0.05, 0.10),
	                return_target = (0.05, 0.05),
	                costs = cost,
	                prices = prices.iloc[-2, :].values if prices.iloc[-1, :].isnull().values.any() else prices.iloc[-1, :].values,
	                gamma = risk_tolerance[2])

	x1 = pd.DataFrame(soln.x[:int(len(mu_bl1))], index=mu_bl1.index, columns=['weight'])
	x2 = pd.DataFrame(soln.x[int(len(mu_bl2)):], index=mu_bl2.index, columns=['weight'])
	print('\n\n********************************************************************')
	print('\tperiod one results')
	print('********************************************************************\n')

	#print(x1)

	print("\nportfolio return: %f" % (ret(mu_bl1, x1) * 100))
	print("portfolio volatility: %f" % (vol(cov_bl1, x1) * 100))
	print("portfolio var%f: %f" % (1-0.05, var(mu_bl1, cov_bl1, 0.05, x1)))
	print("portfolio cvar%f: %f" % (1-0.05, cvar(mu_bl1, cov_bl1, 0.05, x1)))


	print('\n\n********************************************************************')
	print('\tperiod two results')
	print('********************************************************************\n')

	#print(x2)

	print("\nportfolio return: %f" % (ret(mu_bl2, x1) * 100))
	print("portfolio volatility: %f" % (vol(cov_bl2, x1) * 100))
	print("portfolio var%f: %f" % (1-0.05, var(mu_bl2, cov_bl2, 0.05, x1)))
	print("portfolio cvar%f: %f" % (1-0.05, cvar(mu_bl2, cov_bl2, 0.05, x1)))

	return (ret(mu_bl1, x1) * 100), (ret(mu_bl2, x1) * 100)

def cycle_days():
	training_list = []
	end_date = datetime.now().strftime("%Y-%m-%d")
	start_date = (datetime.strptime(end_date, "%Y-%m-%d") - relativedelta(years=6)).strftime("%Y-%m-%d")
	training_start_date = (datetime.strptime(end_date, "%Y-%m-%d") - relativedelta(years=8)).strftime("%Y-%m-%d")
	#prices = get_data(tickers, 'adjClose', training_start_date, end_date, save=False)
	#factors = fama_french(training_start_date, end_date, save=False)
	while start_date < end_date:
		print(start_date, training_start_date)
		prices = get_data(tickers, 'adjClose', training_start_date, start_date, save=False)
		factors = fama_french(training_start_date, start_date, save=False)
		#fix dat errors without try except
		#new_prices = prices.loc[training_start_date:start_date]
		#new_factors = factors.loc[training_start_date:start_date]
		return1, return2 = run_optimization(start_date, training_start_date, prices, factors)
		training_list.append([start_date, return1, return2])
		start_date = (datetime.strptime(start_date,"%Y-%m-%d") + relativedelta(days = 1)).strftime("%Y-%m-%d")
		training_start_date = (datetime.strptime(training_start_date,"%Y-%m-%d") + relativedelta(days = 1)).strftime("%Y-%m-%d")
	
		training_data = pd.DataFrame(training_list,columns = ['Date', 'return1', 'return2']).set_index('Date')
		training_data.to_csv('training_data.csv')

def get_prices():
	end_date = datetime.now().strftime("%Y-%m-%d")
	start_date = (datetime.strptime(end_date, "%Y-%m-%d") - relativedelta(years=6)).strftime("%Y-%m-%d")
	#mapping = {'ITOT': 'prices', 'DIA': 'prices', 'SPY': 'prices', 'XLG': 'prices', 'AIA': 'prices', 'GXC': 'prices', 'XLY': 'prices',
	#		   'XLE': 'prices', 'XLF': 'prices', 'XLV': 'prices', 'XLI': 'prices', 'XLB': 'prices', 'XLK': 'prices', 'XLU': 'prices', 
	#		   'ICLN': 'prices', 'CGW': 'prices', 'WOOD': 'prices', 'IYR': 'prices'}
	prices = get_data(tickers, 'adjClose', start_date, end_date, save=False)
	prices['prices'] = prices.apply(lambda x: ','.join(x.astype(str)), axis = 1)
	prices['prices'] = prices['prices'].apply(lambda x: [float(y) for y in x.split(',')])
	prices.to_csv('prices.csv')
get_prices()