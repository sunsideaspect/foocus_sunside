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

## Face lock (рекомендовано)

1. Character ON  
2. Завантаж еталон обличчя в UI (**Face ref**) — анфас, чисте лице  
3. Галочка **Face lock після генерації**  
4. Generate  

Пайплайн: SDXL кадр → unload VRAM → Inswapper swap → збереження.  
Старий Image Prompt **FaceSwap** лишається вимкненим (OOM на Colab).

Пакет: `insightface` + `onnxruntime-gpu` (ставить Colab). Модель `inswapper_128.onnx` качається сама в `models/insightface/`.

## Export names
Files save as `{character}_{style}_{timestamp}_{rand}.png` when product prefix is set.

## Full Fooocus UI
```bash
python launch.py --preset realistic_cyberrealistic_xl --disable-sunside-product
```
