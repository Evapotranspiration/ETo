# -*- coding: utf-8 -*-
"""
Dual crop coefficient method (FAO 56 Eq 58).
"""
import numpy as np


def etc_dual(self, Kcb, Ke=None, Kr=None, Kc_max=None, few=None, **kwargs):
    """
    Dual crop coefficient ETc = (Kcb + Ke) * ETo (FAO 56 Eq 58).

    Parameters
    ----------
    Kcb : float or np.ndarray
        Basal crop coefficient.
    Ke : float or np.ndarray, optional
        Soil evaporation coefficient. If not provided, estimated from
        Kr, Kc_max, few, and Kcb.
    Kr : float or np.ndarray, optional
        Evaporation reduction coefficient (0-1). Required if Ke not provided.
    Kc_max : float or np.ndarray, optional
        Maximum Kc following rain/irrigation. Required if Ke not provided.
    few : float or np.ndarray, optional
        Fraction of soil surface wetted and exposed (0-1). Required if Ke
        not provided.
    **kwargs
        Passed to eto_fao().

    Returns
    -------
    np.ndarray
        ETc in mm.
    """
    if Ke is None:
        if Kr is None or Kc_max is None or few is None:
            raise ValueError('When Ke is not provided, Kr, Kc_max, and few are required')
        Kcb = np.asarray(Kcb, dtype=np.float64)
        Kr = np.asarray(Kr, dtype=np.float64)
        Kc_max = np.asarray(Kc_max, dtype=np.float64)
        few = np.asarray(few, dtype=np.float64)
        # FAO 56 Eq 71: Ke = Kr * (Kc_max - Kcb), limited by few * Kc_max
        Ke = np.minimum(Kr * (Kc_max - Kcb), few * Kc_max)

    return (np.asarray(Kcb) + np.asarray(Ke)) * self.eto_fao(**kwargs)
