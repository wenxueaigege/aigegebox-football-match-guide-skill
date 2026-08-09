# 球队视觉配置规范

```json
{
  "teamId": "arsenal",
  "nameZh": "阿森纳",
  "nameEn": "Arsenal",
  "crest": "assets/<teamId>-crest-official.svg",
  "crestSource": "https://club.example.com/path/to/official-crest.svg",
  "crestSourcePage": "https://club.example.com/official-page",
  "crestRightsNote": "官网公开资源；公开传播前确认俱乐部商标使用规范。",
  "colors": {
    "primary": "#d71920",
    "secondary": "#ffffff",
    "accent": "#f4c542",
    "text": "#241b19"
  },
  "styleProfile": "classic-football",
  "leagueNameZh": "英超联赛",
  "leagueNameEn": "Premier League",
  "leagueTitle": "英超联赛",
  "competitionSpecs": [
    {
      "name": "UEFA Champions League",
      "competitionType": "continental",
      "section": "cup",
      "layout": "split-rows",
      "showPending": true
    }
  ],
  "competitionOrder": ["EFL Cup", "FA Cup", "UEFA Champions League"],
  "competitionLabels": {
    "domestic-league": "联赛",
    "continental": "欧战",
    "domestic-cup": "国内杯赛"
  }
}
```

颜色用于排版，不代表官方品牌授权。队徽资源规则固定为：先检查 `assets/` 中是否已有该球队的官方队徽，已有则直接复用；没有才从俱乐部官网获取并保存到 `assets/`。`crestSource` 必须是官网资源地址，`crestSourcePage` 必须记录官网页面，`crestRightsNote` 记录公开传播注意事项。官网资源无法核验时不得生成正式海报，也不得用文字盾牌替代；仅内部排版草稿可显式允许文字占位。

## 队徽获取步骤

1. 按 `teamId` 检查 `assets/<teamId>-crest-official.*` 和球队 JSON 的 `crest` 字段。
2. 如果本地已有官方资源，先复用并检查文件可读性、透明背景和宽高比，不重新下载。
3. 如果本地没有，打开俱乐部官网，优先从官网页面引用的官方 SVG/PNG 下载原文件；不使用搜索结果缩略图或第三方转载图。
4. 保存本地文件，补齐 `crestSource`、`crestSourcePage` 和 `crestRightsNote`，再运行渲染和视觉检查。
5. 官网无法访问、只有低清截图或来源无法确认时，暂停生成并提示用户提供官网队徽文件。
