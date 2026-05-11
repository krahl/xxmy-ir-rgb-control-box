"""Light platform for XXMY MY302 IR RGB Control Box."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .entity import XXMYEntity
from .profile import COLOR_COMMANDS, EFFECT_COMMANDS, CommandKey, nearest_color_command

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the MY302 light entity."""
    async_add_entities([XXMYLight(entry)])


class XXMYLight(XXMYEntity, LightEntity, RestoreEntity):
    """Assumed-state RGB light for the MY302 IR controller."""

    _attr_name = None
    _attr_assumed_state = True
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB
    _attr_supported_features = LightEntityFeature.EFFECT
    _attr_effect_list = list(EFFECT_COMMANDS)

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, unique_id_suffix="light")
        self._attr_is_on = False
        self._attr_rgb_color = COLOR_COMMANDS[CommandKey.WHITE]
        self._attr_effect = None

    async def async_added_to_hass(self) -> None:
        """Restore the last assumed light state."""
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        if last_state is None:
            return

        if (rgb_color := last_state.attributes.get(ATTR_RGB_COLOR)) is not None:
            self._attr_rgb_color = tuple(rgb_color)
        self._attr_effect = last_state.attributes.get(ATTR_EFFECT)
        self._attr_is_on = last_state.state == STATE_ON

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on or adjust the assumed light state."""
        command_key = CommandKey.ON

        if (effect := kwargs.get(ATTR_EFFECT)) in EFFECT_COMMANDS:
            command_key = EFFECT_COMMANDS[effect]
            self._attr_effect = effect
        elif (rgb_color := kwargs.get(ATTR_RGB_COLOR)) is not None:
            command_key = nearest_color_command(tuple(rgb_color))
            self._attr_rgb_color = COLOR_COMMANDS[command_key]
            self._attr_effect = None

        await self._send_key(command_key)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the assumed light."""
        await self._send_key(CommandKey.OFF)
        self._attr_is_on = False
        self.async_write_ha_state()
