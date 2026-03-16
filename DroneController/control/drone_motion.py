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
        s = self.client.getMultirotorState(vehicle_name=self.vehicle_name)
        p = s.kinematics_estimated.position
        return p.x_val, p.y_val, p.z_val

    def get_yaw(self):
        s = self.client.getMultirotorState(vehicle_name=self.vehicle_name)
        pitch, roll, yaw = airsim.to_eularian_angles(s.kinematics_estimated.orientation)
        return pitch, roll, yaw

    def _move_to_world_target(self, tx, ty, tz, timeout_s=20.0, arrive_dist_m=0.10):
        t0 = time.time()
        print(f"[motion] move_to_target:start target=({tx:.3f},{ty:.3f},{tz:.3f})")
        while True:
            # Guard against simulator paused state between tasks.
            self.client.simPause(False)
            x, y, z = self.get_pos()
            ex, ey, ez = tx - x, ty - y, tz - z
            dist = math.sqrt(ex * ex + ey * ey + ez * ez)
            if dist <= float(arrive_dist_m):
                print(f"[motion] move_to_target:arrived dist={dist:.4f} pos=({x:.3f},{y:.3f},{z:.3f})")
                break
            if time.time() - t0 > float(timeout_s):
                raise TimeoutError(
                    f"[motion] move_to_target timeout target=({tx:.3f},{ty:.3f},{tz:.3f}) "
                    f"current=({x:.3f},{y:.3f},{z:.3f}) dist={dist:.3f} arrive_dist_m={arrive_dist_m:.3f}"
                )

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

    def _turn_to_yaw(self, target_yaw_rad, timeout_s=20.0):
        print(f"[motion] turn_to_yaw:start target={target_yaw_rad:.6f}")
        self.client.simPause(False)
        target_deg = math.degrees(self._normalize_angle(target_yaw_rad))
        print(f"[motion] turn_to_yaw:rotateToYawAsync target_deg={target_deg:.3f}")
        self.client.rotateToYawAsync(target_deg, timeout_sec=float(timeout_s), vehicle_name=self.vehicle_name).join()

        # Poll for convergence because some simulator states return from async before yaw settles.
        t0 = time.time()
        yaw = 0.0
        err = math.pi
        while True:
            self.client.simPause(False)
            _, _, yaw = self.get_yaw()
            err = self._normalize_angle(target_yaw_rad - yaw)
            if abs(err) < math.radians(3):
                break
            if time.time() - t0 > float(timeout_s):
                break
            time.sleep(0.03)

        if abs(err) >= math.radians(3):
            # Fallback: force-set yaw directly if rotate API is unavailable/stalled.
            print("[motion] turn_to_yaw:fallback simSetVehiclePose")
            x, y, z = self.get_pos()
            q = airsim.to_quaternion(0.0, 0.0, self._normalize_angle(target_yaw_rad))
            self.client.simSetVehiclePose(
                airsim.Pose(airsim.Vector3r(x, y, z), q),
                ignore_collision=True,
                vehicle_name=self.vehicle_name,
            )
            _, _, yaw = self.get_yaw()
            err = self._normalize_angle(target_yaw_rad - yaw)

        if abs(err) >= math.radians(3):
            raise TimeoutError(
                f"[motion] turn_to_yaw timeout target={target_yaw_rad:.6f} current={yaw:.6f} err={err:.6f}"
            )
        print(f"[motion] turn_to_yaw:arrived yaw={yaw:.6f} err={err:.6f}")

    def turn_left(self, angle_deg):
        _, _, curr = self.get_yaw()
        target = self._normalize_angle(curr - math.radians(angle_deg))
        self._turn_to_yaw(target)

    def turn_right(self, angle_deg):
        _, _, curr = self.get_yaw()
        target = self._normalize_angle(curr + math.radians(angle_deg))
        self._turn_to_yaw(target)
