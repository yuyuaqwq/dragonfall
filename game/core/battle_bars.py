# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - battle_bars.py（v139 通用挂敌身条 / 蓄力三律）

把《云海猎团》职业融合提炼的 2 个通用机制实现为纯函数模块：
1. enemy_bar  挂敌身资源条（拳师破绽 shaken / 暗影神谕诅咒 curse / 斗士晕眩）
   —— 积蓄挂在敌方身上（enemy.buffs 新键），独立于异常免疫，
      阈值递增防无限控、触发后免疫窗口、阶段转换保留部分进度
2. charge     蓄力三律（游侠电荷 / 弓手 / 时咒）
   —— 边攒边打出伤、打断仅 -1 阶不清零（P3）、满阶强制释放

数据驱动铁律：
- 不写任何职业特判（不出现 class_name 字符串比较）
- 所有数值从 battle_config ENEMY_BAR_CFG / CHARGE_CFG 读（或调用方传入）
- 无配置 = 默认不启用
- 状态存 enemy dict / player dict 新 key（随战斗序列化）
"""

# 注意：不在此处顶层 import data.battle_config（core ↔ data 循环导入）。
# CFG 配置在函数内延迟导入（与 core 层惯例一致），或由调用方传入覆盖。


def _battle_cfg(name: str) -> dict:
    """延迟读取 battle_config MECH_CFG 机制表（避免顶层循环导入）。

    支持两种导入路径：正常包上下文（相对导入）与独立加载（绝对导入回退）。
    v181 P2E-P3a：读点改查 MECH_CFG[机制键]（原直读 ENEMY_BAR_CFG/CHARGE_CFG 顶层名）。
    """
    import importlib
    try:
        from ..data.battle_config import MECH_CFG  # noqa: F401
        return MECH_CFG.get(name, {}) or {}
    except Exception:
        pass
    try:
        # 绝对导入回退（importlib 直接加载模块时相对导入无包上下文）
        bc = importlib.import_module("game.data.battle_config")
        return bc.MECH_CFG.get(name, {}) or {}
    except Exception:
        return {}



def _cfg(cfg: dict, key, default=None):
    if not isinstance(cfg, dict):
        return default
    return cfg.get(key, default)


# ============================================================
# 一、enemy_bar 挂敌身资源条
# ============================================================

def bar_def(bar_key: str) -> dict:
    """读取 bar 类型配置（ENEMY_BAR_CFG[bar_key]），无则 {}。"""
    cfg = _battle_cfg("enemy_bar").get(bar_key) if isinstance(_battle_cfg("enemy_bar"), dict) else None
    return cfg or {}


def bar_state(enemy: dict, bar_key: str) -> dict:
    """读取敌方 bar 状态（enemy.buffs[bar_key]），无则初始化。

    结构：{"val": 0, "threshold": N, "trigger_count": 0, "immune_turns": 0}
    """
    buffs = enemy.get("buffs")
    if not isinstance(buffs, dict):
        buffs = {}
        enemy["buffs"] = buffs
    bs = buffs.get(bar_key)
    if not isinstance(bs, dict):
        bd = bar_def(bar_key)
        bs = {
            "val": 0,
            "threshold": int(bd.get("threshold_base", 50) or 0),
            "trigger_count": 0,
            # 初始免疫窗口 = 0（免疫只在触发后由 bar_trigger 设置）
            "immune_turns": 0,
        }
        buffs[bar_key] = bs
    return bs


def bar_gain(enemy: dict, bar_key: str, amount: int, logs: list | None = None) -> int:
    """积蓄注入：val += amount（封顶 max），返回新值。"""
    bd = bar_def(bar_key)
    if not bd:
        return 0
    bs = bar_state(enemy, bar_key)
    mx = int(bd.get("max", 100) or 100)
    bs["val"] = min(mx, int(bs.get("val", 0) or 0) + int(amount or 0))
    if logs is not None:
        logs.append(f"💥 破绽积蓄 +{amount}（{bs['val']}/{mx}）")
    return bs["val"]


def bar_should_trigger(enemy: dict, bar_key: str) -> bool:
    """是否应触发（val ≥ threshold 且免疫期已过）。"""
    bd = bar_def(bar_key)
    if not bd:
        return False
    bs = bar_state(enemy, bar_key)
    if int(bs.get("immune_turns", 0) or 0) > 0:
        return False
    return int(bs.get("val", 0) or 0) >= int(bs.get("threshold", bd.get("threshold_base", 50)) or 0)


def bar_trigger(enemy: dict, bar_key: str, logs: list | None = None) -> bool:
    """执行触发：效果由调用方处理（本函数管理阈值递增/免疫/计数），返回是否触发。"""
    bd = bar_def(bar_key)
    if not bd:
        return False
    if not bar_should_trigger(enemy, bar_key):
        return False
    bs = bar_state(enemy, bar_key)
    # 阈值递增（防无限控）：threshold × threshold_inc，封顶 threshold_cap × base
    base = int(bd.get("threshold_base", 50) or 50)
    inc = float(bd.get("threshold_inc", 1.35) or 1.0)
    cap = float(bd.get("threshold_cap", 2.5) or 1.0)
    new_thr = int(bs.get("threshold", base) * inc)
    bs["threshold"] = min(int(base * cap), new_thr)
    bs["trigger_count"] = int(bs.get("trigger_count", 0) or 0) + 1
    # 触发后清空积蓄 + 免疫窗口
    bs["val"] = 0
    bs["immune_turns"] = int(bd.get("immune_turns", 0) or 0)
    if logs is not None:
        bname = bd.get("name", bar_key)
        logs.append(f"💢 【{bname}】触发！(第 {bs['trigger_count']} 次)")
    return True


def bar_tick(enemy: dict, bar_key: str, logs: list | None = None) -> bool:
    """刻开始：免疫期递减 + 积蓄自然衰减。返回是否触发（调用方处理效果）。"""
    bd = bar_def(bar_key)
    if not bd:
        return False
    bs = bar_state(enemy, bar_key)
    # 免疫期递减
    if int(bs.get("immune_turns", 0) or 0) > 0:
        bs["immune_turns"] = int(bs["immune_turns"]) - 1
    # 自然衰减
    decay = int(bd.get("decay_per_turn", 0) or 0)
    if decay > 0:
        bs["val"] = max(0, int(bs.get("val", 0) or 0) - decay)
    # 触发检查
    return bar_should_trigger(enemy, bar_key)


def bar_preserve(enemy: dict, bar_key: str, pct: float | None = None) -> None:
    """阶段转换保留：val 保留 pct 比例（进度遗产）。"""
    bd = bar_def(bar_key)
    if not bd:
        return
    bs = bar_state(enemy, bar_key)
    p = float(pct if pct is not None else bd.get("phase_preserve_pct", 0.5) or 0.5)
    bs["val"] = int(int(bs.get("val", 0) or 0) * p)


# ============================================================
# 二、charge 蓄力三律
# ============================================================

def charge_def(skill_info: dict) -> dict:
    """读取技能电荷配置（charge dict / charge_cfg dict），无则 {}。

    v139：数据层统一用 charge_cfg 字段（云海弓手三律翻译），charge 保留旧蓄力 int。
    charge_def 优先读 charge（dict 才读），回退读 charge_cfg。
    """
    if not isinstance(skill_info, dict):
        return {}
    c = skill_info.get("charge")
    if isinstance(c, dict):
        return c
    cc = skill_info.get("charge_cfg")
    if isinstance(cc, dict) and cc:
        return cc
    return {}


def charge_state(player: dict) -> dict:
    """玩家电荷状态：{"stages": 0, "skill": str|None, "max": int}"""
    st = player.get("v139_charge")
    if not isinstance(st, dict):
        st = {"stages": 0, "skill": None, "max": 0}
        player["v139_charge"] = st
    return st


def charge_start(player: dict, skill_info: dict, logs: list | None = None) -> bool:
    """开始蓄力：设置电荷 0 阶。返回是否成功（技能有 charge 配置）。"""
    cd = charge_def(skill_info)
    if not cd:
        return False
    mx = int(cd.get("max", _cfg(_battle_cfg("charge"), "max", 3)) or 3)
    st = charge_state(player)
    st["stages"] = 0
    st["skill"] = skill_info.get("name")
    st["max"] = mx
    if logs is not None:
        sname = skill_info.get("name", "蓄力")
        logs.append(f"⏳ 开始蓄力【{sname}】(0/{mx} 阶)…")
    return True


def charge_tick(player: dict, skill_info: dict, logs: list | None = None) -> dict:
    """蓄力刻：+1 阶 + 边攒边打出伤。

    返回 {"staged": int, "dmg_mult": float, "released": bool}：
      staged    当前阶数
      dmg_mult  本刻边攒边打的伤害倍率（0.7/1.3/1.9 按阶）
      released  是否满阶强制释放（调用方执行释放逻辑）
    """
    cd = charge_def(skill_info)
    if not cd:
        return {"staged": 0, "dmg_mult": 0.0, "released": False}
    st = charge_state(player)
    mx = int(st.get("max", _cfg(_battle_cfg("charge"), "max", 3)) or 3)
    # v139：首次蓄力记录技能名（供受击打断/满阶释放识别），切技能自动重置阶数
    cur_skill = st.get("skill")
    if cur_skill and cur_skill != skill_info.get("name"):
        st["stages"] = 0
        st["max"] = mx
    st["skill"] = skill_info.get("name")
    st["stages"] = min(mx, int(st.get("stages", 0) or 0) + 1)
    stages = st["stages"]
    dmg_list = cd.get("dmg_per_stage", _cfg(_battle_cfg("charge"), "dmg_per_stage", [0.7, 1.3, 1.9]))
    dmg = float(dmg_list[min(stages - 1, len(dmg_list) - 1)]) if dmg_list else 0.0
    if logs is not None:
        sname = skill_info.get("name", "蓄力")
        logs.append(f"⚡ 蓄力【{sname}】{stages}/{mx} 阶，边攒边打 ×{dmg}！")
    released = False
    if stages >= mx:
        released = bool(cd.get("force_release", _cfg(_battle_cfg("charge"), "force_release", True)))
        if logs is not None and released:
            logs.append(f"💥 蓄力满阶！【{sname}】强制释放！")
    return {"staged": stages, "dmg_mult": dmg, "released": released}


def charge_on_hit(player: dict, skill_info: dict, logs: list | None = None) -> bool:
    """受击：打断仅 -1 阶不清零（P3）。返回是否仍处于蓄力（stages > 0）。"""
    cd = charge_def(skill_info)
    if not cd:
        return False
    st = charge_state(player)
    if int(st.get("stages", 0) or 0) <= 0:
        return False
    pen = int(cd.get("interrupt_penalty", _cfg(_battle_cfg("charge"), "interrupt_penalty", 1)) or 1)
    st["stages"] = max(0, int(st.get("stages", 0) or 0) - pen)
    if logs is not None:
        sname = skill_info.get("name", "蓄力")
        logs.append(f"🔨 蓄力【{sname}】被打断！(剩 {st['stages']} 阶，不清零)")
    return int(st.get("stages", 0) or 0) > 0


def charge_release_power(skill_info: dict) -> dict:
    """满阶释放威力配置。返回 {"power": float, "extra": dict}。"""
    cd = charge_def(skill_info)
    if not cd:
        return {"power": 1.0, "extra": {}}
    return {
        "power": float(cd.get("release_power", _cfg(_battle_cfg("charge"), "release_power", 2.8)) or 1.0),
        "extra": cd.get("release_extra", _cfg(_battle_cfg("charge"), "release_extra", {}) or {}),
    }


def charge_clear(player: dict) -> None:
    """清除电荷状态（释放后/战斗结束）。"""
    player["v139_charge"] = {"stages": 0, "skill": None, "max": 0}


# ============================================================
# 刻开始统一入口（供 battle.py _turn_start 调用）
# ============================================================

def turn_start_bars(enemy: dict, logs: list | None = None) -> list:
    """敌方刻开始：所有已配置 bar 类型的免疫递减 + 衰减 + 触发检查。

    返回触发列表 [bar_key, ...]（调用方处理触发效果）。
    """
    out = []
    cfg_all = _battle_cfg("enemy_bar")
    if not isinstance(cfg_all, dict):
        return out
    for bar_key in cfg_all:
        if bar_tick(enemy, bar_key, logs):
            out.append(bar_key)
    return out
