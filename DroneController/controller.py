# controller.py
from DroneController.llm_interface import LLMInterface
from DroneController.logger import Logger
from DroneController.motion_executor import MotionExecutor


class DroneController:
    """
    主控制器：
    - 调用 LLMInterface 获取动作
    - 调用 MotionExecutor 解析并执行动作
    - 调用 Logger 写日志
    - 控制任务循环
    """

    def __init__(self, executor=None, log_filename="drone_log.txt", output_dir=None, overwrite_logs=True):
        self.llm = LLMInterface()
        self.executor = executor if executor is not None else MotionExecutor()
        self.motion = self.executor.motion
        self.logger = Logger(log_filename, output_dir=output_dir, overwrite=overwrite_logs)


    def get_drone_state(self):
        """从 DroneMotion 获取当前状态"""
        x, y, z = self.motion.get_pos()
        pitch, roll, yaw = self.motion.get_yaw()
        return {"x": x, "y": y, "z": z,
                "pitch": pitch, "roll": roll, "yaw": yaw
                }

    def run(self, max_steps=None):
        """
        主循环：
        - 获取大模型动作
        - 解析
        - 执行
        - 写日志
        - 判断是否结束
        """
        self.motion.client.simPause(False)
        trajectory = []
        plan_steps = []
        step_count = 0
        end_reason = "unknown"

        # 记录起点，便于后续轨迹评估。
        start_state = self.get_drone_state()
        trajectory.append([start_state["x"], start_state["y"], start_state["z"]])

        while True:
            # ---------------------------------------------------------
            # 1. 获取真实传感器数据（图像 + 深度 + 状态）
            # ---------------------------------------------------------
            sensor_data = self.executor.get_sensor_data()

            # ---------------------------------------------------------
            # 2. 构造 prompt（真实数据 → 文本）
            # ---------------------------------------------------------
            prompt = self.executor.build_prompt(sensor_data)

            # ---------------------------------------------------------
            # 3. 发送 prompt 给 LLMInterface（假装大模型收到了真实数据）
            # ---------------------------------------------------------
            action_json, status = self.llm.get_action(prompt)

            # ---------------------------------------------------------
            # 4. 解析动作
            # ---------------------------------------------------------
            parsed = self.executor.parse(action_json)

            # ---------------------------------------------------------
            # 5. 执行动作
            # ---------------------------------------------------------
            exec_status = self.executor.execute(parsed)

            # ---------------------------------------------------------
            # 6. 获取无人机状态（执行动作后）
            # ---------------------------------------------------------
            drone_state = self.get_drone_state()

            # ---------------------------------------------------------
            # 7. 写日志
            # ---------------------------------------------------------
            self.logger.log({
                "prompt": prompt,
                "llm_output": action_json,
                "parsed_action": parsed,
                "execution_status": exec_status,
                "drone_state": drone_state,
                "sensor_data": {
                    "depth_summary": sensor_data["depth_summary"]
                }
            })

            step_count += 1
            trajectory.append([drone_state["x"], drone_state["y"], drone_state["z"]])
            plan_steps.append({
                "step": step_count,
                "raw_model_output": action_json,
                "parsed_action": parsed,
                "execute_status": exec_status,
                "drone_state_after": drone_state,
            })

            # ---------------------------------------------------------
            # 8. 判断是否结束任务
            # ---------------------------------------------------------
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