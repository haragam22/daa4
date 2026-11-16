# Measured results for the future report

Generated from summary.csv and collisions.csv. Runtime values are the median of the three seed medians; each seed median uses seven timed repetitions. Error bars show the minimum and maximum seed medians, not confidence intervals. Comparison and collision points are medians across the three seeds.

## Runtime and character comparisons

| Dataset | n | Algorithm | Time (ms) | Character comparisons |
|---|---:|---|---:|---:|
| random | 1,000 | KMP | 0.1124 | 1,259 |
| random | 1,000 | Rabin-Karp | 0.2348 | 16 |
| random | 5,000 | KMP | 0.4146 | 6,190 |
| random | 5,000 | Rabin-Karp | 0.9577 | 23 |
| random | 10,000 | KMP | 0.8578 | 12,425 |
| random | 10,000 | Rabin-Karp | 1.9464 | 25 |
| random | 50,000 | KMP | 4.3789 | 62,286 |
| random | 50,000 | Rabin-Karp | 9.6436 | 78 |
| random | 100,000 | KMP | 8.5972 | 124,721 |
| random | 100,000 | Rabin-Karp | 19.6482 | 141 |
| repetitive | 1,000 | KMP | 0.1109 | 1,011 |
| repetitive | 1,000 | Rabin-Karp | 0.7877 | 11,868 |
| repetitive | 5,000 | KMP | 1.4758 | 5,011 |
| repetitive | 5,000 | Rabin-Karp | 9.7560 | 59,868 |
| repetitive | 10,000 | KMP | 2.4468 | 10,011 |
| repetitive | 10,000 | Rabin-Karp | 19.9939 | 119,868 |
| repetitive | 50,000 | KMP | 15.5791 | 50,011 |
| repetitive | 50,000 | Rabin-Karp | 111.5805 | 599,868 |
| repetitive | 100,000 | KMP | 34.9687 | 100,011 |
| repetitive | 100,000 | Rabin-Karp | 220.7418 | 1,199,868 |

## Spurious hits versus modulus

| q | Median spurious hits | Minimum | Maximum | Median true matches |
|---:|---:|---:|---:|---:|
| 5 | 20,051 | 19,785 | 20,151 | 1 |
| 11 | 9,102 | 9,067 | 9,216 | 1 |
| 101 | 995 | 965 | 1,009 | 1 |
| 1009 | 96 | 94 | 99 | 1 |
| 10007 | 12 | 11 | 12 | 1 |

## Figure captions and interpretation constraints

1. runtime.png: preprocessing plus search, without counters; excludes validation and I/O. Includes output-list construction. Bars show variation across seeds.
2. comparisons.png: KMP LPS plus search character comparisons versus Rabin–Karp candidate-verification character comparisons. Hash checks and arithmetic are separate work, so character counts alone do not predict speed.
3. collisions.png: fixed random DNA/motif pairs while changing q; base 4, encoding A=0/C=1/G=2/T=3. Both axes are logarithmic; bars show minimum/maximum spurious counts across seeds.

Repetitive inputs have n-m+1 true matches. Rabin–Karp verifies all m characters at every window, illustrating its O(nm) verification cost. Here m stays fixed, so runtime can still grow approximately linearly with n.

Synthetic DNA and three seeds do not establish performance on biological genomes. Timings are specific to this Python implementation and machine. The repetitive dataset may repeat across seeds because its alphabet choice has only four possibilities; seeds are not independent workload diversity there.
