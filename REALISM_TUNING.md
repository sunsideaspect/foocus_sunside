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

For maximum prompt-following with minimal auto-corrections, use:

```bash
python entry_with_update.py --preset realistic_direct_prompt
```

For reducing "same default face" bias across generations, use:

```bash
python entry_with_update.py --preset realistic_diverse
```

For the strongest one-click preset (extra steps + stronger structure/detail control), use:

```bash
python entry_with_update.py --preset realistic_super
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
- runs automatic structure control during enhance passes using ControlNet Canny + CPDS from the current image
- stores only final enhanced outputs by default to reduce noisy intermediate picks

This is an approximation-based scorer, not a semantic human judge, but it usually removes the weakest outputs automatically.

## Direct prompt preset (minimum interference)

`realistic_direct_prompt` is tuned to reduce pipeline "override" behavior:

- `default_pro_mode_enabled = false` (no auto ranking / keep-top filtering)
- `default_pro_mode_detail_pass_enabled = false`
- `default_pro_mode_structure_control_enabled = false`
- lighter negative prompt to avoid over-blocking prompt intent
- single-image default (`default_image_number = 1`) to simplify direct comparisons
- image-prompt UI is off by default and IP type defaults to `ImagePrompt` (not `FaceSwap`) to avoid hidden identity lock

If your prompt is still constrained, start from this preset and only then enable extra modules one by one.

## Diverse faces preset (anti face-lock)

`realistic_diverse` is tuned for stronger facial variety:

- switches base model to `juggernautXL_v8Rundiffusion`
- disables style LoRAs by default
- keeps pro/detail/structure controls disabled
- starts on `uov_tab` with image-prompt off by default
- uses lighter CFG/steps defaults to avoid collapsing to one repeated face

## Super preset (maximum quality defaults)

`realistic_super` is an aggressive variant of `realistic_pro` for quick "max quality" tests:

- higher default steps (`default_overwrite_step = 84`)
- stronger local detail pass (`default_pro_mode_detail_strength = 0.42`)
- stronger structure control (`canny_weight = 0.95`, `cpds_weight = 0.8`)
- moderate batch size (`default_image_number = 6`) to keep runtime practical

### Pro structure-control tuning

`realistic_pro` now includes a stage-3 structure pass to stabilize anatomy/silhouette while enhancing:

- `default_pro_mode_structure_control_enabled`
- `default_pro_mode_structure_use_canny`
- `default_pro_mode_structure_use_cpds`
- `default_pro_mode_structure_canny_stop / weight`
- `default_pro_mode_structure_cpds_stop / weight`

If output becomes too rigid, reduce structure weights slightly (`-0.05` to `-0.15`) or disable one branch (`canny` or `cpds`).

## Practical limits

- This pipeline can strongly preserve identity, but it cannot guarantee exact 1:1 identity in every pose, angle, or lighting setup.
- Extreme prompt changes (e.g., profile view from frontal-only source) will reduce similarity.
