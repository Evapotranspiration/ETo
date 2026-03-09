# -*- coding: utf-8 -*-
"""
Crop coefficient functions for ETc estimation (FAO 56).
"""
import numpy as np


# FAO 56 Table 12 — single crop coefficients (Kc_ini, Kc_mid, Kc_end)
KC_TABLE = {
    'alfalfa':          (0.40, 1.20, 1.15),
    'barley':           (0.30, 1.15, 0.25),
    'beans_dry':        (0.40, 1.15, 0.35),
    'beans_green':      (0.50, 1.05, 0.90),
    'cabbage':          (0.70, 1.05, 0.95),
    'cotton':           (0.35, 1.15, 0.70),
    'grape':            (0.30, 0.85, 0.45),
    'groundnut':        (0.40, 1.15, 0.60),
    'lettuce':          (0.70, 1.00, 0.95),
    'maize_grain':      (0.30, 1.20, 0.60),
    'maize_sweet':      (0.30, 1.15, 1.05),
    'millet':           (0.30, 1.00, 0.30),
    'onion_dry':        (0.70, 1.05, 0.75),
    'peanut':           (0.40, 1.15, 0.60),
    'potato':           (0.50, 1.15, 0.75),
    'rice':             (1.05, 1.20, 0.90),
    'sorghum':          (0.30, 1.00, 0.55),
    'soybean':          (0.40, 1.15, 0.50),
    'sugarcane':        (0.40, 1.25, 0.75),
    'sunflower':        (0.35, 1.15, 0.35),
    'tomato':           (0.60, 1.15, 0.80),
    'wheat_winter':     (0.70, 1.15, 0.25),
    'wheat_spring':     (0.30, 1.15, 0.25),
}


def kc_adjust(Kc, u2, RH_min, h):
    """
    Climate adjustment of Kc for non-standard conditions (FAO 56 Eq 62).

    Parameters
    ----------
    Kc : float
        Tabulated crop coefficient (Kc_mid or Kc_end).
    u2 : float
        Mean daily wind speed at 2 m (m/s).
    RH_min : float
        Mean minimum relative humidity (%).
    h : float
        Mean plant height (m).

    Returns
    -------
    float
        Adjusted Kc.
    """
    return Kc + (0.04*(u2 - 2) - 0.004*(RH_min - 45)) * (h/3)**0.3


def etc(self, Kc=None, crop=None, stage=None, **kwargs):
    """
    Crop evapotranspiration ETc = Kc * ETo (FAO 56 Eq 58, single Kc).

    Parameters
    ----------
    Kc : float or np.ndarray, optional
        Crop coefficient. If not provided, looked up from KC_TABLE.
    crop : str, optional
        Crop name (key in KC_TABLE). Required if Kc is not provided.
    stage : str, optional
        Growth stage: 'ini', 'mid', or 'end'. Required if crop is provided
        without Kc.
    **kwargs
        Passed to eto_fao().

    Returns
    -------
    np.ndarray
        ETc in mm.
    """
    if Kc is None:
        if crop is None:
            raise ValueError('Either Kc or crop must be provided')
        crop_lower = crop.lower()
        if crop_lower not in KC_TABLE:
            raise ValueError(f'Unknown crop: {crop}. Available: {sorted(KC_TABLE.keys())}')
        if stage is None:
            raise ValueError('stage must be provided when using crop lookup')
        stage_idx = {'ini': 0, 'mid': 1, 'end': 2}
        if stage not in stage_idx:
            raise ValueError(f"stage must be 'ini', 'mid', or 'end', got '{stage}'")
        Kc = KC_TABLE[crop_lower][stage_idx[stage]]

    return np.asarray(Kc) * self.eto_fao(**kwargs)


def etc_adj(self, Kc, TAW, Dr, p=0.5, **kwargs):
    """
    Adjusted ETc under water stress (FAO 56 Eq 84).

    ETc_adj = Ks * Kc * ETo

    Parameters
    ----------
    Kc : float or np.ndarray
        Crop coefficient.
    TAW : float or np.ndarray
        Total available water in root zone (mm).
    Dr : float or np.ndarray
        Root zone depletion (mm).
    p : float
        Depletion fraction for no stress (default 0.5).
    **kwargs
        Passed to eto_fao().

    Returns
    -------
    np.ndarray
        ETc_adj in mm.
    """
    TAW = np.asarray(TAW, dtype=np.float64)
    Dr = np.asarray(Dr, dtype=np.float64)
    Ks = np.clip((TAW - Dr) / ((1 - p) * TAW), 0, 1)
    return Ks * np.asarray(Kc) * self.eto_fao(**kwargs)
