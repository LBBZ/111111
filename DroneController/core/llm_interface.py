import json


class LLMInterface:
    def __init__(self):
        self.mock_outputs = [
            {
                "scores": {"front": 0.82, "left": 0.40, "right": 0.10, "back": 0.02, "down": 0.15},
                "confidence": 0.88,
                "target_direction": "front-left",
                "turn_direction": "left",
                "turn_angle_deg": 18.0,
                "forward_distance": 2.5,
                "vertical_movement": 0.2,
                "notes": "Building visible ahead-left; forward path mostly clear.",
            },
            {
                "scores": {"front": 0.30, "left": 0.05, "right": 0.75, "back": 0.01, "down": 0.20},
                "confidence": 0.92,
                "target_direction": "front-right",
                "turn_direction": "right",
                "turn_angle_deg": 25.0,
                "forward_distance": 3.0,
                "vertical_movement": 0.0,
                "notes": "Right corridor is open; building visible on the right side.",
            },
            {
                "scores": {"front": 0.10, "left": 0.70, "right": 0.20, "back": 0.05, "down": 0.05},
                "confidence": 0.80,
                "target_direction": "left",
                "turn_direction": "left",
                "turn_angle_deg": 30.0,
                "forward_distance": 1.5,
                "vertical_movement": 0.8,
                "notes": "Obstacle ahead; safer path is left with required altitude gain.",
            },
        ]
        self.index = 0
        self.bootstrap_index = 0

    def _is_bootstrap_prompt(self, prompt: str) -> bool:
        try:
            obj = json.loads(prompt)
        except Exception:
            return False
        task_ctx = obj.get("task_context", {})
        if not isinstance(task_ctx, dict):
            return False
        return task_ctx.get("task_kind") == "bootstrap_simple"

    def get_action(self, prompt):
        if self._is_bootstrap_prompt(prompt):
            if self.bootstrap_index == 0:
                self.bootstrap_index += 1
                return (
                    {
                        "scores": {"front": 0.1, "left": 0.1, "right": 0.1, "back": 0.1, "down": 0.9},
                        "confidence": 0.99,
                        "target_direction": "up",
                        "turn_direction": "none",
                        "turn_angle_deg": 0.0,
                        "forward_distance": 0.0,
                        "vertical_movement": 1.0,
                        "notes": "Bootstrap warm-up: move up once.",
                    },
                    "running",
                )
            return (
                {
                    "done": True,
                    "message": "Bootstrap completed.",
                    "target_location_direction": "up",
                },
                "done",
            )

        if self.index < len(self.mock_outputs):
            output = self.mock_outputs[self.index]
            self.index += 1
            return output, "running"

        done_json = {
            "done": True,
            "message": "Mission completed.",
            "target_location_direction": "front-left",
        }
        return done_json, "done"
