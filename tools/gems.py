import math
import textwrap
from app import mcp


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


@mcp.tool()
def create_cabochon_gem(
    layer: str = "Gem_Cabochon",
    diameter: float = 8.0,
    height: float = 4.0,
    base_height: float = 1.0,
    shape: str = "round",
) -> str:
    """Create a cabochon (domed, unfaceted) gemstone — round or oval.

    Cabochons are polished rather than faceted, common for opals, turquoise,
    moonstone, and jade. The profile is a smooth dome on top with a flat or
    shallow base underneath. Built using Revolve for round, or Loft for oval.

    Args:
        layer: Layer for the cabochon gem.
        diameter: Diameter in mm (or major axis for oval).
        height: Dome height in mm above the girdle.
        base_height: Height of the flat base below the girdle.
        shape: 'round' or 'oval' (oval uses 0.7× minor axis).
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        layer = "{layer}"
        if not rs.IsLayer(layer):
            rs.AddLayer(layer)
        rs.CurrentLayer(layer)

        d = {diameter}
        r = d / 2.0
        h = {height}
        base_h = {base_height}
        shape = "{shape}"

        if shape == "oval":
            r_minor = r * 0.7
        else:
            r_minor = r

        # Build profile for revolve (round) or sections for loft (oval)
        if shape == "round":
            # Profile: flat base -> girdle -> dome top
            pts = []
            pts.append((0, 0, -base_h))       # center bottom
            pts.append((r, 0, -base_h))        # base edge
            pts.append((r, 0, 0))              # girdle
            # Dome arc points
            n_arc = 12
            for i in range(n_arc + 1):
                angle = math.pi / 2.0 * i / n_arc
                px = r * math.cos(angle)
                pz = h * math.sin(angle)
                pts.append((px, 0, pz))
            pts.append((0, 0, h))              # top

            crv = rs.AddInterpCurve(pts)
            line = rs.AddLine((0, 0, -base_h), (0, 0, h))
            axis = ((0, 0, -base_h), (0, 0, h))
            srf = rs.AddRevSrf(crv, axis, 0, 360)
            if srf:
                rs.CapPlanarHoles(srf)
            rs.DeleteObjects([crv, line])
            print("Round cabochon: {{:.1f}}mm dia x {{:.1f}}mm high on '{layer}'".format(d, h + base_h))
        else:
            # Oval: loft ellipses at different heights
            sections = []
            # Base ellipse
            plane = rs.MovePlane(rs.WorldXYPlane(), (0, 0, -base_h))
            sections.append(rs.AddEllipse(plane, r, r_minor))
            # Girdle
            plane = rs.MovePlane(rs.WorldXYPlane(), (0, 0, 0))
            sections.append(rs.AddEllipse(plane, r, r_minor))
            # Mid dome
            frac = 0.7
            plane = rs.MovePlane(rs.WorldXYPlane(), (0, 0, h * 0.5))
            sections.append(rs.AddEllipse(plane, r * frac, r_minor * frac))
            # Near top
            frac2 = 0.3
            plane = rs.MovePlane(rs.WorldXYPlane(), (0, 0, h * 0.85))
            sections.append(rs.AddEllipse(plane, r * frac2, r_minor * frac2))

            loft = rs.AddLoftSrf(sections)
            if loft:
                for s in loft:
                    rs.CapPlanarHoles(s)
            rs.DeleteObjects(sections)
            print("Oval cabochon: {{:.1f}}x{{:.1f}}mm on '{layer}'".format(d, d * 0.7))
    """)


@mcp.tool()
def flow_gems_to_surface(
    gem_layer: str = "Gems_Flat",
    target_layer: str = "Ring_Band",
    result_layer: str = "Gems_Flowed",
) -> str:
    """Flow gems from a flat reference plane onto a curved jewelry surface.

    Places gems arranged on a flat plane and uses FlowAlongSrf to map them
    onto a curved target surface (ring, pendant, bangle). Gem orientations
    follow the target surface normals.

    Args:
        gem_layer: Layer with gems arranged on a flat XY plane.
        target_layer: Layer with the curved target surface.
        result_layer: Layer for the flowed gem positions.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        if not rs.IsLayer("{gem_layer}"):
            print("ERROR: Layer '{gem_layer}' not found")
        elif not rs.IsLayer("{target_layer}"):
            print("ERROR: Layer '{target_layer}' not found")
        else:
            if not rs.IsLayer("{result_layer}"):
                rs.AddLayer("{result_layer}")

            gems = rs.ObjectsByLayer("{gem_layer}")
            targets = rs.ObjectsByLayer("{target_layer}")

            if not gems:
                print("ERROR: No gems on '{gem_layer}'")
            elif not targets:
                print("ERROR: No target surface on '{target_layer}'")
            else:
                target = targets[0]

                # Create base reference surface from gem bounding box
                bb = rs.BoundingBox(gems)
                if bb:
                    base_srf = rs.AddSrfPt([
                        (bb[0][0], bb[0][1], 0),
                        (bb[1][0], bb[0][1], 0),
                        (bb[1][0], bb[3][1], 0),
                        (bb[0][0], bb[3][1], 0),
                    ])

                    if base_srf:
                        # Copy gems, flow copies to target surface
                        gem_copies = rs.CopyObjects(gems)
                        rs.SelectObjects(gem_copies)

                        # FlowAlongSrf: from base surface to target surface
                        cmd = "_FlowAlongSrf"
                        rs.Command(cmd, False)
                        rs.UnselectAllObjects()

                        new_objs = rs.LastCreatedObjects()
                        if new_objs:
                            for obj in new_objs:
                                rs.ObjectLayer(obj, "{result_layer}")
                            print("Flowed {{}} gems onto target surface → '{result_layer}'".format(
                                len(new_objs)))
                        else:
                            # Move copies to result layer as fallback
                            for g in gem_copies:
                                rs.ObjectLayer(g, "{result_layer}")
                            print("FlowAlongSrf needs manual surface selection")
                            print("  {{}} gem copies moved to '{result_layer}'".format(len(gem_copies)))

                        rs.DeleteObject(base_srf)
                    else:
                        print("ERROR: Base surface creation failed")
                else:
                    print("ERROR: Cannot compute gem bounding box")
    """)
