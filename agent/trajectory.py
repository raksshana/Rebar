from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import json


@dataclass
class Step:
    step_index: int
    tool_name: str
    tool_args: dict
    tool_result: dict
    thought: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Trajectory:
    task_id: str
    model_id: str
    source_schema_id: str
    dest_schema_id: str
    max_steps: int
    steps: list[Step] = field(default_factory=list)
    completed: bool = False
    final_score: float | None = None

    def save(self, path: str) -> None:
        data = {
            "task_id": self.task_id,
            "model_id": self.model_id,
            "source_schema_id": self.source_schema_id,
            "dest_schema_id": self.dest_schema_id,
            "max_steps": self.max_steps,
            "steps": [s.to_dict() for s in self.steps],
            "completed": self.completed,
            "final_score": self.final_score,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: str) -> Trajectory:
        with open(path) as f:
            data = json.load(f)
        steps = [Step(**s) for s in data.pop("steps")]
        return cls(steps=steps, **data)
