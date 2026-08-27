# -*- coding: utf-8 -*-
"""临时脚本：逐级跨级胜率拐点扫描（只分析不改源码）

口径（与 tests/numeric_sim.py / test_numeric_equip_dependency.py 一致）：
  - 玩家 11 级，标准 39 点加点（STD_ATTR：战/拳全力、法/牧全智、游/刺全敏）
  - 怪：role=dps 普通怪，等级 11..18（等级差 0..7）
  - 每格 seeds=8 固定种子（seed 0..7）纯普攻（use_skill=False），BT.Battle 真实引擎
  - 裸装 equip={}；满装 = 标准配置（N03 锁定）：Lv.10-15 铁港系列名册 5 槽
    （FULL_RIDS + 固定生成种子 101..105），全职业同套

输出：
  ① 裸装矩阵（职业 × 怪等级胜场/8）
  ② 满装矩阵（同）
  ③ 每职业两组拐点：
     - 全胜区间（胜率 8/8 连续覆盖的等级差上限 k ⇒ 差 0..k 级内碾压）
     - 首次跌破 8/8 的等级差（若存在）
     - 打不过拐点（胜率首次跌破 6/8 的等级差；≥6/8 全程则记 '≥7 未跌破'）
  ④ 裸装 vs 满装打不过拐点等级差对比

运行（插件真实环境）：
  C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe scripts/_tmp_lv_scan.py
"""
import os
import sys
import random

_HERE = os.path.dirname(os.path.abspath(__file__))
_PLUGIN_DIR = os.path.dirname(_HERE)                       # dragonfall/
_TESTS_DIR = os.path.join(_PLUGIN_DIR, "tests")
sys.path.insert(0, _TESTS_DIR)

import numeric_sim  # noqa: E402
from numeric_sim import STD_ATTR, PLAYER_LV, class_battle_matrix  # noqa: E402
from data.plugins.dragonfall.game import content as C  # noqa: E402

# ---------------- 标准满装（N03 锁定：Lv.10-15 铁港系列名册 5 槽，固定种子生成） ----------------
FULL_RIDS = {
    "weapon": "eq_wan_dao",          # 弯刀 Lv.14 blue sword
    "helm":   "eq_chuan_zhang_mao",  # 船长帽 Lv.14 blue
    "armor":  "eq_shui_shou_jia_ke", # 水手夹克 Lv.15 blue
    "legs":   "eq_shui_shou_hu_tui", # 水手护腿 Lv.14 blue
    "boots":  "eq_hai_dao_xue",      # 海盗靴 Lv.14 blue
}
GEN_SEEDS = {slot: 100 + i for i, slot in enumerate(FULL_RIDS, start=1)}


def make_full_equip():
    equip = {}
    for slot, rid in FULL_RIDS.items():
        random.seed(GEN_SEEDS[slot])
        equip[slot] = C.generate_roster_equip(rid)
    return equip


# ---------------- 扫描参数 ----------------
CLASSES = ["战士", "法师", "牧师", "刺客", "游侠", "拳师"]   # 任务卡顺序
MONSTER_LVS = list(range(11, 19))                          # 11..18，等级差 0..7（任务卡范围）
EXT_LVS = list(range(11, 25))                              # 扩展 11..24，等级差 0..13（找满装真拐点）
SEEDS = 8


def scan(equip, lvs=None):
    """返回 {cls: [(mlv, wins, avg_round), ...]}"""
    lvs = lvs or MONSTER_LVS
    out = {}
    for cls in CLASSES:
        row = []
        for mlv in lvs:
            wins, avg = class_battle_matrix(cls, PLAYER_LV, STD_ATTR[cls],
                                            equip, "dps", mlv, seeds=SEEDS)
            row.append((mlv, wins, round(avg, 2)))
        out[cls] = row
    return out


def print_matrix(title, matrix):
    print("\n" + "=" * 78)
    print("【%s】（11 级标准加点 39 点 × 普通 dps 怪，seeds=%d 纯普攻，胜场/8）" % (title, SEEDS))
    print("=" * 78)
    header = "       | " + " | ".join("11v%d" % mlv for mlv in MONSTER_LVS)
    print(header)
    print("-" * len(header))
    for cls in CLASSES:
        cells = []
        for mlv, wins, avg in matrix[cls]:
            mark = "" if wins == 8 else ("!" if wins < 6 else "~")
            cells.append("%d/8%s" % (wins, mark))
        print("%-6s | %s" % (cls, " | ".join(cells)))
    print("（标记：空=8/8 全胜；~=6~7/8；!=跌破 6/8）")


def inflection(cls, cls_row, title=""):
    """计算拐点并打印。返回 (crush_k, first_drop_below8, lose_k)。"""
    diffs = [mlv - PLAYER_LV for mlv, _, _ in cls_row]
    wins = [w for _, w, _ in cls_row]

    # 全胜区间：从 0 开始连续的 8/8
    k = -1
    for i, w in enumerate(wins):
        if w == 8:
            k = diffs[i]
        else:
            break
    # 首次跌破 8/8
    first_b8 = None
    for i, w in enumerate(wins):
        if w < 8:
            first_b8 = diffs[i]
            break
    # 打不过拐点：首次跌破 6/8
    lose_k = None
    for i, w in enumerate(wins):
        if w < 6:
            lose_k = diffs[i]
            break
    crush_txt = "差 0..%d 级全胜（8/8）" % k if k >= 0 else "同级即非全胜"
    if first_b8 is not None:
        b8_txt = "差 %d 级首次跌破 8/8" % first_b8
    else:
        b8_txt = "差 0..%d 级均 8/8 未跌破" % diffs[-1]
    lose_txt = ("差 %d 级起打不过（<%d/8）" % (lose_k, 6)) if lose_k is not None else "全程 ≥%d/8 未跌破 6/8" % 6
    print("  %s: %s；%s；%s" % (cls, crush_txt, b8_txt, lose_txt))
    return k, first_b8, lose_k


def extended_report(equip_m, equip_m_ext, title):
    """扩展段（11v19..11v24）打印 + 用合并行算拐点。返回 {cls: (k, first_b8, lose_k)}"""
    print("\n◆ %s扩展段（11v19..11v24，继续找真拐点）：" % title)
    merged = {}
    for cls in CLASSES:
        row = equip_m[cls] + equip_m_ext[cls]
        merged[cls] = row
        ext_cells = ["%d/8" % w for _, w, _ in equip_m_ext[cls]]
        print("  %-4s 11v19..24: %s" % (cls, " ".join(ext_cells)))
    print("  拐点（合并 11..24）：")
    out = {}
    for cls in CLASSES:
        print("  ", end="")
        out[cls] = inflection(cls, merged[cls], title)
    return out


def main():
    full_equip = make_full_equip()
    print("满装标准配置（同 N03 固定种子）:")
    for slot, it in full_equip.items():
        print("  %-7s %-18s lv=%s stats=%s affixes=%s" %
              (slot, it.get("name"), it.get("lv"), it.get("stats"), it.get("affixes")))

    bare_m = scan({}, MONSTER_LVS)
    full_m = scan(full_equip, MONSTER_LVS)

    print_matrix("裸装矩阵", bare_m)
    print_matrix("满装矩阵（标准配置）", full_m)

    print("\n" + "=" * 78)
    print("【拐点总表（任务卡范围 11..18）】")
    print("=" * 78)
    print("\n◆ 裸装：")
    bares = {}
    for cls in CLASSES:
        bares[cls] = inflection(cls, bare_m[cls], "裸装")
    print("\n◆ 满装（标准配置）：")
    fulls = {}
    for cls in CLASSES:
        fulls[cls] = inflection(cls, full_m[cls], "满装")

    # ---- 扩展段：找裸装/满装的真拐点（11..24） ----
    print("\n" + "#" * 78)
    print("# 扩展扫描（11v19..11v24）——主矩阵两档在范围内都未跌破的，这里找真拐点")
    print("#" * 78)
    bare_m_ext = scan({}, [lv for lv in EXT_LVS if lv >= 19])
    full_m_ext = scan(full_equip, [lv for lv in EXT_LVS if lv >= 19])
    bares_x = extended_report(bare_m, bare_m_ext, "裸装")
    fulls_x = extended_report(full_m, full_m_ext, "满装（标准配置）")

    print("\n" + "=" * 78)
    print("【裸装 vs 满装 拐点对比（扩展 11..24 口径；打不过 = 胜率首次跌破 6/8 的等级差）】")
    print("=" * 78)
    print("  职业 | 裸装打不过(差N级) | 满装打不过(差N级) | 满装多撑几级")
    for cls in CLASSES:
        bk = bares_x[cls][2]
        fk = fulls_x[cls][2]
        b_txt = "差%d" % bk if bk is not None else "≥13 内不败"
        f_txt = "差%d" % fk if fk is not None else "≥13 内不败"
        if bk is None and fk is None:
            delta = "持平(均不败)"
        elif bk is None:
            delta = "比裸装强(裸装差%d)" % bk
        elif fk is None:
            delta = "+∞(满装不败)"
        else:
            delta = "+%d 级" % (fk - bk) if fk > bk else ("持平" if fk == bk else "%d 级(满装更早崩)" % (fk - bk))
        print("  %-4s | %-14s | %-14s | %s" % (cls, b_txt, f_txt, delta))


if __name__ == "__main__":
    main()