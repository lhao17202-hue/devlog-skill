# 会话日志 JSON Schema

## 会话记录 (session log)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SessionLog",
  "type": "object",
  "required": ["session_id", "timestamp", "summary"],
  "properties": {
    "session_id": {
      "type": "string",
      "description": "唯一标识，格式 s_YYYYMMDD_HHMMSS"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "会话开始时间，ISO 8601"
    },
    "duration_minutes": {
      "type": "number",
      "description": "会话时长（分钟）"
    },
    "user_goals": {
      "type": "array",
      "items": {"type": "string"},
      "description": "用户在本次会话中提出的目标"
    },
    "tasks_completed": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["task", "status"],
        "properties": {
          "task": {"type": "string", "description": "任务描述"},
          "status": {
            "type": "string",
            "enum": ["done", "partial", "failed"],
            "description": "完成状态"
          },
          "files": {
            "type": "array",
            "items": {"type": "string"},
            "description": "涉及的变更文件"
          },
          "notes": {"type": "string", "description": "备注"}
        }
      }
    },
    "tasks_pending": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["task", "reason"],
        "properties": {
          "task": {"type": "string"},
          "reason": {"type": "string", "description": "未完成原因"}
        }
      }
    },
    "blockers": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["description"],
        "properties": {
          "description": {"type": "string"},
          "severity": {
            "type": "string",
            "enum": ["critical", "major", "minor"]
          },
          "status": {
            "type": "string",
            "enum": ["open", "in_progress", "resolved"]
          }
        }
      }
    },
    "errors_encountered": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["error"],
        "properties": {
          "error": {"type": "string", "description": "错误描述"},
          "category": {
            "type": "string",
            "enum": ["env", "code", "dependency", "data", "config", "unknown"],
            "description": "错误分类"
          },
          "resolution": {"type": "string", "description": "解决方案"},
          "time_cost_minutes": {"type": "number", "description": "解决耗时"}
        }
      }
    },
    "key_decisions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["decision", "rationale"],
        "properties": {
          "decision": {"type": "string"},
          "rationale": {"type": "string", "description": "决策理由"},
          "alternatives": {
            "type": "array",
            "items": {"type": "string"},
            "description": "被否决的备选方案"
          }
        }
      }
    },
    "tools_usage": {
      "type": "object",
      "description": "工具调用次数统计",
      "properties": {
        "Read": {"type": "integer"},
        "Write": {"type": "integer"},
        "Edit": {"type": "integer"},
        "Bash": {"type": "integer"},
        "Grep": {"type": "integer"},
        "Glob": {"type": "integer"}
      }
    },
    "files_changed": {
      "type": "array",
      "items": {"type": "string"},
      "description": "本次会话变更的文件路径（项目相对路径）"
    },
    "summary": {
      "type": "string",
      "description": "一句话摘要，包含核心成果和关键结论"
    },
    "tags": {
      "type": "array",
      "items": {"type": "string"},
      "description": "分类标签，如 auth, api, frontend, bugfix, refactor"
    },
    "mood": {
      "type": "string",
      "enum": ["productive", "stuck", "exploratory", "mixed"],
      "description": "会话整体感受（可选）"
    }
  }
}
```

## 项目索引 (index.json)

```json
{
  "project": "string — 项目名称",
  "created": "string — 创建日期 ISO",
  "updated": "string — 最后更新 ISO",
  "current_phase": "string — 当前开发阶段",
  "total_sessions": "number — 总会话数",
  "total_hours": "number — 总耗时",
  "total_tasks_completed": "number",
  "total_errors": "number",
  "sessions": ["string — session_id 列表"],
  "milestones": [
    {
      "name": "string",
      "target_date": "string",
      "actual_date": "string | null",
      "status": "planned | in_progress | done | delayed"
    }
  ],
  "tags_summary": {
    "string (tag)": "number (使用次数)"
  },
  "error_categories": {
    "string (category)": "number (出现次数)"
  }
}
```

## 项目配置 (config.json)

```json
{
  "project_name": "string",
  "description": "string",
  "created": "string — ISO date",
  "tags_preset": ["string — 预定义标签列表"],
  "milestones": [
    {
      "name": "string",
      "target_date": "string — ISO date",
      "description": "string"
    }
  ],
  "focus_areas": ["string — 当前关注的技术领域"],
  "report_preferences": {
    "daily_time": "string — HH:MM，日报默认时间",
    "weekly_day": "string — Monday/Tuesday/...，周报默认日",
    "language": "string — zh-CN / en"
  }
}
```
