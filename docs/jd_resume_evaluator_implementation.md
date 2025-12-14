# JD × Resume 匹配评估器（LangChain 多模型可切换）实施文档

目标：在 **30 分钟内**实现一个最小可用的“岗位 JD 与简历匹配度评估”脚本，并且通过 **LangChain 配置/参数**选择不同 LLM（OpenAI / Zhipu / Ollama）。

## 0. 输入与现状确认

你提到的输入文件在当前仓库未发现（请确认真实路径或补充到仓库）：

- `docs/AI_Coding_Challenge_First_Principles_Engineer.md`
- `job_box/JD_Senior AI Engineer.md`
- `resume_box/Resume_EN_20250529.md`

本实施以“输入为两份 Markdown 文本（JD + Resume）”为前提；文件路径存在后即可直接跑通。

## 1. 交付物（最小可用）

- 新增入口：`main.py`
  - 读取：`--job <path>` + `--cv <path>`
  - 选择引擎：`--engine mock|openai`
  -（LLM 引擎）选择模型：`--model <name>`（OpenAI 兼容 Chat Completions）
  - 输出：
    - `outputs/jd_resume_eval/<timestamp>/report.json`
    - `outputs/jd_resume_eval/<timestamp>/input_meta.json`（包含裁剪/截断说明）
    -（失败排查）`raw_output.txt`（当模型返回无法解析的内容时）

## 2. 关键约束（为避免“编造”与不可追溯）

- 所有结论必须给出 **证据引用**：每条优势/缺口至少包含 1 条来自 JD 或 Resume 的原文摘录。
- 不允许引入简历/JD 未出现的技术品牌、产品名、指标数字；如需推断，只能用“可能/推测/需要确认”等措辞，并列为 `follow_up_questions`。
- 输出必须是 **严格 JSON**（解析失败时保底保存原始模型输出到 `raw_output.txt` 便于排查）。

## 3. 输出 Schema（v0）

固定 JSON 结构（字段名固定，便于后续自动化与对比多模型输出）：

```json
{
  "overall_score": 0,
  "recommend_interview": true,
  "score_breakdown": {
    "must_haves": 0,
    "nice_to_haves": 0,
    "llm_engineering": 0,
    "mlops": 0,
    "system_design": 0,
    "impact_and_ownership": 0
  },
  "strengths": [
    {"claim": "...", "evidence_quotes": ["..."]}
  ],
  "gaps": [
    {"gap": "...", "impact": "...", "evidence_quotes": ["..."]}
  ],
  "follow_up_questions": ["..."],
  "risk_flags": ["..."]
}
```

说明：
- `overall_score`：0–100（整数）
- `score_breakdown.*`：0–100（整数），用于解释总分构成
- `evidence_quotes`：来自 JD 或 Resume 的短摘录（建议每条 1–3 句）

## 4. 模型/引擎选择（实现策略）

为了最小可用与可移植性，先实现两种引擎：

- `mock`：不依赖外部 API，使用简单规则生成结构化报告（用于本地跑通与回归）
- `openai`：通过 OpenAI 兼容 `POST /v1/chat/completions` 调用真实模型

LLM 引擎常用环境变量：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`（默认 `https://api.openai.com/v1`）

建议默认：
- `temperature=0.0`（评估场景更稳定）

## 5. Prompt（v0，单次调用完成）

### System
- 角色：资深技术招聘官 + 严格证据引用的评估官
- 强制规则：
  - 不得臆造技术、产品、数字
  - 每条结论必须引用原文
  - 输出必须为严格 JSON（不允许额外文本）

### User
包含三段：
1) JD 原文（完整粘贴）
2) Resume 原文（完整粘贴）
3) 输出 Schema 与评分口径（上面的 JSON 字段 + 评分维度解释）

## 6. 执行流程（30 分钟落地）

1) 读取 `--jd/--resume` 文本
2) `load_runtime_config()`（确保 provider 凭证可用）
3) `make_chat_model(--model, temperature)`（切换不同 LLM）
4) 构造 prompt 并调用一次 `llm.invoke(...)`
5) 解析 JSON：
   - 成功：写入 `report.json`
   - 失败：写入 `raw_output.txt` + 返回非 0 exit code

## 7. 命令与验收

### 准备（一次性）
```bash
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

### 运行（示例）
```bash
python3 main.py \
  --job "job_box/JD_Senior AI Engineer.md" \
  --cv "resume_box/Resume_EN_20250529.md" \
  --engine "mock"
```

（可选）真实 LLM：
```bash
export OPENAI_API_KEY="..."
python3 main.py \
  --job "job_box/JD_Senior AI Engineer.md" \
  --cv "resume_box/Resume_EN_20250529.md" \
  --engine "openai" \
  --model "gpt-4o-mini" \
  --temperature 0
```

### 验收标准（v0）
- 生成 `report.json` 且可被 `python -c 'import json; json.load(open(...))'` 解析
- `strengths/gaps` 中每条均包含 `evidence_quotes`（非空）
- 至少输出 5 条 `follow_up_questions`（用于面试追问）

## 8. 风险与快速修复

- 模型输出非 JSON：在 prompt 中重复“只输出 JSON”，并在代码侧做一次轻量纠错（例如截取第一个 `{` 到最后一个 `}`）。
- 证据引用不足：将“每条结论必须含引文”写入 system，并在 schema 校验失败时让模型重试一次（最多 1 次，防止超时）。
- 不同模型输出字段漂移：对字段做严格校验，缺字段直接判失败并保存 `raw_output.txt`。

## 9. 输入边界（Prompt Size Budget）与裁剪策略

现实中 JD/简历可能非常长（尤其包含项目细节、附件、作品集链接列表）。输入过大时会带来两类问题：

1) **超过模型上下文**：直接报错或输出严重退化
2) **即使未超上下文**：注意力分散，证据引用质量下降，JSON 结构更容易漂移

因此实现上建议引入“预算（budget）+ 可解释裁剪”的机制：

- `--max-jd-chars`：JD 最大字符数（默认 60,000）
- `--max-cv-chars`：CV 最大字符数（默认 140,000）
- `--max-prompt-chars`：Prompt 总预算（默认 220,000，包含 schema/规则等开销）
- `--outline-if-needed / --no-outline-if-needed`：
  - 超预算时先提取“标题/要点”（Markdown headings + bullets）作为 **可追溯 excerpt**
  - 仍超预算再进行硬截断（hard truncate）

输出会生成 `input_meta.json`，包含：

- 原始字符数、实际使用字符数
- 发生过哪些截断/提取
- prompt 字符数的估算

建议的验收点（与输出质量强相关）：

- 当出现任何截断/提取时，`risk_flags` 必须明确提示“可能遗漏未包含证据”
- `evidence_quotes` 必须来自**提供给模型的文本片段**（否则属于不可追溯结论）

调试建议：

- 先用 `--dry-run` 查看字符数/截断情况，再决定是否需要提高预算或改用两段式链路。

## 9. 下一步（超出 30 分钟但建议）

- 增加 `--multi-model`：同一份 JD/Resume 用多个模型跑，输出并排对比（便于选择评估模型）
- 引入两段式链路（抽取事实 → 对齐评分），降低幻觉与漏项
- 把 rubric/字段定义迁移到一个 YAML 配置（与 `latest_resumes/prompt_config.yaml` 类似），使评估维度可配置
