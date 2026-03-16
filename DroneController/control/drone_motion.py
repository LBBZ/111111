import math
import time

import airsim

from DroneController.infra.airsim_client import AirSimClientSingleton


class DroneMotion:
    def __init__(self, vehicle_name="keli", base_speed=3.0):
        print("Planing DroneMotion.")
        self.client = AirSimClientSingleton()
        self.vehicle_name = vehicle_name
        self.base_speed = base_speed
        self.dt = 0.02

    def get_pos(self):
        s = self.client.getMultirotorState()
        p = s.kinematics_estimated.position
        return p.x_val, p.y_val, p.z_val

    def get_yaw(self):
        s = self.client.getMultirotorState()
        pitch, roll, yaw = airsim.to_eularian_angles(s.kinematics_estimated.orientation)
        return pitch, roll, yaw

    def _move_to_world_target(self, tx, ty, tz):
        while True:
            x, y, z = self.get_pos()
            ex, ey, ez = tx - x, ty - y, tz - z
            dist = math.sqrt(ex * ex + ey * ey + ez * ez)
            if dist < 0.05:
                break

            vx, vy, vz = ex, ey, ez
            speed = self.base_speed
            norm = math.sqrt(vx * vx + vy * vy + vz * vz)
            if norm > speed:
                vx, vy, vz = vx / norm * speed, vy / norm * speed, vz / norm * speed

            self.client.moveByVelocityAsync(vx, vy, vz, self.dt, vehicle_name=self.vehicle_name)
            time.sleep(self.dt)

    def move_forward(self, d):
        _, _, yaw = self.get_yaw()
        x0, y0, z0 = self.get_pos()
        tx = x0 + d * math.cos(yaw)
        ty = y0 + d * math.sin(yaw)
        self._move_to_world_target(tx, ty, z0)

    def move_backward(self, d):
        self.move_forward(-d)

    def move_left(self, d):
        _, _, yaw = self.get_yaw()
        x0, y0, z0 = self.get_pos()
        tx = x0 + d * math.sin(yaw)
        ty = y0 - d * math.cos(yaw)
        self._move_to_world_target(tx, ty, z0)

    def move_right(self, d):
        self.move_left(-d)

    def move_up(self, d):
        x0, y0, z0 = self.get_pos()
        self._move_to_world_target(x0, y0, z0 - d)

    def move_down(self, d):
        self.move_up(-d)

    def teleport(self, x, y, z, yaw_rad=0):
        target_position = airsim.Vector3r(x, y, z)
        q = airsim.to_quaternion(0, 0, yaw_rad)
        self.client.simSetVehiclePose(
            airsim.Pose(target_position, q),
            ignore_collision=True,
            vehicle_name=self.vehicle_name,
        )

    def initialize_pose(self, x, y, z, yaw_deg=0.0, pitch_deg=0.0, roll_deg=0.0):
        """Initialize vehicle pose in NED meters and keep simulator running for follow-up steps."""
        v3d = airsim.Vector3r(float(x), float(y), float(z))
        qua = airsim.to_quaternion(
            math.radians(float(pitch_deg)),
            math.radians(float(roll_deg)),
            math.radians(float(yaw_deg)),
        )
        pose = airsim.Pose(v3d, qua)
        print(f"初始化位置: \n{v3d}")
        print(f"初始化朝向: \n{qua}")

        self.client.simPause(True)
        self.client.simSetVehiclePose(
            pose,
            ignore_collision=True,
            vehicle_name=self.vehicle_name
        )
        self.client.simPause(False)
        time.sleep(0.05)
        self.client.simPause(True)
        print("等待姿态稳定...")
        # 同步控制器目标
        state = self.client.getMultirotorState(vehicle_name=self.vehicle_name)
        p = state.kinematics_estimated.position

        self.client.simPause(False)
        self.client.moveToPositionAsync(
            p.x_val,
            p.y_val,
            p.z_val,
            1,
            vehicle_name=self.vehicle_name
        ).join()
        print("姿态稳定完毕, 进入悬停状态")
        print(f"当前实际位置: {self.get_pos()}")


    def _normalize_angle(self, a):
        while a > math.pi:
            a -= 2 * math.pi
        while a < -math.pi:
            a += 2 * math.pi
        return a

    def _turn_to_yaw(self, target_yaw_rad):
        while True:
            _, _, yaw = self.get_yaw()
            err = self._normalize_angle(target_yaw_rad - yaw)
            if abs(err) < math.radians(2):
                break

            k = 1.5
            yaw_rate = k * err
            max_rate = math.radians(90)
            yaw_rate = max(-max_rate, min(max_rate, yaw_rate))

            self.client.moveByVelocityBodyFrameAsync(
                0,
                0,
                0,
                self.dt,
                yaw_mode=airsim.YawMode(is_rate=True, yaw_or_rate=math.degrees(yaw_rate)),
                vehicle_name=self.vehicle_name,
            )
            time.sleep(self.dt)

    def turn_left(self, angle_deg):
        _, _, curr = self.get_yaw()
        target = self._normalize_angle(curr - math.radians(angle_deg))
        self._turn_to_yaw(target)

    def turn_right(self, angle_deg):
        _, _, curr = self.get_yaw()
        target = self._normalize_angle(curr + math.radians(angle_deg))
        self._turn_to_yaw(target)
