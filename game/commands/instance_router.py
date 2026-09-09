# -*- coding: utf-8 -*-
"""v181.N5b4-5a R1：副本战斗行动命令层 Router（battle2 原生重写）。

v3 蓝图 docs/REFACTOR_v181P4_N5B5a_instance_mainline.md §4：
InstanceBattleRouter 接管副本行动入口（战斗执行/轮转/结算全新代码），
instance.py 老 _instance_act 停用不手术（R3 删除清单）；玩法壳函数保留引用。

依赖：
- instance_battle.py（控制器：build_battle/act/sync_views/next_actor_key）
- InstanceCmds 玩法壳方法（self._instance_kill_reward/_instance_victory/
  _instance_defeat/_instance_save/_instance_battle_footer/_player/... 运行时
  Main/InstanceCmds 实例拥有，本类不静态 import instance.py）
- 引擎零改动：本文件不 import 旧 game.battle

调用协议对齐旧 _instance_act：
    async for _r in self._instance_router(event, group_id, qq_id, player, st,
                                          action, skill_name, target):
        yield _r
"""
from __future__ import annotations

import time

from .. import content as C
from .. import db
from .. import engine as E
from .base import CommandBase
from . import instance_battle as IB

INSTANCE_TIMEOUT = 60  # 副本行动超时（秒）——与 instance.py 模块常量同源（v101.30d 60s）


class InstanceRouterCmds(CommandBase):
    """副本战斗行动路由薄壳（battle2 版，v3 §4.1-4.5 全逻辑）。"""

    # ------------------------------------------------------------------
    # 4.1 入口守卫 + 轮转
    # ------------------------------------------------------------------
    def _router_authoritative_st(self, st: dict) -> dict:
        """权威大陆实例 st：world_id=inst: 时优先取大陆实例（队友/自己可能已行动，
        大陆实例永远最新）；无大陆实例（测试/旧镜像）回落传入 st。"""
        _wid = (st or {}).get("world_id") or ""
        if _wid.startswith("inst:"):
            try:
                _live = C.get_instance_st(_wid)
                if _live is not None and not _live.get("_expired"):
                    return _live
            except Exception:
                pass
        return st

    def _router_no_enemy_hint(self, event, group_id, st):
        """肃清/无敌人引导（对应旧 _instance_act 2465-2483，读视图）。"""
        if st.get("stage_pending"):
            return event.plain_result("当前区域还有敌人潜伏！『探索』找到它们～")
        nxt = ""
        stages = st.get("inst_stages") or []
        idx = st.get("stage_idx", 0)
        if stages and idx < len(stages) - 1:
            nxt = f"前方是【{stages[idx + 1]['name']}】……输入『深入』继续推进！"
        else:
            nxt = "这是最后一层，输入『深入』挑战 Boss！"
        return event.plain_result(f"当前区域的敌人已被肃清！\n{nxt}")

    def _router_wait_hint(self, event, group_id, st, cur_key):
        members = st.get("members") or []
        try:
            st["turn"] = members.index(cur_key)
        except Exception:
            st["turn"] = 0
        cur_name = (self._player(group_id, cur_key) or {}).get("name", cur_key)
        return event.plain_result(f"⏳ 现在是 {cur_name} 的刻，等待 TA 行动～")

    # ------------------------------------------------------------------
    # 4.4 结算辅助（薄壳；账务 5b 完善）
    # ------------------------------------------------------------------
    def _router_collect_killed(self, st: dict, since_prev: bool = False) -> list:
        """battle killed（uid 累计）→ 死亡敌人单位 dict 列表。

        v3 §4.4 死亡账：battle2 击杀记录（state.killed uid）转玩法壳消费的
        单位快照（st[\"_last_killed\"]/击杀任务）。死亡 actor 不从 sides 移除
        （只进 killed），因此从 enemy side 按 uid 取 hp<=0 的 actor 快照。
        副本内 state.killed 为整场累计；玩家行动一段只消费新增段（上一段
        已入账的过滤由调用方控制——见 _router_advance_killed）。
        """
        _b = st.get("battle") or {}
        uids = set(_b.get("killed") or [])
        out = []
        for a in (IB._enemies_of(st) or []):
            if a.get("uid") in uids and int(a.get("hp", 1) or 0) <= 0:
                out.append(dict(a))
        return out

    def _router_snapshot_killed(self, st: dict) -> set:
        """记录当前 battle killed uid 集合（用于 diff 本刻新增死亡）。"""
        _b = st.get("battle") or {}
        return set(_b.get("killed") or [])

    def _router_advance_killed(self, st: dict, prev_killed: set) -> list:
        """本刻新增死亡敌人 → 玩法壳账（st[\"_last_killed\"] 单刻语义）。

        对齐旧 compact：_last_killed = 本刻死亡（新死亡单位），供
        _instance_kill_reward（读 _last_killed）/ _instance_victory 兜底
        （读 _last_killed 找 Boss）。整场累计 killed 与上段快照 diff。
        """
        _b = st.get("battle") or {}
        cur_uids = set(_b.get("killed") or [])
        new_uids = cur_uids - (prev_killed or set())
        if not new_uids:
            return []
        units = []
        for a in (IB._enemies_of(st) or []):
            if a.get("uid") in new_uids and int(a.get("hp", 1) or 0) <= 0:
                units.append(dict(a))
        if units:
            st["_last_killed"] = units
            st["killed_enemies"] = []  # compact 语义：单刻账已并入 _last_killed
        return units

    def _router_has_living_players(self, group_id, st) -> bool:
        """当前在场且存活玩家 ≥1（读视图 alive/st 顶层，玩法壳语义）。"""
        cur = self._instance_current_members(group_id, st)
        for k in cur:
            if st.get("alive", {}).get(str(k), True) and \
                    int((st.get("players") or {}).get(str(k), {}).get("hp", 0) or 0) > 0:
                return True
        return False

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------
    async def _instance_router(self, event, group_id, qq_id, player, st,
                               action, skill_name=None, target=None):
        """副本刻行动（battle2 版）——v3 蓝图 §4.1-4.5 全逻辑新写。

        参数/协议对齐旧 _instance_act（CombatCmds 接线点 R2 改调本方法）。
        返回 async generator：yield event.plain_result(...) 文本。
        """
        from ..core.skill_kinds import K_HEAL, K_BUFF
        # 嘲讽强制剩余帧递减（每玩家行动帧；到 0 清强制回正常仇恨）
        _tl = int(st.get("taunt_left", 0) or 0)
        if _tl > 0:
            st["taunt_left"] = _tl - 1
            if st["taunt_left"] <= 0:
                st.pop("taunt_target", None)
                try:
                    yield event.plain_result("……嘲讽效果结束，怪物恢复了本能仇恨！")
                except Exception:
                    pass
        # 4.1a 权威 st（大陆实例优先）
        st = self._router_authoritative_st(st)

        # 4.1b 懒构建 battle state（遭遇/切怪点若未 build_battle——R3 前过渡态）
        # R4 修复：battle sides 敌 uid 与视图 enemies uid 不一致（切房/新怪入场只更新
        # 视图、残留上一场 sides 打旧尸体死循环）→ 强制重建
        _b = st.get("battle") or {}
        _need_build = False
        if not _b.get("sides"):
            _need_build = True
        elif st.get("enemies"):
            _b_uids = {str(u.get("uid") or "") for u in
                       ((_b.get("sides") or {}).get("enemy") or [])}
            _v_uids = {str(u.get("uid") or "") for u in st.get("enemies")}
            if _b_uids != _v_uids:
                _need_build = True
        if _need_build:
            # 无敌人视图 → 肃清引导（不 build）
            if not (st.get("enemies") or []):
                yield self._router_no_enemy_hint(event, group_id, st)
                return
            try:
                IB.build_battle(st)
            except Exception:
                yield event.plain_result("战斗状态异常，请重新遭遇！")
                return

        # 4.1c 无敌人（视图空——战斗中途被肃清完）→ 引导
        if not (st.get("enemies") or []):
            yield self._router_no_enemy_hint(event, group_id, st)
            return

        # 当前成员/存活前置
        members = st.get("members") or []
        now = int(time.time())
        logs = []

        # ---- 1. 轮转：谁该行动（存活玩家 ct 最小者）+ 超时自动防御 ----
        # 对应旧 2494-2521；超时自动防御 = 对非请求超时者调 act("defend")（v3 4.1）
        guard = 0
        while True:
            guard += 1
            if guard > 20:  # 防死循环保险（多 AFK 消化上限）
                break
            cur_key = IB.next_actor_key(st)
            if cur_key is None:
                # 无存活玩家 → 失败结算
                st["over"] = True
                async for _r in self._instance_defeat(event, group_id, qq_id, player, st, logs):
                    yield _r
                return
            if str(cur_key) == str(qq_id):
                break
            # 非请求者：超时 → 自动防御；未超时 → 等待提示
            if now - int(st.get("turn_time", now) or now) > INSTANCE_TIMEOUT:
                _def_name = (self._player(group_id, cur_key) or {}).get("name", cur_key)
                logs.append(f"⏰ {_def_name} 迟迟没有行动，自动进入防御姿态！")
                _dlogs, _dended, _dnxt = IB.act(st, group_id, cur_key, "defend")
                IB.sync_views(st, group_id)
                logs += _dlogs
                if _dended or not IB.next_actor_key(st):
                    break
                continue
            # 未超时 → 等待（含轮转到请求者前的等待提示）
            yield self._router_wait_hint(event, group_id, st, cur_key)
            return

        # 2. 确认轮到当前请求者；无存活玩家守卫（自动防御段可能全灭）
        if not self._router_has_living_players(group_id, st):
            st["over"] = True
            async for _r in self._instance_defeat(event, group_id, qq_id, player, st, logs):
                yield _r
            return
        cur_key = str(qq_id)
        try:
            st["turn"] = members.index(cur_key)
        except Exception:
            st["turn"] = 0
        st["turn_time"] = now

        # ---- 2.5 目标解析（heal/buff 已在 IB.act 内强制 None 防奶敌）----
        _tgt = target
        if action == "skill" and skill_name:
            try:
                _info = E.skill_info(player.get("class_name") or "", skill_name) or {}
            except Exception:
                _info = {}
            if _info.get("kind") in (K_HEAL, K_BUFF):
                _tgt = None

        # 行动前敌 hp 快照（账务 dealt：行动前后敌 hp 差）
        _prev_killed = self._router_snapshot_killed(st)
        try:
            _hp_before = sum(int(u.get("hp", 0) or 0) for u in IB._enemies_of(st))
        except Exception:
            _hp_before = 0
        try:
            _mem_before = sum(int((st.get("players") or {}).get(str(m), {}).get("hp", 0) or 0)
                              for m in members
                              if st.get("alive", {}).get(str(m), True))
        except Exception:
            _mem_before = 0

        # ---- 3. 行动（instance_battle.act：from_state → human_act → 落回）----
        act_logs, ended, _who = IB.act(st, group_id, qq_id, action, skill_name, target=_tgt)
        IB.sync_views(st, group_id)
        logs += act_logs

        # ---- 3.5 账务薄壳（v3 §4.3：dealt/仇恨；5b 基础 + v173.5 仇恨配置）----
        try:
            # v173.5：本次行动技能仇恨配置——hate_mult 伤害仇恨倍率（缺省 1）；
            # effect=taunt 嘲讽：仇恨=当前最高×hate_taunt_mult+100 + 强制锁
            _hm = 1.0
            _is_taunt = False
            _tmult = 3.0
            _tlock = 3
            if action == "skill" and skill_name:
                try:
                    _cfg = self._find_skill_cfg(player, skill_name) or {}
                    _hm = float(_cfg.get("hate_mult", 1.0) or 1.0)
                    if str(_cfg.get("effect", "")) == "taunt":
                        _is_taunt = True
                        _tmult = float(_cfg.get("hate_taunt_mult", 3.0) or 3.0)
                        _tlock = int(_cfg.get("hate_lock_turns", 3) or 3)
                except Exception:
                    pass
            _hp_after = sum(int(u.get("hp", 0) or 0) for u in IB._enemies_of(st))
            dealt = max(0, _hp_before - _hp_after)
            if dealt > 0:
                st.setdefault("contribution", {})
                st["contribution"][str(qq_id)] = st["contribution"].get(str(qq_id), 0) + dealt
                st.setdefault("threat", {})
                st["threat"][str(qq_id)] = st["threat"].get(str(qq_id), 0) + int(dealt * max(0.0, _hm))
            # 嘲讽（v173.5 数值模型：仇恨=当前最高×N+100，强制 taunt_target lock 帧）
            if _is_taunt:
                _th = st.setdefault("threat", {})
                _mx = max([float(v) for v in _th.values()] or [0.0])
                _th[str(qq_id)] = int(_mx * max(0.0, _tmult) + 100)
                st["taunt_target"] = str(qq_id)
                st["taunt_left"] = max(int(st.get("taunt_left", 0) or 0), max(1, _tlock))
                logs.append("🛡️ 你高声嘲讽，怪物怒火尽归你身！（强制攻击自己）")
            # 治疗仇恨（v49 语义基础：×0.8）
            _mem_after = sum(int((st.get("players") or {}).get(str(m), {}).get("hp", 0) or 0)
                             for m in members
                             if st.get("alive", {}).get(str(m), True))
            _heal = max(0, _mem_after - _mem_before)
            if _heal > 0:
                st.setdefault("threat", {})
                st["threat"][str(qq_id)] = st["threat"].get(str(qq_id), 0) + int(_heal * 0.8)
        except Exception:
            pass

        # ---- 4. 结算分支（v3 §4.4，读 actors/视图结果）----
        # 4a. 玩家倒地（本次行动/敌方段致死）→ 全员倒地失败 / 同归
        if not self._router_has_living_players(group_id, st):
            st["over"] = True
            if not (st.get("enemies") or []):
                logs.append("⚔️ 同归于尽！你与敌人同时倒下了……")
            async for _r in self._instance_defeat(event, group_id, qq_id, player, st, logs):
                yield _r
            return

        # 死亡账（本刻新增）——切怪/层清/通关结算前入 _last_killed
        self._router_advance_killed(st, _prev_killed)

        # 4b. 敌全灭（视图空——sync_views 已过滤死亡）→ 分层判定
        if not (st.get("enemies") or []):
            # 守卫（暗格精英守卫）→ 宝箱分支（不通关）
            if st.get("secret_guard_pending"):
                st["secret_guard_pending"] = False
                kill_lines = self._instance_kill_reward(group_id, st)
                st["secret_chest"] = True
                st["mode"] = "map"
                st["boss"] = None
                st["enemy"] = None
                st["enemies"] = []
                # 战斗结束 → 解锁 + 保存（玩法壳行为保留）
                for _m0 in list((st.get("pets") or {}).keys()):
                    try:
                        (st["pets"][_m0]).pop("_last_hit_at", None)
                    except Exception:
                        pass
                for _m in st["members"]:
                    self._unlock_battle(group_id, _m)
                self._instance_save(group_id, st)
                yield event.plain_result(
                    "\n".join(logs) +
                    (("\n" + "\n".join(kill_lines)) if kill_lines else "") +
                    "\n━━━━━━━━━━━━\n"
                    "✅ 精英守卫被击败了！密室深处露出一口【神秘宝箱】……\n"
                    "🔐 『调查 宝箱』看看里面藏着什么！"
                )
                return

            # dungeon rooms（v137 副本地图化）：Boss 房通关 / 普通房回地图
            if st.get("rooms"):
                cur_sa = ""
                try:
                    cur_sa = (self._player(group_id, st.get("leader") or "") or {}).get("cur_subarea", "") or ""
                except Exception:
                    cur_sa = ""
                _rstate = (st.get("rooms") or {}).get(cur_sa) or {}
                _is_boss_r = bool(_rstate.get("_is_boss"))
                if not _is_boss_r:
                    try:
                        _dun_cfg = (C.MAP_BY_ID.get(st.get("inst_id") or "") or {}).get("dungeon") or {}
                        _is_boss_r = (_dun_cfg.get("boss_room") or "") == cur_sa
                    except Exception:
                        _is_boss_r = False
                _room_boss = _is_boss_r and (
                    not (_rstate.get("monsters_left") or []) or bool(_rstate.get("_boss_room")))
                if _room_boss:
                    _rstate["boss_alive"] = False
                    _rstate["_boss_room"] = True
                # 同步大陆权威 st（rooms 同对象或镜像更新）
                try:
                    _wid = st.get("world_id") or ""
                    if _wid.startswith("inst:"):
                        _sa = C.get_instance_st(_wid)
                        if _sa is not None:
                            _ra = (_sa.get("rooms") or {}).get(cur_sa) or {}
                            _ra["boss_alive"] = False
                            _ra["_boss_room"] = True
                except Exception:
                    pass
                st["stage_cleared"] = True
                st["over"] = False
                st["mode"] = "map"
                st["boss"] = None
                st["enemy"] = None
                st["enemies"] = []
                for _m0 in list((st.get("pets") or {}).keys()):
                    try:
                        (st["pets"][_m0]).pop("_last_hit_at", None)
                    except Exception:
                        pass
                for _m in st["members"]:
                    self._unlock_battle(group_id, _m)
                self._instance_save(group_id, st)
                if _room_boss:
                    _st_final = st
                    try:
                        _wid2 = st.get("world_id") or ""
                        if _wid2.startswith("inst:"):
                            _st_final = C.get_instance_st(_wid2) or st
                    except Exception:
                        _st_final = st
                    async for _r in self._instance_victory(
                            event, group_id, qq_id, player, _st_final,
                            logs + [f"👑 副本 Boss 已被击败！"]):
                        yield _r
                    return
                map_view = self._instance_map_view(st, group_id)
                yield event.plain_result(
                    "\n".join(logs) +
                    (("\n" + "\n".join(self._instance_kill_reward(group_id, st))) if (st.get("_last_killed") or []) else "") +
                    f"\n━━━━━━━━━━━━\n"
                    f"✅ 【{cur_sa}】的敌人被肃清了！\n"
                    f"{map_view}\n"
                    f"━━━━━━━━━━━━\n"
                    f"🧭 副本内可继续探索/移动，或『副本』查看进度！"
                )
                return

            # stages 副本：stage_pending 有怪 → 切下一只；否则层清/通关
            pending = st.get("stage_pending") or []
            stages = st.get("inst_stages") or []
            if pending:
                # 切下一只（build_battle 重新构造）
                kill_lines = self._instance_kill_reward(group_id, st)
                nxt = pending.pop(0)
                _boss = C.build_monster(nxt, {"id": st.get("inst_id"), "name": st.get("inst_id"), "area": "instance"})
                st["boss"] = _boss
                if nxt[2] == "elite":
                    self._instance_elite_scale(st, st["boss"])
                st["enemy"] = st["boss"]
                st["enemies"] = [st["boss"]]  # 切怪默认单怪；副本 minions 由 R3 组装
                st["_last_killed"] = []
                st["killed_enemies"] = []
                st["turn"] = 0
                st["turn_time"] = int(time.time())
                for _m0 in list((st.get("pets") or {}).keys()):
                    try:
                        (st["pets"][_m0]).pop("_last_hit_at", None)
                    except Exception:
                        pass
                try:
                    IB.build_battle(st)
                    IB.sync_views(st, group_id)
                except Exception:
                    pass
                self._instance_save(group_id, st)
                yield event.plain_result(
                    "\n".join(logs) +
                    (("\n" + "\n".join(kill_lines)) if kill_lines else "") +
                    f"\n━━━━━━━━━━━━\n"
                    f"⚔️ 又一只怪物挡在面前！\n"
                    f"{self._instance_battle_footer(st, group_id)}\n"
                    f"⏳ 轮到 {self._router_next_player_name(st, group_id)} 行动！『攻击』『技能 <名称>』『防御』"
                )
                return
            if stages:
                last = st.get("stage_idx", 0) >= len(stages) - 1
                if not last:
                    # 层肃清 → 地图模式
                    kill_lines = self._instance_kill_reward(group_id, st)
                    st["stage_cleared"] = True
                    st["over"] = False
                    st["mode"] = "map"
                    st["boss"] = None
                    st["enemy"] = None
                    st["enemies"] = []
                    for _m0 in list((st.get("pets") or {}).keys()):
                        try:
                            (st["pets"][_m0]).pop("_last_hit_at", None)
                        except Exception:
                            pass
                    for _m in st["members"]:
                        self._unlock_battle(group_id, _m)
                    self._instance_save(group_id, st)
                    cur_name = stages[st.get("stage_idx", 0)]["name"]
                    nxt_name = stages[st.get("stage_idx", 0) + 1]["name"]
                    map_view = self._instance_map_view(st, group_id)
                    yield event.plain_result(
                        "\n".join(logs) +
                        (("\n" + "\n".join(kill_lines)) if kill_lines else "") +
                        f"\n━━━━━━━━━━━━\n"
                        f"✅ 【{cur_name}】的敌人被肃清了！\n"
                        f"{map_view}\n"
                        f"━━━━━━━━━━━━\n"
                        f"🧭 前方是【{nxt_name}】……输入『深入』继续推进！"
                    )
                    return
            # 末层 / 无 stages → 通关
            st["over"] = True
            _fc_cur = self._instance_current_members(group_id, st) or [str(st.get("leader") or "")]
            st["first_clear"] = not any(
                a.get("ach_key") == f"inst_clear_{st['inst_id']}" and a.get("progress", 0) >= 1
                for _m2 in _fc_cur
                for a in (db.get_achievements(group_id, _m2) or [])
            )
            async for _r in self._instance_victory(event, group_id, qq_id, player, st, logs):
                yield _r
            return

        # ---- 5. 未结束：收尾展示（v3 §4.5：footer + 轮到 X + 保存）----
        nxt_key = IB.next_actor_key(st)
        if nxt_key and nxt_key in members:
            st["turn"] = members.index(nxt_key)
        else:
            st["turn"] = 0
        st["turn_time"] = now
        self._instance_save(group_id, st)
        nxt_name = self._router_next_player_name(st, group_id, nxt_key)
        yield event.plain_result(
            "\n".join(logs) +
            "\n━━━━━━━━━━━━\n"
            f"{self._instance_battle_footer(st, group_id)}\n"
            f"⏳ 轮到 {nxt_name} 行动！『攻击』『技能 <名称>』『防御』"
        )

    # ------------------------------------------------------------------
    # 展示辅助（轮转名——新写读 players 视图，不依赖旧 CT helpers）
    # ------------------------------------------------------------------
    def _router_next_player_name(self, st: dict, group_id: int, fallback_key=None) -> str:
        nxt = IB.next_actor_key(st)
        key = str(nxt) if nxt else (str(fallback_key) if fallback_key else str(st.get("members", [""])[0] or ""))
        return (st.get("players", {}).get(key, {}) or {}).get("name", key)
