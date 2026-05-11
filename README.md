# XXMY MY302 IR RGB Control Box

Home Assistant custom integration for the infrared based **RGB Control Box IR
Remote Control**, model **MY302**, from Shenzhen Xiang Xin Mao Yuan Electronics
& Technology Co., Ltd. The integration controls the receiver through a Home
Assistant `infrared` transmitter entity, for example the Seeed Studio XIAO IR
Mate running ESPHome's IR/RF proxy firmware.

## Features

- Assumed-state RGB light entity for the MY302 control box.
- Native Home Assistant color and effect controls.
- Button entities for all 24 physical remote keys.
- Brighter/darker buttons instead of a fake brightness slider.
- Built-in common 24-key MY302 profile.
- Optional learned raw-code overrides for receiver or remote variants.
- English and German translations.

## Requirements

- Home Assistant 2026.4 or newer.
- An `infrared` transmitter entity, usually provided by ESPHome.
- A XIAO IR Mate, Broadlink, or another supported IR emitter positioned so the
  MY302 receiver can see it.

## Installation

### HACS

1. Add this repository as a custom HACS integration repository.
2. Install **XXMY MY302 IR RGB Control Box**.
3. Restart Home Assistant.
4. Add the integration and select the infrared transmitter entity.

### Manual

Copy `custom_components/xxmy_ir_rgb_control_box` into your Home Assistant
`custom_components` directory and restart Home Assistant.

## Learning Real Codes With XIAO IR Mate

Most users should not need to learn all buttons. The integration ships with a
common 24-key profile using extended NEC address `0xEF00`.

For maintainers, or for a device variant, flash the capture snippet from
`scripts/esphome/xiao_ir_mate_capture.yaml` or merge the important parts into
your XIAO IR Mate ESPHome YAML. When you press a remote button, the XIAO emits a
Home Assistant event:

```text
esphome.xxmy_ir_code_captured
```

The integration remembers the latest valid capture. Open the integration's
options, choose **Learn latest capture**, select the matching button, and save.
Learned commands override the built-in profile.

You can also import or export the full learned command map as JSON from the
options flow. The repository now also includes the decoded NEC capture for the
known MY302 remote in `scripts/captures/my302_raw_codes.json`; the baked profile
matches that capture.

## UI Notes

Home Assistant will show a normal light card for color and effects, similar to
the MiPow PlayBulb integration's native light UI. The MY302 receiver cannot
report state and does not support press-and-hold brightness through Home
Assistant, so brightness is represented by the `Brighter` and `Darker` button
entities instead of a slider.

## Command Keys

The 24 keys are represented as:

```text
brighter, darker, off, on,
red, green, blue, white,
red_orange, green_light, blue_dark, flash,
red_amber, green_cyan, blue_royal, strobe,
red_yellow, green_sky, blue_pink, fade,
red_pale_yellow, green_aqua, blue_purple, smooth
```

## Development

The reusable command/profile layer lives in `profile.py` and `raw_command.py`.
MY302-specific behavior is isolated in the default profile, so another IR HACS
integration can reuse the same model and replace only the profile data.
