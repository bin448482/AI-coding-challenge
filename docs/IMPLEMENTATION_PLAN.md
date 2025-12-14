# 候选人筛选总结工具 - 实施方案

## 项目概述

构建一个最小化的可工作原型，使用 LangChain 和 LLM 生成候选人筛选总结。

**关键约束：**
- 30分钟编码时间
- 使用 LangChain（支持多个 LLM）
- 输入：职位描述和简历文件（分别存放在不同文件夹）
- 输出：Markdown 格式
- 支持 Claude 和 OpenAI 等多个 LLM

---

## 项目结构

```
D:\0-development\projects\AI-coding-challenge\
├── main.py                    # 入口点
├── requirements.txt           # 依赖
├── .env.example              # 环境变量模板
├── config.py                 # 配置管理
├── data_loader.py            # 数据加载
├── screening_engine.py       # 核心筛选逻辑（LangChain）
├── output_formatter.py       # 输出格式化
├── prompts.py                # 提示词模板
├── docs/
│   ├── AI_Coding_Challenge_First_Principles_Engineer.md
│   └── IMPLEMENTATION_PLAN.md
├── data/
│   ├── job_descriptions/     # 职位描述文件
│   └── cvs/                  # 简历文件
└── outputs/                  # 生成的筛选总结
```

---

## 核心组件

### 1. config.py - 配置管理
- 从 .env 加载 API 密钥
- 支持模型选择（Claude、OpenAI 等）
- 提供默认值

### 2. data_loader.py - 数据加载
- 从 `data/job_descriptions/` 和 `data/cvs/` 读取文件
- 返回原始文本内容

### 3. prompts.py - 提示词模板
- 单个结构化提示词，生成所有必需部分
- 输出格式：Markdown，包含以下部分：
  - 候选人总结（2-3 句）
  - 优势与要求对比（要点）
  - 潜在风险或差距（要点）
  - 建议的面试问题（3-5 个）

### 4. screening_engine.py - 核心逻辑
- 初始化 LangChain LLMChain
- 函数：`screen_candidate(job_description, cv) -> str`
- 调用 LLM 并返回响应

### 5. output_formatter.py - 输出格式化
- 确保 Markdown 结构一致
- 写入 `outputs/` 目录（带时间戳）

### 6. main.py - 入口点
- 接受命令行参数（职位描述文件、简历文件）
- 编排：加载数据 → 运行筛选 → 格式化输出
- 输出到控制台和文件

---

## 实施步骤（优先级顺序）

### 第 1 阶段：基础设置（5 分钟）
1. 创建 `requirements.txt`：
   - langchain
   - python-dotenv
   - anthropic 或 openai

2. 创建 `config.py`：
   - 加载 API 密钥
   - 设置默认模型

3. 创建 `.env.example`

### 第 2 阶段：数据处理（5 分钟）
4. 创建 `data_loader.py`
5. 创建 `data/` 目录结构

### 第 3 阶段：提示词和引擎（10 分钟）
6. 创建 `prompts.py`
7. 创建 `screening_engine.py`

### 第 4 阶段：输出和集成（7 分钟）
8. 创建 `output_formatter.py`
9. 创建 `main.py`
10. 创建 `README.md`

---

## 关键设计决策

### 为什么这个方案？
- **最小化代码**：每个模块单一职责
- **快速设置**：无数据库，无复杂配置
- **LangChain 灵活性**：轻松切换 LLM
- **可扩展**：新增输出格式或 LLM 需要最少改动

### 权衡
- **无验证**：信任输入文件格式正确（节省时间）
- **单个提示词**：一次 LLM 调用（更快、更简单）
- **无缓存**：每次运行都调用 LLM（可接受）
- **基础错误处理**：快速失败，清晰消息
- **同步调用**：足够简单

---

## 配置策略

```
.env（不提交）：
ANTHROPIC_API_KEY=sk-...
LLM_MODEL=claude-3-5-sonnet-20241022
LLM_PROVIDER=anthropic

.env.example（提交）：
ANTHROPIC_API_KEY=your_key_here
LLM_MODEL=claude-3-5-sonnet-20241022
LLM_PROVIDER=anthropic
```

---

## 提示词策略

单个结构化提示词，包含：
1. 上下文（职位描述和简历）
2. 具体输出部分要求
3. Markdown 格式指导
4. 语气指导（专业、简洁）

---

## 依赖（requirements.txt）

```
langchain==0.1.x
langchain-anthropic==0.1.x
python-dotenv==1.0.x
```

---

## 使用流程

```bash
# 设置
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 配置
cp .env.example .env
# 编辑 .env 添加 API 密钥

# 运行
python main.py data/job_descriptions/senior_backend.txt data/cvs/john_doe.txt

# 输出
# 控制台：打印筛选总结
# 文件：outputs/screening_2025-12-14_10-30-45.md
```

---

## 关键文件

- **main.py** - 编排整个工作流
- **screening_engine.py** - LangChain 集成和 LLM 交互
- **prompts.py** - 提示词模板定义输出结构
- **config.py** - API 密钥和模型配置
- **requirements.txt** - 最小依赖

---

## 测试策略

跳过单元测试（时间限制）。改为：
1. 在 `data/` 创建示例 JD 和 CV 文件
2. 运行端到端测试一次
3. 验证输出是有效的 Markdown
4. 完成

---

## 实施优先级

1. **必须**：config.py、data_loader.py、screening_engine.py、main.py
2. **应该**：prompts.py、output_formatter.py、requirements.txt
3. **可选**：README.md、.env.example（但推荐）
