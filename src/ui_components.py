# -*- coding: utf-8 -*-
"""Reusable Textual widgets for the Acoustica UI."""

from __future__ import annotations

from rich.style import Style
from rich.text import Text
from textual import events
from textual.reactive import reactive
from textual.widget import Widget

from .constants import (
    BAR_COLOURS,
    BLOCK,
    FREQ_BANDS,
    FREQ_LABELS,
    SOURCE_COLOUR,
    SOURCE_DOT,
)
from .physics import calculate_mode_pressure_map, rt60_quality
from .state import AcousticState


class ComparisonBarChart(Widget):
    """Side-by-side bar chart comparing RT60 values for two rooms."""

    DEFAULT_CSS = """
    ComparisonBarChart {
        height: 14;
        border: solid $accent;
        padding: 0 1;
    }
    """

    def __init__(self, rt60_a: list[float], rt60_b: list[float], room_a_name: str = "Room A", room_b_name: str = "Room B") -> None:
        super().__init__()
        self._rt60_a = rt60_a
        self._rt60_b = rt60_b
        self._room_a_name = room_a_name
        self._room_b_name = room_b_name

    def update_values(self, rt60_a: list[float], rt60_b: list[float], room_a_name: str = "Room A", room_b_name: str = "Room B"):
        """Update the chart with new RT60 values."""
        self._rt60_a = rt60_a
        self._rt60_b = rt60_b
        self._room_a_name = room_a_name
        self._room_b_name = room_b_name
        self.refresh()

    def _get_bar_color(self, val_a: float, val_b: float, is_room_a: bool) -> str:
        """Determine bar color based on which room has better acoustics.
        
        Lower RT60 is generally better (less reverberation = more clarity).
        Uses green for the better room, red for the worse room.
        """
        diff = val_b - val_a
        threshold = 0.05  # Small threshold to avoid coloring nearly equal values
        
        if abs(diff) < threshold:
            return "dim white"  # Similar values - neutral color
        
        if is_room_a:
            # Room A: lower RT60 is better
            return "bright_green" if diff > threshold else "bright_red"
        else:
            # Room B: lower RT60 is better  
            return "bright_green" if diff < -threshold else "bright_red"

    def render(self) -> Text:
        width_chars = max(self.size.width - 2, 8)
        height_chars = max(self.size.height - 2, 6)
        
        # Calculate max value for scaling
        all_vals = list(self._rt60_a) + list(self._rt60_b)
        max_rt = max(all_vals) if all_vals and max(all_vals) > 1e-9 else 1.0
        
        # Reserve space for header and labels
        header_height = 2
        label_height = 2
        chart_height = height_chars - header_height - label_height
        bar_height = chart_height - 1
        
        # Width per frequency band
        num_bands = len(FREQ_BANDS)
        slot_width = max(4, width_chars // num_bands)
        
        # Initialize grid
        grid = [[" "] * width_chars for _ in range(height_chars)]
        gstyle = [[""] * width_chars for _ in range(height_chars)]
        
        # Draw header
        header_text = f"RT60 COMPARISON"
        for i, ch in enumerate(header_text):
            if i < width_chars:
                grid[0][i] = ch
                gstyle[0][i] = "bold gold1"
        
        # Draw room labels (A and B for each band)
        for idx, freq in enumerate(FREQ_LABELS):
            slot_x = idx * slot_width
            center_x = slot_x + slot_width // 2
            
            # Frequency label at bottom
            freq_str = freq.strip()
            for li, lc in enumerate(freq_str):
                col = slot_x + slot_width // 4 + li
                if 0 <= col < width_chars:
                    grid[height_chars - 1][col] = lc
                    gstyle[height_chars - 1][col] = "dim white"
            
            # Get values for this band
            val_a = self._rt60_a[idx] if idx < len(self._rt60_a) else 0
            val_b = self._rt60_b[idx] if idx < len(self._rt60_b) else 0
            
            # Draw Room A bar (left half of slot)
            bar_a_width = max(1, slot_width // 2 - 1)
            bar_a_x = slot_x + 1
            color_a = self._get_bar_color(val_a, val_b, True)
            
            frac_a = val_a / max_rt if max_rt > 0 else 0.0
            eights_fill_a = int(frac_a * bar_height * 8)
            full_rows_a = eights_fill_a // 8
            part_a = eights_fill_a % 8
            
            for row in range(full_rows_a):
                row_idx = header_height + bar_height - 1 - row
                for col in range(bar_a_x, min(bar_a_x + bar_a_width, width_chars)):
                    grid[row_idx][col] = "█"
                    gstyle[row_idx][col] = color_a
            
            if part_a > 0 and full_rows_a < bar_height:
                row_idx = header_height + bar_height - 1 - full_rows_a
                ch = BLOCK[part_a]
                for col in range(bar_a_x, min(bar_a_x + bar_a_width, width_chars)):
                    grid[row_idx][col] = ch
                    gstyle[row_idx][col] = color_a
            
            # Draw Room B bar (right half of slot)
            bar_b_width = max(1, slot_width // 2 - 1)
            bar_b_x = slot_x + slot_width // 2
            color_b = self._get_bar_color(val_a, val_b, False)
            
            frac_b = val_b / max_rt if max_rt > 0 else 0.0
            eights_fill_b = int(frac_b * bar_height * 8)
            full_rows_b = eights_fill_b // 8
            part_b = eights_fill_b % 8
            
            for row in range(full_rows_b):
                row_idx = header_height + bar_height - 1 - row
                for col in range(bar_b_x, min(bar_b_x + bar_b_width, width_chars)):
                    grid[row_idx][col] = "█"
                    gstyle[row_idx][col] = color_b
            
            if part_b > 0 and full_rows_b < bar_height:
                row_idx = header_height + bar_height - 1 - full_rows_b
                ch = BLOCK[part_b]
                for col in range(bar_b_x, min(bar_b_x + bar_b_width, width_chars)):
                    grid[row_idx][col] = ch
                    gstyle[row_idx][col] = color_b
            
            # Draw values above bars
            val_a_str = f"{val_a:.2f}"
            val_b_str = f"{val_b:.2f}"
            
            # Position values above their respective bars
            val_row = header_height + bar_height - full_rows_a - (1 if part_a else 0) - 1
            for li, lc in enumerate(val_a_str):
                col = bar_a_x + li
                if 0 <= col < width_chars and val_row >= header_height:
                    grid[val_row][col] = lc
                    gstyle[val_row][col] = color_a
            
            val_row = header_height + bar_height - full_rows_b - (1 if part_b else 0) - 1
            for li, lc in enumerate(val_b_str):
                col = bar_b_x + li
                if 0 <= col < width_chars and val_row >= header_height:
                    grid[val_row][col] = lc
                    gstyle[val_row][col] = color_b
            
            # Draw "A" and "B" labels below the bars
            ab_row = height_chars - 2
            if 0 <= bar_a_x < width_chars:
                grid[ab_row][bar_a_x + bar_a_width // 2] = "A"
                gstyle[ab_row][bar_a_x + bar_a_width // 2] = "dim cyan"
            if 0 <= bar_b_x < width_chars:
                grid[ab_row][bar_b_x + bar_b_width // 2] = "B"
                gstyle[ab_row][bar_b_x + bar_b_width // 2] = "dim magenta"
        
        # Build output text
        out = Text()
        for row_idx, row in enumerate(grid):
            for col_idx, ch in enumerate(row):
                style = gstyle[row_idx][col_idx]
                out.append(ch, style=Style.parse(style) if style else Style())
            if row_idx < height_chars - 1:
                out.append("\n")
        return out


class RoomCanvas(Widget):
    DEFAULT_CSS = """
    RoomCanvas {
        height: 1fr;
        border: solid $accent;
        padding: 0 1;
    }
    """
    source_info: reactive[str] = reactive("no source -- click to place")

    def __init__(self, state: AcousticState) -> None:
        super().__init__()
        self._state = state

    def render(self) -> Text:
        width_chars = max(self.size.width - 2, 4)
        height_chars = max(self.size.height - 2, 4)
        room_width = self._state.width
        room_length = self._state.length
        if room_width < 0.1 or room_length < 0.1:
            return Text("Invalid dimensions", style="bright_red")
        char_aspect = 2.13
        ratio = (room_width / room_length) * char_aspect
        if width_chars / height_chars > ratio:
            room_height = height_chars
            room_width_chars = max(1, int(room_height * ratio))
        else:
            room_width_chars = width_chars
            room_height = max(1, int(room_width_chars / ratio))
        offset_x = (width_chars - room_width_chars) // 2
        offset_y = (height_chars - room_height) // 2
        grid = [[" "] * width_chars for _ in range(height_chars)]
        styles = [[None] * width_chars for _ in range(height_chars)]

        def _put(row, col, ch, sty=""):
            if 0 <= row < height_chars and 0 <= col < width_chars:
                grid[row][col] = ch
                styles[row][col] = sty

        if self._state.view_mode == "map":
            mode_indices = self._map_mode_indices()
            pressure = calculate_mode_pressure_map(
                room_width,
                room_length,
                self._state.height,
                mode_indices,
                resolution=(room_width_chars - 2, room_height - 2),
                intensity_scale=self._state.map_intensity,
            )
            shade_chars = " .:-=+*#%@"
            shade_len = len(shade_chars) - 1
            for row in range(1, room_height - 1):
                for col in range(1, room_width_chars - 1):
                    value = pressure[row - 1][col - 1]
                    
                    # Recommendation logic:
                    # S - Speakers: High pressure areas (> 0.9) - nodal anti-nodes
                    # L - Listener: Low pressure areas (< 0.1) - nodes
                    if value > 0.92:
                        ch = "S"
                        colour = "bold bright_red"
                    elif value < 0.08:
                        ch = "L"
                        colour = "bold bright_green"
                    else:
                        idx = min(shade_len, max(0, int(value * shade_len)))
                        ch = shade_chars[idx]
                        colour = "color({})".format(232 + idx)
                        
                    _put(offset_y + row, offset_x + col, ch, colour)
        else:
            for row in range(1, room_height - 1):
                for col in range(1, room_width_chars - 1):
                    _put(offset_y + row, offset_x + col, "\u00b7", "color(237)")

        _put(offset_y, offset_x, "\u250c", "bold gold1")
        _put(offset_y, offset_x + room_width_chars - 1, "\u2510", "bold gold1")
        _put(offset_y + room_height - 1, offset_x, "\u2514", "bold gold1")
        _put(offset_y + room_height - 1, offset_x + room_width_chars - 1, "\u2518", "bold gold1")
        for col in range(1, room_width_chars - 1):
            _put(offset_y, offset_x + col, "\u2500", "gold1")
            _put(offset_y + room_height - 1, offset_x + col, "\u2500", "gold1")
        for row in range(1, room_height - 1):
            _put(offset_y + row, offset_x, "\u2502", "gold1")
            _put(offset_y + row, offset_x + room_width_chars - 1, "\u2502", "gold1")

        dim_width = " W={:.1f}m ".format(room_width)
        dim_length = " L={:.1f}m ".format(room_length)
        label_x = offset_x + max(0, (room_width_chars - len(dim_width)) // 2)
        label_y = offset_y + room_height
        if label_y < height_chars:
            for idx, ch in enumerate(dim_width):
                _put(label_y, label_x + idx, ch, "dark_orange")
        for idx, ch in enumerate(dim_length):
            _put(offset_y + idx, offset_x + room_width_chars + 1, ch, "dark_orange")

        if self._state.view_mode != "map" and self._state.source is not None:
            frac_x, frac_y = self._state.source
            source_x = offset_x + 1 + int(frac_x * (room_width_chars - 2))
            source_y = offset_y + 1 + int(frac_y * (room_height - 2))
            for col in range(1, room_width_chars - 1):
                if grid[source_y][offset_x + col] in ("\u00b7", " "):
                    _put(source_y, offset_x + col, "\u254c", "dim {}".format(SOURCE_COLOUR))
            for row in range(1, room_height - 1):
                if grid[offset_y + row][source_x] in ("\u00b7", " ", "\u254c"):
                    _put(offset_y + row, source_x, "\u254e", "dim {}".format(SOURCE_COLOUR))
            _put(source_y, source_x, SOURCE_DOT, "bold {}".format(SOURCE_COLOUR))
            for idx, ch in enumerate("S1"):
                _put(source_y - 1, source_x + 1 + idx, ch, SOURCE_COLOUR)

        out = Text()
        for row_idx, row in enumerate(grid):
            for col_idx, ch in enumerate(row):
                style = styles[row_idx][col_idx]
                out.append(ch, style=Style.parse(style) if style else Style())
            if row_idx < height_chars - 1:
                out.append("\n")
        return out

    def on_click(self, event: events.Click) -> None:
        if self._state.view_mode == "map":
            return
        if event.button == 1:
            self._place_source(event.x, event.y)
        elif event.button == 3:
            self._state.source = None
            self.source_info = "no source -- click to place"
            self.refresh()

    def _map_mode_indices(self):
        mode = self._state.map_mode
        if mode == "width-1":
            return (0, 1, 0)
        if mode == "height-1":
            return (0, 0, 1)
        return (1, 0, 0)

    def _canvas_to_room(self, px, py):
        width_chars = max(self.size.width - 2, 4)
        height_chars = max(self.size.height - 2, 4)
        room_width = self._state.width
        room_length = self._state.length
        char_aspect = 2.13
        ratio = (room_width / room_length) * char_aspect
        if width_chars / height_chars > ratio:
            room_height = height_chars
            room_width_chars = max(1, int(room_height * ratio))
        else:
            room_width_chars = width_chars
            room_height = max(1, int(room_width_chars / ratio))
        offset_x = (width_chars - room_width_chars) // 2
        offset_y = (height_chars - room_height) // 2
        cursor_x, cursor_y = px - 1, py
        if room_width_chars <= 2 or room_height <= 2:
            return None
        if not (
            offset_x + 1 <= cursor_x <= offset_x + room_width_chars - 2
            and offset_y + 1 <= cursor_y <= offset_y + room_height - 2
        ):
            return None
        frac_x = (cursor_x - offset_x - 1) / (room_width_chars - 2)
        frac_y = (cursor_y - offset_y - 1) / (room_height - 2)
        return (max(0.0, min(1.0, frac_x)), max(0.0, min(1.0, frac_y)))

    def _place_source(self, px, py):
        pos = self._canvas_to_room(px, py)
        if pos is None:
            return
        self._state.source = pos
        frac_x, frac_y = pos
        width, length = self._state.width, self._state.length
        self.source_info = "S1  X={:.2f} m   Y={:.2f} m".format(frac_x * width, frac_y * length)
        self.refresh()


class BarChart(Widget):
    DEFAULT_CSS = """
    BarChart {
        height: 12;
        border: solid $accent;
        padding: 0 1;
    }
    """

    def __init__(self, state: AcousticState) -> None:
        super().__init__()
        self._state = state

    def render(self) -> Text:
        vals = self._state.rt60_vals
        max_rt = max(vals) if vals and max(vals) > 1e-9 else 1.0
        width_chars = max(self.size.width - 2, 6)
        height_chars = max(self.size.height - 2, 4)
        bar_height = height_chars - 2
        slot_width = max(2, width_chars // len(FREQ_BANDS))
        grid = [[" "] * width_chars for _ in range(height_chars)]
        gstyle = [[""] * width_chars for _ in range(height_chars)]

        for idx, (rt, colour, lbl) in enumerate(zip(vals, BAR_COLOURS, FREQ_LABELS)):
            bar_x = idx * slot_width + slot_width // 4
            bar_width = max(1, slot_width - slot_width // 2)
            frac = rt / max_rt if max_rt > 0 else 0.0
            eights_fill = int(frac * bar_height * 8)
            full_rows = eights_fill // 8
            part = eights_fill % 8
            for row in range(full_rows):
                row_idx = height_chars - 2 - row
                for col in range(bar_x, min(bar_x + bar_width, width_chars)):
                    grid[row_idx][col] = "\u2588"
                    gstyle[row_idx][col] = colour
            if part > 0 and full_rows < bar_height:
                row_idx = height_chars - 2 - full_rows
                ch = BLOCK[part]
                for col in range(bar_x, min(bar_x + bar_width, width_chars)):
                    grid[row_idx][col] = ch
                    gstyle[row_idx][col] = colour
            val_str = "{:.2f}".format(rt)
            lbl_row = height_chars - 2 - full_rows - (1 if part else 0) - 1
            for li, lc in enumerate(val_str):
                col = bar_x + li
                if 0 <= col < width_chars and 0 <= lbl_row < height_chars:
                    grid[lbl_row][col] = lc
                    gstyle[lbl_row][col] = colour
            for li, lc in enumerate(lbl.strip()):
                col = bar_x + li
                if 0 <= col < width_chars:
                    grid[height_chars - 1][col] = lc
                    gstyle[height_chars - 1][col] = "dim white"

        out = Text()
        for row_idx, row in enumerate(grid):
            for col_idx, ch in enumerate(row):
                style = gstyle[row_idx][col_idx]
                out.append(ch, style=Style.parse(style) if style else Style())
            if row_idx < height_chars - 1:
                out.append("\n")
        return out
