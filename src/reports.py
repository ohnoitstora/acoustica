# -*- coding: utf-8 -*-
"""Reports listing screen with tabs and pagination."""

from __future__ import annotations

from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Container, Horizontal, Middle, ScrollableContainer, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Label, ListItem, ListView, Static, TabbedContent, TabPane

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"

# Report type directories
REPORT_TYPES = {
    "analysis": REPORTS_DIR / "analysis",
    "material": REPORTS_DIR / "material",
    "treatment": REPORTS_DIR / "treatment",
    "mixer": REPORTS_DIR / "mixer",
    "other": REPORTS_DIR,  # Root directory for legacy/uncategorized reports
}

REPORT_TYPE_LABELS = {
    "analysis": "Analysis Reports",
    "material": "Material Reports",
    "treatment": "Treatment Reports",
    "mixer": "Mixer Reports",
    "other": "Other Reports",
}

# Pagination settings
REPORTS_PER_PAGE = 10


class ReportViewModal(ModalScreen):
    """Modal to display report content with optional tabbed view for analysis reports."""

    BINDINGS = [Binding("escape", "dismiss", "Close")]

    def __init__(self, report_path: Path):
        super().__init__()
        self._report_path = report_path
        self._report_content = self._load_report()
        self._is_analysis = "SOUND PRESSURE MAP" in self._report_content

    def compose(self) -> ComposeResult:
        with Container(id="report-modal-container"):
            yield Label(self._report_path.name, id="report-modal-title")
            
            if self._is_analysis:
                # Split content into calculation results and pressure map
                parts = self._report_content.split("SOUND PRESSURE MAP")
                calc_results = parts[0].strip()
                # Re-add the header to the map part
                pressure_map = "SOUND PRESSURE MAP" + parts[1] if len(parts) > 1 else ""
                
                with TabbedContent(id="report-tabs"):
                    with TabPane("Calculation Results", id="tab-results"):
                        with ScrollableContainer(classes="report-scroll"):
                            yield Static(calc_results, classes="report-text")
                    with TabPane("Pressure Map", id="tab-map"):
                        with ScrollableContainer(classes="report-scroll"):
                            yield Static(pressure_map, classes="report-text pressure-map-text")
            else:
                with ScrollableContainer(id="report-modal-scroll"):
                    yield Static(self._report_content, id="report-modal-content", classes="report-text")
            
            yield Button("Close", id="btn-close-report", variant="primary")

    def _load_report(self) -> str:
        try:
            return self._report_path.read_text(encoding="utf-8")
        except OSError:
            return "Error: Could not read report file."

    @on(Button.Pressed, "#btn-close-report")
    def close_modal(self):
        self.dismiss()


class ReportsScreen(Screen):
    """Show exported report files with tabs and pagination."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self._report_files: dict[str, list[Path]] = {
            "analysis": [],
            "material": [],
            "treatment": [],
            "mixer": [],
            "other": [],
        }
        self._current_page: dict[str, int] = {
            "analysis": 0,
            "material": 0,
            "treatment": 0,
            "mixer": 0,
            "other": 0,
        }

    def compose(self) -> ComposeResult:
        with Middle():
            with Center():
                with Vertical(id="reports-container"):
                    yield Label("Saved Reports", id="reports-title")
                    yield Label("View and manage your exported reports", id="reports-subtitle")
                    yield Label("", id="reports-spacer")
                    
                    # Tabbed content for different report types
                    with TabbedContent(id="reports-tabs"):
                        for report_type, label in REPORT_TYPE_LABELS.items():
                            with TabPane(label, id=f"tab-{report_type}"):
                                with Vertical(classes="report-tab-content"):
                                    # Report count label
                                    yield Label(
                                        f"No {label.lower()}",
                                        id=f"count-{report_type}",
                                        classes="report-count"
                                    )
                                    # Report list
                                    yield ListView(
                                        id=f"list-{report_type}",
                                        classes="reports-list"
                                    )
                                    # Pagination controls
                                    with Horizontal(classes="pagination-row"):
                                        yield Button(
                                            "◀ Prev",
                                            id=f"prev-{report_type}",
                                            classes="pagination-btn",
                                            variant="primary"
                                        )
                                        yield Label(
                                            "Page 1 of 1",
                                            id=f"page-{report_type}",
                                            classes="pagination-label"
                                        )
                                        yield Button(
                                            "Next ▶",
                                            id=f"next-{report_type}",
                                            classes="pagination-btn",
                                            variant="primary"
                                        )
                    
                    yield Label("", id="reports-spacer-bottom")
                    yield Button("← Back to Menu", id="btn-back", variant="primary")

    def on_mount(self):
        self._refresh_all_reports()
        self.set_interval(2.0, self._check_for_updates)

    def _get_report_files_by_type(self, report_type: str) -> list[Path]:
        """Get all .txt files for a specific report type."""
        all_files = []
        report_dir = REPORT_TYPES[report_type]
        report_dir.mkdir(parents=True, exist_ok=True)
        
        if report_type == "other":
            # For "other", only get files directly in root, not subdirectories
            all_files.extend(report_dir.glob("*.txt"))
        else:
            all_files.extend(report_dir.glob("*.txt"))
        
        return sorted(all_files, key=lambda p: p.stat().st_mtime, reverse=True)

    def _check_for_updates(self):
        """Check if any report files have changed."""
        needs_refresh = False
        for report_type in REPORT_TYPES:
            current_files = self._get_report_files_by_type(report_type)
            current_names = [f.name for f in current_files]
            existing_names = [f.name for f in self._report_files[report_type]]
            if current_names != existing_names:
                needs_refresh = True
                break
        if needs_refresh:
            self._refresh_all_reports()

    def _refresh_all_reports(self):
        """Refresh reports for all types."""
        for report_type in REPORT_TYPES:
            self._report_files[report_type] = self._get_report_files_by_type(report_type)
            self._current_page[report_type] = 0
            self._refresh_report_list(report_type)

    def _refresh_report_list(self, report_type: str):
        """Refresh the report list for a specific type with pagination."""
        list_view = self.query_one(f"#list-{report_type}", ListView)
        list_view.clear()
        
        files = self._report_files[report_type]
        total_files = len(files)
        
        # Update count label
        count_label = self.query_one(f"#count-{report_type}", Label)
        if total_files == 0:
            count_label.update(f"No {REPORT_TYPE_LABELS[report_type].lower()}")
        else:
            count_label.update(f"{total_files} {REPORT_TYPE_LABELS[report_type].lower()}")
        
        if not files:
            list_view.append(ListItem(Label("No reports found.")))
            self._update_pagination(report_type, 0, 0)
            return
        
        # Calculate pagination
        current_page = self._current_page[report_type]
        total_pages = max(1, (total_files + REPORTS_PER_PAGE - 1) // REPORTS_PER_PAGE)
        
        # Ensure current page is valid
        if current_page >= total_pages:
            current_page = total_pages - 1
            self._current_page[report_type] = current_page
        
        # Get files for current page
        start_idx = current_page * REPORTS_PER_PAGE
        end_idx = min(start_idx + REPORTS_PER_PAGE, total_files)
        page_files = files[start_idx:end_idx]
        
        # Add files to list
        for report in page_files:
            # Format: filename (date)
            from datetime import datetime
            try:
                mtime = datetime.fromtimestamp(report.stat().st_mtime)
                date_str = mtime.strftime("%Y-%m-%d %H:%M")
            except OSError:
                date_str = "Unknown date"
            
            display_text = f"{report.name}"
            list_view.append(ListItem(Label(display_text)))
        
        self._update_pagination(report_type, current_page + 1, total_pages)

    def _update_pagination(self, report_type: str, current_page: int, total_pages: int):
        """Update pagination controls."""
        page_label = self.query_one(f"#page-{report_type}", Label)
        page_label.update(f"Page {current_page} of {total_pages}")
        
        prev_btn = self.query_one(f"#prev-{report_type}", Button)
        next_btn = self.query_one(f"#next-{report_type}", Button)
        
        prev_btn.disabled = current_page <= 1
        next_btn.disabled = current_page >= total_pages

    @on(Button.Pressed, ".pagination-btn")
    def _on_pagination_btn(self, event: Button.Pressed):
        """Handle pagination button clicks."""
        btn_id = event.button.id or ""
        if not btn_id.startswith(("prev-", "next-")):
            return
        
        action, report_type = btn_id.split("-", 1)
        
        if action == "prev":
            self._current_page[report_type] = max(0, self._current_page[report_type] - 1)
        elif action == "next":
            total_files = len(self._report_files[report_type])
            total_pages = max(1, (total_files + REPORTS_PER_PAGE - 1) // REPORTS_PER_PAGE)
            self._current_page[report_type] = min(
                total_pages - 1, self._current_page[report_type] + 1
            )
        
        self._refresh_report_list(report_type)

    @on(ListView.Selected)
    def view_report(self, event: ListView.Selected):
        """Handle report selection."""
        list_view = event.list_view
        list_id = list_view.id or ""
        
        if not list_id.startswith("list-"):
            return
        
        report_type = list_id.replace("list-", "")
        files = self._report_files[report_type]
        
        if not files:
            return
        
        # Calculate actual index based on current page
        current_page = self._current_page[report_type]
        start_idx = current_page * REPORTS_PER_PAGE
        actual_idx = start_idx + list_view.index
        
        if 0 <= actual_idx < len(files):
            self.app.push_screen(ReportViewModal(files[actual_idx]))

    @on(Button.Pressed, "#btn-back")
    def go_back(self):
        self.app.pop_screen()
