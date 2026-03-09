# Methodology

## Reference Evapotranspiration (ETo)

Evapotranspiration (ET) is the combined process of evaporation from surfaces and transpiration from plant tissues. Since direct measurement of actual ET is difficult, indirect estimates are made using meteorological data.

The international standard for estimating reference ET was developed by the United Nations Food and Agriculture Organization (UN-FAO). The method uses the Penman-Monteith equation and provides guidelines for estimating missing meteorological parameters. It can work with as little data as minimum and maximum temperature, up to the full set of meteorological parameters.

The term "reference ET" (ETo) defines a specific vegetated surface (a hypothetical grass reference crop) by which the ET estimation is standardised. Different crop coefficients can then be applied to convert ETo to other crop types.

### FAO 56 Penman-Monteith

The FAO 56 Penman-Monteith equation is implemented in `eto_fao()`. It supports daily, hourly, and monthly time steps.

The `ref_crop` parameter selects the reference surface:

- `'short'` (default) — FAO 56 grass reference (Cn=900, Cd=0.34 for daily)
- `'tall'` — ASCE alfalfa reference (Cn=1600, Cd=0.38 for daily; Cn=66, Cd varies day/night for hourly)

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

#### Dew point temperature (T_dew)

After e_a is determined, if T_dew was not provided as input, it is back-calculated using the inverse Magnus formula:

T_dew = 237.3 × ln(e_a / 0.6108) / (17.27 - ln(e_a / 0.6108))

This makes T_dew available in `ts_param` for downstream use regardless of input.

#### Vapour pressure deficit (VPD)

VPD is always computed and stored in `ts_param`:

- **Daily**: VPD = e_s - e_a
- **Hourly**: VPD = e_mean - e_a

#### Incoming solar radiation (R_s)

Extraterrestrial radiation (R_a) is always computed from latitude and day of year (FAO Eq 21 for daily, Eq 28 for hourly). For hourly data, R_a is clamped to ≥ 0 to prevent negative values when the sun is below the horizon.

If `R_s` is not provided:

1. From sunshine hours `n_sun` using the Angstrom formula (FAO Eq 35) — R_s = (a_s + b_s × n/N) × R_a
2. From temperature range using the Hargreaves radiation formula (FAO Eq 50) — R_s = K_rs × (T_max - T_min)^0.5 × R_a

#### Clear-sky radiation (R_so)

R_so is used to compute the cloudiness factor for net longwave radiation:

- When default Angstrom coefficients are used (a_s=0.25, b_s=0.5): R_so = (0.75 + 2×10⁻⁵ × z_msl) × R_a (FAO Eq 37)
- When custom a_s/b_s are provided: R_so = (a_s + b_s) × R_a (FAO Eq 36)

The R_s/R_so ratio is computed safely — when R_so = 0 (nighttime hours), the ratio defaults to 1.0 to avoid division by zero.

#### Net radiation (R_n)

If `R_n` is not provided, it is computed from R_s:

1. R_n = R_ns - R_nl, where R_ns = (1 - albedo) × R_s (FAO Eq 38) and R_nl is the net outgoing longwave radiation (FAO Eq 39 for daily, Eq 40 for hourly)

#### Soil heat flux (G)

If `G` is not provided:

- **Daily**: G = 0 (FAO Eq 42 — negligible for daily time steps)
- **Hourly daytime** (R_n > 0): G = 0.1 × R_n (FAO Eq 45)
- **Hourly nighttime** (R_n ≤ 0): G = 0.5 × R_n (FAO Eq 46)
- **Monthly**: G = 0.14 × (T_mean_i - T_mean_{i-1}) (FAO Eq 44, first month defaults to 0)

#### Wind speed (U_2)

Wind speed at 2 m height is needed for the Penman-Monteith equation. If `U_z` is provided, it is converted:

1. U_2 = U_z × 4.87 / ln(67.8 × z_u - 5.42) (FAO Eq 47)

If `U_z` is not provided, a default of U_2 = 2 m/s is used (FAO recommendation for missing wind data).

### Output clamping

ETo values are clamped at the lower bound (default 0 mm) since physically ETo cannot be negative. Values exceeding the upper bound (default 15 mm) are set to NaN to flag suspect data. This applies to both `eto_fao()` and `eto_hargreaves()`.

## Hargreaves

The Hargreaves equation is a simplified method for estimating ETo using only temperature data. It is implemented in `eto_hargreaves()` and is only valid for daily time steps.

The [History and Evaluation of Hargreaves Evapotranspiration Equation](http://onlinecalc.sdsu.edu/onlinehargreaves.pdf) provides a detailed description and background.

## Crop Evapotranspiration (ETc)

Crop evapotranspiration is estimated by multiplying reference ET by crop coefficients.

### Single crop coefficient (ETc = Kc × ETo)

The `etc()` method implements FAO 56 Chapter 6. A single crop coefficient Kc integrates crop and soil evaporation effects. Kc values can be provided directly or looked up from the built-in `KC_TABLE` (FAO 56 Table 12) for 23 major crops at three growth stages (ini, mid, end).

The `kc_adjust()` function provides climate adjustment of tabulated Kc values for non-standard conditions (FAO 56 Eq 62), accounting for wind speed, humidity, and plant height.

### Dual crop coefficient (ETc = (Kcb + Ke) × ETo)

The `etc_dual()` method implements FAO 56 Chapter 7. The basal crop coefficient (Kcb) represents transpiration only, while the soil evaporation coefficient (Ke) is either provided directly or estimated from the evaporation reduction coefficient (Kr), maximum Kc (Kc_max), and exposed wetted soil fraction (few) per FAO 56 Eq 71.

### Water stress (ETc_adj = Ks × Kc × ETo)

The `etc_adj()` method implements FAO 56 Eq 84. The water stress coefficient Ks reduces ETc based on root zone depletion:

Ks = clip((TAW - Dr) / ((1 - p) × TAW), 0, 1)

where TAW is total available water, Dr is root zone depletion, and p is the depletion fraction for no stress (default 0.5).

## References

1. Allen, R. G., Pereira, L. S., Raes, D., & Smith, M. (1998). Crop evapotranspiration — Guidelines for computing crop water requirements. FAO Irrigation and drainage paper 56. FAO, Rome, 300(9), D05109.
2. Hargreaves, G. and Allen, R. (2003). History and Evaluation of Hargreaves Evapotranspiration Equation. Journal of Irrigation and Drainage Engineering. Vol. 129, Issue 1 (February 2003).
3. ASCE-EWRI (2005). The ASCE Standardized Reference Evapotranspiration Equation. ASCE Task Committee on Standardization of Reference Evapotranspiration.
