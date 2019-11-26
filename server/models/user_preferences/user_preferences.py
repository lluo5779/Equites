from server.common.database import Database
import pandas as pd
import datetime


def fetch_latest_questionnaire_from_type(option_type):
    """Called when portfolio name has not been declared by the user (ie. from portfolioview edit button)"""
    if "_questionnaire" not in option_type:
        option_type = option_type + "_questionnaire"

    df = pd.read_sql('select * from {} order by "timestamp" asc;'.format(option_type),
                    Database.DATABASE.engine)
    print("df", df)
    if len(df) != 1:
        df = df.iloc[0]
    return df



def fetch_questionnaire_from_uuid_and_type(option_type, uuid):
    """Called when selecting specific portfolio (ie. from port dashboard)"""
    if "_questionnaire" not in option_type:
        option_type = option_type + "_questionnaire"
    query ="""select * from '{}' where "uuid" like '{}';""".format(option_type, uuid)

    df =  pd.read_sql(query,
                       Database.DATABASE.engine, index_col='index')
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

    if 'option_type' not in questionnaire:
        questionnaire['option_type'] = [option_type]
    questionnaire['uuid'] = [uuid]
    questionnaire['timestamp'] = [datetime.datetime.utcnow()]
    print("this is questionaire: ", questionnaire)

    questionnaire=questionnaire.set_index('uuid')
    print("this is questionaire: ", questionnaire)
    questionnaire.to_sql(option_type, con=Database.DATABASE.engine, if_exists="append")


def update_new_questionnaire(questionnaire, option_type, uuid):
    if type(questionnaire) != dict:
        raise TypeError("Please supply a dictionary to update new questionnaire")

    if "_questionnaire" not in option_type:
        option_type = option_type + "_questionnaire"

    if 'option_type' not in questionnaire:
        questionnaire['option_type'] = [option_type]

    query = 'select * from {}'.format(option_type)
    old_df = pd.read_sql(query, con=Database.DATABASE.engine)
    if 'level_0' in old_df.columns:
        old_df = old_df.drop(['level_0'], axis=1)
    if 'index' in old_df.columns:
        old_df = old_df.drop(['index'], axis=1)


    print('old_df: \n', old_df)
    print(uuid)

    """When user edits an existing question naire"""

    old_df.loc[old_df.uuid == uuid, list(questionnaire.keys())] = list(questionnaire.values())
    print("Database row after upsert from some uuid: ", old_df.loc[old_df.uuid == uuid])
    old_df.to_sql(name=option_type, con=Database.DATABASE.engine, if_exists="replace")

    print("Successfully updated questionnaire database")
