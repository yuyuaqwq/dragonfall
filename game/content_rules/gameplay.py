# -*- coding: utf-8 -*-
"""内容侧战斗/成长辅助（S5：自 `game/engine.py` 拆出）。

归此的内容函数（既非技能表读、也非玩家面板，但同样读游戏表/名词）：

  - `element_reaction` / `element_mark_apply` / `mech_stack_gain`：读 `MECH_CFG`
    （data/battle_config.py 机制单表）与元素印记常量
  - `check_player_level_up`：读 `C.exp_to_next` / `C.EVOLVE_LEVELS` / `C.CHAPTER_PACK`，
    调用面板公式与技能表、写 `db.event_state` 与 `store.inventory`
  - `resolve_drop`：读 `C.MATERIALS` / `C.ITEMS`

判据：**凡读游戏表/职业名 → 内容侧**。旧路径 `game.engine.*` 保留 shim re-export
（S9 收口时删；docs/ENGINE_CONTENT_SPLIT_PLAN.md §6.4）。
"""
from .. import content as C
from content.mech.class_data import MECH_CFG   # B14 收口：原 ..data.battle_config（包内单源，15 组 deep-equal）
from .panel import player_base_stats, player_final_stats
from .skills import _sk_table


# ============================================================
# 元素系统
# ============================================================
# 元素亲和可切换的系（法师）
ELEMENT_OPTIONS = ["fire", "ice", "thunder"]
ELEMENT_CN = {"fire": "火", "ice": "冰", "thunder": "雷"}
# 元素印记 key（存敌方 actor buffs，层数）
ELEMENT_MARKS = {"fire": "fire_mark", "ice": "ice_mark", "thunder": "thunder_mark"}

# ============================================================
# v2.0 元素反应（12 章 3.1，严格按策划案表）——定义见 data/battle_config.py
# 当前系 × 目标印记 → 反应：蒸发 / 超载 / 冻结（预留，法师暂无水系技能）/ 感电
# ============================================================
# （ELEMENT_REACTIONS 表本体 v125.2 B1 已下沉 data/battle_config.py，顶部 import 保持对外接口）


def element_reaction(cur_element: str, target_marks: dict) -> dict | None:
    """判定元素反应。
    cur_element: 当前系 fire/ice/thunder
    target_marks: 敌方印记 dict（key 见 ELEMENT_MARKS，值为层数）
    返回反应 dict 或 None：{"name", "mult", "clear", "extra"}
    """
    for mark_key, layers in target_marks.items():
        if layers and layers > 0:
            r = MECH_CFG["element"]["reactions"].get((cur_element, mark_key))
            if r:
                return r
    return None


def element_mark_apply(target_marks: dict, element: str, layers: int = 1, max_layers: int = 5) -> dict:
    """给目标挂元素印记(带上限)。返回更新后的印记 dict。"""
    mark_key = ELEMENT_MARKS.get(element, "")
    if not mark_key:
        return target_marks
    target_marks[mark_key] = min(max_layers, target_marks.get(mark_key, 0) + layers)
    return target_marks


# v181.M-R2b：core_resource_def / core_resource_def_by_key 已退役删除（旧 core_resources.py
# 按 class/key 查资源定义——文件本体已随 v181.M-R2c 退役删除；现资源名/cap 单源 = EFFECT_RULES（game/data/battle_rules.py），
# 展示名查 EFFECT_RULES[key].name、上限查 cap——脱战校验/技能表/药水调用点已全部改读新源）。


def mech_stack_gain(mech: str, p_mech: dict, mval: int) -> int:
    """叠层(带上限)。返回新层数。未配上限的机制不限制。"""
    cap = MECH_CFG["mech_stack"]["max"].get(mech, 99)
    return min(cap, p_mech.get(mech, 0) + mval)


# ============================================================
# 升级 / 掉落
# ============================================================

def check_player_level_up(group_id, qq_id, player: dict) -> tuple[list, dict]:
    """检查是否升级(处理多次连升)。返回 (log列表, 更新后的player)"""
    logs = []
    # v95.12 #143：消费读档惰性升级暂存的提示（get_player 已静默升级写回，这里补回提示）
    if player.get("_lv_logs"):
        logs = player.pop("_lv_logs")
    # v110 审计修复：100 级硬顶（07 章"以 100 为终极等级"，成就"达到100级"为里程碑）——
    # 原实现可无限升级为空成长；达 100 级后经验不再消费
    while player["level"] < 100 and player["exp"] >= C.exp_to_next(player["level"]):
        player["exp"] -= C.exp_to_next(player["level"])
        player["level"] += 1
        tier = player.get("class_tier", 0)
        prev_base = player_base_stats(player["class_name"], player["level"] - 1, tier)
        # v101.28l #419：升级横幅差值必须同口径裸装对比（此前新级最终属性−旧级裸装，
        # 装备/属性点/称号加成全被算进"升级成长"→ playtest 实锤虚高 50 倍/40 倍）
        new_base = player_base_stats(player["class_name"], player["level"], tier)
        # v94 #41：升级重算必须传全 7 参数（race/evolve_path/title_bonus 漏传 → 写入值与面板/战斗重算不一致）
        st = player_final_stats(player["class_name"], player["level"], player.get("equipment", {}), tier, player.get("attributes"), player.get("evolve_path", 0), player.get("_title_bonus", {}) or {}, player.get("race"))
        player["attr_pts"] = player.get("attr_pts", 0) + 3  # 每级 +3 自由属性点
        player["skill_points"] = player.get("skill_points", 0) + 1  # 每级 +1 技能点
        player["max_hp"] = st["max_hp"]
        player["max_mp"] = st["max_mp"]
        player["hp"] = st["max_hp"]
        player["mp"] = st["max_mp"]
        # v12：等级只解锁"可学习资格"，不再自动学会（要花技能点学）
        # v95 #136：available 是 sk_xxx ID，learned_now 是中文名（v46 内存层转名），
        # 必须取 info["name"] 比较，否则已学技能也计入"可学"（s not in learned_now 恒 True）
        available = [info.get("name", s) for s, info in _sk_table(player["class_name"]).items()
                     if info["lv"] <= player["level"]]
        learned_now = set(player.get("learned_skills", []))
        can_learn = [s for s in available if s not in learned_now]
        logs.append(
            f"🎉 恭喜升级！现在 {player['level']} 级！"
            f"(生命上限 +{new_base['hp'] - prev_base['hp']}, 攻击 +{new_base['atk'] - prev_base['atk']})"
            f"\n📌 属性点 +3、技能点 +1(『属性』加点 / 『技能学习 <名称>』学技能)"
        )
        if can_learn:
            # v101.30d #O54：提示语修正——可学的含 5 技能点被动（风行步/狩猎咆哮等），
            # 不再叫"新技能"误导（playtest 小蓝：提示与"新技能"概念出入）
            logs.append(f"📖 有 {len(can_learn)} 个技能可学习（含被动）！『技能学习 <技能名>』消耗技能点学会(『技能列表』查看)")
        if player["level"] == C.EVOLVE_LEVELS[1]:
            logs.append(f"🌟 你已达到 {player['level']} 级，可以转职了！(输入『转职』查看)")
        # v140 波3.3：章节礼包——每 10 级里程碑发放一次（event_state 防重复）
        if player["level"] % 10 == 0:
            try:
                from .. import db as _db
                _ck = f"chapter_pack_{player['level']}_{qq_id}"
                if not _db.get_event_state(_ck):
                    _packs = {p["lv"]: p for p in C.CHAPTER_PACK}
                    _pack = _packs.get(player["level"])
                    if _pack:
                        from ..store.inventory import add_item as _add_item
                        _got = []
                        for _iname in _pack.get("items", []):
                            _iid = C.resolve("items", _iname)
                            if _iid in C.ITEMS:
                                _add_item(group_id, qq_id, _iid, C.ITEMS[_iid])
                                _got.append(_iname)
                            else:
                                _imid = C.resolve("materials", _iname)
                                if _imid in C.MATERIALS:
                                    _add_item(group_id, qq_id, _imid, {"name": C.display("materials", _imid), "type": C.MATERIALS[_imid].get("type", "材料"), "stackable": True, "price": C.MATERIALS[_imid]["price"]})
                                    _got.append(_iname)
                        if _got:
                            _db.set_event_state(_ck, "1")
                            logs.append(f"🎁 章节里程碑达成！获得【{_pack.get('name', '礼包')}】：{'、'.join(_got)}！")
            except Exception:
                pass
    return logs, player


def resolve_drop(name: str):
    """v110 审计修复：掉落名解析——材料优先，其次 ITEMS（消耗品/副本钥匙 i_key_* 等）。

    战斗/副本掉落结算原先只认 MATERIALS，钥匙类消耗品（29 章入场钥匙）结构上发不出
    （D11 P0-2：设计 29:505「遗骸搜出龙宫宝珠」在当前架构不可实现）。返回 item ID。
    """
    mid = C.resolve("materials", name)
    if mid in C.MATERIALS:
        return mid
    for _k, _v in C.ITEMS.items():
        if _v.get("name") == name:
            return _k
    return None
