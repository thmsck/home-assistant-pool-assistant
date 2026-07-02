from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys


MEASUREMENT_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "pool_assistant"
    / "measurement.py"
)
SPEC = importlib.util.spec_from_file_location(
    "pool_assistant_measurement",
    MEASUREMENT_PATH,
)
measurement = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = measurement
SPEC.loader.exec_module(measurement)

calculate_measurement_status = measurement.calculate_measurement_status


def test_measurement_status_current_when_recent_and_synchronized() -> None:
    now = datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc)
    measured = [
        now - timedelta(hours=1),
        now - timedelta(hours=2),
        now - timedelta(hours=3),
    ]

    result = calculate_measurement_status(
        measured_at=measured,
        now=now,
        free_chlorine_measured_at=measured[0],
        total_chlorine_measured_at=measured[1],
    )

    assert result is not None
    assert result.state == "current"
    assert result.label == "Aktuell"
    assert round(result.newest_age_days, 3) == round(1 / 24, 3)
    assert result.chemistry_age_delta_hours == 2
    assert result.chlorine_pair_age_delta_hours == 1


def test_measurement_status_unsynced_when_chemistry_times_differ_too_much() -> None:
    now = datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc)
    measured = [
        now - timedelta(hours=1),
        now - timedelta(hours=2),
        now - timedelta(hours=60),
    ]

    result = calculate_measurement_status(measured_at=measured, now=now)

    assert result is not None
    assert result.state == "unsynced"
    assert result.label == "Nicht synchron"
    assert result.chemistry_age_delta_hours == 59


def test_measurement_status_unsynced_when_chlorine_pair_differs_too_much() -> None:
    now = datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc)
    free_at = now - timedelta(hours=1)
    total_at = now - timedelta(hours=14)

    result = calculate_measurement_status(
        measured_at=[free_at, total_at, now - timedelta(hours=2)],
        now=now,
        free_chlorine_measured_at=free_at,
        total_chlorine_measured_at=total_at,
    )

    assert result is not None
    assert result.state == "unsynced"
    assert result.chlorine_pair_age_delta_hours == 13


def test_measurement_status_stale_when_newest_measurement_is_old() -> None:
    now = datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc)
    measured = [
        now - timedelta(days=8),
        now - timedelta(days=9),
        now - timedelta(days=10),
    ]

    result = calculate_measurement_status(measured_at=measured, now=now)

    assert result is not None
    assert result.state == "stale"
    assert result.label == "Veraltet"


def test_measurement_status_stale_when_oldest_measurement_is_very_old() -> None:
    now = datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc)
    measured = [
        now - timedelta(hours=1),
        now - timedelta(days=31),
    ]

    result = calculate_measurement_status(measured_at=measured, now=now)

    assert result is not None
    assert result.state == "stale"


def test_measurement_status_unknown_without_measurements() -> None:
    now = datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc)

    assert calculate_measurement_status(measured_at=[], now=now) is None
