# aigegebox-football-match-guide

格格的工具箱公开 Skill：整理成年男子一线足球队的完整赛季赛程、赛事分类和中国大陆看球渠道，并生成球队定制的赛程长图。

## 目录

实际 Skill 位于 `skills/football-match-guide/`，包含：

- `SKILL.md`：触发条件与工作流程。
- `scripts/`：规范化、校验、覆盖检查和海报渲染脚本。
- `references/`：赛程、转播、队徽和排版规则。
- `teams/`：球队视觉配置。
- `examples/`：结构化赛程示例。
- `assets/`：官方队徽和确定性排版资源。

## 使用边界

- 默认地区：中国大陆。
- 默认对象：男子成年一线队。
- 未确认的对手、时间、场地和转播显示为待定，不猜测。
- 队徽库已有官方资源时直接复用；没有时必须从俱乐部官网获取并登记来源。
- 不使用 AI 生图处理队徽、日期或赛程文字。
- 本 Skill 不包含服务器部署和实时后台同步。

## 安装

通过 Codex Skill Installer 安装：

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --url https://github.com/你的用户名/aigegebox-football-match-guide-skill/tree/main/skills/football-match-guide
```

安装后重启或重新打开 Codex 会话，再使用 `$aigegebox-football-match-guide` 调用。

二维码来源参数仍使用 `from=football-match-guide`，用于兼容已有访问统计和历史链接。
