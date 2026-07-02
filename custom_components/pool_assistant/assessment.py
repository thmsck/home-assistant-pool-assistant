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
    recommendation_state: str
    recommendation_summary: str
    recommendations: tuple[str, ...]
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
    recommendation_state, recommendation_summary, recommendations = _recommendation(
        ph=ph,
        hocl_mg_l=hocl_mg_l,
        cya_mg_l=cya_mg_l,
        alkalinity_mg_l=alkalinity_mg_l,
        bound_chlorine_mg_l=bound_chlorine_mg_l,
        chlorine_plausible=chlorine_plausible,
        measurement_status=measurement_status,
        disinfection_state=disinfection_state,
        algae_risk=algae_risk,
        load_status=load_status,
    )

    return PoolAssessment(
        algae_risk=algae_risk,
        chemistry_index=chemistry_index,
        pool_status=pool_status,
        summary=summary,
        load_status=load_status,
        recommendation_state=recommendation_state,
        recommendation_summary=recommendation_summary,
        recommendations=recommendations,
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


def _recommendation(
    *,
    ph: float,
    hocl_mg_l: float,
    cya_mg_l: float,
    alkalinity_mg_l: float | None,
    bound_chlorine_mg_l: float | None,
    chlorine_plausible: bool | None,
    measurement_status: str | None,
    disinfection_state: str,
    algae_risk: str,
    load_status: str,
) -> tuple[str, str, tuple[str, ...]]:
    if measurement_status == "stale":
        return (
            "Messen",
            "Messwerte sind veraltet.",
            (
                "Vollständige PoolLab-Messreihe durchführen.",
                "Vor Dosierentscheidungen pH, freies Chlor, Gesamtchlor, CYA und Alkalinität aktualisieren.",
            ),
        )
    if measurement_status == "unsynced":
        return (
            "Messen",
            "Messwerte stammen nicht aus derselben Messreihe.",
            (
                "Relevante PoolLab-Werte in einer zusammenhängenden Messreihe neu messen.",
                "Vor Dosierentscheidungen keine gemischten Alt- und Neumessungen verwenden.",
            ),
        )
    if chlorine_plausible is False:
        return (
            "Messen",
            "Freies Chlor und Gesamtchlor sind unplausibel.",
            (
                "Freies Chlor und Gesamtchlor direkt nacheinander erneut messen.",
                "Küvetten, Tabletten/Reagenzien und Messablauf prüfen.",
            ),
        )

    priority = 0
    actions: list[str] = []

    if disinfection_state == "critical":
        priority = max(priority, 3)
        actions.append("Aktives Chlor ist zu niedrig; Desinfektionsleistung zeitnah erhöhen.")
    elif disinfection_state == "limited":
        priority = max(priority, 1)
        actions.append("Aktives Chlor liegt im gelben Bereich; bei Sonne, Badebetrieb oder Trübung freies Chlor erhöhen.")

    if algae_risk == "critical":
        priority = max(priority, 3)
        actions.append("Chemisches Algenrisiko ist kritisch; Ursache vor Nutzung prüfen.")
    elif algae_risk == "high":
        priority = max(priority, 2)
        actions.append("Chemisches Algenrisiko ist erhöht; HOCl, pH und CYA gezielt korrigieren.")
    elif algae_risk == "medium":
        priority = max(priority, 1)
        actions.append("Chemisches Algenrisiko beobachten; Entwicklung nach Umwälzung oder Nachdosierung erneut prüfen.")

    if load_status == "high":
        priority = max(priority, 2)
        actions.append("Gebundenes Chlor ist hoch; oxidieren/schocken und Filterbetrieb prüfen.")
    elif load_status == "elevated":
        priority = max(priority, 1)
        actions.append("Gebundenes Chlor ist erhöht; Filter laufen lassen und freies/Gesamtchlor erneut messen.")
    elif load_status == "slightly_elevated":
        priority = max(priority, 1)
        actions.append("Gebundenes Chlor ist leicht erhöht; weiter beobachten.")

    if ph > 7.8:
        priority = max(priority, 2)
        actions.append("pH ist deutlich erhöht; pH senken, da die Chlorwirkung reduziert ist.")
    elif ph > 7.6:
        priority = max(priority, 1)
        actions.append("pH ist erhöht; pH-Senkung prüfen.")
    elif ph < 7.0:
        priority = max(priority, 2)
        actions.append("pH ist niedrig; pH anheben und Messung bestätigen.")

    if cya_mg_l > 90:
        priority = max(priority, 2)
        actions.append("CYA ist sehr hoch; kein organisches Chlor verwenden und Verdünnung/Wasserwechsel planen.")
    elif cya_mg_l > 70:
        priority = max(priority, 1)
        actions.append("CYA ist erhöht; organisches Chlor vermeiden und Entwicklung beobachten.")

    if alkalinity_mg_l is not None:
        if alkalinity_mg_l < 50:
            priority = max(priority, 2)
            actions.append("Alkalinität ist niedrig; pH-Stabilität prüfen und TA-Anhebung planen.")
        elif alkalinity_mg_l < 70:
            priority = max(priority, 1)
            actions.append("Alkalinität ist leicht niedrig; pH-Schwankungen beobachten.")
        elif alkalinity_mg_l > 150:
            priority = max(priority, 1)
            actions.append("Alkalinität ist hoch; pH-Korrekturen können träge reagieren.")

    if not actions:
        return (
            "Keine Maßnahme",
            "Wasserchemie liegt im Zielbereich.",
            ("Regulären Messrhythmus beibehalten.",),
        )

    if priority >= 3:
        state = "Kritisch"
        summary = "Zeitnah korrigieren."
    elif priority == 2:
        state = "Korrigieren"
        summary = "Korrektur ist sinnvoll."
    else:
        state = "Beobachten"
        summary = "Werte beobachten und bei Bedarf nachmessen."

    return state, summary, tuple(dict.fromkeys(actions))
