"""Parametric cable clip, built with CadQuery.

The part is a flat base plate with two mounting holes, and an upright ring in
the middle that a cable passes through. Every dimension is a parameter on
`ClipParams`, so the part can be re-generated at any size:

    uv run cable_clip.py                       # build + export, defaults
    uv run cable_clip.py --set opening_diameter=8 --outdir out/
    uv run cable_clip.py --list                # show the parameter table

Exports STEP + STL and writes `model.json` (dimensions and measured results)
for the web viewer in `cable-clip/`.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass, fields
from pathlib import Path

import cadquery as cq

# Density used for the printed mass estimate, g/cm^3 (generic PLA).
PRINT_DENSITY_G_CM3 = 1.24


class ParamError(ValueError):
    """A parameter combination that cannot be built."""


@dataclass(frozen=True)
class ClipParams:
    """Every dimension of the clip, in millimetres.

    Layout: X is the 40 mm base length, Y the 20 mm base width, Z points up
    from the underside of the base. The ring stands in the XZ plane, so the
    cable passes through it along Y.
    """

    base_length: float = 40.0  # X, overall
    base_width: float = 20.0  # Y, overall
    base_thickness: float = 4.0  # Z, base plate height
    base_edge_radius: float = 3.0  # rounding of the four base corners
    base_top_chamfer: float = 0.6  # rounding of the top outer edge (0 = skip)

    hole_diameter: float = 4.0  # M4 clearance
    hole_spacing: float = 28.0  # centre to centre, along X

    opening_diameter: float = 10.0  # cable bore
    loop_wall: float = 3.0  # ring thickness, radial
    loop_width: float = 6.0  # ring thickness, along Y
    loop_embed: float = 1.0  # how far the ring sinks into the base
    loop_bore_chamfer: float = 0.5  # lead-in at the bore mouth (0 = skip)
    loop_seam_fillet: float = 1.2  # fillet where the ring meets the base (0 = skip)

    # -- derived ------------------------------------------------------------

    @property
    def loop_outer_radius(self) -> float:
        return self.opening_diameter / 2.0 + self.loop_wall

    @property
    def loop_center_z(self) -> float:
        """Height of the ring centre above the underside of the base."""
        return self.base_thickness + self.loop_outer_radius - self.loop_embed

    @property
    def overall_height(self) -> float:
        return self.loop_center_z + self.loop_outer_radius

    @property
    def hole_positions(self) -> list[tuple[float, float]]:
        return [(-self.hole_spacing / 2.0, 0.0), (self.hole_spacing / 2.0, 0.0)]

    # -- validation ---------------------------------------------------------

    def validate(self) -> None:
        p = self
        positives = [
            "base_length", "base_width", "base_thickness", "hole_diameter",
            "hole_spacing", "opening_diameter", "loop_wall", "loop_width",
        ]
        for name in positives:
            if getattr(p, name) <= 0:
                raise ParamError(f"{name} must be > 0, got {getattr(p, name)}")
        for name in ("base_edge_radius", "base_top_chamfer", "loop_bore_chamfer",
                     "loop_seam_fillet", "loop_embed"):
            if getattr(p, name) < 0:
                raise ParamError(f"{name} must be >= 0, got {getattr(p, name)}")

        if p.hole_spacing + p.hole_diameter > p.base_length:
            raise ParamError(
                f"holes ({p.hole_spacing} c/c + {p.hole_diameter} dia) do not fit "
                f"in {p.base_length} mm of base length"
            )
        if p.hole_diameter > p.base_width - 2 * 2.0:
            raise ParamError(
                f"hole {p.hole_diameter} mm leaves < 2 mm of material to the "
                f"{p.base_width} mm base edge"
            )
        if p.hole_spacing / 2 - p.hole_diameter / 2 < p.loop_outer_radius:
            raise ParamError(
                f"ring (outer dia {2 * p.loop_outer_radius} mm) runs into the "
                f"mounting hole at {p.hole_spacing / 2} mm from centre"
            )
        if 2 * p.loop_outer_radius > p.base_width:
            raise ParamError(
                f"ring outer dia {2 * p.loop_outer_radius} mm is wider than the "
                f"{p.base_width} mm base"
            )
        if p.loop_embed >= p.base_thickness:
            raise ParamError(
                f"loop_embed {p.loop_embed} mm would push the ring through the "
                f"{p.base_thickness} mm base"
            )
        if p.loop_width > p.base_width:
            raise ParamError(f"loop_width {p.loop_width} mm exceeds the base width")
        if p.base_edge_radius > min(p.base_length, p.base_width) / 2:
            raise ParamError("base_edge_radius rounds the base away entirely")


# -- build ------------------------------------------------------------------


def build(p: ClipParams = ClipParams()) -> tuple[cq.Workplane, dict]:
    """Return (solid, notes). `notes` records which optional dress-ups applied."""
    p.validate()
    notes: dict[str, object] = {}

    base = (
        cq.Workplane("XY")
        .box(p.base_length, p.base_width, p.base_thickness, centered=(True, True, False))
    )
    if p.base_edge_radius > 0:
        base = base.edges("|Z").fillet(p.base_edge_radius)

    # Round the outer top edge of the plate while it is still a plain plate,
    # well away from the ring.
    notes["base_top_chamfer"] = "skipped (not requested)"
    if p.base_top_chamfer > 0:
        try:
            base = base.newObject(_plate_top_edges(base)).chamfer(p.base_top_chamfer)
            notes["base_top_chamfer"] = "applied"
        except Exception as exc:
            notes["base_top_chamfer"] = f"skipped ({type(exc).__name__})"

    ring = (
        cq.Workplane("XY")
        .circle(p.loop_outer_radius)
        .circle(p.opening_diameter / 2.0)
        .extrude(p.loop_width, both=True)  # tube, axis on Z, centred on the origin
        .rotate((0, 0, 0), (1, 0, 0), 90)  # axis now along Y: cable runs in Y
        .translate((0, 0, p.loop_center_z))
    )

    part = base.union(ring)

    # Fillet the closed loop where the ring skin meets the base top face.
    if p.loop_seam_fillet > 0:
        seam = _ring_seam_edges(part, p)
        if seam:
            try:
                part = part.newObject(seam).fillet(p.loop_seam_fillet)
                notes["seam_fillet"] = f"applied to {len(seam)} edges"
            except Exception as exc:  # OCC kernel errors are not typed
                notes["seam_fillet"] = f"skipped ({type(exc).__name__})"
        else:
            notes["seam_fillet"] = "skipped (no seam edges found)"

    # Lead-in so a cable can be pushed into the bore.
    if p.loop_bore_chamfer > 0:
        mouths = _bore_mouth_edges(part, p)
        try:
            part = part.newObject(mouths).chamfer(p.loop_bore_chamfer)
            notes["bore_chamfer"] = f"applied to {len(mouths)} edges"
        except Exception as exc:
            notes["bore_chamfer"] = f"skipped ({type(exc).__name__})"

    # Mounting holes, cut last so dress-ups cannot close them off.
    for hx, hy in p.hole_positions:
        pin = (
            cq.Workplane("XY", origin=(hx, hy, -1.0))
            .circle(p.hole_diameter / 2.0)
            .extrude(p.base_thickness + 2.0)
        )
        part = part.cut(pin)

    return part, notes


def _center(shape) -> cq.Vector:
    """Centre of a selector object, which may be a raw or wrapped shape."""
    shp = shape if hasattr(shape, "Center") else cq.occ_impl.shapes.Shape.cast(shape)
    return shp.Center()


def _zflat(shape) -> tuple[float, float]:
    """z extent of an edge, raw or wrapped."""
    shp = shape if hasattr(shape, "BoundingBox") else cq.occ_impl.shapes.Shape.cast(shape)
    bb = shp.BoundingBox()
    return bb.zmin, bb.zmax


def _plate_top_edges(plate: cq.Workplane) -> list:
    """Every edge of a plain plate's top face (its outer outline)."""
    return [
        e for e in plate.edges().vals()
        if abs(_zflat(e)[0] - _zflat(e)[1]) < 1e-9
        and abs(_zflat(e)[0] - plate.val().BoundingBox().zmax) < 1e-6
    ]


def _ring_seam_edges(part: cq.Workplane, p: ClipParams) -> list:
    """Closed loop where the ring stands on the base top face.

    The ring's outer surface is a cylinder about the Y axis, so at
    z = base_thickness its footprint is the rectangle |x| <= footprint_half_x,
    |y| <= loop_width / 2. Edges lying in that plane and inside that rectangle
    are the seam; the plate outline (|y| up to base_width/2) and the hole rims
    (|x| up to hole_spacing/2 + hole_diameter/2) both fall outside it.
    """
    zc = p.loop_center_z
    footprint_half_x = math.sqrt(max(p.loop_outer_radius**2 - (zc - p.base_thickness) ** 2, 0.0))
    out = []
    for edge in part.edges().vals():
        zmin, zmax = _zflat(edge)
        c = _center(edge)
        in_plane = abs(zmin - p.base_thickness) < 1e-6 and abs(zmax - p.base_thickness) < 1e-6
        inside = (
            abs(c.x) <= footprint_half_x + 1e-6
            and abs(c.y) <= p.loop_width / 2.0 + 1e-6
        )
        if in_plane and inside:
            out.append(edge)
    return out


def _bore_mouth_edges(part: cq.Workplane, p: ClipParams) -> list:
    """The two rims of the cable bore, at y = +/- loop_width / 2."""
    r = p.opening_diameter / 2.0
    out = []
    for edge in part.edges().vals():
        c = _center(edge)
        if abs(abs(c.y) - p.loop_width / 2.0) > 1e-4:
            continue
        if abs(math.hypot(c.x, c.z - p.loop_center_z) - r) < 1e-4:
            out.append(edge)
    return out


# -- measurement ------------------------------------------------------------


def measure(part: cq.Workplane) -> dict:
    solid = part.val()
    bb = solid.BoundingBox()
    # Volume is in mm^3 (model units are mm); mass estimate assumes a solid print.
    volume_mm3 = solid.Volume()
    closed = (
        all(sh.Closed() for sol in solid.Solids() for sh in sol.Shells())
        if solid.Solids()
        else bool(solid.Closed())
    )
    return {
        "valid": bool(solid.isValid()),
        "closed": closed,
        "volume_mm3": round(volume_mm3, 2),
        "surface_area_mm2": round(solid.Area(), 2),
        "bounding_box_mm": {
            "x": round(bb.xlen, 3),
            "y": round(bb.ylen, 3),
            "z": round(bb.zlen, 3),
        },
        # Estimates, not measurements: "solid" is volume x PLA density,
        # "infill_20pct" assumes 20% of that volume is plastic. Both ignore
        # perimeters, top/bottom skin and support, so a real print is heavier.
        "estimated_mass_g": {
            "solid_pla": round(volume_mm3 / 1000.0 * PRINT_DENSITY_G_CM3, 2),
            "pla_20pct_infill": round(volume_mm3 / 1000.0 * 0.2 * PRINT_DENSITY_G_CM3, 2),
        },
        "density_assumed_g_cm3": PRINT_DENSITY_G_CM3,
    }


def describe(p: ClipParams, stats: dict, notes: dict) -> dict:
    """Everything the web viewer needs: parameters, derived sizes, measurements."""
    return {
        "name": "Cable clip",
        "units": "mm",
        "parameters": {f.name: getattr(p, f.name) for f in fields(p)},
        "derived": {
            "loop_outer_diameter": round(2 * p.loop_outer_radius, 3),
            "loop_center_height": round(p.loop_center_z, 3),
            "overall_height": round(p.overall_height, 3),
            "hole_centre_x": round(p.hole_spacing / 2.0, 3),
            "hole_to_base_edge": round(p.base_width / 2 - p.hole_diameter / 2, 3),
            "base_corner_radius": p.base_edge_radius,
        },
        "measured": stats,
        "dress_up_notes": notes,
    }


# -- export -----------------------------------------------------------------


def export(part: cq.Workplane, outdir: Path, formats: list[str]) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    if "step" in formats:
        from cadquery import exporters

        path = outdir / "cable-clip.step"
        exporters.export(part, str(path), exporters.ExportTypes.STEP)
        written.append(path)
    if "stl" in formats:
        from cadquery import exporters

        path = outdir / "cable-clip.stl"
        exporters.export(
            part, str(path), exporters.ExportTypes.STL, tolerance=0.02, angularTolerance=0.1
        )
        written.append(path)
    return written


# -- CLI --------------------------------------------------------------------


def _parse_overrides(pairs: list[str]) -> dict:
    overrides = {}
    valid = {f.name: f.type for f in fields(ClipParams)}
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"--set expects name=value, got {pair!r}")
        name, raw = pair.split("=", 1)
        name = name.strip()
        if name not in valid:
            raise SystemExit(f"unknown parameter {name!r}; try --list")
        try:
            overrides[name] = float(raw)
        except ValueError:
            raise SystemExit(f"{name} needs a number, got {raw!r}")
    return overrides


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--outdir", type=Path, default=Path(__file__).parent,
                    help="where to write STEP/STL/model.json (default: cable-clip)")
    ap.add_argument("--set", action="append", default=[], metavar="NAME=VALUE",
                    help="override a dimension, e.g. --set opening_diameter=8")
    ap.add_argument("--formats", default="step,stl",
                    help="comma list: step,stl (default: step,stl)")
    ap.add_argument("--no-json", action="store_true", help="skip writing model.json")
    ap.add_argument("--list", action="store_true", help="list parameters and exit")
    args = ap.parse_args(argv)

    if args.list:
        for f in fields(ClipParams):
            print(f"{f.name:22s} = {getattr(ClipParams(), f.name):>6} mm")
        return 0

    params = ClipParams(**_parse_overrides(args.set))
    part, notes = build(params)
    stats = measure(part)
    info = describe(params, stats, notes)

    if not stats["valid"] or not stats["closed"]:
        print(f"BUILT SOLID IS BAD: valid={stats['valid']} closed={stats['closed']}",
              file=sys.stderr)
        return 1

    formats = [f.strip().lower() for f in args.formats.split(",") if f.strip()]
    written = export(part, args.outdir, formats)
    if not args.no_json:
        args.outdir.mkdir(parents=True, exist_ok=True)
        json_path = args.outdir / "model.json"
        json_path.write_text(json.dumps(info, indent=2) + "\n")
        written.append(json_path)

    print(json.dumps(info, indent=2))
    print()
    for path in written:
        print(f"wrote {path} ({path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
