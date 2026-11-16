"""Render print-ready graphs and compact tables from the measured CSV files."""
import argparse
import csv
import statistics
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .benchmark import DATASETS, MODULI, SIZES, write_csv


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def aggregate(summary, collisions):
    scaling = []
    for dataset in DATASETS:
        for n in SIZES:
            for algorithm in ("KMP", "Rabin-Karp"):
                rows = [r for r in summary if r["dataset"] == dataset
                        and int(r["n"]) == n and r["algorithm"] == algorithm]
                if len(rows) != 3:
                    raise ValueError("Expected three seeds per scaling point.")
                times = [float(r["median_time_ns"]) / 1e6 for r in rows]
                scaling.append(dict(dataset=dataset, n=n, algorithm=algorithm,
                                    time_ms=statistics.median(times), min_time_ms=min(times), max_time_ms=max(times),
                                    comparisons=statistics.median(int(r["preprocessing_comparisons"])
                                                                  + int(r["search_comparisons"]) for r in rows)))
    collision_points = []
    for q in MODULI:
        rows = [r for r in collisions if int(r["q"]) == q]
        if len(rows) != 3:
            raise ValueError("Expected three seeds per modulus.")
        hits = [int(r["spurious_hits"]) for r in rows]
        collision_points.append(dict(q=q, spurious_hits=statistics.median(hits),
                                     min_spurious_hits=min(hits), max_spurious_hits=max(hits),
                                     true_matches=statistics.median(int(r["true_matches"]) for r in rows)))
    return scaling, collision_points


def render(results, figures):
    figures.mkdir(parents=True, exist_ok=True)
    scaling, collisions = aggregate(read_csv(results / "summary.csv"), read_csv(results / "collisions.csv"))
    write_csv(results / "chart_scaling.csv", scaling)
    write_csv(results / "chart_collisions.csv", collisions)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    styles = {"KMP": dict(color="#185c91", marker="o", linestyle="-"),
              "Rabin-Karp": dict(color="#b54b13", marker="s", linestyle="--")}
    for field, ylabel, title, filename in (
        ("time_ms", "Search time (ms)", "Runtime versus DNA length", "runtime"),
        ("comparisons", "Character comparisons", "Character comparisons versus DNA length", "comparisons")):
        fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), layout="constrained")
        for axis, kind in zip(axes, DATASETS):
            for algorithm in styles:
                rows = [r for r in scaling if r["dataset"] == kind and r["algorithm"] == algorithm]
                x = [r["n"] for r in rows]
                y = [r[field] for r in rows]
                if field == "time_ms":
                    error = [[r[field] - r["min_time_ms"] for r in rows],
                             [r["max_time_ms"] - r[field] for r in rows]]
                    axis.errorbar(x, y, yerr=error, capsize=3, label=algorithm, **styles[algorithm])
                else:
                    axis.plot(x, y, label=algorithm, **styles[algorithm])
            axis.set(xlabel="DNA length n (characters)", ylabel=ylabel,
                     title="Random DNA + planted motif" if kind == "random" else "Repetitive DNA + overlapping matches")
            axis.ticklabel_format(style="sci", axis="both", scilimits=(0, 4))
            axis.grid(alpha=.2)
            axis.legend()
        fig.suptitle(title + " (m = 12, q = 1009)")
        for extension in ("png", "pdf"):
            fig.savefig(figures / f"{filename}.{extension}", dpi=200)
        plt.close(fig)
    fig, axis = plt.subplots(figsize=(7, 4.2), layout="constrained")
    x = [r["q"] for r in collisions]
    y = [r["spurious_hits"] for r in collisions]
    errors = [[r["spurious_hits"] - r["min_spurious_hits"] for r in collisions],
              [r["max_spurious_hits"] - r["spurious_hits"] for r in collisions]]
    axis.errorbar(x, y, yerr=errors, color="#185c91", marker="o", capsize=4)
    axis.set(xscale="log", yscale="log", xlabel="Modulus q (log scale)",
             ylabel="Spurious hits (log scale)", title="Rabin–Karp collisions (n = 100,000; m = 12)")
    axis.set_xticks(x, labels=[str(q) for q in x])
    axis.grid(alpha=.2, which="both")
    for extension in ("png", "pdf"):
        fig.savefig(figures / f"collisions.{extension}", dpi=200)
    plt.close(fig)
    lines = ["# Measured results for the future report", "",
             "Generated from summary.csv and collisions.csv. Runtime values are the median of the three seed medians; each seed median uses seven timed repetitions. Error bars show the minimum and maximum seed medians, not confidence intervals. Comparison and collision points are medians across the three seeds.", "",
             "## Runtime and character comparisons", "",
             "| Dataset | n | Algorithm | Time (ms) | Character comparisons |",
             "|---|---:|---|---:|---:|"]
    for row in scaling:
        lines.append(f"| {row['dataset']} | {row['n']:,} | {row['algorithm']} | {row['time_ms']:.4f} | {row['comparisons']:,} |")
    lines += ["", "## Spurious hits versus modulus", "",
              "| q | Median spurious hits | Minimum | Maximum | Median true matches |",
              "|---:|---:|---:|---:|---:|"]
    for row in collisions:
        lines.append(f"| {row['q']} | {row['spurious_hits']:,} | {row['min_spurious_hits']:,} | {row['max_spurious_hits']:,} | {row['true_matches']} |")
    lines += ["", "## Figure captions and interpretation constraints", "",
              "1. runtime.png: preprocessing plus search, without counters; excludes validation and I/O. Includes output-list construction. Bars show variation across seeds.",
              "2. comparisons.png: KMP LPS plus search character comparisons versus Rabin–Karp candidate-verification character comparisons. Hash checks and arithmetic are separate work, so character counts alone do not predict speed.",
              "3. collisions.png: fixed random DNA/motif pairs while changing q; base 4, encoding A=0/C=1/G=2/T=3. Both axes are logarithmic; bars show minimum/maximum spurious counts across seeds.", "",
              "Repetitive inputs have n-m+1 true matches. Rabin–Karp verifies all m characters at every window, illustrating its O(nm) verification cost. Here m stays fixed, so runtime can still grow approximately linearly with n.", "",
              "Synthetic DNA and three seeds do not establish performance on biological genomes. Timings are specific to this Python implementation and machine. The repetitive dataset may repeat across seeds because its alphabet choice has only four possibilities; seeds are not independent workload diversity there."]
    (results / "tables.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Generated three graphs in PNG and PDF, chart data, and tables.md in {results}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument("--figures", type=Path, default=Path("figures"))
    args = parser.parse_args()
    render(args.results, args.figures)
