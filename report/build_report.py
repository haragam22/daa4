"""Build the six-page assignment DOCX from the verified Stage 1 measurements."""
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Mm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report"
ASSETS = OUT / "assets"
ASSETS.mkdir(exist_ok=True)
BLUE = "183D59"
TEAL = "237D88"
plt.rcParams.update({"font.family": "Calibri", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False})


def read(name):
    with (ROOT / "results" / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


scaling = read("chart_scaling.csv")
collisions = read("chart_collisions.csv")
env = json.loads((ROOT / "results/environment.json").read_text())


def save(fig, name):
    fig.savefig(ASSETS / f"{name}.png", dpi=260, bbox_inches="tight", pad_inches=.05)
    plt.close(fig)


def box(ax, x, y, w, h, label, fill="#edf3f6"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04",
                              facecolor=fill, edgecolor="#36586c", linewidth=.9))
    ax.text(x+w/2, y+h/2, label, ha="center", va="center", fontsize=10)


def arrow(ax, start, end):
    ax.annotate("", xy=end, xytext=start,
                arrowprops=dict(arrowstyle="->", color="#36586c", lw=1.2))


def diagrams():
    fig, ax = plt.subplots(figsize=(6.8, 1.75))
    ax.set(xlim=(0, 10), ylim=(0, 2.5)); ax.axis("off")
    box(ax, .1, .85, 1.65, .7, "DNA file\n+ motif")
    box(ax, 2.15, .85, 1.9, .7, "Normalize\nand validate")
    box(ax, 4.6, 1.5, 1.75, .65, "KMP / LPS")
    box(ax, 4.6, .25, 1.75, .65, "Rabin–Karp")
    box(ax, 7.1, .85, 2.65, .7, "Verify equal positions\nDisplay / JSON export")
    arrow(ax, (1.78, 1.2), (2.1, 1.2))
    for y in (1.83, .58):
        arrow(ax, (4.1, 1.2), (4.55, y)); arrow(ax, (6.4, y), (7.05, 1.2))
    ax.text(5, -.05, "Benchmark path: deterministic inputs → timed runs → CSV → tables and graphs",
            ha="center", va="bottom", fontsize=9.5)
    save(fig, "workflow")

    fig, ax = plt.subplots(figsize=(6.8, 1.6))
    ax.set(xlim=(-1.2, 7.1), ylim=(-.6, 2.1)); ax.axis("off")
    for i, char in enumerate("ACACA"):
        ax.add_patch(Rectangle((i, .5), .82, .65, facecolor="#edf3f6", edgecolor="#6b8290"))
        ax.text(i+.41, .82, char, ha="center", va="center", fontsize=12)
        ax.text(i+.41, 1.4, str(i), ha="center", fontsize=9.5)
    ax.plot([0, 2.82], [1.8, 1.8], color="#237D88", lw=3)
    ax.text(1.4, 1.93, "prefix ACA", color="#237D88", ha="center")
    ax.plot([2, 4.82], [.15, .15], color="#a85d26", lw=3)
    ax.text(3.4, -.25, "suffix ACA", color="#a85d26", ha="center")
    ax.text(-.3, .82, "P[0:5]", ha="right", va="center")
    ax.text(5.2, .85, "LPS[4] = 3\nReuse ACA after\na mismatch", va="center")
    save(fig, "lps")

    fig, ax = plt.subplots(figsize=(6.8, 1.6))
    ax.set(xlim=(0, 10), ylim=(0, 2.3)); ax.axis("off")
    box(ax, .1, 1.25, 2, .65, "ACG → hash 6")
    box(ax, 7.8, 1.25, 2, .65, "CGT → hash 27")
    arrow(ax, (2.2, 1.58), (7.7, 1.58))
    ax.text(5, 1.86, "remove A  •  shift ×4  •  append T", ha="center")
    ax.text(5, .88, "q = 101:  (4 × (6 − 0 × 16) + 3) mod 101 = 27", ha="center")
    ax.text(5, .28, "Collision check, q = 5:  h(AA) = h(CC) = 0, but AA ≠ CC → reject CC",
            ha="center", bbox=dict(facecolor="#f5eee7", edgecolor="none", pad=5))
    save(fig, "rolling_hash")


def charts():
    colors = {"KMP": "#185c91", "Rabin-Karp": "#b54b13"}
    for metric, ylabel, filename in (("time_ms", "Time (ms)", "runtime"),
                                     ("comparisons", "Character comparisons", "comparisons")):
        fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.25), layout="constrained")
        for ax, kind in zip(axes, ("random", "repetitive")):
            for name in colors:
                rows = [r for r in scaling if r["dataset"] == kind and r["algorithm"] == name]
                xs = [int(r["n"])/1000 for r in rows]
                ys = [float(r[metric]) for r in rows]
                style = dict(color=colors[name], marker="o" if name == "KMP" else "s",
                             linestyle="-" if name == "KMP" else "--", markersize=3, label=name)
                if metric == "time_ms":
                    err = [[float(r[metric])-float(r["min_time_ms"]) for r in rows],
                           [float(r["max_time_ms"])-float(r[metric]) for r in rows]]
                    ax.errorbar(xs, ys, yerr=err, capsize=2, **style)
                else:
                    ax.plot(xs, ys, **style)
                    ax.set_yscale("log")
            ax.set(title="Random DNA" if kind == "random" else "Repetitive DNA",
                   xlabel="n (thousand characters)", ylabel=ylabel)
            ax.grid(alpha=.2); ax.legend(fontsize=9.5, frameon=False)
        save(fig, filename)
    fig, ax = plt.subplots(figsize=(6.8, 2.1), layout="constrained")
    x = [int(r["q"]) for r in collisions]; y = [int(r["spurious_hits"]) for r in collisions]
    ax.errorbar(x, y, yerr=[[int(r["spurious_hits"])-int(r["min_spurious_hits"]) for r in collisions],
                           [int(r["max_spurious_hits"])-int(r["spurious_hits"]) for r in collisions]],
                color="#185c91", marker="o", markersize=4, capsize=3)
    ax.set(xscale="log", yscale="log", xlabel="Modulus q (log scale)", ylabel="Spurious hits (log scale)")
    ax.set_xticks(x, labels=[str(v) for v in x]); ax.grid(alpha=.2, which="both")
    save(fig, "collisions")


doc = Document()
sec = doc.sections[0]
sec.page_width = Mm(210); sec.page_height = Mm(297)
sec.top_margin = Mm(15); sec.bottom_margin = Mm(15)
sec.left_margin = Mm(17); sec.right_margin = Mm(17)
sec.header_distance = Mm(7); sec.footer_distance = Mm(7)
for name in ("Normal", "Title", "Subtitle", "Heading 1", "Heading 2", "Caption"):
    st = doc.styles[name]; st.font.name = "Calibri"; st.font.size = Pt(10)
    st.font.color.rgb = RGBColor.from_string("202B33")
    st.paragraph_format.space_after = Pt(5)
    st.paragraph_format.line_spacing = 1.05
for name in ("Heading 1", "Heading 2"):
    st = doc.styles[name]; st.font.bold = True; st.font.color.rgb = RGBColor.from_string("202B33")
    st.paragraph_format.space_before = Pt(9); st.paragraph_format.space_after = Pt(5)
doc.styles["Caption"].font.size = Pt(9.5)
doc.styles["Caption"].font.italic = False
doc.styles["Caption"].font.color.rgb = RGBColor.from_string("465965")


def p(text="", style=None, bold=False):
    par = doc.add_paragraph(style=style)
    run = par.add_run(text); run.bold = bold
    return par


def heading(text):
    return doc.add_heading(text, level=1)


def picture(name, caption, width=6.8):
    par = doc.add_paragraph(); par.paragraph_format.space_after = Pt(2)
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.add_run().add_picture(str(ASSETS / f"{name}.png"), width=Inches(width))
    par.paragraph_format.keep_with_next = True
    p(caption, "Caption")


def table(headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers)); t.autofit = False
    if widths:
        for col, w in zip(t.columns, widths): col.width = Inches(w)
    for c, text in zip(t.rows[0].cells, headers): c.text = str(text)
    for row in rows:
        for c, text in zip(t.add_row().cells, row): c.text = str(text)
    for ri, row in enumerate(t.rows):
        props = row._tr.get_or_add_trPr(); props.append(OxmlElement("w:cantSplit"))
        if ri == 0: props.append(OxmlElement("w:tblHeader"))
        for ci, cell in enumerate(row.cells):
            if widths:
                cell.width = Inches(widths[ci])
            cp = cell._tc.get_or_add_tcPr()
            shade = OxmlElement("w:shd"); shade.set(qn("w:fill"), "F0F2F3" if ri == 0 else "FFFFFF"); cp.append(shade)
            for par in cell.paragraphs:
                par.paragraph_format.space_after = Pt(3); par.paragraph_format.space_before = Pt(3)
                par.paragraph_format.line_spacing = 1
                for run in par.runs:
                    run.font.name = "Calibri"; run.font.size = Pt(10)
                    if ri == 0: run.bold = True
    return t


def code(text):
    par = p(text)
    par.paragraph_format.line_spacing = 1
    par.paragraph_format.space_after = Pt(5)
    par.paragraph_format.left_indent = Mm(3)
    return par


def page():
    doc.add_page_break()


def build():
    diagrams(); charts()
    sec.header.paragraphs[0].text = ""
    sec.footer.paragraphs[0].text = ""
    for text, bold in [
        ("DNA Motif Finder: Comparing KMP and Rabin–Karp", True),
        ("Har Agam Deep Singh  |  03714802724  |  Section 5C123", False),
        ("Submitted to Dr. Jyoti Kaushik", False),
        ("DAA · Assignment 4 · CIC-311 · 17 November 2026", False),
    ]:
        par = p(text, bold=bold)
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.space_after = Pt(3)
    heading("1. Abstract")
    p("This project implements an exact DNA motif finder using Knuth–Morris–Pratt (KMP) and Rabin–Karp string matching. Both algorithms locate every occurrence of a given motif, including overlaps. A Python command-line application validates inputs and exports match positions. Experiments compare execution time and character comparisons on five DNA lengths using random and repetitive sequences. A separate experiment varies the hash modulus to measure spurious hits. The saved run contains 525 timing samples. KMP is faster in the measured comparisons, while larger moduli reduce Rabin–Karp collisions. Correctness is established through oracle comparisons, edge cases, and deliberate collision tests.")
    heading("2. Problem statement and objectives")
    p("Given a DNA sequence T of length n and a nonempty motif P of length m over {A, C, G, T}, return all indices i for which T[i:i+m] = P. Indices are zero-based. The assignment requires at least two algorithms for the same problem, complexity analysis, measured comparisons on at least five input sizes, and a study of spurious hits versus modulus q [1].")
    p("The objectives are to implement both algorithms transparently, verify identical outputs, separate character comparisons from hash work, measure reproducible timing trends, and explain how input repetition and modulus choice affect performance. The selected pair is KMP and Rabin–Karp.")
    table(["Input DNA", "Motif", "Expected positions"], [["ACGTACGTGACG", "ACG", "0, 4, 9"], ["AAAAA", "AAA", "0, 1, 2 (overlapping)"]], [3.2, 1.1, 2.5])
    heading("3. System workflow and scope")
    picture("workflow", "Figure 1. Application workflow; both algorithms receive the same normalized DNA and motif.")
    p("This is an exact single-pattern search tool, not a biological motif-discovery model. It accepts plain text DNA, normalizes case and whitespace, and rejects ambiguous symbols such as N, FASTA headers, and empty motifs. Empty DNA or m > n produces an empty match list. The console previews up to 20 positions; JSON export retains every match.")

    page()
    heading("4. Knuth–Morris–Pratt (KMP)")
    p("KMP avoids restarting the pattern at each mismatch. It first builds an LPS array, where LPS[i] is the length of the longest proper prefix of P[0:i+1] that is also a suffix. A proper prefix excludes the whole substring. During search, j is the number of currently matched pattern characters; LPS determines how much of that work can be reused.")
    table(["Index i", "0", "1", "2", "3", "4", "5"], [["P[i]", "A", "C", "A", "C", "A", "G"], ["LPS[i]", "0", "0", "1", "2", "3", "0"]], [1.3]+[.9]*6)
    picture("lps", "Figure 2. In ACACA, prefix ACA equals suffix ACA. After a mismatch at j = 5, reuse 3 characters.")
    p("For P = ACACAG, a mismatch after ACACA falls back from j = 5 to LPS[4] = 3. The text position does not move backward. The next comparison uses P[3]. Further mismatches may cause additional LPS fallbacks. After a full match, j becomes LPS[m−1], preserving overlapping occurrences.")
    heading("4.1 Pseudocode")
    code("BUILD_LPS(P):\n"
         "    LPS ← array of m zeros; length ← 0; i ← 1\n"
         "    while i < m:\n"
         "        if P[i] = P[length]:\n"
         "            length ← length + 1; LPS[i] ← length; i ← i + 1\n"
         "        else if length > 0: length ← LPS[length − 1]\n"
         "        else: i ← i + 1\n"
         "    return LPS\n\n"
         "KMP(T, P):\n"
         "    reject empty P; if m > n: return []\n"
         "    LPS ← BUILD_LPS(P); i ← 0; j ← 0; matches ← []\n"
         "    while i < n:\n"
         "        if T[i] = P[j]:\n"
         "            i ← i + 1; j ← j + 1\n"
         "            if j = m:\n"
         "                append i − m to matches; j ← LPS[j − 1]\n"
         "        else if j > 0: j ← LPS[j − 1]\n"
         "        else: i ← i + 1\n"
         "    return matches")
    heading("4.2 Correctness and complexity")
    p("Before each search comparison, the first j motif characters equal the text suffix ending immediately before i. A successful comparison extends this invariant. On failure, an LPS fallback retains a prefix already known to match that suffix. Shorter candidate borders remain available, so no valid occurrence is skipped. When j = m, the reported index i−m is therefore a complete match.")
    p("LPS construction takes O(m) time. During search, i only advances, and decreases of j are bounded by its preceding increases; total search work is O(n). Overall time is O(n+m), with O(m) auxiliary space for LPS. Storing k returned positions adds O(k) output space. Preprocessing and search character comparisons are recorded separately.")

    page()
    heading("5. Rabin–Karp rolling-hash matching")
    p("Rabin–Karp compares numeric hashes before checking characters. Encode A=0, C=1, G=2, T=3, use base b=4, and reduce modulo q > 1. A window hash is h(S) = (Σ code(S[j]) × 4^(m−1−j)) mod q. Equal hashes are candidates, not proof of equal strings. Every candidate is verified character by character, stopping at the first mismatch.")
    code("high = 4^(m−1) mod q\nnext_hash = (4 × (window_hash − code(T[i]) × high) + code(T[i+m])) mod q")
    picture("rolling_hash", "Figure 3. Rolling from ACG to CGT and a separate deliberate collision example. Hash equality requires verification.")
    heading("5.1 Pseudocode")
    code("RABIN_KARP(T, P, q):\n"
         "    reject empty P or invalid q; if m > n: return []\n"
         "    high ← 4^(m−1) mod q; pHash ← 0; tHash ← 0\n"
         "    for j ← 0 to m−1:\n"
         "        pHash ← (4 × pHash + code(P[j])) mod q\n"
         "        tHash ← (4 × tHash + code(T[j])) mod q\n"
         "    matches ← []\n"
         "    for i ← 0 to n−m:\n"
         "        count one hash check\n"
         "        if pHash = tHash:\n"
         "            count one hash hit; matched ← true\n"
         "            for j ← 0 to m−1:\n"
         "                count one verification character comparison\n"
         "                if T[i+j] ≠ P[j]: matched ← false; break\n"
         "            if matched: append i to matches\n"
         "            else: count one spurious hit\n"
         "        if i < n−m: update tHash with the rolling formula\n"
         "    return matches")
    heading("5.2 Correctness, spurious hits, and complexity")
    p("The initial hash represents the first window. Subtracting the outgoing weighted character, multiplying by 4, and appending the incoming code preserves that representation for each successive window. Every actual match has the motif hash and passes verification. A collision is rejected, so changing q affects candidate work but cannot introduce a false reported match.")
    p("A spurious hit is a hash-equal window whose characters differ from the motif. Thus hash hits = true matches + spurious hits. If H windows have equal hashes, preprocessing plus search costs O(n+m+Hm) as an upper bound. With few verifications this is typically O(n+m); the worst case is O(nm). Even genuine matches can cause worst-case verification work.")
    table(["Property", "KMP", "Rabin–Karp"], [
        ["Preprocessing", "O(m)", "O(m)"], ["Worst-case total time", "O(n+m)", "O(nm)"],
        ["Auxiliary space", "O(m)", "O(1)"], ["Extra output space", "O(k)", "O(k)"]], [2.8, 2, 2])
    p("Table 1. Complexity assumes fixed-size modulus arithmetic and excludes input storage. Both methods include overlapping matches.", "Caption")

    page()
    heading("6. Implementation and experimental method")
    p(f"The implementation uses Python {env['python']} ({env['implementation']}) on Windows 11, with Matplotlib {env['dependencies']['matplotlib']} for graphs. The recorded processor is Intel64 Family 6 Model 170 Stepping 4, with {env['logical_cpus']} logical CPUs. Source and dataset SHA-256 hashes are saved with the results so the measured implementation can be identified.")
    table(["Component", "Responsibility"], [
        ["src/algorithms.py", "LPS, KMP, Rabin–Karp, normalization, optional metrics"],
        ["src/main.py", "File input, algorithm selection, validation, JSON export"],
        ["src/benchmark.py", "Deterministic datasets, timing batches, CSV and metadata"],
        ["src/plot_results.py; src/verify_results.py", "Measured graphs/tables and independent result audit"]], [3.1, 3.7])
    p("Five lengths are tested: 1,000, 5,000, 10,000, 50,000, and 100,000 characters. Motif length is fixed at m=12, with seeds 42, 43, and 44. Random DNA is generated uniformly and a motif is planted halfway through; incidental matches are also counted. Repetitive DNA consists of one repeated base and has n−m+1 overlapping matches. Both algorithms receive identical inputs; the scaling experiment uses q=1009.")
    p("Each input uses two warmups, one calibration, and seven timed repetitions. Batches target 5 ms and are capped at 100 searches; elapsed batch time is divided by the batch count. Algorithm order reverses on alternate repetitions. time.perf_counter_ns() measures durations [2]. Timings include preprocessing, search, and output-list construction, but exclude validation, generation, I/O, and metric increments. Character counts are collected in a separate instrumented pass.")
    p("Each CSV timing summary is a median of seven repetitions. Tables and graphs below use the median of the three seed medians; runtime error bars show their minimum and maximum, not confidence intervals. There are 60 scaling rows and 15 collision rows, giving 525 saved repetition timings in total.")
    heading("7. Runtime results")
    rows = []
    for n in (1000, 5000, 10000, 50000, 100000):
        vals = []
        for kind in ("random", "repetitive"):
            for algorithm in ("KMP", "Rabin-Karp"):
                r = next(r for r in scaling if int(r["n"]) == n and r["dataset"] == kind and r["algorithm"] == algorithm)
                vals.append(f"{float(r['time_ms']):.4f}")
        rows.append([f"{n:,}"]+vals)
    table(["n", "Random KMP", "Random RK", "Repeat KMP", "Repeat RK"], rows, [1.0, 1.45, 1.45, 1.45, 1.45])
    p("Table 2. Median search times in milliseconds; m=12 and Rabin–Karp q=1009.", "Caption")
    picture("runtime", "Figure 4. Runtime versus DNA length. Error bars show the range of seed medians; axes differ between datasets.")
    p("KMP is faster in all ten dataset/size comparisons in this run. At n=100,000 on random DNA, the medians are 8.5972 ms for KMP and 19.6482 ms for Rabin–Karp. Repetitive inputs require many candidate verifications and output positions. These observations describe this Python implementation and machine, not a universal algorithm ranking.")

    page()
    heading("8. Character comparisons and modulus experiment")
    p("KMP comparisons include LPS construction and text/pattern checks. Rabin–Karp character comparisons count only candidate verification; hash equality checks and rolling arithmetic are separate work. A smaller character count therefore does not necessarily imply a shorter runtime.")
    picture("comparisons", "Figure 5. Median character comparisons across seeds. Logarithmic vertical axes keep the small Rabin–Karp random-input counts visible.")
    table(["At n=100,000", "KMP comparisons", "RK comparisons", "True matches"], [
        ["Random DNA", "124,721", "141", "1 (median)"],
        ["Repetitive DNA", "100,011", "1,199,868", "99,989"]], [1.9, 1.65, 1.65, 1.6])
    p("Table 3. Total character comparisons and match counts. In repetitive DNA, Rabin–Karp verifies all 12 characters in each of 99,989 windows.", "Caption")
    p("For the modulus experiment, n=100,000 and m=12 remain fixed. Each seed uses the same random DNA/motif pair for all five q values; base and encoding also remain fixed. The results isolate the effect of the modulus on hash collisions. Every modulus produces the same true match positions.")
    picture("collisions", "Figure 6. Median spurious hits versus q; both axes are logarithmic. Bars show minimum/maximum counts across seeds.")
    table(["Modulus q", "Median spurious hits", "Minimum", "Maximum"], [
        [r["q"], f"{int(r['spurious_hits']):,}", f"{int(r['min_spurious_hits']):,}", f"{int(r['max_spurious_hits']):,}"] for r in collisions], [1.2, 2.4, 1.6, 1.6])
    p("Table 4. Collision counts over 99,989 windows per seed. The median true-match count is one for every q.", "Caption")
    p("Median spurious hits decrease from 20,051 at q=5 to 12 at q=10007. This agrees with the expectation that a larger hash range often reduces random collisions. It is not a guarantee of strict monotonic improvement for arbitrary strings. Character verification is essential at every modulus, as the AA/CC example demonstrates.")

    page()
    heading("9. Correctness and validation")
    p("Nine automated test methods pass. They compare both algorithms with a separate brute-force oracle on all strings over {A,C} through length five and motifs of lengths one to three, plus 300 seeded random pairs. The tests check overlapping and boundary matches, no matches, a single-character motif, equal text/motif, empty DNA, and a motif longer than its text.")
    p("Additional checks validate LPS values and hand-counted comparisons, reject empty motifs and invalid symbols, and confirm that the deliberate modulo-5 AA/CC collision is not reported as a match. CLI tests cover selection of either algorithm, invalid q, missing files, normalized input, and full JSON exports beyond the 20-position console preview.")
    p("Every benchmark input also agrees with an independent repeated built-in string-search reference. The saved-result audit reconstructs datasets, recomputes metrics, checks hash-hit identities, reconciles timing medians with all 525 raw samples, and verifies that plotted aggregates match the CSV data. SHA-256 checks connect the saved run to its source files and generated inputs.")
    heading("10. Discussion and limitations")
    p("The random-input results illustrate a distinction between counting character comparisons and measuring total work: Rabin–Karp makes far fewer character checks, but performs modular arithmetic and dictionary lookups at each window. KMP avoids that hash work and is faster here. On repetitive DNA, KMP reuses matched structure; Rabin–Karp verifies every true match, causing 12 checks per window.")
    p("With fixed m=12, even O(nm) work can appear approximately linear as n increases. This experiment does not establish empirical scaling in m. Some timings are not proportional to input size, particularly for smaller repetitive inputs. Scheduling, CPU state, allocation, or background activity may contribute; the experiment does not isolate their causes. Reversing algorithm order and retaining raw repetitions helps make the comparison inspectable, but does not remove all timing noise.")
    p("The evidence is limited to synthetic strings, three seeds, one motif length, and one machine. Repetitive seeds can choose the same base, so they do not represent three independent workload types. The tool supports exact A/C/G/T matching only; it does not handle ambiguous bases, substitutions, insertions, deletions, or biological significance.")
    heading("11. Conclusion and future work")
    p("Both algorithms correctly find all exact motif positions, including overlaps. KMP provides O(n+m) worst-case time and stable reuse of repeated structure. Rabin–Karp demonstrates rolling hashes and the importance of collision verification; larger moduli reduce spurious hits in the measured inputs. KMP is faster in this saved run, while the collision experiment explains how q changes Rabin–Karp verification work. Future work can vary motif length, add finite-automaton matching, and support validated FASTA input or approximate matching as separate extensions.")
    heading("12. Reproduction and submission contents")
    code("python -m src.main data/example.txt ACG\n"
         "python -m tests.run_checks\n"
         "python -m src.benchmark\n"
         "python -m src.plot_results\n"
         "python -m src.verify_results")
    p("Run commands from the project root after installing requirements.txt. Submit this report together with src/, tests/, data/, requirements.txt, and README.md. Supporting measurements are in results/; original graphs are in figures/. The sample command returns positions [0, 4, 9]. Benchmark timings will vary on rerun; the generated sequences and correctness outcomes are deterministic.")
    heading("References and evidence sources")
    p("[1] MAIT, Department of Computer Science & Engineering. DAA_Assignment_4_Project.pdf, Assignment 4: Algorithm Project, CIC-311, session 2026–27. Supplied assignment brief.")
    p("[2] Python Software Foundation. time — Time access and conversions, perf_counter_ns documentation. https://docs.python.org/3/library/time.html#time.perf_counter_ns (accessed 17 November 2026).")
    p("[3] Project evidence: src/algorithms.py; tests/test_algorithms.py; results/raw_timings.csv, summary.csv, collisions.csv, datasets.json, and environment.json. All reported measurements are from the saved project run.")
    doc.core_properties.title = "DNA Motif Finder: Comparing KMP and Rabin–Karp"
    doc.core_properties.author = "Har Agam Deep Singh"
    doc.core_properties.subject = "DAA Assignment 4 • CIC-311 • Enrollment 03714802724"
    # Explicitly enforce requested typeface for every textual run, including table text.
    for element in doc.element.iter(qn("w:r")):
        rp = element.find(qn("w:rPr"))
        if rp is None: rp = OxmlElement("w:rPr"); element.insert(0, rp)
        fonts = rp.find(qn("w:rFonts"))
        if fonts is None: fonts = OxmlElement("w:rFonts"); rp.append(fonts)
        for attr in ("ascii", "hAnsi", "eastAsia", "cs"): fonts.set(qn("w:"+attr), "Calibri")
    target = OUT / "DNA_Motif_Finder_Report.docx"
    doc.save(target)
    print(f"Built {target}")


if __name__ == "__main__":
    build()
