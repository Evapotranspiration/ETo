# Quick Start

This guide walks through a complete ETo calculation using the included example dataset.

## Load the example data

ETo ships with a zipped CSV of daily meteorological data. We load it using the standard library:

```python
import zipfile
import csv
import io
import numpy as np
from eto import ETo, datasets

# Get the path to the example dataset
path = datasets.get_path('example_daily')

# Load the CSV without pandas
with zipfile.ZipFile(path) as z:
    name = z.namelist()[0]
    with z.open(name) as f:
        reader = csv.reader(io.TextIOWrapper(f))
        header = next(reader)
        rows = list(reader)

# Parse into numpy arrays
dates = np.array([row[0] for row in rows], dtype='datetime64[D]')
data = {}
for i, col in enumerate(header):
    if col == 'date':
        continue
    data[col] = np.array([float(row[i]) for row in rows], dtype=np.float64)
```

The example data contains columns: `R_s`, `T_max`, `T_min`, `e_a`.

## Run parameter estimation and calculate ETo

```python
et = ETo(data, freq='D', z_msl=500, lat=-43.6, lon=172, TZ_lon=173, dates=dates)
```

This estimates all missing meteorological parameters (pressure, radiation, wind speed, etc.) from the available data.

## Get results

```python
# FAO 56 Penman-Monteith ETo
eto_fao = et.eto_fao()
print(f"Mean daily ETo: {np.nanmean(eto_fao):.2f} mm")
print(f"Total ETo: {np.nansum(eto_fao):.2f} mm")

# Hargreaves ETo (simplified method)
eto_har = et.eto_hargreaves()
print(f"Mean daily Hargreaves ETo: {np.nanmean(eto_har):.2f} mm")
```

Both methods return a `np.ndarray` with the same length as the input data.

## Inspect estimated parameters

The full set of estimated parameters is available as a dictionary of arrays:

```python
# All estimated parameter names
print(list(et.ts_param.keys()))

# Check a specific parameter
print(et.ts_param['R_n'][:5])  # Net radiation (first 5 values)
```

## Check estimation quality

The `est_val` array tracks which parameters were estimated:

```python
print(et.est_val[:5])
```

A value of `0` means all parameters were measured directly. Higher values indicate more estimation was needed. See the [Usage guide](../guide/usage.md#estimation-quality-tracking) for details on interpreting these values.
