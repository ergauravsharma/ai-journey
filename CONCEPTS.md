# AI Journey — Concepts Log

One concept per entry: **what it is**, **why it matters**, **example**. Review before starting the next day.

---

## Day 1 — Toolchain

**Git workflow**
- *Definition*: Git tracks changes to your code over time. Three core commands move a change from your laptop to GitHub.
- *Why it matters*: gives you version history and lets you undo mistakes, and is how every real software team collaborates.
- *Example*:


  In code: `load_dotenv()` reads `.env` into memory, then `os.environ["GOOGLE_API_KEY"]` retrieves it — the key never appears in your actual script.

---

---

## Day 2 — Python refresh

**Virtual environment (venv)**
- *Definition*: an isolated copy of Python + packages, separate from your system-wide Python install.
- *Why it matters*: different projects often need different (conflicting) versions of the same package. A venv keeps them from interfering with each other.
- *Example*:

---

## Day 3 — LLM access

**Hosted API vs. local model**
- *Definition*: a **hosted** model (e.g., Google Gemini) runs on Google's servers — you send a request over the internet and get a response back. A **local** model (e.g., via Ollama) runs directly on your own laptop's CPU/GPU.
- *Why it matters*: hosted = more powerful, needs internet, costs money past free tier. Local = free, private, works offline, but limited by your hardware.
- *Example*: `call_hosted()` sends a request to `client.models.generate_content(...)` (Google's servers); `call_local()` sends a request to `http://localhost:11434` (your own machine, Ollama's local server).

**.env + .gitignore**
- *Definition*: `.env` is a file holding secret values (like API keys) as `KEY=value` pairs. `.gitignore` tells Git which files to never track.
- *Why it matters*: API keys pushed to a public GitHub repo can be stolen and abused (people scan GitHub for exposed keys within minutes). Keeping `.env` out of Git prevents that.
- *Example*: pip freeze > requirements.txt # generate it from what's currently installed
pip install -r requirements.txt # recreate the environment elsewhere

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
- *Why it matters*: too low a cap can cut off the answer entirely — this bit you today! Reasoning models (like `gemini-3.6-flash`) use tokens for internal "thinking" before the visible answer, so they need a bigger budget than non-reasoning models.
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
*(to fill in once we finish today)*

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
- *Example*: ticket3 (ambiguous — refund complaint) got confidence 0.92, notably lower than the clear-cut tickets (0.98) — a useful threshold to flag for review.