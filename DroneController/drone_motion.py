# drone_motion.py
import time
import airsim
import math

class DroneMotion:
    def __init__(self, vehicle_name="", base_speed=3.0):
        self.client = airsim.MultirotorClient()
        self.client.confirmConnection()
        self.client.enableApiControl(True, vehicle_name)
        self.client.armDisarm(True, vehicle_name)
        self.vehicle_name = vehicle_name
        self.base_speed = base_speed

    # ---------------------------
    # 世界坐标系移动（你的环境实际支持的）
    # ---------------------------
    def _move_world(self, vx, vy, vz, distance):
        duration = distance / self.base_speed
        self.client.moveByVelocityAsync(
            vx * self.base_speed,
            vy * self.base_speed,
            vz * self.base_speed,
            duration,
            vehicle_name=self.vehicle_name
        ).join()
        time.sleep(0.05)

    # ---------------------------
    # 6 个方向动作（world-frame + NED Z）
    # ---------------------------
    def move_forward(self, distance):
        self._move_world(vx=1, vy=0, vz=0, distance=distance)

    def move_backward(self, distance):
        self._move_world(vx=-1, vy=0, vz=0, distance=distance)

    def move_right(self, distance):
        self._move_world(vx=0, vy=1, vz=0, distance=distance)

    def move_left(self, distance):
        self._move_world(vx=0, vy=-1, vz=0, distance=distance)

    def move_up(self, distance):
        self._move_world(vx=0, vy=0, vz=-1, distance=distance)  # NED

    def move_down(self, distance):
        self._move_world(vx=0, vy=0, vz=1, distance=distance)   # NED

    # ---------------------------
    # yaw（UE 弧度）
    # ---------------------------
    def turn_left(self, angle_deg):
        duration = 1.0
        yaw_rate = angle_deg / duration
        self.client.rotateByYawRateAsync(yaw_rate, duration).join()
        time.sleep(0.05)

    def turn_right(self, angle_deg):
        duration = 1.0
        yaw_rate = -angle_deg / duration
        self.client.rotateByYawRateAsync(yaw_rate, duration).join()
        time.sleep(0.05)
