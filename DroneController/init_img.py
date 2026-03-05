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
motion.client.simPause(False)

# -----------------------------
# 外部调用入口
# -----------------------------
def capture_views_at_pose(x, y, z, yaw_deg):
    """外部调用入口：移动到指定 pose → 拍 9 张图 → 恢复原位"""
    yaw_rad = math.radians(yaw_deg)

    motion.teleport(x, y, z)
    print(f"瞬移到位置: {airsim.Vector3r(x, y, z)}")

    # 8 个方向
    angles = [
        (0,   "forward.png"),
        (45,  "forward_right.png"),
        (90,  "right.png"),
        (135, "rear_right.png"),
        (180, "rear.png"),
        (-135,"rear_left.png"),
        (-90, "left.png"),
        (-45, "forward_left.png"),
    ]



    # top-down（使用 bottom camera）
    img = camera.capture_down()
    camera.save_image(img, os.path.join(OUTPUT_DIR, "top_down.png"))

    for ang, name in angles:
        yaw = math.radians(ang)

        motion.client.simPause(True)
        motion.teleport(x, y, z, yaw)
        motion.client.simPause(False)
        time.sleep(0.05)   # 只给一帧时间
        motion.client.simPause(True)

        img = camera.capture_front()
        camera.save_image(img, os.path.join(OUTPUT_DIR, name))

    # 瞬移到原始位置
    motion.teleport(x, y, z)
    print(f"瞬移到位置: {airsim.Vector3r(x, y, z)}")
    motion.client.simPause(True)

# -----------------------------
# 测试入口（固定坐标）
# -----------------------------
def main_test():
    capture_views_at_pose(
        x=7400.67,
        y=-3555.19,
        z=-53.37,
        yaw_deg=0
    )
    print("Test completed.")

# -----------------------------
# 主入口
# -----------------------------
if __name__ == "__main__":
    main_test()
