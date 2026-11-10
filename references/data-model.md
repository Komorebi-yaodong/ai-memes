# 数据结构与接口

## 索引文件

`https://aigengtu.com/gallery-index.json`

- 体积约 1.6 MB，**不要整份读进上下文**，用 `scripts/aigengtu.py` 过滤后再取结果
- 顶层：`{ "gallery": { 分类名: { name, images: [...] } }, "generated_at": "..." }`
- 分类固定 12 个，**条目数持续增长**（2026-11 快照为 3101，此前 2400+）。任何数字都要现取，见下方"更新机制"

## 单条字段

| 字段 | 覆盖率 | 含义 |
|---|---|---|
| `name` | 3101/3101 | 中文标题，台词通常嵌在 `『』` 里 |
| `alt` | 3101/3101 | 中文画面描述（角色 + 动作 + 台词） |
| `preview` | 3101/3101 | 压缩预览图 URL（webp，适合热链） |
| `original` | 3101/3101 | 原图 URL，**扩展名不定** |
| `category` | 3101/3101 | 角色分类 |
| `type` | 2596/3101 | 梗图 / 漫画 / 立绘 / 设定图 / 其他 |
| `alt_en` | 752/3101 | 英文画面描述 |
| `alt_ja` | 635/3101 | 日文画面描述 |
| `story` | **751/3101** | `{ zh, en, origin, contributor }`，zh 是"什么梗 + 什么场景发" |
| `anim` | 11/3101 | 动图标记 |

`id` 不在 JSON 里，需从 `original` 的 `/meme/(\d+)\.` 解析；脚本已处理（去掉前导零）。

## URL 规则（已逐个验证返回 200）

| 用途 | 规则 |
|---|---|
| 详情页 | `https://aigengtu.com/zh/meme/{id}`，`/meme/28` 与 `/meme/028` 均可 |
| 预览图 | `https://img.aigengtu.com/0_preview/meme/{三位补零}.webp` |
| 原图 | 取 `original` 字段，**不要自己拼** |

**扩展名分布**（2026-11 快照）：png 1219、jpg 752、webp 626、gif 252、jpeg 252。五种并存，硬编码任何一种都会挂掉大半。

## 编号特征

- 编号只增不减，新收录往后追加；快照时范围为 1 ~ 3509，中间有空号（改字差分被合并进主图，或未过人工终审）——**查不到号是正常的**，脚本会返回 `found: false` 并提示换编号。
- 新编号会超过旧的 max id，所以**不要用"编号 < N"做遍历边界**，要遍历就遍历索引里的实际条目。
- 动图（`anim` 标记）只取首帧做预览。

## 更新机制

| 项 | 实测 |
|---|---|
| `generated_at` | 天级刷新（如 `2026-11-08T10:02:05`） |
| HTTP `Cache-Control` | `public, max-age=3600` |
| HTTP `ETag` | 存在，可用于 `If-None-Match` 条件请求 |
| 脚本策略 | 缓存 1 小时 → 过期发条件请求 → 304 就只更新校验时间，200 才重写文件 |
| 强制刷新 | `--refresh`（命令级）或 `sync`（独立命令） |

要判断"最近有没有更新"，比对本地缓存的 `generated_at` 与 `sync` 后的新值即可。

## 兜底数据源

| 来源 | 用途 |
|---|---|
| `https://aigengtu.com/sitemap.xml` | 391 KB，全量页面 URL + image 标签 + 四语 hreflang，适合需要全站清单时 |
| `https://aigengtu.com/archive?p=N` | 52 页目录，仅当索引拿不到时兜底 |
| GitHub `the-beating-light-of-the-nail/deepseek-chan-meme-pack` | 精选 19 张预览 + 投稿/举报 issue 通道 |

## 三个坑

1. `archive?q=关键词` **不会过滤**——检索是前端 JS，URL 参数服务端不认。
2. `robots.txt` 里 `Disallow: /api/`，别去调它的内部接口。
3. 站内各处的数字互相打架：首页写"2400+"、GitHub 写"1400+"、档案馆写"3101 枚"，**全都会过期**。唯一可信的是索引里的实际条目数（`stats` 实时取）。
