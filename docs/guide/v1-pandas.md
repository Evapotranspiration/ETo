# Legacy v1.x API (Pandas)

!!! warning
    This page documents the **v1.x API** which used pandas DataFrames. If you are using ETo v2.0+, see the [Usage guide](usage.md) instead.

## Installation (v1.x)

```bash
pip install eto==1.1.2
```

The v1.x series requires pandas as its core dependency.

## Initialising

The package is used via the main `ETo` class. It can be initialised without any parameters:

```python
from eto import ETo, datasets
import pandas as pd

et1 = ETo()
```

## Parameter estimation

Input data must be a `pd.DataFrame` with a `DatetimeIndex`. Column names correspond to meteorological parameters.

```python
ex1_path = datasets.get_path('example_daily')
tsdata = pd.read_csv(
    ex1_path, parse_dates=True,
    infer_datetime_format=True,
    index_col='date',
    compression='zip'
)
```

Run parameter estimation:

```python
z_msl = 500
lat = -43.6
lon = 172
TZ_lon = 173
freq = 'D'

et1.param_est(tsdata, freq, z_msl, lat, lon, TZ_lon)
et1.ts_param.head()  # pd.DataFrame of all estimated parameters
```

## Calculate ETo

```python
# FAO 56 Penman-Monteith
eto1 = et1.eto_fao()       # pd.Series
eto1.head()

# Hargreaves
eto2 = et1.eto_hargreaves() # pd.Series
```

## Interpolation (v1.x only)

v1.x supported built-in interpolation of the output:

```python
# Returns a DataFrame with original and interpolated columns
eto_filled = et1.eto_fao(interp='linear', maxgap=15)
```

This feature was removed in v2.0.

## Time series regularisation (v1.x only)

The `tsreg` static method could resample and interpolate time series:

```python
ts_regular = ETo.tsreg(ts, freq='D', interp='linear', maxgap=15)
```

This feature was removed in v2.0.

## Hourly estimation (v1.x)

For hourly data, the DataFrame needed an hourly `DatetimeIndex`:

```python
# Resample daily to hourly using tsreg
tsdata_hourly = et1.tsreg(
    et1.ts_param[['R_s', 'T_mean', 'e_a']],
    'h', 'time'
)

et_hourly = ETo(tsdata_hourly, 'h', z_msl=500, lat=-43.6, lon=172, TZ_lon=173)
eto_hourly = et_hourly.eto_fao()
```

## Input parameters

The v1.x `param_est` function accepted a `pd.DataFrame` with these column names:

| Column | Description |
|--------|-------------|
| `R_n` | Net radiation (MJ/m²) |
| `R_s` | Incoming shortwave radiation (MJ/m²) |
| `G` | Net soil heat flux (MJ/m²) |
| `T_min` | Minimum temperature (°C) |
| `T_max` | Maximum temperature (°C) |
| `T_mean` | Mean temperature (°C) |
| `T_dew` | Dew point temperature (°C) |
| `RH_min` | Minimum relative humidity (%) |
| `RH_max` | Maximum relative humidity (%) |
| `RH_mean` | Mean relative humidity (%) |
| `n_sun` | Sunshine hours per day |
| `U_z` | Wind speed at height z (m/s) |
| `P` | Atmospheric pressure (kPa) |
| `e_a` | Actual vapour pressure (kPa) |

## Migrating to v2.0

See the [Migration guide](migration.md) for a detailed comparison and code examples.
