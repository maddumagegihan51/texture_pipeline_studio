if "bpy" in locals():
    import importlib

    if "properties" in locals():
        importlib.reload(properties)
    if "operators" in locals():
        importlib.reload(operators)
    if "ui" in locals():
        importlib.reload(ui)
else:
    from . import operators, properties, ui

import bpy

modules = (
    properties,
    operators,
    ui,
)


def register():
    for mod in modules:
        mod.register()


def unregister():
    for mod in reversed(modules):
        mod.unregister()
