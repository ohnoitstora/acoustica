# -*- coding: utf-8 -*-
"""Shared constants for the Acoustica TUI."""

import json
from pathlib import Path

SPEED_OF_SOUND = 343.0
SABINE_K = 0.161

FREQ_BANDS = [125, 250, 500, 1000, 2000, 4000]
FREQ_LABELS = ["125", "250", "500", "1k ", "2k ", "4k "]

# Load all materials from JSON file
MATERIALS: dict[str, list[float]] = {}
CUSTOM_MATERIALS_PATH = Path(__file__).resolve().parent.parent / "custom_materials.json"

if CUSTOM_MATERIALS_PATH.exists():
    try:
        with open(CUSTOM_MATERIALS_PATH, "r") as f:
            custom_data = json.load(f)
            for mat in custom_data.get("materials", []):
                name = mat.get("name")
                coeffs = mat.get("absorption_coefficients", {})
                # Map frequency labels to the expected list format
                freq_list = [
                    coeffs.get("125Hz", 0.0),
                    coeffs.get("250Hz", 0.0),
                    coeffs.get("500Hz", 0.0),
                    coeffs.get("1000Hz", 0.0),
                    coeffs.get("2000Hz", 0.0),
                    coeffs.get("4000Hz", 0.0)
                ]
                if name:
                    MATERIALS[name] = freq_list
    except Exception:
        pass # If file is malformed, start with empty materials

MATERIAL_NAMES = list(MATERIALS.keys())

SOURCE_COLOUR = "bright_red"
SOURCE_DOT = "\u25cf"

BAR_COLOURS = [
    "bright_red", "dark_orange", "gold1",
    "bright_green", "bright_blue", "medium_purple"
]
BLOCK = " \u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588"
