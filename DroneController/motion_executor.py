# motion_executor.py
import json
import textwrap

from DroneController.airsim_client import AirSimClientSingleton
from DroneController.drone_camera import DroneCamera
from DroneController.drone_motion import DroneMotion
from DroneController.image_processing import merge_images, compute_depth_index


class MotionExecutor:
    """
    解析大模型输出 JSON → 控制器可直接使用的动作参数
    并提供 execute() 调用 DroneMotion 的动作函数。
    """
    def __init__(self,
                 client=AirSimClientSingleton().get_client(),
                 motion=DroneMotion(),
                 camera=DroneCamera()
                 ):

        self.client = client
        self.motion = motion
        self.camera = camera


    def parse(self, action_json: dict):
        """
        输入：大模型返回的 JSON（dict）
        输出：解析后的动作结构（dict）
        """

        # -------- 1. 任务结束 JSON --------
        if "done" in action_json:
            return {
                "type": "done",
                "message": action_json.get("message", ""),
                "target_location_direction": action_json.get("target_location_direction", "unknown"),
                "raw": action_json
            }

        # -------- 2. 正常动作 JSON --------
        turn_dir = action_json.get("turn_direction", "none")
        turn_angle = float(action_json.get("turn_angle_deg", 0.0))
        forward = float(action_json.get("forward_distance", 0.0))
        vertical = float(action_json.get("vertical_movement", 0.0))

        return {
            "type": "motion",
            "turn": {
                "direction": turn_dir,
                "angle_deg": turn_angle
            },
            "forward": forward,
            "vertical": vertical,
            "raw": action_json
        }

    # ----------------------------------------------------------------------
    # 根据解析结果调用 DroneMotion 的动作函数
    # ----------------------------------------------------------------------
    def execute(self, parsed_action: dict):
        """
        根据解析后的动作结构调用 DroneMotion 的函数。
        解析器不负责循环、不负责任务结束判断、不负责日志。
        """

        if parsed_action["type"] == "done":
            # 解析器不做控制逻辑，只返回状态
            return "done"

        # -------- 执行转向 --------
        turn = parsed_action["turn"]
        direction = turn["direction"]
        angle = turn["angle_deg"]

        if direction == "left" and angle > 0:
            self.motion.turn_left(angle)
        elif direction == "right" and angle > 0:
            self.motion.turn_right(angle)
        # direction == "none" → 不转向

        # -------- 执行前进 --------
        forward = parsed_action["forward"]
        if forward > 0:
            self.motion.move_forward(forward)

        # -------- 执行升降 --------
        vertical = parsed_action["vertical"]
        if vertical > 0:
            self.motion.move_up(abs(vertical))
        elif vertical < 0:
            self.motion.move_down(abs(vertical))

        return "ok"

    def get_sensor_data(self):
        """
        调用真实接口获取：
        - mosaic 图像（merge_img）
        - depth summary（每个方向的 depth_index）
        - drone state（pos + yaw）
        """

        # -----------------------------
        # 1. 获取真实 RGB 图像
        # -----------------------------
        imgs = self.camera.capture_all()   # 返回 dict: {"Front": img, "Left": img, ...}

        # 拼接 mosaic 图像
        merge_img = merge_images(imgs)

        # -----------------------------
        # 2. 获取真实深度图并计算 depth index
        # -----------------------------
        depths = self.camera.capture_all_depth()  # 返回 dict: {"Front": depth_img, ...}

        depth_summary = {}
        for pose in ["Front", "Left", "TopDown", "Right", "Back"]:
            depth_img = depths[pose]
            depth_index = compute_depth_index(depth_img)
            depth_summary[pose.lower()] = float(depth_index)

        # -----------------------------
        # 3. 获取无人机状态（真实）
        # -----------------------------
        x, y, z = self.motion.get_pos()
        pitch, roll, yaw = self.motion.get_yaw()

        drone_state = {
            "x": round(x, 2),
            "y": round(y, 2),
            "z": round(z, 2),
            "pitch": round(pitch, 2),
            "roll": round(roll, 2),
            "yaw": round(yaw, 2)
        }

        # -----------------------------
        # 4. 返回结构化数据
        # -----------------------------
        return {
            "mosaic_image": merge_img,
            "depth_summary": depth_summary,
            "drone_state": drone_state
        }


    def build_prompt(self, sensor_data):
        """
        把 sensor_data 打包成 prompt 字符串
        """
        mosaic = sensor_data["mosaic_image"]
        depths = sensor_data["depth_summary"]
        state = sensor_data["drone_state"]

        # TODO: 未来改成真实 base64
        prompt_json = {
            "image": "<base64 placeholder>",
            "depth_summary": depths,
            "drone_state": state
        }

        # 返回 JSON 字符串 + 原始图像
        return json.dumps(prompt_json, ensure_ascii=False)