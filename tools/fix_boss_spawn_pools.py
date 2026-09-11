# -*- coding: utf-8 -*-
"""修 v180 boss 设计「合表要求」漏项：boss 常态技能池（spawn 6 元组）未同步设计身份技。

依据（设计稿 _archive_unused/workspace_20260907/boss_design/out/组A_新手区.py:13）：
  「引擎常态技能池来自 instances.py 该副本 boss 6 元组的技能数组（build_monster 直写
   skills），phases.add_skills 只在该血量阈值触发后才追加。故各 Boss 卡的身份技/常态
   循环技能必须直接写进 boss 元组技能数组——否则常态不出招。」
→ AI 权重（MONSTER_MODS.ai.weights）引用到的技能若既不在 spawn 也不在 phases，
  运行期 _skill_index 查不到 → do_skill 静默空放（tools/audit_ai_moves_resolvable.py
  报 DEAD 17 处 / 12 只怪）。

用法：python tools/fix_boss_spawn_pools.py [--apply]
"""
import os
import sys
import ast

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FILES = ["game/data/subareas.py", "game/data/instances.py"]

# 同名技能的设计专属变体 → 常态池直接换成变体（口径：设计 NEW_SKILLS 里的 Boss 专属版）
RENAME = {
    "ms_shui_xi": "ms_shui_xi_aolan",
    "ms_bing_xi": "ms_bing_xi_lord",
    "ms_zhan_chui": "ms_zhan_chui_lord",
    "ms_suo_lian": "ms_suo_lian_ding_zui",
    "ms_zhao_huan_ku_lou": "ms_zhao_ku_lou_mi",
    "ms_mei_huo_zhi_ge": "ms_mei_huo_ge_blue",
    "ms_ju_lang": "ms_ju_lang_blue",
    "ms_zhao_huan_chu_shou": "ms_zhao_chu_shou_blue",
    "ms_huo_qiang": "ms_ha_huo_qiang_qi",
    "ms_ai_hao": "ms_you_hui_hui_chang",
    "ms_long_wei": "ms_long_wei_ji_tui",
}
# 设计新增的常态身份/循环技（原池没有）→ 追加
ADD = {
    "b_goblin_chief": ["ms_lve_duo_h_ling"],
    "b_fort_ghost": ["ms_you_xiang_ji"],
    "b_dawn_elf": ["ms_yue_guang_xin", "ms_yue_hua_lian_shan", "ms_gen_xu_chan_rao_x"],
    "b_trial_knight": ["ms_dun_ji_shi_lian"],
    "b_under_dragon": ["ms_shi_lin_suan_shi", "ms_shi_gu_shen_tun"],
    # 连招链（chains[].seq 经 auto_act → ActCtx 解析，同样要求真持有）引用但未持有：
    "b_marcus": ["ms_chu_xing_xuan_du"],
    "b_storm_master": ["ms_f6_lei_bao_feng_yan", "ms_f6_feng_bao_feng_yan"],
}
TARGETS = set(ADD) | {
    "b_aolan", "b_frost_lord", "b_gray_lord", "b_king_odric",
    "b_marcus", "b_siren_queen", "b_jack_pirate", "b_dawn_elf",
}

# 设计稿逐 Boss 明示的建议数组（组A），以它为准
DESIGN_EXACT = {
    "b_goblin_chief": ["ms_lian_zhan", "ms_lve_duo_h_ling", "ms_zhao_huan", "ms_nu_hou"],
    "b_fort_ghost": ["ms_you_hui_hui_chang", "ms_you_xiang_ji", "ms_chuan_shen", "ms_zhao_huan_ku_lou"],
    "b_jack_pirate": ["ms_wan_dao", "ms_ha_huo_qiang_qi", "ms_zhao_huan_shui_gui"],
}


def new_skills(mid, old):
    if mid in DESIGN_EXACT:
        return list(DESIGN_EXACT[mid])
    out = [RENAME.get(s, s) for s in old]
    for s in ADD.get(mid, []):
        if s not in out:
            out.append(s)
    return out


def render(lst, multiline, indent, nl):
    """生成新技能列表字面量；multiline=True 时保持原多行风格（同缩进、同样式换行符）。"""
    if not multiline:
        return "[" + ", ".join('"%s"' % s for s in lst) + "]"
    inner = ("," + nl).join("%s    \"%s\"" % (indent, s) for s in lst)
    return "[" + nl + inner + nl + indent + "]"


def main(apply=False):
    for fn in FILES:
        p = os.path.join(PLUGIN_DIR, fn)
        src = open(p, encoding="utf-8", newline="").read()
        nl = "\r\n" if "\r\n" in src else "\n"
        tree = ast.parse(src)
        edits = []  # (start, end, new_text, mid, old, new)
        for node in ast.walk(tree):
            if not (isinstance(node, (ast.Tuple, ast.List)) and len(node.elts) == 6):
                continue
            try:
                vals = [ast.literal_eval(e) for e in node.elts]
            except Exception:
                continue
            mid = vals[0]
            if not isinstance(mid, str) or mid not in TARGETS:
                continue
            old = list(vals[4])
            new = new_skills(mid, old)
            if new == old:
                continue
            seg = ast.get_source_segment(src, node.elts[4])
            lines = src.splitlines(keepends=True)
            base_a = sum(len(x) for x in lines[:node.elts[4].lineno - 1])
            base_b = sum(len(x) for x in lines[:node.elts[4].end_lineno - 1])
            a = base_a + node.elts[4].col_offset
            b = base_b + node.elts[4].end_col_offset
            indent = " " * node.elts[4].col_offset
            edits.append((a, b, render(new, "\n" in seg or "\r\n" in seg, indent, nl),
                          mid, old, new))
        if not edits:
            print(f"-- {fn}: 无需改动")
            continue
        print(f"== {fn}: {len(edits)} 处")
        for a, b, txt, mid, old, new in sorted(edits, key=lambda x: -x[0]):
            print(f"  {mid}\n     - {old}\n     + {new}")
        if apply:
            for a, b, txt, mid, old, new in sorted(edits, key=lambda x: -x[0]):
                src = src[:a] + txt + src[b:]
            open(p, "w", encoding="utf-8", newline="").write(src)
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
