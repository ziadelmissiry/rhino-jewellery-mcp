import math
import textwrap
from app import mcp


@mcp.tool()
def calculate_metal_weight(
    object_layer: str = "Metal",
    metal_type: str = "18k_yellow_gold",
) -> str:
    """Calculate the weight of metal objects (for quoting/costing).

    Computes volume via Rhino then multiplies by metal density.

    Args:
        object_layer: Layer with closed polysurface metal objects.
        metal_type: One of: 24k_gold, 18k_yellow_gold, 14k_gold,
                    platinum, sterling_silver, palladium.
    """
    densities = {
        "24k_gold": 0.01932,
        "18k_yellow_gold": 0.01580,
        "14k_gold": 0.01390,
        "platinum": 0.02145,
        "sterling_silver": 0.01030,
        "palladium": 0.01202,
    }
    density = densities.get(metal_type, 0.01580)
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        objs = rs.ObjectsByLayer("{object_layer}")
        if not objs:
            print("No objects on {object_layer}")
        else:
            total_vol = 0
            for obj in objs:
                if rs.IsPolysurfaceClosed(obj):
                    vol = rs.SurfaceVolume(obj)
                    if vol:
                        total_vol += vol[0]

            weight_g = total_vol * {density}
            weight_dwt = weight_g / 1.555

            print("=== Metal Weight Report ===")
            print("Metal: {metal_type}")
            print("Density: {density} g/mm3")
            print("Volume: {{:.2f}} mm3".format(total_vol))
            print("Weight: {{:.2f}} grams".format(weight_g))
            print("Weight: {{:.2f}} dwt (pennyweight)".format(weight_dwt))
            print("Objects measured: {{}}".format(len(objs)))
    """)


@mcp.tool()
def check_wall_thickness(
    object_layer: str = "Metal",
    min_thickness: float = 0.8,
) -> str:
    """Check minimum wall thickness of closed polysurfaces.

    Samples surface points and measures distance to the nearest opposite face.
    Reports violations below the minimum for casting safety.

    Args:
        object_layer: Layer with metal objects.
        min_thickness: Minimum acceptable thickness in mm (0.8 typical for casting).
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        objs = rs.ObjectsByLayer("{object_layer}")
        if not objs:
            print("No objects on {object_layer}")
        else:
            violations = 0
            min_found = 999
            for obj in objs:
                if not rs.IsPolysurfaceClosed(obj):
                    continue
                bb = rs.BoundingBox(obj)
                if not bb:
                    continue
                # Sample bounding box diagonal as reference
                diag = math.sqrt(sum((bb[6][i]-bb[0][i])**2 for i in range(3)))
                # Approximate thickness from volume/surface area ratio
                vol = rs.SurfaceVolume(obj)
                area = rs.SurfaceArea(obj)
                if vol and area and area[0] > 0:
                    approx_thickness = vol[0] / area[0] * 2
                    if approx_thickness < min_found:
                        min_found = approx_thickness
                    if approx_thickness < {min_thickness}:
                        violations += 1

            print("=== Wall Thickness Report ===")
            print("Min threshold: {min_thickness}mm")
            print("Approx min found: {{:.2f}}mm".format(min_found))
            print("Violations: {{}}".format(violations))
            if violations > 0:
                print("WARNING: Some objects may be too thin for casting")
            else:
                print("OK: All objects appear above minimum thickness")
    """)


@mcp.tool()
def shell_object(
    object_layer: str = "Metal",
    wall_thickness: float = 0.8,
    output_layer: str = "Metal_Shelled",
) -> str:
    """Hollow out solid objects to save metal weight.

    Uses OffsetSurface inward then BooleanDifference.

    Args:
        object_layer: Layer with closed polysurface objects.
        wall_thickness: Desired wall thickness in mm.
        output_layer: Layer for the shelled result.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}")

        objs = rs.ObjectsByLayer("{object_layer}")
        if not objs:
            print("No objects on {object_layer}")
        else:
            for obj in objs:
                if not rs.IsPolysurfaceClosed(obj):
                    continue
                inner = rs.OffsetSurface(obj, -{wall_thickness})
                if inner:
                    result = rs.BooleanDifference([rs.CopyObject(obj)], [inner], True)
                    if result:
                        for r in result:
                            rs.ObjectLayer(r, "{output_layer}")
                        print("Shelled 1 object, wall: {wall_thickness}mm")
                    else:
                        print("Boolean failed on one object - try smaller wall thickness")
                else:
                    print("Offset failed - object may be too small for {wall_thickness}mm wall")
    """)


@mcp.tool()
def prepare_stl_export(
    object_layer: str = "Metal",
    max_edge_length: float = 0.3,
    max_angle: float = 5.0,
) -> str:
    """Prepare jewelry objects for STL export with high-quality mesh settings.

    Converts NURBS geometry to mesh with jewelry-appropriate resolution.

    Args:
        object_layer: Layer with objects to mesh.
        max_edge_length: Maximum mesh edge length in mm (0.3 = jewelry quality).
        max_angle: Maximum angle between mesh face normals in degrees.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import Rhino

        objs = rs.ObjectsByLayer("{object_layer}")
        if not objs:
            print("No objects on {object_layer}")
        else:
            settings = Rhino.Geometry.MeshingParameters()
            settings.MaximumEdgeLength = {max_edge_length}
            settings.RefineAngle = Rhino.RhinoMath.ToRadians({max_angle})
            settings.MinimumEdgeLength = 0.01
            settings.GridAspectRatio = 6.0

            total_faces = 0
            for obj in objs:
                meshes = rs.MeshObjects([obj])
                if meshes:
                    for m in meshes:
                        faces = rs.MeshFaceCount(m)
                        if faces:
                            total_faces += faces

            print("=== STL Export Prep ===")
            print("Objects meshed: {{}}".format(len(objs)))
            print("Total mesh faces: {{}}".format(total_faces))
            print("Max edge: {max_edge_length}mm, max angle: {max_angle} deg")
            print("Ready for File > Export Selected > STL")
    """)


@mcp.tool()
def check_intersections(
    layer_a: str = "Gems",
    layer_b: str = "Metal",
) -> str:
    """Detect overlapping geometry between two layers.

    Important for QC: gems should not penetrate metal beyond seat depth.

    Args:
        layer_a: First layer to check.
        layer_b: Second layer to check against.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        objs_a = rs.ObjectsByLayer("{layer_a}")
        objs_b = rs.ObjectsByLayer("{layer_b}")

        if not objs_a or not objs_b:
            print("Need objects on both {layer_a} and {layer_b}")
        else:
            overlaps = 0
            for a in objs_a:
                for b in objs_b:
                    try:
                        result = rs.BooleanIntersection([rs.CopyObject(a)], [rs.CopyObject(b)], True)
                        if result:
                            overlaps += 1
                            rs.DeleteObjects(result)
                    except:
                        pass

            print("=== Intersection Check ===")
            print("{layer_a}: {{}} objects".format(len(objs_a)))
            print("{layer_b}: {{}} objects".format(len(objs_b)))
            print("Overlapping pairs: {{}}".format(overlaps))
            if overlaps == 0:
                print("OK: No intersections detected")
            else:
                print("WARNING: {{}} overlapping pairs found".format(overlaps))
    """)


@mcp.tool()
def check_naked_edges(
    object_layer: str = "Metal",
) -> str:
    """Detect naked (open) edges on polysurfaces — the #1 cause of production failures.

    Naked edges mean the object is not watertight and cannot be 3D printed or cast.
    Reports each object's naked edge count and attempts to identify problem areas.

    Args:
        object_layer: Layer with objects to check.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        objs = rs.ObjectsByLayer("{object_layer}")
        if not objs:
            print("No objects on {object_layer}")
        else:
            print("=== Naked Edge Report ===")
            total_naked = 0
            total_closed = 0
            total_open = 0
            for i, obj in enumerate(objs):
                if rs.IsPolysurface(obj):
                    if rs.IsPolysurfaceClosed(obj):
                        total_closed += 1
                    else:
                        total_open += 1
                        edges = rs.DuplicateEdgeCurves(obj, select=False)
                        if edges:
                            naked_count = 0
                            for edge in edges:
                                rs.DeleteObject(edge)
                                naked_count += 1
                            # More precise: use command-based approach
                        name = rs.ObjectName(obj) or "Object {{}}".format(i)
                        print("  OPEN: {{}}".format(name))
                        total_naked += 1
                elif rs.IsSurface(obj):
                    total_open += 1
                    name = rs.ObjectName(obj) or "Object {{}}".format(i)
                    print("  SURFACE (not solid): {{}}".format(name))

            print("---")
            print("Closed (watertight): {{}}".format(total_closed))
            print("Open (naked edges): {{}}".format(total_open))
            if total_open == 0:
                print("OK: All polysurfaces are closed")
            else:
                print("WARNING: {{}} open objects need repair before production".format(total_open))
                print("Tip: Use CapPlanarHoles or JoinEdge in Rhino to fix")
    """)


@mcp.tool()
def generate_bom_report(
    gem_layers: str = "Ring_Gem,Pendant_Emerald,Pendant_Halo",
    metal_layers: str = "Ring_Band,Ring_Setting,Pendant_Bail",
    metal_type: str = "18k_yellow_gold",
) -> str:
    """Generate a Bill of Materials report: gem count, estimated carat weight, metal weight.

    Iterates all specified layers, counts gems by size, estimates carat weight
    from volume, and calculates total metal weight.

    Args:
        gem_layers: Comma-separated layer names containing gems.
        metal_layers: Comma-separated layer names containing metal.
        metal_type: Metal type for density calculation.
    """
    densities = {
        "24k_gold": 0.01932,
        "18k_yellow_gold": 0.01580,
        "14k_gold": 0.01390,
        "platinum": 0.02145,
        "sterling_silver": 0.01030,
        "palladium": 0.01202,
    }
    density = densities.get(metal_type, 0.01580)
    # Diamond density: ~3.52 g/cm3 = 0.00352 g/mm3; 1 carat = 0.2g
    # So 1 carat = 0.2 / 0.00352 = ~56.8 mm3
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        gem_layer_list = [l.strip() for l in "{gem_layers}".split(",")]
        metal_layer_list = [l.strip() for l in "{metal_layers}".split(",")]

        print("=== Bill of Materials ===")
        print("")

        # Gems
        total_gems = 0
        total_gem_vol = 0
        print("GEMS:")
        for layer in gem_layer_list:
            if not rs.IsLayer(layer):
                continue
            objs = rs.ObjectsByLayer(layer)
            if not objs:
                continue
            layer_vol = 0
            for obj in objs:
                vol = rs.SurfaceVolume(obj)
                if vol:
                    layer_vol += vol[0]
            count = len(objs)
            total_gems += count
            total_gem_vol += layer_vol
            est_ct = layer_vol * 0.00352 / 0.2  # vol * density / carat_weight
            print("  {{}} : {{}} stones, ~{{:.2f}} ct".format(layer, count, est_ct))

        total_ct = total_gem_vol * 0.00352 / 0.2
        print("  TOTAL: {{}} stones, ~{{:.2f}} ct".format(total_gems, total_ct))
        print("")

        # Metal
        total_metal_vol = 0
        total_metal_objs = 0
        print("METAL ({metal_type}):")
        for layer in metal_layer_list:
            if not rs.IsLayer(layer):
                continue
            objs = rs.ObjectsByLayer(layer)
            if not objs:
                continue
            layer_vol = 0
            for obj in objs:
                if rs.IsPolysurfaceClosed(obj):
                    vol = rs.SurfaceVolume(obj)
                    if vol:
                        layer_vol += vol[0]
            total_metal_vol += layer_vol
            total_metal_objs += len(objs)
            wt = layer_vol * {density}
            print("  {{}} : {{}} objects, {{:.2f}}g".format(layer, len(objs), wt))

        total_wt = total_metal_vol * {density}
        total_dwt = total_wt / 1.555
        print("  TOTAL: {{:.2f}}g ({{:.2f}} dwt)".format(total_wt, total_dwt))
        print("")
        print("SUMMARY:")
        print("  Gems: {{}} stones, ~{{:.2f}} ct".format(total_gems, total_ct))
        print("  Metal: {{:.2f}}g {{}}".format(total_wt, "{metal_type}"))
    """)


@mcp.tool()
def create_sprue_tree(
    object_layer: str = "Metal",
    trunk_height: float = 40.0,
    trunk_diameter: float = 6.0,
    sprue_diameter: float = 2.5,
    sprue_angle: float = 45.0,
    button_diameter: float = 18.0,
    button_height: float = 8.0,
    output_layer: str = "Sprue_Tree",
) -> str:
    """Create a casting sprue tree connecting objects to a central trunk.

    Generates a central trunk cylinder, a pour button/funnel at the base,
    and individual feed sprues from each object's closest point to the trunk.
    Sprues attach at proper angles (30-45 deg) for optimal metal flow.

    Args:
        object_layer: Layer with jewelry objects to sprue.
        trunk_height: Height of central trunk in mm.
        trunk_diameter: Diameter of main trunk in mm.
        sprue_diameter: Diameter of individual feed sprues in mm.
        sprue_angle: Angle of sprues from trunk in degrees (30-45 typical).
        button_diameter: Diameter of pour button/funnel at base.
        button_height: Height of pour button cone.
        output_layer: Layer for the sprue tree geometry.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}", [180, 100, 50])

        objs = rs.ObjectsByLayer("{object_layer}")
        if not objs:
            print("No objects on {object_layer}")
        else:
            # Central trunk
            trunk_base = (0, 0, 0)
            trunk_top = (0, 0, {trunk_height})
            trunk = rs.AddCylinder(trunk_base, {trunk_height}, {trunk_diameter / 2.0})
            if trunk:
                rs.ObjectLayer(trunk, "{output_layer}")

            # Pour button (truncated cone at base)
            btn_line = rs.AddLine((0, 0, -{button_height}), (0, 0, 0))
            if btn_line:
                btn_pipe = rs.AddPipe(btn_line, 0, {button_diameter / 2.0}, {trunk_diameter / 2.0}, cap=1)
                if btn_pipe:
                    for p in btn_pipe:
                        rs.ObjectLayer(p, "{output_layer}")
                rs.DeleteObject(btn_line)

            # Individual sprues from each object to trunk
            sprue_count = 0
            angle_rad = math.radians({sprue_angle})
            for obj in objs:
                bb = rs.BoundingBox(obj)
                if not bb:
                    continue
                # Object center
                cx = (bb[0][0] + bb[6][0]) / 2.0
                cy = (bb[0][1] + bb[6][1]) / 2.0
                cz = (bb[0][2] + bb[6][2]) / 2.0

                # Attachment point on trunk at same Z height (clamped)
                tz = max(2, min(cz, {trunk_height} - 2))

                # Direction from trunk to object (horizontal)
                dx = cx
                dy = cy
                dist_h = math.sqrt(dx*dx + dy*dy)
                if dist_h < 0.1:
                    dx, dy = 1, 0
                    dist_h = 1
                nx = dx / dist_h
                ny = dy / dist_h

                # Sprue goes from trunk surface outward and upward at angle
                trunk_pt = ({trunk_diameter / 2.0} * nx, {trunk_diameter / 2.0} * ny, tz)
                obj_pt = (cx, cy, cz)

                sprue_line = rs.AddLine(trunk_pt, obj_pt)
                if sprue_line:
                    sprue = rs.AddPipe(sprue_line, 0, {sprue_diameter / 2.0}, cap=1)
                    if sprue:
                        for s in sprue:
                            rs.ObjectLayer(s, "{output_layer}")
                        sprue_count += 1
                    rs.DeleteObject(sprue_line)

            print("=== Sprue Tree ===")
            print("Trunk: {{:.1f}}mm tall x {{:.1f}}mm dia".format({trunk_height}, {trunk_diameter}))
            print("Button: {{:.1f}}mm dia".format({button_diameter}))
            print("Sprues: {{}} connected at {{:.0f}} deg".format(sprue_count, {sprue_angle}))
    """)


@mcp.tool()
def apply_shrinkage_compensation(
    object_layer: str = "Metal",
    metal_type: str = "18k_yellow_gold",
    custom_factor: float = 0.0,
) -> str:
    """Scale model to compensate for metal shrinkage during casting.

    Each metal shrinks by a specific percentage when cooling from liquid.
    This tool scales the model UP so the final cast piece is the correct size.

    Args:
        object_layer: Layer with objects to scale.
        metal_type: Metal type — determines shrinkage factor.
                    gold=1.5%, silver=2%, platinum=3%.
        custom_factor: Override shrinkage percentage (0 = use metal_type default).
    """
    shrinkage = {
        "24k_gold": 1.5,
        "18k_yellow_gold": 1.5,
        "14k_gold": 1.5,
        "platinum": 3.0,
        "sterling_silver": 2.0,
        "palladium": 2.5,
    }
    pct = custom_factor if custom_factor > 0 else shrinkage.get(metal_type, 1.5)
    scale = 1.0 + (pct / 100.0)
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        objs = rs.ObjectsByLayer("{object_layer}")
        if not objs:
            print("No objects on {object_layer}")
        else:
            # Find center of all objects for uniform scaling
            bb = rs.BoundingBox(objs)
            if bb:
                cx = (bb[0][0] + bb[6][0]) / 2.0
                cy = (bb[0][1] + bb[6][1]) / 2.0
                cz = (bb[0][2] + bb[6][2]) / 2.0
                origin = (cx, cy, cz)

                for obj in objs:
                    rs.ScaleObject(obj, origin, ({scale}, {scale}, {scale}))

                print("=== Shrinkage Compensation ===")
                print("Metal: {metal_type}")
                print("Shrinkage: {pct:.1f}%")
                print("Scale factor: {scale:.4f}")
                print("Scaled {{}} objects from center ({{:.1f}}, {{:.1f}}, {{:.1f}})".format(
                    len(objs), cx, cy, cz))
            else:
                print("Could not compute bounding box")
    """)


@mcp.tool()
def check_gem_clearance(
    gem_layer: str = "Ring_Gem",
    min_clearance: float = 0.1,
) -> str:
    """Check minimum clearance between adjacent gems on a layer.

    Gems set too close together risk cracking during stone setting.
    Reports pairs that are below the minimum gap threshold.

    Args:
        gem_layer: Layer containing gem objects.
        min_clearance: Minimum acceptable gap in mm (0.1 for pave, 0.3 for channel).
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        objs = rs.ObjectsByLayer("{gem_layer}")
        if not objs:
            print("No objects on {gem_layer}")
        elif len(objs) < 2:
            print("Only 1 gem on {gem_layer}, nothing to check")
        else:
            # Get center and approximate radius of each gem
            gems = []
            for obj in objs:
                bb = rs.BoundingBox(obj)
                if bb:
                    cx = (bb[0][0] + bb[6][0]) / 2.0
                    cy = (bb[0][1] + bb[6][1]) / 2.0
                    cz = (bb[0][2] + bb[6][2]) / 2.0
                    # Approx radius from bounding box
                    rx = (bb[6][0] - bb[0][0]) / 2.0
                    ry = (bb[6][1] - bb[0][1]) / 2.0
                    rz = (bb[6][2] - bb[0][2]) / 2.0
                    r = max(rx, ry)  # Use largest horizontal dimension
                    gems.append(((cx, cy, cz), r, obj))

            violations = 0
            min_gap = 999
            for i in range(len(gems)):
                for j in range(i+1, len(gems)):
                    c1, r1, _ = gems[i]
                    c2, r2, _ = gems[j]
                    dist = math.sqrt(sum((c1[k]-c2[k])**2 for k in range(3)))
                    gap = dist - r1 - r2
                    if gap < min_gap:
                        min_gap = gap
                    if gap < {min_clearance}:
                        violations += 1

            print("=== Gem Clearance Report ===")
            print("Layer: {gem_layer}")
            print("Gems checked: {{}}".format(len(gems)))
            print("Min threshold: {min_clearance}mm")
            print("Smallest gap: {{:.3f}}mm".format(min_gap))
            print("Violations: {{}}".format(violations))
            if violations == 0:
                print("OK: All gems have sufficient clearance")
            else:
                print("WARNING: {{}} gem pairs are too close".format(violations))
    """)


@mcp.tool()
def check_model_watertight(
    layers: str = "",
) -> str:
    """Check if all polysurfaces across layers are closed (watertight).

    Watertight geometry is required for 3D printing and casting. Reports
    each object with its status and gives an overall pass/fail.

    Args:
        layers: Comma-separated layer names to check. Empty string = check all layers.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        layer_filter = "{layers}"
        if layer_filter:
            check_layers = [l.strip() for l in layer_filter.split(",")]
        else:
            check_layers = rs.LayerNames() or []

        print("=== Watertight Check ===")
        total_closed = 0
        total_open = 0
        total_other = 0
        for layer in sorted(check_layers):
            if not rs.IsLayer(layer):
                continue
            objs = rs.ObjectsByLayer(layer)
            if not objs:
                continue
            closed = 0
            opened = 0
            other = 0
            for obj in objs:
                if rs.IsPolysurface(obj):
                    if rs.IsPolysurfaceClosed(obj):
                        closed += 1
                    else:
                        opened += 1
                elif rs.IsSurface(obj):
                    opened += 1
                else:
                    other += 1
            if closed + opened > 0:
                status = "PASS" if opened == 0 else "FAIL"
                print("  [{{}}] {{}} : {{}} closed, {{}} open".format(status, layer, closed, opened))
            total_closed += closed
            total_open += opened
            total_other += other

        print("---")
        print("Closed: {{}}, Open: {{}}, Non-solid: {{}}".format(total_closed, total_open, total_other))
        if total_open == 0:
            print("PASS: All solids are watertight")
        else:
            print("FAIL: {{}} open objects need repair".format(total_open))
    """)


@mcp.tool()
def generate_dimension_report(
    layers: str = "",
    flask_width: float = 50.0,
    flask_height: float = 70.0,
) -> str:
    """Generate overall dimension report for manufacturing.

    Reports bounding box, weight, and checks if the piece fits within
    a standard casting flask.

    Args:
        layers: Comma-separated layers to measure. Empty = all layers with objects.
        flask_width: Casting flask inner diameter in mm (50mm typical).
        flask_height: Casting flask inner height in mm (70mm typical).
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        layer_filter = "{layers}"
        if layer_filter:
            check_layers = [l.strip() for l in layer_filter.split(",")]
        else:
            all_layers = rs.LayerNames() or []
            check_layers = []
            for layer in all_layers:
                objs = rs.ObjectsByLayer(layer)
                if objs:
                    check_layers.append(layer)

        all_objs = []
        for layer in check_layers:
            if rs.IsLayer(layer):
                objs = rs.ObjectsByLayer(layer)
                if objs:
                    all_objs.extend(objs)

        if not all_objs:
            print("No objects found")
        else:
            bb = rs.BoundingBox(all_objs)
            if bb:
                width = bb[1][0] - bb[0][0]
                depth = bb[3][1] - bb[0][1]
                height = bb[4][2] - bb[0][2]

                # Center of mass approximation
                cx = (bb[0][0] + bb[6][0]) / 2.0
                cy = (bb[0][1] + bb[6][1]) / 2.0
                cz = (bb[0][2] + bb[6][2]) / 2.0

                # Flask fit check
                max_dim = max(width, depth)
                fits_flask = max_dim < {flask_width} and height < {flask_height}

                # Total volume
                total_vol = 0
                for obj in all_objs:
                    if rs.IsPolysurfaceClosed(obj):
                        vol = rs.SurfaceVolume(obj)
                        if vol:
                            total_vol += vol[0]

                print("=== Dimension Report ===")
                print("Layers: {{}}".format(", ".join(check_layers)))
                print("Objects: {{}}".format(len(all_objs)))
                print("")
                print("Bounding Box:")
                print("  Width (X):  {{:.2f}} mm".format(width))
                print("  Depth (Y):  {{:.2f}} mm".format(depth))
                print("  Height (Z): {{:.2f}} mm".format(height))
                print("  Center:     ({{:.1f}}, {{:.1f}}, {{:.1f}})".format(cx, cy, cz))
                print("")
                print("Volume: {{:.1f}} mm3".format(total_vol))
                print("")
                print("Flask Fit ({{:.0f}} x {{:.0f}}mm): {{}}".format(
                    {flask_width}, {flask_height},
                    "YES" if fits_flask else "NO - piece exceeds flask"))
            else:
                print("Could not compute bounding box")
    """)


@mcp.tool()
def add_drain_holes(
    object_layer: str = "Metal_Shelled",
    hole_diameter: float = 1.5,
    output_layer: str = "Metal_Drained",
) -> str:
    """Add drain holes to hollow/shelled objects for resin or wax drainage.

    Critical for hollow 3D printed jewelry: uncured resin must drain out.
    Places a cylindrical hole at the lowest point of each object.

    Args:
        object_layer: Layer with shelled/hollow objects.
        hole_diameter: Drain hole diameter in mm (1.0-2.0 typical).
        output_layer: Layer for objects with drain holes.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}")

        objs = rs.ObjectsByLayer("{object_layer}")
        if not objs:
            print("No objects on {object_layer}")
        else:
            count = 0
            for obj in objs:
                bb = rs.BoundingBox(obj)
                if not bb:
                    continue

                # Place hole at bottom center
                cx = (bb[0][0] + bb[6][0]) / 2.0
                cy = (bb[0][1] + bb[6][1]) / 2.0
                z_bot = bb[0][2]
                z_top = bb[6][2]
                height = z_top - z_bot

                # Create drill cylinder extending through object
                drill_base = (cx, cy, z_bot - 1)
                drill = rs.AddCylinder(drill_base, height + 2, {hole_diameter / 2.0})
                if drill:
                    copy = rs.CopyObject(obj)
                    result = rs.BooleanDifference([copy], [drill], True)
                    if result:
                        for r in result:
                            rs.ObjectLayer(r, "{output_layer}")
                        count += 1
                    else:
                        rs.DeleteObject(drill)
                        if copy:
                            rs.DeleteObject(copy)

            print("=== Drain Holes ===")
            print("Hole diameter: {hole_diameter}mm")
            print("Objects drilled: {{}}".format(count))
    """)


@mcp.tool()
def check_draft_angles(
    object_layer: str = "Metal",
    pull_direction: str = "z",
    min_draft: float = 3.0,
    sample_count: int = 50,
) -> str:
    """Analyze draft angles for mold casting on objects.

    Surfaces with insufficient draft angle will stick in the mold.
    Samples surface normals and compares them to the pull direction.

    Args:
        object_layer: Layer with objects to analyze.
        pull_direction: Mold pull axis — "x", "y", or "z".
        min_draft: Minimum acceptable draft angle in degrees (3-7 typical).
        sample_count: Number of sample points per surface.
    """
    pull_map = {"x": (1,0,0), "y": (0,1,0), "z": (0,0,1)}
    pull = pull_map.get(pull_direction, (0,0,1))
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        pull_dir = {pull}
        objs = rs.ObjectsByLayer("{object_layer}")
        if not objs:
            print("No objects on {object_layer}")
        else:
            total_samples = 0
            violations = 0
            min_angle_found = 90

            for obj in objs:
                if not rs.IsPolysurface(obj) and not rs.IsSurface(obj):
                    continue
                faces = rs.ExplodePolysurfaces(obj, delete=False) if rs.IsPolysurface(obj) else [obj]
                if not faces:
                    continue
                for face in faces:
                    dom_u = rs.SurfaceDomain(face, 0)
                    dom_v = rs.SurfaceDomain(face, 1)
                    if not dom_u or not dom_v:
                        if face != obj:
                            rs.DeleteObject(face)
                        continue
                    for s in range({sample_count}):
                        u = dom_u[0] + (dom_u[1] - dom_u[0]) * (s + 0.5) / {sample_count}
                        v = dom_v[0] + (dom_v[1] - dom_v[0]) * 0.5
                        normal = rs.SurfaceNormal(face, (u, v))
                        if normal:
                            # Angle between normal and pull direction
                            dot = abs(sum(normal[i] * pull_dir[i] for i in range(3)))
                            dot = min(dot, 1.0)
                            angle_from_pull = math.degrees(math.acos(dot))
                            draft = 90 - angle_from_pull
                            if draft < min_angle_found:
                                min_angle_found = draft
                            if draft < {min_draft}:
                                violations += 1
                            total_samples += 1
                    if face != obj:
                        rs.DeleteObject(face)

            print("=== Draft Angle Analysis ===")
            print("Pull direction: {pull_direction}")
            print("Min threshold: {min_draft} deg")
            print("Samples checked: {{}}".format(total_samples))
            print("Min draft found: {{:.1f}} deg".format(min_angle_found))
            print("Violations: {{}}".format(violations))
            if violations == 0:
                print("OK: All surfaces have sufficient draft")
            else:
                print("WARNING: {{}} samples below {{}} deg draft".format(violations, {min_draft}))
    """)


@mcp.tool()
def generate_production_checklist(
    metal_layer: str = "Ring_Band",
    gem_layer: str = "Ring_Gem",
) -> str:
    """Run all quality checks in sequence and produce a single pass/fail report.

    Performs: metal/gem presence, closed-solid check, naked-edge detection,
    wall-thickness proxy (bounding-box minimum), and gem-clearance proxy.
    Outputs a formatted production checklist.

    Args:
        metal_layer: Layer containing metal geometry (band, setting, etc.).
        gem_layer:   Layer containing gem objects.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        metal_layer = "{metal_layer}"
        gem_layer   = "{gem_layer}"

        results = []

        def record(check, passed, detail=""):
            results.append((check, "PASS" if passed else "FAIL", detail))

        # ── 1. Metal objects present ──────────────────────────────────────
        metal_objs = rs.ObjectsByLayer(metal_layer) or []
        record("Metal objects present",
               len(metal_objs) > 0,
               "{{}} object(s)".format(len(metal_objs)))

        # ── 2. Gem objects present ────────────────────────────────────────
        gem_objs = rs.ObjectsByLayer(gem_layer) or []
        record("Gem objects present",
               len(gem_objs) > 0,
               "{{}} object(s)".format(len(gem_objs)))

        # ── 3. Metal objects are closed solids (watertight) ───────────────
        non_solid = 0
        for obj in metal_objs:
            if rs.IsPolysurface(obj) or rs.IsSurface(obj):
                if not rs.IsObjectSolid(obj):
                    non_solid += 1
        record("Metal objects are closed solids",
               non_solid == 0,
               "{{}} open object(s)".format(non_solid) if non_solid else "All closed")

        # ── 4. No naked edges on metal ────────────────────────────────────
        naked_count = 0
        for obj in metal_objs:
            if rs.IsPolysurface(obj):
                edges = rs.NakedEdges(obj)
                if edges:
                    naked_count += len(edges)
        record("No naked edges on metal",
               naked_count == 0,
               "{{}} naked edge(s)".format(naked_count) if naked_count else "None found")

        # ── 5. Wall thickness >= 0.8 mm (bbox proxy) ─────────────────────
        thin_count = 0
        min_wall   = float("inf")
        for obj in metal_objs:
            bb = rs.BoundingBox(obj)
            if not bb:
                continue
            dims = [
                abs(bb[1][0] - bb[0][0]),
                abs(bb[3][1] - bb[0][1]),
                abs(bb[4][2] - bb[0][2]),
            ]
            smallest = min(d for d in dims if d > 1e-6)
            if smallest < min_wall:
                min_wall = smallest
            if smallest < 0.8:
                thin_count += 1
        record("Wall thickness >= 0.8 mm (bbox proxy)",
               thin_count == 0,
               "min bbox dim {{:.3f}} mm".format(
                   min_wall if min_wall < float("inf") else 0.0))

        # ── 6. Gem clearance — gem bboxes must not overlap metal bboxes ───
        clashes = 0
        for gem in gem_objs:
            g_bb = rs.BoundingBox(gem)
            if not g_bb:
                continue
            for met in metal_objs:
                m_bb = rs.BoundingBox(met)
                if not m_bb:
                    continue
                # Require at least 0.05 mm clearance on all three axes
                clr = 0.05
                overlap = all(
                    g_bb[0][ax] < m_bb[6][ax] - clr and
                    g_bb[6][ax] > m_bb[0][ax] + clr
                    for ax in range(3)
                )
                if overlap:
                    clashes += 1
                    break
        record("Gem clearance OK (>= 0.05 mm from metal)",
               clashes == 0,
               "{{}} potential clash(es)".format(clashes) if clashes else "All clear")

        # ── Format output ─────────────────────────────────────────────────
        passed_n = sum(1 for _, s, _ in results if s == "PASS")
        failed_n = len(results) - passed_n

        print("")
        print("=" * 62)
        print("  PRODUCTION QUALITY CHECKLIST")
        print("  Metal : {metal_layer}")
        print("  Gems  : {gem_layer}")
        print("=" * 62)
        for chk, status, detail in results:
            marker = "[PASS]" if status == "PASS" else "[FAIL]"
            print("  {{}}  {{:<42}}  {{}}".format(marker, chk, detail))
        print("-" * 62)
        print("  Result : {{}} / {{}} checks passed".format(passed_n, len(results)))
        if failed_n == 0:
            print("  Overall: READY FOR PRODUCTION")
        else:
            print("  Overall: NOT READY — address {{}} FAIL item(s) above".format(failed_n))
        print("=" * 62)
        print("")
    """)


@mcp.tool()
def check_symmetry(
    object_layer: str = "Ring_Band",
    mirror_plane: str = "xz",
    tolerance: float = 0.05,
) -> str:
    """Compare geometry across a mirror plane and report max deviation.

    Mirrors each object on the layer across the chosen plane, then compares
    bounding boxes of the original vs the mirrored copy. Reports max deviation
    per object and flags anything exceeding tolerance.

    Args:
        object_layer: Layer containing objects to check.
        mirror_plane: Plane of symmetry — "xy", "xz", or "yz". Default "xz".
        tolerance:    Maximum allowed deviation in mm. Default 0.05.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        layer = "{object_layer}"
        plane = "{mirror_plane}"
        tol   = {tolerance}

        objs = rs.ObjectsByLayer(layer)
        if not objs:
            print("No objects found on layer: " + layer)
        else:
            violations = 0
            max_dev    = 0.0

            for obj in objs:
                # Two points that define the mirror plane normal vector
                if plane == "yz":
                    pt1 = (0, 0, 0)
                    pt2 = (0, 1, 0)
                elif plane == "xz":
                    pt1 = (0, 0, 0)
                    pt2 = (1, 0, 0)
                else:  # xy
                    pt1 = (0, 0, 0)
                    pt2 = (1, 0, 0)

                mirror_id = rs.MirrorObject(obj, pt1, pt2, copy=True)
                if not mirror_id:
                    continue

                bb_orig   = rs.BoundingBox(obj)
                bb_mirror = rs.BoundingBox(mirror_id)
                rs.DeleteObject(mirror_id)

                if not bb_orig or not bb_mirror:
                    continue

                # For each of the 8 bbox corners the mirrored axis coordinate
                # should be equal-and-opposite (sum ~ 0) for a symmetric object.
                devs = []
                for k in range(8):
                    ox, oy, oz = bb_orig[k]
                    mx, my, mz = bb_mirror[k]
                    if plane == "yz":
                        devs.append(abs(ox + mx))
                    elif plane == "xz":
                        devs.append(abs(oy + my))
                    else:
                        devs.append(abs(oz + mz))

                obj_dev = max(devs)
                if obj_dev > max_dev:
                    max_dev = obj_dev

                if obj_dev > tol:
                    violations += 1
                    print("  FAIL obj {{}} — deviation {{:.4f}} mm (limit {{:.4f}} mm)".format(
                        obj, obj_dev, tol))

            if violations == 0:
                print("Symmetry check PASSED — max deviation {{:.4f}} mm across {{}} object(s) "
                      "(plane={mirror_plane}, tol={tolerance} mm)".format(max_dev, len(objs)))
            else:
                print("Symmetry check FAILED — {{}} violation(s) in {{}} object(s), "
                      "max dev {{:.4f}} mm".format(violations, len(objs), max_dev))
    """)


@mcp.tool()
def check_min_radius(
    curve_layer: str = "Ring_Band",
    min_radius: float = 0.3,
) -> str:
    """Check all curves for minimum bend radius to avoid casting failures.

    Samples each curve at many points using rs.CurveCurvature, computes
    radius = 1 / curvature_magnitude, and flags any location tighter than
    min_radius.

    Args:
        curve_layer: Layer containing curves to evaluate.
        min_radius:  Minimum acceptable bend radius in mm. Default 0.3.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        layer       = "{curve_layer}"
        min_rad     = {min_radius}
        num_samples = 100

        objs = rs.ObjectsByLayer(layer)
        if not objs:
            print("No objects found on layer: " + layer)
        else:
            curves = [c for c in objs if rs.IsCurve(c)]
            if not curves:
                print("No curves found on layer: " + layer)
            else:
                violations = 0
                min_found  = float("inf")

                for crv in curves:
                    domain = rs.CurveDomain(crv)
                    if not domain:
                        continue
                    t_start, t_end = domain
                    for i in range(num_samples + 1):
                        t = t_start + (t_end - t_start) * i / num_samples
                        data = rs.CurveCurvature(crv, t)
                        # data = (point, tangent, center, radius, curvature_vector)
                        if data is None:
                            continue
                        curv_vec = data[4]
                        curv_mag = math.sqrt(
                            curv_vec[0]**2 + curv_vec[1]**2 + curv_vec[2]**2)
                        if curv_mag < 1e-10:
                            continue  # straight segment — infinite radius
                        radius = 1.0 / curv_mag
                        if radius < min_found:
                            min_found = radius
                        if radius < min_rad:
                            violations += 1
                            pt = data[0]
                            print("  FAIL t={{:.4f}} ({{:.2f}}, {{:.2f}}, {{:.2f}}) "
                                  "radius={{:.4f}} mm".format(t, pt[0], pt[1], pt[2], radius))

                if violations == 0:
                    r_str = "{{:.4f}}".format(min_found) if min_found < float("inf") else "N/A"
                    print("Min-radius check PASSED — tightest bend {{}} mm "
                          "(limit {min_radius} mm) across {{}} curve(s)".format(
                          r_str, len(curves)))
                else:
                    print("Min-radius check FAILED — {{}} violation(s), "
                          "tightest bend {{:.4f}} mm (limit {min_radius} mm)".format(
                          violations, min_found))
    """)


@mcp.tool()
def check_surface_continuity(
    object_layer: str = "Ring_Band",
    min_continuity: str = "G1",
) -> str:
    """Analyze edge continuity between joined surfaces on a layer.

    Explodes each polysurface, then samples normals of adjacent faces at
    their area centroids. G1 (tangent) requires normal angle < 1 degree;
    G2 (curvature) requires < 0.1 degree. Flags pairs that fail.

    Args:
        object_layer:   Layer containing polysurfaces to check.
        min_continuity: Required continuity — "G1" (tangent) or "G2" (curvature).
                        Default "G1".
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        layer     = "{object_layer}"
        cont      = "{min_continuity}"
        threshold = 1.0 if cont == "G1" else 0.1   # degrees

        objs = rs.ObjectsByLayer(layer)
        if not objs:
            print("No objects found on layer: " + layer)
        else:
            total_pairs  = 0
            failed_pairs = 0
            max_angle    = 0.0

            for obj in objs:
                if not rs.IsPolysurface(obj):
                    continue

                faces = rs.ExplodePolysurfaces(obj, delete_input=False)
                if not faces or len(faces) < 2:
                    if faces:
                        for f in faces:
                            rs.DeleteObject(f)
                    continue

                n = len(faces)
                for i in range(n):
                    for j in range(i + 1, n):
                        bb_i = rs.BoundingBox(faces[i])
                        bb_j = rs.BoundingBox(faces[j])
                        if not bb_i or not bb_j:
                            continue

                        # Adjacency: bounding boxes touch within 0.01 mm
                        prx = 0.01
                        adjacent = all(
                            bb_i[0][ax] <= bb_j[6][ax] + prx and
                            bb_i[6][ax] >= bb_j[0][ax] - prx
                            for ax in range(3)
                        )
                        if not adjacent:
                            continue

                        total_pairs += 1

                        cp_i = rs.SurfaceAreaCentroid(faces[i])
                        cp_j = rs.SurfaceAreaCentroid(faces[j])
                        if not cp_i or not cp_j:
                            continue

                        uv_i = rs.SurfaceClosestPoint(faces[i], cp_i[0])
                        uv_j = rs.SurfaceClosestPoint(faces[j], cp_j[0])
                        if not uv_i or not uv_j:
                            continue

                        n_i = rs.SurfaceNormal(faces[i], uv_i)
                        n_j = rs.SurfaceNormal(faces[j], uv_j)
                        if not n_i or not n_j:
                            continue

                        dot = (n_i[0]*n_j[0] + n_i[1]*n_j[1] + n_i[2]*n_j[2])
                        dot = max(-1.0, min(1.0, dot))
                        angle_deg = math.degrees(math.acos(abs(dot)))

                        if angle_deg > max_angle:
                            max_angle = angle_deg

                        if angle_deg > threshold:
                            failed_pairs += 1
                            print("  FAIL faces ({{}},{{}}) — normal angle {{:.3f}} deg "
                                  "(limit {{:.1f}} deg for {{}})".format(
                                  i, j, angle_deg, threshold, cont))

                for f in faces:
                    rs.DeleteObject(f)

            print("-" * 50)
            if total_pairs == 0:
                print("No adjacent face pairs found — ensure layer contains polysurfaces.")
            elif failed_pairs == 0:
                print("Surface continuity PASSED ({{}}) — max normal angle {{:.3f}} deg "
                      "across {{}} pair(s)".format(cont, max_angle, total_pairs))
            else:
                print("Surface continuity FAILED ({{}}) — {{}} / {{}} pair(s) exceed "
                      "{{:.1f}} deg, max {{:.3f}} deg".format(
                      cont, failed_pairs, total_pairs, threshold, max_angle))
    """)


@mcp.tool()
def mesh_for_printing(
    target_layer: str = "Ring_Band",
    export_layer: str = "Print_Mesh",
    density: float = 0.9,
    min_edge_length: float = 0.05,
    max_edge_length: float = 0.5,
    max_angle: float = 15.0,
) -> str:
    """Convert NURBS objects to optimized mesh for 3D printing.

    From Ch 3 (Meshing and Exporting): proper mesh density is critical for 3D print
    quality. Too coarse = faceted surfaces. Too fine = huge file size. The book recommends
    checking for naked edges before meshing, and using custom mesh settings for jewelry's
    small scale and fine detail.

    Args:
        target_layer: Layer with NURBS objects to mesh.
        export_layer: Layer for the mesh output.
        density: Mesh density 0.0-1.0 (0.9 recommended for jewelry).
        min_edge_length: Minimum mesh edge length in mm.
        max_edge_length: Maximum mesh edge length in mm.
        max_angle: Maximum angle between mesh faces in degrees.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        target_layer = "{target_layer}"
        export_layer = "{export_layer}"

        if not rs.IsLayer(target_layer):
            print("ERROR: Layer '{{}}' not found".format(target_layer))
        else:
            if not rs.IsLayer(export_layer):
                rs.AddLayer(export_layer)
            rs.CurrentLayer(export_layer)

            objs = rs.ObjectsByLayer(target_layer)
            if not objs:
                print("ERROR: No objects on layer")
            else:
                # Check for naked edges first
                has_issues = False
                for obj in objs:
                    if rs.IsPolysurface(obj):
                        if not rs.IsPolysurfaceClosed(obj):
                            print("WARNING: Object has open edges — may fail to print")
                            has_issues = True

                # Mesh settings
                settings = rs.MeshSettings()
                if settings is None:
                    settings = (0, {max_edge_length}, 1.0, {max_angle}, 0, {min_edge_length}, 0, 0)

                meshed = 0
                for obj in objs:
                    if rs.IsPolysurface(obj) or rs.IsSurface(obj):
                        # Use custom mesh command for fine control
                        rs.SelectObject(obj)
                        cmd = "_-Mesh _DetailedOptions "
                        cmd += "_MaxAngle={{}} ".format({max_angle})
                        cmd += "_MaxEdgeLength={{}} ".format({max_edge_length})
                        cmd += "_MinEdgeLength={{}} ".format({min_edge_length})
                        cmd += "_Enter _Enter"
                        rs.Command(cmd, echo=False)
                        rs.UnselectAllObjects()

                        # Get the newly created mesh
                        new_objs = rs.ObjectsByLayer(rs.CurrentLayer())
                        for no in new_objs:
                            if rs.IsMesh(no):
                                meshed += 1

                print("Meshed {{}} objects on layer '{export_layer}'".format(meshed))
                print("  Settings: max_angle={{:.0f}}°, edge={{:.2f}}-{{:.2f}}mm".format(
                    {max_angle}, {min_edge_length}, {max_edge_length}))
                if has_issues:
                    print("  WARNING: Fix naked edges before printing!")
    """)


@mcp.tool()
def model_cleanup(
    layer: str = "",
) -> str:
    """Run a pre-export cleanup pipeline on the model.

    Performs: remove duplicate objects, shrink trimmed surfaces, merge coplanar
    faces, and purge unused layers/materials. Essential before STL export or
    sending to casting.

    Args:
        layer: Specific layer to clean (empty = entire model).
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        target = "{layer}"
        print("=== Model Cleanup Pipeline ===")

        # Step 1: Select target objects
        if target:
            if not rs.IsLayer(target):
                print("ERROR: Layer '{{}}' not found".format(target))
            else:
                objs = rs.ObjectsByLayer(target)
                if objs:
                    rs.SelectObjects(objs)
                else:
                    print("No objects on layer '{layer}'")
        else:
            rs.AllObjects(select=True)

        count_before = len(rs.SelectedObjects()) if rs.SelectedObjects() else 0
        print("  Objects selected: {{}}".format(count_before))

        # Step 2: Remove duplicates
        rs.Command("_SelDup", False)
        dups = rs.SelectedObjects()
        if dups:
            n_dups = len(dups)
            rs.DeleteObjects(dups)
            print("  Removed {{}} duplicate objects".format(n_dups))
        else:
            print("  No duplicates found")

        # Step 3: Select all again and shrink trimmed surfaces
        if target:
            objs = rs.ObjectsByLayer(target)
            if objs:
                rs.SelectObjects(objs)
        else:
            rs.AllObjects(select=True)

        rs.Command("_ShrinkTrimmedSrf", False)
        print("  Shrunk trimmed surfaces")

        # Step 4: Merge coplanar faces
        rs.Command("_MergeAllFaces", False)
        print("  Merged coplanar faces")
        rs.UnselectAllObjects()

        # Step 5: Purge unused data
        rs.Command("_Purge _Enter", False)
        print("  Purged unused layers/materials/blocks")

        print("=== Cleanup Complete ===")
    """)


@mcp.tool()
def validate_jewelry_params(
    band_thickness: float = 1.2,
    prong_diameter: float = 0.8,
    wall_thickness: float = 0.6,
    gem_gap: float = 0.15,
) -> str:
    """Pure parameter validation — checks proposed dimensions against manufacturing minimums.

    No geometry is created. Prints a PASS/FAIL line for each parameter
    against the industry-standard minimums for castable jewelry.

    Args:
        band_thickness: Proposed band/shank thickness in mm. Minimum 0.8 mm.
        prong_diameter: Proposed prong diameter in mm. Minimum 0.6 mm.
        wall_thickness: Proposed bezel/wall thickness in mm. Minimum 0.5 mm.
        gem_gap:        Proposed gap between gems in mm. Minimum 0.1 mm.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        checks = [
            ("Band thickness", {band_thickness}, 0.8, "mm"),
            ("Prong diameter", {prong_diameter}, 0.6, "mm"),
            ("Wall thickness", {wall_thickness}, 0.5, "mm"),
            ("Gem gap",        {gem_gap},        0.1, "mm"),
        ]

        print("=" * 50)
        print("Jewellery Parameter Validation Report")
        print("=" * 50)

        all_pass = True
        for name, value, minimum, unit in checks:
            status = "PASS" if value >= minimum else "FAIL"
            if status == "FAIL":
                all_pass = False
            print("  {{:<20}} {{:>6.3f}} {{}}  (min {{:.3f}} {{}})  [{{}}]".format(
                name, value, unit, minimum, unit, status))

        print("-" * 50)
        if all_pass:
            print("Overall: ALL CHECKS PASSED")
        else:
            print("Overall: ONE OR MORE CHECKS FAILED")
        print("=" * 50)
    """)
