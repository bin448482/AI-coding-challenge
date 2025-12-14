from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from enum import Enum

from jd_resume_evaluator.json_parse import parse_json_object
from jd_resume_evaluator.prompting import build_system_prompt, build_user_prompt
from jd_resume_evaluator.text_prep import PreparedInputs


class EngineName(str, Enum):
    mock = "mock"
    openai = "openai"


@dataclass(frozen=True)
class EngineResult:
    report_dict: dict
    raw_output: str | None


def evaluate_with_engine(
    *,
    engine: EngineName,
    prepared: PreparedInputs,
    model: str,
    temperature: float,
    openai_base_url: str | None = None,
    openai_api_key: str | None = None,
) -> tuple[dict, str | None]:
    if engine == EngineName.mock:
        result = _evaluate_mock(prepared)
        return result.report_dict, result.raw_output

    if engine == EngineName.openai:
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for --engine openai.")
        if not openai_base_url:
            raise ValueError("openai_base_url is required for --engine openai.")
        result = _evaluate_openai_http(
            prepared=prepared,
            model=model,
            temperature=temperature,
            base_url=openai_base_url.rstrip("/"),
            api_key=openai_api_key,
        )
        return result.report_dict, result.raw_output

    raise ValueError(f"Unknown engine: {engine}")


def _evaluate_openai_http(
    *,
    prepared: PreparedInputs,
    model: str,
    temperature: float,
    base_url: str,
    api_key: str,
) -> EngineResult:
    system = build_system_prompt()
    user = build_user_prompt(prepared)

    payload = {
        "model": model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }

    req = urllib.request.Request(
        url=f"{base_url}/chat/completions",
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI HTTPError {e.code}: {detail}") from e

    parsed = json.loads(body)
    content = parsed["choices"][0]["message"]["content"]

    report_dict = parse_json_object(content)
    return EngineResult(report_dict=report_dict, raw_output=content)


def _evaluate_mock(prepared: PreparedInputs) -> EngineResult:
    jd = prepared.jd_text
    cv = prepared.cv_text

    jd_keywords = _extract_keywords(jd, max_keywords=12)
    hits = []
    misses = []
    for kw in jd_keywords:
        evidence = _first_line_containing(cv, kw) or _first_line_containing(jd, kw)
        if evidence:
            hits.append((kw, evidence))
        else:
            misses.append(kw)

    found_ratio = (len(hits) / max(len(jd_keywords), 1)) if jd_keywords else 0.0
    overall_score = int(round(45 + 55 * found_ratio))

    strengths = [{"claim": f"Has signal for: {kw}", "evidence_quotes": [quote]} for kw, quote in hits[:8]]
    gaps = [
        {
            "gap": f"No clear evidence for: {kw}",
            "impact": "May not meet one or more JD expectations; validate in interview or with work samples.",
            "evidence_quotes": [
                _first_line_containing(jd, kw)
                or " ".join([ln.strip() for ln in jd.splitlines() if ln.strip()][:2]).strip()
            ],
        }
        for kw in misses[:8]
    ]

    follow_ups = [f"Can you provide specific examples demonstrating {kw}?" for kw in misses[:5]]
    while len(follow_ups) < 5:
        follow_ups.append("What was your most impactful recent project, and what metrics improved?")

    risk_flags = []
    if prepared.meta.truncation_notes:
        risk_flags.append("Inputs were truncated/excerpted; assessment may miss evidence outside included text.")
    if not jd_keywords:
        risk_flags.append("JD keyword extraction found few signals; scoring may be unreliable.")

    score_breakdown = {
        "must_haves": int(round(60 * found_ratio)),
        "nice_to_haves": int(round(40 * found_ratio)),
        "llm_engineering": int(round(50 * found_ratio)),
        "mlops": int(round(50 * found_ratio)),
        "system_design": int(round(50 * found_ratio)),
        "impact_and_ownership": int(round(50 * found_ratio)),
    }

    report = {
        "overall_score": max(0, min(100, overall_score)),
        "recommend_interview": overall_score >= 70,
        "score_breakdown": score_breakdown,
        "strengths": strengths or [{"claim": "Insufficient evidence in provided text.", "evidence_quotes": [jd[:120]]}],
        "gaps": gaps or [],
        "follow_up_questions": follow_ups,
        "risk_flags": risk_flags,
    }
    return EngineResult(report_dict=report, raw_output=None)


_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9_+.#/-]{1,30}")


def _extract_keywords(text: str, max_keywords: int) -> list[str]:
    # Prefer backticked keywords if present.
    backticked = re.findall(r"`([^`]{1,40})`", text)
    candidates = [c.strip() for c in backticked if c.strip()]

    # Otherwise, fall back to token-ish words.
    if not candidates:
        candidates = _TOKEN.findall(text)

    # Normalize and de-duplicate while keeping order.
    seen: set[str] = set()
    keywords: list[str] = []
    for cand in candidates:
        key = cand.strip()
        if not key:
            continue
        if key.lower() in {"the", "and", "with", "for", "you", "your"}:
            continue
        if key.lower() in seen:
            continue
        seen.add(key.lower())
        keywords.append(key)
        if len(keywords) >= max_keywords:
            break
    return keywords


def _first_line_containing(text: str, needle: str) -> str | None:
    needle_lower = needle.lower()
    for line in text.splitlines():
        if needle_lower in line.lower():
            cleaned = line.strip()
            if cleaned:
                return cleaned
    return None
