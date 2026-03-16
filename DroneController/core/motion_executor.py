import json

from DroneController.control.drone_motion import DroneMotion
from DroneController.infra.airsim_client import AirSimClientSingleton
from DroneController.perception.drone_camera import DroneCamera
from DroneController.perception.image_processing import compute_depth_index, merge_images


class MotionExecutor:
    """Parse model output and execute motion commands."""

    def __init__(self, client=None, motion=None, camera=None):
        self.client = client if client is not None else AirSimClientSingleton()
        self.motion = motion if motion is not None else DroneMotion()
        self.camera = camera if camera is not None else DroneCamera()

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
