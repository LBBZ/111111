import time
import airsim
import math

client = airsim.MultirotorClient()
client.confirmConnection()
client.enableApiControl(True)
client.armDisarm(True)
client.simPause(False)

print("Taking off...")
client.takeoffAsync().join()
time.sleep(1)

# 读取初始状态
state0 = client.getMultirotorState()
p0 = state0.kinematics_estimated.position
print(f"Initial position: x={p0.x_val:.2f}, y={p0.y_val:.2f}, z={p0.z_val:.2f}")

# ---------------------------------------------------------
# ① 测试上升方向
# ---------------------------------------------------------
print("\nTesting UP direction...")
client.moveByVelocityBodyFrameAsync(0, 0, -1, 2).join()  # 理论上：NED 上升 = vz=-1
time.sleep(0.5)

state1 = client.getMultirotorState()
p1 = state1.kinematics_estimated.position
print(f"After UP: x={p1.x_val:.2f}, y={p1.y_val:.2f}, z={p1.z_val:.2f}")

# 判断 Z 方向
if p1.z_val < p0.z_val:
    print(">>> Detected: NED (z decreases when going UP)")
else:
    print(">>> Detected: Z-UP (z increases when going UP)")

# ---------------------------------------------------------
# ② 测试 yaw 是否影响前进方向
# ---------------------------------------------------------
print("\nTesting yaw + forward...")

# 旋转 90 度
client.rotateByYawRateAsync(90, 1).join()
time.sleep(0.5)

# 前进 2 米
client.moveByVelocityBodyFrameAsync(1, 0, 0, 2).join()
time.sleep(0.5)

state2 = client.getMultirotorState()
p2 = state2.kinematics_estimated.position
print(f"After yaw + forward: x={p2.x_val:.2f}, y={p2.y_val:.2f}, z={p2.z_val:.2f}")

dx = p2.x_val - p1.x_val
dy = p2.y_val - p1.y_val

print(f"Movement vector: dx={dx:.2f}, dy={dy:.2f}")

# 判断是否是 body-frame
if abs(dx) < 0.5 and abs(dy) > 1.0:
    print(">>> Detected: BODY-FRAME (forward follows yaw)")
else:
    print(">>> Detected: WORLD-FRAME (forward ignores yaw)")

client.simPause(True)