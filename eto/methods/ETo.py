# -*- coding: utf-8 -*-
"""
Function to estimate reference ET (ETo) from the FAO 56 paper using a minimum of T_min and T_max for daily estimates and T_mean and RH_mean for hourly, but utilizing the maximum number of available met parameters. The function prioritizes the estimation of specific parameters based on the available input data.
"""
from pandas import DatetimeIndex, DataFrame, Series, concat
from numpy import nan, in1d, array, pi, sin, cos, arccos, tan, log, exp


def fao_eto(df, z_msl=500, lat=-43.6, lon=172, TZ_lon=173, z_u=2, time_int='days', max_ETo=15, min_ETo=0, fill=False, maxgap=15, export=None):
    """
    Function to estimate reference ET (ETo) from the `FAO 56 paper <http://www.fao.org/docrep/X0490E/X0490E00.htm>`_ [1]_ using a minimum of T_min and T_max for daily estimates and T_mean and RH_mean for hourly, but optionally utilising the maximum number of available met parameters. The function prioritizes the estimation of specific parameters based on the available input data.

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
    max_ETo : float or int
        The max realistic value of ETo (mm).
    min_ETo : float or int
        The min realistic value of ETo (mm).
    fill : False or str
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


    def tsreg(ts, freq=None, interp=False):
        """
        Function to regularize a time series object (pandas).
        The first three indeces must be regular for freq=None!!!

        ts -- pandas time series dataframe.\n
        freq -- Either specify the known frequency of the data or use None and
        determine the frequency from the first three indices.\n
        interp -- Should linear interpolation be applied on all missing data?
        """

        from pandas import infer_freq

        if freq is None:
            freq = infer_freq(ts.index[:3])
        ts1 = ts.resample(freq).mean()
        if interp:
            ts1 = ts1.interpolate('time')

        return(ts1)

    met_names = array(['R_n', 'R_s', 'G', 'T_min', 'T_max', 'T_mean', 'T_dew', 'RH_min', 'RH_max', 'RH_mean', 'n_sun', 'U_z', 'P'])

    #######################################
    ######
    ## Coefficients - Do not change unless you know why!

    K_rs = 0.16	# Rs calc coefficient (0.16 for inland stations, 0.19 for coastal stations)
    a_s = 0.25	# Rs calc coefficient
    b_s = 0.5	    # Rs calc coefficient
    alb = 0.23	# Albedo (should be fixed for the reference crop)

    ####################################
    ##### Set up the DataFrame and estimated values series
    new_cols = met_names[~in1d(met_names, df.columns)]
    new_df = DataFrame(nan, index=df.index, columns=new_cols)
    df1 = tsreg(concat([df, new_df], axis=1))

    est_val = Series(0, index=df1.index, name='est_val')

    ####################################
    ###### Calculations

    ######
    ### Time index
    if type(df.index) is not DatetimeIndex:
        raise ValueError('DataFrame must have a datetime index!')

    # Create the Day of the year vector
    Day = df.index.dayofyear

    ######
    ## Atmospheric components

    # Air Pressure
    est_val.loc[df1['P'].isnull()] = est_val.loc[df1['P'].isnull()] + 1000000
    df1.loc[df1['P'].isnull(), 'P'] = 101.3*((293 - 0.0065*z_msl)/293)**5.26

    # Psychrometric constant
    gamma = (0.665*10**-3)*df1['P']

    ######
    ## Temperature and humidity components
    est_val.loc[df1['T_mean'].isnull()] = est_val.loc[df1['T_mean'].isnull()] + 100000
    df1.loc[df1['T_mean'].isnull(), 'T_mean'] = (df1.loc[df1['T_mean'].isnull(), 'T_max'] + df1.loc[df1['T_mean'].isnull(), 'T_min'])/2

    ## Vapor pressures
    if time_int == 'days':
        e_max = 0.6108*exp(17.27*df1['T_max']/(df1['T_max']+237.3))
        e_min = 0.6108*exp(17.27*df1['T_min']/(df1['T_min']+237.3))
        e_s = (e_max+e_min)/2

        Delta = 4098*(0.6108*exp(17.27*df1['T_mean']/(df1['T_mean'] + 237.3)))/((df1['T_mean'] + 237.3)**2)

        # e_a if dewpoint temperature is known
        e_a = 0.6108*exp(17.27*df1['T_dew']/(df1['T_dew'] + 237.3))

        # e_a if min and max temperatures and humidities are known
        est_val.loc[df1['T_dew'].isnull()] = est_val.loc[df1['T_dew'].isnull()] + 10000
        e_a.loc[e_a.isnull()] = (e_min[e_a.isnull()] * df1.loc[e_a.isnull(), 'RH_max']/100 + e_max[e_a.isnull()] * df1.loc[e_a.isnull(), 'RH_min']/100)/2

        # e_a if only mean humidity is known
        est_val.loc[e_a.isnull()] = est_val.loc[e_a.isnull()] + 10000
        e_a.loc[e_a.isnull()] = df1.loc[e_a.isnull(), 'RH_mean']/100*(e_max[e_a.isnull()] + e_min[e_a.isnull()])/2

        # e_a if humidity is not known
        est_val.loc[e_a.isnull()] = est_val.loc[e_a.isnull()] + 10000
        e_a.loc[e_a.isnull()] = 0.6108*exp(17.27*df1.loc[e_a.isnull(), 'T_min']/(df1.loc[e_a.isnull(), 'T_min'] + 237.3))

    elif time_int == 'hours':
        e_mean = 0.6108*exp(17.27*df1['T_mean']/(df1['T_mean']+237.3))
        e_a = e_mean*df1['RH_mean']/100


    ######
    ## Raditation components

    # R_a
    phi = lat*pi/180
    delta = 0.409*sin(2*pi*Day/365-1.39)
    d_r = 1+0.033*cos(2*pi*Day/365)
    w_s = arccos(-tan(phi)*tan(delta))

    if time_int == 'days':
        R_a = 24*60/pi*0.082*d_r*(w_s*sin(phi)*sin(delta) + cos(phi)*cos(delta)*sin(w_s))
    elif time_int == 'hours':
        hour_vec = df.index.hour
        b = (2*pi*(Day - 81))/364
        S_c = 0.1645*sin(2*b) - 0.1255*cos(b) - 0.025*sin(b)
        w = pi/12*(((hour_vec+0.5) + 0.6666667*(TZ_lon - lon) + S_c) - 12)
        w_1 = w - (pi*hour_vec)/24
        w_2 = w + (pi*hour_vec)/24

        R_a = 12*60/pi*0.082*d_r*((w_2 - w_1)*sin(phi)*sin(delta) + cos(phi)*cos(delta)*(sin(w_2) - sin(w_1)))

    # Daylight hours
    N = 24*w_s/pi

    # R_s if n_sun is known
    est_val.loc[df1['R_s'].isnull()] = est_val.loc[df1['R_s'].isnull()] + 1000
    df1.loc[df1['R_s'].isnull(), 'R_s'] = (a_s + b_s*df1.loc[df1['R_s'].isnull(), 'n_sun']/N[df1['R_s'].isnull().values])*R_a[df1['R_s'].isnull().values]

    # R_s if n_sun is not known
    est_val.loc[df1['R_s'].isnull()] = est_val.loc[df1['R_s'].isnull()] + 1000
    df1.loc[df1['R_s'].isnull(), 'R_s'] = K_rs*((df1.loc[df1['R_s'].isnull(), 'T_max'] - df1.loc[df1['R_s'].isnull(), 'T_min'])**0.5)*R_a[df1['R_s'].isnull().values]

    # R_so
    R_so = (0.75 + 2*10**(-5)*z_msl)*R_a

    # R_ns from R_s
    R_ns = (1 - alb)*df1['R_s']

    # R_nl
    if time_int == 'days':
        R_nl = (4.903*10**(-9))*(((df1['T_max'] + 273.16)**4 + (df1['T_min'] + 273.16) **4)/2)*(0.34-0.14*(e_a) **0.5)*((1.35*df1['R_s']/R_so) - 0.35)
    elif time_int == 'hours':
        R_nl = (2.043*10**(-10))*((df1['T_mean'] + 273.16)**4)*(0.34-0.14*(e_a) **0.5)*((1.35*df1['R_s']/R_so) - 0.35)

    # R_n
    est_val.loc[df1['R_n'].isnull()] = est_val.loc[df1['R_n'].isnull()] + 100
    df1.loc[df1['R_n'].isnull(), 'R_n'] = R_ns[df1['R_n'].isnull()] - R_nl[df1['R_n'].isnull()]

    # G
    est_val.loc[df1['G'].isnull()] = est_val.loc[df1['G'].isnull()] + 10
    df1.loc[df1['G'].isnull(), 'G'] = 0


    ######
    ## Wind component

    U_2 = df1['U_z']*4.87/(log(67.8*z_u - 5.42))

    # or use 2 if wind speed is not known
    est_val.loc[df1['U_z'].isnull()] = est_val.loc[df1['U_z'].isnull()] + 1
    df1.loc[df1['U_z'].isnull(), 'U_z'] = 2


    ######
    ## ETo equation

    if time_int == 'days':
#        ETo_Har = 0.0023*(self.ts_param['T_mean'] + 17.8)*((self.ts_param['T_max'] - self.ts_param['T_min']) **0.5)*self.ts_param['R_a']
        ETo_FAO = (0.408*self.ts_param['delta']*(self.ts_param['R_n'] - self.ts_param['G']) + self.ts_param['gamma']*900/(self.ts_param['T_mean'] + 273)*self.ts_param['U_2']*(self.ts_param['e_s'] - self.ts_param['e_a']))/(self.ts_param['delta'] + self.ts_param['gamma']*(1 + 0.34*self.ts_param['U_2']))
    elif time_int == 'hours':
#        ETo_Har = Series(nan, index=self.ts_param.index)
        ETo_FAO = (0.408*self.ts_param['delta']*(self.ts_param['R_n'] - self.ts_param['G']) + self.ts_param['gamma']*37/(self.ts_param['T_mean'] + 273)*self.ts_param['U_2']*(self.ts_param['e_mean'] - self.ts_param['e_a']))/(self.ts_param['delta'] + self.ts_param['gamma']*(1 + 0.34*self.ts_param['U_2']))

    ## Remove extreme values
#    ETo_Har[ETo_Har > 20] = np.nan
#    ETo_Har[ETo_Har < min_ETo] = np.nan

    ETo_FAO[ETo_FAO > max_ETo] = np.nan
    ETo_FAO[ETo_FAO < min_ETo] = np.nan

    ## Combine results
#    ETo = concat([ETo_FAO.round(2), ETo_Har.round(2), self.est_val], axis=1)
#    ETo.columns = ['ETo_FAO_mm', 'ETo_Har_mm', 'self.est_val']
    ETo = pd.concat([ETo_FAO.round(2), self.est_val], axis=1)
    ETo.columns = ['ETo_FAO_mm', 'self.est_val']

    ## ETo equation with filled holes using interpolation (use with caution)
    if isinstance(fill, str):
        ETo_FAO_fill = ETo_FAO.interpolate(fill, limit=maxgap)
        ETo_FAO_fill.name = 'ETo_FAO_fill_mm'
#        ETo_Har_fill = ETo_Har.interpolate('pchip', limit=maxgap)
#        ETo_fill = concat([ETo_FAO_fill.round(2), ETo_Har_fill.round(2)], axis=1)
#        ETo_fill.columns = ['ETo_FAO_fill_mm', 'ETo_Har_fill_mm']
#        ETo = concat([ETo, ETo_fill], axis=1)
        ETo = pd.concat([ETo, ETo_FAO_fill.round(2)], axis=1)

    ## Save data and return
    if isinstance(export, str):
        ETo.to_csv(export)
    return ETo

