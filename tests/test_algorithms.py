import itertools
import json
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from src.algorithms import Metrics, build_lps, kmp, normalize_dna, rabin_karp

ROOT = Path(__file__).resolve().parents[1]


def oracle(text, pattern):
    return [i for i in range(len(text) - len(pattern) + 1)
            if text[i:i + len(pattern)] == pattern]


class AlgorithmTests(unittest.TestCase):
    def check_pair(self, text, pattern):
        expected = oracle(text, pattern)
        metrics = Metrics()
        self.assertEqual(kmp(text, pattern, metrics), expected)
        self.assertEqual(kmp(text, pattern), expected)
        for q in (2, 5, 11, 101, 1009, 10007):
            metrics = Metrics()
            self.assertEqual(rabin_karp(text, pattern, q, metrics), expected)
            self.assertEqual(rabin_karp(text, pattern, q), expected)
            windows = max(0, len(text) - len(pattern) + 1)
            self.assertEqual(metrics.hash_checks, windows)
            self.assertEqual(metrics.rolling_updates, max(0, windows - 1))
            self.assertEqual(metrics.hash_hits, len(expected) + metrics.spurious_hits)

    def test_examples_and_boundaries(self):
        for text, pattern in [("ACGTACGTGACG", "ACG"), ("AAAAA", "AAA"),
                              ("", "A"), ("AC", "ACG"), ("T", "T"),
                              ("ACGT", "ACGT"), ("AAAA", "C"),
                              ("TACGT", "T"), ("ACGTTACG", "ACG")]:
            with self.subTest(text=text, pattern=pattern):
                self.check_pair(text, pattern)

    def test_exhaustive_small_binary_alphabet(self):
        for n in range(6):
            for letters in itertools.product("AC", repeat=n):
                for m in range(1, 4):
                    for motif in itertools.product("AC", repeat=m):
                        self.check_pair("".join(letters), "".join(motif))

    def test_seeded_random_oracle(self):
        rng = random.Random(2026)
        for _ in range(300):
            text = "".join(rng.choices("ACGT", k=rng.randrange(100)))
            motif = "".join(rng.choices("ACGT", k=rng.randrange(1, 20)))
            self.check_pair(text, motif)

    def test_lps_and_comparison_counts(self):
        self.assertEqual(build_lps("ACACAG"), [0, 0, 1, 2, 3, 0])
        metrics = Metrics()
        self.assertEqual(kmp("AAAA", "AA", metrics), [0, 1, 2])
        self.assertEqual(metrics.preprocessing_comparisons, 1)
        self.assertEqual(metrics.search_comparisons, 4)
        metrics = Metrics()
        rabin_karp("AAAA", "AA", 5, metrics)
        self.assertEqual(metrics.search_comparisons, 6)

    def test_crafted_collision_is_rejected(self):
        # AA = 0; CC = 5, so both hash to zero modulo 5.
        metrics = Metrics()
        self.assertEqual(rabin_karp("CC", "AA", 5, metrics), [])
        self.assertEqual(metrics.hash_hits, 1)
        self.assertEqual(metrics.spurious_hits, 1)
        self.assertEqual(metrics.search_comparisons, 1)
        self.assertEqual(rabin_karp("AA", "AA", 5), [0])

    def test_normalization_and_rejection(self):
        self.assertEqual(normalize_dna(" aC\ng\tt "), "ACGT")
        self.assertEqual(normalize_dna("ac g", motif=True), "ACG")
        for invalid in ("ACGN", ">header\nACGT", "123", "ACU"):
            with self.assertRaises(ValueError):
                normalize_dna(invalid)
        with self.assertRaises(ValueError):
            normalize_dna(" \n", motif=True)
        for search in (kmp, rabin_karp):
            with self.assertRaises(ValueError):
                search("ACGT", "")
        for q in (-1, 0, 1, 2.5, True):
            with self.assertRaises(ValueError):
                rabin_karp("A", "A", q)


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-m", "src.main", *map(str, args)],
                              cwd=ROOT, text=True, capture_output=True)

    def test_example_and_export(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "nested" / "result.json"
            result = self.run_cli("data/example.txt", "acg", "--output", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            records = json.loads(output.read_text())["results"]
            self.assertEqual(len(records), 2)
            for record in records:
                self.assertEqual(record["positions"], [0, 4, 9])

    def test_truncation_preserves_full_export(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "result.json"
            result = self.run_cli("data/overlaps.txt", "AA", "--output", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("full list in JSON export", result.stdout)
            for record in json.loads(output.read_text())["results"]:
                self.assertEqual(record["positions"], list(range(39)))

    def test_selection_and_invalid_cli(self):
        for algorithm in ("kmp", "rk"):
            result = self.run_cli("data/example.txt", "ACG", "--algorithm", algorithm)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.count("match(es)"), 1)
        for args in [("data/example.txt", "N"), ("data/example.txt", ""),
                     ("data/example.txt", "A", "--q", "1"), ("missing.txt", "A")]:
            result = self.run_cli(*args)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("error:", result.stderr)


if __name__ == "__main__":
    unittest.main()
