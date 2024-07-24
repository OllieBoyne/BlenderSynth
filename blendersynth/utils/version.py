import bpy
from typing import Union

def is_version(version_num: Union[int, float]) -> bool:
    """Check if the Blender version is equal to the given version number.

    If integer provided, only checks major version.

    :param version_num: version number to check against
    """

    major, minor = map(int, bpy.app.version_string.split(".")[:2])

    if isinstance(version_num, int):
        return major == version_num

    target_major, target_minor = map(int, str(version_num).split("."))

    return (major, minor) == (target_major, target_minor)


def is_version_plus(version_num: Union[int, float]) -> bool:
    """Check if the Blender version is greater than or equal to the given version number.

    is_version_plus(4.0) equivalent to is version 4.0+

    :param version_num: version number to check against
    """

    version_num = float(version_num)
    major, minor = map(int, bpy.app.version_string.split(".")[:2])
    target_major, target_minor = map(int, str(version_num).split("."))
    return (major, minor) >= (target_major, target_minor)
