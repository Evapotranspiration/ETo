# -*- coding: utf-8 -*-
"""
Utility functions.
"""
import pandas as pd


def tsreg(ts, freq=None, interp=False, maxgap=None):
    """
    Function to regularize a time series object (pandas).
    The first three indeces must be regular for freq=None!!!

    ts -- pandas time series dataframe.\n
    freq -- Either specify the known frequency of the data or use None and
    determine the frequency from the first three indices.\n
    interp -- Interpolation method.
    """

    if freq is None:
        freq = pd.infer_freq(ts.index[:3])
    ts1 = ts.resample(freq).mean()
    if isinstance(interp, str):
        ts1 = ts1.interpolate(interp, limit=maxgap)

    return ts1
