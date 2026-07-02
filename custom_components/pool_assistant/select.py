"""Select platform for Pool Assistant."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DEFAULT_WATER_APPEARANCE,
    DOMAIN,
    SIGNAL_APPEARANCE_UPDATED,
    WATER_APPEARANCE_OPTIONS,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pool Assistant select entities."""

    async_add_entities([PoolWaterAppearanceSelect(hass, entry)])


class PoolWaterAppearanceSelect(SelectEntity, RestoreEntity):
    """Manual visual pool water appearance select."""

    _attr_icon = "mdi:eye"
    _attr_name = "Wasseroptik"
    _attr_options = list(WATER_APPEARANCE_OPTIONS)

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the water appearance select."""

        self.hass = hass
        self.entry = entry
        config = self.entry.data | self.entry.options
        self._attr_unique_id = f"{entry.entry_id}_water_appearance"
        self._attr_current_option = DEFAULT_WATER_APPEARANCE
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=config[CONF_NAME],
            manufacturer="Pool Assistant",
            model="O'Brien/USEPA chlorine-cyanuric acid model",
        )

    async def async_added_to_hass(self) -> None:
        """Restore the previous appearance state."""

        if (last_state := await self.async_get_last_state()) is not None:
            if last_state.state in WATER_APPEARANCE_OPTIONS:
                self._attr_current_option = last_state.state
        self._store_current_option()

    async def async_select_option(self, option: str) -> None:
        """Set the selected water appearance."""

        if option not in WATER_APPEARANCE_OPTIONS:
            return
        self._attr_current_option = option
        self._store_current_option()
        self.async_write_ha_state()

    def _store_current_option(self) -> None:
        self.hass.data[DOMAIN][self.entry.entry_id]["water_appearance"] = (
            self._attr_current_option
        )
        async_dispatcher_send(
            self.hass,
            f"{SIGNAL_APPEARANCE_UPDATED}_{self.entry.entry_id}",
        )
