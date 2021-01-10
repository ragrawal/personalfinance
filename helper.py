from datetime import datetime, timedelta
from copy import copy

import yaml
from tqdm import tqdm 
import pandas as pd
from plaid import Client
from model_helper import *
import joblib

CONFIG = None

with open("config.yaml") as fp:
    CONFIG = yaml.load(fp)

client = None
MODEL = joblib.load('model.pkl')

def getClient():
    global client
    if client:
        return client

    client = Client(
        client_id=CONFIG['plaid']['client_id'], 
        secret=CONFIG['plaid']['secret'], 
        environment='development'
    )
    return client



def MonthDates():
    dt = datetime.now()
    st = (dt - timedelta(days=dt.day - 1)).strftime("%Y-%m-%d")
    et = dt.strftime("%Y-%m-%d")
    return (st, et)



def getTransactions(config, start_date, end_date):

    client = getClient()

    access_token = config['access_token']
    products = config['products']

    accounts = dict([(x['account_id'], x['name']) for x in client.Accounts.get(access_token)['accounts']])
    output = []

    if 'bank' in products:        
        counter = 0
        while True:
            response = client.Transactions.get(access_token, start_date=start_date, end_date=end_date)
            counter += len(response['transactions'])

            for t in response['transactions']:
                if t['pending'] == True:
                    continue

                output.append({
                    'id': t['transaction_id'],
                    'account': accounts[t['account_id']],
                    'amount': t['amount'],
                    'date': t['date'],
                    'name': t['name'],
                    'merchant': t['merchant_name'],
                    'category': None, 
                })

            if counter >= response['total_transactions']:
                break


    if 'investment' in products:
        counter = 0
        while True:
            response = client.InvestmentTransactions.get(access_token, start_date=start_date, end_date=end_date)
            counter += len(response['investment_transactions'])

            for t in response['investment_transactions']:
                output.append({
                    'id': t['investment_transaction_id'],
                    'account': accounts[t['account_id']],
                    'amount': t['amount'],
                    'date': t['date'],
                    'name': t['name'],
                    'merchant': t.get('official_name', None),
                    'category': None,
                })            

            if counter >= response['total_investment_transactions']:
                break

    
    df = pd.DataFrame.from_dict(output).reset_index(drop=True)    
    if (df.shape[0] == 0):
        return None

    df['category'] = MODEL.predict(df)
    return df


def getAllTransactions(start_date, end_date):

    df = []   
    for account in tqdm(CONFIG['accounts']):
        transactions = getTransactions(
                account,
                start_date,
                end_date
            )
        if transactions is not None:
            transactions['institution'] = account['name']
            df.append(transactions) 

    if len(df) > 0:        
        return pd.concat(df, axis=0)

    return None


def getAllAccounts():
    output = []
    client = getClient()
    for account in tqdm(CONFIG['accounts']):
        response = client.Accounts.get(account['access_token'])
        row = {'Institution': account['name']}
        for acc in response['accounts']:
            row['balance'] = acc['balances']['current']
            row['name'] = acc['name']
            row['type'] = acc['type']
            row['official_name'] = acc['official_name']
            row['subtype'] = acc['subtype']
            output.append(copy(row))
    return pd.DataFrame.from_dict(output)


def UploadToGoogleSheet(transactions, sheetName, workbook='Transactions'):
    workbook = Spread(workbook)
    workbook.df_to_sheet(transactions, index=False, sheet=sheetName, start='A1', replace=True)




