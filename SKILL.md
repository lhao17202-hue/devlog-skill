---
name: devlog
description: AI 编程项目智能复盘助手。无缝记录每次 AI 编程会话的关键信息，自动提炼进度、卡点、问题、优化点，一键生成日报/周报/迭代方案。当用户提到项目进度、复盘、日报、周报、迭代方案、进度报告、问题总结、版本对比、项目记录时使用。也适用于"今天做了什么"、"这周进展"、"项目卡在哪里"、"下一步该做什么"等场景。
---

# DevLog — AI 编程项目进度复盘

## 概述

DevLog 为你的 AI 辅助编程项目提供一整套进度管理和智能复盘能力。设计理念是 **"零摩擦记录，高价值输出"**——记录阶段尽量自动无感，复盘阶段提供深度洞察。

### 核心能力

- **无感记录**：自动捕获每次 AI 编程会话的关键信息，结构化存储
- **智能复盘**：聚合多次会话，自动提炼进度趋势、卡点分布、高频问题
- **迭代驱动**：基于复盘结果，生成可执行的下一轮迭代方案（含工时估算、排期、风险矩阵）

## 数据模型

所有数据存储在项目根目录的 `.devlog/` 下：

```
.devlog/
├── sessions/                 # 会话日志
│   └── YYYY-MM-DD/
│       └── s_{timestamp}.json
├── reports/                  # 生成的报告
│   ├── daily/                # 日报
│   ├── weekly/               # 周报
│   └── iterations/           # 迭代方案
├── index.json                # 项目进度索引
└── config.json               # 项目配置
```

### 会话日志结构

每次会话记录为一个 JSON 文件，完整 Schema 见 `references/log-schema.md`。核心字段：`session_id`、`timestamp`、`user_goals`、`tasks_completed`、`tasks_pending`、`blockers`、`errors_encountered`、`key_decisions`、`files_changed`、`summary`、`tags`。

## 工作流程

### 第一步：初始化（仅需一次）

在项目根目录执行初始化：

```bash
python scripts/setup.py --project-dir /path/to/project --project-name "my-app"
```

会创建 `.devlog/` 目录结构、`config.json`、`index.json`。

### 第二步：日常记录

每次 AI 编程会话结束后，手动或自动记录：

```bash
python scripts/log_session.py --project-dir . \
  --summary "完成后端登录 API 和 JWT 认证" \
  --goals "实现登录API, 配置JWT" \
  --tasks-done "创建登录路由=done:src/auth/login.ts|配置JWT中间件=done:src/middleware/auth.ts" \
  --errors "JWT secret未配置=config:添加到.env" \
  --tags "auth,backend,api" \
  --duration 45 \
  --mood productive
```

### 第三步：生成报告

```bash
# 日报
python scripts/generate_report.py --project-dir . --type daily

# 周报
python scripts/generate_report.py --project-dir . --type weekly

# 迭代方案（最有价值的输出）
python scripts/generate_report.py --project-dir . --type iteration --label "sprint-2"
```

### 第四步：复盘与迭代

迭代方案是整个 DevLog 最有价值的输出，它会：

1. **问题归因** — 按错误分类定位根因，附具体改进方向
2. **工时估算** — 基于任务关键词智能推断每项任务耗时
3. **排期建议** — 按每天 ~3h 有效编码时间自动拆分为多天计划
4. **风险矩阵** — 识别风险的概率、影响及应对措施
5. **成功标准** — 本轮迭代完成的量化判断标准
6. **改进闭环** — 复盘发现 → 改进措施 → 对应任务，确保问题被跟踪

## 报告模板

### 日报
今日概览 → 完成事项 → 未完成事项 → 卡点/阻塞 → 错误记录 → 明日计划（基于数据自动生成）→ 标签分布 → 优化点

### 周报
本周概览 → 每日分布 → 错误分类统计 → 文件热点（含热度指示）→ 关注领域 → 迭代优化建议

### 迭代方案
复盘数据 → 问题根因分析 → 卡点处理 → 下轮迭代任务（含预估工时、依赖）→ 建议排期 → 风险矩阵 → 成功标准 → 改进措施闭环

## 集成到你的 AI 编程工具

DevLog 的 Python 脚本独立于任何特定的 AI 编程工具。你可以：

- **手动使用**：每次会话后运行 `log_session.py`
- **Hook/Plugin**：配置你的 AI 工具的 post-session hook 自动调用
- **CI/CD**：在 Git hook 或 CI pipeline 中生成周报

## 脚本说明

| 脚本 | 用途 |
|------|------|
| `scripts/setup.py` | 初始化 `.devlog/` 目录结构 |
| `scripts/log_session.py` | 从对话提取并结构化存储会话日志 |
| `scripts/generate_report.py` | 聚合日志生成日报/周报/迭代方案 |

## 最佳实践

1. **保持记录习惯**：每次编程会话结束后花 30 秒记录，回报是精准的复盘洞察
2. **标签要一致**：在 `config.json` 中预定义标签，保持一致性方便聚合
3. **定期复盘**：建议至少每周做一次正式复盘，日报每天快速浏览
4. **报告要行动**：复盘的价值不在报告本身，而在它产生的下一步行动
5. **日志要诚实**：记录真实的问题和失败——掩盖问题会让复盘失去意义
