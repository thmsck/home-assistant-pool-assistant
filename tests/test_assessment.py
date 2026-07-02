from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ASSESSMENT_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "pool_assistant"
    / "assessment.py"
)
SPEC = importlib.util.spec_from_file_location("pool_assistant_assessment", ASSESSMENT_PATH)
assessment = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = assessment
SPEC.loader.exec_module(assessment)

assess_pool_water = assessment.assess_pool_water


def test_good_water_scores_high() -> None:
    result = assess_pool_water(
        ph=7.3,
        hocl_mg_l=0.07,
        cya_mg_l=35,
        alkalinity_mg_l=90,
        bound_chlorine_mg_l=0.1,
        chlorine_plausible=True,
        measurement_status="current",
    )

    assert result.algae_risk == "low"
    assert result.chemistry_index == 100
    assert result.load_status == "normal"
    assert result.visual_status == "clear"
    assert result.pool_status == "Perfekt"
    assert result.recommendation_state == "Keine Maßnahme"


def test_unsynced_measurements_dominate_pool_status() -> None:
    result = assess_pool_water(
        ph=7.3,
        hocl_mg_l=0.07,
        cya_mg_l=35,
        alkalinity_mg_l=90,
        bound_chlorine_mg_l=0.1,
        chlorine_plausible=True,
        measurement_status="unsynced",
    )

    assert result.algae_risk == "high"
    assert result.pool_status == "Messwerte nicht synchron"
    assert result.measurement_score == 60
    assert result.recommendation_state == "Messen"


def test_implausible_chlorine_measurement_is_critical_risk() -> None:
    result = assess_pool_water(
        ph=7.31,
        hocl_mg_l=0.0253,
        cya_mg_l=140,
        alkalinity_mg_l=82,
        bound_chlorine_mg_l=0,
        chlorine_plausible=False,
        measurement_status="unsynced",
    )

    assert result.algae_risk == "critical"
    assert result.pool_status == "Messwerte nicht synchron"
    assert result.load_status == "check_measurement"
    assert result.bound_chlorine_score == 40
    assert result.recommendation_state == "Messen"


def test_limited_disinfection_is_medium_risk_when_measurements_are_current() -> None:
    result = assess_pool_water(
        ph=7.3,
        hocl_mg_l=0.03,
        cya_mg_l=40,
        alkalinity_mg_l=90,
        bound_chlorine_mg_l=0.1,
        chlorine_plausible=True,
        measurement_status="current",
    )

    assert result.algae_risk == "medium"
    assert result.pool_status == "Beobachten"
    assert result.disinfection_score == 70
    assert result.recommendation_state == "Beobachten"


def test_high_bound_chlorine_does_not_raise_algae_risk() -> None:
    result = assess_pool_water(
        ph=7.3,
        hocl_mg_l=0.07,
        cya_mg_l=35,
        alkalinity_mg_l=90,
        bound_chlorine_mg_l=0.8,
        chlorine_plausible=True,
        measurement_status="current",
    )

    assert result.algae_risk == "low"
    assert result.load_status == "high"
    assert result.bound_chlorine_score == 20
    assert result.pool_status == "Handlungsbedarf"
    assert result.recommendation_state == "Korrigieren"


def test_limited_disinfection_and_elevated_bound_chlorine_recommend_observation() -> None:
    result = assess_pool_water(
        ph=7.31,
        hocl_mg_l=0.0284,
        cya_mg_l=45,
        alkalinity_mg_l=82,
        bound_chlorine_mg_l=0.46,
        chlorine_plausible=True,
        measurement_status="current",
    )

    assert result.pool_status == "Beobachten"
    assert result.algae_risk == "medium"
    assert result.load_status == "elevated"
    assert result.recommendation_state == "Beobachten"
    assert any("Aktives Chlor" in action for action in result.recommendations)
    assert any("Gebundenes Chlor" in action for action in result.recommendations)


def test_cloudy_water_raises_pool_status_without_changing_chemistry_index() -> None:
    result = assess_pool_water(
        ph=7.3,
        hocl_mg_l=0.07,
        cya_mg_l=35,
        alkalinity_mg_l=90,
        bound_chlorine_mg_l=0.1,
        chlorine_plausible=True,
        measurement_status="current",
        water_appearance="Milchig",
    )

    assert result.chemistry_index == 100
    assert result.algae_risk == "low"
    assert result.visual_status == "cloudy"
    assert result.pool_status == "Handlungsbedarf"
    assert result.recommendation_state == "Korrigieren"
    assert any("milchig" in action for action in result.recommendations)


def test_green_water_is_critical_context() -> None:
    result = assess_pool_water(
        ph=7.3,
        hocl_mg_l=0.07,
        cya_mg_l=35,
        alkalinity_mg_l=90,
        bound_chlorine_mg_l=0.1,
        chlorine_plausible=True,
        measurement_status="current",
        water_appearance="Grün",
    )

    assert result.chemistry_index == 100
    assert result.algae_risk == "low"
    assert result.visual_status == "green"
    assert result.pool_status == "Kritisch"
    assert result.recommendation_state == "Kritisch"
    assert any("grün" in action.lower() for action in result.recommendations)


def test_critical_disinfection_recommends_ph_reduction_above_7_4() -> None:
    result = assess_pool_water(
        ph=7.56,
        hocl_mg_l=0.0077,
        cya_mg_l=73.3,
        alkalinity_mg_l=200,
        bound_chlorine_mg_l=0.01,
        chlorine_plausible=True,
        measurement_status="current",
        water_appearance="Grün",
    )

    assert result.pool_status == "Kritisch"
    assert result.recommendation_state == "Kritisch"
    assert any("pH auf 7,1-7,2" in action for action in result.recommendations)
    assert "pH auf 7,1-7,2" in result.recommendations[0]
