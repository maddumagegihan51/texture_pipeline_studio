import re

ADDON_ID = "texture_pipeline_studio"

RES_FOLDERS = ["16k", "8k", "4k", "2k", "1k", "512", "256"]
RES_PATTERN = re.compile(
    r"([\\/])(16k|8k|4k|2k|1k|512|256)([\\/])",
    re.IGNORECASE,
)
TPS_NODE_PREFIX = "TPS."
UDIM_TILE_PATTERN = re.compile(r"\.(\d{4})$")

MAP_RULES = (
    ("BaseColor", ("basecolor", "base_color", "albedo", "diffuse", "col", "bc")),
    ("Roughness", ("roughness", "rough", "rgh")),
    ("Metallic", ("metalness", "metallic", "metal", "met", "mtl")),
    ("Normal", ("normal", "normalmap", "nrm", "nrml", "nor", "nrmal")),
    ("Displacement", ("displacement", "disp", "height", "hgt")),
    ("Alpha", ("alpha", "opacity", "opac")),
)

TOKEN_TO_MAP = {}
for map_type, keywords in MAP_RULES:
    for kw in keywords:
        TOKEN_TO_MAP[kw] = map_type

MAP_KEYWORDS = set(TOKEN_TO_MAP.keys())
VALID_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".exr", ".webp", ".tga"}
UDIM_EXT_PATTERN = re.compile(r"^\.\d{4}$")

IMAGE_CACHE = {}
TEXTURE_INDEX = {}
