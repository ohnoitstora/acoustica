# 🎵 Acoustica

<div align="center">

**Professional Acoustic Analysis & Room Mode Calculator**

A powerful terminal-based (TUI) acoustic analyzer built with [Textual](https://github.com/Textualize/textual)

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Textual](https://img.shields.io/badge/TUI-Textual-purple.svg)](https://github.com/Textualize/textual)

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Physics](#-physics) • [Project Structure](#-project-structure)

</div>

---

## 📖 Overview

Acoustica is a comprehensive acoustic analysis tool that runs entirely in your terminal. Analyze room acoustics, calculate reverberation times (RT60), identify room modes, design acoustic treatments, and even simulate how your room affects sound—all without needing a GUI.

**Perfect for:**
- 🎙️ Recording studio design
- 🎬 Home theater optimization
- 🎤 Podcast room treatment
- 🎓 Acoustic engineering education
- 🏠 General room acoustic analysis

**Works everywhere:**
- ✅ Any terminal emulator (iTerm2, Terminal, Alacritty, etc.)
- ✅ VS Code integrated terminal
- ✅ GitHub Codespaces
- ✅ SSH sessions
- ✅ tmux/screen sessions

---

## 🎯 Features

### 📊 Acoustic Analysis
- **RT₆₀ Calculation** — Sabine's formula applied per octave band (125 Hz – 4 kHz)
- **Room Mode Analysis** — Identify problematic axial modes for Length, Width, and Height
- **Live Frequency Response** — Interactive bar chart showing RT₆₀ across all octave bands
- **Quality Assessment** — Automatic room quality rating (Dead/Dry/Live/Bright)
- **Interactive 2D Canvas** — Click to place up to 8 sound sources and visualize room layout
- **Pressure Map View** — Visualize sound pressure distribution for axial room modes
- **Multi-Source Support** — Place and manage up to 8 simultaneous sound sources

### ⊞ Acoustic Mixer
- **Real-time Decay Visualization** — See sound decay from 0 to -60 dB over time
- **Material Presets** — Load absorption coefficients directly from the material library
- **Frequency Band Focus** — Highlight specific bands (125 Hz – 4 kHz) on the decay graph
- **Live Graph Updates** — Instant visualization as you adjust absorption values
- **+/- Controls & Direct Input** — Adjust each band with buttons or type values directly
- **Reset All / Flat 0.5** — Quick reset buttons for reflective or mid-absorption baseline
- **Export Reports** — Save mixer configurations with RT60 calculations per band

### 🎨 Material Management
- **Material Library** — Real absorption coefficients for 6 octave bands (125–4000 Hz)
- **Material Builder** — Create, edit, and manage custom acoustic materials
  - Select existing material from dropdown to edit
  - Real-time name uniqueness validation
  - Input validation for absorption coefficients (0.00–1.00 range)
  - Export material specifications as detailed reports
  - Persistent storage in `custom_materials.json`
- **Material Database Browser** — Browse, search, compare, and manage all materials
  - Search and filter materials by name
  - Sort by name or absorption values (average, low freq, high freq)
  - Side-by-side comparison with visual bar charts
  - Lock Material B (Space) to compare with current selection
  - Export detailed comparison reports with ASCII graphs
  - Edit or delete materials directly from the browser
- **Built-in Materials** — Concrete, Gypsum Board, Carpet, Acoustic Foam, Hardwood Floor, Glass, Brick, Heavy Curtain, and more — all stored in `custom_materials.json`

### 🔧 Treatment Calculator
- **Smart Treatment Planning** — Calculate exactly how much acoustic treatment you need
- **RT60 Presets** — Recording Studio (0.3s), Home Theater (0.5s), Lecture Hall (1.0s), Concert Hall (1.5s), Church/Cathedral (2.0s), or Custom
- **Live Results** — Absorption sabins, panel count, coverage area, and cost update instantly
- **Cost Estimation** — Input price per panel for accurate budget planning
- **Frequency-Specific** — Target any of the 6 octave bands for precise treatment
- **Export Plans** — Save detailed treatment plans with material requirements and costs

### 🎧 Audio Simulation
- **Impulse Response Generation** — Synthetic IR based on your room's RT60 values
- **Convolution Reverb** — Simulate actual room acoustics with real audio processing
- **Audio Export** — Generate dry/wet comparison files (440 Hz test tone)
- **A/B Testing** — Listen externally to compare your room's acoustic signature
- **Report Integration** — Audio files bundled with analysis reports

### 📁 Report Management
- **Comprehensive Reports** — Export detailed `.txt` reports with all analysis data
- **Tabbed Report Browser** — Browse and view reports organized by category:
  - Analysis Reports
  - Material Reports
  - Material Comparisons
  - Treatment Reports
  - Mixer Reports
  - Other Reports
- **Paginated Listing** — 10 reports per page with previous/next navigation
- **Inline Viewer** — Read report content directly in the TUI without leaving the app
- **Organized Storage** — Separate folders for each module under `reports/`
- **Timestamped Exports** — Automatic file naming with date/time stamps

### ⚖️ Room Comparator
- **Side-by-Side Analysis** — Load two saved room snapshots and compare their full acoustic profiles at a glance
- **Room Snapshots** — Save any room configuration (dimensions + materials) as a named snapshot; snapshots persist to `snapshots/` as JSON files
- **Comparison Panels** — Each panel shows dimensions, materials, RT60 per band, axial modes, Room NRC, and Schroeder frequency
- **RT60 Bar Chart** — Color-coded `ComparisonBarChart` widget showing both rooms side by side for every octave band
- **Acoustic Radar Chart** — Spider/radar chart (`AcousticRadarChart`) that plots each room's acoustic personality across frequency bands
- **Diff Table** — `AcousticDiffTable` highlights per-band differences and provides an automatic impact analysis summary
- **Compare Math** — In-app overlay with a full mathematical breakdown: RT60 deltas per band, NRC delta, Schroeder frequency delta, volume delta, and plain-English interpretation
- **Keyboard Shortcut** — `Escape` to return to the main menu

### 🎨 User Experience
- **Synthwave Theme** — Beautiful purple/amber/pink dark mode design
- **Modular Navigation** — Main menu with quick access to all features
- **Keyboard Shortcuts** — Efficient navigation with hotkeys
- **Interactive Help** — Built-in "How It Works" physics explainer (Ctrl+H)
- **State Persistence** — Auto-save/restore functionality

---

## 📸 Screenshot

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ACOUSTICA -- REVERB & ROOM MODE ANALYZER          Sabine  Axial Modes  RT60    │
│  ? How It Works        ~ Reset        v Export        ♫ Listen                  │
├──────────────────────┬───────────────────────────────┬──────────────────────────┤
│  ROOM SETTINGS       │  ROOM CANVAS -- Top-Down View │  ANALYSIS RESULTS        │
│  DIMENSIONS (m)      │                               │  RT60  (Sabine)          │
│  Width:  [6.0] [-][+]│  ┌────────────────┐           │  RT60 @ 500 Hz = 0.847 s │
│  Length: [9.0] [-][+]│  │· · · · · · · · │           │  Live -- small halls     │
│  Height: [3.0] [-][+]│  │╎ · · · ● · · · │           │                          │
│                      │  │╎ · · · ╎ · · · │           │  AXIAL ROOM MODES        │
│  MATERIALS           │  │· · · · · · · · │           │  L: 19Hz  38Hz  57Hz     │
│  Walls:  [Gypsum ▼]  │  └────────────────┘           │  W: 29Hz  57Hz  86Hz     │
│  Floor:  [Carpet ▼]  │   W=6.0m                      │  H: 57Hz  114Hz 171Hz    │
│  Ceiling:[Gypsum ▼]  │  S1  X=3.00m  Y=4.50m         │                          │
│                      │                               │  RT60 PER OCTAVE BAND    │
│  GEOMETRY            │                               │  ████████████████        │
│  Volume:  162.00 m3  │                               │  0.85 0.72 0.65 ...      │
│  Area:    198.00 m2  │                               │  125  250  500  1k ...   │
└──────────────────────┴───────────────────────────────┴──────────────────────────┘
```

---

## 🚀 Installation

### Prerequisites

- **Python 3.10+** required
- Works on macOS, Linux, and Windows

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/ohnoitstora/acoustica.git
   cd acoustica
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Acoustica**
   ```bash
   python -m src.app
   ```

### Dependencies

- `textual>=0.60.0` — Terminal UI framework
- `numpy>=1.20.0` — Audio processing and numerical calculations
- `scipy` — Signal processing for convolution reverb

---

## 💻 Usage

### Launch Methods

**Primary method (recommended):**
```bash
python -m src.app
```

**Legacy entrypoint (compatibility):**
```bash
python acoustic_analyzer.py
```

### Main Menu

On launch, you'll see the main menu with options:

1. **▶ Start Analysis** — Open the acoustic analyzer
2. **⚖️ Room Comparator** — Compare room configurations side by side
3. **⊞ Acoustic Mixer** — Real-time decay visualization
4. **🔧 Material Builder** — Create/edit custom materials
5. **📚 Material Database** — Browse, compare, and manage materials
6. **📄 View Saved Reports** — Browse exported reports
7. **🧮 Treatment Calculator** — Calculate treatment requirements

---

## ⌨️ Keyboard Shortcuts

### Global Shortcuts
| Key | Action |
|-----|--------|
| `Ctrl+M` | Return to Main Menu |
| `Q` | Quit Application |

### Analyzer Screen
| Key | Action |
|-----|--------|
| `Ctrl+H` | How It Works (physics modal) |
| `Ctrl+R` | Reset to Default Values |
| `Ctrl+E` | Export Analysis Report |

### Canvas Controls
| Action | Result |
|--------|--------|
| Left-click inside room | Place/move sound source (max 8) |
| Right-click | Remove nearest sound source |

### Acoustic Mixer
| Key | Action |
|-----|--------|
| `Ctrl+S` | Export Mixer Report |
| `Ctrl+M` | Return to Main Menu |

---
## 📚 Feature Guide

### ⚖️ Room Comparator

Save room configurations as snapshots and compare two rooms' acoustic properties side by side:

**Saving a Snapshot:**
1. Configure a room in the Analyzer (dimensions + materials)
2. Click **💾 Save Snapshot** in the Analyzer header
3. Enter a name for the snapshot — it's saved to `snapshots/` as a JSON file

**Comparing Rooms:**
1. Open **⚖️ Room Comparator** from the main menu
2. Select a snapshot in the **Room A** and **Room B** dropdowns
3. Both panels populate with full acoustic data: dimensions, materials, RT60 per band, axial modes, Room NRC, and Schroeder frequency
4. The **RT60 Bar Chart** renders a color-coded side-by-side bar graph
5. The **Radar Chart** plots each room's frequency-domain acoustic personality
6. The **Diff Table** highlights band-by-band differences with an automatic impact summary
7. Click **📊 Compare Math** to see a detailed numerical breakdown with plain-English interpretation

**What each metric means:**
- **Room NRC** — Noise Reduction Coefficient; area-weighted average absorption across the room's surfaces (higher = more damped)
- **Schroeder Frequency** — The crossover below which discrete room modes dominate; above it, diffuse-field acoustics apply
- **RT60 Δ** — Positive = Room B is more reverberant; negative = Room B is more damped

---

### 🎧 Audio Simulation (Listen Feature)

The **♫ Listen** button in the analyzer opens an audio generation modal:

**What it does:**
1. **Generates Test Signal** — Creates a 440 Hz sine wave (A4 note)
2. **Calculates Impulse Response** — Synthetic IR based on your room's RT60 values
3. **Applies Convolution Reverb** — Simulates realistic room acoustics
4. **Exports Audio Files** — Saves to `reports/room_{timestamp}/`:
   - `report.txt` — Complete acoustic analysis
   - `dry.wav` — Original test tone (no reverb)
   - `reverb.wav` — Test tone with room acoustics applied

**Use case:** Compare audio files externally to hear how your room configuration affects sound quality.

---

### ⊞ Acoustic Mixer

Real-time visualization of sound decay across 6 frequency bands:

**Features:**
- **Material Presets** — Load absorption coefficients from the material library
- **Manual Adjustment** — Fine-tune each frequency band (125 Hz – 4 kHz)
- **+/- Buttons & Direct Input** — Increment by 0.05 steps or type exact values
- **Visual Absorption Bars** — Per-band progress bars showing absorption level
- **Frequency Focus** — Highlight specific bands to isolate their decay curve
- **Live Graph** — Watch the exponential decay curve update as you adjust values
- **Reset All / Flat 0.5** — Quick reset buttons for reflective or mid-absorption baseline
- **RT60 Calculation** — Calculated reverb time per band included in export

**How it works:**
1. Select a material preset or adjust values manually
2. Use +/- buttons or type values directly (0.00–1.00)
3. Watch the reverb decay curve update in real-time
4. Click frequency buttons ("All", "125", "250" …) to focus on a specific band
5. Export your configuration as a timestamped text report

**Physics:**
- Higher absorption → faster decay (shorter RT60)
- Lower absorption → slower decay (longer RT60)
- The graph shows exponential decay from 0 dB to -60 dB

---

### 🎨 Material Builder

Create and manage custom acoustic materials with precision:

**Features:**
- **Edit Mode** — Select an existing material from the dropdown to modify its coefficients
- **Create Mode** — Choose "< New Material >" to build a new material from scratch
- **Validation** — Real-time uniqueness checker for material names
- **Coefficient Input** — Set absorption values (0.00–1.00) for **6 frequency bands**:
  - 125 Hz, 250 Hz, 500 Hz, 1 kHz, 2 kHz, 4 kHz
- **Persistence** — Materials saved to and loaded from `custom_materials.json`
- **Export** — Generate detailed material specification reports to `reports/material/`

**Workflow:**
1. Launch Material Builder from the main menu
2. Select an existing material or choose "< New Material >"
3. Enter/modify the material name and absorption coefficients
4. Click **Save** to store the material
5. Click **Export** to generate a report (optional)

Materials are immediately available in the Analyzer's wall/floor/ceiling dropdowns and the Acoustic Mixer's preset selector.

---

### 📚 Material Database Browser

Browse, search, compare, and manage all acoustic materials:

**Features:**
- **Material List** — View all materials with their absorption coefficients for 6 frequency bands
- **Search** — Filter materials by name in real-time
- **Sort Options** — Sort by name, average absorption, low frequency, or high frequency performance
- **Visual Comparison** — Side-by-side bar charts showing absorption coefficients
- **Lock Material B** — Press `Space` to lock a material for comparison with the currently selected one
- **Export Comparison** — Generate detailed comparison reports with ASCII graphs
- **Edit/Delete** — Modify or remove materials directly from the browser

**Keyboard Shortcuts:**
| Key | Action |
|-----|--------|
| `↑/↓` | Navigate through materials |
| `Space` | Lock/Unlock Material B for comparison |
| `E` | Edit selected material |
| `D` | Delete selected material |
| `Ctrl+S` | Export comparison report |
| `Escape` | Return to main menu |

**Comparison Report Includes:**
- Material details (names)
- Frequency-by-frequency absorption comparison
- Visual ASCII bar graphs for each frequency
- Difference analysis (higher/lower/similar)
- Summary analysis with recommendations

---

### 🔧 Treatment Calculator

Calculate precise acoustic treatment requirements:

**Input Parameters:**
- **Target RT60** — Select a preset or enter a custom value:
  - Recording Studio (0.3 s)
  - Home Theater (0.5 s)
  - Lecture Hall (1.0 s)
  - Concert Hall (1.5 s)
  - Church/Cathedral (2.0 s)
  - Custom (free input)
- **Room Volume** — In cubic meters
- **Current RT60** — Your room's measured reverberation time
- **Frequency Band** — Target one of the 6 octave bands (125 Hz – 4 kHz)
- **Treatment Material** — Select from the material library
- **Price per Panel ($)** — For budget estimation

**Output (live-updating):**
- Absorption sabins needed
- Panel coverage area (m²)
- Number of panels required
- Estimated total cost ($)

**Export:** Saves a comprehensive plan to `reports/treatment/`

---

## 🔬 Physics

### Sabine's Reverberation Formula

The RT₆₀ (reverberation time) is calculated using Sabine's formula:

$$RT_{60} = \frac{0.161 \times V}{\sum (S_i \times \alpha_i)}$$

**Where:**
- **RT₆₀** = Time for sound to decay by 60 dB (seconds)
- **V** = Room volume (m³)
- **Sᵢ** = Surface area of boundary i (m²)
- **αᵢ** = Absorption coefficient at specific frequency (0.00-1.00)
  - 0.00 = Perfectly reflective (mirror)
  - 1.00 = Perfectly absorptive (anechoic)

**Quality Categories:**
- `0.0 - 0.3s` — Dead (recording booth)
- `0.3 - 0.6s` — Dry (control room)
- `0.6 - 1.2s` — Live (small venue)
- `1.2s+` — Bright (concert hall)

---

### Axial Room Modes

Standing waves occur at specific frequencies determined by room dimensions:

$$f_n = \frac{n \times c}{2L}$$

**Where:**
- **fₙ** = Modal frequency (Hz)
- **n** = Harmonic number (1, 2, 3, ...)
- **c** = Speed of sound = 343 m/s (at 20°C, sea level)
- **L** = Room dimension (Width, Length, or Height in meters)

**Why it matters:**
- Room modes cause frequency response irregularities
- Certain frequencies are amplified (resonance)
- Other frequencies are canceled (nulls)
- First 3 harmonics (fundamental + 2 overtones) are most problematic

**Example:** A 6m wide room has modes at:
- 1st: 343/(2×6) = 28.6 Hz
- 2nd: 343/6 = 57.2 Hz
- 3rd: 343×3/(2×6) = 85.8 Hz

---

### Schroeder Frequency

The Schroeder frequency marks the transition between the modal region (where discrete standing waves dominate) and the statistical region (where diffuse-field conditions apply):

$$f_{sch} = 2000 \sqrt{\frac{\overline{RT_{60}}}{V}}$$

**Where:**
- **$f_{sch}$** = Schroeder frequency (Hz)
- **$\overline{RT_{60}}$** = Average RT₆₀ across all octave bands (s)
- **V** = Room volume (m³)

**Why it matters:**
- Below $f_{sch}$ — treat the room modally (target specific room-mode frequencies)
- Above $f_{sch}$ — broadband absorption is more effective
- Smaller, more reverberant rooms have a higher Schroeder frequency

---

### Noise Reduction Coefficient (NRC)

NRC is the standardized single-number rating for how absorptive a material (or an entire room) is:

$$NRC = \frac{\alpha_{250} + \alpha_{500} + \alpha_{1k} + \alpha_{2k}}{4}$$

Rounded to the nearest **0.05**.

**Room NRC** extends this to an entire room by first computing surface-area-weighted absorption coefficients for walls, floor, and ceiling, then applying the NRC formula to the resulting values.

**Scale:**
- `0.00` — Perfectly reflective (concrete, glass)
- `0.25` — Low absorption (plywood, hard surfaces)
- `0.50–0.75` — Moderate absorption (carpet, curtains)
- `1.00` — Perfectly absorptive (anechoic treatment)

---

### Impulse Response Synthesis

For audio simulation, Acoustica generates synthetic impulse responses:

**Method:**
1. Calculate decay rate from RT60: `b = 3 × ln(10) / RT60`
2. Generate exponential decay envelope: `A(t) = e^(-b×t)`
3. Apply frequency-dependent decay (per octave band)
4. Add diffuse reflection noise
5. Convolve with test signal for realistic reverb

This approximates how a real room responds to transient sounds.

---

### Material Absorption Coefficients

Default materials included (ISO 354 compliant):

All materials are stored in `custom_materials.json` (ISO 354 compliant values):

| Material | 125 Hz | 250 Hz | 500 Hz | 1 kHz | 2 kHz | 4 kHz |
|----------|--------|--------|--------|-------|-------|-------|
| **Concrete (Bare)** | 0.01 | 0.01 | 0.02 | 0.02 | 0.03 | 0.04 |
| **Gypsum Board** | 0.29 | 0.10 | 0.05 | 0.04 | 0.07 | 0.09 |
| **Carpet (Thick)** | 0.02 | 0.06 | 0.14 | 0.37 | 0.60 | 0.65 |
| **Acoustic Foam** | 0.10 | 0.25 | 0.55 | 0.80 | 0.90 | 0.95 |
| **Hardwood Floor** | 0.15 | 0.11 | 0.10 | 0.07 | 0.06 | 0.07 |
| **Glass (Window)** | 0.18 | 0.06 | 0.04 | 0.03 | 0.02 | 0.02 |
| **Brick (Painted)** | 0.01 | 0.01 | 0.02 | 0.02 | 0.02 | 0.03 |
| **Heavy Curtain** | 0.07 | 0.31 | 0.49 | 0.75 | 0.70 | 0.60 |

**Note:** Absorption coefficients vary with frequency. Low frequencies (bass) require thicker/denser materials than high frequencies (treble). Additional custom materials can be added via the Material Builder and are appended to `custom_materials.json`.

---

## 📂 Project Structure

```
acoustica/
├── acoustic_analyzer.py          # Legacy compatibility entrypoint
├── custom_materials.json         # Material library (user-editable)
├── requirements.txt              # Python dependencies
├── README.md                     # This file
│
├── assets/
│   └── app.css                   # Textual styling (synthwave theme)
│
├── snapshots/                    # Saved room snapshots (JSON)
│
├── reports/                      # Exported reports
│   ├── analysis/                 # RT60 analysis exports
│   ├── material/                 # Material specification exports
│   ├── material_comparison/      # Material comparison reports
│   ├── treatment/                # Treatment calculator exports
│   ├── mixer/                    # Acoustic mixer exports
│   └── room_{timestamp}/         # Combined report + audio pairs (Listen feature)
│
└── src/                          # Main application source
    ├── __init__.py
    ├── app.py                    # Main Textual app & AnalyzerScreen
    ├── audio_engine.py           # Audio generation & convolution
    ├── calculator.py             # Treatment calculator screen
    ├── comparator.py             # Room comparator + snapshot system
    ├── constants.py              # Physics constants & material loader
    ├── export_report.py          # Report generation utilities
    ├── material_builder.py       # Material builder screen
    ├── material_browser.py       # Material database browser screen
    ├── menu.py                   # Main menu screen
    ├── mixer.py                  # Acoustic mixer screen
    ├── modal.py                  # Modal screens (How It Works, Listen)
    ├── physics.py                # RT60, room modes, NRC & Schroeder calculations
    ├── reports.py                # Saved reports browser screen
    ├── state.py                  # Shared application state
    ├── state_backup.py           # State persistence utilities
    └── ui_components.py          # Custom widgets (Canvas, BarChart,
                                  #   ComparisonBarChart, AcousticRadarChart,
                                  #   AcousticDiffTable)
```

---

## 🛠️ Technical Stack

- **UI Framework:** [Textual](https://github.com/Textualize/textual) — Modern TUI framework
- **Numerical Computing:** NumPy — RT60 calculations, audio processing
- **Signal Processing:** SciPy — Convolution, impulse responses
- **Language:** Python 3.10+ — Type hints, modern async/await
- **Architecture:** Modular screens with shared state management

---

## 🎓 Use Cases

### Recording Studio Design
Calculate optimal RT60 for tracking/mixing rooms, identify problematic resonances, design treatment plans with cost estimates.

### Home Theater Optimization
Achieve cinematic sound with proper reverberation control, eliminate room modes that create boomy bass.

### Podcast/Voice Recording
Create dead/dry acoustic environment ideal for voice clarity and minimal post-processing.

### Acoustic Engineering Education
Demonstrate wave physics, absorption coefficients, and room acoustics interactively.

### General Room Analysis
Understand how room geometry and materials affect sound quality before renovation or treatment purchases.

---

## 📋 Changelog

### Latest
- **Feature:** **Material Database Browser** — New screen for browsing, searching, sorting, and comparing all materials from your custom library
  - Search materials by name with real-time filtering
  - Sort by name or absorption values (average, low frequency, high frequency)
  - Side-by-side comparison with visual bar charts
  - Lock Material B (Space) to compare with current selection
  - Export detailed comparison reports with ASCII graphs and analysis
  - Edit or delete materials directly from the browser
  - Centered delete confirmation modal
- **Feature:** Added "Material Comparisons" tab to the Reports screen
- **Feature:** `material_browser.py` — New module for Material Database Browser functionality

### Previous
- **Feature:** **Room Comparator** — Save any room configuration as a named snapshot and compare two rooms side by side with full acoustic breakdowns, RT60 bar charts, radar charts, diff tables, and a detailed "Compare Math" overlay
- **Feature:** **Schroeder Frequency** — Computed per room ($f_{sch} = 2000\sqrt{RT_{60}/V}$) and displayed in the comparator panels
- **Feature:** **NRC & Room NRC** — Noise Reduction Coefficient calculated per material and as a surface-area-weighted room average; shown in comparator panels
- **Feature:** `ComparisonBarChart`, `AcousticRadarChart`, `AcousticDiffTable` — Three new custom TUI widgets powering the comparator visualizations
- **Feature:** Snapshot persistence — room snapshots saved to `snapshots/` as JSON for future sessions
- **Fix:** Resolved `NoMatches` crash when opening the Room Comparator — `set_room_a_values()` was querying DOM widgets before the screen was composed. Values are now stored in instance variables first and the DOM is only updated when the screen is already mounted.
- **Fix:** Resolved export button ID collision between the Analyzer header and Material Builder — the header `v Export` button now renders correctly with its intended dark-orange `.hdr-btn` style

---

## 🤝 Contributing

Contributions are welcome! Please feel free to:

- Report bugs or suggest features via [Issues](https://github.com/ohnoitstora/acoustica/issues)
- Submit pull requests with improvements
- Share acoustic material measurements for the library
- Improve documentation

---

## 📝 License

MIT License — See LICENSE file for details.

---

## 🔗 Links

- **Repository:** https://github.com/ohnoitstora/acoustica
- **Textual Framework:** https://github.com/Textualize/textual
- **ISO 354 Standard:** Acoustics — Measurement of sound absorption

---

## ✨ Acknowledgments

- Built with [Textual](https://github.com/Textualize/textual) by Textualize
- Absorption coefficients based on ISO 354 measurements
- Physics equations from classic acoustical engineering references
- Inspired by professional acoustic modeling tools

---

**Made with 💜 for acoustic engineers, audio professionals, and sound enthusiasts everywhere.**

