# -*- coding: utf-8 -*-
"""
Utility functions.
"""

HOURLY = ('h', '1h')
DAILY = ('d', '1d')
MONTHLY = ('m', '1m')
TIME_LABELS = ('start', 'end')
RS_RSO_MIN = 0.3
"""Lower limit on Rs/Rso (ASCE-EWRI 2005). FAO-56 states only the upper limit of 1; below about 0.26 its
cloudiness factor (1.35 Rs/Rso - 0.35) turns negative, i.e. net longwave becomes a gain."""


def is_hourly(freq):
    """
    True for an hourly frequency, False for daily or monthly; anything else raises.

    Accepted (case-insensitive): 'h' / '1h' (hourly), 'D' / '1D' (daily), 'M' / '1M' (monthly). The
    equations assume exactly these periods, so other strings ('3h', '30min', 'T', 'month') are refused
    rather than silently computed with the wrong period.
    """
    f = str(freq).lower()
    if f in HOURLY:
        return True
    if f in DAILY or f in MONTHLY:
        return False
    raise ValueError(f'Unsupported frequency {freq!r}: use "h" (hourly), "D" (daily) or "M" (monthly)')
