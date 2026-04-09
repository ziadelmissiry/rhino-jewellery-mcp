import math
import json
import textwrap
from app import mcp


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
