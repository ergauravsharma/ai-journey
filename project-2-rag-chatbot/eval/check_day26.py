"""
Day 26 — Offline check for Exercise 2 (reciprocal_rank).

No API key or Chroma index needed: this only tests your scoring function.

Run from the project-2-rag-chatbot folder:
    python eval/check_day26.py

Keep editing reciprocal_rank() in eval_retrieval.py until this prints PASS.
"""

import sys
from pathlib import Path

# Make eval_retrieval.py importable no matter which folder you run this from
sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_retrieval import reciprocal_rank, mean_reciprocal_rank

# Each case: (input rank, expected score). None means "right chunk not found".
CASES = [
    (1, 1.0),
    (2, 0.5),
    (3, 1 / 3),
    (5, 0.2),
    (None, 0.0),
]


def main():
    failures = 0

    for rank, expected in CASES:
        try:
            got = reciprocal_rank(rank)
        except NotImplementedError:
            print("NOT STARTED: reciprocal_rank() still raises NotImplementedError.")
            print("Open eval/eval_retrieval.py, write the function, delete the raise line.")
            sys.exit(1)
        except Exception as error:  # e.g. TypeError from dividing by None
            print(f"FAIL  rank={rank!r}: crashed with {type(error).__name__}: {error}")
            failures += 1
            continue

        # Compare floats with a small tolerance: 1/3 can't be stored exactly
        if abs(got - expected) < 1e-9:
            print(f"ok    rank={rank!r} -> {got:.3f}")
        else:
            print(f"FAIL  rank={rank!r}: expected {expected:.3f}, got {got!r}")
            failures += 1

    # MRR is the average of the scores above, so check it end to end too:
    # ranks 1, 2 and a miss -> (1.0 + 0.5 + 0.0) / 3 = 0.5
    fake_results = [{"rank": 1}, {"rank": 2}, {"rank": None}]
    mrr = mean_reciprocal_rank(fake_results)
    if mrr is not None and abs(mrr - 0.5) < 1e-9:
        print(f"ok    MRR of ranks [1, 2, miss] -> {mrr:.2f}")
    else:
        print(f"FAIL  MRR of ranks [1, 2, miss]: expected 0.50, got {mrr!r}")
        failures += 1

    print("\nPASS" if failures == 0 else f"\n{failures} check(s) failed. Keep going!")
    sys.exit(0 if failures == 0 else 1)


if __name__ == "__main__":
    main()
