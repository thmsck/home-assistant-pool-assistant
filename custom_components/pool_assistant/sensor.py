"""Sensor platform for Pool Assistant."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, PERCENTAGE
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.template import TemplateError
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt as dt_util

from .chemistry import PoolChemistryResult, calculate_pool_chemistry
from .const import (
    ATTR_MODEL,
    ATTR_MODEL_TEMPERATURE_C,
    ATTR_POOL_VOLUME_M3,
    ATTR_SOURCE_ALKALINITY,
    ATTR_SOURCE_CYA,
    ATTR_SOURCE_FREE_CHLORINE,
    ATTR_SOURCE_PH,
    ATTR_SOURCE_TEMPERATURE,
    ATTR_SOURCE_TOTAL_CHLORINE,
    CONF_ALKALINITY_ENTITY,
    CONF_CYA_ENTITY,
    CONF_FREE_CHLORINE_ENTITY,
    CONF_PH_ENTITY,
    CONF_POOL_VOLUME_M3,
    CONF_TEMPERATURE_ENTITY,
    CONF_TOTAL_CHLORINE_ENTITY,
    DEFAULT_POOL_VOLUME_M3,
    DEFAULT_TEMPERATURE_C,
    DOMAIN,
)

UNIT_MG_L = "mg/l"
HOCL_RED_THRESHOLD_MG_L = 0.016
HOCL_GREEN_THRESHOLD_MG_L = 0.05
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


@dataclass(frozen=True)
class PoolAssistantResult:
    """Calculated Pool Assistant values and source metadata."""

    chemistry: PoolChemistryResult
    bound_chlorine_mg_l: float | None
    bound_chlorine_raw_delta_mg_l: float | None
    chlorine_plausible: bool | None
    measurement_status: MeasurementStatus | None


@dataclass(frozen=True, kw_only=True)
class PoolAssistantSensorDescription(SensorEntityDescription):
    """Description of a Pool Assistant sensor."""

    value_fn: Callable[[PoolAssistantResult], StateType]
    attributes_fn: Callable[[PoolAssistantResult], dict[str, Any]] | None = None


SENSORS: tuple[PoolAssistantSensorDescription, ...] = (
    PoolAssistantSensorDescription(
        key="hocl",
        name="Aktives Chlor HOCl",
        native_unit_of_measurement=UNIT_MG_L,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
        icon="mdi:molecule",
        value_fn=lambda result: round(result.chemistry.hocl_mg_l, 4),
    ),
    PoolAssistantSensorDescription(
        key="ocl",
        name="Hypochlorit OCl",
        native_unit_of_measurement=UNIT_MG_L,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
        icon="mdi:molecule",
        value_fn=lambda result: round(result.chemistry.ocl_mg_l, 4),
    ),
    PoolAssistantSensorDescription(
        key="bound_chlorine",
        name="Gebundenes Chlor",
        native_unit_of_measurement=UNIT_MG_L,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:molecule",
        value_fn=lambda result: (
            round(result.bound_chlorine_mg_l, 2)
            if result.bound_chlorine_mg_l is not None
            else None
        ),
        attributes_fn=lambda result: _bound_chlorine_attributes(result),
    ),
    PoolAssistantSensorDescription(
        key="unbound_chlorine_percent",
        name="Ungebundenes Chlor",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:percent",
        value_fn=lambda result: round(result.chemistry.unbound_chlorine_percent, 2),
    ),
    PoolAssistantSensorDescription(
        key="cya_bound_chlorine_percent",
        name="An CYA gebundenes Chlor",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:percent",
        value_fn=lambda result: round(result.chemistry.cya_bound_chlorine_percent, 2),
    ),
    PoolAssistantSensorDescription(
        key="chlorine_speciation",
        name="Chlor-Spezies",
        icon="mdi:chart-donut",
        value_fn=lambda result: "calculated",
        attributes_fn=lambda result: {
            f"{name}_percent": round(value, 4)
            for name, value in result.chemistry.species_percent.items()
        },
    ),
    PoolAssistantSensorDescription(
        key="disinfection_status",
        name="Desinfektionsstatus",
        icon="mdi:shield-check",
        value_fn=lambda result: _disinfection_status(result.chemistry.hocl_mg_l),
        attributes_fn=lambda result: _disinfection_attributes(result.chemistry.hocl_mg_l),
    ),
    PoolAssistantSensorDescription(
        key="measurement_age",
        name="Messalter",
        native_unit_of_measurement="d",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:calendar-clock",
        value_fn=lambda result: (
            round(result.measurement_status.newest_age_days, 1)
            if result.measurement_status is not None
            else None
        ),
        attributes_fn=lambda result: _measurement_age_attributes(result),
    ),
    PoolAssistantSensorDescription(
        key="measurement_status",
        name="Messstatus",
        icon="mdi:clipboard-pulse",
        value_fn=lambda result: (
            result.measurement_status.state
            if result.measurement_status is not None
            else "unknown"
        ),
        attributes_fn=lambda result: _measurement_status_attributes(result),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pool Assistant sensors."""

    async_add_entities(
        [PoolAssistantSensor(hass, entry, description) for description in SENSORS]
    )


class PoolAssistantSensor(SensorEntity):
    """Pool Assistant calculated sensor."""

    entity_description: PoolAssistantSensorDescription
    _attr_should_poll = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        description: PoolAssistantSensorDescription,
    ) -> None:
        """Initialize a Pool Assistant sensor."""

        self.hass = hass
        self.entry = entry
        self.entity_description = description
        config = self.entry.data | self.entry.options
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=config[CONF_NAME],
            manufacturer="Pool Assistant",
            model="O'Brien/USEPA chlorine-cyanuric acid model",
        )
        self._attr_available = False
        self._attr_native_value: StateType = None
        self._attr_extra_state_attributes: dict[str, Any] = {}

    async def async_added_to_hass(self) -> None:
        """Register state listeners."""

        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                self._source_entities,
                self._async_source_changed,
            )
        )
        self._update_value()

    @property
    def _config(self) -> dict[str, Any]:
        return self.entry.data | self.entry.options

    @property
    def _source_entities(self) -> list[str]:
        config = self._config
        entities = [
            config[CONF_PH_ENTITY],
            config[CONF_FREE_CHLORINE_ENTITY],
            config[CONF_CYA_ENTITY],
        ]
        total_chlorine_entity = config.get(CONF_TOTAL_CHLORINE_ENTITY)
        if total_chlorine_entity:
            entities.append(total_chlorine_entity)
        alkalinity_entity = config.get(CONF_ALKALINITY_ENTITY)
        if alkalinity_entity:
            entities.append(alkalinity_entity)
        temperature_entity = config.get(CONF_TEMPERATURE_ENTITY)
        if temperature_entity:
            entities.append(temperature_entity)
        return entities

    @callback
    def _async_source_changed(self, event: Event) -> None:
        self._update_value()
        self.async_write_ha_state()

    @callback
    def _update_value(self) -> None:
        result = self._calculate()
        if result is None:
            self._attr_available = False
            self._attr_native_value = None
            self._attr_extra_state_attributes = {}
            return

        self._attr_available = True
        self._attr_native_value = self.entity_description.value_fn(result)
        config = self._config
        chemistry = result.chemistry
        attributes = {
            ATTR_MODEL: chemistry.model,
            ATTR_MODEL_TEMPERATURE_C: chemistry.temperature_c,
            ATTR_POOL_VOLUME_M3: config.get(
                CONF_POOL_VOLUME_M3,
                DEFAULT_POOL_VOLUME_M3,
            ),
            ATTR_SOURCE_PH: config[CONF_PH_ENTITY],
            ATTR_SOURCE_FREE_CHLORINE: config[CONF_FREE_CHLORINE_ENTITY],
            ATTR_SOURCE_CYA: config[CONF_CYA_ENTITY],
        }
        if config.get(CONF_TOTAL_CHLORINE_ENTITY):
            attributes[ATTR_SOURCE_TOTAL_CHLORINE] = config[CONF_TOTAL_CHLORINE_ENTITY]
        if config.get(CONF_ALKALINITY_ENTITY):
            attributes[ATTR_SOURCE_ALKALINITY] = config[CONF_ALKALINITY_ENTITY]
        if config.get(CONF_TEMPERATURE_ENTITY):
            attributes[ATTR_SOURCE_TEMPERATURE] = config[CONF_TEMPERATURE_ENTITY]
        if self.entity_description.attributes_fn is not None:
            attributes.update(self.entity_description.attributes_fn(result))
        self._attr_extra_state_attributes = attributes

    def _calculate(self) -> PoolAssistantResult | None:
        try:
            config = self._config
            ph = _state_float(self.hass, config[CONF_PH_ENTITY])
            free_chlorine = _state_float(self.hass, config[CONF_FREE_CHLORINE_ENTITY])
            cya = _state_float(self.hass, config[CONF_CYA_ENTITY])
            temperature_entity = config.get(CONF_TEMPERATURE_ENTITY)
            temperature = (
                _state_float(self.hass, temperature_entity)
                if temperature_entity
                else DEFAULT_TEMPERATURE_C
            )
            chemistry = calculate_pool_chemistry(
                ph=ph,
                free_chlorine_mg_l=free_chlorine,
                cya_mg_l=cya,
                temperature_c=temperature,
            )
            bound_chlorine = None
            raw_delta = None
            chlorine_plausible = None
            total_chlorine_entity = config.get(CONF_TOTAL_CHLORINE_ENTITY)
            if total_chlorine_entity:
                total_chlorine = _state_float(self.hass, total_chlorine_entity)
                raw_delta = total_chlorine - free_chlorine
                bound_chlorine = max(raw_delta, 0.0)
                chlorine_plausible = total_chlorine + 0.05 >= free_chlorine

            return PoolAssistantResult(
                chemistry=chemistry,
                bound_chlorine_mg_l=bound_chlorine,
                bound_chlorine_raw_delta_mg_l=raw_delta,
                chlorine_plausible=chlorine_plausible,
                measurement_status=_measurement_status(self.hass, config),
            )
        except (TypeError, ValueError):
            return None


def _state_float(hass: HomeAssistant, entity_id: str) -> float:
    state = hass.states.get(entity_id)
    if state is None or state.state in {"unknown", "unavailable", ""}:
        raise ValueError(f"Source entity {entity_id} has no usable state")
    return float(state.state)


def _measurement_status(
    hass: HomeAssistant,
    config: dict[str, Any],
) -> MeasurementStatus | None:
    source_entities = [
        config[CONF_PH_ENTITY],
        config[CONF_FREE_CHLORINE_ENTITY],
        config[CONF_CYA_ENTITY],
    ]
    for optional_key in (
        CONF_TOTAL_CHLORINE_ENTITY,
        CONF_ALKALINITY_ENTITY,
    ):
        entity_id = config.get(optional_key)
        if entity_id:
            source_entities.append(entity_id)

    measured_at = [_measured_at(hass, entity_id) for entity_id in source_entities]
    if any(value is None for value in measured_at):
        return None

    now = dt_util.utcnow()
    timestamps = [value.timestamp() for value in measured_at if value is not None]
    newest = max(timestamps)
    oldest = min(timestamps)
    newest_age_days = (now.timestamp() - newest) / SECONDS_PER_DAY
    oldest_age_days = (now.timestamp() - oldest) / SECONDS_PER_DAY
    chemistry_age_delta_hours = (newest - oldest) / 3600

    chlorine_pair_delta_hours = None
    total_chlorine_entity = config.get(CONF_TOTAL_CHLORINE_ENTITY)
    if total_chlorine_entity:
        free_at = _measured_at(hass, config[CONF_FREE_CHLORINE_ENTITY])
        total_at = _measured_at(hass, total_chlorine_entity)
        if free_at is not None and total_at is not None:
            chlorine_pair_delta_hours = (
                abs(free_at.timestamp() - total_at.timestamp()) / 3600
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


def _measured_at(hass: HomeAssistant, entity_id: str) -> datetime | None:
    state = hass.states.get(entity_id)
    if state is None:
        return None
    value = state.attributes.get("measured_at")
    if value is None:
        return state.last_updated
    try:
        parsed = dt_util.parse_datetime(value)
    except (TypeError, ValueError, TemplateError):
        return None
    if parsed is None:
        return None
    return dt_util.as_utc(parsed)


def _bound_chlorine_attributes(result: PoolAssistantResult) -> dict[str, Any]:
    attributes: dict[str, Any] = {}
    if result.bound_chlorine_raw_delta_mg_l is not None:
        attributes["raw_delta"] = round(result.bound_chlorine_raw_delta_mg_l, 2)
    if result.chlorine_plausible is not None:
        attributes["plausible"] = result.chlorine_plausible
    return attributes


def _measurement_age_attributes(result: PoolAssistantResult) -> dict[str, Any]:
    if result.measurement_status is None:
        return {}
    status = result.measurement_status
    attributes: dict[str, Any] = {
        "oldest_age_days": round(status.oldest_age_days, 1),
        "chemistry_age_delta_hours": round(status.chemistry_age_delta_hours, 1),
    }
    if status.chlorine_pair_age_delta_hours is not None:
        attributes["chlorine_pair_age_delta_hours"] = round(
            status.chlorine_pair_age_delta_hours,
            1,
        )
    return attributes


def _measurement_status_attributes(result: PoolAssistantResult) -> dict[str, Any]:
    if result.measurement_status is None:
        return {"label": "Unbekannt"}
    return {"label": result.measurement_status.label}


def _disinfection_status(hocl_mg_l: float) -> str:
    if hocl_mg_l < HOCL_RED_THRESHOLD_MG_L:
        return "critical"
    if hocl_mg_l < HOCL_GREEN_THRESHOLD_MG_L:
        return "limited"
    return "effective"


def _disinfection_attributes(hocl_mg_l: float) -> dict[str, Any]:
    if hocl_mg_l < HOCL_RED_THRESHOLD_MG_L:
        color = "red"
        label = "Desinfektionsleistung zu gering"
    elif hocl_mg_l < HOCL_GREEN_THRESHOLD_MG_L:
        color = "yellow"
        label = "Tötet einige Algen und Bakterien"
    else:
        color = "green"
        label = "Tötet Algen und Bakterien"

    return {
        "hocl_mg_l": round(hocl_mg_l, 4),
        "color": color,
        "label": label,
        "red_below_mg_l": HOCL_RED_THRESHOLD_MG_L,
        "yellow_from_mg_l": HOCL_RED_THRESHOLD_MG_L,
        "green_from_mg_l": HOCL_GREEN_THRESHOLD_MG_L,
    }
