"""Command line entry point.

Examples:
    PYTHONPATH=src python3 -m xtrack.cli --dir .xtrack log --run baseline \
        --param lr=0.01 --metric acc=0.881 --note "first try"
    PYTHONPATH=src python3 -m xtrack.cli --dir .xtrack best --metric acc
    PYTHONPATH=src python3 -m xtrack.cli --dir .xtrack compare --metric acc
"""

from __future__ import annotations

import argparse
import json
import sys

from .compare import best_run, compare_table
from .store import Run, RunStore, parse_assignments


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="xtrack",
                                     description="Local JSONL experiment tracker.")
    parser.add_argument("--dir", default=".xtrack", help="store directory")
    sub = parser.add_subparsers(dest="command", required=True)

    p_log = sub.add_parser("log", help="append a run")
    p_log.add_argument("--run", required=True, help="run name")
    p_log.add_argument("--metric", action="append", default=[], metavar="K=V")
    p_log.add_argument("--param", action="append", default=[], metavar="K=V")
    p_log.add_argument("--note", default="")
    p_log.add_argument("--git-sha", default="")

    p_list = sub.add_parser("list", help="list runs as JSON")

    p_best = sub.add_parser("best", help="print the best run for a metric")
    p_best.add_argument("--metric", required=True)
    p_best.add_argument("--min", dest="mode", action="store_const",
                        const="min", default="max",
                        help="lower is better (default: higher is better)")

    p_cmp = sub.add_parser("compare", help="markdown table of runs")
    p_cmp.add_argument("--metric", default=None, help="sort by this metric")
    p_cmp.add_argument("--min", dest="mode", action="store_const",
                       const="min", default="max")

    args = parser.parse_args(argv)
    store = RunStore(args.dir)

    try:
        if args.command == "log":
            metrics = {k: float(v) for k, v in
                       parse_assignments(args.metric).items()}
            run = store.log(Run(name=args.run, metrics=metrics,
                                params=parse_assignments(args.param),
                                note=args.note, git_sha=args.git_sha))
            print(f"logged run {run.name!r} at {run.ts} "
                  f"({len(metrics)} metrics, {len(run.params)} params)")
        elif args.command == "list":
            print(json.dumps([r.to_dict() for r in store.runs()], indent=2))
        elif args.command == "best":
            run = best_run(store.runs(), args.metric, mode=args.mode)
            if run is None:
                print(f"no runs with metric {args.metric!r}", file=sys.stderr)
                return 1
            print(f"{run.name}\t{args.metric}={run.metrics[args.metric]:.6g}\t{run.ts}")
        elif args.command == "compare":
            print(compare_table(store.runs(), metric=args.metric, mode=args.mode))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
