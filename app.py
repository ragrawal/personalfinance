import os 
import sys
from datetime import datetime, timedelta
os.environ['GSPREAD_PANDAS_CONFIG_DIR'] = '.'

import pandas as pd
from tqdm import tqdm 
from gspread_pandas import Spread, Client

import helper


def UpdateStatement(end_date):
    et = datetime.strptime(end_date, "%Y-%m-%d")
    start_date = et.strftime("%Y-%m-01")

    df = helper.getAllTransactions(start_date, end_date)

    if df is None:
        return

    workbook = Spread(helper.CONFIG['sheets']['workbook'])
    sheet_title = helper.CONFIG['sheets']['transactions']

    # Grab Existing Sheet
    sheet = workbook.find_sheet(sheet_title)
    if sheet is not None:
        header = sheet.row_values(1)  
        if 'id' not in header:      
            raise ValueError('Unable to find id column. If sheet is empty, then delete it')
        ids = sheet.col_values(header.index('id') + 1)
        colOrder = [x for x in header if x in df.columns]
        newDF = df[~(df['id'].isin(ids))][colOrder].copy()        
        sheet.append_rows(newDF.values.tolist())
    else:
        workbook.df_to_sheet(df, index=False, sheet=sheet_title, replace=True)


def UpdateBalances():
    df = helper.getAllAccounts()
    workbook = Spread(helper.CONFIG['sheets']['balances'])
    workbook.df_to_sheet(df, index=False, sheet='balances', replace=True)


if __name__ == '__main__':
    assert len(sys.argv) >= 2, "Missing command"

    if sys.argv[1] == "UpdateTransactions":
        assert len(sys.argv) >= 3, "For UpdateTransactions, provide end_date in %Y-%m-%d format"
        UpdateStatement(sys.argv[2])

    elif sys.argv[1] == 'UpdateBalances':
        UpdateBalances()



    



        