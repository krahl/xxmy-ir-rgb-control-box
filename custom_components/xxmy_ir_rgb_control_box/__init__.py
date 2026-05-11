"""XXMY MY302 IR RGB Control Box integration."""

from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import Event, HomeAssistant, callback

from .const import DATA_LATEST_CAPTURE, DOMAIN, EVENT_IR_CODE_CAPTURED

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.LIGHT, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up XXMY MY302 from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    entry.async_on_unload(
        hass.bus.async_listen(EVENT_IR_CODE_CAPTURED, _async_capture_event(hass))
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an XXMY MY302 config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


def _async_capture_event(hass: HomeAssistant):
    """Build an event listener for ESPHome capture events."""

    @callback
    def _listener(event: Event) -> None:
        payload = _normalize_capture_payload(dict(event.data))
        if payload is None:
            _LOGGER.warning("Ignoring malformed MY302 IR capture event: %s", event.data)
            return
        hass.data.setdefault(DOMAIN, {})[DATA_LATEST_CAPTURE] = payload
        _LOGGER.info("Stored latest MY302 IR capture with %d timings", len(payload["timings"]))

    return _listener


def _normalize_capture_payload(data: dict[str, Any]) -> dict[str, Any] | None:
    """Normalize one raw capture event."""
    raw = data.get("timings") or data.get("code") or data.get("raw")
    if raw is None:
        return None

    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            raw = [part.strip() for part in raw.split(",") if part.strip()]

    if not isinstance(raw, list) or not raw:
        return None

    try:
        timings = [int(value) for value in raw]
        modulation = int(data.get("modulation") or data.get("carrier_frequency") or 38000)
    except (TypeError, ValueError):
        return None

    return {"timings": timings, "modulation": modulation}
