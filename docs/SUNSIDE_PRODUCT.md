# Sunside Product Mode

Slim Fooocus UI for NSFW photoreal visual factory.

## Defaults
- Product mode **ON** (disable with `--disable-sunside-product` or `SUNSIDE_PRODUCT=0`)
- Model: CyberRealistic XL only (Colab)
- Default style: **Fooocus Semi Realistic** (quality negative only)
- Sunside styles = **look only** (phone grain, night ISO, steam…) — not scene/framing
- NSFW blackout: off

## Simple UI
1. **Prompt** = сцена, поза, кадр, одяг (головне)
2. **Character** (опційно) → лише якір зовнішності + negative identity
3. **Styles** → look зображення (опційно 1 Sunside + Semi Realistic)
4. **Size** → Generate

## Characters
Folder layout:

```
characters/<id>/
  character.json
  anchor.txt
  negative.txt
  preview.jpg
  face_ref.jpg   # optional, for Face lock
```

## Face lock

**Вимкнено в product mode.** Inswapper/insightface на Colab валить процес (OOM/SIGKILL) навіть на CPU — `try/except` це не рятує.

Однаковість обличчя зараз: Character `anchor.txt` + промпт + face LoRA в пресеті.

## Export names
Files save as `{character}_{style}_{timestamp}_{rand}.png` when product prefix is set.

## Full Fooocus UI
```bash
python launch.py --preset realistic_cyberrealistic_xl --disable-sunside-product
```
