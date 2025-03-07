"""Sensor platform for chore_helper."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import constants
from .task import Task
from .constants import LOGGER


SCAN_INTERVAL = timedelta(seconds=10)
THROTTLE_INTERVAL = timedelta(seconds=60)


async def async_setup_entry(
    _: HomeAssistant, config_entry: ConfigEntry, async_add_devices: AddEntitiesCallback
) -> None:
    """Create chore entities defined in config_flow and add them to HA."""
    async_add_devices([Task(config_entry)], True)
