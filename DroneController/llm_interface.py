# llm_interface.py
import json

class LLMInterface:
    def __init__(self):
        # 三个逻辑自洽的模拟输出
        self.mock_outputs = [
            {
                "scores": {
                    "front": 0.82,
                    "left": 0.40,
                    "right": 0.10,
                    "back": 0.02,
                    "down": 0.15
                },
                "confidence": 0.88,
                "target_direction": "front-left",
                "turn_direction": "left",
                "turn_angle_deg": 18.0,
                "forward_distance": 2.5,
                "vertical_movement": 0.2,
                "notes": "Building visible ahead-left; forward path mostly clear."
            },
            {
                "scores": {
                    "front": 0.30,
                    "left": 0.05,
                    "right": 0.75,
                    "back": 0.01,
                    "down": 0.20
                },
                "confidence": 0.92,
                "target_direction": "front-right",
                "turn_direction": "right",
                "turn_angle_deg": 25.0,
                "forward_distance": 3.0,
                "vertical_movement": 0.0,
                "notes": "Right corridor is open; building visible on the right side."
            },
            {
                "scores": {
                    "front": 0.10,
                    "left": 0.70,
                    "right": 0.20,
                    "back": 0.05,
                    "down": 0.05
                },
                "confidence": 0.80,
                "target_direction": "left",
                "turn_direction": "left",
                "turn_angle_deg": 30.0,
                "forward_distance": 1.5,
                "vertical_movement": 0.8,
                "notes": "Obstacle ahead; safer path is left with required altitude gain."
            }
        ]

        self.index = 0  # 当前返回第几个 JSON

    def get_action(self, prompt):
        """
        返回：
        - action_json: dict（大模型动作）
        - status: "running" 或 "done"
        """

        # 1,2,3 次调用 → 返回模拟 JSON
        if self.index < len(self.mock_outputs):
            output = self.mock_outputs[self.index]
            self.index += 1
            return output, "running"

        # 第 4 次及以后 → 返回任务结束 JSON
        done_json = {
            "done": True,
            "message": "Mission completed.",
            "target_location_direction": "front-left"  # 模拟目标方位
        }

        return done_json, "done"
