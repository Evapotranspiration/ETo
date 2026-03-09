# API Reference

All public classes and methods are available from the top-level `eto` package.

```python
from eto import ETo
```

## ETo Class

| Name | Description |
|------|-------------|
| [`ETo`](eto.md#eto.core.ETo) | Main class for parameter estimation and ETo/ETc calculation |

## Reference ET Methods

| Method | Description |
|--------|-------------|
| [`param_est`](eto.md#eto.param_est.param_est) | Estimate missing meteorological parameters |
| [`eto_fao`](eto.md#eto.methods.ETo.eto_fao) | FAO 56 Penman-Monteith reference ET (short/tall crop) |
| [`eto_hargreaves`](eto.md#eto.methods.hargreaves.hargreaves) | Hargreaves reference ET (daily only) |

## Crop ET Methods

| Method | Description |
|--------|-------------|
| [`etc`](eto.md#eto.crop_coefficients.etc) | Single crop coefficient ETc = Kc × ETo |
| [`etc_dual`](eto.md#eto.methods.dual_kc.etc_dual) | Dual crop coefficient ETc = (Kcb + Ke) × ETo |
| [`etc_adj`](eto.md#eto.crop_coefficients.etc_adj) | Water-stress adjusted ETc = Ks × Kc × ETo |

## Utility Functions

| Function | Description |
|----------|-------------|
| [`kc_adjust`](eto.md#eto.crop_coefficients.kc_adjust) | Climate adjustment of Kc (FAO 56 Eq 62) |
