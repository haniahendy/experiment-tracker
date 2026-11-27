"""Run comparison and best-run selection."""

from __future__ import annotations

from typing import List, Optional, Sequence

from .store import Run


def best_run(runs: Sequence[Run], metric: str, mode: str = "max") -> Optional[Run]:
    """Return the run with the best value of ``metric``.

    Runs missing the metric are ignored; ties keep the earliest logged run.
    """
    if mode not in ("max", "min"):
        raise ValueError("mode must be 'max' or 'min'")
    candidates = [r for r in runs if metric in r.metrics]
    if not candidates:
        return None
    key = lambda r: r.metrics[metric]
    return max(candidates, key=key) if mode == "max" else min(candidates, key=key)


def _fmt_cell(value) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def compare_table(runs: Sequence[Run], metric: Optional[str] = None,
                  mode: str = "max") -> str:
    """Markdown table of runs; optionally sorted by one metric."""
    rows = list(runs)
    if metric is not None:
        reverse = mode == "max"
        rows.sort(
            key=lambda r: (metric not in r.metrics, -r.metrics.get(metric, 0.0)
                           if reverse else r.metrics.get(metric, 0.0)),
        )
    metric_names = sorted({m for r in rows for m in r.metrics})
    param_names = sorted({p for r in rows for p in r.params})
    header = ["run", "ts"] + [f"metric:{m}" for m in metric_names] + \
             [f"param:{p}" for p in param_names] + ["note"]
    lines = ["| " + " | ".join(header) + " |",
             "|" + "|".join(" --- " for _ in header) + "|"]
    for run in rows:
        cells = [run.name, run.ts]
        cells += [_fmt_cell(run.metrics[m]) if m in run.metrics else "" for m in metric_names]
        cells += [_fmt_cell(run.params[p]) if p in run.params else "" for p in param_names]
        cells.append(run.note)
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)
