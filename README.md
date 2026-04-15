# Kicad LGA Wizard

LGA footprint creator for the KiCad Footprint Wizard. It generates generic **rectangular Land Grid Array (LGA)** footprints with independent X/Y pitch and places pads on the **bottom copper** by default (ideal for CPU‑style substrates and interposers).

## Features

- Rectangular LGA pad array
  - Independent pitch in X and Y (non‑square grids)
  - Configurable number of columns and rows
  - Pads created as SMD on `B.Cu`, `B.Mask`, and `B.Paste`
- Package outline
  - Body width/length parameters
  - IPC‑style beveled corner on `F.Fab`
  - Pin‑1 marker and outline on `F.SilkS`
  - Courtyard rectangle on `F.CrtYd` with configurable margin
- Implemented as a standard **Footprint Wizard** script (`lga_wizard.py`).

> ⚠️ This is an experimental script targeting KiCad 10. API details may change between KiCad versions.

## Requirements

- KiCad 10.x (tested with Windows build)
- Python scripting enabled in KiCad

## Installation

1. Clone or download this repository.
2. Copy `lga_wizard.py` to your KiCad user plugin directory, for example on Windows:
   ```text
   C:\Users\<USER>\Documents\KiCad\10.0\scripting\plugins\
   ```
3. Restart KiCad's **Footprint Editor**.

If everything is installed correctly, the wizard will appear as **`LGA (rectangular)`** in the Footprint Wizard dialog.

## Usage

1. Open **Footprint Editor** in KiCad.
2. Go to **File → Footprint Wizard…** (or **Tools → Footprint Wizard** depending on version).
3. Select **`LGA (rectangular)`** from the list.
4. Adjust the parameters in the left panel and click **Update** to preview the footprint.
5. When satisfied, click **OK** to generate the footprint into the current library, then save as usual.

### Parameters

**Pads**
- `pitch_x` – pad spacing in X (mm).
- `pitch_y` – pad spacing in Y (mm).
- `size` – square pad size (mm).
- `columns` (`nx`) – number of pad columns.
- `rows` (`ny`) – number of pad rows.

**Package**
- `width` (`X`) – body width (mm), measured across the array.
- `length` (`Y`) – body length (mm).
- `margin` – courtyard margin (mm) added around the body.

### Layers used

- Pads: `B.Cu`, `B.Mask`, `B.Paste`
- Outline: `F.Fab`
- Silkscreen + pin‑1 marker: `F.SilkS`
- Courtyard: `F.CrtYd`

## Roadmap

Planned improvements:

- Support for **multiple pad blocks / gaps** (e.g. split arrays).
- AM5‑style LGA‑1718 helper: mask for missing pads and fixed 40×40 mm body.
- Optional generation of top‑side LGA footprints.

Contributions via issues and pull requests are welcome – especially for AM5 pad‑map data and testing on other KiCad versions.
