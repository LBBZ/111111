import cv2
import numpy as np

import cv2
import numpy as np

def merge_images(
        imgs: dict,
        output_size=(512, 512),
        border_thickness=3
):
    """
    根据 9 个方向的图像拼接成 3x3 mosaic。
    imgs 必须包含以下键：
        Front, Back, Left, Right,
        FrontLeft, FrontRight, BackLeft, BackRight,
        TopDown
    """

    required_keys = [
        "Front", "Back", "Left", "Right",
        "FrontLeft", "FrontRight", "BackLeft", "BackRight",
        "TopDown"
    ]
    for k in required_keys:
        if k not in imgs:
            raise ValueError(f"缺少图像: {k}")

    # 统一大小
    h, w = imgs["Front"].shape[:2]
    resized = {k: cv2.resize(imgs[k], (w, h)) for k in required_keys}

    # 黑色边框
    v_border = np.zeros((h, border_thickness, 3), dtype=np.uint8)
    h_border = np.zeros((border_thickness, 3*w + 2*border_thickness, 3), dtype=np.uint8)

    # Row1: FrontLeft | Front | FrontRight
    row1 = np.hstack((resized["FrontLeft"], v_border, resized["Front"], v_border, resized["FrontRight"]))

    # Row2: Left | TopDown | Right
    row2 = np.hstack((resized["Left"], v_border, resized["TopDown"], v_border, resized["Right"]))

    # Row3: BackLeft | Back | BackRight
    row3 = np.hstack((resized["BackLeft"], v_border, resized["Back"], v_border, resized["BackRight"]))

    # 拼接三行
    merged = np.vstack((row1, h_border, row2, h_border, row3))

    # 最终缩放
    merged_resized = cv2.resize(merged, output_size, interpolation=cv2.INTER_AREA)

    return merged_resized

def compress_image_to_size(img, output_size=(512, 512)):
    """
    输入:
        img: numpy 图像 (H, W, C)
        target_size: (width, height)，例如 (512, 512)

    返回:
        resized_img: 压缩后的图像 (target_size)
    """
    if img is None:
        return None

    # target_size 是 (W, H)，cv2.resize 也是 (W, H)
    resized_img = cv2.resize(img, output_size, interpolation=cv2.INTER_AREA)
    return resized_img

def compute_depth_index(depth: np.ndarray,
                        min_valid=1e-3,
                        max_valid=1e4,
                        percentile=5.0):
    """
    输入:
        depth: AirSim 返回的深度图 (H, W), float32, 单位米
        min_valid: 过滤无效小值（例如 0）
        max_valid: 过滤异常大值
        percentile: 使用最近百分之多少像素来估计最近障碍距离

    返回:
        depth_index: float，越小表示障碍越近；None 表示无有效像素
    """

    if depth is None:
        return None

    # 展平
    d = depth.reshape(-1).astype(np.float32)

    # 过滤无效值
    valid_mask = (d > min_valid) & (d < max_valid) & np.isfinite(d)
    d_valid = d[valid_mask]

    if d_valid.size == 0:
        return None

    # 最近 percentile% 像素
    thresh = np.percentile(d_valid, percentile)
    near_pixels = d_valid[d_valid <= thresh]

    if near_pixels.size == 0:
        return float(thresh)

    return float(near_pixels.mean())
