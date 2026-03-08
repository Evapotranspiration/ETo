# ETo

**Python package for calculating reference evapotranspiration (FAO 56)**

---

ETo estimates reference evapotranspiration using the [UN-FAO 56 paper](http://www.fao.org/docrep/X0490E/X0490E00.htm) methodology. It requires a minimum of T_min and T_max for daily estimates or T_mean and RH_mean for hourly estimates, and uses all available meteorological parameters to improve accuracy.

## Key Features

- **FAO 56 Penman-Monteith** — the international standard for reference ET estimation
- **Hargreaves method** — simplified daily ET when limited data is available
- **Automatic parameter estimation** — missing met parameters are estimated from available data using FAO 56 fallback chains
- **Quality tracking** — `est_val` array records which parameters were estimated and at what quality level
- **Minimal dependencies** — only requires NumPy

## Quick Example

```python
import numpy as np
from eto import ETo

# Prepare daily meteorological data
data = {
    'T_min': np.array([10.0, 12.0, 8.0, 11.0, 9.0]),
    'T_max': np.array([25.0, 28.0, 22.0, 26.0, 23.0]),
    'RH_min': np.array([40.0, 45.0, 35.0, 42.0, 38.0]),
    'RH_max': np.array([85.0, 90.0, 80.0, 88.0, 82.0]),
}

dates = np.arange('2020-01-01', '2020-01-06', dtype='datetime64[D]')

et = ETo(data, freq='D', z_msl=500, lat=-43.6, dates=dates)

eto_fao = et.eto_fao()       # np.ndarray of daily ETo (mm)
eto_har = et.eto_hargreaves() # np.ndarray of daily Hargreaves ETo (mm)
```

## Next Steps

- [Installation](getting-started/installation.md) — install ETo
- [Quick Start](getting-started/quickstart.md) — complete walkthrough of a typical workflow
- [User Guide](guide/usage.md) — detailed usage for daily and hourly estimation
- [API Reference](reference/index.md) — full class and method reference
