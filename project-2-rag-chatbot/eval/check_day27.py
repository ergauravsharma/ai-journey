"""
Day 27 — Offline check for the exact_match() exercise.

No API key needed: this only tests your string-matching function.

Run from the project-2-rag-chatbot folder:
    python eval/check_day27.py

Keep editing exact_match() in eval_answers.py until this prints PASS.
"""

import sys
from pathlib import Path

# Make eval_answers.py importable no matter which folder you run this from
sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_answers import exact_match

# Each case: (chatbot answer, golden fact, expected result)
CASES = [
    ("Refunds are allowed within 30 days of purchase.", "within 30 days", True),
    ("You have WITHIN 30 DAYS to ask for one.", "within 30 days", True),          # case shouldn't matter
    ("The Pro plan is $29 per month per user.", "$29 per month", True),
    ("You have a month to ask for a refund.", "within 30 days", False),           # right idea, different words
    ("The Pro plan costs $29 a month.", "$29 per month", False),                  # why we need the LLM judge
    ("", "100 MB", False),                                                        # empty answer
]


def main():
    failures = 0

    for answer_text, fact, expected in CASES:
        try:
            got = exact_match(answer_text, fact)
        except NotImplementedError:
            print("NOT STARTED: exact_match() still raises NotImplementedError.")
            print("Open eval/eval_answers.py, write the function, delete the raise line.")
            sys.exit(1)

        if got is expected:
            print(f"ok    {fact!r} in {answer_text[:45]!r} -> {got}")
        else:
            print(f"FAIL  {fact!r} in {answer_text[:45]!r}: expected {expected}, got {got!r}")
            failures += 1

    print("\nPASS" if failures == 0 else f"\n{failures} check(s) failed. Keep going!")
    sys.exit(0 if failures == 0 else 1)


if __name__ == "__main__":
    main()
