import json
from datetime import datetime

class Color:
    BLUE = "\033[34m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    RESET = "\033[0m"


class Logger:
    """
    双日志系统：
    - 人类可读 txt
    - 机器可读 json
    """

    def __init__(self, txt_file="drone_log.txt", json_file="drone_log.jsonl"):
        self.txt_file = txt_file
        self.json_file = json_file

    def log(self, entry: dict):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # -----------------------------
        # 1. 写人类可读 txt 日志
        # -----------------------------
        with open(self.txt_file, "a", encoding="utf-8") as f:
            f.write("\n" + "="*60 + "\n")
            f.write(f"Timestamp: {timestamp}\n")

            # Prompt JSON（带缩进）
            f.write("\n--- Prompt JSON ---\n")
            try:
                prompt_dict = json.loads(entry["prompt"])
                f.write(json.dumps(prompt_dict, indent=4, ensure_ascii=False) + "\n")
            except:
                f.write("<invalid prompt json>\n")

            # LLM Output
            f.write("\n--- LLM Output ---\n")
            f.write(json.dumps(entry.get("llm_output", {}), indent=4, ensure_ascii=False) + "\n")

            # Parsed Action
            f.write("\n--- Parsed Action ---\n")
            f.write(json.dumps(entry.get("parsed_action", {}), indent=4, ensure_ascii=False) + "\n")

            # Drone State
            f.write("\n--- Drone State ---\n")
            f.write(json.dumps(entry.get("drone_state", {}), indent=4, ensure_ascii=False) + "\n")

            # Depth Summary
            f.write("\n--- Depth Summary ---\n")
            depth_summary = entry.get("sensor_data", {}).get("depth_summary", {})
            f.write(json.dumps(depth_summary, indent=4, ensure_ascii=False) + "\n")

            f.write("="*60 + "\n")

        # -----------------------------
        # 2. 写机器可读 jsonl 日志
        # -----------------------------
        json_entry = {
            "timestamp": timestamp,
            "prompt": prompt_dict,
            "llm_output": entry.get("llm_output", {}),
            "parsed_action": entry.get("parsed_action", {}),
            "drone_state": entry.get("drone_state", {}),
            "sensor_data": entry.get("sensor_data", {})
        }

        with open(self.json_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(json_entry, ensure_ascii=False) + "\n")

    def log_console(self, entry):
        print(Color.BLUE + f"[Timestamp] {entry['timestamp']}" + Color.RESET)

        print(Color.YELLOW + "\n[Prompt JSON]" + Color.RESET)
        print(entry["prompt"])

        print(Color.CYAN + "\n[LLM Output]" + Color.RESET)
        print(entry["llm_output"])

        print(Color.GREEN + "\n[Parsed Action]" + Color.RESET)
        print(entry["parsed_action"])

        print(Color.MAGENTA + "\n[Drone State]" + Color.RESET)
        print(entry["drone_state"])

        print(Color.RESET)
