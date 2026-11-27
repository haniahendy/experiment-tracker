# experiment-tracker

A tiny local experiment tracker for ML runs. Appends each run as one
JSON Line to a plain file: no server, no database, no dependencies , 
and answers the questions you actually ask during a tuning loop: what
did I try, which run won, and what differed.

Pure Python 3.10+, zero dependencies.

## Usage

```bash
PYTHONPATH=src python3 -m xtrack.cli --dir .xtrack log --run baseline \
    --param lr=0.01 --param model=logreg \
    --metric acc=0.881 --metric loss=0.41 --note "first try"
PYTHONPATH=src python3 -m xtrack.cli --dir .xtrack best --metric acc
PYTHONPATH=src python3 -m xtrack.cli --dir .xtrack compare --metric acc
```

```
tuned	acc=0.903	2026-11-26T08:41:30+00:00
```

```markdown
| run | ts | metric:acc | metric:loss | param:lr | param:model | note |
| --- | --- | --- | --- | --- | --- | --- |
| tuned | 2026-11-26T08:41:30+00:00 | 0.903 | 0.33 | 0.05 | logreg |  |
| baseline | 2026-11-26T08:41:30+00:00 | 0.881 | 0.41 | 0.01 | logreg | first try |
```

`compare` prints a Markdown table you can paste into a PR or lab note;
`best --min` flips to lower-is-better (loss, latency); `list` dumps all
runs as JSON. Values are parsed as int/float/bool when they look like
one, strings otherwise. The store is `.xtrack/runs.jsonl`: commit it
for a paper trail or gitignore it; the tool doesn't care.

## Honest limits

- Local and single-writer by design: no concurrency control, so parallel
  training jobs must use separate `--dir`s and merge files afterwards.
- No artifact storage (models, plots); log paths in `--note` or params
  and keep artifacts elsewhere.
- Metrics are trusted as given: the tracker records numbers, it does
  not recompute or validate them against a dataset.
- No user accounts or sharing; for team dashboards use a hosted tracker
  instead. This is the layer below that, for the solo tuning loop.
- Timestamps are UTC ISO-8601 from the logging machine's clock.

## Tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

12 tests: value parsing and assignment validation, append/read
round-trip, corrupt-line diagnostics, best-run selection with missing
metrics and mode checks, and sorted Markdown table rendering.
