import json
import os
import tempfile
import unittest

from xtrack import Run, RunStore, best_run, compare_table
from xtrack.store import parse_assignments, parse_value


def make_store():
    tmp = tempfile.TemporaryDirectory()
    return tmp, RunStore(tmp.name)


class TestParseValue(unittest.TestCase):
    def test_scalars(self):
        self.assertEqual(parse_value("0.01"), 0.01)
        self.assertEqual(parse_value("64"), 64)
        self.assertEqual(parse_value("true"), True)
        self.assertEqual(parse_value("adam"), "adam")

    def test_assignments_last_wins_and_validation(self):
        self.assertEqual(parse_assignments(["a=1", "a=2"]), {"a": 2})
        with self.assertRaises(ValueError):
            parse_assignments(["no-equals"])
        with self.assertRaises(ValueError):
            parse_assignments(["=1"])


class TestStore(unittest.TestCase):
    def test_log_and_read_back(self):
        tmp, store = make_store()
        self.addCleanup(tmp.cleanup)
        store.log(Run(name="r1", metrics={"acc": 0.9}, params={"lr": 0.01}))
        store.log(Run(name="r2", metrics={"acc": 0.8}))
        runs = store.runs()
        self.assertEqual([r.name for r in runs], ["r1", "r2"])
        self.assertEqual(runs[0].metrics["acc"], 0.9)
        self.assertTrue(runs[0].ts)  # timestamp filled automatically

    def test_empty_store_reads_empty(self):
        tmp, store = make_store()
        self.addCleanup(tmp.cleanup)
        self.assertEqual(store.runs(), [])

    def test_corrupt_line_reports_line_number(self):
        tmp, store = make_store()
        self.addCleanup(tmp.cleanup)
        os.makedirs(tmp.name, exist_ok=True)
        with open(store.path, "w") as fh:
            fh.write('{"name": "ok", "metrics": {}}\nnot-json\n')
        with self.assertRaises(ValueError) as ctx:
            store.runs()
        self.assertIn("line 2", str(ctx.exception))

    def test_blank_run_name_rejected(self):
        tmp, store = make_store()
        self.addCleanup(tmp.cleanup)
        with self.assertRaises(ValueError):
            store.log(Run(name=""))

    def test_metric_names_union(self):
        tmp, store = make_store()
        self.addCleanup(tmp.cleanup)
        store.log(Run(name="r1", metrics={"acc": 0.9, "f1": 0.8}))
        store.log(Run(name="r2", metrics={"loss": 0.3}))
        self.assertEqual(store.metric_names(), ["acc", "f1", "loss"])


class TestCompare(unittest.TestCase):
    def _runs(self):
        return [
            Run(name="a", metrics={"acc": 0.80, "loss": 0.40}, ts="t1"),
            Run(name="b", metrics={"acc": 0.91, "loss": 0.25}, ts="t2"),
            Run(name="c", metrics={"acc": 0.85}, ts="t3"),
        ]

    def test_best_max_and_min(self):
        runs = self._runs()
        self.assertEqual(best_run(runs, "acc").name, "b")
        self.assertEqual(best_run(runs, "loss", mode="min").name, "b")

    def test_best_ignores_missing_metric(self):
        runs = self._runs()
        self.assertEqual(best_run(runs, "loss").name, "a")

    def test_best_none_when_metric_absent(self):
        self.assertIsNone(best_run(self._runs(), "auc"))

    def test_best_rejects_bad_mode(self):
        with self.assertRaises(ValueError):
            best_run(self._runs(), "acc", mode="median")

    def test_compare_table_sorted(self):
        table = compare_table(self._runs(), metric="acc")
        lines = table.splitlines()
        self.assertTrue(lines[0].startswith("| run |"))
        body = [ln for ln in lines if ln.startswith("| ") and "---" not in ln][1:]
        self.assertIn("| b |", body[0])
        self.assertIn("| a |", body[-1])
        self.assertIn("metric:acc", lines[0])
        self.assertIn("metric:loss", lines[0])


if __name__ == "__main__":
    unittest.main()
