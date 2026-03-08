# -*- coding: utf-8 -*-
"""
Class to estimate reference ET (ETo) from the FAO 56 paper using a minimum of T_min and T_max for daily estimates and T_mean and RH_mean for hourly, but utilizing the maximum number of available met parameters. The function prioritizes the estimation of specific parameters based on the available input data.
"""
import numpy as np
from eto.param_est import param_est
from eto.methods.ETo import eto_fao
from eto.methods.hargreaves import hargreaves


class ETo(object):
    """
    Class to handle the parameter estimation of metereological values and the calcuation of reference ET and similar ET methods.

    This class can be either initiated with empty parameters or will initialise to the param_est function.

    Parameters
    ----------
    data : dict of str to np.ndarray, or None
        Input meteorological data. Keys are parameter names (R_n, R_s, G,
        T_min, T_max, T_mean, T_dew, RH_min, RH_max, RH_mean, n_sun, U_z,
        P, e_a). All arrays must have the same length.
    freq : str
        Time frequency: 'D' for daily, 'H' or 'h' for hourly.
    day_of_year : np.ndarray of int, or None
        Day of year (1-366). Required if dates is not provided.
    hour : np.ndarray of int, or None
        Hour of day (0-23). Required for hourly frequency if dates is not provided.
    dates : np.ndarray of datetime64, or None
        Datetime array. Used to derive day_of_year and hour if they are not provided.
    """

    def __init__(self, data=None, freq='D', z_msl=None, lat=None, lon=None, TZ_lon=None,
                 z_u=2, K_rs=0.16, a_s=0.25, b_s=0.5, alb=0.23,
                 day_of_year=None, hour=None, dates=None):

        if data is None:
            pass
        else:
            # Validate data is a dict with consistent array lengths
            if not isinstance(data, dict):
                raise TypeError('data must be a dict of str to np.ndarray')
            lengths = [len(v) for v in data.values()]
            if lengths and len(set(lengths)) > 1:
                raise ValueError('All arrays in data must have the same length')
            n = lengths[0] if lengths else 0

            # Derive temporal arrays
            if dates is not None:
                dates = np.asarray(dates)
                day_of_year = (dates.astype('datetime64[D]') - dates.astype('datetime64[Y]')).astype(int) + 1
                if 'h' in freq.lower():
                    hour = (dates - dates.astype('datetime64[D]')).astype('timedelta64[h]').astype(int)
            elif day_of_year is not None:
                day_of_year = np.asarray(day_of_year)
            else:
                raise ValueError('Either dates or day_of_year must be provided')

            # Validate temporal array lengths
            if len(day_of_year) != n:
                raise ValueError('day_of_year length must match data array length')
            if 'h' in freq.lower():
                if hour is None:
                    raise ValueError('hour array or dates must be provided for hourly frequency')
                hour = np.asarray(hour)
                if len(hour) != n:
                    raise ValueError('hour length must match data array length')

            self.param_est(data, freq, z_msl, lat, lon, TZ_lon, z_u, K_rs, a_s, b_s, alb,
                           day_of_year=day_of_year, hour=hour)


### Add in the ETo methods
ETo.param_est = param_est
ETo.eto_fao = eto_fao
ETo.eto_hargreaves = hargreaves
