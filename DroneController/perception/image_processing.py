import cv2
import numpy as np


def merge_images(imgs: dict, output_size=(512, 512), border_thickness=3):
    required_keys = [
        "Front",
        "Back",
        "Left",
        "Right",
        "FrontLeft",
        "FrontRight",
        "BackLeft",
        "BackRight",
        "TopDown",
    ]
    for k in required_keys:
        if k not in imgs:
            raise ValueError(f"Missing image: {k}")

    h, w = imgs["Front"].shape[:2]
    resized = {k: cv2.resize(imgs[k], (w, h)) for k in required_keys}

    v_border = np.zeros((h, border_thickness, 3), dtype=np.uint8)
    h_border = np.zeros((border_thickness, 3 * w + 2 * border_thickness, 3), dtype=np.uint8)

    row1 = np.hstack((resized["FrontLeft"], v_border, resized["Front"], v_border, resized["FrontRight"]))
    row2 = np.hstack((resized["Left"], v_border, resized["TopDown"], v_border, resized["Right"]))
    row3 = np.hstack((resized["BackLeft"], v_border, resized["Back"], v_border, resized["BackRight"]))

    merged = np.vstack((row1, h_border, row2, h_border, row3))
    merged_resized = cv2.resize(merged, output_size, interpolation=cv2.INTER_AREA)
    return merged_resized


def compress_image_to_size(img, output_size=(512, 512)):
    if img is None:
        return None
    return cv2.resize(img, output_size, interpolation=cv2.INTER_AREA)


def compute_depth_index(depth: np.ndarray, min_valid=1e-3, max_valid=1e4, percentile=5.0):
    if depth is None:
        return None

    d = depth.reshape(-1).astype(np.float32)
    valid_mask = (d > min_valid) & (d < max_valid) & np.isfinite(d)
    d_valid = d[valid_mask]

    if d_valid.size == 0:
        return None

    thresh = np.percentile(d_valid, percentile)
    near_pixels = d_valid[d_valid <= thresh]

    if near_pixels.size == 0:
        return float(thresh)

    return float(near_pixels.mean())
