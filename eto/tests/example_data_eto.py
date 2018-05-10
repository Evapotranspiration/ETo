# -*- coding: utf-8 -*-
"""
Created on Wed May  9 08:51:29 2018

@author: MichaelEK
"""
import pandas as pd
from pdsql import mssql


############################################
### Parameters

server = 'sql2012dev01'
database = 'hydro'
table = 'TSDataNumericDaily'

from_date = '2000-01-01'
to_date = '2015-12-31'

dataset_ids = {18: 'T_max', 20: 'T_min', 34: 'R_s', 28: 'e_a'}

sites = [17244]

export_data = r'E:\ecan\git\ETo\eto\datasets\test1.csv'

###########################################
### extract data

tsdata = mssql.rd_sql(server, database, table, where_col={'ExtSiteID': sites, 'DatasetTypeID': list(dataset_ids.keys())}, from_date=from_date, to_date=to_date, date_col='DateTime')

tsdata1 = tsdata.drop(['ExtSiteID', 'QualityCode', 'ModDate'], axis=1).copy()
tsdata1.columns = ['parameter', 'date', 'value']
tsdata1.replace({'parameter': dataset_ids}, inplace=True)

tsdata2 = tsdata1.pivot_table('value', 'date', 'parameter')

tsdata2['e_a'] = tsdata2['e_a'] * 0.1

## Checks
tsdata3 = tsdata2[tsdata2['T_max'].notnull() & tsdata2['T_min'].notnull()]

tsdata3.to_csv(export_data)














