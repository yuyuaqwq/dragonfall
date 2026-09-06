# -*- coding: utf-8 -*-
"""v154 测试辅助：读条命中制下，玩家行动后推进到命中结算。

用法（替代旧式 `b.player_turn(...)` 后立即断言）：
    logs, ended = b.player_turn("attack", None, p)
    b.finish_turn(p)   # 推进到玩家下次行动点，触发 cast_done（命中结算）
    # 之后断言才可靠（叠层/伤害/打断都已生效）

原理：v154 玩家行动 = 出手（排 cast_done 事件），出招读条结束才命中结算。
finish_turn 推进 _process_until(p_ct + ε)，触发所有 <= p_ct 的事件（含 cast_done）。
"""
def finish_turn(b, p):
    import game.battle as BT
    logs = []
    b._process_until(float(getattr(b, "p_ct", 0) or 0) + 0.001, logs, p)
    return logs


def player_act_advance(b, action, skill_name, p, target=None, enemy_act=True):
    """v180G B7 统一 CTB：测试侧等价命令层 player_act（出手登记 + advance 推进）。

    替代直接 `b.player_turn(...)`（现在纯登记不推进）。返回 (logs, ended)，
    ended 含 advance 推完后的战斗结束状态。who（下一决策者）单人=自己，测试不关心。
    """
    import game.battle as BT
    logs, ended, _who = b.player_act(action, skill_name, p, target=target, enemy_act=enemy_act)
    return logs, ended


def finish_enemy_cast(b, p, max_t=30.0):
    """敌方出手（_enemy_turn）后推进到 cast_done 结算。

    v154 敌方对称读条：_enemy_turn 只排敌方出招读条（cast_done 事件），
    命中结算在 _enemy_cast_done（事件触发时）。直接调 _enemy_turn 后
    需要推进事件队列才能看到伤害/免伤/反制日志。
    """
    import game.battle as BT
    logs = []
    # 找敌方 cast_done 事件时间（若无，说明是特例分支：被控/增益/蓄力）
    cast_t = None
    for ev in b._events:
        if ev[2].get("type") == "cast_done" and ev[2].get("side") == "e":
            cast_t = float(ev[0])
            break
    if cast_t is None:
        return logs
    b._process_until(cast_t + 0.001, logs, p)
    return logs


def enemy_turn_cast(b, p):
    """敌方行动 = 出手 + 推进命中结算，返回合并日志（_enemy_turn + 命中日志）。

    适配 v154 对称读条：旧测试调 _enemy_turn 后立即查日志，现在要
    推进到 cast_done 命中结算才看得到伤害/免伤日志。
    """
    logs, _ = b._enemy_turn(p)
    cast_logs = finish_enemy_cast(b, p)
    return logs + cast_logs


