# -*- coding: utf-8 -*-
"""给 SS / SSR 风格的「专属技能」条目补上 ``{"exclusive":1}``。

专属技能 = 该风格 ``ActiveSkills`` 的**第一个条目**（EX 技能），例如：

    [
        ["黑曜君王", "…", "14", "6"],
        [ …效果… ],
        ["39", "62", "76"],
        {"黑曜君王1": […], "黑曜君王2": […]},
        {"exclusive":1}          ← 本次补的字段
    ],

不是专属的情况（已通用化）不再补：
  * 该角色**第一个 SS 风格**（style_id 最小）的专属技能（同角色其它风格也能用）；
  * ``data_source.GENERALIZED_SKILLS`` 里列出的技能。

判断用的就是 ``data_source`` 自己的逻辑（``StyleInfo.skills[*].is_exclusive`` +
``source_group == 0``），保证数据与工具完全一致。

只做**文本插入**：不改动文件其它内容、不重排既有格式，可重复执行（已有则跳过）。

用法：
    python 工具/排轴/fill_exclusive.py --dry-run   # 只看要改什么
    python 工具/排轴/fill_exclusive.py             # 实际写入
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

from 工具.排轴.data_source import get_data_source          # noqa: E402

TARGET_FILES = ("SSRstyles.json", "SSstyles.json")
FIELD = '{"exclusive":1}'


def find_array_span(text, key, offset=0):
    """返回 offset 之后 ``"key": [`` 里那个数组的 (左括号位置, 右括号位置)。"""
    m = re.search(r'"%s"\s*:\s*\[' % re.escape(key), text[offset:])
    if not m:
        return None
    lb = offset + m.end() - 1
    return lb, match_bracket(text, lb)


def last_element_end(text, lb, rb):
    """返回组内最后一个顶层元素结束后的位置（用来把字段接在它后面）。"""
    i = lb + 1
    last = None
    while i < rb:
        ch = text[i]
        if ch in "[{":
            close = "]" if ch == "[" else "}"
            end = match_bracket(text, i, close)
            if end is None:
                return None
            last = end + 1
            i = end + 1
        elif ch == '"':
            end = i + 1
            esc = False
            while end < len(text):
                c = text[end]
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    break
                end += 1
            last = end + 1
            i = end + 1
        else:
            i += 1
    return last


def match_bracket(text, lb, close="]"):
    """从 lb（'[' 或 '{'）开始找到配对的右括号位置（跳过字符串内容）。"""
    opens = "[" if close == "]" else "{"
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
            elif ch == opens:
                depth += 1
            elif ch == close:
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    return None


def first_element_span(text, lb):
    """数组左括号 lb 之后第一个元素的 (左括号位置, 右括号位置)。"""
    i = lb + 1
    while i < len(text) and text[i] in " \t\r\n":
        i += 1
    if i >= len(text) or text[i] != "[":
        return None
    rb = match_bracket(text, i)
    return (i, rb) if rb is not None else None


def insert_point(text, glb, grb):
    """把字段接在组内最后一个元素后面（沿用用户示例的写法：``…},{"exclusive":1}``）。"""
    at = last_element_end(text, glb, grb)
    if at is None:
        return None
    return at, "," + FIELD


def main():
    ap = argparse.ArgumentParser(description="给 SS/SSR 专属技能补 exclusive 字段")
    ap.add_argument("--dry-run", action="store_true", help="只打印，不写文件")
    args = ap.parse_args()

    ds = get_data_source()
    # 角色目录 -> 角色名（有些存档里的 style_info[2] 与 teams.json 不一致，按目录匹配更稳）
    dir_to_role = {}
    for _team, role_name, role_path in ds.load_roles():
        role_dir = os.path.abspath(os.path.join(ROOT, str(role_path).lstrip("./")))
        dir_to_role[os.path.normcase(role_dir)] = role_name
    changed_files = 0
    changed_styles = 0
    skipped = []
    problems = []

    for rel_dir in sorted(os.listdir(os.path.join(ROOT, "角色"))):
        base = os.path.join(ROOT, "角色", rel_dir)
        if not os.path.isdir(base) or rel_dir == "__pycache__":
            continue
        for char in sorted(os.listdir(base)):
            char_dir = os.path.join(base, char)
            if not os.path.isdir(char_dir):
                continue
            for fn in TARGET_FILES:
                path = os.path.join(char_dir, fn)
                if not os.path.isfile(path):
                    continue
                rel = os.path.relpath(path, ROOT)
                text = io.open(path, encoding="utf-8").read()
                try:
                    data = json.loads(text)
                except Exception as e:
                    problems.append((rel, "JSON 解析失败 %s" % e))
                    continue
                if not isinstance(data, dict) or not data:
                    continue

                # 该角色的全部风格（用来判「第一个 SS 风格」等通用化例外）
                role = dir_to_role.get(os.path.normcase(os.path.abspath(char_dir)), "")
                if not role:
                    for style in data.values():
                        info = style.get("style_info") or []
                        if len(info) > 2 and info[2]:
                            role = str(info[2])
                            break
                style_infos = {st.name: st for st in ds.styles(role)} if role else {}

                inserts = []
                pos = 0
                for name, style in data.items():
                    span = find_array_span(text, "ActiveSkills", pos)
                    if span is None:
                        problems.append((rel, "%s 找不到 ActiveSkills" % name))
                        break
                    arr_lb, arr_rb = span
                    pos = arr_rb + 1
                    group = first_element_span(text, arr_lb)
                    if group is None:
                        problems.append((rel, "%s 的 ActiveSkills 第一项不是列表" % name))
                        continue
                    glb, grb = group
                    if '"exclusive"' in text[glb:grb]:
                        skipped.append((rel, name, "已有字段"))
                        continue
                    st = style_infos.get(name)
                    if st is None:
                        problems.append((rel, "%s 在 data_source 里找不到" % name))
                        continue
                    exclusive = any(sk.source_group == 0 and sk.is_exclusive
                                    for sk in st.skills)
                    if not exclusive:
                        skipped.append((rel, name, "非专属（已通用化）"))
                        continue
                    inserts.append(insert_point(text, glb, grb))
                    changed_styles += 1

                if not inserts:
                    continue
                new_text = text
                for at, inserted in sorted(inserts, key=lambda t: -t[0]):
                    new_text = new_text[:at] + inserted + new_text[at:]
                # 写之前先确认还是合法 JSON，且结构只多了这一个字段
                try:
                    after = json.loads(new_text)
                except Exception as e:
                    problems.append((rel, "插入后 JSON 失效：%s" % e))
                    continue
                changed_files += 1
                print("%-52s +%d 个 exclusive" % (rel, len(inserts)))
                if not args.dry_run:
                    io.open(path, "w", encoding="utf-8", newline="").write(new_text)

    print("\n文件 %d 个，专属技能 %d 个%s"
          % (changed_files, changed_styles,
             "（dry-run，未写入）" if args.dry_run else ""))
    if skipped:
        print("跳过 %d 个：" % len(skipped))
        for rel, name, why in skipped[:12]:
            print("   %-44s %-18s %s" % (rel, name, why))
        if len(skipped) > 12:
            print("   …还有 %d 个" % (len(skipped) - 12))
    if problems:
        print("问题 %d 个：" % len(problems))
        for rel, why in problems[:12]:
            print("   %-44s %s" % (rel, why))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
