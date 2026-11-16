"""Run from the project root: python -m src.main --help."""
import argparse
import json
from dataclasses import asdict
from pathlib import Path
from time import perf_counter_ns

from .algorithms import Metrics, kmp, normalize_dna, rabin_karp


def main():
    parser = argparse.ArgumentParser(description="Find every exact DNA motif occurrence (zero-based).")
    parser.add_argument("file", type=Path, help="Plain text DNA file; whitespace is allowed")
    parser.add_argument("motif", help="Nonempty A/C/G/T motif")
    parser.add_argument("--algorithm", choices=("both", "kmp", "rk"), default="both")
    parser.add_argument("--q", type=int, default=1009, help="Rabin–Karp modulus > 1")
    parser.add_argument("--output", type=Path, help="Export full positions and metrics as JSON")
    args = parser.parse_args()
    try:
        text = normalize_dna(args.file.read_text(encoding="utf-8-sig"))
        pattern = normalize_dna(args.motif, motif=True)
        if args.q <= 1:
            raise ValueError("Modulus q must be greater than 1.")
        records = []
        algorithms = [("KMP", lambda metrics=None: kmp(text, pattern, metrics)),
                      ("Rabin-Karp", lambda metrics=None: rabin_karp(text, pattern, args.q, metrics))]
        if args.algorithm != "both":
            algorithms = [algorithms[0 if args.algorithm == "kmp" else 1]]
        print(f"DNA length: {len(text)} | Motif: {pattern} | Length: {len(pattern)}")
        for name, search in algorithms:
            start = perf_counter_ns()
            positions = search()
            elapsed = perf_counter_ns() - start
            metrics = Metrics()
            if positions != search(metrics):
                raise RuntimeError("Instrumented search disagrees with timed search.")
            record = dict(algorithm=name, positions=positions, match_count=len(positions),
                          elapsed_ns=elapsed, metrics=asdict(metrics))
            records.append(record)
            preview = str(positions[:20]) + (" ... (full list in JSON export)" if len(positions) > 20 else "")
            print(f"{name}: {len(positions)} match(es); positions: {preview}")
            print(f"  Search time: {elapsed / 1e6:.4f} ms (single run; use benchmarks for comparison)")
            print(f"  Character comparisons: {metrics.preprocessing_comparisons + metrics.search_comparisons}")
            if name == "Rabin-Karp":
                print(f"  q={args.q}; hash hits={metrics.hash_hits}; spurious hits={metrics.spurious_hits}")
        if len(records) == 2 and records[0]["positions"] != records[1]["positions"]:
            raise RuntimeError("Algorithms disagree.")
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(dict(n=len(text), motif=pattern, q=args.q,
                                                  results=records), indent=2), encoding="utf-8")
            print(f"Saved {args.output}")
    except (OSError, UnicodeError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
