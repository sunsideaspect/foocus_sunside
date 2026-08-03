# Paste this ENTIRE cell into your CURRENT Colab session and run it.
# It prints train.log (if any) and runs a minimal Kohya SDXL LoRA train with LIVE output.

import os, sys, glob, shutil, subprocess, zipfile
from pathlib import Path

print("===== EXISTING LOG (if any) =====")
log_path = "/content/outputs/sola_face_lora/train.log"
if os.path.isfile(log_path):
    txt = open(log_path, encoding="utf-8", errors="replace").read()
    print(txt[-15000:] if len(txt) > 15000 else txt)
else:
    print("(no train.log yet)")

# Ensure sd-scripts
if not os.path.isdir("/content/sd-scripts"):
    %cd /content
    !git clone --depth 1 https://github.com/kohya-ss/sd-scripts.git /content/sd-scripts
    %cd /content/sd-scripts
    !pip -q install accelerate==0.31.0 transformers==4.41.2 diffusers==0.29.2 safetensors ftfy einops opencv-python-headless toml voluptuous bitsandbytes==0.43.1
else:
    %cd /content/sd-scripts

# Find dataset
found = None
for root, dirs, files in os.walk("/content"):
    if "10_sola_face" in dirs:
        # prefer sola_data
        cand = os.path.join(root, "10_sola_face")
        if "/sola_data" in cand.replace("\\", "/") or found is None:
            found = cand
            if "/sola_data" in cand.replace("\\", "/"):
                break

if not found:
    print("Dataset not found. Upload sola_face_kohya.zip now...")
    from google.colab import files
    os.makedirs("/content/sola_data", exist_ok=True)
    os.chdir("/content/sola_data")
    up = files.upload()
    for name in up:
        if name.lower().endswith(".zip"):
            zipfile.ZipFile(name).extractall("/content/sola_data")
    for root, dirs, files in os.walk("/content/sola_data"):
        if "10_sola_face" in dirs:
            found = os.path.join(root, "10_sola_face")
            break

assert found, "Still no 10_sola_face — upload foocus_new/datasets/sola_face_kohya.zip"
TRAIN_ROOT = os.path.dirname(found)
OUT = "/content/outputs/sola_face_lora"
os.makedirs(OUT, exist_ok=True)
n = len([f for f in os.listdir(found) if f.lower().endswith(".jpg")])
print("FOUND", found, "images", n, "TRAIN_ROOT", TRAIN_ROOT)

os.chdir("/content/sd-scripts")
cmd = [
    sys.executable, "sdxl_train_network.py",
    "--pretrained_model_name_or_path=stabilityai/stable-diffusion-xl-base-1.0",
    f"--train_data_dir={TRAIN_ROOT}",
    f"--output_dir={OUT}",
    "--output_name=sola_face_sdxl",
    "--save_model_as=safetensors",
    "--save_precision=fp16",
    "--caption_extension=.txt",
    "--resolution=512,512",
    "--enable_bucket",
    "--min_bucket_reso=256",
    "--max_bucket_reso=1024",
    "--train_batch_size=1",
    "--gradient_checkpointing",
    "--max_train_epochs=5",
    "--save_every_n_epochs=1",
    "--learning_rate=1e-4",
    "--unet_lr=1e-4",
    "--text_encoder_lr=5e-5",
    "--lr_scheduler=cosine",
    "--lr_warmup_steps=20",
    "--optimizer_type=AdamW",
    "--network_module=networks.lora",
    "--network_dim=8",
    "--network_alpha=8",
    "--mixed_precision=fp16",
    "--cache_latents",
    "--cache_latents_to_disk",
    "--seed=42",
    "--keep_tokens=1",
    "--max_data_loader_n_workers=0",
]
env = os.environ.copy()
env["PYTHONPATH"] = "/content/sd-scripts" + os.pathsep + env.get("PYTHONPATH", "")
env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

print("===== TRAIN LIVE =====")
print(" ".join(cmd))
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, cwd="/content/sd-scripts")
lines = []
for line in p.stdout:
    print(line, end="")
    lines.append(line)
code = p.wait()
open(OUT + "/train_live.log", "w", encoding="utf-8").write("".join(lines))
paths = glob.glob(OUT + "/**/*.safetensors", recursive=True)
print("exit", code, "safetensors", paths)

if code != 0 or not paths:
    print("\n===== COPY FROM HERE TO CHAT =====\n")
    print("".join(lines[-200:]))
    raise RuntimeError("Failed — paste the COPY block above")
else:
    from google.colab import files
    best = [p for p in paths if "sola_face_sdxl" in os.path.basename(p)] or paths
    files.download(sorted(best, key=os.path.getmtime)[-1])
    print("SUCCESS downloaded")
