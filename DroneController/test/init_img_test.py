import math
import os
import sys
import time
from pathlib import Path

import airsim

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from DroneController.perception.drone_camera import DroneCamera
from DroneController.control.drone_motion import DroneMotion
from DroneController.perception.image_processing import merge_images, compress_image_to_size, compute_depth_index

BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(BASE_DIR, "artifacts", "current", "task_step_init")
os.makedirs(OUTPUT_DIR, exist_ok=True)

motion = DroneMotion()
camera = DroneCamera()

# -----------------------------
# 外部调用入口
# -----------------------------
def capture_views_at_pose(x, y, z, yaw_deg = 0):
    """外部调用入口：移动到指定 pose → 拍 9 张图 → 保存 RGB/Depth/Segmentation → 恢复原位"""
    yaw_rad = int(math.radians(yaw_deg))

    # 暂停仿真，瞬移
    motion.client.simPause(True)
    motion.teleport(x, y, z, yaw_rad)
    print(f"瞬移到位置: {airsim.Vector3r(x, y, z)}")

    motion.client.simPause(False)
    time.sleep(0.05)
    motion.client.simPause(True)

    # -----------------------------
    # 1. RGB 图像
    # -----------------------------
    # 测试完成
    imgs = camera.capture_all()
    for name, img in imgs.items():
        camera.save_image(img, os.path.join(OUTPUT_DIR, f"{name}.png"))

    merge_img = merge_images(imgs)
    compress_down_img = compress_image_to_size(imgs["TopDown"])

    camera.save_image(merge_img, os.path.join(OUTPUT_DIR, f"CompressedMerge.png"))
    camera.save_image(compress_down_img, os.path.join(OUTPUT_DIR, f"CompressedDown.png"))

    # -----------------------------
    # 2. 深度图
    # -----------------------------
    # 测试完成
    depths = camera.capture_all_depth()
    for name, depth in depths.items():
        # 原始深度（米）
        camera.save_depth_data(depth, os.path.join(OUTPUT_DIR, f"{name}_depth.npy"))
        # 可视化深度（16-bit PNG）
        camera.save_depth_image(depth, os.path.join(OUTPUT_DIR, f"{name}_depth.png"))
    print("深度指数越小表示障碍越近")
    for pose in ["Front", "Left", "TopDown", "Right", "Back"]:
        depth_img = depths[pose]
        depth_index = compute_depth_index(depth_img)
        print(f"{pose} 深度指数: {depth_index}")

    # -----------------------------
    # 3. Segmentation 图像
    # -----------------------------
    # 测试完成
    segs = camera.capture_all_seg()
    for name, seg in segs.items():
        # RGB 可视化图
        camera.save_segmentation_vis(seg, os.path.join(OUTPUT_DIR, f"{name}_seg.png"))
        # 单通道 ID mask（PNG）
        camera.save_segmentation_id(seg, os.path.join(OUTPUT_DIR, f"{name}_seg_id.png"))
        # NPY（大模型友好）
        camera.save_segmentation_npy(seg, os.path.join(OUTPUT_DIR, f"{name}_seg.npy"))


# -----------------------------
# 测试入口（固定坐标）
# -----------------------------
def main_test():
    capture_views_at_pose(
        x=0,
        y=0,
        z=0,
        yaw_deg=0
    )
    print("Test completed.")

# -----------------------------
# 主入口
# -----------------------------
if __name__ == "__main__":
    main_test()
