# 中国大陆转播数据规范

每场比赛的 `broadcasts` 为数组，允许多个平台：

```json
[
  {
    "region": "CN-mainland",
    "platform": "咪咕视频",
    "channel": "足球频道",
    "status": "confirmed",
    "source": "https://example.com/official-broadcast",
    "updatedAt": "2026-08-08",
    "note": ""
  }
]
```

允许的状态：`confirmed`、`scheduled`、`tbd`、`changed`。

- `confirmed`：官方或版权平台已明确确认。
- `scheduled`：平台节目单已经排期，但仍可能变化。
- `tbd`：尚未公布。
- `changed`：原安排发生变化，需在 `note` 说明。

没有可靠来源时不要填写平台名称，直接使用 `tbd`。海报必须注明：`转播信息以中国大陆当地实际播出安排为准`。
