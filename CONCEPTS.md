# AI Journey — Concepts Log

One concept per entry: **what it is**, **why it matters**, **example**. Review before starting the next day.

---

## Day 1 — Toolchain

**Git workflow**
- *Definition*: Git tracks changes to your code over time. Three core commands move a change from your laptop to GitHub.
- *Why it matters*: gives you version history and lets you undo mistakes, and is how every real software team collaborates.
- *Example*:git add hello.py # stage the file (mark it ready to save)
git commit -m "message" # save a snapshot locally, with a description
git push # upload that snapshot to GitHub


---

## Day 2 — Python refresh

**Virtual environment (venv)**
- *Definition*: an isolated copy of Python + packages, separate from your system-wide Python install.
- *Why it matters*: different projects often need different (conflicting) versions of the same package. A venv keeps them from interfering with each other.
- *Example*:
python -m venv venv # create it (once per project)
venv\Scripts\activate # turn it on (every time you work on the project)

  You know it's active when your terminal prompt shows `(venv)` at the start.

**Type hints**
- *Definition*: annotations that say what type a function expects in and returns, without enforcing it at runtime.
- *Why it matters*: makes code self-documenting and lets your editor/tools catch mistakes before you run the code.
- *Example*:
```python
  def add(a: int, b: int) -> int:
      return a + b
```
  Here, `a` and `b` should be integers, and the function returns an integer. If you pass a string by mistake, your editor will warn you.

**requirements.txt**
- *Definition*: a text file listing your project's packages and exact versions.
- *Why it matters*: anyone (including future-you on a new laptop) can recreate your exact environment with one command.
- *Example*:

pip freeze > requirements.txt # generate it from what's currently installed
pip install -r requirements.txt # recreate the environment elsewhere


---

## Day 3 — LLM access

**Hosted API vs. local model**
- *Definition*: a **hosted** model (e.g., Google Gemini) runs on Google's servers — you send a request over the internet and get a response back. A **local** model (e.g., via Ollama) runs directly on your own laptop's CPU/GPU.
- *Why it matters*: hosted = more powerful, needs internet, costs money past free tier. Local = free, private, works offline, but limited by your hardware.
- *Example*: `call_hosted()` sends a request to `client.models.generate_content(...)` (Google's servers); `call_local()` sends a request to `http://localhost:11434` (your own machine, Ollama's local server).

**.env + .gitignore**
- *Definition*: `.env` is a file holding secret values (like API keys) as `KEY=value` pairs. `.gitignore` tells Git which files to never track.
- *Why it matters*: API keys pushed to a public GitHub repo can be stolen and abused (people scan GitHub for exposed keys within minutes). Keeping `.env` out of Git prevents that.
- *Example*:
.env

GOOGLE_API_KEY=abc123...

.gitignore

.env

  In code: `load_dotenv()` reads `.env` into memory, then `os.environ["GOOGLE_API_KEY"]` retrieves it — the key never appears in your actual script.

---

## Day 4 — Real LLM calls, error handling, retry

**Messages / roles**
- *Definition*: LLM APIs let you separate a **system** instruction (how the AI should behave) from the **user** message (what's being asked).
- *Why it matters*: lets you set consistent behavior (tone, format, constraints) independent of whatever the user asks each time.
- *Example*:
```python
  system_instruction = "You are a concise summarizer."
  # vs. the actual content being summarized:
  contents = text
```

**Temperature**
- *Definition*: a number (usually 0–1+) controlling how random/creative the model's output is.
- *Why it matters*: low temperature = consistent, factual, repeatable answers (good for summaries, classification). High temperature = varied, creative answers (good for brainstorming).
- *Example*: `temperature=0.2` for a summarizer (you want the same article summarized the same way each time) vs. `temperature=0.9` for a brainstorming tool (you want different ideas each run).

**Tokens & max_output_tokens**
- *Definition*: a token is roughly ¾ of a word — the unit models read and write in. `max_output_tokens` caps how many tokens the response can use.
- *Why it matters*: too low a cap can cut off the answer entirely — this bit you on Day 4! Reasoning models (like `gemini-3.6-flash`) use tokens for internal "thinking" before the visible answer, so they need a bigger budget than non-reasoning models.
- *Example*: you set `max_output_tokens=300`, but the model spent 288 tokens "thinking" and only had 12 left for the real answer → truncated output. Raising it to `1024` fixed it.

**Retry logic**
- *Definition*: wrapping an API call in a loop that catches failures and tries again a few times before giving up.
- *Why it matters*: networks blip, APIs rate-limit, servers hiccup — production code shouldn't crash on the first failure.
- *Example*:
```python
  for attempt in range(1, max_retries + 1):
      try:
          return call_the_api()
      except Exception as e:
          if attempt == max_retries:
              raise
          time.sleep(2 * attempt)  # wait a bit longer each retry
```

---

## Day 5 — Structured output

**Structured output (JSON + pydantic validation)**
- *Definition*: instead of asking the model for free-form text, you define an exact schema (using pydantic) and ask the model to return data matching that shape. The SDK validates the response against your schema automatically.
- *Why it matters*: free-form text is fine for a human to read, but breaks any code that needs to *use* the output (e.g., store it in a database, feed it to another function). Structured output makes LLM responses reliable enough to plug into real systems.
- *Example*:
```python
  class Summary(BaseModel):
      title: str
      bullets: list[str]
      sentiment: str

  response = client.models.generate_content(
      ...,
      config=types.GenerateContentConfig(
          response_mime_type="application/json",
          response_schema=Summary,
      ),
  )
  result = response.parsed  # already a validated Summary object, not raw text
```
  If the model's output didn't match the schema (wrong types, missing fields), pydantic would raise a validation error instead of your code silently breaking later.

---

## Day 6 — Prompting basics

**Principle 1: Write clear instructions**
- *Definition*: separate instructions from content using delimiters (triple quotes `"""`, backslashes, angle brackets `< >`, XML tags), and ask for structured output (JSON, HTML) when the response needs to be parsed by code.
- *Why it matters*: prevents the model from confusing your instructions with the input text, and makes output usable by downstream code instead of just human-readable.
- *Example*: `Summarize the text between the triple quotes below: """<text>"""` — unambiguous about what's instruction vs. content.

**Principle 2: Give the model time to think**
- *Definition*: break complex tasks into steps and ask the model to reason through them, rather than demanding an immediate final answer.
- *Why it matters*: reduces rushed or wrong answers, especially on multi-step problems like math or analysis.
- *Example*: "A store had 120 apples, sold 45% Monday, sold 30 more Tuesday. Think step by step before giving the final answer." → model worked through 120 → 54 sold → 66 left → 30 sold → 36 final, instead of guessing a number directly.

**Iterative prompt development**
- *Definition*: write a first-draft prompt → check the result → identify what's wrong (length, tone, format, missing info) → refine → repeat.
- *Why it matters*: the first prompt rarely gives the ideal output — treating prompting as an iterative process (like debugging code) gets much better results than expecting perfection on the first try.
- *Example*: common fixes include clarifying instructions, giving more "thinking room," or adding an example (few-shot) to steer the format/tone.

---

## Day 7 — Prompting patterns

**Chain-of-thought**
- *Definition*: instructing the model to reason through intermediate steps before producing a final answer, rather than jumping straight to the output.
- *Why it matters*: forces more careful reasoning, which improves accuracy on anything requiring analysis, not just simple lookup.
- *Example*: "First, identify the main topic and key points. Then produce the JSON summary." — vs. just "Summarize this as JSON," which skips the reasoning step.

**Role prompting**
- *Definition*: assigning the model a persona or expertise level in the system instruction, shaping its tone and judgment.
- *Why it matters*: "You are an expert news editor" produces more careful, professional output than a generic instruction — the model calibrates its behavior to the assigned role.
- *Example*: `"You are an expert news editor with 15 years of experience..."` vs. plain `"You are a summarizer."`

**Delimiters for multi-part prompts**
- *Definition*: using triple quotes, XML tags, etc. to clearly mark where instructions end and content begins.
- *Why it matters*: prevents the model from confusing your instructions with the text it's processing — especially important as prompts get longer/more complex.
- *Example*: `contents=f'"""{text}"""'` — wraps the raw article text so it's unambiguous what's "the content to summarize" vs "the instruction."

---

## Day 8 — Classification + schema validation

**Enums for fixed categories**
- *Definition*: a Python `Enum` restricts a field to an exact, predefined set of values — the model (and pydantic) can't produce anything outside that set.
- *Why it matters*: classification tasks need a closed set of labels (e.g., billing/technical/general/complaint) — free text would let the model invent inconsistent category names.
- *Example*:
```python
  class Category(str, Enum):
      BILLING = "billing"
      TECHNICAL = "technical"
```

**Handling validation errors separately from API errors**
- *Definition*: catching `ValidationError` (bad/unexpected shape from the model) as a distinct case from general exceptions (network issues, API failures).
- *Why it matters*: these are different failure modes needing different handling — a validation error might mean you need a better prompt, while a network error just needs a retry.
- *Example*: `except ValidationError as e:` before the general `except Exception as e:`.

**Confidence scores as a review signal**
- *Definition*: asking the model to self-report how certain it is, alongside its answer.
- *Why it matters*: in production, low-confidence classifications can be routed to a human for review instead of auto-processed — this is how real triage systems avoid silently mishandling ambiguous cases.
- *Example*: an ambiguous refund complaint got confidence 0.92, notably lower than clear-cut tickets (0.98) — a useful threshold to flag for review.

---

## Day 9 — Function/tool calling

**Tool calling**
- *Definition*: describing a real function to the model (name, purpose, parameters) so it can decide, on its own, when to call it — the model itself never executes the function; it just tells your code what to call and with what arguments.
- *Why it matters*: LLMs are unreliable at things like precise math, live data lookups, or actions in the real world (sending an email, querying a database). Tool calling lets the model delegate those to code you control and trust.
- *Example*: asked "347 × 892 − 1500?", the model returned `function_call: calculate({'expression': '347 * 892 - 1500'})` instead of guessing the answer itself — your real `calculate()` function computed it, and the model's final response used that actual result.

**The tool-calling flow (4 steps)**
1. Send the prompt + tool description to the model.
2. Model responds with a `function_call` (name + arguments) instead of a direct answer, if it decides a tool is needed.
3. Your code runs the real function.
4. You send the function's result back to the model, which produces a final natural-language answer incorporating it.
- *Why it matters*: this exact loop — model decides → your code executes → model responds — is the foundation of every "agent" from Week 7 onward. An agent is essentially this loop repeated with multiple tools available.

---

## Day 10 — Triage core
*(to fill in once we finish today)*

---
## Day 10 — Triage core + real-world API limits

**Combining classification + generation in one schema**
- *Definition*: a single pydantic schema can mix fixed-category fields (category, priority, sentiment as Enums) with free-text generative fields (draft_reply) in one response.
- *Why it matters*: real applications often need both — structured data for routing/logging, and natural text for the human-facing output — and getting both in one call is more efficient than two separate requests.

**Differentiating error types for retry strategy**
- *Definition*: not all API failures are the same — rate limits (429), server overload (503), and daily quota exhaustion all need different handling.
- *Why it matters*: a 503 is worth retrying with backoff (the server will recover). A daily quota error (429 with "PerDay" in the quota ID) will NOT resolve no matter how many times or how long you retry — you have to wait for the reset window or switch models/providers. Recognizing this distinction prevents wasted retries and wasted time.
- *Example*: today's run showed both — a `PerMinute` 429 that transient backoff could theoretically fix, and later a `PerDay` 429 that no retry within the same session could resolve.



## Day 12 — Streamlit UI

**Streamlit basics: inputs, outputs, layout**
- *Definition*: Streamlit turns a plain Python script into a web app — no HTML/CSS/JS needed. Widgets like `st.text_area()` and `st.button()` handle input; `st.write()`, `st.metric()`, `st.columns()` handle output and layout.
- *Why it matters*: this is what turns a script only you can run into something anyone can open in a browser and use — the difference between a personal tool and a shareable portfolio piece.
- *Example*:
```python
  ticket_text = st.text_area("Ticket text")   # input
  if st.button("Triage Ticket"):              # only runs on click, not every keystroke
      result = triage(ticket_text)            # reuse existing logic
      col1, col2, col3 = st.columns(3)        # layout
      col1.metric("Category", result.category.value)  # output
```
  Running it: `streamlit run app.py` — auto-opens a browser tab at `localhost:8501`, and the app reloads live as you edit the file.

  ## Day 13 — Polish: error handling, guardrails, example inputs

**Graceful error handling in a UI**
- *Definition*: wrapping risky operations (like an API call) in `try/except` inside the UI layer, so failures show a user-friendly message instead of crashing the app or exposing a raw traceback.
- *Why it matters*: real users will hit real failures (bad API key, network issue, rate limit) — a crashed app or a scary stack trace looks broken and unprofessional; a calm error message looks intentional.
- *Example*: tested by temporarily breaking the API key — confirmed the app showed "Something went wrong... Please try again" instead of an unhandled exception, with technical details available but de-emphasized underneath.

**Input guardrails**
- *Definition*: validating user input before sending it to the model — checking for empty input, excessive length, etc.
- *Why it matters*: prevents wasted API calls (and quota) on obviously invalid input, and gives immediate feedback instead of a confusing delay or error.
- *Example*: empty ticket text → warning shown immediately, no API call made at all.

**Example inputs via `st.session_state`**
- *Definition*: pre-filled example buttons that populate the input field when clicked, using Streamlit's session state to control widget values.
- *Why it matters*: lowers the barrier for someone trying your app for the first time — they can see it work before writing their own input, which matters a lot for a portfolio demo.

## Day 14 — Deploy (Streamlit Community Cloud)

**Deploying with secrets management**
- *Definition*: Streamlit Community Cloud deploys directly from a GitHub repo, auto-redeploying on every push to `main`. Secrets (like API keys) are stored separately in the platform's encrypted secrets manager (`st.secrets`), never in your code or `.env` (which stays local-only, gitignored).
- *Why it matters*: this is how real deployed apps handle secrets — the deployment platform, not your codebase, holds the sensitive credentials.
- *Example*: `get_api_key()` checks `st.secrets["GOOGLE_API_KEY"]` first (works on Streamlit Cloud), falling back to `os.environ["GOOGLE_API_KEY"]` (works locally via `.env`) — one function, works in both environments.