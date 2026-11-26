"""
Day 27 — Answer-quality evaluation (LLM-as-judge) for the CloudDesk RAG chatbot.

Day 26 asked: "Did the retriever bring back the right chunk?"
Today asks:   "Given those chunks, did the chatbot write a CORRECT answer?"

Retrieval can be perfect and the answer still wrong (the model misreads the
chunk, mixes up two plans, or ignores the fact). So we grade the final answer.

Two graders, side by side:
    1. exact_match  — cheap string check: does the answer contain the golden fact?
    2. LLM judge    — a second LLM call reads question + golden fact + answer
                      and decides correct / partially_correct / incorrect.

Comparing them shows WHY teams use LLM judges: string matching marks
"$29 a month" wrong when the golden fact is "$29 per month".

Run from the project-2-rag-chatbot folder:
    python eval/eval_answers.py               # all in-scope questions
    python eval/eval_answers.py --limit 3     # quick test on the first 3
    python eval/eval_answers.py --delay 4     # wait 4s between calls (free-tier rate limits)
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

# This script lives in eval/, but rag.py lives one folder up.
# Adding the parent folder to Python's search path lets us import it normally.
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

EVAL_DIR = Path(__file__).resolve().parent
GOLDEN_SET_PATH = EVAL_DIR / "golden_set.json"
RESULTS_DIR = EVAL_DIR / "results"

JUDGE_MODEL = "gemini-3.6-flash"  # same model family the app uses


# ---------------------------------------------------------------------------
# Grader 1: exact match (no LLM)
# ---------------------------------------------------------------------------

def exact_match(answer_text: str, expected_fact: str) -> bool:
    """YOUR TURN (Day 27 exercise): return True if the golden fact appears
    anywhere in the answer, ignoring upper/lower case.

    Examples:
        exact_match("Refunds are allowed within 30 days.", "within 30 days")  -> True
        exact_match("You have WITHIN 30 DAYS to ask.", "within 30 days")      -> True
        exact_match("You have a month to ask.", "within 30 days")             -> False

    Hint: is_relevant() in eval_retrieval.py does the same kind of check on chunks.
    Delete the `raise` line below once you've written it.
    Check it with: python eval/check_day27.py"""
    # Lower-case both sides so "WITHIN 30 DAYS" still matches "within 30 days"
    answer_lower = answer_text.lower()
    fact_lower = expected_fact.lower()

    # "in" checks whether one string appears anywhere inside the other
    return fact_lower in answer_lower

# ---------------------------------------------------------------------------
# Grader 2: LLM as judge
# ---------------------------------------------------------------------------

class JudgeVerdict(BaseModel):
    """The structured answer we force the judge to give. Literal limits the
    verdict to exactly these three labels, so the output is easy to count."""
    verdict: Literal["correct", "partially_correct", "incorrect"]
    reason: str  # one sentence, so a human can audit the judge's decisions


JUDGE_INSTRUCTIONS = (
    "You are grading a customer-support chatbot. You get a user question, the "
    "GOLDEN FACT that a correct answer must contain, and the chatbot's ANSWER.\n\n"
    "Grade only factual correctness against the golden fact:\n"
    "- correct: the answer states the golden fact (same meaning, any wording) "
    "and says nothing that contradicts it.\n"
    "- partially_correct: the answer is on the right topic but the golden fact "
    "is missing, vague, or mixed with a wrong detail.\n"
    "- incorrect: the answer contradicts the golden fact, gives a different "
    "fact, or says it doesn't know.\n\n"
        "Extra details, caveats or exceptions (for example, a different rule for "
    "another plan) are fine and must NOT lower the grade, as long as the golden "
    "fact is stated. Ignore tone, length and formatting. Give a one-sentence reason."
)


def make_judge():
    """Build the judge once. Imported inside the function so check_day27.py
    can test exact_match() without an API key."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.prompts import ChatPromptTemplate

    llm = ChatGoogleGenerativeAI(
        model=JUDGE_MODEL,
        temperature=0,  # the judge should give the same grade every run
        google_api_key=os.environ["GOOGLE_API_KEY"],
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", JUDGE_INSTRUCTIONS),
        ("user", "QUESTION: {question}\nGOLDEN FACT: {expected_fact}\nANSWER: {answer}"),
    ])
    # prompt | structured LLM = a chain that returns a JudgeVerdict object
    return prompt | llm.with_structured_output(JudgeVerdict)


# ---------------------------------------------------------------------------
# Running the evaluation
# ---------------------------------------------------------------------------

def load_golden_set(path: Path) -> list[dict]:
    """Read the list of test questions (with their expected answers) from JSON."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def call_with_retry(fn, *args, attempts: int = 3, first_wait: float = 15):
    """Call fn(*args). If Google says it's overloaded (503), wait and try again.

    This is "exponential backoff": wait 15s, then 30s, doubling each time, so
    we don't hammer a server that's already struggling. Any OTHER error
    (like 429 = daily quota used up) is raised straight away, because
    waiting a few seconds won't fix it."""
    wait = first_wait

    for attempt in range(1, attempts + 1):
        try:
            return fn(*args)  # success: hand the result straight back
        except Exception as error:
            overloaded = "503" in str(error) or "UNAVAILABLE" in str(error)

            # A different error, or this was our last try: stop and show it
            if not overloaded or attempt == attempts:
                raise

            print(f"   Gemini is busy (503). Waiting {wait:.0f}s, then try {attempt + 1} of {attempts}...")
            time.sleep(wait)
            wait *= 2  # double the wait before the next try


def evaluate(answer_fn, judge, golden_set: list[dict], k: int, delay: float) -> list[dict]:
    """Ask the chatbot every in-scope question, then grade each answer twice.

    answer_fn is any function taking (question, k) and returning
    {"answer": str, "sources": list}, so we can swap in other chatbots later."""
    results = []
    in_scope = [q for q in golden_set if q["type"] != "out_of_scope"]  # refusals are Day 28

    for number, item in enumerate(in_scope, start=1):
        print(f"[{number}/{len(in_scope)}] {item['id']}: {item['question'][:60]}")

        # Step 1: get the chatbot's real answer (retries if Gemini is busy)
        bot = call_with_retry(answer_fn, item["question"], k)

        # Step 2: grade with the string check (None if the exercise isn't done yet)
        try:
            matched = exact_match(bot["answer"], item["expected_fact"])
        except NotImplementedError:
            matched = None

        # Step 3: grade with the LLM judge (also retries if Gemini is busy)
        verdict: JudgeVerdict = call_with_retry(judge.invoke, {
            "question": item["question"],
            "expected_fact": item["expected_fact"],
            "answer": bot["answer"],
        })

        results.append({
            "id": item["id"],
            "type": item["type"],
            "question": item["question"],
            "expected_fact": item["expected_fact"],
            "answer": bot["answer"],
            "sources": bot["sources"],
            # Did the bot cite the file the fact actually lives in?
            "cited_right_source": item["expected_source"] in bot["sources"],
            "exact_match": matched,
            "judge_verdict": verdict.verdict,
            "judge_reason": verdict.reason,
        })

        # Each question costs 2 LLM calls; pausing avoids free-tier 429 errors
        if delay and number < len(in_scope):
            time.sleep(delay)

    return results


def share(results: list[dict], condition) -> float:
    """Fraction of results for which condition(result) is True."""
    return sum(1 for r in results if condition(r)) / len(results) if results else 0.0


def print_report(results: list[dict]):
    """Per-question table, summary scores, and the cases worth reading by hand."""
    print(f"\nAnswer-quality evaluation — {len(results)} questions\n")
    print(f"{'ID':<5} {'Type':<12} {'Judge':<18} {'Exact':<6} Question")
    print("-" * 85)
    for r in results:
        exact_text = "-" if r["exact_match"] is None else ("yes" if r["exact_match"] else "no")
        print(f"{r['id']:<5} {r['type']:<12} {r['judge_verdict']:<18} {exact_text:<6} {r['question'][:40]}")

    print("\nSummary")
    print(f"  Judge: correct            {share(results, lambda r: r['judge_verdict'] == 'correct'):.0%}")
    print(f"  Judge: partially correct  {share(results, lambda r: r['judge_verdict'] == 'partially_correct'):.0%}")
    print(f"  Judge: incorrect          {share(results, lambda r: r['judge_verdict'] == 'incorrect'):.0%}")
    print(f"  Cited the right source    {share(results, lambda r: r['cited_right_source']):.0%}")

    # Split by question type, same as Day 26: are paraphrased questions harder?
    for qtype in ("direct", "paraphrased"):
        subset = [r for r in results if r["type"] == qtype]
        if subset:
            score = share(subset, lambda r: r["judge_verdict"] == "correct")
            print(f"  Judge correct ({qtype}): {score:.0%}  ({len(subset)} questions)")

    if all(r["exact_match"] is None for r in results):
        print("  Exact match:              (finish the Day 27 exercise)")
        return

    print(f"  Exact match               {share(results, lambda r: r['exact_match']):.0%}")

    # Where the two graders disagree is the interesting part: usually the
    # answer is right but worded differently, so the string check missed it
    disagreements = [
        r for r in results if r["exact_match"] != (r["judge_verdict"] == "correct")
    ]
    if disagreements:
        print("\nGraders disagree (read these yourself and decide who's right):")
        for r in disagreements:
            print(f"  {r['id']}: golden fact = '{r['expected_fact']}'")
            print(f"     answer: {r['answer'][:150]}")
            print(f"     judge:  {r['judge_verdict']} - {r['judge_reason']}")


def save_results(results: list[dict], k: int) -> Path:
    """Save this run to eval/results/ next to the Day 26 retrieval runs."""
    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    out_path = RESULTS_DIR / f"answers_k{k}_{stamp}.json"
    summary = {
        "k": k,
        "judge_model": JUDGE_MODEL,
        "judge_correct": share(results, lambda r: r["judge_verdict"] == "correct"),
        "cited_right_source": share(results, lambda r: r["cited_right_source"]),
        "results": results,
    }
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate answer quality with an LLM judge.")
    parser.add_argument("--k", type=int, default=5, help="chunks to retrieve per question (app uses 5)")
    parser.add_argument("--limit", type=int, default=None, help="only run N in-scope questions")
    parser.add_argument("--delay", type=float, default=0, help="seconds to wait between questions")
    parser.add_argument("--start", type=int, default=0, help="skip the first N in-scope questions (to run in batches)")
    args = parser.parse_args()

    # Imported here (not at the top) so exact_match() can be tested offline
    from rag import answer

    def rag_answer(question: str, k: int) -> dict:
        return answer(question, history=[], k=k)  # fresh conversation per question

    # Load all questions, then keep only the in-scope ones (refusals were Day 28)
    golden_set = load_golden_set(GOLDEN_SET_PATH)
    in_scope = [q for q in golden_set if q["type"] != "out_of_scope"]

    # Slice out one batch: from --start, and --limit questions long.
    # end=None means "go to the end of the list".
    end = args.start + args.limit if args.limit else None
    batch = in_scope[args.start:end]

    results = evaluate(rag_answer, make_judge(), batch, args.k, args.delay)
    print_report(results)
    saved_to = save_results(results, args.k)
    print(f"\nSaved results to {saved_to.relative_to(PROJECT_DIR)}")
