# -*- coding: utf-8 -*-
"""
Class to estimate reference ET (ETo) from the FAO 56 paper using a minimum of T_min and T_max for daily estimates and T_mean and RH_mean for hourly, but utilizing the maximum number of available met parameters. The function prioritizes the estimation of specific parameters based on the available input data.
"""
import pandas as pd


class ETo(object):
    """
    Class to handle the parameter estimation of metereological values and the calcuation of reference ET and similar ET methods.

    This class can be either initiated with empty parameters or will initialise to the param_est function.
    """
    from copy import copy
    from eto.param_est import param_est
    from eto.methods.ETo import eto_fao
    from eto.methods.hargreaves import hargreaves


    def __init__(self, df=None, z_msl=500, lat=-43.6, lon=172, TZ_lon=173, z_u=2, time_int='days', K_rs=0.16, a_s=0.25, b_s=0.5, alb=0.23):
        if df is None:
            pass
        else:
            self.param_est(df, z_msl, lat, lon, TZ_lon, z_u, time_int, K_rs, a_s, b_s, alb)


    @staticmethod
    def tsreg(ts, freq=None, interp=False, maxgap=None):
        """
        Function to regularize a time series object (pandas).
        The first three indeces must be regular for freq=None!!!

        Parameters
        ----------
        ts : DataFrame
            With a DateTimeIndex.
        freq : str or None
            Either specify the known frequency of the data or use None and
        determine the frequency from the first three indices.
        interp : str
            Interpolation method.

        Returns
        -------
        DataFrame
        """

        if freq is None:
            freq = pd.infer_freq(ts.index[:3])
        ts1 = ts.resample(freq).mean()
        if isinstance(interp, str):
            ts1 = ts1.interpolate(interp, limit=maxgap)

        return ts1
