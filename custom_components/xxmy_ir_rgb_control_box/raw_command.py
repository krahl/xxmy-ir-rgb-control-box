"""Infrared command helpers."""

from __future__ import annotations

from dataclasses import dataclass

NEC_HEADER_MARK = 9000
NEC_HEADER_SPACE = -4500
NEC_BIT_MARK = 560
NEC_ZERO_SPACE = -560
NEC_ONE_SPACE = -1690


@dataclass(frozen=True)
class RawInfraredCommand:
    """Simple raw IR command compatible with Home Assistant infrared emitters."""

    timings: tuple[int, ...]
    modulation: int = 38000

    def get_raw_timings(self) -> list[int]:
        """Return raw timings as alternating mark/space durations in microseconds."""
        return list(self.timings)


def encode_nec_extended(address: int, command: int, modulation: int = 38000) -> RawInfraredCommand:
    """Encode a common extended NEC command as raw timings.

    Extended NEC transmits a 16-bit address followed by an 8-bit command and
    the inverse command, all least-significant bit first.
    """
    bits: list[int] = []

    for value, width in ((address, 16), (command, 8), ((~command) & 0xFF, 8)):
        for bit in range(width):
            bits.append((value >> bit) & 1)

    timings: list[int] = [NEC_HEADER_MARK, NEC_HEADER_SPACE]
    for bit in bits:
        timings.extend((NEC_BIT_MARK, NEC_ONE_SPACE if bit else NEC_ZERO_SPACE))
    timings.append(NEC_BIT_MARK)

    return RawInfraredCommand(tuple(timings), modulation)
