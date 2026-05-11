"""Config flow for XXMY MY302 IR RGB Control Box."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.infrared import (
    DOMAIN as INFRARED_DOMAIN,
    async_get_emitters,
)
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_INFRARED_ENTITY_ID,
    DATA_LATEST_CAPTURE,
    DOMAIN,
    OPTION_COMMAND_OVERRIDES,
    OptionMode,
)
from .profile import COMMAND_KEYS, export_command_overrides, validate_command_overrides_json


class XXMYConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the MY302 config flow."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Create the options flow."""
        return XXMYOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        emitter_entity_ids = async_get_emitters(self.hass)
        if not emitter_entity_ids:
            return self.async_abort(reason="no_emitters")

        if user_input is not None:
            entity_id = user_input[CONF_INFRARED_ENTITY_ID]
            await self.async_set_unique_id(f"xxmy_my302_{entity_id}")
            self._abort_if_unique_id_configured()

            ent_reg = er.async_get(self.hass)
            registry_entry = ent_reg.async_get(entity_id)
            entity_name = (
                registry_entry.name or registry_entry.original_name or entity_id
                if registry_entry
                else entity_id
            )
            return self.async_create_entry(
                title=f"XXMY MY302 via {entity_name}",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_INFRARED_ENTITY_ID): EntitySelector(
                        EntitySelectorConfig(
                            domain=INFRARED_DOMAIN,
                            include_entities=emitter_entity_ids,
                        )
                    )
                }
            ),
        )


class XXMYOptionsFlow(OptionsFlow):
    """Options flow for learned command overrides."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry
        self._errors: dict[str, str] = {}

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Select an options action."""
        if user_input is not None:
            mode = OptionMode(user_input["mode"])
            if mode == OptionMode.LEARN_LATEST:
                return await self.async_step_learn_latest()
            if mode == OptionMode.IMPORT_JSON:
                return await self.async_step_import_json()
            if mode == OptionMode.EXPORT_JSON:
                return await self.async_step_export_json()
            if mode == OptionMode.CLEAR_OVERRIDES:
                return self.async_create_entry(
                    title="",
                    data={**self._config_entry.options, OPTION_COMMAND_OVERRIDES: {}},
                )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("mode"): SelectSelector(
                        SelectSelectorConfig(
                            options=[mode.value for mode in OptionMode],
                            translation_key="mode",
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
            errors=self._errors,
        )

    async def async_step_learn_latest(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Store the latest ESPHome capture event for one command."""
        latest_capture = self.hass.data.get(DOMAIN, {}).get(DATA_LATEST_CAPTURE)
        if user_input is not None:
            if latest_capture is None:
                return self.async_show_form(
                    step_id="learn_latest",
                    data_schema=self._learn_schema(),
                    errors={"base": "no_capture"},
                )

            overrides = dict(self._config_entry.options.get(OPTION_COMMAND_OVERRIDES, {}))
            overrides[user_input["command_key"]] = latest_capture
            return self.async_create_entry(
                title="",
                data={**self._config_entry.options, OPTION_COMMAND_OVERRIDES: overrides},
            )

        return self.async_show_form(
            step_id="learn_latest",
            data_schema=self._learn_schema(),
            description_placeholders={
                "capture_status": "available" if latest_capture else "missing"
            },
        )

    async def async_step_import_json(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Import command overrides from JSON."""
        if user_input is not None:
            try:
                imported = validate_command_overrides_json(user_input["command_map"])
            except (TypeError, ValueError):
                return self.async_show_form(
                    step_id="import_json",
                    data_schema=self._import_schema(),
                    errors={"base": "invalid_json"},
                )

            return self.async_create_entry(
                title="",
                data={**self._config_entry.options, OPTION_COMMAND_OVERRIDES: imported},
            )

        return self.async_show_form(step_id="import_json", data_schema=self._import_schema())

    async def async_step_export_json(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show current command override JSON."""
        if user_input is not None:
            return self.async_create_entry(title="", data=dict(self._config_entry.options))

        overrides = self._config_entry.options.get(OPTION_COMMAND_OVERRIDES, {})
        return self.async_show_form(
            step_id="export_json",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "command_map",
                        default=export_command_overrides(overrides),
                    ): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.TEXT, multiline=True)
                    )
                }
            ),
        )

    def _learn_schema(self) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required("command_key"): SelectSelector(
                    SelectSelectorConfig(
                        options=[key.value for key in COMMAND_KEYS],
                        translation_key="command_key",
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )

    def _import_schema(self) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required("command_map"): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT, multiline=True)
                )
            }
        )
