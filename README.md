# ETo

**A Python package for calculating reference evapotranspiration**

---

ETo calculates reference evapotranspiration (ETo) using the [UN-FAO 56 paper](http://www.fao.org/docrep/X0490E/X0490E00.htm) methodology. It estimates missing meteorological parameters from available data and supports both daily and hourly time steps.

## Documentation

Full documentation is available at [mullenkamp.github.io/ETo](https://mullenkamp.github.io/ETo/).

## Installation

```bash
pip install eto
```

or:

```bash
conda install -c mullenkamp eto
```

The only dependency is [NumPy](https://numpy.org/).

## Quick Example

```python
import numpy as np
from eto import ETo

data = {
    'T_min': np.array([10.0, 12.0, 8.0]),
    'T_max': np.array([25.0, 28.0, 22.0]),
}
dates = np.arange('2020-01-01', '2020-01-04', dtype='datetime64[D]')

et = ETo(data, freq='D', z_msl=500, lat=-43.6, dates=dates)
eto = et.eto_fao()  # np.ndarray of ETo in mm
```
