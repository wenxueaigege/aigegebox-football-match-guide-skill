---
name: aigegebox-football-match-guide
description: 整理成年男子一线足球队的完整赛季赛程、赛事分类和中国大陆转播渠道，校验官方来源与待定信息，并生成球队定制的看球赛程长图和覆盖报告。Use when a user asks for a football team's season schedule, match viewing guide, broadcast guide, or fixture poster.
---

# 球迷看球赛程

将球队赛程整理成球迷可以直接保存和分享的看球指南。重点是信息完整、来源清楚和中国大陆观看渠道，不是让用户自己研究排版。

本 Skill 只在当前 Agent 能读取本目录、运行 Python、写入输出文件时承诺完整海报结果。普通聊天窗口如果不能执行脚本，应退化为整理结构化赛程和输出生成步骤，不要声称已经生成 SVG/PNG。

## 工作流程

1. 先只确认两个用户选择：`球队`（必填）和`是否挂链接`（是 / 否）。球队未明确时先追问，不开始抓取或排版；默认地区为 `CN-mainland`，默认对象为男子成年一线队。
2. 如果用户选择“是”，再询问二维码要打开的完整网址、海报底部显示的网址和署名；用户只给一个网址时，二维码和底部默认使用同一网址。用户选择“否”时使用 `--no-qr`，不放二维码，但保留正常的海报信息和底部说明。
3. 获取赛程。具备联网能力时优先查俱乐部、赛事组织方和中国大陆版权平台的官方页面；没有联网能力时要求用户提供官方页面、JSON、CSV 或表格。
4. 汇总所有可确认的成年队赛事：联赛、国内杯赛、联赛杯、洲际赛事、超级杯、世俱杯、资格赛、附加赛和官方友谊赛。
5. 规范化比赛数据。先运行 `scripts/normalize_fixtures.py`，再运行 `scripts/validate_fixtures.py`。
6. 对日期、对手、赛事或转播渠道不确定的项目使用 `tbd`，显示“待定”，绝不凭常识补全；用户提供的既有海报、对话记录或结构化数据可以作为辅助来源，但必须标注为用户参考或 `scheduled`，不能冒充官方确认。
7. 运行 `scripts/check_coverage.py`，输出已发现赛事、未覆盖赛事、转播确认数和最后检查时间。
8. 先按 `references/data-cache-policy.md` 运行 `scripts/sync_data_cache.py` 尝试读取独立资料库。缓存先读、来源后核验；资料库不可访问时回退到 `examples/` 和 `teams/`，并在输出中标明回退来源。同步只写本地缓存，不修改 Skill 或 GitHub。
9. 读取球队配置并检查队徽库：先按 `teamId` 检查 `assets/` 中是否已有经过核验的官方队徽；已有就直接复用，不重复下载。库中没有时，必须从该俱乐部官网获取官方队徽资源，保存到 `assets/<teamId>-crest-official.<ext>`，并填写 `crest`、`crestSource`、`crestSourcePage` 和 `crestRightsNote`。官网无法访问或无法确认资源时暂停正式海报生成，向用户说明，不得用文字盾牌代替。
10. 以 `asOfDate` 或最后检查日期为基准，排除已经结束、已取消和已过去的比赛，再运行 `scripts/render_poster.py`，生成面向未来看球的完整赛季长图。原始 JSON 和覆盖报告保留完整历史记录，不删除已结束比赛。根据第 2 步选择传入 `--qr-url`、`--footer-url`、`--footer-label` 或 `--no-qr`。
11. 输出来源、更新时间、待确认项目和覆盖报告。
12. 海报完成后，如用户明确同意，才运行 `scripts/prepare_contribution.py` 生成脱敏候选包；可选地提交受控接口。未同意、不联网或接口失败都不影响正常生成。候选包进入人工审核，不直接提交 GitHub。

## 渲染模块边界

- `scripts/render_poster.py` 是稳定的命令行兼容入口，不直接承担所有布局规则。
- `scripts/poster/registry.py` 负责赛事注册和分区；`expectedCompetitions` 只用于覆盖检查，不参与海报分区。
- `scripts/poster/classic_layout.py` 负责杯赛面板排列，短赛事成对排列，长赛事按行拆分为双列，确保所有记录都被渲染。
- `scripts/poster/output.py` 负责 HTML、SVG 尺寸和 PNG 栅格化；输出层不读取球队赛事逻辑。
- `scripts/sync_data_cache.py` 只负责公共资料库读取和本地缓存，不修改渲染器。
- `scripts/prepare_contribution.py` 只负责明确同意后的脱敏候选包和可选受控提交，不保存用户网址或身份。
- `scripts/validate_dataset.py` 只负责独立资料库结构、来源、队徽和敏感字段校验。
- 球队配置可使用 `competitionSpecs` 声明赛事名称、类型、区域、布局和待定显示策略；旧的 `competitionOrder` 继续兼容。

## 数据来源规则

- 赛程优先使用俱乐部、联赛、杯赛或赛事组织方的官方来源。
- 中国大陆转播优先使用版权平台、央视及相关频道的官方节目安排。
- 其他平台内容只能作为参考，必须标注来源和状态，不能伪装成官方确认。
- 用户提供的 WorkBuddy 参考海报可以补充视觉上已经确认的北京时间、场地和渠道展示；这类字段要保留来源说明，并在海报中提示赛前复核。
- 队徽按“本地官方资源优先、缺失时官网获取”执行：先查 `assets/` 和球队配置；库中已有合规资源直接复用，库中没有才访问俱乐部官网下载。不得使用搜索引擎缩略图、维基、第三方球队资料站、AI 重绘或文字盾牌作为正式队徽。
- 同一场比赛可以有多个转播渠道；每个渠道单独保存平台、频道、状态、来源和更新时间。
- 重新生成意味着重新检查当前官方信息，不做后台同步，也不假装数据永远有效。

## 输出规则

- 输出完整赛季赛程长图的 SVG 矢量母版和 HTML 预览版。
- 默认使用 `rsvg-convert` 或 CairoSVG 生成 4 倍 PNG：`season-poster-4x.png`。
- 本机缺少 SVG 栅格化工具时仍保留 SVG/HTML，并明确提示 macOS 可运行 `brew install librsvg`。
- 队徽优先使用俱乐部官网提供的 SVG/PNG，必须保持原始宽高比；队徽文件嵌入 SVG/HTML 前先核对本地资产与官网来源，公开或商业传播前确认商标使用许可。
- 海报底部必须显示生成时间和“转播信息以中国大陆当地实际播出安排为准”。
- 输出覆盖检查报告，明确哪些赛事或渠道仍未确认。
- 不使用 AI 生图处理文字、日期、队徽或赛程；使用确定性 SVG/HTML 排版。

## 脚本入口

在本 Skill 目录下运行：

```bash
python3 scripts/normalize_fixtures.py input.json -o normalized.json
python3 scripts/validate_fixtures.py normalized.json -o validation.json
python3 scripts/check_coverage.py normalized.json -o coverage.json
python3 scripts/render_poster.py normalized.json --output-dir output
# 仅保留矢量母版和 HTML，不生成 PNG
python3 scripts/render_poster.py normalized.json --output-dir output --no-png
# 使用用户自己的网址和二维码目标
python3 scripts/render_poster.py normalized.json --output-dir output \
  --qr-url "https://example.com/your-page" \
  --footer-url "https://example.com" \
  --footer-label "我的主页"
# 只替换二维码目标；未单独指定底部网址时，底部同步显示该二维码网址
python3 scripts/render_poster.py normalized.json --output-dir output --qr-url "https://example.com/your-page"
# 明确不生成二维码，但保留默认底部网址
python3 scripts/render_poster.py normalized.json --output-dir output --no-qr
```

详细字段规则见：

- `references/fixture-schema.md`
- `references/broadcast-schema.md`
- `references/validation-rules.md`
- `references/team-profile-schema.md`
- `references/data-cache-policy.md`
- `references/contribution-policy.md`
- `references/poster-layout.md`
- `scripts/qr_code.py`（标准库二维码编码器，供海报渲染脚本调用）

## 失败处理

- 找不到官方赛程时，不编造比赛；要求用户提供来源或输入文件。
- 找不到转播渠道时显示“转播待定”，不批量套用常见平台。
- 队徽缺失、来源不是官网或本地文件无法读取时，正式渲染必须失败并提示补齐队徽；只有明确使用 `--allow-text-crest` 的内部排版草稿才允许文字占位，草稿不得作为正式交付。
- 脚本无法运行时至少交付结构化 JSON 和可复制的 SVG/HTML 方案。
- 对来源冲突保留两个来源并标记“需要人工确认”，不擅自选择一个作为事实。
