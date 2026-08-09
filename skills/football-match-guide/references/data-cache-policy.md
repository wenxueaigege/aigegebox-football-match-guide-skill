# 公共资料库与本地缓存策略

## 资料库

公共资料库与 Skill 分离维护：

`https://github.com/wenxueaigege/aigegebox-football-match-data`

默认读取地址为：

`https://raw.githubusercontent.com/wenxueaigege/aigegebox-football-match-data/main`

资料库只保存球队档案、官方队徽元数据、结构化赛季快照和来源记录，不保存用户二维码、署名、个人资料或海报成品。

## 读取顺序

1. 检查当前工作区的本地缓存。
2. 缓存缺失或需要更新时读取公共资料库 `catalog.json` 和球队赛季快照。
3. 根据快照中的来源重新核验官方赛程和中国大陆转播安排。
4. 将本次更新写入本地缓存，不直接写入 Skill 仓库或 GitHub。
5. 公共资料库不可访问时，回退到 Skill 内置 `examples/` 和 `teams/` 数据，并在输出中注明回退来源。

同步脚本：

```bash
python3 scripts/sync_data_cache.py --team-id arsenal --season 2026/27
```

缓存目录默认是当前工作区的 `.aigegebox-football-cache/`，也可以使用环境变量 `AIGEGEBOX_FOOTBALL_CACHE_DIR` 或 `--cache-dir` 指定。缓存中不应放入二维码网址、署名或其他用户信息。

## 新鲜度

- 赛程结构：超过 7 天重新核验。
- 中国大陆转播安排：超过 24 小时重新核验；比赛临近 72 小时，每次生成都核验。
- 队徽资源：本地资源和来源仍有效时直接复用，每 90 天复核一次来源。

缓存时间只表示资料读取时间，不能证明信息当前仍然正确。海报必须显示最后检查时间；来源冲突时保留旧快照，标记“需要人工确认”，不自动覆盖。

## 边界

缓存优先是节省重复读取和提高离线可用性，不是后台同步，也不是无条件信任缓存。任何联网失败都不能阻止已经可用的本地海报生成，但必须诚实说明数据来源和可能过期。
