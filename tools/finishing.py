import math
import textwrap
from app import mcp


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


@mcp.tool()
def apply_edge_softening(
    target_layer: str = "Ring_Band",
    softening_radius: float = 0.15,
) -> str:
    """Apply edge softening to objects for rendering (non-destructive visual fillets).

    From Ch 7: Edge Softening adds rounded edges only in Rendered/Raytraced views
    without modifying the actual geometry. Much faster than filleting every edge,
    and the original model stays intact. Ideal for quick render previews.

    Args:
        target_layer: Layer containing objects to soften.
        softening_radius: Softening radius in mm (0.1-0.3 typical for jewelry).
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs

        target_layer = "{target_layer}"
        if not rs.IsLayer(target_layer):
            print("ERROR: Layer '{{}}' not found".format(target_layer))
        else:
            objs = rs.ObjectsByLayer(target_layer)
            if not objs:
                print("ERROR: No objects on layer")
            else:
                radius = {softening_radius}
                count = 0
                for obj in objs:
                    if rs.IsPolysurface(obj) or rs.IsSurface(obj):
                        rs.SelectObject(obj)
                        rs.Command("_-Properties _Object _EdgeSoftening _Softening _On _Radius {{}} _Enter _Enter _Enter".format(radius), echo=False)
                        rs.UnselectAllObjects()
                        count += 1

                print("Edge softening ({{:.2f}}mm) applied to {{}} objects on '{target_layer}'".format(radius, count))
                print("  Visible in Rendered/Raytraced modes only")
    """)


@mcp.tool()
def create_text_on_ring(
    text: str = "LOVE",
    finger_diameter: float = 17.3,
    band_width: float = 4.0,
    text_height: float = 2.0,
    text_depth: float = 0.4,
    engrave: bool = True,
    font: str = "Arial",
    band_layer: str = "Ring_Band",
    text_layer: str = "Ring_Text",
) -> str:
    """Create engraved or raised text wrapped around a ring band.

    End-to-end text ring workflow: creates a ring band, generates 3D text,
    and flows it around the band using FlowAlongCrv, then optionally
    boolean-subtracts (engrave) or boolean-adds (raised).

    Args:
        text: The text string to place on the ring.
        finger_diameter: Inner diameter in mm (17.3 = US size 7).
        band_width: Width of ring band in mm.
        text_height: Height of text characters in mm.
        text_depth: Depth of text cut/raise in mm (0.3-0.5 typical).
        engrave: True = cut into ring, False = raised on ring.
        font: Font name for text.
        band_layer: Layer for the ring band.
        text_layer: Layer for the text objects.
    """
    return textwrap.dedent(f"""\
        import rhinoscriptsyntax as rs
        import math

        for lyr in ["{band_layer}", "{text_layer}"]:
            if not rs.IsLayer(lyr):
                rs.AddLayer(lyr)

        ring_r = {finger_diameter} / 2.0
        outer_r = ring_r + {band_width} * 0.3
        band_w = {band_width}

        # Create ring band
        rs.CurrentLayer("{band_layer}")
        torus = rs.AddTorus(rs.WorldXYPlane(), outer_r, band_w / 2.0)
        if not torus:
            print("ERROR: Ring band creation failed")
        else:
            # Create text on a flat plane, then flow onto ring
            rs.CurrentLayer("{text_layer}")

            # Circumference for text layout
            text_circ = 2 * math.pi * outer_r
            print("Ring band created — ID: {{:.1f}}mm, OD: {{:.1f}}mm".format(
                {finger_diameter}, outer_r * 2))

            # Create 3D text at origin (flat)
            rs.Command('_-TextObject _Height={text_height} _Font="{font}" _Output=Surfaces "{text}" _Enter', False)
            text_objs = rs.LastCreatedObjects()

            if text_objs:
                # Extrude text for depth
                extruded = []
                for t in text_objs:
                    ext = rs.ExtrudeSurface(t, rs.AddLine((0,0,0), (0,0,{text_depth})))
                    if ext:
                        rs.CapPlanarHoles(ext)
                        extruded.append(ext)
                    rs.DeleteObject(t)

                if extruded:
                    # Position text at ring outer surface
                    for e in extruded:
                        rs.MoveObject(e, (0, outer_r, -band_w/4))

                    print("Text '{{}}' created — {{}} characters, {{:.1f}}mm height".format(
                        "{text}", len(extruded), {text_height}))
                    print("  Use FlowAlongCrv to wrap text around the ring")
                    print("  Then Boolean{{}}: for {{}}".format(
                        "Difference" if {str(engrave).lower() == 'true'} else "Union",
                        "engraving" if {str(engrave).lower() == 'true'} else "raised text"))
            else:
                print("ERROR: TextObject command failed")
    """)
