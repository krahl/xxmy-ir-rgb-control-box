"""Reusable IR command profile model and the default MY302 profile."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import json
from typing import Any

from .const import DEFAULT_MODULATION
from .raw_command import RawInfraredCommand, encode_nec_extended


class CommandKey(StrEnum):
    """Semantic command keys for a 24-key RGB controller remote."""

    BRIGHTER = "brighter"
    DARKER = "darker"
    OFF = "off"
    ON = "on"
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    WHITE = "white"
    RED_ORANGE = "red_orange"
    GREEN_LIGHT = "green_light"
    BLUE_DARK = "blue_dark"
    FLASH = "flash"
    RED_AMBER = "red_amber"
    GREEN_CYAN = "green_cyan"
    BLUE_ROYAL = "blue_royal"
    STROBE = "strobe"
    RED_YELLOW = "red_yellow"
    GREEN_SKY = "green_sky"
    BLUE_PINK = "blue_pink"
    FADE = "fade"
    RED_PALE_YELLOW = "red_pale_yellow"
    GREEN_AQUA = "green_aqua"
    BLUE_PURPLE = "blue_purple"
    SMOOTH = "smooth"


COMMAND_KEYS: tuple[CommandKey, ...] = tuple(CommandKey)

COMMAND_ROWS: tuple[tuple[CommandKey, ...], ...] = (
    (CommandKey.BRIGHTER, CommandKey.DARKER, CommandKey.OFF, CommandKey.ON),
    (CommandKey.RED, CommandKey.GREEN, CommandKey.BLUE, CommandKey.WHITE),
    (CommandKey.RED_ORANGE, CommandKey.GREEN_LIGHT, CommandKey.BLUE_DARK, CommandKey.FLASH),
    (CommandKey.RED_AMBER, CommandKey.GREEN_CYAN, CommandKey.BLUE_ROYAL, CommandKey.STROBE),
    (CommandKey.RED_YELLOW, CommandKey.GREEN_SKY, CommandKey.BLUE_PINK, CommandKey.FADE),
    (CommandKey.RED_PALE_YELLOW, CommandKey.GREEN_AQUA, CommandKey.BLUE_PURPLE, CommandKey.SMOOTH),
)

COMMAND_NEC_IDS: dict[CommandKey, int] = {
    command: index for index, command in enumerate(key for row in COMMAND_ROWS for key in row)
}

COLOR_COMMANDS: dict[CommandKey, tuple[int, int, int]] = {
    CommandKey.RED: (255, 0, 0),
    CommandKey.GREEN: (0, 255, 0),
    CommandKey.BLUE: (0, 0, 255),
    CommandKey.WHITE: (255, 255, 255),
    CommandKey.RED_ORANGE: (255, 80, 0),
    CommandKey.RED_AMBER: (255, 150, 0),
    CommandKey.RED_YELLOW: (255, 255, 0),
    CommandKey.RED_PALE_YELLOW: (255, 255, 128),
    CommandKey.GREEN_LIGHT: (128, 255, 0),
    CommandKey.GREEN_CYAN: (0, 255, 255),
    CommandKey.GREEN_SKY: (0, 160, 255),
    CommandKey.GREEN_AQUA: (0, 255, 128),
    CommandKey.BLUE_DARK: (0, 0, 128),
    CommandKey.BLUE_ROYAL: (65, 105, 225),
    CommandKey.BLUE_PINK: (255, 105, 180),
    CommandKey.BLUE_PURPLE: (128, 0, 255),
}

EFFECT_COMMANDS: dict[str, CommandKey] = {
    "flash": CommandKey.FLASH,
    "strobe": CommandKey.STROBE,
    "fade": CommandKey.FADE,
    "smooth": CommandKey.SMOOTH,
}


@dataclass(frozen=True)
class CommandProfile:
    """IR command profile for a remote-controlled device."""

    key: str
    name: str
    manufacturer: str
    model: str
    modulation: int
    nec_address: int
    raw_commands: dict[CommandKey, tuple[int, ...]]

    def command(self, key: CommandKey, overrides: dict[str, Any] | None = None) -> RawInfraredCommand:
        """Return a raw command, preferring user-learned overrides."""
        override = (overrides or {}).get(key.value)
        if override:
            return RawInfraredCommand(
                tuple(int(value) for value in override["timings"]),
                int(override.get("modulation", self.modulation)),
            )

        raw = self.raw_commands.get(key)
        if raw is not None:
            return RawInfraredCommand(raw, self.modulation)

        return encode_nec_extended(self.nec_address, COMMAND_NEC_IDS[key], self.modulation)


def _build_common_my302_profile() -> CommandProfile:
    return CommandProfile(
        key="xxmy_my302_common_24_key",
        name="XXMY MY302 common 24-key RGB",
        manufacturer="Shenzhen Xiang Xin Mao Yuan Electronics & Technology Co., Ltd",
        model="MY302",
        modulation=DEFAULT_MODULATION,
        nec_address=0xEF00,
        raw_commands={
            key: tuple(encode_nec_extended(0xEF00, command_id).get_raw_timings())
            for key, command_id in COMMAND_NEC_IDS.items()
        },
    )


MY302_PROFILE = _build_common_my302_profile()


def nearest_color_command(rgb_color: tuple[int, int, int]) -> CommandKey:
    """Return the supported preset closest to the requested RGB value."""
    red, green, blue = rgb_color

    def distance(item: tuple[CommandKey, tuple[int, int, int]]) -> int:
        _, color = item
        return (red - color[0]) ** 2 + (green - color[1]) ** 2 + (blue - color[2]) ** 2

    return min(COLOR_COMMANDS.items(), key=distance)[0]


def validate_command_overrides_json(value: str) -> dict[str, dict[str, Any]]:
    """Validate a JSON command override map."""
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("Command map must be an object")

    allowed = {key.value for key in COMMAND_KEYS}
    result: dict[str, dict[str, Any]] = {}
    for key, command in parsed.items():
        if key not in allowed:
            raise ValueError(f"Unknown command key: {key}")
        if not isinstance(command, dict):
            raise ValueError(f"Command {key} must be an object")
        timings = command.get("timings")
        if not isinstance(timings, list) or not timings:
            raise ValueError(f"Command {key} must contain a non-empty timings list")
        result[key] = {
            "timings": [int(timing) for timing in timings],
            "modulation": int(command.get("modulation", DEFAULT_MODULATION)),
        }
    return result


def export_command_overrides(overrides: dict[str, Any]) -> str:
    """Return stable JSON for command overrides."""
    return json.dumps(overrides, indent=2, sort_keys=True)
