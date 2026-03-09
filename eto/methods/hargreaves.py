# -*- coding: utf-8 -*-
"""
Created on Sun May 13 09:45:39 2018

@author: MichaelEK
"""
import numpy as np


def hargreaves(self, max_ETo=15, min_ETo=0):
    """
    Function to estimate Hargreaves ETo using a minimum of T_min and T_max, but optionally utilising the maximum number of available met parameters.

    Parameters
    ----------
    max_ETo : float or int
        The max realistic value of ETo (mm).
    min_ETo : float or int
        The min realistic value of ETo (mm).

    Returns
    -------
    np.ndarray
        Estimated ETo in mm.
    """

    ######
    ## ETo equation

    if 'h' in self.freq.lower():
        raise ValueError('Hargreaves should not be calculated at time frequencies of less than a day.')

    ETo_Har = 0.0023*(self.ts_param['T_mean'] + 17.8)*((self.ts_param['T_max'] - self.ts_param['T_min']) **0.5)*self.ts_param['R_a']*0.408

    ## Clamp negatives to min_ETo, NaN for suspect highs
    ETo_Har = np.maximum(ETo_Har, min_ETo)
    ETo_Har[ETo_Har > max_ETo] = np.nan

    return np.round(ETo_Har, 2)
