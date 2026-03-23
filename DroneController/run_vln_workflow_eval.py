import argparse
import sys
from pathlib import Path

def _ensure_project_root_on_path() -> None:
    project_root = Path(__file__).resolve().parent.parent
    root_str = str(project_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


_ensure_project_root_on_path()

from DroneController.workflow.manager import WorkflowManager


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run online VLN workflow evaluation with mandatory task sequence."
    )
    parser.add_argument("--dataset_root", type=str, default=str(Path("Datasets") / "vln"))
    parser.add_argument("--task_root", type=str, default="task")
    parser.add_argument(
        "--task_ids",
        type=int,
        nargs="+",
        required=True,
        help="Task sequence, e.g. --task_ids 1 2 3",
    )
    parser.add_argument("--max_steps", type=int, default=200)
    parser.add_argument("--bootstrap_max_steps", type=int, default=5)
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    manager = WorkflowManager(
        dataset_root=Path(args.dataset_root),
        task_root=Path(args.task_root),
        max_steps=args.max_steps,
        bootstrap_max_steps=args.bootstrap_max_steps,
    )
    result = manager.run(task_ids=args.task_ids)
    return int(result.exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
