#!/usr/bin/env python3
"""初始化 .devlog/ 目录结构和配置文件。

用法:
    python setup.py --project-dir /path/to/project --project-name "my-app"

选项:
    --project-dir   项目根目录（默认当前目录）
    --project-name  项目名称（默认使用目录名）
"""

import json
import sys
from datetime import datetime
from pathlib import Path


LOG_DIR = ".devlog"


def create_directories(project_dir: Path) -> Path:
    """Create .devlog/ directory structure."""
    log_dir = project_dir / LOG_DIR

    dirs = [
        log_dir,
        log_dir / "sessions",
        log_dir / "reports" / "daily",
        log_dir / "reports" / "weekly",
        log_dir / "reports" / "iterations",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"  OK {d.relative_to(project_dir)}")

    return log_dir


def create_config(log_dir: Path, project_name: str):
    """Create config.json with sensible defaults."""
    config = {
        "project_name": project_name,
        "description": "",
        "created": datetime.now().strftime("%Y-%m-%d"),
        "tags_preset": ["feature", "bugfix", "refactor", "docs", "infra", "research"],
        "milestones": [],
        "focus_areas": [],
        "report_preferences": {
            "daily_time": "18:00",
            "weekly_day": "Friday",
            "language": "zh-CN"
        }
    }
    config_path = log_dir / "config.json"
    if not config_path.exists():
        config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  OK config.json created")
    else:
        print(f"  SKIP config.json already exists")


def create_index(log_dir: Path, project_name: str):
    """Create index.json if it doesn't exist."""
    index = {
        "project": project_name,
        "created": datetime.now().strftime("%Y-%m-%d"),
        "updated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "current_phase": "init",
        "total_sessions": 0,
        "total_hours": 0.0,
        "total_tasks_completed": 0,
        "total_errors": 0,
        "sessions": [],
        "milestones": [],
        "tags_summary": {},
        "error_categories": {}
    }
    index_path = log_dir / "index.json"
    if not index_path.exists():
        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  OK index.json created")
    else:
        print(f"  SKIP index.json already exists")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Initialize DevLog project tracking")
    parser.add_argument("--project-dir", default=".", help="Project root directory")
    parser.add_argument("--project-name", help="Project name (default: directory name)")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    project_name = args.project_name or project_dir.name
    print(f"DevLog — Initializing progress tracking")
    print(f"  Project: {project_name}")
    print(f"  Directory: {project_dir}\n")

    print("[1/3] Creating directory structure...")
    log_dir = create_directories(project_dir)

    print("\n[2/3] Creating config and index files...")
    create_config(log_dir, project_name)
    create_index(log_dir, project_name)

    print("\n[3/3] Done!")
    print(f"  Log directory: {log_dir}")
    print(f"  Next step: record your first session with log_session.py")
    print(f"  See README.md for usage examples.")


if __name__ == "__main__":
    main()
