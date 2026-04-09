import math
import textwrap
from app import mcp


@mcp.tool()
def boolean_union_layers(
    source_layers: str = "Metal_Band,Metal_Head,Metal_Setting",
    output_layer: str = "Metal_Unified",
) -> str:
    """Boolean union all objects from multiple layers into a single solid.

    Args:
        source_layers: Comma-separated layer names.
        output_layer: Layer for the unified result.
    """
    layers = [l.strip() for l in source_layers.split(",")]
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}")

        layers = {layers}
        all_objs = []
        for layer in layers:
            objs = rs.ObjectsByLayer(layer)
            if objs: all_objs.extend(objs)

        if len(all_objs) < 2:
            print("Need at least 2 objects for union")
        else:
            result = rs.BooleanUnion(all_objs, delete_input=False)
            if result:
                for r in result: rs.ObjectLayer(r, "{output_layer}")
                print("Unified {{}} objects into {{}}".format(len(all_objs), len(result)))
            else:
                print("Boolean union failed - objects may not overlap")
    """)


@mcp.tool()
def array_polar(
    source_layer: str = "Prong",
    count: int = 6,
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    axis: str = "Z",
    angle: float = 360.0,
    output_layer: str = "Prongs_Array",
) -> str:
    """Array objects in a circular pattern around an axis.

    Critical for prong spacing, pave layouts, any radial symmetry.

    Args:
        source_layer: Layer with objects to array.
        count: Total number of copies (including original).
        center_x/y/z: Center of rotation.
        axis: Rotation axis ("X", "Y", or "Z").
        angle: Total sweep angle in degrees.
        output_layer: Layer for the copies.
    """
    axis_vec = {"X": "(1,0,0)", "Y": "(0,1,0)", "Z": "(0,0,1)"}.get(axis, "(0,0,1)")
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}")

        objs = rs.ObjectsByLayer("{source_layer}")
        if not objs:
            print("No objects on {source_layer}")
        else:
            center = ({center_x}, {center_y}, {center_z})
            for i in range(1, {count}):
                angle = {angle} * i / {count}
                copies = rs.CopyObjects(objs)
                if copies:
                    rs.RotateObjects(copies, center, angle, {axis_vec})
                    for c in copies:
                        rs.ObjectLayer(c, "{output_layer}")

            print("Arrayed {{}} objects x {count} around {axis}-axis".format(len(objs)))
    """)


@mcp.tool()
def offset_curve_on_layer(
    source_layer: str = "Rail",
    distance: float = 2.0,
    output_layer: str = "Rail_Offset",
) -> str:
    """Offset a curve to create a parallel path.

    Args:
        source_layer: Layer with the source curve.
        distance: Offset distance in mm (positive = outward from origin).
        output_layer: Layer for the offset curve.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}")

        curves = rs.ObjectsByLayer("{source_layer}")
        if not curves:
            print("No curves on {source_layer}")
        else:
            for curve in curves:
                pt = rs.EvaluateCurve(curve, rs.CurveDomain(curve)[0])
                offset = rs.OffsetCurve(curve, (0,0,0), {distance})
                if offset:
                    for o in offset:
                        rs.ObjectLayer(o, "{output_layer}")
                    print("Offset {{}} curve(s) by {distance}mm".format(len(offset)))
                else:
                    print("Offset failed")
    """)


@mcp.tool()
def sweep1_profile(
    rail_layer: str = "Rail",
    profile_layer: str = "Profile",
    output_layer: str = "Swept_Surface",
    closed: bool = True,
) -> str:
    """Sweep a cross-section profile along a single rail curve.

    Fundamental for custom band shapes, channels, bezels with non-circular profiles.

    Args:
        rail_layer: Layer with the rail curve.
        profile_layer: Layer with the profile curve (positioned at rail start).
        output_layer: Layer for the swept surface.
        closed: Whether to close the sweep back to the start.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}")

        rails = rs.ObjectsByLayer("{rail_layer}")
        profiles = rs.ObjectsByLayer("{profile_layer}")

        if not rails or not profiles:
            print("Need curves on both {rail_layer} and {profile_layer}")
        else:
            result = rs.AddSweep1(rails[0], profiles, closed={closed})
            if result:
                for r in result:
                    rs.ObjectLayer(r, "{output_layer}")
                print("Sweep1: {{}} surface(s) created".format(len(result)))
            else:
                print("Sweep1 failed - check profile is near rail start")
    """)


@mcp.tool()
def sweep2_rails(
    rail1_layer: str = "Rail_Left",
    rail2_layer: str = "Rail_Right",
    profile_layer: str = "Profile",
    output_layer: str = "Swept_Surface",
) -> str:
    """Sweep a profile between two rail curves for varying-width shapes.

    Args:
        rail1_layer/rail2_layer: Layers with the two rail curves.
        profile_layer: Layer with the cross-section profile(s).
        output_layer: Layer for the result.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}")

        r1 = rs.ObjectsByLayer("{rail1_layer}")
        r2 = rs.ObjectsByLayer("{rail2_layer}")
        profiles = rs.ObjectsByLayer("{profile_layer}")

        if not r1 or not r2 or not profiles:
            print("Need curves on all three layers")
        else:
            result = rs.AddSweep2([r1[0], r2[0]], profiles)
            if result:
                for r in result:
                    rs.ObjectLayer(r, "{output_layer}")
                print("Sweep2: {{}} surface(s) created".format(len(result)))
            else:
                print("Sweep2 failed")
    """)


@mcp.tool()
def align_object_to_point(
    source_layer: str = "Component",
    target_x: float = 0.0,
    target_y: float = 0.0,
    target_z: float = 0.0,
) -> str:
    """Move objects so their bounding-box center lands on a target point.

    Args:
        source_layer: Layer with objects to move.
        target_x/y/z: Destination point.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        objs = rs.ObjectsByLayer("{source_layer}")
        if not objs:
            print("No objects on {source_layer}")
        else:
            bb = rs.BoundingBox(objs)
            if bb:
                cx = (bb[0][0] + bb[6][0]) / 2
                cy = (bb[0][1] + bb[6][1]) / 2
                cz = (bb[0][2] + bb[6][2]) / 2
                delta = ({target_x}-cx, {target_y}-cy, {target_z}-cz)
                rs.MoveObjects(objs, delta)
                print("Moved {{}} objects to ({target_x},{target_y},{target_z})".format(len(objs)))
    """)


@mcp.tool()
def array_along_curve(
    object_layer: str = "Bead",
    curve_layer: str = "Rail",
    count: int = 15,
    output_layer: str = "Milgrain",
) -> str:
    """Array an object along a curve path — the core milgrain technique.

    Takes one object and copies it N times evenly spaced along a curve.
    Essential for milgrain beads, stone rows, and any repeating element
    that follows a curved path.

    PJ Chen technique: create one sphere bead, then ArrayCrv along
    a projected curve to create the milgrain row.

    Args:
        object_layer: Layer with the object to array (e.g., a single bead).
        curve_layer: Layer with the path curve to array along.
        count: Number of copies along the curve.
        output_layer: Layer for the arrayed copies.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}")

        objs = rs.ObjectsByLayer("{object_layer}")
        curves = rs.ObjectsByLayer("{curve_layer}")

        if not objs or not curves:
            print("Need objects on {object_layer} and curve on {curve_layer}")
        else:
            obj = objs[0]
            curve = curves[0]
            length = rs.CurveLength(curve)
            spacing = length / {count}

            placed = 0
            for i in range({count}):
                pt = rs.CurveArcLengthPoint(curve, spacing * i)
                if pt:
                    # Get curve frame for orientation
                    param = rs.CurveClosestPoint(curve, pt)
                    frame = rs.CurvePerpFrame(curve, param)

                    copy = rs.CopyObject(obj)
                    if copy:
                        # Move from object center to curve point
                        bb = rs.BoundingBox(copy)
                        if bb:
                            center = ((bb[0][0]+bb[6][0])/2, (bb[0][1]+bb[6][1])/2, (bb[0][2]+bb[6][2])/2)
                            rs.MoveObject(copy, (pt[0]-center[0], pt[1]-center[1], pt[2]-center[2]))
                        rs.ObjectLayer(copy, "{output_layer}")
                        placed += 1

            print("Arrayed {{}} copies along curve ({count} requested)".format(placed))
    """)


@mcp.tool()
def project_curves_to_surface(
    curve_layer: str = "Design_Curves",
    surface_layer: str = "Ring_Band",
    direction: str = "Z",
    output_layer: str = "Projected_Curves",
) -> str:
    """Project flat design curves onto a curved surface.

    Critical PJ Chen technique: design your pattern flat in Front View,
    then project it onto the ring band to get curves that follow the
    3D surface. These projected curves are then used for milgrain
    ArrayCrv placement.

    Args:
        curve_layer: Layer with flat design curves.
        surface_layer: Layer with the target surface (e.g., ring band).
        direction: Projection direction ("X", "Y", or "Z").
        output_layer: Layer for the projected curves.
    """
    dir_map = {"X": "(1,0,0)", "Y": "(0,1,0)", "Z": "(0,0,1)"}
    dir_vec = dir_map.get(direction, "(0,0,1)")
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}")

        curves = rs.ObjectsByLayer("{curve_layer}")
        surfaces = rs.ObjectsByLayer("{surface_layer}")

        if not curves or not surfaces:
            print("Need curves on {curve_layer} and surface on {surface_layer}")
        else:
            projected = rs.ProjectCurveToSurface(curves, surfaces, {dir_vec})
            if projected:
                for p in projected:
                    rs.ObjectLayer(p, "{output_layer}")
                print("Projected {{}} curves onto surface".format(len(projected)))
            else:
                print("Projection failed - check curves are above/below surface in {direction} direction")
    """)


@mcp.tool()
def cap_and_close(
    object_layer: str = "Metal",
) -> str:
    """Cap all planar holes on objects to create closed solids.

    PJ Chen uses this after trimming/splitting to close surfaces
    into proper solids before BooleanUnion.

    Args:
        object_layer: Layer with open polysurfaces to cap.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        objs = rs.ObjectsByLayer("{object_layer}")
        if not objs:
            print("No objects on {object_layer}")
        else:
            capped = 0
            for obj in objs:
                if rs.IsPolysurface(obj) and not rs.IsPolysurfaceClosed(obj):
                    if rs.CapPlanarHoles(obj):
                        capped += 1
            print("Capped {{}} open polysurfaces on {object_layer}".format(capped))
    """)


@mcp.tool()
def fillet_curve_corners(
    curve_layer: str = "Design_Curves",
    radius: float = 0.5,
    output_layer: str = "Design_Filleted",
) -> str:
    """Round sharp corners on design curves before extruding.

    PJ Chen uses FilletCorners (0.3-0.5mm) on her petal patterns
    to soften pointed tips before creating 3D geometry.

    Args:
        curve_layer: Layer with curves to fillet.
        radius: Fillet radius in mm.
        output_layer: Layer for the filleted curves.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}")

        curves = rs.ObjectsByLayer("{curve_layer}")
        if not curves:
            print("No curves on {curve_layer}")
        else:
            count = 0
            for crv in curves:
                rs.SelectObject(crv)
            rs.Command("-_FilletCorners {radius}", False)
            rs.UnselectAllObjects()

            # Move results to output layer
            new_curves = rs.ObjectsByLayer("{curve_layer}")
            if new_curves:
                for c in new_curves:
                    rs.ObjectLayer(c, "{output_layer}")
                    count += 1
            print("Filleted {{}} curves with {radius}mm radius".format(count))
    """)


@mcp.tool()
def clear_layer(
    layer_name: str = "Ring_Setting",
) -> str:
    """Delete all objects on a named layer so you can rebuild just that element.

    Use this to selectively redo one part of a design without destroying
    everything else. For example, clear Ring_Setting and re-run the setting
    tool with adjusted parameters. The layer itself is kept (empty) so new
    objects can be added to it immediately.

    Args:
        layer_name: The layer to clear. All objects on this layer will be deleted.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{layer_name}"):
            print("Layer '{layer_name}' does not exist")
        else:
            objs = rs.ObjectsByLayer("{layer_name}")
            if not objs:
                print("Layer '{layer_name}' is already empty")
            else:
                count = len(objs)
                rs.DeleteObjects(objs)
                print("Cleared {{}} objects from layer '{layer_name}'".format(count))
    """)


@mcp.tool()
def list_scene_layers() -> str:
    """List all layers in the scene with their object counts.

    Use this to inspect what's currently in the Rhino document before
    making changes. Shows each layer name and how many objects it contains,
    helping you decide which layer to clear or rebuild.
    """
    return textwrap.dedent("""\
        import rhinoscriptsyntax as rs

        layers = rs.LayerNames()
        if not layers:
            print("No layers in document")
        else:
            print("=== Scene Layers ===")
            total = 0
            for layer in sorted(layers):
                objs = rs.ObjectsByLayer(layer)
                count = len(objs) if objs else 0
                if count > 0:
                    print("  {} : {} objects".format(layer, count))
                    total += count
            print("---")
            print("Total: {} objects across {} layers".format(total, len(layers)))
    """)


@mcp.tool()
def duplicate_and_mirror(
    source_layer: str = "Default",
    output_layer: str = "Mirrored",
    mirror_plane: str = "yz",
    offset: float = 0.0,
) -> str:
    """Duplicate objects from a layer and mirror them to create bilateral symmetry.

    Copies all objects on source_layer, mirrors them across the chosen plane
    (optionally shifted by offset along the plane's normal axis), and places
    the mirrored copies on output_layer.

    Args:
        source_layer: Layer containing the original objects to mirror.
        output_layer: Layer to receive the mirrored copies.
        mirror_plane: Plane to mirror across — "xy", "xz", or "yz". Default "yz".
        offset: Shift of the mirror plane along its normal axis (mm). Default 0.0.

    Returns:
        RhinoScript Python code ready for execute_rhinoscript_python_code.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        source_layer  = "{source_layer}"
        output_layer  = "{output_layer}"
        mirror_plane  = "{mirror_plane}".lower()
        offset        = {offset}

        # Ensure output layer exists
        if not rs.IsLayer(output_layer):
            rs.AddLayer(output_layer)

        if not rs.IsLayer(source_layer):
            print("Source layer '{{}}' not found.".format(source_layer))
        else:
            objs = rs.ObjectsByLayer(source_layer)
            if not objs:
                print("No objects found on source layer '{{}}'.".format(source_layer))
            else:
                # Define mirror plane origin and normal
                if mirror_plane == "xy":
                    origin = (0.0, 0.0, offset)
                    normal = (0.0, 0.0, 1.0)
                elif mirror_plane == "xz":
                    origin = (0.0, offset, 0.0)
                    normal = (0.0, 1.0, 0.0)
                else:  # yz (default)
                    origin = (offset, 0.0, 0.0)
                    normal = (1.0, 0.0, 0.0)

                mirrored = []
                for obj in objs:
                    copied = rs.CopyObject(obj)
                    if copied:
                        mirrored_obj = rs.MirrorObject(copied, origin, normal)
                        if mirrored_obj:
                            rs.ObjectLayer(mirrored_obj, output_layer)
                            mirrored.append(mirrored_obj)
                        else:
                            rs.DeleteObject(copied)

                print("Mirrored {{}} object(s) from '{{}}' to '{{}}' across {{}} plane (offset={{}} mm).".format(
                    len(mirrored), source_layer, output_layer, mirror_plane.upper(), offset))
    """)


@mcp.tool()
def revolve_profile(
    profile_layer: str = "Revolve_Profile",
    result_layer: str = "Revolved_Form",
    profile_points: str = "0,0;5,0;5,3;3,5;0,5",
    axis_start: str = "0,0,0",
    axis_end: str = "0,0,1",
    start_angle: float = 0.0,
    end_angle: float = 360.0,
) -> str:
    """Revolve a 2D profile curve around an axis to create gem cutters, gallery bars, domes, or any radial form.

    The six key solid modelling commands in jewellery CAD are Extrude, Revolve, Sweep1, Sweep2, Loft, and Boolean.
    This tool covers Revolve — essential for creating round gem shapes, bezels, dome tops, and rotational cutters.

    Args:
        profile_layer: Layer for the input profile curve.
        result_layer: Layer for the revolved solid.
        profile_points: Semicolon-separated 2D points (x,y) defining the profile polyline.
        axis_start: Axis start point (x,y,z).
        axis_end: Axis end point (x,y,z).
        start_angle: Start angle in degrees (0 for full revolve).
        end_angle: End angle in degrees (360 for full revolve).
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        # Parse profile points
        raw_pts = "{profile_points}".split(";")
        pts = []
        for p in raw_pts:
            coords = [float(c) for c in p.split(",")]
            if len(coords) == 2:
                pts.append((coords[0], coords[1], 0))
            else:
                pts.append(tuple(coords))

        if len(pts) < 2:
            print("ERROR: Need at least 2 profile points")
        else:
            # Setup layers
            for lyr in ["{profile_layer}", "{result_layer}"]:
                if not rs.IsLayer(lyr):
                    rs.AddLayer(lyr)

            rs.CurrentLayer("{profile_layer}")

            # Build profile curve
            if pts[0] != pts[-1]:
                pts.append(pts[0])  # close it
            crv = rs.AddPolyline(pts)

            # Parse axis
            ax_s = tuple(float(c) for c in "{axis_start}".split(","))
            ax_e = tuple(float(c) for c in "{axis_end}".split(","))

            rs.CurrentLayer("{result_layer}")

            # Revolve
            srf = rs.AddRevSrf(crv, (ax_s, ax_e), {start_angle}, {end_angle})
            if srf:
                # Cap if full revolve
                if abs({end_angle} - {start_angle}) >= 359.9:
                    capped = rs.CapPlanarHoles(srf)
                print("Revolved form created on layer '{result_layer}'")
            else:
                print("ERROR: Revolve failed — check profile and axis")
    """)


@mcp.tool()
def loft_sections(
    layer: str = "Lofted_Form",
    sections_z: str = "0,2,4,6",
    radii: str = "5,6,4,3",
    sides: int = 0,
    closed_loft: bool = False,
) -> str:
    """Loft between multiple cross-sections at different heights to create tapered or organic forms.

    Loft is one of the six key solid modelling commands. It connects two or more cross-section
    curves to build a smooth solid. Essential for tapered shanks, graduated bezels, and organic forms.

    Args:
        layer: Layer for the lofted solid.
        sections_z: Semicolon-separated Z heights for each cross-section.
        radii: Semicolon-separated radii for circular cross-sections at each height.
        sides: Number of polygon sides (0 = circle).
        closed_loft: Whether to close the loft into a loop.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        layer = "{layer}"
        if not rs.IsLayer(layer):
            rs.AddLayer(layer)
        rs.CurrentLayer(layer)

        z_vals = [float(v) for v in "{sections_z}".split(",")]
        r_vals = [float(v) for v in "{radii}".split(",")]
        sides = {sides}

        if len(z_vals) != len(r_vals):
            print("ERROR: sections_z and radii must have same count")
        elif len(z_vals) < 2:
            print("ERROR: Need at least 2 cross-sections")
        else:
            curves = []
            for z, r in zip(z_vals, r_vals):
                plane = rs.MovePlane(rs.WorldXYPlane(), (0, 0, z))
                if sides > 2:
                    crv = rs.AddPolygon(plane, r, sides)
                else:
                    crv = rs.AddCircle(plane, r)
                curves.append(crv)

            loft = rs.AddLoftSrf(curves, closed={closed_loft})
            if loft:
                for obj in loft:
                    capped = rs.CapPlanarHoles(obj)
                print("Lofted {{}} sections on layer '{layer}'".format(len(curves)))
            else:
                print("ERROR: Loft failed")

            # Clean up section curves
            rs.DeleteObjects(curves)
    """)


@mcp.tool()
def subd_to_nurbs(
    source_layer: str = "SubD_Ring",
    result_layer: str = "NURBS_Ring",
) -> str:
    """Convert SubD objects on a layer to NURBS polysurfaces for manufacturing.

    Selects all SubD objects on the source layer, runs ToNURBS, then validates
    the result (checks for naked edges and watertightness).

    Args:
        source_layer: Layer containing SubD objects.
        result_layer: Layer for the NURBS output.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{source_layer}"):
            print("ERROR: Layer '{source_layer}' not found")
        else:
            if not rs.IsLayer("{result_layer}"):
                rs.AddLayer("{result_layer}")

            objs = rs.ObjectsByLayer("{source_layer}")
            if not objs:
                print("ERROR: No objects on '{source_layer}'")
            else:
                converted = 0
                issues = 0
                for obj in objs:
                    obj_type = rs.ObjectType(obj)
                    if obj_type == 8192:  # SubD
                        rs.SelectObject(obj)
                        rs.Command("_ToNURBS _Enter", False)
                        rs.UnselectAllObjects()
                        # Get newly created NURBS object (last added)
                        new_objs = rs.LastCreatedObjects()
                        if new_objs:
                            for n in new_objs:
                                rs.ObjectLayer(n, "{result_layer}")
                                # Check watertight
                                if rs.IsPolysurface(n):
                                    if not rs.IsPolysurfaceClosed(n):
                                        issues += 1
                                        print("  WARNING: Open polysurface — has naked edges")
                            converted += 1

                print("Converted {{}} SubD objects to NURBS on '{result_layer}'".format(converted))
                if issues > 0:
                    print("  {{}} objects have naked edges — check with ShowEdges".format(issues))
                else:
                    print("  All objects are watertight")
    """)


@mcp.tool()
def bend_flat_to_ring(
    source_layer: str = "Flat_Design",
    result_layer: str = "Ring_Bent",
    finger_diameter: float = 17.3,
) -> str:
    """Bend a flat-modeled decorative element into a ring shape.

    A common jewelry CAD pattern: design a decoration flat, then use the Bend
    command to wrap it around a ring mandrel at the target finger size.

    Args:
        source_layer: Layer with the flat geometry to bend.
        result_layer: Layer for the bent ring result.
        finger_diameter: Target inner diameter in mm (17.3 = US size 7).
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{source_layer}"):
            print("ERROR: Layer '{source_layer}' not found")
        else:
            if not rs.IsLayer("{result_layer}"):
                rs.AddLayer("{result_layer}")

            objs = rs.ObjectsByLayer("{source_layer}")
            if not objs:
                print("ERROR: No objects on '{source_layer}'")
            else:
                # Get bounding box of flat design
                all_bb = rs.BoundingBox(objs)
                if not all_bb:
                    print("ERROR: Cannot compute bounding box")
                else:
                    # The design length should wrap around the ring circumference
                    ring_r = {finger_diameter} / 2.0
                    circumference = math.pi * {finger_diameter}

                    x_min = all_bb[0][0]
                    x_max = all_bb[1][0]
                    design_len = x_max - x_min
                    y_mid = (all_bb[0][1] + all_bb[3][1]) / 2.0
                    z_mid = (all_bb[0][2] + all_bb[4][2]) / 2.0

                    # Copy objects to result layer
                    copies = rs.CopyObjects(objs)
                    for c in copies:
                        rs.ObjectLayer(c, "{result_layer}")

                    # Select copies and bend
                    rs.SelectObjects(copies)
                    # Bend from line (flat X-axis span) to arc (ring circumference)
                    spine_start = (x_min, y_mid, z_mid)
                    spine_end = (x_max, y_mid, z_mid)
                    bend_through = (x_min + design_len / 2.0, y_mid + ring_r, z_mid)

                    cmd = "_Bend {{}},{{}},{{}} {{}},{{}},{{}} {{}},{{}},{{}}".format(
                        spine_start[0], spine_start[1], spine_start[2],
                        spine_end[0], spine_end[1], spine_end[2],
                        bend_through[0], bend_through[1], bend_through[2])
                    rs.Command(cmd, False)
                    rs.UnselectAllObjects()

                    print("Bent flat design to ring on '{result_layer}' — target {{:.1f}}mm diameter".format(
                        {finger_diameter}))
    """)


@mcp.tool()
def wirecut_pattern(
    body_layer: str = "Ring_Band",
    pattern_layer: str = "Cut_Pattern",
    result_layer: str = "Ring_Pierced",
) -> str:
    """Cut openwork/pierced patterns through a solid body using WireCut.

    Takes closed curves on the pattern layer and uses them to cut through all
    solids on the body layer, creating pierced/openwork jewelry designs.

    Args:
        body_layer: Layer containing the solid body to cut through.
        pattern_layer: Layer with closed curves defining the cut profiles.
        result_layer: Layer for the pierced result.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{body_layer}"):
            print("ERROR: Layer '{body_layer}' not found")
        elif not rs.IsLayer("{pattern_layer}"):
            print("ERROR: Layer '{pattern_layer}' not found")
        else:
            if not rs.IsLayer("{result_layer}"):
                rs.AddLayer("{result_layer}")

            bodies = rs.ObjectsByLayer("{body_layer}")
            cutters = rs.ObjectsByLayer("{pattern_layer}")

            if not bodies:
                print("ERROR: No solids on '{body_layer}'")
            elif not cutters:
                print("ERROR: No cut curves on '{pattern_layer}'")
            else:
                # Copy bodies to result layer
                body_copies = rs.CopyObjects(bodies)
                for b in body_copies:
                    rs.ObjectLayer(b, "{result_layer}")

                cuts_made = 0
                for cutter in cutters:
                    if rs.IsCurveClosed(cutter):
                        for body in body_copies:
                            rs.UnselectAllObjects()
                            rs.SelectObject(body)
                            rs.Command("_WireCut _SelID {{}} _BothSides=Yes _Enter".format(
                                rs.coerceguid(cutter)), False)
                            rs.UnselectAllObjects()
                            cuts_made += 1

                print("WireCut: {{}} cuts through {{}} bodies on '{result_layer}'".format(
                    cuts_made, len(body_copies)))
                print("  Delete unwanted pieces manually, keep the pierced result")
    """)
