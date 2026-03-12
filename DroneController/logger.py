# logger.py
import time
from datetime import datetime

class Logger:
    """
    改造版日志系统：
    - 分块写入，提升可读性
    - 大字段只写摘要，不写完整矩阵
    """

    def __init__(self, filename="drone_log.txt"):
        self.filename = filename

    def log(self, entry: dict):
        """
        entry: dict，包含 prompt, llm_output, parsed_action, drone_state, sensor_data 等
        """

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(self.filename, "a", encoding="utf-8") as f:
            f.write("\n" + "="*60 + "\n")
            f.write(f"Timestamp: {timestamp}\n")

            # Prompt 摘要
            f.write("\n--- Prompt ---\n")
            prompt = entry.get("prompt", "")
            if isinstance(prompt, str):
                # 避免写出整块矩阵
                f.write(prompt[:200] + "...\n" if len(prompt) > 200 else prompt + "\n")

            # LLM 输出
            f.write("\n--- LLM Output ---\n")
            f.write(str(entry.get("llm_output", {})) + "\n")

            # 解析后的动作
            f.write("\n--- Parsed Action ---\n")
            f.write(str(entry.get("parsed_action", {})) + "\n")

            # 执行状态
            f.write("\n--- Execution Status ---\n")
            f.write(str(entry.get("execution_status", "")) + "\n")

            # 无人机状态
            f.write("\n--- Drone State ---\n")
            f.write(str(entry.get("drone_state", {})) + "\n")

            # 传感器数据（深度摘要）
            f.write("\n--- Sensor Data (Depth Summary) ---\n")
            f.write(str(entry.get("sensor_data", {}).get("depth_summary", {})) + "\n")

            f.write("="*60 + "\n")
