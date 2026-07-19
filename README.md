# Sunside Visual Factory

Форк [Fooocus](https://github.com/lllyasviel/Fooocus) → **продакшн-фабрика** реалістичних NSFW / amateur кадрів (Colab).

**Репозиторій:** https://github.com/sunsideaspect/foocus_sunside  

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sunsideaspect/foocus_sunside/blob/main/fooocus_colab.ipynb)

## Швидкий старт (Colab)

1. **Runtime → GPU** → **Restart session**
2. **Run all** (10–20 хв перший раз)
3. Дочекайся **`App started successful`**
4. Відкрий **`https://….gradio.live`**

### Simple flow
**Character** (опційно) → **Scenario / Style** → **Size** → промпт сцени → **Generate**

## Product mode (за замовчуванням)

- Одна модель: **CyberRealistic XL** + emotional / face / body LoRA
- Стилі: лише **Sunside** (+ Semi Realistic)
- Чекбокс **Character**: Aria / Mila / Vera (якір у промпт)
- **Size**: Story / Square / Landscape / Landing / Custom W×H
- **Scenario** chips для швидких сцен + batch×4
- Black Out NSFW вимкнено
- Імена файлів: `aria_hidden_camera_….png`

Повний Fooocus UI: `--disable-sunside-product` або `SUNSIDE_PRODUCT=0`.

Деталі: [docs/SUNSIDE_PRODUCT.md](docs/SUNSIDE_PRODUCT.md)

## Characters

```
characters/<id>/character.json
characters/<id>/anchor.txt
characters/<id>/negative.txt
characters/<id>/preview.jpg
characters/<id>/face_ref.jpg   # optional → Face pass
```

## Face consistency

Stock **FaceSwap** (Image Prompt) на Colab часто крашиться — не використовувати.

Опційний **Face pass** (Inswapper) після генерації, якщо є `face_ref.jpg` + insightface.

## Прапорці запуску

`--disable-censor` · `--disable-pro-mode` · `--disable-preset-selection` · product ON by default
