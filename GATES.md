# Gates: DNA motif finder Stage 1

Scope: Implement, test, benchmark, and document the CLI project; printable assignment report is Stage 2.

- [x] G1: Algorithms and CLI satisfy oracle, overlap, collision, validation, and export checks
  CHECK: python -m tests.run_checks
  EXPECT: ALGORITHMS AND CLI VERIFIED
  EVIDENCE: automatic-evidence=v1; definition-sha256=ce7a000e6ef205bb1b6818e61c7b376b27535b0129bfdb00812a42d929fcda8e; exit=0; EXPECT=matched; output-sha256=ffefd15a2c9236cec5e91f2b28b9029cc77c8f0a471c5fe00071ae19d12d86e4; output-bytes=1054; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\harag\Documents\coding\daa\ass4; path=867dca977851/41 entries

- [x] G2: Saved experiments cover the plan and agree with raw timing and recomputed metrics
  CHECK: python -m src.verify_results
  EXPECT: EXPERIMENTS VERIFIED
  EVIDENCE: automatic-evidence=v1; definition-sha256=c806779b228b0d8f91c77db1c181247dd28e4fc53baf276115b3e54e3e375534; exit=0; EXPECT=matched; output-sha256=67d446179748346ba61bc861b2340439afbac93db38aeac6b2270880dd30a190; output-bytes=96; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\harag\Documents\coding\daa\ass4; path=867dca977851/41 entries

- [x] G3: Figures are readable and documentation explains reproduction and measured findings
  EVIDENCE: Inspected all three PNG figures: legible axes, legends, and titles, with no clipping. Reviewed README reproduction commands, algorithm pseudocode, metric definitions, and results/findings.md against saved tables. Report remains explicitly Stage 2.


