from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from jd_resume_evaluator.engines import EngineName, evaluate_with_engine
from jd_resume_evaluator.report import EvaluationReport, validate_report_dict
from jd_resume_evaluator.text_prep import InputBudgets, PreparedInputs, prepare_inputs


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate JD ↔ CV fit and output a structured screening report."
    )
    parser.add_argument("--job", required=True, help="Path to the job description (Markdown/text).")
    parser.add_argument("--cv", required=True, help="Path to the candidate CV/resume (Markdown/text).")
    parser.add_argument(
        "--engine",
        default="mock",
        choices=[e.value for e in EngineName],
        help="Evaluation engine: mock (offline) or openai (Chat Completions HTTP).",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("MODEL", "gpt-4o-mini"),
        help="Model name (used by LLM engines).",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="LLM temperature (LLM engines only).",
    )
    parser.add_argument(
        "--openai-base-url",
        default=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        help="Base URL for OpenAI-compatible API (LLM engines only).",
    )
    parser.add_argument(
        "--openai-api-key",
        default=os.environ.get("OPENAI_API_KEY"),
        help="OpenAI API key (or set OPENAI_API_KEY).",
    )
    parser.add_argument(
        "--max-jd-chars",
        type=int,
        default=60_000,
        help="Max characters to include from JD after compression/truncation.",
    )
    parser.add_argument(
        "--max-cv-chars",
        type=int,
        default=140_000,
        help="Max characters to include from CV after compression/truncation.",
    )
    parser.add_argument(
        "--max-prompt-chars",
        type=int,
        default=220_000,
        help="Max total prompt characters; inputs are compressed/truncated to fit.",
    )
    parser.add_argument(
        "--outline-if-needed",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="When inputs exceed budgets, extract headings/bullets before truncation.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print prompt/input size stats and exit without calling any engine.",
    )
    parser.add_argument(
        "--out-dir",
        default="outputs/jd_resume_eval",
        help="Directory to write outputs into (timestamped subdir).",
    )
    return parser.parse_args(argv)


def _write_outputs(out_dir: Path, prepared: PreparedInputs, report: EvaluationReport, raw: str | None) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    report_path = out_dir / "report.json"
    report_path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    meta_path = out_dir / "input_meta.json"
    meta_path.write_text(
        json.dumps(asdict(prepared.meta), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    if raw is not None:
        (out_dir / "raw_output.txt").write_text(raw, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    budgets = InputBudgets(
        max_jd_chars=args.max_jd_chars,
        max_cv_chars=args.max_cv_chars,
        max_prompt_chars=args.max_prompt_chars,
        outline_if_needed=bool(args.outline_if_needed),
    )
    prepared = prepare_inputs(Path(args.job), Path(args.cv), budgets=budgets)

    if args.dry_run:
        print(json.dumps(asdict(prepared.meta), ensure_ascii=False, indent=2))
        return 0

    engine = EngineName(args.engine)
    report_dict, raw_output = evaluate_with_engine(
        engine=engine,
        prepared=prepared,
        model=args.model,
        temperature=float(args.temperature),
        openai_base_url=args.openai_base_url,
        openai_api_key=args.openai_api_key,
    )
    validate_report_dict(report_dict)
    report = EvaluationReport.from_dict(report_dict)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.out_dir) / timestamp
    _write_outputs(out_dir, prepared=prepared, report=report, raw=raw_output)

    print(str(out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
