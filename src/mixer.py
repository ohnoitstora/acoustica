# -*- coding: utf-8 -*-
"""Acoustic Mixer screen for real-time reverb decay visualization."""

from __future__ import annotations

import datetime
import math
from pathlib import Path

from rich.style import Style
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Button, Footer, Input, Label, Select

from .constants import FREQ_BANDS, FREQ_LABELS, BAR_COLOURS, MATERIALS, MATERIAL_NAMES

# Directory for mixer reports
MIXER_REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports" / "mixer"


class DecayGraph(Widget):
    """Widget that displays sound decay curve from 0 to -60 dB over time."""

    DEFAULT_CSS = """
    DecayGraph {
        height: 1fr;
        border: solid #2e1a52;
        background: #0a0616;
        padding: 0 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._absorption_values = [0.5] * 6
        self._max_rt60 = 3.0
        self._highlight_band: int | None = None  # Highlight specific frequency band

    def update_absorption(self, values: list[float]) -> None:
        """Update absorption values and refresh the graph."""
        self._absorption_values = values[:6] if len(values) >= 6 else values + [0.5] * (6 - len(values))
        self.refresh()

    def set_highlight(self, band_idx: int | None) -> None:
        """Set which frequency band to highlight (None for all)."""
        self._highlight_band = band_idx
        self.refresh()

    def render(self) -> Text:
        width_chars = max(self.size.width - 2, 10)
        height_chars = max(self.size.height - 2, 8)

        grid = [[" "] * width_chars for _ in range(height_chars)]
        styles = [[None] * width_chars for _ in range(height_chars)]

        def _put(row, col, ch, sty=None):
            if 0 <= row < height_chars and 0 <= col < width_chars:
                grid[row][col] = ch
                styles[row][col] = sty

        # Draw axes
        axis_col = 6
        for row in range(height_chars):
            _put(row, axis_col, "│", "dim #6b5f7a")
        _put(0, axis_col, "┐", "dim #6b5f7a")
        _put(height_chars - 1, axis_col, "┘", "dim #6b5f7a")

        axis_row = height_chars - 2
        for col in range(axis_col + 1, width_chars):
            _put(axis_row, col, "─", "dim #6b5f7a")
        _put(axis_row, width_chars - 1, "┤", "dim #6b5f7a")

        # Y-axis labels (dB)
        db_labels = [(0, "0dB"), (height_chars // 2, "-30"), (height_chars - 2, "-60")]
        for row, label in db_labels:
            for i, ch in enumerate(label):
                if axis_col - len(label) + i >= 0:
                    _put(row, axis_col - len(label) + i, ch, "dim #9180a8")

        # X-axis label
        time_label = "Time →"
        for i, ch in enumerate(time_label):
            col = axis_col + 3 + i
            if col < width_chars:
                _put(height_chars - 1, col, ch, "dim #9180a8")

        graph_width = width_chars - axis_col - 2
        graph_height = height_chars - 3

        if graph_width > 0 and graph_height > 0:
            for band_idx, (alpha, color, label) in enumerate(
                zip(self._absorption_values, BAR_COLOURS, FREQ_LABELS)
            ):
                # Determine if this band should be highlighted
                is_highlighted = self._highlight_band is None or self._highlight_band == band_idx
                curve_color = color if is_highlighted else f"dim {color}"
                
                min_rt60 = 0.2
                rt60 = min_rt60 + (self._max_rt60 - min_rt60) * (1.0 - alpha)
                decay_constant = 13.8 / rt60

                curve_points = []
                for col in range(graph_width):
                    t = (col / max(graph_width - 1, 1)) * self._max_rt60
                    db_level = -60.0 * (1.0 - math.exp(-decay_constant * t))
                    row = int((-db_level / 60.0) * graph_height)
                    row = min(max(row, 0), graph_height - 1)
                    row = graph_height - 1 - row
                    curve_points.append((row, col))

                prev_row = None
                for row, col in curve_points:
                    if prev_row is not None:
                        step = 1 if row >= prev_row else -1
                        for r in range(prev_row, row + step, step):
                            _put(r, axis_col + 1 + col, "│", curve_color)
                    _put(row, axis_col + 1 + col, "●", f"bold {curve_color}")
                    prev_row = row

        # Add legend
        legend_y = 1
        legend_x = width_chars - 20
        for idx, (label, color) in enumerate(zip(FREQ_LABELS, BAR_COLOURS)):
            is_highlighted = self._highlight_band is None or self._highlight_band == idx
            legend_color = color if is_highlighted else f"dim {color}"
            if legend_x > axis_col + 10 and legend_y + idx < height_chars - 3:
                _put(legend_y + idx, legend_x, "●", f"bold {legend_color}")
                for i, ch in enumerate(label.strip()):
                    if legend_x + 2 + i < width_chars:
                        _put(legend_y + idx, legend_x + 2 + i, ch, f"dim #e8d5ff" if is_highlighted else "dim #4a4a5a")

        out = Text()
        for row_idx, row in enumerate(grid):
            for col_idx, ch in enumerate(row):
                style = styles[row_idx][col_idx]
                out.append(ch, style=Style.parse(style) if style else Style())
            if row_idx < height_chars - 1:
                out.append("\n")
        return out


class AcousticMixerPanel(Widget):
    """Reusable mixer panel for sliders + decay graph."""

    def __init__(self, show_back_button: bool = True, embedded: bool = False):
        super().__init__()
        self._absorption_values = [0.5] * 6
        self._current_material = ""
        self._highlight_band: int | None = None
        self._suspend_material_sync = False
        self._show_back_button = show_back_button
        self._is_embedded = embedded
        if self._is_embedded:
            self.add_class("mixer-embed")

    def on_mount(self):
        """Initialize the graph with current values."""
        self._update_graph()
        if self._is_embedded:
            self._disable_preset_controls()
        self._sync_focus_buttons()

    def _disable_preset_controls(self) -> None:
        preset_label = self.query_one("#mixer-preset-controls", Container)
        preset_label.display = False

    def _sync_focus_buttons(self) -> None:
        if self._highlight_band is None:
            active_id = "btn-freq-all"
        else:
            active_id = f"btn-freq-{self._highlight_band}"
        for button in self.query(".freq-btn"):
            button.remove_class("freq-btn-active")
        self.query_one(f"#{active_id}", Button).add_class("freq-btn-active")

    def compose(self) -> ComposeResult:
        with Horizontal(id="mixer-panel"):
            # Left panel - Controls
            with Vertical(id="mixer-sliders-panel", classes="mixer-panel") as sliders_panel:
                if self._show_back_button:
                    yield Button("← Back", id="btn-mixer-back", classes="mixer-back-inline")
                sliders_panel.border_title = "FREQUENCY BANDS"

                # Material selector
                with Container(id="mixer-preset-controls"):
                    yield Label("Load Material Preset", classes="mixer-section-title")
                    yield Select(
                        [("— Custom —", "")] + [(name, name) for name in MATERIAL_NAMES],
                        value="",
                        id="sel-material-preset",
                    )

                yield Label("Adjust absorption per band", classes="mixer-section-title")
                yield Label("(0 = reflective, 1 = fully absorptive)", classes="mixer-hint")

                with VerticalScroll(id="sliders-container"):
                    for idx, (freq, label, color) in enumerate(
                        zip(FREQ_BANDS, FREQ_LABELS, BAR_COLOURS)
                    ):
                        with Container(classes="slider-group"):
                            with Horizontal(classes="slider-header"):
                                yield Label(
                                    f"{label.strip()}",
                                    classes="slider-freq-label",
                                )
                                yield Label(
                                    f"{self._absorption_values[idx]:.2f}",
                                    id=f"slider-value-{idx}",
                                    classes="slider-value",
                                )
                            with Horizontal(classes="slider-control-row"):
                                yield Button("-", id=f"dec-slider-{idx}", classes="slider-btn")
                                yield Input(
                                    f"{self._absorption_values[idx]:.2f}",
                                    id=f"input-slider-{idx}",
                                    classes="slider-input",
                                    restrict=r"[0-9.]*",
                                )
                                yield Button("+", id=f"inc-slider-{idx}", classes="slider-btn")
                            with Horizontal(classes="slider-bar-container"):
                                bar_width = int(self._absorption_values[idx] * 20)
                                bar_char = "█" * bar_width + "░" * (20 - bar_width)
                                yield Label(
                                    bar_char,
                                    id=f"slider-bar-{idx}",
                                    classes="slider-bar",
                                )

                with Horizontal(classes="mixer-controls"):
                    yield Button("Reset All", id="btn-reset-sliders", variant="primary")
                    yield Button("Flat 0.5", id="btn-flat-mid", variant="primary")

            # Right panel - Decay graph and controls
            with Vertical(id="mixer-graph-panel", classes="mixer-panel") as graph_panel:
                graph_panel.border_title = "REVERB DECAY CURVE"
                yield Label(
                    "Sound level decay from 0 dB to -60 dB over time",
                    classes="mixer-graph-hint",
                )

                # Frequency band selector buttons
                with Horizontal(id="freq-selector"):
                    yield Label("Focus:", classes="freq-selector-label")
                    yield Button("All", id="btn-freq-all", classes="freq-btn freq-btn-active freq-btn-all")
                    for idx, label in enumerate(FREQ_LABELS):
                        yield Button(
                            label.strip(),
                            id=f"btn-freq-{idx}",
                            classes=f"freq-btn freq-btn-{idx}",
                        )

                yield DecayGraph()

                # Export button
                with Horizontal(classes="mixer-export-row"):
                    yield Button("📄 Export Report", id="btn-export-mixer", variant="primary")
                    yield Label("", id="export-status")

    def set_absorption_values(self, values: list[float], material_label: str | None = None) -> None:
        """Set absorption values and refresh the panel."""
        padded = values[:6] if len(values) >= 6 else values + [0.5] * (6 - len(values))
        self._absorption_values = padded
        self._current_material = material_label or ""
        if not self._is_embedded:
            preset_select = self.query_one("#sel-material-preset", Select)
            self._suspend_material_sync = True
            preset_select.value = material_label or ""
            self._suspend_material_sync = False
        self._apply_slider_values()

    @on(Select.Changed, "#sel-material-preset")
    def _on_material_selected(self, event: Select.Changed) -> None:
        """Load absorption values from selected material."""
        if self._suspend_material_sync:
            return
        if event.value == Select.BLANK or event.value == "":
            return
        if self._is_embedded:
            self._suspend_material_sync = True
            self.query_one("#sel-material-preset", Select).value = ""
            self._suspend_material_sync = False
            return

        material_name = str(event.value)
        if material_name in MATERIALS:
            self._absorption_values = MATERIALS[material_name].copy()
            self._current_material = material_name
            self._apply_slider_values()

    @on(Input.Submitted)
    @on(Input.Changed)
    def _on_input_changed(self, event: Input.Changed) -> None:
        """Handle direct input value changes - updates graph immediately."""
        if self._is_embedded:
            return
        input_id = event.input.id
        if input_id and input_id.startswith("input-slider-"):
            try:
                idx = int(input_id.split("-")[-1])
                if 0 <= idx < 6:
                    val = float(event.value)
                    val = max(0.0, min(1.0, val))
                    self._absorption_values[idx] = val
                    self._update_slider_display(idx, val)
                    self._update_graph()
                    self._current_material = ""  # Custom values
                    self._suspend_material_sync = True
                    self.query_one("#sel-material-preset", Select).value = ""
                    self._suspend_material_sync = False
            except (ValueError, TypeError):
                pass

    @on(Button.Pressed, ".slider-btn")
    def _on_slider_btn(self, event: Button.Pressed) -> None:
        """Handle +/- button presses - updates graph immediately."""
        if self._is_embedded:
            return
        btn_id = event.button.id or ""
        if btn_id.startswith("inc-"):
            idx = int(btn_id.split("-")[-1])
            delta = 0.05
        elif btn_id.startswith("dec-"):
            idx = int(btn_id.split("-")[-1])
            delta = -0.05
        else:
            return

        if 0 <= idx < 6:
            new_val = max(0.0, min(1.0, self._absorption_values[idx] + delta))
            self._absorption_values[idx] = new_val
            self._update_slider_display(idx, new_val)
            self._update_graph()
            self._current_material = ""
            self._suspend_material_sync = True
            self.query_one("#sel-material-preset", Select).value = ""
            self._suspend_material_sync = False

    @on(Button.Pressed, ".freq-btn")
    def _on_freq_btn(self, event: Button.Pressed) -> None:
        """Handle frequency band selection buttons."""
        if self._is_embedded:
            return
        btn_id = event.button.id or ""

        # Update button styles
        for btn in self.query(".freq-btn"):
            btn.remove_class("freq-btn-active")
        event.button.add_class("freq-btn-active")

        if btn_id == "btn-freq-all":
            self._highlight_band = None
        elif btn_id.startswith("btn-freq-"):
            idx = int(btn_id.split("-")[-1])
            self._highlight_band = idx

        graph = self.query_one(DecayGraph)
        graph.set_highlight(self._highlight_band)
        self._sync_focus_buttons()

    @on(Button.Pressed, "#btn-export-mixer")
    def action_export(self):
        """Export the current mixer settings to a text file."""
        self.export_report()

    @on(Button.Pressed, "#btn-mixer-back")
    def action_main_menu(self):
        """Return to main menu."""
        if self._show_back_button:
            self.app.pop_screen()

    def _update_slider_display(self, idx: int, value: float) -> None:
        """Update the numeric display and bar for a slider."""
        value_label = self.query_one(f"#slider-value-{idx}", Label)
        value_label.update(f"{value:.2f}")

        input_field = self.query_one(f"#input-slider-{idx}", Input)
        input_field.value = f"{value:.2f}"

        bar_label = self.query_one(f"#slider-bar-{idx}", Label)
        bar_width = int(value * 20)
        bar_char = "█" * bar_width + "░" * (20 - bar_width)
        bar_label.update(bar_char)

    def _update_graph(self) -> None:
        """Update the decay graph with current absorption values."""
        graph = self.query_one(DecayGraph)
        graph.update_absorption(self._absorption_values)

    @on(Button.Pressed, "#btn-reset-sliders")
    def _reset_sliders(self):
        """Reset all sliders to 0.0 (fully reflective)."""
        if self._is_embedded:
            return
        self._absorption_values = [0.0] * 6
        self._current_material = ""
        self._suspend_material_sync = True
        self.query_one("#sel-material-preset", Select).value = ""
        self._suspend_material_sync = False
        self._apply_slider_values()

    @on(Button.Pressed, "#btn-flat-mid")
    def _flat_mid_sliders(self):
        """Set all sliders to 0.5 (medium absorption)."""
        if self._is_embedded:
            return
        self._absorption_values = [0.5] * 6
        self._current_material = ""
        self._suspend_material_sync = True
        self.query_one("#sel-material-preset", Select).value = ""
        self._suspend_material_sync = False
        self._apply_slider_values()

    def _apply_slider_values(self):
        """Apply current values to all slider widgets."""
        for idx, value in enumerate(self._absorption_values):
            self._update_slider_display(idx, value)
        self._update_graph()

    def export_report(self):
        """Export the mixer settings to a text file."""
        MIXER_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mixer_report_{timestamp}.txt"
        filepath = MIXER_REPORTS_DIR / filename

        sep = "=" * 64
        sep2 = "-" * 44

        lines = [
            sep,
            "  ACOUSTICA -- ACOUSTIC MIXER REPORT",
            f"  Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            sep,
            "",
            "ABSORPTION COEFFICIENTS",
            sep2,
        ]

        if self._current_material:
            lines.append(f"  Material Preset: {self._current_material}")
            lines.append("")

        lines.append("  Frequency  |  Absorption  |  RT60 (sec)")
        lines.append(sep2)

        for idx, (freq, label, alpha) in enumerate(zip(FREQ_BANDS, FREQ_LABELS, self._absorption_values)):
            min_rt60 = 0.2
            max_rt60 = 3.0
            rt60 = min_rt60 + (max_rt60 - min_rt60) * (1.0 - alpha)
            lines.append(f"  {freq:>5} Hz   |     {alpha:.2f}     |    {rt60:.2f}")

        lines.extend([
            "",
            "DECAY CURVE ANALYSIS",
            sep2,
            "  The graph shows sound level decay from 0 dB to -60 dB.",
            "  Higher absorption = faster decay (shorter reverb).",
            "  Lower absorption = slower decay (longer reverb).",
            "",
            sep,
            "  End of Mixer Report -- Acoustica",
            sep,
        ])

        try:
            filepath.write_text("\n".join(lines), encoding="utf-8")
            self.query_one("#export-status", Label).update(f"✓ Saved: {filename}")
            self.app.notify(f"Report saved: {filename}", severity="information", timeout=4)
        except OSError as e:
            self.query_one("#export-status", Label).update("✗ Error saving file")
            self.app.notify(f"Error: {e}", severity="error")


class AcousticMixerScreen(Screen):
    """Acoustic mixer screen with frequency sliders and decay visualization."""

    BINDINGS = [
        Binding("ctrl+m", "main_menu", "Main Menu"),
        Binding("ctrl+s", "export", "Export"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Horizontal(id="mixer-header"):
            yield Label("  ⊞  ACOUSTIC MIXER", id="mixer-header-title")
            yield Label("Real-time decay visualization", id="mixer-header-subtitle")
        yield AcousticMixerPanel(show_back_button=True)
        yield Footer()

    def action_export(self):
        panel = self.query_one(AcousticMixerPanel)
        panel.export_report()

    @on(Button.Pressed, "#btn-mixer-back")
    def action_main_menu(self):
        """Return to main menu."""
        self.app.pop_screen()


