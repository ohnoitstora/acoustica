# -*- coding: utf-8 -*-
"""Main menu screen for Acoustica."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Middle, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label


class MainMenuScreen(Screen):
    """Main menu screen shown on app start."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Middle():
            with Center():
                with Vertical(id="menu-container"):
                    yield Label("ACOUSTICA", id="menu-title")
                    yield Label("Acoustic Reverb & Room Mode Analyzer", id="menu-subtitle")
                    yield Label("", id="menu-spacer")
                    yield Button("▶  Start Analysis", id="btn-start", variant="primary")
                    yield Button("⊞  Acoustic Mixer", id="btn-mixer", variant="primary")
                    yield Button("🔧  Material Builder", id="btn-materials", variant="primary")
                    yield Button("📄  View Saved Reports", id="btn-reports", variant="primary")
                    yield Button("🧮  Treatment Calculator", id="btn-calculator", variant="primary")
                    yield Button("⏻  Exit", id="btn-exit", variant="primary")
                    yield Label("", id="menu-spacer-bottom")
                    yield Label("Press Q to quit", id="menu-hint")

    @on(Button.Pressed, "#btn-start")
    def start_analysis(self):
        self.app.push_screen("analyzer")

    @on(Button.Pressed, "#btn-materials")
    def open_material_builder(self):
        self.app.push_screen("material_builder")

    @on(Button.Pressed, "#btn-reports")
    def open_reports(self):
        self.app.push_screen("reports")

    @on(Button.Pressed, "#btn-calculator")
    def open_calculator(self):
        self.app.push_screen("calculator")

    @on(Button.Pressed, "#btn-mixer")
    def open_mixer(self):
        self.app.push_screen("mixer")

    @on(Button.Pressed, "#btn-exit")
    def exit_app(self):
        self.app.exit()
