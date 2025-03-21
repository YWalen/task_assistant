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
        "_last_completed",
        "_overdue",
        "_overdue_days",
        "_frequency",
        "_period",
        "_type",
        "_start_date",
        "config_entry",
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
        self._frequency: str = config.get(constants.CONF_FREQUENCY)
        self._period: int = config.get(constants.CONF_PERIOD)
        self._type: str = config.get(constants.CONF_TYPE)
        self._schedule: int | None = int(config.get(constants.CONF_SCHEDULE))
        self._schedule_day: int | None = int(config.get(constants.CONF_SCHEDULE_DAY))
        self._offset: int | None = int(config.get(constants.CONF_OFFSET))
        self._attr_state = self._days
        self._start_date: datetime
        self._start_date = datetime.fromisoformat(config.get(constants.CONF_START_DATE)).replace(tzinfo=None)
        self._last_completed: datetime = self._start_date

    async def async_added_to_hass(self) -> None:
        """When sensor is added to HA, restore state and add it to calendar."""
        await super().async_added_to_hass()
        self.hass.data[constants.DOMAIN][constants.SENSOR_PLATFORM][self.entity_id] = self

        # Restore stored state
        if (state := await self.async_get_last_state()) is not None:
            self._last_updated = None  # Unblock update - after options change
            self._attr_state = state.state
            if state.attributes.get(constants.ATTR_DUE_DATE, None) is not None:
                self._due_date = datetime.fromisoformat(state.attributes.get(constants.ATTR_DUE_DATE, None)).replace(tzinfo=None)
            if state.attributes.get(constants.ATTR_LAST_COMPLETED, None) is not None:
                self._start_date = datetime.fromisoformat(state.attributes.get(constants.ATTR_LAST_COMPLETED, None)).replace(tzinfo=None)
            if state.attributes.get(constants.ATTR_START_DATE, None) is not None:
                self._due_date = datetime.fromisoformat(state.attributes.get(constants.ATTR_START_DATE, None)).replace(tzinfo=None)
            self._overdue = state.attributes.get(constants.ATTR_OVERDUE, False)
            self._overdue_days = state.attributes.get(constants.ATTR_OVERDUE_DAYS, None)

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
    def start_date(self) -> datetime | None:
        """Return start date attribute."""
        return self._start_date

    @property
    def due_date(self) -> datetime | None:
        """Return next date attribute."""
        return self._due_date

    @property
    def overdue(self) -> bool:
        """Return overdue attribute."""
        return self._overdue

    @property
    def overdue_days(self) -> int | None:
        """Return overdue_days attribute."""
        return self._overdue_days

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
    def last_completed(self) -> datetime | None:
        """Return when the task was last copmleted."""
        return self._last_completed

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
            constants.ATTR_DUE_DATE: self.due_date,
            constants.ATTR_START_DATE: self.start_date,
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

    def get_nth_weekday_of_month(self, time, year, month, weekday, nth):
        """
        Finds the date of the nth occurrence of a weekday in a specific month and year.
        """
        # Start from the first day of the month
        first_day = date(year, month, 1)
        # Calculate the first occurrence of the target weekday
        days_to_weekday = (weekday - first_day.weekday() + 7) % 7
        first_occurrence = first_day + timedelta(days=days_to_weekday)
        # Calculate the nth occurrence
        nth_occurrence = first_occurrence + timedelta(weeks=nth - 1)

        # Check if the nth occurrence is still in the same month
        if nth_occurrence.month != month:
            return None  # That nth weekday does not exist in this month
        return datetime.combine(nth_occurrence, time)

    def get_next_due_date(self) -> datetime | None:
        """Get next date from self._due_dates."""
        due_date = helpers.now()
        if self._type == "after":
            due_date = self._add_period_offset(self._last_completed, self._frequency, self._period)
        elif self._type == "every":
            while self._last_completed > self._start_date:
                self._start_date = self._add_period_offset(self._start_date, self._frequency, self._period)
            due_date = self._add_period_offset(self._start_date, self._frequency, self._period)
        elif self._type == "scheduled":
            task_time = self._start_date.time()
            year = self._last_completed.year
            month = self._last_completed.month
            due_date = self.get_nth_weekday_of_month(task_time, year, month, self._schedule_day, self._schedule)
            while due_date and due_date <= helpers.now():
                # If due date has passed or doesn't exist, move to next month
                year = year + (1 if month == 12 else 0)
                month = 1 if month == 12 else month + 1
                due_date = self.get_nth_weekday_of_month(task_time, year, month, self._schedule_day, self._schedule)
        due_date = self._add_period_offset(due_date, "days", self._offset)
        return due_date

    def complete_task(self):
        self._last_completed = helpers.now()

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
            overdue_time = self._due_date - self._last_updated
            self._days = overdue_time.days
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

    def _add_period_offset(self, start_date: datetime, frequency: str, period: int) -> datetime:
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
