# -*- coding: utf-8 -*-
"""
Function to estimate reference ET (ETo) from the FAO 56 paper using a minimum of T_min and T_max for daily estimates and T_mean and RH_mean for hourly, but utilizing the maximum number of available met parameters.
"""
import numpy as np


def eto_fao(self, max_ETo=15, min_ETo=0, ref_crop='short'):
    """
    Function to estimate reference ET (ETo) from the `FAO 56 paper <http://www.fao.org/docrep/X0490E/X0490E00.htm>`_ [1]_ using a minimum of T_min and T_max for daily estimates and T_mean and RH_mean for hourly, but optionally utilising the maximum number of available met parameters.

    Parameters
    ----------
    max_ETo : float or int
        The max realistic value of ETo (mm).
    min_ETo : float or int
        The min realistic value of ETo (mm).
    ref_crop : str
        Reference crop type: 'short' (FAO 56 grass) or 'tall' (ASCE alfalfa).

    Returns
    -------
    np.ndarray
        Estimated ETo in mm.

    References
    ----------

    .. [1] Allen, R. G., Pereira, L. S., Raes, D., & Smith, M. (1998). Crop evapotranspiration-Guidelines for computing crop water requirements-FAO Irrigation and drainage paper 56. FAO, Rome, 300(9), D05109.
    """

    ######
    ## ETo equation — select Cn and Cd based on ref_crop and frequency
    if 'h' in self.freq.lower():
        if ref_crop == 'tall':
            Cn = 66
            Cd = np.where(self.ts_param['R_n'] > 0, 0.25, 1.7)
        else:
            Cn = 37
            Cd = 0.34
        ETo_FAO = (0.408*self.ts_param['delta']*(self.ts_param['R_n'] - self.ts_param['G']) + self.ts_param['gamma']*Cn/(self.ts_param['T_mean'] + 273)*self.ts_param['U_2']*(self.ts_param['e_mean'] - self.ts_param['e_a']))/(self.ts_param['delta'] + self.ts_param['gamma']*(1 + Cd*self.ts_param['U_2']))
    else:
        if ref_crop == 'tall':
            Cn = 1600
            Cd = 0.38
        else:
            Cn = 900
            Cd = 0.34
        ETo_FAO = (0.408*self.ts_param['delta']*(self.ts_param['R_n'] - self.ts_param['G']) + self.ts_param['gamma']*Cn/(self.ts_param['T_mean'] + 273)*self.ts_param['U_2']*(self.ts_param['e_s'] - self.ts_param['e_a']))/(self.ts_param['delta'] + self.ts_param['gamma']*(1 + Cd*self.ts_param['U_2']))

    ## Clamp negatives to min_ETo, NaN for suspect highs
    ETo_FAO = np.maximum(ETo_FAO, min_ETo)
    ETo_FAO[ETo_FAO > max_ETo] = np.nan

    return np.round(ETo_FAO, 2)
