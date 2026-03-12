import os
import cv2
import numpy as np

def load_and_merge_images(
        folder_path: str,
        img_names: list,
        output_size=(512, 512)
):
    """
    输入:
        folder_path: 图片所在目录
        img_names: 需要读取的图片名列表（长度必须为4）
        output_size: 拼接后缩放到的分辨率 (W, H)

    返回:
        merged_img: 拼接并缩放后的 numpy 图像 (H, W, 3)
    """

    if len(img_names) != 4:
        raise ValueError("img_names 必须包含 4 个文件名")

    # 读取四张图
    imgs = []
    for name in img_names:
        path = os.path.join(folder_path, name)
        img = cv2.imread(path)
        if img is None:
            raise FileNotFoundError(f"无法读取图片: {path}")
        imgs.append(img)

    # 保证四张图大小一致（如果不一致，自动 resize 到第一张的大小）
    h, w = imgs[0].shape[:2]
    imgs = [cv2.resize(img, (w, h)) for img in imgs]

    # 2×2 拼接
    top = np.hstack((imgs[0], imgs[1]))
    bottom = np.hstack((imgs[2], imgs[3]))
    merged = np.vstack((top, bottom))

    # 降低分辨率
    merged_resized = cv2.resize(merged, output_size)

    return merged_resized

def merge_images(
        imgs: list,
        output_size=(512, 512)
):
    """
    输入:
        imgs: 图片列表
        output_size: 拼接后缩放到的分辨率 (W, H)

    返回:
        merged_img: 拼接并缩放后的 numpy 图像 (H, W, 3)
    """

    if len(imgs) != 4:
        raise ValueError("img_names 必须包含 4 图像")

    # 保证四张图大小一致（如果不一致，自动 resize 到第一张的大小）
    h, w = imgs[0].shape[:2]
    imgs = [cv2.resize(img, (w, h)) for img in imgs]

    # 2×2 拼接
    top = np.hstack((imgs[0], imgs[1]))
    bottom = np.hstack((imgs[2], imgs[3]))
    merged = np.vstack((top, bottom))

    # 降低分辨率
    merged_resized = cv2.resize(merged, output_size)

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
