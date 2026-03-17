# Realism and Face-Preservation Tuning

This fork is tuned to prioritize photorealistic outputs and stronger face preservation from a reference image.

## Quick start

Use the new preset:

```bash
python entry_with_update.py --preset realistic_identity
```

For an automated best-of-N flow (generate many, keep top-ranked), use:

```bash
python entry_with_update.py --preset realistic_pro
```

The preset enables:

- `Quality` performance mode
- realistic stock-photo model defaults
- image prompt panel by default
- first image prompt slot set to `FaceSwap` with stronger stop/weight
- second image prompt slot reserved for optional second `FaceSwap` reference
- style list disabled by default to reduce identity drift

## Recommended workflow for face-preserving generations

1. Open **Input Image** -> **Image Prompt**.
2. Put the target face in slot #1 (`FaceSwap`).
3. Use a clean, front-facing source portrait for best identity retention.
4. Keep prompts focused on scene, lens, lighting, and clothing instead of face shape.
5. Start with the preset defaults:
   - `FaceSwap #1 stop`: `0.99`
   - `FaceSwap #1 weight`: `1.35`
   - optional `FaceSwap #2` for a second source photo
6. If identity is weak:
   - increase weight in small steps (`+0.05`)
   - keep stop very high (`0.98-0.99`)
   - add a second reference image of the same person in slot #2 (`FaceSwap`)
7. If composition is too rigid or artifacts appear:
   - decrease weight slightly
   - lower stop to `0.95-0.97`

## Quality controls (most impactful)

- **Performance**: keep `Quality` for detail fidelity.
- **Steps**: higher steps improve texture consistency (identity preset uses a high default override).
- **Sampler/Scheduler**: `dpmpp_2m_sde_gpu + karras` is kept as default.
- **Styles**: the identity preset disables styles by default to minimize face drift.

## Lock-identity mode (when "still not the same person")

Use this checklist:

1. Use square output (`1024x1024`) and `Image Number = 1`.
2. Keep only face references (`FaceSwap`) in image prompt slots.
3. Avoid face-shape words in prompt (jawline, nose shape, lip shape, eye shape).
4. Keep `CFG` in the moderate range (`3.4-4.0`).
5. Keep `Steps` high (`64-80`).
6. Generate a small batch with fixed seed, choose the closest face, then iterate that seed.

## Pro mode (automatic ranking)

`realistic_pro` adds a first-stage ranking system to reduce manual cherry-picking:

- generates a larger batch (`default_image_number = 8`)
- scores candidates by detail/contrast/exposure/entropy proxies
- keeps only the top results (`default_pro_mode_keep_count = 2`)
- runs automatic local detail passes for `face`, `hand`, and `body` using SAM masks + inpaint
- stores only final enhanced outputs by default to reduce noisy intermediate picks

This is an approximation-based scorer, not a semantic human judge, but it usually removes the weakest outputs automatically.

## Practical limits

- This pipeline can strongly preserve identity, but it cannot guarantee exact 1:1 identity in every pose, angle, or lighting setup.
- Extreme prompt changes (e.g., profile view from frontal-only source) will reduce similarity.
