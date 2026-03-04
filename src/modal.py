# -*- coding: utf-8 -*-
"""Modal screens for the Acoustica TUI."""

from __future__ import annotations

import datetime
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

from .audio_engine import generate_room_audio, save_audio_pair, save_wav
from .constants import FREQ_BANDS
from .export_report import export_report

HOW_IT_WORKS_TEXT = """
================================================================
 1.  RT60  --  Reverberation Time  (Sabine Formula)
================================================================

RT60 = time (seconds) for sound energy to decay 60 dB.

  Formula:  RT60 = (0.161 * V) / sum(Si * alphai)

  V      = room volume [m3]
  Si     = surface area of boundary i [m2]
  alphai = absorption coeff (0 = reflective, 1 = absorptive)
  0.161  = Sabine metric constant

  Typical targets:
    Recording studio:  0.3 - 0.5 s    Home theater: 0.4 - 0.6 s
    Conference room:   0.6 - 0.8 s    Concert hall: 1.5 - 2.5 s

================================================================
 2.  Axial Room Modes  (Standing Waves / "Room Boom")
================================================================

Sound bouncing between parallel walls creates standing waves.

  Formula:  fn = (n * c) / (2 * L)

  n = 1, 2, 3 ...  harmonic number
  c = 343 m/s      speed of sound at 20 degC
  L = room dimension (Width / Length / Height)

  Example -- 6 m wide room:
    f1 = 343 / (2*6) = 28.6 Hz (fundamental)
    f2 = 57.2 Hz    f3 = 85.8 Hz

================================================================
 3.  Material Absorption Coefficients
================================================================

  Concrete (Bare)  -- nearly fully reflective
  Gypsum Board     -- absorptive mainly at low frequencies
  Carpet (Thick)   -- strong absorption above 500 Hz
  Acoustic Foam    -- highly effective above 250 Hz (a~0.9+)
  Hardwood Floor   -- moderate absorption, low-mid freqs
  Glass (Window)   -- mostly reflective across all bands
  Brick (Painted)  -- low absorption
  Heavy Curtain    -- good broad-band absorber, mid/high

================================================================
 4.  Controls
================================================================

  Left-click  inside room  -> Add source (max 8)
  Right-click              -> Remove nearest source
  [+ Add Source]           -> Quick-place at room centre
  [~ Reset]                -> Clear all + restore defaults
  Ctrl+E                   -> Export .txt report
  Ctrl+H                   -> This screen
  Ctrl+M                   -> Back to main menu
  Main Menu                -> Start analysis / saved reports
  Saved Reports            -> Browse exported reports
  Q                        -> Quit

================================================================
"""


class HowItWorksModal(ModalScreen):
    DEFAULT_CSS = """
    HowItWorksModal {
        align: center middle;
    }
    HowItWorksModal > Container {
        width: 68;
        height: 90%;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    HowItWorksModal > Container > Label#title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    HowItWorksModal > Container > ScrollableContainer {
        height: 1fr;
    }
    HowItWorksModal > Container > Button {
        margin-top: 1;
        width: 14;
    }
    """
    BINDINGS = [Binding("escape", "dismiss", "Close")]

    def compose(self) -> ComposeResult:
        with Container():
            yield Label("  ACOUSTIC PHYSICS EXPLAINED", id="title")
            with ScrollableContainer():
                yield Static(HOW_IT_WORKS_TEXT)
            yield Button("X  Close", variant="primary", id="close_btn")

    @on(Button.Pressed, "#close_btn")
    def close(self):
        self.dismiss()


class ListenModal(ModalScreen):
    """Modal for listening to and comparing room audio."""

    DEFAULT_CSS = """
    ListenModal {
        align: center middle;
    }
    ListenModal > Container {
        width: 70;
        height: 28;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    ListenModal > Container > Label#title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    ListenModal > Container > Vertical {
        height: 1fr;
    }
    ListenModal > Container > Horizontal {
        margin-top: 1;
    }
    ListenModal .rt60-row {
        height: 1;
    }
    ListenModal .rt60-label {
        width: 12;
    }
    ListenModal .rt60-value {
        width: 8;
        color: $accent;
    }
    ListenModal .section-title {
        text-style: bold;
        margin-top: 1;
        margin-bottom: 1;
    }
    ListenModal .info-label {
        color: $text-muted;
        margin-bottom: 1;
    }
    ListenModal > Container > Horizontal > Button {
        margin-right: 1;
    }
    """
    BINDINGS = [Binding("escape", "dismiss", "Close")]

    def __init__(self, state, reports_dir: Path):
        super().__init__()
        self._state = state
        self._reports_dir = reports_dir  # Base reports directory
        self._dry_signal = None
        self._wet_signal = None
        self._ir = None
        self._export_name = None

    def compose(self) -> ComposeResult:
        with Container():
            yield Label("♫  ROOM AUDIO COMPARISON", id="title")
            with Vertical():
                yield Label("", id="info-label")
                yield Label("RT60 VALUES (Reverberation Time)", classes="section-title")
                with Vertical(id="rt60-container"):
                    for i, freq in enumerate(FREQ_BANDS):
                        with Horizontal(classes="rt60-row"):
                            yield Label(f"{freq:>5} Hz:", classes="rt60-label")
                            yield Label(f"{self._state.rt60_vals[i]:.3f} s", classes="rt60-value", id=f"rt60-{freq}")
                yield Label("", classes="section-title")
                yield Label("Generated Audio Files:", classes="section-title")
                yield Label("  • dry.wav: Original 440 Hz sine wave", classes="info-label")
                yield Label("  • reverb.wav: Same tone with room reverb applied", classes="info-label")
                yield Label("", id="status-label")
            with Horizontal():
                yield Button("Export Report + Audio", id="btn-export", variant="primary")
                yield Button("Close", id="btn-close", variant="default")

    def on_mount(self):
        # Generate audio
        self._generate_audio()
        self._update_status("Audio generated. Click Export to save.")

    def _generate_audio(self):
        """Generate dry and wet audio signals."""
        rt60_values = self._state.rt60_vals
        self._dry_signal, self._wet_signal, self._ir = generate_room_audio(
            rt60_values, frequency=440.0, duration=1.0, volume=0.5
        )
        self._export_name = f"room_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def _update_status(self, message: str):
        try:
            status_label = self.query_one("#status-label", Label)
            status_label.update(message)
        except Exception:
            pass

    @on(Button.Pressed, "#btn-export")
    def export_all(self):
        """Export both report and audio files to a dedicated folder."""
        try:
            # Create export directory: reports/{export_name}/
            export_dir = self._reports_dir / self._export_name
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Save audio files
            if self._dry_signal is not None and self._wet_signal is not None:
                dry_path, wet_path = save_audio_pair(
                    self._dry_signal,
                    self._wet_signal,
                    export_dir
                )
                
                if dry_path and wet_path:
                    # Export the report to the same directory
                    report_path = export_report(
                        self._state, 
                        self._update_status,
                        output_path=export_dir,
                        base_name="report"
                    )
                    
                    if report_path:
                        self._update_status(f"✓ Exported to: reports/{self._export_name}/")
                    else:
                        self._update_status("✗ Failed to save report")
                else:
                    self._update_status("✗ Failed to save audio files")
            else:
                self._update_status("✗ No audio generated")
        except Exception as e:
            self._update_status(f"✗ Export error: {e}")

    @on(Button.Pressed, "#btn-close")
    def close(self):
        self.dismiss()
