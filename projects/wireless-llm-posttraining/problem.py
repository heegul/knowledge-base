"""Independent toy wireless resource-allocation task and exact reference solver.

Two orthogonal resource blocks (RBs) must be assigned to distinct users.  The
input table contains measured achievable rates in Mbps.  Exhaustive search is
an exact solver for THIS small discrete problem, not a paper reproduction.
"""

from __future__ import annotations

import itertools
import json
import random
import re
from pathlib import Path


DATA_SEED = 241124
RESPONSE_RE = re.compile(r"\s*RB1=U(\d+),RB2=U(\d+)\s*\Z")


def solve(rates: list[list[int]]) -> tuple[tuple[int, int], int]:
    """Return lexicographically first maximizer and its sum rate."""
    n = len(rates)
    if n < 2 or any(len(row) != 2 for row in rates):
        raise ValueError("Need >=2 users and exactly 2 RB rates per user")
    candidates = ((i, j) for i in range(n) for j in range(n) if i != j)
    best = max(candidates, key=lambda x: (rates[x[0]][0] + rates[x[1]][1], -x[0], -x[1]))
    return best, rates[best[0]][0] + rates[best[1]][1]


def prompt(rates: list[list[int]]) -> str:
    rows = "\n".join(f"U{i}: RB1={a}, RB2={b}" for i, (a, b) in enumerate(rates))
    return (
        "Allocate two orthogonal wireless resource blocks. Rates are Mbps. "
        "Assign one distinct user to each RB to maximize total rate.\n"
        + rows
        + "\nReply exactly RB1=Ux,RB2=Uy with no explanation.\nAnswer:"
    )


def format_answer(pair: tuple[int, int]) -> str:
    return f"RB1=U{pair[0]},RB2=U{pair[1]}"


def parse_answer(text: str, n_users: int) -> tuple[int, int] | None:
    match = RESPONSE_RE.fullmatch(text)
    if not match:
        return None
    i, j = map(int, match.groups())
    return (i, j) if i < n_users and j < n_users and i != j else None


def score(rates: list[list[int]], response: str) -> dict:
    pair = parse_answer(response, len(rates))
    optimum, optimum_rate = solve(rates)
    if pair is None:
        return {"feasible": False, "optimal": False, "achieved_rate": None,
                "optimal_rate": optimum_rate, "ratio": 0.0, "reward": 0.0}
    achieved = rates[pair[0]][0] + rates[pair[1]][1]
    ratio = achieved / optimum_rate
    return {"feasible": True, "optimal": achieved == optimum_rate,
            "achieved_rate": achieved, "optimal_rate": optimum_rate,
            "ratio": ratio, "reward": ratio}


def make_splits() -> dict[str, list[dict]]:
    rng = random.Random(DATA_SEED)
    seen = set()
    specs = {"train": (512, 3, 1, 9), "validation": (64, 3, 1, 9),
             "test_id": (64, 3, 1, 9), "test_rate_shift": (64, 3, 10, 30),
             "test_more_users": (64, 4, 1, 9), "rl_prompts": (160, 3, 1, 9)}
    result = {}
    for split, (count, n, low, high) in specs.items():
        rows = []
        while len(rows) < count:
            rates = [[rng.randint(low, high), rng.randint(low, high)] for _ in range(n)]
            key = (n, tuple(itertools.chain.from_iterable(rates)))
            if key in seen:
                continue
            seen.add(key)
            optimum, optimum_rate = solve(rates)
            rows.append({"id": f"{split}-{len(rows):04d}", "rates": rates,
                         "answer": format_answer(optimum), "optimal_rate": optimum_rate})
        result[split] = rows
    return result


def write_splits(directory: Path) -> dict[str, list[dict]]:
    directory.mkdir(parents=True, exist_ok=True)
    splits = make_splits()
    for name, rows in splits.items():
        with (directory / f"{name}.jsonl").open("w", encoding="utf-8") as file:
            for row in rows:
                file.write(json.dumps(row, separators=(",", ":")) + "\n")
    return splits
