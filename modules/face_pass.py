"""Post-generation face lock via InsightFace Inswapper.

Unlike Fooocus Image Prompt FaceSwap (IP-Adapter), this runs AFTER generation
and frees SDXL VRAM first — much safer on Colab T4.
"""
from __future__ import annotations

import os
import traceback

_analyser = None
_swapper = None
_load_attempted = False

INSIGHTFACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../models/insightface'))
INSWAPPER_NAME = 'inswapper_128.onnx'
INSWAPPER_URLS = [
    'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/inswapper_128.onnx',
    'https://huggingface.co/ezioruan/inswapper_128.onnx/resolve/main/inswapper_128.onnx',
]


def free_generation_vram():
    """Unload SDXL / LoRAs so InsightFace can use GPU/CPU safely."""
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
            torch.cuda.ipc_collect()
    except Exception:
        pass
    print('[Sunside FaceLock] generation VRAM released')


def face_lock_ready() -> bool:
    try:
        import insightface  # noqa: F401
        import cv2  # noqa: F401
        return True
    except Exception:
        return False


def _download_inswapper() -> str | None:
    os.makedirs(INSIGHTFACE_DIR, exist_ok=True)
    target = os.path.join(INSIGHTFACE_DIR, INSWAPPER_NAME)
    if os.path.isfile(target) and os.path.getsize(target) > 1_000_000:
        return target
    from modules.model_loader import load_file_from_url
    for url in INSWAPPER_URLS:
        try:
            print(f'[Sunside FaceLock] downloading inswapper from {url}')
            load_file_from_url(url=url, model_dir=INSIGHTFACE_DIR, file_name=INSWAPPER_NAME)
            if os.path.isfile(target) and os.path.getsize(target) > 1_000_000:
                return target
        except Exception as e:
            print(f'[Sunside FaceLock] download failed: {e}')
    return target if os.path.isfile(target) else None


def _ensure_models():
    global _analyser, _swapper, _load_attempted
    if _analyser is not None and _swapper is not None:
        return True
    if _load_attempted and (_analyser is None or _swapper is None):
        # allow retry after install
        pass
    _load_attempted = True
    try:
        from insightface.app import FaceAnalysis
        from insightface.model_zoo import get_model

        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        # Prefer CPU on very tight VRAM after failed CUDA init
        try:
            _analyser = FaceAnalysis(name='buffalo_l', providers=providers)
            _analyser.prepare(ctx_id=0, det_size=(640, 640))
        except Exception:
            print('[Sunside FaceLock] CUDA face analysis failed — falling back to CPU')
            providers = ['CPUExecutionProvider']
            _analyser = FaceAnalysis(name='buffalo_l', providers=providers)
            _analyser.prepare(ctx_id=-1, det_size=(640, 640))

        swapper_path = _download_inswapper()
        if not swapper_path:
            print('[Sunside FaceLock] inswapper_128.onnx missing')
            _analyser = None
            return False

        _swapper = get_model(swapper_path, providers=providers)
        print(f'[Sunside FaceLock] ready ({swapper_path}, providers={providers})')
        return True
    except Exception as e:
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
        return cv2.imread(face_ref)
    arr = np.asarray(face_ref)
    if arr.ndim != 3:
        return None
    if arr.shape[2] == 4:
        arr = arr[:, :, :3]
    # Gradio numpy is RGB
    return cv2.cvtColor(arr.astype('uint8'), cv2.COLOR_RGB2BGR)


def apply_face_lock(image_rgb, face_ref, free_vram_first: bool = False):
    """
    Swap faces in image_rgb using face_ref (file path or RGB numpy).
    Returns RGB numpy (original on failure).
    """
    if image_rgb is None or face_ref is None:
        return image_rgb
    if free_vram_first:
        free_generation_vram()
    if not _ensure_models():
        return image_rgb
    try:
        import cv2
        import numpy as np

        src_bgr = _to_bgr(face_ref)
        if src_bgr is None:
            print('[Sunside FaceLock] invalid face ref')
            return image_rgb

        dst_bgr = cv2.cvtColor(np.asarray(image_rgb).astype('uint8'), cv2.COLOR_RGB2BGR)
        src_faces = _analyser.get(src_bgr)
        dst_faces = _analyser.get(dst_bgr)
        if not src_faces:
            print('[Sunside FaceLock] no face in reference — skip')
            return image_rgb
        if not dst_faces:
            print('[Sunside FaceLock] no face in generated image — skip')
            return image_rgb

        src_face = max(src_faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
        result = dst_bgr
        for face in dst_faces:
            result = _swapper.get(result, face, src_face, paste_back=True)
        print(f'[Sunside FaceLock] swapped {len(dst_faces)} face(s)')
        return cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
    except Exception:
        print('[Sunside FaceLock] failed:')
        traceback.print_exc()
        return image_rgb


# Back-compat alias
def apply_face_pass(image_rgb, face_ref_path: str):
    return apply_face_lock(image_rgb, face_ref_path, free_vram_first=False)
