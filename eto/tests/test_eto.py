# -*- coding: utf-8 -*-
"""
Created on Wed May  9 15:12:14 2018

@author: MichaelEK
"""
import pytest
import pandas as pd
import os
from eto import ETo

###############################
### Parameters

_module_path = os.path.dirname(__file__)
example_csv = 'example1.csv'
results_csv = 'example1_results.csv'

example1 = os.path.join(_module_path, example_csv)
results1 = os.path.join(_module_path, results_csv)

###############################
### Tests

tsdata = pd.read_csv(example1, parse_dates=True, infer_datetime_format=True, index_col='date')

tsresults = pd.read_csv(results1, parse_dates=True, infer_datetime_format=True, index_col='date')


def test_eto_fao():
    et1 = ETo(tsdata).eto_fao().sum()
    res1 = tsresults['ETo_FAO_mm'].sum()

    assert et1 == res1


def test_eto_har():
    et1 = ETo(tsdata).eto_hargreaves().sum()
    res1 = tsresults['ETo_Har_mm'].sum()

    assert et1 == res1
