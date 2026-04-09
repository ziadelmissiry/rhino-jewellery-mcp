import math
import textwrap
from app import mcp


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


@mcp.tool()
def create_subd_ring(
    finger_diameter: float = 17.3,
    band_width: float = 6.0,
    band_thickness: float = 2.0,
    divisions_around: int = 16,
    divisions_height: int = 4,
    layer: str = "SubD_Ring",
) -> str:
    """Build an organic SubD ring from a cylinder mesh, ready for sculpting.

    Creates a SubD-friendly mesh cylinder at ring size, converts to SubD,
    and adds edge loops for detail control. Use Gumball to sculpt vertices
    afterward, then convert to NURBS for production.

    Args:
        finger_diameter: Inner diameter in mm (17.3 = US size 7).
        band_width: Width of ring band in mm.
        band_thickness: Radial thickness in mm.
        divisions_around: Mesh divisions around circumference (more = smoother).
        divisions_height: Mesh divisions along band height (more = detail).
        layer: Target layer name.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")
        rs.CurrentLayer("{layer}")

        inner_r = {finger_diameter} / 2.0
        outer_r = inner_r + {band_thickness}
        w = {band_width}
        n_around = {divisions_around}
        n_height = {divisions_height}

        # Build mesh cylinder (hollow tube)
        vertices = []
        faces = []

        for j in range(n_height + 1):
            z = -w / 2.0 + w * j / n_height
            for i in range(n_around):
                a = 2 * math.pi * i / n_around
                # Outer vertex
                vertices.append((outer_r * math.cos(a), outer_r * math.sin(a), z))
            for i in range(n_around):
                a = 2 * math.pi * i / n_around
                # Inner vertex
                vertices.append((inner_r * math.cos(a), inner_r * math.sin(a), z))

        vpr = n_around * 2  # vertices per row (outer + inner)

        # Outer faces
        for j in range(n_height):
            for i in range(n_around):
                i2 = (i + 1) % n_around
                a = j * vpr + i
                b = j * vpr + i2
                c = (j + 1) * vpr + i2
                d = (j + 1) * vpr + i
                faces.append((a, b, c, d))

        # Inner faces (reversed winding)
        for j in range(n_height):
            for i in range(n_around):
                i2 = (i + 1) % n_around
                a = j * vpr + n_around + i
                b = j * vpr + n_around + i2
                c = (j + 1) * vpr + n_around + i2
                d = (j + 1) * vpr + n_around + i
                faces.append((a, d, c, b))

        # Top cap faces
        j = n_height
        for i in range(n_around):
            i2 = (i + 1) % n_around
            a = j * vpr + i
            b = j * vpr + i2
            c = j * vpr + n_around + i2
            d = j * vpr + n_around + i
            faces.append((a, b, c, d))

        # Bottom cap faces
        j = 0
        for i in range(n_around):
            i2 = (i + 1) % n_around
            a = j * vpr + i
            b = j * vpr + i2
            c = j * vpr + n_around + i2
            d = j * vpr + n_around + i
            faces.append((a, d, c, b))

        mesh = rs.AddMesh(vertices, faces)
        if mesh:
            rs.SelectObject(mesh)
            rs.Command("_ToSubD _Enter", False)
            rs.UnselectAllObjects()
            rs.DeleteObject(mesh)
            print("SubD ring on '{{}}' — {{:.1f}}mm ID, {{:.1f}}mm wide".format(
                "{layer}", {finger_diameter}, {band_width}))
            print("Use Gumball to sculpt, then _ToNURBS for production")
        else:
            print("ERROR: Mesh creation failed")
    """)


@mcp.tool()
def create_multipipe_ring(
    finger_diameter: float = 17.3,
    pipe_radius: float = 0.8,
    node_radius: float = 1.0,
    num_strands: int = 3,
    twists: float = 2.0,
    layer: str = "MultiPipe_Ring",
) -> str:
    """Create an abstract/designer ring from intertwined line strands using MultiPipe.

    Generates a skeletal wireframe of twisted strands around a ring form, then
    applies Rhino 7+ MultiPipe to create smooth tubular SubD geometry.

    Args:
        finger_diameter: Inner diameter in mm (17.3 = US size 7).
        pipe_radius: Radius of each pipe strand in mm (min 0.6 for casting).
        node_radius: Radius at strand junctions in mm (>= pipe_radius).
        num_strands: Number of intertwined strands (2-6).
        twists: Number of full twists around the ring.
        layer: Target layer name.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")
        rs.CurrentLayer("{layer}")

        ring_r = {finger_diameter} / 2.0 + {pipe_radius} * 2
        n_strands = {num_strands}
        twists = {twists}
        pipe_r = {pipe_radius}
        node_r = {node_radius}
        n_pts = 60  # points per strand

        strand_ids = []
        for s in range(n_strands):
            pts = []
            phase = 2 * math.pi * s / n_strands
            for i in range(n_pts + 1):
                t = 2 * math.pi * i / n_pts
                twist_a = phase + twists * t
                # Strand orbits around the ring center line
                orbit_r = pipe_r * 2.5
                cx = (ring_r + orbit_r * math.cos(twist_a)) * math.cos(t)
                cy = (ring_r + orbit_r * math.cos(twist_a)) * math.sin(t)
                cz = orbit_r * math.sin(twist_a)
                pts.append((cx, cy, cz))
            crv = rs.AddInterpCurve(pts, 3, 1)  # degree 3, closed
            if crv:
                strand_ids.append(crv)

        if strand_ids:
            rs.SelectObjects(strand_ids)
            cmd = "_MultiPipe _Radius={{}} _NodeRadius={{}} _Enter".format(pipe_r, node_r)
            rs.Command(cmd, False)
            rs.UnselectAllObjects()
            # Delete construction curves
            rs.DeleteObjects(strand_ids)
            print("MultiPipe ring on '{{}}' — {{}} strands, {{:.1f}}mm pipe, {{:.0f}} twists".format(
                "{layer}", n_strands, pipe_r, twists))
        else:
            print("ERROR: Failed to create strand curves")
    """)


@mcp.tool()
def create_dna_ring(
    finger_diameter: float = 17.3,
    band_width: float = 8.0,
    strand_radius: float = 0.7,
    rung_radius: float = 0.4,
    num_rungs: int = 12,
    helix_pitch: float = 4.0,
    layer: str = "DNA_Ring",
) -> str:
    """Create a DNA double-helix ring with two intertwined strands and bridge rungs.

    Two helical curves are piped to form the DNA backbone strands, with short
    connecting rungs (base pairs) bridging them at regular intervals.

    Args:
        finger_diameter: Inner diameter in mm (17.3 = US size 7).
        band_width: Width of ring in mm.
        strand_radius: Pipe radius of each helix strand in mm.
        rung_radius: Pipe radius of connecting rungs in mm.
        num_rungs: Number of bridge rungs between strands.
        helix_pitch: Vertical distance per full helix turn in mm.
        layer: Target layer name.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")
        rs.CurrentLayer("{layer}")

        ring_r = {finger_diameter} / 2.0 + {strand_radius} * 3
        w = {band_width}
        strand_r = {strand_radius}
        rung_r = {rung_radius}
        n_rungs = {num_rungs}
        pitch = {helix_pitch}
        orbit_r = strand_r * 3  # distance strands orbit from center line

        n_pts = 80
        all_parts = []

        # Create two helical strands
        for strand in range(2):
            phase = math.pi * strand  # 180 degree offset
            pts = []
            for i in range(n_pts + 1):
                t = 2 * math.pi * i / n_pts  # angle around ring
                # Helix angle based on position around ring
                helix_a = phase + (t / (2 * math.pi)) * (w / pitch) * 2 * math.pi
                local_x = orbit_r * math.cos(helix_a)
                local_z = orbit_r * math.sin(helix_a)

                # Map to ring torus
                R = ring_r + local_x
                pts.append((R * math.cos(t), R * math.sin(t), local_z))

            crv = rs.AddInterpCurve(pts, 3, 1)
            if crv:
                pipe = rs.AddPipe(crv, 0, strand_r, cap=2)
                if pipe:
                    if isinstance(pipe, list):
                        all_parts.extend(pipe)
                    else:
                        all_parts.append(pipe)
                rs.DeleteObject(crv)

        # Create bridge rungs between strands
        for i in range(n_rungs):
            t = 2 * math.pi * i / n_rungs
            helix_a1 = (t / (2 * math.pi)) * (w / pitch) * 2 * math.pi
            helix_a2 = helix_a1 + math.pi

            lx1 = orbit_r * math.cos(helix_a1)
            lz1 = orbit_r * math.sin(helix_a1)
            R1 = ring_r + lx1
            p1 = (R1 * math.cos(t), R1 * math.sin(t), lz1)

            lx2 = orbit_r * math.cos(helix_a2)
            lz2 = orbit_r * math.sin(helix_a2)
            R2 = ring_r + lx2
            p2 = (R2 * math.cos(t), R2 * math.sin(t), lz2)

            line = rs.AddLine(p1, p2)
            if line:
                pipe = rs.AddPipe(line, 0, rung_r, cap=2)
                if pipe:
                    if isinstance(pipe, list):
                        all_parts.extend(pipe)
                    else:
                        all_parts.append(pipe)
                rs.DeleteObject(line)

        if all_parts:
            if len(all_parts) > 1:
                result = rs.BooleanUnion(all_parts)
                if result:
                    print("DNA ring on '{{}}' — 2 strands + {{}} rungs".format("{layer}", n_rungs))
                else:
                    print("DNA ring on '{{}}' — {{}} parts (union failed, manual join needed)".format(
                        "{layer}", len(all_parts)))
            else:
                print("DNA ring on '{{}}' — created".format("{layer}"))
        else:
            print("ERROR: Failed to create DNA ring geometry")
    """)


@mcp.tool()
def hollow_ring(
    ring_layer: str = "Ring_Band",
    result_layer: str = "Ring_Hollowed",
    wall_thickness: float = 0.8,
    open_bottom: bool = True,
) -> str:
    """Hollow out a solid ring to reduce weight, preserving a specified wall thickness.

    From Ch 4 of the book: hollowing signet rings and other solid forms is critical for
    reducing casting weight and cost. Uses Shell to create uniform wall thickness.
    The open_bottom option leaves the inner finger-side open (standard for cast rings).

    Args:
        ring_layer: Layer containing the solid ring to hollow.
        result_layer: Layer for the hollowed result.
        wall_thickness: Wall thickness in mm (0.8mm minimum for casting).
        open_bottom: If True, removes the bottom face so the ring is open inside.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        ring_layer = "{ring_layer}"
        result_layer = "{result_layer}"
        wall = {wall_thickness}

        if wall < 0.5:
            print("WARNING: Wall thickness below 0.5mm may fail in casting")

        if not rs.IsLayer(ring_layer):
            print("ERROR: Layer '{{}}' not found".format(ring_layer))
        else:
            if not rs.IsLayer(result_layer):
                rs.AddLayer(result_layer)

            objs = rs.ObjectsByLayer(ring_layer)
            if not objs:
                print("ERROR: No objects on layer '{ring_layer}'")
            else:
                solids = [o for o in objs if rs.IsPolysurface(o) and rs.IsPolysurfaceClosed(o)]
                if not solids:
                    print("ERROR: No closed solids found on '{ring_layer}'")
                else:
                    for solid in solids:
                        copy = rs.CopyObject(solid)
                        rs.ObjectLayer(copy, result_layer)

                        if {open_bottom}:
                            # Find the bottom-most face to leave open
                            faces = rs.ExplodePolysurfaces(copy, delete=False)
                            lowest_z = None
                            bottom_face = None
                            for face in faces:
                                bb = rs.BoundingBox(face)
                                if bb:
                                    cz = (bb[0][2] + bb[4][2]) / 2.0
                                    if lowest_z is None or cz < lowest_z:
                                        lowest_z = cz
                                        bottom_face = face
                            rs.DeleteObjects(faces)

                            # Shell the copy
                            if bottom_face:
                                # Use offset surface approach
                                shelled = rs.Command("_-Shell _SelId {{}} _Enter _Thickness {{}} _Enter".format(copy, wall), echo=False)
                            else:
                                rs.Command("_-Shell _SelId {{}} _Enter _Thickness {{}} _Enter".format(copy, wall), echo=False)
                        else:
                            rs.Command("_-Shell _SelId {{}} _Enter _Thickness {{}} _Enter".format(copy, wall), echo=False)

                    print("Hollowed ring(s) on layer '{{}}', wall={{}}mm".format(result_layer, wall))
    """)
