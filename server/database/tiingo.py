import requests
from utils import *
from pandas_datareader import tiingo
from datetime import date, timedelta

today = date.today()
date_6months = date.today() - timedelta(6*365/12)


def initTiingoDailyReader(symbols, start = getFormattedDate(date_6months), end = getFormattedDate(today), api_key = None):
    print("Initializing Tiingo reader with start {} and end {}".format(start, end))

    return tiingo.TiingoDailyReader(
        symbols, start=start, end=end, api_key=api_key
    )

# symbols = ['AAPL', 'ACN']
def getEndOfDayPrices(symbols):
    token = "2e64578d69892c20fab750efe3ae9ed176f7c1af"
    start = getFormattedDate(date_6months)
    end = getFormattedDate(today)
    df = initTiingoDailyReader(symbols, start=start, end=end, api_key=token).read()
    return df




# if __name__ == '__main__':
#     token = "2e64578d69892c20fab750efe3ae9ed176f7c1af"
#     symbols = ['AAPL', 'ACN']
#     startDate = "2012-1-1"
#     endDate = "2016-1-1"
#     # reader = initTiingoDailyReader(symbols,api_key=token)
#     # print(type(reader.read()))
#     print(getEndOfDayPrices(symbols))





    def getEndofDayPriceAPI(
            method = "get",
            ticker = 'AAPL',
            startDate="2012-1-1",
            endDate="2016-1-1",
            format="json",
            resampleFreq="monthly",
            token="2e64578d69892c20fab750efe3ae9ed176f7c1af"):

        url = "https://api.tiingo.com/tiingo/daily/{}/prices?startDate={}&endDate={}&format={}&resampleFreq={}&token={}"\
            .format(ticker,startDate, endDate, format, resampleFreq, token)
        print("fetching from :", url)
        data = ''''''
        if (method == "get"):
            response = requests.get(url, data=data)
            print("Request successful: ", url)
        else:
            print("Your method is not supported at this moment.")
        response = response.json()
        return convertTiingoResponseToDF(response)
