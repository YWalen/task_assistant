"""Constants for the Task Assistant integration."""

from logging import Logger, getLogger
from homeassistant.helpers import selector

LOGGER: Logger = getLogger(__package__)

DOMAIN = "task_assistant"
ATTRIBUTION = "Data is provided by task_assistant"
CONFIG_VERSION = 1

ATTR_DUE_DATE = "due_date"
ATTR_LAST_COMPLETED = "last_completed"
ATTR_LAST_UPDATED = "last_updated"
ATTR_OVERDUE = "overdue"
ATTR_OVERDUE_TIME = "overdue_time"
ATTR_OVERDUE_DAYS = "overdue_days"
ATTR_START_DATE = "start_date"

BINARY_SENSOR_DEVICE_CLASS = "connectivity"
DEVICE_CLASS = "task_assistant__schedule"
SENSOR_PLATFORM = "sensor"

CONF_SENSOR = "sensor"
CONF_ENABLED = "enabled"
CONF_TYPE = "type"
CONF_FREQUENCY = "frequency"
CONF_PERIOD = "period"
CONF_ICON = "icon"
CONF_SENSORS = "sensors"
CONF_START_DATE = "start_date"
CONF_SCHEDULE = "schedule"
CONF_SCHEDULE_DAY = "schedule_day"

DEFAULT_NAME = DOMAIN
DEFAULT_TYPE = "after"
DEFAULT_FREQUENCY = "days"
DEFAULT_PERIOD = 1
DEFAULT_SCHEDULE = 1
DEFAULT_SCHEDULE_DAY = 0
DEFAULT_ICON = "mdi:calendar"
ICON = DEFAULT_ICON

TYPE_OPTIONS = [
    selector.SelectOptionDict(value="after", label="After"),
    selector.SelectOptionDict(value="every", label="Every"),
    selector.SelectOptionDict(value="scheduled", label="Scheduled"),
]

FREQUENCY_OPTIONS = [
    selector.SelectOptionDict(value="hours", label="Hours"),
    selector.SelectOptionDict(value="days", label="Days"),
    selector.SelectOptionDict(value="weeks", label="Weeks"),
    selector.SelectOptionDict(value="months", label="Months"),
    selector.SelectOptionDict(value="years", label="Years"),
]

DAY_OPTIONS = [
    selector.SelectOptionDict(value=0, label="Monday"),
    selector.SelectOptionDict(value=1, label="Tuesday"),
    selector.SelectOptionDict(value=2, label="Wednesday"),
    selector.SelectOptionDict(value=3, label="Thursday"),
    selector.SelectOptionDict(value=4, label="Friday"),
    selector.SelectOptionDict(value=5, label="Saturday"),
    selector.SelectOptionDict(value=6, label="Sunday"),
]

MONTH_OPTIONS = [
    selector.SelectOptionDict(value="jan", label="January"),
    selector.SelectOptionDict(value="feb", label="February"),
    selector.SelectOptionDict(value="mar", label="March"),
    selector.SelectOptionDict(value="apr", label="April"),
    selector.SelectOptionDict(value="may", label="May"),
    selector.SelectOptionDict(value="jun", label="June"),
    selector.SelectOptionDict(value="jul", label="July"),
    selector.SelectOptionDict(value="aug", label="August"),
    selector.SelectOptionDict(value="sep", label="September"),
    selector.SelectOptionDict(value="oct", label="October"),
    selector.SelectOptionDict(value="nov", label="November"),
    selector.SelectOptionDict(value="dec", label="December"),
]

SCHEDULE_OPTIONS = [
    selector.SelectOptionDict(value=1, label="1st"),
    selector.SelectOptionDict(value=2, label="2nd"),
    selector.SelectOptionDict(value=3, label="3rd"),
    selector.SelectOptionDict(value=4, label="4th"),
    selector.SelectOptionDict(value=5, label="5th"),
    selector.SelectOptionDict(value=-1, label="last"),
    selector.SelectOptionDict(value=-2, label="2nd from last"),
    selector.SelectOptionDict(value=-3, label="3rd from last"),
    selector.SelectOptionDict(value=-4, label="4th from last"),
]
