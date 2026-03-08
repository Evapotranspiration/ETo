# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ETo is a Python package for calculating reference evapotranspiration (ETo) based on the FAO 56 paper. It requires a minimum of T_min and T_max for daily estimates or T_mean and RH_mean for hourly estimates, and uses all available meteorological parameters to improve accuracy.

Only production dependency: `pandas`. Build system: `uv`.

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
1. **Parameter estimation** (`eto/param_est.py`) — estimates missing meteorological parameters from available data. Handles both daily (`'D'`) and hourly (`'h'`) frequencies. Tracks estimation quality with a 0-3 scale.
2. **ETo calculation methods** (`eto/methods/`) — `eto_fao()` (FAO 56 standard) and `hargreaves()` (simplified, daily only).

Methods are attached to the `ETo` class dynamically at module level (bottom of `core.py`), not defined as regular class methods. They receive `self` as first parameter and act as instance methods.

**Typical flow**: `ETo(df, freq, lat=..., z_msl=...)` → `param_est()` populates `self.ts_param` (DataFrame of estimated parameters) → `eto_fao()` or `eto_hargreaves()` computes ET using those parameters.

Key input columns: `R_n`, `R_s`, `G`, `T_min`, `T_max`, `T_mean`, `T_dew`, `RH_min`, `RH_max`, `RH_mean`, `n_sun`, `U_z`, `P`, `e_a`.

## Branch Strategy

- `dev` — development branch
- `master` — stable/release branch
- CI runs tests on push to `dev` and PRs to `master` (Python 3.8–3.11)
