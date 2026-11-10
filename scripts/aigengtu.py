#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""aigengtu.py —— 梗鲸 aigengtu.com 表情包检索器（供 AI 调用）

数据源：https://aigengtu.com/gallery-index.json（公开全量索引，robots 允许抓取）
馆藏是**动态增长**的：索引按天级刷新，条目数会变。所以本脚本：
  - 用 ETag 做条件请求（304 极便宜），缓存默认 1 小时过期，过期即静默校验
  - 任何输出都带实时 total，不要把数量写死

命令：
  sync                    强制校验/刷新索引（打印实时条目数）
  stats                   索引概况（实时总数、缓存年龄、分类分布）
  cats                    分类及数量
  search <词...> [-n N] [-c 角色] [--json]   AND 检索（所有词都要命中）
  pick   <词...> [-n N] [-c 角色] [--json]   模糊检索（命中任意词，按相关度排序）
  show   <编号>           按编号查单条
  random [N]              随机抽 N 条
  latest [N]              最新收录的 N 条（按编号倒序，用来看更新了什么）

可选参数：--json 输出机器可读 JSON（AI 优先用）；--refresh 立即联网校验索引
"""
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

INDEX_URL = "https://aigengtu.com/gallery-index.json"
UA = "Mozilla/5.0 (compatible; MemeSkill/1.1)"
_HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(_HERE, "..", "cache", "aigengtu_index.json")
TTL = int(os.environ.get("AIGENGTU_TTL", "3600"))  # 秒，与源站 Cache-Control 对齐


def _paths():
    p = os.path.abspath(CACHE)
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
    except Exception:
        p = os.path.join(os.environ.get("TEMP", "."), "aigengtu_index.json")
    return p, p + ".meta.json"


def _read_meta(mp):
    try:
        with open(mp, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_meta(mp, meta):
    try:
        with open(mp, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False)
    except Exception:
        pass


def _fetch(etag=None, timeout=90):
    headers = {"User-Agent": UA}
    if etag:
        headers["If-None-Match"] = etag
    req = urllib.request.Request(INDEX_URL, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.read(), resp.headers.get("ETag", "")
    except urllib.error.HTTPError as e:
        if e.code == 304:
            return None, etag
        raise


def sync(force=True, quiet=False):
    """确保拿到可用索引；force=True 时联网做条件校验。返回 (data, meta)"""
    cp, mp = _paths()
    meta = _read_meta(mp)
    fresh = (time.time() - meta.get("checked_at", 0)) < TTL

    if os.path.exists(cp) and fresh and not force:
        return load_local(cp), meta

    if os.path.exists(cp) and not force and fresh:
        return load_local(cp), meta

    raw, etag = _fetch(meta.get("etag") if os.path.exists(cp) else None)
    now = time.time()
    if raw is None:  # 304：索引没变，只更新校验时间
        meta["checked_at"] = now
        _write_meta(mp, meta)
        if not quiet:
            print("索引无变化（304）｜共 %d 条" % meta.get("count", 0))
        return load_local(cp), meta

    with open(cp, "wb") as f:
        f.write(raw)
    data = json.loads(raw)
    meta = {
        "etag": etag,
        "checked_at": now,
        "fetched_at": now,
        "count": sum(len(v.get("images", [])) for v in data.get("gallery", {}).values()),
        "generated_at": data.get("generated_at", ""),
    }
    _write_meta(mp, meta)
    if not quiet:
        print("索引已更新｜共 %d 条｜generated_at=%s" % (meta["count"], meta["generated_at"]))
    return data, meta


def load_local(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_index(force=False):
    cp, _ = _paths()
    if not os.path.exists(cp):
        return sync(force=True, quiet=True)
    return sync(force=force, quiet=True)


def flatten(data):
    out = []
    for cat, bucket in data.get("gallery", {}).items():
        for im in bucket.get("images", []):
            m = re.search(r"/meme/(\d+)\.", im.get("original", ""))
            im["id"] = m.group(1).lstrip("0") if m else ""
            im.setdefault("category", cat)
            out.append(im)
    return out


def _story(im):
    return im.get("story") or {}


def blob(im):
    st = _story(im)
    vals = [im.get("name", ""), im.get("alt", ""), im.get("alt_en", ""),
            im.get("alt_ja", ""), im.get("type", ""), im.get("category", "")]
    vals += [st.get("zh", ""), st.get("en", ""), st.get("origin", "")]
    return " ".join(v or "" for v in vals).lower()


def out(im, score=None):
    st = _story(im)
    d = {
        "id": im.get("id"),
        "name": im.get("name", ""),
        "category": im.get("category", ""),
        "type": im.get("type", ""),
        "detail_url": "https://aigengtu.com/zh/meme/%s" % im.get("id"),
        "image": im.get("original"),
        "preview": im.get("preview"),
        "story_zh": st.get("zh", ""),
    }
    if score is not None:
        d["score"] = score
    return d


def print_human(rows, total):
    print("命中 %d 条，显示 %d 条：\n" % (total, len(rows)))
    for im, score in rows:
        head = "#%-5s [%s/%s] %s" % (im.get("id"), im.get("category"), im.get("type") or "-", im.get("name"))
        if score is not None:
            head += "  (score %d)" % score
        print(head)
        print("       详情 https://aigengtu.com/zh/meme/%s" % im.get("id"))
        print("       原图 %s" % im.get("original"))
        if _story(im).get("zh"):
            print("       梗解 %s" % _story(im)["zh"][:140])
        print()


def parse(argv):
    words, num, cat, as_json, refresh = [], 10, None, False, False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("-n", "--num"):
            num = int(argv[i + 1]); i += 2; continue
        if a in ("-c", "--cat"):
            cat = argv[i + 1]; i += 2; continue
        if a == "--json":
            as_json = True; i += 1; continue
        if a == "--refresh":
            refresh = True; i += 1; continue
        words.append(a); i += 1
    return words, num, cat, as_json, refresh


def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    cmd = sys.argv[1]
    args, num, cat, as_json, refresh = parse(sys.argv[2:])

    if cmd == "sync":
        sync(force=True); return

    data, meta = get_index(force=refresh)
    items = flatten(data)

    if cmd == "stats":
        from collections import Counter
        c = Counter(i["category"] for i in items)
        age = int(time.time() - meta.get("checked_at", 0))
        with_story = sum(1 for i in items if _story(i).get("zh"))
        print("实时总数 %d ｜ 有梗解 %d ｜ generated_at %s" % (len(items), with_story, meta.get("generated_at", "?")))
        print("本地缓存 %d 分钟前校验（TTL %d 分钟；过期会自动条件校验，也可 --refresh）" % (age // 60, TTL // 60))
        for k, v in c.most_common():
            print("  %-12s %d" % (k, v))
        return

    if cmd == "cats":
        from collections import Counter
        print(json.dumps(Counter(i["category"] for i in items).most_common(), ensure_ascii=False))
        return

    if cmd == "show":
        if not args:
            print("用法：show <编号>"); return
        target = args[0].lstrip("0") or "0"
        hits = [i for i in items if i["id"] == target]
        if not hits:
            print(json.dumps({"found": False, "id": target,
                              "hint": "编号可能空缺（改字差分被并入主图或未过审），换编号或改用 search/pick"},
                             ensure_ascii=False, indent=2))
            return
        print(json.dumps([out(i) for i in hits], ensure_ascii=False, indent=2))
        return

    if cmd == "random":
        n = num if not args else int(args[0])
        print(json.dumps([out(i) for i in random.sample(items, min(n, len(items)))],
                         ensure_ascii=False, indent=2))
        return

    if cmd == "latest":
        n = num if not args else int(args[0])
        newest = sorted(items, key=lambda i: int(i["id"] or 0), reverse=True)[:n]
        print(json.dumps({"total_in_index": len(items),
                          "items": [out(i) for i in newest]}, ensure_ascii=False, indent=2))
        return

    if cmd in ("search", "pick"):
        if not args:
            print("用法：%s <关键词...>" % cmd); return
        pool = [i for i in items if cat is None or i["category"] == cat]
        words = [w.lower() for w in args if w.strip()]
        scored = []
        for im in pool:
            text = blob(im)
            name_alt = (im.get("name", "") + im.get("alt", "")).lower()
            hits = [w for w in words if w in text]
            if not hits:
                continue
            if cmd == "search" and len(hits) < len(words):
                continue
            score = sum(3 if w in name_alt else 1 for w in hits) + 2 * (len(hits) - 1)
            if _story(im).get("zh"):
                score += 1
            scored.append((im, score))
        scored.sort(key=lambda x: (-x[1], int(x[0]["id"] or 0)))
        rows = scored[:num]
        if as_json:
            print(json.dumps({"total_in_index": len(items), "matched": len(scored),
                              "items": [out(i, s) for i, s in rows]},
                             ensure_ascii=False, indent=2))
        else:
            print_human(rows, len(scored))
        return

    print("未知命令：%s\n%s" % (cmd, __doc__))


if __name__ == "__main__":
    main()
