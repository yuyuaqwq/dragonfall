# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - class_sets.py（阶段八重写，2026-08-06）

10 章五节名册套装注册：9 系列 5 件套（头盔/胸甲/护腿/鞋子/项链）。
- bonus_2：2 件属性百分比（引擎 set_bonus_2 消费）
- bonus_4_stats：4 件属性百分比（engine.set_bonus_2 叠加，>=4 件生效）
- bonus_4.effect：4 件特效（战斗触发型，保留旧结构兼容）
- bonus_5：5 件效果（v104 起战斗落地：battle 对敌增伤/元素增伤、battle_mech 抗寒）
- 治疗加成（圣光套 2 件）由 battle 治疗段消费（bonus_2.heal 字段）

⚠️ 旧世界毕业套（CLASS_SET_THEMES 6 职业×5 阶段）已废弃：不再动态合并进 CRAFT_RECIPES，
锻造配方 = 10 章名册（craft.py）。旧 SETS 42 条仍残留在 data/sets.py（兼容旧档 set 字段，
待确认后清理）；名册套装由 _assembly 调 _build_class_sets 注册/覆盖同名 key，不删除旧数据。

v181-P2A：套装数值表 _SERIES_SET_BONUS 已原值下沉 game/data/set_bonus_data.py
（SERIES_SET_BONUS，纯搬移零逻辑）——本模块保留装配器 _build_class_sets（注册进
SETS 的装配行为是逻辑，留在 core），经别名 _SERIES_SET_BONUS 消费数据表。
"""

from ..data import SERIES_SETS, SETS
from ..data.set_bonus_data import SERIES_SET_BONUS
from ..core.index import pinyin_id

# v181-P2A：数据表已下沉 data/set_bonus_data.py——保留原名别名，装配器零改动
_SERIES_SET_BONUS = SERIES_SET_BONUS


def _build_class_sets():
    """注册 10 章名册套装到 SETS(幂等：key 唯一，重复运行覆盖同名)。"""
    for series, set_name in SERIES_SETS.items():
        b = _SERIES_SET_BONUS[series]
        set_id = f"set_{pinyin_id(set_name)}"
        entry = {
            "quality": b["quality"],
            "icon": b["icon"],
            "bonus_2": dict(b["bonus_2"]),
            "name": set_name,
        }
        # v136 Phase6：职业套装归属（本职业 100% / 非本职业 60% 职业折扣）
        if b.get("class"):
            entry["class"] = b["class"]
        # v181-A1：圣光套任意件数持有加成（piece_heal_power）随套装注册（battle 治疗段泛读）
        if b.get("piece_heal_power") is not None:
            entry["piece_heal_power"] = b["piece_heal_power"]
        if b.get("bonus_4_stats"):
            entry["bonus_4_stats"] = dict(b["bonus_4_stats"])
        if b.get("bonus_4"):
            entry["bonus_4"] = dict(b["bonus_4"])
        if b.get("bonus_3"):
            entry["bonus_3"] = dict(b["bonus_3"])
        if b.get("bonus_3_stats"):
            entry["bonus_3_stats"] = dict(b["bonus_3_stats"])
        if b.get("bonus_5"):
            entry["bonus_5"] = dict(b["bonus_5"])
        if b.get("bonus_5_ctrl_immune"):
            # v180-B ②：5 件套控制免疫（霜狼抗寒等）随套装注册数据化
            entry["bonus_5_ctrl_immune"] = list(b["bonus_5_ctrl_immune"])
        if b.get("bonus_5_cond"):
            # v126 数值下沉：5 件战斗条件（enemy_contains/player_hp_below/dmg_mult/tag）随套装注册
            entry["bonus_5_cond"] = dict(b["bonus_5_cond"])
        SETS[set_id] = entry
