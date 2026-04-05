"""
Social Golfer Problem solver with Latin Square constraint.

Hard constraint: every trainee visits every table exactly once.
Soft constraint: maximize unique trainee-trainee pairings.

Algorithm: generate K permutations of [0..N-1] as group offsets.
Each trainee's route: table[r] = (member_number + offset[group][r]) % N
This guarantees each trainee visits all N tables exactly once.
Then optimize the permutation set for minimal co-occurrence.
"""

from __future__ import annotations

import itertools
import json
import random
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path


def co_occurrence_score(offsets: list[tuple[int, ...]], N: int, K: int) -> tuple[int, int, int]:
    """Compute (max_co, total_sq_co, -unique_pairs) for a set of offset permutations."""
    T = N * K
    met = [[0] * T for _ in range(T)]

    for r in range(N):
        # Build table assignments for this round
        tables: list[list[int]] = [[] for _ in range(N)]
        for g in range(K):
            for m in range(N):
                idx = g * N + m
                table = (m + offsets[g][r]) % N
                tables[table].append(idx)

        for table in tables:
            for i in range(len(table)):
                for j in range(i + 1, len(table)):
                    met[table[i]][table[j]] += 1
                    met[table[j]][table[i]] += 1

    max_co = 0
    total_sq = 0
    unique_pairs = 0
    for i in range(T):
        for j in range(i + 1, T):
            c = met[i][j]
            if c > max_co:
                max_co = c
            total_sq += c * c
            if c > 0:
                unique_pairs += 1

    return (max_co, total_sq, -unique_pairs)


def per_person_stats(offsets: list[tuple[int, ...]], N: int, K: int) -> tuple[int, int, float]:
    """Return (min_unique, max_unique, avg_unique) meetings per person."""
    T = N * K
    met = [[0] * T for _ in range(T)]

    for r in range(N):
        tables: list[list[int]] = [[] for _ in range(N)]
        for g in range(K):
            for m in range(N):
                idx = g * N + m
                table = (m + offsets[g][r]) % N
                tables[table].append(idx)

        for table in tables:
            for i in range(len(table)):
                for j in range(i + 1, len(table)):
                    met[table[i]][table[j]] += 1
                    met[table[j]][table[i]] += 1

    per_person = []
    for i in range(T):
        unique = sum(1 for j in range(T) if j != i and met[i][j] > 0)
        per_person.append(unique)

    return min(per_person), max(per_person), sum(per_person) / len(per_person)


def solve(N: int, K: int, attempts: int = 200) -> list[tuple[int, ...]]:
    """Find K permutations of [0..N-1] that minimize co-occurrence."""
    all_perms = list(itertools.permutations(range(N)))
    best_offsets: list[tuple[int, ...]] | None = None
    best_score = (float('inf'), float('inf'), float('inf'))

    if N <= 7:
        # Brute-force greedy: pick best permutation for each group
        for _ in range(attempts):
            offsets: list[tuple[int, ...]] = []

            # Group 0: identity or random permutation
            offsets.append(tuple(range(N)))

            for g in range(1, K):
                best_perm = None
                best_perm_score = (float('inf'), float('inf'), float('inf'))

                # Try all permutations for this group
                candidates = all_perms if N <= 6 else random.sample(all_perms, min(1000, len(all_perms)))
                for perm in candidates:
                    trial = offsets + [perm]
                    score = co_occurrence_score(trial, N, len(trial))
                    if score < best_perm_score:
                        best_perm_score = score
                        best_perm = perm

                offsets.append(best_perm)

            score = co_occurrence_score(offsets, N, K)
            if score < best_score:
                best_score = score
                best_offsets = offsets[:]
    else:
        # For large N, use random sampling
        for _ in range(attempts):
            offsets = [tuple(range(N))]  # group 0 = identity
            for g in range(1, K):
                perm = list(range(N))
                random.shuffle(perm)
                offsets.append(tuple(perm))

            score = co_occurrence_score(offsets, N, K)
            if score < best_score:
                best_score = score
                best_offsets = offsets[:]

    return best_offsets


def offsets_to_schedule(offsets: list[tuple[int, ...]], N: int, K: int) -> list[list[list[int]]]:
    """Convert offset permutations to round-by-round table assignments."""
    all_rounds = []
    for r in range(N):
        tables: list[list[int]] = [[] for _ in range(N)]
        for g in range(K):
            for m in range(N):
                idx = g * N + m
                table = (m + offsets[g][r]) % N
                tables[table].append(idx)
        all_rounds.append([sorted(t) for t in tables])
    return all_rounds


def verify_latin_square(schedule: list[list[list[int]]], N: int, K: int) -> bool:
    """Verify every trainee visits every table exactly once."""
    T = N * K
    for i in range(T):
        visited = set()
        for r, round_tables in enumerate(schedule):
            for t, table in enumerate(round_tables):
                if i in table:
                    if t in visited:
                        return False
                    visited.add(t)
        if visited != set(range(N)):
            return False
    return True


def main():
    N_range = range(3, 9)
    K_range = range(2, 7)

    results: dict[str, dict] = {}
    stats: list[dict] = []

    for N in N_range:
        for K in K_range:
            T = N * K
            if T > 48:
                continue

            key = f"{N},{K}"
            print(f"Solving N={N}, K={K} (T={T})...", end=" ", flush=True)

            attempts = 500 if N <= 5 else 200
            offsets = solve(N, K, attempts=attempts)
            schedule = offsets_to_schedule(offsets, N, K)

            assert verify_latin_square(schedule, N, K), f"Latin square violation for ({N},{K})!"

            score = co_occurrence_score(offsets, N, K)
            max_co = score[0]
            unique_pairs = -score[2]
            total_pairs = T * (T - 1) // 2
            mn, mx, avg = per_person_stats(offsets, N, K)

            print(f"max_co={max_co}, unique={unique_pairs}/{total_pairs} ({100*unique_pairs/total_pairs:.0f}%), "
                  f"per_person={mn}~{mx} (avg {avg:.1f})")

            results[key] = {
                "offsets": [list(o) for o in offsets],
                "schedule": schedule,
            }
            stats.append({
                "N": N, "K": K, "T": T, "rounds": N,
                "max_co_occurrence": max_co,
                "unique_pairs": unique_pairs,
                "total_pairs": total_pairs,
                "coverage_pct": round(100 * unique_pairs / total_pairs, 1),
                "per_person_min": mn,
                "per_person_max": mx,
                "per_person_avg": round(avg, 1),
            })

    # Write solutions.py
    output_path = Path(__file__).resolve().parents[1] / "src" / "solutions.py"
    with output_path.open("w", encoding="utf-8") as f:
        f.write('"""Pre-computed optimal schedules for the Social Golfer Problem.\n\n')
        f.write("Each trainee visits every table exactly once (Latin Square constraint).\n\n")
        f.write("Key: (num_tables, trainees_per_table)\n")
        f.write("Value: list of N rounds. Each round is a list of N tables.\n")
        f.write("  Each table is a list of trainee indices (0-based).\n")
        f.write("  Trainee index = group * num_tables + member_number.\n")
        f.write('"""\n\n')
        f.write("from __future__ import annotations\n\n\n")
        f.write("SCHEDULES: dict[tuple[int, int], list[list[list[int]]]] = {\n")

        for key_str in sorted(results.keys(), key=lambda x: tuple(map(int, x.split(",")))):
            n, k = key_str.split(",")
            schedule = results[key_str]["schedule"]
            f.write(f"    ({n}, {k}): [\n")
            for round_tables in schedule:
                f.write(f"        {round_tables},\n")
            f.write("    ],\n")

        f.write("}\n")

    print(f"\nWritten to {output_path}")

    stats_path = Path(__file__).resolve().parent / "solution_stats.json"
    with stats_path.open("w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"Stats written to {stats_path}")


if __name__ == "__main__":
    main()
