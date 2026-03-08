# -*- coding: utf-8 -*-
"""
Function to estimate reference ET (ETo) from the FAO 56 paper using a minimum of T_min and T_max for daily estimates and T_mean and RH_mean for hourly, but utilizing the maximum number of available met parameters.
"""
import numpy as np


def eto_fao(self, max_ETo=15, min_ETo=0):
    """
    Function to estimate reference ET (ETo) from the `FAO 56 paper <http://www.fao.org/docrep/X0490E/X0490E00.htm>`_ [1]_ using a minimum of T_min and T_max for daily estimates and T_mean and RH_mean for hourly, but optionally utilising the maximum number of available met parameters.

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

    References
    ----------

    .. [1] Allen, R. G., Pereira, L. S., Raes, D., & Smith, M. (1998). Crop evapotranspiration-Guidelines for computing crop water requirements-FAO Irrigation and drainage paper 56. FAO, Rome, 300(9), D05109.
    """

    ######
    ## ETo equation
    if 'h' in self.freq.lower():
        ETo_FAO = (0.408*self.ts_param['delta']*(self.ts_param['R_n'] - self.ts_param['G']) + self.ts_param['gamma']*37/(self.ts_param['T_mean'] + 273)*self.ts_param['U_2']*(self.ts_param['e_mean'] - self.ts_param['e_a']))/(self.ts_param['delta'] + self.ts_param['gamma']*(1 + 0.34*self.ts_param['U_2']))
    else:
        ETo_FAO = (0.408*self.ts_param['delta']*(self.ts_param['R_n'] - self.ts_param['G']) + self.ts_param['gamma']*900/(self.ts_param['T_mean'] + 273)*self.ts_param['U_2']*(self.ts_param['e_s'] - self.ts_param['e_a']))/(self.ts_param['delta'] + self.ts_param['gamma']*(1 + 0.34*self.ts_param['U_2']))

    ## Remove extreme values
    ETo_FAO[ETo_FAO > max_ETo] = np.nan
    ETo_FAO[ETo_FAO < min_ETo] = np.nan

    return np.round(ETo_FAO, 2)
