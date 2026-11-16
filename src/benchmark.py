"""Deterministic experiments; run with python -m src.benchmark."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import random
import statistics
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter_ns

from .algorithms import Metrics, kmp, rabin_karp

SIZES = (1000, 5000, 10000, 50000, 100000)
SEEDS = (42, 43, 44)
MODULI = (5, 11, 101, 1009, 10007)
DATASETS = ("random", "repetitive")
M = 12
WARMUPS = 2
REPETITIONS = 7
TARGET_BATCH_NS = 5_000_000
MAX_BATCH = 100


def dataset(kind, n, seed):
    rng = random.Random(seed)
    if kind == "random":
        motif = "".join(rng.choices("ACGT", k=M))
        text = "".join(rng.choices("ACGT", k=n))
        middle = n // 2
        return text[:middle] + motif + text[middle + M:], motif
    if kind == "repetitive":
        letter = rng.choice("ACGT")
        return letter * n, letter * M
    raise ValueError(f"Unknown dataset: {kind}")


def oracle(text, motif):
    """Independent reference using repeated built-in find, allowing overlaps."""
    matches = []
    start = 0
    while True:
        position = text.find(motif, start)
        if position < 0:
            return matches
        matches.append(position)
        start = position + 1


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def measure(functions):
    """Warm up, calibrate, then alternate/reverse order across repetitions."""
    batches = {}
    for name, search in functions.items():
        for _ in range(WARMUPS):
            search()
        start = perf_counter_ns()
        search()
        elapsed = max(1, perf_counter_ns() - start)
        batches[name] = min(MAX_BATCH, max(1, (TARGET_BATCH_NS + elapsed - 1) // elapsed))
    samples = {name: [] for name in functions}
    for repetition in range(REPETITIONS):
        order = list(functions)
        if repetition % 2:
            order.reverse()
        for name in order:
            search = functions[name]
            count = batches[name]
            start = perf_counter_ns()
            for _ in range(count):
                search()
            elapsed = (perf_counter_ns() - start) / count
            samples[name].append((repetition + 1, count, elapsed))
    return samples


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    raw, summary, collisions, manifest = [], [], [], []
    for kind in DATASETS:
        for n in SIZES:
            for seed in SEEDS:
                text, motif = dataset(kind, n, seed)
                expected = oracle(text, motif)
                manifest.append(dict(dataset=kind, seed=seed, n=n, motif=motif,
                                     sha256=hashlib.sha256(text.encode("ascii")).hexdigest()))
                searches = {"KMP": lambda: kmp(text, motif),
                            "Rabin-Karp": lambda: rabin_karp(text, motif, 1009)}
                samples = measure(searches)
                for name in searches:
                    metrics = Metrics()
                    found = (kmp(text, motif, metrics) if name == "KMP"
                             else rabin_karp(text, motif, 1009, metrics))
                    assert found == expected == searches[name]()
                    common = dict(experiment="scaling", dataset=kind, seed=seed,
                                  n=n, m=M, algorithm=name, q=1009 if name == "Rabin-Karp" else "")
                    for repetition, batch, elapsed in samples[name]:
                        raw.append(dict(**common, repetition=repetition, batch_count=batch,
                                        elapsed_ns_per_search=elapsed))
                    summary.append(dict(**common, median_time_ns=statistics.median(s[2] for s in samples[name]),
                                        match_count=len(found), **asdict(metrics)))
            print(f"Scaling measured: {kind}, n={n}", flush=True)
    for seed in SEEDS:
        text, motif = dataset("random", 100000, seed)
        expected = oracle(text, motif)
        searches = {q: (lambda q=q: rabin_karp(text, motif, q)) for q in MODULI}
        samples = measure(searches)
        for q in MODULI:
            metrics = Metrics()
            found = rabin_karp(text, motif, q, metrics)
            assert found == expected == searches[q]()
            assert metrics.hash_hits == len(found) + metrics.spurious_hits
            for repetition, batch, elapsed in samples[q]:
                raw.append(dict(experiment="collisions", dataset="random", seed=seed,
                                n=len(text), m=M, algorithm="Rabin-Karp", q=q,
                                repetition=repetition, batch_count=batch, elapsed_ns_per_search=elapsed))
            collisions.append(dict(seed=seed, n=len(text), m=M, q=q, windows=metrics.hash_checks,
                                   true_matches=len(found), hash_hits=metrics.hash_hits,
                                   spurious_hits=metrics.spurious_hits,
                                   median_time_ns=statistics.median(s[2] for s in samples[q])))
        print(f"Modulus experiment measured: seed={seed}", flush=True)
    write_csv(output / "raw_timings.csv", raw)
    write_csv(output / "summary.csv", summary)
    write_csv(output / "collisions.csv", collisions)
    (output / "datasets.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (Path(__file__), Path(__file__).with_name("algorithms.py"))}
    environment = dict(benchmark_date_utc=datetime.now(timezone.utc).isoformat(),
                       os=platform.platform(), cpu=platform.processor(), logical_cpus=os.cpu_count(),
                       python=platform.python_version(), implementation=platform.python_implementation(),
                       dependencies={"matplotlib": importlib.metadata.version("matplotlib")},
                       sizes=SIZES, seeds=SEEDS, motif_length=M, moduli=MODULI, base=4,
                       warmups=WARMUPS, repetitions=REPETITIONS, target_batch_ns=TARGET_BATCH_NS,
                       max_batch=MAX_BATCH, counter="time.perf_counter_ns", source_sha256=hashes,
                       aggregation="Median of seven repetitions per input; chart/table median of three seed medians.",
                       timing_scope="Preprocessing and search with counters disabled; excludes validation and I/O.",
                       order="Forward order on even zero-based repetitions; reversed on odd repetitions.")
    (output / "environment.json").write_text(json.dumps(environment, indent=2), encoding="utf-8")
    print(f"Saved {len(raw)} timings, {len(summary)} scaling rows, {len(collisions)} collision rows to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results"))
    run(parser.parse_args().output)
