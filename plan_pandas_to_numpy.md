# Implementation Plan: Convert ETo Package from Pandas to NumPy

## Overview

Convert every file in the ETo package so that pandas is no longer imported anywhere. The input API changes from a `pd.DataFrame` with `DatetimeIndex` to a `dict[str, np.ndarray]` plus either `day_of_year`/`hour` integer arrays or a `dates` datetime64 array. All internal state uses `dict[str, np.ndarray]` instead of `pd.DataFrame`, and all outputs are plain `np.ndarray`.

Key decisions:
- **Input**: `dict[str, np.ndarray]` + temporal arrays (no DataFrame)
- **Internal state**: `self.ts_param` → `dict[str, np.ndarray]`, `self.est_val` → `np.ndarray`
- **Output**: `eto_fao()` and `eto_hargreaves()` return `np.ndarray` (same length as input)
- **Removed**: interpolation params, `tsreg`, pandas dependency
- **Only dependency**: `numpy`

---

## File 1: `eto/core.py`

### Current state
- Imports `pandas as pd` and `copy`
- `__init__` accepts `df` (DataFrame) or `None`
- Has a `tsreg` static method (pandas resampling/interpolation utility)
- Dynamically attaches `param_est`, `eto_fao`, `eto_hargreaves`, and `copy` to the class

### Changes

**Remove**: `import pandas as pd`, the `tsreg` static method, `ETo.copy = copy`, and `from copy import copy`.

**Add**: `import numpy as np`

**New constructor signature**:
```python
def __init__(self, data=None, freq='D', z_msl=None, lat=None, lon=None, TZ_lon=None,
             z_u=2, K_rs=0.16, a_s=0.25, b_s=0.5, alb=0.23,
             day_of_year=None, hour=None, dates=None):
```

**`data` parameter**: `dict[str, np.ndarray]` where keys are met parameter names (`R_n`, `R_s`, `G`, `T_min`, `T_max`, `T_mean`, `T_dew`, `RH_min`, `RH_max`, `RH_mean`, `n_sun`, `U_z`, `P`, `e_a`). All arrays must have the same length.

**Temporal parameters** — exactly one of two paths:
- **Path A** (direct): `day_of_year` (int array, 1–366). For hourly: `hour` (int array, 0–23) also required.
- **Path B** (from dates): `dates` (`np.ndarray` of `datetime64`). Constructor derives `day_of_year` and (if hourly) `hour`:
  ```
  day_of_year = (dates.astype('datetime64[D]') - dates.astype('datetime64[Y]')).astype(int) + 1
  hour = (dates - dates.astype('datetime64[D]')).astype('timedelta64[h]').astype(int)
  ```

**Constructor behavior**:
- `data is None` → do nothing (empty init, same as today)
- Otherwise → validate temporal args, validate all arrays in `data` have the same length, derive `day_of_year`/`hour` if `dates` provided, then call `self.param_est(...)`

**Dynamic method attachment** (bottom of file): Keep `ETo.param_est`, `ETo.eto_fao`, `ETo.eto_hargreaves`. Remove `ETo.copy`.

---

## File 2: `eto/param_est.py`

This is the largest change. Every pandas pattern is replaced with a numpy equivalent.

### Remove
- `import pandas as pd`

### New signature
```python
def param_est(self, data, freq='D', z_msl=None, lat=None, lon=None, TZ_lon=None,
              z_u=2, K_rs=0.16, a_s=0.25, b_s=0.5, alb=0.23,
              day_of_year=None, hour=None):
```

`data` is `dict[str, np.ndarray]`. `day_of_year` and `hour` are `np.ndarray` (already derived by the constructor).

### Pattern replacements

| Current pandas pattern | NumPy replacement |
|---|---|
| `pd.DataFrame(np.nan, ...)` + `pd.concat` to build `ts_param` | Loop `met_names`; copy existing keys, add missing as `np.full(n, np.nan)` |
| `pd.Series(0, ...)` for `est_val` | `np.zeros(n, dtype=np.int64)` |
| `self.ts_param['col'].isnull()` | `np.isnan(self.ts_param['col'])` |
| `self.est_val.loc[mask] = self.est_val.loc[mask] + N` | `self.est_val[mask] += N` |
| `self.ts_param.loc[mask, 'col'] = value` | `self.ts_param['col'][mask] = value` |
| `self.ts_param['gamma'] = expr` | Same (dict key assignment) |
| `Day = df.index.dayofyear` | `Day = day_of_year` |
| `hour_vec = df.index.hour` | `hour_vec = hour` |
| `type(df.index) is not pd.DatetimeIndex` check | Remove (constructor already validated temporal args) |
| `N[self.ts_param['R_s'].isnull().values]` | `N[mask]` (no `.values` needed — both already ndarrays) |

### Specific sections

**Setup (lines 84–93)**: Build `self.ts_param` as dict. For each name in `met_names`: if present in `data`, copy with `np.array(v, dtype=np.float64)`; if missing, create `np.full(n, np.nan)`. Create `self.est_val = np.zeros(n, dtype=np.int64)`.

**Validation (lines 97–107)**: Replace `.isnull().any()` with `np.isnan(...).any()`.

**Temporal (lines 114–118, 177)**: Use `day_of_year` and `hour` args directly.

**All conditional estimation blocks (lines 124–234)**: Each follows the same mechanical translation — compute `mask = np.isnan(self.ts_param['col'])`, then `self.est_val[mask] += N` and `self.ts_param['col'][mask] = formula[mask]`.

**Arithmetic expressions**: All the FAO equations already use numpy operations (np.exp, np.sin, etc.) on arrays. No changes needed to the math itself.

---

## File 3: `eto/methods/ETo.py`

### Remove
- `import pandas as pd`
- `interp` and `maxgap` parameters
- Entire interpolation block (lines 49–53)
- `ETo_FAO.name = 'ETo_FAO_mm'`

### New signature
```python
def eto_fao(self, max_ETo=15, min_ETo=0):
```

### Changes
- Column access (`self.ts_param['col']`) stays identical (dict uses same bracket syntax)
- Extreme-value clamping (`ETo_FAO[ETo_FAO > max_ETo] = np.nan`) works on ndarrays — no change
- Return `np.round(ETo_FAO, 2)`
- Update docstring: return type is `np.ndarray`

---

## File 4: `eto/methods/hargreaves.py`

Same changes as `ETo.py`:

### Remove
- `import pandas as pd`
- `interp` and `maxgap` parameters
- Interpolation block (lines 47–51)
- `ETo_Har.name = 'ETo_Har_mm'`

### New signature
```python
def hargreaves(self, max_ETo=15, min_ETo=0):
```

### Return
`np.round(ETo_Har, 2)`

---

## File 5: `eto/util.py`

### Current state
Contains only `tsreg()` — a pandas resampling/interpolation utility.

### Changes
**Delete the file** (or empty it). `tsreg` is removed from the class and not used anywhere else.

---

## File 6: `eto/__init__.py`

Bump version to `2.0.0` to signal the breaking API change. No other changes needed.

---

## File 7: `eto/datasets/__init__.py`

No changes. This module only returns file paths via `os.path`.

---

## File 8: `pyproject.toml`

- Change `dependencies` from `["pandas"]` to `["numpy"]`
- Clean up stale Python 2.7/3.4/3.5/3.6 classifiers

---

## File 9: `eto/tests/test_eto.py`

### Helper functions

Replace `make_daily_df` / `make_hourly_df` with:

- **`make_daily_data(columns_dict, n_days=10, start='2020-01-01')`**: Returns `(data_dict, dates)` where `dates` is `np.arange(start, ..., dtype='datetime64[D]')`.

- **`make_hourly_data(columns_dict, n_hours=48, start='2020-06-15')`**: Returns `(data_dict, dates)` where `dates` is `np.arange(start, ..., dtype='datetime64[h]')`.

### Fixture changes

- **`daily_data`**: Replace `pd.read_csv(...)` with stdlib `zipfile` + `csv` or `io` + `np.genfromtxt`. Return `(data_dict, dates)`.
- **`daily_results`**: Same — return `dict[str, np.ndarray]`.
- **`daily_et`**: `ETo(data, 'D', dates=dates, **params)`.
- **`hourly_et`**: Construct synthetic hourly data directly (no more `tsreg` resampling). Build a 48-hour dataset with known `T_mean`, `RH_mean`, `R_s` values.

### Assertion changes

| Current pandas pattern | NumPy replacement |
|---|---|
| `et.eto_fao().sum()` | `np.nansum(et.eto_fao())` |
| `et.est_val.iloc[0]` | `et.est_val[0]` |
| `result.dropna()` | `result[~np.isnan(result)]` |
| `result.notna().any()` | `np.any(~np.isnan(result))` |
| `isinstance(result, pd.DataFrame)` | `isinstance(result, np.ndarray)` |
| `.values` in `assert_allclose` | Drop (already ndarray) |

### Tests to delete
- `test_eto_fao_interpolation` — interp parameter removed
- `test_hargreaves_interpolation` — interp parameter removed
- `test_tsreg_infer_freq` — `tsreg` removed

### Tests to modify
- `test_non_datetime_index_raises` → rename to `test_missing_temporal_args_raises`: verify that omitting both `day_of_year` and `dates` raises an error

### New tests to add
1. **`test_dates_path`** — passing `dates` as datetime64 array produces same result as explicit `day_of_year`
2. **`test_hour_derivation_from_dates`** — hourly dates correctly derive both `day_of_year` and `hour`
3. **`test_input_length_mismatch_raises`** — arrays of different lengths in `data` raise ValueError
4. **`test_day_of_year_length_mismatch_raises`** — `day_of_year` length not matching data raises ValueError
5. **`test_output_is_ndarray`** — `eto_fao()` and `eto_hargreaves()` return `np.ndarray`
6. **`test_output_length_matches_input`** — output array length equals input array length

---

## File 10: `CLAUDE.md`

- Change "Only production dependency: `pandas`" → "Only production dependency: `numpy`"
- Update typical flow: `ETo(data_dict, freq, lat=..., z_msl=..., dates=...)` or `ETo(data_dict, freq, lat=..., z_msl=..., day_of_year=..., hour=...)`
- Note `self.ts_param` is `dict[str, np.ndarray]`, `self.est_val` is `np.ndarray`
- Note `eto_fao()` / `eto_hargreaves()` return `np.ndarray`
- Remove mention of `tsreg`
- Key input columns are now dict keys, not DataFrame columns

---

## Implementation Sequence

1. `pyproject.toml` — change dependency, bump version in `eto/__init__.py`
2. `eto/util.py` — delete or empty
3. `eto/param_est.py` — full rewrite (largest change)
4. `eto/core.py` — new constructor, remove `tsreg`/`copy`
5. `eto/methods/ETo.py` — remove pandas/interp, return ndarray
6. `eto/methods/hargreaves.py` — same as ETo.py
7. `eto/tests/test_eto.py` — rewrite all helpers/fixtures/tests
8. `CLAUDE.md` — update docs

Steps 2–6 form a single coherent change and should be done together, then tests (step 7), then validate with `uv run pytest`.

---

## Potential Challenges

1. **CSV fixture loading without pandas**: The test fixtures currently use `pd.read_csv` to load zipped CSVs. Replace with stdlib `zipfile` + `csv` modules, parsing dates into `np.datetime64` and numeric columns into `np.float64` arrays.

2. **Numerical precision of golden tests**: The current tests (`test_eto_fao_daily`, `test_eto_har_daily`) compare exact sums. The math is identical (numpy was doing the computation even under pandas), but `pd.Series.sum()` vs `np.nansum()` may handle NaN slightly differently. Verify after implementation.

3. **Day-of-year leap year edge case**: The derivation `(date - year_start).astype(int) + 1` must correctly yield DOY 366 for Dec 31 of leap years. `np.datetime64` handles this natively.

4. **In-place mutation**: All input arrays must be `.copy()`'d during setup to avoid mutating user data.
