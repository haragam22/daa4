"""KMP and Rabin–Karp. Core functions accept already validated uppercase DNA.

Input preparation is intentionally separate from algorithm timing. All returned
positions are zero-based and overlapping matches are included.
"""
from dataclasses import dataclass

DNA_CODES = {"A": 0, "C": 1, "G": 2, "T": 3}
BASE = 4


@dataclass
class Metrics:
    preprocessing_comparisons: int = 0
    search_comparisons: int = 0
    hash_checks: int = 0
    rolling_updates: int = 0
    hash_hits: int = 0
    spurious_hits: int = 0


def normalize_dna(value: str, *, motif: bool = False) -> str:
    """Remove whitespace, uppercase, then enforce the supported alphabet."""
    sequence = "".join(value.split()).upper()
    invalid = sorted(set(sequence) - DNA_CODES.keys())
    if invalid:
        raise ValueError("Only A/C/G/T and whitespace are supported; invalid: "
                         + repr("".join(invalid)))
    if motif and not sequence:
        raise ValueError("Motif must not be empty.")
    return sequence


def build_lps(pattern: str, metrics: Metrics | None = None) -> list[int]:
    """lps[i] = length of longest proper prefix/suffix of pattern[:i+1]."""
    lps = [0] * len(pattern)
    length = 0
    i = 1
    while i < len(pattern):
        if metrics is not None:
            metrics.preprocessing_comparisons += 1
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        elif length:
            length = lps[length - 1]
        else:
            i += 1
    return lps


def kmp(text: str, pattern: str, metrics: Metrics | None = None) -> list[int]:
    if not pattern:
        raise ValueError("Motif must not be empty.")
    n, m = len(text), len(pattern)
    if m > n:
        return []
    lps = build_lps(pattern, metrics)
    positions = []
    i = j = 0
    while i < n:
        if metrics is not None:
            metrics.search_comparisons += 1
        if text[i] == pattern[j]:
            i += 1
            j += 1
            if j == m:
                positions.append(i - m)
                j = lps[j - 1]
        elif j:
            j = lps[j - 1]
        else:
            i += 1
    return positions


def rabin_karp(text: str, pattern: str, q: int = 1009,
               metrics: Metrics | None = None) -> list[int]:
    if not pattern:
        raise ValueError("Motif must not be empty.")
    if isinstance(q, bool) or not isinstance(q, int) or q <= 1:
        raise ValueError("Modulus q must be an integer greater than 1.")
    n, m = len(text), len(pattern)
    if m > n:
        return []
    high = pow(BASE, m - 1, q)
    pattern_hash = window_hash = 0
    for j in range(m):
        pattern_hash = (BASE * pattern_hash + DNA_CODES[pattern[j]]) % q
        window_hash = (BASE * window_hash + DNA_CODES[text[j]]) % q
    positions = []
    for start in range(n - m + 1):
        if metrics is not None:
            metrics.hash_checks += 1
        if pattern_hash == window_hash:
            if metrics is not None:
                metrics.hash_hits += 1
            matched = True
            for j in range(m):
                if metrics is not None:
                    metrics.search_comparisons += 1
                if text[start + j] != pattern[j]:
                    matched = False
                    break
            if matched:
                positions.append(start)
            elif metrics is not None:
                metrics.spurious_hits += 1
        if start < n - m:
            window_hash = (BASE * (window_hash - DNA_CODES[text[start]] * high)
                           + DNA_CODES[text[start + m]]) % q
            if metrics is not None:
                metrics.rolling_updates += 1
    return positions
