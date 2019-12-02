import numpy as np
import pandas as pd


def risk_prefs(horizon, aversion, cardinal, return_target, l, mu_bl1, mu_bl2, cov_bl1):

    if horizon is None:
        horizon = 10

    alpha = 0.05

    safe_target = float(((mu_bl1 + mu_bl2) / 2).mean())

    # set the variances for the first period estimates
    vars = pd.DataFrame(np.diag(cov_bl1), index=cov_bl1.index)

    risk_mul, turn_mul = l, 1

    if horizon <= 1:
        # select the 12 assets with the lowest variances
        risk_mul *= 2
        turn_mul *= 0.25
        alpha = 0.20

    elif horizon <= 5:
        risk_mul *= 0.75
        turn_mul *= 1
        alpha = 0.10

    else:
        risk_mul *= 0.25
        turn_mul *= 2


    print("RISK PREFERENCES\n\n\n")
    if return_target > safe_target:
        risk_mul *= 0.5

    if aversion == 1:
        cardinality = list(np.where(mu_bl1.rank() > len(mu_bl1) - cardinal, 1, 0).ravel())
        exposures = (0.02, 0.30)
    elif aversion == 2:
        cardinality = list(np.where(pd.DataFrame(np.divide(mu_bl1.values, vars.values).ravel()).rank() > len(mu_bl1) - cardinal, 1, 0).ravel())
        exposures = (0.04, 0.20)
    else:
        # NO SINGLE NAME STOCKS
        vars = pd.DataFrame(np.diag(cov_bl1.iloc[:-10, :-10]), index=mu_bl1[:-10].index)
        cardinality = list(np.where(vars.rank(ascending=True) > (len(mu_bl1[:-10])- cardinal), 1, 0).ravel()) + [0]*10
        exposures = (0.05, 0.15)

    risk_mul *= aversion

    return (alpha, alpha*1.02), (risk_mul, turn_mul), exposures, cardinality
