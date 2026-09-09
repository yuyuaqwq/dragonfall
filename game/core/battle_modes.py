# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - battle_modes.py（v139 通用状态机：dual_form / focus / vent）

把《云海猎团》职业融合提炼的 3 个通用状态机实现为纯函数模块：
1. dual_form  双形态（狂战士狂暴 / 龙裔龙焰 / 暮影影舞 / 淬势者倾泻）
   —— 免费切换承重墙、P1 归零无惩罚、P3 受击不清零（单刻封顶）
2. focus      架设态（法师元素架设 / 时咒时间凝滞）
   —— 站桩换火力：增伤 + 受击加重 + 打断不清零（资源保留）
3. vent       排气节流阀（游侠凝神屏息 / 星语者猎印满 5）
   —— 满值强制排气 + 位移泄压 + 排气后段数补偿

数据驱动铁律：
- 本模块不写任何职业特判（不出现 class_name 字符串比较）
- 所有数值从 player dict 的 dual_form/focus/vent 数据字段 + battle_config CFG 读
- 无字段 = 默认不启用（兼容旧存档/旧职业）
- 状态存 player dict 内新 key（v139_modes），随玩家存档序列化
"""

# 注意：不在此处顶层 import data.battle_config（core ↔ data 循环导入）。
# CFG 配置在函数内延迟导入（与 core 层惯例一致），或由调用方传入覆盖。


def _battle_cfg(name: str) -> dict:
    """延迟读取 battle_config MECH_CFG 机制表（避免顶层循环导入）。

    支持两种导入路径：正常包上下文（相对导入）与独立加载（绝对导入回退）。
    v181 P2E-P3a：读点改查 MECH_CFG[机制键]（原直读 DUAL_FORM_CFG/FOCUS_CFG/VENT_CFG 顶层名）。
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
    """安全读取配置（缺失返回默认）。"""
    if not isinstance(cfg, dict):
        return default
    return cfg.get(key, default)


def modes_state(player: dict) -> dict:
    """读取玩家 v139 模式状态 dict（无则初始化空）。"""
    st = player.get("v139_modes")
    if not isinstance(st, dict):
        st = {}
        player["v139_modes"] = st
    return st


# ============================================================
# 一、dual_form 双形态
# ============================================================

def dual_form_def(player: dict) -> dict:
    """读取玩家 dual_form 数据定义（v139 形态字段——原 core_resources.py 定义随 R2c 退役，字段值
    留档 docs/REFACTOR_v181_CLASS_MECH_ASSEMBLY.md『v139 形态层设计留档』章 §1），无则 {}。"""
    return player.get("dual_form") or {}


def dual_form_state(player: dict) -> dict:
    """当前形态状态：{"form": "base"|"alt", "turns_left": int, "auto": bool}"""
    st = modes_state(player)
    df = st.get("dual_form")
    if not isinstance(df, dict):
        df = {"form": "base", "turns_left": 0, "auto": False}
        st["dual_form"] = df
    return df


def dual_form_active(player: dict) -> bool:
    """是否处于第二形态（alt）。"""
    return dual_form_state(player).get("form") == "alt"


def dual_form_can_enter(player: dict, res_value: int) -> bool:
    """是否能进入第二形态：资源 ≥ enter_requirement。"""
    d = dual_form_def(player)
    if not d:
        return False
    req = d.get("enter_requirement", _cfg(_battle_cfg("dual_form"), "enter_requirement", 10))
    return int(res_value or 0) >= int(req or 0)


def dual_form_enter(player: dict, logs: list | None = None) -> bool:
    """进入第二形态（免费切换，不占行动）。返回是否成功。"""
    d = dual_form_def(player)
    if not d:
        return False
    df = dual_form_state(player)
    if df.get("form") == "alt":
        return False
    df["form"] = "alt"
    df["auto"] = bool(d.get("auto_enter", False))
    df["turns_left"] = int(d.get("duration", _cfg(_battle_cfg("dual_form"), "auto_duration", 3)) or 0)
    if logs is not None:
        fname = d.get("form") or "第二形态"
        logs.append(f"⚡ 进入【{fname}】！")
    return True


def dual_form_tick(player: dict, logs: list | None = None) -> list:
    """刻开始结算：维持成本 + 自动形态计时 + 强制回基础形态检查。

    返回日志列表（追加到调用方 logs）。
    """
    out = []
    d = dual_form_def(player)
    if not d:
        return out
    df = dual_form_state(player)
    if df.get("form") != "alt":
        return out
    # 自动形态（暮影影舞）：turns_left 递减，归零自动退出
    if df.get("auto"):
        left = int(df.get("turns_left", 0) or 0) - 1
        df["turns_left"] = max(0, left)
        if left <= 0:
            df["form"] = "base"
            if logs is not None:
                out.append("🌫️ 影舞态消退，回归常态。")
        return out
    # 手动形态（狂战士狂暴/龙裔龙焰）：维护成本从资源扣（由调用方传资源，本函数只返回应扣量）
    # v153：maintain_cost 支持浮点（狂暴每刻 −0.6 层），调用方按 float 扣
    mc = float(d.get("maintain_cost", _cfg(_battle_cfg("dual_form"), "maintain", 1)) or 0)
    if mc > 0:
        out.append({"maintain_cost": mc})
    return out


def dual_form_hit(player: dict, logs: list | None = None) -> int:
    """受击结算：返回应扣资源量（P3：不清零、单刻封顶 hit_cost_cap）。

    注：实际扣资源由调用方执行（本函数保持纯函数不写 resources）。
    """
    d = dual_form_def(player)
    if not d:
        return 0
    df = dual_form_state(player)
    if df.get("form") != "alt":
        return 0
    # P3 保护：自动形态（影舞）受击不清空
    if df.get("auto") and d.get("no_hit_clear"):
        return 0
    hc = int(d.get("hit_cost", _cfg(_battle_cfg("dual_form"), "hit", 1)) or 0)
    cap = int(d.get("hit_cost_cap", _cfg(_battle_cfg("dual_form"), "cap", 1)) or hc)
    return max(0, min(cap, hc))


def dual_form_force_return(player: dict, res_value: int) -> bool:
    """是否应强制回基础形态（资源 < force_return）。"""
    d = dual_form_def(player)
    if not d:
        return False
    df = dual_form_state(player)
    if df.get("form") != "alt" or df.get("auto"):
        return False
    fr = int(d.get("force_return", _cfg(_battle_cfg("dual_form"), "force_return", 4)) or 0)
    return int(res_value or 0) < fr


def dual_form_exit(player: dict, logs: list | None = None) -> bool:
    """退出第二形态（免费）。P1：归零无惩罚。返回是否成功。"""
    d = dual_form_def(player)
    if not d:
        return False
    df = dual_form_state(player)
    if df.get("form") != "alt":
        return False
    df["form"] = "base"
    df["auto"] = False
    df["turns_left"] = 0
    if logs is not None:
        fname = d.get("form") or "第二形态"
        logs.append(f"🔙 退出【{fname}】，回归常态。")
    return True


def dual_form_mult(player: dict) -> float:
    """形态增伤倍率（alt 形态 = 1 + dmg_bonus）。"""
    d = dual_form_def(player)
    if not d:
        return 1.0
    if dual_form_state(player).get("form") != "alt":
        return 1.0
    bonus = float(d.get("dmg_bonus", _cfg(_battle_cfg("dual_form"), "dmg_bonus", 0.20)) or 0.0)
    return 1.0 + bonus


def dual_form_lock_gain(player: dict) -> bool:
    """形态中是否锁死资源累积（暮影影舞 lock_gain）。"""
    d = dual_form_def(player)
    if not d:
        return False
    df = dual_form_state(player)
    return df.get("form") == "alt" and bool(d.get("lock_gain", False))


# ============================================================
# 二、focus 架设态
# ============================================================

def focus_def(player: dict) -> dict:
    """读取玩家 focus 数据定义，无则 {}。"""
    return player.get("focus") or {}


def focus_state(player: dict) -> dict:
    """当前专注状态：{"active": bool, "turns": int}"""
    st = modes_state(player)
    fs = st.get("focus")
    if not isinstance(fs, dict):
        fs = {"active": False, "turns": 0}
        st["focus"] = fs
    return fs


def focus_active(player: dict) -> bool:
    return bool(focus_state(player).get("active"))


def focus_can_enter(player: dict) -> bool:
    """是否能进入专注（不检查资源，由调用方决定动作入口）。"""
    return bool(focus_def(player))


def focus_enter(player: dict, logs: list | None = None) -> bool:
    """进入专注。返回是否成功。"""
    d = focus_def(player)
    if not d:
        return False
    fs = focus_state(player)
    if fs.get("active"):
        return False
    fs["active"] = True
    fs["turns"] = 0
    if logs is not None:
        logs.append("🧘 进入专注施法状态！")
    return True


def focus_tick(player: dict, logs: list | None = None) -> dict:
    """刻开始结算：专注计时 + max_turns 检查。

    返回 {"gain": int, "expired": bool} —— gain=本刻额外资源（enter_gain 首刻 + gain_per_turn），
    expired=是否因超时自动退出。
    """
    d = focus_def(player)
    if not d:
        return {"gain": 0, "expired": False}
    fs = focus_state(player)
    if not fs.get("active"):
        return {"gain": 0, "expired": False}
    fs["turns"] = int(fs.get("turns", 0) or 0) + 1
    gain = int(d.get("gain_per_turn", _cfg(_battle_cfg("focus"), "gain_per_turn", 1)) or 0)
    if fs["turns"] == 1:
        gain += int(d.get("enter_gain", _cfg(_battle_cfg("focus"), "enter_gain", 1)) or 0)
    mx = int(d.get("max_turns", _cfg(_battle_cfg("focus"), "max_turns", 3)) or 3)
    if fs["turns"] >= mx:
        fs["active"] = False
        if logs is not None:
            logs.append("⏳ 专注时间结束，回归常态。")
        return {"gain": gain, "expired": True}
    return {"gain": gain, "expired": False}


def focus_on_hit(player: dict, logs: list | None = None) -> bool:
    """受击：打断判定（interrupt_rate 概率）。返回是否被打断（资源保留，只退出专注）。"""
    d = focus_def(player)
    if not d:
        return False
    fs = focus_state(player)
    if not fs.get("active"):
        return False
    rate = float(d.get("interrupt_rate", _cfg(_battle_cfg("focus"), "interrupt_rate", 0.30)) or 0.0)
    import random
    if random.random() < rate:
        fs["active"] = False
        if logs is not None:
            logs.append("💥 专注被打破！（资源保留）")
        return True
    return False


def focus_mult(player: dict, skill_info: dict | None = None) -> float:
    """专注增伤倍率。no_burst_skills=True 时：耗资源大爆发技不吃增伤（防 EQ 超上限）。"""
    d = focus_def(player)
    if not d:
        return 1.0
    fs = focus_state(player)
    if not fs.get("active"):
        return 1.0
    if d.get("no_burst_skills") and skill_info:
        # 消耗核心资源的技能（res_cost 非空）不享受专注增伤
        if skill_info.get("res_cost") or skill_info.get("consume_all"):
            return 1.0
    bonus = float(d.get("dmg_bonus", _cfg(_battle_cfg("focus"), "dmg_bonus", 0.40)) or 0.0)
    return 1.0 + bonus


def focus_taken_bonus(player: dict) -> float:
    """专注中受击加重倍率（默认 1.0，专注中 1 + taken_bonus）。"""
    d = focus_def(player)
    if not d:
        return 1.0
    fs = focus_state(player)
    if not fs.get("active"):
        return 1.0
    bonus = float(d.get("taken_bonus", _cfg(_battle_cfg("focus"), "taken_bonus", 0.20)) or 0.0)
    return 1.0 + bonus


def focus_blocked(action: str, player: dict) -> bool:
    """专注中行动拦截：blocked 列表内行动被禁（可防御/道具）。"""
    d = focus_def(player)
    if not d:
        return False
    fs = focus_state(player)
    if not fs.get("active"):
        return False
    blocked = d.get("blocked", _cfg(_battle_cfg("focus"), "blocked", ("attack", "skill", "swap")))
    return action in blocked


def focus_exit(player: dict, logs: list | None = None) -> bool:
    """主动退出专注（free_exit 免费无损）。返回是否成功。"""
    d = focus_def(player)
    if not d:
        return False
    fs = focus_state(player)
    if not fs.get("active"):
        return False
    fs["active"] = False
    fs["turns"] = 0
    if logs is not None:
        logs.append("🧘 解除专注状态。")
    return True


# ============================================================
# 三、vent 排气节流阀
# ============================================================

def vent_def(player: dict) -> dict:
    """读取玩家 vent 数据定义，无则 {}。"""
    return player.get("vent") or {}


def vent_should_trigger(player: dict, res_value: int) -> bool:
    """是否应触发排气（资源 ≥ trigger）。"""
    d = vent_def(player)
    if not d:
        return False
    trig = int(d.get("trigger", _cfg(_battle_cfg("vent"), "trigger", 100)) or 0)
    if "vent_at" in d:  # 星语者猎印用 vent_at 键
        trig = int(d.get("vent_at", 5) or 0)
    return int(res_value or 0) >= trig


def vent_apply(player: dict, logs: list | None = None) -> dict:
    """执行排气：资源重置 + 下刻段数补偿。

    返回 {"reset_to": int, "seg_bonus": int} —— 调用方负责把资源设为 reset_to。
    """
    d = vent_def(player)
    if not d:
        return {"reset_to": 0, "seg_bonus": 0}
    reset = int(d.get("reset", _cfg(_battle_cfg("vent"), "reset", 0)) or 0)
    seg = int(d.get("seg_bonus", _cfg(_battle_cfg("vent"), "seg_bonus", 1)) or 0)
    st = modes_state(player)
    st["vented"] = {"turns": int(_cfg(_battle_cfg("vent"), "bonus_duration", 1) or 1), "seg_bonus": seg}
    if logs is not None:
        logs.append("💨 气息排空，蓄势待发！")
    return {"reset_to": reset, "seg_bonus": seg}


def vent_relief(player: dict, amount: int | None = None, logs: list | None = None) -> int:
    """位移/闪避泄压：返回应扣资源量（调用方执行）。"""
    d = vent_def(player)
    if not d:
        return 0
    if amount is None:
        amount = int(d.get("vent_on_dodge", _cfg(_battle_cfg("vent"), "vent_on_dodge", 15)) or 0)
    if logs is not None and amount > 0:
        logs.append(f"💨 身法灵动，泄压 {amount}！")
    return max(0, int(amount or 0))


def vent_seg_bonus(player: dict) -> int:
    """当前是否享受排气后段数补偿（bonus_duration 刻内）。"""
    st = modes_state(player)
    v = st.get("vented")
    if not isinstance(v, dict):
        return 0
    if int(v.get("turns", 0) or 0) <= 0:
        return 0
    v["turns"] = int(v["turns"]) - 1
    return int(v.get("seg_bonus", 0) or 0)


# ============================================================
# 刻开始统一入口（供 battle.py _turn_start 调用）
# ============================================================

def turn_start_modes(player: dict, res_read_fn, res_spend_fn, logs: list | None = None) -> list:
    """刻开始统一处理 dual_form/focus/vent 三状态机。

    res_read_fn(key) -> int  读取资源值
    res_spend_fn(key, amount) -> bool  扣资源（返回是否成功）
    返回日志列表（追加到调用方）。
    """
    out = []
    # 1. dual_form 刻结算（维护成本）
    d = dual_form_def(player)
    if d:
        out.extend(dual_form_tick(player, logs))
        for item in out:
            if isinstance(item, dict) and "maintain_cost" in item:
                key = d.get("key", "rage")
                mc = item["maintain_cost"]
                if res_spend_fn(key, mc):
                    if logs is not None:
                        fname = d.get("form") or "形态"
                        out.append(f"⚡【{fname}】维持消耗 {mc}。")
                # 强制回基础形态检查
                if dual_form_force_return(player, res_read_fn(key)):
                    dual_form_exit(player, logs)
                    if logs is not None:
                        out.append("⚠️ 力量不支，被迫回到常态！")
    # 2. vent 排气检查（满值强制排气）
    v = vent_def(player)
    if v:
        key = v.get("key", "energy")
        if vent_should_trigger(player, res_read_fn(key)):
            r = vent_apply(player, logs)
            res_spend_fn(key, res_read_fn(key))  # 清零（实际扣当前值）
            if logs is not None:
                out.append(f"💨 气息满溢，自动排气！(重置 {r['reset_to']})")
    # 3. focus 刻结算（额外资源 + 超时退出）
    f = focus_def(player)
    if f:
        r = focus_tick(player, logs)
        if r.get("gain"):
            key = f.get("key", "element")
            if res_spend_fn is not None:
                # 反向：focus 是加资源，但本入口只给 spend；调用方在 battle.py 用 _res_gain
                out.append({"focus_gain": r["gain"], "key": key})
    return out
