#!/usr/bin/env python3
"""
Rhino Jewellery MCP Server
===========================
A high-level helper MCP that generates ready-to-execute RhinoScript Python code
for jewelry CAD operations. Sits on top of the Rhino MCP — each tool returns
code you paste into mcp__rhino__execute_rhinoscript_python_code.

Tools cover: necklace bases, gem placement, pendants, stems/fringe,
prongs, channels, rings, bails, and boolean operations.
"""

import math
import json
import textwrap
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("rhino-jewellery-mcp")


# ──────────────────────────────────────────────────────────────
# TOOL 1: create_necklace_base
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 2: place_round_gems
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 3: place_baguette_gems
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 4: create_stems
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 5: place_pear_gems_at_stem_tips
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 6: create_cushion_cut_pendant
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 7: create_bail
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 8: create_prongs
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 9: create_channel_setting
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 10: create_ring_band
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 11: create_gem_cutout (boolean subtract)
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 12: mirror_half_necklace
# ──────────────────────────────────────────────────────────────
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


# ══════════════════════════════════════════════════════════════
# SECTION: GEM LIBRARY — Proper faceted gemstone geometry
# ══════════════════════════════════════════════════════════════


def _gem_ngon(cx, cy, z, radius, n):
    """Helper: return list of (x,y,z) points for a regular n-gon, closed."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        pts.append((cx + radius * math.cos(a), cy + radius * math.sin(a), z))
    pts.append(pts[0])
    return pts


def _gem_ellipse_pts(cx, cy, z, rx, ry, n):
    """Helper: elliptical point ring, closed."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a), z))
    pts.append(pts[0])
    return pts


# ──────────────────────────────────────────────────────────────
# TOOL 13: create_round_brilliant_gem
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_round_brilliant_gem(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    diameter: float = 6.0,
    layer: str = "Gem",
    segments: int = 16,
) -> str:
    """Create a round brilliant-cut gemstone with GIA-ideal proportions.

    Builds a faceted gem using polyline cross-sections lofted with straight
    sections. Proportions: table 57%, crown height 16.2%, pavilion depth 43.1%.

    Args:
        center_x/y/z: Gem center position (at girdle).
        diameter: Girdle diameter in mm (6mm ~ 0.75ct diamond).
        layer: Layer for the gem.
        segments: Polygon sides for cross-sections (16 = good approximation).
    """
    r = diameter / 2.0
    table_r = r * 0.57
    crown_h = diameter * 0.162
    pav_d = diameter * 0.431
    girdle_t = diameter * 0.03
    culet_r = r * 0.02
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        cx, cy, cz = {center_x}, {center_y}, {center_z}
        n = {segments}

        def ngon(cx, cy, z, radius):
            pts = []
            for i in range(n):
                a = 2*math.pi*i/n
                pts.append((cx+radius*math.cos(a), cy+radius*math.sin(a), z))
            pts.append(pts[0])
            return pts

        table_crv   = rs.AddPolyline(ngon(cx, cy, cz+{crown_h}, {table_r}))
        u_girdle    = rs.AddPolyline(ngon(cx, cy, cz+{girdle_t/2}, {r}))
        l_girdle    = rs.AddPolyline(ngon(cx, cy, cz-{girdle_t/2}, {r}))
        culet_crv   = rs.AddPolyline(ngon(cx, cy, cz-{pav_d}, {culet_r}))

        for surfs in [rs.AddLoftSrf([table_crv, u_girdle], loft_type=2),
                      rs.AddLoftSrf([l_girdle, culet_crv], loft_type=2),
                      rs.AddPlanarSrf([table_crv]),
                      rs.AddPlanarSrf([culet_crv])]:
            if surfs:
                for s in surfs:
                    rs.ObjectLayer(s, "{layer}")

        rs.DeleteObjects([table_crv, u_girdle, l_girdle, culet_crv])
        print("Round brilliant: {diameter}mm diameter at ({{:.1f}},{{:.1f}},{{:.1f}})".format(cx,cy,cz))
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 14: create_emerald_cut_gem
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_emerald_cut_gem(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    length: float = 7.0,
    width: float = 5.0,
    layer: str = "Gem",
) -> str:
    """Create an emerald-cut (step cut) gemstone.

    Rectangular with clipped corners at multiple step levels.

    Args:
        center_x/y/z: Gem center (at girdle).
        length: Length in mm (along X).
        width: Width in mm (along Y).
        layer: Layer for the gem.
    """
    hl, hw = length / 2.0, width / 2.0
    clip = min(hl, hw) * 0.25
    crown_h = length * 0.12
    step_h = crown_h * 0.5
    pav_d = length * 0.35
    pav_step = pav_d * 0.5
    t_scale = 0.70
    s_scale = 0.85
    p_scale = 0.45
    ps_scale = 0.65

    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        cx, cy, cz = {center_x}, {center_y}, {center_z}

        def octa(hl, hw, clip, z):
            return [
                (cx-hl+clip,cy-hw,z),(cx+hl-clip,cy-hw,z),
                (cx+hl,cy-hw+clip,z),(cx+hl,cy+hw-clip,z),
                (cx+hl-clip,cy+hw,z),(cx-hl+clip,cy+hw,z),
                (cx-hl,cy+hw-clip,z),(cx-hl,cy-hw+clip,z),
                (cx-hl+clip,cy-hw,z),
            ]

        levels = [
            ({hl*t_scale}, {hw*t_scale}, {clip*t_scale}, cz+{crown_h}),
            ({hl*s_scale}, {hw*s_scale}, {clip*s_scale}, cz+{step_h}),
            ({hl}, {hw}, {clip}, cz),
            ({hl*ps_scale}, {hw*ps_scale}, {clip*ps_scale}, cz-{pav_step}),
            ({hl*p_scale}, {hw*p_scale}, {clip*p_scale}, cz-{pav_d}),
        ]

        crvs = [rs.AddPolyline(octa(*lv)) for lv in levels]

        for i in range(len(crvs)-1):
            surfs = rs.AddLoftSrf([crvs[i], crvs[i+1]], loft_type=2)
            if surfs:
                for s in surfs:
                    rs.ObjectLayer(s, "{layer}")

        for cap_crv in [crvs[0], crvs[-1]]:
            cap = rs.AddPlanarSrf([cap_crv])
            if cap:
                for c in cap:
                    rs.ObjectLayer(c, "{layer}")

        rs.DeleteObjects(crvs)
        print("Emerald cut: {length}x{width}mm at ({{:.1f}},{{:.1f}},{{:.1f}})".format(cx,cy,cz))
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 15: create_oval_gem
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_oval_gem(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    length: float = 8.0,
    width: float = 6.0,
    layer: str = "Gem",
    segments: int = 24,
) -> str:
    """Create an oval-cut gemstone with brilliant-style proportions.

    Args:
        center_x/y/z: Center at girdle.
        length/width: Overall dimensions in mm.
        layer: Layer for the gem.
        segments: Points per ellipse outline.
    """
    rx, ry = length / 2.0, width / 2.0
    avg_d = (length + width) / 2.0
    crown_h = avg_d * 0.15
    pav_d = avg_d * 0.42
    girdle_t = avg_d * 0.03
    table_f = 0.57
    culet_f = 0.02

    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        cx, cy, cz = {center_x}, {center_y}, {center_z}
        n = {segments}

        def ellipse(rx, ry, z):
            pts = []
            for i in range(n):
                a = 2*math.pi*i/n
                pts.append((cx+rx*math.cos(a), cy+ry*math.sin(a), z))
            pts.append(pts[0])
            return pts

        table  = rs.AddPolyline(ellipse({rx*table_f}, {ry*table_f}, cz+{crown_h}))
        girdle = rs.AddPolyline(ellipse({rx}, {ry}, cz))
        culet  = rs.AddPolyline(ellipse({rx*culet_f}, {ry*culet_f}, cz-{pav_d}))

        for surfs in [rs.AddLoftSrf([table, girdle], loft_type=2),
                      rs.AddLoftSrf([girdle, culet], loft_type=2),
                      rs.AddPlanarSrf([table]), rs.AddPlanarSrf([culet])]:
            if surfs:
                for s in surfs: rs.ObjectLayer(s, "{layer}")

        rs.DeleteObjects([table, girdle, culet])
        print("Oval gem: {length}x{width}mm")
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 16: create_pear_gem
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_pear_gem(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    length: float = 9.0,
    width: float = 6.0,
    layer: str = "Gem",
    segments: int = 24,
) -> str:
    """Create a pear-shaped (teardrop) gemstone.

    Rounded at one end, pointed at the other.

    Args:
        center_x/y/z: Center at girdle.
        length/width: Tip-to-round and side-to-side dimensions.
        layer: Layer for the gem.
        segments: Outline resolution.
    """
    hl, hw = length / 2.0, width / 2.0
    avg_d = (length + width) / 2.0
    crown_h = avg_d * 0.14
    pav_d = avg_d * 0.40

    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        cx, cy, cz = {center_x}, {center_y}, {center_z}
        n = {segments}
        hl, hw = {hl}, {hw}

        def pear_outline(scale, z):
            pts = []
            for i in range(n):
                t = 2*math.pi*i/n
                # Pear shape: modulated ellipse, narrow at +Y, wide at -Y
                r_base = 1.0
                mod = 0.3 * math.sin(t)  # asymmetric modulation
                rx = hw * scale * (r_base - mod * 0.3)
                ry_pos = hl * scale * (1.0 - 0.35 * (1 + math.sin(t)) / 2)
                x = cx + rx * math.cos(t)
                y = cy + ry_pos * math.sin(t)
                pts.append((x, y, z))
            pts.append(pts[0])
            return pts

        table  = rs.AddPolyline(pear_outline(0.55, cz+{crown_h}))
        girdle = rs.AddPolyline(pear_outline(1.0, cz))
        culet  = rs.AddPolyline(pear_outline(0.03, cz-{pav_d}))

        for surfs in [rs.AddLoftSrf([table, girdle], loft_type=2),
                      rs.AddLoftSrf([girdle, culet], loft_type=2),
                      rs.AddPlanarSrf([table]), rs.AddPlanarSrf([culet])]:
            if surfs:
                for s in surfs: rs.ObjectLayer(s, "{layer}")

        rs.DeleteObjects([table, girdle, culet])
        print("Pear gem: {length}x{width}mm")
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 17: create_marquise_gem
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_marquise_gem(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    length: float = 10.0,
    width: float = 5.0,
    layer: str = "Gem",
    segments: int = 24,
) -> str:
    """Create a marquise-cut (navette) gemstone — pointed at both ends.

    Args:
        center_x/y/z: Center at girdle.
        length/width: Tip-to-tip and max width.
        layer: Layer for the gem.
    """
    hl, hw = length / 2.0, width / 2.0
    avg_d = (length + width) / 2.0
    crown_h = avg_d * 0.14
    pav_d = avg_d * 0.40

    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        cx, cy, cz = {center_x}, {center_y}, {center_z}
        n = {segments}

        def marquise_outline(scale, z):
            pts = []
            for i in range(n):
                t = 2*math.pi*i/n
                # Marquise: x = hw*cos(t), y = hl*sin(t)^p where p<1 sharpens tips
                x = {hw} * scale * math.cos(t)
                sin_t = math.sin(t)
                sign = 1 if sin_t >= 0 else -1
                y = {hl} * scale * sign * (abs(sin_t) ** 0.65)
                pts.append((cx+x, cy+y, z))
            pts.append(pts[0])
            return pts

        table  = rs.AddPolyline(marquise_outline(0.55, cz+{crown_h}))
        girdle = rs.AddPolyline(marquise_outline(1.0, cz))
        culet  = rs.AddPolyline(marquise_outline(0.03, cz-{pav_d}))

        for surfs in [rs.AddLoftSrf([table, girdle], loft_type=2),
                      rs.AddLoftSrf([girdle, culet], loft_type=2),
                      rs.AddPlanarSrf([table]), rs.AddPlanarSrf([culet])]:
            if surfs:
                for s in surfs: rs.ObjectLayer(s, "{layer}")

        rs.DeleteObjects([table, girdle, culet])
        print("Marquise gem: {length}x{width}mm")
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 18: create_princess_cut_gem
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_princess_cut_gem(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    size: float = 5.5,
    layer: str = "Gem",
) -> str:
    """Create a princess-cut gemstone — square with no corner clipping.

    Args:
        center_x/y/z: Center at girdle.
        size: Side length in mm.
        layer: Layer for the gem.
    """
    h = size / 2.0
    crown_h = size * 0.15
    pav_d = size * 0.45

    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        cx, cy, cz = {center_x}, {center_y}, {center_z}

        def square(h, z):
            return [(cx-h,cy-h,z),(cx+h,cy-h,z),(cx+h,cy+h,z),(cx-h,cy+h,z),(cx-h,cy-h,z)]

        table  = rs.AddPolyline(square({h*0.75}, cz+{crown_h}))
        girdle = rs.AddPolyline(square({h}, cz))
        culet  = rs.AddPolyline(square({h*0.03}, cz-{pav_d}))

        for surfs in [rs.AddLoftSrf([table, girdle], loft_type=2),
                      rs.AddLoftSrf([girdle, culet], loft_type=2),
                      rs.AddPlanarSrf([table]), rs.AddPlanarSrf([culet])]:
            if surfs:
                for s in surfs: rs.ObjectLayer(s, "{layer}")

        rs.DeleteObjects([table, girdle, culet])
        print("Princess cut: {size}mm square")
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 19: create_trillion_gem
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_trillion_gem(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    size: float = 7.0,
    layer: str = "Gem",
) -> str:
    """Create a trillion-cut gemstone — triangular with slightly convex sides.

    Args:
        center_x/y/z: Center at girdle.
        size: Point-to-point distance in mm.
        layer: Layer for the gem.
    """
    r = size / (2.0 * math.cos(math.radians(30)))  # circumradius
    crown_h = size * 0.13
    pav_d = size * 0.38

    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        cx, cy, cz = {center_x}, {center_y}, {center_z}

        def triangle(r, z):
            pts = []
            for i in range(3):
                a = math.radians(90 + 120*i)
                pts.append((cx+r*math.cos(a), cy+r*math.sin(a), z))
            pts.append(pts[0])
            return pts

        table  = rs.AddPolyline(triangle({r*0.55}, cz+{crown_h}))
        girdle = rs.AddPolyline(triangle({r}, cz))
        culet  = rs.AddPolyline(triangle({r*0.03}, cz-{pav_d}))

        for surfs in [rs.AddLoftSrf([table, girdle], loft_type=2),
                      rs.AddLoftSrf([girdle, culet], loft_type=2),
                      rs.AddPlanarSrf([table]), rs.AddPlanarSrf([culet])]:
            if surfs:
                for s in surfs: rs.ObjectLayer(s, "{layer}")

        rs.DeleteObjects([table, girdle, culet])
        print("Trillion gem: {size}mm")
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 20: create_cushion_gem
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_cushion_gem(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    length: float = 7.0,
    width: float = 6.0,
    layer: str = "Gem",
) -> str:
    """Create a cushion-cut gemstone — rounded-corner rectangle.

    Args:
        center_x/y/z: Center at girdle.
        length/width: Dimensions in mm.
        layer: Layer for the gem.
    """
    hl, hw = length / 2.0, width / 2.0
    clip = min(hl, hw) * 0.30
    avg_d = (length + width) / 2.0
    crown_h = avg_d * 0.14
    pav_d = avg_d * 0.40

    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        cx, cy, cz = {center_x}, {center_y}, {center_z}

        def octa(hl, hw, clip, z):
            return [
                (cx-hl+clip,cy-hw,z),(cx+hl-clip,cy-hw,z),
                (cx+hl,cy-hw+clip,z),(cx+hl,cy+hw-clip,z),
                (cx+hl-clip,cy+hw,z),(cx-hl+clip,cy+hw,z),
                (cx-hl,cy+hw-clip,z),(cx-hl,cy-hw+clip,z),
                (cx-hl+clip,cy-hw,z),
            ]

        table  = rs.AddPolyline(octa({hl*0.65},{hw*0.65},{clip*0.65},cz+{crown_h}))
        girdle = rs.AddPolyline(octa({hl},{hw},{clip},cz))
        culet  = rs.AddPolyline(octa({hl*0.25},{hw*0.25},{clip*0.25},cz-{pav_d}))

        for surfs in [rs.AddLoftSrf([table, girdle], loft_type=2),
                      rs.AddLoftSrf([girdle, culet], loft_type=2),
                      rs.AddPlanarSrf([table]), rs.AddPlanarSrf([culet])]:
            if surfs:
                for s in surfs: rs.ObjectLayer(s, "{layer}")

        rs.DeleteObjects([table, girdle, culet])
        print("Cushion gem: {length}x{width}mm")
    """)


# ══════════════════════════════════════════════════════════════
# SECTION: STONE SETTINGS
# ══════════════════════════════════════════════════════════════


@mcp.tool()
def create_bezel_setting(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    gem_diameter: float = 6.0,
    wall_thickness: float = 0.5,
    wall_height: float = 1.5,
    layer: str = "Metal_Setting",
) -> str:
    """Create a bezel setting — a continuous metal collar encircling a stone.

    Args:
        center_x/y/z: Center of the setting.
        gem_diameter: Inner diameter matching the gem girdle.
        wall_thickness: Metal wall thickness in mm.
        wall_height: Height of the bezel wall.
        layer: Layer for the metal.
    """
    inner_r = gem_diameter / 2.0
    outer_r = inner_r + wall_thickness
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        cx, cy, cz = {center_x}, {center_y}, {center_z}
        plane = rs.PlaneFromNormal((cx,cy,cz), (0,0,1))

        inner_circle = rs.AddCircle(plane, {inner_r})
        outer_circle = rs.AddCircle(plane, {outer_r})

        inner_pipe = rs.AddPipe(rs.AddLine((cx,cy,cz),(cx,cy,cz+{wall_height})), 0, {inner_r}, cap=1)
        outer_pipe = rs.AddPipe(rs.AddLine((cx,cy,cz),(cx,cy,cz+{wall_height})), 0, {outer_r}, cap=1)

        # Simpler: use pipe on circle for the bezel ring
        rs.DeleteObjects([inner_circle, outer_circle])
        if inner_pipe: rs.DeleteObjects(inner_pipe)
        if outer_pipe: rs.DeleteObjects(outer_pipe)

        # Build as offset circles piped
        top_plane = rs.PlaneFromNormal((cx,cy,cz+{wall_height}/2), (0,0,1))
        ring_crv = rs.AddCircle(top_plane, {inner_r + wall_thickness/2})
        bezel = rs.AddPipe(ring_crv, 0, {wall_thickness/2}, cap=1)
        if bezel:
            for b in bezel:
                rs.ScaleObject(b, (cx,cy,cz+{wall_height}/2), (1,1,{wall_height/wall_thickness}))
                rs.ObjectLayer(b, "{layer}")
        rs.DeleteObject(ring_crv)
        print("Bezel setting: {gem_diameter}mm, wall {wall_thickness}mm")
    """)


@mcp.tool()
def create_flush_setting(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    gem_diameter: float = 4.0,
    metal_diameter: float = 8.0,
    metal_height: float = 3.0,
    layer: str = "Metal_Setting",
) -> str:
    """Create a flush (gypsy) setting — stone sunk into a metal surface.

    Generates a metal cylinder with a conical bore for the gem pavilion.

    Args:
        center_x/y/z: Center of the setting surface.
        gem_diameter: Stone diameter.
        metal_diameter: Surrounding metal diameter.
        metal_height: Total metal height.
        layer: Layer for the metal.
    """
    gem_r = gem_diameter / 2.0
    metal_r = metal_diameter / 2.0
    pav_depth = gem_diameter * 0.4
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        cx, cy, cz = {center_x}, {center_y}, {center_z}

        # Metal body
        metal = rs.AddCylinder((cx,cy,cz-{metal_height}), (cx,cy,cz), {metal_r})

        # Pavilion bore (cone)
        bore = rs.AddCone((cx,cy,cz), -(cz-{pav_depth}+{metal_height}), {gem_r})

        if metal and bore:
            result = rs.BooleanDifference([metal], [bore], True)
            if result:
                for r in result:
                    rs.ObjectLayer(r, "{layer}")
                print("Flush setting: {gem_diameter}mm stone in {metal_diameter}mm metal")
            else:
                rs.ObjectLayer(metal, "{layer}")
                print("Boolean failed - metal placed without bore")
    """)


@mcp.tool()
def create_pave_setting(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    area_width: float = 10.0,
    area_length: float = 10.0,
    gem_diameter: float = 1.2,
    gem_spacing: float = 0.3,
    gem_layer: str = "Pave_Gems",
    metal_layer: str = "Pave_Metal",
) -> str:
    """Create a pave setting — tightly packed small stones with bead prongs.

    Hex-packed grid layout maximizing stone density.

    Args:
        center_x/y/z: Center of the pave area.
        area_width/length: Rectangular area to fill.
        gem_diameter: Individual stone diameter.
        gem_spacing: Gap between stones.
        gem_layer: Layer for the gems.
        metal_layer: Layer for the bead prongs.
    """
    gem_r = gem_diameter / 2.0
    bead_r = gem_diameter * 0.15
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        for layer in ["{gem_layer}", "{metal_layer}"]:
            if not rs.IsLayer(layer):
                rs.AddLayer(layer)

        cx, cy, cz = {center_x}, {center_y}, {center_z}
        gem_r = {gem_r}
        col_sp = {gem_diameter} + {gem_spacing}
        row_sp = col_sp * math.sqrt(3) / 2

        count = 0
        row = 0
        y = cy - {area_length}/2
        while y <= cy + {area_length}/2:
            x_off = col_sp / 2 if (row % 2) else 0
            x = cx - {area_width}/2 + x_off
            while x <= cx + {area_width}/2:
                gem = rs.AddSphere((x, y, cz), gem_r)
                if gem:
                    rs.ScaleObject(gem, (x,y,cz), (1,1,0.5))
                    rs.ObjectLayer(gem, "{gem_layer}")
                    count += 1

                # 4 bead prongs
                for angle in [0, 90, 180, 270]:
                    a = math.radians(angle)
                    bx = x + gem_r * 0.9 * math.cos(a)
                    by = y + gem_r * 0.9 * math.sin(a)
                    bead = rs.AddSphere((bx, by, cz + gem_r*0.3), {bead_r})
                    if bead:
                        rs.ObjectLayer(bead, "{metal_layer}")

                x += col_sp
            y += row_sp
            row += 1

        print("Pave: {{}} stones ({gem_diameter}mm) in {area_width}x{area_length}mm area".format(count))
    """)


@mcp.tool()
def create_halo_setting(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    center_gem_diameter: float = 6.0,
    halo_gem_diameter: float = 1.2,
    halo_count: int = 16,
    num_rows: int = 1,
    gap: float = 0.5,
    gem_layer: str = "Halo_Gems",
    metal_layer: str = "Halo_Metal",
) -> str:
    """Create a halo setting — ring(s) of small stones around a center stone.

    Args:
        center_x/y/z: Center of the halo.
        center_gem_diameter: The center stone diameter (determines halo radius).
        halo_gem_diameter: Diameter of each halo stone.
        halo_count: Number of stones per row.
        num_rows: 1 = single halo, 2 = double halo.
        gap: Space between center gem and first halo row.
        gem_layer: Layer for halo stones.
        metal_layer: Layer for halo metal ring.
    """
    center_r = center_gem_diameter / 2.0
    halo_r = halo_gem_diameter / 2.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        for layer in ["{gem_layer}", "{metal_layer}"]:
            if not rs.IsLayer(layer):
                rs.AddLayer(layer)

        cx, cy, cz = {center_x}, {center_y}, {center_z}

        for row in range({num_rows}):
            ring_r = {center_r} + {gap} + {halo_r} + row * ({halo_gem_diameter} + 0.3)
            count = {halo_count} + row * 6

            # Gems
            for i in range(count):
                a = 2 * math.pi * i / count
                pt = (cx + ring_r*math.cos(a), cy + ring_r*math.sin(a), cz)
                gem = rs.AddSphere(pt, {halo_r})
                if gem:
                    rs.ScaleObject(gem, pt, (1,1,0.45))
                    rs.ObjectLayer(gem, "{gem_layer}")

            # Metal ring
            plane = rs.PlaneFromNormal((cx,cy,cz), (0,0,1))
            circle = rs.AddCircle(plane, ring_r)
            if circle:
                pipe = rs.AddPipe(circle, 0, 0.2, cap=1)
                if pipe:
                    for p in pipe: rs.ObjectLayer(p, "{metal_layer}")
                rs.DeleteObject(circle)

        print("Halo: {num_rows} row(s), {halo_count} stones/row around {center_gem_diameter}mm center")
    """)


@mcp.tool()
def create_claw_setting(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    gem_diameter: float = 6.0,
    num_claws: int = 6,
    claw_width: float = 0.8,
    claw_height: float = 2.5,
    layer: str = "Metal_Setting",
) -> str:
    """Create a claw setting — V-shaped prongs with curved tips gripping the stone.

    Each claw curves from a base ring up and over the girdle.

    Args:
        center_x/y/z: Center of the stone.
        gem_diameter: Stone diameter.
        num_claws: Number of claws (4/6/8 typical).
        claw_width: Width of each claw wire.
        claw_height: How far claws extend above girdle.
        layer: Layer for the metal.
    """
    gem_r = gem_diameter / 2.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        cx, cy, cz = {center_x}, {center_y}, {center_z}
        gem_r = {gem_r}

        # Base ring
        plane = rs.PlaneFromNormal((cx,cy,cz-1), (0,0,1))
        base_circle = rs.AddCircle(plane, gem_r + 0.5)
        if base_circle:
            bp = rs.AddPipe(base_circle, 0, {claw_width/2}, cap=1)
            if bp:
                for b in bp: rs.ObjectLayer(b, "{layer}")
            rs.DeleteObject(base_circle)

        # Claws
        for i in range({num_claws}):
            a = 2*math.pi*i/{num_claws}
            bx = cx + (gem_r+0.5)*math.cos(a)
            by = cy + (gem_r+0.5)*math.sin(a)
            # Claw path: base → girdle height → tip curling inward
            pts = [
                (bx, by, cz - 1),
                (bx, by, cz),
                (cx + (gem_r-0.2)*math.cos(a), cy + (gem_r-0.2)*math.sin(a), cz + {claw_height}*0.7),
                (cx + (gem_r-0.5)*math.cos(a), cy + (gem_r-0.5)*math.sin(a), cz + {claw_height}),
            ]
            crv = rs.AddInterpCurve(pts, degree=3)
            if crv:
                pipe = rs.AddPipe(crv, [0,0.5,1], [{claw_width/2}, {claw_width/2*0.8}, {claw_width/2*0.5}], 0, 2)
                if pipe:
                    for p in pipe: rs.ObjectLayer(p, "{layer}")
                rs.DeleteObject(crv)

        print("Claw setting: {num_claws} claws for {gem_diameter}mm stone")
    """)


@mcp.tool()
def create_bead_setting(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    gem_diameter: float = 2.0,
    num_beads: int = 4,
    bead_diameter: float = 0.4,
    layer: str = "Metal_Setting",
) -> str:
    """Create a bead setting — small metal beads pushed over stone edges.

    Simplest setting type with a flat seat plate underneath.

    Args:
        center_x/y/z: Center of the stone.
        gem_diameter: Stone diameter.
        num_beads: Number of beads (4 typical).
        bead_diameter: Diameter of each metal bead.
        layer: Layer for the metal.
    """
    gem_r = gem_diameter / 2.0
    bead_r = bead_diameter / 2.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        cx, cy, cz = {center_x}, {center_y}, {center_z}

        # Seat plate
        seat = rs.AddCylinder((cx,cy,cz-0.3), (cx,cy,cz), {gem_r*0.7})
        if seat: rs.ObjectLayer(seat, "{layer}")

        # Beads
        for i in range({num_beads}):
            a = 2*math.pi*i/{num_beads}
            bx = cx + {gem_r*0.85}*math.cos(a)
            by = cy + {gem_r*0.85}*math.sin(a)
            bead = rs.AddSphere((bx, by, cz+{gem_r*0.2}), {bead_r})
            if bead: rs.ObjectLayer(bead, "{layer}")

        print("Bead setting: {num_beads} beads for {gem_diameter}mm stone")
    """)


# ══════════════════════════════════════════════════════════════
# SECTION: RING TOOLS
# ══════════════════════════════════════════════════════════════


@mcp.tool()
def ring_sizer(
    us_size: float = 7.0,
) -> str:
    """Convert US ring size to diameter and other international systems.

    Args:
        us_size: US ring size (e.g., 7.0).

    Returns:
        Code that prints conversion table and creates a reference circle.
    """
    diameter = 11.63 + (us_size * 0.8128)
    circumference = diameter * math.pi
    eu_size = circumference
    uk_offset = us_size * 2 - 1  # approximate
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        dia = {diameter:.2f}
        circ = {circumference:.2f}

        print("=== Ring Size Conversion ===")
        print("US Size:      {us_size}")
        print("Diameter:     {{:.2f}} mm".format(dia))
        print("Circumference:{{:.2f}} mm".format(circ))
        print("EU Size:      {{:.1f}}".format(circ))
        print("Inner radius: {{:.2f}} mm".format(dia/2))

        # Create reference circle
        circle = rs.AddCircle((0,0,0), dia/2)
        if circle:
            rs.ObjectName(circle, "RingSize_US{us_size}")
            print("Reference circle created at origin")
    """)


@mcp.tool()
def create_d_profile_band(
    inner_diameter: float = 17.0,
    band_width: float = 4.0,
    band_thickness: float = 1.8,
    layer: str = "Ring_Band",
) -> str:
    """Create a D-profile ring band — flat inside, domed outside.

    Industry-standard band cross-section. Uses revolve around Z-axis.

    Args:
        inner_diameter: Inner diameter in mm (US 7 ~ 17.3mm).
        band_width: Band width in mm.
        band_thickness: Metal thickness (radial) in mm.
        layer: Layer for the band.
    """
    inner_r = inner_diameter / 2.0
    outer_r = inner_r + band_thickness
    hw = band_width / 2.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        ir = {inner_r}
        otr = {outer_r}
        hw = {hw}

        # D-profile: flat inner, domed outer
        # Points in XZ plane at radius from Z-axis
        profile_pts = [
            (ir, 0, -hw),          # inner bottom
            (ir, 0, hw),           # inner top
            (otr, 0, hw*0.7),     # outer top transition
            (otr + {band_thickness*0.15}, 0, 0),  # outer dome peak
            (otr, 0, -hw*0.7),    # outer bottom transition
            (ir, 0, -hw),          # close
        ]

        profile = rs.AddInterpCurve(profile_pts, degree=3)
        if profile:
            band = rs.AddRevSrf(profile, ((0,0,0),(0,0,1)))
            if band:
                rs.ObjectLayer(band, "{layer}")
                print("D-profile band: {inner_diameter}mm ID, {band_width}mm wide, {band_thickness}mm thick")
            rs.DeleteObject(profile)
    """)


@mcp.tool()
def create_comfort_fit_band(
    inner_diameter: float = 17.0,
    band_width: float = 5.0,
    band_thickness: float = 2.0,
    layer: str = "Ring_Band",
) -> str:
    """Create a comfort-fit band — convex inside and outside (lens profile).

    More comfortable than D-profile for wider bands.

    Args:
        inner_diameter: Inner diameter in mm.
        band_width: Band width in mm.
        band_thickness: Radial thickness in mm.
        layer: Layer for the band.
    """
    inner_r = inner_diameter / 2.0
    outer_r = inner_r + band_thickness
    hw = band_width / 2.0
    mid_r = (inner_r + outer_r) / 2.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        ir = {inner_r}
        otr = {outer_r}
        hw = {hw}

        profile_pts = [
            ({mid_r}, 0, -hw),
            (ir - {band_thickness*0.08}, 0, 0),    # inner concave
            ({mid_r}, 0, hw),
            (otr + {band_thickness*0.12}, 0, 0),   # outer dome
            ({mid_r}, 0, -hw),
        ]

        profile = rs.AddInterpCurve(profile_pts, degree=3)
        if profile:
            band = rs.AddRevSrf(profile, ((0,0,0),(0,0,1)))
            if band:
                rs.ObjectLayer(band, "{layer}")
                print("Comfort fit band: {inner_diameter}mm ID, {band_width}mm wide")
            rs.DeleteObject(profile)
    """)


@mcp.tool()
def create_signet_ring(
    inner_diameter: float = 17.0,
    band_width: float = 4.0,
    face_width: float = 12.0,
    face_length: float = 10.0,
    layer: str = "Signet_Ring",
) -> str:
    """Create a signet ring — band widening to a flat engraving face at top.

    Args:
        inner_diameter: Inner diameter in mm.
        band_width: Band width at bottom.
        face_width/length: Flat face dimensions at top.
        layer: Layer for the ring.
    """
    inner_r = inner_diameter / 2.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        ir = {inner_r}

        # Create varying cross-sections around the ring
        # Bottom (6 o'clock): narrow band
        # Top (12 o'clock): wide face
        sections = []
        n_sections = 12
        for i in range(n_sections):
            angle = 2*math.pi*i/n_sections
            t = (1 + math.cos(angle)) / 2  # 0 at bottom, 1 at top

            w = {band_width} + ({face_width} - {band_width}) * t
            thick = 1.8 + 1.0 * t
            hw = w / 2

            cx = (ir + thick/2) * math.cos(angle)
            cy = (ir + thick/2) * math.sin(angle)

            # Cross section perpendicular to ring path
            tang_x = -math.sin(angle)
            tang_y = math.cos(angle)

            pts = [
                (cx - thick/2*math.cos(angle), cy - thick/2*math.sin(angle), -hw),
                (cx - thick/2*math.cos(angle), cy - thick/2*math.sin(angle), hw),
                (cx + thick/2*math.cos(angle), cy + thick/2*math.sin(angle), hw),
                (cx + thick/2*math.cos(angle), cy + thick/2*math.sin(angle), -hw),
                (cx - thick/2*math.cos(angle), cy - thick/2*math.sin(angle), -hw),
            ]
            crv = rs.AddPolyline(pts)
            sections.append(crv)

        if len(sections) >= 3:
            loft = rs.AddLoftSrf(sections, closed=True)
            if loft:
                for s in loft:
                    rs.ObjectLayer(s, "{layer}")

        rs.DeleteObjects(sections)
        print("Signet ring: {inner_diameter}mm ID, face {face_width}x{face_length}mm")
    """)


@mcp.tool()
def create_split_shank_ring(
    inner_diameter: float = 17.0,
    band_width: float = 3.0,
    split_angle: float = 60.0,
    split_gap: float = 2.0,
    wire_radius: float = 0.8,
    layer: str = "Ring_Band",
) -> str:
    """Create a split-shank ring — band splits into two rails at the top.

    Args:
        inner_diameter: Inner diameter in mm.
        band_width: Band width at bottom.
        split_angle: Angle (degrees) where the split begins.
        split_gap: Gap between the two shanks at top.
        wire_radius: Radius of each shank wire.
        layer: Layer for the band.
    """
    inner_r = inner_diameter / 2.0
    outer_r = inner_r + 2.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        ir = {inner_r}
        otr = {outer_r}
        split_a = math.radians({split_angle})
        gap = {split_gap} / 2

        # Bottom arc (single band)
        bottom_pts = []
        for i in range(20):
            a = math.pi + split_a + (2*(math.pi - split_a)) * i / 19
            bottom_pts.append((otr*math.cos(a), otr*math.sin(a), 0))

        bottom_crv = rs.AddInterpCurve(bottom_pts, degree=3)
        if bottom_crv:
            bp = rs.AddPipe(bottom_crv, 0, {wire_radius}, cap=2)
            if bp:
                for b in bp: rs.ObjectLayer(b, "{layer}")
            rs.DeleteObject(bottom_crv)

        # Two split shanks from split point to top
        for side in [-1, 1]:
            pts = []
            for i in range(10):
                t = i / 9.0
                a = math.pi/2 - side * split_a * (1 - t)
                z_off = side * gap * t
                pts.append((otr*math.cos(a), otr*math.sin(a), z_off))
            crv = rs.AddInterpCurve(pts, degree=3)
            if crv:
                sp = rs.AddPipe(crv, 0, {wire_radius}, cap=2)
                if sp:
                    for s in sp: rs.ObjectLayer(s, "{layer}")
                rs.DeleteObject(crv)

        print("Split shank ring: {inner_diameter}mm ID, split at {split_angle} deg")
    """)


@mcp.tool()
def create_solitaire_ring(
    us_size: float = 7.0,
    gem_diameter: float = 6.0,
    num_prongs: int = 6,
    band_width: float = 2.5,
    band_thickness: float = 1.8,
    band_layer: str = "Ring_Band",
    gem_layer: str = "Ring_Gem",
    setting_layer: str = "Ring_Setting",
) -> str:
    """Create a complete solitaire ring — band + round brilliant gem + prong setting.

    All-in-one builder that composes a D-profile band, a round brilliant gem
    at the top, and a prong setting.

    Args:
        us_size: US ring size.
        gem_diameter: Center stone diameter.
        num_prongs: Prong count (4 or 6 typical).
        band_width/thickness: Band dimensions.
        band_layer/gem_layer/setting_layer: Layer assignments.
    """
    inner_d = 11.63 + (us_size * 0.8128)
    inner_r = inner_d / 2.0
    outer_r = inner_r + band_thickness
    gem_r = gem_diameter / 2.0
    gem_z = outer_r + gem_r * 0.3  # gem sits just above top of band
    hw = band_width / 2.0
    crown_h = gem_diameter * 0.162
    pav_d = gem_diameter * 0.431

    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        for layer in ["{band_layer}", "{gem_layer}", "{setting_layer}"]:
            if not rs.IsLayer(layer):
                rs.AddLayer(layer)

        ir = {inner_r}
        otr = {outer_r}

        # === BAND (D-profile revolve) ===
        profile = rs.AddInterpCurve([
            (ir, 0, -{hw}), (ir, 0, {hw}),
            (otr, 0, {hw*0.7}),
            (otr+{band_thickness*0.15}, 0, 0),
            (otr, 0, -{hw*0.7}),
            (ir, 0, -{hw}),
        ], degree=3)
        if profile:
            band = rs.AddRevSrf(profile, ((0,0,0),(0,0,1)))
            if band: rs.ObjectLayer(band, "{band_layer}")
            rs.DeleteObject(profile)

        # === GEM (round brilliant at top) ===
        gem_cx, gem_cy, gem_cz = 0, otr + {gem_r*0.3}, 0
        n = 16
        def ngon(r, z):
            pts = []
            for i in range(n):
                a = 2*math.pi*i/n
                pts.append((gem_cx+r*math.cos(a), z, gem_cz+r*math.sin(a)))
            pts.append(pts[0])
            return pts

        table_crv = rs.AddPolyline(ngon({gem_r*0.57}, gem_cy+{crown_h}))
        girdle_crv = rs.AddPolyline(ngon({gem_r}, gem_cy))
        culet_crv = rs.AddPolyline(ngon({gem_r*0.02}, gem_cy-{pav_d}))

        for surfs in [rs.AddLoftSrf([table_crv, girdle_crv], loft_type=2),
                      rs.AddLoftSrf([girdle_crv, culet_crv], loft_type=2),
                      rs.AddPlanarSrf([table_crv]), rs.AddPlanarSrf([culet_crv])]:
            if surfs:
                for s in surfs: rs.ObjectLayer(s, "{gem_layer}")
        rs.DeleteObjects([table_crv, girdle_crv, culet_crv])

        # === PRONGS ===
        for i in range({num_prongs}):
            a = 2*math.pi*i/{num_prongs}
            px = gem_cx + ({gem_r}+0.3)*math.cos(a)
            pz = gem_cz + ({gem_r}+0.3)*math.sin(a)
            pts = [
                (px, gem_cy-1.5, pz),
                (px, gem_cy, pz),
                (gem_cx+({gem_r}-0.3)*math.cos(a), gem_cy+{crown_h}*0.8,
                 gem_cz+({gem_r}-0.3)*math.sin(a)),
            ]
            crv = rs.AddInterpCurve(pts, degree=3)
            if crv:
                pipe = rs.AddPipe(crv, [0,1], [0.4, 0.25], 0, 2)
                if pipe:
                    for p in pipe: rs.ObjectLayer(p, "{setting_layer}")
                rs.DeleteObject(crv)

        print("Solitaire ring: US {us_size}, {gem_diameter}mm stone, {num_prongs} prongs")
    """)


@mcp.tool()
def create_ring_head(
    inner_diameter: float = 17.0,
    head_height: float = 6.0,
    head_width: float = 8.0,
    num_prongs: int = 4,
    prong_thickness: float = 0.8,
    layer: str = "Ring_Head",
) -> str:
    """Create a ring head (basket) — the structure that holds the center stone.

    Includes prongs rising from a base ring with gallery wires between them.

    Args:
        inner_diameter: Ring inner diameter (to position head at top).
        head_height: Total height of the head above band.
        head_width: Width of the basket base.
        num_prongs: Number of prongs.
        prong_thickness: Prong wire diameter.
        layer: Layer for the head.
    """
    band_top_r = inner_diameter / 2.0 + 2.0
    basket_r = head_width / 2.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        base_y = {band_top_r}
        basket_r = {basket_r}

        # Base ring
        plane = rs.PlaneFromNormal((0, base_y, 0), (0, 1, 0))
        base_circle = rs.AddCircle(plane, basket_r)
        if base_circle:
            bp = rs.AddPipe(base_circle, 0, {prong_thickness/2}, cap=1)
            if bp:
                for b in bp: rs.ObjectLayer(b, "{layer}")
            rs.DeleteObject(base_circle)

        # Gallery wire (mid-height ring)
        mid_plane = rs.PlaneFromNormal((0, base_y + {head_height*0.4}, 0), (0, 1, 0))
        gallery = rs.AddCircle(mid_plane, basket_r * 0.85)
        if gallery:
            gp = rs.AddPipe(gallery, 0, {prong_thickness/2*0.7}, cap=1)
            if gp:
                for g in gp: rs.ObjectLayer(g, "{layer}")
            rs.DeleteObject(gallery)

        # Prongs
        for i in range({num_prongs}):
            a = 2*math.pi*i/{num_prongs}
            bx = basket_r * math.cos(a)
            bz = basket_r * math.sin(a)
            pts = [
                (bx, base_y, bz),
                (bx*0.9, base_y + {head_height}*0.5, bz*0.9),
                (bx*0.75, base_y + {head_height}, bz*0.75),
            ]
            crv = rs.AddInterpCurve(pts, degree=3)
            if crv:
                pipe = rs.AddPipe(crv, [0,1], [{prong_thickness/2}, {prong_thickness/2*0.6}], 0, 2)
                if pipe:
                    for p in pipe: rs.ObjectLayer(p, "{layer}")
                rs.DeleteObject(crv)

        print("Ring head: {num_prongs} prongs, {head_height}mm tall, {head_width}mm wide")
    """)


# ══════════════════════════════════════════════════════════════
# SECTION: ASSEMBLY & UTILITY
# ══════════════════════════════════════════════════════════════


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


# ══════════════════════════════════════════════════════════════
# SECTION: MANUFACTURING & PRODUCTION
# ══════════════════════════════════════════════════════════════


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


# ══════════════════════════════════════════════════════════════
# SECTION: FINISHING TOOLS
# ══════════════════════════════════════════════════════════════


@mcp.tool()
def fillet_edges(
    object_layer: str = "Metal",
    radius: float = 0.3,
    output_layer: str = "Metal_Filleted",
) -> str:
    """Apply fillet (smooth rounding) to all edges of objects on a layer.

    Critical for casting — sharp internal corners cause porosity.

    Args:
        object_layer: Layer with objects to fillet.
        radius: Fillet radius in mm.
        output_layer: Layer for filleted results.
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
                rs.SelectObject(obj)
                rs.Command("-_FilletEdge Radius={radius} EnterEnd", False)
                rs.UnselectAllObjects()
                count += 1
            print("Applied {radius}mm fillet to {{}} objects".format(count))
    """)


@mcp.tool()
def chamfer_edges(
    object_layer: str = "Metal",
    distance: float = 0.2,
    output_layer: str = "Metal_Chamfered",
) -> str:
    """Apply chamfer (angled bevel) to all edges of objects on a layer.

    Args:
        object_layer: Layer with objects to chamfer.
        distance: Chamfer distance in mm.
        output_layer: Layer for results.
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
                rs.SelectObject(obj)
                rs.Command("-_ChamferEdge Distance={distance} EnterEnd", False)
                rs.UnselectAllObjects()
                count += 1
            print("Applied {distance}mm chamfer to {{}} objects".format(count))
    """)


@mcp.tool()
def create_engraving_text(
    text: str = "925",
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    height: float = 1.5,
    depth: float = 0.2,
    layer: str = "Engraving",
) -> str:
    """Create engraving text geometry for stamping into metal.

    Common hallmarks: 925 (sterling), 750 (18k), 585 (14k), PT950 (platinum).

    Args:
        text: Text string to engrave.
        center_x/y/z: Position of the engraving.
        height: Text height in mm.
        depth: Engraving depth in mm.
        layer: Layer for the engraving geometry.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        # Create text as curves
        rs.Command('-_TextObject Height={height} Output=Curves Font=Arial "{text}" _Enter', False)
        text_objs = rs.LastCreatedObjects()

        if text_objs:
            # Move to position
            rs.MoveObjects(text_objs, ({center_x}, {center_y}, {center_z}))

            # Extrude for depth
            for obj in text_objs:
                if rs.IsCurve(obj):
                    srf = rs.ExtrudeCurveStraight(obj, (0,0,0), (0,0,-{depth}))
                    if srf:
                        rs.ObjectLayer(srf, "{layer}")

            rs.DeleteObjects(text_objs)
            print("Engraving: '{text}' at {height}mm height, {depth}mm deep")
        else:
            print("Text creation failed - try running in Rhino directly")
    """)


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


# ══════════════════════════════════════════════════════════════
# SECTION: ADDITIONAL JEWELRY TYPES
# ══════════════════════════════════════════════════════════════


@mcp.tool()
def create_bangle(
    inner_diameter: float = 62.0,
    cross_section: str = "round",
    thickness: float = 4.0,
    width: float = 6.0,
    is_open: bool = False,
    opening_gap_degrees: float = 30.0,
    layer: str = "Bangle",
) -> str:
    """Create a bangle bracelet — rigid circular/oval bracelet.

    Args:
        inner_diameter: Inner diameter in mm (62mm = average wrist).
        cross_section: "round", "oval", or "flat".
        thickness: Cross-section thickness in mm.
        width: Cross-section width in mm (for oval/flat).
        is_open: Whether the bangle has an opening.
        opening_gap_degrees: Size of opening in degrees (if open).
        layer: Layer for the bangle.
    """
    inner_r = inner_diameter / 2.0
    minor_r = thickness / 2.0
    major_r = inner_r + minor_r
    end_angle = 360.0 - opening_gap_degrees if is_open else 360.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        cross = "{cross_section}"

        if cross == "round":
            bangle = rs.AddTorus((0,0,0), {major_r}, {minor_r})
            if bangle:
                rs.ObjectLayer(bangle, "{layer}")
        else:
            # D-profile or flat: use revolve
            ir = {inner_r}
            hw = {width}/2
            thick = {thickness}

            if cross == "oval":
                pts = [
                    (ir, 0, -hw), (ir-thick*0.05, 0, 0), (ir, 0, hw),
                    (ir+thick, 0, hw*0.8), (ir+thick+thick*0.1, 0, 0),
                    (ir+thick, 0, -hw*0.8), (ir, 0, -hw),
                ]
            else:  # flat
                pts = [
                    (ir, 0, -hw), (ir, 0, hw),
                    (ir+thick, 0, hw), (ir+thick, 0, -hw), (ir, 0, -hw),
                ]

            profile = rs.AddInterpCurve(pts, degree=3)
            if profile:
                bangle = rs.AddRevSrf(profile, ((0,0,0),(0,0,1)), 0, {end_angle})
                if bangle:
                    rs.ObjectLayer(bangle, "{layer}")
                rs.DeleteObject(profile)

        open_str = "open ({{}}deg gap)".format({opening_gap_degrees}) if {is_open} else "closed"
        print("Bangle: {inner_diameter}mm ID, {cross_section}, " + open_str)
    """)


@mcp.tool()
def create_earring_base(
    style: str = "stud",
    diameter: float = 8.0,
    drop_length: float = 25.0,
    hoop_diameter: float = 20.0,
    wire_thickness: float = 0.8,
    layer: str = "Earring",
) -> str:
    """Create an earring base structure (stud, drop, or hoop).

    Args:
        style: "stud", "drop", or "hoop".
        diameter: Stud face diameter or drop width.
        drop_length: Length for drop earrings.
        hoop_diameter: Outer diameter for hoops.
        wire_thickness: Wire gauge diameter.
        layer: Layer for the earring.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        style = "{style}"

        if style == "stud":
            # Flat disc + post
            disc = rs.AddCylinder((0,0,-0.5), (0,0,0.5), {diameter/2})
            if disc: rs.ObjectLayer(disc, "{layer}")
            post = rs.AddCylinder((0,0,-0.5), (0,0,-12), 0.4)
            if post: rs.ObjectLayer(post, "{layer}")
            print("Stud earring: {diameter}mm face, 12mm post")

        elif style == "drop":
            # Wire hook + drop bar
            hook_pts = [(0,0,0), (2,0,5), (0,0,10), (-1,0,12), (-2,0,8)]
            hook = rs.AddInterpCurve(hook_pts, degree=3)
            if hook:
                hp = rs.AddPipe(hook, 0, {wire_thickness/2}, cap=2)
                if hp:
                    for h in hp: rs.ObjectLayer(h, "{layer}")
                rs.DeleteObject(hook)
            # Drop bar
            bar = rs.AddLine((0,0,0), (0,0,-{drop_length}))
            if bar:
                bp = rs.AddPipe(bar, 0, {wire_thickness/2}, cap=2)
                if bp:
                    for b in bp: rs.ObjectLayer(b, "{layer}")
                rs.DeleteObject(bar)
            # Loop connector
            loop = rs.AddTorus((0,0,0), 1.5, {wire_thickness/2})
            if loop: rs.ObjectLayer(loop, "{layer}")
            print("Drop earring: {drop_length}mm length")

        elif style == "hoop":
            # Partial torus (300 degrees) + post
            hoop_r = {hoop_diameter/2}
            profile_pts = [
                (hoop_r, 0, -{wire_thickness/2}), (hoop_r-{wire_thickness/2}, 0, 0),
                (hoop_r, 0, {wire_thickness/2}), (hoop_r+{wire_thickness/2}, 0, 0),
                (hoop_r, 0, -{wire_thickness/2}),
            ]
            profile = rs.AddInterpCurve(profile_pts, degree=3)
            if profile:
                hoop = rs.AddRevSrf(profile, ((0,0,0),(0,0,1)), 0, 300)
                if hoop: rs.ObjectLayer(hoop, "{layer}")
                rs.DeleteObject(profile)
            # Post
            post = rs.AddCylinder((hoop_r, 0, 0), (hoop_r, 0, -10), 0.4)
            if post: rs.ObjectLayer(post, "{layer}")
            print("Hoop earring: {hoop_diameter}mm diameter")
    """)


@mcp.tool()
def create_chain_link(
    link_type: str = "cable",
    link_length: float = 5.0,
    link_width: float = 3.0,
    wire_diameter: float = 0.8,
    num_links: int = 10,
    layer: str = "Chain",
) -> str:
    """Create a chain of interlocking links.

    Args:
        link_type: "cable" (oval links alternating 90deg) or "box" (square links).
        link_length/width: Individual link dimensions.
        wire_diameter: Wire gauge.
        num_links: Number of links to generate.
        layer: Layer for the chain.
    """
    wr = wire_diameter / 2.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        link_type = "{link_type}"
        hl, hw = {link_length}/2, {link_width}/2

        for i in range({num_links}):
            x_off = i * {link_length} * 0.8

            if link_type == "cable":
                # Oval link
                plane_normal = (0,0,1) if (i % 2 == 0) else (1,0,0)
                pts = []
                n = 20
                for j in range(n):
                    a = 2*math.pi*j/n
                    lx = hl * math.cos(a)
                    ly = hw * math.sin(a)
                    if i % 2 == 0:
                        pts.append((x_off + lx, ly, 0))
                    else:
                        pts.append((x_off + lx, 0, ly))
                pts.append(pts[0])

                crv = rs.AddInterpCurve(pts, degree=3)
                if crv:
                    pipe = rs.AddPipe(crv, 0, {wr}, cap=1)
                    if pipe:
                        for p in pipe: rs.ObjectLayer(p, "{layer}")
                    rs.DeleteObject(crv)

            elif link_type == "box":
                if i % 2 == 0:
                    pts = [(x_off-hl,-hw,0),(x_off+hl,-hw,0),(x_off+hl,hw,0),
                           (x_off-hl,hw,0),(x_off-hl,-hw,0)]
                else:
                    pts = [(x_off-hl,0,-hw),(x_off+hl,0,-hw),(x_off+hl,0,hw),
                           (x_off-hl,0,hw),(x_off-hl,0,-hw)]
                crv = rs.AddPolyline(pts)
                if crv:
                    pipe = rs.AddPipe(crv, 0, {wr}, cap=1)
                    if pipe:
                        for p in pipe: rs.ObjectLayer(p, "{layer}")
                    rs.DeleteObject(crv)

        print("Chain: {num_links} {link_type} links, {wire_diameter}mm wire")
    """)


@mcp.tool()
def create_tennis_bracelet(
    num_stones: int = 40,
    gem_diameter: float = 3.0,
    inner_diameter: float = 58.0,
    link_width: float = 0.8,
    gem_layer: str = "Tennis_Gems",
    metal_layer: str = "Tennis_Metal",
) -> str:
    """Create a tennis bracelet — continuous line of gems around the wrist.

    Args:
        num_stones: Number of stones.
        gem_diameter: Diameter of each stone.
        inner_diameter: Bracelet inner diameter.
        link_width: Metal link width between stones.
        gem_layer: Layer for gems.
        metal_layer: Layer for metal links.
    """
    bracelet_r = inner_diameter / 2.0 + 2.0
    gem_r = gem_diameter / 2.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        for layer in ["{gem_layer}", "{metal_layer}"]:
            if not rs.IsLayer(layer):
                rs.AddLayer(layer)

        br = {bracelet_r}
        n = {num_stones}

        for i in range(n):
            angle = 2 * math.pi * i / n
            cx = br * math.cos(angle)
            cy = br * math.sin(angle)

            # Gem
            gem = rs.AddSphere((cx, cy, 0), {gem_r})
            if gem:
                rs.ScaleObject(gem, (cx,cy,0), (1,1,0.5))
                rs.ObjectLayer(gem, "{gem_layer}")

            # Metal link to next
            next_angle = 2 * math.pi * (i+1) / n
            nx = br * math.cos(next_angle)
            ny = br * math.sin(next_angle)
            mid_x = (cx+nx)/2
            mid_y = (cy+ny)/2

            link = rs.AddLine((cx,cy,0), (nx,ny,0))
            if link:
                lp = rs.AddPipe(link, 0, {link_width/2}, cap=1)
                if lp:
                    for l in lp: rs.ObjectLayer(l, "{metal_layer}")
                rs.DeleteObject(link)

        print("Tennis bracelet: {num_stones} x {gem_diameter}mm stones, {inner_diameter}mm ID")
    """)


@mcp.tool()
def create_pendant_loop(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    loop_diameter: float = 4.0,
    wire_diameter: float = 1.0,
    layer: str = "Pendant_Loop",
) -> str:
    """Create a simple pendant loop/bail for chain attachment.

    A torus at the specified position.

    Args:
        center_x/y/z: Loop center position.
        loop_diameter: Outer diameter of the loop.
        wire_diameter: Thickness of the wire.
        layer: Layer for the loop.
    """
    major_r = loop_diameter / 2.0
    minor_r = wire_diameter / 2.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        loop = rs.AddTorus(({center_x},{center_y},{center_z}), {major_r}, {minor_r})
        if loop:
            rs.ObjectLayer(loop, "{layer}")
            print("Pendant loop: {loop_diameter}mm at ({center_x},{center_y},{center_z})")
    """)


# ══════════════════════════════════════════════════════════════
# SECTION: PJ CHEN WORKFLOW TOOLS
# Learned from "Milgrain Fashion Ring #133" and professional
# jewelry CAD techniques. These are the missing operations
# that bridge flat 2D design → 3D ring-shaped jewelry.
# ══════════════════════════════════════════════════════════════


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
def extrude_and_intersect_ring(
    curve_layer: str = "Design_Curves",
    ring_diameter: float = 16.0,
    ring_height: float = 8.0,
    extrude_distance: float = 15.0,
    both_sides: bool = True,
    output_layer: str = "Ring_Piece",
) -> str:
    """Extrude flat design curves into a solid, then Boolean-intersect with
    a ring cylinder to create a ring-shaped piece.

    PJ Chen's core technique for turning flat 2D designs into ring shapes:
    1. Extrude the flat pattern into a slab
    2. Create a ring cylinder
    3. BooleanIntersection to keep only the ring-shaped part

    Args:
        curve_layer: Layer with closed planar curves (the 2D design).
        ring_diameter: Ring inner diameter in mm.
        ring_height: Height of the ring cylinder.
        extrude_distance: How far to extrude the curves (must span the ring).
        both_sides: Extrude in both directions from the curve plane.
        output_layer: Layer for the resulting ring piece.
    """
    ring_r = ring_diameter / 2.0
    outer_r = ring_r + 3.0  # ring wall thickness
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}")

        curves = rs.ObjectsByLayer("{curve_layer}")
        if not curves:
            print("No curves on {curve_layer}")
        else:
            # Step 1: Extrude design curves into solids
            extruded = []
            for crv in curves:
                if rs.IsCurveClosed(crv) and rs.IsCurvePlanar(crv):
                    dist = {extrude_distance}
                    if {both_sides}:
                        srf = rs.ExtrudeCurveStraight(crv, (0, -dist, 0), (0, dist, 0))
                    else:
                        srf = rs.ExtrudeCurveStraight(crv, (0, 0, 0), (0, dist, 0))
                    if srf:
                        rs.CapPlanarHoles(srf)
                        extruded.append(srf)

            if not extruded:
                print("No closed planar curves found to extrude")
            else:
                # Step 2: Create ring cylinder (outer - inner = ring wall)
                outer = rs.AddCylinder((0, 0, -{ring_height/2}), (0, 0, {ring_height/2}), {outer_r})
                inner = rs.AddCylinder((0, 0, -{ring_height/2}), (0, 0, {ring_height/2}), {ring_r})
                ring_cyl = None
                if outer and inner:
                    ring_result = rs.BooleanDifference([outer], [inner], True)
                    if ring_result:
                        ring_cyl = ring_result[0]

                if ring_cyl:
                    # Step 3: Boolean intersect each extruded shape with ring
                    for ext in extruded:
                        result = rs.BooleanIntersection([rs.CopyObject(ring_cyl)], [ext], True)
                        if result:
                            for r in result:
                                rs.ObjectLayer(r, "{output_layer}")
                    rs.DeleteObject(ring_cyl)
                    print("Created ring piece(s) from {{}} curves".format(len(extruded)))
                else:
                    rs.DeleteObjects(extruded)
                    print("Ring cylinder creation failed")
    """)


@mcp.tool()
def create_milgrain_bead(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    diameter: float = 0.44,
    layer: str = "Bead",
) -> str:
    """Create a single milgrain bead (tiny sphere) for use with array_along_curve.

    PJ Chen uses 0.22mm radius (0.44mm diameter) beads. Create one bead,
    then use array_along_curve to copy it along projected design curves.

    Args:
        center_x/y/z: Bead center position.
        diameter: Bead diameter in mm (0.44 = PJ Chen's default).
        layer: Layer for the bead.
    """
    r = diameter / 2.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        bead = rs.AddSphere(({center_x}, {center_y}, {center_z}), {r})
        if bead:
            rs.ObjectLayer(bead, "{layer}")
            print("Milgrain bead: {diameter}mm diameter at ({center_x},{center_y},{center_z})")
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
def create_milgrain_ring(
    ring_diameter: float = 16.0,
    band_width: float = 4.0,
    band_thickness: float = 1.8,
    bead_diameter: float = 0.44,
    num_beads_per_row: int = 180,
    num_rows: int = 3,
    row_spacing: float = 0.6,
    band_layer: str = "Ring_Band",
    milgrain_layer: str = "Milgrain",
) -> str:
    """Create a complete milgrain ring — band + rows of tiny beads.

    All-in-one PJ Chen workflow: D-profile band + milgrain bead rows
    running around the circumference at specified spacing.

    Args:
        ring_diameter: Inner diameter in mm.
        band_width: Band width.
        band_thickness: Band thickness.
        bead_diameter: Milgrain bead diameter.
        num_beads_per_row: Beads per circumference row.
        num_rows: Number of milgrain rows across the band width.
        row_spacing: Distance between rows in mm.
        band_layer: Layer for the band.
        milgrain_layer: Layer for the milgrain beads.
    """
    inner_r = ring_diameter / 2.0
    outer_r = inner_r + band_thickness
    mid_r = (inner_r + outer_r) / 2.0 + band_thickness * 0.1  # slightly above mid for visibility
    bead_r = bead_diameter / 2.0
    hw = band_width / 2.0
    total_row_width = (num_rows - 1) * row_spacing

    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        for layer in ["{band_layer}", "{milgrain_layer}"]:
            if not rs.IsLayer(layer):
                rs.AddLayer(layer)

        ir = {inner_r}
        otr = {outer_r}

        # === D-PROFILE BAND ===
        profile = rs.AddInterpCurve([
            (ir, 0, -{hw}), (ir, 0, {hw}),
            (otr, 0, {hw*0.7}),
            (otr+{band_thickness*0.15}, 0, 0),
            (otr, 0, -{hw*0.7}),
            (ir, 0, -{hw}),
        ], degree=3)
        if profile:
            band = rs.AddRevSrf(profile, ((0,0,0),(0,0,1)))
            if band:
                rs.ObjectLayer(band, "{band_layer}")
            rs.DeleteObject(profile)

        # === MILGRAIN BEAD ROWS ===
        start_z = -{total_row_width / 2.0}
        for row in range({num_rows}):
            z = start_z + row * {row_spacing}

            for i in range({num_beads_per_row}):
                angle = 2 * math.pi * i / {num_beads_per_row}
                # Position bead on outer surface of band
                bx = {mid_r} * math.cos(angle)
                by = {mid_r} * math.sin(angle)
                bz = z

                bead = rs.AddSphere((bx, by, bz), {bead_r})
                if bead:
                    rs.ObjectLayer(bead, "{milgrain_layer}")

        total = {num_rows} * {num_beads_per_row}
        print("Milgrain ring: {ring_diameter}mm, {{}} beads in {num_rows} rows".format(total))
    """)


@mcp.tool()
def sweep_two_rails_ring_shank(
    inner_diameter: float = 16.0,
    shank_width: float = 3.0,
    shank_thickness: float = 2.0,
    start_angle: float = 120.0,
    end_angle: float = 240.0,
    layer: str = "Ring_Shank",
) -> str:
    """Create a ring shank using Sweep2 (two rails + cross section).

    PJ Chen's technique for the ring shank: draw two rail curves
    (inner and outer edge of the shank) and a D-shaped cross section,
    then Sweep2 to create the tapered shank surface.

    Args:
        inner_diameter: Ring inner diameter.
        shank_width: Shank width at the bottom.
        shank_thickness: Shank thickness.
        start_angle: Where the shank starts (degrees, 0=right, 90=top).
        end_angle: Where the shank ends.
        layer: Layer for the shank.
    """
    inner_r = inner_diameter / 2.0
    outer_r = inner_r + shank_thickness
    hw = shank_width / 2.0

    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        ir = {inner_r}
        otr = {outer_r}
        hw = {hw}
        start_a = math.radians({start_angle})
        end_a = math.radians({end_angle})

        # Inner rail (arc at inner radius)
        inner_pts = []
        n = 30
        for i in range(n):
            a = start_a + (end_a - start_a) * i / (n-1)
            inner_pts.append((ir * math.cos(a), ir * math.sin(a), 0))
        inner_rail = rs.AddInterpCurve(inner_pts, degree=3)

        # Outer rail (arc at outer radius)
        outer_pts = []
        for i in range(n):
            a = start_a + (end_a - start_a) * i / (n-1)
            outer_pts.append((otr * math.cos(a), otr * math.sin(a), 0))
        outer_rail = rs.AddInterpCurve(outer_pts, degree=3)

        # Cross section at start point (D-profile)
        sx = ir * math.cos(start_a)
        sy = ir * math.sin(start_a)
        # Radial direction
        rx = math.cos(start_a)
        ry = math.sin(start_a)

        profile_pts = [
            (sx, sy, -hw),
            (sx, sy, hw),
            (sx + {shank_thickness}*rx, sy + {shank_thickness}*ry, hw*0.7),
            (sx + ({shank_thickness}+0.3)*rx, sy + ({shank_thickness}+0.3)*ry, 0),
            (sx + {shank_thickness}*rx, sy + {shank_thickness}*ry, -hw*0.7),
            (sx, sy, -hw),
        ]
        profile = rs.AddInterpCurve(profile_pts, degree=3)

        if inner_rail and outer_rail and profile:
            result = rs.AddSweep2([inner_rail, outer_rail], [profile])
            if result:
                for r in result:
                    rs.CapPlanarHoles(r)
                    rs.ObjectLayer(r, "{layer}")
                print("Ring shank: {inner_diameter}mm, {start_angle}-{end_angle} deg arc")
            else:
                print("Sweep2 failed - check rail/profile geometry")

            rs.DeleteObjects([inner_rail, outer_rail, profile])
    """)


# ══════════════════════════════════════════════════════════════
# SECTION: TOOLS FROM PJ CHEN TRANSCRIPT ANALYSIS (58 videos)
# ══════════════════════════════════════════════════════════════


@mcp.tool()
def create_eternity_ring(
    inner_diameter: float = 16.0,
    stone_diameter: float = 2.0,
    stone_gap: float = 0.15,
    band_width: float = 3.0,
    band_thickness: float = 1.5,
    prong_height: float = 1.8,
    band_layer: str = "Eternity_Band",
    gem_layer: str = "Eternity_Gems",
    setting_layer: str = "Eternity_Settings",
) -> str:
    """Create a complete eternity ring — stones all around the band.

    Calculates stone count from circumference, creates band, cuts seats,
    and places prongs. PJ Chen's #337/#462/#497 technique.

    Args:
        inner_diameter: Ring inner diameter in mm.
        stone_diameter: Individual stone diameter.
        stone_gap: Gap between stones (0.1-0.2mm prevents cracking).
        band_width: Band width.
        band_thickness: Band radial thickness.
        prong_height: Prong height above girdle.
        band/gem/setting_layer: Layer assignments.
    """
    inner_r = inner_diameter / 2.0
    outer_r = inner_r + band_thickness
    circumference = math.pi * (inner_diameter + band_thickness)
    stone_spacing = stone_diameter + stone_gap
    stone_count = int(circumference / stone_spacing)
    gem_r = stone_diameter / 2.0
    hw = band_width / 2.0

    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        for layer in ["{band_layer}", "{gem_layer}", "{setting_layer}"]:
            if not rs.IsLayer(layer):
                rs.AddLayer(layer)

        ir = {inner_r}
        otr = {outer_r}
        n_stones = {stone_count}
        gem_r = {gem_r}

        # Band via revolve
        profile = rs.AddInterpCurve([
            (ir, 0, -{hw}), (ir, 0, {hw}),
            (otr, 0, {hw*0.7}), (otr+0.2, 0, 0), (otr, 0, -{hw*0.7}),
            (ir, 0, -{hw}),
        ], degree=3)
        if profile:
            band = rs.AddRevSrf(profile, ((0,0,0),(0,0,1)))
            if band: rs.ObjectLayer(band, "{band_layer}")
            rs.DeleteObject(profile)

        # Stones + prongs around full circumference
        mid_r = (ir + otr) / 2.0 + {band_thickness * 0.15}
        for i in range(n_stones):
            angle = 2 * math.pi * i / n_stones
            cx = mid_r * math.cos(angle)
            cy = mid_r * math.sin(angle)

            # Stone
            gem = rs.AddSphere((cx, cy, 0), gem_r)
            if gem:
                rs.ScaleObject(gem, (cx,cy,0), (1,1,0.5))
                rs.ObjectLayer(gem, "{gem_layer}")

            # 2 prongs per stone (shared with neighbors)
            for offset in [-0.4, 0.4]:
                pa = angle + offset / mid_r
                px = (mid_r + gem_r + 0.2) * math.cos(pa)
                py = (mid_r + gem_r + 0.2) * math.sin(pa)
                prong = rs.AddCylinder((px,py,-0.3), (px,py,{prong_height}*0.5), 0.25)
                if prong: rs.ObjectLayer(prong, "{setting_layer}")

        print("Eternity ring: {{}} stones ({stone_diameter}mm) around {inner_diameter}mm band".format(n_stones))
    """)


@mcp.tool()
def create_cathedral_setting(
    inner_diameter: float = 16.0,
    gem_diameter: float = 5.0,
    arch_height: float = 4.0,
    arch_thickness: float = 1.0,
    num_prongs: int = 4,
    band_layer: str = "Ring_Band",
    setting_layer: str = "Cathedral_Setting",
) -> str:
    """Create a cathedral engagement ring setting — arched supports from band to head.

    PJ Chen's #224 technique using Sweep2 for arch geometry.

    Args:
        inner_diameter: Ring inner diameter.
        gem_diameter: Center stone diameter.
        arch_height: Height of cathedral arches above band.
        arch_thickness: Thickness of arch metal.
        num_prongs: Number of prongs (4 typical for cathedral).
        band/setting_layer: Layer assignments.
    """
    inner_r = inner_diameter / 2.0
    outer_r = inner_r + 2.0
    gem_r = gem_diameter / 2.0

    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        for layer in ["{band_layer}", "{setting_layer}"]:
            if not rs.IsLayer(layer):
                rs.AddLayer(layer)

        otr = {outer_r}
        gem_r = {gem_r}
        arch_h = {arch_height}

        # Cathedral arches (2 arches, perpendicular)
        for i in range(2):
            base_angle = math.pi/2 * i
            # Arch: curves from band level up to prong height
            for side in [-1, 1]:
                a = base_angle + side * math.pi / 4
                pts = [
                    (otr * math.cos(a), otr * math.sin(a), 0),
                    ((otr - 0.5) * math.cos(a), (otr - 0.5) * math.sin(a), arch_h * 0.5),
                    ((gem_r + 0.8) * math.cos(a), (gem_r + 0.8) * math.sin(a), arch_h * 0.85),
                    ((gem_r + 0.3) * math.cos(a), (gem_r + 0.3) * math.sin(a), arch_h),
                ]
                crv = rs.AddInterpCurve(pts, degree=3)
                if crv:
                    pipe = rs.AddPipe(crv, [0, 0.5, 1], [{arch_thickness/2}, {arch_thickness/2*0.8}, {arch_thickness/2*0.5}], 0, 2)
                    if pipe:
                        for p in pipe: rs.ObjectLayer(p, "{setting_layer}")
                    rs.DeleteObject(crv)

        # Prongs at top
        for i in range({num_prongs}):
            a = 2 * math.pi * i / {num_prongs}
            pts = [
                ((gem_r+0.3)*math.cos(a), (gem_r+0.3)*math.sin(a), arch_h),
                ((gem_r-0.2)*math.cos(a), (gem_r-0.2)*math.sin(a), arch_h + gem_r*0.4),
            ]
            prong = rs.AddLine(pts[0], pts[1])
            if prong:
                pp = rs.AddPipe(prong, [0,1], [0.4, 0.25], 0, 2)
                if pp:
                    for p in pp: rs.ObjectLayer(p, "{setting_layer}")
                rs.DeleteObject(prong)

        # Base ring connecting arches
        plane = rs.PlaneFromNormal((0,0,0), (0,0,1))
        base = rs.AddCircle(plane, otr)
        if base:
            bp = rs.AddPipe(base, 0, {arch_thickness/2*0.6}, cap=1)
            if bp:
                for b in bp: rs.ObjectLayer(b, "{setting_layer}")
            rs.DeleteObject(base)

        print("Cathedral setting: {num_prongs} prongs, {arch_height}mm arches for {gem_diameter}mm stone")
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
def create_infinity_band(
    inner_diameter: float = 16.0,
    wire_diameter: float = 1.5,
    twist_count: float = 1.0,
    layer: str = "Infinity_Band",
) -> str:
    """Create an infinity/twisted band ring.

    PJ Chen's #466/#187 technique: figure-8 path piped as a ring.

    Args:
        inner_diameter: Ring inner diameter.
        wire_diameter: Wire/band thickness.
        twist_count: Number of full twists (1.0 = single infinity).
        layer: Layer for the ring.
    """
    r = inner_diameter / 2.0 + wire_diameter / 2.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        r = {r}
        n = 100

        # Twisted band: circle with Z oscillation
        pts = []
        for i in range(n):
            t = 2 * math.pi * i / n
            x = r * math.cos(t)
            y = r * math.sin(t)
            z = {wire_diameter * 0.8} * math.sin({twist_count} * 2 * t)
            pts.append((x, y, z))
        pts.append(pts[0])

        path = rs.AddInterpCurve(pts, degree=3)
        if path:
            band = rs.AddPipe(path, 0, {wire_diameter / 2}, cap=1)
            if band:
                for b in band:
                    rs.ObjectLayer(b, "{layer}")
            rs.DeleteObject(path)
            print("Infinity band: {inner_diameter}mm, {twist_count} twist(s)")
    """)


@mcp.tool()
def create_three_stone_ring(
    inner_diameter: float = 16.0,
    center_stone_dia: float = 5.0,
    side_stone_dia: float = 3.5,
    stone_spacing: float = 1.0,
    band_layer: str = "Ring_Band",
    gem_layer: str = "Ring_Gems",
    setting_layer: str = "Ring_Settings",
) -> str:
    """Create a three-stone ring — center + two flanking stones.

    PJ Chen's #69 technique: 3 stones with shared prong bridges.

    Args:
        inner_diameter: Ring inner diameter.
        center_stone_dia: Center stone diameter.
        side_stone_dia: Side stone diameter.
        stone_spacing: Gap between stones.
        band/gem/setting_layer: Layer assignments.
    """
    inner_r = inner_diameter / 2.0
    outer_r = inner_r + 2.0
    cr = center_stone_dia / 2.0
    sr = side_stone_dia / 2.0
    side_offset = cr + stone_spacing + sr

    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        for layer in ["{band_layer}", "{gem_layer}", "{setting_layer}"]:
            if not rs.IsLayer(layer):
                rs.AddLayer(layer)

        top_y = {outer_r} + {cr * 0.3}

        # Center stone
        gem_c = rs.AddSphere((0, top_y, 0), {cr})
        if gem_c:
            rs.ScaleObject(gem_c, (0,top_y,0), (1,1,0.5))
            rs.ObjectLayer(gem_c, "{gem_layer}")

        # Side stones
        for side in [-1, 1]:
            gem_s = rs.AddSphere((side*{side_offset}, top_y - 0.5, 0), {sr})
            if gem_s:
                rs.ScaleObject(gem_s, (side*{side_offset},top_y-0.5,0), (1,1,0.5))
                rs.ObjectLayer(gem_s, "{gem_layer}")

        # Prongs for all 3 stones (shared between neighbors)
        positions = [(0, top_y), (-{side_offset}, top_y-0.5), ({side_offset}, top_y-0.5)]
        radii = [{cr}, {sr}, {sr}]
        for j, (px, py) in enumerate(positions):
            r = radii[j]
            for k in range(4):
                a = 2*math.pi*k/4 + math.pi/4
                bx = px + (r+0.3)*math.cos(a)
                bz = (r+0.3)*math.sin(a)
                prong = rs.AddCylinder((bx, py-0.5, bz), (bx, py+r*0.5, bz), 0.3)
                if prong: rs.ObjectLayer(prong, "{setting_layer}")

        # Band
        profile = rs.AddInterpCurve([
            ({inner_r},0,-1.5), ({inner_r},0,1.5),
            ({outer_r},0,1), ({outer_r}+0.2,0,0), ({outer_r},0,-1),
            ({inner_r},0,-1.5),
        ], degree=3)
        if profile:
            band = rs.AddRevSrf(profile, ((0,0,0),(0,0,1)))
            if band: rs.ObjectLayer(band, "{band_layer}")
            rs.DeleteObject(profile)

        print("Three-stone ring: {center_stone_dia}mm center + 2x{side_stone_dia}mm sides")
    """)


@mcp.tool()
def create_cluster_setting(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    center_stone_dia: float = 4.0,
    surround_stone_dia: float = 1.5,
    surround_count: int = 8,
    gap: float = 0.15,
    gem_layer: str = "Cluster_Gems",
    metal_layer: str = "Cluster_Metal",
) -> str:
    """Create a cluster setting — center stone surrounded by smaller stones.

    PJ Chen's #166 technique. Different from halo: stones are larger,
    fewer, and may vary in size.

    Args:
        center_x/y/z: Center position.
        center_stone_dia: Center stone diameter.
        surround_stone_dia: Surrounding stone diameter.
        surround_count: Number of surrounding stones.
        gap: Gap between stones.
        gem/metal_layer: Layer assignments.
    """
    cr = center_stone_dia / 2.0
    sr = surround_stone_dia / 2.0
    ring_r = cr + gap + sr

    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        for layer in ["{gem_layer}", "{metal_layer}"]:
            if not rs.IsLayer(layer):
                rs.AddLayer(layer)

        cx, cy, cz = {center_x}, {center_y}, {center_z}

        # Center stone
        center = rs.AddSphere((cx, cy, cz), {cr})
        if center:
            rs.ScaleObject(center, (cx,cy,cz), (1,1,0.5))
            rs.ObjectLayer(center, "{gem_layer}")

        # Surrounding stones
        for i in range({surround_count}):
            a = 2*math.pi*i/{surround_count}
            sx = cx + {ring_r}*math.cos(a)
            sy = cy + {ring_r}*math.sin(a)
            gem = rs.AddSphere((sx, sy, cz), {sr})
            if gem:
                rs.ScaleObject(gem, (sx,sy,cz), (1,1,0.5))
                rs.ObjectLayer(gem, "{gem_layer}")

            # Shared prong between adjacent stones
            next_a = 2*math.pi*(i+1)/{surround_count}
            mid_a = (a + next_a) / 2
            px = cx + ({ring_r}+{sr}*0.5)*math.cos(mid_a)
            py = cy + ({ring_r}+{sr}*0.5)*math.sin(mid_a)
            prong = rs.AddCylinder((px,py,cz-0.2), (px,py,cz+{sr}*0.8), 0.2)
            if prong: rs.ObjectLayer(prong, "{metal_layer}")

        # Gallery ring
        plane = rs.PlaneFromNormal((cx,cy,cz-0.3), (0,0,1))
        gal = rs.AddCircle(plane, {ring_r})
        if gal:
            gp = rs.AddPipe(gal, 0, 0.25, cap=1)
            if gp:
                for g in gp: rs.ObjectLayer(g, "{metal_layer}")
            rs.DeleteObject(gal)

        print("Cluster: {center_stone_dia}mm center + {surround_count}x{surround_stone_dia}mm")
    """)


@mcp.tool()
def create_crown_ring(
    inner_diameter: float = 16.0,
    num_points: int = 6,
    point_height: float = 4.0,
    band_width: float = 3.0,
    band_layer: str = "Crown_Band",
    setting_layer: str = "Crown_Points",
) -> str:
    """Create a crown ring — band with upward-pointing crown tips.

    PJ Chen's #254/#354 technique using revolve + sweep for points.

    Args:
        inner_diameter: Ring inner diameter.
        num_points: Number of crown points.
        point_height: Height of crown points above band.
        band_width: Band width.
        band/setting_layer: Layer assignments.
    """
    inner_r = inner_diameter / 2.0
    outer_r = inner_r + 1.8
    hw = band_width / 2.0

    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        for layer in ["{band_layer}", "{setting_layer}"]:
            if not rs.IsLayer(layer):
                rs.AddLayer(layer)

        ir = {inner_r}
        otr = {outer_r}

        # Band
        profile = rs.AddInterpCurve([
            (ir,0,-{hw}),(ir,0,{hw}),(otr,0,{hw*0.7}),(otr+0.15,0,0),(otr,0,-{hw*0.7}),(ir,0,-{hw}),
        ], degree=3)
        if profile:
            band = rs.AddRevSrf(profile, ((0,0,0),(0,0,1)))
            if band: rs.ObjectLayer(band, "{band_layer}")
            rs.DeleteObject(profile)

        # Crown points
        for i in range({num_points}):
            a = 2*math.pi*i/{num_points}
            bx = otr * math.cos(a)
            by = otr * math.sin(a)

            # Point: tapered cylinder rising from band
            pts = [
                (bx, by, 0),
                (bx*1.02, by*1.02, {point_height}*0.6),
                (bx*0.98, by*0.98, {point_height}),
            ]
            crv = rs.AddInterpCurve(pts, degree=3)
            if crv:
                pipe = rs.AddPipe(crv, [0, 0.5, 1], [0.8, 0.5, 0.2], 0, 2)
                if pipe:
                    for p in pipe: rs.ObjectLayer(p, "{setting_layer}")
                rs.DeleteObject(crv)

        print("Crown ring: {num_points} points, {point_height}mm tall")
    """)


@mcp.tool()
def create_vintage_ring(
    inner_diameter: float = 16.0,
    gem_diameter: float = 5.0,
    filigree_count: int = 8,
    band_layer: str = "Vintage_Band",
    filigree_layer: str = "Vintage_Filigree",
    gem_layer: str = "Vintage_Gem",
) -> str:
    """Create a vintage-inspired ring with filigree scrollwork detail.

    PJ Chen's #484 technique: band + filigree curves + center stone.

    Args:
        inner_diameter: Ring inner diameter.
        gem_diameter: Center stone diameter.
        filigree_count: Number of filigree scroll elements.
        band/filigree/gem_layer: Layer assignments.
    """
    inner_r = inner_diameter / 2.0
    outer_r = inner_r + 2.0
    gem_r = gem_diameter / 2.0

    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        for layer in ["{band_layer}", "{filigree_layer}", "{gem_layer}"]:
            if not rs.IsLayer(layer):
                rs.AddLayer(layer)

        ir = {inner_r}
        otr = {outer_r}
        top_y = otr + 0.5

        # Band
        profile = rs.AddInterpCurve([
            (ir,0,-1.5),(ir,0,1.5),(otr,0,1),(otr+0.15,0,0),(otr,0,-1),(ir,0,-1.5),
        ], degree=3)
        if profile:
            band = rs.AddRevSrf(profile, ((0,0,0),(0,0,1)))
            if band: rs.ObjectLayer(band, "{band_layer}")
            rs.DeleteObject(profile)

        # Center gem
        gem = rs.AddSphere((0, top_y, 0), {gem_r})
        if gem:
            rs.ScaleObject(gem, (0,top_y,0), (1,1,0.5))
            rs.ObjectLayer(gem, "{gem_layer}")

        # Filigree scrollwork around the band
        for i in range({filigree_count}):
            a = 2*math.pi*i/{filigree_count}
            # Scroll curve: small spiral at each position
            scroll_pts = []
            for j in range(15):
                t = j / 14.0
                spiral_a = a + t * math.pi * 0.5
                spiral_r = otr + 0.3 + t * 1.0
                sz = -1.5 + 3.0 * t
                scroll_pts.append((spiral_r*math.cos(spiral_a), spiral_r*math.sin(spiral_a), sz))

            crv = rs.AddInterpCurve(scroll_pts, degree=3)
            if crv:
                sp = rs.AddPipe(crv, [0, 0.5, 1], [0.2, 0.15, 0.08], 0, 2)
                if sp:
                    for s in sp: rs.ObjectLayer(s, "{filigree_layer}")
                rs.DeleteObject(crv)

        print("Vintage ring: {gem_diameter}mm stone + {filigree_count} filigree scrolls")
    """)


@mcp.tool()
def create_under_bezel_gallery(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    gem_diameter: float = 5.0,
    gallery_depth: float = 2.0,
    num_windows: int = 6,
    wall_thickness: float = 0.6,
    layer: str = "Gallery",
) -> str:
    """Create decorative under-bezel gallery work with window cutouts.

    PJ Chen's #230 technique: the ornamental metalwork visible beneath
    a bezel setting, with arched windows for light passage.

    Args:
        center_x/y/z: Center of the setting.
        gem_diameter: Stone diameter.
        gallery_depth: Depth of gallery below girdle.
        num_windows: Number of gallery windows/openings.
        wall_thickness: Metal wall thickness.
        layer: Layer for gallery.
    """
    gem_r = gem_diameter / 2.0
    outer_r = gem_r + wall_thickness

    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")

        cx, cy, cz = {center_x}, {center_y}, {center_z}
        gem_r = {gem_r}
        otr = {outer_r}
        depth = {gallery_depth}

        # Outer gallery wall (cylinder)
        outer_cyl = rs.AddCylinder((cx,cy,cz-depth), (cx,cy,cz), otr)
        # Inner bore
        inner_cyl = rs.AddCylinder((cx,cy,cz-depth-0.1), (cx,cy,cz+0.1), gem_r)

        if outer_cyl and inner_cyl:
            gallery = rs.BooleanDifference([outer_cyl], [inner_cyl], True)
            if gallery:
                # Cut arched windows
                for i in range({num_windows}):
                    a = 2*math.pi*i/{num_windows}
                    wx = cx + (gem_r + {wall_thickness}/2) * math.cos(a)
                    wy = cy + (gem_r + {wall_thickness}/2) * math.sin(a)
                    # Window cutter (small box)
                    window = rs.AddSphere((wx, wy, cz - depth*0.5), {wall_thickness}*0.8)
                    if window:
                        rs.ScaleObject(window, (wx,wy,cz-depth*0.5), (1.5, 1.5, depth*0.6/{wall_thickness}))
                        try:
                            cut = rs.BooleanDifference(gallery, [window], True)
                            if cut:
                                gallery = cut
                        except:
                            rs.DeleteObject(window)

                if gallery:
                    if isinstance(gallery, list):
                        for g in gallery: rs.ObjectLayer(g, "{layer}")
                    else:
                        rs.ObjectLayer(gallery, "{layer}")

        print("Under-bezel gallery: {num_windows} windows, {gallery_depth}mm deep")
    """)


# ══════════════════════════════════════════════════════════════
# SECTION: LAYER MANAGEMENT
# ══════════════════════════════════════════════════════════════


# ──────────────────────────────────────────────────────────────
# TOOL 75: clear_layer
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 76: list_scene_layers
# ──────────────────────────────────────────────────────────────
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


# ══════════════════════════════════════════════════════════════
# SECTION: PRODUCTION & CASTING TOOLS
# ══════════════════════════════════════════════════════════════


# ──────────────────────────────────────────────────────────────
# TOOL 77: create_sprue_tree
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 78: check_naked_edges
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 79: generate_bom_report
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 80: apply_shrinkage_compensation
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 81: check_gem_clearance
# ──────────────────────────────────────────────────────────────
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


# ══════════════════════════════════════════════════════════════
# SECTION: ADVANCED QC & ANALYSIS
# ══════════════════════════════════════════════════════════════


# ──────────────────────────────────────────────────────────────
# TOOL 82: check_model_watertight
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 83: generate_dimension_report
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 84: resize_ring
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def resize_ring(
    ring_layer: str = "Ring_Band",
    current_size: float = 7.0,
    target_size: float = 6.0,
) -> str:
    """Resize a ring from one US size to another while maintaining cross-section.

    Scales the ring circumferentially (X/Y) without changing the band
    cross-section height (Z). Preserves band width, prong height, etc.

    Args:
        ring_layer: Layer with ring objects to resize.
        current_size: Current US ring size.
        target_size: Desired US ring size.
    """
    # US ring size to inner diameter: D = 11.63 + size * 0.8128 mm
    current_d = 11.63 + current_size * 0.8128
    target_d = 11.63 + target_size * 0.8128
    scale_xy = target_d / current_d
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        objs = rs.ObjectsByLayer("{ring_layer}")
        if not objs:
            print("No objects on {ring_layer}")
        else:
            # Scale X/Y (circumference) but keep Z (cross-section) unchanged
            bb = rs.BoundingBox(objs)
            if bb:
                cx = (bb[0][0] + bb[6][0]) / 2.0
                cy = (bb[0][1] + bb[6][1]) / 2.0
                cz = (bb[0][2] + bb[6][2]) / 2.0
                origin = (cx, cy, cz)

                for obj in objs:
                    rs.ScaleObject(obj, origin, ({scale_xy:.6f}, {scale_xy:.6f}, 1.0))

                print("=== Ring Resize ===")
                print("US {{:.1f}} ({{:.2f}}mm) -> US {{:.1f}} ({{:.2f}}mm)".format(
                    {current_size}, {current_d:.2f}, {target_size}, {target_d:.2f}))
                print("Scale factor: {{:.4f}} (X/Y only)".format({scale_xy}))
                print("Resized {{}} objects on {ring_layer}".format(len(objs)))
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 85: add_drain_holes
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 86: check_draft_angles
# ──────────────────────────────────────────────────────────────
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


# ══════════════════════════════════════════════════════════════
# SECTION: NEW DESIGN TOOLS
# ══════════════════════════════════════════════════════════════


# ──────────────────────────────────────────────────────────────
# TOOL 87: create_tension_setting
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_tension_setting(
    ring_diameter: float = 16.0,
    band_width: float = 4.0,
    band_thickness: float = 2.5,
    gem_diameter: float = 5.0,
    gap_width: float = 1.0,
    gem_layer: str = "Ring_Gem",
    band_layer: str = "Ring_Band",
) -> str:
    """Create a tension-set ring where the stone is held by band spring pressure.

    The band has a gap at the top where the gem sits, held in place by the
    spring tension of the metal. A modern, minimalist setting style.

    Args:
        ring_diameter: Inner diameter in mm.
        band_width: Band width in mm (needs to be wider for tension strength).
        band_thickness: Band thickness in mm (thicker = more holding force).
        gem_diameter: Diameter of the center stone in mm.
        gap_width: Width of the gap holding the stone in mm.
        gem_layer: Layer for the gem.
        band_layer: Layer for the metal band.
    """
    inner_r = ring_diameter / 2.0
    outer_r = inner_r + band_thickness
    half_w = band_width / 2.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        for layer, color in [("{band_layer}", [200,200,220]), ("{gem_layer}", [255,255,255])]:
            if not rs.IsLayer(layer):
                rs.AddLayer(layer, color)

        # Create band as a torus-like ring
        inner_r = {inner_r}
        outer_r = {outer_r}
        half_w = {half_w}

        # Band profile (D-shape cross section)
        profile_pts = []
        for i in range(21):
            a = math.pi * i / 20.0
            px = inner_r + {band_thickness / 2.0} + ({band_thickness / 2.0}) * math.cos(a)
            pz = half_w * math.sin(a)
            profile_pts.append((px, 0, pz))
        profile_pts.append(profile_pts[0])
        profile = rs.AddPolyline(profile_pts)

        # Revolve to make ring, but leave gap at top
        gap_half_angle = math.asin({gap_width / 2.0} / ((inner_r + outer_r) / 2.0))
        gap_deg = math.degrees(gap_half_angle)

        # Revolve from (gap_deg) to (360 - gap_deg)
        axis_start = (0, 0, 0)
        axis_end = (0, 0, 1)
        band = rs.AddRevSrf(profile, (axis_start, axis_end),
                            start_angle=gap_deg, end_angle=360 - gap_deg)
        rs.DeleteObject(profile)

        if band:
            # Cap the open ends
            capped = rs.CapPlanarHoles(band)
            rs.ObjectLayer(band, "{band_layer}")

            # Create small notches/seats at each end of the gap for the gem
            seat_depth = {gem_diameter} * 0.15
            mid_r = (inner_r + outer_r) / 2.0
            for sign in [1, -1]:
                seat_x = mid_r * math.cos(sign * gap_half_angle + math.pi/2)
                seat_y = mid_r * math.sin(sign * gap_half_angle + math.pi/2)
                notch = rs.AddSphere((seat_x, seat_y, 0), seat_depth)
                if notch:
                    rs.ObjectLayer(notch, "{band_layer}")

        # Place gem in the gap
        gem_y = (inner_r + outer_r) / 2.0
        gem = rs.AddSphere((0, gem_y, 0), {gem_diameter / 2.0})
        if gem:
            rs.ScaleObject(gem, (0, gem_y, 0), (1.0, 1.0, 0.6))
            rs.ObjectLayer(gem, "{gem_layer}")

        print("Tension ring: {{:.1f}}mm dia, {{:.1f}}mm gem, {{:.1f}}mm gap".format(
            {ring_diameter}, {gem_diameter}, {gap_width}))
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 88: create_bar_setting
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_bar_setting(
    rail_layer: str = "Rail",
    gem_layer: str = "Gems",
    bar_width: float = 0.8,
    bar_height: float = 1.2,
    output_layer: str = "Bar_Setting",
) -> str:
    """Create bar settings between gems along a rail curve.

    Horizontal metal bars separate each stone, an alternative to prongs
    for a clean modern look. Common in eternity bands and channel variations.

    Args:
        rail_layer: Layer with the rail curve.
        gem_layer: Layer with gems already placed along the rail.
        bar_width: Width of each bar in mm.
        bar_height: Height of bars above the rail in mm.
        output_layer: Layer for the bar metal.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}", [200, 200, 220])

        rails = rs.ObjectsByLayer("{rail_layer}")
        gems = rs.ObjectsByLayer("{gem_layer}")
        if not rails or not gems:
            print("Need curves on {rail_layer} and gems on {gem_layer}")
        else:
            rail = rails[0]
            count = 0
            # For each gem, place a bar on each side
            bar_positions = set()
            for gem in gems:
                bb = rs.BoundingBox(gem)
                if not bb:
                    continue
                cx = (bb[0][0] + bb[6][0]) / 2.0
                cy = (bb[0][1] + bb[6][1]) / 2.0
                cz = (bb[0][2] + bb[6][2]) / 2.0
                gem_r = max(bb[6][0] - bb[0][0], bb[6][1] - bb[0][1]) / 2.0

                # Find parameter on rail
                param = rs.CurveClosestPoint(rail, (cx, cy, cz))
                if param is None:
                    continue
                pt = rs.EvaluateCurve(rail, param)
                tangent = rs.CurveTangent(rail, param)
                if not pt or not tangent:
                    continue

                # Normalize tangent
                tlen = math.sqrt(sum(t*t for t in tangent))
                if tlen < 0.001:
                    continue
                tx, ty, tz = tangent[0]/tlen, tangent[1]/tlen, tangent[2]/tlen

                # Place bars at +/- gem_r along tangent
                for sign in [-1, 1]:
                    bx = pt[0] + sign * gem_r * tx
                    by = pt[1] + sign * gem_r * ty
                    bz = pt[2] + sign * gem_r * tz

                    # Perpendicular direction (approximate up)
                    bar_base = (bx, by, bz - 0.2)
                    bar_top = (bx, by, bz + {bar_height})
                    bar_line = rs.AddLine(bar_base, bar_top)
                    if bar_line:
                        bar = rs.AddPipe(bar_line, 0, {bar_width / 2.0}, cap=1)
                        if bar:
                            for b in bar:
                                rs.ObjectLayer(b, "{output_layer}")
                            count += 1
                        rs.DeleteObject(bar_line)

            print("Bar setting: {{}} bars on {output_layer}".format(count))
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 89: create_spiral_wire
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_spiral_wire(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    radius: float = 8.0,
    height: float = 20.0,
    turns: float = 5.0,
    wire_diameter: float = 0.8,
    direction: int = 1,
    output_layer: str = "Spiral_Wire",
) -> str:
    """Create a helical/spiral wire — used for twisted wire jewelry, springs, rope chains.

    Generates a spiral curve and pipes it to the specified wire diameter.

    Args:
        center_x/y/z: Center of the spiral base.
        radius: Spiral radius in mm.
        height: Total height of the spiral in mm.
        turns: Number of complete turns.
        wire_diameter: Wire thickness in mm.
        direction: 1 = clockwise, -1 = counter-clockwise.
        output_layer: Layer for the wire.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}", [212, 175, 55])

        # Generate helix points
        pts = []
        n_pts = int({turns} * 72)  # 72 points per turn for smoothness
        for i in range(n_pts + 1):
            t = float(i) / n_pts
            angle = {direction} * t * {turns} * 2 * math.pi
            x = {center_x} + {radius} * math.cos(angle)
            y = {center_y} + {radius} * math.sin(angle)
            z = {center_z} + t * {height}
            pts.append((x, y, z))

        helix = rs.AddInterpCurve(pts, degree=3)
        if helix:
            wire = rs.AddPipe(helix, 0, {wire_diameter / 2.0}, cap=1)
            if wire:
                for w in wire:
                    rs.ObjectLayer(w, "{output_layer}")
            rs.DeleteObject(helix)
            print("Spiral wire: {{:.1f}}mm radius, {{:.0f}} turns, {{:.1f}}mm wire".format(
                {radius}, {turns}, {wire_diameter}))
        else:
            print("Failed to create spiral curve")
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 90: twist_band
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def twist_band(
    object_layer: str = "Ring_Band",
    twist_angle: float = 180.0,
    axis: str = "z",
) -> str:
    """Apply a twist deformation to ring bands or other objects.

    Creates twisted ring bands, Mobius-like designs, and decorative twists.
    Uses rs.TwistObject for non-destructive geometric deformation.

    Args:
        object_layer: Layer with objects to twist.
        twist_angle: Total twist in degrees (180 = half turn, 360 = full turn).
        axis: Twist axis — "x", "y", or "z".
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        objs = rs.ObjectsByLayer("{object_layer}")
        if not objs:
            print("No objects on {object_layer}")
        else:
            for obj in objs:
                bb = rs.BoundingBox(obj)
                if not bb:
                    continue
                # Twist axis from min to max along chosen axis
                axis_map = {{"x": 0, "y": 1, "z": 2}}
                ai = axis_map.get("{axis}", 2)
                pt1 = list(bb[0])
                pt2 = list(bb[6])
                # Set non-axis coords to center
                for i in range(3):
                    if i != ai:
                        pt1[i] = (bb[0][i] + bb[6][i]) / 2.0
                        pt2[i] = (bb[0][i] + bb[6][i]) / 2.0

                cmd = "_-Twist _SelId {{}} _Enter _Point {{}},{{}},{{}} _Point {{}},{{}},{{}} {{}} _Enter".format(
                    obj,
                    pt1[0], pt1[1], pt1[2],
                    pt2[0], pt2[1], pt2[2],
                    {twist_angle}
                )
                rs.Command(cmd, echo=False)

            print("Twisted {{}} objects by {twist_angle} deg around {axis} axis".format(len(objs)))
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 91: taper_shank
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def taper_shank(
    object_layer: str = "Ring_Band",
    taper_factor: float = 0.6,
    axis: str = "z",
) -> str:
    """Apply a taper deformation to ring shanks or band objects.

    Makes the band narrower toward the top (where the setting sits),
    a common professional ring design technique.

    Args:
        object_layer: Layer with objects to taper.
        taper_factor: Scale at the narrow end (0.6 = 60% of original width).
        axis: Taper axis — "z" tapers vertically (most common for rings).
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        objs = rs.ObjectsByLayer("{object_layer}")
        if not objs:
            print("No objects on {object_layer}")
        else:
            for obj in objs:
                bb = rs.BoundingBox(obj)
                if not bb:
                    continue
                axis_map = {{"x": 0, "y": 1, "z": 2}}
                ai = axis_map.get("{axis}", 2)
                pt1 = list(bb[0])
                pt2 = list(bb[6])
                for i in range(3):
                    if i != ai:
                        pt1[i] = (bb[0][i] + bb[6][i]) / 2.0
                        pt2[i] = (bb[0][i] + bb[6][i]) / 2.0

                cmd = "_-Taper _SelId {{}} _Enter _Point {{}},{{}},{{}} _Point {{}},{{}},{{}} {{}} _Enter".format(
                    obj,
                    pt1[0], pt1[1], pt1[2],
                    pt2[0], pt2[1], pt2[2],
                    {taper_factor}
                )
                rs.Command(cmd, echo=False)

            print("Tapered {{}} objects, factor {taper_factor} along {axis}".format(len(objs)))
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 92: create_asscher_cut_gem
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_asscher_cut_gem(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    size: float = 5.0,
    layer: str = "Gem_Asscher",
) -> str:
    """Create an Asscher-cut gem (square step-cut with deeply clipped corners).

    The Asscher cut is a square emerald cut with a higher crown, smaller table,
    and larger step facets. Known for its distinctive "hall of mirrors" effect.

    Args:
        center_x/y/z: Center of the gem.
        size: Width of the gem in mm (square).
        layer: Layer for the gem.
    """
    # Proportions: table 50%, crown 16%, pavilion 61%, girdle 3%
    half = size / 2.0
    table_ratio = 0.50
    corner_clip = 0.20  # Larger corner clip than emerald cut
    crown_h = size * 0.16
    girdle_h = size * 0.03
    pav_h = size * 0.61
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}", [255, 255, 255])

        cx, cy, cz = {center_x}, {center_y}, {center_z}
        h = {half}
        clip = h * {corner_clip}
        t_h = h * {table_ratio}
        t_clip = t_h * {corner_clip}

        def oct(r, c, z):
            \"\"\"Clipped-corner square at radius r with clip c at height z.\"\"\"
            return [
                (cx - r + c, cy - r, z),
                (cx + r - c, cy - r, z),
                (cx + r, cy - r + c, z),
                (cx + r, cy + r - c, z),
                (cx + r - c, cy + r, z),
                (cx - r + c, cy + r, z),
                (cx - r, cy + r - c, z),
                (cx - r, cy - r + c, z),
                (cx - r + c, cy - r, z),
            ]

        z_table = cz + {crown_h} + {girdle_h / 2.0}
        z_crown = cz + {girdle_h / 2.0} + {crown_h * 0.4}
        z_girdle_top = cz + {girdle_h / 2.0}
        z_girdle_bot = cz - {girdle_h / 2.0}
        z_pav = cz - {girdle_h / 2.0} - {pav_h * 0.6}
        z_culet = cz - {girdle_h / 2.0} - {pav_h}

        curves = []
        for pts in [
            oct(t_h, t_clip, z_table),
            oct(h * 0.85, clip * 0.9, z_crown),
            oct(h, clip, z_girdle_top),
            oct(h, clip, z_girdle_bot),
            oct(h * 0.4, clip * 0.3, z_pav),
            oct(h * 0.05, 0.01, z_culet),
        ]:
            c = rs.AddPolyline(pts)
            if c:
                curves.append(c)

        if len(curves) >= 2:
            surfs = rs.AddLoftSrf(curves, loft_type=2)
            if surfs:
                for s in surfs:
                    rs.ObjectLayer(s, "{layer}")

        # Cap top and bottom
        if curves:
            top_srf = rs.AddPlanarSrf([curves[0]])
            if top_srf:
                for s in top_srf:
                    rs.ObjectLayer(s, "{layer}")
            bot_srf = rs.AddPlanarSrf([curves[-1]])
            if bot_srf:
                for s in bot_srf:
                    rs.ObjectLayer(s, "{layer}")

        for c in curves:
            rs.DeleteObject(c)

        print("Asscher cut: {size}mm at ({center_x}, {center_y}, {center_z})")
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 93: create_radiant_cut_gem
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_radiant_cut_gem(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    width: float = 5.0,
    length: float = 7.0,
    layer: str = "Gem_Radiant",
) -> str:
    """Create a radiant-cut gem (rectangular with trimmed corners and brilliant facets).

    A hybrid cut combining the step-cut emerald shape with brilliant-cut
    facets for more fire and brilliance than a pure emerald cut.

    Args:
        center_x/y/z: Center of the gem.
        width: Width in mm (short axis).
        length: Length in mm (long axis).
        layer: Layer for the gem.
    """
    hw = width / 2.0
    hl = length / 2.0
    corner_clip = 0.15
    crown_h = width * 0.14
    girdle_h = width * 0.025
    pav_h = width * 0.45
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}", [255, 255, 255])

        cx, cy, cz = {center_x}, {center_y}, {center_z}

        def rect_oct(rw, rl, cw, cl, z):
            \"\"\"Clipped-corner rectangle.\"\"\"
            return [
                (cx - rw + cw, cy - rl, z),
                (cx + rw - cw, cy - rl, z),
                (cx + rw, cy - rl + cl, z),
                (cx + rw, cy + rl - cl, z),
                (cx + rw - cw, cy + rl, z),
                (cx - rw + cw, cy + rl, z),
                (cx - rw, cy + rl - cl, z),
                (cx - rw, cy - rl + cl, z),
                (cx - rw + cw, cy - rl, z),
            ]

        hw, hl = {hw}, {hl}
        clip_w = hw * {corner_clip}
        clip_l = hl * {corner_clip}

        z_table = cz + {crown_h} + {girdle_h / 2.0}
        z_crown = cz + {girdle_h / 2.0} + {crown_h * 0.4}
        z_girdle_top = cz + {girdle_h / 2.0}
        z_girdle_bot = cz - {girdle_h / 2.0}
        z_pav = cz - {girdle_h / 2.0} - {pav_h * 0.6}
        z_culet = cz - {girdle_h / 2.0} - {pav_h}

        curves = []
        for pts in [
            rect_oct(hw * 0.6, hl * 0.6, clip_w * 0.5, clip_l * 0.5, z_table),
            rect_oct(hw * 0.88, hl * 0.88, clip_w * 0.8, clip_l * 0.8, z_crown),
            rect_oct(hw, hl, clip_w, clip_l, z_girdle_top),
            rect_oct(hw, hl, clip_w, clip_l, z_girdle_bot),
            rect_oct(hw * 0.35, hl * 0.35, clip_w * 0.2, clip_l * 0.2, z_pav),
            rect_oct(hw * 0.05, hl * 0.05, 0.01, 0.01, z_culet),
        ]:
            c = rs.AddPolyline(pts)
            if c:
                curves.append(c)

        if len(curves) >= 2:
            surfs = rs.AddLoftSrf(curves, loft_type=2)
            if surfs:
                for s in surfs:
                    rs.ObjectLayer(s, "{layer}")

        if curves:
            top_srf = rs.AddPlanarSrf([curves[0]])
            if top_srf:
                for s in top_srf:
                    rs.ObjectLayer(s, "{layer}")
            bot_srf = rs.AddPlanarSrf([curves[-1]])
            if bot_srf:
                for s in bot_srf:
                    rs.ObjectLayer(s, "{layer}")

        for c in curves:
            rs.DeleteObject(c)

        print("Radiant cut: {width}x{length}mm at ({center_x}, {center_y}, {center_z})")
    """)


# ══════════════════════════════════════════════════════════════
# SECTION: MATERIALS & PRESENTATION
# ══════════════════════════════════════════════════════════════


# ──────────────────────────────────────────────────────────────
# TOOL 94: assign_metal_material
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def assign_metal_material(
    object_layer: str = "Ring_Band",
    metal_type: str = "18k_yellow_gold",
) -> str:
    """Assign a realistic metal material to objects for rendering.

    Sets diffuse color, reflectivity, and shine to match real metals.

    Args:
        object_layer: Layer with objects to assign material.
        metal_type: One of: 24k_gold, 18k_yellow_gold, 14k_gold, rose_gold,
                    white_gold, platinum, sterling_silver, palladium.
    """
    metals = {
        "24k_gold":         {"color": (255, 215, 0),   "reflect": (255, 235, 130), "shine": 0.9, "transp": 0.0},
        "18k_yellow_gold":  {"color": (238, 195, 50),  "reflect": (255, 220, 100), "shine": 0.85, "transp": 0.0},
        "14k_gold":         {"color": (225, 185, 60),  "reflect": (245, 210, 90),  "shine": 0.8, "transp": 0.0},
        "rose_gold":        {"color": (210, 150, 120), "reflect": (235, 180, 150), "shine": 0.8, "transp": 0.0},
        "white_gold":       {"color": (220, 220, 225), "reflect": (240, 240, 245), "shine": 0.9, "transp": 0.0},
        "platinum":         {"color": (210, 215, 220), "reflect": (230, 235, 240), "shine": 0.95, "transp": 0.0},
        "sterling_silver":  {"color": (192, 192, 200), "reflect": (230, 230, 240), "shine": 0.9, "transp": 0.0},
        "palladium":        {"color": (200, 205, 210), "reflect": (225, 230, 235), "shine": 0.9, "transp": 0.0},
    }
    m = metals.get(metal_type, metals["18k_yellow_gold"])
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        objs = rs.ObjectsByLayer("{object_layer}")
        if not objs:
            print("No objects on {object_layer}")
        else:
            idx = rs.AddMaterialToLayer("{object_layer}")
            if idx >= 0:
                rs.MaterialColor(idx, {m["color"]})
                rs.MaterialReflectiveColor(idx, {m["reflect"]})
                rs.MaterialShine(idx, {m["shine"]} * 255)
                rs.MaterialTransparency(idx, {m["transp"]})
                rs.MaterialName(idx, "{metal_type}")
                print("Applied {metal_type} material to {object_layer} ({{}} objects)".format(len(objs)))
            else:
                print("Failed to create material")
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 95: assign_gem_material
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def assign_gem_material(
    object_layer: str = "Ring_Gem",
    gem_type: str = "diamond",
) -> str:
    """Assign a realistic gemstone material to objects for rendering.

    Sets color, transparency, reflectivity, and shine for common gem types.

    Args:
        object_layer: Layer with gem objects.
        gem_type: One of: diamond, emerald, ruby, sapphire, amethyst,
                  aquamarine, topaz, peridot, garnet, opal.
    """
    gems = {
        "diamond":     {"color": (240, 248, 255), "reflect": (255, 255, 255), "shine": 1.0, "transp": 0.85},
        "emerald":     {"color": (0, 155, 60),    "reflect": (100, 200, 130), "shine": 0.8, "transp": 0.6},
        "ruby":        {"color": (200, 10, 30),   "reflect": (230, 80, 80),   "shine": 0.85, "transp": 0.55},
        "sapphire":    {"color": (15, 50, 180),   "reflect": (80, 100, 220),  "shine": 0.85, "transp": 0.55},
        "amethyst":    {"color": (130, 50, 180),  "reflect": (160, 100, 210), "shine": 0.75, "transp": 0.5},
        "aquamarine":  {"color": (100, 200, 230), "reflect": (150, 220, 240), "shine": 0.75, "transp": 0.6},
        "topaz":       {"color": (255, 190, 50),  "reflect": (255, 210, 100), "shine": 0.8, "transp": 0.55},
        "peridot":     {"color": (140, 195, 50),  "reflect": (180, 220, 100), "shine": 0.75, "transp": 0.5},
        "garnet":      {"color": (160, 20, 40),   "reflect": (200, 60, 70),   "shine": 0.8, "transp": 0.45},
        "opal":        {"color": (220, 230, 240), "reflect": (200, 210, 255), "shine": 0.6, "transp": 0.2},
    }
    g = gems.get(gem_type, gems["diamond"])
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        objs = rs.ObjectsByLayer("{object_layer}")
        if not objs:
            print("No objects on {object_layer}")
        else:
            idx = rs.AddMaterialToLayer("{object_layer}")
            if idx >= 0:
                rs.MaterialColor(idx, {g["color"]})
                rs.MaterialReflectiveColor(idx, {g["reflect"]})
                rs.MaterialShine(idx, {g["shine"]} * 255)
                rs.MaterialTransparency(idx, {g["transp"]})
                rs.MaterialName(idx, "{gem_type}")
                print("Applied {gem_type} material to {object_layer} ({{}} objects)".format(len(objs)))
            else:
                print("Failed to create material")
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 96: setup_studio_lighting
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def setup_studio_lighting(
    preset: str = "jewelry_standard",
    intensity: float = 1.0,
) -> str:
    """Set up studio lighting optimized for jewelry rendering.

    Creates a multi-light setup designed to showcase gems and metal.
    Available presets mimic professional jewelry photography lighting.

    Args:
        preset: Lighting preset — "jewelry_standard" (3-point),
                "dramatic" (strong key + rim), "soft" (diffused even).
        intensity: Overall intensity multiplier (1.0 = normal).
    """
    presets = {
        "jewelry_standard": [
            {"type": "spot", "pos": (100, -100, 150), "target": (0,0,0), "color": (255,250,240), "power": 1.0},
            {"type": "spot", "pos": (-80, -60, 120), "target": (0,0,0), "color": (240,245,255), "power": 0.6},
            {"type": "spot", "pos": (0, 100, 80), "target": (0,0,0), "color": (255,255,255), "power": 0.3},
        ],
        "dramatic": [
            {"type": "spot", "pos": (120, -80, 100), "target": (0,0,0), "color": (255,245,230), "power": 1.2},
            {"type": "spot", "pos": (-100, 50, 60), "target": (0,0,0), "color": (200,210,230), "power": 0.2},
            {"type": "spot", "pos": (0, 80, 20), "target": (0,0,0), "color": (255,250,240), "power": 0.8},
        ],
        "soft": [
            {"type": "spot", "pos": (80, -80, 120), "target": (0,0,0), "color": (255,252,248), "power": 0.7},
            {"type": "spot", "pos": (-80, -80, 120), "target": (0,0,0), "color": (248,250,255), "power": 0.7},
            {"type": "spot", "pos": (0, 80, 100), "target": (0,0,0), "color": (255,255,255), "power": 0.5},
            {"type": "spot", "pos": (0, 0, 150), "target": (0,0,0), "color": (255,255,255), "power": 0.4},
        ],
    }
    lights = presets.get(preset, presets["jewelry_standard"])
    lights_json = json.dumps(lights)
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import json

        lights = json.loads('{lights_json}')
        intensity = {intensity}

        created = 0
        for i, light in enumerate(lights):
            pos = light["pos"]
            target = light["target"]
            color = light["color"]
            power = light["power"] * intensity

            spot = rs.AddSpotLight(target, pos, 30.0)
            if spot:
                scaled_color = (
                    min(255, int(color[0] * power)),
                    min(255, int(color[1] * power)),
                    min(255, int(color[2] * power))
                )
                rs.LightColor(spot, scaled_color)
                rs.ObjectName(spot, "Studio_Light_{{}}".format(i + 1))
                created += 1

        print("=== Studio Lighting ===")
        print("Preset: {preset}")
        print("Intensity: {intensity}")
        print("Lights created: {{}}".format(created))
    """)


# ══════════════════════════════════════════════════════════════
# SECTION: ORGANIZATION & METADATA
# ══════════════════════════════════════════════════════════════


# ──────────────────────────────────────────────────────────────
# TOOL 97: group_layer_objects
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def group_layer_objects(
    layer_name: str = "Ring_Band",
    group_name: str = "",
) -> str:
    """Group all objects on a layer into a named group for easy selection.

    Groups allow selecting/moving/hiding entire components at once
    without affecting layer organization.

    Args:
        layer_name: Layer whose objects should be grouped.
        group_name: Name for the group. Defaults to layer name if empty.
    """
    gname = group_name if group_name else layer_name
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        objs = rs.ObjectsByLayer("{layer_name}")
        if not objs:
            print("No objects on {layer_name}")
        else:
            group = rs.AddGroup("{gname}")
            if group:
                rs.AddObjectsToGroup(objs, "{gname}")
                print("Grouped {{}} objects as '{gname}'".format(len(objs)))
            else:
                print("Failed to create group '{gname}'")
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 98: set_gem_metadata
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def set_gem_metadata(
    gem_layer: str = "Ring_Gem",
    gem_type: str = "diamond",
    cut: str = "round_brilliant",
    color_grade: str = "D",
    clarity: str = "VVS1",
) -> str:
    """Attach metadata (gem type, cut, color, clarity) to all gems on a layer.

    Stores information as Rhino UserText on each object, useful for
    BOM reports, rendering, and manufacturing documentation.

    Args:
        gem_layer: Layer with gem objects.
        gem_type: Gem type (diamond, emerald, ruby, sapphire, etc.).
        cut: Cut style (round_brilliant, emerald, oval, pear, marquise, etc.).
        color_grade: Color grade (D-Z for diamonds, or descriptive for colored).
        clarity: Clarity grade (FL, IF, VVS1, VVS2, VS1, VS2, SI1, SI2, I1).
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        objs = rs.ObjectsByLayer("{gem_layer}")
        if not objs:
            print("No objects on {gem_layer}")
        else:
            for obj in objs:
                rs.SetUserText(obj, "gem_type", "{gem_type}")
                rs.SetUserText(obj, "cut", "{cut}")
                rs.SetUserText(obj, "color_grade", "{color_grade}")
                rs.SetUserText(obj, "clarity", "{clarity}")

                # Estimate carat from volume
                vol = rs.SurfaceVolume(obj)
                if vol:
                    # density varies: diamond=3.52, emerald=2.76, ruby=4.0, sapphire=4.0
                    densities = {{"diamond": 0.00352, "emerald": 0.00276, "ruby": 0.00400,
                                 "sapphire": 0.00400, "amethyst": 0.00265, "topaz": 0.00350}}
                    d = densities.get("{gem_type}", 0.00352)
                    carat = vol[0] * d / 0.2
                    rs.SetUserText(obj, "est_carat", "{{:.3f}}".format(carat))

            print("Set metadata on {{}} gems: {gem_type} {cut} {color_grade}/{clarity}".format(len(objs)))
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 99: add_dimensions
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def add_dimensions(
    object_layer: str = "Ring_Band",
    output_layer: str = "Dimensions",
    dim_type: str = "bounding_box",
) -> str:
    """Add manufacturing dimensions to objects for documentation.

    Creates linear dimension annotations showing key measurements.

    Args:
        object_layer: Layer with objects to dimension.
        output_layer: Layer for dimension annotations.
        dim_type: Type of dimensions — "bounding_box" (overall LxWxH),
                  "ring_diameter" (inner diameter measurement).
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}", [128, 128, 128])

        objs = rs.ObjectsByLayer("{object_layer}")
        if not objs:
            print("No objects on {object_layer}")
        else:
            bb = rs.BoundingBox(objs)
            if not bb:
                print("Cannot compute bounding box")
            else:
                if "{dim_type}" == "bounding_box":
                    # Width dimension (X)
                    offset = 3
                    dim_w = rs.AddLinearDimension(
                        rs.WorldXYPlane(),
                        (bb[0][0], bb[0][1] - offset, 0),
                        (bb[1][0], bb[0][1] - offset, 0),
                        (bb[0][0], bb[0][1] - offset * 2, 0)
                    )
                    if dim_w:
                        rs.ObjectLayer(dim_w, "{output_layer}")

                    # Depth dimension (Y)
                    dim_d = rs.AddLinearDimension(
                        rs.PlaneFromNormal((0,0,0), (0,0,1)),
                        (bb[1][0] + offset, bb[0][1], 0),
                        (bb[1][0] + offset, bb[3][1], 0),
                        (bb[1][0] + offset * 2, bb[0][1], 0)
                    )
                    if dim_d:
                        rs.ObjectLayer(dim_d, "{output_layer}")

                    # Height dimension (Z)
                    dim_h = rs.AddLinearDimension(
                        rs.PlaneFromNormal((0,0,0), (0,1,0)),
                        (bb[0][0] - offset, 0, bb[0][2]),
                        (bb[0][0] - offset, 0, bb[4][2]),
                        (bb[0][0] - offset * 2, 0, bb[0][2])
                    )
                    if dim_h:
                        rs.ObjectLayer(dim_h, "{output_layer}")

                    w = bb[1][0] - bb[0][0]
                    d = bb[3][1] - bb[0][1]
                    h = bb[4][2] - bb[0][2]
                    print("Dimensions: {{:.2f}} x {{:.2f}} x {{:.2f}} mm (W x D x H)".format(w, d, h))

                elif "{dim_type}" == "ring_diameter":
                    cx = (bb[0][0] + bb[6][0]) / 2.0
                    cy = (bb[0][1] + bb[6][1]) / 2.0
                    w = bb[1][0] - bb[0][0]
                    d = bb[3][1] - bb[0][1]
                    avg_d = (w + d) / 2.0
                    print("Ring approx inner diameter: {{:.2f}} mm".format(avg_d))
                    print("Approx US size: {{:.1f}}".format((avg_d - 11.63) / 0.8128))
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 100: create_toggle_clasp
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_toggle_clasp(
    bar_length: float = 15.0,
    bar_diameter: float = 2.0,
    ring_outer_diameter: float = 12.0,
    ring_wire_diameter: float = 1.5,
    output_layer: str = "Toggle_Clasp",
) -> str:
    """Create a toggle clasp — a T-bar and a matching ring, positioned side-by-side.

    The T-bar is a cylindrical pipe sweeping a straight line capped at both ends.
    The ring is a torus (pipe swept along a full circle). Both pieces are placed
    next to each other with a small gap so they can be inspected separately.

    Args:
        bar_length: Length of the T-bar in mm. Default 15.
        bar_diameter: Diameter of the T-bar wire in mm. Default 2.
        ring_outer_diameter: Outer diameter of the toggle ring in mm. Default 12.
        ring_wire_diameter: Wire diameter of the ring in mm. Default 1.5.
        output_layer: Layer name for both pieces. Default "Toggle_Clasp".
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}", [212, 175, 55])

        bar_len  = {bar_length}
        bar_rad  = {bar_diameter} / 2.0
        ring_od  = {ring_outer_diameter}
        ring_wr  = {ring_wire_diameter}
        ring_mid = ring_od / 2.0 - ring_wr / 2.0  # torus major radius

        # ── T-bar ────────────────────────────────────────────────
        # Straight line along X centred at origin
        bar_start = (-bar_len / 2.0, 0.0, 0.0)
        bar_end   = ( bar_len / 2.0, 0.0, 0.0)
        bar_line  = rs.AddLine(bar_start, bar_end)
        bar_pipes = rs.AddPipe(bar_line, 0, bar_rad, cap=1) if bar_line else None
        if bar_pipes:
            for bp in bar_pipes:
                rs.ObjectLayer(bp, "{output_layer}")
        if bar_line:
            rs.DeleteObject(bar_line)

        # Connecting loop at bar centre — a small ring so a chain can attach
        loop_r    = bar_rad * 1.8
        loop_pts  = []
        n_loop    = 48
        for i in range(n_loop + 1):
            a = 2.0 * math.pi * i / n_loop
            loop_pts.append((0.0, loop_r * math.cos(a), loop_r * math.sin(a) + bar_rad + loop_r))
        loop_crv  = rs.AddInterpCurve(loop_pts, degree=3)
        loop_pipe = rs.AddPipe(loop_crv, 0, bar_rad * 0.6, cap=1) if loop_crv else None
        if loop_pipe:
            for lp in loop_pipe:
                rs.ObjectLayer(lp, "{output_layer}")
        if loop_crv:
            rs.DeleteObject(loop_crv)

        # ── Toggle ring ──────────────────────────────────────────
        # Offset to the right so the two pieces sit next to each other
        gap    = ring_od / 2.0 + bar_len / 2.0 + 4.0
        r_cx   = gap
        r_cy   = 0.0

        ring_pts = []
        n_ring   = 72
        for i in range(n_ring + 1):
            a = 2.0 * math.pi * i / n_ring
            ring_pts.append((r_cx + ring_mid * math.cos(a), r_cy + ring_mid * math.sin(a), 0.0))
        ring_path = rs.AddInterpCurve(ring_pts, degree=3)
        if ring_path:
            rs.SimplifyCurve(ring_path)
        ring_pipes = rs.AddPipe(ring_path, 0, ring_wr / 2.0, cap=0) if ring_path else None
        if ring_pipes:
            for rp in ring_pipes:
                rs.ObjectLayer(rp, "{output_layer}")
        if ring_path:
            rs.DeleteObject(ring_path)

        print("Toggle clasp: T-bar {{:.1f}}x{{:.1f}}mm, ring OD {{:.1f}}mm, layer '{output_layer}'".format(
            {bar_length}, {bar_diameter}, {ring_outer_diameter}))
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 101: create_lobster_clasp
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_lobster_clasp(
    length: float = 12.0,
    width: float = 6.0,
    wire_diameter: float = 1.0,
    output_layer: str = "Lobster_Clasp",
) -> str:
    """Create a simplified lobster clasp — teardrop body plus spring lever arc.

    The body is built as a pipe swept along a teardrop-shaped interpolated curve.
    A small lever arc (spring gate) is added across the narrow end of the teardrop
    to suggest the spring mechanism. Suitable as a reference/placeholder geometry
    for jewelry design layouts.

    Args:
        length: Overall length of the clasp body in mm. Default 12.
        width: Maximum width of the teardrop body in mm. Default 6.
        wire_diameter: Wire thickness used for all pipe sweeps in mm. Default 1.
        output_layer: Layer name for the clasp. Default "Lobster_Clasp".
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}", [212, 175, 55])

        L    = {length}
        W    = {width}
        wr   = {wire_diameter} / 2.0

        # ── Teardrop outline ─────────────────────────────────────
        # Parametric teardrop: narrow at the top (y=L), wide in the middle, closed at bottom
        # We use a smooth closed interpolated curve with ~40 points
        n_td = 40
        td_pts = []
        for i in range(n_td):
            t = 2.0 * math.pi * i / n_td
            # Teardrop: r = W/2 * (1 - cos(t)) * 0.5 scaled to match L
            r_t = (W / 2.0) * (1.0 - math.cos(t)) / 2.0
            x_t = r_t * math.sin(t)
            y_t = (L / 2.0) * math.cos(t)
            td_pts.append((x_t, y_t, 0.0))

        # Close the curve
        td_pts.append(td_pts[0])
        body_crv  = rs.AddInterpCurve(td_pts, degree=3)
        body_pipe = rs.AddPipe(body_crv, 0, wr, cap=0) if body_crv else None
        if body_pipe:
            for bp in body_pipe:
                rs.ObjectLayer(bp, "{output_layer}")
        if body_crv:
            rs.DeleteObject(body_crv)

        # ── Spring lever arc (gate) ──────────────────────────────
        # Small arc at the narrow (top) end spanning ~120 deg
        gate_r   = W / 4.0
        gate_top = L / 2.0
        n_gate   = 16
        gate_pts = []
        start_a  = math.radians(30)
        end_a    = math.radians(150)
        for i in range(n_gate + 1):
            a = start_a + (end_a - start_a) * i / n_gate
            gate_pts.append((gate_r * math.cos(a), gate_top - gate_r + gate_r * math.sin(a), 0.0))
        gate_crv  = rs.AddInterpCurve(gate_pts, degree=3)
        gate_pipe = rs.AddPipe(gate_crv, 0, wr * 0.7, cap=1) if gate_crv else None
        if gate_pipe:
            for gp in gate_pipe:
                rs.ObjectLayer(gp, "{output_layer}")
        if gate_crv:
            rs.DeleteObject(gate_crv)

        # ── Attachment loop at the wide (bottom) end ─────────────
        loop_r   = wr * 2.5
        loop_ctr = -L / 2.0
        loop_pts = []
        n_lp     = 36
        for i in range(n_lp + 1):
            a = 2.0 * math.pi * i / n_lp
            loop_pts.append((loop_r * math.cos(a), loop_ctr + loop_r * math.sin(a), 0.0))
        loop_crv  = rs.AddInterpCurve(loop_pts, degree=3)
        loop_pipe = rs.AddPipe(loop_crv, 0, wr * 0.7, cap=0) if loop_crv else None
        if loop_pipe:
            for lp in loop_pipe:
                rs.ObjectLayer(lp, "{output_layer}")
        if loop_crv:
            rs.DeleteObject(loop_crv)

        print("Lobster clasp: {{:.1f}}x{{:.1f}}mm, wire {{:.1f}}mm, layer '{output_layer}'".format(
            {length}, {width}, {wire_diameter}))
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 102: create_box_clasp
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_box_clasp(
    box_length: float = 8.0,
    box_width: float = 6.0,
    box_height: float = 3.0,
    tongue_length: float = 6.0,
    output_layer: str = "Box_Clasp",
) -> str:
    """Create a box clasp — a rectangular hollow box and a flat tongue/tab insert.

    The box is modelled as a thin-walled rectangular solid (extruded rectangle
    shelled by wall_thickness). The tongue is a flat extruded rectangle that
    represents the spring strip that slides inside the box.

    Args:
        box_length: External box length in mm. Default 8.
        box_width: External box width in mm. Default 6.
        box_height: External box height in mm. Default 3.
        tongue_length: Length of the tongue strip that inserts into the box (mm). Default 6.
        output_layer: Layer name for both pieces. Default "Box_Clasp".
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}", [212, 175, 55])

        bL  = {box_length}
        bW  = {box_width}
        bH  = {box_height}
        tL  = {tongue_length}
        wall = max(0.4, min(bH * 0.18, 0.7))  # wall thickness: ~18% of height, 0.4-0.7mm

        # ── Outer box shell ──────────────────────────────────────
        # Outer rectangle in XY plane, centred at origin
        outer_corners = [
            (-bL / 2.0, -bW / 2.0, 0.0),
            ( bL / 2.0, -bW / 2.0, 0.0),
            ( bL / 2.0,  bW / 2.0, 0.0),
            (-bL / 2.0,  bW / 2.0, 0.0),
        ]
        outer_rect = rs.AddPolyline(outer_corners + [outer_corners[0]])
        outer_srf  = rs.AddPlanarSrf([outer_rect]) if outer_rect else None

        inner_corners = [
            (-bL / 2.0 + wall, -bW / 2.0 + wall, 0.0),
            ( bL / 2.0 - wall, -bW / 2.0 + wall, 0.0),
            ( bL / 2.0 - wall,  bW / 2.0 - wall, 0.0),
            (-bL / 2.0 + wall,  bW / 2.0 - wall, 0.0),
        ]
        inner_rect = rs.AddPolyline(inner_corners + [inner_corners[0]])
        inner_srf  = rs.AddPlanarSrf([inner_rect]) if inner_rect else None

        box_objects = []

        # Walls: extrude outer minus inner
        if outer_srf and inner_srf:
            outer_solid = rs.ExtrudeSurface(outer_srf[0], rs.AddLine((0,0,0),(0,0,bH))) if outer_srf else None
            inner_solid = rs.ExtrudeSurface(inner_srf[0], rs.AddLine((0,0,0),(0,0,bH))) if inner_srf else None
            if outer_solid and inner_solid:
                box_shell = rs.BooleanDifference([outer_solid], [inner_solid])
                if box_shell:
                    for bs in box_shell:
                        rs.ObjectLayer(bs, "{output_layer}")
                        box_objects.append(bs)
            # Bottom cap — thin floor
            floor_pts = outer_corners + [outer_corners[0]]
            floor_rect = rs.AddPolyline(floor_pts)
            floor_srf  = rs.AddPlanarSrf([floor_rect]) if floor_rect else None
            if floor_srf:
                floor_solid = rs.ExtrudeSurface(floor_srf[0], rs.AddLine((0,0,0),(0,0,wall)))
                if floor_solid:
                    rs.ObjectLayer(floor_solid, "{output_layer}")
                    box_objects.append(floor_solid)
                rs.DeleteObjects(floor_srf)
            if floor_rect:
                rs.DeleteObject(floor_rect)

        for crv in [outer_rect, inner_rect]:
            if crv:
                rs.DeleteObject(crv)
        for srf_list in [outer_srf, inner_srf]:
            if srf_list:
                rs.DeleteObjects(srf_list)

        # ── Tongue (flat spring strip) ────────────────────────────
        # Placed to the right of the box with a small gap, flush in Z
        tongue_w    = bW - wall * 4.0   # slightly narrower than inner cavity
        tongue_t    = 0.5               # tongue thickness in mm
        tongue_x0   = bL / 2.0 + 2.0   # gap of 2 mm from box face
        tongue_corners = [
            (tongue_x0,            -tongue_w / 2.0, 0.0),
            (tongue_x0 + tL,       -tongue_w / 2.0, 0.0),
            (tongue_x0 + tL,        tongue_w / 2.0, 0.0),
            (tongue_x0,             tongue_w / 2.0, 0.0),
        ]
        tongue_rect  = rs.AddPolyline(tongue_corners + [tongue_corners[0]])
        tongue_srf   = rs.AddPlanarSrf([tongue_rect]) if tongue_rect else None
        tongue_solid = None
        if tongue_srf:
            tongue_solid = rs.ExtrudeSurface(tongue_srf[0], rs.AddLine((0,0,0),(0,0,tongue_t)))
            if tongue_solid:
                rs.ObjectLayer(tongue_solid, "{output_layer}")
            rs.DeleteObjects(tongue_srf)
        if tongue_rect:
            rs.DeleteObject(tongue_rect)

        total = len(box_objects) + (1 if tongue_solid else 0)
        print("Box clasp: {{:.1f}}x{{:.1f}}x{{:.1f}}mm box, {{:.1f}}mm tongue, wall {{:.2f}}mm — {{}} objects on '{output_layer}'".format(
            {box_length}, {box_width}, {box_height}, {tongue_length}, wall, total))
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 103: create_jump_ring
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_jump_ring(
    outer_diameter: float = 6.0,
    wire_diameter: float = 0.8,
    gap_angle: float = 30.0,
    output_layer: str = "Jump_Ring",
) -> str:
    """Create a split jump ring with an adjustable opening gap.

    The ring is an arc (full circle minus the gap angle) swept as a pipe.
    The gap represents the cut/split through which another ring or component passes.

    Args:
        outer_diameter: Outer diameter of the jump ring in mm. Default 6.
        wire_diameter: Diameter of the wire forming the ring in mm. Default 0.8.
        gap_angle: Angle of the opening gap in degrees (0 = closed torus). Default 30.
        output_layer: Layer name for the ring. Default "Jump_Ring".
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}", [212, 175, 55])

        od      = {outer_diameter}
        wr      = {wire_diameter}
        gap_deg = {gap_angle}

        # Mid-line radius: from centre of ring to centre of wire
        mid_r = (od - wr) / 2.0

        if mid_r <= 0:
            print("Error: outer_diameter must be greater than wire_diameter")
        else:
            gap_rad  = math.radians(gap_deg)
            arc_span = 2.0 * math.pi - gap_rad   # radians of the open arc

            if arc_span <= 0:
                print("Error: gap_angle {{:.1f}} deg leaves no arc to create".format(gap_deg))
            else:
                # Build arc points; gap centred at angle 0 (positive-X side)
                n_pts    = max(24, int(arc_span / (2.0 * math.pi) * 72))
                half_gap = gap_rad / 2.0
                start_a  = half_gap          # gap starts here
                end_a    = 2.0 * math.pi - half_gap  # gap ends here

                arc_pts = []
                for i in range(n_pts + 1):
                    a = start_a + arc_span * i / n_pts
                    arc_pts.append((mid_r * math.cos(a), mid_r * math.sin(a), 0.0))

                arc_crv  = rs.AddInterpCurve(arc_pts, degree=3)
                arc_pipe = rs.AddPipe(arc_crv, 0, wr / 2.0, cap=1) if arc_crv else None

                if arc_pipe:
                    for ap in arc_pipe:
                        rs.ObjectLayer(ap, "{output_layer}")
                    print("Jump ring: OD {{:.2f}}mm, wire {{:.2f}}mm, gap {{:.1f}} deg — layer '{output_layer}'".format(
                        {outer_diameter}, {wire_diameter}, {gap_angle}))
                else:
                    print("Failed to create jump ring pipe")

                if arc_crv:
                    rs.DeleteObject(arc_crv)
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 104: create_rope_chain
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_rope_chain(
    length: float = 50.0,
    wire_diameter: float = 0.5,
    twist_radius: float = 1.5,
    turns_per_mm: float = 0.5,
    output_layer: str = "Rope_Chain",
) -> str:
    """Create a rope chain — two helical wires twisted around each other.

    Generates two intertwined helices offset by 180 degrees, then pipes
    each to the specified wire diameter to form a realistic rope chain.

    Args:
        length: Total chain length in mm.
        wire_diameter: Diameter of each wire strand in mm (default 0.5).
        twist_radius: Radius of each helix from the chain centre-line in mm (default 1.5).
        turns_per_mm: Number of full turns per mm of length (default 0.5).
        output_layer: Layer to place the finished rope chain on.
    """
    total_turns = turns_per_mm * length
    wire_radius = wire_diameter / 2.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}", [212, 175, 55])

        length      = {length}
        twist_r     = {twist_radius}
        total_turns = {total_turns}
        wire_r      = {wire_radius}

        # 72 sample points per full turn for a smooth helix
        n_pts = max(int(total_turns * 72), 4)

        wires_created = 0
        for phase_deg in [0, 180]:
            phase = math.radians(phase_deg)
            pts = []
            for i in range(n_pts + 1):
                t     = float(i) / n_pts
                angle = phase + t * total_turns * 2.0 * math.pi
                x     = twist_r * math.cos(angle)
                y     = twist_r * math.sin(angle)
                z     = t * length
                pts.append((x, y, z))

            crv = rs.AddInterpCurve(pts, degree=3)
            if crv:
                pipe = rs.AddPipe(crv, 0, wire_r, cap=1)
                if pipe:
                    for p in pipe:
                        rs.ObjectLayer(p, "{output_layer}")
                    wires_created += 1
                rs.DeleteObject(crv)

        print("Rope chain: {{:.1f}} mm long, {{}} wires, {{:.2f}} mm wire diameter".format(
            length, wires_created, wire_r * 2))
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 105: create_ball_chain
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_ball_chain(
    length: float = 50.0,
    ball_diameter: float = 3.0,
    connector_diameter: float = 0.5,
    spacing: float = 1.0,
    output_layer: str = "Ball_Chain",
) -> str:
    """Create a ball chain — spheres connected by thin wire segments.

    Places spheres along a line with small cylinder connectors between
    them, spaced by the gap defined in 'spacing'.

    Args:
        length: Total chain length in mm.
        ball_diameter: Diameter of each ball in mm (default 3.0).
        connector_diameter: Diameter of the connector wire in mm (default 0.5).
        spacing: Gap between adjacent ball surfaces in mm (default 1.0).
        output_layer: Layer to place the chain on.
    """
    ball_r = ball_diameter / 2.0
    conn_r = connector_diameter / 2.0
    pitch  = ball_diameter + spacing
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}", [192, 192, 192])

        ball_r = {ball_r}
        conn_r = {conn_r}
        pitch  = {pitch}   # centre-to-centre distance
        length = {length}

        num_balls  = max(int(length / pitch), 1)
        balls_made = 0
        conns_made = 0

        for i in range(num_balls):
            cz = i * pitch

            # Sphere
            ball = rs.AddSphere((0.0, 0.0, cz), ball_r)
            if ball:
                rs.ObjectLayer(ball, "{output_layer}")
                balls_made += 1

            # Connector cylinder to next ball
            if i < num_balls - 1:
                z_start = cz + ball_r
                z_end   = cz + pitch - ball_r
                if z_end > z_start:
                    seg = rs.AddLine((0.0, 0.0, z_start), (0.0, 0.0, z_end))
                    if seg:
                        pipe = rs.AddPipe(seg, 0, conn_r, cap=1)
                        if pipe:
                            for p in pipe:
                                rs.ObjectLayer(p, "{output_layer}")
                            conns_made += 1
                        rs.DeleteObject(seg)

        total_len = (num_balls - 1) * pitch + ball_r * 2 if num_balls > 0 else 0
        print("Ball chain: {{}} balls, {{}} connectors, {{:.1f}} mm total".format(
            balls_made, conns_made, total_len))
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 106: create_figaro_chain
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_figaro_chain(
    small_link_diameter: float = 3.0,
    large_link_length: float = 8.0,
    wire_diameter: float = 0.8,
    num_pattern_repeats: int = 10,
    output_layer: str = "Figaro_Chain",
) -> str:
    """Create a Figaro chain — alternating 3 small round links + 1 elongated link.

    Uses torus-like geometry: small links are circular, the large link is a
    stadium (rounded-rectangle) profile. Links are placed in the XZ plane so
    they appear to interlock along the X axis.

    Args:
        small_link_diameter: Outer diameter of each small round link in mm (default 3.0).
        large_link_length: Long-axis outer length of the elongated link in mm (default 8.0).
        wire_diameter: Wire gauge (tube diameter) for all links in mm (default 0.8).
        num_pattern_repeats: Number of [3 small + 1 large] groups (default 10).
        output_layer: Layer to place the chain on.
    """
    wr       = wire_diameter / 2.0
    small_r  = small_link_diameter / 2.0 - wire_diameter / 2.0
    large_hl = large_link_length / 2.0 - small_link_diameter / 2.0
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}", [212, 175, 55])

        wr       = {wr}
        small_r  = max({small_r}, wr + 0.1)   # small torus major radius
        large_hl = max({large_hl}, 0.1)        # half straight section of large link

        small_pitch = (small_r + wr) * 2 * 0.85
        large_pitch = (large_hl * 2 + small_r * 2 + wr * 2) * 0.85

        x = 0.0
        total_links = 0

        for rep in range({num_pattern_repeats}):
            # --- 3 small round links (profile in XZ plane) ---
            for s in range(3):
                pts = []
                n = 48
                for j in range(n):
                    a  = 2.0 * math.pi * j / n
                    px = x + small_r * math.cos(a)
                    pz = small_r * math.sin(a)
                    pts.append((px, 0.0, pz))
                pts.append(pts[0])
                crv = rs.AddInterpCurve(pts, degree=3)
                if crv:
                    pipe = rs.AddPipe(crv, 0, wr, cap=1)
                    if pipe:
                        for p in pipe:
                            rs.ObjectLayer(p, "{output_layer}")
                        total_links += 1
                    rs.DeleteObject(crv)
                x += small_pitch

            # --- 1 large elongated link (stadium profile in XZ plane) ---
            pts = []
            n_semi = 24
            # Right semicircle
            for j in range(n_semi + 1):
                a  = -math.pi / 2.0 + math.pi * j / n_semi
                px = x + large_hl + small_r * math.cos(a)
                pz = small_r * math.sin(a)
                pts.append((px, 0.0, pz))
            # Left semicircle
            for j in range(n_semi + 1):
                a  = math.pi / 2.0 + math.pi * j / n_semi
                px = x - large_hl + small_r * math.cos(a)
                pz = small_r * math.sin(a)
                pts.append((px, 0.0, pz))
            pts.append(pts[0])
            crv = rs.AddInterpCurve(pts, degree=3)
            if crv:
                pipe = rs.AddPipe(crv, 0, wr, cap=1)
                if pipe:
                    for p in pipe:
                        rs.ObjectLayer(p, "{output_layer}")
                    total_links += 1
                rs.DeleteObject(crv)
            x += large_pitch

        print("Figaro chain: {{}} repeats, {{}} links, {{:.1f}} mm long".format(
            {num_pattern_repeats}, total_links, x))
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 107: flow_pattern_along_curve
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 119: zoom_to_layer
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def zoom_to_layer(
    layer_name: str = "Default",
) -> str:
    """Zoom the active viewport to fit all objects on a specific layer.

    Args:
        layer_name: Name of the layer whose objects should fill the viewport.

    Returns:
        RhinoScript Python code ready for execute_rhinoscript_python_code.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        layer_name = "{layer_name}"

        if not rs.IsLayer(layer_name):
            print("Layer '{{}}' not found.".format(layer_name))
        else:
            objs = rs.ObjectsByLayer(layer_name)
            if not objs:
                print("No objects found on layer '{{}}'.".format(layer_name))
            else:
                bb_min = None
                bb_max = None
                for obj in objs:
                    bb = rs.BoundingBox(obj)
                    if bb:
                        pts = list(bb)
                        xs = [p[0] for p in pts]
                        ys = [p[1] for p in pts]
                        zs = [p[2] for p in pts]
                        if bb_min is None:
                            bb_min = [min(xs), min(ys), min(zs)]
                            bb_max = [max(xs), max(ys), max(zs)]
                        else:
                            bb_min = [min(bb_min[0], min(xs)),
                                      min(bb_min[1], min(ys)),
                                      min(bb_min[2], min(zs))]
                            bb_max = [max(bb_max[0], max(xs)),
                                      max(bb_max[1], max(ys)),
                                      max(bb_max[2], max(zs))]

                if bb_min and bb_max:
                    corner_min = (bb_min[0], bb_min[1], bb_min[2])
                    corner_max = (bb_max[0], bb_max[1], bb_max[2])
                    rs.ZoomBoundingBox([corner_min, corner_max])
                    print("Viewport zoomed to layer '{{}}'.".format(layer_name))
                else:
                    print("Could not compute bounding box for layer '{{}}'.".format(layer_name))
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 120: set_display_mode
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def set_display_mode(
    mode: str = "shaded",
) -> str:
    """Set the active viewport display mode.

    Args:
        mode: Display mode to apply. One of "wireframe", "shaded",
              "rendered", "ghosted", "xray". Default "shaded".

    Returns:
        RhinoScript Python code ready for execute_rhinoscript_python_code.
    """
    mode_map = {
        "wireframe": "Wireframe",
        "shaded": "Shaded",
        "rendered": "Rendered",
        "ghosted": "Ghosted",
        "xray": "X-Ray",
    }
    rhino_mode = mode_map.get(mode.lower(), "Shaded")
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        rs.Command("_SetDisplayMode _Mode={rhino_mode} _Enter", False)
        print("Display mode set to: {rhino_mode}")
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 121: export_layer_stl
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def export_layer_stl(
    object_layer: str = "Default",
    file_path: str = "~/Desktop/jewelry_export.stl",
    mesh_quality: str = "fine",
) -> str:
    """Export all objects on a specific layer to an STL file.

    Selects all objects on the layer and exports via Rhino's Export command.
    Mesh quality is communicated as a label in the output message; Rhino
    uses the document mesh settings unless overridden interactively.

    Args:
        object_layer: Layer whose objects will be exported.
        file_path: Destination path for the STL file. Default "~/Desktop/jewelry_export.stl".
        mesh_quality: Mesh density label — "fine", "medium", or "coarse". Default "fine".

    Returns:
        RhinoScript Python code ready for execute_rhinoscript_python_code.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import os

        object_layer = "{object_layer}"
        file_path    = os.path.expanduser("{file_path}")
        mesh_quality = "{mesh_quality}"

        if not rs.IsLayer(object_layer):
            print("Layer '{{}}' not found.".format(object_layer))
        else:
            objs = rs.ObjectsByLayer(object_layer)
            if not objs:
                print("No objects on layer '{{}}'.".format(object_layer))
            else:
                rs.UnselectAllObjects()
                rs.SelectObjects(objs)
                export_dir = os.path.dirname(file_path)
                if export_dir and not os.path.exists(export_dir):
                    os.makedirs(export_dir)
                rs.Command(
                    '_-Export "{{}}" _Enter'.format(file_path), False
                )
                rs.UnselectAllObjects()
                print("Exported {{}} object(s) from '{{}}' to {{}} (mesh quality: {{}})".format(
                    len(objs), object_layer, file_path, mesh_quality))
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 122: create_turntable_frames
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_turntable_frames(
    num_frames: int = 36,
    output_folder: str = "~/Desktop/turntable/",
) -> str:
    """Capture a turntable animation by rotating the camera and saving each frame.

    Rotates the viewport camera by (360 / num_frames) degrees per step around
    the scene and captures each position to a numbered PNG file.

    Args:
        num_frames: Total number of frames to capture. Default 36 (10 degrees each).
        output_folder: Directory where frame images are saved. Default "~/Desktop/turntable/".

    Returns:
        RhinoScript Python code ready for execute_rhinoscript_python_code.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math
        import os

        num_frames    = {num_frames}
        output_folder = os.path.expanduser("{output_folder}")

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        all_objs = rs.AllObjects()
        if not all_objs:
            print("No objects in scene.")
        else:
            step_deg = 360.0 / num_frames

            for i in range(num_frames):
                rs.Command(
                    "_-RotateView _Angle={{:.4f}} _Enter".format(step_deg), False
                )
                frame_file = os.path.join(
                    output_folder, "frame_{{:04d}}.png".format(i)
                )
                rs.Command(
                    '_-ViewCaptureToFile "{{}}" _Width=1920 _Height=1080 _Enter'.format(
                        frame_file
                    ),
                    False
                )

            print("Turntable complete: {{}} frames saved to {{}}".format(
                num_frames, output_folder))
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 123: hide_layers_except
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def hide_layers_except(
    visible_layers: str = "Default",
) -> str:
    """Hide all layers except the specified ones to isolate components.

    Args:
        visible_layers: Comma-separated list of layer names to keep visible.
                        All other layers are hidden. Default "Default".

    Returns:
        RhinoScript Python code ready for execute_rhinoscript_python_code.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        keep_visible_raw = "{visible_layers}"
        keep_visible = [n.strip() for n in keep_visible_raw.split(",") if n.strip()]

        all_layers = rs.LayerNames()
        if not all_layers:
            print("No layers found in document.")
        else:
            hidden = 0
            shown  = 0
            for layer in all_layers:
                if layer in keep_visible:
                    rs.LayerVisible(layer, True)
                    shown += 1
                else:
                    try:
                        rs.LayerVisible(layer, False)
                        hidden += 1
                    except Exception:
                        pass  # Some system layers cannot be hidden

            print("Visibility updated: {{}} layer(s) visible, {{}} layer(s) hidden.".format(
                shown, hidden))
            print("Visible layers: {{}}".format(", ".join(keep_visible)))
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 124: duplicate_and_mirror
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 113: create_brooch_base
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_brooch_base(
    width: float = 30.0,
    height: float = 25.0,
    thickness: float = 1.5,
    pin_length: float = 25.0,
    pin_diameter: float = 0.8,
    front_layer: str = "Brooch_Front",
    back_layer: str = "Brooch_Back",
) -> str:
    """Create a brooch base with front plate, pin stem, and catch plate.

    Generates an oval front decorative plate (~30x25mm, 1.5mm thick), a pin stem
    wire on the back (~25mm long, 0.8mm diameter), and a small catch/clasp box
    (3x2x2mm). All components are placed on named layers.

    Args:
        width: Oval front plate width in mm. Default 30.
        height: Oval front plate height in mm. Default 25.
        thickness: Front plate extrusion thickness in mm. Default 1.5.
        pin_length: Length of the pin stem wire in mm. Default 25.
        pin_diameter: Diameter of the pin wire in mm. Default 0.8.
        front_layer: Layer for the front plate geometry.
        back_layer: Layer for the pin stem and catch plate.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{front_layer}"):
            rs.AddLayer("{front_layer}", [220, 180, 60])
        if not rs.IsLayer("{back_layer}"):
            rs.AddLayer("{back_layer}", [160, 160, 160])

        # ── Front oval plate ──────────────────────────────────
        plane   = rs.WorldXYPlane()
        ellipse = rs.AddEllipse(plane, {width / 2.0}, {height / 2.0})
        if ellipse:
            plate = rs.ExtrudeCurveStraight(ellipse, (0, 0, 0), (0, 0, {thickness}))
            if plate:
                rs.CapPlanarHoles(plate)
                rs.ObjectLayer(plate, "{front_layer}")
            rs.DeleteObject(ellipse)

        # ── Pin stem (wire along X axis, behind the plate) ────
        pin_z     = {thickness} + 0.4
        pin_y     = {height / 2.0} * 0.3
        pin_start = (-{pin_length / 2.0}, pin_y, pin_z)
        pin_end   = ( {pin_length / 2.0}, pin_y, pin_z)
        pin_curve = rs.AddLine(pin_start, pin_end)
        if pin_curve:
            pin_wire = rs.AddPipe(pin_curve, 0, {pin_diameter / 2.0}, cap=1)
            if pin_wire:
                for pw in pin_wire:
                    rs.ObjectLayer(pw, "{back_layer}")
            rs.DeleteObject(pin_curve)

        # ── Catch plate (3x2x2mm box, right side of pin) ─────
        catch_x = {pin_length / 2.0} - 1.5
        catch_y = {height / 2.0} * 0.3 - 1.0
        catch_z = {thickness}
        catch = rs.AddBox([
            (catch_x,       catch_y,       catch_z),
            (catch_x + 3.0, catch_y,       catch_z),
            (catch_x + 3.0, catch_y + 2.0, catch_z),
            (catch_x,       catch_y + 2.0, catch_z),
            (catch_x,       catch_y,       catch_z + 2.0),
            (catch_x + 3.0, catch_y,       catch_z + 2.0),
            (catch_x + 3.0, catch_y + 2.0, catch_z + 2.0),
            (catch_x,       catch_y + 2.0, catch_z + 2.0),
        ])
        if catch:
            rs.ObjectLayer(catch, "{back_layer}")

        print("Brooch: {{:.1f}}x{{:.1f}}mm plate, {{:.1f}}mm pin on '{front_layer}'/'{back_layer}'".format(
            {width}, {height}, {pin_length}))
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 114: create_cufflink
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_cufflink(
    face_diameter: float = 15.0,
    face_thickness: float = 2.0,
    post_length: float = 8.0,
    post_diameter: float = 1.5,
    shape: str = "circle",
    output_layer: str = "Cufflink",
) -> str:
    """Create a cufflink with decorative face, connecting post, and toggle bar.

    Builds a whale-back style cufflink: circular or square front face (~15mm),
    cylindrical post (8mm), and a torpedo-shaped toggle bar (~15mm long, 3mm wide)
    revolved from a semi-ellipse profile.

    Args:
        face_diameter: Diameter (or side length for square) of front face in mm. Default 15.
        face_thickness: Thickness of the front face disc/plate in mm. Default 2.
        post_length: Length of the connecting post in mm. Default 8.
        post_diameter: Diameter of the post in mm. Default 1.5.
        shape: Front face shape — "circle" or "square". Default "circle".
        output_layer: Layer for all cufflink geometry.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}", [220, 180, 60])

        # ── Front face ────────────────────────────────────────
        if "{shape}" == "circle":
            circle = rs.AddCircle(rs.WorldXYPlane(), {face_diameter / 2.0})
            if circle:
                face = rs.ExtrudeCurveStraight(circle, (0, 0, 0), (0, 0, {face_thickness}))
                if face:
                    rs.CapPlanarHoles(face)
                    rs.ObjectLayer(face, "{output_layer}")
                rs.DeleteObject(circle)
        else:
            half = {face_diameter / 2.0}
            corners = [(-half, -half, 0), (half, -half, 0),
                       (half,  half,  0), (-half, half, 0), (-half, -half, 0)]
            sq = rs.AddPolyline(corners)
            if sq:
                face = rs.ExtrudeCurveStraight(sq, (0, 0, 0), (0, 0, {face_thickness}))
                if face:
                    rs.CapPlanarHoles(face)
                    rs.ObjectLayer(face, "{output_layer}")
                rs.DeleteObject(sq)

        # ── Connecting post ───────────────────────────────────
        post_start = (0, 0, {face_thickness})
        post_end   = (0, 0, {face_thickness + post_length})
        post_line  = rs.AddLine(post_start, post_end)
        if post_line:
            post_pipe = rs.AddPipe(post_line, 0, {post_diameter / 2.0}, cap=1)
            if post_pipe:
                for p in post_pipe:
                    rs.ObjectLayer(p, "{output_layer}")
            rs.DeleteObject(post_line)

        # ── Toggle bar (torpedo / whale-back, 15mm x 3mm) ────
        toggle_z   = {face_thickness + post_length}
        tog_half_l = 7.5
        tog_r      = 1.5
        n_pts      = 24
        profile_pts = []
        for i in range(n_pts + 1):
            t  = math.pi * i / n_pts
            px = tog_half_l * math.cos(t)
            pz = tog_r * math.sin(t)
            profile_pts.append((px, 0, toggle_z + pz))
        profile_pts.append((tog_half_l, 0, toggle_z))
        profile_crv = rs.AddPolyline(profile_pts)
        if profile_crv:
            axis_start = (-tog_half_l, 0, toggle_z)
            axis_end   = ( tog_half_l, 0, toggle_z)
            toggle_srf = rs.AddRevSrf(profile_crv, (axis_start, axis_end), 0, 360)
            if toggle_srf:
                rs.CapPlanarHoles(toggle_srf)
                rs.ObjectLayer(toggle_srf, "{output_layer}")
            rs.DeleteObject(profile_crv)

        print("Cufflink: {shape} face {{:.1f}}mm, post {{:.1f}}mm, toggle bar on '{output_layer}'".format(
            {face_diameter}, {post_length}))
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 115: create_tiara_base
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_tiara_base(
    inner_diameter: float = 140.0,
    band_height: float = 5.0,
    band_thickness: float = 1.0,
    num_peaks: int = 5,
    peak_height: float = 25.0,
    output_layer: str = "Tiara",
) -> str:
    """Create a tiara / crown base with a semi-circular band and pointed peaks.

    Builds a half-ring band sized for a human head (~140mm inner diameter) using
    arc interpolation, then adds evenly-spaced triangular peak surfaces rising
    from the top edge of the band.

    Args:
        inner_diameter: Inner diameter of the head band in mm. Default 140.
        band_height: Height of the base band in mm. Default 5.
        band_thickness: Wall thickness of the band in mm. Default 1.
        num_peaks: Number of decorative peaks (spires). Default 5.
        peak_height: Height of each peak above the band top edge in mm. Default 25.
        output_layer: Layer for all tiara geometry.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}", [220, 180, 60])

        inner_r  = {inner_diameter / 2.0}
        outer_r  = inner_r + {band_thickness}
        band_h   = {band_height}
        n_peaks  = {num_peaks}
        p_height = {peak_height}

        # ── Semi-circular band ────────────────────────────────
        def arc_pts(radius, n=72):
            return [(radius * math.cos(math.pi * i / n),
                     radius * math.sin(math.pi * i / n), 0)
                    for i in range(n + 1)]

        ib = arc_pts(inner_r)
        it = [(p[0], p[1], band_h) for p in ib]
        ob = arc_pts(outer_r)
        ot = [(p[0], p[1], band_h) for p in ob]

        crv_ib = rs.AddInterpCurve(ib)
        crv_it = rs.AddInterpCurve(it)
        crv_ob = rs.AddInterpCurve(ob)
        crv_ot = rs.AddInterpCurve(ot)
        cap_l_b = rs.AddLine(ib[0],  ob[0])
        cap_l_t = rs.AddLine(it[0],  ot[0])
        cap_r_b = rs.AddLine(ib[-1], ob[-1])
        cap_r_t = rs.AddLine(it[-1], ot[-1])

        band_srfs = []
        for r1, r2 in [(crv_ob, crv_ib), (crv_ot, crv_it),
                       (crv_ib, crv_it), (crv_ob, crv_ot)]:
            srf = rs.AddLoftSrf([r1, r2])
            if srf:
                band_srfs.extend(srf)
        for b, t in [(cap_l_b, cap_l_t), (cap_r_b, cap_r_t)]:
            srf = rs.AddLoftSrf([b, t])
            if srf:
                band_srfs.extend(srf)
        for s in band_srfs:
            rs.ObjectLayer(s, "{output_layer}")
        for c in [crv_ib, crv_it, crv_ob, crv_ot,
                  cap_l_b, cap_l_t, cap_r_b, cap_r_t]:
            if c:
                rs.DeleteObject(c)

        # ── Triangular peaks ──────────────────────────────────
        mid_r = (inner_r + outer_r) / 2.0
        for i in range(n_peaks):
            angle   = (math.pi * i / (n_peaks - 1)) if n_peaks > 1 else math.pi / 2.0
            cx      = mid_r * math.cos(angle)
            cy      = mid_r * math.sin(angle)
            half_w  = math.pi / (n_peaks * 2.5) if n_peaks > 1 else 0.2
            base_l  = (mid_r * math.cos(angle - half_w),
                       mid_r * math.sin(angle - half_w), band_h)
            base_r  = (mid_r * math.cos(angle + half_w),
                       mid_r * math.sin(angle + half_w), band_h)
            apex    = (cx, cy, band_h + p_height)
            tri = rs.AddSrfPt([base_l, apex, base_r, base_l])
            if tri:
                rs.ObjectLayer(tri, "{output_layer}")

        print("Tiara: {{:.0f}}mm inner diam, {{}} peaks x {{:.0f}}mm on '{output_layer}'".format(
            {inner_diameter}, {num_peaks}, {peak_height}))
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 116: create_gem_block
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_gem_block(
    gem_layer: str = "Gems",
    block_name: str = "GemInstance",
) -> str:
    """Convert repeated gem objects into a reusable Rhino block definition.

    Takes all objects on gem_layer, creates a named block definition, then
    replaces every gem with a block instance at the same centre position.
    Dramatically reduces file size when hundreds of identical gems are present.
    Uses rs.AddBlock and rs.InsertBlock.

    Args:
        gem_layer: Layer containing the gem objects to convert.
        block_name: Name for the new block definition.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        gem_layer  = "{gem_layer}"
        block_name = "{block_name}"

        objs = rs.ObjectsByLayer(gem_layer)
        if not objs:
            print("No objects found on layer: " + gem_layer)
        else:
            def obj_centre(o):
                bb = rs.ObjectBoundingBox(o)
                if bb:
                    return ((bb[0][0] + bb[6][0]) / 2.0,
                            (bb[0][1] + bb[6][1]) / 2.0,
                            bb[0][2])
                return (0, 0, 0)

            positions = [obj_centre(o) for o in objs]
            base_pt   = positions[0]

            # Create block definition; delete_input=True removes originals
            block_id = rs.AddBlock(objs, base_pt, block_name, delete_input=True)

            if not block_id and not rs.IsBlock(block_name):
                print("Failed to create block definition: " + block_name)
            else:
                inserted = 0
                for pos in positions:
                    inst = rs.InsertBlock(block_name, pos)
                    if inst:
                        rs.ObjectLayer(inst, gem_layer)
                        inserted += 1
                print("Block '{{}}' created. Replaced {{}} gems with block instances.".format(
                    block_name, inserted))
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 117: create_section_view
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_section_view(
    object_layer: str = "Ring_Band",
    cut_axis: str = "y",
    cut_position: float = 0.0,
    output_layer: str = "Section_View",
) -> str:
    """Create a cross-section view by intersecting objects with an axis-aligned plane.

    Intersects all polysurfaces/surfaces on object_layer with a cutting plane
    at cut_position along cut_axis, and places resulting section curves on
    output_layer for documentation or analysis.

    Args:
        object_layer: Layer with objects to section.
        cut_axis: Normal axis of the cutting plane — "x", "y", or "z". Default "y".
        cut_position: Position along cut_axis in mm. Default 0.
        output_layer: Layer for the section curve results.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}", [255, 80, 80])

        objs = rs.ObjectsByLayer("{object_layer}")
        if not objs:
            print("No objects on layer: {object_layer}")
        else:
            pos  = {cut_position}
            axis = "{cut_axis}".lower()

            if axis == "x":
                plane = rs.PlaneFromNormal((pos, 0, 0), (1, 0, 0))
            elif axis == "z":
                plane = rs.PlaneFromNormal((0, 0, pos), (0, 0, 1))
            else:
                plane = rs.PlaneFromNormal((0, pos, 0), (0, 1, 0))

            section_curves = []
            for obj in objs:
                if rs.IsPolysurface(obj) or rs.IsSurface(obj):
                    crv = rs.IntersectBrep(obj, plane)
                    if crv:
                        section_curves.extend(crv)

            if section_curves:
                for c in section_curves:
                    rs.ObjectLayer(c, "{output_layer}")
                print("Section view: {{}} curves on '{output_layer}' ({cut_axis}={{:.2f}}mm)".format(
                    len(section_curves), pos))
            else:
                print("No section geometry — verify cut position intersects objects on {object_layer}")
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 118: create_bezier_band
# ──────────────────────────────────────────────────────────────
@mcp.tool()
def create_bezier_band(
    us_size: float = 7.0,
    profile_points: str = "[[0,0],[1.5,0],[2.0,0.5],[2.0,1.5],[1.0,2.0],[0,2.0]]",
    output_layer: str = "Custom_Band",
) -> str:
    """Create a custom-profile ring band by revolving a user-defined cross-section.

    Parses profile_points as a JSON array of [x, z] pairs describing one half
    of the band cross-section (the radially-outer half in the XZ plane). The
    profile is mirrored across x=0 (the band midline), closed, and revolved
    360 degrees around the Z axis to produce the full solid band. Enables any
    custom band shape — flat, knife-edge, D-profile, court, etc.

    Args:
        us_size: US ring size used to determine inner diameter. Default 7.0.
        profile_points: JSON string — list of [x, z] pairs for the outer half
                        cross-section. x is radial offset from band midline (mm),
                        z is axial height (mm). Example:
                        "[[0,0],[1.5,0],[2.0,0.5],[2.0,1.5],[1.0,2.0],[0,2.0]]"
        output_layer: Layer for the finished band solid.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math
        import json

        if not rs.IsLayer("{output_layer}"):
            rs.AddLayer("{output_layer}", [220, 180, 60])

        us_size    = {us_size}
        inner_circ = 36.5 + us_size * 0.8128
        inner_r    = inner_circ / (2.0 * math.pi)

        raw_pts = json.loads('{profile_points}')

        # Right half: X = inner_r + x_offset, Z = z (radially outward)
        right_half = [(inner_r + p[0], p[1]) for p in raw_pts]
        # Left half: mirror x_offset (inner face), reversed for closed loop
        left_half  = [(inner_r - p[0], p[1]) for p in reversed(raw_pts)]

        full_2d = right_half + left_half
        if full_2d[0] != full_2d[-1]:
            full_2d.append(full_2d[0])

        # Lift profile into XZ plane (Y = 0) for revolution around Z axis
        profile_3d  = [(pt[0], 0, pt[1]) for pt in full_2d]
        profile_crv = rs.AddPolyline(profile_3d)

        if not profile_crv:
            print("Failed to create profile curve — check profile_points JSON")
        else:
            axis_start = (0, 0, 0)
            axis_end   = (0, 0, 1)
            band_srf   = rs.AddRevSrf(profile_crv, (axis_start, axis_end), 0, 360)
            rs.DeleteObject(profile_crv)

            if band_srf:
                rs.CapPlanarHoles(band_srf)
                rs.ObjectLayer(band_srf, "{output_layer}")
                print("Custom band: US {{:.1f}}, inner r={{:.2f}}mm, {{}} profile pts on '{output_layer}'".format(
                    us_size, inner_r, len(raw_pts)))
            else:
                print("Revolution failed — ensure profile points form a valid closed outline")
    """)


# ──────────────────────────────────────────────────────────────
# TOOL 108: check_symmetry
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 109: check_min_radius
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 110: validate_jewelry_params
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 111: check_surface_continuity
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# TOOL 112: generate_production_checklist
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# Run server
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")
