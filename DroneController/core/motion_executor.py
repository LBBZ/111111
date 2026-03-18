import time
import json

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
        print(f"[execute] turn direction={direction} angle_deg={angle}")

        if direction == "left" and angle > 0:
            t0 = time.time()
            print("[execute] turn_left:start")
            self.motion.turn_left(angle)
            print(f"[execute] turn_left:ok dt={int((time.time() - t0) * 1000)}ms")
        elif direction == "right" and angle > 0:
            t0 = time.time()
            print("[execute] turn_right:start")
            self.motion.turn_right(angle)
            print(f"[execute] turn_right:ok dt={int((time.time() - t0) * 1000)}ms")

        forward = parsed_action["forward"]
        if forward > 0:
            t0 = time.time()
            print(f"[execute] move_forward:start d={forward}")
            self.motion.move_forward(forward)
            print(f"[execute] move_forward:ok dt={int((time.time() - t0) * 1000)}ms")

        vertical = parsed_action["vertical"]
        if vertical > 0:
            t0 = time.time()
            print(f"[execute] move_up:start d={abs(vertical)}")
            self.motion.move_up(abs(vertical))
            print(f"[execute] move_up:ok dt={int((time.time() - t0) * 1000)}ms")
        elif vertical < 0:
            t0 = time.time()
            print(f"[execute] move_down:start d={abs(vertical)}")
            self.motion.move_down(abs(vertical))
            print(f"[execute] move_down:ok dt={int((time.time() - t0) * 1000)}ms")

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
