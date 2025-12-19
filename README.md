# JD × Resume Evaluator (Evidence-Based Screening Report)
A small, auditable JD↔CV matching evaluator: generates **strict JSON** screening reports under a controlled input budget, suitable for automated comparison and human review.

## Interview note: about the 30-minute time limit
The “finish in 30 minutes” constraint mentioned in the interview video felt tight to me. Even when using AI-assisted programming, I don’t treat AI as just a code-writing tool; I integrate it into a full software engineering workflow (requirements clarification, solution design, solution review, test-case design and review, implementation, code review, acceptance, and documentation maintenance). In practice, I also often use a “cross-review” approach: for example, use Claude to explore alternative designs (it tends to surface unexpected ideas), then combine that with GPT for consistency and feasibility checks, and make trade-offs based on real needs. Because model reasoning and multi-turn dialog take time, a single round trip often costs ~6–7 minutes; once you add reading, understanding, and human review, a few iterations can easily exceed 30 minutes.

Also, I did make a few small omissions/mistakes in the video, which I attribute to time pressure. Since the requirement was explicitly to complete it within 30 minutes, I treated “deliverable within 30 minutes” as the primary constraint when planning, and prioritized safer, faster-to-implement approaches over deeper design and validation.

I typically break development into an explicit “artifact chain”, and try to make every step **human-reviewable and post-mortem friendly**:
- Requirements analysis → requirements review (identify unclear points / items to confirm) → implementation doc → implementation doc review → test-case doc → test-case doc review → code implementation → test writing → code review → functionality vs. requirements alignment check → documentation completeness check

What I care about more is that every artifact produced during delivery should be reviewable and traceable (not only code, but also requirements/design/test cases/acceptance conclusions), and that maintenance/debugging/new feature work should remain possible without relying on AI. That’s why I mentioned documentation maintenance at the end of the video: it helps both future humans and AI pick up the context and understand the trade-offs made in this build.

## Background / Problem
- Screening JDs and resumes often relies on subjective judgment, making conclusions hard to trace and review (“Why do we think it matches / doesn’t match?”).
- If you paste the full JD+CV into an LLM, common issues include:
  - Oversized inputs causing context overflow or degraded outputs (non-JSON, schema drift, missing citations).
  - Unstable evidence references: conclusions that sound plausible but can’t be located in the text.
- Traditional keyword matching can do coarse filtering, but struggles to produce structured “risks / follow-ups / evidence chains”, and it’s hard to explain the scoring basis.

## Solution
- Centered on **evidence-first + structured output**: every strength/gap must include source quotes (evidence quotes), producing a fixed-schema JSON report.
- Stability via **input budgets + explainable truncation**: enforce character budgets for JD/CV and an overall prompt budget; when over budget, extract headings/bullets first, then hard-truncate, and write truncation metadata to `input_meta.json`.
- Key trade-offs:
  - **Parsing and traceability first** (strict JSON + schema validation), then “analysis depth”.
  - A `mock` engine for offline regression and fast iteration; a real LLM via the `openai` engine (OpenAI-compatible Chat Completions).

## Architecture
- Overall architecture: a single-process CLI tool that takes two Markdown/text files and writes structured evaluation outputs into a timestamped directory.
- Module breakdown:
  - `main.py`: argument parsing, input prep, engine invocation, schema validation, and writing outputs
  - `jd_resume_evaluator/text_prep.py`: normalization, budgeting, outline extraction, truncation, and metadata
  - `jd_resume_evaluator/prompting.py`: JSON-only prompts, schema scaffold, and truncation note injection
  - `jd_resume_evaluator/engines.py`: `mock` (offline) and `openai` (network) engines
  - `jd_resume_evaluator/json_parse.py`: tolerant JSON object extraction from model output
  - `jd_resume_evaluator/report.py`: output schema validation and data structures
- Data flow / call chain (text version):
  1) `main.py` reads `--job/--cv` → `prepare_inputs()` normalizes + truncates → returns `PreparedInputs + meta`
  2) `evaluate_with_engine()`:
     - `mock`: generate a report dict based on JD keywords and CV matches
     - `openai`: build system/user prompts → `POST /v1/chat/completions` → parse JSON object
  3) `validate_report_dict()` strictly validates the schema → write `outputs/.../report.json` and `input_meta.json`

## Key Features
- [x] `mock` engine (works offline; great for quick regression)
- [x] `openai` engine (OpenAI-compatible Chat Completions)
- [x] Strict JSON output + schema validation (missing fields / wrong types fail fast)
- [x] Input budgets and explainable truncation (outline extraction + truncation + `input_meta.json`)
- [x] `--dry-run` to preview budgets and truncation (no model calls)
- [ ] Token-level budgets (more precise context control)
- [ ] Multi-model comparison runs (compare stability and consistency side-by-side)
- [ ] `pytest` tests (cover truncation, JSON extraction, schema validation, mock stability)
- [ ] Configurable rubric (YAML/JSON for scoring dimensions and weights)

## Tech Stack
| Category | Choice |
|---|---|
| Language | Python 3.12+ |
| Framework | None (stdlib only) |
| Data / Storage | Local filesystem (`outputs/`) |
| Infra / Cloud | Optional: OpenAI-compatible API (`/v1/chat/completions`) |
| Other Tools | `venv`, `pip`, JSON schema validation (custom), deterministic mock engine |

## Getting Started
### Prerequisites
- Python 3.12+
- (Optional) Access to an OpenAI-compatible endpoint and an API key (if using `--engine openai`)

### Installation
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

### Run
```bash
# Offline (recommended first)
python3 main.py --job job_box/JD_Senior\ AI\ Engineer.md --cv resume_box/Resume_EN_20250529.md --engine mock

# Preview input budgets/truncation (no model calls)
python3 main.py --job job_box/JD_Senior\ AI\ Engineer.md --cv resume_box/Resume_EN_20250529.md --dry-run
```

## Configuration
Key configuration (`openai` engine):
- `OPENAI_API_KEY`: API key
- `OPENAI_BASE_URL`: Base URL (default: `https://api.openai.com/v1`)

Example environment variables:
```bash
export OPENAI_API_KEY="..."
export OPENAI_BASE_URL="https://api.openai.com/v1"
```

Input budget options (to avoid oversized prompts):
- `--max-jd-chars` (default 60000)
- `--max-cv-chars` (default 140000)
- `--max-prompt-chars` (default 220000)
- `--outline-if-needed/--no-outline-if-needed` (enabled by default: extract headings/bullets first, then truncate)

## Usage Example
Example 1: offline quick evaluation (for iteration and regression)
```bash
python3 main.py \
  --job "job_box/JD_Senior AI Engineer.md" \
  --cv "resume_box/Resume_EN_20250529.md" \
  --engine mock
```

Example 2: real model evaluation (strict JSON-only)
```bash
export OPENAI_API_KEY="..."
python3 main.py \
  --job "job_box/JD_Senior AI Engineer.md" \
  --cv "resume_box/Resume_EN_20250529.md" \
  --engine openai \
  --model "gpt-4o-mini" \
  --temperature 0
```

Output directory structure (one timestamped directory per run):
- `outputs/jd_resume_eval/<timestamp>/report.json`: structured evaluation report
- `outputs/jd_resume_eval/<timestamp>/input_meta.json`: input sizes, truncation flags, and reasons
- `outputs/jd_resume_eval/<timestamp>/raw_output.txt`: raw model output (kept only for debugging)

## Design Highlights
- **Traceability first**: every strength/gap is tied back to source text via `evidence_quotes`, avoiding conclusions that “sound right but can’t be verified”.
- **Strict, machine-parseable output**: JSON-only prompt + tolerant `parse_json_object()` extraction + strict `validate_report_dict()` validation, preventing downstream automation from breaking on messy outputs.
- **Input budget management**:
  - Budgets are not “silent truncation”, but “explainable truncation”: `input_meta.json` records original size, used size, and reasons.
  - Outline extraction (headings/bullets) is enabled by default to preserve structured signals under the same budget and reduce the chance of randomly truncating critical paragraphs.
- **Offline baseline**: the `mock` engine provides deterministic outputs for fast development and for comparing against LLM drift (more maintainable than “fully model-dependent” systems).

## Roadmap
- [ ] Token-level budgets and context estimation (more precise control of each model’s context window)
- [ ] Multi-model parallel evaluation and diffing (stability/consistency/cost trade-offs)
- [ ] Two-stage pipeline: fact extraction → scoring alignment (reduce hallucinations, improve citation coverage)
- [ ] Configurable scoring dimensions and weights (YAML/JSON)
- [ ] `pytest` test suite and basic CI

## Status
- Current: Demo / PoC
- Best for: interview demos, prototyping, and evaluation-process design discussions
- Production note: would need token budgeting, test coverage, retry/failure handling, and clear integration boundaries with ATS/HR systems

## Author
- Role: Software Engineer / AI Engineer (prototype + engineering implementation)
- Purpose: learning and interview demo (emphasizing traceable, parseable, maintainable LLM engineering practices)
