from server.common.database import Database
from server.models.portfolio.portfolio import get_past_portfolios
import pandas as pd
import datetime


def fetch_latest_questionnaire_from_type(option_type):
    """Called when portfolio name has not been declared by the user (ie. from portfolioview edit button)"""
    if option_type is None:
        return {}

    if "_questionnaire" not in option_type:
        option_type = option_type + "_questionnaire"

    df = pd.read_sql('select * from {} order by "timestamp" asc;'.format(option_type),
                    Database.DATABASE.engine, index_col='uuid')
    print("df", df)
    if len(df) != 1:
        df = df.iloc[0]
    return df



def fetch_questionnaire_from_uuid_and_type(option_type, uuid):
    """Called when selecting specific portfolio (ie. from port dashboard)"""
    if "_questionnaire" not in option_type:
        option_type = option_type + "_questionnaire"
    option_type = option_type.lower()
    query ="""select * from {} where "uuid" like '{}';""".format(option_type, uuid)

    df =  pd.read_sql(query,
                       Database.DATABASE.engine, index_col='uuid')
    print("df", df)
    if len(df) != 1:
        df = df.iloc[0]
    return df

def initialize_new_questionnaire(questionnaire, option_type, uuid):
    """Insert new questionnaire when user clicks save"""
    q = {}
    if (type(questionnaire) == dict):
        for key, val in questionnaire.items():
            if key != 'index':

                q[key] = [val] if type(val) != list else val
        questionnaire = pd.DataFrame(q)


    if "_questionnaire" not in option_type:
        option_type = option_type + "_questionnaire"

    option_type = option_type.lower()
    if 'option_type' not in questionnaire:
        questionnaire['option_type'] = [option_type]
    questionnaire['uuid'] = [uuid]
    questionnaire['timestamp'] = [datetime.datetime.utcnow()]
    print("this is questionaire: ", questionnaire)

    questionnaire=questionnaire.set_index('uuid')
    print("this is questionaire: ", questionnaire)
    questionnaire.to_sql(option_type, con=Database.DATABASE.engine, if_exists="append", index=True)


def update_new_questionnaire(questionnaire, option_type, uuid):
    if type(questionnaire) != dict:
        raise TypeError("Please supply a dictionary to update new questionnaire")

    if "_questionnaire" not in option_type:
        option_type = option_type + "_questionnaire"

    questionnaire['option_type'] = [option_type]

    option_type = option_type.lower()
    query = 'select * from {}'.format(option_type)
    old_df = pd.read_sql(query, con=Database.DATABASE.engine, index_col='uuid')
    # if 'level_0' in old_df.columns:
    #     old_df = old_df.drop(['level_0'], axis=1)
    # if 'index' in old_df.columns:
    #     old_df = old_df.drop(['index'], axis=1)


    print('old_df: \n', old_df)
    print(uuid)

    """When user edits an existing question naire"""

    old_df.loc[uuid, list(questionnaire.keys())] = list(questionnaire.values())
    print("Database row after upsert from some uuid: ", old_df.loc[uuid])
    old_df.to_sql(name=option_type, con=Database.DATABASE.engine, if_exists="replace", index=True)

    print("Successfully updated questionnaire database")


def fetch_all_questionnaires(username):
    portfolio_table = get_past_portfolios(username, get_all=True)[2]
    wealth_ids = list(portfolio_table[portfolio_table['portfolio_type'] == 'Wealth'].index)
    purchase_ids = list(portfolio_table[portfolio_table['portfolio_type'] == 'Purchase'].index)
    retirement_ids = list(portfolio_table[portfolio_table['portfolio_type'] == 'Retirement'].index)

    _ids = {'wealth_questionnaire': wealth_ids, 'purchase_questionnaire': purchase_ids,
            'retirement_questionnaire': retirement_ids}

    questionnaires = {}
    for key, ids in _ids.items():
        query = """select * from {} where "uuid" in {}""".format(key, "('" + "', '".join(ids) + "')")
        questionnaires[key] = pd.read_sql(query, con=Database.DATABASE.engine, index_col='uuid')
        questionnaires[key] = pd.concat([questionnaires[key], portfolio_table[portfolio_table.index.isin(ids)]['portfolio_name']], axis=1)

    df_to_display = pd.DataFrame(columns = ['portfolioName', 'budget', 'target', 'end_date', 'optionType'])
    for q_name, q_df in questionnaires.items():
        if 'purchase' in q_name:
            vals = ['portfolio_name', 'initialInvestment', 'purchaseAmount', 'purchaseDate']
            df_ = q_df[vals]
            df_['optionType'] = 'purchase'
        elif 'retirement' in q_name:
            vals = ['portfolio_name', 'initialInvestment', 'retirementAmount', 'retirementDate']
            df_ = q_df[vals]
            df_['optionType'] = 'retirement'
        else:
            vals = ['portfolio_name', 'initialInvestment']
            df_ = q_df[vals]
            df_['tmp1'] = ""
            df_['tmp2'] = ""
            df_['optionType'] = 'wealth'


        df_.columns = ['portfolioName','budget', 'target', 'end_date', 'optionType']
        df_to_display = pd.concat([df_to_display, df_], axis=0, join='outer', ignore_index=False, keys=None,
                                  levels=None, names=None, verify_integrity=False, copy=True)

    return df_to_display