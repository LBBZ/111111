import time
import json
import math

from DroneController.control.drone_motion import DroneMotion
from DroneController.infra.airsim_client import AirSimClientSingleton
from DroneController.perception.drone_camera import DroneCamera
from DroneController.perception.image_processing import compute_depth_index, merge_images


class MotionExecutor:
    """Parse model output and execute motion commands."""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, client=None, motion=None, camera=None):
        if self.__class__._initialized:
            return
        self.client = client if client is not None else AirSimClientSingleton()
        self.motion = motion if motion is not None else DroneMotion()
        self.camera = camera if camera is not None else DroneCamera()
        self.__class__._initialized = True

    def parse(self, action_json: dict):
        if "done" in action_json:
            return {
                "type": "done",
                "message": action_json.get("message", ""),
                "target_location_direction": action_json.get("target_location_direction", "unknown"),
                "raw": action_json,
            }

        turn_dir = action_json.get("turn_direction", "none")
        turn_angle = float(action_json.get("turn_angle_deg", 0.0))
        forward = float(action_json.get("forward_distance", 0.0))
        vertical = float(action_json.get("vertical_movement", 0.0))

        return {
            "type": "motion",
            "turn": {"direction": turn_dir, "angle_deg": turn_angle},
            "forward": forward,
            "vertical": vertical,
            "raw": action_json,
        }

    def execute(self, parsed_action: dict):
        if parsed_action["type"] == "done":
            return "done"

        turn = parsed_action["turn"]
        direction = turn["direction"]
        angle = turn["angle_deg"]

        if direction == "left" and angle > 0:
            self.motion.turn_left(angle)
        elif direction == "right" and angle > 0:
            self.motion.turn_right(angle)

        forward = parsed_action["forward"]
        if forward > 0:
            self.motion.move_forward(forward)

        vertical = parsed_action["vertical"]
        if vertical > 0:
            self.motion.move_up(abs(vertical))
        elif vertical < 0:
            self.motion.move_down(abs(vertical))

        return "ok"

    @staticmethod
    def estimate_target_position(current_state: dict, parsed_action: dict):
        x = float(current_state.get("x", 0.0))
        y = float(current_state.get("y", 0.0))
        z = float(current_state.get("z", 0.0))
        yaw_rad = float(current_state.get("yaw", 0.0))

        if parsed_action.get("type") != "motion":
            return {"x": x, "y": y, "z": z}

        turn = parsed_action.get("turn", {})
        direction = turn.get("direction", "none")
        angle_rad = math.radians(float(turn.get("angle_deg", 0.0)))
        if direction == "left":
            yaw_rad -= angle_rad
        elif direction == "right":
            yaw_rad += angle_rad

        forward = float(parsed_action.get("forward", 0.0))
        vertical = float(parsed_action.get("vertical", 0.0))
        return {
            "x": x + forward * math.cos(yaw_rad),
            "y": y + forward * math.sin(yaw_rad),
            "z": z - vertical,
        }

    def get_sensor_data(self):
        imgs = self.camera.capture_all()
        merge_img = merge_images(imgs)

        depths = self.camera.capture_all_depth()
        depth_summary = {}
        for pose in ["Front", "Left", "TopDown", "Right", "Back"]:
            depth_img = depths[pose]
            depth_index = compute_depth_index(depth_img)
            depth_summary[pose.lower()] = float(depth_index) if depth_index is not None else None

        x, y, z = self.motion.get_pos()
        pitch, roll, yaw = self.motion.get_yaw()
        drone_state = {
            "x": round(x, 2),
            "y": round(y, 2),
            "z": round(z, 2),
            "pitch": round(pitch, 2),
            "roll": round(roll, 2),
            "yaw": round(yaw, 2),
        }

        return {
            "mosaic_image": merge_img,
            "rgb_views": imgs,
            "depth_maps": depths,
            "depth_summary": depth_summary,
            "drone_state": drone_state,
        }

    def build_prompt(self, sensor_data, task_context=None):
        prompt_json = {
            "image": "<base64 placeholder>",
            "depth_summary": sensor_data["depth_summary"],
            "drone_state": sensor_data["drone_state"],
        }
        if task_context:
            prompt_json["task_context"] = task_context
        return json.dumps(prompt_json, ensure_ascii=False)
