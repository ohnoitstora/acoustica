# -*- coding: utf-8 -*-
"""Material Database Browser screen for Acoustica."""

from __future__ import annotations

import datetime
import json
from pathlib import Path

from rich.style import Style
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, Center, Middle
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Select, Static

from .constants import FREQ_BANDS, FREQ_LABELS, BAR_COLOURS, BLOCK

CUSTOM_MATERIALS_PATH = Path(__file__).resolve().parent.parent / "custom_materials.json"
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports" / "material_comparison"


class MaterialComparisonBars(Widget):
    """Widget that displays absorption coefficients as horizontal bars for comparison."""
    
    DEFAULT_CSS = """
    MaterialComparisonBars {
        height: 12;
        padding: 0 1;
    }
    """
    
    def __init__(self, material_a: dict | None = None, material_b: dict | None = None):
        super().__init__()
        self._material_a = material_a
        self._material_b = material_b
    
    def update_materials(self, material_a: dict | None, material_b: dict | None):
        """Update the materials to compare."""
        self._material_a = material_a
        self._material_b = material_b
        self.refresh()
    
    def _get_coeffs(self, material: dict | None) -> list[float]:
        """Extract coefficients from material dict."""
        if not material:
            return [0.0] * 6
        coeffs = material.get("absorption_coefficients", {})
        return [
            coeffs.get("125Hz", 0.0),
            coeffs.get("250Hz", 0.0),
            coeffs.get("500Hz", 0.0),
            coeffs.get("1000Hz", 0.0),
            coeffs.get("2000Hz", 0.0),
            coeffs.get("4000Hz", 0.0),
        ]
    
    def render(self) -> Text:
        width = max(self.size.width - 2, 20)
        height = max(self.size.height - 2, 8)
        
        coeffs_a = self._get_coeffs(self._material_a)
        coeffs_b = self._get_coeffs(self._material_b)
        
        name_a = self._material_a.get("name", "Material A") if self._material_a else "Material A"
        name_b = self._material_b.get("name", "Material B") if self._material_b else "Material B"
        
        out = Text()
        
        # Header
        out.append("ABSORPTION COMPARISON\n", style=Style.parse("bold gold1"))
        out.append(f"A: {name_a[:20]}\n", style=Style.parse("cyan"))
        out.append(f"B: {name_b[:20]}\n", style=Style.parse("magenta"))
        out.append("─" * (width - 4) + "\n", style=Style.parse("dim white"))
        
        # Bar width for each material
        bar_width = (width - 12) // 2
        
        for i, freq in enumerate(FREQ_BANDS):
            val_a = coeffs_a[i]
            val_b = coeffs_b[i]
            
            # Frequency label
            freq_str = f"{freq:>4}Hz "
            out.append(freq_str, style=Style.parse("dim white"))
            
            # Material A bar
            filled_a = int(val_a * bar_width)
            empty_a = bar_width - filled_a
            out.append("█" * filled_a, style=Style.parse("cyan"))
            out.append("░" * empty_a, style=Style.parse("dim cyan"))
            
            # Material B bar
            filled_b = int(val_b * bar_width)
            empty_b = bar_width - filled_b
            out.append(" ", style=Style.parse(""))
            out.append("█" * filled_b, style=Style.parse("magenta"))
            out.append("░" * empty_b, style=Style.parse("dim magenta"))
            
            # Values
            out.append(f" {val_a:.2f}/{val_b:.2f}\n", style=Style.parse("white"))
        
        return out


class MaterialListItem(Static):
    """A single material item in the list."""
    
    def __init__(self, material: dict, index: int):
        super().__init__()
        self.material = material
        self.index = index
        self._is_selected = False
        self._is_locked_b = False
    
    def set_selected(self, selected: bool):
        self._is_selected = selected
        self.refresh()
    
    def set_locked_b(self, locked: bool):
        self._is_locked_b = locked
        self.refresh()
    
    def render(self) -> Text:
        name = self.material.get("name", "Unknown")
        coeffs = self.material.get("absorption_coefficients", {})
        
        # Build the display line
        out = Text()
        
        # Selection indicator
        if self._is_selected:
            out.append("▶ ", style=Style.parse("bold yellow"))
        else:
            out.append("  ", style=Style.parse(""))
        
        # Lock indicator
        if self._is_locked_b:
            out.append("🔒 ", style=Style.parse("bold magenta"))
        else:
            out.append("   ", style=Style.parse(""))
        
        # Material name (truncated)
        display_name = name[:25].ljust(25)
        if self._is_selected:
            out.append(display_name, style=Style.parse("bold white"))
        else:
            out.append(display_name, style=Style.parse("white"))
        
        # Coefficient values
        out.append(" ", style=Style.parse(""))
        for i, freq in enumerate(FREQ_BANDS):
            val = coeffs.get(f"{freq}Hz", 0.0)
            color = BAR_COLOURS[i] if i < len(BAR_COLOURS) else "white"
            out.append(f"{val:>4.2f} ", style=Style.parse(color))
        
        return out


class MaterialListWidget(Widget):
    """Scrollable list of materials."""
    
    DEFAULT_CSS = """
    MaterialListWidget {
        height: 1fr;
        overflow-y: scroll;
        background: $surface;
        border: solid $accent;
    }
    """
    
    def __init__(self, materials: list[dict]):
        super().__init__()
        self._materials = materials
        self._filtered_materials = materials.copy()
        self._selected_index = 0
        self._locked_index: int | None = None
    
    def set_materials(self, materials: list[dict]):
        """Set the materials list."""
        self._materials = materials
        self._filtered_materials = materials.copy()
        self._selected_index = min(self._selected_index, len(self._filtered_materials) - 1) if self._filtered_materials else 0
        self.refresh()
    
    def filter_materials(self, search_term: str):
        """Filter materials by search term."""
        if not search_term:
            self._filtered_materials = self._materials.copy()
        else:
            search_lower = search_term.lower()
            self._filtered_materials = [
                m for m in self._materials
                if search_lower in m.get("name", "").lower()
            ]
        self._selected_index = min(self._selected_index, len(self._filtered_materials) - 1) if self._filtered_materials else 0
        self.refresh()
    
    def sort_materials(self, sort_mode: str):
        """Sort materials by name or absorption values."""
        if sort_mode == "name":
            self._filtered_materials.sort(key=lambda m: m.get("name", "").lower())
        elif sort_mode == "absorption_avg":
            self._filtered_materials.sort(
                key=lambda m: sum(m.get("absorption_coefficients", {}).values()),
                reverse=True
            )
        elif sort_mode == "absorption_low":
            # Sort by average of low frequencies (125, 250 Hz)
            def low_avg(m):
                coeffs = m.get("absorption_coefficients", {})
                return (coeffs.get("125Hz", 0) + coeffs.get("250Hz", 0)) / 2
            self._filtered_materials.sort(key=low_avg, reverse=True)
        elif sort_mode == "absorption_high":
            # Sort by average of high frequencies (2000, 4000 Hz)
            def high_avg(m):
                coeffs = m.get("absorption_coefficients", {})
                return (coeffs.get("2000Hz", 0) + coeffs.get("4000Hz", 0)) / 2
            self._filtered_materials.sort(key=high_avg, reverse=True)
        self.refresh()
    
    def move_up(self):
        """Move selection up."""
        if self._selected_index > 0:
            self._selected_index -= 1
            self.refresh()
            return True
        return False
    
    def move_down(self):
        """Move selection down."""
        if self._selected_index < len(self._filtered_materials) - 1:
            self._selected_index += 1
            self.refresh()
            return True
        return False
    
    def toggle_lock(self):
        """Toggle lock on current material as Material B."""
        if self._locked_index == self._selected_index:
            self._locked_index = None
        else:
            self._locked_index = self._selected_index
        self.refresh()
    
    def get_selected_material(self) -> dict | None:
        """Get the currently selected material."""
        if 0 <= self._selected_index < len(self._filtered_materials):
            return self._filtered_materials[self._selected_index]
        return None
    
    def get_locked_material(self) -> dict | None:
        """Get the locked material (Material B)."""
        if self._locked_index is not None and 0 <= self._locked_index < len(self._filtered_materials):
            return self._filtered_materials[self._locked_index]
        return None
    
    def get_selected_index(self) -> int:
        """Get the current selected index."""
        return self._selected_index
    
    def render(self) -> Text:
        out = Text()
        
        # Header
        header = "    " + "NAME".ljust(25) + "  "
        for freq in FREQ_LABELS:
            header += f"{freq:>5} "
        out.append(header + "\n", style=Style.parse("bold gold1"))
        out.append("─" * 70 + "\n", style=Style.parse("dim white"))
        
        if not self._filtered_materials:
            out.append("No materials found.\n", style=Style.parse("dim white"))
            return out
        
        for i, mat in enumerate(self._filtered_materials):
            name = mat.get("name", "Unknown")
            coeffs = mat.get("absorption_coefficients", {})
            
            # Selection indicator
            if i == self._selected_index:
                out.append("▶ ", style=Style.parse("bold yellow"))
            else:
                out.append("  ", style=Style.parse(""))
            
            # Lock indicator
            if i == self._locked_index:
                out.append("🔒 ", style=Style.parse("bold magenta"))
            else:
                out.append("   ", style=Style.parse(""))
            
            # Material name
            display_name = name[:25].ljust(25)
            if i == self._selected_index:
                out.append(display_name, style=Style.parse("bold white on #2e1a52"))
            else:
                out.append(display_name, style=Style.parse("white"))
            
            out.append("  ", style=Style.parse(""))
            
            # Coefficient values with colors
            for j, freq in enumerate(FREQ_BANDS):
                val = coeffs.get(f"{freq}Hz", 0.0)
                color = BAR_COLOURS[j] if j < len(BAR_COLOURS) else "white"
                out.append(f"{val:>5.2f}", style=Style.parse(color))
                out.append(" ", style=Style.parse(""))
            
            out.append("\n", style=Style.parse(""))
        
        return out


class DeleteConfirmModal(Screen):
    """Modal for confirming material deletion."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Cancel"),
    ]
    
    def __init__(self, material_name: str, on_confirm: callable):
        super().__init__()
        self._material_name = material_name
        self._on_confirm = on_confirm
    
    def compose(self) -> ComposeResult:
        with Middle():
            with Center():
                with Vertical(id="delete-modal-container"):
                    yield Label("⚠️  DELETE MATERIAL", id="delete-modal-title")
                    yield Label(f"Are you sure you want to delete:", id="delete-modal-message")
                    yield Label(f"'{self._material_name}'?", id="delete-modal-name")
                    with Horizontal(id="delete-modal-buttons"):
                        yield Button("Cancel", id="btn-cancel-delete", variant="default")
                        yield Button("Delete", id="btn-confirm-delete", variant="error")
    
    @on(Button.Pressed, "#btn-cancel-delete")
    def cancel(self):
        self.app.pop_screen()
    
    @on(Button.Pressed, "#btn-confirm-delete")
    def confirm(self):
        self.app.pop_screen()
        if self._on_confirm:
            self._on_confirm()


class MaterialDatabaseBrowserScreen(Screen):
    """Screen for browsing and managing the material database."""
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "app.pop_screen", "Back"),
        Binding("up", "move_up", "Up"),
        Binding("down", "move_down", "Down"),
        Binding("space", "toggle_lock", "Lock Material B"),
        Binding("e", "edit_material", "Edit"),
        Binding("d", "delete_material", "Delete"),
        Binding("ctrl+s", "export_comparison", "Export Comparison"),
    ]
    
    def __init__(self):
        super().__init__()
        self._materials: list[dict] = []
        self._search_term = ""
        self._sort_mode = "name"
    
    def compose(self) -> ComposeResult:
        with Vertical(id="material-browser-container"):
            # Header
            with Horizontal(id="browser-header"):
                yield Label("📚 MATERIAL DATABASE BROWSER", id="browser-title")
                yield Button("← Back", id="btn-browser-back", variant="primary")
            
            # Search and Sort Controls
            with Horizontal(id="browser-controls"):
                with Vertical(classes="control-group"):
                    yield Label("Search:", classes="control-label")
                    yield Input(placeholder="Type to filter materials...", id="search-input")
                with Vertical(classes="control-group"):
                    yield Label("Sort by:", classes="control-label")
                    yield Select(
                        [
                            ("Name", "name"),
                            ("Avg Absorption", "absorption_avg"),
                            ("Low Freq (125-250Hz)", "absorption_low"),
                            ("High Freq (2k-4kHz)", "absorption_high"),
                        ],
                        value="name",
                        id="sort-select"
                    )
            
            # Main content area
            with Horizontal(id="browser-main"):
                # Material list
                with Vertical(id="material-list-panel"):
                    self._material_list = MaterialListWidget([])
                    yield self._material_list
                
                # Comparison panel
                with Vertical(id="comparison-panel"):
                    yield Label("COMPARISON", classes="panel-title")
                    self._comparison_bars = MaterialComparisonBars()
                    yield self._comparison_bars
                    
                    # Action buttons
                    with Horizontal(id="material-action-buttons"):
                        yield Button("✏️  Edit", id="btn-edit", variant="primary")
                        yield Button("🗑️  Delete", id="btn-delete", variant="error")
                    
                    # Export button on separate row
                    with Horizontal(id="export-button-row"):
                        yield Button("📥  Export Comparison Report", id="btn-export-comparison", variant="success")
            
            # Footer with hints
            with Horizontal(id="browser-footer"):
                yield Label("↑/↓: Navigate  |  Space: Lock Material B  |  E: Edit  |  D: Delete  |  Ctrl+S: Export  |  Esc: Back", id="browser-hint")
    
    def on_mount(self):
        self._load_materials()
    
    def _load_materials(self):
        """Load materials from JSON file."""
        if CUSTOM_MATERIALS_PATH.exists():
            try:
                with open(CUSTOM_MATERIALS_PATH, "r") as f:
                    data = json.load(f)
                    self._materials = data.get("materials", [])
            except (json.JSONDecodeError, IOError):
                self._materials = []
        else:
            self._materials = []
        
        self._material_list.set_materials(self._materials)
        self._update_comparison()
    
    def _update_comparison(self):
        """Update the comparison panel."""
        selected = self._material_list.get_selected_material()
        locked = self._material_list.get_locked_material()
        
        # Material A is the currently selected, Material B is the locked one
        # If nothing is locked, show selected as both
        if locked:
            self._comparison_bars.update_materials(selected, locked)
        else:
            self._comparison_bars.update_materials(selected, selected)
    
    @on(Input.Changed, "#search-input")
    def on_search_changed(self, event: Input.Changed):
        """Handle search input changes."""
        self._search_term = event.value
        self._material_list.filter_materials(self._search_term)
        self._update_comparison()
    
    @on(Select.Changed, "#sort-select")
    def on_sort_changed(self, event: Select.Changed):
        """Handle sort selection changes."""
        if event.value != Select.BLANK:
            self._sort_mode = str(event.value)
            self._material_list.sort_materials(self._sort_mode)
            self._update_comparison()
    
    @on(Button.Pressed, "#btn-browser-back")
    def go_back(self):
        self.app.pop_screen()
    
    @on(Button.Pressed, "#btn-edit")
    def action_edit_material(self):
        """Edit the selected material."""
        selected = self._material_list.get_selected_material()
        if selected:
            # Navigate to material builder with this material selected
            builder = self.app.get_screen("material_builder")
            # Set the material in the builder
            self.app.push_screen("material_builder")
            # After pushing, set the material
            try:
                select = builder.query_one("#select-material", Select)
                select.value = selected.get("name", "")
            except Exception:
                pass
    
    @on(Button.Pressed, "#btn-delete")
    def action_delete_material(self):
        """Delete the selected material."""
        selected = self._material_list.get_selected_material()
        if selected:
            self._show_delete_confirm(selected)
    
    def _show_delete_confirm(self, material: dict):
        """Show delete confirmation modal."""
        name = material.get("name", "")
        self.app.push_screen(
            DeleteConfirmModal(name, lambda: self._do_delete(material))
        )
    
    def _do_delete(self, material: dict):
        """Actually delete the material."""
        name = material.get("name", "")
        
        # Load current materials
        materials_data = {"materials": []}
        if CUSTOM_MATERIALS_PATH.exists():
            try:
                with open(CUSTOM_MATERIALS_PATH, "r") as f:
                    materials_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Remove the material
        existing = materials_data.get("materials", [])
        materials_data["materials"] = [m for m in existing if m.get("name") != name]
        
        # Save back to file
        try:
            with open(CUSTOM_MATERIALS_PATH, "w") as f:
                json.dump(materials_data, f, indent=2)
            self.app.notify(f"Deleted material: {name}")
            self._load_materials()
        except IOError as e:
            self.app.notify(f"Error deleting: {e}", severity="error")
    
    def action_move_up(self):
        """Move selection up."""
        if self._material_list.move_up():
            self._update_comparison()
    
    def action_move_down(self):
        """Move selection down."""
        if self._material_list.move_down():
            self._update_comparison()
    
    def action_toggle_lock(self):
        """Toggle lock on current material as Material B."""
        self._material_list.toggle_lock()
        self._update_comparison()
    
    @on(Button.Pressed, "#btn-export-comparison")
    def action_export_comparison(self):
        """Export comparison report between Material A and Material B."""
        selected = self._material_list.get_selected_material()
        locked = self._material_list.get_locked_material()
        
        if not selected or not locked:
            self.app.notify("Select and lock materials to compare first.", severity="warning")
            return
            
        self._do_export_comparison(selected, locked)

    def _do_export_comparison(self, mat_a: dict, mat_b: dict):
        """Generate and save the comparison report."""
        name_a = mat_a.get("name", "Material A")
        name_b = mat_b.get("name", "Material B")
        coeffs_a = mat_a.get("absorption_coefficients", {})
        coeffs_b = mat_b.get("absorption_coefficients", {})
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sep = "=" * 64
        sep2 = "-" * 64
        
        lines = [
            sep,
            "  ACOUSTICA -- MATERIAL COMPARISON REPORT",
            f"  Generated : {timestamp}",
            sep,
            "",
            "MATERIAL DETAILS",
            sep2,
            f"  {'Property':<20} | {'Material A':<20} | {'Material B':<20}",
            f"  {'Name':<20} | {name_a[:20]:<20} | {name_b[:20]:<20}",
            sep2,
            "",
            "ABSORPTION COEFFICIENTS COMPARISON",
            sep2,
            f"  {'Freq (Hz)':<10} | {'Mat A':<10} | {'Mat B':<10} | {'Difference':<10} | {'Trend'}",
            sep2,
        ]
        
        avg_a = 0
        avg_b = 0
        
        for freq in FREQ_BANDS:
            val_a = coeffs_a.get(f"{freq}Hz", 0.0)
            val_b = coeffs_b.get(f"{freq}Hz", 0.0)
            diff = val_b - val_a
            trend = "Higher" if diff > 0.05 else ("Lower" if diff < -0.05 else "Similar")
            
            avg_a += val_a
            avg_b += val_b
            
            lines.append(f"  {freq:<10} | {val_a:<10.2f} | {val_b:<10.2f} | {diff:<10.2f} | {trend}")
            
            # Visual ASCII Bars
            bar_a = int(val_a * 20)
            bar_b = int(val_b * 20)
            lines.append(f"    Mat A: [{'#' * bar_a + ' ' * (20 - bar_a)}]")
            lines.append(f"    Mat B: [{'#' * bar_b + ' ' * (20 - bar_b)}]")
            lines.append("")
            
        avg_a /= len(FREQ_BANDS)
        avg_b /= len(FREQ_BANDS)
        
        lines.extend([
            sep2,
            f"  {'AVERAGE':<10} | {avg_a:<10.2f} | {avg_b:<10.2f} | {avg_b - avg_a:<10.2f}",
            sep2,
            "",
            "SUMMARY ANALYSIS",
            sep2,
        ])
        
        if avg_b > avg_a + 0.1:
            lines.append(f"  * {name_b} is significantly more absorptive overall than {name_a}.")
        elif avg_b < avg_a - 0.1:
            lines.append(f"  * {name_b} is significantly more reflective overall than {name_a}.")
        else:
            lines.append(f"  * Both materials have similar overall absorption characteristics.")
            
        # Specific frequency analysis
        low_a = (coeffs_a.get("125Hz", 0) + coeffs_a.get("250Hz", 0)) / 2
        low_b = (coeffs_b.get("125Hz", 0) + coeffs_b.get("250Hz", 0)) / 2
        if low_b > low_a + 0.1:
            lines.append(f"  * {name_b} performs better at low frequencies.")
            
        high_a = (coeffs_a.get("2000Hz", 0) + coeffs_a.get("4000Hz", 0)) / 2
        high_b = (coeffs_b.get("2000Hz", 0) + coeffs_b.get("4000Hz", 0)) / 2
        if high_b > high_a + 0.1:
            lines.append(f"  * {name_b} performs better at high frequencies.")
            
        lines.extend([
            "",
            sep,
            "  End of Comparison Report -- Acoustica",
            sep,
        ])
        
        # Save report
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"comp_{name_a[:10]}_{name_b[:10]}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filename = filename.replace(" ", "_").replace("/", "_")
        path = REPORTS_DIR / filename
        
        try:
            path.write_text("\n".join(lines), encoding="utf-8")
            self.app.notify(f"✓ Exported: {filename}", severity="information")
        except Exception as e:
            self.app.notify(f"Export failed: {e}", severity="error")

    def on_key(self, event):
        """Handle key events."""
        if event.key == "up":
            self.action_move_up()
            event.stop()
        elif event.key == "down":
            self.action_move_down()
            event.stop()
        elif event.key == "space":
            self.action_toggle_lock()
            event.stop()
        elif event.key == "e":
            self.action_edit_material()
            event.stop()
        elif event.key == "d":
            self.action_delete_material()
            event.stop()
