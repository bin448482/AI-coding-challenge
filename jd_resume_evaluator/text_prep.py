from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InputBudgets:
    max_jd_chars: int
    max_cv_chars: int
    max_prompt_chars: int
    outline_if_needed: bool = True


@dataclass(frozen=True)
class InputMeta:
    jd_path: str
    cv_path: str
    jd_chars_original: int
    cv_chars_original: int
    jd_chars_used: int
    cv_chars_used: int
    prompt_chars_estimate: int
    truncation_notes: list[str]


@dataclass(frozen=True)
class PreparedInputs:
    jd_text: str
    cv_text: str
    meta: InputMeta


_BULLET_PREFIX = re.compile(r"^\s*([-*•]|\d+\.)\s+")
_HEADING_PREFIX = re.compile(r"^\s{0,3}#{1,6}\s+")


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u0000", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip() + "\n"


def _outline_extract(text: str, max_chars: int) -> str:
    lines = text.splitlines()

    picked: list[str] = []
    for line in lines:
        if _HEADING_PREFIX.match(line) or _BULLET_PREFIX.match(line):
            cleaned = line.strip()
            if cleaned:
                picked.append(cleaned)

    # Keep a small header to make truncation explicit.
    header = (
        "[NOTE] Input too large; extracted headings/bullets to fit prompt limits. "
        "Evidence quotes must come from the included excerpts.\n"
    )
    out = header + "\n".join(picked) + "\n"

    if len(out) <= max_chars:
        return out

    # Hard truncate as last resort, but avoid cutting mid-line too badly.
    truncated = out[: max_chars - 1].rsplit("\n", 1)[0] + "\n"
    return truncated


def _truncate(text: str, max_chars: int, label: str) -> tuple[str, list[str]]:
    if len(text) <= max_chars:
        return text, []
    note = f"{label} truncated from {len(text)} to {max_chars} chars."
    truncated = text[: max_chars - 1] + "\n"
    return truncated, [note]


def _apply_budgets(text: str, max_chars: int, label: str, outline_if_needed: bool) -> tuple[str, list[str]]:
    if len(text) <= max_chars:
        return text, []

    notes: list[str] = [f"{label} exceeded budget ({len(text)} > {max_chars})."]
    if outline_if_needed:
        outlined = _outline_extract(text, max_chars=max_chars)
        if len(outlined) < len(text):
            notes.append(f"{label} converted to outline excerpts.")
        text = outlined

    text, more = _truncate(text, max_chars=max_chars, label=label)
    notes.extend(more)
    return text, notes


def prepare_inputs(jd_path: Path, cv_path: Path, budgets: InputBudgets) -> PreparedInputs:
    jd_raw = _normalize(_read_text(jd_path))
    cv_raw = _normalize(_read_text(cv_path))
    if not jd_raw.strip():
        raise ValueError(f"JD file is empty after normalization: {jd_path}")
    if not cv_raw.strip():
        raise ValueError(f"CV file is empty after normalization: {cv_path}")

    jd_text, jd_notes = _apply_budgets(
        jd_raw, max_chars=budgets.max_jd_chars, label="JD", outline_if_needed=budgets.outline_if_needed
    )
    cv_text, cv_notes = _apply_budgets(
        cv_raw, max_chars=budgets.max_cv_chars, label="CV", outline_if_needed=budgets.outline_if_needed
    )

    # Very rough overhead for prompt scaffolding/schema.
    overhead = 8_000
    prompt_chars_estimate = len(jd_text) + len(cv_text) + overhead

    truncation_notes = jd_notes + cv_notes
    if prompt_chars_estimate > budgets.max_prompt_chars:
        # Scale down CV first, then JD, keeping at least 5k each.
        truncation_notes.append(
            f"Prompt estimate {prompt_chars_estimate} exceeds max_prompt_chars={budgets.max_prompt_chars}; "
            "applying additional truncation."
        )
        available = max(budgets.max_prompt_chars - overhead, 10_000)
        jd_target = max(min(len(jd_text), available // 3), 5_000)
        cv_target = max(min(len(cv_text), available - jd_target), 5_000)

        jd_text, extra = _truncate(jd_text, max_chars=jd_target, label="JD")
        truncation_notes.extend(extra)
        cv_text, extra = _truncate(cv_text, max_chars=cv_target, label="CV")
        truncation_notes.extend(extra)
        prompt_chars_estimate = len(jd_text) + len(cv_text) + overhead

    meta = InputMeta(
        jd_path=str(jd_path),
        cv_path=str(cv_path),
        jd_chars_original=len(jd_raw),
        cv_chars_original=len(cv_raw),
        jd_chars_used=len(jd_text),
        cv_chars_used=len(cv_text),
        prompt_chars_estimate=prompt_chars_estimate,
        truncation_notes=truncation_notes,
    )
    return PreparedInputs(jd_text=jd_text, cv_text=cv_text, meta=meta)
