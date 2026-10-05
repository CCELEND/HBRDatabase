# -*- coding: utf-8 -*-
"""本地「角色」数据 与 cn.hbr.quest 的参考数据 全量对照。

参考数据来源（cn.hbr.quest 前端用的同一套接口）：
    https://master.hbr.quest/v1/cn/styles.json      （343 个风格）

用法（在项目根目录执行）：
    python 工具/排轴/check_data_vs_hbrquest.py             # 首次自动下载，之后用缓存
    python 工具/排轴/check_data_vs_hbrquest.py --refresh   # 强制重新下载
    python 工具/排轴/check_data_vs_hbrquest.py --all       # 连 A/S 风格也一起列出
    python 工具/排轴/check_data_vs_hbrquest.py --no-cache  # 不落盘，直接联网

输出分区：
    1) 收录范围：参考站有、本地缺的 SS/SSR 风格
    2) 风格名对不上（疑似错字/改名），附相似度建议
    3) 技能 Hit 数差异（会自动区分「真攻击」与「非攻击占位值」）
    4) 技能 SP 消耗差异（会自动区分「消耗 SP」与「消耗信念/EP」）
    5) 稀有度 / 元素 / 职能 差异

说明：脚本**只读**，不会修改任何文件。
"""

import argparse
import io
import json
import os
import re
import sys
import tempfile
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

REF_URL = "https://master.hbr.quest/v1/cn/styles.json"
CACHE_DIR = os.path.join(tempfile.gettempdir(), "hbr_quest_ref")
CACHE_FILE = os.path.join(CACHE_DIR, "styles_cn.json")

# 参考站字段 → 本地中文
ELEMENT_MAP = {"Fire": "火", "Ice": "冰", "Thunder": "雷",
               "Light": "光", "Dark": "暗"}
ROLE_MAP = {"Attacker": "攻击者", "Breaker": "破盾者", "Blaster": "破坏者",
            "Healer": "治疗者", "Buffer": "增益者", "Debuffer": "减益者",
            "Defender": "防御者", "Admiral": "指挥者", "Rider": "驰骋者"}

_DOTS = "\u30fb\u00b7\u2022\u2027\u2219\u22c5\uFF65"


def norm(text):
    """归一化名字：全角→半角、去空白、去中点（・·• 在两边写法不同）。"""
    s = unicodedata.normalize("NFKC", str(text or ""))
    s = re.sub(r"\s+", "", s)
    for d in _DOTS:
        s = s.replace(d, "")
    return s


def ref_chara(style):
    """参考站 chara 形如「茅森 月歌 — Ruka Kayamori — …」，取中文名。"""
    return norm(style.get("chara", "").split("\u2014")[0])


def load_reference(refresh=False, use_cache=True):
    if use_cache and not refresh and os.path.isfile(CACHE_FILE):
        with io.open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    print("[*] 正在下载参考数据：%s" % REF_URL)
    raw = None
    try:
        import requests
        r = requests.get(REF_URL, timeout=120)
        r.raise_for_status()
        raw = r.content
    except ImportError:
        from urllib.request import urlopen
        with urlopen(REF_URL, timeout=120) as resp:
            raw = resp.read()
    data = json.loads(raw.decode("utf-8"))
    if use_cache:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with io.open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False))
        print("[+] 已缓存：%s" % CACHE_FILE)
    return data


def load_local():
    """用排轴自己的解析器读本地数据（这样校验的就是工具真正用的结果）。"""
    os.chdir(ROOT)   # data_source 用相对路径读 ./角色/...
    from 工具.排轴.data_source import get_data_source
    ds = get_data_source()
    result = []
    for role in ds.role_names():
        for st in ds.styles(role):
            result.append((role, st))
    return result


def walk_parts(node):
    """深度遍历参考技能的 parts / strval，产出所有 part（dict）。"""
    if not isinstance(node, dict):
        return
    if node.get("skill_type"):
        yield node
    for key in ("parts", "strval"):
        for item in (node.get(key) or []):
            for sub in walk_parts(item):
                yield sub


def is_real_attack(ref_skill):
    """该技能是否有真正的「攻击」part。

    * ``AttackSkill`` / ``DamageRateChangeAttackSkill`` 等算攻击；
    * ``FixedHpDamageRateAttack``（按当前 HP 百分比伤害）按实测**不算**
      —— 它不影响 OD 也没有 Hit。
    """
    for p in walk_parts(ref_skill):
        st = str(p.get("skill_type") or "")
        if "Attack" in st and "Fixed" not in st:
            return True
    return False


def sp_cost_kind(note):
    """本地 SP 消耗字段里写的其实是别的资源时返回说明，否则 None。"""
    s = str(note or "").upper()
    if "TOKEN" in s:
        return "消耗信念(TOKEN)"
    if s.startswith("EP") or "EP" == s:
        return "消耗EP"
    if "全部SP" in str(note or ""):
        return "消耗全部SP"
    return None


def main():
    ap = argparse.ArgumentParser(description="本地角色数据 vs cn.hbr.quest 对照")
    ap.add_argument("--refresh", action="store_true", help="强制重新下载参考数据")
    ap.add_argument("--no-cache", action="store_true", help="不落盘缓存")
    ap.add_argument("--all", action="store_true", help="连 A/S 风格也一起列出")
    ap.add_argument("--max", type=int, default=40, help="每节最多列出多少条")
    ap.add_argument("--out", default=None, help="把报告同时写入该文件（UTF-8）")
    args = ap.parse_args()

    buf = None
    old_stdout = sys.stdout
    if args.out:
        buf = io.StringIO()
        sys.stdout = buf
    try:
        _run(args)
    finally:
        sys.stdout = old_stdout
    if args.out:
        with io.open(args.out, "w", encoding="utf-8") as f:
            f.write(buf.getvalue())
        print("[+] 报告已写入：%s" % args.out)


def _run(args):
    ref = load_reference(refresh=args.refresh, use_cache=not args.no_cache)
    local = load_local()
    print("[+] 参考风格 %d 个；本地风格 %d 个" % (len(ref), len(local)))

    ref_by_id = {s.get("id"): s for s in ref}
    ref_by_key = {}
    for s in ref:
        ref_by_key.setdefault((ref_chara(s), norm(s.get("name"))), s)

    matched, unmatched = [], []
    used_keys = set()
    for role, st in local:
        r = None
        sid = getattr(st, "style_id", None)
        if sid is not None:
            try:
                r = ref_by_id.get(int(sid))
            except (TypeError, ValueError):
                r = None
        key = (norm(role), norm(st.name))
        if r is None:
            r = ref_by_key.get(key)
        if r is not None:
            matched.append((role, st, r))
            used_keys.add((ref_chara(r), norm(r.get("name"))))
        else:
            unmatched.append((role, st))

    # ---- 1) 收录范围 ----
    missing = [s for s in ref if (ref_chara(s), norm(s.get("name"))) not in used_keys]
    if not args.all:
        missing_show = [s for s in missing if s.get("tier") in ("SS", "SSR")]
    else:
        missing_show = missing
    print("\n=== 1) 参考站有、本地没有的风格（%d 个）===" % len(missing_show))
    for s in sorted(missing_show, key=lambda x: x.get("id", 0))[:args.max]:
        print("   %-4s id=%-9s %-10s %s" % (
            s.get("tier"), s.get("id"), ref_chara(s), s.get("name")))
    if len(missing_show) > args.max:
        print("   ...还有 %d 个" % (len(missing_show) - args.max))

    # ---- 2) 名字对不上 ----
    print("\n=== 2) 本地有、参考站对不上名字的风格（疑似错字/改名，%d 个）==="
          % len(unmatched))
    import difflib
    by_chara = {}
    for s in ref:
        by_chara.setdefault(ref_chara(s), []).append(s)
    for role, st in unmatched[:args.max]:
        cands = by_chara.get(norm(role), [])
        best = difflib.get_close_matches(
            norm(st.name), [norm(c.get("name")) for c in cands], n=1, cutoff=0.5)
        hint = ""
        if best:
            for c in cands:
                if norm(c.get("name")) == best[0]:
                    hint = "  ←→ 参考「%s」id=%s tier=%s" % (
                        c.get("name"), c.get("id"), c.get("tier"))
                    break
        print("   %-4s %-10s 「%s」%s" % (st.rarity, st.career or role,
                                          st.name, hint))
    if len(unmatched) > args.max:
        print("   ...还有 %d 个" % (len(unmatched) - args.max))

    # ---- 3) 技能对照 ----
    bad_sp, bad_hits, notfound, not_attack_ok = [], [], [], []
    checked = 0
    for role, st, r in matched:
        ref_skills = {norm(k.get("name")): k for k in (r.get("skills") or [])}
        for sk in st.skills:
            rk = ref_skills.get(norm(sk.name))
            if rk is None:
                notfound.append((role, st.name, sk.name))
                continue
            checked += 1
            # SP 消耗
            rh = rk.get("hit_count")
            rsp = rk.get("sp_cost")
            if rsp is not None and sk.sp_cost != rsp:
                kind = sp_cost_kind(getattr(sk, "sp_cost_note", None))
                if kind:
                    not_attack_ok.append((role, st.name, sk.name, sk.sp_cost,
                                          rsp, kind))
                else:
                    bad_sp.append((role, st.name, sk.name, sk.sp_cost, rsp))
            # Hit 数
            if rh is not None:
                want = None if rh < 0 else rh
                if sk.hits != want:
                    if not is_real_attack(rk):
                        not_attack_ok.append(
                            (role, st.name, sk.name, sk.hits, rh,
                             "参考为占位值（无攻击 part）"))
                    else:
                        bad_hits.append((role, st.name, sk.name, sk.hits, rh))

    print("\n=== 3) 技能 Hit 数差异（%d 处）===" % len(bad_hits))
    for role, style, skill, a, b in bad_hits[:args.max]:
        print("   %-8s %-16s %-16s 本地=%-5s 参考=%s" % (role, style, skill, a, b))

    print("\n=== 4) 技能 SP 消耗差异（%d 处）===" % len(bad_sp))
    for role, style, skill, a, b in bad_sp[:args.max]:
        print("   %-8s %-16s %-16s 本地=%-5s 参考=%s" % (role, style, skill, a, b))

    # ---- 5) 属性 ----
    bad_attr = []
    for role, st, r in matched:
        if (st.rarity or "") != (r.get("tier") or ""):
            bad_attr.append((st.name, "稀有度", st.rarity, r.get("tier")))
        want_el = "".join(sorted(ELEMENT_MAP.get(e, e)
                                 for e in (r.get("elements") or [])))
        local_el = "".join(sorted(st.element or ""))
        if want_el != local_el:
            bad_attr.append((st.name, "元素", local_el or "无", want_el or "无"))
        want_role = ROLE_MAP.get(r.get("role") or "", r.get("role") or "")
        if want_role and (st.career or "") != want_role:
            bad_attr.append((st.name, "职能", st.career, want_role))
    print("\n=== 5) 属性差异（稀有度/元素/职能，%d 处）===" % len(bad_attr))
    for name, field, a, b in bad_attr[:args.max]:
        print("   %-16s %-6s 本地=%-6s 参考=%s" % (name, field, a, b))

    # ---- 汇总 ----
    print("\n" + "=" * 60)
    print("对照技能 %d 个 | 缺风格 %d | 名字对不上 %d | "
          "Hit 差异 %d | SP 差异 %d | 属性差异 %d"
          % (checked, len(missing_show), len(unmatched), len(bad_hits),
             len(bad_sp), len(bad_attr)))
    print("（另有 %d 处是「消耗信念/EP」或「非攻击占位值」，属正常，未计入差异）"
          % len(not_attack_ok))
    print("参考数据缓存：%s" % CACHE_FILE)


if __name__ == "__main__":
    main()
