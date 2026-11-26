"""
Day 28 — Refusal evaluation for the CloudDesk RAG chatbot.

Day 26 asked: "Did we retrieve the right chunk?"
Day 27 asked: "Is the answer correct?"
Today asks:   "When the docs DON'T contain the answer, does the bot admit it,
               or does it make something up?"

A made-up answer (a "hallucination") is worse than no answer: a customer who
is told "yes, we accept PayPal" when you don't will open an angry ticket.
rag.py tells the model to say it doesn't have the information, and today we
check whether it actually obeys.

Each question costs only ONE Gemini call (the chatbot). We detect refusals
with a phrase list instead of an LLM judge, to save free-tier quota.

Run from the project-2-rag-chatbot folder:
    python eval/eval_refusals.py --delay 4
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Same Windows memory fix as Day 27: must run BEFORE numpy is imported (via rag)
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

# This script lives in eval/, but rag.py lives one folder up.
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

EVAL_DIR = Path(__file__).resolve().parent
GOLDEN_SET_PATH = EVAL_DIR / "golden_set.json"
RESULTS_DIR = EVAL_DIR / "results"

# Ways the bot says "I don't know". All lower-case, because is_refusal()
# compares against a lower-cased answer.
REFUSAL_PHRASES = [
    "don't have that information",
    "do not have that information",
    "don't have information",
    "do not have information",
    "no information",
    "not mentioned",
    "isn't mentioned",
    "doesn't mention",
    "does not mention",
    "not specified",
    "not in the context",
    "not provided",
    "couldn't find",
    "could not find",
]


def is_refusal(answer_text: str) -> bool:
    """YOUR TURN (Day 28 exercise): return True if the answer contains ANY
    phrase from REFUSAL_PHRASES, ignoring upper/lower case.

    Examples:
        is_refusal("I don't have that information.")             -> True
        is_refusal("The context doesn't mention PayPal.")         -> True
        is_refusal("Yes, CloudDesk accepts PayPal.")              -> False

    Hint: lower-case the answer once, then loop over REFUSAL_PHRASES and
    return True as soon as one phrase is found. If the loop finishes without
    finding one, return False.
    Delete the `raise` line below once you've written it.
    Check it with: python eval/check_day28.py"""
    # Lower-case the answer once, so we don't repeat it for every phrase
    answer_lower = answer_text.lower()

    # Check each refusal phrase; stop as soon as one is found
    for phrase in REFUSAL_PHRASES:
        if phrase in answer_lower:
            return True

    # The loop finished without finding any phrase: not a refusal
    return False

def load_golden_set(path: Path) -> list[dict]:
    """Read the list of test questions from JSON."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evaluate(answer_fn, questions: list[dict], k: int, delay: float) -> list[dict]:
    """Ask the chatbot every out-of-scope question and record whether it refused.

    answer_fn takes (question, k) and returns {"answer": str, "sources": list}."""
    results = []

    for number, item in enumerate(questions, start=1):
        print(f"[{number}/{len(questions)}] {item['id']}: {item['question'][:60]}")

        # Step 1: get the chatbot's real answer
        bot = answer_fn(item["question"], k)

        # Step 2: did it refuse? A correct refusal should also cite no sources,
        # because there was nothing in the docs to draw on
        refused = is_refusal(bot["answer"])

        results.append({
            "id": item["id"],
            "question": item["question"],
            "answer": bot["answer"],
            "sources": bot["sources"],
            "refused": refused,
            "cited_sources_anyway": refused and len(bot["sources"]) > 0,
        })

        # Pause between questions to stay under the free-tier rate limit
        if delay and number < len(questions):
            time.sleep(delay)

    return results


def print_report(results: list[dict]):
    """Per-question table, the refusal rate, and full text of any non-refusals."""
    print(f"\nRefusal evaluation — {len(results)} out-of-scope questions\n")
    print(f"{'ID':<5} {'Refused':<9} {'Sources':<22} Question")
    print("-" * 85)
    for r in results:
        sources = ", ".join(r["sources"]) or "-"
        print(f"{r['id']:<5} {'yes' if r['refused'] else 'NO':<9} {sources[:21]:<22} {r['question'][:45]}")

    refused = [r for r in results if r["refused"]]
    print("\nSummary")
    print(f"  Refusal rate:                {len(refused) / len(results):.0%}  ({len(refused)}/{len(results)})")
    print(f"  Refused but cited sources:   {sum(r['cited_sources_anyway'] for r in results)}")

    # Anything NOT refused is either a hallucination, or a refusal worded in a
    # way our phrase list doesn't know. Only a human can tell, so print it all.
    not_refused = [r for r in results if not r["refused"]]
    if not_refused:
        print("\nNot detected as refusals (read each one: hallucination, or a phrase to add?):")
        for r in not_refused:
            print(f"\n  {r['id']}: {r['question']}")
            print(f"     answer: {r['answer']}")


def save_results(results: list[dict], k: int) -> Path:
    """Save this run to eval/results/ next to the Day 26 and Day 27 runs."""
    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    out_path = RESULTS_DIR / f"refusals_k{k}_{stamp}.json"
    summary = {
        "k": k,
        "refusal_rate": sum(r["refused"] for r in results) / len(results) if results else 0.0,
        "results": results,
    }
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check that the bot refuses out-of-scope questions.")
    parser.add_argument("--k", type=int, default=5, help="chunks to retrieve per question (app uses 5)")
    parser.add_argument("--delay", type=float, default=0, help="seconds to wait between questions")
    args = parser.parse_args()

    # Imported here (not at the top) so is_refusal() can be tested offline
    from rag import answer

    def rag_answer(question: str, k: int) -> dict:
        return answer(question, history=[], k=k)  # fresh conversation per question

    # Only the out-of-scope questions: these are the ones the bot should refuse
    out_of_scope = [q for q in load_golden_set(GOLDEN_SET_PATH) if q["type"] == "out_of_scope"]

    results = evaluate(rag_answer, out_of_scope, args.k, args.delay)
    print_report(results)
    saved_to = save_results(results, args.k)
    print(f"\nSaved results to {saved_to.relative_to(PROJECT_DIR)}")
