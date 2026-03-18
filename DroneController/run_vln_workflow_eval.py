import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from DroneController.workflow.manager import WorkflowManager


def main() -> int:
    parser = argparse.ArgumentParser(description="Run online VLN workflow evaluation with mandatory task sequence.")
    parser.add_argument("--dataset_root", type=str, default=str(Path("Datasets") / "vln"))
    parser.add_argument("--task_root", type=str, default="task")
    parser.add_argument("--task_ids", type=int, nargs="+", required=True, help="Task sequence, e.g. --task_ids 1 2 3")
    parser.add_argument("--max_steps", type=int, default=200)
    parser.add_argument("--bootstrap_max_steps", type=int, default=5)
    args = parser.parse_args()

    dataset_root = Path(args.dataset_root)
    task_root = Path(args.task_root)

    manager = WorkflowManager(
        dataset_root=dataset_root,
        task_root=task_root,
        max_steps=int(args.max_steps),
        bootstrap_max_steps=int(args.bootstrap_max_steps),
    )
    result = manager.run(task_ids=[int(t) for t in args.task_ids])
    return int(result.exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
