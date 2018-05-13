# -*- coding: utf-8 -*-
"""
Functions for parameter estimation.
"""
import numpy as np
import pandas as pd


def param_est(self, df, z_msl=500, lat=-43.6, lon=172, TZ_lon=173, z_u=2, time_int='days', K_rs=0.16, a_s=0.25, b_s=0.5, alb=0.23):
    """
    Function to estimate the parameters necessary to calculate reference ET (ETo) from the `FAO 56 paper <http://www.fao.org/docrep/X0490E/X0490E00.htm>`_ [1]_ using a minimum of T_min and T_max for daily estimates and T_mean and RH_mean for hourly, but optionally utilising the maximum number of available met parameters. The function prioritizes the estimation of specific parameters based on the available input data.

    Parameters
    ----------
    df : DataFrame
        Input Met data (see Input df section).
    z_msl : float or int
        Elevation of the met station above mean sea level (m) (only needed if P is not in df).
    lat : float or int
        The latitude of the met station (dec deg) (only needed if R_s or R_n are not in df).
    lon : float or int
        The longitude of the met station (dec deg) (only needed if calculating ETo hourly)
    TZ_lon : float or int
        The longitude of the center of the time zone (dec deg) (only needed if calculating ETo hourly).
    z_u : float or int
        The height of the wind speed measurement (m).
    time_int : str
        The time interval of the input and output (either 'days' or 'hours').
    K_rs : float
        Rs calc coefficient (0.16 for inland stations, 0.19 for coastal stations)
    a_s : float
        Rs calc coefficient
    b_s : float
        Rs calc coefficient
    alb : float
        Albedo (should be fixed for the reference crop)

    Returns
    -------
    DataFrame

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
    e_a
        Actual Vapour pressure derrived from RH

    Parameter estimation
    --------------------
    Parameter estimation values refer to the quality level of the input parameters into the ETo equations. Where a 0 (or nothing) refers to no necessary parameter estimation (all measurement data was available), while a 1 refers to parameters that have the best input estimations and up to a value of 3 is the worst. Starting from the right, the first value refers to U_z, the second value refers to G, the third value refers to R_n, the fourth value refers to R_s, the fifth value refers to e_a, the sixth value refers to T_mean, the seventh value refers to P.

    .. [1] Allen, R. G., Pereira, L. S., Raes, D., & Smith, M. (1998). Crop evapotranspiration-Guidelines for computing crop water requirements-FAO Irrigation and drainage paper 56. FAO, Rome, 300(9), D05109.
    """

    met_names = np.array(['R_n', 'R_s', 'G', 'T_min', 'T_max', 'T_mean', 'T_dew', 'RH_min', 'RH_max', 'RH_mean', 'n_sun', 'U_z', 'P', 'e_a'])
    if time_int == 'days':
        self.time_int = 'D'
    elif time_int == 'hours':
        self.time_int = 'H'

    ####################################
    ##### Set up the DataFrame and estimated values series
    new_cols = met_names[~np.in1d(met_names, df.columns)]
    new_df = pd.DataFrame(np.nan, index=df.index, columns=new_cols)
    self.ts_param = pd.concat([df, new_df], axis=1).copy()

    self.est_val = pd.Series(0, index=self.ts_param.index, name='est_val')

    ####################################
    ###### Calculations

    ######
    ### Time index
    if type(df.index) is not pd.DatetimeIndex:
        raise ValueError('DataFrame must have a datetime index!')

    # Create the Day of the year vector
    Day = df.index.dayofyear

    ######
    ## Atmospheric components

    # Air Pressure
    self.est_val.loc[self.ts_param['P'].isnull()] = self.est_val.loc[self.ts_param['P'].isnull()] + 1000000
    self.ts_param.loc[self.ts_param['P'].isnull(), 'P'] = 101.3*((293 - 0.0065*z_msl)/293)**5.26

    # Psychrometric constant
    self.ts_param['gamma'] = (0.665*10**-3)*self.ts_param['P']

    ######
    ## Temperature and humidity components
    self.est_val.loc[self.ts_param['T_mean'].isnull()] = self.est_val.loc[self.ts_param['T_mean'].isnull()] + 100000
    self.ts_param.loc[self.ts_param['T_mean'].isnull(), 'T_mean'] = (self.ts_param.loc[self.ts_param['T_mean'].isnull(), 'T_max'] + self.ts_param.loc[self.ts_param['T_mean'].isnull(), 'T_min'])/2

    ## Vapor pressures
    if time_int == 'days':
        self.ts_param['e_max'] = 0.6108*np.exp(17.27*self.ts_param['T_max']/(self.ts_param['T_max']+237.3))
        self.ts_param['e_min'] = 0.6108*np.exp(17.27*self.ts_param['T_min']/(self.ts_param['T_min']+237.3))
        self.ts_param['e_s'] = (self.ts_param['e_max']+self.ts_param['e_min'])/2

        self.ts_param['delta'] = 4098*(0.6108*np.exp(17.27*self.ts_param['T_mean']/(self.ts_param['T_mean'] + 237.3)))/((self.ts_param['T_mean'] + 237.3)**2)

        # e_a if dewpoint temperature is known
        self.ts_param.loc[self.ts_param['e_a'].isnull(), 'e_a'] = 0.6108*np.exp(17.27*self.ts_param.loc[self.ts_param['e_a'].isnull(), 'T_dew']/(self.ts_param.loc[self.ts_param['e_a'].isnull(), 'T_dew'] + 237.3))

        # e_a if min and max temperatures and humidities are known
        self.est_val.loc[self.ts_param['T_dew'].isnull()] = self.est_val.loc[self.ts_param['T_dew'].isnull()] + 10000
        self.ts_param['e_a'].loc[self.ts_param['e_a'].isnull()] = (self.ts_param['e_min'][self.ts_param['e_a'].isnull()] * self.ts_param.loc[self.ts_param['e_a'].isnull(), 'RH_max']/100 + self.ts_param['e_max'][self.ts_param['e_a'].isnull()] * self.ts_param.loc[self.ts_param['e_a'].isnull(), 'RH_min']/100)/2

        # self.ts_param['e_a'] if only mean humidity is known
        self.est_val.loc[self.ts_param['e_a'].isnull()] = self.est_val.loc[self.ts_param['e_a'].isnull()] + 10000
        self.ts_param['e_a'].loc[self.ts_param['e_a'].isnull()] = self.ts_param.loc[self.ts_param['e_a'].isnull(), 'RH_mean']/100*(self.ts_param['e_max'][self.ts_param['e_a'].isnull()] + self.ts_param['e_min'][self.ts_param['e_a'].isnull()])/2

        # e_a if humidity is not known
        self.est_val.loc[self.ts_param['e_a'].isnull()] = self.est_val.loc[self.ts_param['e_a'].isnull()] + 10000
        self.ts_param['e_a'].loc[self.ts_param['e_a'].isnull()] = 0.6108*np.exp(17.27*self.ts_param.loc[self.ts_param['e_a'].isnull(), 'T_min']/(self.ts_param.loc[self.ts_param['e_a'].isnull(), 'T_min'] + 237.3))

    elif time_int == 'hours':
        self.ts_param['e_mean'] = 0.6108*np.exp(17.27*self.ts_param['T_mean']/(self.ts_param['T_mean']+237.3))
        self.ts_param.loc[self.ts_param['e_a'].isnull(), 'e_a'] = self.ts_param.loc[self.ts_param['e_a'].isnull(), 'e_mean']*self.ts_param.loc[self.ts_param['e_a'].isnull(), 'RH_mean']/100
    else:
        raise ValueError('time_int must be either days or hours.')


    ######
    ## Raditation components

    # R_a
    phi = lat*np.pi/180
    delta = 0.409*np.sin(2*np.pi*Day/365-1.39)
    d_r = 1+0.033*np.cos(2*np.pi*Day/365)
    w_s = np.arccos(-np.tan(phi)*np.tan(delta))

    if time_int == 'days':
        self.ts_param['R_a'] = 24*60/np.pi*0.082*d_r*(w_s*np.sin(phi)*np.sin(delta) + np.cos(phi)*np.cos(delta)*np.sin(w_s))
    elif time_int == 'hours':
        hour_vec = df.index.hour
        b = (2*np.pi*(Day - 81))/364
        S_c = 0.1645*np.sin(2*b) - 0.1255*np.cos(b) - 0.025*np.sin(b)
        w = np.pi/12*(((hour_vec+0.5) + 0.6666667*(TZ_lon - lon) + S_c) - 12)
        w_1 = w - (np.pi*hour_vec)/24
        w_2 = w + (np.pi*hour_vec)/24

        self.ts_param['R_a'] = 12*60/np.pi*0.082*d_r*((w_2 - w_1)*np.sin(phi)*np.sin(delta) + np.cos(phi)*np.cos(delta)*(np.sin(w_2) - np.sin(w_1)))
    else:
        raise ValueError('time_int must be either days or hours.')

    # Daylight hours
    N = 24*w_s/np.pi

    # R_s if n_sun is known
    self.est_val.loc[self.ts_param['R_s'].isnull()] = self.est_val.loc[self.ts_param['R_s'].isnull()] + 1000
    self.ts_param.loc[self.ts_param['R_s'].isnull(), 'R_s'] = (a_s + b_s*self.ts_param.loc[self.ts_param['R_s'].isnull(), 'n_sun']/N[self.ts_param['R_s'].isnull().values])*self.ts_param['R_a'][self.ts_param['R_s'].isnull().values]

    # R_s if n_sun is not known
    self.est_val.loc[self.ts_param['R_s'].isnull()] = self.est_val.loc[self.ts_param['R_s'].isnull()] + 1000
    self.ts_param.loc[self.ts_param['R_s'].isnull(), 'R_s'] = K_rs*((self.ts_param.loc[self.ts_param['R_s'].isnull(), 'T_max'] - self.ts_param.loc[self.ts_param['R_s'].isnull(), 'T_min'])**0.5)*self.ts_param['R_a'][self.ts_param['R_s'].isnull().values]

    # R_so
    R_so = (0.75 + 2*10**(-5)*z_msl)*self.ts_param['R_a']

    # R_ns from R_s
    R_ns = (1 - alb)*self.ts_param['R_s']

    # R_nl
    if time_int == 'days':
        R_nl = (4.903*10**(-9))*(((self.ts_param['T_max'] + 273.16)**4 + (self.ts_param['T_min'] + 273.16) **4)/2)*(0.34-0.14*(self.ts_param['e_a']) **0.5)*((1.35*self.ts_param['R_s']/R_so) - 0.35)
    elif time_int == 'hours':
        R_nl = (2.043*10**(-10))*((self.ts_param['T_mean'] + 273.16)**4)*(0.34-0.14*(self.ts_param['e_a']) **0.5)*((1.35*self.ts_param['R_s']/R_so) - 0.35)

    # R_n
    self.est_val.loc[self.ts_param['R_n'].isnull()] = self.est_val.loc[self.ts_param['R_n'].isnull()] + 100
    self.ts_param.loc[self.ts_param['R_n'].isnull(), 'R_n'] = R_ns[self.ts_param['R_n'].isnull()] - R_nl[self.ts_param['R_n'].isnull()]

    # G
    self.est_val.loc[self.ts_param['G'].isnull()] = self.est_val.loc[self.ts_param['G'].isnull()] + 10
    self.ts_param.loc[self.ts_param['G'].isnull(), 'G'] = 0


    ######
    ## Wind component

    self.ts_param['U_2'] = self.ts_param['U_z']*4.87/(np.log(67.8*z_u - 5.42))

    # or use 2 if wind speed is not known
    self.est_val.loc[self.ts_param['U_z'].isnull()] = self.est_val.loc[self.ts_param['U_z'].isnull()] + 1
    self.ts_param.loc[self.ts_param['U_z'].isnull(), 'U_2'] = 2

    #######
    ## Assign the ET methods
    # self.eto_fao = self._eto_fao
    # self.hargreaves = self._hargreaves
