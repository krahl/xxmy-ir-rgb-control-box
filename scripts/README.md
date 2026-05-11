# Maintainer Capture Workflow

1. Flash or merge `esphome/xiao_ir_mate_capture.yaml` into the XIAO IR Mate.
2. In Home Assistant, enable ESPHome actions for that device.
3. Add this integration and open its options.
4. Press a physical MY302 remote button.
5. Choose **Learn latest capture** and map that capture to the matching command.
6. Repeat for all 24 buttons.
7. Export the JSON command map from the options flow.
8. Save the exported map as `scripts/captures/my302_raw_codes.json`.

The current integration can already use exported JSON as learned overrides. A
future maintainer pass can convert the capture artifact into a baked raw profile
so new users do not need to learn their remotes.
