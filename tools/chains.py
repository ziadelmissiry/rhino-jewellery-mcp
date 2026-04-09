import math
import textwrap
from app import mcp


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


@mcp.tool()
def create_hinge_mechanism(
    layer: str = "Hinge",
    hinge_outer_diameter: float = 3.0,
    pin_diameter: float = 1.0,
    hinge_length: float = 6.0,
    num_knuckles: int = 3,
    clearance: float = 0.1,
) -> str:
    """Create a barrel hinge mechanism for bracelets, bangles, or lockets.

    From Ch 3: hinges use interlocking barrel knuckles with a pin hole drilled through.
    The pin hole is intentionally undersized (drilled out later in manufacturing).
    Knuckles alternate between the two sides of the hinge.

    Args:
        layer: Layer for the hinge components.
        hinge_outer_diameter: Outer diameter of hinge barrel in mm.
        pin_diameter: Pin hole diameter in mm (undersized for manufacturing).
        hinge_length: Total length of the hinge barrel in mm.
        num_knuckles: Number of knuckle segments (odd number, typically 3 or 5).
        clearance: Gap between knuckles in mm.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        layer = "{layer}"
        if not rs.IsLayer(layer):
            rs.AddLayer(layer)
        rs.CurrentLayer(layer)

        outer_r = {hinge_outer_diameter} / 2.0
        pin_r = {pin_diameter} / 2.0
        total_len = {hinge_length}
        n_knuckles = {num_knuckles}
        clearance = {clearance}

        knuckle_len = (total_len - clearance * (n_knuckles - 1)) / n_knuckles

        side_a = []
        side_b = []

        for i in range(n_knuckles):
            z_start = i * (knuckle_len + clearance)

            # Outer cylinder
            plane = rs.MovePlane(rs.WorldXYPlane(), (0, 0, z_start))
            outer_crv = rs.AddCircle(plane, outer_r)
            knuckle = rs.ExtrudeCurveStraight(outer_crv, (0,0,0), (0,0,knuckle_len))
            rs.CapPlanarHoles(knuckle)
            rs.DeleteObject(outer_crv)

            # Pin hole
            pin_crv = rs.AddCircle(plane, pin_r)
            pin_cutter = rs.ExtrudeCurveStraight(pin_crv, (0,0,0), (0,0,knuckle_len))
            rs.CapPlanarHoles(pin_cutter)
            rs.DeleteObject(pin_crv)

            result = rs.BooleanDifference([knuckle], [pin_cutter])

            if i % 2 == 0:
                side_a.append(result[0] if result else knuckle)
            else:
                side_b.append(result[0] if result else knuckle)

        print("Hinge: {{}} knuckles, {{:.1f}}mm OD, {{:.1f}}mm pin on layer '{layer}'".format(
            n_knuckles, outer_r * 2, pin_r * 2))
        print("  Side A: {{}} knuckles, Side B: {{}} knuckles".format(len(side_a), len(side_b)))
    """)
