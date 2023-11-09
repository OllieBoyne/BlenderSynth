import bpy

AREA_TYPES = [
    "VIEW_3D",
    "IMAGE_EDITOR",
    "NODE_EDITOR",
    "SEQUENCE_EDITOR",
    "CLIP_EDITOR",
    "DOPESHEET_EDITOR",
    "GRAPH_EDITOR",
    "NLA_EDITOR",
    "TEXT_EDITOR",
    "CONSOLE",
    "INFO",
    "TOPBAR",
    "STATUSBAR",
    "OUTLINER",
    "PROPERTIES",
    "FILE_BROWSER",
    "SPREADSHEET",
    "PREFERENCES",
]
"""List of all area types"""


def get_areas(area_type):
    """Yield all areas of the given type.

    :param area_type: Area type to get (one of :attr:`~blendersynth.utils.layout.AREA_TYPES`)
    """
    assert area_type in AREA_TYPES, f"Invalid area type: {area_type}"

    for area in bpy.context.screen.areas:
        if area.type == area_type:
            yield area


def get_area(area_type) -> bpy.types.Area:
    """Return the first found area of the given type.

    :param area_type: Area type to get (one of :attr:`~blendersynth.utils.layout.AREA_TYPES`)
    """
    for area in get_areas(area_type):
        return area


def change_area_to(area_type_from: str, area_type_to: str):
    """Change the first area found.

    :param area_type_from: Area type to change from (one of :attr:`~blendersynth.utils.layout.AREA_TYPES`)
    :param area_type_to: Area type to change to (one of :attr:`~blendersynth.utils.layout.AREA_TYPES`)
    """
    get_area(area_type_from).type = area_type_to
