"""Audit saved results against dataset reconstruction, metrics, and raw timings."""
import hashlib
import json
import math
import statistics
from dataclasses import asdict
from pathlib import Path

from .algorithms import Metrics, kmp, rabin_karp
from .benchmark import DATASETS, MODULI, REPETITIONS, SEEDS, SIZES, dataset, oracle
from .plot_results import aggregate, read_csv


def verify(root=Path(".")):
    results = root / "results"
    raw = read_csv(results / "raw_timings.csv")
    summary = read_csv(results / "summary.csv")
    collisions = read_csv(results / "collisions.csv")
    expected_scaling = {(d, s, n, a) for d in DATASETS for s in SEEDS for n in SIZES
                        for a in ("KMP", "Rabin-Karp")}
    actual_scaling = {(r["dataset"], int(r["seed"]), int(r["n"]), r["algorithm"]) for r in summary}
    assert actual_scaling == expected_scaling and len(summary) == len(expected_scaling)
    expected_collisions = {(s, q) for s in SEEDS for q in MODULI}
    assert {(int(r["seed"]), int(r["q"])) for r in collisions} == expected_collisions
    assert len(collisions) == len(expected_collisions)
    used_raw = set()

    def check_times(row, experiment):
        indices = [i for i, r in enumerate(raw) if r["experiment"] == experiment
                   and r["seed"] == row["seed"] and r["q"] == row["q"]
                   and r["n"] == row["n"] and r["m"] == row["m"]
                   and (experiment == "collisions" or
                        (r["dataset"] == row["dataset"] and r["algorithm"] == row["algorithm"]))]
        assert len(indices) == REPETITIONS
        samples = [raw[i] for i in indices]
        assert {int(r["repetition"]) for r in samples} == set(range(1, REPETITIONS + 1))
        assert all(1 <= int(r["batch_count"]) <= 100 for r in samples)
        times = [float(r["elapsed_ns_per_search"]) for r in samples]
        assert all(math.isfinite(t) and t > 0 for t in times)
        assert math.isclose(statistics.median(times), float(row["median_time_ns"]), rel_tol=1e-12)
        assert not used_raw.intersection(indices)
        used_raw.update(indices)

    for row in summary:
        text, motif = dataset(row["dataset"], int(row["n"]), int(row["seed"]))
        assert len(motif) == int(row["m"]) == 12
        metrics = Metrics()
        if row["algorithm"] == "KMP":
            assert row["q"] == ""
            positions = kmp(text, motif, metrics)
        else:
            assert int(row["q"]) == 1009
            positions = rabin_karp(text, motif, int(row["q"]), metrics)
        assert positions == oracle(text, motif)
        assert len(positions) == int(row["match_count"])
        for key, value in asdict(metrics).items():
            assert int(row[key]) == value
        check_times(row, "scaling")
    for row in collisions:
        assert int(row["n"]) == 100000 and int(row["m"]) == 12
        text, motif = dataset("random", int(row["n"]), int(row["seed"]))
        metrics = Metrics()
        positions = rabin_karp(text, motif, int(row["q"]), metrics)
        assert positions == oracle(text, motif)
        assert len(positions) == int(row["true_matches"])
        assert int(row["windows"]) == len(text) - len(motif) + 1 == metrics.hash_checks
        assert int(row["hash_hits"]) == metrics.hash_hits == len(positions) + metrics.spurious_hits
        assert int(row["spurious_hits"]) == metrics.spurious_hits
        check_times(row, "collisions")
    assert len(used_raw) == len(raw)
    assert any(int(r["spurious_hits"]) > 0 for r in collisions)
    manifest = json.loads((results / "datasets.json").read_text())
    expected_datasets = {(d, s, n) for d in DATASETS for s in SEEDS for n in SIZES}
    assert {(r["dataset"], r["seed"], r["n"]) for r in manifest} == expected_datasets
    assert len(manifest) == len(expected_datasets)
    for row in manifest:
        text, motif = dataset(row["dataset"], row["n"], row["seed"])
        assert motif == row["motif"] and len(text) == row["n"]
        assert hashlib.sha256(text.encode("ascii")).hexdigest() == row["sha256"]
    env = json.loads((results / "environment.json").read_text())
    assert env["repetitions"] == REPETITIONS and env["warmups"] == 2
    assert env["seeds"] == list(SEEDS) and env["sizes"] == list(SIZES)
    assert env["moduli"] == list(MODULI) and env["base"] == 4
    for name, digest in env["source_sha256"].items():
        assert hashlib.sha256((root / "src" / name).read_bytes()).hexdigest() == digest
    for expected, filename in zip(aggregate(summary, collisions), ("chart_scaling.csv", "chart_collisions.csv")):
        actual = read_csv(results / filename)
        assert len(actual) == len(expected)
        for a, e in zip(actual, expected):
            for key, value in e.items():
                assert a[key] == str(value)
    for name in ("runtime", "comparisons", "collisions"):
        png = (root / "figures" / f"{name}.png").read_bytes()
        pdf = (root / "figures" / f"{name}.pdf").read_bytes()
        assert png.startswith(b"\x89PNG\r\n\x1a\n") and len(png) > 10000
        assert pdf.startswith(b"%PDF-") and len(pdf) > 1000
    assert (results / "tables.md").stat().st_size > 1000
    print(f"EXPERIMENTS VERIFIED: {len(raw)} timing samples, {len(summary)} scaling rows, {len(collisions)} collision rows; six figure files")


if __name__ == "__main__":
    verify()
