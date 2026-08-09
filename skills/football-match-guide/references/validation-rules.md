# 校验规则

## 必须满足

- 顶层必须包含 `team`、`season` 和 `fixtures`。
- 每场比赛必须有 `competition`、`competitionType`、`status` 和 `source` 字段；演示数据可使用 `sourceMode: demo` 和 `source: demo-data`。
- 已确认比赛必须有日期和对手；否则降级为 `tbd` 或 `unconfirmed`。
- 日期必须是 `YYYY-MM-DD`。
- 比赛状态必须使用规范枚举。
- 转播状态为 `confirmed` 或 `changed` 时必须有来源。
- 同一 `fixtureId` 不得重复。

## 需要提示但不阻止

- 时间为空。
- 对手待定。
- 转播渠道为空。
- 来源不是官方来源。
- 赛事名称没有出现在预期赛事清单中。
- 同一场比赛存在多个来源或多个时间版本。

## 对外表述

校验失败时使用中文说明，不把 Python 堆栈直接展示给球迷。所有不确定信息都必须在海报和覆盖报告中可见。
