# DNA Motif Finder

GitHub repository: [hragam22/daa4](https://www.github.com/hragam22/daa4)

A Design and Analysis of Algorithms project comparing **KMP** and **Rabin–Karp** for exact DNA motif matching. Given DNA text and a motif, both algorithms return every zero-based starting position, including overlaps.

Example: `ACGTACGTGACG` with motif `ACG` returns `[0, 4, 9]`.

## Setup

Run commands from this project folder. Python 3.10 or newer is required. The search program and correctness tests use only the Python standard library. Matplotlib is needed for graphs and the full result audit.

```powershell
python -m pip install -r requirements.txt
```

The measured environment, including the actual Python version, is saved in `results/environment.json`. No external dataset downloads are required.

## Run the finder

```powershell
python -m src.main data/example.txt ACG
python -m src.main data/example.txt ACG --algorithm kmp
python -m src.main data/example.txt ACG --algorithm rk --q 5
python -m src.main data/overlaps.txt AA --output results/example_matches.json
python -m src.main --help
```

Input is a plain UTF-8 text file containing A/C/G/T. Letter case and whitespace are normalized. The motif uses the same normalization. Invalid symbols and empty motifs are rejected. FASTA headers and ambiguous bases such as N are not supported. Empty DNA or a motif longer than the DNA gives no matches.

The default runs both algorithms and verifies that their positions agree. The console shows at most 20 positions; `--output` saves all positions and metrics as JSON. Positions are **zero-based**. A displayed single-run time is illustrative, not a benchmark conclusion.

## Reproduce the experiments

```powershell
python -m tests.run_checks
python -m src.benchmark
python -m src.plot_results
python -m src.verify_results
```

The benchmark overwrites generated CSV/environment files in `results/`. The plotting command overwrites charts and generated tables. Rerun plotting after benchmarking, then audit the new results. Timing values naturally change between runs; inputs and correctness outcomes are deterministic. Benchmark generation normally takes tens of seconds to a few minutes depending on hardware.

To keep an additional run:

```powershell
python -m src.benchmark --output results/another_run
python -m src.plot_results --results results/another_run --figures figures/another_run
```

The result verifier audits the default `results/` and `figures/` paths. The alternate-run commands preserve the default measured submission artifacts.

## Algorithms and complexity

### KMP

KMP preprocesses the motif into an LPS array: `lps[i]` is the length of the longest proper prefix of `pattern[:i+1]` that is also its suffix. A mismatch uses this array to avoid repeating already established comparisons. After finding a match, the same fallback preserves overlaps.

For motif `ACACAG`, the LPS array is `[0, 0, 1, 2, 3, 0]`.

```text
BUILD_LPS(P):
    LPS = zero array of length m
    length = 0; i = 1
    while i < m:
        if P[i] == P[length]:
            length += 1; LPS[i] = length; i += 1
        else if length > 0:
            length = LPS[length - 1]
        else:
            i += 1
    return LPS

KMP(T, P):
    reject empty P; return [] if m > n
    LPS = BUILD_LPS(P)
    i = 0; j = 0; matches = []
    while i < n:
        if T[i] == P[j]:
            i += 1; j += 1
            if j == m:
                append i-m to matches
                j = LPS[j-1]
        else if j > 0:
            j = LPS[j-1]
        else:
            i += 1
    return matches
```

### Rabin–Karp

The base is 4, with A=0, C=1, G=2, T=3. Hash a length-m string as the polynomial of its codes modulo q. Let `high = 4^(m-1) mod q`. Rolling the window from position i to i+1 uses:

```text
next_hash = (4 * (window_hash - code(T[i]) * high) + code(T[i+m])) mod q
```

An equal hash is only a candidate. Compare its characters directly before recording a match. Thus collisions affect work, not correctness.

For example, `AA` encodes 0 and `CC` encodes 5. Modulo 5 both hashes are 0, but their strings differ: this is one spurious hit. The test suite confirms that it is rejected.

```text
RABIN_KARP(T, P, q):
    reject empty P and invalid q; return [] if m > n
    high = 4^(m-1) mod q
    compute pattern_hash and first window_hash
    matches = []
    for i = 0 to n-m:
        if pattern_hash == window_hash:
            compare P with T starting at i, stopping at first mismatch
            if all m characters match: append i to matches
            otherwise: count one spurious hit
        if i < n-m:
            roll window_hash using the formula above
    return matches
```

| Algorithm | Preprocessing | Search | Auxiliary space |
|---|---|---|---|
| KMP | O(m) | O(n) | O(m) |
| Rabin–Karp | O(m) | O(n + Hm) upper bound, where H is hash hits | O(1) |

Rabin–Karp is typically O(n+m) with few candidate verifications, and O(nm) in the worst case. Even without spurious hits, many true matches require verification. Both algorithms store an additional O(k) output for k matches. Space excludes input and output storage. These bounds assume fixed-size modulus arithmetic; this project uses small moduli.

## Experimental design

- Five DNA lengths: 1,000; 5,000; 10,000; 50,000; 100,000.
- Motif length: 12. Seeds: 42, 43, 44.
- Random inputs: deterministic uniform DNA with the motif planted halfway through; incidental matches are counted too.
- Repetitive inputs: one repeated base, with a length-12 repeated-base motif; every window matches, including overlaps. Different seeds can choose the same base.
- Scaling comparison: KMP versus Rabin–Karp with q=1009.
- Collision experiment: fixed random DNA/motif per seed, n=100,000, q in {5, 11, 101, 1009, 10007}.
- Two warmups, one untimed calibration, seven timed repetitions. Calibrated batches target 5 ms, capped at 100 searches. Raw CSV records the actual batch count and per-search time.
- Algorithm/modulus order reverses on alternate repetitions.
- Timings include preprocessing, search, and result-list construction. They exclude input validation, generation, file I/O, printing, and metric increments. Optional-counter branches still exist in both timed cores.
- Each summary row is the median of seven repetitions. Charts/tables use the median of the three seed medians. Runtime error bars show the min/max seed medians, not confidence intervals.

The datasets are synthetic A/C/G/T strings, not sampled biological genomes. This tool finds exact occurrences; it does not establish biological significance or discover unknown motifs.

## Metrics

| Field | Meaning |
|---|---|
| preprocessing_comparisons | Character equality checks while constructing KMP LPS |
| search_comparisons | KMP text/pattern checks, or Rabin–Karp verification character checks |
| hash_checks | Rabin–Karp pattern/window hash equality checks |
| rolling_updates | Number of Rabin–Karp window slides |
| hash_hits | Windows whose hash equals the motif hash |
| spurious_hits | Hash hits rejected by character verification |

`hash_hits = match_count + spurious_hits`. The Rabin–Karp window count is `max(0, n-m+1)`. Character counts exclude hash arithmetic, indexing, loop conditions, and numeric comparisons. A smaller character count does not necessarily mean a faster search.

## Generated artifacts

- `results/raw_timings.csv`: individual repetition timings for both experiments.
- `results/summary.csv`: timing medians and algorithm metrics for every scaling input.
- `results/collisions.csv`: per-seed collision results for every modulus.
- `results/datasets.json`: motif and SHA-256 of each deterministic DNA input.
- `results/environment.json`: hardware/runtime metadata, settings, and source hashes.
- `results/chart_scaling.csv`, `results/chart_collisions.csv`: exact plotted aggregates.
- `results/tables.md`: readable measured tables, captions, and interpretation notes for the report.
- `figures/runtime.png`, `figures/comparisons.png`, `figures/collisions.png`: graphs, also available as vector PDF files.
- `results/findings.md`: interpretation of the verified saved run.

## Validation

Nine test methods cover a brute-force oracle, all binary-alphabet DNA strings through length five against motifs through length three, 300 deterministic random pairs, hand-counted comparison cases, LPS values, overlapping/boundary matches, deliberate collisions, normalization, invalid input, algorithm selection, and complete JSON exports.

The benchmark also checks every experimental input against an independent built-in string-search reference. `src.verify_results` reconstructs datasets, recomputes metrics, checks experiment coverage and collision invariants, reconciles summary medians with raw samples, checks source hashes, and compares chart aggregates with the measured data.

## Assignment status

Stage 1 is the implementation and measured evidence. The printable 4–6 page assignment report is Stage 2, using `plan.md` and these artifacts. Student identity fields remain in the report plan for later completion.

The assignment's general requirement is at least two algorithms. This project implements KMP and Rabin–Karp; finite automaton matching remains an extension if the instructor requires all algorithms listed in the project row.
