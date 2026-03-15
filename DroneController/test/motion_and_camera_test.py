import os
import random
import time
import airsim
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from DroneController.control.drone_motion import DroneMotion
from DroneController.perception.drone_camera import DroneCamera
from DroneController.infra.airsim_client import AirSimClientSingleton

BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(BASE_DIR, "artifacts", "current")
os.makedirs(OUTPUT_DIR, exist_ok=True)

TASK_FILE = os.path.join(OUTPUT_DIR, "task_test.txt")

client = AirSimClientSingleton().get_client()
motion = DroneMotion()
camera = DroneCamera()

motion.client.simPause(False)

print("Init Position.")
# 设置初始位置
target_position = airsim.Vector3r(0, 0, 0)
motion.client.simSetVehiclePose(
    airsim.Pose(target_position, airsim.Quaternionr(0, 0, 0, 1)),
    True
)
motion.move_up(0.01) # 启动飞控悬停
print("Initialized at target position.")

ACTIONS = [
    ("move_forward",  motion.move_forward),
    ("move_backward", motion.move_backward),
    ("move_left",     motion.move_left),
    ("move_right",    motion.move_right),
    ("move_up",       motion.move_up),
    ("move_down",     motion.move_down),
    ("turn_left",     motion.turn_left),
    ("turn_right",    motion.turn_right),
]

steps = []

for name, func in ACTIONS:
    steps.append((name, func))

while len(steps) < 16:
    steps.append(random.choice(ACTIONS))

random.shuffle(steps)

with open(TASK_FILE, "w", encoding="utf-8") as f:
    for i, (name, func) in enumerate(steps, start=1):

        if "turn" in name:
            param = random.uniform(90, 90)
        else:
            param = random.uniform(5.0, 10.0)

        # 获取动作前状态
        state = motion.client.getMultirotorState()
        pos = state.kinematics_estimated.position
        ori = state.kinematics_estimated.orientation
        pitch, roll, yaw = airsim.to_eularian_angles(ori)

        f.write(f"Step {i}:\n")
        f.write(f"  Action: {name}({param:.2f})\n")
        f.write(f"  Start Position\n")
        f.write(f"  Position: x={pos.x_val:.2f}, y={pos.y_val:.2f}, z={pos.z_val:.2f}\n")
        f.write(f"  Orientation: pitch={pitch:.2f}, roll={roll:.2f}, yaw={yaw:.2f}\n\n")

        print(f"[Step {i}] Executing: {name}({param:.2f})")
        func(param)  # 闭环控制，自动结束
        time.sleep(3)

        # 获取动作后状态（动作结束后立即）
        state = motion.client.getMultirotorState()
        pos = state.kinematics_estimated.position
        ori = state.kinematics_estimated.orientation
        pitch, roll, yaw = airsim.to_eularian_angles(ori)

        f.write(f"  End Position\n")
        f.write(f"  Position: x={pos.x_val:.2f}, y={pos.y_val:.2f}, z={pos.z_val:.2f}\n")
        f.write(f"  Orientation: pitch={pitch:.2f}, roll={roll:.2f}, yaw={yaw:.2f}\n\n")

        # 拍照
        step_dir = os.path.join(OUTPUT_DIR, f"test_step_{i}")
        os.makedirs(step_dir, exist_ok=True)

        # -----------------------------
        # 1. RGB 图像
        # -----------------------------
        imgs = camera.capture_all()
        for img_name, img in imgs.items():
            camera.save_image(img, os.path.join(step_dir, img_name + ".png"))

        # -----------------------------
        # 2. 深度图
        # -----------------------------
        depths = camera.capture_all_depth()
        for cam_name, depth in depths.items():
            camera.save_depth_data(depth, os.path.join(step_dir, cam_name + "_depth.npy"))
            camera.save_depth_image(depth, os.path.join(step_dir, cam_name + "_depth.png"))

        # -----------------------------
        # 3. Segmentation 图像（新增）
        # -----------------------------
        segs = camera.capture_all_seg()
        for cam_name, seg in segs.items():
            # RGB 可视化图
            camera.save_segmentation_vis(seg, os.path.join(step_dir, cam_name + "_seg.png"))
            # 单通道 ID mask（PNG）
            camera.save_segmentation_id(seg, os.path.join(step_dir, cam_name + "_seg_id.png"))
            # NPY（大模型友好）
            camera.save_segmentation_npy(seg, os.path.join(step_dir, cam_name + "_seg.npy"))

        print(f"[Step {i}] Saved images to {step_dir}")

print("Test completed.")
motion.client.simPause(True)
