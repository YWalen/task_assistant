"""An entity for a single task."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any
from dateutil.relativedelta import relativedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_NAME,
)
from homeassistant.helpers.restore_state import RestoreEntity

from . import constants, helpers
from .constants import LOGGER


class Task(RestoreEntity):
    """Task Sensor class."""

    __slots__ = (
        "_attr_icon",
        "_attr_name",
        "_attr_state",
        "_due_date",
        "_last_updated",
        "_overdue",
        "_overdue_days",
        "_overdue_time",
        "_frequency",
        "_period",
        "_after_finished",
        "_start_date",
        "config_entry",
        "last_completed",
    )

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Read configuration and initialise class variables."""
        self._days: int | None = None
        self._due_date: datetime | None = None
        config = config_entry.options
        self.config_entry = config_entry
        self._attr_name = (
            config_entry.title
            if config_entry.title is not None
            else config.get(CONF_NAME)
        )
        self._attr_icon = config.get(constants.CONF_ICON)
        self._last_updated: datetime | None = None
        self._overdue: bool = False
        self._overdue_days: int | None = None
        self._overdue_time: datetime | None = None
        self._frequency: str = config.get(constants.CONF_FREQUENCY)
        self._period: int = config.get(constants.CONF_PERIOD)
        self._after_finished: bool = config.get(constants.CONF_AFTER_FINISHED)
        self._attr_state = self._days
        self._start_date: date
        try:
            self._start_date = helpers.to_date(config.get(constants.CONF_START_DATE))
        except ValueError:
            self._start_date = helpers.now()
        self.last_completed: datetime = self._start_date

    async def async_added_to_hass(self) -> None:
        """When sensor is added to HA, restore state and add it to calendar."""
        await super().async_added_to_hass()
        self.hass.data[constants.DOMAIN][constants.SENSOR_PLATFORM][self.entity_id] = self

        # Restore stored state
        if (state := await self.async_get_last_state()) is not None:
            self._last_updated = None  # Unblock update - after options change
            self._attr_state = state.state
            next_due_date = (
                helpers.parse_datetime(state.attributes[constants.ATTR_DUE_DATE])
                if constants.ATTR_DUE_DATE in state.attributes
                else None
            )
            self._due_date = (
                None if next_due_date is None else next_due_date
            )
            self.last_completed = (
                helpers.parse_datetime(state.attributes[constants.ATTR_LAST_COMPLETED])
                if constants.ATTR_LAST_COMPLETED in state.attributes
                else None
            )
            self._overdue = state.attributes.get(constants.ATTR_OVERDUE, False)
            self._overdue_days = state.attributes.get(constants.ATTR_OVERDUE_DAYS, None)
            self._overdue_time = state.attributes.get(constants.ATTR_OVERDUE_TIME, None)

    async def async_will_remove_from_hass(self) -> None:
        """When sensor is removed from HA, remove it and its calendar entity."""
        await super().async_will_remove_from_hass()
        del self.hass.data[constants.DOMAIN][constants.SENSOR_PLATFORM][self.entity_id]

    @property
    def unique_id(self) -> str:
        """Return a unique ID to use for this sensor."""
        if "unique_id" in self.config_entry.data:  # From legacy config
            return self.config_entry.data["unique_id"]
        return self.config_entry.entry_id

    @property
    def name(self) -> str | None:
        """Return the name of the sensor."""
        return self._attr_name

    @property
    def next_due_date(self) -> date | None:
        """Return next date attribute."""
        return self._next_due_date

    @property
    def overdue(self) -> bool:
        """Return overdue attribute."""
        return self._overdue

    @property
    def overdue_days(self) -> int | None:
        """Return overdue_days attribute."""
        return self._overdue_days

    @property
    def overdue_time(self) -> int | None:
        """Return overdue_times attribute."""
        return self._overdue_time

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return unit of measurement - None for numerical value."""
        return "day" if self._days == 1 else "days"

    @property
    def native_value(self) -> object:
        """Return the state of the sensor."""
        return self._attr_state

    @property
    def last_updated(self) -> datetime | None:
        """Return when the sensor was last updated."""
        return self._last_updated

    @property
    def icon(self) -> str:
        """Return the entity icon."""
        return self._attr_icon

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            constants.ATTR_LAST_COMPLETED: self.last_completed,
            constants.ATTR_LAST_UPDATED: self.last_updated,
            constants.ATTR_OVERDUE: self.overdue,
            constants.ATTR_OVERDUE_DAYS: self.overdue_days,
            constants.ATTR_OVERDUE_TIME: self.overdue_times,
            ATTR_UNIT_OF_MEASUREMENT: self.native_unit_of_measurement,
            # Needed for translations to work
            ATTR_DEVICE_CLASS: self.DEVICE_CLASS,
        }

    @property
    def DEVICE_CLASS(self) -> str:  # pylint: disable=C0103
        """Return the class of the sensor."""
        return constants.DEVICE_CLASS

    def __repr__(self) -> str:
        """Return main sensor parameters."""
        return (
            f"{self.__class__.__name__}(name={self._attr_name}, "
            f"entity_id={self.entity_id}, "
            f"state={self.state}, "
            f"attributes={self.extra_state_attributes})"
        )

    def get_next_due_date(self) -> datetime | None:
        """Get next date from self._due_dates."""
        next_due_date = self._add_period_offset(self._last_updated, self._frequency, self._period)
        if not self._after_finished:
            while next_due_date < self.last_completed:
                self._start_date = next_due_date
                next_due_date = self._add_period_offset(self._last_updated, self._frequency, self._period)
        return next_due_date

    async def async_update(self) -> None:
        """Get the latest data and updates the states."""
        if not self.hass.is_running:
            return

        LOGGER.debug("(%s) Calling update", self._attr_name)
        LOGGER.debug(
            "(%s) Dates loaded, firing a task_helper_loaded event",
            self._attr_name,
        )
        event_data = {
            "entity_id": self.entity_id,
        }
        self.hass.bus.async_fire("task_helper_loaded", event_data)
        self.update_state()

    def update_state(self) -> None:
        """Pick the first event from task dates, update attributes."""
        LOGGER.debug("(%s) Looking for next task date", self._attr_name)
        self._last_updated = helpers.now()
        self._due_date = self.get_next_due_date()
        if self._due_date is not None:
            LOGGER.debug(
                "(%s) next_due_date (%s), today (%s)",
                self._attr_name,
                self._due_date,
                self._last_updated,
            )
            self._overdue_time = self._due_date - self._last_updated
            self._days = self._overdue_time.days
            LOGGER.debug(
                "(%s) Found next task date: %s, that is in %d days",
                self._attr_name,
                self._due_date,
                self._days,
            )
            self._attr_state = self._days
            self._overdue = self._days < 0
            self._overdue_days = 0 if self._days > -1 else abs(self._days)
        else:
            self._days = None
            self._attr_state = None
            self._overdue = False
            self._overdue_days = None
            self._overdue_time = None

    def _add_period_offset(self, start_date: datetime, frequency: str, period: int) -> date:
        if frequency == "hours":
            return start_date + timedelta(hours=period)
        elif frequency == "days":
            return start_date + timedelta(days=period)
        elif frequency == "weeks":
            return start_date + timedelta(weeks=period)
        elif frequency == "months":
            return start_date + relativedelta(months=period)
        elif frequency == "years":
            return start_date + relativedelta(years=period)
        else:
            raise ValueError("Invalid unit. Use 'hours', 'days', 'weeks', 'months' or 'years'.")
