import os
from config import db
from database.models import User
from database.tiingo import getEndOfDayPrices
from datetime import date, timedelta

# Create the database
db.create_all()


def populateTickers(symbols):

    resampleFreq="monthly"
    startDate = (date.today() - timedelta(days=6*365)).isoformat()
    print('today is: ', startDate)
    endDate = date.today().isoformat()


    eodPrices_df = getEndOfDayPrices(symbols=symbols,
                                 startDate=startDate,
                                 endDate=endDate,
                                 freq=resampleFreq)
    eodPrices_df.to_sql('EodPrices-Assets', con = db.engine, if_exists = "replace", index=True)

symbols = ['IVV', 'SPDW', 'SPEM', # Market-cap Equity
           'SPYD', 'SPFF', 'VTEB', 'SPXB', # Income Solutions
           'XLC','XLY','XLE','XLF','XLV','XLI','XLB','XLRE','XLK','XLU', # Sector Solutions
           'SNPE','SPYX','ICLN','CGW','GRNB'# Thematic
           ]

populateTickers(symbols)

# iterate over the PEOPLE structure and populate the database
# for person in PEOPLE:
#     p = Person(lname=person.get("lname"), fname=person.get("fname"))
#     db.session.add(p)
#
# db.session.commit()
