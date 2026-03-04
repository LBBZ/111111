# drone_motion.py
import time
import airsim

class DroneMotion:
    def __init__(self, vehicle_name: str = "", base_speed: float = 3.0):
        """
        base_speed: m/s，用来把“距离”换成“飞行时间”
        """
        self.client = airsim.MultirotorClient()
        self.client.confirmConnection()
        self.client.enableApiControl(True, vehicle_name)
        self.client.armDisarm(True, vehicle_name)
        self.vehicle_name = vehicle_name
        self.base_speed = base_speed

    def _move_body(self, vx: float, vy: float, vz: float, distance: float):
        """
        在机体坐标系下飞一段距离（m）
        vx, vy, vz 是方向（单位向量），distance 是标量
        """
        if distance <= 0:
            return
        duration = distance / self.base_speed
        self.client.moveByVelocityBodyFrameAsync(
            vx * self.base_speed,
            vy * self.base_speed,
            vz * self.base_speed,
            duration,
            vehicle_name=self.vehicle_name
        ).join()
        time.sleep(0.01)

    # -------- 前后左右上下：6 个接口 --------

    def move_forward(self, distance: float):
        """机头方向前进 distance 米"""
        self._move_body(vx=1.0, vy=0.0, vz=0.0, distance=distance)

    def move_backward(self, distance: float):
        """机头方向后退 distance 米"""
        self._move_body(vx=-1.0, vy=0.0, vz=0.0, distance=distance)

    def move_left(self, distance: float):
        """机体左侧方向移动 distance 米"""
        self._move_body(vx=0.0, vy=-1.0, vz=0.0, distance=distance)

    def move_right(self, distance: float):
        """机体右侧方向移动 distance 米"""
        self._move_body(vx=0.0, vy=1.0, vz=0.0, distance=distance)

    def move_up(self, distance: float):
        """向上飞 distance 米（NED 里 z 负方向）"""
        self._move_body(vx=0.0, vy=0.0, vz=-1.0, distance=distance)

    def move_down(self, distance: float):
        """向下飞 distance 米（NED 里 z 正方向）"""
        self._move_body(vx=0.0, vy=0.0, vz=1.0, distance=distance)

    # -------- 左右转向：2 个接口 --------

    def turn_left(self, angle_deg: float):
        """左转 angle_deg 度（逆时针）"""
        if angle_deg == 0:
            return
        # 用固定时长，角速度 = 角度 / 时间
        duration = 1.0
        yaw_rate = angle_deg / duration
        self.client.rotateByYawRateAsync(yaw_rate, duration).join()
        time.sleep(0.01)

    def turn_right(self, angle_deg: float):
        """右转 angle_deg 度（顺时针）"""
        if angle_deg == 0:
            return
        duration = 1.0
        yaw_rate = -angle_deg / duration
        self.client.rotateByYawRateAsync(yaw_rate, duration).join()
        time.sleep(0.01)
