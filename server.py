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


# ──────────────────────────────────────────────────────────────
# Run server
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")
