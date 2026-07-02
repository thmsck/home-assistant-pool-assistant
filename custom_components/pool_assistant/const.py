"""Constants for Pool Assistant."""

from __future__ import annotations

DOMAIN = "pool_assistant"

CONF_PH_ENTITY = "ph_entity"
CONF_FREE_CHLORINE_ENTITY = "free_chlorine_entity"
CONF_TOTAL_CHLORINE_ENTITY = "total_chlorine_entity"
CONF_CYA_ENTITY = "cya_entity"
CONF_ALKALINITY_ENTITY = "alkalinity_entity"
CONF_TEMPERATURE_ENTITY = "temperature_entity"
CONF_POOL_VOLUME_M3 = "pool_volume_m3"

DEFAULT_NAME = "Pool Assistant"
DEFAULT_TEMPERATURE_C = 25.0
DEFAULT_POOL_VOLUME_M3 = 16.0
DEFAULT_WATER_APPEARANCE = "Klar"
WATER_APPEARANCE_OPTIONS = (
    "Klar",
    "Leicht trüb",
    "Milchig",
    "Grünlich",
    "Grün",
    "Braun/verschmutzt",
)
SIGNAL_APPEARANCE_UPDATED = f"{DOMAIN}_appearance_updated"

ATTR_MODEL = "model"
ATTR_MODEL_TEMPERATURE_C = "model_temperature_c"
ATTR_POOL_VOLUME_M3 = "pool_volume_m3"
ATTR_WATER_APPEARANCE = "water_appearance"
ATTR_SOURCE_PH = "source_ph"
ATTR_SOURCE_FREE_CHLORINE = "source_free_chlorine"
ATTR_SOURCE_TOTAL_CHLORINE = "source_total_chlorine"
ATTR_SOURCE_CYA = "source_cya"
ATTR_SOURCE_ALKALINITY = "source_alkalinity"
ATTR_SOURCE_TEMPERATURE = "source_temperature"
