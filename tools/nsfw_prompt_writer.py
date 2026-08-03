"""Solazola-aesthetic prompt pack (soft boudoir → hard explicit solo). Adults 18+ only."""
from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

_UNDERAGE_RE = re.compile(
    r"\b(child|kid|toddler|infant|baby|minor|underage|teenager|schoolgirl|loli|shota|"
    r"дитин|підліт|школяр|малоліт|неповноліт)\b",
    re.I,
)

BASE_NEGATIVE = (
    "teen, teenager, child, underage, baby face, schoolgirl, bad anatomy, extra limbs, "
    "deformed hands, fused fingers, plastic skin, airbrushed porcelain, anime, cgi, cartoon, "
    "watermark, text, logo, cinematic color grade, oversharpen, 8k, hdr"
)

SOFT: Dict[str, Tuple[str, str]] = {
    "robe_studio": (
        "Sheer floral robe nude studio",
        "full body photoreal studio photo, plain light grey wall, slim adult woman standing facing camera, "
        "long straight brown hair middle part, sheer black mesh open robe with colorful floral embroidery, "
        "robe open, nude underneath, hands lightly covering breasts at collarbone, soft even beauty lighting, "
        "natural skin texture, calm sultry eye contact",
    ),
    "floral_corset": (
        "Floral milkmaid corset",
        "medium close-up photoreal portrait, bright modern apartment, slim adult woman long straight dark brown hair, "
        "white floral corset crop top orange yellow blossoms, lace trim, puffed milkmaid sleeves, hook-and-eye front, "
        "deep cleavage, soft daylight, looking at camera, shallow DOF",
    ),
    "red_lace_dark": (
        "Red lace dark bedroom",
        "medium photoreal boudoir, dark bedroom bokeh, long dark brown hair, bright red lace bra and garter panties, "
        "black lace-top thigh highs, finger on parted lips, soft low-key light, suggestive eye contact",
    ),
    "prone_lace": (
        "Prone black lace",
        "photoreal bedroom, rumpled white sheets, adult woman on stomach propped on elbows, black lace bra and panties, "
        "knees bent hips arched, soft daylight, looking at camera",
    ),
}

HARD: Dict[str, Tuple[str, str]] = {
    "spread_bed": (
        "Legs spread on bed",
        "photoreal amateur erotic photo, modern minimal bedroom, white bed, soft natural daylight, "
        "slim adult woman long straight brown hair middle part, sitting on bed edge facing camera, "
        "legs spread wide knees out, explicit pussy fully visible, pink lace panties pulled aside, "
        "looking at camera, natural skin texture, raw unedited",
    ),
    "spread_sofa": (
        "Legs spread on grey sofa",
        "photoreal amateur erotic photo, modern living room grey sofa, soft daylight, "
        "slim adult woman long straight brown hair, one leg up on sofa, dark red lace lingerie, "
        "panties hooked aside, fingers spreading herself, explicit wet pussy clear, calm dirty eye contact",
    ),
    "kneel_lift": (
        "Kneeling top lifted",
        "photoreal amateur, white bed, slim adult woman kneeling on mattress, long brown hair, "
        "white crop tank lifted over bare breasts, black lace thong, thighs apart, back slightly arched, "
        "looking at camera, soft window light",
    ),
    "full_frontal": (
        "Full frontal nude stand",
        "photoreal full body, plain textured wall, slim adult woman standing nude, hands behind head, "
        "long straight brown hair, weight on one hip, explicit breasts and pussy visible, soft even light, "
        "looking at camera, raw amateur still",
    ),
    "stairs_nude": (
        "Nude on stairs",
        "photoreal indoor staircase, warm soft light, slim adult woman seated on steps nude, "
        "long brown hair, legs casually open, explicit frontal, calm expression, modern apartment, shallow DOF",
    ),
    "all_fours": (
        "All fours looking back",
        "photoreal bedroom, slim adult woman on all fours on bed, looking back over shoulder, "
        "black thong pulled between cheeks, long brown hair, arched back, soft daylight, erotic amateur photo",
    ),
}


def scene_choices(tier: str = "hard") -> List[str]:
    src = HARD if tier == "hard" else SOFT
    return [f"{k} — {v[0]}" for k, v in src.items()]


def blocks_underage(text: str) -> bool:
    return bool(_UNDERAGE_RE.search(text or ""))


@dataclass
class PromptPack:
    prompt: str
    negative: str
    tip: str


def _key(choice: str, fallback: str) -> str:
    return ((choice or fallback).split("—", 1)[0].strip() or fallback)


def compose(scene_choice: str, tier: str = "hard", extra: str = "", randomize: bool = False) -> PromptPack:
    if blocks_underage(extra) or blocks_underage(scene_choice):
        return PromptPack("", BASE_NEGATIVE, "Заблоковано: лише 18+.")
    src = HARD if tier.startswith("hard") else SOFT
    if randomize:
        sid = random.choice(list(src.keys()))
    else:
        sid = _key(scene_choice, next(iter(src)))
        if sid not in src:
            sid = next(iter(src))
    label, body = src[sid]
    if extra.strip():
        body = f"{body}, {extra.strip()}"
    body = f"{body}, photorealistic, no watermark"
    return PromptPack(body, BASE_NEGATIVE, f"**{label}** · tier={tier} · Character якір окремо")


if __name__ == "__main__":
    for t in ("soft", "hard"):
        print("====", t)
        for c in scene_choices(t):
            print(compose(c, t).prompt[:120], "...")
