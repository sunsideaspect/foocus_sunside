"""Build a soft face mask for Fix Face when SAM/GroundingDINO finds nothing."""
from __future__ import annotations

import numpy as np


def face_bbox_mask(img_rgb: np.ndarray, padding: float = 0.35) -> np.ndarray | None:
    """Return HxW uint8 mask (255=face) or None if no face."""
    try:
        import cv2
        import modules.config
        from extras.facexlib.utils.face_restoration_helper import FaceRestoreHelper
    except Exception as e:
        print(f'[Sunside FixFace] facexlib unavailable for fallback mask: {e}')
        return None

    if img_rgb is None or img_rgb.ndim != 3:
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
            print('[Sunside FixFace] fallback: no face bbox')
            return None
        x1, y1, x2, y2 = [float(v) for v in helper.det_faces[0][:4]]
        bw, bh = x2 - x1, y2 - y1
        x1 = max(0, int(x1 - bw * padding))
        y1 = max(0, int(y1 - bh * padding))
        x2 = min(w, int(x2 + bw * padding))
        y2 = min(h, int(y2 + bh * padding * 0.2))
        mask = np.zeros((h, w), dtype=np.uint8)
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        ax, ay = max(1, (x2 - x1) / 2), max(1, (y2 - y1) / 2)
        cv2.ellipse(
            mask,
            (int(cx), int(cy)),
            (int(ax), int(ay)),
            0, 0, 360,
            255,
            -1,
        )
        mask = cv2.GaussianBlur(mask, (0, 0), sigmaX=max(3, int(min(ax, ay) * 0.15)))
        print(f'[Sunside FixFace] fallback bbox mask ok ({x2 - x1}x{y2 - y1})')
        return mask
    except Exception as e:
        print(f'[Sunside FixFace] fallback mask failed: {e}')
        return None
