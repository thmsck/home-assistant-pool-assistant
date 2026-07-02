"""Measurement freshness and synchronization logic for Pool Assistant."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

SECONDS_PER_DAY = 86400


@dataclass(frozen=True)
class MeasurementStatus:
    """Source measurement age and synchronization status."""

    state: str
    label: str
    newest_age_days: float
    oldest_age_days: float
    chlorine_pair_age_delta_hours: float | None
    chemistry_age_delta_hours: float


def calculate_measurement_status(
    *,
    measured_at: list[datetime],
    now: datetime,
    free_chlorine_measured_at: datetime | None = None,
    total_chlorine_measured_at: datetime | None = None,
) -> MeasurementStatus | None:
    """Calculate measurement freshness and synchronization status."""

    if not measured_at:
        return None

    timestamps = [value.timestamp() for value in measured_at]
    newest = max(timestamps)
    oldest = min(timestamps)
    newest_age_days = (now.timestamp() - newest) / SECONDS_PER_DAY
    oldest_age_days = (now.timestamp() - oldest) / SECONDS_PER_DAY
    chemistry_age_delta_hours = (newest - oldest) / 3600

    chlorine_pair_delta_hours = None
    if free_chlorine_measured_at is not None and total_chlorine_measured_at is not None:
        chlorine_pair_delta_hours = (
            abs(
                free_chlorine_measured_at.timestamp()
                - total_chlorine_measured_at.timestamp()
            )
            / 3600
        )

    if newest_age_days > 7 or oldest_age_days > 30:
        state = "stale"
        label = "Veraltet"
    elif (
        chemistry_age_delta_hours > 48
        or (
            chlorine_pair_delta_hours is not None
            and chlorine_pair_delta_hours > 12
        )
    ):
        state = "unsynced"
        label = "Nicht synchron"
    else:
        state = "current"
        label = "Aktuell"

    return MeasurementStatus(
        state=state,
        label=label,
        newest_age_days=newest_age_days,
        oldest_age_days=oldest_age_days,
        chlorine_pair_age_delta_hours=chlorine_pair_delta_hours,
        chemistry_age_delta_hours=chemistry_age_delta_hours,
    )
