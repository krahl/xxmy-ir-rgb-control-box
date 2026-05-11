"""Common entity helpers for XXMY MY302 IR RGB Control Box."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.infrared import async_send_command
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import Event, EventStateChangedData, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_INFRARED_ENTITY_ID, DOMAIN, OPTION_COMMAND_OVERRIDES
from .profile import CommandKey, MY302_PROFILE

_LOGGER = logging.getLogger(__name__)


class XXMYEntity(Entity):
    """Base entity for the MY302 device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        unique_id_suffix: str,
        infrared_entity_id: str | None = None,
    ) -> None:
        self._entry = entry
        self._infrared_entity_id = infrared_entity_id or entry.data[CONF_INFRARED_ENTITY_ID]
        self._attr_unique_id = f"{entry.entry_id}_{unique_id_suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MY302_PROFILE.manufacturer,
            model=MY302_PROFILE.model,
        )

    @property
    def _command_overrides(self) -> dict[str, Any]:
        return self._entry.options.get(OPTION_COMMAND_OVERRIDES, {})

    async def async_added_to_hass(self) -> None:
        """Subscribe to selected infrared emitter availability."""
        await super().async_added_to_hass()

        @callback
        def _async_ir_state_changed(event: Event[EventStateChangedData]) -> None:
            new_state = event.data["new_state"]
            ir_available = new_state is not None and new_state.state != STATE_UNAVAILABLE
            if ir_available != self.available:
                _LOGGER.info(
                    "Infrared entity %s used by %s is %s",
                    self._infrared_entity_id,
                    self.entity_id,
                    "available" if ir_available else "unavailable",
                )
                self._attr_available = ir_available
                self.async_write_ha_state()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._infrared_entity_id], _async_ir_state_changed
            )
        )

        ir_state = self.hass.states.get(self._infrared_entity_id)
        self._attr_available = ir_state is not None and ir_state.state != STATE_UNAVAILABLE

    async def _send_key(self, key: CommandKey) -> None:
        """Send one IR command through the selected emitter."""
        command = MY302_PROFILE.command(key, self._command_overrides)
        await async_send_command(
            self.hass,
            self._infrared_entity_id,
            command,
            context=self._context,
        )
