# DevLog

<p align="center">
  <b>AI 编程项目智能复盘助手</b><br>
  无缝记录 · 自动提炼 · 一键生成日报/周报/迭代方案
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/platform-cross--platform-lightgrey.svg" alt="Platform">
</p>

---

## 这是什么？

DevLog 是一套轻量级 Python 工具，专为 **AI 辅助编程场景** 设计。它能：

- 📝 **无缝记录**每次 AI 编程会话的关键信息（目标、任务、错误、决策、文件变更）
- 📊 **自动提炼**进度趋势、卡点分布、高频错误模式
- 📋 **一键生成**日报 / 周报 / 迭代方案（Markdown + JSON 双格式）
- 🔄 **闭环改进**将复盘发现映射到具体迭代任务，确保问题被跟踪

> 如果你每天用 AI 写代码但不知道"这一周到底干了什么"、"项目卡在哪里"、"下一步该做什么"——DevLog 就是为你准备的。

## 快速开始

### 安装

```bash
git clone https://github.com/lhao17202-hue/devlog-skill.git
cd devlog-skill
# 纯 Python 脚本，无需 pip install，Python 3.9+ 即可
```

### 三步上手

```bash
# 1. 初始化项目
python scripts/setup.py --project-dir ~/my-project --project-name "my-app"

# 2. 记录一次会话
python scripts/log_session.py --project-dir ~/my-project \
  --summary "完成后端登录 API 和 JWT 认证" \
  --goals "实现登录API" \
  --tasks-done "创建登录路由=done:src/auth/login.ts|配置JWT=done:src/middleware/auth.ts" \
  --tags "auth,backend" \
  --duration 45

# 3. 生成日报
python scripts/generate_report.py --project-dir ~/my-project --type daily
```

## 核心功能

### 📝 会话日志记录

每次 AI 编程会话结束后，用一条命令记录关键信息：

```bash
python scripts/log_session.py --project-dir . \
  --summary "一句话摘要" \
  --goals "用户目标1, 用户目标2" \
  --tasks-done "任务A=done:文件1,文件2|任务B=pending:原因" \
  --errors "错误描述=分类:解决方案" \
  --decisions "决策=理由" \
  --tags "标签1,标签2" \
  --duration 60 \
  --mood productive
```

### 📊 智能报告生成

**日报** — 今日概览 + 完成事项 + 卡点 + 明日计划（基于数据自动生成）

```bash
python scripts/generate_report.py --project-dir . --type daily --date 2026-07-12
```

**周报** — 进度趋势 + 错误分类 + 文件热点 + 迭代建议

```bash
python scripts/generate_report.py --project-dir . --type weekly
```

**迭代方案** ⭐ — 最有价值的输出：
- 🔍 问题根因分析（按错误分类定位）
- ⏱️ 任务工时估算（智能推断）
- 📅 按天排期（~3h/天有效编码时间）
- 🎯 风险矩阵（概率 × 影响 × 应对）
- ✅ 成功标准（量化判断）
- 🔄 改进闭环（复盘发现 → 措施 → 任务）

```bash
python scripts/generate_report.py --project-dir . --type iteration --label "sprint-2"
```

### 📁 数据存储

所有数据存储在项目根目录的 `.devlog/` 下（建议加入 `.gitignore`）：

```
.devlog/
├── sessions/                 # 会话日志 (JSON)
│   └── YYYY-MM-DD/
│       └── s_{timestamp}.json
├── reports/                  # 生成的报告 (Markdown + JSON)
│   ├── daily/
│   ├── weekly/
│   └── iterations/
├── index.json                # 项目进度索引
└── config.json               # 项目配置
```

## 报告效果预览

### 日报示例

```markdown
# 项目日报 — 2026年07月12日

## 今日概览
| 指标 | 数值 |
|------|------|
| 会话数 | 2 |
| 总耗时 | 90 分钟 |
| 完成任务 | 4 个 |

## 完成事项
| 会话 | 任务 | 涉及文件 |
|------|------|---------|
| s_20260712_0930 | 创建登录API | src/auth/login.ts |
| s_20260712_1430 | 修复导航栏 | src/components/Nav.tsx |

## 明日计划
1. 解决卡点：后端分页API阻塞前端
2. 继续推进：前端登录页面（后端已就绪）
3. 质量改进：关注 config 类错误（近期出现3次）
```

### 迭代方案预览

```markdown
# 迭代方案 — sprint-2

## 复盘数据
| 指标 | 数值 |
|------|------|
| 统计会话数 | 12 |
| 总耗时 | 9.0h |

## 下轮迭代任务
| 编号 | 类型 | 任务 | 预估工时 | 依赖 |
|------|------|------|---------|------|
| P1 | 卡点 | 后端分页API | 1.5h | 无 |
| P2 | 质量 | 解决 config 类错误 | 1.0h | 无 |
| P3 | 待完成 | 前端登录页面 | 2.0h | JWT已就绪 |

**核心工时**: 10.5h

## 风险矩阵
| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|---------|
| config错误反复 | 高 | 中 | 启动时环境变量统一校验 |
```

更多完整示例见 [`examples/`](examples/) 目录。

## 集成到你的工作流

DevLog 的脚本独立于任何特定的 AI 编程工具。你可以：

| 集成方式 | 说明 |
|---------|------|
| **手动** | 每次会话后运行 `log_session.py` |
| **Git Hook** | 在 `post-commit` 中记录变更 |
| **AI Tool Hook** | 配置 AI 工具的 post-session hook |
| **Cron / 定时** | 每天 18:00 自动生成日报 |

## 项目结构

```
devlog-skill/
├── README.md
├── LICENSE
├── SKILL.md                   # AI Skill 定义
├── scripts/
│   ├── setup.py               # 项目初始化
│   ├── log_session.py         # 会话记录
│   └── generate_report.py     # 报告生成
├── templates/                 # 报告模板参考
├── references/                # 数据 Schema 文档
└── examples/                  # 示例输出
```

## 适用场景

- ✅ 个人开发者用 AI 辅助编程，需要追踪进度
- ✅ 小团队没有专职 PM，需要自动化进度管理
- ✅ 开源项目维护者需要记录开发日志
- ✅ 自由职业者需要向客户提供工作日报

## 贡献

欢迎 Issue 和 PR！详见 [CONTRIBUTING.md](CONTRIBUTING.md)

## 许可证

MIT © [lhao17202-hue](https://github.com/lhao17202-hue)
