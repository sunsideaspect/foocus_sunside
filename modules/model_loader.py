import os
import shutil
from urllib.parse import urlparse, unquote
from typing import Optional
from urllib.request import Request, urlopen


def _parse_hf_url(url: str):
    """Parse https://huggingface.co/{repo}/resolve/{rev}/{path} into parts."""
    try:
        p = urlparse(url)
        if p.netloc not in ("huggingface.co", "hf.co") and "huggingface.co" not in url:
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
    """Download with a browser-like User-Agent (HF often 403s bare torch.hub/urllib)."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
    }
    req = Request(url, headers=headers)
    tmp = cached_file + ".tmp"
    try:
        with urlopen(req, timeout=120) as resp, open(tmp, "wb") as out:
            total = resp.headers.get("Content-Length")
            total_n = int(total) if total and total.isdigit() else None
            done = 0
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                done += len(chunk)
                if progress and total_n:
                    pct = int(100 * done / total_n)
                    print(f"\rDownloading: {pct}% ({done}/{total_n})", end="", flush=True)
        if progress:
            print()
        os.replace(tmp, cached_file)
    except Exception:
        if os.path.isfile(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        raise


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

    print(f'Downloading: "{url}" to {cached_file}\n')

    # 1) Prefer huggingface_hub (handles auth, mirrors, Colab 403)
    hf_parts = _parse_hf_url(url)
    if hf_parts is not None:
        repo_id, revision, repo_file = hf_parts
        try:
            from huggingface_hub import hf_hub_download
            downloaded = hf_hub_download(
                repo_id=repo_id,
                filename=repo_file,
                revision=revision,
                local_dir=None,
            )
            shutil.copy2(downloaded, cached_file)
            return cached_file
        except Exception as e:
            print(f'[Download] huggingface_hub failed ({e}); trying urllib…')

    # 2) urllib with User-Agent (fixes many HF 403 from Colab/torch.hub)
    try:
        _download_with_urllib(url, cached_file, progress=progress)
        return cached_file
    except Exception as e:
        print(f'[Download] urllib failed ({e}); trying torch.hub…')

    # 3) Legacy fallback
    from torch.hub import download_url_to_file
    download_url_to_file(url, cached_file, progress=progress)
    return cached_file
