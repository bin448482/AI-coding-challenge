# JD × Resume Evaluator (Evidence-Based Screening Report)
一个小而可审计的 JD↔CV 匹配评估器：在可控输入预算下生成**严格 JSON** 的筛选报告，适合做自动化对比与人工复核。

## Background / Problem
- JD 与简历筛选经常依赖主观判断，结论难追溯、难复盘（“为什么说匹配/不匹配？”）。
- 直接把完整 JD+CV 塞给 LLM，常见问题：
  - 输入过大导致上下文溢出 / 输出退化（非 JSON、字段漂移、引用缺失）。
  - 证据引用不稳定，出现“看起来合理但无法在文本中定位”的结论。
- 传统关键词匹配能做粗筛，但很难输出结构化的“风险/追问/证据链”，也难以解释评分依据。

## Solution
- 以“**证据优先 + 结构化输出**”为核心：每条优势/缺口必须带原文引用（evidence quotes），并产出固定 schema 的 JSON 报告。
- 以“**输入边界（budget）+ 可解释裁剪**”保障稳定性：对 JD/CV 设定字符预算与总 prompt 预算，超限时先提取 headings/bullets，再做硬截断，并把裁剪信息写入 `input_meta.json`。
- 关键取舍：
  - **先保证可解析与可追溯**（严格 JSON + schema 校验）再谈“分析深度”。
  - 提供 `mock` 引擎用于离线回归与快速迭代；真实 LLM 通过 `openai` 引擎接入（OpenAI 兼容 Chat Completions）。

## Architecture
- 系统整体架构：单进程 CLI 工具，输入两份 Markdown/文本文件，输出时间戳目录下的结构化评估结果。
- 模块划分：
  - `main.py`：参数解析、输入准备、调用引擎、schema 校验、落盘输出
  - `jd_resume_evaluator/text_prep.py`：文本归一化、预算控制、outline 提取、截断与元信息
  - `jd_resume_evaluator/prompting.py`：JSON-only 提示词、schema scaffold、截断提示注入
  - `jd_resume_evaluator/engines.py`：`mock`（离线）与 `openai`（网络）引擎
  - `jd_resume_evaluator/json_parse.py`：从模型输出中提取 JSON object（容错）
  - `jd_resume_evaluator/report.py`：输出 schema 校验与数据结构
- 数据流 / 调用链路（文字版）：
  1) `main.py` 读取 `--job/--cv` → `prepare_inputs()` 做归一化与裁剪 → 得到 `PreparedInputs + meta`
  2) `evaluate_with_engine()`：
     - `mock`：基于 JD 关键词与 CV 命中行生成 report dict
     - `openai`：构造 system/user prompt → `POST /v1/chat/completions` → 解析 JSON object
  3) `validate_report_dict()` 严格校验 schema → 写入 `outputs/.../report.json` 与 `input_meta.json`

## Key Features
- [x] `mock` 引擎（离线可跑通、适合快速回归）
- [x] `openai` 引擎（OpenAI 兼容 Chat Completions）
- [x] 严格 JSON 输出 + schema 校验（字段缺失/类型不符直接失败）
- [x] 输入预算与可解释裁剪（outline 提取 + 截断 + `input_meta.json`）
- [x] `--dry-run` 预览字符预算与截断情况（不调用模型）
- [ ] token 级预算（更精确的上下文控制）
- [ ] 多模型对比运行（同一输入并排对比输出稳定性与一致性）
- [ ] `pytest` 测试（覆盖裁剪、JSON 提取、schema 校验、mock 稳定性）
- [ ] 可配置 rubric（YAML/JSON 配置评分维度与权重）

## Tech Stack
| Category | Choice |
|---|---|
| Language | Python 3.12+ |
| Framework | None（stdlib only） |
| Data / Storage | Local filesystem (`outputs/`) |
| Infra / Cloud | Optional: OpenAI-compatible API (`/v1/chat/completions`) |
| Other Tools | `venv`, `pip`, JSON schema validation (custom), deterministic mock engine |

## Getting Started
### Prerequisites
- Python 3.12+
- （可选）可访问的 OpenAI 兼容接口与 API Key（如果使用 `--engine openai`）

### Installation
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

### Run
```bash
# 离线（推荐先跑通）
python3 main.py --job job_box/JD_Senior\ AI\ Engineer.md --cv resume_box/Resume_EN_20250529.md --engine mock

# 仅查看输入预算与截断（不调用模型）
python3 main.py --job job_box/JD_Senior\ AI\ Engineer.md --cv resume_box/Resume_EN_20250529.md --dry-run
```

## Configuration
关键配置项（`openai` 引擎）：
- `OPENAI_API_KEY`：API key
- `OPENAI_BASE_URL`：Base URL（默认 `https://api.openai.com/v1`）

环境变量示例：
```bash
export OPENAI_API_KEY="..."
export OPENAI_BASE_URL="https://api.openai.com/v1"
```

输入边界相关参数（避免 prompt 过大）：
- `--max-jd-chars`（默认 60000）
- `--max-cv-chars`（默认 140000）
- `--max-prompt-chars`（默认 220000）
- `--outline-if-needed/--no-outline-if-needed`（默认开启：先抽 headings/bullets 再截断）

## Usage Example
示例 1：离线快速评估（用于迭代与回归）
```bash
python3 main.py \
  --job "job_box/JD_Senior AI Engineer.md" \
  --cv "resume_box/Resume_EN_20250529.md" \
  --engine mock
```

示例 2：真实模型评估（严格 JSON-only）
```bash
export OPENAI_API_KEY="..."
python3 main.py \
  --job "job_box/JD_Senior AI Engineer.md" \
  --cv "resume_box/Resume_EN_20250529.md" \
  --engine openai \
  --model "gpt-4o-mini" \
  --temperature 0
```

输出目录结构（每次运行一个时间戳目录）：
- `outputs/jd_resume_eval/<timestamp>/report.json`：结构化评估结果
- `outputs/jd_resume_eval/<timestamp>/input_meta.json`：输入大小、是否截断、截断原因
- `outputs/jd_resume_eval/<timestamp>/raw_output.txt`：模型原始输出（仅在需要排查时写入/保留）

## Design Highlights（重点）
- **可追溯性优先**：每条 strength/gap 通过 `evidence_quotes` 绑定原文片段，避免“看起来合理但无法验证”的结论。
- **严格可解析输出**：JSON-only prompt + `parse_json_object()` 容错提取 + `validate_report_dict()` 严格校验，避免下游自动化被脏输出破坏。
- **输入边界治理**：
  - 预算不是“静默截断”，而是“可解释裁剪”：`input_meta.json` 明确记录原始大小、使用大小与裁剪原因。
  - 默认启用 outline 抽取（headings/bullets），在相同预算下尽量保留结构化信息，减少重要段落被随机截断的概率。
- **离线基线能力**：`mock` 引擎提供确定性输出，便于快速开发与对照 LLM 输出漂移（工程上比“完全依赖模型”更容易维护）。

## Roadmap
- [ ] token 级预算与上下文预估（更精确地控制不同模型的上下文窗口）
- [ ] 多模型并行评估与差异对比（稳定性/一致性/成本权衡）
- [ ] 两段式链路：事实抽取 → 评分对齐（降低幻觉、提高引用覆盖）
- [ ] 评分维度与权重配置化（YAML/JSON）
- [ ] `pytest` 测试套件与基础 CI

## Status
- 当前状态：Demo / PoC
- 适用场景：面试展示、原型验证、评估流程设计讨论
- 生产使用建议：需要补齐 token 预算、测试覆盖、失败重试策略、以及与业务侧 ATS/HR 系统的集成边界定义

## Author
- 角色：Software Engineer / AI Engineer（原型与工程化落地）
- 项目用途：学习与面试展示（强调可追溯、可解析、可维护的 LLM 工程实践）
