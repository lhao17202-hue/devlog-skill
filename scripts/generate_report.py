#!/usr/bin/env python3
"""聚合会话日志，生成日报/周报/迭代方案。

用法:
    python generate_report.py --project-dir PATH --type daily   [--date YYYY-MM-DD]
    python generate_report.py --project-dir PATH --type weekly  [--week-start YYYY-MM-DD]
    python generate_report.py --project-dir PATH --type iteration [--label v1]

读取 .devlog/sessions/ 下的日志，聚合统计后输出 Markdown 报告。
同时生成对应的 JSON 元数据文件。
"""

import json
import sys
import argparse
from datetime import datetime, timedelta, date
from pathlib import Path
from collections import Counter, defaultdict


def load_sessions(progress_dir: Path, since: date, until: date) -> list[dict]:
    """Load all session logs within the given date range."""
    sessions = []
    sessions_root = progress_dir / "sessions"
    if not sessions_root.exists():
        return sessions

    for date_dir in sorted(sessions_root.iterdir()):
        if not date_dir.is_dir():
            continue
        try:
            dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d").date()
        except ValueError:
            continue
        if since <= dir_date <= until:
            for session_file in sorted(date_dir.glob("*.json")):
                try:
                    sessions.append(json.loads(
                        session_file.read_text(encoding="utf-8")))
                except (json.JSONDecodeError, KeyError):
                    continue
    return sessions


def load_index(progress_dir: Path) -> dict:
    """Load project index."""
    index_path = progress_dir / "index.json"
    if index_path.exists():
        return json.loads(index_path.read_text(encoding="utf-8"))
    return {}


# ── Daily Report ──────────────────────────────────────────────

def generate_daily_report(sessions: list[dict], report_date: date) -> str:
    """Generate a daily report in Markdown."""
    total_tasks = sum(len(s.get("tasks_completed", [])) for s in sessions)
    total_duration = sum(s.get("duration_minutes", 0) for s in sessions)
    all_tags = Counter()
    all_errors = []
    all_blockers = []
    all_pending = []
    all_files = []

    for s in sessions:
        for tag in s.get("tags", []):
            all_tags[tag] += 1
        all_errors.extend(s.get("errors_encountered", []))
        all_blockers.extend(s.get("blockers", []))
        all_pending.extend(s.get("tasks_pending", []))
        all_files.extend(s.get("files_changed", []))

    L = []
    L.append(f"# 项目日报 — {report_date.strftime('%Y年%m月%d日')}")
    L.append("")
    L.append("## 今日概览")
    L.append("")
    L.append("| 指标 | 数值 |")
    L.append("|------|------|")
    L.append(f"| 会话数 | {len(sessions)} |")
    L.append(f"| 总耗时 | {total_duration:.0f} 分钟 |")
    L.append(f"| 完成任务 | {total_tasks} 个 |")
    L.append(f"| 遇到错误 | {len(all_errors)} 个 |")
    L.append(f"| 变更文件 | {len(all_files)} 个 |")
    L.append("")

    if sessions:
        L.append("## 完成事项")
        L.append("")
        L.append("| 会话 | 任务 | 涉及文件 |")
        L.append("|------|------|---------|")
        for s in sessions:
            sid = s.get("session_id", "?")[:16]
            for task in s.get("tasks_completed", []):
                files = ", ".join(task.get("files", [])[:3])
                if len(task.get("files", [])) > 3:
                    files += f" +{len(task['files']) - 3} more"
                L.append(f"| {sid} | {task['task']} | {files} |")
        L.append("")

    if all_pending:
        L.append("## 未完成事项")
        L.append("")
        for task in all_pending:
            reason = task.get("reason", "")
            L.append(f"- **{task['task']}** — {reason}")
        L.append("")

    if all_blockers:
        L.append("## 卡点 / 阻塞")
        L.append("")
        for b in all_blockers:
            sev = b.get("severity", "major")
            label = {"critical": "[!!]", "major": "[!]", "minor": "[-]"}.get(sev, "[!]")
            L.append(f"- {label} {b['description']}")
        L.append("")

    if all_errors:
        L.append("## 错误记录")
        L.append("")
        L.append("| 错误 | 分类 | 解决方案 |")
        L.append("|------|------|---------|")
        for e in all_errors:
            L.append(f"| {e.get('error', '?')} | {e.get('category', '?')} | {e.get('resolution', '-')} |")
        L.append("")

    L.append("## 明日计划")
    L.append("")
    # Generate data-driven next-day suggestions
    suggestions = []
    if all_blockers:
        for b in all_blockers:
            suggestions.append(f"解决卡点：{b.get('description', '')}")
    if all_pending:
        for task in all_pending[:3]:
            reason = task.get("reason", "")
            suggestions.append(f"继续推进：{task.get('task', '')}{'（依赖：' + reason + '）' if reason else ''}")
    # Suggest addressing top error category
    error_cats_today = Counter()
    for s in sessions:
        for e in s.get("errors_encountered", []):
            error_cats_today[e.get("category", "unknown")] += 1
    if error_cats_today:
        top_cat = error_cats_today.most_common(1)[0]
        suggestions.append(f"质量改进：关注{top_cat[0]}类错误，今日出现{top_cat[1]}次")

    if suggestions:
        for i, sug in enumerate(suggestions, 1):
            L.append(f"{i}. {sug}")
    else:
        L.append("*（基于今日未完成事项和里程碑自动生成，或手动补充）*")
    L.append("")

    if all_tags:
        L.append("## 标签分布")
        L.append("")
        for tag, count in all_tags.most_common():
            L.append(f"- **{tag}**: {count}")
        L.append("")

    return "\n".join(L)


# ── Weekly Report ─────────────────────────────────────────────

def generate_weekly_report(sessions: list[dict], week_start: date) -> str:
    """Generate a weekly report in Markdown."""
    week_end = week_start + timedelta(days=6)
    total_tasks = sum(len(s.get("tasks_completed", [])) for s in sessions)
    total_duration = sum(s.get("duration_minutes", 0) for s in sessions)
    total_errors = sum(len(s.get("errors_encountered", [])) for s in sessions)
    total_sessions = len(sessions)
    days_count = max((week_end - week_start).days + 1, 1)

    # Aggregate by day
    by_day = defaultdict(lambda: {"sessions": 0, "tasks": 0, "duration": 0, "errors": 0})
    for s in sessions:
        try:
            day = datetime.fromisoformat(s["timestamp"]).strftime("%m/%d")
        except (ValueError, KeyError):
            day = "?"
        by_day[day]["sessions"] += 1
        by_day[day]["tasks"] += len(s.get("tasks_completed", []))
        by_day[day]["duration"] += s.get("duration_minutes", 0)
        by_day[day]["errors"] += len(s.get("errors_encountered", []))

    # Error categorization
    error_cats = Counter()
    for s in sessions:
        for e in s.get("errors_encountered", []):
            error_cats[e.get("category", "unknown")] += 1

    # Tag trends
    tag_trends = Counter()
    for s in sessions:
        for tag in s.get("tags", []):
            tag_trends[tag] += 1

    # File hotspots
    file_counts = Counter()
    for s in sessions:
        for f in s.get("files_changed", []):
            file_counts[f] += 1

    L = []
    L.append(f"# 项目周报 — {week_start.strftime('%m/%d')} ~ {week_end.strftime('%m/%d')}")
    L.append("")
    L.append("## 本周概览")
    L.append("")
    L.append("| 指标 | 数值 | 日均 |")
    L.append("|------|------|------|")
    L.append(f"| 会话数 | {total_sessions} | {total_sessions/days_count:.1f}/天 |")
    L.append(f"| 总耗时 | {total_duration:.0f} 分钟 | {total_duration/days_count:.0f} 分钟/天 |")
    L.append(f"| 完成任务 | {total_tasks} | {total_tasks/days_count:.1f}/天 |")
    L.append(f"| 错误数 | {total_errors} | {total_errors/days_count:.1f}/天 |")
    L.append("")

    if by_day:
        L.append("## 每日分布")
        L.append("")
        L.append("| 日期 | 会话 | 任务 | 耗时(分) | 错误 |")
        L.append("|------|------|------|---------|------|")
        for day, stats in sorted(by_day.items()):
            L.append(f"| {day} | {stats['sessions']} | {stats['tasks']} | {stats['duration']:.0f} | {stats['errors']} |")
        L.append("")

    if error_cats:
        L.append("## 错误分类")
        L.append("")
        L.append("| 分类 | 次数 | 占比 |")
        L.append("|------|------|------|")
        for cat, count in error_cats.most_common():
            pct = count / total_errors * 100 if total_errors else 0
            L.append(f"| {cat} | {count} | {pct:.0f}% |")
        L.append("")

    if file_counts:
        L.append("## 文件热点 (修改最频繁)")
        L.append("")
        # Highlight files changed across multiple sessions (real hotspots)
        # vs files changed only once
        L.append("| 文件 | 修改次数 | 涉及会话 | 热度 |")
        L.append("|------|---------|---------|------|")
        for f, count in file_counts.most_common(10):
            # Find which sessions touched this file
            session_ids = []
            for s in sessions:
                if f in s.get("files_changed", []):
                    sid = s.get("session_id", "?")
                    session_ids.append(sid.split("_")[-1][:4] if "_" in sid else sid[:6])
            session_str = ", ".join(session_ids)
            # Hot indicator: 3+ changes = HOT, 2 = WARM, 1 = normal
            if count >= 3:
                hot = "[HIGH]"
            elif count >= 2:
                hot = "[MED]"
            else:
                hot = "-"
            L.append(f"| {f} | {count} | {session_str} | {hot} |")
        L.append("")

        # Call out the real hotspots
        hot_files = [(f, c) for f, c in file_counts.items() if c >= 3]
        if hot_files:
            L.append("> 以下文件修改频繁，建议重点关注设计稳定性和测试覆盖：")
            for f, c in hot_files:
                L.append(f"> - `{f}` ({c}次)")
            L.append("")
        elif not any(c >= 2 for _, c in file_counts.items()):
            L.append("> 本周无高频修改文件，代码变更较为分散。这在早期开发阶段是正常的。")
            L.append("")

    if tag_trends:
        L.append("## 关注领域")
        L.append("")
        for tag, count in tag_trends.most_common():
            L.append(f"- **{tag}** ({count}次)")
        L.append("")

    # Iteration suggestions
    L.append("## 迭代优化建议")
    L.append("")
    if error_cats:
        top_error = error_cats.most_common(1)[0]
        L.append(f"1. **减少 `{top_error[0]}` 类错误**：本周出现 {top_error[1]} 次，建议排查根因并加入检查清单")
    if total_sessions > 0 and total_tasks / total_sessions < 1:
        L.append(f"2. **提升单次会话产出**：平均每会话 {total_tasks/total_sessions:.1f} 个任务，考虑更聚焦的任务拆分")
    if total_errors > total_tasks * 0.3:
        L.append(f"3. **关注错误率**：错误/任务比 {total_errors/total_tasks*100:.0f}%，建议加强测试")
    if not error_cats:
        L.append("*暂无足够数据生成建议*")
    L.append("")

    return "\n".join(L)


# ── Iteration Report ──────────────────────────────────────────

def _estimate_task_hours(task_desc: str, avg_session_minutes: float) -> float:
    """Estimate task hours based on name patterns and historical session duration."""
    desc_lower = task_desc.lower()
    # Heuristic: tasks mentioning certain keywords tend to take longer
    if any(kw in desc_lower for kw in ["api", "接口", "数据库", "database", "migrate", "迁移"]):
        base = 1.5
    elif any(kw in desc_lower for kw in ["页面", "page", "ui", "组件", "component"]):
        base = 2.0
    elif any(kw in desc_lower for kw in ["test", "测试", "检验", "校验", "validate"]):
        base = 1.0
    elif any(kw in desc_lower for kw in ["fix", "修复", "bug"]):
        base = 0.5
    elif any(kw in desc_lower for kw in ["config", "配置", "env", "环境"]):
        base = 0.5
    elif any(kw in desc_lower for kw in ["doc", "文档", "readme"]):
        base = 0.5
    else:
        # Default: half of average session duration
        base = max(0.5, avg_session_minutes / 120)
    return round(base, 1)


def _estimate_risk(description: str, error_count: int, total_tasks: int) -> dict:
    """Estimate risk probability and impact."""
    desc_lower = description.lower()
    # Probability heuristics
    if error_count >= 3:
        prob = "高"
    elif error_count >= 2:
        prob = "中"
    else:
        prob = "低"

    # Impact heuristics
    if any(kw in desc_lower for kw in ["阻塞", "block", "crash", "崩溃", "critical"]):
        impact = "高"
    elif any(kw in desc_lower for kw in ["性能", "perform", "安全", "security", "数据"]):
        impact = "高"
    elif any(kw in desc_lower for kw in ["样式", "style", "ui", "兼容"]):
        impact = "中"
    else:
        impact = "中"

    return {"description": description, "probability": prob, "impact": impact}


def generate_iteration_report(sessions: list[dict], index: dict,
                              label: str = "") -> str:
    """Generate an iteration plan based on accumulated session data.

    This is the most valuable output of the progress-review skill,
    providing root cause analysis, prioritized tasks with time estimates,
    a schedule, risk matrix, success criteria, and concrete improvements.
    """
    total_sessions = len(sessions)
    total_tasks = sum(len(s.get("tasks_completed", [])) for s in sessions)
    total_errors = sum(len(s.get("errors_encountered", [])) for s in sessions)
    total_duration = sum(s.get("duration_minutes", 0) for s in sessions)
    avg_session = total_duration / total_sessions if total_sessions > 0 else 0

    # ── Aggregate data ──
    errors_by_cat = defaultdict(list)
    for s in sessions:
        for e in s.get("errors_encountered", []):
            cat = e.get("category", "unknown")
            errors_by_cat[cat].append(e.get("error", ""))

    all_pending = []
    for s in sessions:
        all_pending.extend(s.get("tasks_pending", []))

    all_blockers = []
    for s in sessions:
        all_blockers.extend(s.get("blockers", []))

    all_decisions = []
    for s in sessions:
        for d in s.get("key_decisions", []):
            d["_session_id"] = s.get("session_id", "")
            all_decisions.append(d)

    # ── Build task list with estimates ──
    high_tasks = []   # (label, description, hours, deps)
    mid_tasks = []
    low_tasks = []

    # P0: Critical blockers
    for b in all_blockers:
        if b.get("severity") == "critical":
            desc = b.get("description", "")
            hours = _estimate_task_hours(desc, avg_session)
            high_tasks.append(("卡点", desc, hours, "无"))

    # P0: Top error category fix
    if errors_by_cat:
        top_cat = max(errors_by_cat, key=lambda k: len(errors_by_cat[k]))
        top_count = len(errors_by_cat[top_cat])
        desc = f"系统性解决 {top_cat} 类错误（累计{top_count}次）"
        hours = _estimate_task_hours(desc, avg_session)
        high_tasks.append(("质量", desc, hours, "无"))

    # P1: Pending tasks (blocked or important)
    for task in all_pending:
        desc = task.get("task", "")
        hours = _estimate_task_hours(desc, avg_session)
        high_tasks.append(("待完成", desc, hours, "无"))

    # P2: Structural improvements based on error categories
    structural_improvements = {
        "config": ("配置校验", "增加启动时环境变量统一校验层", 1.0, "无"),
        "env": ("环境标准化", "引入 devcontainer 或 Docker Compose 统一开发环境", 2.0, "无"),
        "code": ("代码质量", "增加 lint-staged + 单元测试覆盖率门槛", 1.5, "无"),
        "dependency": ("依赖管理", "锁定依赖版本 + 定期升级 + 依赖审计", 1.0, "无"),
    }
    for cat in errors_by_cat:
        if cat in structural_improvements:
            label_s, desc, hours, deps = structural_improvements[cat]
            mid_tasks.append((label_s, desc, hours, deps))

    # P2: API contract if there are integration issues
    if any("api" in str(s.get("tags", [])).lower() for s in sessions):
        mid_tasks.append(("API规范", "制定前后端API契约文档", 1.5, "无"))

    # P2: Based on key decisions
    if all_decisions:
        mid_tasks.append(("技术沉淀", "基于决策记录固化常用技术选型标准", 0.5, "无"))

    # P3: Documentation and low-priority
    low_tasks.append(("文档", "更新项目 README 和开发指南，纳入本轮经验", 0.5, "无"))
    low_tasks.append(("检查清单", "根据错误分类补充开发检查清单", 0.5, "无"))

    # ── Build risk matrix ──
    risks = []
    for cat, errors in errors_by_cat.items():
        if len(errors) >= 2:
            risks.append(_estimate_risk(f"{cat}类错误反复出现", len(errors), total_tasks))
    for b in all_blockers:
        risks.append(_estimate_risk(b.get("description", ""), 1, total_tasks))
    if len(all_pending) > total_tasks * 0.5:
        risks.append({
            "description": "任务积压：未完成任务超过已完成任务的50%",
            "probability": "高", "impact": "中"
        })
    if total_sessions > 0 and avg_session < 15:
        risks.append({
            "description": "短会话频繁：平均会话 < 15分钟，上下文切换成本高",
            "probability": "中", "impact": "低"
        })

    # ── Schedule estimate ──
    total_high_hours = sum(t[2] for t in high_tasks)
    total_mid_hours = sum(t[2] for t in mid_tasks)
    total_low_hours = sum(t[2] for t in low_tasks)
    core_hours = total_high_hours + total_mid_hours
    # Assume ~3 productive hours per day
    days_needed = max(2, int(core_hours / 3 + 0.5))

    # ── Render report ──
    L = []
    L.append(f"# 迭代方案{f' — {label}' if label else ''}")
    L.append("")
    L.append("## 复盘数据")
    L.append("")
    L.append("| 指标 | 数值 |")
    L.append("|------|------|")
    L.append(f"| 统计会话数 | {total_sessions} |")
    L.append(f"| 总耗时 | {total_duration:.0f} 分钟 ({total_duration/60:.1f}h) |")
    L.append(f"| 完成任务 | {total_tasks} |")
    L.append(f"| 累计错误 | {total_errors} |")
    L.append(f"| 待处理卡点 | {len(all_blockers)} |")
    L.append(f"| 未完成任务 | {len(all_pending)} |")
    L.append(f"| 平均每会话产出 | {total_tasks/total_sessions:.1f} 个任务" if total_sessions > 0 else "")
    L.append("")

    # ── Root cause analysis ──
    if errors_by_cat:
        L.append("## 问题根因分析")
        L.append("")
        hints = {
            "env": "环境配置不够标准化，建议引入 devcontainer 或 Docker Compose 统一开发环境。",
            "config": "配置文件缺少校验，建议增加 config schema 验证和默认值。",
            "dependency": "依赖管理存在问题，建议锁定版本 + 定期升级 + 依赖审计。",
            "code": "代码质量问题，建议增加 lint-staged + 单元测试覆盖率门槛。",
            "data": "数据相关问题，建议加强数据校验和迁移脚本测试。",
        }
        for cat, errors in sorted(errors_by_cat.items(), key=lambda x: -len(x[1])):
            L.append(f"### {cat}（{len(errors)}次）")
            for e in list(dict.fromkeys(errors))[:5]:
                L.append(f"- {e}")
            L.append("")
            hint = hints.get(cat)
            if hint:
                L.append(f"> 根因推测：{hint}")
            L.append("")

    # ── Blocker resolution ──
    if all_blockers:
        L.append("## 卡点处理")
        L.append("")
        L.append("| 卡点 | 严重度 | 建议措施 |")
        L.append("|------|--------|---------|")
        for b in all_blockers[:10]:
            sev = b.get("severity", "major")
            desc = b.get("description", "?")
            suggestion = "需协调相关方制定专项解决方案"
            if "api" in desc.lower():
                suggestion = "采用 API-first 开发：先定义契约文档，再并行开发前后端"
            elif "环境" in desc or "env" in desc.lower():
                suggestion = "引入 Docker 或 devcontainer 标准化环境"
            L.append(f"| {desc} | {sev} | {suggestion} |")
        L.append("")

    # ── Iteration tasks with estimates ──
    L.append("## 下轮迭代任务")
    L.append("")

    def write_task_group(title: str, tasks: list, start_num: int):
        L.append(f"### {title}")
        L.append("")
        L.append("| 编号 | 类型 | 任务 | 预估工时 | 依赖 |")
        L.append("|------|------|------|---------|------|")
        n = start_num
        for label_s, desc, hours, deps in tasks:
            L.append(f"| P{n} | {label_s} | {desc} | {hours}h | {deps} |")
            n += 1
        L.append("")
        return n

    n = write_task_group("高优先级", high_tasks, 1) if high_tasks else None
    n = write_task_group("中优先级", mid_tasks, n or 1) if mid_tasks else (n or 1)
    n = write_task_group("低优先级（弹性任务）", low_tasks, n or 1) if low_tasks else (n or 1)

    L.append(f"**核心工时（高+中优先级）**: {total_high_hours + total_mid_hours:.1f}h")
    L.append(f"**全部工时（含弹性任务）**: {total_high_hours + total_mid_hours + total_low_hours:.1f}h")
    L.append("")

    # ── Schedule ──
    L.append("## 建议排期")
    L.append("")
    cumulative = 0.0
    day = 1
    all_prioritized = high_tasks + mid_tasks
    day_tasks = []
    for label_s, desc, hours, deps in all_prioritized:
        if cumulative + hours > 3.5 and day_tasks:
            task_list = " → ".join(f"{t[0]}" for t in day_tasks)
            L.append(f"**第{day}天** (~{cumulative:.1f}h): {task_list}")
            day += 1
            cumulative = 0.0
            day_tasks = []
        cumulative += hours
        day_tasks.append((desc[:20], hours))
    if day_tasks:
        task_list = " → ".join(f"{t[0]}" for t in day_tasks)
        L.append(f"**第{day}天** (~{cumulative:.1f}h): {task_list}")
    low_desc = "、".join(f"{t[0]}" for t in low_tasks)
    L.append(f"**弹性**: {low_desc}（按实际进度穿插）")
    L.append(f"")
    L.append(f"> 预估总工期 {days_needed} 天（按每天 ~3h 有效编码时间计）")
    L.append("")

    # ── Risk matrix ──
    if risks:
        L.append("## 风险矩阵")
        L.append("")
        L.append("| 风险 | 概率 | 影响 | 应对措施 |")
        L.append("|------|------|------|---------|")
        mitigations = {
            "config": "在迭代早期完成环境变量统一校验层",
            "code": "引入 pre-commit lint + CI 质量门禁",
            "env": "Docker 化开发环境，消除'我这能跑'问题",
            "dependency": "锁定版本号 + package.json engines 字段",
        }
        for r in risks:
            desc = r["description"]
            prob = r["probability"]
            impact = r["impact"]
            # Find matching mitigation
            mitigation = "制定专项应对方案"
            for cat_key, mit in mitigations.items():
                if cat_key in desc.lower():
                    mitigation = mit
                    break
            L.append(f"| {desc} | {prob} | {impact} | {mitigation} |")
        L.append("")

    # ── Success criteria ──
    L.append("## 成功标准")
    L.append("")
    L.append("本轮迭代完成的判断标准：")
    L.append("")
    n = 1
    if all_blockers:
        L.append(f"{n}. **卡点清零**：所有活跃阻塞项已解决或降级")
        n += 1
    if all_pending:
        L.append(f"{n}. **遗留任务归零**：{len(all_pending)} 个待完成事项全部交付")
        n += 1
    if errors_by_cat:
        top_cat = max(errors_by_cat, key=lambda k: len(errors_by_cat[k]))
        L.append(f"{n}. **质量改善**：{top_cat}类错误复发率降低 50% 以上")
        n += 1
    L.append(f"{n}. **文档更新**：项目文档反映最新架构和开发规范")
    L.append("")

    # ── Improvement measures ──
    L.append("## 改进措施（对应本轮复盘）")
    L.append("")
    L.append("| 复盘发现 | 改进措施 | 对应任务 |")
    L.append("|----------|---------|---------|")
    if "config" in errors_by_cat:
        L.append(f"| 配置管理薄弱（{len(errors_by_cat['config'])}次配置错误） | 启动时统一环境变量校验 | P2 配置校验 |")
    if "code" in errors_by_cat:
        L.append(f"| 代码质量问题（{len(errors_by_cat['code'])}次代码错误） | 增加 lint-staged + 测试门槛 | P2 代码质量 |")
    if "env" in errors_by_cat:
        L.append(f"| 环境不一致（{len(errors_by_cat['env'])}次环境错误） | Docker / devcontainer 标准化 | P2 环境标准化 |")
    if all_blockers:
        L.append(f"| 前后端协作阻塞（{len(all_blockers)}个活跃卡点） | API-first 开发模式 + 契约文档 | P1 待完成 |")
    if all_decisions:
        L.append(f"| 技术决策分散（{len(all_decisions)}个决策未归档） | 建立技术决策记录 (ADR) | P3 文档 |")
    L.append("")

    return "\n".join(L)


# ── Main ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate progress reports")
    parser.add_argument("--project-dir", required=True, help="Project root directory")
    parser.add_argument("--type", required=True,
                        choices=["daily", "weekly", "iteration"],
                        help="Report type")
    parser.add_argument("--date", help="Target date for daily (YYYY-MM-DD)")
    parser.add_argument("--week-start", help="Week start for weekly (YYYY-MM-DD)")
    parser.add_argument("--label", default="", help="Label for iteration report")
    parser.add_argument("--output", help="Output file path (auto if omitted)")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    progress_dir = project_dir / ".devlog"
    reports_dir = progress_dir / "reports"
    index = load_index(progress_dir)

    if args.type == "daily":
        report_date = (datetime.strptime(args.date, "%Y-%m-%d").date()
                       if args.date else date.today())
        sessions = load_sessions(progress_dir, report_date, report_date)
        report = generate_daily_report(sessions, report_date)
        out_dir = reports_dir / "daily"
        out_file = out_dir / f"daily_{report_date.strftime('%Y%m%d')}.md"

    elif args.type == "weekly":
        if args.week_start:
            week_start = datetime.strptime(args.week_start, "%Y-%m-%d").date()
        else:
            week_start = date.today() - timedelta(days=date.today().weekday())
        week_end = week_start + timedelta(days=6)
        sessions = load_sessions(progress_dir, week_start, week_end)
        report = generate_weekly_report(sessions, week_start)
        out_dir = reports_dir / "weekly"
        out_file = out_dir / f"weekly_{week_start.strftime('%Y%m%d')}.md"

    else:  # iteration
        sessions = load_sessions(progress_dir, date(2000, 1, 1), date.today())
        report = generate_iteration_report(sessions, index, args.label)
        out_dir = reports_dir / "iterations"
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = args.label.replace(" ", "_") if args.label else ts
        out_file = out_dir / f"iteration_{slug}.md"

    out_dir.mkdir(parents=True, exist_ok=True)

    if args.output:
        out_file = Path(args.output)
    out_file.write_text(report, encoding="utf-8")

    # JSON metadata
    json_file = out_file.with_suffix(".json")
    json_data = {
        "type": args.type,
        "generated_at": datetime.now().isoformat(),
        "project": index.get("project", project_dir.name),
        "sessions_count": len(sessions),
        "markdown_report": str(out_file)
    }
    json_file.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(report)
    print(f"\n---")
    print(f"Report saved: {out_file}")
    print(f"JSON saved:  {json_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
