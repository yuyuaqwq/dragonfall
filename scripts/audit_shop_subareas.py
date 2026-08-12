# -*- coding: utf-8 -*-
"""全量子区域商店配货审计（2026-08-12 鱼鱼要求"仔细查"鹿香灶坊卖装备类问题）。

对每个 shop=True 的子区域，模拟 shop 命令的渲染逻辑，输出：
  子区域 → 商店类型(_sa_shop_kind) → 铁匠判定(_is_smith_shop) → 配货物品 → 挂载武器/装备
找出"不该卖武器/装备却挂了"的不合理配置。

用法：C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe scripts/audit_shop_subareas.py
"""
import os
import sys

sys.path.insert(0, r"C:\Users\yuyu\qqbot")
sys.path.insert(0, r"C:\Users\yuyu\qqbot\data\plugins\dragonfall")
os.environ["GWEN_GAME_DB"] = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\test_game_data.db"

from data.plugins.dragonfall.game import content as C
from data.plugins.dragonfall.game.commands.base import CommandBase


def shop_kind_of(name: str, funcs: list, healer: bool, shop: bool) -> str:
    """复刻 base.py _sa_shop_kind 的判定（v101.28o 收紧版，不依赖 player 对象）。"""
    funcs = funcs or []
    if "alchemy" in funcs or any(k in name for k in ("草药", "炼金")):
        return "herb"
    if "craft" in funcs or any(k in name for k in ("铁匠", "锻造", "军械", "工坊", "强化", "锻室")):
        return "smith"
    if healer or "heal" in funcs or any(k in name for k in ("酒馆", "旅店", "客栈")):
        return "tavern"
    if any(k in name for k in ("灶", "烹饪", "食铺", "磨坊", "膳房")):
        return "cook"
    if any(k in name for k in ("集市", "商行", "码头", "商店", "杂货", "货栈", "商会", "补给", "营地")):
        return "general"
    if shop or "shop" in funcs:
        return "misc"
    return None


def is_smith_of(name: str, funcs: list) -> bool:
    funcs = funcs or []
    if "炼金" in name:
        return False
    if "craft" in funcs:
        return True
    return any(k in name for k in ("铁匠", "锻造", "军械", "工坊", "强化"))


def main():
    rows = []
    for m in C.MAPS:
        mid = m.get("id", "")
        for sa in (m.get("subareas") or []):
            if not sa.get("shop"):
                continue
            name = sa["name"]
            funcs = sa.get("funcs") or []
            healer = bool(sa.get("healer"))
            kind = shop_kind_of(name, funcs, healer, True)
            is_smith = is_smith_of(name, funcs)
            sa_id = sa["id"]
            area_id = m.get("area", mid)
            items = C.SHOP_SUBAREA_ITEMS.get(sa_id)
            n_items = len(items) if items else 0
            # 会不会挂武器（shop 命令 smith 分支或 general 分支）
            n_weapons = 0
            if is_smith:
                n_weapons = len(C.SHOP_WEAPONS.get(mid) or C.SHOP_WEAPONS.get(area_id, []))
                n_equip = len(C.SHOP_EQUIP.get(mid) or C.SHOP_EQUIP.get(area_id, []))
            elif kind == "general":
                n_weapons = len(C.SHOP_WEAPONS.get(mid) or C.SHOP_WEAPONS.get(area_id, []))
                n_equip = 0
            else:
                n_equip = 0
            # 物品名（判断类型合理性）
            item_names = []
            for iid in items or []:
                it = C.ITEMS.get(iid)
                if it:
                    item_names.append(it["name"])
            flag = ""
            if kind == "general" and n_weapons > 0 and not any(k in name for k in ("集市", "商行", "码头", "商店", "杂货", "货栈", "商会", "补给", "营地")):
                flag = "⚠️ 疑似不合理(兜底general挂武器)"
            if is_smith and n_equip > 0 and not any(k in name for k in ("铁匠", "锻造", "军械", "工坊", "强化")):
                flag = "⚠️ 疑似不合理(smith挂装备)"
            rows.append((mid, sa_id, name, kind, is_smith, n_items, n_weapons, n_equip, ",".join(item_names[:6]), flag))

    print("地图 | 子区域 | 类型 | 铁匠 | 配货数 | 武器数 | 装备数 | 配货物品 | 标记")
    print("-" * 130)
    for r in rows:
        print(" | ".join(str(x) for x in r))
    print()
    bad = [r for r in rows if r[9]]
    print("⚠️ 疑似不合理共 {} 处：".format(len(bad)))
    for r in bad:
        print("  ", r[2], "→ kind={} is_smith={} 武器{} 装备{}".format(r[3], r[4], r[6], r[7]))


if __name__ == "__main__":
    main()
