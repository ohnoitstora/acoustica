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


def compute_schroeder_frequency(rt60_vals: list[float], volume: float) -> float:
    """
    Calculate the Schroeder frequency (critical frequency) for a room.
    
    The Schroeder frequency marks the transition between the modal region
    (where discrete room modes dominate) and the statistical region
    (where diffuse field conditions apply).
    
    Formula: f_schroeder = 2000 * sqrt(RT60 / V)
    
    Args:
        rt60_vals: List of RT60 values per frequency band
        volume: Room volume in cubic meters
        
    Returns:
        Schroeder frequency in Hz, or 0.0 if volume is invalid
    """
    if volume <= 0 or not rt60_vals:
        return 0.0
    
    # Use average RT60 across all bands for calculation
    avg_rt60 = sum(rt60_vals) / len(rt60_vals)
    if avg_rt60 <= 0:
        return 0.0
    
    # Schroeder formula: f_sch = 2000 * sqrt(RT60 / V)
    schroeder_freq = 2000.0 * math.sqrt(avg_rt60 / volume)
    return schroeder_freq


def calculate_nrc(absorption_coeffs: list[float]) -> float:
    """
    Calculate the Noise Reduction Coefficient (NRC) for a material.
    
    NRC is the average absorption coefficient at 250, 500, 1000, and 2000 Hz,
    rounded to the nearest 0.05.
    
    Args:
        absorption_coeffs: List of 6 absorption coefficients for bands
                          [125, 250, 500, 1000, 2000, 4000] Hz
                          
    Returns:
        NRC value between 0.00 and 1.00
    """
    if len(absorption_coeffs) < 5:
        return 0.0
    
    # NRC uses 250, 500, 1000, 2000 Hz (indices 1, 2, 3, 4)
    nrc_bands = absorption_coeffs[1:5]
    avg = sum(nrc_bands) / 4.0
    
    # Round to nearest 0.05
    nrc = round(avg * 20.0) / 20.0
    
    # Clamp to valid range
    return max(0.0, min(1.0, nrc))


def calculate_weighted_absorption(
    width: float,
    length: float,
    height: float,
    wall_mat: str,
    floor_mat: str,
    ceil_mat: str,
    materials_dict: dict
) -> list[float]:
    """
    Calculate weighted absorption coefficients for the entire room.
    
    Returns absorption coefficients per frequency band weighted by surface area.
    
    Args:
        width, length, height: Room dimensions in meters
        wall_mat, floor_mat, ceil_mat: Material names
        materials_dict: Dictionary mapping material names to absorption lists
        
    Returns:
        List of 6 weighted absorption coefficients
    """
    wall_area = 2.0 * length * height + 2.0 * width * height
    floor_area = width * length
    ceiling_area = width * length
    total_area = wall_area + floor_area + ceiling_area
    
    if total_area <= 0:
        return [0.0] * 6
    
    wall_absorption = materials_dict.get(wall_mat, [0.0] * 6)
    floor_absorption = materials_dict.get(floor_mat, [0.0] * 6)
    ceiling_absorption = materials_dict.get(ceil_mat, [0.0] * 6)
    
    weighted = []
    for i in range(6):
        weighted_abs = (
            wall_area * wall_absorption[i] +
            floor_area * floor_absorption[i] +
            ceiling_area * ceiling_absorption[i]
        ) / total_area
        weighted.append(weighted_abs)
    
    return weighted


def calculate_room_nrc(width: float, length: float, height: float,
                       wall_mat: str, floor_mat: str, ceil_mat: str,
                       materials_dict: dict) -> float:
    """
    Calculate the effective NRC for an entire room based on weighted absorption.
    
    Args:
        width, length, height: Room dimensions in meters
        wall_mat, floor_mat, ceil_mat: Material names
        materials_dict: Dictionary mapping material names to absorption lists
        
    Returns:
        Room NRC value between 0.00 and 1.00
    """
    weighted = calculate_weighted_absorption(
        width, length, height, wall_mat, floor_mat, ceil_mat, materials_dict
    )
    return calculate_nrc(weighted)

