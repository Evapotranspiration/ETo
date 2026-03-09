# -*- coding: utf-8 -*-
"""
Function for parameter estimation.
"""
import warnings
import numpy as np


def param_est(self, data, freq='D', z_msl=None, lat=None, lon=None, TZ_lon=None, z_u=2, K_rs=0.16, a_s=0.25, b_s=0.5, alb=0.23, day_of_year=None, hour=None, validate=True):
    """
    Function to estimate the parameters necessary to calculate reference ET (ETo) from the `FAO 56 paper <http://www.fao.org/docrep/X0490E/X0490E00.htm>`_ using a minimum of T_min and T_max for daily estimates and T_mean and RH_mean for hourly, but optionally utilising the maximum number of available met parameters.

    Parameters
    ----------
    data : dict of str to np.ndarray
        Input meteorological data.
    freq : str
        Time frequency string ('D' for daily, 'H'/'h' for hourly).
    z_msl : float, int, or None
        Elevation above mean sea level (m).
    lat : float, int, or None
        Latitude (decimal degrees).
    lon : float, int, or None
        Longitude (decimal degrees).
    TZ_lon : float, int, or None
        Longitude of the center of the time zone (decimal degrees).
    z_u : float or int
        Height of wind speed measurement (m). Default is 2 m.
    K_rs : float
        Rs calc coefficient (0.16 inland, 0.19 coastal).
    a_s : float
        Rs calc coefficient.
    b_s : float
        Rs calc coefficient.
    alb : float
        Albedo. Should be 0.23 for the reference crop.
    day_of_year : np.ndarray of int
        Day of year (1-366).
    hour : np.ndarray of int or None
        Hour of day (0-23). Required for hourly frequency.
    validate : bool
        If True (default), warn when input values are outside physically
        reasonable ranges.

    Returns
    -------
    None (populates self.ts_param and self.est_val)
    """

    met_names = ['R_n', 'R_s', 'G', 'T_min', 'T_max', 'T_mean', 'T_dew', 'RH_min', 'RH_max', 'RH_mean', 'n_sun', 'U_z', 'P', 'e_a']
    self.freq = freq

    ####################################
    ##### Set up the dict and estimated values array
    n = len(day_of_year)
    self.ts_param = {}
    for name in met_names:
        if name in data:
            self.ts_param[name] = np.array(data[name], dtype=np.float64).copy()
        else:
            self.ts_param[name] = np.full(n, np.nan)

    self.est_val = np.zeros(n, dtype=np.int64)

    ####################################
    ###### Input range validation
    if validate:
        for t_key in ('T_min', 'T_max', 'T_mean', 'T_dew'):
            v = self.ts_param[t_key]
            if np.any(np.isfinite(v) & ((v < -50) | (v > 60))):
                warnings.warn(f'{t_key} has values outside [-50, 60] °C')
        for rh_key in ('RH_min', 'RH_max', 'RH_mean'):
            v = self.ts_param[rh_key]
            if np.any(np.isfinite(v) & ((v < 0) | (v > 100))):
                warnings.warn(f'{rh_key} has values outside [0, 100] %')
        v = self.ts_param['R_s']
        if np.any(np.isfinite(v) & (v < 0)):
            warnings.warn('R_s has negative values')
        v = self.ts_param['U_z']
        if np.any(np.isfinite(v) & (v < 0)):
            warnings.warn('U_z has negative values')
        v = self.ts_param['P']
        if np.any(np.isfinite(v) & (v <= 0)):
            warnings.warn('P has non-positive values')

    ####################################
    ###### Check to make sure minimum requirements are met
    if 'h' in freq.lower():
        T_mean_bool = np.isnan(self.ts_param['T_mean']).any()
        RH_mean_bool = np.isnan(self.ts_param['RH_mean']).any()
        e_a_bool = np.isnan(self.ts_param['e_a']).any()
        if T_mean_bool | (RH_mean_bool & e_a_bool):
            raise ValueError('Minimum data input was not met. Check your data.')
    else:
        T_min_bool = np.isnan(self.ts_param['T_min']).any()
        T_max_bool = np.isnan(self.ts_param['T_max']).any()
        if T_min_bool | T_max_bool:
            raise ValueError('Minimum data input was not met. Check your data.')

    ####################################
    ###### Calculations

    ######
    ### Time index
    Day = day_of_year

    ######
    ## Atmospheric components

    # Air Pressure
    mask = np.isnan(self.ts_param['P'])
    self.est_val[mask] += 1000000
    self.ts_param['P'][mask] = 101.3*((293 - 0.0065*z_msl)/293)**5.26

    # Psychrometric constant
    self.ts_param['gamma'] = (0.665*10**-3)*self.ts_param['P']

    ######
    ## Temperature and humidity components
    mask = np.isnan(self.ts_param['T_mean'])
    self.est_val[mask] += 100000
    self.ts_param['T_mean'][mask] = (self.ts_param['T_max'][mask] + self.ts_param['T_min'][mask])/2

    ## Vapor pressures
    if 'h' in freq.lower():
        self.ts_param['e_mean'] = 0.6108*np.exp(17.27*self.ts_param['T_mean']/(self.ts_param['T_mean']+237.3))
        mask = np.isnan(self.ts_param['e_a'])
        self.ts_param['e_a'][mask] = self.ts_param['e_mean'][mask]*self.ts_param['RH_mean'][mask]/100
    else:
        self.ts_param['e_max'] = 0.6108*np.exp(17.27*self.ts_param['T_max']/(self.ts_param['T_max']+237.3))
        self.ts_param['e_min'] = 0.6108*np.exp(17.27*self.ts_param['T_min']/(self.ts_param['T_min']+237.3))
        self.ts_param['e_s'] = (self.ts_param['e_max']+self.ts_param['e_min'])/2

        # e_a if dewpoint temperature is known
        mask = np.isnan(self.ts_param['e_a'])
        self.ts_param['e_a'][mask] = 0.6108*np.exp(17.27*self.ts_param['T_dew'][mask]/(self.ts_param['T_dew'][mask] + 237.3))

        # e_a if min and max temperatures and humidities are known
        mask = np.isnan(self.ts_param['e_a'])
        self.est_val[mask] += 10000
        self.ts_param['e_a'][mask] = (self.ts_param['e_min'][mask] * self.ts_param['RH_max'][mask]/100 + self.ts_param['e_max'][mask] * self.ts_param['RH_min'][mask]/100)/2

        # e_a if only max humidity is known (FAO Eq 18)
        mask = np.isnan(self.ts_param['e_a'])
        self.est_val[mask] += 10000
        self.ts_param['e_a'][mask] = self.ts_param['e_min'][mask] * self.ts_param['RH_max'][mask]/100

        # e_a if only mean humidity is known
        mask = np.isnan(self.ts_param['e_a'])
        self.est_val[mask] += 10000
        self.ts_param['e_a'][mask] = self.ts_param['RH_mean'][mask]/100*(self.ts_param['e_max'][mask] + self.ts_param['e_min'][mask])/2

        # e_a if humidity is not known
        mask = np.isnan(self.ts_param['e_a'])
        self.est_val[mask] += 10000
        self.ts_param['e_a'][mask] = 0.6108*np.exp(17.27*self.ts_param['T_min'][mask]/(self.ts_param['T_min'][mask] + 237.3))

    # T_dew from e_a (inverse Magnus formula, FAO Eq 14 inverted)
    mask = np.isnan(self.ts_param['T_dew']) & (self.ts_param['e_a'] > 0)
    if mask.any():
        ln_ratio = np.log(self.ts_param['e_a'][mask] / 0.6108)
        self.ts_param['T_dew'][mask] = 237.3 * ln_ratio / (17.27 - ln_ratio)

    # VPD
    if 'h' in freq.lower():
        self.ts_param['VPD'] = self.ts_param['e_mean'] - self.ts_param['e_a']
    else:
        self.ts_param['VPD'] = self.ts_param['e_s'] - self.ts_param['e_a']

    # Delta
    self.ts_param['delta'] = 4098*(0.6108*np.exp(17.27*self.ts_param['T_mean']/(self.ts_param['T_mean'] + 237.3)))/((self.ts_param['T_mean'] + 237.3)**2)


    ######
    ## Raditation components

    # R_a
    phi = lat*np.pi/180
    delta = 0.409*np.sin(2*np.pi*Day/365-1.39)
    d_r = 1+0.033*np.cos(2*np.pi*Day/365)
    w_s = np.arccos(-np.tan(phi)*np.tan(delta))

    if 'h' in freq.lower():
        hour_vec = hour
        b = (2*np.pi*(Day - 81))/364
        S_c = 0.1645*np.sin(2*b) - 0.1255*np.cos(b) - 0.025*np.sin(b)
        w = np.pi/12*(((hour_vec+0.5) + 0.06667*(TZ_lon - lon) + S_c) - 12)
        w_1 = w - (np.pi*1)/24
        w_2 = w + (np.pi*1)/24

        self.ts_param['R_a'] = 12*60/np.pi*0.082*d_r*((w_2 - w_1)*np.sin(phi)*np.sin(delta) + np.cos(phi)*np.cos(delta)*(np.sin(w_2) - np.sin(w_1)))
        self.ts_param['R_a'] = np.maximum(self.ts_param['R_a'], 0)
    else:
        self.ts_param['R_a'] = 24*60/np.pi*0.082*d_r*(w_s*np.sin(phi)*np.sin(delta) + np.cos(phi)*np.cos(delta)*np.sin(w_s))

    # Daylight hours
    N = 24*w_s/np.pi

    # R_s if n_sun is known
    mask = np.isnan(self.ts_param['R_s'])
    self.est_val[mask] += 1000
    self.ts_param['R_s'][mask] = (a_s + b_s*self.ts_param['n_sun'][mask]/N[mask])*self.ts_param['R_a'][mask]

    # R_s if n_sun is not known
    mask = np.isnan(self.ts_param['R_s'])
    self.est_val[mask] += 1000
    self.ts_param['R_s'][mask] = K_rs*((self.ts_param['T_max'][mask] - self.ts_param['T_min'][mask])**0.5)*self.ts_param['R_a'][mask]

    # R_so (FAO Eq 37 for default coefficients, Eq 36 for calibrated)
    if a_s == 0.25 and b_s == 0.5:
        R_so = (0.75 + 2e-5*z_msl) * self.ts_param['R_a']
    else:
        R_so = (a_s + b_s) * self.ts_param['R_a']

    # R_ns from R_s
    R_ns = (1 - alb)*self.ts_param['R_s']

    # R_nl — safe R_s/R_so ratio to avoid division by zero when R_so=0
    Rs_Rso = np.where(R_so > 0, np.minimum(self.ts_param['R_s'] / np.where(R_so > 0, R_so, 1.0), 1.0), 1.0)
    if 'h' in freq.lower():
        R_nl = (2.043e-10)*((self.ts_param['T_mean'] + 273.16)**4)*(0.34-0.14*self.ts_param['e_a']**0.5)*(1.35*Rs_Rso - 0.35)
    else:
        R_nl = (4.903e-9)*(((self.ts_param['T_max'] + 273.16)**4 + (self.ts_param['T_min'] + 273.16)**4)/2)*(0.34-0.14*self.ts_param['e_a']**0.5)*(1.35*Rs_Rso - 0.35)

    # R_n
    mask = np.isnan(self.ts_param['R_n'])
    self.est_val[mask] += 100
    self.ts_param['R_n'][mask] = R_ns[mask] - R_nl[mask]

    # G
    mask = np.isnan(self.ts_param['G'])
    self.est_val[mask] += 10
    if 'h' in freq.lower():
        day_mask = mask & (self.ts_param['R_n'] > 0)
        night_mask = mask & (self.ts_param['R_n'] <= 0)
        self.ts_param['G'][day_mask] = 0.1 * self.ts_param['R_n'][day_mask]
        self.ts_param['G'][night_mask] = 0.5 * self.ts_param['R_n'][night_mask]
    elif freq.upper() == 'M':
        G_monthly = np.zeros(n)
        G_monthly[1:] = 0.14 * (self.ts_param['T_mean'][1:] - self.ts_param['T_mean'][:-1])
        self.ts_param['G'][mask] = G_monthly[mask]
    else:
        self.ts_param['G'][mask] = 0


    ######
    ## Wind component

    self.ts_param['U_2'] = self.ts_param['U_z']*4.87/(np.log(67.8*z_u - 5.42))

    # or use 2 if wind speed is not known
    mask = np.isnan(self.ts_param['U_z'])
    self.est_val[mask] += 1
    self.ts_param['U_2'][mask] = 2
