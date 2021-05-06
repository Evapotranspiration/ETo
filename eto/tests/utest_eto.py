# -*- coding: utf-8 -*-
"""
Created on Wed May  9 15:12:14 2018

@author: MichaelEK
"""
import pandas as pd
import os
from eto import ETo

###############################
### Parameters

# _module_path = os.path.dirname(__file__)
file_path = '/media/sdb1/Projects/eto/issues/mendosa'
example_csv = 'alnarp.csv'
results_csv = 'example_daily_results.csv'

example1 = os.path.join(file_path, example_csv)
# results1 = os.path.join(_module_path, results_csv)

z_msl=12
lat=55.6689
lon=13.10
TZ_lon=15

###############################
### Tests

tsdata = pd.read_table(example1, sep=';', parse_dates=True, infer_datetime_format=True, index_col='DATUM').drop('STATION', axis=1)

# tsresults = pd.read_csv(results1, parse_dates=True, infer_datetime_format=True, index_col='date')

et1 = ETo(tsdata, 'H', z_msl, lat, lon, TZ_lon, K_rs=0.16)
eto1 = et1.eto_fao()





def test_eto_fao_daily():
    et1 = ETo(tsdata, 'H', z_msl, lat, lon, TZ_lon)
    eto1 = et1.eto_fao()
    res1 = tsresults['ETo_FAO_mm'].sum()

    assert eto1 == res1

et1 = ETo(tsdata, 'D', z_msl, lat, lon, TZ_lon)

def test_eto_har_daily():
    eto2 = et1.eto_hargreaves().sum()
    res1 = tsresults['ETo_Har_mm'].sum()

    assert eto2 == res1

def test_eto_fao_hourly():
    tsdata2 = et1.ts_param[['R_s', 'T_mean', 'e_a']]
    tsdata3 = et1.tsreg(tsdata2, 'H', 'time')
    et2 = ETo(tsdata3, 'H', z_msl, lat, lon, TZ_lon)
    eto3 = et2.eto_fao().sum()

    res1 = tsresults['ETo_FAO_mm'].sum()

    assert eto3 > res1














