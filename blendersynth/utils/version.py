import bpy


def is_version(version_num: int) -> bool:
    """Check if the Blender version is equal to the given version number.

    :param version_num: version number to check against
    """
    return int(bpy.app.version_string.split(".")[0]) == version_num


def is_version_plus(version_num: int) -> bool:
    """Check if the Blender version is greater than or equal to the given version number.

    is_version_plus(4.0) equivalent to is version 4.0+

    :param version_num: version number to check against
    """
    return int(bpy.app.version_string.split(".")[0]) >= version_num
