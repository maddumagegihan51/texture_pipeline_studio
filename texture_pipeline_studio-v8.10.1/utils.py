import os
import re

import bpy

from .constants import (
    MAP_KEYWORDS,
    RES_FOLDERS,
    RES_PATTERN,
    TOKEN_TO_MAP,
    UDIM_EXT_PATTERN,
    UDIM_TILE_PATTERN,
    VALID_IMAGE_EXTS,
)


def _to_os_path(path):
    return path.replace("/", os.sep)


def is_unc_or_absolute(path):
    if not path:
        return False
    if path.startswith("\\\\"):
        return True
    return os.path.isabs(_to_os_path(path))


def norm_path(path):
    if not path:
        return ""
    path = path.strip()
    if is_unc_or_absolute(path):
        return os.path.normpath(_to_os_path(path))
    return os.path.normpath(bpy.path.abspath(path))


def is_resolution_folder(name):
    lowered = name.lower()
    return any(lowered == folder for folder in RES_FOLDERS)


def purge_orphan_data():
    try:
        bpy.ops.outliner.orphans_purge(
            do_local_ids=True,
            do_linked_ids=True,
            do_recursive=True,
        )
    except RuntimeError:
        pass


def mat_key(name):
    name = name.lower()
    name = re.sub(r"_v\d+", "", name)
    name = re.sub(r"\.\d+$", "", name)
    return name


def file_tokens(filename):
    stem = os.path.splitext(os.path.basename(filename))[0].lower()
    stem = re.sub(r"_v\d+", "", stem)
    return [t for t in re.split(r"[_\-.]+", stem) if t]


def strip_udim_tokens(tokens):
    tokens = list(tokens)
    while tokens and re.fullmatch(r"\d{4}", tokens[-1]):
        tokens.pop()
    return tokens


def parse_udim_name(filename):
    stem = os.path.splitext(os.path.basename(filename))[0].lower()
    stem = re.sub(r"_v\d+", "", stem)
    match = UDIM_TILE_PATTERN.search(stem)
    if not match:
        return stem, None
    tile = int(match.group(1))
    base = stem[: match.start()]
    return base, tile


def to_udim_filepath(filepath):
    filepath = norm_path(filepath)
    if not filepath:
        return filepath

    folder = os.path.dirname(filepath)
    name = os.path.basename(filepath)
    stem, ext = os.path.splitext(name)

    if "<UDIM>" in stem:
        return filepath

    stem = re.sub(r"\.\d{4}$", "", stem)
    return norm_path(os.path.join(folder, stem + ".<UDIM>" + ext))


def is_valid_texture_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext in VALID_IMAGE_EXTS:
        return True
    if UDIM_EXT_PATTERN.match(ext) and os.path.isfile(filepath):
        return True
    return False


def texture_base_key(filename):
    tokens = strip_udim_tokens(file_tokens(filename))

    while tokens and tokens[-1] in MAP_KEYWORDS:
        tokens.pop()

    if not tokens:
        return None

    return "_".join(tokens)


def detect_map_type(filename):
    tokens = strip_udim_tokens(file_tokens(filename))
    if not tokens:
        return None

    last = tokens[-1]
    if last in TOKEN_TO_MAP:
        return TOKEN_TO_MAP[last]

    if len(tokens) >= 2:
        last_two = "_".join(tokens[-2:])
        if last_two in TOKEN_TO_MAP:
            return TOKEN_TO_MAP[last_two]

    for token in reversed(tokens):
        if token in TOKEN_TO_MAP:
            return TOKEN_TO_MAP[token]

        for kw, map_type in TOKEN_TO_MAP.items():
            if len(kw) < 4:
                continue
            if token == kw or token.endswith(kw) or kw in token:
                return map_type

    stem = "_".join(tokens)
    suffix_rules = (
        ("Displacement", (r"displacement$", r"disp$", r"height$", r"hgt$")),
        ("Normal", (r"normal$", r"normalmap$", r"nrm$", r"nrml$", r"nor$")),
        ("Metallic", (r"metalness$", r"metallic$", r"metal$", r"met$", r"mtl$")),
        ("Roughness", (r"roughness$", r"rough$", r"rgh$")),
        ("BaseColor", (r"basecolor$", r"base_color$", r"albedo$", r"diffuse$", r"col$", r"bc$")),
        ("Alpha", (r"alpha$", r"opacity$", r"opac$")),
    )

    for map_type, patterns in suffix_rules:
        for pattern in patterns:
            if re.search(pattern, stem):
                return map_type

    return None


def name_matches_material(filename, material_name):
    key = mat_key(material_name)
    tokens = file_tokens(filename)

    if key in tokens:
        return True

    joined = "_".join(tokens)
    if joined == key:
        return True
    if joined.startswith(key + "_"):
        return True
    if joined.endswith("_" + key):
        return True

    file_base = texture_base_key(filename)
    if file_base and file_base == key:
        return True

    return False


def swap_resolution_in_path(path, new_resolution):
    normalized = norm_path(path)

    def repl(match):
        return f"{match.group(1)}{new_resolution}{match.group(3)}"

    return RES_PATTERN.sub(repl, normalized, count=1)


def get_target_objects(context, settings):
    if settings.lod_scope == "SCENE":
        return [obj for obj in context.scene.objects if obj.type == "MESH"]
    return [obj for obj in context.selected_objects if obj.type == "MESH"]


def iter_material_slots(objects):
    for obj in objects:
        for slot in obj.material_slots:
            if slot.material:
                yield obj, slot.material


def resolve_texture_root(settings):
    if not settings.root_path.strip():
        return None, "Set Texture Root first."

    root = norm_path(settings.root_path)
    if not os.path.isdir(root):
        return None, f"Texture root not found: {root}"

    folder_name = os.path.basename(root.rstrip("\\/"))
    if is_resolution_folder(folder_name):
        return root, None

    res_root = os.path.join(root, settings.resolution)
    if not os.path.isdir(res_root):
        return None, f"Resolution folder not found: {norm_path(res_root)}"

    return norm_path(res_root), None


def maybe_purge_orphans(settings):
    if settings.purge_orphans:
        purge_orphan_data()
