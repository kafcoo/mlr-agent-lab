# Parametric Cable Clip (CadQuery)

Parametric 3D model of a mounting cable clip built with [CadQuery](https://cadquery.readthedocs.io/).

The part consists of a flat base plate with two M4 clearance mounting holes, rounded corners, top chamfers, and an upright circular ring in the center for cable routing.

## Dimensional Layout

- **Base Plate:** 40 mm (length) × 20 mm (width) × 4 mm (thickness), 3 mm corner radius, 0.6 mm top edge chamfer.
- **Mounting Holes:** 4.0 mm diameter (M4 clearance), 28 mm center-to-center spacing along X.
- **Cable Bore:** 10 mm inner diameter, 3 mm wall thickness (16 mm outer diameter), 6 mm width along Y, 1.2 mm seam fillet with base.

## Outputs

- `cable-clip.step` — ISO 10303 STEP CAD solid model
- `cable-clip.stl` — High-resolution triangulated surface mesh for 3D printing
- `model.json` — Calculated bounding dimensions, volume, surface area, and estimated PLA mass

## Usage

```bash
# Build and export default STEP, STL, and model.json
uv run python cable_clip.py

# Override dimensions (e.g. 12 mm cable bore)
uv run python cable_clip.py --set opening_diameter=12

# List all available parameters and defaults
uv run python cable_clip.py --list
```
