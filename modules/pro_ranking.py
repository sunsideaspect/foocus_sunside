import os
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np


@dataclass
class RankedResult:
    item: Any
    score: float
    sharpness: float
    contrast: float
    exposure: float
    saturation: float
    clipping_penalty: float
    entropy: float


def _load_rgb(item: Any) -> np.ndarray | None:
    if isinstance(item, np.ndarray):
        if item.ndim == 3 and item.shape[2] == 3:
            return item
        return None

    if isinstance(item, str) and os.path.exists(item):
        image = cv2.imread(item, cv2.IMREAD_COLOR)
        if image is None:
            return None
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    return None


def _score_image(img_rgb: np.ndarray) -> tuple[float, float, float, float, float, float, float]:
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    gray_f = gray.astype(np.float32)

    # Focus/detail proxy.
    sharpness = float(cv2.Laplacian(gray_f, cv2.CV_32F).var() / 1000.0)

    # Global contrast proxy.
    contrast = float(gray_f.std() / 64.0)

    # Balanced exposure around middle-gray.
    mean_intensity = float(gray_f.mean())
    exposure = max(0.0, 1.0 - abs(mean_intensity - 127.5) / 127.5)

    hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    sat_mean = float(hsv[..., 1].mean() / 255.0)
    # Reward moderate saturation, penalize washed out and oversaturated frames.
    saturation = max(0.0, 1.0 - abs(sat_mean - 0.35) / 0.35)

    clipped_low = float((gray <= 2).mean())
    clipped_high = float((gray >= 253).mean())
    clipping_penalty = clipped_low + clipped_high

    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).ravel()
    hist = hist / (hist.sum() + 1e-8)
    entropy = float(-np.sum(hist * np.log2(hist + 1e-8)) / 8.0)

    # Weighted blend tuned for portrait realism selection.
    score = (
        0.38 * sharpness
        + 0.18 * contrast
        + 0.14 * exposure
        + 0.10 * saturation
        + 0.20 * entropy
        - 0.25 * clipping_penalty
    )

    return score, sharpness, contrast, exposure, saturation, clipping_penalty, entropy


def rank_results(items: list[Any]) -> tuple[list[Any], list[Any], list[RankedResult]]:
    scored: list[RankedResult] = []
    unscored: list[Any] = []

    for item in items:
        rgb = _load_rgb(item)
        if rgb is None:
            unscored.append(item)
            continue
        score, sharpness, contrast, exposure, saturation, clipping_penalty, entropy = _score_image(rgb)
        scored.append(
            RankedResult(
                item=item,
                score=score,
                sharpness=sharpness,
                contrast=contrast,
                exposure=exposure,
                saturation=saturation,
                clipping_penalty=clipping_penalty,
                entropy=entropy,
            )
        )

    scored.sort(key=lambda x: x.score, reverse=True)

    ranked_items = [x.item for x in scored]
    return ranked_items, unscored, scored
