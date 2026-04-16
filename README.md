# Kicad LGA Wizard

LGA footprint creator for KiCad. This repository contains **two different tools** for creating Land Grid Array (LGA) footprints:

1. **Footprint Wizard Script** (`lga_wizard.py`) - A parametric wizard for quick generation of standard rectangular LGA footprints
2. **Interactive Plugin** (`lga_designer_plugin/`) - A full-featured interactive plugin with visual grid editor for custom layouts

Both tools create footprints with pads on the bottom copper layer (`B.Cu`), ideal for CPU-style substrates and interposers.

> ⚠️ This is an experimental script targeting KiCad 10. API details may change between KiCad versions.

## Features

### Footprint Wizard (`lga_wizard.py`)

Quick parametric generation of standard LGA footprints:

- Rectangular LGA pad array
  - Independent pitch in X and Y (non-square grids)
  - Configurable number of columns and rows
  - Pads created as SMD on `B.Cu`, `B.Mask`, and `B.Paste`
  - Pad shape selectable: rectangular, round, or rounded rectangle
- Package outline
  - Body width/length parameters
  - IPC-style beveled corner on `F.Fab`
  - Pin‑1 marker and outline on `F.SilkS`
  - Courtyard rectangle on `F.CrtYd` with configurable margin

### Interactive Plugin (`lga_designer_plugin/`)

Full-featured interactive designer with visual grid editor:

- **All features from the Footprint Wizard**, plus:
- **Interactive Grid Editor**
  - Click to toggle individual pads on/off
  - Visual preview of active (blue) and removed (dark) pads
- **Row/Column Selection**
  - Double-click to select entire rows (highlighted in orange)
  - Right-click to select entire columns (highlighted in teal)
  - Remove selected rows, columns, or their intersection with one click
  - Perfect for quickly customizing large matrices like AM5 LGA-1718
- **Staggered Pads**
  - Enable staggered layout alternating in rows OR columns
  - Configurable offset as fraction of pitch
  - Ideal for high-density interconnects
- **Multiple Layout Patterns**
  - Create split arrays with different patterns in different regions
  - Example: AM5-style with half the matrix having one pattern, half another
- **Export Options**
  - Generate footprint directly to user library
  - Preview in footprint viewer before saving
  - Save to any library from the viewer

## Requirements

- KiCad 10.x (tested with Windows build)
- Python scripting enabled in KiCad

## Installation

### Option 1: Footprint Wizard

1. Clone or download this repository
2. Copy `lga_wizard.py` to your KiCad user plugin directory:
   ```text
   C:\Users\<USER>\Documents\KiCad\10.0\scripting\plugins\
   ```
3. Restart KiCad's **Footprint Editor**

The wizard will appear as **`LGA (rectangular)`** in the Footprint Wizard dialog.

### Option 2: Interactive Plugin

1. Clone or download this repository
2. Copy the entire `lga_designer_plugin` folder to your KiCad plugins directory:
   ```text
   C:\Users\<USER>\Documents\KiCad\10.0\scripting\plugins\
   ```
3. Restart KiCad's **PCB Editor**

The plugin will appear in the toolbar or under **Tools → External Plugins → LGA Footprint Designer**.

## Usage

### Footprint Wizard

1. Open **Footprint Editor** in KiCad
2. Go to **File → Footprint Wizard…** (or **Tools → Footprint Wizard**)
3. Select **`LGA (rectangular)`** from the list
4. Adjust the parameters in the left panel and click **Update** to preview
5. Click **OK** to generate the footprint into the current library

#### Parameters

**Pads**
- `pitch_x` – pad spacing in X (mm)
- `pitch_y` – pad spacing in Y (mm)
- `size_x` – pad width (mm)
- `size_y` – pad height (mm)
- `shape` – pad shape: `rect`, `round`, or `roundrect` (default)
- `columns` (`nx`) – number of pad columns
- `rows` (`ny`) – number of pad rows

**Package**
- `width` (`X`) – body width (mm)
- `length` (`Y`) – body length (mm)
- `margin` – courtyard margin (mm)

### Interactive Plugin

1. Open **PCB Editor** in KiCad (a board must be loaded)
2. Click the **LGA Footprint Designer** toolbar button or go to **Tools → External Plugins**
3. Configure parameters in the left panel:
   - Footprint name
   - Grid dimensions (columns, rows)
   - Pitch X/Y
   - Pad size X/Y
   - Pad shape (roundrect, rect, round)
   - Roundrect corner ratio
   - Soldermask type (SMD or NSMD)
   - Staggered mode (enable/disable, select row or column staggering)
   - Stagger offset
4. Use the interactive grid on the right:
   - **Click** a pad to toggle it on/off
   - **Double-click** to select/deselect an entire row
   - **Right-click** to select/deselect an entire column
   - Use the selection buttons to remove rows, columns, or intersections
5. Click **Generate Footprint** to create and preview the footprint
6. Save the footprint to any library from the preview window

#### Tips for Large Matrices (e.g., AM5 LGA-1718)

1. Set up the full grid dimensions (e.g., 40x40 for AM5)
2. Use double-click and right-click to select rows/columns that should be removed
3. Click "Remove intersection" to clear pads at specific row/column crossings
4. Enable staggered mode if needed for your design
5. Generate and save the custom footprint

## Layers Used

- **Pads**: `B.Cu`, `B.Mask`, `B.Paste`
- **Outline**: `F.Fab`
- **Silkscreen + pin‑1 marker**: `F.SilkS`
- **Courtyard**: `F.CrtYd`

## Roadmap

Planned improvements:

- Preset templates for common packages (AM5, Intel sockets, etc.)
- Import/export pad mask configurations
- Support for non-rectangular pad shapes
- Top-side LGA footprint option
- Enhanced courtyard generation following IPC standards

Contributions via issues and pull requests are welcome – especially for pad-map data and testing on other KiCad versions.
