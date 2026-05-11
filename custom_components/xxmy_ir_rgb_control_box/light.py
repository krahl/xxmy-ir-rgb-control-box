"""Light platform for XXMY MY302 IR RGB Control Box."""

from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
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
BRIGHTNESS_STEPS = 16
BRIGHTNESS_REPEAT_DELAY = 0.06


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
        self._attr_brightness = 255
        self._attr_effect = None

    async def async_added_to_hass(self) -> None:
        """Restore the last assumed light state."""
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        if last_state is None:
            return

        if (rgb_color := last_state.attributes.get(ATTR_RGB_COLOR)) is not None:
            self._attr_rgb_color = tuple(rgb_color)
        if (brightness := last_state.attributes.get(ATTR_BRIGHTNESS)) is not None:
            self._attr_brightness = int(brightness)
        self._attr_effect = last_state.attributes.get(ATTR_EFFECT)
        self._attr_is_on = last_state.state == STATE_ON

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on or adjust the assumed light state."""
        command_key = CommandKey.ON

        brightness = kwargs.get(ATTR_BRIGHTNESS)
        has_light_command = (
            ATTR_EFFECT in kwargs
            or ATTR_RGB_COLOR in kwargs
            or brightness is None
            or (not self._attr_is_on and int(brightness) > 0)
        )

        if (effect := kwargs.get(ATTR_EFFECT)) in EFFECT_COMMANDS:
            command_key = EFFECT_COMMANDS[effect]
            self._attr_effect = effect
        elif (rgb_color := kwargs.get(ATTR_RGB_COLOR)) is not None:
            command_key = nearest_color_command(tuple(rgb_color))
            self._attr_rgb_color = COLOR_COMMANDS[command_key]
            self._attr_effect = None

        if has_light_command:
            await self._send_key(command_key)

        if brightness is not None:
            await self._async_apply_brightness(int(brightness))

        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the assumed light."""
        await self._send_key(CommandKey.OFF)
        self._attr_is_on = False
        self.async_write_ha_state()

    async def _async_apply_brightness(self, brightness: int) -> None:
        """Translate an absolute brightness target into IR step presses."""
        brightness = max(0, min(255, brightness))
        current_step = self._brightness_to_step(self._attr_brightness or 0)
        target_step = self._brightness_to_step(brightness)
        delta = target_step - current_step

        if delta > 0:
            await self._async_send_repeated_key(CommandKey.BRIGHTER, delta)
        elif delta < 0:
            await self._async_send_repeated_key(CommandKey.DARKER, abs(delta))

        self._attr_brightness = brightness

    async def _async_send_repeated_key(self, key: CommandKey, count: int) -> None:
        """Send repeated step commands with a short gap for the IR receiver."""
        for index in range(count):
            await self._send_key(key)
            if index + 1 < count:
                await asyncio.sleep(BRIGHTNESS_REPEAT_DELAY)

    @staticmethod
    def _brightness_to_step(brightness: int) -> int:
        """Map Home Assistant brightness 0..255 to 16 physical remote steps."""
        return max(0, min(BRIGHTNESS_STEPS, (brightness * BRIGHTNESS_STEPS) // 255))
