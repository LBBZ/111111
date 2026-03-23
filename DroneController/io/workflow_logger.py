from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Union


class _Color:
    BLUE = "\033[34m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    CYAN = "\033[36m"
    RESET = "\033[0m"


class WorkflowLogger:
    """Main workflow logger: colored console + task directory detailed logs."""

    def __init__(self, task_root: Union[str, Path]):
        self.task_root = Path(task_root)
        self.task_root.mkdir(parents=True, exist_ok=True)
        self.console_path = self.task_root / "console.log"
        self.error_path = self.task_root / "error.log"
        self.md_path = self.task_root / "workflow_detail.md"
        self.console_path.write_text("", encoding="utf-8")
        self.error_path.write_text("", encoding="utf-8")
        self.md_path.write_text(
            "# 任务流详细日志\n\n"
            "## 本次运行将保存的文件\n"
            "- meta.json: 任务元信息（初始化、时间戳、错误）\n"
            "- plan.json: 每步动作计划\n"
            "- traj.csv: 轨迹点\n"
            "- results.json: 指标和终止原因\n"
            "- lifecycle.jsonl: 生命周期阶段日志\n"
            "- drone_log.txt / drone_log.json: 控制器详细日志\n"
            "- step_visual/: 每步图像和深度快照\n\n"
            "## 运行事件\n",
            encoding="utf-8",
        )

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _write_console(self, line: str) -> None:
        with self.console_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def _write_error(self, line: str) -> None:
        with self.error_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def _append_md(self, line: str) -> None:
        with self.md_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def info(self, msg: str) -> None:
        line = f"[{self._now()}][INFO] {msg}"
        print(f"{_Color.CYAN}{line}{_Color.RESET}")
        self._write_console(line)

    def warn(self, msg: str) -> None:
        line = f"[{self._now()}][WARN] {msg}"
        print(f"{_Color.YELLOW}{line}{_Color.RESET}")
        self._write_console(line)
        self._write_error(line)

    def error(self, msg: str) -> None:
        line = f"[{self._now()}][ERROR] {msg}"
        print(f"{_Color.RED}{line}{_Color.RESET}")
        self._write_console(line)
        self._write_error(line)

    def task_start(self, task_id, task_kind: str) -> None:
        msg = f"task start id={task_id} kind={task_kind}"
        line = f"[{self._now()}][TASK] {msg}"
        print(f"{_Color.BLUE}{line}{_Color.RESET}")
        self._write_console(line)
        self._append_md(f"- {self._now()} START task_id={task_id} kind={task_kind}")

    def task_end(self, task_id, ok: bool, end_reason: str) -> None:
        status = "OK" if ok else "FAILED"
        color = _Color.GREEN if ok else _Color.RED
        line = f"[{self._now()}][TASK] end id={task_id} status={status} end_reason={end_reason}"
        print(f"{color}{line}{_Color.RESET}")
        self._write_console(line)
        self._append_md(f"- {self._now()} END task_id={task_id} status={status} end_reason={end_reason}")

    def write_task_artifacts(self, task_id, output_dir: Union[str, Path], file_map: Dict[str, str]) -> None:
        self._append_md("")
        self._append_md(f"### task_id={task_id}")
        self._append_md(f"- output_dir: `{Path(output_dir)}`")
        for name, desc in file_map.items():
            self._append_md(f"- `{name}`: {desc}")

    def write_run_summary(self, lines: Iterable[str]) -> None:
        self._append_md("")
        self._append_md("## 运行汇总")
        for line in lines:
            self._append_md(f"- {line}")

