import bpy


def load_blend(src):
    """Load a .blend file into the current blender session.

    Note: This can cause context issues, so use with caution. If possible, use `blendersynth.run_this_script` instead.
    """

    def fix_context():
        """Fix bpy.context if some command (like .blend import) changed/emptied it"""
        for window in bpy.context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                if area.type == "VIEW_3D":
                    for region in area.regions:
                        if region.type == "WINDOW":
                            override = {
                                "window": window,
                                "screen": screen,
                                "area": area,
                                "region": region,
                            }
                            bpy.ops.screen.screen_full_area(override)
                            break

    f = bpy.ops.wm.open_mainfile(filepath=src)
    fix_context()
    return f
