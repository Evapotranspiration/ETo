# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ETo is a Python package for calculating reference evapotranspiration (ETo) and crop evapotranspiration (ETc) based on the FAO 56 paper. It requires a minimum of T_min and T_max for daily estimates or T_mean and RH_mean for hourly estimates, and uses all available meteorological parameters to improve accuracy. Supports daily, hourly, and monthly time steps.

Only production dependency: `numpy`. Build system: `uv`.

## Common Commands

```bash
# Run all tests
uv run pytest

# Run a single test
uv run pytest eto/tests/test_eto.py::test_name

# Install in development mode
uv sync

# Lint (used in CI)
uv run flake8
```

## Architecture

The main `ETo` class (`eto/core.py`) orchestrates the workflow:
1. **Parameter estimation** (`eto/param_est.py`) — estimates missing meteorological parameters from available data. Handles daily (`'D'`), hourly (`'h'`), and monthly (`'M'`) frequencies. Tracks estimation quality with a numeric scale. Also computes derived parameters: `T_dew` (inverse Magnus from e_a), `VPD` (vapour pressure deficit), and `delta` (slope of saturation vapour pressure curve).
2. **ETo calculation methods** (`eto/methods/`) — `eto_fao()` (FAO 56 standard, supports short/tall reference crop via ASCE standardization) and `hargreaves()` (simplified, daily only).
3. **Crop coefficient methods** — `etc()` (single Kc, FAO 56 Table 12), `etc_dual()` (dual Kcb+Ke, FAO 56 Eq 58), `etc_adj()` (water stress Ks, FAO 56 Eq 84). Defined in `eto/crop_coefficients.py` and `eto/methods/dual_kc.py`.

Methods are attached to the `ETo` class dynamically at module level (bottom of `core.py`), not defined as regular class methods. They receive `self` as first parameter and act as instance methods.

**Typical flow**: `ETo(data_dict, freq, lat=..., z_msl=..., dates=...)` or `ETo(data_dict, freq, lat=..., z_msl=..., day_of_year=..., hour=...)` → `param_est()` populates `self.ts_param` (`dict[str, np.ndarray]` of estimated parameters) and `self.est_val` (`np.ndarray`) → `eto_fao()` or `eto_hargreaves()` returns `np.ndarray`. For crop ET: `etc(Kc=...)` or `etc(crop='maize_grain', stage='mid')`.

Key input dict keys: `R_n`, `R_s`, `G`, `T_min`, `T_max`, `T_mean`, `T_dew`, `RH_min`, `RH_max`, `RH_mean`, `n_sun`, `U_z`, `P`, `e_a`.

Derived output keys in `ts_param`: `VPD`, `T_dew` (if back-calculated), `delta`, `gamma`, `e_s`, `e_mean`, `R_a`, `U_2`.

## Branch Strategy

- `dev` — development branch
- `master` — stable/release branch
- CI runs tests on push to `dev` and PRs to `master` (Python 3.8–3.11)
