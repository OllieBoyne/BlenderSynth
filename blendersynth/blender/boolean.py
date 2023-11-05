import blendersynth as bsyn


def _apply_boolean(
    *meshes: bsyn.Mesh, operation: str = "UNION", hide_others: bool = True
) -> bsyn.Mesh:
    target, *others = meshes
    for other in others:
        target.add_child(other)

        modifier = target.obj.modifiers.new(type="BOOLEAN", name="bool")
        modifier.object = other.obj
        modifier.operation = operation

        bsyn.ops.object.modifier_apply(modifier="bool")
        if hide_others:
            other.obj.hide_render = True
            other.obj.hide_set(True)
    return target


def union(*meshes: bsyn.Mesh, hide_others=True):
    return _apply_boolean(*meshes, operation="UNION", hide_others=hide_others)


def difference(*meshes: bsyn.Mesh, hide_others=True):
    return _apply_boolean(*meshes, operation="DIFFERENCE", hide_others=hide_others)


def intersect(*meshes: bsyn.Mesh, hide_others=True):
    return _apply_boolean(*meshes, operation="INTERSECT", hide_others=hide_others)
