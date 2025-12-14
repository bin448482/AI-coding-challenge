from __future__ import annotations

import json

from jd_resume_evaluator.text_prep import PreparedInputs


def build_system_prompt() -> str:
    return (
        "You are a senior technical recruiter and a strict evidence-based evaluator.\n"
        "Hard rules:\n"
        "1) Do NOT invent technologies, products, employers, numbers, or achievements not present in the provided JD/CV.\n"
        "2) Every strength/gap MUST include at least one exact quote copied verbatim from the JD or CV.\n"
        "3) Output MUST be strict JSON only (no Markdown, no commentary).\n"
        "4) If the inputs look truncated/excerpted, explicitly add a risk_flag.\n"
    )


def _schema_text() -> str:
    schema = {
        "overall_score": 0,
        "recommend_interview": True,
        "score_breakdown": {
            "must_haves": 0,
            "nice_to_haves": 0,
            "llm_engineering": 0,
            "mlops": 0,
            "system_design": 0,
            "impact_and_ownership": 0,
        },
        "strengths": [{"claim": "...", "evidence_quotes": ["..."]}],
        "gaps": [{"gap": "...", "impact": "...", "evidence_quotes": ["..."]}],
        "follow_up_questions": ["..."],
        "risk_flags": ["..."],
    }
    return json.dumps(schema, ensure_ascii=False, indent=2)


def build_user_prompt(prepared: PreparedInputs) -> str:
    meta_hint = ""
    if prepared.meta.truncation_notes:
        meta_hint = (
            "Input notes (may indicate truncation/excerpts):\n- "
            + "\n- ".join(prepared.meta.truncation_notes)
            + "\n\n"
        )

    return (
        f"{meta_hint}"
        "Job Description (JD):\n"
        "<JD>\n"
        f"{prepared.jd_text}"
        "</JD>\n\n"
        "Candidate CV/Resume:\n"
        "<CV>\n"
        f"{prepared.cv_text}"
        "</CV>\n\n"
        "Return JSON with exactly this schema (field names must match):\n"
        f"{_schema_text()}\n\n"
        "Scoring guidance:\n"
        "- overall_score: integer 0..100\n"
        "- Provide 5+ follow_up_questions focused on uncertainties.\n"
        "- Keep evidence_quotes short (1-3 sentences each) and copied verbatim.\n"
    )

