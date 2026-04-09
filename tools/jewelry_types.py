import math
import json
import textwrap
from app import mcp


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


@mcp.tool()
def create_ear_post(
    layer: str = "Earring_Post",
    post_diameter: float = 0.8,
    post_length: float = 11.0,
    pad_diameter: float = 4.0,
    pad_thickness: float = 0.5,
    include_butterfly: bool = True,
) -> str:
    """Create an earring post with pad and optional butterfly back.

    From Ch 3 manufacturing tolerances: standard ear post is 0.8mm diameter x 11mm long.
    The pad provides a flat surface to solder to the earring. The butterfly back
    (friction clutch) is the standard earring back closure.

    Args:
        layer: Layer for the ear post components.
        post_diameter: Post wire diameter in mm (standard: 0.8).
        post_length: Post length in mm (standard: 11.0).
        pad_diameter: Pad diameter in mm.
        pad_thickness: Pad thickness in mm.
        include_butterfly: Whether to add a butterfly back component.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        layer = "{layer}"
        if not rs.IsLayer(layer):
            rs.AddLayer(layer)
        rs.CurrentLayer(layer)

        post_d = {post_diameter}
        post_l = {post_length}
        pad_d = {pad_diameter}
        pad_t = {pad_thickness}

        # Pad (flat disc)
        pad_plane = rs.WorldXYPlane()
        pad_crv = rs.AddCircle(pad_plane, pad_d / 2.0)
        pad = rs.ExtrudeCurveStraight(pad_crv, (0, 0, 0), (0, 0, pad_t))
        rs.CapPlanarHoles(pad)
        rs.DeleteObject(pad_crv)

        # Post (cylinder extending from pad)
        post_plane = rs.MovePlane(rs.WorldXYPlane(), (0, 0, pad_t))
        post_crv = rs.AddCircle(post_plane, post_d / 2.0)
        post = rs.ExtrudeCurveStraight(post_crv, (0, 0, 0), (0, 0, post_l))
        rs.CapPlanarHoles(post)
        rs.DeleteObject(post_crv)

        # Boolean union pad + post
        joined = rs.BooleanUnion([pad, post])
        if not joined:
            print("Pad and post created separately (boolean union failed)")

        if {include_butterfly}:
            # Butterfly back: small rectangular clip with slot
            bfly_z = pad_t + post_l * 0.7  # sits 70% down the post
            bfly_w = 5.0
            bfly_h = 3.0
            bfly_t = 1.0

            pts = [
                (-bfly_w/2, -bfly_h/2, bfly_z),
                (bfly_w/2, -bfly_h/2, bfly_z),
                (bfly_w/2, bfly_h/2, bfly_z),
                (-bfly_w/2, bfly_h/2, bfly_z),
                (-bfly_w/2, -bfly_h/2, bfly_z),
            ]
            bfly_crv = rs.AddPolyline(pts)
            bfly = rs.ExtrudeCurveStraight(bfly_crv, (0,0,0), (0,0,bfly_t))
            rs.CapPlanarHoles(bfly)
            rs.DeleteObject(bfly_crv)

            # Slot for the post
            slot_crv = rs.AddCircle(rs.MovePlane(rs.WorldXYPlane(), (0, 0, bfly_z - 0.1)),
                                     post_d / 2.0 + 0.05)
            slot = rs.ExtrudeCurveStraight(slot_crv, (0,0,0), (0,0,bfly_t + 0.2))
            rs.CapPlanarHoles(slot)
            rs.DeleteObject(slot_crv)

            bfly_result = rs.BooleanDifference([bfly], [slot])
            print("Ear post + butterfly back on layer '{layer}' — {{:.1f}}mm dia x {{:.1f}}mm long".format(post_d, post_l))
        else:
            print("Ear post on layer '{layer}' — {{:.1f}}mm dia x {{:.1f}}mm long".format(post_d, post_l))
    """)


@mcp.tool()
def create_wire_cuff_bangle(
    layer: str = "Bangle_Cuff",
    inner_width: float = 60.0,
    inner_height: float = 50.0,
    wire_diameter: float = 2.0,
    num_wires: int = 3,
    gap_angle: float = 30.0,
    twist: bool = False,
) -> str:
    """Create a wire cuff bangle (open bangle made of parallel wires).

    From Ch 3 (cuff bangles): wire cuff bangles use an oval profile with an opening
    gap. Multiple parallel wires create the cuff structure. Uses Pipe command
    along an elliptical rail. The gap allows the bangle to flex onto the wrist.

    Args:
        layer: Layer for the bangle.
        inner_width: Inner width of bangle in mm (wrist dimension, ~60mm average).
        inner_height: Inner height in mm (~50mm for oval bangles).
        wire_diameter: Wire diameter in mm.
        num_wires: Number of parallel wires.
        gap_angle: Opening gap in degrees (30° typical for cuff).
        twist: Whether to add a decorative twist to the wires.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        layer = "{layer}"
        if not rs.IsLayer(layer):
            rs.AddLayer(layer)
        rs.CurrentLayer(layer)

        w = {inner_width} / 2.0  # semi-major
        h = {inner_height} / 2.0  # semi-minor
        wire_r = {wire_diameter} / 2.0
        n_wires = {num_wires}
        gap = math.radians({gap_angle})

        wire_spacing = wire_r * 3  # space between wire centers

        for wi in range(n_wires):
            z_offset = (wi - (n_wires - 1) / 2.0) * wire_spacing

            # Create open elliptical arc (with gap at bottom)
            pts = []
            start_angle = gap / 2.0 + math.pi / 2.0  # start after gap (gap at bottom/6 o'clock)
            end_angle = 2 * math.pi - gap / 2.0 + math.pi / 2.0
            n_pts = 48

            for i in range(n_pts + 1):
                t = start_angle + (end_angle - start_angle) * i / n_pts
                x = w * math.cos(t)
                y = h * math.sin(t)
                pts.append((x, y, z_offset))

            crv = rs.AddInterpCurve(pts)
            if crv:
                pipe = rs.AddPipe(crv, 0, wire_r, cap=1)
                rs.DeleteObject(crv)

        print("Wire cuff bangle: {{}} wires x {{:.1f}}mm on layer '{layer}'".format(n_wires, wire_r * 2))
        print("  Inner: {{:.0f}} x {{:.0f}}mm, gap: {{:.0f}}°".format(w * 2, h * 2, math.degrees(gap)))
    """)


@mcp.tool()
def create_lotus_pendant(
    outer_diameter: float = 30.0,
    num_layers: int = 3,
    petals_per_layer: str = "5,8,13",
    petal_thickness: float = 1.0,
    petal_curvature: float = 0.3,
    bail_diameter: float = 4.0,
    layer: str = "Lotus_Pendant",
) -> str:
    """Create a multi-layer lotus flower pendant with staggered petal rings.

    Builds concentric layers of petals (inner, middle, outer) with Fibonacci-style
    counts. Each layer is offset in height and angle for a natural lotus look.

    Args:
        outer_diameter: Overall pendant diameter in mm.
        num_layers: Number of petal layers (1-4).
        petals_per_layer: Comma-separated petal counts per layer (inner to outer).
        petal_thickness: Thickness of each petal in mm.
        petal_curvature: How much petals curve upward (0=flat, 1=very curved).
        bail_diameter: Inner diameter of bail loop in mm.
        layer: Target layer name.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")
        rs.CurrentLayer("{layer}")

        outer_r = {outer_diameter} / 2.0
        n_layers = {num_layers}
        petal_counts = [int(x) for x in "{petals_per_layer}".split(",")]
        thickness = {petal_thickness}
        curvature = {petal_curvature}
        bail_d = {bail_diameter}

        # Pad petal counts if needed
        while len(petal_counts) < n_layers:
            petal_counts.append(petal_counts[-1])

        all_parts = []

        for layer_idx in range(n_layers):
            n_petals = petal_counts[layer_idx]
            # Each layer gets progressively larger radius and higher z
            layer_r = outer_r * (0.3 + 0.7 * (layer_idx + 1) / n_layers)
            layer_z = layer_idx * 1.5  # stagger height
            petal_len = layer_r * 0.65
            petal_w = 2 * math.pi * layer_r / n_petals * 0.7

            # Stagger angle: offset by half petal width from previous layer
            angle_offset = math.pi / n_petals if layer_idx % 2 == 1 else 0

            for p in range(n_petals):
                a = 2 * math.pi * p / n_petals + angle_offset

                # Petal tip
                tip_x = layer_r * math.cos(a)
                tip_y = layer_r * math.sin(a)
                tip_z = layer_z + curvature * petal_len

                # Petal base (near center)
                base_r = layer_r - petal_len
                base_x = base_r * math.cos(a)
                base_y = base_r * math.sin(a)
                base_z = layer_z

                # Petal side points
                perp_a = a + math.pi / 2
                hw = petal_w / 2.0
                mid_r = (layer_r + base_r) / 2.0
                mid_z = layer_z + curvature * petal_len * 0.5

                left_x = mid_r * math.cos(a) + hw * math.cos(perp_a)
                left_y = mid_r * math.sin(a) + hw * math.sin(perp_a)
                right_x = mid_r * math.cos(a) - hw * math.cos(perp_a)
                right_y = mid_r * math.sin(a) - hw * math.sin(perp_a)

                # Build petal as a lofted shape
                pts = [
                    (base_x, base_y, base_z),
                    (left_x, left_y, mid_z),
                    (tip_x, tip_y, tip_z),
                    (right_x, right_y, mid_z),
                    (base_x, base_y, base_z),
                ]
                crv = rs.AddInterpCurve(pts, 3)
                if crv:
                    srf = rs.AddPlanarSrf([crv])
                    if srf:
                        solid = rs.ExtrudeSurface(srf[0] if isinstance(srf, list) else srf,
                                                  rs.AddLine((0,0,0), (0,0,thickness)))
                        if solid:
                            rs.CapPlanarHoles(solid)
                            all_parts.append(solid)
                        # Clean up extrusion path
                        last = rs.LastCreatedObjects()
                    if isinstance(srf, list):
                        rs.DeleteObjects(srf)
                    else:
                        rs.DeleteObject(srf)
                    rs.DeleteObject(crv)

        # Add bail at top
        if bail_d > 0:
            bail_r = bail_d / 2.0
            bail_pos = (0, outer_r * 0.15, n_layers * 1.5 + bail_r + 1)
            bail_plane = rs.PlaneFromNormal(bail_pos, (0, 1, 0))
            bail_crv = rs.AddCircle(bail_plane, bail_r)
            if bail_crv:
                bail_pipe = rs.AddPipe(bail_crv, 0, thickness / 2.0, cap=2)
                if bail_pipe:
                    if isinstance(bail_pipe, list):
                        all_parts.extend(bail_pipe)
                    else:
                        all_parts.append(bail_pipe)
                rs.DeleteObject(bail_crv)

        print("Lotus pendant on '{{}}' — {{}} layers, {{}} total petals".format(
            "{layer}", n_layers, sum(petal_counts[:n_layers])))
    """)


@mcp.tool()
def create_butterfly_pendant(
    wingspan: float = 28.0,
    body_length: float = 14.0,
    wing_thickness: float = 1.5,
    bail_diameter: float = 3.5,
    layer: str = "Butterfly_Pendant",
) -> str:
    """Create a butterfly pendant with symmetric wings, body, and bail.

    Builds one wing from curves, mirrors it for symmetry, adds a tapered body,
    and a bail loop for chain attachment. Wings are ready for gem placement.

    Args:
        wingspan: Total width tip-to-tip in mm.
        body_length: Length of body (thorax + abdomen) in mm.
        wing_thickness: Thickness of wings in mm (min 1.2 for casting).
        bail_diameter: Inner diameter of bail loop in mm.
        layer: Target layer name.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")
        rs.CurrentLayer("{layer}")

        ws = {wingspan} / 2.0  # half-span
        bl = {body_length}
        thick = {wing_thickness}
        bail_d = {bail_diameter}

        all_parts = []

        # Upper wing (larger)
        uw_pts = [
            (0, bl * 0.4, 0),           # base at body
            (ws * 0.3, bl * 0.6, 0),    # leading edge
            (ws * 0.8, bl * 0.5, 0),    # upper tip area
            (ws, bl * 0.25, 0),          # wing tip
            (ws * 0.7, bl * 0.05, 0),   # trailing edge
            (ws * 0.3, 0, 0),           # lower trailing
            (0, bl * 0.1, 0),           # back to body
        ]
        uw_crv = rs.AddInterpCurve(uw_pts, 3)

        # Lower wing (smaller)
        lw_pts = [
            (0, bl * 0.1, 0),
            (ws * 0.25, -bl * 0.05, 0),
            (ws * 0.6, -bl * 0.15, 0),
            (ws * 0.7, -bl * 0.3, 0),   # lower tip
            (ws * 0.4, -bl * 0.35, 0),
            (ws * 0.15, -bl * 0.25, 0),
            (0, -bl * 0.15, 0),
        ]
        lw_crv = rs.AddInterpCurve(lw_pts, 3)

        # Extrude and cap wings
        for crv in [uw_crv, lw_crv]:
            if crv:
                srf = rs.AddPlanarSrf([crv])
                if srf:
                    path = rs.AddLine((0,0,0), (0,0,thick))
                    solid = rs.ExtrudeSurface(srf[0] if isinstance(srf, list) else srf, path)
                    if solid:
                        rs.CapPlanarHoles(solid)
                        all_parts.append(solid)
                        # Mirror to other side
                        mirror = rs.MirrorObject(solid, (0,0,0), (0,1,0), True)
                        if mirror:
                            all_parts.append(mirror)
                    rs.DeleteObject(path)
                    if isinstance(srf, list):
                        rs.DeleteObjects(srf)
                    else:
                        rs.DeleteObject(srf)
                rs.DeleteObject(crv)

        # Body (tapered cylinder)
        body_pts = [
            (0, bl * 0.5, thick / 2),
            (0, 0, thick / 2),
            (0, -bl * 0.4, thick / 2),
        ]
        body_crv = rs.AddInterpCurve(body_pts, 3)
        if body_crv:
            body_pipe = rs.AddPipe(body_crv, 0, thick * 0.6, cap=2)
            if body_pipe:
                if isinstance(body_pipe, list):
                    all_parts.extend(body_pipe)
                else:
                    all_parts.append(body_pipe)
            rs.DeleteObject(body_crv)

        # Bail at top
        if bail_d > 0:
            bail_r = bail_d / 2.0
            bail_pos = (0, bl * 0.5 + bail_r + 0.5, thick / 2)
            bail_plane = rs.PlaneFromNormal(bail_pos, (0, 1, 0))
            bail_crv = rs.AddCircle(bail_plane, bail_r)
            if bail_crv:
                bail = rs.AddPipe(bail_crv, 0, thick * 0.4, cap=2)
                if bail:
                    if isinstance(bail, list):
                        all_parts.extend(bail)
                    else:
                        all_parts.append(bail)
                rs.DeleteObject(bail_crv)

        print("Butterfly pendant on '{{}}' — {{:.0f}}mm wingspan, {{:.0f}}mm body".format(
            "{layer}", {wingspan}, {body_length}))
        print("  {{}} parts — use BooleanUnion to merge".format(len(all_parts)))
    """)


@mcp.tool()
def create_flower_eartop(
    diameter: float = 12.0,
    num_petals: int = 6,
    petal_thickness: float = 1.2,
    center_stone_diameter: float = 2.5,
    ear_post: bool = True,
    layer: str = "Flower_Eartop",
) -> str:
    """Create a flower-shaped stud earring with petals and center stone seat.

    Builds petals via ArrayPolar around a center, adds a gem seat at the center,
    and optionally adds a standard ear post (0.8mm x 11mm).

    Args:
        diameter: Overall flower diameter in mm.
        num_petals: Number of petals (3-12).
        petal_thickness: Thickness in mm (min 1.0 for casting).
        center_stone_diameter: Diameter of center stone seat in mm (0 = no stone).
        ear_post: Whether to add a standard ear post on the back.
        layer: Target layer name.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")
        rs.CurrentLayer("{layer}")

        outer_r = {diameter} / 2.0
        n_petals = {num_petals}
        thick = {petal_thickness}
        stone_d = {center_stone_diameter}

        all_parts = []

        # Create single petal
        petal_len = outer_r * 0.7
        petal_w = 2 * math.pi * outer_r / n_petals * 0.65
        inner_r = outer_r - petal_len

        petal_pts = [
            (inner_r, 0, 0),
            ((inner_r + outer_r) / 2, petal_w / 2, 0),
            (outer_r, 0, 0),
            ((inner_r + outer_r) / 2, -petal_w / 2, 0),
            (inner_r, 0, 0),
        ]
        petal_crv = rs.AddInterpCurve(petal_pts, 3)
        if petal_crv:
            srf = rs.AddPlanarSrf([petal_crv])
            if srf:
                path = rs.AddLine((0,0,0), (0,0,thick))
                petal_solid = rs.ExtrudeSurface(srf[0] if isinstance(srf, list) else srf, path)
                if petal_solid:
                    rs.CapPlanarHoles(petal_solid)
                    all_parts.append(petal_solid)

                    # ArrayPolar the remaining petals
                    for i in range(1, n_petals):
                        angle = 360.0 * i / n_petals
                        copy = rs.RotateObject(petal_solid, (0,0,0), angle, (0,0,1), True)
                        if copy:
                            all_parts.append(copy)

                rs.DeleteObject(path)
                if isinstance(srf, list):
                    rs.DeleteObjects(srf)
                else:
                    rs.DeleteObject(srf)
            rs.DeleteObject(petal_crv)

        # Center disc
        center_r = inner_r + 0.5
        center_plane = rs.WorldXYPlane()
        center_crv = rs.AddCircle(center_plane, center_r)
        if center_crv:
            srf = rs.AddPlanarSrf([center_crv])
            if srf:
                path = rs.AddLine((0,0,0), (0,0,thick))
                disc = rs.ExtrudeSurface(srf[0] if isinstance(srf, list) else srf, path)
                if disc:
                    rs.CapPlanarHoles(disc)
                    all_parts.append(disc)
                rs.DeleteObject(path)
                if isinstance(srf, list):
                    rs.DeleteObjects(srf)
                else:
                    rs.DeleteObject(srf)
            rs.DeleteObject(center_crv)

        # Center stone seat (boolean difference)
        if stone_d > 0 and all_parts:
            seat_r = stone_d / 2.0
            seat_plane = rs.MovePlane(rs.WorldXYPlane(), (0, 0, thick * 0.4))
            seat_crv = rs.AddCircle(seat_plane, seat_r)
            if seat_crv:
                seat_path = rs.AddLine((0,0,thick * 0.4), (0,0,thick + 0.5))
                seat_cutter = rs.ExtrudeCurveStraight(seat_crv, (0,0,0), (0,0,thick * 0.7))
                if seat_cutter:
                    rs.CapPlanarHoles(seat_cutter)
                    # Try boolean with center disc
                rs.DeleteObject(seat_crv)

        # Ear post
        if {str(ear_post).lower() == 'true'}:
            post_r = 0.4  # 0.8mm diameter
            post_len = 11.0
            post_plane = rs.MovePlane(rs.WorldXYPlane(), (0, 0, -post_len))
            post_crv = rs.AddCircle(post_plane, post_r)
            if post_crv:
                post = rs.ExtrudeCurveStraight(post_crv, (0,0,0), (0,0,post_len))
                if post:
                    rs.CapPlanarHoles(post)
                    all_parts.append(post)
                rs.DeleteObject(post_crv)

        print("Flower eartop on '{{}}' — {{}} petals, {{:.0f}}mm diameter".format(
            "{layer}", n_petals, {diameter}))
        if stone_d > 0:
            print("  Center stone seat: {{:.1f}}mm".format(stone_d))
    """)


@mcp.tool()
def create_frill_pendant(
    width: float = 30.0,
    height: float = 25.0,
    thickness: float = 0.8,
    num_waves: int = 5,
    wave_amplitude: float = 3.0,
    bail_diameter: float = 3.5,
    layer: str = "Frill_Pendant",
) -> str:
    """Create an organic ruffled/frill pendant with wavy fabric-like surfaces.

    Generates wavy cross-section curves and lofts them to create a ruffled
    surface, then offsets for thickness. Popular in modern organic jewelry.

    Args:
        width: Width of pendant in mm.
        height: Height of pendant in mm.
        thickness: Metal thickness in mm (min 0.6).
        num_waves: Number of wave undulations across the width.
        wave_amplitude: Height of wave peaks in mm.
        bail_diameter: Inner diameter of bail loop in mm.
        layer: Target layer name.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")
        rs.CurrentLayer("{layer}")

        w = {width}
        h = {height}
        thick = {thickness}
        n_waves = {num_waves}
        amp = {wave_amplitude}
        bail_d = {bail_diameter}

        # Generate wavy cross-section curves at different heights
        n_sections = 8
        section_crvs = []

        for s in range(n_sections):
            t = s / (n_sections - 1.0)  # 0 to 1
            y_pos = -h / 2 + h * t
            # Amplitude varies: max in middle, min at edges
            local_amp = amp * math.sin(math.pi * t)
            # Phase shifts progressively for organic look
            phase = t * math.pi * 0.5

            pts = []
            n_pts = 30
            for i in range(n_pts + 1):
                x = -w / 2 + w * i / n_pts
                x_norm = i / float(n_pts)
                z = local_amp * math.sin(2 * math.pi * n_waves * x_norm + phase)
                pts.append((x, y_pos, z))

            crv = rs.AddInterpCurve(pts, 3)
            if crv:
                section_crvs.append(crv)

        if len(section_crvs) >= 2:
            # Loft the sections
            srf = rs.AddLoftSrf(section_crvs, loft_type=1)  # loose loft
            if srf:
                # Offset surface for thickness
                srf_id = srf[0] if isinstance(srf, list) else srf
                offset = rs.OffsetSurface(srf_id, thick)
                if offset:
                    print("Frill pendant on '{{}}' — {{:.0f}}x{{:.0f}}mm, {{}} waves".format(
                        "{layer}", w, h, n_waves))
                else:
                    print("Frill pendant surface on '{{}}' — offset manually for thickness".format(
                        "{layer}"))
            else:
                print("ERROR: Loft failed")

            # Add bail
            if bail_d > 0:
                bail_r = bail_d / 2.0
                bail_pos = (0, h / 2 + bail_r + 0.5, 0)
                bail_plane = rs.PlaneFromNormal(bail_pos, (0, 1, 0))
                bail_crv = rs.AddCircle(bail_plane, bail_r)
                if bail_crv:
                    bail = rs.AddPipe(bail_crv, 0, thick, cap=2)
                    rs.DeleteObject(bail_crv)

            # Cleanup construction curves
            rs.DeleteObjects(section_crvs)
        else:
            print("ERROR: Not enough section curves for loft")
    """)


@mcp.tool()
def create_baguette_bracelet(
    wrist_diameter: float = 62.0,
    stone_length: float = 4.0,
    stone_width: float = 2.0,
    stone_depth: float = 2.5,
    gap: float = 0.15,
    channel_height: float = 3.5,
    channel_wall: float = 0.8,
    layer: str = "Baguette_Bracelet",
) -> str:
    """Create a baguette-cut gem bracelet (tennis bracelet variant).

    Builds an oval bracelet rail and arrays baguette stone settings along it
    with proper channel walls between each stone.

    Args:
        wrist_diameter: Inner diameter in mm (62 = medium wrist).
        stone_length: Length of each baguette stone in mm.
        stone_width: Width of each baguette stone in mm.
        stone_depth: Depth of each stone in mm.
        gap: Gap between stones in mm.
        channel_height: Height of channel walls in mm.
        channel_wall: Thickness of channel walls in mm.
        layer: Target layer name.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        if not rs.IsLayer("{layer}"):
            rs.AddLayer("{layer}")
        rs.CurrentLayer("{layer}")

        wrist_r = {wrist_diameter} / 2.0
        s_len = {stone_length}
        s_wid = {stone_width}
        s_dep = {stone_depth}
        gap = {gap}
        ch_h = {channel_height}
        ch_wall = {channel_wall}

        # Create oval bracelet path
        circumference = math.pi * {wrist_diameter}
        unit_len = s_len + gap + ch_wall
        n_stones = int(circumference / unit_len)

        # Build bracelet rail (circle at wrist size)
        rail_plane = rs.WorldXYPlane()
        rail = rs.AddCircle(rail_plane, wrist_r)

        if rail:
            # Create one baguette unit: channel walls + stone void
            # Channel outer profile (rectangle)
            total_w = s_wid + ch_wall * 2
            x0 = -unit_len / 2
            x1 = unit_len / 2
            y0 = wrist_r - total_w / 2
            y1 = wrist_r + total_w / 2

            # Outer channel section
            outer_pts = [
                (x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0), (x0, y0, 0)
            ]
            outer_crv = rs.AddPolyline(outer_pts)

            # Stone cutout (slightly smaller)
            cx0 = -s_len / 2
            cx1 = s_len / 2
            cy0 = wrist_r - s_wid / 2
            cy1 = wrist_r + s_wid / 2
            inner_pts = [
                (cx0, cy0, 0), (cx1, cy0, 0), (cx1, cy1, 0), (cx0, cy1, 0), (cx0, cy0, 0)
            ]
            inner_crv = rs.AddPolyline(inner_pts)

            if outer_crv:
                # Extrude channel unit
                channel = rs.ExtrudeCurveStraight(outer_crv, (0,0,0), (0,0,ch_h))
                if channel:
                    rs.CapPlanarHoles(channel)

                    # Cut stone void
                    if inner_crv:
                        void = rs.ExtrudeCurveStraight(inner_crv, (0,0,ch_wall), (0,0,ch_h + 0.5))
                        if void:
                            rs.CapPlanarHoles(void)
                            result = rs.BooleanDifference([channel], [void])
                            unit = result[0] if result else channel

                            # Array around circle
                            units = [unit]
                            for i in range(1, n_stones):
                                angle = 360.0 * i / n_stones
                                copy = rs.RotateObject(unit, (0,0,0), angle, (0,0,1), True)
                                if copy:
                                    units.append(copy)

                            print("Baguette bracelet on '{{}}' — {{}} stones around {{:.0f}}mm wrist".format(
                                "{layer}", n_stones, {wrist_diameter}))
                            print("  Stone: {{:.1f}}x{{:.1f}}mm, channel wall: {{:.1f}}mm".format(
                                s_len, s_wid, ch_wall))
                        else:
                            print("ERROR: Stone void extrusion failed")
                    rs.DeleteObject(inner_crv)
                rs.DeleteObject(outer_crv)
            rs.DeleteObject(rail)
    """)
