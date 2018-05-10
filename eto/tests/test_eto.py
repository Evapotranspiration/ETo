# -*- coding: utf-8 -*-
"""
Created on Wed May  9 15:12:14 2018

@author: MichaelEK
"""
import pytest
import pandas as pd


###############################
### Parameters

csv1 = r'E:\ecan\git\ETo\eto\datasets\test1.csv'

###############################
### Tests

tsdata = pd.read_csv(csv1, parse_dates=True, infer_datetime_format=True, index_col='date')

et1 = ETo(tsdata)
et1.eto_fao()
interp1 = et1.eto_fao(interp='linear')

































