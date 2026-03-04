# -*- coding: utf-8 -*-
"""Shared state container for the Acoustica application."""

from __future__ import annotations

from .physics import compute_axial_modes, compute_rt60_per_band


class AcousticState:
    def __init__(self):
        self.width = 6.0
        self.length = 9.0
        self.height = 3.0
        self.wall_mat = "Gypsum Board"
        self.floor_mat = "Carpet (Thick)"
        self.ceil_mat = "Gypsum Board"
        self.source: tuple[float, float] | None = None
        self.view_mode = "room"
        self.map_mode = "length-1"
        self.rt60_vals: list[float] = [0.0] * 6
        self.modes: dict[str, list[float]] = {}
        self.map_intensity = 1.0

    def recompute(self):
        width, length, height = self.width, self.length, self.height
        if width >= 0.1 and length >= 0.1 and height >= 0.1:
            self.rt60_vals = compute_rt60_per_band(
                width, length, height, self.wall_mat, self.floor_mat, self.ceil_mat
            )
            self.modes = compute_axial_modes(width, length, height)
            self.map_intensity = self._compute_map_intensity()
        else:
            self.rt60_vals = [0.0] * 6
            self.modes = {}
            self.map_intensity = 0.0

    @property
    def volume(self):
        return self.width * self.length * self.height

    @property
    def surface_area(self):
        width, length, height = self.width, self.length, self.height
        return 2 * (length * height) + 2 * (width * height) + 2 * (width * length)

    def _compute_map_intensity(self):
        if not self.rt60_vals:
            return 0.0
        avg_rt = sum(self.rt60_vals) / len(self.rt60_vals)
        if avg_rt <= 0:
            return 0.0
        scale = avg_rt / 1.5
        return max(0.2, min(1.0, scale))

    @property
    def rt60_500(self):
        return self.rt60_vals[2] if len(self.rt60_vals) > 2 else 0.0
