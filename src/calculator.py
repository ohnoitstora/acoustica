# -*- coding: utf-8 -*-
"""Treatment Calculator screen for Acoustica."""

from __future__ import annotations

import datetime
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Grid, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Input, Label, Select

from .constants import FREQ_BANDS, FREQ_LABELS, MATERIAL_NAMES, MATERIALS

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports" / "treatment"


class TreatmentCalculatorScreen(Screen):
    """Acoustic treatment calculator screen with live results."""

    BINDINGS = [
        Binding("ctrl+m", "main_menu", "Main Menu"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self._room_volume = 100.0  # m³
        self._target_rt60 = 0.5  # seconds
        self._current_rt60 = 1.2  # seconds
        self._absorption_needed = 0.0  # sabins

    def compose(self) -> ComposeResult:
        with Horizontal(id="calc-header"):
            yield Label("  🧮 TREATMENT CALCULATOR", id="calc-header-title")
            yield Label("Calculate absorption requirements", id="calc-header-subtitle")
            yield Button("← Back", id="btn-calc-back", classes="hdr-btn")
        with Container(id="calc-body"):
            with Grid(id="calc-grid"):
                # Left column - User inputs
                with VerticalScroll(id="calc-inputs") as inputs:
                    inputs.border_title = "ROOM PARAMETERS"
                    yield Label("RT60 Preset", classes="calc-section-title")
                    yield Select(
                        [
                            ("Custom", "custom"),
                            ("Recording Studio (0.3s)", "0.3"),
                            ("Home Theater (0.5s)", "0.5"),
                            ("Lecture Hall (1.0s)", "1.0"),
                            ("Concert Hall (1.5s)", "1.5"),
                            ("Church/Cathedral (2.0s)", "2.0"),
                        ],
                        value="custom",
                        id="sel-rt60-preset",
                    )
                    yield Label("Room Volume (m³)", classes="calc-section-title")
                    yield Input(
                        str(self._room_volume),
                        id="inp-volume",
                        classes="calc-input",
                        restrict=r"[0-9.]*",
                    )
                    yield Label("Target RT60 (seconds)", classes="calc-section-title")
                    yield Input(
                        str(self._target_rt60),
                        id="inp-target",
                        classes="calc-input",
                        restrict=r"[0-9.]*",
                    )
                    yield Label("Current RT60 (seconds)", classes="calc-section-title")
                    yield Input(
                        str(self._current_rt60),
                        id="inp-current",
                        classes="calc-input",
                        restrict=r"[0-9.]*",
                    )
                    yield Label("Frequency Band (Hz)", classes="calc-section-title")
                    yield Select(
                        [(label.strip(), val) for label, val in zip(FREQ_LABELS, FREQ_BANDS)],
                        value=500,
                        id="sel-frequency",
                    )
                    yield Label("Treatment Material", classes="calc-section-title")
                    yield Select(
                        [(m, m) for m in MATERIAL_NAMES],
                        value="Acoustic Foam",
                        id="sel-material",
                    )
                    yield Label("Price Per Panel ($)", classes="calc-section-title")
                    yield Input(
                        "50",
                        id="inp-price",
                        classes="calc-input",
                        restrict=r"[0-9.]*",
                    )
                # Right column - Live results
                with Vertical(id="calc-results") as results:
                    results.border_title = "CALCULATED REQUIREMENTS"
                    yield Label("Absorption Needed", classes="calc-result-label")
                    yield Label(
                        "0.00 sabins",
                        id="lbl-absorption",
                        classes="calc-result-value",
                    )
                    yield Label("Panel Coverage", classes="calc-result-label")
                    yield Label(
                        "0.00 m²",
                        id="lbl-coverage",
                        classes="calc-result-value",
                    )
                    yield Label("Estimated Panels", classes="calc-result-label")
                    yield Label(
                        "0 panels",
                        id="lbl-panels",
                        classes="calc-result-value",
                    )
                    yield Label("Total Cost", classes="calc-result-label")
                    yield Label(
                        "$0.00",
                        id="lbl-cost",
                        classes="calc-result-value",
                    )
                    yield Label("", id="calc-spacer")
                    yield Label(
                        "Adjust inputs to see live updates",
                        id="calc-hint",
                    )
                    yield Button("📄 Export Plan", id="btn-export-plan", variant="primary")
        yield Footer()

    def on_mount(self):
        self._calculate()

    @on(Input.Submitted)
    @on(Input.Changed)
    def _on_input(self, event):
        id_ = event.input.id
        try:
            val = float(event.value)
        except (ValueError, TypeError):
            return
        if val <= 0:
            return
        if id_ == "inp-volume":
            self._room_volume = val
        elif id_ == "inp-target":
            self._target_rt60 = val
            # If user manually changes target, switch preset to custom
            preset_sel = self.query_one("#sel-rt60-preset", Select)
            if str(preset_sel.value) != "custom":
                # Only switch if value is different (avoid loop with preset selection)
                try:
                    preset_val = float(str(preset_sel.value))
                    if abs(preset_val - val) > 0.001:
                        preset_sel.value = "custom"
                except ValueError:
                    preset_sel.value = "custom"
        elif id_ == "inp-current":
            self._current_rt60 = val
        elif id_ == "inp-price":
            # Price per panel - just trigger recalculation
            pass
        else:
            return
        self._calculate()

    @on(Select.Changed)
    def _on_select(self, event):
        if event.value == Select.BLANK:
            return
        
        # Handle RT60 preset selection
        if event.select.id == "sel-rt60-preset":
            preset_value = str(event.value)
            if preset_value != "custom":
                try:
                    rt60_val = float(preset_value)
                    self._target_rt60 = rt60_val
                    # Update the target input field
                    target_input = self.query_one("#inp-target", Input)
                    target_input.value = str(rt60_val)
                except ValueError:
                    pass
        
        self._calculate()

    @on(Button.Pressed, "#btn-calc-back")
    def action_main_menu(self):
        self.app.pop_screen()

    def _calculate(self):
        """Calculate absorption requirements based on inputs."""
        # Sabine formula: RT60 = 0.161 * V / A
        # Solving for A: A = 0.161 * V / RT60
        SABINE_K = 0.161

        current_absorption = (SABINE_K * self._room_volume) / max(
            self._current_rt60, 0.01
        )
        target_absorption = (SABINE_K * self._room_volume) / max(
            self._target_rt60, 0.01
        )
        self._absorption_needed = max(0, target_absorption - current_absorption)

        # Get selected frequency index
        sel_freq = self.query_one("#sel-frequency", Select)
        try:
            freq_val = int(sel_freq.value)
            freq_idx = FREQ_BANDS.index(freq_val)
        except (ValueError, TypeError):
            freq_idx = 2  # Default to 500Hz (index 2)

        # Get material absorption coefficient for that frequency
        select = self.query_one("#sel-material", Select)
        mat_name = str(select.value)
        coeffs = MATERIALS.get(mat_name, [0.5] * 6)
        
        # Ensure we have enough coefficients, otherwise fallback
        if freq_idx < len(coeffs):
            coeff = coeffs[freq_idx]
        else:
            coeff = 0.5

        # Calculate coverage area needed
        coverage_area = self._absorption_needed / max(coeff, 0.01)

        # Estimate number of panels (assuming 60x60cm panels)
        panel_area = 0.6 * 0.6  # m² per panel
        num_panels = int(coverage_area / panel_area)

        # Get price per panel
        price_input = self.query_one("#inp-price", Input)
        try:
            price_per_panel = float(price_input.value)
        except (ValueError, TypeError):
            price_per_panel = 50.0
        
        # Calculate total cost
        total_cost = num_panels * price_per_panel

        # Update display
        self.query_one("#lbl-absorption", Label).update(
            "{:.2f} sabins".format(self._absorption_needed)
        )
        self.query_one("#lbl-coverage", Label).update(
            "{:.2f} m²".format(coverage_area)
        )
        self.query_one("#lbl-panels", Label).update(
            "{} panels".format(num_panels)
        )
        self.query_one("#lbl-cost", Label).update(
            "${:,.2f}".format(total_cost)
        )

        # Store current values for export
        self._last_coverage_area = coverage_area
        self._last_num_panels = num_panels
        self._last_coeff = coeff
        self._last_freq_idx = freq_idx
        self._last_price = price_per_panel
        self._last_total_cost = total_cost

    @on(Button.Pressed, "#btn-export-plan")
    def _export_plan(self):
        """Export the treatment calculation results to a text file."""
        # Get current values from widgets
        sel_freq = self.query_one("#sel-frequency", Select)
        select = self.query_one("#sel-material", Select)
        
        try:
            freq_val = int(sel_freq.value)
            freq_idx = FREQ_BANDS.index(freq_val)
        except (ValueError, TypeError):
            freq_val = 500
            freq_idx = 2
        
        mat_name = str(select.value) if select.value else "Unknown"
        
        # Get coefficient for display
        coeffs = MATERIALS.get(mat_name, [0.5] * 6)
        if freq_idx < len(coeffs):
            coeff = coeffs[freq_idx]
        else:
            coeff = 0.5
        
        # Calculate coverage and panels
        coverage_area = self._absorption_needed / max(coeff, 0.01)
        panel_area = 0.6 * 0.6
        num_panels = int(coverage_area / panel_area)
        
        # Get price and calculate cost
        price_input = self.query_one("#inp-price", Input)
        try:
            price_per_panel = float(price_input.value)
        except (ValueError, TypeError):
            price_per_panel = 50.0
        total_cost = num_panels * price_per_panel
        
        # Generate report content
        sep = "=" * 64
        sep2 = "-" * 44
        lines = [
            sep,
            "  ACOUSTICA -- TREATMENT CALCULATOR REPORT",
            "  Generated : {}".format(datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")),
            sep,
            "",
            "ROOM PARAMETERS",
            sep2,
            "  Room Volume      : {:.2f} m³".format(self._room_volume),
            "  Target RT60      : {:.2f} s".format(self._target_rt60),
            "  Current RT60     : {:.2f} s".format(self._current_rt60),
            "",
            "TREATMENT SPECIFICATION",
            sep2,
            "  Frequency Band   : {} Hz".format(freq_val),
            "  Material         : {}".format(mat_name),
            "  Absorption Coeff : {:.2f}".format(coeff),
            "",
            "CALCULATED REQUIREMENTS",
            sep2,
            "  Absorption Needed: {:.2f} sabins".format(self._absorption_needed),
            "  Panel Coverage   : {:.2f} m²".format(coverage_area),
            "  Estimated Panels : {} panels".format(num_panels),
            "  (Based on 60x60cm panels)",
            "",
            "COST ESTIMATE",
            sep2,
            "  Price Per Panel  : ${:,.2f}".format(price_per_panel),
            "  Total Cost       : ${:,.2f}".format(total_cost),
            "",
            sep,
            "  End of Report -- Acoustica Treatment Calculator",
            sep,
        ]
        
        # Save to reports directory
        fname = "treatment_plan_{}.txt".format(
            datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        out_path = REPORTS_DIR / fname
        
        try:
            out_path.write_text("\n".join(lines), encoding="utf-8")
            self.app.notify(
                "Treatment plan saved -> {}".format(out_path),
                severity="information",
                timeout=6
            )
        except OSError as exc:
            self.app.notify(str(exc), severity="error")
