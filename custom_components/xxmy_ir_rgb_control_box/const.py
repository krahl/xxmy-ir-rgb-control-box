"""Constants for the XXMY MY302 IR RGB Control Box integration."""

from enum import StrEnum

DOMAIN = "xxmy_ir_rgb_control_box"

CONF_INFRARED_ENTITY_ID = "infrared_entity_id"

EVENT_IR_CODE_CAPTURED = "esphome.xxmy_ir_code_captured"
DATA_LATEST_CAPTURE = "latest_capture"

OPTION_COMMAND_OVERRIDES = "command_overrides"

DEFAULT_MODULATION = 38000


class CaptureField(StrEnum):
    """Known fields accepted from the ESPHome capture event."""

    CODE = "code"
    RAW = "raw"
    TIMINGS = "timings"
    CARRIER_FREQUENCY = "carrier_frequency"
    MODULATION = "modulation"


class OptionMode(StrEnum):
    """Options flow modes."""

    LEARN_LATEST = "learn_latest"
    IMPORT_JSON = "import_json"
    EXPORT_JSON = "export_json"
    CLEAR_OVERRIDES = "clear_overrides"
