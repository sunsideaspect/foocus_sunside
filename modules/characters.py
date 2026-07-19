"""Built-in Sunside characters with stable appearance anchors."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

CHARACTERS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../characters'))


@dataclass
class Character:
    id: str
    name: str
    anchor: str
    negative: str
    preview_path: str | None = None
    face_ref_path: str | None = None

    @property
    def label(self) -> str:
        return self.name


_cache: dict[str, Character] | None = None


def _read_text(path: str) -> str:
    if not os.path.isfile(path):
        return ''
    with open(path, encoding='utf-8') as f:
        return f.read().strip()


def _optional_image(path: str) -> str | None:
    return path if os.path.isfile(path) else None


def load_characters() -> dict[str, Character]:
    global _cache
    if _cache is not None:
        return _cache

    characters: dict[str, Character] = {}
    if not os.path.isdir(CHARACTERS_DIR):
        _cache = characters
        return characters

    for entry in sorted(os.listdir(CHARACTERS_DIR)):
        folder = os.path.join(CHARACTERS_DIR, entry)
        if not os.path.isdir(folder):
            continue
        meta_path = os.path.join(folder, 'character.json')
        if os.path.isfile(meta_path):
            with open(meta_path, encoding='utf-8') as f:
                meta = json.load(f)
            cid = str(meta.get('id') or entry)
            name = str(meta.get('name') or entry.title())
        else:
            cid = entry
            name = entry.title()

        anchor = _read_text(os.path.join(folder, 'anchor.txt'))
        negative = _read_text(os.path.join(folder, 'negative.txt'))
        if not anchor:
            continue

        characters[cid] = Character(
            id=cid,
            name=name,
            anchor=anchor,
            negative=negative,
            preview_path=_optional_image(os.path.join(folder, 'preview.jpg')),
            face_ref_path=_optional_image(os.path.join(folder, 'face_ref.jpg')),
        )

    _cache = characters
    return characters


def character_choices() -> list[str]:
    return [c.name for c in load_characters().values()]


def get_by_name(name: str | None) -> Character | None:
    if not name:
        return None
    for c in load_characters().values():
        if c.name == name or c.id == name:
            return c
    return None


def apply_character_to_prompt(prompt: str, character: Character | None) -> str:
    """Prepend appearance anchor; append light face-protect (NSFW tokens steal face budget)."""
    if character is None:
        return prompt
    prompt = (prompt or '').strip()
    face_protect = (
        'sharp coherent face, intact eyes and mouth, natural facial proportions, '
        'detailed facial features'
    )
    if not prompt:
        return f'{character.anchor}, {face_protect}'
    if character.anchor[:48] in prompt:
        if 'coherent face' not in prompt.lower():
            return f'{prompt}, {face_protect}'
        return prompt
    # Face/identity first, scene after — CLIP attends more to early tokens
    return f'{character.anchor}, {face_protect}, {prompt}'


def merge_character_negative(negative: str, character: Character | None) -> str:
    if character is None or not character.negative:
        return negative
    parts = [p.strip() for p in (negative or '', character.negative) if p and p.strip()]
    # de-dupe while preserving order
    seen = set()
    out = []
    for part in ', '.join(parts).split(','):
        token = part.strip()
        key = token.lower()
        if not token or key in seen:
            continue
        seen.add(key)
        out.append(token)
    return ', '.join(out)
