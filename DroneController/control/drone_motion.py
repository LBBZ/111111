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

    def _move_to_world_target(self, tx, ty, tz, timeout_s=20.0):
        # Use AirSim position API directly; tx/ty/tz are already world-frame targets.
        _, _, yaw = self.get_yaw()
        self.client.moveToPositionAsync(
            float(tx),
            float(ty),
            float(tz),
            float(self.base_speed),
            timeout_sec=float(timeout_s),
            yaw_mode=airsim.YawMode(is_rate=False, yaw_or_rate=math.degrees(yaw)),
            vehicle_name=self.vehicle_name,
        ).join()

    def _body_offset_to_world_target(self, forward_m=0.0, right_m=0.0, up_m=0.0):
        _, _, yaw = self.get_yaw()
        x0, y0, z0 = self.get_pos()
        # AirSim NED: x-forward, y-right, z-down.
        dx = forward_m * math.cos(yaw) + right_m * math.sin(yaw)
        dy = forward_m * math.sin(yaw) - right_m * math.cos(yaw)
        dz = -up_m
        return x0 + dx, y0 + dy, z0 + dz

    def move_forward(self, d):
        tx, ty, tz = self._body_offset_to_world_target(forward_m=d)
        self._move_to_world_target(tx, ty, tz)

    def move_backward(self, d):
        self.move_forward(-d)

    def move_left(self, d):
        tx, ty, tz = self._body_offset_to_world_target(right_m=-d)
        self._move_to_world_target(tx, ty, tz)

    def move_right(self, d):
        self.move_left(-d)

    def move_up(self, d):
        tx, ty, tz = self._body_offset_to_world_target(up_m=d)
        self._move_to_world_target(tx, ty, tz)

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
        self.client.reset()
        self.client.enableApiControl(True)
        self.client.armDisarm(True)

        v3d = airsim.Vector3r(float(x), float(y), float(z))
        qua = airsim.to_quaternion(
            math.radians(float(pitch_deg)),
            math.radians(float(roll_deg)),
            math.radians(float(yaw_deg)),
        )
        pose = airsim.Pose(v3d, qua)
        self.client.simPause(True)
        self.client.simSetVehiclePose(
            pose,
            ignore_collision=True,
            vehicle_name=self.vehicle_name
        )
        self.client.simPause(False)
        time.sleep(0.05)
        self.client.simPause(True)
        # 同步控制器目标
        state = self.client.getMultirotorState(vehicle_name=self.vehicle_name)
        p = state.kinematics_estimated.position

        self.client.simPause(False)
        _, _, yaw = self.get_yaw()
        self.client.moveToPositionAsync(
            p.x_val,
            p.y_val,
            p.z_val,
            1,
            yaw_mode=airsim.YawMode(is_rate=False, yaw_or_rate=math.degrees(yaw)),
            vehicle_name=self.vehicle_name
        ).join()

    def _normalize_angle(self, a):
        while a > math.pi:
            a -= 2 * math.pi
        while a < -math.pi:
            a += 2 * math.pi
        return a

    def _turn_to_yaw(self, target_yaw_rad, timeout_s=20.0):
        self.client.simPause(False)
        target_deg = math.degrees(self._normalize_angle(target_yaw_rad))
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

    def turn_left(self, angle_deg):
        _, _, curr = self.get_yaw()
        target = self._normalize_angle(curr - math.radians(angle_deg))
        self._turn_to_yaw(target)

    def turn_right(self, angle_deg):
        _, _, curr = self.get_yaw()
        target = self._normalize_angle(curr + math.radians(angle_deg))
        self._turn_to_yaw(target)
