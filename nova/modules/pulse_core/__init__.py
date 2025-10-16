"""
Pulse Core module initialization.

This module exposes the primary functions `generate_pulse` and `build_pulse_card` from `pulse_core`.
"""

from .pulse_core import generate_pulse, build_pulse_card

__all__ = ["generate_pulse", "build_pulse_card"]
