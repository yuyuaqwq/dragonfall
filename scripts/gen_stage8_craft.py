# -*- coding: utf-8 -*-
"""阶段八生成器：10 章名册 → CRAFT_RECIPES（锻造配方）

运行：C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe qqbot/scripts/gen_stage8_craft.py
输出：dragonfall/game/data/craft.py 的 CRAFT_RECIPES 定义（替换旧世界 235 配方）

规则：
- 名册 91 件除传说（source=legend）外全部可锻造
- 白/蓝（source 商店/锻造）：无需图纸；紫（图纸）/橙（boss）：需图纸（blueprint=装备名+图纸）
- 材料：系列主题材料（10 章 7.1 + 外域补齐），数量随等级梯度
- 配方名 = 装备名（确定性），锻造产物 = generate_roster_equip（名册精确生成）
"""
import sys, os
QQBOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, QQBOT)
from data.plugins.dragonfall.game import content as C
from data.plugins.dragonfall.game.core.index import pinyin_id

# 系列 → (主材料, 辅材料)（10 章 7.1 + 外域补齐；材料 ID 全部验证过存在）
SERIES_MATS = {
    "橡木": ("mat_shi_lai_mu_nian_ye", "mat_ye_zhu_ya"),   # 史莱姆黏液 / 野猪牙
    "铁港": ("mat_ge_bu_lin_hui_ji", "mat_hai_yao_lin_pian"),  # 哥布林徽记 / 海妖鳞片
    "圣光": ("mat_sheng_guang_jie_jing", "mat_sheng_dian_tie_kuai"),  # 圣光结晶 / 圣殿铁块
    "月语": ("mat_jing_ling_lu_jiao", "mat_yue_lang_mao_pi"),  # 精灵鹿角 / 月狼毛皮
    "霜狼": ("mat_shuang_ju_mo_xue", "mat_tie_kuang_shi"),  # 霜巨魔血 / 铁矿石
    "龙脊": ("mat_long_lin_sui_pian", "mat_shen_yuan_quan_ya"),  # 龙鳞碎片 / 深渊犬牙
    "海神": ("mat_shen_hai_shui_jing", "mat_hai_yan_jie_jing"),  # 深海水晶 / 海盐结晶
    "地底": ("mat_shen_yuan_quan_ya", "mat_shen_yuan_e_mo_jiao"),  # 深渊犬牙 / 深渊恶魔角
    "苍穹": ("mat_feng_zhi_yu", "mat_xing_hui_chen"),  # 风之羽 / 星辉尘
}

SERIES_DESC = {
    "橡木": "南境橡木镇的基础工艺，结实耐用",
    "铁港": "铁港城工匠的手艺，带着海风的咸味",
    "圣光": "晨曦城圣光教团的制式装备",
    "月语": "精灵月语工艺，轻盈灵动",
    "霜狼": "北境霜狼部族的御寒战具",
    "龙脊": "龙脊山隘的龙裔锻造技艺",
    "海神": "无尽海的海神祭器工艺",
    "地底": "幽暗地域的黑曜锻造术",
    "苍穹": "风翼群岛的苍穹工匠之作",
}


def mat_count(lv: int, base: int) -> int:
    """材料数量梯度：低级 2-3 个，高级 5-8 个"""
    return base + lv // 25


def build_recipes() -> dict:
    out = {}
    for rid, r in C.EQUIP_ROSTER.items():
        if r["source"] == "legend":
            continue  # 传说不走锻造（世界掉落/主线/声望专属）
        name = r["name"]
        key = "rec_" + pinyin_id(name)
        if key in out:
            print(f"⚠️ 配方 key 冲突: {key}（{name}）")
            continue
        m1, m2 = SERIES_MATS[r["series"]]
        mats = {m1: mat_count(r["lv"], 2)}
        if r["lv"] >= 12:
            mats[m2] = mat_count(r["lv"], 1)
        rec = {
            "slot": r["slot"],
            "quality": r["quality"],
            "lv": r["lv"],
            "mats": mats,
            "gold": r["lv"] * 8 + 20,
            "desc": SERIES_DESC[r["series"]],
            "name": name,
            "roster_id": rid,
        }
        if r.get("weapon_type"):
            rec["weapon_type"] = r["weapon_type"]
        if r["source"] in ("图纸", "boss"):
            rec["blueprint"] = f"{name}图纸"
        out[key] = rec
    return out


def main():
    recs = build_recipes()
    lines = [
        "# -*- coding: utf-8 -*-",
        '"""奥兰迪亚·余烬纪年 数据层 - craft.py（阶段八重写，2026-08-06）',
        "",
        "锻造配方 = 10 章装备名册（传说不锻造）。",
        "- 白/蓝：材料直接锻造（10 章 7.2）；紫/橙：需图纸（blueprint，『学习』解锁）",
        "- 配方名 = 装备名（确定性），产物 = generate_roster_equip（名册精确生成）",
        '- CRAFT_RECIPE_ALIASES 保留（旧世界玩家输入别名，v48 约定常驻）',
        '"""',
        "CRAFT_RECIPES = {",
    ]
    for key in sorted(recs):
        rec = recs[key]
        lines.append(f"    {key!r}: {{")
        for f in ("slot", "quality", "lv", "weapon_type"):
            if f in rec:
                v = rec[f]
                lines.append(f"        {f!r}: {v!r},")
        lines.append("        \"mats\": {")
        for mk, mv in rec["mats"].items():
            lines.append(f"            {mk!r}: {mv},")
        lines.append("        },")
        for f in ("gold", "desc", "name", "roster_id", "blueprint"):
            if f in rec:
                lines.append(f"        {f!r}: {rec[f]!r},")
        lines.append("    },")
    lines.append("}")
    # v48 约定常驻的旧世界别名（仅保留仍存活的 3 个配方 key；
    # 其余约 42 个旧换代配方 key 已悬空删除——不再整段保留旧 tail 以免重新写入死数据）
    lines.append("CRAFT_RECIPE_ALIASES = {")
    lines.append('    "rec_tie_jian": [')
    lines.append('        "铁剑",')
    lines.append('        "新手剑"')
    lines.append("    ],")
    lines.append('    "rec_xue_tu_fa_zhang": [')
    lines.append('        "学徒杖",')
    lines.append('        "法杖"')
    lines.append("    ],")
    lines.append('    "rec_lie_gong": [')
    lines.append('        "新手弓",')
    lines.append('        "短弓"')
    lines.append("    ],")
    lines.append("}")
    out_path = os.path.join(QQBOT, "data/plugins/dragonfall/game/data/craft.py")
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    # 验证
    import importlib
    sys.path.insert(0, os.path.dirname(out_path))
    sys.path.insert(0, os.path.join(QQBOT, "data/plugins/dragonfall"))
    # 读回验证：只 exec CRAFT_RECIPES 定义部分（结束锚点用 ALIASES 定义行，避开 docstring 字样）
    txt = open(out_path, encoding="utf-8").read()
    rec_part = txt[txt.index("CRAFT_RECIPES = {"):txt.index("CRAFT_RECIPE_ALIASES = {")]
    check = {}
    exec(compile(rec_part, out_path, "exec"), check)
    recs_gen = check["CRAFT_RECIPES"]
    print(f"生成 {len(recs_gen)} 个配方")
    print(f"需图纸: {sum(1 for r in recs_gen.values() if 'blueprint' in r)}")
    print(f"免图纸: {sum(1 for r in recs_gen.values() if 'blueprint' not in r)}")
    for k in ("rec_tie_jian", "rec_jin_gou_wan_dao"):
        if k in recs_gen:
            print(f"{k}: {recs_gen[k]}")
    return len(recs_gen)


if __name__ == "__main__":
    main()
