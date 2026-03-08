# Migration from v1.x to v2.0

ETo v2.0 replaces the pandas dependency with pure NumPy. This is a breaking API change.

## Summary of changes

- **Input**: `pd.DataFrame` with `DatetimeIndex` → `dict[str, np.ndarray]` + `dates` or `day_of_year`/`hour`
- **Internal state**: `self.ts_param` is now `dict[str, np.ndarray]` (was `pd.DataFrame`); `self.est_val` is now `np.ndarray` (was `pd.Series`)
- **Output**: `eto_fao()` and `eto_hargreaves()` return `np.ndarray` (was `pd.Series` or `pd.DataFrame`)
- **Removed**: `interp`/`maxgap` parameters, `tsreg()` method, `copy` method
- **Dependency**: `numpy` only (no pandas)

## Code migration

### Constructing the ETo object

=== "v1.x (pandas)"

    ```python
    import pandas as pd
    from eto import ETo

    df = pd.read_csv('met_data.csv', parse_dates=True, index_col='date')
    et = ETo(df, freq='D', z_msl=500, lat=-43.6)
    ```

=== "v2.0 (numpy)"

    ```python
    import numpy as np
    from eto import ETo

    # Load your data into a dict of arrays
    data = {
        'T_min': np.array([...]),
        'T_max': np.array([...]),
        'R_s': np.array([...]),
    }
    dates = np.array([...], dtype='datetime64[D]')

    et = ETo(data, freq='D', z_msl=500, lat=-43.6, dates=dates)
    ```

### Getting results

=== "v1.x (pandas)"

    ```python
    eto_series = et.eto_fao()           # pd.Series
    total = eto_series.sum()             # NaN-unaware
    total = eto_series.dropna().sum()    # NaN-safe
    ```

=== "v2.0 (numpy)"

    ```python
    eto_array = et.eto_fao()             # np.ndarray
    total = np.nansum(eto_array)         # NaN-safe
    ```

### Accessing estimated parameters

=== "v1.x (pandas)"

    ```python
    et.ts_param['R_n']          # pd.Series
    et.ts_param.loc[0, 'R_n']   # scalar
    et.est_val.iloc[0]           # scalar
    ```

=== "v2.0 (numpy)"

    ```python
    et.ts_param['R_n']          # np.ndarray
    et.ts_param['R_n'][0]       # scalar
    et.est_val[0]                # scalar
    ```

### Interpolation (removed)

The `interp` and `maxgap` parameters have been removed from `eto_fao()` and `eto_hargreaves()`. If you need interpolation, apply it to the output array directly:

```python
# v2.0: post-process with scipy or your own logic
from scipy.interpolate import interp1d

eto = et.eto_fao()
valid = ~np.isnan(eto)
if valid.any():
    f = interp1d(np.where(valid)[0], eto[valid], bounds_error=False, fill_value=np.nan)
    eto_filled = f(np.arange(len(eto)))
```

### tsreg (removed)

The `tsreg()` static method for time series regularisation has been removed. Use pandas or scipy directly if you need resampling.

## Pattern reference

| v1.x pandas pattern | v2.0 numpy equivalent |
|---|---|
| `pd.DataFrame({'T_min': [...], ...}, index=dates)` | `{'T_min': np.array([...]), ...}` + `dates=dates` |
| `et.eto_fao().sum()` | `np.nansum(et.eto_fao())` |
| `et.est_val.iloc[0]` | `et.est_val[0]` |
| `result.dropna()` | `result[~np.isnan(result)]` |
| `isinstance(result, pd.Series)` | `isinstance(result, np.ndarray)` |
| `et.ts_param['R_n'].values` | `et.ts_param['R_n']` |
| `et.eto_fao(interp='linear')` | Removed — interpolate output yourself |
| `et.tsreg(ts, freq)` | Removed — use pandas/scipy directly |
