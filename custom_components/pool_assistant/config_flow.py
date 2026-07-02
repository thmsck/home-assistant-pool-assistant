"""Config flow for Pool Assistant."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig

from .const import (
    CONF_ALKALINITY_ENTITY,
    CONF_CYA_ENTITY,
    CONF_FREE_CHLORINE_ENTITY,
    CONF_PH_ENTITY,
    CONF_POOL_VOLUME_M3,
    CONF_TEMPERATURE_ENTITY,
    CONF_TOTAL_CHLORINE_ENTITY,
    DEFAULT_NAME,
    DEFAULT_POOL_VOLUME_M3,
    DOMAIN,
)


class PoolAssistantConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pool Assistant."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""

        if user_input is not None:
            title = user_input[CONF_NAME]
            return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(include_volume_default=False),
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> PoolAssistantOptionsFlow:
        """Create the options flow."""

        return PoolAssistantOptionsFlow()


class PoolAssistantOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Pool Assistant."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Manage Pool Assistant options."""

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_schema(self.config_entry.data | self.config_entry.options),
        )


def _schema(
    defaults: dict[str, Any] | None = None,
    *,
    include_volume_default: bool = True,
) -> vol.Schema:
    defaults = defaults or {}
    sensor_selector = EntitySelector(EntitySelectorConfig(domain="sensor"))
    volume_field = (
        vol.Required(
            CONF_POOL_VOLUME_M3,
            default=defaults.get(CONF_POOL_VOLUME_M3, DEFAULT_POOL_VOLUME_M3),
        )
        if include_volume_default
        else vol.Required(CONF_POOL_VOLUME_M3)
    )
    fields: dict[Any, Any] = {
        vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
        volume_field: vol.All(vol.Coerce(float), vol.Range(min=1.0, max=100.0)),
        vol.Required(CONF_PH_ENTITY, default=defaults.get(CONF_PH_ENTITY)): sensor_selector,
        vol.Required(
            CONF_FREE_CHLORINE_ENTITY,
            default=defaults.get(CONF_FREE_CHLORINE_ENTITY),
        ): sensor_selector,
        vol.Required(
            CONF_TOTAL_CHLORINE_ENTITY,
            default=defaults.get(CONF_TOTAL_CHLORINE_ENTITY),
        ): sensor_selector,
        vol.Required(CONF_CYA_ENTITY, default=defaults.get(CONF_CYA_ENTITY)): sensor_selector,
        vol.Required(
            CONF_ALKALINITY_ENTITY,
            default=defaults.get(CONF_ALKALINITY_ENTITY),
        ): sensor_selector,
    }
    if CONF_TEMPERATURE_ENTITY in defaults:
        fields[
            vol.Optional(
                CONF_TEMPERATURE_ENTITY,
                default=defaults[CONF_TEMPERATURE_ENTITY],
            )
        ] = sensor_selector
    else:
        fields[vol.Optional(CONF_TEMPERATURE_ENTITY)] = sensor_selector
    return vol.Schema(fields)
