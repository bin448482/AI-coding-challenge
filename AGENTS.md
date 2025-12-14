# Repository Guidelines

## Project Structure

- `docs/`: Challenge brief and design notes (start here).
- `main.py`: CLI entry point for the JD↔CV evaluator.
- `jd_resume_evaluator/`: Small modules (input prep, prompting, engines, schema validation).
- `job_box/`: Job descriptions (Markdown).
- `resume_box/`: Candidate CVs/resumes (Markdown).
- `outputs/`: Generated evaluation results (timestamped; gitignored).
- `.venv/`: Local Python virtual environment (ignored by Git via `.gitignore`).

Primary design doc: `docs/jd_resume_evaluator_implementation.md`.

## Setup, Run, and Common Commands

- Create venv: `python3 -m venv .venv`
- Activate (bash/zsh): `source .venv/bin/activate`
- Install deps (once `requirements.txt` exists): `python3 -m pip install -r requirements.txt`
- Run entrypoint: `python3 main.py --job <path> --cv <path> --engine mock`
- Preview input budgets/truncation (no model calls): `python3 main.py --job <path> --cv <path> --dry-run`

Keep generated outputs out of version control unless they are fixtures/examples.

## Coding Style & Naming

- Python: 4-space indentation, explicit imports, small single-purpose modules.
- Prefer type hints for public functions and dataclasses for structured data.
- File/module naming: `snake_case.py`; CLI args in `kebab-case` when applicable.
- If you add formatters/linters, prefer `ruff` + `black` and document the exact commands in this file.

## Testing Guidelines

There is no test suite yet. If you add one:

- Use `pytest` and place tests under `tests/` mirroring module names (e.g., `tests/test_data_loader.py`).
- Keep tests fast and deterministic; mock external LLM calls.
- Provide a single command: `pytest -q`.

## Commit & Pull Request Guidelines

Current Git history is minimal (e.g., `配置初始环境`). Keep commits small and readable:

- Subject line: short, imperative, and consistent (Chinese or English is fine).
- Include context in the body when changing prompts, model behavior, or output formats.

PRs should include: a brief description, how to run, example input/output (Markdown), and any config changes.

## Security & Configuration

- Never commit secrets. Use `.env` locally and keep `.env.example` up to date if you introduce new variables (API keys, model names, etc.).
