import os
from config import db
from models import User, FactorModel
from tiingo import getEndOfDayPrices
# Create the database
db.create_all()


def populateTickers(ticker):

    method = "get"
    format="json"
    resampleFreq="monthly"

    eodPrices_df = getEndOfDayPrices(['AAPL', 'ACN'])
    # eodPrices_df = getEndOfDayPrice(method=method,
    #                              ticker=ticker,
    #                              startDate=startDate,
    #                              endDate=endDate,
    #                              format=format,
    #                              resampleFreq=resampleFreq)
    eodPrices_df.to_sql('EodPrices-' + ticker, con = db.engine, if_exists = "replace", index=True)
token = "2e64578d69892c20fab750efe3ae9ed176f7c1af"

symbols = ['AAPL', 'ACN']
# startDate = "2012-1-1"
# endDate = "2016-1-1"
# reader = initTiingoDailyReader(symbols,api_key=token)
# print(help(reader.read()))

ticker = 'AAPL'
startDate="2012-1-1"
endDate="2016-1-1"
populateTickers("All")

# iterate over the PEOPLE structure and populate the database
# for person in PEOPLE:
#     p = Person(lname=person.get("lname"), fname=person.get("fname"))
#     db.session.add(p)
#
# db.session.commit()
