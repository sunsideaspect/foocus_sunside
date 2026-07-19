"""Post-generation face lock via InsightFace Inswapper (CPU-first for Colab).

Default is CPU onnxruntime: after SDXL, GPU ORT often OOMs/kills the process.
Set SUNSIDE_FACELOCK_CPU=0 to try CUDA.
"""
from __future__ import annotations

import os
import traceback

_analyser = None
_swapper = None
_init_error = None

INSIGHTFACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../models/insightface'))
INSWAPPER_NAME = 'inswapper_128.onnx'
INSWAPPER_URLS = [
    'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/inswapper_128.onnx',
    'https://huggingface.co/ezioruan/inswapper_128.onnx/resolve/main/inswapper_128.onnx',
]


def _want_cpu() -> bool:
    return os.environ.get('SUNSIDE_FACELOCK_CPU', '1').strip() not in ('0', 'false', 'False')


def free_generation_vram():
    try:
        import ldm_patched.modules.model_management as mm
        mm.unload_all_models()
        mm.soft_empty_cache(True)
    except Exception as e:
        print(f'[Sunside FaceLock] unload warning: {e}')
    try:
        import gc
        import torch
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            try:
                torch.cuda.ipc_collect()
            except Exception:
                pass
            try:
                torch.cuda.synchronize()
            except Exception:
                pass
    except Exception:
        pass
    print('[Sunside FaceLock] generation VRAM released')


def face_lock_status() -> str:
    if _analyser is not None and _swapper is not None:
        return 'ready'
    if _init_error:
        return f'error: {_init_error}'
    try:
        import insightface  # noqa: F401
        import onnxruntime  # noqa: F401
        import cv2  # noqa: F401
        return 'deps_ok'
    except Exception as e:
        return f'missing_deps: {e}'


def _download_inswapper() -> str | None:
    os.makedirs(INSIGHTFACE_DIR, exist_ok=True)
    target = os.path.join(INSIGHTFACE_DIR, INSWAPPER_NAME)
    if os.path.isfile(target) and os.path.getsize(target) > 1_000_000:
        return target
    try:
        from modules.model_loader import load_file_from_url
    except Exception:
        load_file_from_url = None
    for url in INSWAPPER_URLS:
        try:
            print(f'[Sunside FaceLock] downloading inswapper ...')
            if load_file_from_url:
                load_file_from_url(url=url, model_dir=INSIGHTFACE_DIR, file_name=INSWAPPER_NAME)
            else:
                import urllib.request
                urllib.request.urlretrieve(url, target)
            if os.path.isfile(target) and os.path.getsize(target) > 1_000_000:
                return target
        except Exception as e:
            print(f'[Sunside FaceLock] download failed: {e}')
    return target if os.path.isfile(target) and os.path.getsize(target) > 1_000_000 else None


def _ensure_models():
    global _analyser, _swapper, _init_error
    if _analyser is not None and _swapper is not None:
        return True
    try:
        # Prefer CPU onnxruntime — avoids killing Colab after SDXL
        import onnxruntime as ort
        from insightface.app import FaceAnalysis
        from insightface.model_zoo import get_model

        if _want_cpu():
            providers = ['CPUExecutionProvider']
            ctx_id = -1
            print('[Sunside FaceLock] using CPU onnxruntime (stable on Colab)')
        else:
            avail = ort.get_available_providers()
            if 'CUDAExecutionProvider' in avail:
                providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
                ctx_id = 0
            else:
                providers = ['CPUExecutionProvider']
                ctx_id = -1

        os.makedirs(INSIGHTFACE_DIR, exist_ok=True)
        # insightface stores buffalo under <root>/models/buffalo_l
        _analyser = FaceAnalysis(name='buffalo_l', root=INSIGHTFACE_DIR, providers=providers)
        _analyser.prepare(ctx_id=ctx_id, det_size=(320, 320))

        swapper_path = _download_inswapper()
        if not swapper_path:
            _init_error = 'inswapper_128.onnx missing'
            print(f'[Sunside FaceLock] {_init_error}')
            _analyser = None
            return False

        _swapper = get_model(swapper_path, providers=providers)
        _init_error = None
        print(f'[Sunside FaceLock] ready path={swapper_path} providers={providers}')
        return True
    except Exception as e:
        _init_error = str(e)
        print(f'[Sunside FaceLock] unavailable: {e}')
        traceback.print_exc()
        _analyser = None
        _swapper = None
        return False


def _to_bgr(face_ref):
    import cv2
    import numpy as np

    if face_ref is None:
        return None
    if isinstance(face_ref, str):
        if not os.path.isfile(face_ref):
            return None
        img = cv2.imread(face_ref)
        return img
    arr = np.asarray(face_ref)
    if arr.ndim != 3:
        return None
    if arr.shape[2] == 4:
        arr = arr[:, :, :3]
    return cv2.cvtColor(arr.astype('uint8'), cv2.COLOR_RGB2BGR)


def apply_face_lock(image_rgb, face_ref, free_vram_first: bool = False):
    """Swap faces; never raises — returns original image on any failure."""
    if image_rgb is None or face_ref is None:
        return image_rgb
    try:
        if free_vram_first:
            free_generation_vram()
        if not _ensure_models():
            print('[Sunside FaceLock] skip — models not ready:', face_lock_status())
            return image_rgb

        import cv2
        import numpy as np

        src_bgr = _to_bgr(face_ref)
        if src_bgr is None:
            print('[Sunside FaceLock] invalid face ref')
            return image_rgb

        dst = np.asarray(image_rgb)
        if dst.dtype != np.uint8:
            dst = np.clip(dst, 0, 255).astype('uint8')
        dst_bgr = cv2.cvtColor(dst, cv2.COLOR_RGB2BGR)

        src_faces = _analyser.get(src_bgr)
        dst_faces = _analyser.get(dst_bgr)
        if not src_faces:
            print('[Sunside FaceLock] no face in reference — skip')
            return image_rgb
        if not dst_faces:
            print('[Sunside FaceLock] no face in output — skip')
            return image_rgb

        src_face = max(src_faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
        result = dst_bgr
        for face in dst_faces:
            result = _swapper.get(result, face, src_face, paste_back=True)
        print(f'[Sunside FaceLock] ok — swapped {len(dst_faces)} face(s)')
        return cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
    except Exception:
        print('[Sunside FaceLock] failed (keeping original frame):')
        traceback.print_exc()
        return image_rgb


def apply_face_pass(image_rgb, face_ref_path: str):
    return apply_face_lock(image_rgb, face_ref_path, free_vram_first=False)
