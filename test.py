# -*- coding: utf-8 -*-
"""
面试候选人筛选器 —— 把面试官时间集中到"最值得深入沟通"的候选人身上。

核心逻辑（由 interviews.csv 分析得出，见 README.md）：
  无效面试的根问题不是"分数不够高"，而是渠道准入失控 ——
  员工内推 × 非商业销售部 的面试无效率 50.2%，其余全部仅 3.7%。

  因此筛选分两档：
    PRE_SCREEN  该交叉池 -> 必须先人工复筛，通过后才安排面试
    DIRECT      其余      -> 直接安排面试（该池无效率 3.7%，复筛是浪费）

  经济口径：复筛 1 次 = 12 工时；避免 1 次无效面试 = 75 工时。
  盈亏平衡拦截率 = 12/75 = 16%；本策略实际只需在复筛池里拦下 31.9% 即回本。

用法：
    python test.py                        # 运行诊断 + 全量筛选，写出 screened.csv
    python test.py --analyze-only         # 只跑诊断
    python test.py --in 新的.csv --out 结果.csv
    python test.py --id 1558 1817         # 只查指定 interview_id
"""

import argparse
import collections
import csv
import os
import sys

# ---- 口径常量（来自业务约定） ----
COST_NO_SHOW = 75      # 每次爽约损失工时
COST_RESREEN = 12      # 每次提前人工复筛花费工时
BE_RATIO = COST_RESREEN / COST_NO_SHOW          # 单次拦截盈亏平衡 16%
BE_POOL_RATE = COST_RESREEN / (0.502 * COST_NO_SHOW)   # 复筛池盈亏平衡 31.9%

PRE_SCREEN = "PRE_SCREEN"   # 需人工复筛
DIRECT = "DIRECT"           # 直接安排

ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(ROOT, "interviews.csv")
DEFAULT_OUT = os.path.join(ROOT, "screened.csv")


# ---------------- 数据读取 ----------------
def read_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit("错误：%s 没有数据行" % path)
    return rows


def flag(row):
    """is_valid -> 1 / 0 / None（None = 空值，未判定，不参与无效率分母）"""
    v = (row.get("is_valid") or "").strip()
    if v == "":
        return None
    try:
        return int(v)
    except ValueError:
        return None


def need_rescreen(row):
    """核心筛选条件：员工内推 且 非商业销售部"""
    return row.get("channel") == "员工内推" and row.get("department") != "商业销售部"


def verdict(row):
    return PRE_SCREEN if need_rescreen(row) else DIRECT


def invalid_rate(rows):
    judged = [r for r in rows if flag(r) is not None]
    if not judged:
        return 0, 0, 0.0
    inv = sum(1 for r in judged if flag(r) == 0)
    return len(judged), inv, inv / len(judged) * 100


# ---------------- 诊断 ----------------
def analyze(rows):
    print("=" * 68)
    print("诊断：无效面试到底卡在哪")
    print("=" * 68)
    total = len(rows)
    judged, inv, rate = invalid_rate(rows)
    blank = total - judged
    print("\n[全量] %d 条记录，已判定 %d，未判定(空值) %d (%.1f%%)"
          % (total, judged, blank, blank / total * 100))
    print("       无效面试 %d 次 -> 无效率 %.1f%% -> 损失 %.0f 工时"
          % (inv, rate, inv * COST_NO_SHOW))

    print("\n--- 维度1：渠道 ---")
    g = collections.defaultdict(list)
    for r in rows:
        g[r.get("channel", "")].append(r)
    for name, sub in sorted(g.items(), key=lambda kv: -invalid_rate(kv[1])[2]):
        j, i, p = invalid_rate(sub)
        print("  %-12s n=%4d 判定=%4d 无效=%3d 无效率=%5.1f%%" % (name, len(sub), j, i, p))

    print("\n--- 维度2：部门 ---")
    g = collections.defaultdict(list)
    for r in rows:
        g[r.get("department", "")].append(r)
    for name, sub in sorted(g.items(), key=lambda kv: -invalid_rate(kv[1])[2]):
        j, i, p = invalid_rate(sub)
        print("  %-12s n=%4d 判定=%4d 无效=%3d 无效率=%5.1f%%" % (name, len(sub), j, i, p))

    print("\n--- 维度3：渠道 × 部门（找出真正的交叉点）---")
    chs = sorted({r.get("channel", "") for r in rows})
    dts = sorted({r.get("department", "") for r in rows})
    g = collections.defaultdict(list)
    for r in rows:
        g[(r.get("channel", ""), r.get("department", ""))].append(r)
    print("  " + "渠道".ljust(14) + "".join(d.rjust(16) for d in dts))
    for c in chs:
        line = "  " + c.ljust(14)
        for d in dts:
            j, i, p = invalid_rate(g[(c, d)])
            line += ("%d/%d=%.0f%%" % (i, j, p)).rjust(16)
        print(line)

    print("\n--- 维度4：match_score 分层（检验「分数能不能救」）---")
    def sb(s):
        s = int(s)
        return "0-5" if s <= 5 else "6-10" if s <= 10 else "11-15" if s <= 15 \
            else "16-20" if s <= 20 else "21-25" if s <= 25 else "26-30"
    for label, cond in [("复筛池(内推×非商销)", need_rescreen),
                        ("直接池(其余)", lambda r: not need_rescreen(r))]:
        g = collections.defaultdict(list)
        for r in rows:
            if cond(r):
                g[sb(r.get("match_score", "0"))].append(r)
        print("  %s" % label)
        for b in ["0-5", "6-10", "11-15", "16-20", "21-25", "26-30"]:
            if b not in g:
                continue
            j, i, p = invalid_rate(g[b])
            print("    %-6s n=%4d 无效=%3d 无效率=%5.1f%%" % (b, len(g[b]), i, p))

    # 分组结论
    print("\n--- 结论分组 ---")
    pool = [r for r in rows if need_rescreen(r)]
    direct = [r for r in rows if not need_rescreen(r)]
    pj, pi, pp = invalid_rate(pool)
    dj, dp, dpct = invalid_rate(direct)
    print("  复筛池 (员工内推 × 非商业销售部) : 判定=%4d 无效=%3d 无效率=%5.1f%%" % (pj, pi, pp))
    print("  直接池 (其余全部)                : 判定=%4d 无效=%3d 无效率=%5.1f%%" % (dj, dp, dpct))

    print("\n--- 经济账（口径：爽约 75 工时 / 复筛 12 工时）---")
    print("  全量无效面试 %d 次 -> %5.0f 工时损失" % (inv, inv * COST_NO_SHOW))
    print("  复筛池规模 %d -> 成本 %d 工时" % (pj, pj * COST_RESREEN))
    print("  池内无效 %d -> 上限收益 %d 工时" % (pi, pi * COST_NO_SHOW))
    print("  单次拦截盈亏平衡 = 12/75 = %.1f%%" % (BE_RATIO * 100))
    print("  复筛池盈亏平衡拦截率 = 12/(%.1f%%*75) = %.1f%%  <- 池内实测 %.1f%%"
          % (pp, BE_POOL_RATE * 100, pp))
    return pj, pi, pp


# ---------------- 筛选 ----------------
def screen(rows):
    out = []
    for r in rows:
        v = verdict(r)
        r = dict(r)
        r["screen_action"] = v
        r["screen_reason"] = (
            "员工内推×非商业销售部：无效率50.2%，先人工复筛" if v == PRE_SCREEN
            else "其余分组：无效率3.7%，直接安排"
        )
        out.append(r)
    return out


def report(rows, screened):
    print("\n" + "=" * 68)
    print("筛选结果")
    print("=" * 68)
    pre = [r for r in screened if r["screen_action"] == PRE_SCREEN]
    direct = [r for r in screened if r["screen_action"] == DIRECT]
    pj, pi, pp = invalid_rate(pre)
    dj, di, dp = invalid_rate(direct)

    print("\n%-14s %5s  %6s  %10s  %12s  %12s"
          % ("动作", "条数", "占比", "池无效率", "复筛成本(工时)", "无效→节省(工时)"))
    for name, sub, j, i, p in [
        (PRE_SCREEN, pre, pj, pi, pp),
        (DIRECT, direct, dj, di, dp),
    ]:
        print("%-14s %5d  %5.1f%%  %9.1f%%  %12d  %12d"
              % (name, len(sub), len(sub) / len(screened) * 100, p,
                 len(sub) * COST_RESREEN, i * COST_NO_SHOW))

    all_j, all_i, _ = invalid_rate(screened)
    covered = pi / all_i * 100 if all_i else 0
    cost = pj * COST_RESREEN
    upper = pi * COST_NO_SHOW
    print("\n  需人工复筛 %d 条 (%.1f%%)，覆盖全部无效面试的 %.1f%%" % (pj, pj / len(screened) * 100, covered))
    print("  上限收益 %.0f - 成本 %d = 净 +%.0f 工时" % (upper, cost, upper - cost))
    print("  只要复筛池拦下 %.1f%% 就回本（池内实测无效率 %.1f%%）" % (BE_POOL_RATE * 100, pp))
    print("  直接安排 %d 条，占用复筛人力 0（该池无效率仅 %.1f%%）" % (dj, dp))

    # 敏感性
    print("\n  敏感性（复筛池实际能拦下多少）：")
    for f in (0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0):
        net = f * pi * COST_NO_SHOW - cost
        print("    拦截率 %3.0f%% -> 净 %+7.0f 工时  %s"
              % (f * 100, net, "✓ 盈利" if net >= 0 else "✗ 亏损"))
    return pre, direct


def main():
    ap = argparse.ArgumentParser(description="面试候选人筛选器")
    ap.add_argument("--in", dest="inp", default=DEFAULT_CSV, help="输入 CSV")
    ap.add_argument("--out", dest="out", default=DEFAULT_OUT, help="输出 CSV")
    ap.add_argument("--analyze-only", action="store_true", help="只诊断不写文件")
    ap.add_argument("--id", nargs="*", help="只查指定 interview_id")
    a = ap.parse_args()

    rows = read_rows(a.inp)
    pj, pi, pp = analyze(rows)

    if a.analyze_only:
        return

    if a.id:
        want = set(str(x) for x in a.id)
        rows = [r for r in rows if str(r.get("interview_id", "")).strip() in want]
        if not rows:
            sys.exit("错误：未匹配到 id %s" % ",".join(sorted(want)))

    screened = screen(rows)
    pre, direct = report(rows, screened)

    if not a.id:
        fields = list(screened[0].keys())
        with open(a.out, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(screened)
        print("\n已写出 %d 行 -> %s" % (len(screened), a.out))
    else:
        print("\n逐条结果：")
        for r in screened:
            print("  id=%-6s %-16s %-8s %s  match=%-3s  %s"
                  % (r.get("interview_id"), r.get("department"), r.get("channel"),
                     r["screen_action"], r.get("match_score"), r["screen_reason"]))


if __name__ == "__main__":
    main()
