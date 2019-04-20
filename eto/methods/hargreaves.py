# -*- coding: utf-8 -*-
"""
Created on Sun May 13 09:45:39 2018

@author: MichaelEK
"""
import pandas as pd
import numpy as np


def hargreaves(self, max_ETo=15, min_ETo=0, interp=False, maxgap=15):
    """
    Function to estimate Hargreaves ETo using a minimum of T_min and T_max, but optionally utilising the maximum number of available met parameters. The function prioritizes the estimation of specific parameters based on the available input data.

    Parameters
    ----------
    max_ETo : float or int
        The max realistic value of ETo (mm).
    min_ETo : float or int
        The min realistic value of ETo (mm).
    interp : False or str
        Should missing values be filled by interpolation? Either False if no interpolation should be performed, or a string of the interpolation method. See Pandas interpolate function for methods. Recommended interpolators are 'linear' or 'pchip'.
    maxgap : int
        The maximum missing value gap for the interpolation.

    Returns
    -------
    DataFrame or Series
        If fill=False, then the function will return a Series of estimated ETo in mm. If fill is a str, then the function will return a DataFrame with an additional column for the filled ETo value in mm.
    """

    ######
    ## ETo equation

    if 'H' in self.freq:
        raise ValueError('Hargreaves should not be calculated at time frequencies of less than a day.')

    ETo_Har = 0.0023*(self.ts_param['T_mean'] + 17.8)*((self.ts_param['T_max'] - self.ts_param['T_min']) **0.5)*self.ts_param['R_a']*0.408

    ETo_Har.name = 'ETo_Har_mm'

    ## Remove extreme values
    ETo_Har[ETo_Har > max_ETo] = np.nan
    ETo_Har[ETo_Har < min_ETo] = np.nan

    ## ETo equation with filled holes using interpolation (use with caution)
    if isinstance(interp, str):
        ETo_Har_fill = self.tsreg(ETo_Har, self.freq, interp, maxgap)
        ETo_Har_fill.name = 'ETo_Har_interp_mm'
        ETo = pd.concat([ETo_Har, ETo_Har_fill], axis=1).round(2)
    else:
        ETo = ETo_Har.round(2)

    return ETo


