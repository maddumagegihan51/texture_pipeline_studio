import bpy

from .constants import RES_FOLDERS
from .properties import get_settings


def draw_tps_settings(layout, context):
    settings = get_settings(context)
    col = layout.column(align=True)

    col.prop(settings, "root_path")
    col.prop(settings, "resolution")
    col.prop(settings, "preserve_materials")
    col.prop(settings, "purge_orphans")
    col.prop(settings, "lod_scope")
    col.prop(settings, "alpha_blend")
    col.prop(settings, "displacement_mode")

    col.separator()
    col.operator("tps.run", icon="FILE_REFRESH")

    col.separator()
    col.label(text="UDIM:")
    col.operator("tps.convert_to_udim", icon="UV")

    col.separator()
    col.label(text="Resolution Swap:")
    row = col.row(align=True)
    row.scale_y = 1.2
    for res in RES_FOLDERS:
        op = row.operator("tps.lod_swap", text=res.upper())
        op.resolution = res



class TPS_PT_properties(bpy.types.Panel):
    bl_label = "Texture Pipeline Studio"
    bl_idname = "TPS_PT_properties"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        draw_tps_settings(self.layout, context)


classes = (
    TPS_PT_properties,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
