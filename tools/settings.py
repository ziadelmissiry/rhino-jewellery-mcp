import math
import textwrap
from app import mcp


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


@mcp.tool()
def create_cabochon_setting(
    gem_layer: str = "Gem_Cabochon",
    setting_layer: str = "Setting_Cabochon",
    bezel_height: float = 1.5,
    bezel_thickness: float = 0.4,
    base_thickness: float = 0.8,
) -> str:
    """Create a bezel setting that wraps around a cabochon gem.

    A cabochon bezel is a thin metal wall that wraps the stone's girdle and folds
    over the edge to hold it in place. This is the standard setting for cab stones.
    Reads the gem from gem_layer and builds a matching bezel around it.

    Args:
        gem_layer: Layer containing the cabochon gem.
        setting_layer: Layer for the bezel setting.
        bezel_height: Height of the bezel wall above the girdle in mm.
        bezel_thickness: Thickness of the bezel wall in mm.
        base_thickness: Thickness of the base plate under the stone in mm.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        gem_layer = "{gem_layer}"
        setting_layer = "{setting_layer}"

        if not rs.IsLayer(gem_layer):
            print("ERROR: Gem layer '{{}}' not found".format(gem_layer))
        else:
            if not rs.IsLayer(setting_layer):
                rs.AddLayer(setting_layer)
            rs.CurrentLayer(setting_layer)

            gems = rs.ObjectsByLayer(gem_layer)
            if not gems:
                print("ERROR: No gems on layer '{gem_layer}'")
            else:
                gem = gems[0]
                bb = rs.BoundingBox(gem)
                if not bb:
                    print("ERROR: Cannot get gem bounding box")
                else:
                    cx = (bb[0][0] + bb[6][0]) / 2.0
                    cy = (bb[0][1] + bb[6][1]) / 2.0
                    z_min = bb[0][2]
                    z_max = bb[4][2]
                    gem_w = bb[1][0] - bb[0][0]
                    gem_d = bb[2][1] - bb[0][1]

                    bz_h = {bezel_height}
                    bz_t = {bezel_thickness}
                    base_t = {base_thickness}

                    rx_inner = gem_w / 2.0 + 0.05  # tiny clearance
                    ry_inner = gem_d / 2.0 + 0.05
                    rx_outer = rx_inner + bz_t
                    ry_outer = ry_inner + bz_t

                    # Base plate
                    base_plane = rs.MovePlane(rs.WorldXYPlane(), (cx, cy, z_min - base_t))
                    outer_base = rs.AddEllipse(base_plane, rx_outer, ry_outer)
                    base_srf = rs.ExtrudeCurveStraight(outer_base, (0,0,0), (0,0,base_t))
                    rs.CapPlanarHoles(base_srf)
                    rs.DeleteObject(outer_base)

                    # Bezel wall: outer cylinder - inner cylinder
                    girdle_z = z_min  # approximate girdle at bottom of gem
                    wall_plane = rs.MovePlane(rs.WorldXYPlane(), (cx, cy, girdle_z))

                    outer_crv = rs.AddEllipse(wall_plane, rx_outer, ry_outer)
                    inner_crv = rs.AddEllipse(wall_plane, rx_inner, ry_inner)

                    outer_wall = rs.ExtrudeCurveStraight(outer_crv, (0,0,0), (0,0,bz_h))
                    rs.CapPlanarHoles(outer_wall)
                    inner_wall = rs.ExtrudeCurveStraight(inner_crv, (0,0,0), (0,0,bz_h))
                    rs.CapPlanarHoles(inner_wall)

                    bezel = rs.BooleanDifference(outer_wall, inner_wall)

                    rs.DeleteObjects([outer_crv, inner_crv])
                    print("Cabochon bezel setting on layer '{{}}' — wall={{:.1f}}mm, height={{:.1f}}mm".format(
                        setting_layer, bz_t, bz_h))
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


@mcp.tool()
def create_gallery_wire(
    gem_layer: str = "Ring_Gem",
    gallery_layer: str = "Ring_Gallery",
    wire_diameter: float = 1.0,
    offset_below_girdle: float = 0.5,
) -> str:
    """Create a gallery wire (decorative wire swept around a gemstone's pavilion).

    From Ch 3: the gallery wire is a circular cross-section swept along the shape
    of the gemstone rail at the pavilion level. It must not extend wider than the
    girdle. Standard minimum diameter is 1.0mm for casting.

    Args:
        gem_layer: Layer containing the gemstone.
        gallery_layer: Layer for the gallery wire.
        wire_diameter: Diameter of the gallery wire in mm (min 1.0).
        offset_below_girdle: How far below the girdle to place the wire in mm.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        gem_layer = "{gem_layer}"
        gallery_layer = "{gallery_layer}"

        if not rs.IsLayer(gem_layer):
            print("ERROR: Gem layer '{{}}' not found".format(gem_layer))
        else:
            if not rs.IsLayer(gallery_layer):
                rs.AddLayer(gallery_layer)
            rs.CurrentLayer(gallery_layer)

            gems = rs.ObjectsByLayer(gem_layer)
            if not gems:
                print("ERROR: No gems found")
            else:
                gem = gems[0]
                bb = rs.BoundingBox(gem)
                cx = (bb[0][0] + bb[6][0]) / 2.0
                cy = (bb[0][1] + bb[6][1]) / 2.0
                z_min = bb[0][2]
                z_max = bb[4][2]
                girdle_z = (z_min + z_max) / 2.0
                gem_rx = (bb[1][0] - bb[0][0]) / 2.0
                gem_ry = (bb[2][1] - bb[0][1]) / 2.0

                wire_r = {wire_diameter} / 2.0
                wire_z = girdle_z - {offset_below_girdle}

                # Scale radius inward at pavilion level
                total_h = z_max - z_min
                pavilion_frac = (girdle_z - wire_z) / (total_h / 2.0) if total_h > 0 else 0
                taper = max(0.3, 1.0 - pavilion_frac * 0.6)  # taper inward below girdle
                rail_rx = gem_rx * taper
                rail_ry = gem_ry * taper

                # Rail curve (ellipse at pavilion level)
                rail_plane = rs.MovePlane(rs.WorldXYPlane(), (cx, cy, wire_z))
                if abs(rail_rx - rail_ry) < 0.01:
                    rail = rs.AddCircle(rail_plane, rail_rx)
                else:
                    rail = rs.AddEllipse(rail_plane, rail_rx, rail_ry)

                # Wire cross-section
                cs_plane = rs.PlaneFromNormal((cx + rail_rx, cy, wire_z), (0, 1, 0))
                cs_crv = rs.AddCircle(cs_plane, wire_r)

                # Sweep
                gallery = rs.AddSweep1(rail, [cs_crv])
                if gallery:
                    for g in gallery:
                        rs.CapPlanarHoles(g)
                    print("Gallery wire: {{:.1f}}mm dia on layer '{gallery_layer}'".format(wire_r * 2))
                else:
                    # Fallback: pipe
                    pipe = rs.AddPipe(rail, 0, wire_r)
                    if pipe:
                        print("Gallery wire (pipe): {{:.1f}}mm dia on layer '{gallery_layer}'".format(wire_r * 2))
                    else:
                        print("ERROR: Gallery wire creation failed")

                rs.DeleteObjects([rail, cs_crv])
    """)


@mcp.tool()
def create_trellis_gallery(
    gem_layer: str = "Ring_Gem",
    trellis_layer: str = "Ring_Trellis",
    wire_diameter: float = 0.6,
    num_arches: int = 8,
    arch_height: float = 2.0,
) -> str:
    """Create a trellis (open lattice) gallery under a gemstone setting.

    A trellis gallery replaces a solid under-bezel with an elegant open lattice of
    arched wires, allowing light to enter the stone from below. Each arch is a
    semicircular wire connecting the girdle rail to the base of the setting.

    Args:
        gem_layer: Layer containing the gemstone.
        trellis_layer: Layer for the trellis gallery.
        wire_diameter: Diameter of each trellis wire in mm.
        num_arches: Number of trellis arches around the stone.
        arch_height: Height of arches below the girdle in mm.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        gem_layer = "{gem_layer}"
        trellis_layer = "{trellis_layer}"

        if not rs.IsLayer(gem_layer):
            print("ERROR: Gem layer '{{}}' not found".format(gem_layer))
        else:
            if not rs.IsLayer(trellis_layer):
                rs.AddLayer(trellis_layer)
            rs.CurrentLayer(trellis_layer)

            gems = rs.ObjectsByLayer(gem_layer)
            if not gems:
                print("ERROR: No gems found")
            else:
                gem = gems[0]
                bb = rs.BoundingBox(gem)
                cx = (bb[0][0] + bb[6][0]) / 2.0
                cy = (bb[0][1] + bb[6][1]) / 2.0
                z_min = bb[0][2]
                z_max = bb[4][2]
                girdle_z = (z_min + z_max) / 2.0
                gem_r = max(bb[1][0] - bb[0][0], bb[2][1] - bb[0][1]) / 2.0

                wire_r = {wire_diameter} / 2.0
                n = {num_arches}
                arch_h = {arch_height}

                arches_created = 0
                for i in range(n):
                    angle = 2 * math.pi * i / n

                    # Top point at girdle
                    top_x = cx + gem_r * math.cos(angle)
                    top_y = cy + gem_r * math.sin(angle)
                    top_pt = (top_x, top_y, girdle_z)

                    # Bottom point (at center, below)
                    bot_pt = (cx, cy, girdle_z - arch_h)

                    # Mid point for arch (arcs outward)
                    mid_angle = angle
                    mid_r = gem_r * 0.6
                    mid_x = cx + mid_r * math.cos(mid_angle)
                    mid_y = cy + mid_r * math.sin(mid_angle)
                    mid_pt = (mid_x, mid_y, girdle_z - arch_h * 0.4)

                    # Create arch curve
                    arch_crv = rs.AddInterpCurve([top_pt, mid_pt, bot_pt])
                    if arch_crv:
                        pipe = rs.AddPipe(arch_crv, 0, wire_r)
                        if pipe:
                            arches_created += 1
                        rs.DeleteObject(arch_crv)

                # Base ring at bottom
                base_plane = rs.MovePlane(rs.WorldXYPlane(), (cx, cy, girdle_z - arch_h))
                base_crv = rs.AddCircle(base_plane, gem_r * 0.3)
                base_pipe = rs.AddPipe(base_crv, 0, wire_r)
                rs.DeleteObject(base_crv)

                print("Trellis gallery: {{}} arches on layer '{trellis_layer}'".format(arches_created))
    """)


@mcp.tool()
def create_pave_row(
    band_layer: str = "Ring_Band",
    pave_layer: str = "Pave_Stones",
    stone_diameter: float = 1.5,
    stone_spacing: float = 0.25,
    num_stones: int = 12,
    prong_thickness: float = 0.5,
    prong_height: float = 0.4,
    row_angle_start: float = -60.0,
    row_angle_end: float = 60.0,
) -> str:
    """Create a row of pavé-set stones with shared prongs along a ring band.

    From Ch 3 pavé tolerances: 1.5mm stones spaced 0.25mm apart (range 0.20-0.28mm).
    Prong thickness 0.4-0.6mm, prong height matches stone table (~0.4mm).
    Stones are placed along an arc of the ring with micro-prongs between them.

    Args:
        band_layer: Layer with the ring band.
        pave_layer: Layer for pavé stones and prongs.
        stone_diameter: Stone diameter in mm (1.0-2.0 typical).
        stone_spacing: Gap between stones in mm (0.25 standard).
        num_stones: Number of stones in the row.
        prong_thickness: Prong width in mm (0.4-0.6).
        prong_height: Prong height in mm (~0.4, matches stone table).
        row_angle_start: Angular start of row on ring (degrees).
        row_angle_end: Angular end of row on ring (degrees).
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        band_layer = "{band_layer}"
        pave_layer = "{pave_layer}"

        if not rs.IsLayer(band_layer):
            print("ERROR: Band layer '{{}}' not found".format(band_layer))
        else:
            if not rs.IsLayer(pave_layer):
                rs.AddLayer(pave_layer)
            rs.CurrentLayer(pave_layer)

            # Get ring dimensions
            objs = rs.ObjectsByLayer(band_layer)
            if not objs:
                print("ERROR: No objects on band layer")
            else:
                bb = rs.BoundingBox(objs[0])
                cx = (bb[0][0] + bb[6][0]) / 2.0
                cy = (bb[0][1] + bb[6][1]) / 2.0
                cz = (bb[0][2] + bb[4][2]) / 2.0
                ring_r = max(bb[1][0] - bb[0][0], bb[2][1] - bb[0][1]) / 2.0
                ring_h = bb[4][2] - bb[0][2]

                stone_d = {stone_diameter}
                stone_r = stone_d / 2.0
                spacing = {stone_spacing}
                n_stones = {num_stones}
                prong_t = {prong_thickness}
                prong_h = {prong_height}

                # Place stones along arc
                a_start = math.radians({row_angle_start})
                a_end = math.radians({row_angle_end})

                stones_placed = 0
                prongs_placed = 0

                for i in range(n_stones):
                    t = a_start + (a_end - a_start) * i / max(1, n_stones - 1)

                    # Stone center on outer surface of ring
                    sx = cx + ring_r * math.cos(t)
                    sy = cy + ring_r * math.sin(t)
                    sz = cz + ring_h / 2.0 + stone_r * 0.3  # slightly above surface

                    # Simple round stone (hemisphere approximation)
                    stone_plane = rs.MovePlane(rs.WorldXYPlane(), (sx, sy, sz))
                    stone_crv = rs.AddCircle(stone_plane, stone_r)

                    # Pavilion (cone below)
                    pavilion_depth = stone_r * 0.7
                    pts_pav = [(sx, sy, sz)]
                    n_seg = 12
                    for j in range(n_seg + 1):
                        a = 2 * math.pi * j / n_seg
                        pts_pav.append((sx + stone_r * math.cos(a),
                                       sy + stone_r * math.sin(a), sz))
                    # Just place the circle as the stone representation
                    gem = rs.ExtrudeCurveStraight(stone_crv, (0,0,0), (0,0,-pavilion_depth))
                    if gem:
                        rs.CapPlanarHoles(gem)
                        stones_placed += 1
                    rs.DeleteObject(stone_crv)

                    # Shared prong between this stone and next
                    if i < n_stones - 1:
                        t_next = a_start + (a_end - a_start) * (i + 1) / max(1, n_stones - 1)
                        t_mid = (t + t_next) / 2.0
                        px = cx + ring_r * math.cos(t_mid)
                        py = cy + ring_r * math.sin(t_mid)
                        pz = sz

                        # Small prong bead
                        prong_plane = rs.MovePlane(rs.WorldXYPlane(), (px, py, pz))
                        p_crv = rs.AddCircle(prong_plane, prong_t / 2.0)
                        prong = rs.ExtrudeCurveStraight(p_crv, (0,0,0), (0,0,prong_h))
                        if prong:
                            rs.CapPlanarHoles(prong)
                            prongs_placed += 1
                        rs.DeleteObject(p_crv)

                print("Pave row: {{}} stones ({{:.1f}}mm) + {{}} prongs on '{pave_layer}'".format(
                    stones_placed, stone_d, prongs_placed))
                print("  Spacing: {{:.2f}}mm, prong: {{:.1f}}x{{:.1f}}mm".format(
                    spacing, prong_t, prong_h))
    """)
