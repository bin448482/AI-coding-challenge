# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **AI Coding Challenge** to build a prototype that screens candidates against job descriptions. The goal is to produce a short screening summary that helps hiring managers understand candidate fit, key risks, and interview focus areas.

**Timebox:** 30 minutes total for implementation.

**Key files:**
- `docs/AI_Coding_Challenge_First_Principles_Engineer.md` — Challenge brief and evaluation criteria
- `AGENTS.md` — Repository guidelines for coding style, testing, and Git practices
- `job_box/` — Place job descriptions here (currently empty)
- `resume_box/` — Place candidate CVs/resumes here (Markdown examples provided)

## Architecture & Design Approach

The prototype should:

1. **Accept two inputs:** Job description and candidate CV
2. **Output a screening summary** (JSON or Markdown) containing:
   - Brief candidate summary
   - Strengths vs job requirements
   - Potential risks or gaps
   - Suggested interview questions

**Design principles:**
- Minimal viable prototype (30-minute scope)
- Use Claude or another LLM API for analysis (mocking is acceptable)
- Single-purpose, clear data flow
- Avoid over-engineering; focus on core logic

**Suggested structure (from AGENTS.md):**
```
main.py              # Entry point
data/                # Input JDs and CVs (if needed)
outputs/             # Generated screening summaries
requirements.txt     # Python dependencies
```

## Common Commands

### Setup
```bash
python3 -m venv .venv
source .venv/bin/activate      # On Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

### Run the prototype
```bash
python main.py --job <job_path> --cv <cv_path>
```

### Testing (when implemented)
```bash
pytest -q
```

## Environment & Configuration

**API Configuration:** Uses environment variables from `.env`:
- `OPENAI_API_KEY` — Your API key
- `OPENAI_BASE_URL` — API endpoint
- `OPENAI_MODEL` — Model name (e.g., gpt-5.1)
- `TEMPERATURE` — LLM parameter for response variability

**Important:** `.env` is in `.gitignore`. Never commit secrets; update `.env.example` when introducing new variables.

## Coding Standards

**From AGENTS.md:**

- **Python:** 4-space indentation, explicit imports, small single-purpose modules
- **Type hints:** Required for public functions and dataclasses
- **File naming:** `snake_case.py` for modules; `kebab-case` for CLI arguments
- **Formatters/linters:** Prefer `ruff` + `black` if adding them

**Example dataclass:**
```python
from dataclasses import dataclass

@dataclass
class ScreeningSummary:
    candidate_summary: str
    strengths: list[str]
    risks: list[str]
    interview_questions: list[str]
```

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

1. **LLM Integration:** Real API calls vs mock responses?
2. **Input Format:** File paths, JSON, or direct string input?
3. **Output Format:** JSON, Markdown, or HTML?
4. **Scope:** MVP with core screening logic, or extended analysis (e.g., skills match scoring)?
5. **Error Handling:** Minimal validation vs comprehensive checks?

Document these decisions in the code or a short README if they affect usage.

## Quick Reference

| Task | Command |
|------|---------|
| Activate venv | `source .venv/bin/activate` |
| Install deps | `pip install -r requirements.txt` |
| Run prototype | `python main.py --job <job> --cv <cv>` |
| Run tests | `pytest -q` |
| Format code | `black .` (if added) |
| Lint | `ruff check .` (if added) |

## No Test Suite Yet

As noted in AGENTS.md: there is currently no test suite. Add one only if you plan to extend the prototype significantly. Keep it simple and mock LLM calls.
