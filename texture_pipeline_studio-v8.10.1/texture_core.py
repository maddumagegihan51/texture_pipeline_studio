import os

import bpy

from .constants import IMAGE_CACHE, TEXTURE_INDEX, TPS_NODE_PREFIX
from .utils import (
    detect_map_type,
    is_valid_texture_file,
    mat_key,
    name_matches_material,
    norm_path,
    parse_udim_name,
    texture_base_key,
)


def clear_texture_index():
    TEXTURE_INDEX.clear()


def clear_image_cache():
    IMAGE_CACHE.clear()


def load_image(path):
    path = norm_path(path)
    if not path:
        return None

    if path in IMAGE_CACHE:
        return IMAGE_CACHE[path]

    if not os.path.isfile(path):
        return None

    img = bpy.data.images.load(path, check_existing=True)
    img.source = "FILE"
    IMAGE_CACHE[path] = img
    return img


def pick_best_single_path(entries):
    udim_entries = []
    single_entries = []

    for path, depth in entries:
        _, tile = parse_udim_name(os.path.basename(path))
        if tile:
            udim_entries.append((tile, path, depth))
        else:
            single_entries.append((path, depth))

    if udim_entries:
        udim_entries.sort(key=lambda x: (x[2], x[0]))
        return udim_entries[0][1]

    if single_entries:
        single_entries.sort(key=lambda x: x[1])
        return single_entries[0][0]

    return None


def build_texture_index(folder):
    folder = norm_path(folder)
    if folder in TEXTURE_INDEX:
        return TEXTURE_INDEX[folder]

    raw = {}

    for walk_root, _, files in os.walk(folder):
        rel = os.path.relpath(walk_root, folder)
        depth = 0 if rel == "." else rel.count(os.sep) + 1

        for filename in files:
            full = os.path.join(walk_root, filename)
            if not is_valid_texture_file(full):
                continue

            map_type = detect_map_type(filename)
            if not map_type:
                continue

            base_key = texture_base_key(filename)
            if not base_key:
                continue

            raw.setdefault(base_key, {}).setdefault(map_type, []).append((full, depth))

    index = {}
    for base_key, maps in raw.items():
        index[base_key] = {}
        for map_type, entries in maps.items():
            path = pick_best_single_path(entries)
            if path:
                index[base_key][map_type] = path

    TEXTURE_INDEX[folder] = index
    return index


def find_textures_indexed(index, material_name):
    key = mat_key(material_name)

    if key in index:
        return index[key]

    merged = {}
    prefix = key + "_"
    for idx_key, maps in index.items():
        if idx_key.startswith(prefix):
            for map_type, path in maps.items():
                if map_type not in merged:
                    merged[map_type] = path

    return merged


def find_textures(folder, material_name):
    raw = {}
    folder = norm_path(folder)

    for walk_root, _, files in os.walk(folder):
        rel = os.path.relpath(walk_root, folder)
        depth = 0 if rel == "." else rel.count(os.sep) + 1

        for filename in files:
            full_path = os.path.join(walk_root, filename)
            if not is_valid_texture_file(full_path):
                continue

            if not name_matches_material(filename, material_name):
                continue

            map_type = detect_map_type(filename)
            if not map_type:
                continue

            raw.setdefault(map_type, []).append((full_path, depth))

    result = {}
    for map_type, entries in raw.items():
        path = pick_best_single_path(entries)
        if path:
            result[map_type] = path

    return result


def clear_tps_nodes(nodes):
    to_remove = [n for n in nodes if n.name.startswith(TPS_NODE_PREFIX)]
    for node in to_remove:
        nodes.remove(node)


def new_tps_node(nodes, node_type, label):
    node = nodes.new(node_type)
    node.name = TPS_NODE_PREFIX + label
    node.label = label
    return node


def make_tex_node(nodes, links, path, mapping_node, color=False):
    img = load_image(path)
    if not img:
        return None

    tex = new_tps_node(nodes, "ShaderNodeTexImage", os.path.basename(path))
    tex.image = img
    tex.image.colorspace_settings.name = "sRGB" if color else "Non-Color"
    links.new(mapping_node.outputs["Vector"], tex.inputs["Vector"])
    return tex


def build_material(material, texmap, settings):
    material.use_nodes = True
    node_tree = material.node_tree
    nodes = node_tree.nodes
    links = node_tree.links

    if settings.preserve_materials:
        clear_tps_nodes(nodes)
    else:
        nodes.clear()

    bsdf = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
    output = next((n for n in nodes if n.type == "OUTPUT_MATERIAL"), None)

    if not bsdf:
        bsdf = new_tps_node(nodes, "ShaderNodeBsdfPrincipled", "Principled BSDF")
    if not output:
        output = new_tps_node(nodes, "ShaderNodeOutputMaterial", "Material Output")

    if not any(l.from_node == bsdf and l.to_node == output for l in links):
        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    uv = new_tps_node(nodes, "ShaderNodeTexCoord", "Tex Coord")
    mapping = new_tps_node(nodes, "ShaderNodeMapping", "Mapping")
    links.new(uv.outputs["UV"], mapping.inputs["Vector"])

    if "BaseColor" in texmap:
        tex = make_tex_node(nodes, links, texmap["BaseColor"], mapping, color=True)
        if tex:
            links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

    if "Metallic" in texmap:
        tex = make_tex_node(nodes, links, texmap["Metallic"], mapping)
        if tex:
            links.new(tex.outputs["Color"], bsdf.inputs["Metallic"])

    if "Roughness" in texmap:
        tex = make_tex_node(nodes, links, texmap["Roughness"], mapping)
        if tex:
            links.new(tex.outputs["Color"], bsdf.inputs["Roughness"])

    if "Normal" in texmap:
        tex = make_tex_node(nodes, links, texmap["Normal"], mapping)
        if tex:
            normal_map = new_tps_node(nodes, "ShaderNodeNormalMap", "Normal Map")
            links.new(tex.outputs["Color"], normal_map.inputs["Color"])
            links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])

    if "Displacement" in texmap:
        tex = make_tex_node(nodes, links, texmap["Displacement"], mapping)
        if tex:
            disp = new_tps_node(nodes, "ShaderNodeDisplacement", "Displacement")
            links.new(tex.outputs["Color"], disp.inputs["Height"])
            links.new(disp.outputs["Displacement"], output.inputs["Displacement"])
            material.displacement_method = settings.displacement_mode

    if "Alpha" in texmap:
        tex = make_tex_node(nodes, links, texmap["Alpha"], mapping)
        if tex:
            alpha_input = bsdf.inputs.get("Alpha")
            if alpha_input:
                links.new(tex.outputs["Color"], alpha_input)
            material.blend_method = settings.alpha_blend
            material.use_backface_culling = False
