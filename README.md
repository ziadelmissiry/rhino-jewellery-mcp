# Rhino Jewellery MCP

A comprehensive Model Context Protocol (MCP) server providing **74 high-level jewelry CAD tools** for Rhino 3D. Each tool generates ready-to-execute RhinoScript Python code, designed to work alongside the [Rhino MCP](https://github.com/jingcheng-chen/rhinomcp).

Built from professional jewelry CAD workflows, GIA gemstone standards, and techniques extracted from PJ Chen's 58-video tutorial series on jewelry design in Rhino 3D.

## How It Works

```
You (or Claude) ──> rhino-jewellery-mcp ──> RhinoScript code ──> Rhino MCP ──> Rhino 3D
```

1. Call a jewelry tool (e.g., `create_solitaire_ring`)
2. The tool returns complete RhinoScript Python code as a string
3. Execute that code via `mcp__rhino__execute_rhinoscript_python_code`
4. Geometry appears in Rhino

No plugins required. Uses only vanilla RhinoScript (`rhinoscriptsyntax`) commands that ship with Rhino.

## Installation

### Prerequisites

- Python 3.10+
- [Rhino MCP](https://github.com/jingcheng-chen/rhinomcp) installed and running
- Rhino 7 or 8 open

### Setup

```bash
cd ~/rhino-jewellery-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install "mcp[cli]"
```

### Register with Claude Code

Add to `~/.mcp.json`:

```json
{
  "mcpServers": {
    "rhino": {
      "command": "uvx",
      "args": ["rhinomcp"]
    },
    "rhino-jewellery": {
      "command": "/Users/<you>/rhino-jewellery-mcp/.venv/bin/python",
      "args": ["/Users/<you>/rhino-jewellery-mcp/server.py"]
    }
  }
}
```

Restart Claude Code to load the server.

## Tool Reference (74 tools)

### Necklace & Base Structures (12 tools)

| Tool | Description |
|---|---|
| `create_necklace_base` | Anatomically-correct elliptical collar with V-deformation, split into Left/Right rails |
| `place_round_gems` | Place round brilliant-cut gems evenly along a rail curve |
| `place_baguette_gems` | Place baguette/princess-cut rectangular gems along a rail curve |
| `create_stems` | Tapered structural stems radiating outward from a rail curve |
| `place_pear_gems_at_stem_tips` | Pear/marquise-shaped gems at stem tips, pointed inward |
| `create_cushion_cut_pendant` | Cushion-cut pendant with double diamond halo |
| `create_bail` | Bail bridge connecting pendant top to necklace junction |
| `create_prongs` | Prong settings (4 or 6) around gems on a rail curve |
| `create_channel_setting` | U-channel pave metal settings with under-gallery |
| `create_ring_band` | Basic ring band from torus |
| `create_gem_cutout` | Boolean-subtract gems from metal for precise seats |
| `mirror_half_necklace` | Mirror one side to create bilateral symmetry |

### Gem Library (8 tools)

Proper faceted geometry with GIA-standard proportions using polyline cross-sections + `AddLoftSrf(loft_type=2)` for faceted appearance.

| Tool | Cut Style | Key Proportions |
|---|---|---|
| `create_round_brilliant_gem` | Round brilliant | Table 57%, crown 16.2%, pavilion 43.1% |
| `create_emerald_cut_gem` | Step cut | Clipped-corner rectangles at 5 levels |
| `create_oval_gem` | Oval brilliant | Elliptical cross-sections |
| `create_pear_gem` | Pear/teardrop | Semicircle + converging point |
| `create_marquise_gem` | Navette | Pointed both ends, eye shape |
| `create_princess_cut_gem` | Princess | Square, no corner clipping |
| `create_trillion_gem` | Trillion | Triangular with convex sides |
| `create_cushion_gem` | Cushion | Rounded-corner rectangle |

### Stone Settings (6 tools)

| Tool | Setting Type | Description |
|---|---|---|
| `create_bezel_setting` | Bezel | Continuous metal collar encircling stone |
| `create_flush_setting` | Flush/Gypsy | Stone sunk into metal surface with conical bore |
| `create_pave_setting` | Pave | Hex-packed grid of tiny stones with bead prongs |
| `create_halo_setting` | Halo | Ring(s) of small stones around center stone |
| `create_claw_setting` | Claw | V-shaped prongs with curved tips |
| `create_bead_setting` | Bead | Small metal beads pushed over stone edges |

### Ring Tools (7 tools)

| Tool | Description |
|---|---|
| `ring_sizer` | US size to diameter/circumference/EU/UK conversion + reference circle |
| `create_d_profile_band` | D-profile band (flat inside, domed outside) via `AddRevSrf` |
| `create_comfort_fit_band` | Comfort-fit band (convex both sides) |
| `create_signet_ring` | Band widening to flat engraving face at top |
| `create_split_shank_ring` | Band splits into two rails at top |
| `create_solitaire_ring` | Complete solitaire: band + round brilliant + prong setting |
| `create_ring_head` | Basket/head with prongs + gallery wire |

### Assembly & Utility (6 tools)

| Tool | Description |
|---|---|
| `boolean_union_layers` | Union all objects from multiple layers into single solid |
| `array_polar` | Circular pattern array around an axis |
| `offset_curve_on_layer` | Offset a curve to create parallel path |
| `sweep1_profile` | Sweep cross-section along single rail |
| `sweep2_rails` | Sweep profile between two rail curves |
| `align_object_to_point` | Move objects by bounding-box center to target point |

### Manufacturing & Production (5 tools)

| Tool | Description |
|---|---|
| `calculate_metal_weight` | Volume x density for gold/silver/platinum weight + cost |
| `check_wall_thickness` | Verify minimum thickness for casting safety |
| `shell_object` | Hollow out solids to specified wall thickness |
| `prepare_stl_export` | Convert to jewelry-grade mesh for 3D printing |
| `check_intersections` | Detect overlapping geometry between layers |

Supported metals for weight calculation:
- `24k_gold` (19.32 g/cm3)
- `18k_yellow_gold` (15.80 g/cm3)
- `14k_gold` (13.90 g/cm3)
- `platinum` (21.45 g/cm3)
- `sterling_silver` (10.30 g/cm3)
- `palladium` (12.02 g/cm3)

### Finishing (4 tools)

| Tool | Description |
|---|---|
| `fillet_edges` | Smooth rounding on all edges (critical for casting) |
| `chamfer_edges` | Angled bevel on all edges |
| `create_engraving_text` | Text geometry for hallmark stamps (925, 750, PT950) |
| `create_texture_pattern` | Milgrain beads, hammered dents, or knurled grooves along a curve |

### Additional Jewelry Types (5 tools)

| Tool | Description |
|---|---|
| `create_bangle` | Rigid bracelet (round/oval/flat, open or closed) |
| `create_earring_base` | Stud, drop, or hoop earring structure with post |
| `create_chain_link` | Interlocking chain (cable or box pattern) |
| `create_tennis_bracelet` | Continuous gemstone line around wrist |
| `create_pendant_loop` | Simple torus loop for chain attachment |

### PJ Chen Workflow Tools (9 tools)

Techniques extracted from PJ Chen's professional jewelry CAD tutorial series.

| Tool | Technique | Source |
|---|---|---|
| `array_along_curve` | Copy object N times along a curve (milgrain core) | ArrayCrv |
| `project_curves_to_surface` | Project flat 2D curves onto 3D surfaces | Project |
| `extrude_and_intersect_ring` | Extrude flat design, boolean-intersect with ring cylinder | 2D-to-ring |
| `create_milgrain_bead` | Single 0.44mm bead sphere for array use | Milgrain prep |
| `create_petal_pattern` | Radial arc-based petal design with offset | Front View design |
| `cap_and_close` | Cap planar holes to close open polysurfaces | Post-trim cleanup |
| `fillet_curve_corners` | Round sharp corners on 2D curves before extrude | FilletCorners |
| `create_milgrain_ring` | Complete milgrain ring (band + bead rows) | Full workflow |
| `sweep_two_rails_ring_shank` | Ring shank via Sweep2 with D-profile | Shank technique |

### Advanced Jewelry Designs (12 tools)

Complex jewelry patterns extracted from 58 PJ Chen tutorial transcripts.

| Tool | Description | Source Tutorials |
|---|---|---|
| `create_eternity_ring` | Stones all around band with auto stone-count calculation | #337, #462, #497 |
| `create_cathedral_setting` | Arched supports from band to prong head | #224 |
| `create_heart_shape` | Parametric heart solid for pendants/earrings | #165, #474 |
| `create_cross_shape` | Cross solid via rectangle boolean union | #44, #162, #486 |
| `create_leaf_shape` | Organic leaf with center + side veins | #202, #536 |
| `create_snowflake` | Six-armed snowflake with branches | #149 |
| `create_infinity_band` | Twisted ring band with Z oscillation | #466, #187 |
| `create_three_stone_ring` | Center + two flanking stones with shared prongs | #69 |
| `create_cluster_setting` | Center stone surrounded by smaller stones with gallery | #166 |
| `create_crown_ring` | Band with tapered upward-pointing crown tips | #254, #354 |
| `create_vintage_ring` | Filigree scrollwork around band with center stone | #484 |
| `create_under_bezel_gallery` | Decorative window cutouts beneath bezel setting | #230 |

## Usage Examples

### Create a Solitaire Engagement Ring

```python
# Call the tool
code = create_solitaire_ring(us_size=7, gem_diameter=6.0, num_prongs=6)

# Execute in Rhino via Rhino MCP
mcp__rhino__execute_rhinoscript_python_code(code=code)
```

### Create an Eternity Band

```python
code = create_eternity_ring(
    inner_diameter=16.0,
    stone_diameter=2.0,
    stone_gap=0.15,
    band_width=3.0
)
```

### Milgrain Ring (PJ Chen Workflow)

```python
code = create_milgrain_ring(
    ring_diameter=16.0,
    bead_diameter=0.44,
    num_beads_per_row=180,
    num_rows=3
)
```

### Full Necklace Build

```python
# Step 1: Base rails
create_necklace_base(x_radius=65, y_radius=75, v_depth=25)

# Step 2: Structural stems
create_stems(rail_layer="Left_Rail", count=45, length=10)
create_stems(rail_layer="Right_Rail", count=45, length=10)

# Step 3: Gems
place_round_gems(rail_layer="Left_Rail", gem_layer="Emerald_Gems", diameter=2.0)
place_pear_gems_at_stem_tips(rail_layer="Left_Rail", gem_layer="Emerald_Pear", diameter=3.0)

# Step 4: Pendant
create_cushion_cut_pendant(center_x=0, center_y=-75, center_z=-25, size=12)
create_bail(pendant_x=0, pendant_y=-75, pendant_z=-25)
```

## Dimensional Standards

Based on PJ Chen's professional standards and GIA specifications:

| Element | Typical Range | Notes |
|---|---|---|
| Ring inner diameter | 14-18mm | US 5-8; use `ring_sizer` for conversion |
| Band width | 1.5-5mm | Wider for eternity, narrower for solitaire |
| Band thickness | 1.2-2.0mm | Minimum 0.8mm for casting |
| Prong diameter | 0.6-1.5mm | Tapers from base to tip |
| Prong height | 1.5-2.5mm | Above girdle |
| Stone gap | 0.1-0.2mm | Prevents cracking in eternity settings |
| Wall thickness | 0.5-1.0mm | Minimum for structural integrity |
| Fillet radius | 0.2-0.5mm | Critical for casting (no sharp internal corners) |
| Milgrain bead | 0.3-0.5mm | 0.44mm is PJ Chen's standard |
| Halo stones | 1.0-1.5mm | Typically 1/3 of center stone diameter |

## RhinoScript Functions Used

The generated code uses only vanilla `rhinoscriptsyntax` functions:

**Geometry Creation:** `AddSphere`, `AddCylinder`, `AddCone`, `AddTorus`, `AddBox`, `AddPipe`, `AddLoftSrf`, `AddRevSrf`, `AddSweep1`, `AddSweep2`, `AddInterpCurve`, `AddPolyline`, `AddCircle`, `AddLine`, `AddArc3Pt`, `ExtrudeCurveStraight`

**Boolean Operations:** `BooleanUnion`, `BooleanDifference`, `BooleanIntersection`

**Transforms:** `ScaleObject`, `RotateObject`, `RotateObjects`, `MirrorObject`, `MoveObject`, `CopyObject`

**Curve Analysis:** `CurveDomain`, `EvaluateCurve`, `CurveTangent`, `CurvePerpFrame`, `CurveLength`, `CurveArcLengthPoint`, `CurveClosestPoint`

**Surface Analysis:** `SurfaceVolume`, `SurfaceArea`, `OffsetSurface`, `CapPlanarHoles`, `ProjectCurveToSurface`

**Utilities:** `AddLayer`, `ObjectLayer`, `ObjectsByLayer`, `DeleteObject`, `DeleteObjects`, `BoundingBox`, `PlaneFromNormal`

## Project Structure

```
rhino-jewellery-mcp/
  server.py          # MCP server (4,511 lines, 74 tools)
  .venv/             # Python virtual environment
  transcripts/       # 58 PJ Chen tutorial transcripts (reference)
  README.md          # This file
```

## Credits

- Tool design informed by [PJ Chen Jewelry CAD Design](https://www.pjchendesign.com/) tutorial series
- Gemstone proportions from GIA (Gemological Institute of America) standards
- Built on the [Model Context Protocol](https://modelcontextprotocol.io/) by Anthropic
- Requires [Rhino MCP](https://github.com/jingcheng-chen/rhinomcp) for Rhino connectivity

## License

MIT
