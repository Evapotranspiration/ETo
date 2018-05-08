# -*- coding: utf-8 -*-
"""
Class to estimate reference ET (ETo) from the FAO 56 paper using a minimum of T_min and T_max for daily estimates and T_mean and RH_mean for hourly, but utilizing the maximum number of available met parameters. The function prioritizes the estimation of specific parameters based on the available input data.
"""




class ETo(object):
    """

    """
    import param_est

    def __init__(self, df=None, z_msl=500, lat=-43.6, lon=172, TZ_lon=173, z_u=2, time_int='days', K_rs=0.16, a_s=0.25, b_s=0.5, alb=0.23):
        if df is None:
            pass
        else:
            self.param_est(df, z_msl, lat, lon, TZ_lon, z_u, time_int, K_rs, a_s, b_s, alb)




