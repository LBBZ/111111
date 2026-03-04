import os
import random
import time
import airsim

from drone_motion import DroneMotion
from drone_camera import DroneCamera

# -----------------------------
# 初始化输出目录
# -----------------------------
OUTPUT_DIR = "task_test"
os.makedirs(OUTPUT_DIR, exist_ok=True)

TASK_FILE = os.path.join(OUTPUT_DIR, "task_test.txt")

# -----------------------------
# 初始化无人机控制器
# -----------------------------
motion = DroneMotion()
camera = DroneCamera()

motion.client.simPause(False)

print("Taking off...")
motion.client.takeoffAsync().join()

# 设置初始位置
target_position = airsim.Vector3r(7481.66602, -3555.18677, -53.36726)
motion.client.simSetVehiclePose(
    airsim.Pose(target_position, airsim.Quaternionr(0, 0, 0, 1)),
    True
)
print("Initialized at target position.")

# -----------------------------
# 定义 8 个基础动作
# -----------------------------
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

# -----------------------------
# 随机生成 16 个动作序列（覆盖全部 8 个动作）
# -----------------------------
steps = []

# 先确保 8 个动作都出现一次
for name, func in ACTIONS:
    steps.append((name, func))

# 再随机补足到 16 步
while len(steps) < 16:
    steps.append(random.choice(ACTIONS))

# 打乱顺序
random.shuffle(steps)

# -----------------------------
# 执行动作 + 拍照
# -----------------------------
with open(TASK_FILE, "w", encoding="utf-8") as f:
    for i, (name, func) in enumerate(steps, start=1):

        # 随机距离或角度
        if "turn" in name:
            param = random.uniform(10, 45)  # 随机转 30~180 度
        else:
            param = random.uniform(5.0, 10.0)  # 随机移动 5~10 米

        # 等待 5 秒
        time.sleep(5)

        # 获取当前状态（动作前）
        state = motion.client.getMultirotorState()
        pos = state.kinematics_estimated.position
        ori = state.kinematics_estimated.orientation
        pitch, roll, yaw = airsim.to_eularian_angles(ori)


        # 写入 Step 信息
        f.write(f"Step {i}:\n")
        f.write(f"  Action: {name}({param:.2f})\n")
        # 写入开始状态信息
        f.write(f"  Start Position\n")
        f.write(f"  Position: x={pos.x_val:.2f}, y={pos.y_val:.2f}, z={pos.z_val:.2f}\n")
        f.write(f"  Orientation: pitch={pitch:.2f}, roll={roll:.2f}, yaw={yaw:.2f}\n\n")

        # 执行动作
        print(f"[Step {i}] Executing: {name}({param:.2f})")
        func(param)

        # 等待 5 秒
        time.sleep(5)

        # 获取当前状态（动作后）
        state = motion.client.getMultirotorState()
        pos = state.kinematics_estimated.position
        ori = state.kinematics_estimated.orientation
        pitch, roll, yaw = airsim.to_eularian_angles(ori)

        # 写入结束状态信息
        f.write(f"  End Position\n")
        f.write(f"  Position: x={pos.x_val:.2f}, y={pos.y_val:.2f}, z={pos.z_val:.2f}\n")
        f.write(f"  Orientation: pitch={pitch:.2f}, roll={roll:.2f}, yaw={yaw:.2f}\n\n")

        # -----------------------------
        # 三方向拍照
        # -----------------------------
        step_dir = os.path.join(OUTPUT_DIR, f"test_step_{i}")
        os.makedirs(step_dir, exist_ok=True)

        img_front = camera.capture_front()
        img_down  = camera.capture_down()
        img_back  = camera.capture_back()

        camera.save_image(img_front, os.path.join(step_dir, "front.png"))
        camera.save_image(img_down,  os.path.join(step_dir, "down.png"))
        camera.save_image(img_back,  os.path.join(step_dir, "back.png"))

        print(f"[Step {i}] Saved images to {step_dir}")

print("Test completed. All results saved in task_test/")

motion.client.simPause(True)
