"""Local NSFW prompt writer for Sunside — no cloud LLM, no refusals on adult content.

Builds English SDXL prompts + negatives from scene templates.
Adults only: blocks underage keywords.
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple


_UNDERAGE_RE = re.compile(
    r"\b("
    r"child|children|kid|kids|toddler|infant|baby|babies|minor|underage|"
    r"teen(?!age woman|age women)|teenager|schoolgirl|schoolboy|"
    r"prepubescent|loli|shota|pedophil|"
    r"дитин|підліт|школяр|малоліт|неповноліт"
    r")\b",
    flags=re.IGNORECASE,
)

BASE_NEGATIVE = (
    "teen, teenager, child, kid, underage, baby face, schoolgirl, "
    "bad anatomy, extra limbs, deformed hands, missing fingers, fused fingers, "
    "plastic skin, airbrushed, glamour studio, cinematic color grade, "
    "watermark, text, anime, cgi, cartoon, 8k, hdr"
)

# Scene id → (label UA, camera/setting English stub, style hint for UI tip)
SCENES: Dict[str, Tuple[str, str, str]] = {
    "doorway": (
        "Doorway peep",
        "voyeur view from dark hallway through half-open door, doorframe in foreground, "
        "subject inside the lit room beyond the doorway, hallway underexposed, warm room light",
        "Through Doorway",
    ),
    "bath_steam": (
        "Bathroom steam",
        "steamy bathroom, foggy mirror condensation, wet tiles, humid air, candid phone photo",
        "Bathroom Steam",
    ),
    "spontaneous": (
        "Spontaneous snap",
        "wide horizontal candid phone snap, caught mid-action, slight motion blur, "
        "messy apartment, imperfect focus, raw unedited",
        "Spontaneous Snap",
    ),
    "bedside": (
        "Bedside night",
        "nighttime bedroom, warm bedside lamp glow, grainy iso, intimate candid phone photo",
        "Bedside Night",
    ),
    "hidden_cam": (
        "Hidden camera",
        "secret ceiling-corner cctv still, steep high angle, subject small in wide room frame, "
        "grainy spy cam, flat overhead light, unaware of camera",
        "Hidden Camera",
    ),
    "mirror": (
        "Mirror selfie",
        "bathroom or bedroom mirror reflection, phone visible in frame, raw amateur mirror photo",
        "Mirror Selfie",
    ),
    "tripod": (
        "Tripod full scene",
        "wide horizontal tripod phone photo, static camera, full scene in frame, "
        "apartment interior, natural window light, raw amateur still",
        "Tripod Phone",
    ),
    "shower": (
        "Shower sex / peek",
        "steamy shower, water spray, wet tiles, fog, candid wet phone still",
        "Shower Peek / Bathroom Steam",
    ),
    "couch": (
        "Couch living room",
        "messy living room couch, afternoon window light, cluttered apartment, candid snap",
        "Spontaneous Snap",
    ),
    "kitchen": (
        "Kitchen counter",
        "messy kitchen, counter edge, morning light, candid caught-in-the-act phone snap",
        "Spontaneous Snap",
    ),
}

INTENSITY_LABELS = {
    "lingerie": "Домашня білизна (soft)",
    "nude": "Нюд / solo",
    "hard_solo": "Жорсткий solo",
    "hard_sex": "Секс з чоловіком",
}

PARTNER_LABELS = {
    "auto": "Авто (з інтенсивності)",
    "solo": "Тільки вона",
    "man": "З чоловіком",
}

MOTION_LABELS = {
    "still": "Статичний кадр",
    "motion": "У русі / mid-thrust",
}


@dataclass
class PromptPack:
    prompt: str
    negative: str
    tip: str
    scene_id: str
    intensity: str


def scene_choices() -> List[str]:
    return [f"{sid} — {meta[0]}" for sid, meta in SCENES.items()]


def intensity_choices() -> List[str]:
    return [f"{k} — {v}" for k, v in INTENSITY_LABELS.items()]


def partner_choices() -> List[str]:
    return [f"{k} — {v}" for k, v in PARTNER_LABELS.items()]


def motion_choices() -> List[str]:
    return [f"{k} — {v}" for k, v in MOTION_LABELS.items()]


def _key_from_choice(choice: str, fallback: str) -> str:
    raw = (choice or fallback).strip()
    return raw.split("—", 1)[0].strip() or fallback


def blocks_underage(text: str) -> bool:
    return bool(_UNDERAGE_RE.search(text or ""))


def _solo_body(intensity: str, motion: bool) -> str:
    blur = "motion blur on hips and hands, " if motion else ""
    if intensity == "lingerie":
        return (
            f"{blur}adult woman in soft home lingerie, cotton bralette and high-waist panties, "
            "oversized open cardigan, relaxed natural pose, tasteful non-explicit"
        )
    if intensity == "nude":
        return (
            f"{blur}adult woman completely naked, bare breasts and pussy visible, "
            "natural standing or sitting pose, explicit but calm framing"
        )
    # hard_solo
    acts = [
        "fingering herself, explicit wet pussy visible, mouth open moaning",
        "fucking herself with a thick dildo, explicit penetration, wet shiny folds",
        "legs open, two fingers spreading herself, hard nipples, flushed chest",
        "on all fours touching herself from behind, ass and pussy toward camera",
    ]
    act = random.choice(acts)
    return f"{blur}adult woman completely naked, {act}"


def _sex_body(motion: bool) -> str:
    blur = (
        "motion blur on hips and thighs from fast thrusting, mid-thrust energy, "
        if motion
        else "clear frozen sex pose, "
    )
    acts = [
        (
            f"{blur}man vigorously fucking her from behind doggy style on the bed, "
            "she on all fours ass up, explicit penetration, his hands gripping her hips, "
            "she moaning into the sheets, pants around his ankles"
        ),
        (
            f"{blur}missionary on the bed, her legs open around him, "
            "explicit deep penetration, breasts moving, mouth open, sheets crumpled"
        ),
        (
            f"{blur}she riding him reverse cowgirl, hips slamming down, "
            "explicit penetration and wetness visible, hands on his thighs"
        ),
        (
            f"{blur}standing sex against the wall, her legs wrapped around him, "
            "explicit penetration, panties on one ankle, faces turned away moaning"
        ),
        (
            f"{blur}bent over sink or couch armrest, fucked hard from behind, "
            "explicit penetration, wet messy, gripping the edge"
        ),
    ]
    return "adult woman with an adult man, " + random.choice(acts)


def _place_flavor(scene_id: str) -> str:
    flavors = {
        "doorway": "she is busy inside the bedroom, not looking toward the hallway camera, unaware",
        "bath_steam": "wet skin sheen, water droplets, steam in the air",
        "spontaneous": "not posing for the camera, imperfect candid framing",
        "bedside": "intimate low light, duvet messy",
        "hidden_cam": "back or side to camera, unaware voyeur footage",
        "mirror": "looking toward phone screen in the mirror",
        "tripod": "full bodies visible in frame when possible",
        "shower": "water running over bodies, steamy atmosphere",
        "couch": "on the living room couch",
        "kitchen": "on or against the kitchen counter",
    }
    return flavors.get(scene_id, "photorealistic amateur photo")


def compose(
    scene_choice: str,
    intensity_choice: str,
    partner_choice: str = "auto — Авто (з інтенсивності)",
    motion_choice: str = "motion — У русі / mid-thrust",
    extra: str = "",
    seed: int | None = None,
) -> PromptPack:
    if seed is not None:
        random.seed(seed)

    scene_id = _key_from_choice(scene_choice, "spontaneous")
    intensity = _key_from_choice(intensity_choice, "hard_sex")
    partner = _key_from_choice(partner_choice, "auto")
    motion_key = _key_from_choice(motion_choice, "motion")
    motion = motion_key == "motion"

    if scene_id not in SCENES:
        scene_id = "spontaneous"
    if intensity not in INTENSITY_LABELS:
        intensity = "hard_sex"

    extra = (extra or "").strip()
    if blocks_underage(extra) or blocks_underage(scene_choice):
        return PromptPack(
            prompt="",
            negative=BASE_NEGATIVE,
            tip="Заблоковано: лише 18+. Прибери формулювання про неповнолітніх.",
            scene_id=scene_id,
            intensity=intensity,
        )

    if partner == "auto":
        with_man = intensity == "hard_sex"
    else:
        with_man = partner == "man"

    if with_man:
        intensity = "hard_sex"
        body = _sex_body(motion)
    else:
        if intensity == "hard_sex":
            intensity = "hard_solo"
        body = _solo_body(intensity, motion)

    cam, style_hint = SCENES[scene_id][1], SCENES[scene_id][2]
    place = _place_flavor(scene_id)

    parts = [
        cam,
        body,
        place,
        "photorealistic, raw amateur, unedited",
    ]
    if extra and not blocks_underage(extra):
        # keep user extras but do not let them override adult framing
        parts.append(extra)

    prompt = ", ".join(p for p in parts if p)

    neg_bits = [BASE_NEGATIVE]
    if scene_id == "doorway":
        neg_bits.append(
            "standing in hallway, in corridor facing camera, looking at camera, "
            "selfie, no doorframe, beauty portrait"
        )
    if with_man:
        neg_bits.append("solo only, no male partner, censor bar, mosaic")
    if intensity == "lingerie":
        neg_bits.append("nude, naked, nipples, pussy, explicit sex")

    tip = (
        f"Style tip: **{style_hint}**. Character увімкни окремо (якір не дублюй). "
        f"Intensity: {INTENSITY_LABELS.get(intensity, intensity)}."
    )

    return PromptPack(
        prompt=prompt,
        negative=", ".join(neg_bits),
        tip=tip,
        scene_id=scene_id,
        intensity=intensity,
    )


def compose_from_ui(
    scene_choice: str,
    intensity_choice: str,
    partner_choice: str,
    motion_choice: str,
    extra: str,
    randomize: bool,
) -> Tuple[str, str, str]:
    seed = None if randomize else 0
    pack = compose(
        scene_choice=scene_choice,
        intensity_choice=intensity_choice,
        partner_choice=partner_choice,
        motion_choice=motion_choice,
        extra=extra,
        seed=seed,
    )
    return pack.prompt, pack.negative, pack.tip
