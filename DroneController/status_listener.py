import time
import airsim
import math

# 连接 AirSim
client = airsim.MultirotorClient()
client.confirmConnection()

# 打印频率（秒）
INTERVAL = 0.2   # 每 0.2 秒打印一次（5Hz）

def rad2deg(r):
    return r * 180.0 / math.pi

print("开始实时监听无人机坐标与朝向角（Ctrl+C 退出）")

try:
    while True:
        state = client.getMultirotorState()
        pos = state.kinematics_estimated.position
        ori = state.kinematics_estimated.orientation

        pitch, roll, yaw = airsim.to_eularian_angles(ori)

        print(
            f"位置: x={pos.x_val:.2f}, y={pos.y_val:.2f}, z={pos.z_val:.2f} | "
            f"姿态: pitch={rad2deg(pitch):.1f}°, roll={rad2deg(roll):.1f}°, yaw={rad2deg(yaw):.1f}°"
        )

        time.sleep(INTERVAL)

except KeyboardInterrupt:
    print("监听结束。")
