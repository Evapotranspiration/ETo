# -*- coding: utf-8 -*-
"""
Tests for ETo package.
"""
import pandas as pd
import numpy as np
from eto import ETo, datasets
import pytest


###############################
### Helpers

def make_daily_df(columns_dict, n_days=10, start='2020-01-01'):
    index = pd.date_range(start, periods=n_days, freq='D')
    return pd.DataFrame(columns_dict, index=index)


def make_hourly_df(columns_dict, n_hours=48, start='2020-06-15'):
    index = pd.date_range(start, periods=n_hours, freq='h')
    return pd.DataFrame(columns_dict, index=index)


###############################
### Fixtures

@pytest.fixture
def daily_data():
    example1 = datasets.get_path('example_daily')
    return pd.read_csv(example1, parse_dates=True, index_col='date', compression='zip')


@pytest.fixture
def daily_results():
    results1 = datasets.get_path('example_daily_results')
    return pd.read_csv(results1, parse_dates=True, index_col='date', compression='zip')


@pytest.fixture
def daily_params():
    return dict(z_msl=500, lat=-43.6, lon=172, TZ_lon=173)


@pytest.fixture
def daily_et(daily_data, daily_params):
    return ETo(daily_data, 'D', **daily_params)


@pytest.fixture
def hourly_et(daily_et, daily_params):
    tsdata2 = daily_et.ts_param[['R_s', 'T_mean', 'e_a']]
    tsdata3 = daily_et.tsreg(tsdata2, 'h', 'time')
    return ETo(tsdata3, 'h', **daily_params)


###############################
### Original tests (refactored to use fixtures)

def test_eto_fao_daily(daily_data, daily_results, daily_params):
    et1 = ETo(daily_data, 'D', **daily_params)
    eto1 = et1.eto_fao().sum()
    res1 = daily_results['ETo_FAO_mm'].sum()
    assert eto1 == res1


def test_eto_har_daily(daily_et, daily_results):
    eto2 = daily_et.eto_hargreaves().sum()
    res1 = daily_results['ETo_Har_mm'].sum()
    assert eto2 == res1


def test_eto_fao_hourly(hourly_et, daily_results):
    eto3 = hourly_et.eto_fao().sum()
    res1 = daily_results['ETo_FAO_mm'].sum()
    assert eto3 > res1


###############################
### Group 1: Tests for the three recent fixes

def test_hourly_solar_time_angle_coefficient():
    """Verify 0.06667 coefficient produces physically reasonable R_a values."""
    n = 48
    # Use southern hemisphere summer for positive daytime R_a
    # Provide R_s so R_n can be computed (hourly can't estimate R_s)
    R_s_vals = np.tile(np.concatenate([
        np.zeros(6), np.linspace(0.5, 2.5, 6), np.linspace(2.5, 0.5, 6), np.zeros(6)
    ]), n // 24)
    df = make_hourly_df({
        'T_mean': np.full(n, 20.0),
        'RH_mean': np.full(n, 60.0),
        'R_s': R_s_vals,
    }, start='2020-01-15')
    # Use a large TZ_lon - lon difference to amplify any coefficient error
    et = ETo(df, 'h', z_msl=100, lat=-43.6, lon=150, TZ_lon=180)
    R_a = et.ts_param['R_a']
    # Must have some positive (daytime) values
    assert (R_a > 0).any()
    # Daytime R_a should be bounded (< ~5 MJ/m2 per hour)
    assert (R_a[R_a > 0] < 5.0).all()


def test_hourly_soil_heat_flux_day_night():
    """Verify G = 0.1*R_n daytime, G = 0.5*R_n nighttime (FAO Eq 45/46)."""
    n = 48
    # Provide R_n directly with known positive (day) and negative (night) values
    # to isolate G estimation logic from R_n computation
    R_n_vals = np.tile(np.concatenate([
        np.array([-0.5, -0.4, -0.3, -0.2, -0.1, -0.05]),  # night
        np.array([0.5, 1.0, 1.5, 2.0, 1.5, 1.0]),          # day
        np.array([0.5, 1.0, 1.5, 2.0, 1.5, 1.0]),          # day
        np.array([-0.1, -0.2, -0.3, -0.4, -0.5, -0.6]),    # night
    ]), n // 24)
    df = make_hourly_df({
        'T_mean': np.full(n, 20.0),
        'RH_mean': np.full(n, 60.0),
        'R_n': R_n_vals,
    }, n_hours=n, start='2020-01-15')
    et = ETo(df, 'h', z_msl=100, lat=-43.6, lon=172, TZ_lon=173)

    R_n = et.ts_param['R_n']
    G = et.ts_param['G']

    day_mask = R_n > 0
    night_mask = R_n <= 0

    # Must have both day and night hours
    assert day_mask.any() and night_mask.any()

    np.testing.assert_allclose(G[day_mask].values, 0.1 * R_n[day_mask].values)
    np.testing.assert_allclose(G[night_mask].values, 0.5 * R_n[night_mask].values)


def test_ea_fallback_rh_max_only():
    """Verify e_a = e_min * RH_max / 100 when only RH_max available (FAO Eq 18)."""
    df = make_daily_df({
        'T_min': [10.0, 12.0, 8.0],
        'T_max': [25.0, 28.0, 22.0],
        'RH_max': [85.0, 90.0, 80.0],
    }, n_days=3)
    et = ETo(df, 'D', z_msl=100, lat=-43.6)

    e_min = 0.6108 * np.exp(17.27 * df['T_min'] / (df['T_min'] + 237.3))
    expected_ea = e_min * df['RH_max'] / 100

    np.testing.assert_allclose(et.ts_param['e_a'].values, expected_ea.values, rtol=1e-5)


###############################
### Group 2: e_a estimation fallback chain (daily)

def test_ea_from_tdew():
    """e_a from dewpoint temperature (FAO Eq 14)."""
    df = make_daily_df({
        'T_min': [10.0, 12.0],
        'T_max': [25.0, 28.0],
        'T_dew': [8.0, 10.0],
    }, n_days=2)
    et = ETo(df, 'D', z_msl=100, lat=-43.6)

    expected = 0.6108 * np.exp(17.27 * df['T_dew'] / (df['T_dew'] + 237.3))
    np.testing.assert_allclose(et.ts_param['e_a'].values, expected.values, rtol=1e-5)
    # est_val should NOT include the T_dew-missing penalty
    assert (et.est_val % 100000 // 10000 == 0).all()


def test_ea_from_rh_min_rh_max():
    """e_a from RH_min + RH_max (FAO Eq 17)."""
    df = make_daily_df({
        'T_min': [10.0, 12.0],
        'T_max': [25.0, 28.0],
        'RH_min': [40.0, 45.0],
        'RH_max': [85.0, 90.0],
    }, n_days=2)
    et = ETo(df, 'D', z_msl=100, lat=-43.6)

    e_min = 0.6108 * np.exp(17.27 * df['T_min'] / (df['T_min'] + 237.3))
    e_max = 0.6108 * np.exp(17.27 * df['T_max'] / (df['T_max'] + 237.3))
    expected = (e_min * df['RH_max'] / 100 + e_max * df['RH_min'] / 100) / 2

    np.testing.assert_allclose(et.ts_param['e_a'].values, expected.values, rtol=1e-5)


def test_ea_from_rh_mean():
    """e_a from RH_mean only (FAO Eq 19)."""
    df = make_daily_df({
        'T_min': [10.0, 12.0],
        'T_max': [25.0, 28.0],
        'RH_mean': [60.0, 65.0],
    }, n_days=2)
    et = ETo(df, 'D', z_msl=100, lat=-43.6)

    e_min = 0.6108 * np.exp(17.27 * df['T_min'] / (df['T_min'] + 237.3))
    e_max = 0.6108 * np.exp(17.27 * df['T_max'] / (df['T_max'] + 237.3))
    expected = df['RH_mean'] / 100 * (e_max + e_min) / 2

    np.testing.assert_allclose(et.ts_param['e_a'].values, expected.values, rtol=1e-5)


def test_ea_from_tmin_last_resort():
    """e_a from T_min when no humidity data (FAO Eq 48)."""
    df = make_daily_df({
        'T_min': [10.0, 12.0],
        'T_max': [25.0, 28.0],
    }, n_days=2)
    et = ETo(df, 'D', z_msl=100, lat=-43.6)

    expected = 0.6108 * np.exp(17.27 * df['T_min'] / (df['T_min'] + 237.3))
    np.testing.assert_allclose(et.ts_param['e_a'].values, expected.values, rtol=1e-5)


###############################
### Group 3: R_s estimation fallback chain

def test_rs_from_n_sun():
    """R_s estimated from sunshine hours (Angstrom, FAO Eq 35)."""
    df = make_daily_df({
        'T_min': [10.0, 12.0, 8.0, 11.0, 9.0],
        'T_max': [25.0, 28.0, 22.0, 26.0, 23.0],
        'n_sun': [8.0, 10.0, 6.0, 9.0, 7.0],
    }, n_days=5)
    et = ETo(df, 'D', z_msl=100, lat=-43.6)

    # R_s should have been estimated (not NaN)
    assert et.ts_param['R_s'].notna().all()
    # est_val should show 1 level of R_s estimation (1000)
    assert ((et.est_val % 10000 // 1000) >= 1).all()


def test_rs_from_temperature_range():
    """R_s from Hargreaves radiation formula when n_sun unavailable (FAO Eq 50)."""
    df = make_daily_df({
        'T_min': [10.0, 12.0, 8.0, 11.0, 9.0],
        'T_max': [25.0, 28.0, 22.0, 26.0, 23.0],
    }, n_days=5)
    et = ETo(df, 'D', z_msl=100, lat=-43.6)

    # R_s should have been estimated
    assert et.ts_param['R_s'].notna().all()
    # est_val should show 2 levels of R_s estimation (2000)
    assert ((et.est_val % 10000 // 1000) >= 2).all()


###############################
### Group 4: Input validation

def test_daily_missing_tmin_raises():
    df = make_daily_df({'T_max': [25.0, 28.0]}, n_days=2)
    with pytest.raises(ValueError, match='Minimum data input'):
        ETo(df, 'D', z_msl=100, lat=-43.6)


def test_daily_missing_tmax_raises():
    df = make_daily_df({'T_min': [10.0, 12.0]}, n_days=2)
    with pytest.raises(ValueError, match='Minimum data input'):
        ETo(df, 'D', z_msl=100, lat=-43.6)


def test_hourly_missing_tmean_raises():
    df = make_hourly_df({'RH_mean': [60.0] * 48})
    with pytest.raises(ValueError, match='Minimum data input'):
        ETo(df, 'h', z_msl=100, lat=-43.6, lon=172, TZ_lon=173)


def test_hourly_missing_rhmean_and_ea_raises():
    df = make_hourly_df({'T_mean': [20.0] * 48})
    with pytest.raises(ValueError, match='Minimum data input'):
        ETo(df, 'h', z_msl=100, lat=-43.6, lon=172, TZ_lon=173)


def test_non_datetime_index_raises():
    df = pd.DataFrame({'T_min': [10.0], 'T_max': [25.0]}, index=[0])
    with pytest.raises(ValueError, match='datetime'):
        ETo(df, 'D', z_msl=100, lat=-43.6)


###############################
### Group 5: Hourly path coverage

def test_hourly_ea_from_rhmean():
    """Hourly e_a = e_mean * RH_mean / 100."""
    n = 48
    T_mean_vals = np.full(n, 20.0)
    RH_mean_vals = np.full(n, 65.0)
    df = make_hourly_df({'T_mean': T_mean_vals, 'RH_mean': RH_mean_vals})
    et = ETo(df, 'h', z_msl=100, lat=-43.6, lon=172, TZ_lon=173)

    e_mean = 0.6108 * np.exp(17.27 * 20.0 / (20.0 + 237.3))
    expected = e_mean * 65.0 / 100

    np.testing.assert_allclose(et.ts_param['e_a'].values, expected, rtol=1e-5)


def test_hourly_ea_provided_directly():
    """Hourly e_a used as-is when provided."""
    n = 48
    ea_vals = np.full(n, 1.5)
    df = make_hourly_df({'T_mean': np.full(n, 20.0), 'e_a': ea_vals})
    et = ETo(df, 'h', z_msl=100, lat=-43.6, lon=172, TZ_lon=173)

    np.testing.assert_allclose(et.ts_param['e_a'].values, 1.5, rtol=1e-10)


def test_hourly_eto_fao_precision(hourly_et):
    """Hourly ETo should be positive in aggregate and within a reasonable range."""
    eto_vals = hourly_et.eto_fao()
    total = eto_vals.sum()
    # Should be positive
    assert total > 0
    # Individual hourly values should be bounded
    valid = eto_vals.dropna()
    assert (valid <= 15).all()
    assert (valid >= 0).all()


###############################
### Group 6: Method-level paths

def test_hargreaves_hourly_raises():
    n = 48
    df = make_hourly_df({'T_mean': np.full(n, 20.0), 'RH_mean': np.full(n, 60.0)})
    et = ETo(df, 'h', z_msl=100, lat=-43.6, lon=172, TZ_lon=173)
    with pytest.raises(ValueError, match='less than a day'):
        et.eto_hargreaves()


def test_eto_fao_max_min_clipping():
    """Values outside [min_ETo, max_ETo] should be clipped to NaN."""
    df = make_daily_df({
        'T_min': [10.0, 12.0, 8.0, 11.0, 9.0],
        'T_max': [25.0, 28.0, 22.0, 26.0, 23.0],
    }, n_days=5)
    et = ETo(df, 'D', z_msl=100, lat=-43.6)
    # Use a tight max to force clipping
    eto_vals = et.eto_fao(max_ETo=0.5)
    # Any value above 0.5 should now be NaN
    valid = eto_vals.dropna()
    if len(valid) > 0:
        assert (valid <= 0.5).all()


def test_eto_fao_interpolation(daily_et):
    """interp='linear' should return a DataFrame with two columns."""
    result = daily_et.eto_fao(interp='linear')
    assert isinstance(result, pd.DataFrame)
    assert 'ETo_FAO_mm' in result.columns
    assert 'ETo_FAO_interp_mm' in result.columns


def test_hargreaves_interpolation(daily_et):
    """interp='linear' should return a DataFrame with two columns."""
    result = daily_et.eto_hargreaves(interp='linear')
    assert isinstance(result, pd.DataFrame)
    assert 'ETo_Har_mm' in result.columns
    assert 'ETo_Har_interp_mm' in result.columns


###############################
### Group 7: ETo class and miscellaneous

def test_eto_init_empty():
    et = ETo()
    assert not hasattr(et, 'ts_param')


def test_wind_speed_from_uz():
    """U_2 calculated from U_z at height z_u."""
    z_u = 10
    U_z_val = 3.5
    df = make_daily_df({
        'T_min': [10.0, 12.0],
        'T_max': [25.0, 28.0],
        'U_z': [U_z_val, U_z_val],
    }, n_days=2)
    et = ETo(df, 'D', z_msl=100, lat=-43.6, z_u=z_u)

    expected_U2 = U_z_val * 4.87 / np.log(67.8 * z_u - 5.42)
    np.testing.assert_allclose(et.ts_param['U_2'].values, expected_U2, rtol=1e-5)
    # est_val should not include the U_z-missing penalty (1)
    assert ((et.est_val % 10) == 0).all()


def test_custom_krs_changes_rs():
    """Coastal K_rs=0.19 should produce different R_s than inland K_rs=0.16."""
    df = make_daily_df({
        'T_min': [10.0, 12.0, 8.0],
        'T_max': [25.0, 28.0, 22.0],
    }, n_days=3)
    et_inland = ETo(df, 'D', z_msl=100, lat=-43.6, K_rs=0.16)
    et_coastal = ETo(df, 'D', z_msl=100, lat=-43.6, K_rs=0.19)

    assert not np.allclose(
        et_inland.ts_param['R_s'].values,
        et_coastal.ts_param['R_s'].values,
    )


def test_pressure_provided():
    """When P column is provided, it should be used as-is."""
    df = make_daily_df({
        'T_min': [10.0, 12.0],
        'T_max': [25.0, 28.0],
        'P': [95.0, 95.0],
    }, n_days=2)
    et = ETo(df, 'D', z_msl=100, lat=-43.6)

    np.testing.assert_allclose(et.ts_param['P'].values, 95.0)
    # est_val should not include P-missing penalty (1000000)
    assert (et.est_val < 1000000).all()


def test_est_val_tracking():
    """Minimal inputs should produce expected quality value."""
    df = make_daily_df({
        'T_min': [10.0],
        'T_max': [25.0],
    }, n_days=1)
    et = ETo(df, 'D', z_msl=100, lat=-43.6)

    # P(1000000) + T_mean(100000) + e_a(40000) + R_s(2000) + R_n(100) + G(10) + U_z(1)
    expected = 1000000 + 100000 + 40000 + 2000 + 100 + 10 + 1
    assert et.est_val.iloc[0] == expected


def test_tsreg_infer_freq():
    """tsreg with freq=None should infer frequency."""
    index = pd.date_range('2020-01-01', periods=10, freq='D')
    ts = pd.Series(range(10), index=index)
    result = ETo.tsreg(ts, freq=None)
    assert len(result) == 10


def test_daily_g_is_zero():
    """Daily G estimation should always be zero (FAO Eq 42)."""
    df = make_daily_df({
        'T_min': [10.0, 12.0, 8.0],
        'T_max': [25.0, 28.0, 22.0],
    }, n_days=3)
    et = ETo(df, 'D', z_msl=100, lat=-43.6)
    np.testing.assert_allclose(et.ts_param['G'].values, 0.0)
