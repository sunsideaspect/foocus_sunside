import os
import shutil
from urllib.parse import urlparse, unquote
from typing import Optional, List
from urllib.request import Request, urlopen


def _force_disable_xet() -> None:
    os.environ["HF_HUB_DISABLE_XET"] = "1"
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"


_force_disable_xet()


def _parse_hf_url(url: str):
    """Parse https://huggingface.co/{repo}/resolve/{rev}/{path} into parts."""
    try:
        p = urlparse(url)
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


def _candidate_urls(url: str) -> List[str]:
    """Original URL + optional HF mirrors (Xet CDN often 403 on Colab)."""
    out = [url]
    mirror = os.environ.get("HF_MIRROR", "").rstrip("/")
    if mirror and "huggingface.co" in url:
        out.append(url.replace("https://huggingface.co", mirror, 1))
    # Public community mirror (helps when us.gcp.cdn.hf.co Xet fails)
    if "huggingface.co" in url:
        out.append(url.replace("https://huggingface.co", "https://hf-mirror.com", 1))
    # de-dupe preserve order
    seen = set()
    uniq = []
    for u in out:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq


def _auth_headers() -> dict:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
    }
    token = (
        os.environ.get("HF_TOKEN")
        or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        or os.environ.get("HUGGINGFACE_HUB_TOKEN")
    )
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _download_with_urllib(url: str, cached_file: str, progress: bool = True) -> None:
    req = Request(url, headers=_auth_headers())
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
                        pct = min(100, int(100 * done / total_n))
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


def _download_with_hf_hub(repo_id: str, revision: str, repo_file: str, cached_file: str) -> None:
    _force_disable_xet()
    from huggingface_hub import hf_hub_download

    print(f"  [download] huggingface_hub ← {repo_id}/{repo_file}", flush=True)
    downloaded = hf_hub_download(
        repo_id=repo_id,
        filename=repo_file,
        revision=revision,
        force_download=False,
    )
    # Reject Xet failure artifacts? hub raises on 403
    shutil.copy2(downloaded, cached_file)


def _download_with_wget(url: str, cached_file: str) -> None:
    import subprocess
    tmp = cached_file + ".tmp"
    cmd = [
        "wget", "-q", "--show-progress", "--progress=dot:giga",
        "-O", tmp, url,
        "--header", f"User-Agent: {_auth_headers()['User-Agent']}",
    ]
    token = _auth_headers().get("Authorization")
    if token:
        cmd.extend(["--header", f"Authorization: {token}"])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.isfile(tmp) or os.path.getsize(tmp) == 0:
        if os.path.isfile(tmp):
            os.remove(tmp)
        raise RuntimeError((r.stderr or r.stdout or "wget failed").strip()[:500])
    os.replace(tmp, cached_file)


def load_file_from_url(
        url: str,
        *,
        model_dir: str,
        progress: bool = True,
        file_name: Optional[str] = None,
) -> str:
    """Download a file from `url` into `model_dir`, using the file present if possible."""
    _force_disable_xet()

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
    errors = []
    hf_parts = _parse_hf_url(url)

    # 1) huggingface_hub with Xet disabled (best for large LFS)
    if hf_parts is not None:
        repo_id, revision, repo_file = hf_parts
        try:
            _download_with_hf_hub(repo_id, revision, repo_file, cached_file)
            print(f"  [download] ok ({os.path.getsize(cached_file)} bytes)", flush=True)
            return cached_file
        except Exception as e:
            errors.append(f"huggingface_hub: {e}")
            print(f"  [download] huggingface_hub failed: {e}", flush=True)

    # 2) urllib / wget over original + mirrors
    for cand in _candidate_urls(url):
        try:
            print(f"  [download] urllib ← {cand}", flush=True)
            _download_with_urllib(cand, cached_file, progress=progress)
            print(f"  [download] ok ({os.path.getsize(cached_file)} bytes)", flush=True)
            return cached_file
        except Exception as e:
            errors.append(f"urllib({cand}): {e}")
            print(f"  [download] urllib failed: {e}", flush=True)
        try:
            print(f"  [download] wget ← {cand}", flush=True)
            _download_with_wget(cand, cached_file)
            print(f"  [download] ok ({os.path.getsize(cached_file)} bytes)", flush=True)
            return cached_file
        except Exception as e:
            errors.append(f"wget({cand}): {e}")
            print(f"  [download] wget failed: {e}", flush=True)

    raise RuntimeError(
        "Не вдалось завантажити з Hugging Face (часто Colab + Xet CDN 403).\n"
        + "\n".join(errors[-6:])
        + "\n\nСпробуй: Restart session → Run all.\n"
        "Або Colab Secret HF_TOKEN (Read): https://huggingface.co/settings/tokens"
    )
