# Fooocus Sunside

Форк [Fooocus](https://github.com/lllyasviel/Fooocus) для **Google Colab**: фотореалізм, без цензури, вибір preset.

**Репозиторій:** https://github.com/sunsideaspect/foocus_sunside  

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sunsideaspect/foocus_sunside/blob/main/fooocus_colab.ipynb)

## Швидкий старт (Colab)

1. **Runtime → GPU (T4 / L4 / A100)** → **Restart session**
2. **Run all** — перший запуск **10–20 хв** (завантаження моделей)
3. У комірці **«КРОК 2 — Обери модель»** вибери **Juggernaut** або **RealCore XL**
4. Дочекайся в launch-комірці **`App started successful`**
5. Відкрий **`https://….gradio.live`** з виводу комірки

**Моделі (вибір у Colab, комірка «КРОК 2»):**

| Preset | Checkpoint | Розмір |
|--------|------------|--------|
| `realistic_juggernaut_ragnarok` | Juggernaut XL Ragnarok | ~7 GB |
| `realistic_realcore_xl` | [RealCore XL](https://huggingface.co/rityak/RealCoreXL) | ~13 GB |

Завантажується **лише обрана** модель + спільні LoRA (anatomy, add_detail, [face-helper](https://huggingface.co/ostris/face-helper-sdxl-lora)).  
**Прапорці:** `--disable-censor`, `--disable-pro-mode`, `--disable-preset-selection`

## Що всередині

| Файл | Призначення |
|------|-------------|
| `fooocus_colab.ipynb` | Єдиний Colab-ноутбук |
| `presets/realistic_juggernaut_ragnarok.json` | Juggernaut + LoRA + кроки |
| `presets/realistic_realcore_xl.json` | RealCore XL + LoRA + кроки |
| `docs/PRESENTATION_PM_UA.md` | Презентація для PM |
| `docs/fooocus-pro-presentation.html` | HTML-слайди |

## Локальний запуск (NVIDIA)

```bash
python launch.py --preset realistic_juggernaut_ragnarok --disable-censor --disable-pro-mode --disable-preset-selection
```

Потрібна відеокарта NVIDIA з CUDA (мінімум ~4 GB VRAM).

## Презентація

[Презентація Fooocus Pro](https://htmlpreview.github.io/?https://raw.githubusercontent.com/sunsideaspect/foocus_sunside/main/docs/fooocus-pro-presentation.html)

## Ліцензія

Базовий Fooocus — [GPL-3.0](https://github.com/lllyasviel/Fooocus). Форк sunsideaspect — Colab + preset + без blur.
