from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


@dataclass(frozen=True)
class TaskSpec:
    task_id: Union[int, str]
    task_kind: str  # bootstrap_simple | vln
    source_task_id: Optional[int] = None


@dataclass
class TaskRunResult:
    task_id: Union[int, str]
    task_kind: str
    output_dir: str
    ok: bool
    end_reason: str
    steps: int
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowRunResult:
    bootstrap_ok: bool
    task_results: List[TaskRunResult]

    @property
    def exit_code(self) -> int:
        if not self.bootstrap_ok:
            return 1
        return 0 if all(r.ok for r in self.task_results) else 1

