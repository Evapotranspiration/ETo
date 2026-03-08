# Methodology

## Reference Evapotranspiration (ETo)

Evapotranspiration (ET) is the combined process of evaporation from surfaces and transpiration from plant tissues. Since direct measurement of actual ET is difficult, indirect estimates are made using meteorological data.

The international standard for estimating reference ET was developed by the United Nations Food and Agriculture Organization (UN-FAO). The method uses the Penman-Monteith equation and provides guidelines for estimating missing meteorological parameters. It can work with as little data as minimum and maximum temperature, up to the full set of meteorological parameters.

The term "reference ET" (ETo) defines a specific vegetated surface (a hypothetical grass reference crop) by which the ET estimation is standardised. Different crop coefficients can then be applied to convert ETo to other crop types.

### FAO 56 Penman-Monteith

The FAO 56 Penman-Monteith equation is implemented in `eto_fao()`. It supports both daily and hourly time steps.

Extensive documentation on the methods and concepts can be found in the [UN-FAO 56 paper](http://www.fao.org/docrep/X0490E/X0490E00.htm).

### Parameter estimation

When input data is incomplete, the package estimates missing parameters using the fallback chains defined in FAO 56. Parameters are estimated in a specific order, and each estimation step is tracked in the `est_val` quality array. If a parameter is provided in the input data, the corresponding estimation is skipped entirely.

The parameters are estimated in the following order:

#### Atmospheric pressure (P)

If `P` is not provided, it is estimated from station elevation (`z_msl`):

1. P = 101.3 × ((293 - 0.0065 × z_msl) / 293)^5.26 (FAO Eq 7)

#### Mean temperature (T_mean)

If `T_mean` is not provided (daily mode only — hourly requires it as input):

1. T_mean = (T_max + T_min) / 2 (FAO Eq 9)

#### Actual vapour pressure (e_a)

**Hourly mode:**

If `e_a` is not provided, it is estimated from `RH_mean` (which is required for hourly):

1. e_a = e°(T_mean) × RH_mean / 100

**Daily mode:**

The daily fallback chain tries each method in order, stopping at the first that fills all missing values:

1. From dew point temperature T_dew (FAO Eq 14) — best quality
2. From RH_min + RH_max (FAO Eq 17) — e_a = (e°(T_min) × RH_max + e°(T_max) × RH_min) / 200
3. From RH_max only (FAO Eq 18) — e_a = e°(T_min) × RH_max / 100
4. From RH_mean only (FAO Eq 19) — e_a = RH_mean / 100 × (e°(T_max) + e°(T_min)) / 2
5. From T_min (FAO Eq 48) — e_a = e°(T_min) — last resort, assumes dew point ≈ T_min

#### Incoming solar radiation (R_s)

Extraterrestrial radiation (R_a) is always computed from latitude and day of year (FAO Eq 21/28). Then, if `R_s` is not provided:

1. From sunshine hours `n_sun` using the Angstrom formula (FAO Eq 35) — R_s = (a_s + b_s × n/N) × R_a
2. From temperature range using the Hargreaves radiation formula (FAO Eq 50) — R_s = K_rs × (T_max - T_min)^0.5 × R_a

#### Net radiation (R_n)

If `R_n` is not provided, it is computed from R_s:

1. R_n = R_ns - R_nl, where R_ns = (1 - albedo) × R_s (FAO Eq 38) and R_nl is the net outgoing longwave radiation (FAO Eq 39 for daily, Eq 40 for hourly)

#### Soil heat flux (G)

If `G` is not provided:

- **Daily**: G = 0 (FAO Eq 42 — negligible for daily time steps)
- **Hourly daytime** (R_n > 0): G = 0.1 × R_n (FAO Eq 45)
- **Hourly nighttime** (R_n ≤ 0): G = 0.5 × R_n (FAO Eq 46)

#### Wind speed (U_2)

Wind speed at 2 m height is needed for the Penman-Monteith equation. If `U_z` is provided, it is converted:

1. U_2 = U_z × 4.87 / ln(67.8 × z_u - 5.42) (FAO Eq 47)

If `U_z` is not provided, a default of U_2 = 2 m/s is used (FAO recommendation for missing wind data).

## Hargreaves

The Hargreaves equation is a simplified method for estimating ETo using only temperature data. It is implemented in `eto_hargreaves()` and is only valid for daily time steps.

The [History and Evaluation of Hargreaves Evapotranspiration Equation](http://onlinecalc.sdsu.edu/onlinehargreaves.pdf) provides a detailed description and background.

## References

1. Allen, R. G., Pereira, L. S., Raes, D., & Smith, M. (1998). Crop evapotranspiration — Guidelines for computing crop water requirements. FAO Irrigation and drainage paper 56. FAO, Rome, 300(9), D05109.
2. Hargreaves, G. and Allen, R. (2003). History and Evaluation of Hargreaves Evapotranspiration Equation. Journal of Irrigation and Drainage Engineering. Vol. 129, Issue 1 (February 2003).
