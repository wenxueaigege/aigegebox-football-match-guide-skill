# 公共资料候选提交规则

## 只有明确同意才提交

海报生成完成后，Skill 可以询问：

> 是否将本次脱敏后的球队赛程资料提交到 aigegebox 公共资料库？

用户没有明确选择“同意”时，不生成提交包、不上传、不修改 Skill 或 GitHub。正常生成和下载不依赖提交功能。

## 候选包

使用：

```bash
python3 scripts/prepare_contribution.py \
  --snapshot normalized.json \
  --team-profile teams/arsenal.json \
  --output candidate \
  --consent
```

候选包包含 `snapshot.json`、`sources.json`、`team-profile.json` 和 `submission-manifest.json`。脚本会清理二维码目标网址、海报底部网址、署名、本地路径、IP、账号、聊天上下文和个人备注，并以内容哈希标记版本。

候选包默认只保存在本地。它不会直接创建 GitHub commit，也不会自动进入公开资料库。

## 受控提交接口

服务器接口由“格格的工具箱”主线程建设和部署。Skill 只调用约定协议：

```text
POST /api/football-match-guide/data-submissions
```

请求必须包含 `consent: true`，大小不超过 2MB。接口应按 IP 限频、按内容哈希去重，不接受二维码网址、署名等字段，不主动抓取候选资料里的任意 URL。资料只进入私有 `incoming/` 候选区，返回 `submissionId` 后等待人工审核。

可选地在明确同意后提交：

```bash
python3 scripts/prepare_contribution.py \
  --snapshot normalized.json \
  --team-profile teams/arsenal.json \
  --output candidate \
  --consent \
  --endpoint https://www.wenxueaigege.com/api/football-match-guide/data-submissions
```

接口不可用时，候选包仍保留在本地，不能影响海报生成；脚本会提示稍后重试。

## 人工审核

正式公开前必须核对球队、赛季、重复比赛、日期、赛事类型、主客场、官方来源、中国大陆转播依据和队徽官网来源。校验通过后才合并到独立资料库，并更新版本清单。不合格资料保留在候选区并记录原因，不公开提交者身份。
