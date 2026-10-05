# -*- coding: utf-8 -*-
"""给 A/S（以及任何缺少 id 的）风格补上 ``style_info`` 末尾的 ``{id: 图片标签}``。

数据来源：cn.hbr.quest 用的同一套接口 ``master.hbr.quest/v1/cn/styles.json``；
id 按（角色名 + 风格名）匹配；图片标签取本地缩略图文件名（去掉目录与
``_Thumbnail.webp`` 后缀），与 SS/SSR 现有写法一致。

只做**文本插入**，不改动文件其它内容、不重排既有格式。

用法：
    python 工具/排轴/fill_style_ids.py --dry-run   # 只看要改什么
    python 工具/排轴/fill_style_ids.py             # 实际写入
"""

import argparse
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from check_data_vs_hbrquest import load_reference, norm, ref_chara  # noqa: E402


def image_label(info):
    """从 style_info[0] 的缩略图路径推出图片标签（如 RKayamoriDiva_R3）。"""
    path = str(info[0] or "") if info else ""
    base = os.path.basename(path.replace("\\", "/"))
    stem = os.path.splitext(base)[0]
    return stem[:-len("_Thumbnail")] if stem.endswith("_Thumbnail") else stem


def find_style_info_span(text, offset=0):
    """返回 offset 之后第一个 "style_info" 数组的 (左括号位置, 右括号位置)。"""
    m = re.search(r'"style_info"\s*:\s*\[', text[offset:])
    if not m:
        return None
    lb = offset + m.end() - 1          # '[' 的位置
    depth = 0
    i = lb
    in_str = False
    esc = False
    while i < len(text):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    return lb, i
        i += 1
    return None


def main():
    ap = argparse.ArgumentParser(description="给缺 id 的风格补 {id: 图片标签}")
    ap.add_argument("--dry-run", action="store_true", help="只打印，不写文件")
    ap.add_argument("--refresh", action="store_true", help="重新下载参考数据")
    args = ap.parse_args()

    ref = load_reference(refresh=args.refresh)
    ref_map = {}
    for s in ref:
        ref_map.setdefault((ref_chara(s), norm(s.get("name"))), s)

    changed_files = 0
    changed_styles = 0
    missing = []
    problems = []

    for root, dirs, files in os.walk(os.path.join(ROOT, "角色")):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for fn in sorted(files):
            if not fn.endswith(".json") or "style" not in fn.lower():
                continue
            path = os.path.join(root, fn)
            rel = os.path.relpath(path, ROOT)
            text = io.open(path, encoding="utf-8").read()
            try:
                data = json.loads(text)
            except Exception as e:
                problems.append((rel, "JSON解析失败 %s" % e))
                continue
            if not isinstance(data, dict) or not data:
                continue
            if text.count('"style_info"') != len(data):
                problems.append((rel, 'style_info 数量(%d)≠风格数(%d)'
                                 % (text.count('"style_info"'), len(data))))
                continue

            inserts = []          # (插入位置, 插入文本)
            pos = 0
            for name, style in data.items():
                span = find_style_info_span(text, pos)
                if span is None:
                    problems.append((rel, "找不到 %s 的 style_info" % name))
                    break
                lb, rb = span
                pos = rb + 1
                info = style.get("style_info") or []
                if len(info) >= 11 and isinstance(info[10], dict) and info[10]:
                    continue                      # 已有 id
                role = str(info[2]) if len(info) > 2 else ""
                r = ref_map.get((norm(role), norm(name)))
                if r is None:
                    missing.append((rel, name))
                    continue
                ws = rb
                while ws > lb and text[ws - 1] in " \t\r\n":
                    ws -= 1
                indent = text[ws:rb]
                if "\n" not in indent:
                    indent = "\n        "
                inserts.append((ws, "," + indent
                                + '{"%s":"%s"}' % (r["id"], image_label(info))))
                changed_styles += 1

            if not inserts:
                continue
            new_text = text
            for ws, inserted in sorted(inserts, key=lambda t: -t[0]):
                new_text = new_text[:ws] + inserted + new_text[ws:]
            print("%-56s +%d 个 id" % (rel, len(inserts)))
            if not args.dry_run:
                io.open(path, "w", encoding="utf-8", newline="").write(new_text)
            changed_files += 1

    print("\n== 汇总 ==")
    print("涉及文件 %d 个，补上 id 的风格 %d 个" % (changed_files, changed_styles))
    if missing:
        print("参考站里没找到对应风格（未补）：%d 个" % len(missing))
        for rel, n in missing[:20]:
            print("   %-40s %s" % (rel, n))
    if problems:
        print("跳过的问题文件：%d 个" % len(problems))
        for rel, why in problems[:20]:
            print("   %-40s %s" % (rel, why))
    if args.dry_run:
        print("（dry-run，未写入）")


if __name__ == "__main__":
    main()
