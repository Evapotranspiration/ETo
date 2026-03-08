# Methodology

## Reference Evapotranspiration (ETo)

Evapotranspiration (ET) is the combined process of evaporation from surfaces and transpiration from plant tissues. Since direct measurement of actual ET is difficult, indirect estimates are made using meteorological data.

The international standard for estimating reference ET was developed by the United Nations Food and Agriculture Organization (UN-FAO). The method uses the Penman-Monteith equation and provides guidelines for estimating missing meteorological parameters. It can work with as little data as minimum and maximum temperature, up to the full set of meteorological parameters.

The term "reference ET" (ETo) defines a specific vegetated surface (a hypothetical grass reference crop) by which the ET estimation is standardised. Different crop coefficients can then be applied to convert ETo to other crop types.

### FAO 56 Penman-Monteith

The FAO 56 Penman-Monteith equation is implemented in `eto_fao()`. It supports both daily and hourly time steps.

Extensive documentation on the methods and concepts can be found in the [UN-FAO 56 paper](http://www.fao.org/docrep/X0490E/X0490E00.htm).

### Parameter estimation

When input data is incomplete, the package estimates missing parameters using the fallback chains defined in FAO 56. Parameters are estimated in a specific order, and each estimation step is tracked in the `est_val` quality array.

The estimation chain for actual vapour pressure (e_a), for example:

1. From dew point temperature (FAO Eq 14) — best
2. From RH_min + RH_max (FAO Eq 17)
3. From RH_max only (FAO Eq 18)
4. From RH_mean (FAO Eq 19)
5. From T_min (FAO Eq 48) — last resort

## Hargreaves

The Hargreaves equation is a simplified method for estimating ETo using only temperature data. It is implemented in `eto_hargreaves()` and is only valid for daily time steps.

The [History and Evaluation of Hargreaves Evapotranspiration Equation](http://onlinecalc.sdsu.edu/onlinehargreaves.pdf) provides a detailed description and background.

## References

1. Allen, R. G., Pereira, L. S., Raes, D., & Smith, M. (1998). Crop evapotranspiration — Guidelines for computing crop water requirements. FAO Irrigation and drainage paper 56. FAO, Rome, 300(9), D05109.
2. Hargreaves, G. and Allen, R. (2003). History and Evaluation of Hargreaves Evapotranspiration Equation. Journal of Irrigation and Drainage Engineering. Vol. 129, Issue 1 (February 2003).
