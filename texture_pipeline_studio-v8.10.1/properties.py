import bpy

from .constants import RES_FOLDERS


class TPS_Settings(bpy.types.PropertyGroup):
    root_path: bpy.props.StringProperty(
        name="Texture Root",
        subtype="DIR_PATH",
        description=(
            "Folder containing resolution subfolders (4k, 2k, etc.), or a resolution "
            "folder directly. UNC network paths (\\\\server\\share\\...) are supported"
        ),
    )

    resolution: bpy.props.EnumProperty(
        name="Resolution",
        items=[(r, r.upper(), "") for r in RES_FOLDERS],
        default="4k",
    )

    preserve_materials: bpy.props.BoolProperty(
        name="Preserve Custom Nodes",
        default=True,
        description="Keep non-TPS nodes; replace only TPS-generated nodes on re-run",
    )

    purge_orphans: bpy.props.BoolProperty(
        name="Purge Orphan Data",
        default=True,
        description="Remove unused images/materials after operations",
    )

    lod_scope: bpy.props.EnumProperty(
        name="Scope",
        items=[
            ("SELECTED", "Selected Objects", ""),
            ("SCENE", "Whole Scene", ""),
        ],
        default="SELECTED",
    )

    alpha_blend: bpy.props.EnumProperty(
        name="Alpha Blend",
        items=[
            ("HASHED", "Hashed", "Good default for hair/foliage"),
            ("BLEND", "Blend", "True transparency"),
            ("CLIP", "Clip", "Cutout / hard edges"),
        ],
        default="HASHED",
    )

    displacement_mode: bpy.props.EnumProperty(
        name="Displacement",
        items=[
            ("BUMP", "Bump Only", ""),
            ("DISPLACEMENT", "Displacement", "Requires subdivided mesh"),
            ("BOTH", "Both", ""),
        ],
        default="BUMP",
    )


def get_settings(context):
    return context.scene.tps_settings


classes = (
    TPS_Settings,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.tps_settings = bpy.props.PointerProperty(type=TPS_Settings)


def unregister():
    del bpy.types.Scene.tps_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
