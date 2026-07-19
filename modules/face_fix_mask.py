"""Build a soft face mask for Fix Face — no rembg/SAM/CuPy."""
from __future__ import annotations

import numpy as np


def face_bbox_mask(img_rgb: np.ndarray, padding: float = 0.35) -> np.ndarray | None:
    """Return HxW uint8 mask (255=face) or None if no face."""
    if img_rgb is None or getattr(img_rgb, 'ndim', 0) != 3:
        return None
    mask = _facexlib_mask(img_rgb, padding)
    if mask is not None:
        return mask
    return _opencv_haar_mask(img_rgb, padding)


def _ellipse_mask(h, w, x1, y1, x2, y2, padding: float):
    import cv2
    bw, bh = x2 - x1, y2 - y1
    x1 = max(0, int(x1 - bw * padding))
    y1 = max(0, int(y1 - bh * padding))
    x2 = min(w, int(x2 + bw * padding))
    y2 = min(h, int(y2 + bh * padding * 0.2))
    mask = np.zeros((h, w), dtype=np.uint8)
    cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
    ax, ay = max(1.0, (x2 - x1) / 2.0), max(1.0, (y2 - y1) / 2.0)
    cv2.ellipse(mask, (int(cx), int(cy)), (int(ax), int(ay)), 0, 0, 360, 255, -1)
    mask = cv2.GaussianBlur(mask, (0, 0), sigmaX=max(3, int(min(ax, ay) * 0.15)))
    return mask


def _facexlib_mask(img_rgb: np.ndarray, padding: float) -> np.ndarray | None:
    try:
        import modules.config
        from extras.facexlib.utils.face_restoration_helper import FaceRestoreHelper
    except Exception as e:
        print(f'[Sunside FixFace] facexlib unavailable: {e}')
        return None

    h, w = img_rgb.shape[:2]
    try:
        helper = FaceRestoreHelper(
            upscale_factor=1,
            model_rootpath=modules.config.path_controlnet,
            device='cpu',
        )
        helper.clean_all()
        helper.read_image(np.ascontiguousarray(img_rgb[:, :, ::-1].copy()))
        count = helper.get_face_landmarks_5(only_keep_largest=True)
        if count == 0 or not helper.det_faces:
            print('[Sunside FixFace] facexlib: no face')
            return None
        x1, y1, x2, y2 = [float(v) for v in helper.det_faces[0][:4]]
        print(f'[Sunside FixFace] facexlib mask ok ({int(x2 - x1)}x{int(y2 - y1)})')
        return _ellipse_mask(h, w, x1, y1, x2, y2, padding)
    except Exception as e:
        print(f'[Sunside FixFace] facexlib mask failed: {e}')
        return None


def _opencv_haar_mask(img_rgb: np.ndarray, padding: float) -> np.ndarray | None:
    try:
        import cv2
    except Exception:
        return None
    h, w = img_rgb.shape[:2]
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(48, 48))
    if faces is None or len(faces) == 0:
        print('[Sunside FixFace] opencv haar: no face')
        return None
    x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
    print(f'[Sunside FixFace] opencv haar mask ok ({fw}x{fh})')
    return _ellipse_mask(h, w, x, y, x + fw, y + fh, padding)
