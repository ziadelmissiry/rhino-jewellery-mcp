import math
import textwrap
from app import mcp


@mcp.tool()
def create_necklace_base(
    x_radius: float = 65.0,
    y_radius: float = 75.0,
    v_depth: float = 25.0,
    opening_angle: float = 140.0,
    num_points: int = 120,
    left_layer: str = "Left_Rail",
    right_layer: str = "Right_Rail",
) -> str:
    """Create an anatomically-correct necklace base curve.

    Generates an elliptical collar split into Left_Rail and Right_Rail
    with a V-deformation at the front center.

    Args:
        x_radius: Ellipse X-radius in mm (half neck width). Default 65.
        y_radius: Ellipse Y-radius in mm (half neck depth). Default 75.
        v_depth: How far the V-dip drops in Z (mm). Default 25.
        opening_angle: Half-angle of the opening at the back (degrees). Default 140.
        num_points: Interpolation density per rail. Default 120.
        left_layer: Layer name for the left (emerald) rail.
        right_layer: Layer name for the right (diamond) rail.

    Returns:
        RhinoScript Python code ready for execute_rhinoscript_python_code.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        x_radius = {x_radius}
        y_radius = {y_radius}
        v_depth  = {v_depth}
        opening  = {opening_angle}
        n        = {num_points}

        for layer, color in [("{left_layer}", [0,155,60]), ("{right_layer}", [200,200,220])]:
            if not rs.IsLayer(layer):
                rs.AddLayer(layer, color)

        def neck_pt(theta_deg):
            theta = math.radians(theta_deg)
            x = x_radius * math.sin(theta)
            y = -y_radius * math.cos(theta)
            z = -v_depth * math.exp(-(theta_deg**2) / (50.0**2))
            z += 5.0 * (abs(theta_deg) / opening)**2
            return (x, y, z)

        half = n // 2
        left_pts  = [neck_pt(-opening + (opening) * i / half) for i in range(half + 1)]
        right_pts = [neck_pt(opening * i / half) for i in range(half + 1)]

        left_rail  = rs.AddInterpCurve(left_pts, degree=3)
        right_rail = rs.AddInterpCurve(right_pts, degree=3)
        rs.ObjectLayer(left_rail,  "{left_layer}")
        rs.ObjectLayer(right_rail, "{right_layer}")

        v = neck_pt(0)
        print("Left_Rail:  {{}}".format(left_rail))
        print("Right_Rail: {{}}".format(right_rail))
        print("V-junction: ({{:.1f}}, {{:.1f}}, {{:.1f}})".format(*v))
    """)


@mcp.tool()
def place_round_gems(
    rail_layer: str,
    gem_layer: str,
    count: int = 45,
    diameter: float = 2.0,
    z_flatten: float = 0.55,
) -> str:
    """Place round brilliant-cut gems evenly along a rail curve.

    Args:
        rail_layer: Layer containing the rail curve to populate.
        gem_layer: Layer to assign the created gem spheres to.
        count: Number of gems to place.
        diameter: Stone diameter in mm.
        z_flatten: Z-axis scale factor (< 1 flattens). 0.55 is typical.

    Returns:
        RhinoScript Python code.
    """
    r = diameter / 2.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{gem_layer}"):
            rs.AddLayer("{gem_layer}")

        curve = rs.ObjectsByLayer("{rail_layer}")[0]
        domain = rs.CurveDomain(curve)
        count = {count}

        for i in range(count):
            param = domain[0] + (domain[1] - domain[0]) * i / (count - 1)
            pt = rs.EvaluateCurve(curve, param)
            gem = rs.AddSphere(pt, {r})
            rs.ScaleObject(gem, pt, (1.0, 1.0, {z_flatten}))
            rs.ObjectLayer(gem, "{gem_layer}")

        print("Placed {{}} round gems ({diameter}mm) on {rail_layer}".format(count))
    """)


@mcp.tool()
def place_baguette_gems(
    rail_layer: str,
    gem_layer: str,
    count: int = 50,
    width: float = 1.8,
    length: float = 2.5,
    depth: float = 1.2,
) -> str:
    """Place baguette / princess-cut rectangular gems along a rail curve.

    Args:
        rail_layer: Layer with the rail curve.
        gem_layer: Target layer for the gems.
        count: Number of baguettes.
        width: Stone width (across curve) in mm.
        length: Stone length (along curve) in mm.
        depth: Stone depth in mm.

    Returns:
        RhinoScript Python code.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{gem_layer}"):
            rs.AddLayer("{gem_layer}")

        curve = rs.ObjectsByLayer("{rail_layer}")[0]
        domain = rs.CurveDomain(curve)
        count = {count}
        w, l, d = {width}, {length}, {depth}
        hw, hl = w/2.0, l/2.0

        for i in range(count):
            param = domain[0] + (domain[1] - domain[0]) * i / (count - 1)
            pt = rs.EvaluateCurve(curve, param)
            tangent = rs.CurveTangent(curve, param)
            if not pt or not tangent:
                continue

            tmag = math.sqrt(sum(c**2 for c in tangent))
            tx, ty, tz = [c/tmag for c in tangent]
            up = (0, 0, 1)
            wx = ty*up[2] - tz*up[1]
            wy = tz*up[0] - tx*up[2]
            wz = tx*up[1] - ty*up[0]
            wmag = math.sqrt(wx**2 + wy**2 + wz**2)
            if wmag < 0.001:
                continue
            wx, wy, wz = wx/wmag, wy/wmag, wz/wmag

            corners = []
            for dz in [d*0.3, -d*0.7]:
                for dl, dw_sign in [(-hl,-hw),(hl,-hw),(hl,hw),(-hl,hw)]:
                    corners.append((
                        pt[0] + dl*tx + dw_sign*wx,
                        pt[1] + dl*ty + dw_sign*wy,
                        pt[2] + dz
                    ))

            box = rs.AddBox(corners)
            if box:
                rs.ObjectLayer(box, "{gem_layer}")

        print("Placed {{}} baguettes on {rail_layer}".format(count))
    """)


@mcp.tool()
def create_stems(
    rail_layer: str,
    stem_layer: str = "Stems",
    count: int = 45,
    length: float = 10.0,
    base_radius: float = 0.8,
    tip_radius: float = 0.4,
    downward_angle: float = 0.15,
) -> str:
    """Create tapered structural stems radiating outward from a rail curve.

    Each stem is a perpendicular pipe extending away from the necklace center,
    wider at the base and thinner at the tip (conical support).

    Args:
        rail_layer: Layer containing the rail curve.
        stem_layer: Layer for the created stems.
        count: Number of stems to create.
        length: Stem length in mm.
        base_radius: Pipe radius at the rail end (mm).
        tip_radius: Pipe radius at the outer tip (mm).
        downward_angle: Slight downward tilt (0 = horizontal, 0.15 = subtle fan).

    Returns:
        RhinoScript Python code.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{stem_layer}"):
            rs.AddLayer("{stem_layer}")

        curve = rs.ObjectsByLayer("{rail_layer}")[0]
        domain = rs.CurveDomain(curve)
        count = {count}
        stem_len = {length}

        for i in range(count):
            param = domain[0] + (domain[1] - domain[0]) * i / (count - 1)
            pt = rs.EvaluateCurve(curve, param)
            if not pt:
                continue

            dx, dy = pt[0], pt[1]
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < 0.001:
                continue

            out_x = dx / dist
            out_y = dy / dist
            out_z = -{downward_angle}
            mag = math.sqrt(out_x**2 + out_y**2 + out_z**2)
            out_x, out_y, out_z = out_x/mag, out_y/mag, out_z/mag

            tip = (pt[0] + stem_len*out_x, pt[1] + stem_len*out_y, pt[2] + stem_len*out_z)

            line = rs.AddLine(pt, tip)
            if line:
                pipe = rs.AddPipe(line, [0, 1], [{base_radius}, {tip_radius}], 0, 1)
                if pipe:
                    for p in pipe:
                        rs.ObjectLayer(p, "{stem_layer}")
                rs.DeleteObject(line)

        print("Created {{}} tapered stems on {rail_layer}".format(count))
    """)


@mcp.tool()
def place_pear_gems_at_stem_tips(
    rail_layer: str,
    gem_layer: str,
    count: int = 45,
    stem_length: float = 10.0,
    diameter: float = 3.0,
    downward_angle: float = 0.15,
    elongation: float = 0.6,
    z_flatten: float = 0.35,
) -> str:
    """Place pear/marquise-shaped gems at the tips of radiating stems.

    The pointed end of each pear faces inward toward the necklace center.

    Args:
        rail_layer: Layer with the rail curve (to recalculate tip positions).
        gem_layer: Layer for the pear gems.
        count: Number of gems (should match stem count).
        stem_length: Length of stems (mm) to find tip positions.
        diameter: Pear gem diameter in mm.
        downward_angle: Must match stem downward_angle.
        elongation: How much to elongate the pear shape (0.6 = typical).
        z_flatten: Z-axis flatten factor.

    Returns:
        RhinoScript Python code.
    """
    r = diameter / 2.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{gem_layer}"):
            rs.AddLayer("{gem_layer}")

        curve = rs.ObjectsByLayer("{rail_layer}")[0]
        domain = rs.CurveDomain(curve)
        count = {count}
        stem_len = {stem_length}

        for i in range(count):
            param = domain[0] + (domain[1] - domain[0]) * i / (count - 1)
            pt = rs.EvaluateCurve(curve, param)
            if not pt:
                continue

            dx, dy = pt[0], pt[1]
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < 0.001:
                continue

            out_x = dx / dist
            out_y = dy / dist
            out_z = -{downward_angle}
            mag = math.sqrt(out_x**2 + out_y**2 + out_z**2)
            out_x, out_y, out_z = out_x/mag, out_y/mag, out_z/mag

            tip = (pt[0] + stem_len*out_x, pt[1] + stem_len*out_y, pt[2] + stem_len*out_z)

            gem = rs.AddSphere(tip, {r})
            if gem:
                sx = 1.0 + {elongation} * abs(out_x)
                sy = 1.0 + {elongation} * abs(out_y)
                rs.ScaleObject(gem, tip, (sx, sy, {z_flatten}))
                rs.ObjectLayer(gem, "{gem_layer}")

        print("Placed {{}} pear gems at stem tips".format(count))
    """)


@mcp.tool()
def create_cushion_cut_pendant(
    center_x: float = 0.0,
    center_y: float = -75.0,
    center_z: float = -25.0,
    size: float = 12.0,
    gem_layer: str = "Pendant_Emerald",
    halo_layer: str = "Pendant_Halo",
    metal_layer: str = "Pendant_Bail",
    halo_count_inner: int = 24,
    halo_count_outer: int = 32,
    halo_gem_diameter: float = 1.5,
) -> str:
    """Create a cushion-cut pendant with double diamond halo.

    Generates an octagonal-prism gem (table + girdle + pavilion)
    surrounded by two concentric rings of round diamonds.

    Args:
        center_x: X position of pendant center.
        center_y: Y position.
        center_z: Z position.
        size: Diameter of the cushion stone in mm.
        gem_layer: Layer for the center emerald.
        halo_layer: Layer for halo diamonds.
        metal_layer: Layer for halo metal rings.
        halo_count_inner: Stones in inner halo ring.
        halo_count_outer: Stones in outer halo ring.
        halo_gem_diameter: Halo diamond diameter in mm.

    Returns:
        RhinoScript Python code.
    """
    half = size / 2.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        for layer in ["{gem_layer}", "{halo_layer}", "{metal_layer}"]:
            if not rs.IsLayer(layer):
                rs.AddLayer(layer)

        cx, cy, cz = {center_x}, {center_y}, {center_z}
        half = {half}

        # Cushion-cut: table, girdle, pavilion
        table_z  = cz + half * 0.4
        girdle_z = cz
        culet_z  = cz - half * 0.6

        def octa(h, clip_ratio, z):
            c = h * clip_ratio
            return [
                (cx-h+c,cy-h,z),(cx+h-c,cy-h,z),(cx+h,cy-h+c,z),(cx+h,cy+h-c,z),
                (cx+h-c,cy+h,z),(cx-h+c,cy+h,z),(cx-h,cy+h-c,z),(cx-h,cy-h+c,z),
                (cx-h+c,cy-h,z),
            ]

        t_crv = rs.AddPolyline(octa(half*0.75, 0.25, table_z))
        g_crv = rs.AddPolyline(octa(half, 0.25, girdle_z))
        p_crv = rs.AddPolyline(octa(half*0.4, 0.2, culet_z))

        for surfs in [rs.AddLoftSrf([t_crv, g_crv], loft_type=2),
                      rs.AddLoftSrf([g_crv, p_crv], loft_type=2),
                      rs.AddPlanarSrf([t_crv]), rs.AddPlanarSrf([p_crv])]:
            if surfs:
                for s in surfs:
                    rs.ObjectLayer(s, "{gem_layer}")
        rs.DeleteObjects([t_crv, g_crv, p_crv])

        # Inner halo
        h1_r = half + 1.5
        hr = {halo_gem_diameter} / 2.0
        for i in range({halo_count_inner}):
            a = 2*math.pi*i/{halo_count_inner}
            pt = (cx+h1_r*math.cos(a), cy+h1_r*math.sin(a), girdle_z+0.5)
            gem = rs.AddSphere(pt, hr)
            if gem:
                rs.ScaleObject(gem, pt, (1,1,0.45))
                rs.ObjectLayer(gem, "{halo_layer}")

        # Inner halo metal ring
        for i in range({halo_count_inner}):
            a1 = 2*math.pi*i/{halo_count_inner}
            a2 = 2*math.pi*((i+1)%{halo_count_inner})/{halo_count_inner}
            p1 = (cx+h1_r*math.cos(a1), cy+h1_r*math.sin(a1), girdle_z+0.5)
            p2 = (cx+h1_r*math.cos(a2), cy+h1_r*math.sin(a2), girdle_z+0.5)
            seg = rs.AddLine(p1, p2)
            if seg:
                sp = rs.AddPipe(seg, 0, 0.25, cap=1)
                if sp:
                    for s in sp: rs.ObjectLayer(s, "{metal_layer}")
                rs.DeleteObject(seg)

        # Outer halo
        h2_r = half + 3.5
        for i in range({halo_count_outer}):
            a = 2*math.pi*i/{halo_count_outer}
            pt = (cx+h2_r*math.cos(a), cy+h2_r*math.sin(a), girdle_z+0.3)
            gem = rs.AddSphere(pt, hr)
            if gem:
                rs.ScaleObject(gem, pt, (1,1,0.45))
                rs.ObjectLayer(gem, "{halo_layer}")

        for i in range({halo_count_outer}):
            a1 = 2*math.pi*i/{halo_count_outer}
            a2 = 2*math.pi*((i+1)%{halo_count_outer})/{halo_count_outer}
            p1 = (cx+h2_r*math.cos(a1), cy+h2_r*math.sin(a1), girdle_z+0.3)
            p2 = (cx+h2_r*math.cos(a2), cy+h2_r*math.sin(a2), girdle_z+0.3)
            seg = rs.AddLine(p1, p2)
            if seg:
                sp = rs.AddPipe(seg, 0, 0.2, cap=1)
                if sp:
                    for s in sp: rs.ObjectLayer(s, "{metal_layer}")
                rs.DeleteObject(seg)

        print("Pendant: {{}}mm cushion-cut + double halo at ({{:.0f}},{{:.0f}},{{:.0f}})".format(
            {size}, cx, cy, cz))
    """)


@mcp.tool()
def create_bail(
    pendant_x: float = 0.0,
    pendant_y: float = -75.0,
    pendant_z: float = -25.0,
    bail_radius: float = 0.75,
    arch_height: float = 8.0,
    spread: float = 4.0,
    layer: str = "Pendant_Bail",
) -> str:
    """Create a bail (bridge) connecting the pendant top to the necklace junction.

    Two arched pipes form an inverted Y connecting the pendant halo
    to where the rails converge.

    Args:
        pendant_x: Pendant center X.
        pendant_y: Pendant center Y.
        pendant_z: Pendant center Z.
        bail_radius: Pipe radius in mm (diameter = 2x).
        arch_height: How far above the pendant the bail arches.
        spread: Horizontal spread of the two arms.
        layer: Layer for the bail pipes.

    Returns:
        RhinoScript Python code.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        cx, cy, cz = {pendant_x}, {pendant_y}, {pendant_z}
        h = {arch_height}
        s = {spread}

        left_pts = [(-s, cy, cz+2), (-s*0.6, cy, cz+h*0.6), (0, cy, cz+h)]
        right_pts = [(s, cy, cz+2), (s*0.6, cy, cz+h*0.6), (0, cy, cz+h)]

        for pts in [left_pts, right_pts]:
            crv = rs.AddInterpCurve(pts, degree=3)
            if crv:
                pipe = rs.AddPipe(crv, [0, 0.5, 1], [{bail_radius}, {bail_radius}*1.1, {bail_radius}], 0, 2)
                if pipe:
                    for p in pipe:
                        rs.ObjectLayer(p, "{layer}")
                rs.DeleteObject(crv)

        print("Bail created: 2 arms, {bail_radius}mm radius")
    """)


@mcp.tool()
def create_prongs(
    rail_layer: str,
    metal_layer: str,
    gem_count: int = 45,
    prongs_per_gem: int = 4,
    prong_radius: float = 0.15,
    prong_height: float = 1.0,
) -> str:
    """Add prong settings around gems sitting on a rail curve.

    Creates small cylinders arranged in a ring around each gem position.

    Args:
        rail_layer: Layer with the rail curve (gem positions derived from this).
        metal_layer: Layer for the prong cylinders.
        gem_count: Number of gem positions along the curve.
        prongs_per_gem: Prongs per stone (typically 4 or 6).
        prong_radius: Cylinder radius in mm.
        prong_height: How tall the prongs extend above the gem center.

    Returns:
        RhinoScript Python code.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{metal_layer}"):
            rs.AddLayer("{metal_layer}")

        curve = rs.ObjectsByLayer("{rail_layer}")[0]
        domain = rs.CurveDomain(curve)
        count = {gem_count}
        n_prongs = {prongs_per_gem}

        for i in range(count):
            param = domain[0] + (domain[1] - domain[0]) * i / (count - 1)
            pt = rs.EvaluateCurve(curve, param)
            tangent = rs.CurveTangent(curve, param)
            if not pt or not tangent:
                continue

            frame = rs.CurvePerpFrame(curve, param)
            if not frame:
                continue

            prong_dist = 1.2
            for j in range(n_prongs):
                angle = j * 2 * math.pi / n_prongs + math.pi / n_prongs
                dx = frame[1][0]*math.cos(angle) + frame[2][0]*math.sin(angle)
                dy = frame[1][1]*math.cos(angle) + frame[2][1]*math.sin(angle)
                dz = frame[1][2]*math.cos(angle) + frame[2][2]*math.sin(angle)

                base = (pt[0]+prong_dist*dx, pt[1]+prong_dist*dy, pt[2]+prong_dist*dz)
                top  = (base[0], base[1], base[2]+{prong_height})

                prong = rs.AddCylinder(base, top, {prong_radius})
                if prong:
                    rs.ObjectLayer(prong, "{metal_layer}")

        print("Created {{}} prongs ({{}} per gem x {gem_count} gems)".format(
            count * n_prongs, n_prongs))
    """)


@mcp.tool()
def create_channel_setting(
    rail_layer: str,
    metal_layer: str,
    rail_radius: float = 0.4,
    under_rail_depth: float = 0.8,
    cross_link_count: int = 50,
) -> str:
    """Create U-channel / pave metal settings along a rail curve.

    Builds top rail pipes, under-rail pipes, and cross-links
    to form a channel that holds baguette or round stones.

    Args:
        rail_layer: Layer with the curve.
        metal_layer: Layer for the metal geometry.
        rail_radius: Pipe radius for the channel rails.
        under_rail_depth: How far below the top rail the under-gallery sits.
        cross_link_count: Number of cross-support links.

    Returns:
        RhinoScript Python code.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{metal_layer}"):
            rs.AddLayer("{metal_layer}")

        curve = rs.ObjectsByLayer("{rail_layer}")[0]
        domain = rs.CurveDomain(curve)
        n = 60

        # Top rail
        prev = None
        for i in range(n):
            param = domain[0] + (domain[1] - domain[0]) * i / (n - 1)
            pt = rs.EvaluateCurve(curve, param)
            if prev:
                seg = rs.AddLine(prev, pt)
                if seg:
                    sp = rs.AddPipe(seg, 0, {rail_radius}, cap=1)
                    if sp:
                        for s in sp: rs.ObjectLayer(s, "{metal_layer}")
                    rs.DeleteObject(seg)
            prev = pt

        # Under-gallery rail
        prev = None
        for i in range(n):
            param = domain[0] + (domain[1] - domain[0]) * i / (n - 1)
            pt = rs.EvaluateCurve(curve, param)
            under = (pt[0], pt[1], pt[2] - {under_rail_depth})
            if prev:
                seg = rs.AddLine(prev, under)
                if seg:
                    sp = rs.AddPipe(seg, 0, {rail_radius * 0.6}, cap=1)
                    if sp:
                        for s in sp: rs.ObjectLayer(s, "{metal_layer}")
                    rs.DeleteObject(seg)
            prev = under

        # Vertical links
        for i in range({cross_link_count}):
            param = domain[0] + (domain[1] - domain[0]) * i / ({cross_link_count} - 1)
            pt = rs.EvaluateCurve(curve, param)
            under = (pt[0], pt[1], pt[2] - {under_rail_depth})
            vl = rs.AddLine(pt, under)
            if vl:
                vp = rs.AddPipe(vl, 0, {rail_radius * 0.4}, cap=1)
                if vp:
                    for v in vp: rs.ObjectLayer(v, "{metal_layer}")
                rs.DeleteObject(vl)

        print("Channel setting on {rail_layer}: top rail + under-gallery + {{}} links".format({cross_link_count}))
    """)


@mcp.tool()
def create_ring_band(
    inner_diameter: float = 17.0,
    band_width: float = 4.0,
    band_thickness: float = 1.5,
    layer: str = "Ring_Band",
) -> str:
    """Create a ring band (torus section) as a base for ring jewelry.

    Args:
        inner_diameter: Inner diameter of the ring in mm (size 54 EU ~ 17mm).
        band_width: Width of the band in mm.
        band_thickness: Thickness of the metal band in mm.
        layer: Layer for the ring.

    Returns:
        RhinoScript Python code.
    """
    inner_r = inner_diameter / 2.0
    minor_r = band_thickness / 2.0
    major_r = inner_r + minor_r
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        ring = rs.AddTorus((0, 0, 0), {major_r}, {minor_r})
        if ring:
            rs.ObjectLayer(ring, "{layer}")
            # Flatten to band width
            rs.ScaleObject(ring, (0, 0, 0), (1.0, 1.0, {band_width / (2 * minor_r)}))
            print("Ring band: {inner_diameter}mm ID, {band_width}mm wide, {band_thickness}mm thick")
    """)


@mcp.tool()
def create_gem_cutout(
    gem_layer: str,
    metal_layer: str,
    output_layer: str = "Metal_Cut",
) -> str:
    """Boolean-subtract gem volumes from metal to create gem seats.

    Takes all gems on gem_layer and subtracts them from all solids
    on metal_layer, creating precise settings/seats.

    Args:
        gem_layer: Layer with gem solids to subtract.
        metal_layer: Layer with metal solids to cut into.
        output_layer: Layer for the resulting cut metal.

    Returns:
        RhinoScript Python code.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}")

        gems = rs.ObjectsByLayer("{gem_layer}")
        metal = rs.ObjectsByLayer("{metal_layer}")

        if not gems or not metal:
            print("Error: need objects on both layers")
        else:
            result = rs.BooleanDifference(metal, gems, delete_input=False)
            if result:
                for r in result:
                    rs.ObjectLayer(r, "{output_layer}")
                print("Cut {{}} gem seats into metal".format(len(result)))
            else:
                print("Boolean difference failed - check geometry overlap")
    """)


@mcp.tool()
def mirror_half_necklace(
    source_layers: str = "Left_Rail,Emerald_Gems,Gold_Metal",
    mirror_axis: str = "YZ",
) -> str:
    """Mirror one half of a necklace to create the other side.

    Useful when you've modeled only the left side and want to
    mirror it to create the right.

    Args:
        source_layers: Comma-separated layer names to mirror.
        mirror_axis: "YZ" mirrors across X=0, "XZ" mirrors across Y=0.

    Returns:
        RhinoScript Python code.
    """
    layers = [l.strip() for l in source_layers.split(",")]
    if mirror_axis == "YZ":
        start, end = "(0, 0, 0)", "(0, 1, 0)"
    else:
        start, end = "(0, 0, 0)", "(1, 0, 0)"

    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        layers = {layers}
        all_objs = []
        for layer in layers:
            objs = rs.ObjectsByLayer(layer)
            if objs:
                all_objs.extend(objs)

        if all_objs:
            mirrored = rs.MirrorObjects(all_objs, {start}, {end}, copy=True)
            if mirrored:
                print("Mirrored {{}} objects across {mirror_axis} plane".format(len(mirrored)))
            else:
                print("Mirror failed")
        else:
            print("No objects found on specified layers")
    """)
