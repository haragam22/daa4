# Findings from the saved Stage 1 run

These observations use the measured aggregates in `chart_scaling.csv` and `chart_collisions.csv`. See `environment.json` for the recorded machine, Python version, timestamp, and timing settings. Numbers below are medians across seeds, with a seven-repetition median computed first for each seed.

## Observations

- KMP was faster than Rabin–Karp in all ten dataset/size comparisons in this run. This is a result for this implementation and environment, not a universal ranking.
- At n=100,000 on random DNA, KMP took 8.5972 ms and Rabin–Karp took 19.6482 ms. KMP made 124,721 total character comparisons versus 141 Rabin–Karp verification comparisons. Rabin–Karp still performs a hash check per window and rolling-hash arithmetic, which are not counted as character comparisons.
- At n=100,000 on repetitive DNA, KMP took 34.9687 ms and Rabin–Karp took 220.7418 ms. Every one of the 99,989 windows is a genuine match. Rabin–Karp therefore checks 12 characters per window: 1,199,868 verification comparisons, compared with 100,011 total KMP comparisons.
- Median spurious hits fell from 20,051 at q=5 to 9,102 at q=11, 995 at q=101, 96 at q=1009, and 12 at q=10007. All moduli still returned the same true matches. A larger modulus reduced collision work in these inputs; strict monotonic improvement is not guaranteed for arbitrary inputs.

## Interpretation and limits

KMP's LPS array helps handle repeated structure without restarting the motif comparison. Rabin–Karp is effective at filtering most random windows without character verification, but hash arithmetic has a runtime cost. Many true matches make verification expensive even when there are no spurious hits.

The repetitive experiment demonstrates O(nm) verification work. Because m stays fixed at 12 here, its plotted runtime still looks roughly linear in n; these measurements do not by themselves empirically establish growth in m.

The measured timings have visible variation and are not perfectly proportional to input size, especially among the smaller repetitive inputs. Operating-system scheduling, CPU state, allocation, and other activity can affect wall-clock timing; this run does not identify the cause of any individual fluctuation. Error bars show seed-to-seed ranges, and raw repetitions are retained. The algorithm comparison is paired on identical inputs, but cross-dataset timing differences should not be attributed solely to sequence structure.

Only synthetic strings, three seeds, one fixed motif length, and one machine were used. Repetitive seeds sometimes select the same base, so they do not represent three fundamentally different repetitive workloads. Larger modulus values and hash arithmetic should not be interpreted as evidence of biological significance.

## Validation evidence

- Nine correctness/CLI test methods pass, including exhaustive small binary inputs, 300 random cases, hand-counted metrics, and a crafted collision.
- Every benchmark input agrees with an independent built-in string-search oracle.
- The saved-run audit reconstructs the inputs, checks source/data hashes, recomputes metrics, checks all 525 timing samples against 60 scaling and 15 collision rows, and reconciles chart data with the saved measurements.
- Three graphs are provided in PNG and PDF formats. Their tables and captions are in `tables.md`.

The printable assignment report is the next stage; no final report or student identity details have been fabricated.
