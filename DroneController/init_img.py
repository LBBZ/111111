import os
import time
import math
import airsim

from DroneController.drone_camera import DroneCamera
from DroneController.drone_motion import DroneMotion

OUTPUT_DIR = "task_test/task_step_init"
os.makedirs(OUTPUT_DIR, exist_ok=True)

motion = DroneMotion()
camera = DroneCamera()

# -----------------------------
# 外部调用入口
# -----------------------------
def capture_views_at_pose(x, y, z, yaw_deg = 0):
    """外部调用入口：移动到指定 pose → 拍 9 张图 → 恢复原位"""
    yaw_rad = math.radians(yaw_deg)

    motion.client.simPause(True)
    motion.teleport(x, y, z, yaw_rad)
    print(f"瞬移到位置: {airsim.Vector3r(x, y, z)}")
    # 确保瞬移发生
    motion.client.simPause(False)
    time.sleep(0.05)
    motion.client.simPause(True)

    imgs = camera.capture_all()
    for name, img in imgs.items():
        camera.save_image(img, os.path.join(OUTPUT_DIR, name + ".png"))

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
