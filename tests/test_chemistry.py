from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


CHEMISTRY_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "pool_assistant"
    / "chemistry.py"
)
SPEC = importlib.util.spec_from_file_location("pool_assistant_chemistry", CHEMISTRY_PATH)
chemistry = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = chemistry
SPEC.loader.exec_module(chemistry)

calculate_pool_chemistry = chemistry.calculate_pool_chemistry


def test_poollab_reference_case_matches_hocl() -> None:
    result = calculate_pool_chemistry(
        ph=6.9,
        free_chlorine_mg_l=3.0,
        cya_mg_l=140.0,
        temperature_c=26.0,
    )

    assert result.hocl_mg_l == pytest_approx(0.0126, abs=0.0005)
    assert result.species_percent["HOCl"] == pytest_approx(0.42, abs=0.03)
    assert result.species_percent["OCl"] == pytest_approx(0.10, abs=0.03)
    assert result.species_percent["HClCy"] == pytest_approx(95.89, abs=0.3)
    assert result.unbound_chlorine_percent == pytest_approx(0.52, abs=0.05)
    assert result.cya_bound_chlorine_percent == pytest_approx(99.48, abs=0.05)


def test_zero_chlorine_returns_zero_speciation() -> None:
    result = calculate_pool_chemistry(
        ph=7.2,
        free_chlorine_mg_l=0.0,
        cya_mg_l=30.0,
    )

    assert result.hocl_mg_l == 0
    assert result.unbound_chlorine_percent == 0
    assert result.cya_bound_chlorine_percent == 0


def test_zero_cya_uses_hocl_ocl_equilibrium() -> None:
    result = calculate_pool_chemistry(
        ph=7.4,
        free_chlorine_mg_l=0.2,
        cya_mg_l=0.0,
        temperature_c=29.0,
    )

    assert result.hocl_mg_l == pytest_approx(0.1120, abs=0.0001)
    assert result.species_percent["HOCl"] == pytest_approx(55.99, abs=0.01)
    assert result.species_percent["OCl"] == pytest_approx(44.01, abs=0.01)
    assert result.unbound_chlorine_percent == 100
    assert result.cya_bound_chlorine_percent == 0


def pytest_approx(*args, **kwargs):
    import pytest

    return pytest.approx(*args, **kwargs)
