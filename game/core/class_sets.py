# -*- coding: utf-8 -*-

from ..data import CLASS_SET_STAGES, CLASS_SET_THEMES, CRAFT_RECIPES, SETS, WT_CN
from ..core.index import pinyin_id


"""《剑与魔法》数据层 - class_sets.py（v48：生成 key 用 pinyin ID，避免中文 key 重复）"""
def _build_class_sets():
    # v53.1：wtype 是中文（theme["wtype"]），用 WT_CN 反向映射转英文 ID。
    # 不能用 resolve("weapon_types", ...) —— 本函数在 _assembly 里比 weapon_types 索引构建更早执行，
    # resolve 查不到会原样返回中文，导致生成配方 weapon_type="剑" → 锻造时 generate_equip KeyError。
    _wt_rev = {v: k for k, v in WT_CN.items()}
    for cls, theme in CLASS_SET_THEMES.items():
        for idx, st in enumerate(CLASS_SET_STAGES):
            lv = st["lv"]
            label = st["label"]
            prefix = theme["stages"][idx]
            # 套装效果注册（同阶段各职业套名唯一）—— v48：SETS key 转 ID
            set_id = f"set_{pinyin_id(prefix)}"
            SETS[set_id] = {
                "quality": st["quality"], "icon": theme["icon"],
                "bonus_2": theme["bonus_2"], "bonus_4": theme["bonus_4"],
                "name": prefix,
            }
            # 5 件套配方：独立武器名 + 防具（套名+职业部位后缀）—— v48：key 用 pinyin ID
            parts = [
                ("weapon", theme["wtype"], theme["weapons"][idx]),
                ("helm",   None,        f"{prefix}{theme['parts'][0]}"),
                ("armor",  None,        f"{prefix}{theme['parts'][1]}"),
                ("legs",   None,        f"{prefix}{theme['parts'][2]}"),
                ("boots",  None,        f"{prefix}{theme['parts'][3]}"),
            ]
            for slot, wtype, name in parts:
                rid = f"rec_{pinyin_id(name)}"
                if rid in CRAFT_RECIPES:
                    continue  # v48：ID 版已存在（craft.py 已内置）→ 跳过，防重复
                CRAFT_RECIPES[rid] = {
                    "slot": slot, "quality": st["quality"], "lv": lv,
                    "weapon_type": _wt_rev.get(wtype) if wtype else None,
                    "mats": dict(st["mats"]),
                    "gold": st["gold"],
                    "blueprint": f"{prefix}图纸",
                    "class": cls, "set": set_id,
                    "desc": f"{prefix}套装·{label}阶核心部件",
                    "name": name,
                }
