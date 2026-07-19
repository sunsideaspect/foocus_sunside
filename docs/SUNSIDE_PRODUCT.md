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

## Face lock (опційно)

1. Character ON  
2. Завантаж еталон обличчя в UI (**Face ref**) — анфас, чисте лице  
3. Галочка **Face lock після генерації**  
4. Generate  

Пайплайн: SDXL кадр → unload VRAM → Inswapper swap → збереження.  
Старий Image Prompt **FaceSwap** лишається вимкненим (OOM на Colab).

Пакет: `insightface` + `onnxruntime` **CPU** (ставить Colab). Після SDXL GPU ORT часто вбиває сесію — тому Face lock на CPU за замовчуванням (`SUNSIDE_FACELOCK_CPU=1`). Модель `inswapper_128.onnx` качається сама в `models/insightface/`.

## Export names
Files save as `{character}_{style}_{timestamp}_{rand}.png` when product prefix is set.

## Full Fooocus UI
```bash
python launch.py --preset realistic_cyberrealistic_xl --disable-sunside-product
```
