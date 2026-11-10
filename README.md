# AI Memes

一个面向中文语境的 AI 表情包检索工具。它从 [梗鲸（aigengtu.com）](https://aigengtu.com/) 公开的结构化索引中获取数据，在本地完成检索、筛选和排序，方便为聊天、社媒文案或 AI 回复挑选合适的梗图。

> 数据库持续更新，请以运行 `stats` 得到的实时结果为准。

## 功能

- **本地搜索**：首次运行下载索引，后续从本地缓存中搜索。
- **ETag 缓存更新**：默认每小时条件校验一次，避免重复下载完整索引。
- **两种检索模式**：
  - `search`：关键词全部命中（AND）。
  - `pick`：关键词任一命中并按相关度排序（OR，适合不确定的表达）。
- **角色/分类筛选**：可用 `-c` / `--cat` 限定分类或角色。
- **实用命令**：支持索引同步、统计、分类查看、单图查询、随机抽图和查看最新收录。
- **机器可读输出**：检索命令支持 `--json`，便于接入 Agent 或其他自动化流程。

## 环境要求

- Python 3.8+（仅使用标准库，无需安装第三方依赖）
- 可访问 `https://aigengtu.com/gallery-index.json`

## 快速开始

```powershell
# 克隆后进入项目目录
cd E:\Programming\ai-memes

# 首次检索会自动下载索引
python scripts\aigengtu.py pick 无语 嫌弃 翻白眼 -n 5 --json
```

> Windows 下也可以用 `/`：`python scripts/aigengtu.py ...`。

## 常用命令

### 查看索引状态

```powershell
# 强制联网校验/刷新索引
python scripts\aigengtu.py sync

# 查看实时条目数、缓存状态和分类分布
python scripts\aigengtu.py stats

# 列出分类及数量
python scripts\aigengtu.py cats
```

### 搜索表情包

```powershell
# AND：每个关键词都必须命中
python scripts\aigengtu.py search 摸鱼 加班 -n 5 --json

# OR + 相关度排序：任一关键词命中即可
python scripts\aigengtu.py pick 无语 嫌弃 翻白眼 -n 5 --json

# 按分类/角色筛选
python scripts\aigengtu.py pick 崩溃 -c Claude娘 -n 3 --json

# 无视缓存时间，立即联网校验
python scripts\aigengtu.py pick 新图 --refresh --json
```

### 按编号、随机和最新收录查询

```powershell
# 查询指定编号
python scripts\aigengtu.py show 8

# 随机抽取 3 张
python scripts\aigengtu.py random 3

# 查看最近收录的 10 张
python scripts\aigengtu.py latest 10
```

## 输出字段

`--json` 输出中的单项通常包括：

| 字段           | 含义                                       |
| -------------- | ------------------------------------------ |
| `id`         | 梗图编号                                   |
| `name`       | 图名或台词                                 |
| `category`   | 分类/角色                                  |
| `type`       | 图的类型，如梗图、漫画或设定图             |
| `detail_url` | 梗鲸详情页                                 |
| `image`      | 原图 URL；请原样使用，不要自行改扩展名     |
| `preview`    | 预览图 URL                                 |
| `story_zh`   | 中文梗解（如有）                           |
| `score`      | `pick` / `search` 模式下的相关度参考值 |

## 缓存与配置

本地缓存默认写入 `cache/`，已由 `.gitignore` 忽略。缓存默认有效期是 **3600 秒**；可通过环境变量调整：

```powershell
$env:AIGENGTU_TTL=7200
python scripts\aigengtu.py stats
```

如果项目目录不可写，脚本会回退到系统临时目录保存缓存。

## 推荐选图流程

1. 提取用户表达中的**情绪、场景、角色、台词**。
2. 优先用 `pick` 搜索 2～3 个同义或近义词。
3. 先看 `story_zh` 是否与使用场景匹配，再看图名和类型。
4. 最终只选 1～3 张，不要为了凑数输出不相关的图片。

情绪关键词映射和更详细的选图规则请见 [references/playbook.md](references/playbook.md)；数据字段说明见 [references/data-model.md](references/data-model.md)。

## 目录结构

```text
.
├─ scripts/
│  └─ aigengtu.py          # 命令行检索工具
├─ references/
│  ├─ data-model.md        # 索引字段说明
│  └─ playbook.md          # 检索与选图手册
├─ cache/                  # 运行时索引缓存（不提交）
└─ SKILL.md                # 面向 Agent 的使用说明
```

## 数据来源与使用说明

- 数据来源为梗鲸公开索引：`https://aigengtu.com/gallery-index.json`。
- 请勿爬取或调用站点禁止的私有/受限 API；本工具只读取公开索引。
- 图片版权归各原作者或权利人所有。若用于商业用途，请自行确认授权；本项目和数据站点均不提供商业授权。

## License

本项目采用 [MIT License](LICENSE) 开源。

Copyright (c) 2026 Komorebi-yaodong

> MIT 许可证仅适用于本仓库中的代码与文档；梗图及其相关素材的权利仍归各原作者或权利人所有，使用时请遵循相应授权与平台规则。
