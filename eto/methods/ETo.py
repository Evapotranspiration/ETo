# -*- coding: utf-8 -*-
"""
Function to estimate reference ET (ETo) from the FAO 56 paper using a minimum of T_min and T_max for daily estimates and T_mean and RH_mean for hourly, but utilizing the maximum number of available met parameters. The function prioritizes the estimation of specific parameters based on the available input data.
"""
import pandas as pd
import numpy as np


def eto_fao(self, max_ETo=15, min_ETo=0, interp=False, maxgap=15, export=None):
    """
    Function to estimate reference ET (ETo) from the `FAO 56 paper <http://www.fao.org/docrep/X0490E/X0490E00.htm>`_ [1]_ using a minimum of T_min and T_max for daily estimates and T_mean and RH_mean for hourly, but optionally utilising the maximum number of available met parameters. The function prioritizes the estimation of specific parameters based on the available input data.

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
    export : str
        Export path for csv output or None to not export.

    Returns
    -------
    DataFrame
        If fill=False, then the returned DataFrame is two columns of estimated ETo in mm and the parameter estimation values. If fill=True, then the returned DataFrame has an additional column for the filled ETo value in mm.

    Input df
    --------
    The input data must be a DataFrame with specific column names according to the met parameter. The column names should be a minimum of T_min and T_max for daily estimates and T_mean and RH_mean for hourly, but can contain any/all of the following:

    R_n
        Net radiation (MJ/m2)
    R_s
        Incoming shortwave radiation (MJ/m2)
    G
        Net soil heat flux (MJ/m2)
    T_min
        Minimum Temperature (deg C)
    T_max
        Maximum Temperature (deg C)
    T_mean
        Mean Temperature (deg C)
    T_dew
        Dew point temperature (deg C)
    RH_min
        Minimum relative humidity
    RH_max
        Maximum relative humidity
    RH_mean
        Mean relative humidity
    n_sun
        Number of sunshine hours per day
    U_z
        Wind speed at height z (m/s)
    P
        Atmospheric pressure (kPa)

    Parameter estimation
    --------------------
    Parameter estimation values refer to the quality level of the input parameters into the ETo equations. Where a 0 (or nothing) refers to no necessary parameter estimation (all measurement data was available), while a 1 refers to parameters that have the best input estimations and up to a value of 3 is the worst. Starting from the right, the first value refers to U_z, the second value refers to G, the third value refers to R_n, the fourth value refers to R_s, the fifth value refers to e_a, the sixth value refers to T_mean, the seventh value refers to P.

    .. [1] Allen, R. G., Pereira, L. S., Raes, D., & Smith, M. (1998). Crop evapotranspiration-Guidelines for computing crop water requirements-FAO Irrigation and drainage paper 56. FAO, Rome, 300(9), D05109.
    """

    ######
    ## ETo equation

    if self.time_int == 'D':
        ETo_FAO = (0.408*self.ts_param['delta']*(self.ts_param['R_n'] - self.ts_param['G']) + self.ts_param['gamma']*900/(self.ts_param['T_mean'] + 273)*self.ts_param['U_2']*(self.ts_param['e_s'] - self.ts_param['e_a']))/(self.ts_param['delta'] + self.ts_param['gamma']*(1 + 0.34*self.ts_param['U_2']))
    elif self.time_int == 'H':
        ETo_FAO = (0.408*self.ts_param['delta']*(self.ts_param['R_n'] - self.ts_param['G']) + self.ts_param['gamma']*37/(self.ts_param['T_mean'] + 273)*self.ts_param['U_2']*(self.ts_param['e_mean'] - self.ts_param['e_a']))/(self.ts_param['delta'] + self.ts_param['gamma']*(1 + 0.34*self.ts_param['U_2']))

    ETo_FAO.name = 'ETo_FAO_mm'

    ## Remove extreme values
    ETo_FAO[ETo_FAO > max_ETo] = np.nan
    ETo_FAO[ETo_FAO < min_ETo] = np.nan

    ## ETo equation with filled holes using interpolation (use with caution)
    if isinstance(interp, str):
        ETo_FAO_fill = self.tsreg(ETo_FAO, self.time_int, interp, maxgap)
        ETo_FAO_fill.name = 'ETo_FAO_fill_mm'
        ETo = pd.concat([ETo_FAO, ETo_FAO_fill], axis=1).round(2)
    else:
        ETo = ETo_FAO.round(2)

    ## Save data and return
    if isinstance(export, str):
        ETo.to_csv(export)
    return ETo

