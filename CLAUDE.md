# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **AI Coding Challenge** prototype that evaluates the fit between a Job Description (JD) and a Candidate CV/Resume, producing a strict JSON screening report for a hiring manager (fit, risks/unknowns, and interview focus areas).

**Timebox:** 30 minutes total for implementation.

**Key files:**
- `docs/AI_Coding_Challenge_First_Principles_Engineer.md` — Challenge brief and evaluation criteria
- `AGENTS.md` — Repository guidelines for coding style, testing, and Git practices
- `docs/jd_resume_evaluator_implementation.md` — Implementation notes (schema, prompt rules, input budgets)
- `main.py` — CLI entry point
- `jd_resume_evaluator/` — Implementation modules
- `job_box/` — Job descriptions (Markdown)
- `resume_box/` — Candidate CVs/resumes (Markdown)
- `outputs/` — Generated reports (timestamped; gitignored)

## Architecture & Design Approach

The implementation is intentionally small and auditable:

1. `main.py` reads `--job` and `--cv`, prepares inputs with explicit size budgets, then calls an evaluation engine.
2. Engines:
   - `mock` (offline): deterministic rule-based report (useful for quick iteration and CI-like sanity checks).
   - `openai` (network): OpenAI-compatible `POST /v1/chat/completions` using strict JSON-only prompting.
3. Output is always strict JSON with schema validation before writing `report.json`.

Core modules:
- `jd_resume_evaluator/text_prep.py`: normalization + input budgets + outline extraction + truncation metadata
- `jd_resume_evaluator/prompting.py`: JSON-only prompts + schema scaffold + truncation hints
- `jd_resume_evaluator/engines.py`: `mock` and `openai` implementations
- `jd_resume_evaluator/json_parse.py`: best-effort JSON object extraction
- `jd_resume_evaluator/report.py`: schema validation + dataclasses

Design principles:
- Evidence-backed claims (each strength/gap must include quotes copied verbatim from the provided text)
- Strictly machine-parseable output (JSON only)
- Input boundary guardrails to avoid context overflow and degraded reasoning

## Common Commands

### Setup
```bash
python3 -m venv .venv
source .venv/bin/activate      # On Windows: .venv\Scripts\activate
python3 -m pip install -r requirements.txt
```

### Run the prototype
```bash
python3 main.py --job <job_path> --cv <cv_path> --engine mock
```

### Preview prompt/input size (no model calls)
```bash
python3 main.py --job <job_path> --cv <cv_path> --dry-run
```

### Testing (when implemented)
```bash
pytest -q
```

## Environment & Configuration

For the `openai` engine (network required), configure:
- `OPENAI_API_KEY` — API key
- `OPENAI_BASE_URL` — optional (defaults to `https://api.openai.com/v1`)

**Important:** `.env` is in `.gitignore`. Never commit secrets; update `.env.example` when introducing new variables.

## Input Boundary Strategy (Why it exists)

JD/CV inputs can be arbitrarily large. Overly large prompts cause:
- API errors (context overflow) or severe output degradation
- higher chance of non-JSON outputs and weaker evidence quoting

This repo uses **character budgets + explainable truncation**:
- `--max-jd-chars`, `--max-cv-chars`, `--max-prompt-chars`
- If over budget, optionally extract Markdown headings/bullets first (`--outline-if-needed`, default on)
- Always write `outputs/.../input_meta.json` containing original/used sizes and truncation notes

If any truncation happens, engines should include a `risk_flag` indicating the assessment may miss evidence outside the included excerpts.

## Coding Standards

**From AGENTS.md:**

- **Python:** 4-space indentation, explicit imports, small single-purpose modules
- **Type hints:** Required for public functions and dataclasses
- **File naming:** `snake_case.py` for modules; `kebab-case` for CLI arguments
- **Formatters/linters:** Prefer `ruff` + `black` if adding them

## Testing Guidelines

If you add tests:
- Use `pytest` and place under `tests/` (mirror module structure: `tests/test_module_name.py`)
- Keep tests fast and deterministic; mock external LLM calls
- Single command to run: `pytest -q`

## Git & Commit Practices

From AGENTS.md:

- **Subject line:** Short, imperative, consistent (Chinese or English acceptable)
- **Body:** Include context for prompt changes, model behavior, or output format changes
- **PR template:** Brief description, how to run, example I/O (Markdown), config changes noted
- **Keep commits small and readable** — current Git history is minimal

## Decision Points

When implementing, make deliberate choices about:

1. **Engine behavior:** keep `mock` deterministic; keep `openai` strict JSON-only.
2. **Budgeting:** char budgets vs token-aware budgeting (if adding token counting, document the dependency and failure modes).
3. **Evidence policy:** never claim beyond the included text; prefer follow-up questions when uncertain.
4. **Schema evolution:** change output fields carefully (it is intended for automation).

Document these decisions in the code or a short README if they affect usage.

## Quick Reference

| Task | Command |
|------|---------|
| Activate venv | `source .venv/bin/activate` |
| Install deps | `pip install -r requirements.txt` |
| Run (mock) | `python3 main.py --job <job> --cv <cv> --engine mock` |
| Dry-run budgets | `python3 main.py --job <job> --cv <cv> --dry-run` |
| Run tests | `pytest -q` |
| Format code | `black .` (if added) |
| Lint | `ruff check .` (if added) |

## No Test Suite Yet

As noted in AGENTS.md: there is currently no test suite. Add one only if you plan to extend the prototype significantly. Keep it simple and mock LLM calls.
