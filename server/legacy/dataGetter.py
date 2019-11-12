import pandas as pd
from datetime import date

def getSth(db):
    return pd.read_sql(('select "symbol","date", "adjClose" from "EodPrices-All" '
                     'where "date" BETWEEN %(dstart)s AND %(dfinish)s'),
                   db.engine,params={"dstart":date(2019, 5, 1),"dfinish":date(2019, 7, 1)})

