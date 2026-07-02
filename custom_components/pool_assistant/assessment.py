"""Pool water assessment logic for Pool Assistant."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PoolAssessment:
    """Human-oriented assessment of pool water state."""

    algae_risk: str
    chemistry_index: int
    pool_status: str
    summary: str
    load_status: str
    ph_score: int
    disinfection_score: int
    cya_score: int
    alkalinity_score: int | None
    bound_chlorine_score: int | None
    measurement_score: int


def assess_pool_water(
    *,
    ph: float,
    hocl_mg_l: float,
    cya_mg_l: float,
    alkalinity_mg_l: float | None,
    bound_chlorine_mg_l: float | None,
    chlorine_plausible: bool | None,
    measurement_status: str | None,
) -> PoolAssessment:
    """Assess pool water quality from calculated chemistry and source quality."""

    disinfection_state = _disinfection_state(hocl_mg_l)
    algae_risk = _algae_risk(
        ph=ph,
        hocl_mg_l=hocl_mg_l,
        cya_mg_l=cya_mg_l,
        chlorine_plausible=chlorine_plausible,
        measurement_status=measurement_status,
    )
    load_status = _load_status(bound_chlorine_mg_l, chlorine_plausible)
    ph_score = _ph_score(ph)
    disinfection_score = _disinfection_score(disinfection_state)
    cya_score = _cya_score(cya_mg_l)
    alkalinity_score = (
        _alkalinity_score(alkalinity_mg_l)
        if alkalinity_mg_l is not None
        else None
    )
    bound_chlorine_score = _bound_chlorine_score(
        bound_chlorine_mg_l,
        chlorine_plausible,
    )
    measurement_score = _measurement_score(measurement_status)

    weighted_scores = [
        (ph_score, 0.20),
        (disinfection_score, 0.35),
        (cya_score, 0.15),
        (measurement_score, 0.10),
    ]
    if alkalinity_score is not None:
        weighted_scores.append((alkalinity_score, 0.10))
    if bound_chlorine_score is not None:
        weighted_scores.append((bound_chlorine_score, 0.10))

    weight_sum = sum(weight for _score, weight in weighted_scores)
    chemistry_index = round(
        sum(score * weight for score, weight in weighted_scores) / weight_sum
    )

    pool_status, summary = _pool_status(
        chemistry_index=chemistry_index,
        algae_risk=algae_risk,
        disinfection_state=disinfection_state,
        load_status=load_status,
        chlorine_plausible=chlorine_plausible,
        measurement_status=measurement_status,
        cya_mg_l=cya_mg_l,
        ph=ph,
    )

    return PoolAssessment(
        algae_risk=algae_risk,
        chemistry_index=chemistry_index,
        pool_status=pool_status,
        summary=summary,
        load_status=load_status,
        ph_score=ph_score,
        disinfection_score=disinfection_score,
        cya_score=cya_score,
        alkalinity_score=alkalinity_score,
        bound_chlorine_score=bound_chlorine_score,
        measurement_score=measurement_score,
    )


def _disinfection_state(hocl_mg_l: float) -> str:
    if hocl_mg_l < 0.016:
        return "critical"
    if hocl_mg_l < 0.05:
        return "limited"
    return "effective"


def _algae_risk(
    *,
    ph: float,
    hocl_mg_l: float,
    cya_mg_l: float,
    chlorine_plausible: bool | None,
    measurement_status: str | None,
) -> str:
    if (
        measurement_status == "stale"
        or chlorine_plausible is False
        or hocl_mg_l < 0.010
        or cya_mg_l > 120
        or ph > 8.0
    ):
        return "critical"
    if (
        measurement_status == "unsynced"
        or hocl_mg_l < 0.016
        or cya_mg_l > 90
        or ph > 7.8
    ):
        return "high"
    if (
        hocl_mg_l < 0.05
        or cya_mg_l > 70
        or ph > 7.6
    ):
        return "medium"
    return "low"


def _ph_score(ph: float) -> int:
    if 7.2 <= ph <= 7.4:
        return 100
    if 7.0 <= ph < 7.2 or 7.4 < ph <= 7.6:
        return 85
    if 6.8 <= ph < 7.0 or 7.6 < ph <= 7.8:
        return 65
    if 6.6 <= ph < 6.8 or 7.8 < ph <= 8.0:
        return 35
    return 0


def _disinfection_score(disinfection_state: str) -> int:
    if disinfection_state == "effective":
        return 100
    if disinfection_state == "limited":
        return 70
    return 20


def _cya_score(cya_mg_l: float) -> int:
    if 20 <= cya_mg_l <= 50:
        return 100
    if 10 <= cya_mg_l < 20 or 50 < cya_mg_l <= 70:
        return 80
    if 70 < cya_mg_l <= 90:
        return 50
    if 90 < cya_mg_l <= 120:
        return 20
    return 0


def _alkalinity_score(alkalinity_mg_l: float) -> int:
    if 70 <= alkalinity_mg_l <= 120:
        return 100
    if 50 <= alkalinity_mg_l < 70 or 120 < alkalinity_mg_l <= 150:
        return 80
    if 30 <= alkalinity_mg_l < 50 or 150 < alkalinity_mg_l <= 180:
        return 50
    return 20


def _bound_chlorine_score(
    bound_chlorine_mg_l: float | None,
    chlorine_plausible: bool | None,
) -> int | None:
    if chlorine_plausible is False:
        return 40
    if bound_chlorine_mg_l is None:
        return None
    if bound_chlorine_mg_l <= 0.2:
        return 100
    if bound_chlorine_mg_l <= 0.4:
        return 80
    if bound_chlorine_mg_l <= 0.6:
        return 50
    return 20


def _load_status(
    bound_chlorine_mg_l: float | None,
    chlorine_plausible: bool | None,
) -> str:
    if chlorine_plausible is False:
        return "check_measurement"
    if bound_chlorine_mg_l is None:
        return "unknown"
    if bound_chlorine_mg_l <= 0.2:
        return "normal"
    if bound_chlorine_mg_l <= 0.4:
        return "slightly_elevated"
    if bound_chlorine_mg_l <= 0.6:
        return "elevated"
    return "high"


def _measurement_score(measurement_status: str | None) -> int:
    if measurement_status == "current":
        return 100
    if measurement_status == "unsynced":
        return 60
    if measurement_status == "stale":
        return 20
    return 40


def _pool_status(
    *,
    chemistry_index: int,
    algae_risk: str,
    disinfection_state: str,
    load_status: str,
    chlorine_plausible: bool | None,
    measurement_status: str | None,
    cya_mg_l: float,
    ph: float,
) -> tuple[str, str]:
    if measurement_status == "stale":
        return "Messwerte veraltet", "Mindestens eine relevante PoolLab-Messung ist veraltet."
    if measurement_status == "unsynced":
        return "Messwerte nicht synchron", "PoolLab-Messungen stammen nicht aus derselben Messreihe."
    if chlorine_plausible is False:
        return "Messwerte prüfen", "Gesamtchlor ist kleiner als freies Chlor. Messwerte oder Messzeitpunkte prüfen."
    if algae_risk == "critical" or chemistry_index < 50:
        return "Kritisch", "Algenrisiko oder Desinfektionsleistung ist kritisch."
    if load_status == "high":
        return "Handlungsbedarf", "Gebundenes Chlor ist deutlich erhöht."
    if algae_risk == "high" or chemistry_index < 70:
        return "Handlungsbedarf", "Poolwasser benötigt zeitnah Aufmerksamkeit."
    if load_status == "elevated":
        return "Beobachten", "Gebundenes Chlor ist erhöht."
    if algae_risk == "medium" or chemistry_index < 85:
        return "Beobachten", "Poolwasser ist nutzbar, sollte aber beobachtet werden."
    if disinfection_state == "limited":
        return "Beobachten", "Aktives Chlor tötet einige Algen und Bakterien, liegt aber unter dem grünen Bereich."
    if cya_mg_l > 70:
        return "Beobachten", "Cyanursäure ist erhöht."
    if ph > 7.6:
        return "Beobachten", "pH ist erhöht und reduziert die Chlorwirkung."
    if chemistry_index < 95:
        return "Gut", "Wasserwerte liegen im nutzbaren Zielbereich."
    return "Perfekt", "Wasserchemie ist im Zielbereich."
