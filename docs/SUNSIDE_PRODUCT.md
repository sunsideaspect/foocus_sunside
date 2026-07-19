# Sunside Product Mode

Slim Fooocus UI for NSFW photoreal visual factory.

## Defaults
- Product mode **ON** (disable with `--disable-sunside-product` or `SUNSIDE_PRODUCT=0`)
- Model: CyberRealistic XL only (Colab)
- Styles: Sunside pack + Fooocus Semi Realistic
- NSFW blackout: off

## Simple UI
1. **Character** checkbox → Aria / Mila / Vera (prompt anchor auto-injected)
2. **Scenario** chips → style + size + optional batch×4
3. **Size** presets or Custom W×H (512–1536, step 8)
4. Prompt = scene only → Generate

## Characters
Folder layout:

```
characters/<id>/
  character.json
  anchor.txt
  negative.txt
  preview.jpg
  face_ref.jpg   # optional, for Face pass
```

## Face pass
Not stock Fooocus FaceSwap (VRAM crash on Colab).

Optional post-step Inswapper when:
- Character ON
- `face_ref.jpg` present
- Face pass checkbox ON
- `insightface` installed + `models/insightface/inswapper_128.onnx`

## Export names
Files save as `{character}_{style}_{timestamp}_{rand}.png` when product prefix is set.

## Full Fooocus UI
```bash
python launch.py --preset realistic_cyberrealistic_xl --disable-sunside-product
```
