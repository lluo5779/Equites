import pandas as pd
from collections import Counter

def convertTiingoResponseToDF(resp):
    col_names= resp[0].keys()
    dict = Counter()

    for entry in resp:
        for col in col_names:
            if (dict[col] == 0):
                dict[col] = []
            dict[col].append(entry[col])
    df = pd.DataFrame(dict)
    return df

def getFormattedDate(date):
    "2012-1-1"
    return date.strftime("%Y-%m-%d")
