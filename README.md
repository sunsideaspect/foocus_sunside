# Fooocus Sunside

Форк [Fooocus](https://github.com/lllyasviel/Fooocus) для **Google Colab**: фотореалізм, без цензури, один preset.

**Репозиторій:** https://github.com/sunsideaspect/foocus_sunside  

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sunsideaspect/foocus_sunside/blob/main/fooocus_colab.ipynb)

## Швидкий старт (Colab)

1. **Runtime → GPU (T4 / L4 / A100)** → **Restart session**
2. **Run all** — перший запуск **10–20 хв** (завантаження моделей)
3. У launch-комірці дочекайся **`App started successful`**
4. Відкрий **`https://….gradio.live`** з виводу комірки

**Preset:** `realistic_juggernaut_ragnarok` (Juggernaut XL Ragnarok + anatomy LoRAs)  
**Прапорці:** `--disable-censor`, `--disable-pro-mode`, `--disable-preset-selection`

## Що всередині

| Файл | Призначення |
|------|-------------|
| `fooocus_colab.ipynb` | Єдиний Colab-ноутбук |
| `presets/realistic_juggernaut_ragnarok.json` | Модель + LoRA + кроки |
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
