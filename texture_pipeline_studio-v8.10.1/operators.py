import os

import bpy

from .constants import RES_FOLDERS
from .properties import get_settings
from .texture_core import (
    build_material,
    build_texture_index,
    clear_image_cache,
    clear_texture_index,
    find_textures,
    find_textures_indexed,
)
from .utils import (
    get_target_objects,
    iter_material_slots,
    maybe_purge_orphans,
    norm_path,
    resolve_texture_root,
    swap_resolution_in_path,
    to_udim_filepath,
)


class TPS_OT_run(bpy.types.Operator):
    bl_idname = "tps.run"
    bl_label = "Assign Textures"
    bl_description = "Find and assign textures as single images"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = get_settings(context)
        root, error = resolve_texture_root(settings)
        if error:
            self.report({"ERROR"}, error)
            return {"CANCELLED"}

        objects = get_target_objects(context, settings)
        if not objects:
            self.report({"WARNING"}, "No mesh objects in scope.")
            return {"CANCELLED"}

        assigned = 0
        skipped = 0
        seen_materials = set()
        texture_index = build_texture_index(root)
        wm = context.window_manager
        total = max(1, len(objects))
        wm.progress_begin(0, total)

        progress = 0
        for _, material in iter_material_slots(objects):
            progress += 1
            wm.progress_update(min(progress, total))
            if material.name in seen_materials:
                continue
            seen_materials.add(material.name)

            texmap = find_textures_indexed(texture_index, material.name)
            if not texmap:
                texmap = find_textures(root, material.name)

            if texmap:
                build_material(material, texmap, settings)
                assigned += 1
            else:
                skipped += 1

        wm.progress_end()
        clear_image_cache()
        clear_texture_index()
        maybe_purge_orphans(settings)

        msg = f"Assigned {assigned} material(s)"
        if skipped:
            msg += f", skipped {skipped} (no textures found)"
        if settings.purge_orphans:
            msg += ", orphans purged"
        self.report({"INFO"}, msg)

        if assigned == 0:
            self.report({"WARNING"}, "No textures matched. Check naming and root folder.")
            return {"CANCELLED"}

        return {"FINISHED"}


class TPS_OT_convert_to_udim(bpy.types.Operator):
    bl_idname = "tps.convert_to_udim"
    bl_label = "Convert Textures to UDIM"
    bl_description = "Convert Image Texture nodes from Single Image to UDIM tiles"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = get_settings(context)
        objects = get_target_objects(context, settings)

        if not objects:
            self.report({"WARNING"}, "No mesh objects in scope.")
            return {"CANCELLED"}

        converted = 0
        skipped = 0
        seen_images = set()

        for _, mat in iter_material_slots(objects):
            if not mat or not mat.use_nodes:
                continue

            for node in mat.node_tree.nodes:
                if node.type != "TEX_IMAGE" or not node.image:
                    continue

                img = node.image
                img_id = img.as_pointer()
                if img_id in seen_images:
                    continue
                seen_images.add(img_id)

                if img.source == "TILED":
                    skipped += 1
                    continue

                if not img.filepath:
                    skipped += 1
                    continue

                img.source = "TILED"
                img.filepath = to_udim_filepath(img.filepath)

                try:
                    img.reload()
                    converted += 1
                except RuntimeError:
                    skipped += 1

        clear_image_cache()
        maybe_purge_orphans(settings)

        msg = f"Converted {converted} image(s) to UDIM"
        if skipped:
            msg += f", skipped {skipped}"
        if settings.purge_orphans:
            msg += ", orphans purged"
        self.report({"INFO"}, msg)
        return {"FINISHED"}


class TPS_OT_lod_swap(bpy.types.Operator):
    bl_idname = "tps.lod_swap"
    bl_label = "Swap Resolution"
    bl_description = "Swap image paths to another resolution folder"
    bl_options = {"REGISTER", "UNDO"}

    resolution: bpy.props.EnumProperty(
        items=[(r, r.upper(), "") for r in RES_FOLDERS],
        name="Resolution",
    )

    def execute(self, context):
        settings = get_settings(context)
        objects = get_target_objects(context, settings)
        if not objects:
            self.report({"WARNING"}, "No mesh objects in scope.")
            return {"CANCELLED"}

        seen_images = set()
        changed = 0
        missing = 0
        failed = 0

        for _, material in iter_material_slots(objects):
            if not material or not material.use_nodes:
                continue

            for node in material.node_tree.nodes:
                if node.type != "TEX_IMAGE" or not node.image:
                    continue

                image = node.image
                image_id = image.as_pointer()
                if image_id in seen_images:
                    continue
                seen_images.add(image_id)

                old_path = norm_path(image.filepath)
                if not old_path:
                    continue

                new_path = swap_resolution_in_path(old_path, self.resolution)
                if new_path == old_path:
                    continue

                if image.source == "TILED" and "<UDIM>" in new_path:
                    test_path = new_path.replace("<UDIM>", "1001")
                    if not os.path.isfile(test_path):
                        missing += 1
                        continue
                elif not os.path.isfile(new_path):
                    missing += 1
                    continue

                image.filepath = new_path
                try:
                    image.reload()
                    changed += 1
                except RuntimeError:
                    failed += 1

        clear_image_cache()
        maybe_purge_orphans(settings)

        msg = f"Swapped {changed} texture(s) -> {self.resolution.upper()}"
        if missing:
            msg += f", {missing} missing at target resolution"
        if failed:
            msg += f", {failed} failed to reload"
        if settings.purge_orphans:
            msg += ", orphans purged"

        level = "INFO" if changed else "WARNING"
        self.report({level}, msg)
        return {"FINISHED" if changed else "CANCELLED"}


classes = (
    TPS_OT_run,
    TPS_OT_convert_to_udim,
    TPS_OT_lod_swap,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
