from datetime import datetime, timedelta
from copy import copy

import yaml
from tqdm import tqdm 
import pandas as pd
from plaid import Client


CONFIG = None

with open("config.yaml") as fp:
    CONFIG = yaml.load(fp)

client = None

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



def getTransactions(access_token, start_date, end_date, products=['bank']):

    client = getClient()
    accounts = dict([(x['account_id'], x['name']) for x in client.Accounts.get(access_token)['accounts']])
    output = []

    if 'bank' in products:
        
        response = client.Transactions.get(access_token, start_date=start_date, end_date=end_date)
        bankTransactions  = response['transactions']
        while len(bankTransactions) < response['total_transactions']:
            response = client.Transactions.get(access_token, start_date=start_date, end_date=end_date, offset=len(bankTransactions))
            bankTransactions.extend(response['transactions'])
        
        
        for t in bankTransactions:
            output.append({
                'id': t['transaction_id'],
                'account': accounts[t['account_id']],
                'amount': t['amount'],
                'date': t['date'],
                'name': t['name'],
                'category': None, 
            })

    if 'investment' in products:
        response = client.InvestmentTransactions.get(access_token, start_date=start_date, end_date=end_date)
        iTransactions = response['investment_transactions']
        while len(iTransactions) < response['total_investment_transactions']:
            response = client.Transactions.get(access_token, start_date=start_date, end_date=end_date, offset=len(iTransactions))
            iTransactions.extend(response['investment_transactions'])
        
        
        for t in iTransactions:
            output.append({
                'id': t['investment_transaction_id'],
                'account': accounts[t['account_id']],
                'amount': t['amount'],
                'date': t['date'],
                'name': t['name'],
                'category': None,
            })            

    
    df = pd.DataFrame.from_dict(output).reset_index(drop=True)
    if (df.shape[0] == 0):
        return None

    return df[['id', 'date', 'account', 'name', 'amount', 'category']]


def getAllTransactions(start_date, end_date):

    df = []   
    for account in tqdm(CONFIG['accounts']):
        df.append(
            getTransactions(
                account['access_token'],
                start_date,
                end_date,
                account['products']
            )
        )          

    return pd.concat(df, axis=0)


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




