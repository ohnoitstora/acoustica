# -*- coding: utf-8 -*-
"""Main Textual application entrypoint for Acoustica."""

from __future__ import annotations

from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Input, Label, Select

from .calculator import TreatmentCalculatorScreen
from .constants import MATERIAL_NAMES, MATERIALS
from .export_report import export_report, REPORTS_DIR
from .material_builder import MaterialBuilderScreen
from .menu import MainMenuScreen
from .mixer import AcousticMixerPanel, AcousticMixerScreen
from .modal import HowItWorksModal, ListenModal
from .physics import rt60_quality
from .reports import ReportsScreen
from .state import AcousticState
from .ui_components import BarChart, RoomCanvas

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
CSS_PATH = ASSETS_DIR / "app.css"


class AnalyzerScreen(Screen):
    """The main acoustic analyzer screen."""

    BINDINGS = [
        Binding("ctrl+e", "export", "Export Report"),
        Binding("ctrl+r", "reset", "Reset"),
        Binding("ctrl+h", "how_it_works", "How It Works"),
        Binding("ctrl+m", "main_menu", "Main Menu"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, state: AcousticState):
        super().__init__()
        self._state = state

    def compose(self) -> ComposeResult:
        with Horizontal(id="header"):
            yield Label("  ACOUSTICA -- REVERB & ROOM MODE ANALYZER", id="header-title")
            yield Label("Sabine  Axial Modes  RT60", id="header-subtitle")
            yield Button("? How It Works", id="btn-how", classes="hdr-btn")
            yield Button("~ Reset", id="btn-reset", classes="hdr-btn")
            yield Button("v Export", id="btn-export", classes="hdr-btn")
            yield Button("♫ Listen", id="btn-listen", classes="hdr-btn")
        with Horizontal(id="body"):
            with Vertical(id="left-panel") as left:
                left.border_title = "ROOM SETTINGS"
                yield Label("VIEW", classes="section-title")
                yield Select(
                    [
                        ("Room View", "room"),
                        ("Pressure Map", "map"),
                        ("Acoustic Mixer", "mixer"),
                    ],
                    value=self._state.view_mode,
                    id="sel-view-mode",
                )
                with Container(id="map-controls"):
                    yield Label("MAP MODE", classes="section-title")
                    yield Select(
                        [
                            ("Length Mode 1", "length-1"),
                            ("Width Mode 1", "width-1"),
                            ("Height Mode 1", "height-1"),
                        ],
                        value=self._state.map_mode,
                        id="sel-map-mode",
                    )
                yield Label("DIMENSIONS (m)", classes="section-title")
                for name, val, id_ in [
                    ("Width", self._state.width, "inp-width"),
                    ("Length", self._state.length, "inp-length"),
                    ("Height", self._state.height, "inp-height"),
                ]:
                    with Horizontal(classes="dim-row"):
                        yield Label("{}:".format(name), classes="dim-label")
                        yield Button("-", id="dec-{}".format(id_), classes="dim-btn")
                        yield Input(str(val), id=id_, classes="dim-input", restrict=r"[0-9.]*")
                        yield Button("+", id="inc-{}".format(id_), classes="dim-btn")
                yield Label("MATERIALS", classes="section-title")
                for name, var, id_ in [
                    ("Walls", self._state.wall_mat, "sel-wall"),
                    ("Floor", self._state.floor_mat, "sel-floor"),
                    ("Ceiling", self._state.ceil_mat, "sel-ceil"),
                ]:
                    with Horizontal(classes="mat-row"):
                        yield Label("{}:".format(name), classes="mat-label")
                        yield Select([(m, m) for m in MATERIAL_NAMES], value=var, id=id_)
                yield Label("GEOMETRY", classes="section-title")
                with Container(classes="geo-box"):
                    yield Label("", id="lbl-vol", classes="geo-label")
                    yield Label("", id="lbl-area", classes="geo-label")
            with Vertical(id="center-panel") as center:
                center.border_title = "ROOM CANVAS -- Top-Down View"
                yield Label("Left-click: place source  |  Right-click: clear", id="canvas-hint")
                yield RoomCanvas(self._state)
                yield Label("", id="map-mode-label")
                yield Label("no source -- click inside room to place", id="source-coord")
                yield AcousticMixerPanel(show_back_button=False, embedded=True)
            with Vertical(id="right-panel") as right:
                right.border_title = "ANALYSIS RESULTS"
                yield Label("RT60  (Sabine)", classes="section-title")
                yield Label("RT60 = 0.161 * V / sum(S*alpha)", classes="geo-label")
                yield Label("", id="rt60-value")
                yield Label("", id="rt60-quality")
                yield Label("AXIAL ROOM MODES", classes="section-title")
                yield Label("fn = (n * 343) / (2 * L)", classes="geo-label")
                for dim in ("Length", "Width", "Height"):
                    with Horizontal(classes="mode-row"):
                        yield Label("{}:".format(dim[0]), classes="mode-dim-label {}".format(dim))
                        yield Label("---", id="mode-{}".format(dim.lower()), classes="mode-freqs")
                yield Label("RT60 PER OCTAVE BAND", classes="section-title")
                yield BarChart(self._state)
        yield Footer()

    def on_mount(self):
        self._refresh_results()

    def _update_map_controls(self):
        controls = self.query_one("#map-controls", Container)
        controls.display = self._state.view_mode == "map"

    def _update_view_panels(self):
        view_mode = self._state.view_mode
        map_label = self.query_one("#map-mode-label", Label)
        map_label.display = view_mode == "map"
        canvas_hint = self.query_one("#canvas-hint", Label)
        canvas_hint.display = view_mode == "room"
        source_label = self.query_one("#source-coord", Label)
        source_label.display = view_mode == "room"
        room_canvas = self.query_one(RoomCanvas)
        room_canvas.display = view_mode in ("room", "map")
        mixer_panel = self.query_one(AcousticMixerPanel)
        mixer_panel.display = view_mode == "mixer"
        center_panel = self.query_one("#center-panel", Vertical)
        if view_mode == "mixer":
            center_panel.border_title = "ACOUSTIC MIXER"
        elif view_mode == "map":
            center_panel.border_title = "PRESSURE MAP"
        else:
            center_panel.border_title = "ROOM CANVAS -- Top-Down View"

    @on(Input.Submitted)
    @on(Input.Changed)
    def _on_input(self, event):
        id_ = event.input.id
        try:
            val = float(event.value)
        except (ValueError, TypeError):
            return
        if val < 0.1:
            return
        if id_ == "inp-width":
            self._state.width = val
        elif id_ == "inp-length":
            self._state.length = val
        elif id_ == "inp-height":
            self._state.height = val
        else:
            return
        self._recompute_and_refresh()

    @on(Select.Changed)
    def _on_select(self, event):
        if event.value == Select.BLANK:
            return
        id_ = event.select.id
        val = str(event.value)
        if id_ == "sel-wall":
            self._state.wall_mat = val
        elif id_ == "sel-floor":
            self._state.floor_mat = val
        elif id_ == "sel-ceil":
            self._state.ceil_mat = val
        elif id_ == "sel-view-mode":
            self._state.view_mode = val
        elif id_ == "sel-map-mode":
            self._state.map_mode = val
        self._recompute_and_refresh()

    @on(Button.Pressed, ".dim-btn")
    def _on_dim_btn(self, event):
        btn_id = event.button.id or ""
        if btn_id.startswith("inc-"):
            inp_id, delta = btn_id[4:], +0.5
        elif btn_id.startswith("dec-"):
            inp_id, delta = btn_id[4:], -0.5
        else:
            return
        inp = self.query_one("#{}".format(inp_id), Input)
        try:
            cur = float(inp.value)
        except ValueError:
            cur = 1.0
        new_val = max(0.5, cur + delta)
        inp.value = "{:.1f}".format(new_val)
        if inp_id == "inp-width":
            self._state.width = new_val
        elif inp_id == "inp-length":
            self._state.length = new_val
        elif inp_id == "inp-height":
            self._state.height = new_val
        self._recompute_and_refresh()

    @on(Button.Pressed, "#btn-how")
    def action_how_it_works(self):
        self.app.push_screen(HowItWorksModal())

    @on(Button.Pressed, "#btn-reset")
    def action_reset(self):
        self._do_reset()

    @on(Button.Pressed, "#btn-export")
    def action_export(self):
        self._do_export()

    @on(Button.Pressed, "#btn-listen")
    def action_listen(self):
        self._do_listen()

    def action_main_menu(self):
        self.app.pop_screen()

    def _recompute_and_refresh(self):
        self._state.recompute()
        self._refresh_results()

    def _refresh_results(self):
        state = self._state
        self._update_map_controls()
        self._update_view_panels()
        self.query_one("#lbl-vol", Label).update("Volume:  {:.2f} m3".format(state.volume))
        self.query_one("#lbl-area", Label).update("Area:    {:.2f} m2".format(state.surface_area))
        rt500 = state.rt60_500
        self.query_one("#rt60-value", Label).update("RT60 @ 500 Hz  =  {:.3f} s".format(rt500))
        self.query_one("#rt60-quality", Label).update(rt60_quality(rt500) if rt500 > 0 else "--")
        for dim in ("Length", "Width", "Height"):
            freqs = state.modes.get(dim, [])
            txt = "  ".join("{:.0f}Hz".format(f) for f in freqs) if freqs else "---"
            self.query_one("#mode-{}".format(dim.lower()), Label).update(txt)
        self.query_one(BarChart).refresh()
        room_canvas = self.query_one(RoomCanvas)
        room_canvas.refresh()
        self.query_one("#source-coord", Label).update(room_canvas.source_info)
        map_label = self.query_one("#map-mode-label", Label)
        if state.view_mode == "map":
            map_label.update("Map mode: {}".format(state.map_mode.replace("-", " ")))
        else:
            map_label.update("")
        if state.view_mode == "mixer":
            absorption_values = self._compute_mixer_absorption()
            mixer_panel = self.query_one(AcousticMixerPanel)
            mixer_panel.set_absorption_values(absorption_values)

    def _compute_mixer_absorption(self) -> list[float]:
        state = self._state
        width, length, height = state.width, state.length, state.height
        wall_area = 2.0 * length * height + 2.0 * width * height
        floor_area = width * length
        ceiling_area = width * length
        total_area = wall_area + floor_area + ceiling_area
        if total_area <= 0:
            return [0.0] * 6
        wall_absorption = MATERIALS.get(state.wall_mat, [0.0] * 6)
        floor_absorption = MATERIALS.get(state.floor_mat, [0.0] * 6)
        ceiling_absorption = MATERIALS.get(state.ceil_mat, [0.0] * 6)
        absorption_values = []
        for idx in range(6):
            weighted = (
                wall_area * wall_absorption[idx]
                + floor_area * floor_absorption[idx]
                + ceiling_area * ceiling_absorption[idx]
            )
            absorption_values.append(weighted / total_area)
        return absorption_values

    def _do_reset(self):
        self._state.width = 6.0
        self._state.length = 9.0
        self._state.height = 3.0
        self._state.wall_mat = "Gypsum Board"
        self._state.floor_mat = "Carpet (Thick)"
        self._state.ceil_mat = "Gypsum Board"
        self._state.source = None
        self._state.view_mode = "room"
        self._state.map_mode = "length-1"
        self.query_one("#inp-width", Input).value = "6.0"
        self.query_one("#inp-length", Input).value = "9.0"
        self.query_one("#inp-height", Input).value = "3.0"
        self.query_one("#sel-wall", Select).value = "Gypsum Board"
        self.query_one("#sel-floor", Select).value = "Carpet (Thick)"
        self.query_one("#sel-ceil", Select).value = "Gypsum Board"
        self.query_one("#sel-view-mode", Select).value = "room"
        self.query_one("#sel-map-mode", Select).value = "length-1"
        canvas = self.query_one(RoomCanvas)
        canvas.source_info = "no source -- click inside room to place"
        self._recompute_and_refresh()

    def _do_export(self):
        export_report(self._state, self.app.notify)

    def _do_listen(self):
        """Open the Listen modal for audio comparison."""
        self.app.push_screen(ListenModal(self._state, REPORTS_DIR))


class AcousticaApp(App):
    TITLE = "Acoustica"
    CSS_PATH = CSS_PATH
    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self._state = AcousticState()
        self._state.recompute()

    def on_mount(self):
        self.install_screen(MainMenuScreen(), name="menu")
        self.install_screen(AnalyzerScreen(self._state), name="analyzer")
        self.install_screen(MaterialBuilderScreen(), name="material_builder")
        self.install_screen(ReportsScreen(), name="reports")
        self.install_screen(TreatmentCalculatorScreen(), name="calculator")
        self.install_screen(AcousticMixerScreen(), name="mixer")
        self.push_screen("menu")


def run():
    app = AcousticaApp()
    app.run()


if __name__ == "__main__":
    run()
