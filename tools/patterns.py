import math
import textwrap
from app import mcp


@mcp.tool()
def create_texture_pattern(
    rail_layer: str = "",
    pattern: str = "milgrain",
    spacing: float = 0.5,
    feature_size: float = 0.3,
    layer: str = "Texture",
) -> str:
    """Create decorative texture patterns along a curve or edge.

    Patterns: milgrain (row of tiny spheres), hammered (random dents),
    knurled (criss-cross grooves).

    Args:
        rail_layer: Layer with the curve to follow.
        pattern: "milgrain", "hammered", or "knurled".
        spacing: Distance between pattern features in mm.
        feature_size: Size of each feature in mm.
        layer: Layer for the texture geometry.
    """
    r = feature_size / 2.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math
        import random

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        curves = rs.ObjectsByLayer("{rail_layer}")
        if not curves:
            print("No curves on {rail_layer}")
        else:
            curve = curves[0]
            length = rs.CurveLength(curve)
            if not length:
                print("Could not measure curve length")
            else:
                pattern = "{pattern}"
                count = int(length / {spacing})

                if pattern == "milgrain":
                    for i in range(count):
                        pt = rs.CurveArcLengthPoint(curve, {spacing} * i)
                        if pt:
                            bead = rs.AddSphere(pt, {r})
                            if bead:
                                rs.ObjectLayer(bead, "{layer}")
                    print("Milgrain: {{}} beads, {feature_size}mm diameter".format(count))

                elif pattern == "hammered":
                    domain = rs.CurveDomain(curve)
                    for i in range(count):
                        param = domain[0] + (domain[1]-domain[0]) * random.random()
                        pt = rs.EvaluateCurve(curve, param)
                        if pt:
                            offset = (random.uniform(-0.5,0.5), random.uniform(-0.5,0.5), 0)
                            dent_pt = (pt[0]+offset[0], pt[1]+offset[1], pt[2]+offset[2])
                            dent = rs.AddSphere(dent_pt, {r} * random.uniform(0.7, 1.3))
                            if dent:
                                rs.ScaleObject(dent, dent_pt, (1,1,0.3))
                                rs.ObjectLayer(dent, "{layer}")
                    print("Hammered: {{}} dents".format(count))

                elif pattern == "knurled":
                    # Two sets of diagonal lines
                    for direction in [1, -1]:
                        for i in range(count):
                            pt = rs.CurveArcLengthPoint(curve, {spacing} * i)
                            if pt:
                                tangent = rs.CurveTangent(curve, rs.CurveClosestPoint(curve, pt))
                                if tangent:
                                    # Perpendicular
                                    px = -tangent[1] * direction
                                    py = tangent[0] * direction
                                    line = rs.AddLine(
                                        (pt[0]-px*{feature_size}, pt[1]-py*{feature_size}, pt[2]),
                                        (pt[0]+px*{feature_size}, pt[1]+py*{feature_size}, pt[2])
                                    )
                                    if line:
                                        pipe = rs.AddPipe(line, 0, {r*0.3}, cap=1)
                                        if pipe:
                                            for p in pipe: rs.ObjectLayer(p, "{layer}")
                                        rs.DeleteObject(line)
                    print("Knurled: {{}} grooves".format(count*2))
    """)


@mcp.tool()
def create_petal_pattern(
    num_petals: int = 4,
    petal_height: float = 5.0,
    petal_width: float = 3.0,
    offset_thickness: float = 0.4,
    layer: str = "Petal_Design",
) -> str:
    """Create a radial petal/flower pattern — PJ Chen's design starting point.

    Draws arc-based petals in the Front View, polar-arrays them, and offsets
    for thickness. This flat pattern is then used with extrude_and_intersect_ring
    to create ring-shaped pieces.

    Args:
        num_petals: Number of petals (4, 6, 8 typical).
        petal_height: Height of each petal arc.
        petal_width: Width at the base.
        offset_thickness: Curve offset for metal thickness.
        layer: Layer for the design curves.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        # Draw one petal as an arc
        hw = {petal_width} / 2.0
        h = {petal_height}

        # Petal: arc from (-hw, 0, 0) through (0, 0, h) to (hw, 0, 0)
        petal = rs.AddArc3Pt((-hw, 0, 0), (hw, 0, 0), (0, 0, h))
        if not petal:
            print("Arc creation failed")
        else:
            # Mirror to close the petal
            mirror_arc = rs.MirrorObject(petal, (0,0,0), (0,0,1), copy=True)

            # Close the petal
            base_line = rs.AddLine((-hw, 0, 0), (hw, 0, 0))

            # Join into closed curve
            all_crvs = [petal]
            if mirror_arc: all_crvs.append(mirror_arc)
            if base_line: all_crvs.append(base_line)

            joined = rs.JoinCurves(all_crvs, True)
            if joined:
                for j in joined:
                    rs.ObjectLayer(j, "{layer}")

                    # Offset for thickness (both sides)
                    off1 = rs.OffsetCurve(j, (0, 0, {petal_height}+1), {offset_thickness})
                    off2 = rs.OffsetCurve(j, (0, 0, -{petal_height}-1), {offset_thickness})
                    for off in [off1, off2]:
                        if off:
                            for o in off:
                                rs.ObjectLayer(o, "{layer}")

                    # Polar array
                    if {num_petals} > 1:
                        for i in range(1, {num_petals}):
                            angle = 360.0 * i / {num_petals}
                            copies = rs.RotateObjects(rs.ObjectsByLayer("{layer}"), (0,0,0), angle, (0,1,0), True)
                            # Note: copies stay on same layer

                print("Petal pattern: {num_petals} petals, {petal_height}mm tall, offset {offset_thickness}mm")
            else:
                print("Failed to join petal curves")
                rs.DeleteObjects(all_crvs)
    """)


@mcp.tool()
def create_heart_shape(
    width: float = 12.0,
    height: float = 14.0,
    thickness: float = 1.5,
    layer: str = "Heart",
) -> str:
    """Create a heart-shaped outline — for pendants, earrings, or ring tops.

    PJ Chen's #165/#474 technique using arcs + mirror + blend.

    Args:
        width: Heart width in mm.
        height: Heart height (tip to top of lobes).
        thickness: Metal thickness.
        layer: Layer for the heart.
    """
    hw = width / 2.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        hw = {hw}
        h = {height}

        # Heart outline: top lobes + bottom point
        pts = []
        n = 40
        for i in range(n):
            t = 2 * math.pi * i / n
            # Heart parametric equation
            x = hw * 0.9 * math.sin(t) ** 3
            y = (h/2) * (0.8125*math.cos(t) - 0.3125*math.cos(2*t) - 0.125*math.cos(3*t) - 0.0625*math.cos(4*t))
            pts.append((x, 0, y))
        pts.append(pts[0])

        outline = rs.AddInterpCurve(pts, degree=3)
        if outline:
            # Extrude for thickness
            heart = rs.ExtrudeCurveStraight(outline, (0, -{thickness/2}, 0), (0, {thickness/2}, 0))
            if heart:
                rs.CapPlanarHoles(heart)
                rs.ObjectLayer(heart, "{layer}")
            rs.DeleteObject(outline)
            print("Heart shape: {width}x{height}mm, {thickness}mm thick")
    """)


@mcp.tool()
def create_cross_shape(
    arm_length: float = 10.0,
    arm_width: float = 4.0,
    thickness: float = 1.5,
    corner_radius: float = 0.5,
    layer: str = "Cross",
) -> str:
    """Create a cross-shaped solid — for pendants or earrings.

    PJ Chen's #44/#162/#486 technique: extrude + boolean + fillet corners.

    Args:
        arm_length: Length of each arm from center.
        arm_width: Width of each arm.
        thickness: Depth/thickness.
        corner_radius: Fillet radius for corners.
        layer: Layer for the cross.
    """
    hw = arm_width / 2.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        al = {arm_length}
        hw = {hw}

        # Cross = union of two rectangles
        horiz_pts = [(-al,-hw,0),(al,-hw,0),(al,hw,0),(-al,hw,0),(-al,-hw,0)]
        vert_pts = [(-hw,-al,0),(hw,-al,0),(hw,al,0),(-hw,al,0),(-hw,-al,0)]

        h_crv = rs.AddPolyline(horiz_pts)
        v_crv = rs.AddPolyline(vert_pts)

        h_srf = rs.ExtrudeCurveStraight(h_crv, (0,0,0), (0,0,{thickness}))
        v_srf = rs.ExtrudeCurveStraight(v_crv, (0,0,0), (0,0,{thickness}))

        if h_srf: rs.CapPlanarHoles(h_srf)
        if v_srf: rs.CapPlanarHoles(v_srf)

        if h_srf and v_srf:
            cross = rs.BooleanUnion([h_srf, v_srf])
            if cross:
                for c in cross:
                    rs.ObjectLayer(c, "{layer}")
                print("Cross: {arm_length}mm arms, {arm_width}mm wide, {thickness}mm thick")
            else:
                print("Boolean union failed")
        rs.DeleteObjects([h_crv, v_crv])
    """)


@mcp.tool()
def create_leaf_shape(
    length: float = 20.0,
    width: float = 8.0,
    thickness: float = 1.0,
    num_veins: int = 5,
    layer: str = "Leaf",
) -> str:
    """Create an organic leaf shape with vein detail — for pendants/earrings.

    PJ Chen's #202/#536 technique using sweep + offset for veins.

    Args:
        length: Leaf length tip-to-tip.
        width: Maximum leaf width.
        thickness: Leaf thickness.
        num_veins: Number of side veins.
        layer: Layer for the leaf.
    """
    hw = width / 2.0
    hl = length / 2.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        hl = {hl}
        hw = {hw}

        # Leaf outline (pointed both ends, widest at 40% from base)
        pts = []
        n = 30
        for i in range(n):
            t = 2 * math.pi * i / n
            # Asymmetric leaf shape
            x = hl * math.sin(t)
            y_scale = math.sin(t) ** 0.6 if math.sin(t) >= 0 else -(abs(math.sin(t)) ** 0.6)
            y = hw * math.cos(t) * abs(y_scale)
            pts.append((x, y, 0))
        pts.append(pts[0])

        outline = rs.AddInterpCurve(pts, degree=3)
        if outline:
            leaf = rs.ExtrudeCurveStraight(outline, (0,0,-{thickness/2}), (0,0,{thickness/2}))
            if leaf:
                rs.CapPlanarHoles(leaf)
                rs.ObjectLayer(leaf, "{layer}")

            # Center vein
            vein_line = rs.AddLine((-hl*0.9, 0, {thickness/2+0.1}), (hl*0.9, 0, {thickness/2+0.1}))
            if vein_line:
                vp = rs.AddPipe(vein_line, [0, 0.5, 1], [0.15, 0.3, 0.15], 0, 2)
                if vp:
                    for v in vp: rs.ObjectLayer(v, "{layer}")
                rs.DeleteObject(vein_line)

            # Side veins
            for i in range({num_veins}):
                t = -0.3 + 0.6 * i / ({num_veins}-1) if {num_veins} > 1 else 0
                vx = hl * t
                vw = hw * (1 - abs(t)) * 0.7
                for side in [-1, 1]:
                    vein_pts = [(vx, 0, {thickness/2+0.1}), (vx + hl*0.15, side*vw, {thickness/2+0.05})]
                    vl = rs.AddLine(vein_pts[0], vein_pts[1])
                    if vl:
                        vp = rs.AddPipe(vl, [0,1], [0.15, 0.08], 0, 2)
                        if vp:
                            for v in vp: rs.ObjectLayer(v, "{layer}")
                        rs.DeleteObject(vl)

            rs.DeleteObject(outline)
            print("Leaf: {length}x{width}mm with {num_veins} vein pairs")
    """)


@mcp.tool()
def create_snowflake(
    diameter: float = 15.0,
    arm_width: float = 1.5,
    thickness: float = 1.0,
    num_arms: int = 6,
    layer: str = "Snowflake",
) -> str:
    """Create a snowflake design — for pendants or earrings.

    PJ Chen's #149 technique: single arm + polar array.

    Args:
        diameter: Overall diameter.
        arm_width: Width of each arm.
        thickness: Depth.
        num_arms: Number of arms (6 standard).
        layer: Layer for the snowflake.
    """
    arm_len = diameter / 2.0
    hw = arm_width / 2.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        al = {arm_len}
        hw = {hw}

        # Single arm with branches
        arm_pts = [(-hw,0,0),(hw,0,0),(hw*0.6,al,0),(-hw*0.6,al,0),(-hw,0,0)]
        arm_crv = rs.AddPolyline(arm_pts)

        # Branch at 60% up the arm
        br_len = al * 0.35
        for side in [-1, 1]:
            b_pts = [(0, al*0.6, 0), (side*br_len*0.7, al*0.6+br_len*0.5, 0)]
            b_line = rs.AddLine(b_pts[0], b_pts[1])
            if b_line:
                bp = rs.AddPipe(b_line, [0,1], [hw*0.4, hw*0.15], 0, 2)
                if bp:
                    for b in bp: rs.ObjectLayer(b, "{layer}")
                rs.DeleteObject(b_line)

        if arm_crv:
            arm_srf = rs.ExtrudeCurveStraight(arm_crv, (0,0,0), (0,0,{thickness}))
            if arm_srf:
                rs.CapPlanarHoles(arm_srf)
                rs.ObjectLayer(arm_srf, "{layer}")

                # Polar array for all arms
                for i in range(1, {num_arms}):
                    angle = 360.0 * i / {num_arms}
                    copies = rs.CopyObjects(rs.ObjectsByLayer("{layer}"))
                    if copies:
                        rs.RotateObjects(copies, (0,0,0), angle, (0,0,1))

            rs.DeleteObject(arm_crv)

        # Center hub
        hub = rs.AddCylinder((0,0,0), (0,0,{thickness}), hw*1.5)
        if hub: rs.ObjectLayer(hub, "{layer}")

        print("Snowflake: {diameter}mm, {num_arms} arms")
    """)


@mcp.tool()
def flow_pattern_along_curve(
    source_layer: str = "Pattern_Source",
    rail_layer: str = "Rail_Curve",
    count: int = 20,
    output_layer: str = "Pattern_Flow",
) -> str:
    """Flow / array a source object along a target curve.

    Finds the first object on source_layer and the first curve on rail_layer,
    then places 'count' copies evenly distributed along the rail by sampling
    curve parameters and orienting each copy to the curve tangent at that point.

    Args:
        source_layer: Layer containing the object to repeat.
        rail_layer: Layer containing the guide curve.
        count: Number of copies to place along the curve (default 20).
        output_layer: Layer for the placed copies.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}", [100, 200, 220])

        # --- Source object ---
        src_objs = rs.ObjectsByLayer("{source_layer}")
        if not src_objs:
            print("No objects on source layer: {source_layer}")
        else:
            src = src_objs[0]

            # --- Rail curve ---
            rail_objs = rs.ObjectsByLayer("{rail_layer}")
            curve = None
            for obj in rail_objs:
                if rs.IsCurve(obj):
                    curve = obj
                    break

            if not curve:
                print("No curve on rail layer: {rail_layer}")
            else:
                count     = {count}
                is_closed = rs.IsCurveClosed(curve)
                dom       = rs.CurveDomain(curve)

                # Source bounding box centre for pivot alignment
                src_bb = rs.BoundingBox(src)
                if src_bb:
                    src_cx = (src_bb[0][0] + src_bb[6][0]) / 2.0
                    src_cy = (src_bb[0][1] + src_bb[6][1]) / 2.0
                    src_cz = (src_bb[0][2] + src_bb[6][2]) / 2.0
                else:
                    src_cx = src_cy = src_cz = 0.0

                placed = 0

                for i in range(count):
                    if is_closed:
                        t_norm = float(i) / count
                    else:
                        t_norm = float(i) / max(count - 1, 1)

                    t_param = rs.CurveParameter(curve, t_norm)
                    if t_param is None:
                        t_param = dom[0] + t_norm * (dom[1] - dom[0])

                    pt  = rs.EvaluateCurve(curve, t_param)
                    tan = rs.CurveTangent(curve, t_param)
                    if pt is None or tan is None:
                        continue

                    # Normalise tangent
                    tan_len = math.sqrt(tan[0]**2 + tan[1]**2 + tan[2]**2)
                    if tan_len < 1e-10:
                        continue
                    tx = tan[0] / tan_len
                    ty = tan[1] / tan_len

                    # Copy and translate so source centre lands on curve point
                    copy = rs.CopyObject(src)
                    if copy is None:
                        continue

                    rs.MoveObject(copy, (
                        pt[0] - src_cx,
                        pt[1] - src_cy,
                        pt[2] - src_cz,
                    ))

                    # Rotate in XY plane to align source X-axis with curve tangent
                    angle_deg = math.degrees(math.atan2(ty, tx))
                    if abs(angle_deg) > 0.01:
                        rs.RotateObject(copy, pt, angle_deg, (0.0, 0.0, 1.0))

                    rs.ObjectLayer(copy, "{output_layer}")
                    placed += 1

                print("Flowed {{}} copies along '{{}}' onto '{output_layer}'".format(
                    placed, "{rail_layer}"))
    """)


@mcp.tool()
def create_filigree_cutout(
    target_layer: str = "Ring_Band",
    pattern_layer: str = "Filigree_Pattern",
    result_layer: str = "Ring_Filigree",
    pattern: str = "circles",
    count: int = 8,
    pattern_size: float = 2.0,
    depth: float = 10.0,
) -> str:
    """Create filigree (pierced) decorative cutouts on a ring or surface.

    From Ch 5 of the book: filigree cutouts use Extrude + Boolean Difference to
    pierce decorative patterns through a solid. The pattern is projected onto the
    surface and extruded through to cut away material. Common for vintage and
    art-deco pieces.

    Args:
        target_layer: Layer with the solid to cut into.
        pattern_layer: Layer for the filigree pattern curves.
        result_layer: Layer for the result.
        pattern: Pattern type — 'circles', 'diamonds', 'teardrops'.
        count: Number of pattern elements around the ring.
        pattern_size: Size of each pattern element in mm.
        depth: Extrusion depth for the boolean cutter (should exceed object thickness).
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        target_layer = "{target_layer}"
        pattern_layer = "{pattern_layer}"
        result_layer = "{result_layer}"

        if not rs.IsLayer(target_layer):
            print("ERROR: Target layer '{{}}' not found".format(target_layer))
        else:
            for lyr in [pattern_layer, result_layer]:
                if not rs.IsLayer(lyr):
                    rs.AddLayer(lyr)

            # Get target object
            objs = rs.ObjectsByLayer(target_layer)
            if not objs:
                print("ERROR: No objects on target layer")
            else:
                target = objs[0]
                bb = rs.BoundingBox(target)
                cx = (bb[0][0] + bb[6][0]) / 2.0
                cy = (bb[0][1] + bb[6][1]) / 2.0
                cz = (bb[0][2] + bb[4][2]) / 2.0
                obj_r = max(bb[1][0] - bb[0][0], bb[2][1] - bb[0][1]) / 2.0

                rs.CurrentLayer(pattern_layer)
                count = {count}
                sz = {pattern_size}
                depth = {depth}
                pattern = "{pattern}"
                cutters = []

                for i in range(count):
                    angle = 2 * math.pi * i / count
                    px = cx + (obj_r + 1) * math.cos(angle)
                    py = cy + (obj_r + 1) * math.sin(angle)

                    if pattern == "circles":
                        plane = rs.WorldXYPlane()
                        plane = rs.MovePlane(plane, (px, py, cz))
                        crv = rs.AddCircle(plane, sz / 2.0)
                    elif pattern == "diamonds":
                        half = sz / 2.0
                        pts = [(px, py - half, cz), (px + half * 0.6, py, cz),
                               (px, py + half, cz), (px - half * 0.6, py, cz),
                               (px, py - half, cz)]
                        crv = rs.AddPolyline(pts)
                    else:  # teardrops
                        pts = []
                        for t in range(13):
                            a = 2 * math.pi * t / 12
                            r_t = sz / 2.0 * (1 + 0.3 * math.cos(a))
                            pts.append((px + r_t * math.cos(a), py + r_t * math.sin(a), cz))
                        pts.append(pts[0])
                        crv = rs.AddInterpCurve(pts)

                    # Extrude cutter inward toward center
                    direction = (cx - px, cy - py, 0)
                    mag = math.sqrt(direction[0]**2 + direction[1]**2)
                    direction = (direction[0]/mag * depth, direction[1]/mag * depth, 0)
                    ext = rs.ExtrudeCurveStraight(crv, (0,0,0), direction)
                    if ext:
                        rs.CapPlanarHoles(ext)
                        cutters.append(ext)
                    rs.DeleteObject(crv)

                if cutters:
                    rs.CurrentLayer(result_layer)
                    copy = rs.CopyObject(target)
                    rs.ObjectLayer(copy, result_layer)

                    for cutter in cutters:
                        result = rs.BooleanDifference([copy], [cutter], delete_input=True)
                        if result:
                            copy = result[0]

                    print("Filigree: {{}} '{{}}' cutouts on layer '{result_layer}'".format(count, pattern))
                else:
                    print("ERROR: No cutters created")
    """)


@mcp.tool()
def create_surface_inset(
    target_layer: str = "Ring_Band",
    inset_layer: str = "Ring_Inset",
    shape: str = "rectangle",
    width: float = 4.0,
    height: float = 2.0,
    inset_depth: float = 0.3,
    position_angle: float = 0.0,
) -> str:
    """Create a decorative inset (recessed area) on a curved ring surface.

    From Ch 5: Surface Inset Method 1 — extrude a shape and boolean-subtract it from
    the ring surface to create a flat recessed panel. Used for enamel fills, engraving
    areas, or inlaid stone panels on curved ring bands.

    Args:
        target_layer: Layer with the ring/object to inset into.
        inset_layer: Layer for the inset result.
        shape: Shape of inset — 'rectangle', 'oval', 'shield'.
        width: Width of the inset area in mm.
        height: Height of the inset area in mm.
        inset_depth: Depth of the recess in mm.
        position_angle: Angular position on ring (degrees, 0 = front).
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        target_layer = "{target_layer}"
        inset_layer = "{inset_layer}"

        if not rs.IsLayer(target_layer):
            print("ERROR: Layer '{{}}' not found".format(target_layer))
        else:
            if not rs.IsLayer(inset_layer):
                rs.AddLayer(inset_layer)

            objs = rs.ObjectsByLayer(target_layer)
            if not objs:
                print("ERROR: No objects on target layer")
            else:
                target = objs[0]
                bb = rs.BoundingBox(target)
                cx = (bb[0][0] + bb[6][0]) / 2.0
                cy = (bb[0][1] + bb[6][1]) / 2.0
                cz = (bb[0][2] + bb[4][2]) / 2.0
                obj_r = max(bb[1][0] - bb[0][0], bb[2][1] - bb[0][1]) / 2.0

                w = {width}
                h = {height}
                depth = {inset_depth}
                angle = math.radians({position_angle})
                shape = "{shape}"

                # Position on the outside of the ring
                px = cx + (obj_r / 2.0 + 2) * math.cos(angle)
                py = cy + (obj_r / 2.0 + 2) * math.sin(angle)

                # Create cutter shape
                if shape == "rectangle":
                    pts = [
                        (px - w/2, py, cz - h/2),
                        (px + w/2, py, cz - h/2),
                        (px + w/2, py, cz + h/2),
                        (px - w/2, py, cz + h/2),
                        (px - w/2, py, cz - h/2),
                    ]
                    crv = rs.AddPolyline(pts)
                elif shape == "oval":
                    plane = rs.PlaneFromNormal((px, py, cz), (0, 1, 0))
                    crv = rs.AddEllipse(plane, w/2, h/2)
                else:  # shield
                    pts = [
                        (px - w/2, py, cz + h/2),
                        (px + w/2, py, cz + h/2),
                        (px + w/2, py, cz),
                        (px, py, cz - h/2),
                        (px - w/2, py, cz),
                        (px - w/2, py, cz + h/2),
                    ]
                    crv = rs.AddInterpCurve(pts)

                # Extrude inward
                direction = (cx - px, cy - py, 0)
                mag = math.sqrt(direction[0]**2 + direction[1]**2)
                norm_dir = (direction[0]/mag, direction[1]/mag, 0)
                ext_vec = (norm_dir[0] * (depth + obj_r), norm_dir[1] * (depth + obj_r), 0)

                cutter = rs.ExtrudeCurveStraight(crv, (0,0,0), ext_vec)
                if cutter:
                    rs.CapPlanarHoles(cutter)
                    rs.CurrentLayer(inset_layer)
                    copy = rs.CopyObject(target)
                    rs.ObjectLayer(copy, inset_layer)
                    result = rs.BooleanDifference([copy], [cutter], delete_input=True)
                    if result:
                        print("Surface inset '{{}}' {{:.1f}}x{{:.1f}}mm, {{:.1f}}mm deep on '{inset_layer}'".format(
                            shape, w, h, depth))
                    else:
                        print("ERROR: Boolean failed — check shape intersects target")
                rs.DeleteObject(crv)
    """)


@mcp.tool()
def create_mandala_pattern(
    diameter: float = 40.0,
    symmetry_order: int = 8,
    num_rings: int = 3,
    wire_thickness: float = 1.0,
    extrude_height: float = 1.2,
    layer: str = "Mandala_Pattern",
) -> str:
    """Create a parametric mandala pattern for pendants, brooches, or earrings.

    Generates concentric rings of decorative motifs with radial symmetry.
    Each ring has a different decorative element arrayed around the center.

    Args:
        diameter: Overall mandala diameter in mm.
        symmetry_order: Rotational symmetry (6, 8, 10, 12 typical).
        num_rings: Number of concentric decorative rings.
        wire_thickness: Minimum wire/element width in mm (min 0.8 for casting).
        extrude_height: Extrusion depth in mm.
        layer: Target layer name.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")
        rs.CurrentLayer("{layer}")

        outer_r = {diameter} / 2.0
        sym = {symmetry_order}
        n_rings = {num_rings}
        wire_w = {wire_thickness}
        ext_h = {extrude_height}

        all_curves = []

        # Outer border circle
        border = rs.AddCircle(rs.WorldXYPlane(), outer_r)
        if border:
            all_curves.append(border)
        inner_border = rs.AddCircle(rs.WorldXYPlane(), outer_r - wire_w)
        if inner_border:
            all_curves.append(inner_border)

        # Concentric decorative rings
        for ring in range(n_rings):
            r_inner = outer_r * (0.2 + 0.25 * ring)
            r_outer = r_inner + outer_r * 0.2

            # Ring boundary circles
            c1 = rs.AddCircle(rs.WorldXYPlane(), r_inner)
            c2 = rs.AddCircle(rs.WorldXYPlane(), r_outer)
            if c1:
                all_curves.append(c1)
            if c2:
                all_curves.append(c2)

            # Create one motif element, then array it
            angle_step = 2 * math.pi / sym
            r_mid = (r_inner + r_outer) / 2.0
            motif_h = (r_outer - r_inner) * 0.8

            if ring % 3 == 0:
                # Teardrop/petal motif
                pts = [
                    (r_inner + wire_w, 0, 0),
                    (r_mid, motif_h / 2, 0),
                    (r_outer - wire_w, 0, 0),
                    (r_mid, -motif_h / 2, 0),
                    (r_inner + wire_w, 0, 0),
                ]
            elif ring % 3 == 1:
                # Diamond motif
                pts = [
                    (r_inner + wire_w, 0, 0),
                    (r_mid, motif_h / 3, 0),
                    (r_outer - wire_w, 0, 0),
                    (r_mid, -motif_h / 3, 0),
                    (r_inner + wire_w, 0, 0),
                ]
            else:
                # Arch motif
                pts = [
                    (r_inner + wire_w, -motif_h / 3, 0),
                    (r_mid - wire_w, -motif_h / 3, 0),
                    (r_mid, motif_h / 2, 0),
                    (r_mid + wire_w, -motif_h / 3, 0),
                    (r_outer - wire_w, -motif_h / 3, 0),
                ]

            motif_crv = rs.AddInterpCurve(pts, 3)
            if motif_crv:
                all_curves.append(motif_crv)
                # Array polar
                for i in range(1, sym):
                    angle = 360.0 * i / sym
                    copy = rs.RotateObject(motif_crv, (0,0,0), angle, (0,0,1), True)
                    if copy:
                        all_curves.append(copy)

            # Radial spokes in this ring
            for i in range(sym):
                a = angle_step * i
                p1 = (r_inner * math.cos(a), r_inner * math.sin(a), 0)
                p2 = (r_outer * math.cos(a), r_outer * math.sin(a), 0)
                spoke = rs.AddLine(p1, p2)
                if spoke:
                    all_curves.append(spoke)

        # Center circle
        center = rs.AddCircle(rs.WorldXYPlane(), outer_r * 0.15)
        if center:
            all_curves.append(center)

        print("Mandala pattern on '{{}}' — {{}} curves, {{}}-fold symmetry".format(
            "{layer}", len(all_curves), sym))
        print("  Diameter: {{:.0f}}mm, {{}} decorative rings".format({diameter}, n_rings))
        print("  Next: ExtrudeCrv by {{:.1f}}mm, then BooleanUnion for solid".format(ext_h))
    """)


@mcp.tool()
def apply_texture_to_bangle(
    bangle_layer: str = "Bangle",
    texture_layer: str = "Texture_Tile",
    result_layer: str = "Textured_Bangle",
    texture_depth: float = 0.5,
) -> str:
    """Wrap a flat texture pattern onto a bangle/bracelet using FlowAlongSrf.

    Takes a flat texture tile on the texture layer and flows it onto the
    bangle surface. The texture can be BooleanUnion'd (raised) or
    BooleanDifference'd (stamped) into the bangle.

    Args:
        bangle_layer: Layer with the bangle body.
        texture_layer: Layer with flat texture tile objects.
        result_layer: Layer for the textured result.
        texture_depth: Depth of texture impression in mm.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{bangle_layer}"):
            print("ERROR: Layer '{bangle_layer}' not found")
        elif not rs.IsLayer("{texture_layer}"):
            print("ERROR: Layer '{texture_layer}' not found")
        else:
            if not rs.IsLayer("{result_layer}"):
                rs.AddLayer("{result_layer}")

            bangle_objs = rs.ObjectsByLayer("{bangle_layer}")
            texture_objs = rs.ObjectsByLayer("{texture_layer}")

            if not bangle_objs:
                print("ERROR: No objects on '{bangle_layer}'")
            elif not texture_objs:
                print("ERROR: No objects on '{texture_layer}'")
            else:
                # Get bangle surface (first surface/polysurface)
                bangle = bangle_objs[0]

                # Get bounding box of texture to create base surface
                tex_bb = rs.BoundingBox(texture_objs)
                if tex_bb:
                    # Create flat base surface matching texture extents
                    x0, y0 = tex_bb[0][0], tex_bb[0][1]
                    x1, y1 = tex_bb[1][0], tex_bb[3][1]
                    base_srf = rs.AddSrfPt([
                        (x0, y0, 0), (x1, y0, 0),
                        (x1, y1, 0), (x0, y1, 0)
                    ])

                    if base_srf:
                        # Select texture objects + base surface, flow to bangle
                        rs.SelectObjects(texture_objs)
                        rs.Command("_FlowAlongSrf _SelID {{}} _SelID {{}} _Enter".format(
                            rs.coerceguid(base_srf), rs.coerceguid(bangle)), False)
                        rs.UnselectAllObjects()

                        # Move flowed objects to result layer
                        new_objs = rs.LastCreatedObjects()
                        if new_objs:
                            for obj in new_objs:
                                rs.ObjectLayer(obj, "{result_layer}")
                            print("Flowed {{}} texture objects onto bangle → '{result_layer}'".format(
                                len(new_objs)))
                        else:
                            print("FlowAlongSrf produced no output — check surface UV directions")

                        rs.DeleteObject(base_srf)
                    else:
                        print("ERROR: Base surface creation failed")
                else:
                    print("ERROR: Cannot compute texture bounding box")
    """)
