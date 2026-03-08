# Usage

## Input data format

ETo accepts meteorological data as a `dict[str, np.ndarray]` where each key is a parameter name and each value is a 1-D array. All arrays must have the same length.

### Supported parameters

| Key | Description | Unit |
|-----|-------------|------|
| `R_n` | Net radiation | MJ/m² |
| `R_s` | Incoming shortwave radiation | MJ/m² |
| `G` | Net soil heat flux | MJ/m² |
| `T_min` | Minimum temperature | °C |
| `T_max` | Maximum temperature | °C |
| `T_mean` | Mean temperature | °C |
| `T_dew` | Dew point temperature | °C |
| `RH_min` | Minimum relative humidity | % |
| `RH_max` | Maximum relative humidity | % |
| `RH_mean` | Mean relative humidity | % |
| `n_sun` | Sunshine hours per day | hours |
| `U_z` | Wind speed at height z | m/s |
| `P` | Atmospheric pressure | kPa |
| `e_a` | Actual vapour pressure | kPa |

### Minimum requirements

- **Daily**: `T_min` and `T_max`
- **Hourly**: `T_mean` and either `RH_mean` or `e_a`

All other parameters are estimated from the available data using FAO 56 fallback chains.

## Temporal arguments

ETo needs to know the day of year (and hour, for hourly data) for solar radiation calculations. There are two ways to provide this:

### Option 1: Pass `dates`

Pass a `np.ndarray` of `datetime64` values. Day of year and hour are derived automatically:

```python
dates = np.arange('2020-01-01', '2020-04-01', dtype='datetime64[D]')
et = ETo(data, freq='D', z_msl=500, lat=-43.6, dates=dates)
```

### Option 2: Pass `day_of_year` and `hour`

Pass integer arrays directly:

```python
day_of_year = np.arange(1, 92)  # Jan 1 to Mar 31
et = ETo(data, freq='D', z_msl=500, lat=-43.6, day_of_year=day_of_year)
```

For hourly data, `hour` (0-23) is also required:

```python
et = ETo(data, freq='h', z_msl=500, lat=-43.6, lon=172, TZ_lon=173,
         day_of_year=day_of_year, hour=hour)
```

## Daily estimation

Daily estimation requires only `T_min` and `T_max`:

```python
import numpy as np
from eto import ETo

data = {
    'T_min': np.array([10.0, 12.0, 8.0]),
    'T_max': np.array([25.0, 28.0, 22.0]),
}
dates = np.arange('2020-01-01', '2020-01-04', dtype='datetime64[D]')

et = ETo(data, freq='D', z_msl=500, lat=-43.6, dates=dates)
eto = et.eto_fao()  # np.ndarray
```

Providing more parameters (e.g. `R_s`, `RH_min`, `RH_max`, `U_z`) reduces the amount of estimation and improves accuracy.

## Hourly estimation

Hourly estimation requires `T_mean` and either `RH_mean` or `e_a`. The `lon` and `TZ_lon` parameters are also needed for solar time calculations:

```python
data = {
    'T_mean': np.full(48, 20.0),
    'RH_mean': np.full(48, 60.0),
    'R_s': r_s_array,  # hourly shortwave radiation
}
dates = np.arange('2020-06-15', '2020-06-17', dtype='datetime64[h]')

et = ETo(data, freq='h', z_msl=500, lat=-43.6, lon=172, TZ_lon=173, dates=dates)
eto = et.eto_fao()
```

!!! note
    Hargreaves should not be used at sub-daily frequencies. Calling `eto_hargreaves()` on hourly data will raise a `ValueError`.

## Soil heat flux (G)

- **Daily**: G is set to 0 (FAO Eq 42)
- **Hourly**: G = 0.1 × R_n during daytime (R_n > 0) and G = 0.5 × R_n at night (R_n ≤ 0) per FAO Eq 45/46

You can override this by providing `G` in the input data.

## Constructor parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `data` | `dict[str, np.ndarray]` of met data | required |
| `freq` | `'D'` for daily, `'h'` for hourly | `'D'` |
| `z_msl` | Elevation above sea level (m) | `None` |
| `lat` | Latitude (decimal degrees) | `None` |
| `lon` | Longitude (decimal degrees) | `None` |
| `TZ_lon` | Time zone centre longitude (decimal degrees) | `None` |
| `z_u` | Wind measurement height (m) | `2` |
| `K_rs` | R_s coefficient (0.16 inland, 0.19 coastal) | `0.16` |
| `a_s` | R_s Angstrom coefficient | `0.25` |
| `b_s` | R_s Angstrom coefficient | `0.50` |
| `alb` | Albedo (0.23 for reference crop) | `0.23` |
| `dates` | `np.ndarray` of `datetime64` | `None` |
| `day_of_year` | `np.ndarray` of int (1-366) | `None` |
| `hour` | `np.ndarray` of int (0-23) | `None` |

## Estimation quality tracking

The `est_val` attribute is a `np.ndarray` of integers tracking which parameters were estimated. Each digit position represents a parameter:

| Position (from right) | Parameter | Per-level increment |
|------------------------|-----------|---------------------|
| 1 (ones) | U_z | 1 |
| 2 (tens) | G | 10 |
| 3 (hundreds) | R_n | 100 |
| 4 (thousands) | R_s | 1000 |
| 5 (ten-thousands) | e_a | 10000 |
| 6 (hundred-thousands) | T_mean | 100000 |
| 7 (millions) | P | 1000000 |

A value of `0` means all parameters were measured. Higher values indicate more estimation. For example, `1142111` means P was estimated (1), T_mean was estimated (1), e_a required 4 levels of fallback (4), R_s required 2 levels (2), R_n was estimated (1), G was estimated (1), and U_z was estimated (1).

## Output

Both `eto_fao()` and `eto_hargreaves()` return a `np.ndarray` of ETo values in mm, with the same length as the input data. Extreme values outside `[min_ETo, max_ETo]` are set to `NaN`:

```python
eto = et.eto_fao(max_ETo=15, min_ETo=0)  # defaults
```
