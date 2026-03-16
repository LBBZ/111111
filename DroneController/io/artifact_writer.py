import csv
from concurrent.futures import ThreadPoolExecutor
import json
import shutil
import time
from threading import Lock
from pathlib import Path
from typing import Iterable


class WorkflowArtifactWriter:
    """Owns task directory lifecycle and artifact writing for one workflow run."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="artifact_writer")
        self._pending = []
        self._lock = Lock()

    def prepare_for_rerun(self) -> None:
        old_episodes_dir = self.output_dir / "episodes"
        if old_episodes_dir.exists() and old_episodes_dir.is_dir():
            shutil.rmtree(old_episodes_dir)

        legacy_jsonl = self.output_dir / "drone_log.jsonl"
        if legacy_jsonl.exists() and legacy_jsonl.is_file():
            legacy_jsonl.unlink()

        old_step_visual_dir = self.output_dir / "step_visual"
        if old_step_visual_dir.exists() and old_step_visual_dir.is_dir():
            shutil.rmtree(old_step_visual_dir)

    @staticmethod
    def now_str() -> str:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    def write_json(self, name: str, obj) -> None:
        path = self.output_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

    def write_traj_csv(self, name: str, positions_m: Iterable[Iterable[float]]) -> None:
        path = self.output_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["step", "x", "y", "z"])
            for i, p in enumerate(positions_m):
                x, y, z = map(float, p)
                writer.writerow([i, x, y, z])

    def save_step_visual(self, step_idx: int, sensor_data: dict, camera) -> None:
        step_dir = self.output_dir / "step_visual" / f"step_{step_idx:03d}"
        step_dir.mkdir(parents=True, exist_ok=True)

        rgb_views = sensor_data.get("rgb_views", {})
        for view_name in ["Front", "Back", "Left", "Right", "FrontLeft", "FrontRight", "BackLeft", "BackRight", "TopDown"]:
            camera.save_image(rgb_views.get(view_name), str(step_dir / f"{view_name}.png"))

        camera.save_image(sensor_data.get("mosaic_image"), str(step_dir / "Merged.png"))

        depth_maps = sensor_data.get("depth_maps", {})
        for view_name in ["Front", "Back", "Left", "Right", "TopDown"]:
            camera.save_depth_image(depth_maps.get(view_name), str(step_dir / f"{view_name}_depth.png"))

    def save_step_visual_async(self, step_idx: int, sensor_data: dict, camera):
        """Queue visual saving in a background worker to reduce step latency."""
        future = self._executor.submit(self.save_step_visual, int(step_idx), sensor_data, camera)
        with self._lock:
            self._pending.append(future)
        return future

    def wait_for_pending(self) -> None:
        """Block until all queued save jobs finish and raise first error if any."""
        with self._lock:
            pending = self._pending
            self._pending = []
        first_exc = None
        for f in pending:
            try:
                f.result()
            except Exception as e:  # pragma: no cover - surfaced to caller
                if first_exc is None:
                    first_exc = e
        if first_exc is not None:
            raise first_exc

    def close(self) -> None:
        try:
            self.wait_for_pending()
        finally:
            self._executor.shutdown(wait=True)

