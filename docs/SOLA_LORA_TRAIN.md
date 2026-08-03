# Sola Face LoRA — тренування

## Що вже зроблено локально
- Сирий датасет: `datasets/sola_face/` (121 файл)
- Відхилені: `datasets/sola_face/_rejected/` (14)
- Готово до train: **107** jpg + captions у  
  `datasets/sola_face_train/`  
  і Kohya-структура: `datasets/sola_face_kohya/10_sola_face/`
- Trigger: **`sola_face`**
- Скрипт повтору: `python tools/prepare_sola_dataset.py`

## Colab
Відкрий: [sola_face_lora_colab.ipynb](../sola_face_lora_colab.ipynb)

1. Runtime → GPU  
2. Завантаж локальний zip: `datasets/sola_face_kohya.zip` (~26 MB)  
3. Run all  
4. Скачай `sola_face_sdxl.safetensors`

Конфіг (довідково): `configs/sola_face_lora.toml`

## Після трену — Fooocus / Sunside
1. Поклади LoRA в `models/loras/sola_face_sdxl.safetensors`
2. Character → **Sola**
3. Prompt починай з `sola_face,` + сцена (без дубля обличчя)
4. Weight LoRA ≈ **0.8–1.0** (у Models / LoRAs)

Приклад:
```
sola_face, standing nude in minimal apartment, grey sofa, window light, soft teasing look at camera
```

## Нотатки
- Водяні знаки в датасеті ще можуть бути — якщо LoRA малює текст, виріж/замаж 5–10 найгірших і перетренуй.
- T4 тягне SDXL LoRA повільно; A100/L4 краще.
