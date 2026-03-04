# -*- coding: utf-8 -*-
"""Generate the acoustics report export."""

from __future__ import annotations

import datetime
from pathlib import Path

from .constants import FREQ_BANDS
from .physics import calculate_mode_pressure_map, rt60_quality
from .state import AcousticState

# Base reports directory
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"

# Analysis reports subdirectory
REPORTS_ANALYSIS_DIR = REPORTS_DIR / "analysis"


def export_report(state: AcousticState, notify, output_path: Path | None = None, base_name: str | None = None):
    """
    Export an acoustic analysis report.
    
    Args:
        state: The acoustic state containing room data
        notify: Callback function for notifications
        output_path: Optional custom output directory (default: reports/analysis)
        base_name: Optional base name for the file (default: auto-generated timestamp)
    
    Returns:
        Path to the saved report, or None on failure
    """
    if state.width < 0.1 or state.length < 0.1 or state.height < 0.1:
        notify("Room dimensions must be >= 0.1 m", severity="error")
        return None
    
    rt60_vals = state.rt60_vals
    modes = state.modes
    max_rt = max(rt60_vals) if rt60_vals and max(rt60_vals) > 0 else 1.0
    sep = "=" * 64
    sep2 = "-" * 44
    lines = [
        sep,
        "  ACOUSTICA -- ACOUSTIC REVERB & ROOM MODE REPORT",
        "  Generated : {}".format(datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")),
        sep,
        "",
        "ROOM GEOMETRY",
        sep2,
        "  Width  (W) : {:.2f} m".format(state.width),
        "  Length (L) : {:.2f} m".format(state.length),
        "  Height (H) : {:.2f} m".format(state.height),
        "  Volume     : {:.2f} m3".format(state.volume),
        "  Surface A. : {:.2f} m2".format(state.surface_area),
        "",
        "SURFACE MATERIALS",
        sep2,
        "  Walls   : {}".format(state.wall_mat),
        "  Floor   : {}".format(state.floor_mat),
        "  Ceiling : {}".format(state.ceil_mat),
        "",
        "RT60  (Sabine: RT60 = 0.161 * V / sum(S*alpha))",
        sep2,
    ]
    for freq, rt in zip(FREQ_BANDS, rt60_vals):
        bar = int(rt / max_rt * 30 + 0.5) if max_rt > 0 else 0
        lines.append("  {:>5} Hz : {:6.3f} s  {}".format(freq, rt, "#" * bar))
    lines += [
        "",
        "  RT60 @ 500 Hz = {:.3f} s  =>  {}".format(state.rt60_500, rt60_quality(state.rt60_500)),
        "",
        "AXIAL ROOM MODES  (fn = n * 343 / (2 * L))",
        sep2,
    ]
    for dim, freqs in modes.items():
        fstr = "  /  ".join("{:.1f} Hz".format(f) for f in freqs) if freqs else "n/a"
        lines.append("  {:<8}: {}".format(dim, fstr))
    if state.source is not None:
        frac_x, frac_y = state.source
        lines += ["", "SOUND SOURCE POSITION", sep2]
        lines.append("  S1  X = {:.2f} m,  Y = {:.2f} m".format(
            frac_x * state.width, frac_y * state.length
        ))

    # Add Sound Pressure Map if in map mode
    if state.view_mode == "map":
        lines += ["", "SOUND PRESSURE MAP", sep2]
        lines.append("  Mode: {}".format(state.map_mode.replace("-", " ").title()))
        lines.append("")
        
        # Calculate map indices
        nx, ny, nz = (1, 0, 0)
        if state.map_mode == "width-1":
            nx, ny, nz = (0, 1, 0)
        elif state.map_mode == "height-1":
            nx, ny, nz = (0, 0, 1)
            
        # Generate ASCII map
        res_x, res_y = 40, 15
        pressure = calculate_mode_pressure_map(
            state.width,
            state.length,
            state.height,
            (nx, ny, nz),
            resolution=(res_x, res_y),
            intensity_scale=state.map_intensity,
        )
        shade_chars = " .:-=+*#%@"
        shade_len = len(shade_chars) - 1
        
        # Top border
        lines.append("  +" + "-" * res_x + "+")
        for row in range(res_y):
            row_str = "  |"
            for col in range(res_x):
                val = pressure[row][col]
                # Recommendation logic for ASCII
                # S - High pressure (speakers), L - Low pressure (listener)
                if val > 0.92:
                    row_str += "S"
                elif val < 0.08:
                    row_str += "L"
                else:
                    idx = min(shade_len, max(0, int(val * shade_len)))
                    row_str += shade_chars[idx]
            row_str += "|"
            lines.append(row_str)
        # Bottom border
        lines.append("  +" + "-" * res_x + "+")
        lines.append("  (W axis -->)")
        lines.append("")
        lines.append("  Legend: S = Speaker (High Pressure), L = Listener (Low Pressure)")

    lines += ["", sep, "  End of Report -- Acoustica", sep]
    
    # Determine output path and filename
    if output_path is None:
        output_path = REPORTS_ANALYSIS_DIR
    
    if base_name is None:
        fname = "acoustica_report_{}.txt".format(
            datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        )
    else:
        fname = f"{base_name}.txt"
    
    output_path.mkdir(parents=True, exist_ok=True)
    out_path = output_path / fname
    
    try:
        out_path.write_text("\n".join(lines), encoding="utf-8")
        notify("Report saved -> {}".format(out_path), severity="information", timeout=6)
        return out_path
    except OSError as exc:
        notify(str(exc), severity="error")
        return None
