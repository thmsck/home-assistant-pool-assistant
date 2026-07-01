"""Pool water chemistry model based on O'Brien/USEPA cyanuric acid system."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

MW_CL2 = 70.906
MW_CYA = 129.07

PKA = {
    "K1a": 1.80,
    "K2": 3.75,
    "K4": 5.33,
    "K6": 6.88,
    "K7a": 4.51,
    "K8": 10.12,
    "K10": 11.40,
    "K11a": 6.90,
    "K12": 13.50,
    "K": 7.54,
}


@dataclass(frozen=True)
class PoolChemistryResult:
    """Calculated chlorine/cyanuric-acid speciation."""

    ph: float
    free_chlorine_mg_l: float
    cya_mg_l: float
    temperature_c: float
    hocl_mg_l: float
    ocl_mg_l: float
    unbound_chlorine_percent: float
    cya_bound_chlorine_percent: float
    species_percent: dict[str, float]
    model: str = "OBrien-USEPA cyanuric acid equilibrium with temperature-adjusted HOCl pKa"


def calculate_pool_chemistry(
    *,
    ph: float,
    free_chlorine_mg_l: float,
    cya_mg_l: float,
    temperature_c: float = 25.0,
) -> PoolChemistryResult:
    """Calculate free chlorine speciation for pool water.

    Inputs follow the USEPA simulator convention:
    - free_chlorine_mg_l is treated as total chlorine in the equilibrium system,
      expressed as mg/L as Cl2.
    - cya_mg_l is total cyanurate as cyanuric acid.

    The cyanuric-acid equilibrium constants are the O'Brien/USEPA constants for
    25 C. The HOCl/OCl pKa is temperature-adjusted.
    """

    _validate_inputs(ph, free_chlorine_mg_l, cya_mg_l, temperature_c)

    pka = PKA | {"K": _hocl_pka_for_temperature(temperature_c)}
    constants = {name: 10 ** (-value) for name, value in pka.items()}
    hydrogen = 10 ** (-ph)
    total_chlorine = free_chlorine_mg_l / 1000.0 / MW_CL2
    total_cyanurate = cya_mg_l / 1000.0 / MW_CYA

    if free_chlorine_mg_l == 0:
        return PoolChemistryResult(
            ph=ph,
            free_chlorine_mg_l=free_chlorine_mg_l,
            cya_mg_l=cya_mg_l,
            temperature_c=temperature_c,
            hocl_mg_l=0.0,
            ocl_mg_l=0.0,
            unbound_chlorine_percent=0.0,
            cya_bound_chlorine_percent=0.0,
            species_percent=_empty_species(),
        )

    if cya_mg_l == 0:
        hocl = total_chlorine / (1.0 + constants["K"] / hydrogen)
        ocl = total_chlorine - hocl
        species_percent = _empty_species()
        species_percent["HOCl"] = hocl / total_chlorine * 100.0
        species_percent["OCl"] = ocl / total_chlorine * 100.0

        return PoolChemistryResult(
            ph=ph,
            free_chlorine_mg_l=free_chlorine_mg_l,
            cya_mg_l=cya_mg_l,
            temperature_c=temperature_c,
            hocl_mg_l=hocl * MW_CL2 * 1000.0,
            ocl_mg_l=ocl * MW_CL2 * 1000.0,
            unbound_chlorine_percent=100.0,
            cya_bound_chlorine_percent=0.0,
            species_percent=species_percent,
        )

    hocl = _solve_hocl(
        hydrogen=hydrogen,
        total_chlorine=total_chlorine,
        total_cyanurate=total_cyanurate,
        constants=constants,
    )
    species_mol_l = _calculate_species(
        hocl=hocl,
        hydrogen=hydrogen,
        total_cyanurate=total_cyanurate,
        constants=constants,
    )

    species_percent = {
        name: _chlorine_equivalent_fraction(name, value) / total_chlorine * 100.0
        for name, value in species_mol_l.items()
    }
    hocl_mg_l = hocl * MW_CL2 * 1000.0
    ocl_mg_l = species_mol_l["OCl"] * MW_CL2 * 1000.0
    unbound_percent = species_percent["HOCl"] + species_percent["OCl"]

    return PoolChemistryResult(
        ph=ph,
        free_chlorine_mg_l=free_chlorine_mg_l,
        cya_mg_l=cya_mg_l,
        temperature_c=temperature_c,
        hocl_mg_l=hocl_mg_l,
        ocl_mg_l=ocl_mg_l,
        unbound_chlorine_percent=unbound_percent,
        cya_bound_chlorine_percent=max(0.0, 100.0 - unbound_percent),
        species_percent=species_percent,
    )


def _solve_hocl(
    *,
    hydrogen: float,
    total_chlorine: float,
    total_cyanurate: float,
    constants: dict[str, float],
) -> float:
    """Solve the USEPA working equation for HOCl using bisection."""

    upper = total_chlorine / (1.0 + constants["K"] / hydrogen)
    lower = 1e-20
    upper *= 0.999999999999

    def equation(hocl: float) -> float:
        return (
            total_chlorine - hocl * (1.0 + constants["K"] / hydrogen)
        ) * _cyanurate_denominator(
            hocl, hydrogen, constants
        ) - total_cyanurate * _chlorine_denominator(hocl, hydrogen, constants)

    lower_value = equation(lower)
    upper_value = equation(upper)
    if lower_value == 0:
        return lower
    if upper_value == 0:
        return upper
    if lower_value * upper_value > 0:
        raise ValueError("Could not bracket HOCl solution")

    for _ in range(200):
        midpoint = (lower + upper) / 2.0
        midpoint_value = equation(midpoint)
        if midpoint_value == 0:
            return midpoint
        if lower_value * midpoint_value > 0:
            lower = midpoint
            lower_value = midpoint_value
        else:
            upper = midpoint

    return (lower + upper) / 2.0


def _chlorine_denominator(hocl: float, hydrogen: float, k: dict[str, float]) -> float:
    return (
        3
        * hydrogen**3
        * hocl**3
        / (k["K12"] * k["K11a"] * k["K8"] * k["K7a"] * k["K2"] * k["K1a"])
        + 2
        * hydrogen**3
        * hocl**2
        / (k["K12"] * k["K11a"] * k["K8"] * k["K7a"] * k["K2"])
        + hydrogen**3 * hocl / (k["K12"] * k["K11a"] * k["K8"] * k["K4"])
        + 2 * hydrogen**2 * hocl**2 / (k["K12"] * k["K11a"] * k["K8"] * k["K7a"])
        + hydrogen**2 * hocl / (k["K12"] * k["K11a"] * k["K8"])
        + hydrogen * hocl / (k["K12"] * k["K11a"])
    )


def _cyanurate_denominator(hocl: float, hydrogen: float, k: dict[str, float]) -> float:
    return (
        hydrogen**3
        * hocl**3
        / (k["K12"] * k["K11a"] * k["K8"] * k["K7a"] * k["K2"] * k["K1a"])
        + hydrogen**3
        * hocl**2
        / (k["K12"] * k["K11a"] * k["K8"] * k["K7a"] * k["K2"])
        + hydrogen**3 * hocl / (k["K12"] * k["K11a"] * k["K8"] * k["K4"])
        + hydrogen**2 * hocl**2 / (k["K12"] * k["K11a"] * k["K8"] * k["K7a"])
        + hydrogen**2 * hocl / (k["K12"] * k["K11a"] * k["K8"])
        + hydrogen * hocl / (k["K12"] * k["K11a"])
        + hydrogen**3 / (k["K12"] * k["K10"] * k["K6"])
        + hydrogen**2 / (k["K12"] * k["K10"])
        + hydrogen / k["K12"]
        + 1.0
    )


def _calculate_species(
    *,
    hocl: float,
    hydrogen: float,
    total_cyanurate: float,
    constants: dict[str, float],
) -> dict[str, float]:
    k = constants
    cy3 = total_cyanurate / _cyanurate_denominator(hocl, hydrogen, k)
    return {
        "HOCl": hocl,
        "OCl": k["K"] * hocl / hydrogen,
        "HClCy": hydrogen**2 * hocl * cy3 / (k["K12"] * k["K11a"] * k["K8"]),
        "ClCy": hydrogen * hocl * cy3 / (k["K12"] * k["K11a"]),
        "H2ClCy": hydrogen**3
        * hocl
        * cy3
        / (k["K12"] * k["K11a"] * k["K8"] * k["K4"]),
        "Cl2Cy": hydrogen**2
        * hocl**2
        * cy3
        / (k["K12"] * k["K11a"] * k["K8"] * k["K7a"]),
        "HCl2Cy": hydrogen**3
        * hocl**2
        * cy3
        / (k["K12"] * k["K11a"] * k["K8"] * k["K7a"] * k["K2"]),
        "Cl3Cy": hydrogen**3
        * hocl**3
        * cy3
        / (k["K12"] * k["K11a"] * k["K8"] * k["K7a"] * k["K2"] * k["K1a"]),
    }


def _chlorine_equivalent_fraction(species_name: str, mol_l: float) -> float:
    chlorine_atoms = 3 if species_name == "Cl3Cy" else 2 if species_name in {"Cl2Cy", "HCl2Cy"} else 1
    return chlorine_atoms * mol_l


def _hocl_pka_for_temperature(temperature_c: float) -> float:
    temperature_k = temperature_c + 273.15
    return 3000.0 / temperature_k - 10.0686 + 0.0253 * temperature_k


def _empty_species() -> dict[str, float]:
    return {
        "HOCl": 0.0,
        "OCl": 0.0,
        "HClCy": 0.0,
        "ClCy": 0.0,
        "H2ClCy": 0.0,
        "Cl2Cy": 0.0,
        "HCl2Cy": 0.0,
        "Cl3Cy": 0.0,
    }


def _validate_inputs(
    ph: float,
    free_chlorine_mg_l: float,
    cya_mg_l: float,
    temperature_c: float,
) -> None:
    values = {
        "pH": ph,
        "free_chlorine_mg_l": free_chlorine_mg_l,
        "cya_mg_l": cya_mg_l,
        "temperature_c": temperature_c,
    }
    for name, value in values.items():
        if not isfinite(value):
            raise ValueError(f"{name} must be finite")
    if not 0 < ph < 14:
        raise ValueError("pH must be between 0 and 14")
    if free_chlorine_mg_l < 0:
        raise ValueError("free_chlorine_mg_l must not be negative")
    if cya_mg_l < 0:
        raise ValueError("cya_mg_l must not be negative")
    if not 0 <= temperature_c <= 50:
        raise ValueError("temperature_c must be between 0 and 50 C")
