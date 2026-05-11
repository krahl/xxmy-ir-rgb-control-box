"""Button platform for XXMY MY302 IR RGB Control Box."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import XXMYEntity
from .profile import COMMAND_KEYS, CommandKey

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class XXMYButtonDescription(ButtonEntityDescription):
    """Description for a MY302 button entity."""

    command_key: CommandKey


BUTTON_DESCRIPTIONS: tuple[XXMYButtonDescription, ...] = tuple(
    XXMYButtonDescription(
        key=command_key.value,
        translation_key=command_key.value,
        command_key=command_key,
    )
    for command_key in COMMAND_KEYS
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up MY302 button entities."""
    async_add_entities(XXMYButton(entry, description) for description in BUTTON_DESCRIPTIONS)


class XXMYButton(XXMYEntity, ButtonEntity):
    """One physical remote key exposed as a Home Assistant button."""

    entity_description: XXMYButtonDescription

    def __init__(self, entry: ConfigEntry, description: XXMYButtonDescription) -> None:
        super().__init__(entry, unique_id_suffix=f"button_{description.key}")
        self.entity_description = description

    async def async_press(self) -> None:
        """Press the IR remote button."""
        await self._send_key(self.entity_description.command_key)
