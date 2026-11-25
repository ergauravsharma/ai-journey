"""
Day 26 — Retrieval evaluation for the CloudDesk RAG chatbot.

Question this script answers:
    "When a user asks something, does the retriever actually bring back
     the chunk that contains the answer?"

If retrieval misses, the LLM never sees the right text, so even a perfect
prompt can't save the answer. That's why we measure retrieval FIRST
(today), and answer quality later in the week.

Run from the project-2-rag-chatbot folder:
    python eval/eval_retrieval.py            # default: look at top 5 chunks
    python eval/eval_retrieval.py --k 3      # try a different k
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# This script lives in eval/, but load_index.py lives one folder up.
# Adding the parent folder to Python's search path lets us import it normally.
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

EVAL_DIR = Path(__file__).resolve().parent
GOLDEN_SET_PATH = EVAL_DIR / "golden_set.json"
RESULTS_DIR = EVAL_DIR / "results"


def load_golden_set(path: Path) -> list[dict]:
    """Read the list of test questions (with their expected answers) from JSON."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def is_relevant(chunk, expected_source: str, expected_fact: str) -> bool:
    """A chunk counts as 'relevant' only if it comes from the right file
    AND actually contains the fact needed to answer.

    Checking the file alone is too easy: we only have 3 docs, so the right
    file shows up almost every time. Checking for the fact tells us whether
    we got the right PIECE of that file."""
    same_file = chunk.metadata["source"] == expected_source
    has_fact = expected_fact.lower() in chunk.page_content.lower()  # case-insensitive match
    return same_file and has_fact


def find_rank(chunks: list, expected_source: str, expected_fact: str) -> int | None:
    """Return the position (1 = top result) of the first relevant chunk,
    or None if no relevant chunk was retrieved at all."""
    for position, chunk in enumerate(chunks, start=1):
        if is_relevant(chunk, expected_source, expected_fact):
            return position
    return None


def reciprocal_rank(rank: int | None) -> float:
    """YOUR TURN (Exercise 2): score how high the right chunk appeared.

    Rules:
        rank 1    -> 1.0
        rank 2    -> 0.5
        rank 3    -> 0.333...
        not found -> 0.0   (rank is None)

    Hint: it's 1 divided by the rank. Handle None first.
    Delete the `raise` line below once you've written it."""
        # If the right chunk was never retrieved, the question scores zero
    if rank is None:
        return 0.0

    # Otherwise the score is 1 divided by the position:
    # 1st place -> 1.0, 2nd -> 0.5, 3rd -> 0.333...
    return 1 / rank


def evaluate(search_fn, golden_set: list[dict], k: int) -> list[dict]:
    """Run every in-scope question through the retriever and record where
    (if anywhere) the right chunk appeared.

    search_fn is any function that takes (question, k) and returns chunks.
    Passing it in, instead of hard-coding Chroma here, makes this easy to test
    and lets us compare different retrievers later in the week."""
    results = []

    for item in golden_set:
        # Out-of-scope questions have no "right chunk", so retrieval can't be
        # scored for them. We'll use them on Day 28 to test refusals instead.
        if item["type"] == "out_of_scope":
            continue

        chunks = search_fn(item["question"], k)
        rank = find_rank(chunks, item["expected_source"], item["expected_fact"])

        results.append({
            "id": item["id"],
            "type": item["type"],
            "question": item["question"],
            "rank": rank,
            # Keep what the retriever actually returned, so misses can be debugged
            "retrieved": [
                f"{c.metadata['source']}#chunk{c.metadata['chunk_id']}" for c in chunks
            ],
            "top_chunk_preview": chunks[0].page_content[:120].replace("\n", " ") if chunks else "",
        })

    return results


def hit_rate(results: list[dict], at: int) -> float:
    """Fraction of questions where the right chunk appeared in the top `at` results."""
    hits = [r for r in results if r["rank"] is not None and r["rank"] <= at]
    return len(hits) / len(results) if results else 0.0


def mean_reciprocal_rank(results: list[dict]) -> float | None:
    """Average of reciprocal_rank over all questions. Returns None until
    Exercise 2 is done, so the rest of the report still works."""
    try:
        scores = [reciprocal_rank(r["rank"]) for r in results]
    except NotImplementedError:
        return None
    return sum(scores) / len(scores) if scores else 0.0


def print_report(results: list[dict], k: int):
    """Show a per-question table, the summary metrics, and details of any misses."""
    print(f"\nRetrieval evaluation — {len(results)} questions, k={k}\n")
    print(f"{'ID':<5} {'Type':<12} {'Rank':<6} Question")
    print("-" * 80)
    for r in results:
        rank_text = str(r["rank"]) if r["rank"] else "MISS"
        print(f"{r['id']:<5} {r['type']:<12} {rank_text:<6} {r['question'][:55]}")

    print("\nSummary")
    for at in sorted({1, 3, k}):
        if at <= k:  # can't measure hit@5 if we only retrieved 3 chunks
            print(f"  Hit rate @{at}: {hit_rate(results, at):.0%}")

    mrr = mean_reciprocal_rank(results)
    print(f"  MRR:         {mrr:.2f}" if mrr is not None else "  MRR:         (finish Exercise 2)")

    # Split by question type: are paraphrased questions harder than direct ones?
    for qtype in ("direct", "paraphrased"):
        subset = [r for r in results if r["type"] == qtype]
        if subset:
            print(f"  Hit rate @1 ({qtype}): {hit_rate(subset, 1):.0%}  ({len(subset)} questions)")

    misses = [r for r in results if r["rank"] is None]
    if misses:
        print("\nMisses (right chunk not in top k):")
        for r in misses:
            print(f"  {r['id']}: {r['question']}")
            print(f"     retrieved: {', '.join(r['retrieved'])}")
            print(f"     top chunk: {r['top_chunk_preview']}...")


def save_results(results: list[dict], k: int) -> Path:
    """Save this run to eval/results/ so later runs (different k, chunk size,
    etc.) can be compared against it."""
    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    out_path = RESULTS_DIR / f"retrieval_k{k}_{stamp}.json"
    summary = {
        "k": k,
        "hit_rate_at_1": hit_rate(results, 1),
        "hit_rate_at_k": hit_rate(results, k),
        "mrr": mean_reciprocal_rank(results),
        "results": results,
    }
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate retrieval quality.")
    parser.add_argument("--k", type=int, default=5, help="how many chunks to retrieve (app uses 5)")
    args = parser.parse_args()

    # Imported here (not at the top) so the scoring functions above can be
    # tested without needing an API key or the Chroma index
    from load_index import load_index

    vector_store = load_index()  # open the index ONCE, not once per question

    def chroma_search(question: str, k: int) -> list:
        return vector_store.similarity_search(question, k=k)

    golden_set = load_golden_set(GOLDEN_SET_PATH)
    results = evaluate(chroma_search, golden_set, args.k)
    print_report(results, args.k)
    saved_to = save_results(results, args.k)
    print(f"\nSaved results to {saved_to.relative_to(PROJECT_DIR)}")
