import os
import random
import time
import airsim

from drone_motion import DroneMotion
from drone_camera import DroneCamera
from airsim_client import AirSimClientSingleton

OUTPUT_DIR = "task_test"
os.makedirs(OUTPUT_DIR, exist_ok=True)

TASK_FILE = os.path.join(OUTPUT_DIR, "task_test.txt")

print("Planing Client.")
client = AirSimClientSingleton().get_client()
print("Planing DroneMotion.")
motion = DroneMotion()
print("Planing DroneCamera.")
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
        imgs = camera.capture_all()

        for img_name, img in imgs.items():
            camera.save_image(img, os.path.join(step_dir, img_name + ".png"))

        print(f"[Step {i}] Saved images to {step_dir}")

print("Test completed.")
motion.client.simPause(True)
