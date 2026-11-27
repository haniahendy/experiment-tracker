"""Append-only JSONL run store."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterator, List, Optional

STORE_FILENAME = "runs.jsonl"


@dataclass
class Run:
    name: str
    metrics: Dict[str, float] = field(default_factory=dict)
    params: Dict[str, object] = field(default_factory=dict)
    note: str = ""
    git_sha: str = ""
    ts: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "ts": self.ts,
            "metrics": self.metrics,
            "params": self.params,
            "note": self.note,
            "git_sha": self.git_sha,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "Run":
        return cls(
            name=str(payload["name"]),
            ts=str(payload.get("ts", "")),
            metrics={k: float(v) for k, v in payload.get("metrics", {}).items()},
            params=dict(payload.get("params", {})),
            note=str(payload.get("note", "")),
            git_sha=str(payload.get("git_sha", "")),
        )


def parse_value(raw: str):
    """Parse a CLI key=value value into int/float/bool when it looks like one."""
    lowered = raw.lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    for caster in (int, float):
        try:
            return caster(raw)
        except ValueError:
            continue
    return raw


def parse_assignments(pairs) -> Dict[str, object]:
    """Parse repeated --param/--metric k=v flags; later duplicates win."""
    out: Dict[str, object] = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise ValueError(f"expected key=value, got {pair!r}")
        key, raw = pair.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"empty key in {pair!r}")
        out[key] = parse_value(raw.strip())
    return out


class RunStore:
    """Reads and appends runs in a directory's runs.jsonl file."""

    def __init__(self, directory: str) -> None:
        self.directory = directory
        self.path = os.path.join(directory, STORE_FILENAME)

    def log(self, run: Run) -> Run:
        if not run.name:
            raise ValueError("run name must not be empty")
        if not run.ts:
            run.ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        os.makedirs(self.directory, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(run.to_dict(), sort_keys=True) + "\n")
        return run

    def runs(self) -> List[Run]:
        if not os.path.exists(self.path):
            return []
        out: List[Run] = []
        with open(self.path, encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(Run.from_dict(json.loads(line)))
                except (json.JSONDecodeError, KeyError, TypeError) as exc:
                    raise ValueError(f"corrupt store line {line_no}: {exc}") from exc
        return out

    def metric_names(self) -> List[str]:
        names = set()
        for run in self.runs():
            names.update(run.metrics)
        return sorted(names)
