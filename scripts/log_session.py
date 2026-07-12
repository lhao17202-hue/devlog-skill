#!/usr/bin/env python3
"""从会话内容中提取结构化信息并存储为会话日志。

用法:
    python log_session.py --project-dir PATH --summary "..." [options]

这个脚本通常由 Claude（通过 progress-review Skill）调用。
Claude 先分析对话内容，提取关键信息，然后将这些信息作为参数传入。

选项:
    --project-dir    项目根目录（必填）
    --summary        会话一句话摘要（必填）
    --goals          用户目标，逗号分隔
    --tasks-done     已完成任务，格式: "task1=done:file1,file2|task2=done:file3"
    --tasks-pending  未完成任务，格式: "task1=pending:原因|..."
    --blockers       阻塞项，逗号分隔
    --errors         遇到的错误，格式: "描述=分类:解决方案|..."
    --decisions      关键决策，格式: "决策=理由|..."
    --files          变更文件列表
    --tags           标签
    --duration       会话时长（分钟）
    --mood           会话感受 (productive/stuck/exploratory/mixed)
"""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path


def parse_list_arg(value: str | None) -> list[str]:
    """Parse a comma separated list argument."""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_pipe_list(value: str | None) -> list[str]:
    """Parse a pipe separated list argument."""
    if not value:
        return []
    return [item.strip() for item in value.split("|") if item.strip()]


def parse_task_list(value: str | None) -> list[dict]:
    """Parse task list in format: 'task1=done:file1,file2|task2=pending:reason'"""
    if not value:
        return []
    tasks = []
    for item in value.split("|"):
        item = item.strip()
        if not item:
            continue
        parts = item.split("=", 1)
        task_name = parts[0].strip()
        detail = parts[1].strip() if len(parts) > 1 else ""
        if ":" in detail:
            status, extra = detail.split(":", 1)
        else:
            status, extra = detail, ""

        task = {"task": task_name, "status": status}
        if status == "done" and extra:
            task["files"] = [f.strip() for f in extra.split(",") if f.strip()]
            task["notes"] = ""
        elif status == "pending" and extra:
            task["reason"] = extra
        tasks.append(task)
    return tasks


def parse_error_list(value: str | None) -> list[dict]:
    """Parse error list in format: 'error1=category:resolution|error2=category:resolution'"""
    if not value:
        return []
    errors = []
    for item in value.split("|"):
        item = item.strip()
        if not item:
            continue
        if "=" in item:
            error_desc, detail = item.split("=", 1)
            if ":" in detail:
                cat, res = detail.split(":", 1)
            else:
                cat, res = detail, ""
            errors.append({
                "error": error_desc.strip(),
                "category": cat.strip() or "unknown",
                "resolution": res.strip()
            })
        else:
            errors.append({"error": item, "category": "unknown", "resolution": ""})
    return errors


def parse_decision_list(value: str | None) -> list[dict]:
    """Parse decision list in format: 'decision1=rationale|decision2=rationale'"""
    if not value:
        return []
    decisions = []
    for item in value.split("|"):
        item = item.strip()
        if not item:
            continue
        if "=" in item:
            decision, rationale = item.split("=", 1)
            decisions.append({
                "decision": decision.strip(),
                "rationale": rationale.strip()
            })
        else:
            decisions.append({"decision": item, "rationale": ""})
    return decisions


def main():
    parser = argparse.ArgumentParser(description="Record a session log")
    parser.add_argument("--project-dir", required=True, help="Project root directory")
    parser.add_argument("--summary", required=True, help="One-line session summary")
    parser.add_argument("--goals", help="User goals, comma separated")
    parser.add_argument("--tasks-done", help="Completed tasks: name=done:file1,file2|...")
    parser.add_argument("--tasks-pending", help="Pending tasks: name=pending:reason|...")
    parser.add_argument("--blockers", help="Blocker descriptions, comma separated")
    parser.add_argument("--errors", help="Errors: desc=category:resolution|...")
    parser.add_argument("--decisions", help="Decisions: decision=rationale|...")
    parser.add_argument("--files", help="Changed files, comma separated")
    parser.add_argument("--tags", help="Tags, comma separated")
    parser.add_argument("--duration", type=float, default=0, help="Session duration (min)")
    parser.add_argument("--mood", default="mixed",
                        choices=["productive", "stuck", "exploratory", "mixed"])
    parser.add_argument("--session-id", help="Custom session ID (auto if omitted)")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    progress_dir = project_dir / ".claude" / "progress"

    # Ensure directories exist
    today = datetime.now().strftime("%Y-%m-%d")
    session_dir = progress_dir / "sessions" / today
    session_dir.mkdir(parents=True, exist_ok=True)

    # Generate session ID
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = args.session_id or f"s_{ts}"

    # Build session log
    session = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "duration_minutes": args.duration,
        "user_goals": parse_list_arg(args.goals),
        "tasks_completed": parse_task_list(args.tasks_done),
        "tasks_pending": parse_task_list(args.tasks_pending),
        "blockers": [{"description": b, "severity": "major", "status": "open"}
                     for b in parse_list_arg(args.blockers)],
        "errors_encountered": parse_error_list(args.errors),
        "key_decisions": parse_decision_list(args.decisions),
        "tools_usage": {},
        "files_changed": parse_list_arg(args.files),
        "summary": args.summary,
        "tags": parse_list_arg(args.tags),
        "mood": args.mood
    }

    # Write session log
    session_file = session_dir / f"{session_id}.json"
    session_file.write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")

    # Update index
    index_path = progress_dir / "index.json"
    if index_path.exists():
        index = json.loads(index_path.read_text(encoding="utf-8"))
    else:
        index = {
            "project": project_dir.name,
            "created": datetime.now().strftime("%Y-%m-%d"),
            "sessions": [],
            "total_sessions": 0,
            "total_hours": 0.0,
            "total_tasks_completed": 0,
            "total_errors": 0,
            "tags_summary": {},
            "error_categories": {},
            "milestones": []
        }

    index["updated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    if session_id not in index["sessions"]:
        index["sessions"].append(session_id)
    index["total_sessions"] = len(index["sessions"])
    index["total_hours"] = round(index.get("total_hours", 0) + args.duration / 60, 1)
    index["total_tasks_completed"] = (
        index.get("total_tasks_completed", 0) + len(session["tasks_completed"])
    )
    index["total_errors"] = (
        index.get("total_errors", 0) + len(session["errors_encountered"])
    )

    # Update tags summary
    for tag in session["tags"]:
        index.setdefault("tags_summary", {})
        index["tags_summary"][tag] = index["tags_summary"].get(tag, 0) + 1

    # Update error categories
    for err in session["errors_encountered"]:
        cat = err.get("category", "unknown")
        index.setdefault("error_categories", {})
        index["error_categories"][cat] = index["error_categories"].get(cat, 0) + 1

    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Session logged: {session_file}")
    print(f"Index updated: {index_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
