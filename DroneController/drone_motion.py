import time
import math
import airsim

from airsim_client import AirSimClientSingleton

class DroneMotion:
    def __init__(self, vehicle_name = "keli", base_speed=3.0):
        self.client = AirSimClientSingleton().get_client()
        self.vehicle_name = vehicle_name
        self.base_speed = base_speed
        self.dt = 0.02

    def _get_pos(self):
        s = self.client.getMultirotorState()
        p = s.kinematics_estimated.position
        return p.x_val, p.y_val, p.z_val

    def _get_yaw(self):
        s = self.client.getMultirotorState()
        pitch, roll, yaw = airsim.to_eularian_angles(s.kinematics_estimated.orientation)
        return yaw

    # ---------- 平移：方向按机头，闭环到目标坐标 ----------

    def _move_to_world_target(self, tx, ty, tz):
        while True:
            x, y, z = self._get_pos()
            ex, ey, ez = tx - x, ty - y, tz - z
            dist = math.sqrt(ex*ex + ey*ey + ez*ez)
            if dist < 0.05:
                break

            vx, vy, vz = ex, ey, ez
            speed = self.base_speed
            norm = math.sqrt(vx*vx + vy*vy + vz*vz)
            if norm > speed:
                vx, vy, vz = vx/norm*speed, vy/norm*speed, vz/norm*speed

            # 这里直接用世界速度，不再做多余旋转，避免左右反
            self.client.moveByVelocityAsync(
                vx, vy, vz, self.dt,
                vehicle_name = self.vehicle_name
            )
            time.sleep(self.dt)

    def move_forward(self, d):
        yaw = self._get_yaw()
        x0, y0, z0 = self._get_pos()
        tx = x0 + d * math.cos(yaw)
        ty = y0 + d * math.sin(yaw)
        tz = z0
        self._move_to_world_target(tx, ty, tz)

    def move_backward(self, d):
        self.move_forward(-d)

    def move_left(self, d):
        yaw = self._get_yaw()
        x0, y0, z0 = self._get_pos()
        # 右侧 = (sin(yaw), -cos(yaw))
        tx = x0 + d * math.sin(yaw)
        ty = y0 - d * math.cos(yaw)
        tz = z0
        self._move_to_world_target(tx, ty, tz)

    def move_right(self, d):
        self.move_left(-d)

    def move_up(self, d):
        x0, y0, z0 = self._get_pos()
        tz = z0 - d  # NED：上 = z 减小
        self._move_to_world_target(x0, y0, tz)

    def move_down(self, d):
        self.move_up(-d)

    # ---------- 瞬移 ----------
    def teleport(self, x, y, z, yaw_rad = 0):
        # 构造姿态
        target_position = airsim.Vector3r(x, y, z)
        q = airsim.to_quaternion(0, 0, yaw_rad)

        # 瞬移
        self.client.simSetVehiclePose(
            airsim.Pose(target_position, q),
            ignore_collision = True,
            vehicle_name = self.vehicle_name
        )

    # ---------- 转向：闭环到目标 yaw，方向不反，角度准确 ----------

    def _normalize_angle(self, a):
        # 归一化到 [-pi, pi]
        while a > math.pi:
            a -= 2 * math.pi
        while a < -math.pi:
            a += 2 * math.pi
        return a

    def _turn_to_yaw(self, target_yaw_rad):
        while True:
            yaw = self._get_yaw()
            err = self._normalize_angle(target_yaw_rad - yaw)
            if abs(err) < math.radians(2):  # 误差 < 2°
                break

            # 简单 P 控制
            k = 1.5
            yaw_rate = k * err  # rad/s

            # 限制最大转速
            max_rate = math.radians(90)  # 90°/s
            yaw_rate = max(-max_rate, min(max_rate, yaw_rate))

            self.client.moveByVelocityBodyFrameAsync(
                0, 0, 0, self.dt,
                yaw_mode = airsim.YawMode(is_rate = True, yaw_or_rate = math.degrees(yaw_rate)),
                vehicle_name = self.vehicle_name
            )
            time.sleep(self.dt)

    def turn_left(self, angle_deg):
        curr = self._get_yaw()
        target = curr - math.radians(angle_deg)  # 左转 = yaw 减小
        target = self._normalize_angle(target)
        self._turn_to_yaw(target)

    def turn_right(self, angle_deg):
        curr = self._get_yaw()
        target = curr + math.radians(angle_deg)  # 右转 = yaw 增大
        target = self._normalize_angle(target)
        self._turn_to_yaw(target)
