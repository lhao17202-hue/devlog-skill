# 贡献指南

感谢你对 DevLog 的关注！以下是参与贡献的方式。

## 提交 Issue

- 使用清晰的标题描述问题
- 附上复现步骤、期望行为、实际行为
- 如果是功能建议，描述使用场景和期望效果

## 提交 Pull Request

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/my-feature`
3. 提交你的更改：`git commit -m 'Add: 某某功能'`
4. 推送到分支：`git push origin feature/my-feature`
5. 提交 Pull Request

### Commit 规范

- `Add:` 新功能
- `Fix:` 修复 bug
- `Docs:` 文档变更
- `Refactor:` 重构
- `Improve:` 改进已有功能

## 本地开发

```bash
git clone https://github.com/lhao17202-hue/devlog-skill.git
cd devlog-skill

# 初始化测试项目
python scripts/setup.py --project-dir ./test-project --project-name "test"

# 添加测试数据
python scripts/log_session.py --project-dir ./test-project \
  --summary "测试会话" --tags "test" --duration 10

# 生成测试报告
python scripts/generate_report.py --project-dir ./test-project --type daily
```

## 代码风格

- Python 3.9+ 兼容
- 中文注释和文档
- 使用 `pathlib` 而非 `os.path`
- JSON 输出使用 `ensure_ascii=False`
