# 赛程数据规范

## 顶层对象

```json
{
  "team": {},
  "season": "2026/27",
  "region": "CN-mainland",
  "lastCheckedAt": "2026-08-08",
  "asOfDate": "2026-08-08",
  "sourceMode": "official-or-user-provided",
  "expectedCompetitions": [],
  "fixtures": []
}
```

`fixtures` 是比赛对象数组。`expectedCompetitions` 可选，用于覆盖报告指出尚未找到的赛事。

## 比赛对象

```json
{
  "fixtureId": "2026-08-22-premier-league-manchester-united",
  "competition": "Premier League",
  "competitionType": "domestic-league",
  "stage": "第1轮",
  "date": "2026-08-22",
  "dateLabel": "2026年9月15/16日",
  "time": "22:00",
  "opponent": "曼彻斯特联",
  "venue": "home",
  "location": "酋长球场",
  "status": "confirmed",
  "broadcasts": [],
  "source": "https://example.com/official-fixture",
  "updatedAt": "2026-08-08",
  "note": ""
}
```

允许的 `competitionType`：`domestic-league`、`domestic-cup`、`league-cup`、`continental`、`super-cup`、`club-world`、`friendly`、`playoff`、`qualifier`。

允许的 `status`：`confirmed`、`scheduled`、`tbd`、`postponed`、`cancelled`、`unconfirmed`。

`venue` 使用 `home`、`away` 或 `neutral`。未知日期、时间和对手使用 `null`，不要使用虚假的默认值。

`dateLabel` 用于杯赛官方只公布比赛窗口或日期范围的情况；`location` 用于展示具体球场或城市。两者都不能替代 `date` 的机器可排序字段。
