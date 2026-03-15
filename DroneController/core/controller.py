from DroneController.core.llm_interface import LLMInterface
from DroneController.core.motion_executor import MotionExecutor
from DroneController.io.logger import Logger


class DroneController:
    """Controller loop for sensing, planning, execution and logging."""

    def __init__(self, executor=None, log_filename="drone_log.txt", output_dir=None, overwrite_logs=True):
        self.llm = LLMInterface()
        self.executor = executor if executor is not None else MotionExecutor()
        self.motion = self.executor.motion
        self.logger = Logger(log_filename, output_dir=output_dir, overwrite=overwrite_logs)

    def get_drone_state(self):
        x, y, z = self.motion.get_pos()
        pitch, roll, yaw = self.motion.get_yaw()
        return {"x": x, "y": y, "z": z, "pitch": pitch, "roll": roll, "yaw": yaw}

    def run(self, max_steps=None, on_step_end=None):
        self.motion.client.simPause(False)
        trajectory = []
        plan_steps = []
        step_count = 0
        end_reason = "unknown"

        start_state = self.get_drone_state()
        trajectory.append([start_state["x"], start_state["y"], start_state["z"]])

        while True:
            sensor_data = self.executor.get_sensor_data()
            prompt = self.executor.build_prompt(sensor_data)
            action_json, _status = self.llm.get_action(prompt)
            parsed = self.executor.parse(action_json)
            exec_status = self.executor.execute(parsed)
            drone_state = self.get_drone_state()

            self.logger.log(
                {
                    "prompt": prompt,
                    "llm_output": action_json,
                    "parsed_action": parsed,
                    "execution_status": exec_status,
                    "drone_state": drone_state,
                    "sensor_data": {"depth_summary": sensor_data["depth_summary"]},
                }
            )

            step_count += 1
            trajectory.append([drone_state["x"], drone_state["y"], drone_state["z"]])
            plan_steps.append(
                {
                    "step": step_count,
                    "raw_model_output": action_json,
                    "parsed_action": parsed,
                    "execute_status": exec_status,
                    "drone_state_after": drone_state,
                }
            )

            if callable(on_step_end):
                on_step_end(
                    step_count=step_count,
                    sensor_data=sensor_data,
                    action_json=action_json,
                    parsed_action=parsed,
                    execute_status=exec_status,
                    drone_state=drone_state,
                )

            if parsed["type"] == "done":
                print("Mission completed.")
                end_reason = "done"
                break

            if max_steps is not None and step_count >= int(max_steps):
                end_reason = "max_steps"
                break

        self.motion.client.simPause(True)
        return {
            "trajectory": trajectory,
            "plan_steps": plan_steps,
            "status": {
                "done": end_reason == "done",
                "step_count": step_count,
                "end_reason": end_reason,
            },
        }
