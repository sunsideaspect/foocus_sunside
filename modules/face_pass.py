"""Optional post-generation face pass (Inswapper / InsightFace).

Stock Fooocus FaceSwap (IP-Adapter) is unstable on Colab VRAM.
This module applies face identity AFTER generation when insightface+inswapper
are available; otherwise it no-ops safely.
"""
from __future__ import annotations

import os
import traceback

_analyser = None
_swapper = None
_load_attempted = False


def face_pass_available() -> bool:
    try:
        import insightface  # noqa: F401
        return True
    except Exception:
        return False


def _ensure_models():
    global _analyser, _swapper, _load_attempted
    if _load_attempted:
        return _analyser is not None and _swapper is not None
    _load_attempted = True
    try:
        import insightface
        from insightface.app import FaceAnalysis
        import onnxruntime

        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        _analyser = FaceAnalysis(name='buffalo_l', providers=providers)
        _analyser.prepare(ctx_id=0, det_size=(640, 640))

        # Prefer common Fooocus/Comfy path; fall back to insightface model zoo name
        model_candidates = [
            os.path.abspath('./models/insightface/inswapper_128.onnx'),
            os.path.abspath('../models/insightface/inswapper_128.onnx'),
            'inswapper_128.onnx',
        ]
        swapper_path = None
        for p in model_candidates:
            if os.path.isfile(p):
                swapper_path = p
                break
        if swapper_path is None:
            print('[Sunside FacePass] inswapper_128.onnx not found — face pass disabled')
            _analyser = None
            return False

        from insightface.model_zoo import get_model
        _swapper = get_model(swapper_path, providers=providers)
        print(f'[Sunside FacePass] ready ({swapper_path})')
        return True
    except Exception as e:
        print(f'[Sunside FacePass] unavailable: {e}')
        _analyser = None
        _swapper = None
        return False


def apply_face_pass(image_rgb, face_ref_path: str):
    """Swap largest face in image_rgb with face from face_ref_path. Returns RGB numpy."""
    if image_rgb is None or not face_ref_path or not os.path.isfile(face_ref_path):
        return image_rgb
    if not _ensure_models():
        return image_rgb
    try:
        import cv2
        import numpy as np

        src_bgr = cv2.imread(face_ref_path)
        if src_bgr is None:
            return image_rgb
        dst_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

        src_faces = _analyser.get(src_bgr)
        dst_faces = _analyser.get(dst_bgr)
        if not src_faces or not dst_faces:
            print('[Sunside FacePass] no face detected — skip')
            return image_rgb

        src_face = sorted(src_faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]), reverse=True)[0]
        result = dst_bgr
        for face in dst_faces:
            result = _swapper.get(result, face, src_face, paste_back=True)
        return cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
    except Exception:
        print('[Sunside FacePass] failed:')
        traceback.print_exc()
        return image_rgb
