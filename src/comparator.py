# -*- coding: utf-8 -*-
"""Room comparator screen for side-by-side acoustic analysis."""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Grid, Horizontal, Middle, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Select, Static

from .constants import FREQ_BANDS, FREQ_LABELS, MATERIALS
from .physics import (
    calculate_nrc,
    calculate_room_nrc,
    calculate_weighted_absorption,
    compute_axial_modes,
    compute_rt60_per_band,
    compute_schroeder_frequency,
    rt60_quality,
)

SNAPSHOTS_DIR = Path(__file__).resolve().parent.parent / "snapshots"


class RoomSnapshot:
    """Represents a saved room configuration with all acoustic data."""
    
    def __init__(
        self,
        name: str,
        width: float,
        length: float,
        height: float,
        wall_mat: str,
        floor_mat: str,
        ceil_mat: str,
        timestamp: str | None = None,
    ):
        self.name = name
        self.width = width
        self.length = length
        self.height = height
        self.wall_mat = wall_mat
        self.floor_mat = floor_mat
        self.ceil_mat = ceil_mat
        self.timestamp = timestamp or datetime.datetime.now().isoformat()
        
        # Computed values (calculated on init)
        self.rt60_vals: list[float] = []
        self.modes: dict[str, list[float]] = {}
        self.schroeder_freq: float = 0.0
        self.room_nrc: float = 0.0
        self.weighted_absorption: list[float] = []
        self._compute_values()
    
    def _compute_values(self):
        """Calculate all acoustic values for this room."""
        self.rt60_vals = compute_rt60_per_band(
            self.width, self.length, self.height,
            self.wall_mat, self.floor_mat, self.ceil_mat
        )
        self.modes = compute_axial_modes(self.width, self.length, self.height)
        volume = self.width * self.length * self.height
        self.schroeder_freq = compute_schroeder_frequency(self.rt60_vals, volume)
        self.room_nrc = calculate_room_nrc(
            self.width, self.length, self.height,
            self.wall_mat, self.floor_mat, self.ceil_mat,
            MATERIALS
        )
        self.weighted_absorption = calculate_weighted_absorption(
            self.width, self.length, self.height,
            self.wall_mat, self.floor_mat, self.ceil_mat,
            MATERIALS
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert snapshot to dictionary for serialization."""
        return {
            "name": self.name,
            "width": self.width,
            "length": self.length,
            "height": self.height,
            "wall_mat": self.wall_mat,
            "floor_mat": self.floor_mat,
            "ceil_mat": self.ceil_mat,
            "timestamp": self.timestamp,
            "rt60_vals": self.rt60_vals,
            "modes": self.modes,
            "schroeder_freq": self.schroeder_freq,
            "room_nrc": self.room_nrc,
            "weighted_absorption": self.weighted_absorption,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RoomSnapshot":
        """Create a snapshot from a dictionary."""
        snapshot = cls(
            name=data["name"],
            width=data["width"],
            length=data["length"],
            height=data["height"],
            wall_mat=data["wall_mat"],
            floor_mat=data["floor_mat"],
            ceil_mat=data["ceil_mat"],
            timestamp=data.get("timestamp"),
        )
        # Restore computed values if available
        if "rt60_vals" in data:
            snapshot.rt60_vals = data["rt60_vals"]
        if "modes" in data:
            snapshot.modes = data["modes"]
        if "schroeder_freq" in data:
            snapshot.schroeder_freq = data["schroeder_freq"]
        if "room_nrc" in data:
            snapshot.room_nrc = data["room_nrc"]
        if "weighted_absorption" in data:
            snapshot.weighted_absorption = data["weighted_absorption"]
        return snapshot
    
    @property
    def volume(self) -> float:
        return self.width * self.length * self.height
    
    @property
    def surface_area(self) -> float:
        return 2 * (self.length * self.height) + 2 * (self.width * self.height) + 2 * (self.width * self.length)
    
    @property
    def rt60_500(self) -> float:
        return self.rt60_vals[2] if len(self.rt60_vals) > 2 else 0.0


def save_snapshot(snapshot: RoomSnapshot) -> Path:
    """Save a room snapshot to disk."""
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Sanitize name for filename
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in snapshot.name)
    filename = f"{safe_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = SNAPSHOTS_DIR / filename
    
    with open(filepath, "w") as f:
        json.dump(snapshot.to_dict(), f, indent=2)
    
    return filepath


def load_snapshots() -> list[RoomSnapshot]:
    """Load all saved snapshots from disk."""
    snapshots = []
    if SNAPSHOTS_DIR.exists():
        for filepath in sorted(SNAPSHOTS_DIR.glob("*.json")):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    snapshots.append(RoomSnapshot.from_dict(data))
            except (json.JSONDecodeError, KeyError, IOError):
                continue
    return snapshots


def delete_snapshot(snapshot_name: str) -> bool:
    """Delete a snapshot by name."""
    if not SNAPSHOTS_DIR.exists():
        return False
    
    for filepath in SNAPSHOTS_DIR.glob("*.json"):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                if data.get("name") == snapshot_name:
                    filepath.unlink()
                    return True
        except (json.JSONDecodeError, IOError):
            continue
    return False


class RoomComparisonPanel(Static):
    """Panel displaying room data for comparison."""
    
    def __init__(self, snapshot: RoomSnapshot | None = None, is_left: bool = True):
        super().__init__()
        self.snapshot = snapshot
        self.is_left = is_left
        self.border_title = f"{'ROOM A' if is_left else 'ROOM B'}"
    
    def compose(self) -> ComposeResult:
        with Vertical(classes="comparison-room-panel"):
            yield Label("[ No room selected ]", classes="room-title")
            
            with Vertical(classes="room-details"):
                yield Label("Dimensions", classes="section-header")
                yield Label("Width:  --", classes="dim-line")
                yield Label("Length: --", classes="dim-line")
                yield Label("Height: --", classes="dim-line")
                yield Label("Volume: --", classes="dim-line")
                
                yield Label("Materials", classes="section-header")
                yield Label("Walls:  --", classes="mat-line")
                yield Label("Floor:  --", classes="mat-line")
                yield Label("Ceiling: --", classes="mat-line")
                yield Label("Room NRC: --", classes="nrc-line")
                
                yield Label("Acoustic Analysis", classes="section-header")
                yield Label("RT60 @ 500Hz: --", classes="rt60-line")
                yield Label("Quality: --", classes="quality-line")
                yield Label("Schroeder Freq: --", classes="schroeder-line")
                
                yield Label("Axial Modes", classes="section-header")
                yield Label("Length: --", classes="mode-line")
                yield Label("Width:  --", classes="mode-line")
                yield Label("Height: --", classes="mode-line")
                
                yield Label("RT60 Per Band", classes="section-header")
                with Grid(classes="rt60-grid"):
                    for freq in FREQ_LABELS:
                        yield Label(f"{freq}", classes="freq-label")
                    for _ in range(6):
                        yield Label("--", classes="rt60-value")
    
    def update_snapshot(self, snapshot: RoomSnapshot | None):
        """Update the panel with new snapshot data."""
        self.snapshot = snapshot
        self._refresh_display()
    
    def _refresh_display(self):
        """Refresh all displayed values."""
        if not self.snapshot:
            return
        
        snap = self.snapshot
        
        # Update title
        title = self.query_one(".room-title", Label)
        title.update(f"📐 {snap.name}")
        
        # Update dimensions
        dims = self.query(".dim-line")
        dims[0].update(f"Width:  {snap.width:.2f} m")
        dims[1].update(f"Length: {snap.length:.2f} m")
        dims[2].update(f"Height: {snap.height:.2f} m")
        dims[3].update(f"Volume: {snap.volume:.2f} m³")
        
        # Update materials
        mats = self.query(".mat-line")
        mats[0].update(f"Walls:  {snap.wall_mat}")
        mats[1].update(f"Floor:  {snap.floor_mat}")
        mats[2].update(f"Ceiling: {snap.ceil_mat}")
        
        # Update NRC
        nrc_line = self.query_one(".nrc-line", Label)
        nrc_line.update(f"Room NRC: {snap.room_nrc:.2f}")
        
        # Update acoustic analysis
        rt60_line = self.query_one(".rt60-line", Label)
        rt60_line.update(f"RT60 @ 500Hz: {snap.rt60_500:.3f} s")
        
        quality_line = self.query_one(".quality-line", Label)
        quality_line.update(f"Quality: {rt60_quality(snap.rt60_500)}")
        
        schroeder_line = self.query_one(".schroeder-line", Label)
        schroeder_line.update(f"Schroeder Freq: {snap.schroeder_freq:.1f} Hz")
        
        # Update modes
        mode_lines = self.query(".mode-line")
        for i, dim in enumerate(["Length", "Width", "Height"]):
            freqs = snap.modes.get(dim, [])
            freq_str = "  ".join(f"{f:.0f}Hz" for f in freqs) if freqs else "---"
            mode_lines[i].update(f"{dim}: {freq_str}")
        
        # Update RT60 grid
        rt60_values = self.query(".rt60-value")
        for i, val in enumerate(snap.rt60_vals):
            if i < len(rt60_values):
                rt60_values[i].update(f"{val:.3f}")


class RoomComparatorScreen(Screen):
    """Screen for comparing two rooms side-by-side."""
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "app.pop_screen", "Back"),
    ]
    
    def __init__(self):
        super().__init__()
        self._snapshots: list[RoomSnapshot] = []
        self._left_snapshot: RoomSnapshot | None = None
        self._right_snapshot: RoomSnapshot | None = None
    
    def compose(self) -> ComposeResult:
        with Middle():
            with Center():
                with Vertical(id="comparator-container"):
                    yield Label("🔍 ROOM COMPARATOR", id="comparator-title")
                    yield Label("Compare two room configurations side-by-side", id="comparator-subtitle")
                    
                    # Snapshot selection
                    with Horizontal(id="snapshot-selection"):
                        with Vertical(classes="snapshot-col"):
                            yield Label("Room A", classes="snapshot-label")
                            yield Select([], id="select-left", prompt="Select room...")
                        with Vertical(classes="snapshot-col"):
                            yield Label("Room B", classes="snapshot-label")
                            yield Select([], id="select-right", prompt="Select room...")
                    
                    # Comparison panels
                    with Horizontal(id="comparison-panels"):
                        self._left_panel = RoomComparisonPanel(is_left=True)
                        self._right_panel = RoomComparisonPanel(is_left=False)
                        yield self._left_panel
                        yield self._right_panel
                    
                    # Action buttons
                    with Horizontal(id="comparator-buttons"):
                        yield Button("← Back", id="btn-back", variant="primary")
                        yield Button("🔄 Refresh", id="btn-refresh", variant="primary")
                        yield Button("📊 Compare Math", id="btn-compare", variant="success")
    
    def on_mount(self):
        self._load_snapshots()
    
    def _load_snapshots(self):
        """Load available snapshots and update dropdowns."""
        self._snapshots = load_snapshots()
        
        options = [(s.name, s.name) for s in self._snapshots]
        
        left_select = self.query_one("#select-left", Select)
        right_select = self.query_one("#select-right", Select)
        
        left_select._options = options
        right_select._options = options
        
        left_select.refresh()
        right_select.refresh()
    
    @on(Select.Changed, "#select-left")
    def on_left_selected(self, event: Select.Changed):
        """Handle left room selection."""
        if event.value == Select.BLANK:
            self._left_snapshot = None
        else:
            name = str(event.value)
            self._left_snapshot = next((s for s in self._snapshots if s.name == name), None)
        self._left_panel.update_snapshot(self._left_snapshot)
    
    @on(Select.Changed, "#select-right")
    def on_right_selected(self, event: Select.Changed):
        """Handle right room selection."""
        if event.value == Select.BLANK:
            self._right_snapshot = None
        else:
            name = str(event.value)
            self._right_snapshot = next((s for s in self._snapshots if s.name == name), None)
        self._right_panel.update_snapshot(self._right_snapshot)
    
    @on(Button.Pressed, "#btn-back")
    def go_back(self):
        self.app.pop_screen()
    
    @on(Button.Pressed, "#btn-refresh")
    def refresh_snapshots(self):
        self._load_snapshots()
        self.app.notify("Snapshots refreshed")
    
    @on(Button.Pressed, "#btn-compare")
    def show_comparison_math(self):
        """Show detailed mathematical comparison between rooms."""
        if not self._left_snapshot or not self._right_snapshot:
            self.app.notify("Please select both rooms to compare", severity="warning")
            return
        
        left = self._left_snapshot
        right = self._right_snapshot
        
        # Calculate differences
        rt60_diff = right.rt60_500 - left.rt60_500
        nrc_diff = right.room_nrc - left.room_nrc
        schroeder_diff = right.schroeder_freq - left.schroeder_freq
        vol_diff = right.volume - left.volume
        
        # Build comparison text
        lines = [
            "📊 ROOM COMPARISON ANALYSIS",
            "",
            f"Room A: {left.name}",
            f"Room B: {right.name}",
            "",
            "─" * 50,
            "KEY DIFFERENCES",
            "─" * 50,
            f"Volume:        {vol_diff:+.2f} m³  ({vol_diff/left.volume*100:+.1f}%)",
            f"RT60 @ 500Hz:  {rt60_diff:+.3f} s  ({rt60_diff/left.rt60_500*100:+.1f}%)",
            f"Room NRC:      {nrc_diff:+.2f}",
            f"Schroeder Freq: {schroeder_diff:+.1f} Hz",
            "",
            "─" * 50,
            "RT60 COMPARISON BY BAND",
            "─" * 50,
            "Freq    Room A    Room B    Diff",
        ]
        
        for i, freq in enumerate(FREQ_BANDS):
            a_val = left.rt60_vals[i] if i < len(left.rt60_vals) else 0
            b_val = right.rt60_vals[i] if i < len(right.rt60_vals) else 0
            diff = b_val - a_val
            lines.append(f"{freq:>4}Hz   {a_val:.3f}s   {b_val:.3f}s   {diff:+.3f}s")
        
        lines.extend([
            "",
            "─" * 50,
            "INTERPRETATION",
            "─" * 50,
        ])
        
        # Add interpretation
        if rt60_diff > 0.1:
            lines.append("• Room B is more reverberant (longer RT60)")
        elif rt60_diff < -0.1:
            lines.append("• Room B is more damped (shorter RT60)")
        else:
            lines.append("• Similar reverberation characteristics")
        
        if nrc_diff > 0.05:
            lines.append("• Room B has better overall absorption (higher NRC)")
        elif nrc_diff < -0.05:
            lines.append("• Room B has less overall absorption (lower NRC)")
        
        if schroeder_diff > 50:
            lines.append("• Room B transitions to diffuse field at higher frequency")
        elif schroeder_diff < -50:
            lines.append("• Room B transitions to diffuse field at lower frequency")
        
        self.app.notify("\n".join(lines), timeout=10)


class SaveSnapshotModal(Screen):
    """Modal for saving current room as a snapshot."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Cancel"),
    ]
    
    def __init__(self, width: float, length: float, height: float,
                 wall_mat: str, floor_mat: str, ceil_mat: str):
        super().__init__()
        self.width = width
        self.length = length
        self.height = height
        self.wall_mat = wall_mat
        self.floor_mat = floor_mat
        self.ceil_mat = ceil_mat
    
    def compose(self) -> ComposeResult:
        with Middle():
            with Center():
                with Vertical(id="save-snapshot-modal"):
                    yield Label("💾 Save Room Snapshot", id="snapshot-modal-title")
                    yield Label("Enter a name for this room configuration:", classes="modal-hint")
                    
                    yield Input(placeholder="Room name...", id="snapshot-name")
                    
                    with Horizontal(classes="snapshot-preview"):
                        yield Label(f"Dimensions: {self.width:.2f} × {self.length:.2f} × {self.height:.2f} m")
                    
                    with Horizontal(id="snapshot-buttons"):
                        yield Button("Cancel", id="btn-cancel", variant="default")
                        yield Button("Save", id="btn-save", variant="success")
    
    @on(Button.Pressed, "#btn-cancel")
    def cancel(self):
        self.app.pop_screen()
    
    @on(Button.Pressed, "#btn-save")
    def save(self):
        name_input = self.query_one("#snapshot-name", Input)
        name = name_input.value.strip()
        
        if not name:
            self.app.notify("Please enter a name", severity="error")
            return
        
        snapshot = RoomSnapshot(
            name=name,
            width=self.width,
            length=self.length,
            height=self.height,
            wall_mat=self.wall_mat,
            floor_mat=self.floor_mat,
            ceil_mat=self.ceil_mat,
        )
        
        try:
            filepath = save_snapshot(snapshot)
            self.app.notify(f"✓ Saved snapshot: {filepath.name}")
            self.app.pop_screen()
        except Exception as e:
            self.app.notify(f"❌ Error saving: {e}", severity="error")