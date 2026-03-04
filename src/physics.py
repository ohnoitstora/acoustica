# -*- coding: utf-8 -*-
"""Physics calculations for RT60 and room modes."""

from __future__ import annotations

from .constants import FREQ_BANDS, MATERIALS, SABINE_K, SPEED_OF_SOUND


import math


def compute_rt60_per_band(width, length, height, wall_mat, floor_mat, ceil_mat):
    volume = width * length * height
    wall_area = 2.0 * length * height + 2.0 * width * height
    floor_area = width * length
    ceiling_area = width * length
    wall_absorption = MATERIALS[wall_mat]
    floor_absorption = MATERIALS[floor_mat]
    ceiling_absorption = MATERIALS[ceil_mat]
    out = []
    for i in range(len(FREQ_BANDS)):
        absorption_area = (
            wall_area * wall_absorption[i]
            + floor_area * floor_absorption[i]
            + ceiling_area * ceiling_absorption[i]
        )
        out.append(SABINE_K * volume / absorption_area if absorption_area > 1e-9 and volume > 1e-9 else 0.0)
    return out


def compute_axial_modes(width, length, height, n_modes=3):
    out = {}
    for name, dim in [("Length", length), ("Width", width), ("Height", height)]:
        out[name] = (
            [(n * SPEED_OF_SOUND) / (2.0 * dim) for n in range(1, n_modes + 1)]
            if dim >= 0.1
            else []
        )
    return out


def rt60_quality(rt60_500):
    if rt60_500 < 0.30:
        return "Very dry  -- anechoic / over-damped"
    if rt60_500 < 0.50:
        return "Dry       -- recording studios"
    if rt60_500 < 0.80:
        return "Moderate  -- home theaters"
    if rt60_500 < 1.20:
        return "Live      -- small concert halls"
    if rt60_500 < 2.00:
        return "Very live -- lecture halls / churches"
    return "Extreme   -- cathedrals"


def calculate_mode_pressure_map(width, length, height, mode_indices, resolution=20, intensity_scale=1.0):
    """
    Calculates sound pressure distribution for a specific mode.
    mode_indices: tuple of (nx, ny, nz)
    Returns a 2D grid (list of lists) for the floor plane (z=0) normalized 0-1.
    """
    nx, ny, nz = mode_indices
    if isinstance(resolution, tuple):
        res_x, res_y = resolution
    else:
        res_x = res_y = resolution
    res_x = max(2, int(res_x))
    res_y = max(2, int(res_y))
    scale = max(0.0, min(1.0, float(intensity_scale)))
    grid = []

    for i in range(res_y):
        row = []
        y = (i / (res_y - 1)) * length
        for j in range(res_x):
            x = (j / (res_x - 1)) * width

            # Pressure formula for a rectangular room (standing wave)
            # P(x,y,z) = cos(nx*pi*x/L) * cos(ny*pi*y/W) * cos(nz*pi*z/H)
            # We'll look at the floor plane (z=0), so cos(0) = 1
            p = math.cos(nx * math.pi * x / width) * math.cos(ny * math.pi * y / length)

            # Normalize to 0-1 (absolute value of pressure) with absorption scaling
            row.append(abs(p) * scale)
        grid.append(row)

    return grid

