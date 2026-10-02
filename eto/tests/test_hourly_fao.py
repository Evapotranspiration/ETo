"""
Hourly FAO-56 checks added in 2.2.0: Example 19, solar time with east-positive longitude and
interval labels, and the night-time Rs/Rso carried as state.
"""
import warnings

import numpy as np
import pytest

from eto import ETo

# FAO-56 Example 19: N'Diaye, Senegal, 16°13'N 16°15'W, 8 m, 1 October (J = 274), Lz = 15° W.
EX19 = dict(z_msl=8, lat=16 + 13 / 60, lon=-16.25, TZ_lon=-15.0)


def ex19(hour, T, RH, u2, Rs, **kw):
    data = {'T_mean': np.array([T]), 'RH_mean': np.array([RH]), 'U_z': np.array([u2]), 'R_s': np.array([Rs])}
    return ETo(data, 'h', day_of_year=np.array([274]), hour=np.array([hour]), **EX19, **kw)


def test_example19_day_period():
    et = ex19(14, 38.0, 52.0, 3.3, 2.450)
    p = et.ts_param
    assert p['R_a'][0] == pytest.approx(3.543, abs=0.002)
    assert p['R_so'][0] == pytest.approx(2.658, abs=0.002)
    assert p['Rs_Rso'][0] == pytest.approx(0.922, abs=0.001)
    assert p['R_n'][0] == pytest.approx(1.749, abs=0.003)
    assert et.eto_fao()[0] == pytest.approx(0.63)


def test_example19_night_period_uses_the_carried_ratio():
    et = ex19(2, 28.0, 90.0, 1.9, 0.0, rs_rso_init=0.8)
    p = et.ts_param
    assert p['Rs_Rso'][0] == 0.8
    assert p['R_n'][0] == pytest.approx(-0.100, abs=0.002)
    assert et.eto_fao()[0] == pytest.approx(0.0)


def nz_day(time_label='start', lon=171.5, TZ_lon=0.0):
    """One January day of hourly UTC labels at a Canterbury point."""
    n = 24
    data = {'T_mean': np.full(n, 20.0), 'RH_mean': np.full(n, 60.0), 'U_z': np.full(n, 2.0), 'R_s': np.full(n, 0.5)}
    hours = np.arange(n) + (1 if time_label == 'end' else 0)
    return ETo(data, 'h', z_msl=300, lat=-43.5, lon=lon, TZ_lon=TZ_lon, day_of_year=np.full(n, 15),
               hour=hours, time_label=time_label, rs_rso_init=1.0)


def test_extraterrestrial_radiation_peaks_in_the_hour_holding_solar_noon():
    # Solar noon at 171.5°E on 15 January is about 00:40 UTC (equation of time about -9 min). With
    # west-positive arithmetic on east-positive input the peak moves to the 23 UTC hour.
    et = nz_day('start')
    assert int(np.argmax(et.ts_param['R_a'])) == 0
    # The same instant expressed in NZST labels (TZ 180°E) peaks in the 12 h period.
    data = {'T_mean': np.full(24, 20.0), 'RH_mean': np.full(24, 60.0), 'R_s': np.full(24, 0.5)}
    nzst = ETo(data, 'h', z_msl=300, lat=-43.5, lon=171.5, TZ_lon=180.0, day_of_year=np.full(24, 15),
               hour=np.arange(24), rs_rso_init=1.0)
    assert int(np.argmax(nzst.ts_param['R_a'])) == 12


def test_period_ending_labels_shift_by_one_hour():
    start = nz_day('start').ts_param['R_a']
    end = nz_day('end').ts_param['R_a']
    np.testing.assert_allclose(end, start)  # labels 1..24 'end' are the same periods as 0..23 'start'


def test_time_label_is_validated():
    with pytest.raises(ValueError, match='time_label'):
        nz_day('middle')


@pytest.mark.parametrize('freq', ['3h', 'month', '30min', '60min', 'T', 'x'])
def test_frequency_must_match_exactly(freq):
    data = {'T_mean': np.full(3, 20.0), 'RH_mean': np.full(3, 60.0), 'T_min': np.full(3, 10.0), 'T_max': np.full(3, 25.0)}
    with pytest.raises(ValueError, match='Unsupported frequency'):
        ETo(data, freq, z_msl=10, lat=-43.5, lon=171.5, TZ_lon=0.0, day_of_year=np.array([1, 2, 3]),
            hour=np.array([0, 1, 2]))


def three_days(cloud=(0.5, 0.9, 0.3)):
    """Hourly UTC series at 171.5°E: R_s = cloud factor of the day times clear-sky Rso."""
    n = 72
    hours = np.arange(n) % 24
    doy = 15 + np.arange(n) // 24
    clear = ETo({'T_mean': np.full(n, 15.0), 'RH_mean': np.full(n, 70.0)}, 'h', z_msl=300, lat=-43.5,
                lon=171.5, TZ_lon=0.0, day_of_year=doy, hour=hours, rs_rso_init=1.0).ts_param['R_so']
    # UTC hours 0-5 of day d are the NZ afternoon of that day (NZST = UTC+12): the day's cloud factor.
    # Sunset is near 08 UTC, so the FAO reference period (2-3 h before sunset) is the 05 UTC hour.
    # The dusk hours 06-07 get 0.7 and the NZ morning (UTC 12-23) 0.95, so a ratio taken from the
    # wrong hour (a dusk hour, the morning) is visible.
    day_cloud = np.array(cloud)[np.arange(n) // 24]
    rs = clear * np.select([hours <= 5, hours <= 11], [day_cloud, 0.7], 0.95)
    data = {'T_mean': np.full(n, 15.0), 'RH_mean': np.full(n, 70.0), 'U_z': np.full(n, 2.0), 'R_s': rs}
    return data, doy, hours


def run(data, doy, hours, sl, init):
    sub = {k: v[sl] for k, v in data.items()}
    return ETo(sub, 'h', z_msl=300, lat=-43.5, lon=171.5, TZ_lon=0.0, day_of_year=doy[sl], hour=hours[sl],
               rs_rso_init=init)


def test_night_uses_the_ratio_from_two_to_three_hours_before_sunset():
    data, doy, hours = three_days()
    et = run(data, doy, hours, slice(None), 1.0)
    p = et.ts_param
    night = p['R_so'] <= 0
    # Every night hour after the first evening carries that evening's ratio, never the morning's
    # 0.95 or the clear-sky 1.0.
    after_first_evening = night & (np.arange(72) > 12)
    assert after_first_evening.sum() > 15
    # In January the whole NZ night (about 09:30-18:00 UTC) lies inside one UTC day, whose afternoon
    # is the evening before it.
    expect = np.array([0.5, 0.9, 0.3])[np.arange(72) // 24]
    np.testing.assert_allclose(p['Rs_Rso'][after_first_evening], expect[after_first_evening])


def test_chunked_equals_unchunked_with_boundaries_at_night():
    # Boundaries placed in NZ night and low-sun hours (UTC 10-18 is 22:00-06:00 NZST), where the
    # carried state is used. A boundary at UTC 00 (NZ noon) would test nothing.
    data, doy, hours = three_days()
    whole = run(data, doy, hours, slice(None), 1.0)
    # Also every single cut, including those between the reference hour and dark, where the state
    # must be the reference ratio and not the last hour's own ratio.
    for cuts in ([14], [11, 40], [17, 38, 62], [19, 43], *([c] for c in range(1, 72))):
        edges = [0, *cuts, 72]
        init = 1.0
        parts = []
        for a, b in zip(edges[:-1], edges[1:]):
            et = run(data, doy, hours, slice(a, b), init)
            parts.append(et.ts_param['R_n'])
            init = et.rs_rso_last
        np.testing.assert_array_equal(np.concatenate(parts), whole.ts_param['R_n'])


def test_series_starting_at_night_warns_without_an_initial_ratio_and_not_with_one():
    data, doy, hours = three_days()
    with pytest.warns(UserWarning, match='starts at night'):
        run(data, doy, hours, slice(14, 30), None)
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        run(data, doy, hours, slice(14, 30), 0.7)


def test_raw_mode_keeps_negative_unrounded_values():
    # A saturated night (RH 100 %, so no vapour deficit) with net longwave loss: FAO-56 gives a small
    # negative value (dew). Example 19's own night value is +0.004 mm, shown as 0.00.
    et = ex19(2, 10.0, 100.0, 1.0, 0.0, rs_rso_init=0.8)
    raw = et.eto_fao(min_ETo=None, max_ETo=None, decimals=None)
    assert raw[0] < 0
    assert raw[0] != np.round(raw[0], 2)
    assert et.eto_fao()[0] == 0.0


def test_west_longitude_with_utc_labels_finds_the_evening_reference():
    # At 120°W the local evening falls after 00 UTC, so solar time must wrap into the previous day;
    # without the wrap the reference period is never found and nights keep the initial 1.0.
    n = 48
    hours = np.arange(n) % 24
    doy = 180 + np.arange(n) // 24
    base = dict(z_msl=100, lat=40.0, lon=-120.0, TZ_lon=0.0, day_of_year=doy, hour=hours)
    clear = ETo({'T_mean': np.full(n, 20.0), 'RH_mean': np.full(n, 50.0)}, 'h', rs_rso_init=1.0, **base).ts_param['R_so']
    et = ETo({'T_mean': np.full(n, 20.0), 'RH_mean': np.full(n, 50.0), 'R_s': 0.6 * clear}, 'h', rs_rso_init=1.0, **base)
    night = et.ts_param['R_so'] <= 0
    later_nights = night & (np.arange(n) > 24)
    assert later_nights.any()
    np.testing.assert_allclose(et.ts_param['Rs_Rso'][later_nights], 0.6)



# --- review thalweg-step0-code-1 ----------------------------------------------------------------


def test_reference_is_the_hour_two_to_three_hours_before_sunset():
    # Defect caught: a reference window one hour off (3-4 h before sunset). Each afternoon hour gets its
    # own cloud factor, so the carried night value identifies the hour it came from.
    n = 24
    hours = np.arange(n)
    doy = np.full(n, 15)
    base = dict(z_msl=300, lat=-43.5, lon=171.5, TZ_lon=0.0, day_of_year=doy, hour=hours, rs_rso_init=1.0)
    clear = ETo({'T_mean': np.full(n, 15.0), 'RH_mean': np.full(n, 70.0)}, 'h', **base).ts_param['R_so']
    factor = np.full(n, 0.95)
    factor[:8] = [0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75]  # UTC 0-7 = NZST 12-19
    et = ETo({'T_mean': np.full(n, 15.0), 'RH_mean': np.full(n, 70.0), 'R_s': factor * clear}, 'h', **base)
    p = et.ts_param
    night = p['R_so'] <= 0
    # Which afternoon hour satisfies FAO-56's window: compute it from the solar angle directly.
    phi = np.deg2rad(-43.5)
    delta = 0.409 * np.sin(2 * np.pi * 15 / 365 - 1.39)
    ws = np.arccos(-np.tan(phi) * np.tan(delta))
    b = 2 * np.pi * (15 - 81) / 364
    sc = 0.1645 * np.sin(2 * b) - 0.1255 * np.cos(b) - 0.025 * np.sin(b)
    w = np.pi / 12 * ((hours + 0.5) + 0.06667 * (171.5 - 0.0) + sc - 24 * ((hours + 0.5 + 0.06667 * 171.5 + sc) >= 24) - 12)
    ref = (w >= ws - 0.79) & (w <= ws - 0.52)
    assert ref.sum() == 1
    k = int(np.flatnonzero(ref)[0])
    np.testing.assert_allclose(p['Rs_Rso'][night & (hours > k)], factor[k])


def test_carried_ratio_is_the_capped_value():
    # Defect caught: carrying the raw ratio. A reference hour with R_s above clear sky carries 1.0.
    data, doy, hours = three_days(cloud=(1.4, 1.4, 1.4))
    et = run(data, doy, hours, slice(None), 0.5)
    p = et.ts_param
    later_nights = (p['R_so'] <= 0) & (np.arange(72) > 12)
    np.testing.assert_allclose(p['Rs_Rso'][later_nights], 1.0)


def test_rs_rso_is_floored_at_0_3():
    data, doy, hours = three_days(cloud=(0.05, 0.05, 0.05))
    et = run(data, doy, hours, slice(None), 0.05)
    r = et.ts_param['Rs_Rso']
    assert np.nanmin(r) == pytest.approx(0.3)
    later_nights = (et.ts_param['R_so'] <= 0) & (np.arange(72) > 12)
    np.testing.assert_allclose(r[later_nights], 0.3)
    assert (et.ts_param['R_n'][later_nights] < 0).all()  # net longwave stays a loss at night


def test_longitude_difference_wraps_across_the_antimeridian():
    a = nz_day('start', lon=183.5).ts_param['R_a']
    b = nz_day('start', lon=-176.5).ts_param['R_a']
    np.testing.assert_allclose(a, b)
    c = nz_day('start', lon=171.5, TZ_lon=180.0).ts_param['R_a']
    d = nz_day('start', lon=171.5, TZ_lon=-180.0).ts_param['R_a']
    np.testing.assert_allclose(c, d)


def test_sunrise_and_sunset_hours_integrate_only_the_sunlit_part():
    # Defect caught: integrating the whole hour, netting night (negative) against day. Compare each
    # hour's R_a with a fine numerical integral of the instantaneous extraterrestrial radiation.
    et = nz_day('start')
    ra = et.ts_param['R_a']
    phi = np.deg2rad(-43.5)
    for h in range(24):
        # UTC labels at 171.5°E: local solar time = UTC + 11.4 h, so UTC 13-23 fall on the next solar day.
        b0 = 2 * np.pi * (15 - 81) / 364
        sc0 = 0.1645 * np.sin(2 * b0) - 0.1255 * np.cos(b0) - 0.025 * np.sin(b0)
        day = 15 + int(np.floor((h + 0.5 + 0.06667 * 171.5 + sc0) / 24))
        delta = 0.409 * np.sin(2 * np.pi * day / 365 - 1.39)
        dr = 1 + 0.033 * np.cos(2 * np.pi * day / 365)
        # The equation of time (S_c) is taken from the label's day, as the package does; its change
        # across one day is under a minute.
        t = h + (np.arange(600) + 0.5) / 600
        w = np.pi / 12 * (((t + 0.06667 * 171.5 + sc0) % 24) - 12)
        inst = 0.082 * dr * np.maximum(np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.cos(w), 0)
        assert ra[h] == pytest.approx(inst.mean() * 60, abs=2e-3), h
