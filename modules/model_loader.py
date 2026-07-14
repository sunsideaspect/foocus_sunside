import os
import shutil
from urllib.parse import urlparse, unquote
from typing import Optional
from urllib.request import Request, urlopen


# Colab + HF Xet інколи «висить» без прогресу
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")


def _parse_hf_url(url: str):
    """Parse https://huggingface.co/{repo}/resolve/{rev}/{path} into parts."""
    try:
        p = urlparse(url)
        host = (p.netloc or "").lower()
        if "huggingface.co" not in host and host not in ("hf.co",):
            if "resolve" not in p.path:
                return None
        parts = [unquote(x) for x in p.path.strip("/").split("/") if x]
        if "resolve" not in parts:
            return None
        i = parts.index("resolve")
        if i < 1 or i + 2 > len(parts):
            return None
        repo_id = "/".join(parts[:i])
        revision = parts[i + 1]
        filename = "/".join(parts[i + 2:])
        if not repo_id or not filename:
            return None
        return repo_id, revision, filename
    except Exception:
        return None


def _download_with_urllib(url: str, cached_file: str, progress: bool = True) -> None:
    """Download with a browser-like User-Agent (helps some HF 403 cases)."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
    }
    # Optional HF token (Colab secrets / env) — зменшує 403 на LFS
    token = (
        os.environ.get("HF_TOKEN")
        or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        or os.environ.get("HUGGINGFACE_HUB_TOKEN")
    )
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = Request(url, headers=headers)
    tmp = cached_file + ".tmp"
    try:
        with urlopen(req, timeout=180) as resp, open(tmp, "wb") as out:
            total = resp.headers.get("Content-Length")
            total_n = int(total) if total and total.isdigit() else None
            done = 0
            last_pct = -1
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                done += len(chunk)
                if progress:
                    if total_n:
                        pct = int(100 * done / total_n)
                        if pct != last_pct:
                            print(f"\r  → {pct}% ({done}/{total_n} bytes)", end="", flush=True)
                            last_pct = pct
                    else:
                        print(f"\r  → {done} bytes", end="", flush=True)
        if progress:
            print(flush=True)
        os.replace(tmp, cached_file)
    except Exception:
        if os.path.isfile(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        raise


def _download_with_hf_hub(url: str, cached_file: str) -> None:
    hf_parts = _parse_hf_url(url)
    if hf_parts is None:
        raise ValueError("Not a Hugging Face resolve URL")
    repo_id, revision, repo_file = hf_parts
    from huggingface_hub import hf_hub_download

    print(f"  [download] huggingface_hub ← {repo_id}/{repo_file}", flush=True)
    downloaded = hf_hub_download(
        repo_id=repo_id,
        filename=repo_file,
        revision=revision,
    )
    shutil.copy2(downloaded, cached_file)


def load_file_from_url(
        url: str,
        *,
        model_dir: str,
        progress: bool = True,
        file_name: Optional[str] = None,
) -> str:
    """Download a file from `url` into `model_dir`, using the file present if possible.

    Returns the path to the downloaded file.
    """
    domain = os.environ.get("HF_MIRROR", "https://huggingface.co").rstrip('/')
    url = str.replace(url, "https://huggingface.co", domain, 1)
    os.makedirs(model_dir, exist_ok=True)
    if not file_name:
        parts = urlparse(url)
        file_name = os.path.basename(parts.path)
    cached_file = os.path.abspath(os.path.join(model_dir, file_name))
    if os.path.exists(cached_file) and os.path.getsize(cached_file) > 0:
        return cached_file

    print(f'Downloading: "{url}" to {cached_file}', flush=True)

    hf_parts = _parse_hf_url(url)
    errors = []

    # 1) Hugging Face LFS: always prefer hub (urllib часто 403 на великих .safetensors з Colab)
    if hf_parts is not None:
        try:
            _download_with_hf_hub(url, cached_file)
            print(f"  [download] ok ({os.path.getsize(cached_file)} bytes)", flush=True)
            return cached_file
        except Exception as e:
            errors.append(f"huggingface_hub: {e}")
            print(f"  [download] huggingface_hub failed: {e}", flush=True)

    # 2) urllib (+ optional HF_TOKEN)
    try:
        print("  [download] urllib…", flush=True)
        _download_with_urllib(url, cached_file, progress=progress)
        print(f"  [download] ok ({os.path.getsize(cached_file)} bytes)", flush=True)
        return cached_file
    except Exception as e:
        errors.append(f"urllib: {e}")
        print(f"  [download] urllib failed: {e}", flush=True)

    # 3) Legacy
    try:
        print("  [download] torch.hub…", flush=True)
        from torch.hub import download_url_to_file
        download_url_to_file(url, cached_file, progress=progress)
        return cached_file
    except Exception as e:
        errors.append(f"torch.hub: {e}")
        raise RuntimeError(
            "Не вдалось завантажити з Hugging Face.\n"
            + "\n".join(errors)
            + "\n\nЯкщо 403: у Colab додай Secret HF_TOKEN "
            "(https://huggingface.co/settings/tokens) → Restart → Run all."
        ) from e
