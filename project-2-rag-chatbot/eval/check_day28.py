"""
Day 28 — Offline check for the is_refusal() exercise.

No API key needed: this only tests your refusal detector.

Run from the project-2-rag-chatbot folder:
    python eval/check_day28.py

Keep editing is_refusal() in eval_refusals.py until this prints PASS.
"""

import sys
from pathlib import Path

# Make eval_refusals.py importable no matter which folder you run this from
sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_refusals import is_refusal

# Each case: (chatbot answer, should it count as a refusal?)
CASES = [
    ("I don't have that information.", True),
    ("I DON'T HAVE THAT INFORMATION in the documents provided.", True),   # case shouldn't matter
    ("The provided context doesn't mention PayPal.", True),
    ("A Linux desktop app is not mentioned in the documentation.", True),
    ("Yes, CloudDesk accepts PayPal and all major credit cards.", False),  # a hallucination
    ("The Pro plan costs $29 per month per user.", False),                # a normal answer
    ("", False),                                                           # empty answer
]


def main():
    failures = 0

    for answer_text, expected in CASES:
        try:
            got = is_refusal(answer_text)
        except NotImplementedError:
            print("NOT STARTED: is_refusal() still raises NotImplementedError.")
            print("Open eval/eval_refusals.py, write the function, delete the raise line.")
            sys.exit(1)

        if got is expected:
            print(f"ok    {answer_text[:55]!r} -> {got}")
        else:
            print(f"FAIL  {answer_text[:55]!r}: expected {expected}, got {got!r}")
            failures += 1

    print("\nPASS" if failures == 0 else f"\n{failures} check(s) failed. Keep going!")
    sys.exit(0 if failures == 0 else 1)


if __name__ == "__main__":
    main()
