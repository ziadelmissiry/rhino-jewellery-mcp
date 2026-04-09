# Rhino Jewellery MCP

A comprehensive Model Context Protocol (MCP) server providing **155 high-level jewelry CAD tools** for Rhino 3D. Each tool generates ready-to-execute RhinoScript Python code, designed to work alongside the [Rhino MCP](https://github.com/jingcheng-chen/rhinomcp).

Built from professional jewelry CAD workflows, GIA gemstone standards, techniques extracted from PJ Chen's 58-video tutorial series on jewelry design in Rhino 3D, advanced techniques from *Advanced Jewellery CAD Modelling in Rhino*, and workflows from the Creative World Rhino jewelry playlist (54 tutorials).

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

### Step 1: Install Rhino MCP (required dependency)

This server generates RhinoScript code but cannot execute it alone. [Rhino MCP](https://github.com/jingcheng-chen/rhinomcp) is the bridge that sends code to Rhino 3D.

1. Install `uv` if you don't have it:
   ```bash
   # macOS
   brew install uv
   # or pip
   pip install uv
   ```

2. Install the Rhino plugin:
   - Open Rhino 7 or 8
   - Go to **Tools > Package Manager**
   - Search for **rhinomcp** and click **Install**

3. Start the Rhino MCP server:
   - In Rhino's command line, type `RunPythonScript`
   - Then run `mcpstart`
   - You should see a confirmation that the MCP socket server is running

See the [Rhino MCP repo](https://github.com/jingcheng-chen/rhinomcp) for full setup details.

### Step 2: Install Rhino Jewellery MCP

```bash
cd ~/rhino-jewellery-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install "mcp[cli]"
```

### Step 3: Register both servers with Claude Code

Both servers must be in your `~/.mcp.json`. The `rhino` entry connects to Rhino itself; the `rhino-jewellery` entry provides the 76 jewelry CAD tools.

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

Restart Claude Code to load the servers.

### Architecture

```
rhinomcp              = bridge to Rhino 3D (executes code)
rhino-jewellery-mcp   = jewelry CAD tools (generates code)

Both must be running. The jewellery server generates RhinoScript code
strings; the Rhino MCP server executes them inside Rhino.
```

### Verify

Ask Claude: "Create a size 7 solitaire ring". Geometry should appear in Rhino.

## Tool Reference (155 tools)

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

### Gem Library (10 tools)

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
| `create_asscher_cut_gem` | Asscher | Square step-cut, deep clipped corners |
| `create_radiant_cut_gem` | Radiant | Rectangular brilliant + step hybrid |

### Stone Settings (8 tools)

| Tool | Setting Type | Description |
|---|---|---|
| `create_bezel_setting` | Bezel | Continuous metal collar encircling stone |
| `create_flush_setting` | Flush/Gypsy | Stone sunk into metal surface with conical bore |
| `create_pave_setting` | Pave | Hex-packed grid of tiny stones with bead prongs |
| `create_halo_setting` | Halo | Ring(s) of small stones around center stone |
| `create_claw_setting` | Claw | V-shaped prongs with curved tips |
| `create_bead_setting` | Bead | Small metal beads pushed over stone edges |
| `create_tension_setting` | Tension | Stone held by band spring pressure |
| `create_bar_setting` | Bar | Horizontal metal bars between stones |

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

### Assembly & Utility (8 tools)

| Tool | Description |
|---|---|
| `boolean_union_layers` | Union all objects from multiple layers into single solid |
| `array_polar` | Circular pattern array around an axis |
| `offset_curve_on_layer` | Offset a curve to create parallel path |
| `sweep1_profile` | Sweep cross-section along single rail |
| `sweep2_rails` | Sweep profile between two rail curves |
| `align_object_to_point` | Move objects by bounding-box center to target point |
| `clear_layer` | Delete all objects on a named layer for selective rebuild |
| `list_scene_layers` | Print all layers with object counts for scene inspection |

### Manufacturing & Production (9 tools)

| Tool | Description |
|---|---|
| `calculate_metal_weight` | Volume x density for gold/silver/platinum weight + cost |
| `check_wall_thickness` | Verify minimum thickness for casting safety |
| `shell_object` | Hollow out solids to specified wall thickness |
| `prepare_stl_export` | Convert to jewelry-grade mesh for 3D printing |
| `check_intersections` | Detect overlapping geometry between layers |
| `create_sprue_tree` | Auto-generate casting sprue tree with trunk, button, and feed sprues |
| `apply_shrinkage_compensation` | Scale model for metal shrinkage during casting (gold 1.5%, platinum 3%) |
| `add_drain_holes` | Add drain holes to hollow objects for resin/wax 3D print drainage |
| `resize_ring` | Resize ring from one US size to another, preserving cross-section |

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

### Quality Control & Analysis (5 tools)

| Tool | Description |
|---|---|
| `check_naked_edges` | Detect open/naked edges — #1 cause of production failures |
| `check_model_watertight` | Per-object closed polysurface verification across layers |
| `check_gem_clearance` | Minimum gap between adjacent gems (pave: 0.1mm, channel: 0.3mm) |
| `check_draft_angles` | Surface normal analysis for mold casting draft requirements |
| `generate_dimension_report` | Overall dimensions, volume, and casting flask fit check |

### Bill of Materials & Reporting (1 tool)

| Tool | Description |
|---|---|
| `generate_bom_report` | Gem count, estimated carat weight, metal weight across all layers |

### Design Tools (3 tools)

| Tool | Description |
|---|---|
| `create_spiral_wire` | Helical/spiral wire for twisted wire jewelry and rope chains |
| `twist_band` | Twist deformation for ring bands and decorative twists |
| `taper_shank` | Taper deformation for narrowing ring shanks toward the setting |

### Materials & Presentation (3 tools)

| Tool | Description |
|---|---|
| `assign_metal_material` | Apply realistic metal rendering material (gold, platinum, silver, etc.) |
| `assign_gem_material` | Apply gemstone rendering material (diamond, emerald, ruby, etc.) |
| `setup_studio_lighting` | Multi-light studio setup for jewelry rendering (standard, dramatic, soft) |

### Organization & Metadata (3 tools)

| Tool | Description |
|---|---|
| `group_layer_objects` | Group all objects on a layer for easy selection and manipulation |
| `set_gem_metadata` | Attach gem type, cut, color, clarity, and estimated carat as UserText |
| `add_dimensions` | Add linear dimension annotations for manufacturing documentation |

### Clasps & Mechanisms (4 tools)

| Tool | Description |
|---|---|
| `create_toggle_clasp` | T-bar + ring toggle clasp mechanism |
| `create_lobster_clasp` | Teardrop-shaped lobster clasp with spring lever |
| `create_box_clasp` | Rectangular box clasp with tongue piece |
| `create_jump_ring` | Split ring with configurable gap angle |

### Chain Variants (4 tools)

| Tool | Description |
|---|---|
| `create_rope_chain` | Two intertwined helical wires |
| `create_ball_chain` | Spheres connected by thin wire segments |
| `create_figaro_chain` | Alternating 3 small round + 1 elongated link pattern |
| `flow_pattern_along_curve` | Array/flow an object along a target curve |

### Additional Jewelry Types (4 tools)

| Tool | Description |
|---|---|
| `create_brooch_base` | Oval front plate + pin stem + catch plate |
| `create_cufflink` | Decorative face + post + whale-back toggle bar |
| `create_tiara_base` | Semi-circular headband with graduated peaks |
| `create_bezier_band` | Custom-profile ring band from user-specified cross-section |

### Block & View Tools (5 tools)

| Tool | Description |
|---|---|
| `create_gem_block` | Convert gems to reusable block instances (file size optimization) |
| `create_section_view` | Cross-section cut through objects for internal inspection |
| `create_turntable_frames` | Capture viewport rotation frames for animation |
| `zoom_to_layer` | Zoom viewport to fit all objects on a layer |
| `set_display_mode` | Set viewport display mode (wireframe, shaded, rendered, etc.) |

### Export & Layer Utilities (4 tools)

| Tool | Description |
|---|---|
| `export_layer_stl` | Export a specific layer to STL format |
| `hide_layers_except` | Isolate specific layers by hiding all others |
| `duplicate_and_mirror` | Copy and mirror objects for bilateral symmetry |
| `validate_jewelry_params` | Check proposed dimensions against manufacturing minimums |

### Advanced CAD Techniques — from *Advanced Jewellery CAD Modelling in Rhino* (15 tools)

| Tool | Description |
|---|---|
| `revolve_profile` | Revolve a 2D profile around an axis — gem cutters, domes, gallery bars |
| `loft_sections` | Loft between cross-sections at different heights for tapered/organic forms |
| `hollow_ring` | Hollow a solid ring with wall thickness control for weight reduction |
| `create_cabochon_gem` | Create a cabochon (domed, unfaceted) gemstone — round or oval |
| `create_cabochon_setting` | Bezel setting that wraps around a cabochon stone |
| `create_filigree_cutout` | Pierced decorative cutout patterns (circles, diamonds, teardrops) |
| `create_surface_inset` | Recessed panel on curved surfaces for enamel/engraving |
| `create_ear_post` | Earring post + butterfly back with manufacturing tolerances |
| `create_hinge_mechanism` | Barrel hinge with interlocking knuckles and pin hole |
| `create_gallery_wire` | Gallery wire swept around a gemstone's pavilion |
| `create_trellis_gallery` | Open lattice gallery under a stone setting (light entry) |
| `apply_edge_softening` | Non-destructive render-only edge rounding |
| `create_wire_cuff_bangle` | Wire cuff bangle with opening gap and parallel wires |
| `mesh_for_printing` | Optimized NURBS-to-mesh conversion for 3D printing |
| `create_pave_row` | Pavé stone row with book-standard tolerances (0.25mm spacing) |

### YouTube Playlist Techniques — from Creative World Rhino Tutorials (16 tools)

| Tool | Description |
|------|-------------|
| `create_subd_ring` | Build organic SubD ring from cylinder mesh, ready for sculpting |
| `create_multipipe_ring` | Abstract designer ring from twisted line strands via MultiPipe |
| `subd_to_nurbs` | Convert SubD objects to NURBS polysurfaces with validation |
| `create_dna_ring` | DNA double-helix ring with piped strands and bridge rungs |
| `bend_flat_to_ring` | Bend a flat-modeled decoration into a ring shape at target size |
| `wirecut_pattern` | Cut openwork/pierced patterns through solids using WireCut |
| `create_lotus_pendant` | Multi-layer lotus pendant with staggered Fibonacci petal counts |
| `create_butterfly_pendant` | Symmetric butterfly pendant with wings, body, and bail |
| `create_flower_eartop` | Parametric flower stud earring with center stone and ear post |
| `create_frill_pendant` | Organic ruffled/wavy pendant from lofted wave sections |
| `create_baguette_bracelet` | Baguette-cut gem bracelet with channel settings |
| `apply_texture_to_bangle` | Wrap flat texture pattern onto bangle via FlowAlongSrf |
| `model_cleanup` | Pre-export pipeline: SelDup, ShrinkTrimmedSrf, MergeAllFaces, Purge |
| `create_text_on_ring` | End-to-end engraved/raised text ring workflow |
| `create_mandala_pattern` | Parametric mandala with radial symmetry for pendants/brooches |
| `flow_gems_to_surface` | Flow flat-arranged gems onto a curved surface |

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

## Layer-Based Workflow

Every tool assigns its output to named layers (e.g., `Ring_Band`, `Ring_Gem`, `Ring_Setting`). This enables **selective rebuild** — fix one part without destroying the rest.

### The Pattern

1. **Build** — each element lands on its own layer automatically
2. **Inspect** — use `list_scene_layers()` to see what's in the scene
3. **Fix** — use `clear_layer("Ring_Setting")` to remove just the setting
4. **Rebuild** — re-run only the setting tool with adjusted parameters

### Example: Fix a Ring Setting

```python
# See what's in the scene
list_scene_layers()
# Output: Ring_Band (1 object), Ring_Gem (4 objects), Ring_Setting (6 objects)

# Clear only the setting layer
clear_layer(layer_name="Ring_Setting")

# Rebuild with different parameters
create_claw_setting(gem_layer="Ring_Gem", setting_layer="Ring_Setting", prong_count=6)
```

This avoids the costly pattern of deleting everything and rebuilding from scratch.

## Dimensional Standards

Based on PJ Chen's professional standards, GIA specifications, and *Advanced Jewellery CAD Modelling in Rhino*:

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
| Pavé stone spacing | 0.20-0.28mm | 0.25mm average for 1.5mm stones |
| Pavé prong thickness | 0.4-0.6mm | 0.5mm average; height matches stone table |
| Ear post | 0.8mm x 11mm | Standard friction post diameter and length |
| Gallery wire min | 1.0mm dia | Must not extend wider than girdle |
| Hollow ring wall | 0.8mm min | For signet/solid rings; reduces casting weight |
| Polishing allowance | 0.1mm | Metal loss from polishing cast surfaces |
| Hinge pin hole | 1.0mm CAD | Drilled to 1.25mm in manufacturing |
| Cuff bangle gap | ~30° | Opening for wrist flex |

## RhinoScript Functions Used

The generated code uses only vanilla `rhinoscriptsyntax` functions:

**Geometry Creation:** `AddSphere`, `AddCylinder`, `AddCone`, `AddTorus`, `AddBox`, `AddPipe`, `AddLoftSrf`, `AddRevSrf`, `AddSweep1`, `AddSweep2`, `AddInterpCurve`, `AddPolyline`, `AddCircle`, `AddEllipse`, `AddLine`, `AddArc3Pt`, `AddPolygon`, `ExtrudeCurveStraight`

**Boolean Operations:** `BooleanUnion`, `BooleanDifference`, `BooleanIntersection`

**Transforms:** `ScaleObject`, `RotateObject`, `RotateObjects`, `MirrorObject`, `MoveObject`, `CopyObject`, `CopyObjects`, `Command` (Twist, Taper, Bend, WireCut, MultiPipe, ToSubD, ToNURBS, FlowAlongSrf, SelDup, ShrinkTrimmedSrf, MergeAllFaces, Purge, TextObject)

**Curve Analysis:** `CurveDomain`, `EvaluateCurve`, `CurveTangent`, `CurvePerpFrame`, `CurveLength`, `CurveArcLengthPoint`, `CurveClosestPoint`

**Surface Analysis:** `SurfaceVolume`, `SurfaceArea`, `OffsetSurface`, `CapPlanarHoles`, `ProjectCurveToSurface`, `IsPolysurfaceClosed`, `IsMesh`, `MeshSettings`

**Materials:** `AddMaterialToLayer`, `MaterialColor`, `MaterialReflectiveColor`, `MaterialShine`, `MaterialTransparency`, `MaterialName`

**Lights:** `AddSpotLight`, `LightColor`

**Groups:** `AddGroup`, `AddObjectsToGroup`

**Metadata:** `SetUserText`, `GetUserText`

**Dimensions:** `AddLinearDimension`, `WorldXYPlane`

**Utilities:** `AddLayer`, `ObjectLayer`, `ObjectsByLayer`, `LayerNames`, `DeleteObject`, `DeleteObjects`, `BoundingBox`, `PlaneFromNormal`, `MovePlane`, `ObjectName`, `DuplicateEdgeCurves`, `ExplodePolysurfaces`, `SurfaceDomain`, `SurfaceNormal`, `IsSurface`, `IsPolysurface`, `SelectObject`, `SelectObjects`, `UnselectAllObjects`, `AllObjects`, `LastCreatedObjects`, `SelectedObjects`, `AddMesh`, `ObjectType`, `AddSrfPt`, `OffsetSurface`, `AddLoftSrf`, `IsCurveClosed`, `ExtrudeSurface`

## Project Structure

```
rhino-jewellery-mcp/
  server.py          # MCP server (10,867 lines, 155 tools)
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
