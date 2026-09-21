# Day 6 — Prompting Notes

## Principle 1: Write clear instructions
- Use delimiters (backslashes, triple quotes `"""`, angle brackets `< >`, XML tags `<tag>`) to clearly separate instructions from the content being processed — prevents the model from confusing your instructions with the input text.
- Ask for structured output (JSON, HTML, bullet lists) when you need something a program can parse, not just something a human reads.

## Principle 2: Give the model time to think
- Break complex tasks into steps instead of asking for the answer directly — this reduces rushed/wrong answers.
- Ask the model to work out its own solution before judging/comparing (useful when checking correctness).

## Iterative prompt development
- Write a first-draft prompt → check the result → identify what's wrong (too long, wrong tone, missing something, wrong format) → refine → repeat.
- Common fixes: clarify instructions, give more "thinking room," add an example (few-shot), adjust length/tone constraints.

## Experiments (Gemini 3.5 Flash Lite)

**Exp 1 — Delimiters:** Gave a block of trivia text wrapped in triple quotes, asked for a one-sentence summary.
→ Correctly summarized all 4 unrelated facts into one coherent sentence, without confusing the instruction with the content.

**Exp 2 — Structured output:** Asked for 3 programming languages as JSON with "name" and "year_created".
→ Returned valid, correctly-formatted JSON on the first try — no cleanup needed.

**Exp 3 — Step-by-step thinking:** Apple math word problem, asked to think step by step.
→ Model broke it into 5 clear steps (120 → 54 sold Mon → 66 left → 30 sold Tue → 36 final) and got the correct answer. Step-by-step reasoning made it easy to verify each calculation instead of just trusting a final number.