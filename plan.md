# DNA Motif Finder — Project and Report Plan

## 1. Project decisions

- Selected assignment: Project 2, DNA motif finder.
- Working title: DNA Motif Finder: Comparing KMP and Rabin–Karp.
- Primary algorithms: Knuth–Morris–Pratt (KMP) and Rabin–Karp.
- Language: Python 3; command-line interface for a small, explainable implementation.
- Core deliverables: original source code, reproducible measurements, graphs, and a printable 4–6 page report.
- Work sequence: Stage 1 builds and benchmarks the project; Stage 2 creates the printable report using verified Stage 1 results.
- This file is the blueprint. Implementation and report production are subsequent tasks.
- Assignment interpretation: the general task requires at least two algorithms, while the DNA row lists finite automaton, KMP, and Rabin–Karp. The planned core uses two. If all listed algorithms are required, add finite automaton matching and update the report before submission.

## 2. Assignment requirements

Source: DAA_Assignment_4_Project.pdf.

- Find exact motifs in a genome string over {A, C, G, T}.
- Implement at least two algorithms for the same problem.
- Analyse complexity and compare measured results on at least five input sizes.
- Study Rabin–Karp spurious hits as modulus q changes.
- Submit source code and a 4–6 page report containing the problem statement, algorithm pseudocode, complexity analysis, results with graphs, and conclusion.
- Assignment metadata: Maharaja Agrasen Institute of Technology, Delhi; Department of Computer Science & Engineering; Design and Analysis of Algorithms; CIC-311 (GGSIPU); section 5C123; session 2026–27; faculty Dr. Jyoti Kaushik; individual project, Unit IV; 20 marks.
- PDF submission date: 17 November 2026. Confirm any revised deadline separately.

## 3. Idea and problem definition

A DNA motif is a short sequence sought within a longer DNA sequence. Given text T of length n and motif P of length m, return every zero-based position i such that T[i:i+m] equals P. Include overlapping matches.

Example: T = ACGTACGTGACG, P = ACG; expected positions = [0, 4, 9].

The same inputs will be searched with KMP and Rabin–Karp. Both must return identical positions; their preprocessing, character comparisons, runtime, and hashing behaviour will be compared.

Scope: exact single-pattern matching on A/C/G/T sequences. This educational tool does not infer biological significance, perform approximate matching, or support ambiguous nucleotide codes.

Report placeholders:
- [FINAL_PROJECT_TITLE]
- [ABSTRACT_80_TO_120_WORDS]
- [PROBLEM_STATEMENT]
- [PROJECT_OBJECTIVES]
- [EXAMPLE_INPUT_AND_EXPECTED_OUTPUT]
- [SCOPE_AND_LIMITATIONS]

## 4. Technical implementation

### Input and interface

- Accept a DNA sequence from a plain text file and a motif from a CLI argument.
- Normalize letter case and remove sequence whitespace before validation.
- Reject symbols outside A/C/G/T with a clear message; FASTA headers are not supported in the initial version.
- Reject an empty motif. An empty DNA sequence or a motif longer than the DNA returns no matches.
- Support choosing KMP, Rabin–Karp, or both, with both as the default.
- For Rabin–Karp, expose modulus q and validate q > 1; use the documented fixed base 4 and encoding A=0, C=1, G=2, T=3.
- Display sequence length, motif length, match count, and zero-based positions. Truncate long position lists in the console while retaining full results in exported output.

### KMP

1. Construct the longest proper prefix that is also a suffix (LPS) array for the motif.
2. Scan the DNA while using LPS values to resume after a mismatch.
3. After a complete match, record its position and use LPS to preserve overlapping matches.
4. Track preprocessing and search character comparisons separately in the instrumented version.

Complexity: O(n + m) time and O(m) auxiliary space, excluding stored output positions.

### Rabin–Karp

1. Compute the motif hash and the first length-m window hash modulo q.
2. Slide the window with a rolling hash; avoid constructing each substring.
3. When hashes match, compare characters directly to confirm an exact match.
4. Count hash hits, verified matches, and spurious hits separately.
5. A spurious hit is an equal-hash candidate whose characters do not match the motif. Verification prevents false matches in the final output.

Complexity: typically O(n + m) with few candidates, but O(nm) in the worst case due to repeated verification. Auxiliary space is O(1), excluding input and output storage. More precisely, verification cost depends on the number of hash hits and the number of characters checked per hit.

### Measurement definitions

- n: number of DNA characters after normalization.
- m: number of motif characters.
- Runtime: algorithm preprocessing plus search; exclude input generation, validation, file I/O, printing, and graph creation.
- KMP comparisons: actual character equality checks during LPS construction and search, reported separately and in total.
- Rabin–Karp comparisons: actual character checks during candidate verification. Hash comparisons are a separate metric.
- Hash hits = verified matches + spurious hits.
- Rolling-hash updates are counted separately; lower character-comparison counts alone do not imply lower runtime.
- Auxiliary space excludes input and returned match positions; storing k matches adds O(k) space to both algorithms.
- Use a shared core with optional instrumentation; disable counters for timing and enable them in a separate pass for metrics.

### Planned source layout

- src/algorithms.py — KMP, LPS construction, Rabin–Karp, and optional metrics.
- src/main.py — CLI, normalization, validation, and result presentation.
- src/benchmark.py — deterministic datasets, repeated timings, CSV exports.
- src/plot_results.py — charts generated from measured CSV data.
- tests/test_algorithms.py — correctness, edge cases, collision checks.
- data/ — small example DNA inputs.
- results/ — raw timings, aggregate results, collision results, and environment metadata.
- figures/ — generated charts for the report.
- report/ — editable report source and final printable PDF.
- README.md — setup, example commands, experiment reproduction, and interpretation.
- requirements.txt — only necessary dependencies; standard library for algorithms and tests, matplotlib for plots.

Report placeholders:
- [LANGUAGE_AND_VERSION]
- [DEPENDENCIES_AND_VERSIONS]
- [INPUT_FORMAT_AND_VALIDATION]
- [SYSTEM_WORKFLOW]
- [KMP_EXPLANATION_AND_PSEUDOCODE]
- [LPS_WORKED_EXAMPLE]
- [RABIN_KARP_EXPLANATION_AND_PSEUDOCODE]
- [ROLLING_HASH_FORMULA_AND_WORKED_EXAMPLE]
- [METRIC_DEFINITIONS]
- [COMPLEXITY_TABLE_AND_JUSTIFICATION]
- [CLI_EXAMPLE_AND_ACTUAL_OUTPUT]

## 5. Experiment plan

### A. Scaling across input sizes

- Planned DNA sizes n: 1,000; 5,000; 10,000; 50,000; 100,000.
- Fix motif length m = 12 for the primary scaling experiment.
- Use three deterministic dataset seeds, starting with 42, 43, and 44.
- Use identical DNA/motif pairs for both algorithms.
- Include uniform random DNA with a planted motif and repetitive DNA with frequent overlapping matches. Track actual matches rather than assuming planted matches are the only ones.
- Use q = 1009 for the main Rabin–Karp comparison.
- Perform two untimed warmups and seven timed repetitions per algorithm/input pair using time.perf_counter_ns().
- Alternate algorithm order between repetitions to reduce ordering effects.
- Preserve raw timings; calculate the median per input pair, then summarize across seeds with the aggregation method clearly stated.
- If individual runs are too short for stable measurements, use documented repeated-call batches and divide elapsed time by the batch count. Record the batch count.

### B. Spurious hits versus modulus q

- Planned q values: 5, 11, 101, 1009, 10007.
- Hold DNA, motif, base, and encoding fixed while changing q.
- Use n = 100,000 and m = 12 for each of the three seeds on uniform random DNA.
- Record windows examined, hash hits, true matches, spurious hits, and runtime.
- Include a crafted collision example in validation to demonstrate why verification is necessary.
- Expect larger moduli to generally reduce random collisions, but do not claim a strictly decreasing trend for every fixed dataset.

### C. Correctness and edge cases

- Check the stated example, no matches, one match, repeated matches, overlapping matches, and matches at both boundaries.
- Check empty DNA, empty motif rejection, motif longer than DNA, single-character motif, and motif equal to DNA.
- Check normalization and invalid-symbol rejection.
- Compare both algorithms against a simple independent brute-force oracle on deterministic small random inputs.
- Verify results stay identical across all selected moduli, including collision-heavy cases.
- Check hash_hits = matches + spurious_hits and n-m+1 windows when n >= m.

### Result files and graphs

- raw_timings.csv: dataset, seed, n, m, algorithm, q, repetition, batch_count, elapsed_ns_per_search.
- summary.csv: dataset, seed, n, m, algorithm, q, median_time_ns, match_count, preprocessing_comparisons, search_comparisons, hash_checks, rolling_updates, hash_hits, spurious_hits.
- collisions.csv: seed, n, m, q, windows, true_matches, hash_hits, spurious_hits, median_time_ns.
- environment.json: OS, CPU, Python version, dependencies, seeds, timing settings, and benchmark date.
- Figure 1: median runtime versus n for both algorithms, separated by dataset type.
- Figure 2: character comparisons versus n, with precise counting definitions in the caption.
- Figure 3: spurious hits versus q, with logarithmic q-axis if helpful.
- Tables: complexity, compact runtime results across all five sizes, and collision counts.
- All report numbers and graphs must come from generated results. Do not insert invented timings or predicted winners.

Report placeholders:
- [HARDWARE_OS_AND_PYTHON_ENVIRONMENT]
- [DATASET_GENERATION_AND_SEEDS]
- [INPUT_SIZES_AND_MOTIF_LENGTH]
- [WARMUPS_REPETITIONS_AND_AGGREGATION]
- [MODULUS_VALUES_AND_FIXED_CONTROLS]
- [CORRECTNESS_CHECK_RESULTS]
- [MEASURED_RUNTIME_TABLE]
- [MEASURED_COMPARISON_TABLE]
- [MEASURED_COLLISION_TABLE]
- [FIGURE_1_RUNTIME_WITH_CAPTION]
- [FIGURE_2_COMPARISONS_WITH_CAPTION]
- [FIGURE_3_COLLISIONS_WITH_CAPTION]
- [RESULT_INTERPRETATION_SUPPORTED_BY_DATA]
- [EXPERIMENT_LIMITATIONS]

## 6. Stage 1 — Build and measure the project

1. Implement input handling, algorithms, and consistent result/metric structures.
2. Validate correctness against the oracle and targeted edge cases.
3. Add the CLI and small demonstration inputs.
4. Implement deterministic dataset generation and the benchmark runner.
5. Run both algorithms on the five sizes and all required dataset types.
6. Run the q experiment and verify collision-count invariants.
7. Generate CSV files, environment metadata, and graphs from actual measurements.
8. Review unexpected results before writing conclusions.
9. Write README setup and reproduction commands; run them to confirm they work.

Stage 1 completion checklist:
- [x] Both algorithms return all correct positions, including overlaps.
- [x] Input validation and edge-case checks pass.
- [x] Benchmark results cover at least five sizes for both algorithms.
- [x] Modulus experiment records genuine spurious hits and verified matches.
- [x] Raw measurements and environment details are preserved.
- [x] Charts reproduce the saved tables and label units correctly.
- [x] README commands work in the chosen environment.

## 7. Stage 2 — Printable assignment report

Prepare an editable report source and export a final A4 PDF. Target six pages including the title information; avoid a separate cover that consumes the page budget. Use readable 11–12 point body text, consistent margins, numbered figures/tables, page numbers, and print-friendly graph labels. Inspect the final PDF for clipping, unreadable text, blank pages, and the total page count.

### Proposed six-page structure

1. Title/student/course details, short abstract, problem statement, objectives, scope, and example.
2. KMP explanation, LPS example, pseudocode, and complexity.
3. Rabin–Karp explanation, rolling hash, pseudocode, spurious hits, and complexity comparison.
4. Implementation overview, correctness checks, experimental setup, runtime table, and runtime graph.
5. Character-comparison and collision results, graphs, and interpretation.
6. Discussion, limitations, conclusion, future work, and references.

Adjust layout to fit readable content within 4–6 pages; keep full code in the separate source submission.

### Report identity placeholders

- Har Agam Deep Singh
- 03714802724
- [SECTION_CONFIRM_OR_REPLACE_5C123]
- [FINAL_SUBMISSION_DATE]
- [FINAL_PROJECT_TITLE]
- [FACULTY_NAME_CONFIRM_DR_JYOTI_KAUSHIK]
- [COLLEGE_DEPARTMENT_COURSE_AND_PAPER_CODE]

### Final report placeholders

- [DISCUSSION_OF_OBSERVED_ALGORITHM_TRADEOFFS]
- [CONCLUSION_BASED_ON_ACTUAL_MEASUREMENTS]
- [FUTURE_WORK_OPTIONAL_FINITE_AUTOMATON_OR_APPROXIMATE_MATCHING]
- [REFERENCES_ACTUALLY_CONSULTED]
- [SOURCE_CODE_SUBMISSION_LOCATION]
- report/DNA_Motif_Finder_Report.docx
- report/DNA_Motif_Finder_Report.pdf
- 6 pages, rendered by Microsoft Word

Stage 2 completion checklist:
- [x] Identity details are filled accurately; no invented personal details.
- [x] All report placeholders are replaced with verified content.
- [x] Both algorithms have clear pseudocode and justified complexity.
- [x] Results cover five sizes and the q experiment.
- [x] Tables, captions, graphs, and conclusions agree with saved measurements.
- [x] References credit sources actually consulted.
- [x] PDF is readable on A4 and contains 4–6 pages.
- [x] Final submission includes source code and the printable report.

## 8. Details needed before final report production

- Student name and enrollment number.
- Confirmation of section and any updated submission date.
- Any teacher-specific formatting requirements or requirement to implement all three listed algorithms.
- Preferred editable report format, if any; otherwise choose a format that exports reliably to PDF.

These details do not block the core implementation. Keep the corresponding placeholders until confirmed.

## 9. Stage 1 delivery status

Completed: Python CLI, KMP and Rabin-Karp, nine passing test methods, five-size scaling experiments, five-modulus collision experiments, 525 saved timing samples, measured tables, and three graphs in PNG/PDF formats. See README.md for commands, results/tables.md for data, results/findings.md for interpretation, and GATES.md for verification. The printable report remains Stage 2 as requested.


## 10. Stage 2 delivery status

Completed: report/DNA_Motif_Finder_Report.docx and the matching PDF. Six A4 pages, Calibri 10 with 9.5-point captions, six embedded visuals, seven tables, measured results, pseudocode, correctness/complexity analysis, limitations, and references. Student: Har Agam Deep Singh, enrollment 03714802724. Simplified title block and empty headers/footers follow the final user preference. All report fields are filled; earlier placeholder lists remain as planning history. Verification: report/verify_report.py and report/GATES.md.
