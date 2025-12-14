from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvidenceBackedClaim:
    claim: str
    evidence_quotes: list[str]


@dataclass(frozen=True)
class Gap:
    gap: str
    impact: str
    evidence_quotes: list[str]


@dataclass(frozen=True)
class EvaluationReport:
    overall_score: int
    recommend_interview: bool
    score_breakdown: dict[str, int]
    strengths: list[EvidenceBackedClaim]
    gaps: list[Gap]
    follow_up_questions: list[str]
    risk_flags: list[str]

    @staticmethod
    def from_dict(data: dict) -> "EvaluationReport":
        strengths = [EvidenceBackedClaim(**item) for item in data.get("strengths", [])]
        gaps = [Gap(**item) for item in data.get("gaps", [])]
        return EvaluationReport(
            overall_score=int(data["overall_score"]),
            recommend_interview=bool(data["recommend_interview"]),
            score_breakdown={str(k): int(v) for k, v in data.get("score_breakdown", {}).items()},
            strengths=strengths,
            gaps=gaps,
            follow_up_questions=[str(q) for q in data.get("follow_up_questions", [])],
            risk_flags=[str(r) for r in data.get("risk_flags", [])],
        )


def validate_report_dict(data: dict) -> None:
    if not isinstance(data, dict):
        raise ValueError("Report must be a JSON object.")

    required_top = [
        "overall_score",
        "recommend_interview",
        "score_breakdown",
        "strengths",
        "gaps",
        "follow_up_questions",
        "risk_flags",
    ]
    missing = [k for k in required_top if k not in data]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    score = data["overall_score"]
    if not isinstance(score, int) or not (0 <= score <= 100):
        raise ValueError("overall_score must be an integer 0..100.")

    if not isinstance(data["recommend_interview"], bool):
        raise ValueError("recommend_interview must be boolean.")

    if not isinstance(data["score_breakdown"], dict):
        raise ValueError("score_breakdown must be an object.")

    if not isinstance(data["strengths"], list) or not isinstance(data["gaps"], list):
        raise ValueError("strengths and gaps must be arrays.")

    for idx, item in enumerate(data["strengths"]):
        if not isinstance(item, dict):
            raise ValueError(f"strengths[{idx}] must be an object.")
        if "claim" not in item or "evidence_quotes" not in item:
            raise ValueError(f"strengths[{idx}] must contain claim and evidence_quotes.")
        if not isinstance(item["evidence_quotes"], list) or not item["evidence_quotes"]:
            raise ValueError(f"strengths[{idx}].evidence_quotes must be a non-empty array.")

    for idx, item in enumerate(data["gaps"]):
        if not isinstance(item, dict):
            raise ValueError(f"gaps[{idx}] must be an object.")
        for key in ("gap", "impact", "evidence_quotes"):
            if key not in item:
                raise ValueError(f"gaps[{idx}] missing {key}.")
        if not isinstance(item["evidence_quotes"], list) or not item["evidence_quotes"]:
            raise ValueError(f"gaps[{idx}].evidence_quotes must be a non-empty array.")

    if not isinstance(data["follow_up_questions"], list) or len(data["follow_up_questions"]) < 5:
        raise ValueError("follow_up_questions must be an array with at least 5 items.")
    if not isinstance(data["risk_flags"], list):
        raise ValueError("risk_flags must be an array.")

