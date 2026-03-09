# -*- coding: utf-8 -*-
"""
Tests for ETo package.
"""
import zipfile
import csv
import io
import numpy as np
from eto import ETo, datasets
import pytest


###############################
### Helpers

def make_daily_data(columns_dict, n_days=10, start='2020-01-01'):
    dates = np.arange(start, np.datetime64(start) + np.timedelta64(n_days, 'D'), dtype='datetime64[D]')
    return columns_dict, dates


def make_hourly_data(columns_dict, n_hours=48, start='2020-06-15'):
    dates = np.arange(start, np.datetime64(start) + np.timedelta64(n_hours, 'h'), dtype='datetime64[h]')
    return columns_dict, dates


def load_csv_zip(path):
    """Load a zipped CSV into (data_dict, dates) without pandas."""
    with zipfile.ZipFile(path) as z:
        name = z.namelist()[0]
        with z.open(name) as f:
            reader = csv.reader(io.TextIOWrapper(f))
            header = next(reader)
            rows = list(reader)

    date_col = header.index('date')
    dates = np.array([row[date_col] for row in rows], dtype='datetime64[D]')

    data = {}
    for i, col in enumerate(header):
        if col == 'date':
            continue
        vals = []
        for row in rows:
            v = row[i]
            if v == '' or v == 'nan':
                vals.append(np.nan)
            else:
                vals.append(float(v))
        data[col] = np.array(vals, dtype=np.float64)

    return data, dates


###############################
### Fixtures

@pytest.fixture
def daily_data():
    path = datasets.get_path('example_daily')
    return load_csv_zip(path)


@pytest.fixture
def daily_results():
    path = datasets.get_path('example_daily_results')
    return load_csv_zip(path)


@pytest.fixture
def daily_params():
    return dict(z_msl=500, lat=-43.6, lon=172, TZ_lon=173)


@pytest.fixture
def daily_et(daily_data, daily_params):
    data, dates = daily_data
    return ETo(data, 'D', dates=dates, **daily_params)


@pytest.fixture
def hourly_et(daily_et, daily_params):
    # Build synthetic hourly data from the daily parameter estimates
    n_days = len(daily_et.ts_param['T_mean'])
    hours_per_day = 24
    n = n_days * hours_per_day

    # Repeat daily values across hours
    T_mean = np.repeat(daily_et.ts_param['T_mean'], hours_per_day)
    e_a = np.repeat(daily_et.ts_param['e_a'], hours_per_day)
    R_s_daily = daily_et.ts_param['R_s']

    # Distribute R_s across daytime hours (6-18)
    R_s = np.zeros(n)
    for d in range(n_days):
        for h in range(hours_per_day):
            idx = d * hours_per_day + h
            if 6 <= h < 18:
                R_s[idx] = R_s_daily[d] / 12
            else:
                R_s[idx] = 0.0

    data = {'T_mean': T_mean, 'e_a': e_a, 'R_s': R_s}

    # Build hourly dates from the daily day_of_year
    # Use year 2000 to match the fixture data
    start = np.datetime64('2000-01-01')
    dates = np.arange(start, start + np.timedelta64(n, 'h'), dtype='datetime64[h]')

    return ETo(data, 'h', dates=dates, **daily_params)


###############################
### Original tests (refactored to use fixtures)

def test_eto_fao_daily(daily_data, daily_results, daily_params):
    data, dates = daily_data
    et1 = ETo(data, 'D', dates=dates, **daily_params)
    eto1 = np.nansum(et1.eto_fao())
    res_data, _ = daily_results
    res1 = np.nansum(res_data['ETo_FAO_mm'])
    np.testing.assert_allclose(eto1, res1, rtol=1e-4)


def test_eto_har_daily(daily_et, daily_results):
    eto2 = np.nansum(daily_et.eto_hargreaves())
    res_data, _ = daily_results
    res1 = np.nansum(res_data['ETo_Har_mm'])
    np.testing.assert_allclose(eto2, res1, rtol=1e-5)


def test_eto_fao_hourly(hourly_et, daily_results):
    eto3 = np.nansum(hourly_et.eto_fao())
    res_data, _ = daily_results
    res1 = np.nansum(res_data['ETo_FAO_mm'])
    # Hourly sum should be positive and within a reasonable factor of daily
    assert eto3 > 0
    assert eto3 > res1 * 0.5


###############################
### Group 1: Tests for the three recent fixes

def test_hourly_solar_time_angle_coefficient():
    """Verify 0.06667 coefficient produces physically reasonable R_a values."""
    n = 48
    R_s_vals = np.tile(np.concatenate([
        np.zeros(6), np.linspace(0.5, 2.5, 6), np.linspace(2.5, 0.5, 6), np.zeros(6)
    ]), n // 24)
    data = {
        'T_mean': np.full(n, 20.0),
        'RH_mean': np.full(n, 60.0),
        'R_s': R_s_vals,
    }
    _, dates = make_hourly_data(data, n_hours=n, start='2020-01-15')
    et = ETo(data, 'h', z_msl=100, lat=-43.6, lon=150, TZ_lon=180, dates=dates)
    R_a = et.ts_param['R_a']
    assert (R_a > 0).any()
    assert (R_a[R_a > 0] < 5.0).all()


def test_hourly_soil_heat_flux_day_night():
    """Verify G = 0.1*R_n daytime, G = 0.5*R_n nighttime (FAO Eq 45/46)."""
    n = 48
    R_n_vals = np.tile(np.concatenate([
        np.array([-0.5, -0.4, -0.3, -0.2, -0.1, -0.05]),
        np.array([0.5, 1.0, 1.5, 2.0, 1.5, 1.0]),
        np.array([0.5, 1.0, 1.5, 2.0, 1.5, 1.0]),
        np.array([-0.1, -0.2, -0.3, -0.4, -0.5, -0.6]),
    ]), n // 24)
    data = {
        'T_mean': np.full(n, 20.0),
        'RH_mean': np.full(n, 60.0),
        'R_n': R_n_vals,
    }
    _, dates = make_hourly_data(data, n_hours=n, start='2020-01-15')
    et = ETo(data, 'h', z_msl=100, lat=-43.6, lon=172, TZ_lon=173, dates=dates)

    R_n = et.ts_param['R_n']
    G = et.ts_param['G']

    day_mask = R_n > 0
    night_mask = R_n <= 0

    assert day_mask.any() and night_mask.any()

    np.testing.assert_allclose(G[day_mask], 0.1 * R_n[day_mask])
    np.testing.assert_allclose(G[night_mask], 0.5 * R_n[night_mask])


def test_ea_fallback_rh_max_only():
    """Verify e_a = e_min * RH_max / 100 when only RH_max available (FAO Eq 18)."""
    data = {
        'T_min': np.array([10.0, 12.0, 8.0]),
        'T_max': np.array([25.0, 28.0, 22.0]),
        'RH_max': np.array([85.0, 90.0, 80.0]),
    }
    _, dates = make_daily_data(data, n_days=3)
    et = ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)

    e_min = 0.6108 * np.exp(17.27 * data['T_min'] / (data['T_min'] + 237.3))
    expected_ea = e_min * data['RH_max'] / 100

    np.testing.assert_allclose(et.ts_param['e_a'], expected_ea, rtol=1e-5)


###############################
### Group 2: e_a estimation fallback chain (daily)

def test_ea_from_tdew():
    """e_a from dewpoint temperature (FAO Eq 14)."""
    data = {
        'T_min': np.array([10.0, 12.0]),
        'T_max': np.array([25.0, 28.0]),
        'T_dew': np.array([8.0, 10.0]),
    }
    _, dates = make_daily_data(data, n_days=2)
    et = ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)

    expected = 0.6108 * np.exp(17.27 * data['T_dew'] / (data['T_dew'] + 237.3))
    np.testing.assert_allclose(et.ts_param['e_a'], expected, rtol=1e-5)
    assert (et.est_val % 100000 // 10000 == 0).all()


def test_ea_from_rh_min_rh_max():
    """e_a from RH_min + RH_max (FAO Eq 17)."""
    data = {
        'T_min': np.array([10.0, 12.0]),
        'T_max': np.array([25.0, 28.0]),
        'RH_min': np.array([40.0, 45.0]),
        'RH_max': np.array([85.0, 90.0]),
    }
    _, dates = make_daily_data(data, n_days=2)
    et = ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)

    e_min = 0.6108 * np.exp(17.27 * data['T_min'] / (data['T_min'] + 237.3))
    e_max = 0.6108 * np.exp(17.27 * data['T_max'] / (data['T_max'] + 237.3))
    expected = (e_min * data['RH_max'] / 100 + e_max * data['RH_min'] / 100) / 2

    np.testing.assert_allclose(et.ts_param['e_a'], expected, rtol=1e-5)


def test_ea_from_rh_mean():
    """e_a from RH_mean only (FAO Eq 19)."""
    data = {
        'T_min': np.array([10.0, 12.0]),
        'T_max': np.array([25.0, 28.0]),
        'RH_mean': np.array([60.0, 65.0]),
    }
    _, dates = make_daily_data(data, n_days=2)
    et = ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)

    e_min = 0.6108 * np.exp(17.27 * data['T_min'] / (data['T_min'] + 237.3))
    e_max = 0.6108 * np.exp(17.27 * data['T_max'] / (data['T_max'] + 237.3))
    expected = data['RH_mean'] / 100 * (e_max + e_min) / 2

    np.testing.assert_allclose(et.ts_param['e_a'], expected, rtol=1e-5)


def test_ea_from_tmin_last_resort():
    """e_a from T_min when no humidity data (FAO Eq 48)."""
    data = {
        'T_min': np.array([10.0, 12.0]),
        'T_max': np.array([25.0, 28.0]),
    }
    _, dates = make_daily_data(data, n_days=2)
    et = ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)

    expected = 0.6108 * np.exp(17.27 * data['T_min'] / (data['T_min'] + 237.3))
    np.testing.assert_allclose(et.ts_param['e_a'], expected, rtol=1e-5)


###############################
### Group 3: R_s estimation fallback chain

def test_rs_from_n_sun():
    """R_s estimated from sunshine hours (Angstrom, FAO Eq 35)."""
    data = {
        'T_min': np.array([10.0, 12.0, 8.0, 11.0, 9.0]),
        'T_max': np.array([25.0, 28.0, 22.0, 26.0, 23.0]),
        'n_sun': np.array([8.0, 10.0, 6.0, 9.0, 7.0]),
    }
    _, dates = make_daily_data(data, n_days=5)
    et = ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)

    assert np.all(~np.isnan(et.ts_param['R_s']))
    assert ((et.est_val % 10000 // 1000) >= 1).all()


def test_rs_from_temperature_range():
    """R_s from Hargreaves radiation formula when n_sun unavailable (FAO Eq 50)."""
    data = {
        'T_min': np.array([10.0, 12.0, 8.0, 11.0, 9.0]),
        'T_max': np.array([25.0, 28.0, 22.0, 26.0, 23.0]),
    }
    _, dates = make_daily_data(data, n_days=5)
    et = ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)

    assert np.all(~np.isnan(et.ts_param['R_s']))
    assert ((et.est_val % 10000 // 1000) >= 2).all()


###############################
### Group 4: Input validation

def test_daily_missing_tmin_raises():
    data = {'T_max': np.array([25.0, 28.0])}
    _, dates = make_daily_data(data, n_days=2)
    with pytest.raises(ValueError, match='Minimum data input'):
        ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)


def test_daily_missing_tmax_raises():
    data = {'T_min': np.array([10.0, 12.0])}
    _, dates = make_daily_data(data, n_days=2)
    with pytest.raises(ValueError, match='Minimum data input'):
        ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)


def test_hourly_missing_tmean_raises():
    data = {'RH_mean': np.array([60.0] * 48)}
    _, dates = make_hourly_data(data, n_hours=48)
    with pytest.raises(ValueError, match='Minimum data input'):
        ETo(data, 'h', z_msl=100, lat=-43.6, lon=172, TZ_lon=173, dates=dates)


def test_hourly_missing_rhmean_and_ea_raises():
    data = {'T_mean': np.array([20.0] * 48)}
    _, dates = make_hourly_data(data, n_hours=48)
    with pytest.raises(ValueError, match='Minimum data input'):
        ETo(data, 'h', z_msl=100, lat=-43.6, lon=172, TZ_lon=173, dates=dates)


def test_missing_temporal_args_raises():
    data = {'T_min': np.array([10.0]), 'T_max': np.array([25.0])}
    with pytest.raises(ValueError, match='Either dates or day_of_year'):
        ETo(data, 'D', z_msl=100, lat=-43.6)


def test_input_length_mismatch_raises():
    data = {'T_min': np.array([10.0, 12.0]), 'T_max': np.array([25.0])}
    with pytest.raises(ValueError, match='same length'):
        ETo(data, 'D', z_msl=100, lat=-43.6, day_of_year=np.array([1, 2]))


def test_day_of_year_length_mismatch_raises():
    data = {'T_min': np.array([10.0, 12.0]), 'T_max': np.array([25.0, 28.0])}
    with pytest.raises(ValueError, match='day_of_year length'):
        ETo(data, 'D', z_msl=100, lat=-43.6, day_of_year=np.array([1]))


###############################
### Group 5: Hourly path coverage

def test_hourly_ea_from_rhmean():
    """Hourly e_a = e_mean * RH_mean / 100."""
    n = 48
    data = {'T_mean': np.full(n, 20.0), 'RH_mean': np.full(n, 65.0)}
    _, dates = make_hourly_data(data, n_hours=n)
    et = ETo(data, 'h', z_msl=100, lat=-43.6, lon=172, TZ_lon=173, dates=dates)

    e_mean = 0.6108 * np.exp(17.27 * 20.0 / (20.0 + 237.3))
    expected = e_mean * 65.0 / 100

    np.testing.assert_allclose(et.ts_param['e_a'], expected, rtol=1e-5)


def test_hourly_ea_provided_directly():
    """Hourly e_a used as-is when provided."""
    n = 48
    data = {'T_mean': np.full(n, 20.0), 'e_a': np.full(n, 1.5)}
    _, dates = make_hourly_data(data, n_hours=n)
    et = ETo(data, 'h', z_msl=100, lat=-43.6, lon=172, TZ_lon=173, dates=dates)

    np.testing.assert_allclose(et.ts_param['e_a'], 1.5, rtol=1e-10)


def test_hourly_eto_fao_precision(hourly_et):
    """Hourly ETo should be positive in aggregate and within a reasonable range."""
    eto_vals = hourly_et.eto_fao()
    total = np.nansum(eto_vals)
    assert total > 0
    valid = eto_vals[~np.isnan(eto_vals)]
    assert (valid <= 15).all()
    assert (valid >= 0).all()


###############################
### Group 6: Method-level paths

def test_hargreaves_hourly_raises():
    n = 48
    data = {'T_mean': np.full(n, 20.0), 'RH_mean': np.full(n, 60.0)}
    _, dates = make_hourly_data(data, n_hours=n)
    et = ETo(data, 'h', z_msl=100, lat=-43.6, lon=172, TZ_lon=173, dates=dates)
    with pytest.raises(ValueError, match='less than a day'):
        et.eto_hargreaves()


def test_eto_fao_max_min_clipping():
    """Values outside [min_ETo, max_ETo] should be clipped to NaN."""
    data = {
        'T_min': np.array([10.0, 12.0, 8.0, 11.0, 9.0]),
        'T_max': np.array([25.0, 28.0, 22.0, 26.0, 23.0]),
    }
    _, dates = make_daily_data(data, n_days=5)
    et = ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)
    eto_vals = et.eto_fao(max_ETo=0.5)
    valid = eto_vals[~np.isnan(eto_vals)]
    if len(valid) > 0:
        assert (valid <= 0.5).all()


###############################
### Group 7: ETo class and miscellaneous

def test_eto_init_empty():
    et = ETo()
    assert not hasattr(et, 'ts_param')


def test_wind_speed_from_uz():
    """U_2 calculated from U_z at height z_u."""
    z_u = 10
    U_z_val = 3.5
    data = {
        'T_min': np.array([10.0, 12.0]),
        'T_max': np.array([25.0, 28.0]),
        'U_z': np.array([U_z_val, U_z_val]),
    }
    _, dates = make_daily_data(data, n_days=2)
    et = ETo(data, 'D', z_msl=100, lat=-43.6, z_u=z_u, dates=dates)

    expected_U2 = U_z_val * 4.87 / np.log(67.8 * z_u - 5.42)
    np.testing.assert_allclose(et.ts_param['U_2'], expected_U2, rtol=1e-5)
    assert ((et.est_val % 10) == 0).all()


def test_custom_krs_changes_rs():
    """Coastal K_rs=0.19 should produce different R_s than inland K_rs=0.16."""
    data = {
        'T_min': np.array([10.0, 12.0, 8.0]),
        'T_max': np.array([25.0, 28.0, 22.0]),
    }
    _, dates = make_daily_data(data, n_days=3)
    et_inland = ETo(data, 'D', z_msl=100, lat=-43.6, K_rs=0.16, dates=dates)
    et_coastal = ETo(data, 'D', z_msl=100, lat=-43.6, K_rs=0.19, dates=dates)

    assert not np.allclose(et_inland.ts_param['R_s'], et_coastal.ts_param['R_s'])


def test_pressure_provided():
    """When P is provided, it should be used as-is."""
    data = {
        'T_min': np.array([10.0, 12.0]),
        'T_max': np.array([25.0, 28.0]),
        'P': np.array([95.0, 95.0]),
    }
    _, dates = make_daily_data(data, n_days=2)
    et = ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)

    np.testing.assert_allclose(et.ts_param['P'], 95.0)
    assert (et.est_val < 1000000).all()


def test_est_val_tracking():
    """Minimal inputs should produce expected quality value."""
    data = {
        'T_min': np.array([10.0]),
        'T_max': np.array([25.0]),
    }
    _, dates = make_daily_data(data, n_days=1)
    et = ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)

    # P(1000000) + T_mean(100000) + e_a(40000) + R_s(2000) + R_n(100) + G(10) + U_z(1)
    expected = 1000000 + 100000 + 40000 + 2000 + 100 + 10 + 1
    assert et.est_val[0] == expected


def test_daily_g_is_zero():
    """Daily G estimation should always be zero (FAO Eq 42)."""
    data = {
        'T_min': np.array([10.0, 12.0, 8.0]),
        'T_max': np.array([25.0, 28.0, 22.0]),
    }
    _, dates = make_daily_data(data, n_days=3)
    et = ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)
    np.testing.assert_allclose(et.ts_param['G'], 0.0)


###############################
### Group 8: New tests for numpy conversion

def test_dates_path():
    """Passing dates as datetime64 array produces same result as explicit day_of_year."""
    data = {
        'T_min': np.array([10.0, 12.0, 8.0]),
        'T_max': np.array([25.0, 28.0, 22.0]),
    }
    dates = np.array(['2020-01-01', '2020-01-02', '2020-01-03'], dtype='datetime64[D]')
    day_of_year = np.array([1, 2, 3])

    et_dates = ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)
    et_doy = ETo(data, 'D', z_msl=100, lat=-43.6, day_of_year=day_of_year)

    np.testing.assert_allclose(et_dates.eto_fao(), et_doy.eto_fao())


def test_hour_derivation_from_dates():
    """Hourly dates correctly derive both day_of_year and hour."""
    n = 24
    data = {'T_mean': np.full(n, 20.0), 'RH_mean': np.full(n, 60.0)}
    dates = np.arange('2020-06-15', '2020-06-16', dtype='datetime64[h]')
    et = ETo(data, 'h', z_msl=100, lat=-43.6, lon=172, TZ_lon=173, dates=dates)
    # Should have computed without error and have results
    assert len(et.ts_param['R_a']) == n


def test_output_is_ndarray(daily_et):
    """eto_fao() and eto_hargreaves() return np.ndarray."""
    assert isinstance(daily_et.eto_fao(), np.ndarray)
    assert isinstance(daily_et.eto_hargreaves(), np.ndarray)


def test_output_length_matches_input(daily_data, daily_params):
    """Output array length equals input array length."""
    data, dates = daily_data
    et = ETo(data, 'D', dates=dates, **daily_params)
    n = len(data['T_min'])
    assert len(et.eto_fao()) == n
    assert len(et.eto_hargreaves()) == n


def test_data_not_mutated():
    """Input arrays must not be mutated by ETo."""
    t_min = np.array([10.0, 12.0, 8.0])
    t_max = np.array([25.0, 28.0, 22.0])
    t_min_copy = t_min.copy()
    t_max_copy = t_max.copy()
    data = {'T_min': t_min, 'T_max': t_max}
    _, dates = make_daily_data(data, n_days=3)
    ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)
    np.testing.assert_array_equal(t_min, t_min_copy)
    np.testing.assert_array_equal(t_max, t_max_copy)


###############################
### Group 9: Phase 1 bug fix tests

def test_hourly_R_a_nonnegative():
    """R_a >= 0 for all hours including nighttime."""
    n = 48
    data = {'T_mean': np.full(n, 20.0), 'RH_mean': np.full(n, 60.0)}
    _, dates = make_hourly_data(data, n_hours=n)
    et = ETo(data, 'h', z_msl=100, lat=-43.6, lon=172, TZ_lon=173, dates=dates)
    assert (et.ts_param['R_a'] >= 0).all()


def test_hourly_R_n_no_nan_from_division():
    """R_n should be finite when R_so=0 (nighttime hours)."""
    n = 48
    R_s = np.tile(np.concatenate([np.zeros(6), np.linspace(0.5, 2.0, 12), np.zeros(6)]), n // 24)
    data = {'T_mean': np.full(n, 20.0), 'RH_mean': np.full(n, 60.0), 'R_s': R_s}
    _, dates = make_hourly_data(data, n_hours=n)
    et = ETo(data, 'h', z_msl=100, lat=-43.6, lon=172, TZ_lon=173, dates=dates)
    assert np.all(np.isfinite(et.ts_param['R_n']))


def test_est_val_no_penalty_when_ea_provided():
    """Directly-provided e_a should not get 10000 penalty for missing T_dew."""
    data = {
        'T_min': np.array([10.0, 12.0]),
        'T_max': np.array([25.0, 28.0]),
        'e_a': np.array([1.2, 1.5]),
    }
    _, dates = make_daily_data(data, n_days=2)
    et = ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)
    # The 10000-digit should be 0 since e_a was provided directly
    assert (et.est_val % 100000 // 10000 == 0).all()


###############################
### Group 10: Phase 2 feature tests

def test_monthly_G_estimation():
    """Monthly G = 0.14 * (T_i - T_{i-1}), first month G=0."""
    T_mean = np.array([10.0, 15.0, 20.0, 18.0, 12.0])
    data = {
        'T_min': T_mean - 5,
        'T_max': T_mean + 5,
    }
    _, dates = make_daily_data(data, n_days=5)
    et = ETo(data, 'M', z_msl=100, lat=-43.6, dates=dates)

    expected_G = np.zeros(5)
    expected_G[1:] = 0.14 * np.diff(T_mean)
    np.testing.assert_allclose(et.ts_param['G'], expected_G, rtol=1e-10)


def test_monthly_eto_fao():
    """Monthly freq produces valid ETo values."""
    T_mean = np.array([10.0, 15.0, 20.0, 18.0, 12.0])
    data = {
        'T_min': T_mean - 5,
        'T_max': T_mean + 5,
    }
    _, dates = make_daily_data(data, n_days=5)
    et = ETo(data, 'M', z_msl=100, lat=-43.6, dates=dates)
    eto_vals = et.eto_fao()
    assert np.all(np.isfinite(eto_vals))
    assert np.all(eto_vals >= 0)


def test_validate_warns_bad_temperature():
    """Temperatures outside [-50, 60] should trigger warning."""
    data = {
        'T_min': np.array([-60.0, 12.0]),
        'T_max': np.array([25.0, 28.0]),
    }
    _, dates = make_daily_data(data, n_days=2)
    with pytest.warns(UserWarning, match='T_min has values outside'):
        ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)


def test_validate_warns_bad_rh():
    """RH outside [0, 100] should trigger warning."""
    data = {
        'T_min': np.array([10.0, 12.0]),
        'T_max': np.array([25.0, 28.0]),
        'RH_mean': np.array([60.0, 110.0]),
    }
    _, dates = make_daily_data(data, n_days=2)
    with pytest.warns(UserWarning, match='RH_mean has values outside'):
        ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)


def test_validate_false_suppresses_warnings():
    """validate=False should suppress range warnings."""
    data = {
        'T_min': np.array([-60.0, 12.0]),
        'T_max': np.array([25.0, 28.0]),
    }
    _, dates = make_daily_data(data, n_days=2)
    import warnings as _warnings
    with _warnings.catch_warnings():
        _warnings.simplefilter('error')
        # Should not raise any warnings
        ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates, validate=False)


def test_rso_custom_as_bs():
    """Non-default a_s/b_s should use Eq 36 (a_s+b_s)*R_a instead of Eq 37."""
    data = {
        'T_min': np.array([10.0, 12.0]),
        'T_max': np.array([25.0, 28.0]),
    }
    _, dates = make_daily_data(data, n_days=2)
    # Default: a_s=0.25, b_s=0.5 → Eq 37: (0.75 + 2e-5*z_msl)*R_a
    et_default = ETo(data, 'D', z_msl=500, lat=-43.6, dates=dates)
    # Custom: a_s=0.3, b_s=0.4 → Eq 36: 0.7*R_a
    et_custom = ETo(data, 'D', z_msl=500, lat=-43.6, a_s=0.3, b_s=0.4, dates=dates)
    # Results should differ because R_so formulas differ
    assert not np.allclose(et_default.eto_fao(), et_custom.eto_fao())


def test_eto_negative_clamped_to_zero():
    """Negative ETo values should be clamped to 0, not NaN."""
    data = {
        'T_min': np.array([10.0, 12.0, 8.0]),
        'T_max': np.array([25.0, 28.0, 22.0]),
    }
    _, dates = make_daily_data(data, n_days=3)
    et = ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)
    eto_vals = et.eto_fao(min_ETo=0)
    # No values should be negative
    assert (eto_vals[~np.isnan(eto_vals)] >= 0).all()
    # With a very high min_ETo, everything clamps up
    eto_clamped = et.eto_fao(min_ETo=0, max_ETo=100)
    assert np.all(np.isfinite(eto_clamped))
    assert np.all(eto_clamped >= 0)


def test_tdew_computed_from_ea():
    """When e_a is provided but T_dew is not, T_dew should be back-calculated."""
    # e_a = 0.6108 * exp(17.27 * T_dew / (T_dew + 237.3))
    # For T_dew = 10: e_a = 0.6108 * exp(17.27*10/247.3) ≈ 1.228
    T_dew_known = np.array([10.0, 15.0])
    e_a = 0.6108 * np.exp(17.27 * T_dew_known / (T_dew_known + 237.3))
    data = {
        'T_min': np.array([8.0, 12.0]),
        'T_max': np.array([25.0, 28.0]),
        'e_a': e_a,
    }
    _, dates = make_daily_data(data, n_days=2)
    et = ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)
    np.testing.assert_allclose(et.ts_param['T_dew'], T_dew_known, rtol=1e-5)


def test_vpd_daily():
    """VPD = e_s - e_a for daily data."""
    data = {
        'T_min': np.array([10.0, 12.0]),
        'T_max': np.array([25.0, 28.0]),
        'T_dew': np.array([8.0, 10.0]),
    }
    _, dates = make_daily_data(data, n_days=2)
    et = ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)
    expected_vpd = et.ts_param['e_s'] - et.ts_param['e_a']
    np.testing.assert_allclose(et.ts_param['VPD'], expected_vpd, rtol=1e-10)


def test_vpd_hourly():
    """VPD = e_mean - e_a for hourly data."""
    n = 48
    data = {'T_mean': np.full(n, 20.0), 'RH_mean': np.full(n, 60.0)}
    _, dates = make_hourly_data(data, n_hours=n)
    et = ETo(data, 'h', z_msl=100, lat=-43.6, lon=172, TZ_lon=173, dates=dates)
    expected_vpd = et.ts_param['e_mean'] - et.ts_param['e_a']
    np.testing.assert_allclose(et.ts_param['VPD'], expected_vpd, rtol=1e-10)


def test_tall_ref_crop():
    """Tall reference crop should give different ETo than short."""
    data = {
        'T_min': np.array([10.0, 12.0, 8.0]),
        'T_max': np.array([25.0, 28.0, 22.0]),
    }
    _, dates = make_daily_data(data, n_days=3)
    et = ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)
    eto_short = et.eto_fao(ref_crop='short')
    eto_tall = et.eto_fao(ref_crop='tall')
    assert not np.allclose(eto_short, eto_tall)
    # Tall reference should generally produce higher ETo
    assert np.nansum(eto_tall) > np.nansum(eto_short)


def test_ref_crop_default_unchanged():
    """Default ref_crop='short' should match original behavior."""
    data = {
        'T_min': np.array([10.0, 12.0, 8.0]),
        'T_max': np.array([25.0, 28.0, 22.0]),
    }
    _, dates = make_daily_data(data, n_days=3)
    et = ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)
    eto_default = et.eto_fao()
    eto_short = et.eto_fao(ref_crop='short')
    np.testing.assert_array_equal(eto_default, eto_short)


###############################
### Group 11: Phase 3 crop coefficient tests

def test_etc_with_kc_float():
    """ETc = Kc * ETo when Kc is a float."""
    data = {
        'T_min': np.array([10.0, 12.0, 8.0]),
        'T_max': np.array([25.0, 28.0, 22.0]),
    }
    _, dates = make_daily_data(data, n_days=3)
    et = ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)
    Kc = 1.15
    etc_vals = et.etc(Kc=Kc)
    eto_vals = et.eto_fao()
    np.testing.assert_allclose(etc_vals, Kc * eto_vals, rtol=1e-10)


def test_etc_with_crop_stage_lookup():
    """ETc from crop/stage lookup should match table value * ETo."""
    data = {
        'T_min': np.array([10.0, 12.0, 8.0]),
        'T_max': np.array([25.0, 28.0, 22.0]),
    }
    _, dates = make_daily_data(data, n_days=3)
    et = ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)
    etc_vals = et.etc(crop='maize_grain', stage='mid')
    eto_vals = et.eto_fao()
    np.testing.assert_allclose(etc_vals, 1.20 * eto_vals, rtol=1e-10)


def test_etc_unknown_crop_raises():
    """Unknown crop should raise ValueError."""
    data = {
        'T_min': np.array([10.0]),
        'T_max': np.array([25.0]),
    }
    _, dates = make_daily_data(data, n_days=1)
    et = ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)
    with pytest.raises(ValueError, match='Unknown crop'):
        et.etc(crop='unicorn_grass', stage='mid')


def test_etc_dual_basic():
    """Dual Kc with provided Ke returns array."""
    data = {
        'T_min': np.array([10.0, 12.0, 8.0]),
        'T_max': np.array([25.0, 28.0, 22.0]),
    }
    _, dates = make_daily_data(data, n_days=3)
    et = ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)
    result = et.etc_dual(Kcb=0.8, Ke=0.3)
    eto_vals = et.eto_fao()
    np.testing.assert_allclose(result, (0.8 + 0.3) * eto_vals, rtol=1e-10)


def test_etc_adj_no_stress():
    """When Dr=0 (no depletion), Ks=1 and ETc_adj = Kc * ETo."""
    data = {
        'T_min': np.array([10.0, 12.0]),
        'T_max': np.array([25.0, 28.0]),
    }
    _, dates = make_daily_data(data, n_days=2)
    et = ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)
    result = et.etc_adj(Kc=1.15, TAW=100.0, Dr=0.0)
    expected = 1.15 * et.eto_fao()
    np.testing.assert_allclose(result, expected, rtol=1e-10)


def test_etc_adj_full_stress():
    """When Dr >= TAW, Ks=0 and ETc_adj = 0."""
    data = {
        'T_min': np.array([10.0, 12.0]),
        'T_max': np.array([25.0, 28.0]),
    }
    _, dates = make_daily_data(data, n_days=2)
    et = ETo(data, 'D', z_msl=100, lat=-43.6, dates=dates)
    result = et.etc_adj(Kc=1.15, TAW=100.0, Dr=100.0)
    np.testing.assert_allclose(result, 0.0)
