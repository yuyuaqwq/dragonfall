# -*- coding: utf-8 -*-

from .drops import generate_equip, generate_roster_equip
from ..data import CRAFT_RECIPES, CRAFT_RECIPE_ALIASES
from ..core.index import resolve, display as _display


"""《剑与魔法》数据层 - craft.py(v48：输入中文名 → resolve 转 ID 查表；装备名 display 转中文)"""
def craft_recipe_make(name: str, affinity: str | None = None) -> dict | None:
    """按配方锻造一件装备（装备等级 = 配方 lv，名字 = 配方名）
    阶段八：名册配方（roster_id）走名册精确生成（词条 v2/需求/套装）；
    affinity = 词条倾向（20 章 4.3：攻击/防御/元素/机动）"""
    rec = CRAFT_RECIPES.get(name)
    if not rec:
        return None
    if rec.get("roster_id"):
        return generate_roster_equip(rec["roster_id"], affinity)
    # 兜底（无 roster_id 的旧配方）：随机生成 + 覆盖名
    equip = generate_equip(rec["slot"], rec["lv"], rec["quality"],
                           rec.get("weapon_type"))
    equip["name"] = _display("recipes", name)  # v48：配方名转中文（背包/存档显示用中文名）
    # v41：毕业套配方强制带套装归属（set 字段），生成时写入装备
    if rec.get("set"):
        equip["set"] = rec["set"]
    return equip

def craft_recipe_search(text: str):
    """模糊查找配方：精确名 > 别名 > 包含匹配(v48：输入中文/ID 都 resolve)"""
    rid = resolve("recipes", text)
    if rid in CRAFT_RECIPES:
        return rid
    for k, aliases in CRAFT_RECIPE_ALIASES.items():
        if text in aliases:
            return k
    for k in CRAFT_RECIPES:
        if text in _display("recipes", k):  # 中文名包含匹配
            return k
    return None

def craft_recipes_by_material(text: str, max_show: int = 8):
    """#24 材料关键词联想：按材料名模糊匹配，返回使用该材料的配方
    返回 [(name, rec), ...]（按 lv 升序），无匹配返回 []
    """
    out = []
    for name, rec in CRAFT_RECIPES.items():
        hit = False
        for m in rec["mats"]:
            m_cn = _display("materials", m)
            if text in m_cn or m_cn in text:
                hit = True
                break
        # 图纸也可联想：搜「图纸」或蓝图名时命中需图纸的配方
        if not hit and rec.get("blueprint"):
            if text == "图纸" or text in rec["blueprint"] or rec["blueprint"] in text:
                hit = True
        if hit:
            out.append((name, rec))
    out.sort(key=lambda x: x[1]["lv"])
    return out[:max_show]

def craft_recipes_for_level(player_lv: int, max_show: int = 12):
    """列出玩家可锻造(lv 门槛 ±6 内)的配方"""
    out = []
    for name, rec in CRAFT_RECIPES.items():
        if rec["lv"] <= player_lv + 6 and rec["lv"] >= max(1, player_lv - 12):
            out.append((name, rec))
    out.sort(key=lambda x: x[1]["lv"])
    return out[:max_show]
