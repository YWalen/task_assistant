"""Custom integration to manage household chores with Home Assistant.

For more details about this integration, please refer to
https://github.com/bmcclure/ha-chore-helper
"""

from __future__ import annotations

from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_ENTITY_ID,
)
from homeassistant.core import HomeAssistant, ServiceCall
import voluptuous as vol

from . import constants, helpers
from .constants import LOGGER

PLATFORMS: list[str] = [constants.SENSOR_PLATFORM]

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)

frequencies = [f["value"] for f in constants.FREQUENCY_OPTIONS]

SENSOR_SCHEMA = vol.Schema(
    {
        vol.Required(constants.CONF_ICON): cv.icon,
        vol.Required(constants.CONF_FREQUENCY): vol.In(frequencies),
        vol.Required(constants.CONF_PERIOD): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=1000)
        ),
        vol.Required(constants.CONF_AFTER_FINISHED): cv.boolean,
    },
    extra=vol.ALLOW_EXTRA,
)

CONFIG_SCHEMA = vol.Schema(
    {
        constants.DOMAIN: vol.Schema(
            {vol.Optional(constants.CONF_SENSORS): vol.All(cv.ensure_list, [SENSOR_SCHEMA])}
        )
    },
    extra=vol.ALLOW_EXTRA,
)

COMPLETE_NOW_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ENTITY_ID): cv.string,
    }
)

UPDATE_STATE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ENTITY_ID): cv.string,
    }
)


# pylint: disable=unused-argument
async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up platform - register services, initialize data structure."""

    async def handle_update_state(call: ServiceCall) -> None:
        """Handle the update_state service call."""
        entity_id = call.data.get(CONF_ENTITY_ID, "")
        LOGGER.debug("called update_state for %s", entity_id)
        try:
            entity = hass.data[constants.DOMAIN][constants.SENSOR_PLATFORM][entity_id]
            entity.update_state()
        except KeyError as err:
            LOGGER.error("Failed updating state for %s - %s", entity_id, err)

    async def handle_complete_task(call: ServiceCall) -> None:
        """Handle the complete_chore service call."""
        entity_id = call.data.get(CONF_ENTITY_ID, "")
        LOGGER.debug("called complete for %s", entity_id)
        try:
            entity = hass.data[constants.DOMAIN][constants.SENSOR_PLATFORM][entity_id]
            entity.last_completed = dt_util.as_local(helpers.now())
            entity.update_state()
        except KeyError as err:
            LOGGER.error(
                "Failed setting last completed for %s - %s", entity_id, err
            )

    hass.data.setdefault(constants.DOMAIN, {})
    hass.data[constants.DOMAIN].setdefault(constants.SENSOR_PLATFORM, {})
    hass.services.async_register(
        constants.DOMAIN,
        "update_state",
        handle_update_state,
        schema=UPDATE_STATE_SCHEMA,
    )
    hass.services.async_register(
        constants.DOMAIN,
        "complete",
        handle_complete_task,
        schema=COMPLETE_NOW_SCHEMA,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    LOGGER.debug(
        "Setting %s (%s) from ConfigFlow",
        config_entry.title,
        config_entry.options[constants.CONF_FREQUENCY],
    )
    config_entry.add_update_listener(update_listener)

    # Add sensor
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True


async def async_remove_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle removal of an entry."""
    try:
        await hass.config_entries.async_forward_entry_unload(
            config_entry, constants.SENSOR_PLATFORM
        )
        LOGGER.info("Successfully removed sensor from the chore_helper integration")
    except ValueError:
        pass

async def async_reload_entry(hass, entry):
    """Reload the integration without restarting Home Assistant."""
    await async_unload_entry(hass, entry)
    return await async_setup_entry(hass, entry)

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener - to re-create device after options update."""
    await hass.config_entries.async_forward_entry_unload(entry, constants.SENSOR_PLATFORM)
    hass.async_add_job(
        hass.config_entries.async_forward_entry_setup(entry, constants.SENSOR_PLATFORM)
    )
