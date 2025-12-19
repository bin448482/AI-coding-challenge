# JD × Resume Matching Evaluator (LangChain Multi-Model Switchable) Implementation Notes

Goal: implement a minimum viable “job JD vs. resume match evaluation” script within **30 minutes**, and switch between different LLMs (OpenAI / Zhipu / Ollama) via **LangChain configuration/parameters**.

## 0. Inputs and Current State Check

The input files you mentioned were not found in the current repository (please confirm the real paths or add them to the repo):

- `docs/AI_Coding_Challenge_First_Principles_Engineer.md`
- `job_box/JD_Senior AI Engineer.md`
- `resume_box/Resume_EN_20250529.md`

This implementation assumes “two Markdown inputs (JD + Resume)”; once the file paths exist, it should run end-to-end.

## 1. Deliverables (MVP)

- Add entry point: `main.py`
  - Read: `--job <path>` + `--cv <path>`
  - Select engine: `--engine mock|openai`
  - (LLM engine) select model: `--model <name>` (OpenAI-compatible Chat Completions)
  - Outputs:
    - `outputs/jd_resume_eval/<timestamp>/report.json`
    - `outputs/jd_resume_eval/<timestamp>/input_meta.json` (includes truncation/extraction notes)
    - (Debugging on failure) `raw_output.txt` (when the model returns non-parseable content)

## 2. Key Constraints (to Avoid Hallucination and Ensure Traceability)

- Every conclusion must include **evidence**: each strength/gap includes at least one direct quote from the JD or Resume.
- Do not introduce technology brands, product names, or metrics that do not appear in the JD/resume. If inference is needed, use wording like “may / likely / needs confirmation” and put it into `follow_up_questions`.
- Output must be **strict JSON** (if parsing fails, save the raw model output to `raw_output.txt` for debugging).

## 3. Output Schema (v0)

Fixed JSON structure (field names are fixed for automation and multi-model comparison):

```json
{
  "overall_score": 0,
  "recommend_interview": true,
  "score_breakdown": {
    "must_haves": 0,
    "nice_to_haves": 0,
    "llm_engineering": 0,
    "mlops": 0,
    "system_design": 0,
    "impact_and_ownership": 0
  },
  "strengths": [
    {"claim": "...", "evidence_quotes": ["..."]}
  ],
  "gaps": [
    {"gap": "...", "impact": "...", "evidence_quotes": ["..."]}
  ],
  "follow_up_questions": ["..."],
  "risk_flags": ["..."]
}
```

Notes:
- `overall_score`: 0–100 (integer)
- `score_breakdown.*`: 0–100 (integer), to explain how the overall score is composed
- `evidence_quotes`: short quotes from the JD or Resume (recommended 1–3 sentences per item)

## 4. Model/Engine Selection (Implementation Strategy)

For MVP and portability, implement two engines first:

- `mock`: no external APIs; generate structured reports via simple rules (for local runs and regression)
- `openai`: call a real model via OpenAI-compatible `POST /v1/chat/completions`

Common environment variables for the LLM engine:

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL` (default: `https://api.openai.com/v1`)

Recommended defaults:
- `temperature=0.0` (more stable for evaluation use cases)

## 5. Prompt (v0, single-call)

### System
- Role: senior technical recruiter + evidence-strict evaluator
- Hard rules:
  - No hallucinated technologies/products/numbers
  - Every conclusion must cite source text
  - Output must be strict JSON (no extra text)

### User
Contains three parts:
1) JD full text (paste in full)
2) Resume full text (paste in full)
3) Output schema and scoring rubric (the JSON fields above + scoring dimension explanations)

## 6. Execution Flow (30-minute delivery)

1) Read the `--jd/--resume` text
2) `load_runtime_config()` (ensure provider credentials are available)
3) `make_chat_model(--model, temperature)` (switch between LLMs)
4) Build the prompt and call `llm.invoke(...)` once
5) Parse JSON:
   - Success: write `report.json`
   - Failure: write `raw_output.txt` and return a non-zero exit code

## 7. Commands and Acceptance

### Setup (one-time)
```bash
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

### Run (examples)
```bash
python3 main.py \
  --job "job_box/JD_Senior AI Engineer.md" \
  --cv "resume_box/Resume_EN_20250529.md" \
  --engine "mock"
```

(Optional) real LLM:
```bash
export OPENAI_API_KEY="..."
python3 main.py \
  --job "job_box/JD_Senior AI Engineer.md" \
  --cv "resume_box/Resume_EN_20250529.md" \
  --engine "openai" \
  --model "gpt-4o-mini" \
  --temperature 0
```

### Acceptance criteria (v0)
- Generates `report.json` and it can be parsed by `python -c 'import json; json.load(open(...))'`
- Every item in `strengths/gaps` contains non-empty `evidence_quotes`
- Outputs at least 5 `follow_up_questions` (for interview follow-ups)

## 8. Risks and Quick Fixes

- Model outputs non-JSON: repeat “output JSON only” in the prompt, and do a lightweight correction in code (e.g., slice from the first `{` to the last `}`).
- Insufficient evidence: put “every conclusion must include quotes” into system, and retry once on schema validation failure (max 1 retry to avoid timeouts).
- Schema drift across models: strict validation; fail fast on missing fields and save `raw_output.txt`.

## 9. Input Budgets (Prompt Size Budget) and Truncation Strategy

In reality, JDs/resumes can be very long (especially with project details, attachments, or portfolios/links). Oversized inputs cause two classes of problems:

1) **Exceed the model context window**: hard errors or severely degraded output
2) **Even if within context**: attention becomes diluted, evidence quality drops, and JSON structure is more likely to drift

So the implementation should include “budgets + explainable truncation”:

- `--max-jd-chars`: max JD characters (default 60,000)
- `--max-cv-chars`: max CV characters (default 140,000)
- `--max-prompt-chars`: total prompt budget (default 220,000, including schema/rules overhead)
- `--outline-if-needed / --no-outline-if-needed`:
  - If over budget, first extract “headings/bullets” (Markdown headings + bullets) as a **traceable excerpt**
  - If still over budget, hard truncate

The run will generate `input_meta.json`, including:

- original character counts and used character counts
- which extraction/truncation steps happened
- estimated prompt character count

Suggested acceptance checks (strongly tied to output quality):

- When any truncation/extraction occurs, `risk_flags` should clearly warn that “some evidence may be missing”
- `evidence_quotes` must come from **the text actually provided to the model** (otherwise it’s non-traceable)

Debugging suggestions:

- Use `--dry-run` first to inspect character counts/truncation, then decide whether to increase budgets or switch to a two-stage pipeline.

## 9. Next Steps (beyond 30 minutes, recommended)

- Add `--multi-model`: run multiple models on the same JD/resume and compare outputs side-by-side (helps choose an evaluation model)
- Introduce a two-stage pipeline (fact extraction → scoring alignment) to reduce hallucinations and omissions
- Move rubric/field definitions into a YAML config (similar to `latest_resumes/prompt_config.yaml`) to make evaluation dimensions configurable
