import json
from datetime import datetime
from pathlib import Path


class Color:
    BLUE = "\033[34m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    RESET = "\033[0m"


class Logger:
    """Dual log writer: readable txt + formatted machine json."""

    def __init__(self, txt_file="drone_log.txt", json_file="drone_log.json", output_dir=None, overwrite=True):
        if output_dir is None:
            self.txt_file = str(txt_file)
            self.json_file = str(json_file)
        else:
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            self.txt_file = str(out_dir / txt_file)
            self.json_file = str(out_dir / json_file)

        if overwrite:
            Path(self.txt_file).write_text("", encoding="utf-8")
            Path(self.json_file).write_text("[]", encoding="utf-8")

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def log_step(self, step: int, target_pos: dict, task_id=None) -> None:
        line = (
            f"[step={int(step)}] target=({float(target_pos.get('x', 0.0)):.2f},"
            f" {float(target_pos.get('y', 0.0)):.2f}, {float(target_pos.get('z', 0.0)):.2f})"
        )
        if task_id is not None:
            line = f"[task={task_id}] " + line
        print(Color.CYAN + line + Color.RESET)

    def log(self, entry: dict):
        timestamp = self._now()
        prompt_dict = {}

        with open(self.txt_file, "a", encoding="utf-8") as f:
            f.write("\n" + "=" * 60 + "\n")
            f.write(f"Timestamp: {timestamp}\n")

            f.write("\n--- Prompt JSON ---\n")
            try:
                prompt_dict = json.loads(entry["prompt"])
                f.write(json.dumps(prompt_dict, indent=4, ensure_ascii=False) + "\n")
            except Exception:
                prompt_dict = {"raw_prompt": entry.get("prompt", "")}
                f.write("<invalid prompt json>\n")

            f.write("\n--- LLM Output ---\n")
            f.write(json.dumps(entry.get("llm_output", {}), indent=4, ensure_ascii=False) + "\n")

            f.write("\n--- Parsed Action ---\n")
            f.write(json.dumps(entry.get("parsed_action", {}), indent=4, ensure_ascii=False) + "\n")

            f.write("\n--- Drone State ---\n")
            f.write(json.dumps(entry.get("drone_state", {}), indent=4, ensure_ascii=False) + "\n")

            f.write("\n--- Depth Summary ---\n")
            depth_summary = entry.get("sensor_data", {}).get("depth_summary", {})
            f.write(json.dumps(depth_summary, indent=4, ensure_ascii=False) + "\n")

            f.write("=" * 60 + "\n")

        json_entry = {
            "timestamp": timestamp,
            "prompt": prompt_dict,
            "llm_output": entry.get("llm_output", {}),
            "parsed_action": entry.get("parsed_action", {}),
            "drone_state": entry.get("drone_state", {}),
            "sensor_data": entry.get("sensor_data", {}),
        }

        json_path = Path(self.json_file)
        if json_path.exists():
            try:
                records = json.loads(json_path.read_text(encoding="utf-8"))
                if not isinstance(records, list):
                    records = []
            except Exception:
                records = []
        else:
            records = []

        records.append(json_entry)
        json_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

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
