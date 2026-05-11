"""Tests for reusable MY302 profile helpers."""

import json

import pytest

from custom_components.xxmy_ir_rgb_control_box.profile import (
    COMMAND_KEYS,
    MY302_PROFILE,
    CommandKey,
    nearest_color_command,
    validate_command_overrides_json,
)
from custom_components.xxmy_ir_rgb_control_box.raw_command import encode_nec_extended


def test_all_commands_have_default_raw_timings() -> None:
    """Every 24-key command has a baked default command."""
    assert len(COMMAND_KEYS) == 24

    for key in COMMAND_KEYS:
        command = MY302_PROFILE.command(key)
        timings = command.get_raw_timings()
        assert command.modulation == 38000
        assert timings[0:2] == [9000, -4500]
        assert timings[-1] == 560


def test_nec_encoder_uses_expected_command_bits() -> None:
    """The fallback NEC encoder is deterministic."""
    timings = encode_nec_extended(0xEF00, 0x00).get_raw_timings()
    assert timings[0:2] == [9000, -4500]
    assert len(timings) == 67


def test_learned_override_takes_precedence() -> None:
    """User-learned raw timings override the baked profile."""
    command = MY302_PROFILE.command(
        CommandKey.RED,
        {"red": {"timings": [1, -2, 3], "modulation": 40000}},
    )
    assert command.get_raw_timings() == [1, -2, 3]
    assert command.modulation == 40000


@pytest.mark.parametrize(
    ("rgb", "expected"),
    [
        ((250, 10, 10), CommandKey.RED),
        ((10, 250, 10), CommandKey.GREEN),
        ((10, 10, 250), CommandKey.BLUE),
        ((250, 250, 250), CommandKey.WHITE),
    ],
)
def test_nearest_color_command(rgb: tuple[int, int, int], expected: CommandKey) -> None:
    """RGB requests map to the nearest physical preset."""
    assert nearest_color_command(rgb) == expected


def test_validate_command_overrides_json() -> None:
    """Import validation returns normalized command maps."""
    result = validate_command_overrides_json(
        json.dumps({"red": {"timings": ["1", "-2", "3"], "modulation": "38000"}})
    )
    assert result == {"red": {"timings": [1, -2, 3], "modulation": 38000}}


def test_validate_command_overrides_json_rejects_unknown_key() -> None:
    """Unknown command keys are rejected."""
    with pytest.raises(ValueError):
        validate_command_overrides_json(json.dumps({"unknown": {"timings": [1]}}))
