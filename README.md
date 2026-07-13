# Fooocus Sunside

Форк [Fooocus](https://github.com/lllyasviel/Fooocus) для **Google Colab**: фотореалізм, face + body, без цензури.

**Репозиторій:** https://github.com/sunsideaspect/foocus_sunside  

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sunsideaspect/foocus_sunside/blob/main/fooocus_colab.ipynb)

## Швидкий старт (Colab)

1. **Runtime → GPU (T4 / L4 / A100)** → **Restart session**
2. **Run all** — перший запуск **10–20 хв** (завантаження моделей)
3. У комірці **«КРОК 2»** — за замовчуванням **Juggernaut** (full body + face)
4. Дочекайся в launch-комірці **`App started successful`**
5. Відкрий **`https://….gradio.live`** з виводу комірки

**Моделі (вибір у Colab, комірка «КРОК 2»):**

| Preset | Checkpoint | Коли брати |
|--------|------------|------------|
| `realistic_cyberrealistic_xl` | [CyberRealistic XL V10](https://huggingface.co/cyberdelia/CyberRealisticXL) (~6.5 GB) | **Default:** чистий фотореал |
| `realistic_epicrealism_xl` | epiCRealism XL Pure (~7 GB) | Люди / тіло |
| `realistic_juggernaut_ragnarok` | Juggernaut XL Ragnarok (~7 GB) | Full body + universal |
| `realistic_realvis_xl` | [RealVisXL V5](https://huggingface.co/SG161222/RealVisXL_V5.0) (~6.5 GB) | Портрет / лице |
| `realistic_realcore_xl` | [RealCore XL](https://huggingface.co/rityak/RealCoreXL) (~13 GB) | Soft photo (експеримент; OOM на T4) |

Спільні LoRA (ideal, баланс тіло+лице): `bodyproportion` (~0.7), Sufficient Nudity (~0.4), SOAP (~0.18), **face-helper ON** (~0.45–0.5).  
Styles: **Sunside Iphone Selfie** + **Fooocus Semi Realistic**.

**Прапорці:** `--disable-censor`, `--disable-pro-mode`, `--disable-preset-selection`

## Що всередині

| Файл | Призначення |
|------|-------------|
| `fooocus_colab.ipynb` | Єдиний Colab-ноутбук |
| `presets/realistic_juggernaut_ragnarok.json` | Juggernaut + LoRA |
| `presets/realistic_cyberrealistic_xl.json` | CyberRealistic XL V10 |
| `presets/realistic_epicrealism_xl.json` | epiCRealism XL Pure |
| `presets/realistic_realvis_xl.json` | RealVis + LoRA |
| `presets/realistic_realcore_xl.json` | RealCore XL + LoRA |
| `sdxl_styles/sdxl_styles_sunside.json` | Phone / amateur стилі |
| `docs/PRESENTATION_PM_UA.md` | Презентація для PM |
| `docs/fooocus-pro-presentation.html` | HTML-слайди |

## Локальний запуск (NVIDIA)

```bash
python launch.py --preset realistic_cyberrealistic_xl --disable-censor --disable-pro-mode --disable-preset-selection
```

Потрібна відеокарта NVIDIA з CUDA (мінімум ~4 GB VRAM).

## Презентація

[Презентація Fooocus Pro](https://htmlpreview.github.io/?https://raw.githubusercontent.com/sunsideaspect/foocus_sunside/main/docs/fooocus-pro-presentation.html)

## Ліцензія

Базовий Fooocus — [GPL-3.0](https://github.com/lllyasviel/Fooocus). Форк sunsideaspect — Colab + preset + без blur.
