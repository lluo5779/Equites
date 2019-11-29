import numpy as np

from scipy.stats import norm


APPROX_BDAYS_PER_MONTH = 21
APPROX_BDAYS_PER_YEAR = 252

MONTHS_PER_YEAR = 12
WEEKS_PER_YEAR = 52


# CALL THIS
def drawdown_underwater(returns):

    df_cum_rets = cum_returns(returns, starting_value=1.0)
    running_max = np.maximum.accumulate(df_cum_rets)
    underwater = -100 * ((running_max - df_cum_rets) / running_max)

    return underwater


# CALL THIS
def drawdown_table(returns, top=10):
    drawdown_periods = get_top_drawdowns(returns, top=top)
    df_drawdowns = pd.DataFrame(index=list(range(top)),
                                columns=['Net drawdown in %',
                                         'Peak date',
                                         'Valley date',
                                         'Recovery date',
                                         'Duration'])

    for i, (peak, valley, recovery) in enumerate(drawdown_periods):
        if pd.isnull(recovery):
            df_drawdowns.loc[i, 'Duration'] = np.nan
        else:
            df_drawdowns.loc[i, 'Duration'] = len(pd.date_range(peak,
                                                                recovery,
                                                                freq='B'))
        df_drawdowns.loc[i, 'Peak date'] = (peak.to_pydatetime()
                                            .strftime('%Y-%m-%d'))
        df_drawdowns.loc[i, 'Valley date'] = (valley.to_pydatetime()
                                              .strftime('%Y-%m-%d'))
        if isinstance(recovery, float):
            df_drawdowns.loc[i, 'Recovery date'] = recovery
        else:
            df_drawdowns.loc[i, 'Recovery date'] = (recovery.to_pydatetime()
                                                    .strftime('%Y-%m-%d'))
        df_drawdowns.loc[i, 'Net drawdown in %'] = (
            (df_cum.loc[peak] - df_cum.loc[valley]) / df_cum.loc[peak]) * 100

    df_drawdowns['Peak date'] = pd.to_datetime(df_drawdowns['Peak date'])
    df_drawdowns['Valley date'] = pd.to_datetime(df_drawdowns['Valley date'])
    df_drawdowns['Recovery date'] = pd.to_datetime(df_drawdowns['Recovery date'])

    return df_drawdowns


def get_top_drawdowns(returns, top=10):
    # List of drawdown peaks, valleys, and recoveries

    returns = returns.copy()
    df_cum = cum_returns(returns, 1.0)
    running_max = np.maximum.accumulate(df_cum)
    underwater = df_cum / running_max - 1

    drawdowns = []
    for t in range(top):
        peak, valley, recovery = get_max_drawdown_underwater(underwater)

        if not pd.isnull(recovery):
            underwater.drop(underwater[peak: recovery].index[1:-1],
                            inplace=True)
        else:
            underwater = underwater.loc[:peak]

        drawdowns.append((peak, valley, recovery))
        if (len(returns) == 0) or (len(underwater) == 0):
            break

    return drawdowns


def get_max_drawdown_underwater(underwater):
    valley = np.argmin(underwater)
    peak = underwater[:valley][underwater[:valley] == 0].index[-1]

    try:
        recovery = underwater[valley:][underwater[valley:] == 0].index[0]
    except IndexError:
        recovery = np.nan  # drawdown not recovered
    
    return peak, valley, recovery


def get_max_drawdown(returns):
    returns = returns.copy()
    df_cum = cum_returns(returns, 1.0)
    running_max = np.maximum.accumulate(df_cum)
    underwater = df_cum / running_max - 1
    
    return get_max_drawdown_underwater(underwater)


def rolling_volatility(returns, rolling_vol_window):
    # input: daily portfolio returns, dataframe
    # input: window, int
    # output: pd.Series for rolling vols
    return returns.rolling(rolling_vol_window).std() \
        * np.sqrt(APPROX_BDAYS_PER_YEAR)


def rolling_sharpe(returns, rolling_sharpe_window):
    # input: daily portfolio returns, dataframe
    # input: window, int
    # output: pd.Series for rolling sharpe
    return returns.rolling(rolling_sharpe_window).mean() \
        / returns.rolling(rolling_sharpe_window).std() \
        * np.sqrt(APPROX_BDAYS_PER_YEAR)


def ret(mu, x):
    return float(mu.T.dot(x).values)


def cum_returns(returns, starting_value=0, out=None):
    if len(returns) < 1:
        return returns.copy()

    nanmask = np.isnan(returns)
    if np.any(nanmask):
        returns = returns.copy()
        returns[nanmask] = 0

    allocated_output = out is None
    if allocated_output:
        out = np.empty_like(returns)

    np.add(returns, 1, out=out)
    out.cumprod(axis=0, out=out)

    if starting_value == 0:
        np.subtract(out, 1, out=out)
    else:
        np.multiply(out, starting_value, out=out)

    if allocated_output:
        if returns.ndim == 1 and isinstance(returns, pd.Series):
            out = pd.Series(out, index=returns.index)
        elif isinstance(returns, pd.DataFrame):
            out = pd.DataFrame(
                out, index=returns.index, columns=returns.columns,
            )

    return out


def vol(cov, x):
    try:
        return float(np.sqrt(x.T.dot(cov).dot(x)).values)
    except:
        return float(np.sqrt(x.T.dot(cov).dot(x)))



def var(mu, cov, alpha, x):
    try:
        return float(-mu.T.dot(x).values - norm.ppf(alpha) * np.sqrt(x.T.dot(cov).dot(x)).values)
    except:
        return float(-mu.T.dot(x).values - norm.ppf(alpha) * np.sqrt(x.T.dot(cov).dot(x)))


def cvar(mu, cov, alpha, x):
    try:
        return float(-mu.T.dot(x).values - norm.pdf(norm.ppf(alpha)) / alpha * np.sqrt(x.T.dot(cov).dot(x)).values)
    except:
        return float(-mu.T.dot(x).values - norm.pdf(norm.ppf(alpha)) / alpha * np.sqrt(x.T.dot(cov).dot(x)))


