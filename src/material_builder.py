# -*- coding: utf-8 -*-
"""Material Builder screen for Acoustica."""

from __future__ import annotations

import datetime
import json
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Grid, Horizontal, Middle, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Select

from .constants import FREQ_BANDS

CUSTOM_MATERIALS_PATH = Path(__file__).resolve().parent.parent / "custom_materials.json"
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports" / "material"


class MaterialBuilderScreen(Screen):
    """Screen for building and editing custom materials."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "app.pop_screen", "Back"),
    ]

    def _load_materials(self) -> list[dict]:
        """Load existing materials from JSON file."""
        if CUSTOM_MATERIALS_PATH.exists():
            try:
                with open(CUSTOM_MATERIALS_PATH, "r") as f:
                    data = json.load(f)
                    return data.get("materials", [])
            except (json.JSONDecodeError, IOError):
                pass
        return []

    def _get_material_names(self) -> list[str]:
        """Get list of material names for dropdown."""
        materials = self._load_materials()
        return ["< New Material >"] + [mat.get("name", "") for mat in materials]

    def compose(self) -> ComposeResult:
        material_names = self._get_material_names()
        
        with Middle():
            with Center():
                with Vertical(id="material-builder-container"):
                    yield Label("🔧 MATERIAL BUILDER", id="builder-title")
                    yield Label("Create or edit custom materials", id="builder-subtitle")
                    yield Label("", id="builder-spacer")

                    # Material Name Input
                    with Vertical(id="builder-form"):
                        # Material Selector Dropdown
                        yield Label("Select Material to Edit", classes="builder-section-title")
                        yield Select(
                            [(name, name) for name in material_names],
                            value="< New Material >",
                            id="select-material"
                        )
                        
                        yield Label("", classes="builder-spacer-small")
                        
                        yield Label("Material Name", classes="builder-section-title")
                        yield Input(placeholder="Enter material name...", id="input-name", restrict=r"[^\"\']*")
                        yield Label("", id="name-status", classes="name-status")

                        yield Label("", classes="builder-spacer-small")

                        # Frequency Band Inputs
                        yield Label("Absorption Coefficients", classes="builder-section-title")
                        yield Label("Enter values between 0.00 and 1.00", classes="builder-hint")

                        with Grid(id="freq-grid"):
                            for freq in FREQ_BANDS:
                                with Vertical(classes="freq-input-group"):
                                    yield Label(f"{freq} Hz", classes="freq-label")
                                    yield Input(
                                        value="0.00",
                                        id=f"input-{freq}",
                                        classes="freq-input",
                                        restrict=r"[0-9.]*"
                                    )

                        yield Label("", classes="builder-spacer-small")

                        # Status message area
                        yield Label("", id="builder-status")

                    # Buttons
                    with Horizontal(id="builder-buttons"):
                        yield Button("←  Back", id="btn-back", variant="primary")
                        yield Button("📄  Export", id="btn-export", variant="primary")
                        yield Button("💾  Save", id="btn-save", variant="primary")

    @on(Select.Changed, "#select-material")
    def on_material_selected(self, event: Select.Changed):
        """Load selected material data into form."""
        selected_name = str(event.value)
        
        if selected_name == "< New Material >":
            self._clear_form()
            return
        
        # Find the material in the list
        materials = self._load_materials()
        for mat in materials:
            if mat.get("name") == selected_name:
                # Load material data into form
                name_input = self.query_one("#input-name", Input)
                name_input.value = selected_name
                
                coeffs = mat.get("absorption_coefficients", {})
                for freq in FREQ_BANDS:
                    input_widget = self.query_one(f"#input-{freq}", Input)
                    value = coeffs.get(f"{freq}Hz", 0.0)
                    input_widget.value = f"{value:.2f}"
                
                self._check_name_unique()
                break

    @on(Input.Changed, "#input-name")
    def on_name_changed(self, event: Input.Changed):
        """Check if name is unique when changed."""
        self._check_name_unique()

    def _check_name_unique(self):
        """Check if the current name is unique and update status."""
        name_input = self.query_one("#input-name", Input)
        name = name_input.value.strip()
        name_status = self.query_one("#name-status", Label)
        
        if not name:
            name_status.update("")
            return
        
        # Check if this name exists in materials
        materials = self._load_materials()
        exists = any(mat.get("name") == name for mat in materials)
        
        # Check if we're editing an existing material (selected from dropdown)
        select = self.query_one("#select-material", Select)
        selected = str(select.value) if select.value else ""
        is_editing = selected == name
        
        if exists and not is_editing:
            name_status.update("⚠️  Name exists - will update existing")
            name_status.styles.color = "#ffa726"
        elif is_editing:
            name_status.update("✏️  Editing existing material")
            name_status.styles.color = "#42a5f5"
        else:
            name_status.update("✓  New material name")
            name_status.styles.color = "#66bb6a"

    @on(Button.Pressed, "#btn-back")
    def go_back(self):
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-export")
    def export_material(self):
        """Export material as TXT report."""
        name_input = self.query_one("#input-name", Input)
        name = name_input.value.strip()

        if not name:
            self._show_status("❌  Please enter a material name", "error")
            return

        # Get absorption coefficients
        coefficients = {}
        for freq in FREQ_BANDS:
            input_widget = self.query_one(f"#input-{freq}", Input)
            try:
                value = float(input_widget.value or "0")
                value = max(0.0, min(1.0, value))
                coefficients[f"{freq}Hz"] = round(value, 2)
            except ValueError:
                coefficients[f"{freq}Hz"] = 0.0

        # Generate report content
        sep = "=" * 64
        sep2 = "-" * 44
        lines = [
            sep,
            "  ACOUSTICA -- MATERIAL SPECIFICATION REPORT",
            "  Generated : {}".format(datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")),
            sep,
            "",
            "MATERIAL INFORMATION",
            sep2,
            "  Name : {}".format(name),
            "",
            "ABSORPTION COEFFICIENTS",
            sep2,
            "  Frequency    |  Coefficient  |  Performance",
            sep2,
        ]
        
        for freq in FREQ_BANDS:
            coeff = coefficients.get(f"{freq}Hz", 0.0)
            # Performance rating based on coefficient
            if coeff < 0.1:
                perf = "Reflective"
            elif coeff < 0.3:
                perf = "Low Absorption"
            elif coeff < 0.5:
                perf = "Medium Absorption"
            elif coeff < 0.8:
                perf = "High Absorption"
            else:
                perf = "Very High Absorption"
            
            bar = int(coeff * 20)
            lines.append("  {:>5} Hz     |     {:.2f}      |  {}".format(freq, coeff, perf))
            lines.append("                |  {}  |".format("█" * bar + "░" * (20 - bar)))
        
        lines += [
            "",
            "NOTES",
            sep2,
            "  Absorption coefficient ranges from 0.00 (fully reflective)",
            "  to 1.00 (fully absorptive). Values are per ISO 354 standard.",
            "",
            sep,
            "  End of Material Report -- Acoustica",
            sep,
        ]

        # Save to reports directory
        fname = "material_{}_{}.txt".format(
            name.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_"),
            datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        out_path = REPORTS_DIR / fname
        
        try:
            out_path.write_text("\n".join(lines), encoding="utf-8")
            self._show_status(f"✓  Exported to {fname}", "success")
        except OSError as exc:
            self._show_status(f"❌  Export error: {exc}", "error")

    @on(Button.Pressed, "#btn-save")
    def save_material(self):
        # Get material name
        name_input = self.query_one("#input-name", Input)
        name = name_input.value.strip()

        if not name:
            self._show_status("❌  Please enter a material name", "error")
            return

        # Get absorption coefficients and validate
        coefficients = {}
        for freq in FREQ_BANDS:
            input_widget = self.query_one(f"#input-{freq}", Input)
            try:
                value = float(input_widget.value or "0")
                # Clamp between 0 and 1
                value = max(0.0, min(1.0, value))
                coefficients[f"{freq}Hz"] = round(value, 2)
                # Update the input to show clamped value
                input_widget.value = f"{coefficients[f'{freq}Hz']:.2f}"
            except ValueError:
                coefficients[f"{freq}Hz"] = 0.0
                input_widget.value = "0.00"

        # Create material entry
        new_material = {
            "name": name,
            "absorption_coefficients": coefficients
        }

        # Load existing materials
        materials_data = {"materials": []}
        if CUSTOM_MATERIALS_PATH.exists():
            try:
                with open(CUSTOM_MATERIALS_PATH, "r") as f:
                    materials_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        # Check if material with same name exists and update it
        existing_materials = materials_data.get("materials", [])
        updated = False
        for i, mat in enumerate(existing_materials):
            if mat.get("name") == name:
                existing_materials[i] = new_material
                updated = True
                break

        if not updated:
            existing_materials.append(new_material)

        materials_data["materials"] = existing_materials

        # Save to file
        try:
            with open(CUSTOM_MATERIALS_PATH, "w") as f:
                json.dump(materials_data, f, indent=2)
            
            if updated:
                self._show_status(f"✓  Material '{name}' updated!", "success")
            else:
                self._show_status(f"✓  Material '{name}' created!", "success")
            
            # Refresh the dropdown
            self._refresh_material_dropdown()
        except IOError as e:
            self._show_status(f"❌  Error saving: {e}", "error")

    def _refresh_material_dropdown(self):
        """Refresh the material dropdown with updated list."""
        try:
            select = self.query_one("#select-material", Select)
            material_names = self._get_material_names()
            
            # Rebuild the options
            select._options = [(name, name) for name in material_names]
            
            # Set to the current material name
            name_input = self.query_one("#input-name", Input)
            current_name = name_input.value.strip()
            if current_name and current_name in material_names:
                select.value = current_name
            else:
                select.value = "< New Material >"
            
            select.refresh()
        except Exception as e:
            # Fallback if widget manipulation fails
            pass

    def _show_status(self, message: str, status_type: str):
        status_label = self.query_one("#builder-status", Label)
        status_label.update(message)
        if status_type == "error":
            status_label.styles.color = "#ff6b6b"
        else:
            status_label.styles.color = "#51cf66"

    def _clear_form(self):
        """Clear the form after successful save."""
        name_input = self.query_one("#input-name", Input)
        name_input.value = ""
        name_status = self.query_one("#name-status", Label)
        name_status.update("")
        for freq in FREQ_BANDS:
            input_widget = self.query_one(f"#input-{freq}", Input)
            input_widget.value = "0.00"