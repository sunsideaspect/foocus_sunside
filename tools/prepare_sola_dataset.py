#!/usr/bin/env python3
"""Prepare sola_face dataset for SDXL face LoRA training.

- Reject images with short side < 512 (and known tiny originals)
- Convert webp/jpeg → jpg in datasets/sola_face_train/
- Write caption .txt next to each image with trigger sola_face
- Copy rejects to datasets/sola_face/_rejected/
"""
from __future__ import annotations

import shutil
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    import subprocess
    import sys

    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow", "-q"])
    from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "datasets" / "sola_face"
TRAIN = ROOT / "datasets" / "sola_face_train"
REJECT = SRC / "_rejected"
TRIGGER = "sola_face"
MIN_SHORT = 512

# Always reject these known thumbnails / bad crops if still present
FORCE_REJECT = {
    "1.jpg",
    "2.jpg",
    "3.jpg",
    "4.jpg",
    "5.jpg",
    "7.jpg",
    "73.jpg",
    "1111.jpg",
    "123.jpg",
    "2222.jpg",
}

CAPTION = (
    f"{TRIGGER}, photo of a woman, adult woman, long straight brown hair, "
    f"middle part, dark brown eyes, soft oval face, natural skin texture, "
    f"looking at camera"
)


def main() -> None:
    if not SRC.is_dir():
        raise SystemExit(f"Missing source: {SRC}")

    if TRAIN.exists():
        shutil.rmtree(TRAIN)
    TRAIN.mkdir(parents=True)
    REJECT.mkdir(parents=True)

    exts = {".jpg", ".jpeg", ".png", ".webp"}
    files = sorted(
        [p for p in SRC.iterdir() if p.is_file() and p.suffix.lower() in exts],
        key=lambda p: p.name.lower(),
    )

    kept = rejected = 0
    for src in files:
        name = src.name
        try:
            with Image.open(src) as im:
                im = im.convert("RGB")
                w, h = im.size
                short = min(w, h)
        except Exception as e:
            print(f"FAIL {name}: {e}")
            shutil.copy2(src, REJECT / name)
            rejected += 1
            continue

        # ultra-wide thin crops are usually bad for face LoRA
        aspect = max(w, h) / max(short, 1)
        bad = (
            name in FORCE_REJECT
            or short < MIN_SHORT
            or (short < 600 and aspect > 1.7)
        )
        if bad:
            dest = REJECT / name
            if not dest.exists():
                shutil.copy2(src, dest)
            print(f"REJECT {name} ({w}x{h})")
            rejected += 1
            continue

        out_name = f"{src.stem}.jpg"
        out_img = TRAIN / out_name
        # avoid collision if both .jpg and .webp share stem
        n = 1
        while out_img.exists():
            out_name = f"{src.stem}_{n}.jpg"
            out_img = TRAIN / out_name
            n += 1

        im.save(out_img, format="JPEG", quality=95, optimize=True)
        (TRAIN / f"{out_img.stem}.txt").write_text(CAPTION + "\n", encoding="utf-8")
        print(f"KEEP   {name} -> {out_img.name} ({w}x{h})")
        kept += 1

    # Kohya folder naming: <repeats>_<class>
    # Symlink/copy train images into numbered folder for easy zip upload
    kohya = ROOT / "datasets" / "sola_face_kohya" / "10_sola_face"
    if kohya.exists():
        shutil.rmtree(kohya.parent)
    kohya.mkdir(parents=True)
    for p in TRAIN.iterdir():
        shutil.copy2(p, kohya / p.name)

    print("---")
    print(f"kept={kept} rejected={rejected}")
    print(f"train_dir={TRAIN}")
    print(f"kohya_dir={kohya}")
    print(f"trigger={TRIGGER}")


if __name__ == "__main__":
    main()
