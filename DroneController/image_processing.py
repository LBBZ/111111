import os
import cv2
import numpy as np

def load_and_merge_images(
        folder_path: str,
        img_names: list,
        output_size=(512, 512),
        border_thickness=3
):
    if len(img_names) != 5:
        raise ValueError("img_names 必须包含 5 个文件名")

    imgs = []
    for name in img_names:
        path = os.path.join(folder_path, name)
        img = cv2.imread(path)
        if img is None:
            raise FileNotFoundError(f"无法读取图片: {path}")
        imgs.append(img)

    return merge_images(imgs, output_size, border_thickness)

def merge_images(
        imgs: list,
        output_size=(512, 512),
        border_thickness=3
):
    """
    imgs 顺序必须为:
        [Front, Left, Down, Right, Back]
    """

    if len(imgs) != 5:
        raise ValueError("imgs 必须包含 5 张图像")

    img_front, img_left, img_down, img_right, img_back = imgs

    # 统一大小
    h, w = img_front.shape[:2]
    img_left  = cv2.resize(img_left,  (w, h))
    img_down  = cv2.resize(img_down,  (w, h))
    img_right = cv2.resize(img_right, (w, h))
    img_back  = cv2.resize(img_back,  (w, h))

    # 黑色边框
    v_border = np.zeros((h, border_thickness, 3), dtype=np.uint8)
    h_border = np.zeros((border_thickness, 3*w + 2*border_thickness, 3), dtype=np.uint8)

    # 空白区域必须与 row2 宽度一致
    empty = np.zeros((h, 3*w + 2*border_thickness, 3), dtype=np.uint8)

    # Row1: empty | front | empty
    row1 = np.hstack((empty[:, :w], v_border, img_front, v_border, empty[:, :w]))

    # Row2: left | down | right
    row2 = np.hstack((img_left, v_border, img_down, v_border, img_right))

    # Row3: empty | back | empty
    row3 = np.hstack((empty[:, :w], v_border, img_back, v_border, empty[:, :w]))

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
