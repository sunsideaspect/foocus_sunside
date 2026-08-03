"""Boudoir / lingerie prompt pack matching project reference photos.

Offline helper for the Cursor NSFW Prompt Writer chat. Adults 18+ only.
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple


_UNDERAGE_RE = re.compile(
    r"\b("
    r"child|children|kid|kids|toddler|infant|baby|babies|minor|underage|"
    r"teen(?!age woman|tage women)|teenager|schoolgirl|schoolboy|"
    r"prepubescent|loli|shota|pedophil|"
    r"дитин|підліт|школяр|малоліт|неповноліт"
    r")\b",
    flags=re.IGNORECASE,
)

BASE_NEGATIVE = (
    "teen, teenager, child, underage, baby face, bad anatomy, extra limbs, "
    "deformed hands, plastic skin, airbrushed porcelain, anime, cgi, cartoon, "
    "watermark, text, logo, cinematic color grade, oversharpen, 8k, hdr"
)

# id → (label, prompt body, style tip)
SCENES: Dict[str, Tuple[str, str, str]] = {
    "robe_studio": (
        "1 Sheer floral robe nude studio",
        "full body photoreal studio photo, plain light grey wall, slim adult woman standing facing camera, "
        "long straight brown hair middle part, sheer black mesh open robe with small colorful floral embroidery "
        "draped on shoulders, robe open, nude underneath, hands lightly covering breasts at collarbone, "
        "bare stomach and hips visible, soft even beauty lighting, natural skin texture, calm sultry eye contact",
        "none / clean studio",
    ),
    "floral_corset": (
        "2 White floral milkmaid corset",
        "medium close-up photoreal portrait, bright modern apartment, shallow depth of field, adult woman "
        "long straight dark brown hair, white floral corset crop top with orange yellow blossom print, "
        "sweetheart neckline white lace trim, short puffed milkmaid sleeves, center hook-and-eye closures, "
        "deep cleavage, soft natural front light, looking at camera, blurred wall art behind, realistic skin pores",
        "Spontaneous Snap",
    ),
    "red_lace_dark": (
        "3 Red lace dark bedroom",
        "medium photoreal boudoir shot, dark bedroom bokeh, adult woman long dark brown hair over one shoulder, "
        "bright red lace bra and matching red lace garter panties, black lace-top thigh-high stockings, "
        "finger resting on parted lips, other arm across midriff, soft low-key front light, suggestive eye contact, "
        "sharp lace detail",
        "Bedside Night",
    ),
    "red_lace_soft": (
        "4 Red lace soft gaze",
        "vertical photoreal portrait in bedroom, navy blue wall soft bokeh, bed with white and blue pillows, "
        "adult woman long chestnut hair middle part, eyes cast downward soft expression, vivid red lace bra and "
        "high-waist red lace garter belt with thin straps, hint of black stocking, soft warm indoor light, "
        "intricate lace texture, natural skin",
        "Bedside Night",
    ),
    "blue_xmas": (
        "5 Blue sheer Christmas bokeh",
        "photoreal three-quarter back view, looking over shoulder at camera, long wavy light-brown hair, "
        "sheer light-blue off-shoulder crop top with white polka dots and ruffles, matching sheer thong, "
        "Christmas tree warm fairy lights bokeh background, soft even key light on skin, glamorous boudoir photo",
        "Spontaneous Snap",
    ),
    "mesh_bed": (
        "6 Black floral mesh on bed",
        "medium photoreal bedroom shot, white sheets wooden headboard, adult woman sitting on bed slight smile, "
        "long straight brown hair, black sheer mesh lingerie with pink-red floral embroidery, underwire bra "
        "thin ribbon shoulder ties, high-cut side-tie panties, smartphone on bed, soft daylight, "
        "realistic fabric transparency",
        "Spontaneous Snap",
    ),
    "kitchen_sheer": (
        "7 Kitchen sheer turtleneck",
        "photoreal indoor kitchen portrait soft bokeh cabinets, adult woman long straight brown hair, "
        "black sheer long-sleeve polka turtleneck crop tied in a knot at waist, breasts visible through sheer fabric, "
        "black lace panties scalloped edge, one arm raised above head, slight lean back, warm indoor light, "
        "candid glam photo",
        "Spontaneous Snap",
    ),
    "harness": (
        "8 Black harness bodysuit",
        "medium photoreal standing portrait, white wardrobe and paneled door background, adult woman "
        "long straight brown hair past waist, black strappy harness bodysuit with metal rings, mesh panels "
        "and side cutout, soft daylight, intricate strap geometry sharp, pale nails thin bracelet, calm eye contact",
        "Tripod Phone",
    ),
    "prone_lace": (
        "9 Prone black lace on bed",
        "photoreal bedroom medium shot, rumpled white sheets, adult woman lying on stomach propped on elbows, "
        "hands clasped, long straight brown hair, black lace bra with thin decorative chest straps, matching "
        "lace panties, knees bent hips slightly arched, soft natural light, shallow DOF, boudoir gaze at camera",
        "Bedside Night",
    ),
}

INTENSITY_LABELS = {
    "match_ref": "Як на рефі (за замовч.)",
    "softer": "М’якше / менше sheer",
    "harder": "Жорсткіше / більше nude",
}


def scene_choices() -> List[str]:
    return [f"{sid} — {meta[0]}" for sid, meta in SCENES.items()]


def intensity_choices() -> List[str]:
    return [f"{k} — {v}" for k, v in INTENSITY_LABELS.items()]


def _key(choice: str, fallback: str) -> str:
    return ((choice or fallback).split("—", 1)[0].strip() or fallback)


def blocks_underage(text: str) -> bool:
    return bool(_UNDERAGE_RE.search(text or ""))


@dataclass
class PromptPack:
    prompt: str
    negative: str
    tip: str


def compose(scene_choice: str, intensity_choice: str = "match_ref", extra: str = "") -> PromptPack:
    sid = _key(scene_choice, "red_lace_dark")
    intensity = _key(intensity_choice, "match_ref")
    if sid not in SCENES:
        sid = "red_lace_dark"

    extra = (extra or "").strip()
    if blocks_underage(extra) or blocks_underage(scene_choice):
        return PromptPack("", BASE_NEGATIVE, "Заблоковано: лише 18+.")

    label, body, style = SCENES[sid]
    if intensity == "softer":
        body = body.replace("nude underneath, ", "lingerie underneath, ")
        body = body.replace("breasts visible through sheer fabric, ", "subtle sheer fabric, ")
    elif intensity == "harder":
        body = body + ", more explicit revealing pose, stronger erotic tension"

    if extra and not blocks_underage(extra):
        body = f"{body}, {extra}"

    body = f"{body}, photorealistic, raw unedited, no watermark"
    tip = f"**{label}** · Style tip: {style}. Character якір у Sunside окремо."
    return PromptPack(body, BASE_NEGATIVE, tip)


def compose_from_ui(scene_choice: str, intensity_choice: str, extra: str = "") -> Tuple[str, str, str]:
    pack = compose(scene_choice, intensity_choice, extra)
    return pack.prompt, pack.negative, pack.tip


if __name__ == "__main__":
    for c in scene_choices():
        p, n, t = compose_from_ui(c, "match_ref — Як на рефі (за замовч.)")
        print("===", c)
        print(p)
        print()
