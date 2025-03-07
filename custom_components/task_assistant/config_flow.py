"""Adds config flow for Task Helper."""

from __future__ import annotations

# import uuid
from collections.abc import Mapping
from typing import Any, cast

import voluptuous as vol
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaConfigFlowHandler,
    SchemaFlowError,
    SchemaFlowFormStep,
    SchemaFlowMenuStep,
    SchemaOptionsFlowHandler,
)

from . import constants, helpers


async def _validate_config(
    _: SchemaConfigFlowHandler | SchemaOptionsFlowHandler, data: Any
) -> Any:
    """Validate config."""
    return data


def required(
    key: str, options: dict[str, Any], default: Any | None = None
) -> vol.Required:
    """Return vol.Required."""
    if isinstance(options, dict) and key in options:
        suggested_value = options[key]
    elif default is not None:
        suggested_value = default
    else:
        return vol.Required(key)
    return vol.Required(key, description={"suggested_value": suggested_value})


def optional(
    key: str, options: dict[str, Any], default: Any | None = None
) -> vol.Optional:
    """Return vol.Optional."""
    if isinstance(options, dict) and key in options:
        suggested_value = options[key]
    elif default is not None:
        suggested_value = default
    else:
        return vol.Optional(key)
    return vol.Optional(key, description={"suggested_value": suggested_value})


def general_schema_definition(
    handler: SchemaConfigFlowHandler | SchemaOptionsFlowHandler,
) -> Mapping[str, Any]:
    """Create general schema."""
    schema = {
        required(
            constants.CONF_ICON, handler.options, constants.DEFAULT_ICON
        ): selector.IconSelector(),
        required(constants.CONF_AFTER_FINISHED, handler.options, constants.DEFAULT_AFTER_FINISHED,): bool,
        required(
            constants.CONF_FREQUENCY, handler.options, constants.DEFAULT_FREQUENCY
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(options=constants.FREQUENCY_OPTIONS)
        ),
        required(
            constants.CONF_PERIOD, handler.options, constants.DEFAULT_PERIOD
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=1,
                max=1000,
                mode=selector.NumberSelectorMode.BOX,
                step=1,
            )
        ),
    }

    return schema


async def general_config_schema(
    handler: SchemaConfigFlowHandler | SchemaOptionsFlowHandler,
) -> vol.Schema:
    """Generate config schema."""
    schema_obj = {required(CONF_NAME, handler.options): selector.TextSelector()}
    schema_obj.update(general_schema_definition(handler))
    return vol.Schema(schema_obj)


async def general_options_schema(
    handler: SchemaConfigFlowHandler | SchemaOptionsFlowHandler,
) -> vol.Schema:
    """Generate options schema."""
    return vol.Schema(general_schema_definition(handler))

CONFIG_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
    "user": SchemaFlowFormStep(general_config_schema)
}
OPTIONS_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
    "init": SchemaFlowFormStep(general_options_schema)
}


# mypy: ignore-errors
class TaskHelperConfigFlowHandler(SchemaConfigFlowHandler, domain=constants.DOMAIN):
    """Handle a config or options flow for Task Helper."""

    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW
    VERSION = constants.CONFIG_VERSION

    @callback
    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return config entry title.

        The options parameter contains config entry options, which is the union of user
        input from the config flow steps.
        """
        return cast(str, options["name"]) if "name" in options else ""
