# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - instance（组队副本）

v137 副本地图化 + v141 大陆隔离现状（2026-08-30 审计后描述）：
- 副本 = 静态封闭图（MAP_BY_ID 里 22 张 type=副本 的 dungeon 图，无出口 no_exit，
  房间经 SUBAREA_LINKS_INDEX 连通）。开本『副本 <名字>』克隆图 → 大陆实例
  （world_id inst:<uuid>，game/core/worlds.py），全队 players.world_id 指向它。
- dungeon 配置（数据表驱动）：discovery_agro 遇怪概率（core/encounter.py 统一读）、
  rooms 怪物池/资源池（开本生成 rooms[sa_id].monsters_left/pois_left +
  resources_pool 总量，探索/移动经 consume_monster 消费，POI loot 经 consume_poi_loot 扣减）。
- 命令层 CTB 调度：副本战斗走 _instance_act（CTB 行动轴），开本/深入/移动/探索/调查/
  撤退/离开/超时回收全部命令层调度；移动路由经 _instance_move_route →
  world._instance_dungeon_move（队长带队、全队 cur_subarea 同步、遇怪/Boss 房链路）。
- 大陆生命周期：开本 create_instance_world → 撤退保留（rooms/resources_pool 续档）→
  离开/失败/30min 通关超时/24h 过期 destroy_instance_world + world_id 回 mainland。

历史语义（保留）：2 人组队轮流刻 Boss 战——队长『副本 <名字>』开本（需已组队），
队员自动参战；超时自动防御（事件驱动惰性检测，非定时器）；战斗中不能逃跑
（Boss 锁定）；副本失败全队回城。
"""
import random
import re
import time
import uuid

from ._platform import AstrMessageEvent, filter

from .. import content as C
from .. import db
from .. import engine as E
from .. import battle as BT
from ..battle import ACT_TICK  # v167.3 护盾剩余刻数折算（1 刻 = ACT_TICK 秒）
from ..commands.base import CommandBase, no_prof_waiting, require_player

INSTANCE_TIMEOUT = 60  # 副本行动超时（秒）v101.30d #O9/O32：120s→60s，队友挂机自动防御不再"卡死"（playtest 实测 60s+ 无反应）

# v140 波2：副本通关后调查机制——每日调查上限（跨日归零，玩家行 investigate_date/investigate_count）
INVESTIGATE_DAILY_LIMIT = 3
# 调查点奖励概率默认值（数据层 INVESTIGATION_POINTS 逐点可覆盖；蓝符仅 Lv.60+ 副本生效）
INVESTIGATE_BP_CHANCE = 0.25     # 图纸残页
INVESTIGATE_RUNE_CHANCE = 0.15   # 蓝符（Lv.60+）
INVESTIGATE_COLLECT_CHANCE = 0.03  # 收藏


def _inst_map_id(inst_id: str) -> str:
    """v137：副本 INSTANCES key（inst_xxx）→ 地图 MAPS key（xxx）。

    st["inst_id"] 存的是 INSTANCES 的 key（inst_goblin_camp），而 MAP_BY_ID /
    SUBAREAS / SUBAREA_LINKS_INDEX 的 key 是地图 id（goblin_camp，无 inst_ 前缀）。
    副本地图化后所有地图查询（cur_map/dungeon 字段/LINKS/POI）都要经本函数转换，
    否则拿到空 dict → cur_map["name"] KeyError（v98_05 等副本测试崩因）。
    """
    if inst_id and inst_id.startswith("inst_"):
        return inst_id[len("inst_"):]
    return inst_id or ""


class InstanceCmds(CommandBase):

    def _instance_save(self, group_id, st):
        """v141 大陆隔离：副本状态持久化统一入口。

        同时写两处：
        1. battle_state 镜像（兼容旧代码/旧测试/过期回收机制）
        2. 大陆实例 st（权威源，_instance_battle_for 优先读它）

        所有副本内 st 变更后都应走本方法，保证大陆实例永远最新。
        """
        if st is None:
            return
        db.save_battle(group_id, st.get("leader") or "", st)
        _wid = st.get("world_id") or ""
        if _wid.startswith("inst:"):
            C.set_instance_st(_wid, st)

    # ---------------- v137 『加入战斗』：同队伍成员并入正在进行中的副本战斗 ----------------
    # 设计依据：docs/RESEARCH_join_battle.md §四.2/§五/§九（CTB 播种 = 参考点 + 自身 cost；
    # 战斗结束/PVP/满员/重复/0血/异地拒绝；只改状态不推进行动轴）。
    # 本期范围：仅支持『副本战斗』（battle 存队长名下，st["type"]=="instance"）；
    # 野外同场战斗（方案 B 队长键）与『副本锁拆分为战斗锁+副本锁』留待后续 Phase。

    @filter.regex(r"^(?:\[At:[^\]]+\]\s*)?加入战斗(?:\s*|$)")
    @require_player()
    @no_prof_waiting()

    async def join_battle(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！先『注册』开始冒险～")
            return
        new_key = str(qq_id)
        # 0. 加入者自己已在战斗中 → 拒绝（副本队员经 _instance_battle_for 反查队长行）
        if self._in_battle(group_id, qq_id):
            inst_row = self._instance_battle_for(group_id, qq_id)
            if inst_row and str(inst_row["state"].get("leader")) == new_key:
                yield event.plain_result("你就是这场战斗的队长！『攻击』『技能 <名称>』『防御』行动～")
                return
            yield event.plain_result("你正在战斗中！先解决眼前的敌人～")
            return
        # 1. 同队伍校验：无队 → 拒绝
        members = db.party_members(group_id, qq_id)
        if not members:
            yield event.plain_result("你还没有队伍！先『组队 <对方名字>』拉上队友，再一起并肩作战～")
            return
        if str(members[0]) != new_key:
            # 队员视角：目标战斗 = 队长名下（副本 battle 存队长行）
            leader_key = str(members[0])
            battle_row = db.get_battle(group_id, leader_key)
            if not battle_row or battle_row["state"].get("type") != "instance":
                yield event.plain_result("附近没有可加入的战斗！让队长先在副本中遇怪开战吧～")
                return
            st = battle_row["state"]
            # 2a. 地理校验：队员在副本中（副本是封闭地图，野外玩家不能跨图加入）。
            #     队员自己的 battle 行不存在（副本战斗存队长名下），用 _instance_battle_for
            #     反查（party 表 → 队长行）；再比对 inst_id 防跨副本串台。
            inst_row_self = self._instance_battle_for(group_id, qq_id)
            if not inst_row_self or inst_row_self["state"].get("inst_id") != st.get("inst_id"):
                yield event.plain_result("副本是封闭区域——先进入副本（队长『副本 <名字>』开本）才能加入战斗！")
                return
        else:
            # 队长视角：自己开本遇怪 → 自己就是战斗；无需再加入（上面已拦）
            yield event.plain_result("你就是这场战斗的队长！『攻击』『技能 <名称>』『防御』行动～")
            return
        # 3. 战斗状态校验
        if st.get("over") or st.get("cleared"):
            yield event.plain_result("这场战斗已经结束了！")
            return
        if st.get("retreated"):
            yield event.plain_result("这场战斗已经撤退了！")
            return
        if st.get("type") != "instance":
            yield event.plain_result("这个战斗不支持加入！")
            return
        players = st.setdefault("players", {})
        # 3a. 重复加入：已在 st["players"] → 拒绝（幂等）
        if new_key in players:
            yield event.plain_result("你已在战斗中！『攻击』『技能 <名称>』『防御』行动～")
            return
        # 3b. 满员：len(members) >= 4 → 拒绝（与队伍上限对齐）
        if len(st.get("members") or []) >= 4:
            yield event.plain_result("战斗满员了（4 人）！")
            return
        # 3c. 敌方已全灭（残局无怪）→ 拒绝（无敌人可打）
        if not self._instance_enemies_alive(st):
            yield event.plain_result("这场战斗的敌人已经全部倒下！没有可加入的战斗了～")
            return
        # 3d. 0 血 → 拒绝（与开本 0 血拦截同规则）
        if int(player.get("hp", 0) or 0) <= 0:
            yield event.plain_result("💀 你生命值为 0！先去住宿或用药恢复，别拿命加入战斗～")
            return
        # 4. 构造新玩家快照（_instance_start 同款：player_final_stats 实时属性 + 站位/单位字段）
        _p = self._player(group_id, qq_id)
        if not _p:
            yield event.plain_result("你的角色数据异常，无法加入战斗！")
            return
        _st2 = E.player_final_stats(_p["class_name"], _p["level"], _p.get("equipment", {}),
                                    _p.get("class_tier", 0), _p.get("attributes"),
                                    _p.get("evolve_path", 0), None, _p.get("race"))
        _spd = float(_st2.get("spd", 0) or 0)
        snap = {
            "name": _p["name"], "qq_id": qq_id,
            "class_name": _p["class_name"], "level": _p["level"],
            "hp": min(int(_p.get("hp", 0)), int(_st2.get("max_hp", _p.get("max_hp", 100)))),
            "max_hp": int(_st2.get("max_hp", _p.get("max_hp", 100))),
            "mp": min(int(_p.get("mp", 0)), int(_st2.get("max_mp", _p.get("max_mp", C.DEFAULT_MAX_MP)))),
            "max_mp": int(_st2.get("max_mp", _p.get("max_mp", C.DEFAULT_MAX_MP))),
            "atk": _p.get("atk", 0), "def": _p.get("def", 0),
            "matk": _p.get("matk", 0), "mdef": _p.get("mdef", 0),
            "spd": _spd,
            "equipment": _p.get("equipment", {}),
            "skills": _p.get("skills", []),
            "learned_skills": _p.get("learned_skills", []),
            "class_tier": _p.get("class_tier", 0),
            "evolve_path": _p.get("evolve_path", 0),
            "attributes": _p.get("attributes"),
            "title_bonus": self._title_bonus(group_id, qq_id),
            "race": _p.get("race"),
            "rank": C.CLASSES.get(_p["class_name"], {}).get("default_rank", 2),
            "reach": C.CLASSES.get(_p["class_name"], {}).get("reach",
                             C.CLASSES.get(_p["class_name"], {}).get("default_rank", 2)),
            "uid": "p_{}".format(new_key),
            "buffs": {},
            "stacks": {},
            "defending": False,
            "charging": None,
        }
        # 5. CTB 播种（RESEARCH_join_battle.md §四.2）：参考点 = min(存活敌方 ct, 存活玩家 ct)，
        #    新玩家 ct = 参考点 + 自身 _ct_cost(spd) —— 入场有代价、不抢当前行动窗口。
        try:
            ref = None
            ec = [float(u.get("ct", 0) or 0) for u in st.get("enemies") or [] if u.get("hp", 0) > 0]
            pc = [float(s.get("ct", 0) or 0) for k, s in players.items()
                  if st.get("alive", {}).get(str(k), True) and s.get("hp", 0) > 0]
            cands = [c for c in (ec + pc) if c is not None]
            if cands:
                ref = min(cands)
            cost = BT.Battle()._ct_cost(_spd)
            snap["ct"] = (ref if ref is not None else 0.0) + cost
        except Exception:
            snap["ct"] = -_spd  # 兜底：-spd 与旧副本口径一致
        # 6. 并入 st（只改状态，不推进行动轴）
        players[new_key] = snap
        st.setdefault("members", []).append(new_key)
        st.setdefault("alive", {})[new_key] = True
        st.setdefault("p_buffs", {})[new_key] = {}
        st.setdefault("p_hot", {})[new_key] = {}
        st.setdefault("p_food_effects", {})[new_key] = []
        st.setdefault("p_food_affixes", {})[new_key] = []
        st.setdefault("mech_stacks", {})[new_key] = {}
        st.setdefault("p_defending", {})[new_key] = False
        st.setdefault("contribution", {})[new_key] = 0
        st.setdefault("threat", {})[new_key] = 0
        st.setdefault("player_hit", {})[new_key] = False
        st.setdefault("resources", {}).setdefault(new_key, {})
        st.setdefault("cooldown", {}).setdefault(new_key, {})
        st.setdefault("combo_seq", {}).setdefault(new_key, [])
        # v167.3 副本带宠物：加入者战斗快照也带宠物（野外/副本同一套——当前行动者带自己的宠物）
        st.setdefault("pets", {})[new_key] = db.pet_get(qq_id) or {}
        # 7. 持久化 + 锁 + 广播
        try:
            self._instance_save(group_id, st)
        except Exception:
            pass
        self._lock_battle(group_id, qq_id)
        # 同步 DB 血量（快照与 DB 对齐，防 _sync_players_db 用旧值覆盖）
        try:
            db.update_player(group_id, qq_id, hp=snap["hp"], mp=snap["mp"],
                             max_hp=snap["max_hp"], max_mp=snap["max_mp"])
        except Exception:
            pass
        yield event.plain_result(
            f"⚔️ {snap['name']} 加入了战斗！\n"
            f"━━━━━━━━━━━━\n"
            f"{self._instance_battle_footer(st, group_id)}\n"
            f"👥 当前参战：{'、'.join(str(st.get('players', {}).get(m2, {}).get('name', m2)) for m2 in st.get('members', []))}"
        )

    @filter.regex(r"^(?:\[At:[^\]]+\]\s*)?副本(?!地图)(?:[\s\S]*)$")
    @require_player()
    @no_prof_waiting()

    async def instance_cmd(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        # v141 大陆隔离：孤儿大陆自愈——玩家 world_id 残留 inst: 前缀但大陆 st 已
        # 无活跃战斗（cleared/over/镜像 battle_state 已清），销毁孤儿大陆 + world_id 回主大陆。
        # 覆盖场景：异常路径（clear_battle 但未 destroy）/测试清理/重启后事件恢复不一致。
        # 注意：cleared（通关停留搜刮）也视为孤儿销毁——停留超时由下方 30min 分支接管；
        # 30min 超时分支需要 st 里 cleared_time 来判定，故此处先销毁无妨（大陆 st 已无活跃战斗）。
        try:
            _pwid = (player or {}).get("world_id") or ""
            if _pwid.startswith("inst:"):
                _pinst = C.get_instance_world(_pwid)
                _pst = (_pinst or {}).get("st") or {}
                _pb = db.get_battle(group_id, qq_id)
                _mirror_gone = _pb is None or _pb["state"].get("type") != "instance"
                if _pinst is None or _pst.get("over") or _mirror_gone:
                    C.destroy_instance_world(_pwid)
                    db.update_player(group_id, qq_id, world_id="mainland")
                    player["world_id"] = "mainland"
        except Exception:
            pass
        # 已在副本战斗中 → 显示状态
        inst_row = self._instance_battle_for(group_id, qq_id)
        if inst_row:
            # v101.27 #390：通关停留超时（30 分钟）自动传出，防占位
            _st = inst_row["state"]
            if _st.get("cleared") and _st.get("cleared_time") and int(time.time()) - _st["cleared_time"] > 1800:
                # v104 P1（第二轮）：只清当前队伍成员——退队者可能已在别处战斗，不能动 TA 的锁/battle
                _cur = self._instance_current_members(group_id, _st)
                for _m in _st["members"]:
                    if str(_m) not in _cur:
                        continue
                    self._unlock_battle(group_id, _m)
                    db.clear_battle(group_id, _m)
                # v141 审计 P0（30min 通关超时）：与 instance_leave（640-646）同构——
                # 销毁大陆实例 + 当前队伍成员 world_id 回主大陆（只动当前队伍成员，退队者不动）
                _wid2 = _st.get("world_id") or ""
                if _wid2.startswith("inst:"):
                    for _m2 in _st["members"]:
                        if str(_m2) in _cur:
                            db.update_player(group_id, _m2, world_id="mainland")
                    C.destroy_instance_world(_wid2)
                # R3 P3-1：文案与行为对齐——开本不占地图位置，超时只解除战斗锁/
                # 清 battle（v101.27 #390），玩家从未被\"传送\"；沿用『离开副本』口径
                yield event.plain_result("⏳ 通关时间已过 30 分钟，你已自动离开副本。")
                return
            yield event.plain_result(self._instance_status(group_id, qq_id, inst_row))
            return
        # 副本超 24h 无行动被回收（_expired）→ 先给过期提示并清理（再列副本列表）
        _hint = self._instance_expired_hint(group_id, qq_id)
        if _hint:
            yield event.plain_result(_hint + "\n" + self._instance_list(player))
            return
        arg = self._strip_cmd(event, "副本").strip()
        if not arg:
            yield event.plain_result(self._instance_list(player))
            return
        # 队长开本：『副本 <名字>』
        # v87.2：若存在已撤退（retreated）的同副本记录 → 恢复进度继续
        # v104 P1（M04/M05 同源）：恢复前按当前队伍重新校验——退队/换队后
        # 只恢复仍在队伍中的成员，锁不再加给外人；人数/等级不达标则放弃旧进度
        old_row = self._instance_retreated_row(group_id, qq_id)
        if old_row:
            old_st = old_row["state"]
            # v137 副本地图化：rooms 存档恢复——玩家 cur_map + cur_subarea 同步回入口房间
            cur = self._instance_current_members(group_id, old_st)
            ok_members = [m for m in old_st["members"] if str(m) in cur]
            if old_st.get("rooms"):
                _mid = (old_st.get("inst_id") or "").removeprefix("inst_")
                _entry_sa = C.map_entry_subarea(_mid)
                if _entry_sa:
                    for _m in ok_members:
                        db.update_player(group_id, _m, cur_map=_mid, cur_subarea=_entry_sa)
            if old_st.get("inst_id") and (old_st["inst_id"] == arg or
                                          C.INSTANCES.get(old_st["inst_id"], {}).get("name") == arg):
                inst = C.INSTANCES.get(old_st["inst_id"], {})
                # 人数/等级重校验（与 _instance_start 同规则）
                min_players = inst.get("min_players", 2)
                max_players = inst.get("max_players", 3)
                valid = len(ok_members) >= min_players and len(ok_members) <= max_players
                if valid:
                    for m in ok_members:
                        p = self._player(group_id, m)
                        if not p or p["level"] < inst.get("lv", 0):
                            valid = False
                            break
                        # v104 M04 P1（N6 复验缺项）：恢复路径补 0 血/战斗检查，
                        # 与 _instance_start 同规则——0 血恢复会进入地图模式后碰怪即倒；
                        # 成员在野外战斗中会被加锁进本（双线战斗）。不通过则放弃旧进度，
                        # 落到 _instance_start 输出对应拦截提示。
                        if int(p.get("hp", 0)) <= 0:
                            valid = False
                            break
                        if self._in_battle(group_id, m):
                            valid = False
                            break
                if valid:
                    old_st["retreated"] = False
                    old_st["mode"] = "map"
                    # v106 恢复路径与 _instance_start 同规则：按速度降序重排行动序
                    #（快者先出手），与开本规则、29 章 4.1 保持一致
                    old_st["members"] = sorted(
                        ok_members,
                        key=lambda m: int(self._player(group_id, m).get("spd", 0)),
                        reverse=True,
                    )
                    old_st["turn"] = 0
                    for m in ok_members:
                        self._lock_battle(group_id, m)
                    self._instance_save(group_id, old_st)
                    yield event.plain_result(
                        f"{inst.get('icon', '🏰')} 【{inst.get('name', '')}】你回到了副本深处！\n"
                        f"━━━━━━━━━━━━\n"
                        f"{self._instance_map_view(old_st, group_id)}"
                    )
                    return
        async for _r in self._instance_start(event, group_id, qq_id, player, arg):
            yield _r

    @filter.regex(r"^(?:\[At:[^\]]+\]\s*)?深入(?:(?:第\s*)?(\d+)\s*层)?(?:[层进]\s*)?$")
    @require_player()
    @no_prof_waiting()

    async def instance_advance(self, event: AstrMessageEvent):
        """v86.2 副本推进：清完当前层后『深入』进入下一层。"""
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        inst_row = self._instance_battle_for(group_id, qq_id)
        if not inst_row:
            yield event.plain_result("你当前不在副本中！输入『副本』查看副本列表～")
            return
        st = inst_row["state"]
        # v101.27 #390：通关后不能深入（副本已通关，只剩搜刮）
        if st.get("cleared"):
            yield event.plain_result("副本已通关！搜刮完用『离开副本』传出吧～")
            return
        stages = st.get("inst_stages") or []
        if not stages:
            yield event.plain_result("这个副本没有分层结构，直接挑战 Boss 吧～")
            return
        if not st.get("stage_cleared"):
            # O111 修复：与 _instance_act 的肃清提示统一口径——层内还有未遭遇怪物
            # （stage_pending 非空）时引导『探索』（此前只说"先打完"，玩家不知道
            # 该发什么指令，且与"已被肃清"提示矛盾，playtest O111 阿甘实测）
            if st.get("stage_pending"):
                yield event.plain_result("当前层的敌人还没肃清！『探索』找到它们～")
            else:
                yield event.plain_result("当前层的敌人还没肃清！先打完再说～")
            return
        # v137 副本地图化：dungeon 副本（rooms 存档）『深入』= 移动到 Boss 房/下一房间
        # （兼容保留：boss_room 房间在连通表末位，移动到它即触发 Boss 战）
        if st.get("rooms"):
            # v141 审计：副本大陆路径统一走 resolve_map_for（唯一入口契约）；
            # 大陆实例已销毁（world_id 残留 inst:）→ resolve_map_for None → 回退全局静态图
            # （副本图在 MAP_BY_ID 始终存在，与原 C.MAP_BY_ID.get 语义一致）
            _dun_map = C.resolve_map_for(st.get("world_id") or "", _inst_map_id(st.get("inst_id") or "")) \
                or C.MAP_BY_ID.get(_inst_map_id(st.get("inst_id") or ""), {})
            _dun = _dun_map.get("dungeon") or {}
            _br = _dun.get("boss_room")
            _rooms = st["rooms"]
            if _br and _br in _rooms:
                # 队长移动到 Boss 房（触发 _instance_dungeon_move 的 Boss 战链路）
                _cur = (self._player(group_id, st.get("leader")) or {}).get("cur_subarea") or ""
                _links = C.subarea_links(_inst_map_id(st.get("inst_id") or ""), _cur)
                if _cur != _br and _br in _links:
                    async for _r in self._instance_dungeon_move(event, group_id, qq_id, player,
                                                                inst_row, _br):
                        yield _r
                    return
            yield event.plain_result("副本内请使用『移动 <房间>』推进（队长带队）～『副本地图』查看可前往房间。")
            return
        if st["stage_idx"] >= len(stages) - 1:
            yield event.plain_result("已经是最深层了，击败面前的 Boss 就通关了！")
            return
        # 推进下一层
        st["stage_idx"] += 1
        st["stage_cleared"] = False
        next_stage = stages[st["stage_idx"]]
        # v87.2 机关效果：skip_elite_next（下一层跳过精英）/ skip_wave_next（下一层少一波）
        skip_elite = st.get("skip_elite_next", False)
        skip_wave = st.get("skip_wave_next", False)
        st["skip_elite_next"] = False
        st["skip_wave_next"] = False
        s_mons = next_stage.get("monsters") or []
        if skip_wave and s_mons:
            s_mons = list(s_mons[:-1]) if len(s_mons) > 1 else []
        if s_mons or next_stage.get("elite") or next_stage.get("boss"):
            # 地图化：进入新层地图模式（含 Boss 房），探索触发战斗
            st["mode"] = "map"
            st["stage_pending"] = list(s_mons)
            if next_stage.get("elite") and not skip_elite:
                st["stage_pending"].append(next_stage["elite"])
            if next_stage.get("boss"):
                st["stage_pending"].append(next_stage["boss"])
            st["boss"] = None
            st["enemy"] = None
            st["enemies"] = []
            st["stage_secret_found"] = False
            st["stage_secret_cleared"] = False
            self._check_stage_secret_cond(st)  # 新层 secret cond 检查（如海蚀洞窟 L3 藏宝密室）
        st["enemy"] = st["boss"]
        st["round"] = 1
        st["e_minions"] = []  # v101.28m #438：新战斗开始清空旧援军（防止残留挡刀）
        for m in st["members"]:
            st["p_buffs"][m] = {}
            st["p_hot"][m] = {}
            st["p_food_effects"][m] = []
            st["p_defending"][m] = False
        st["turn"] = 0
        st["turn_time"] = int(time.time())
        # 锁全队（层推进重新上锁）
        for m in st["members"]:
            self._lock_battle(group_id, m)
        self._instance_save(group_id, st)
        if st.get("mode") == "map":
            # 新层地图模式：显示层全景
            map_view = self._instance_map_view(st, group_id)
            yield event.plain_result(
                f"🧭 你继续深入……\n"
                f"━━━━━━━━━━━━\n"
                f"{map_view}"
            )
            return
        yield event.plain_result(
            f"🧭 你继续深入……\n"
            f"━━━━━━━━━━━━\n"
            f"🚪 第 {st['stage_idx'] + 1} 层 · {next_stage['name']}\n"
            f"━━━━━━━━━━━━\n"
            f"{self._instance_battle_footer(st, group_id)}\n"
            f"⏳ 轮到 {self._instance_next_player_name(st, group_id)} 行动！『攻击』『技能 <名称>』『防御』"
        )

    # ---------------- 副本地图（v87.2） ----------------
    @filter.regex(r"^(?:\[At:[^\]]+\]\s*)?副本地图\s*$")
    @require_player()
    @no_prof_waiting()

    async def instance_map_view_cmd(self, event: AstrMessageEvent):
        """查看当前层小地图全景(29 章 13.5)"""
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        inst_row = self._instance_battle_for(group_id, qq_id)
        if not inst_row:
            yield event.plain_result("你当前不在副本中！输入『副本』查看副本列表～")
            return
        st = inst_row["state"]
        if st.get("mode") != "map":
            yield event.plain_result("战斗进行中！先解决眼前的敌人～(『攻击』『技能 <名称>』『防御』)")
            return
        yield event.plain_result(self._instance_map_view(st, group_id))

    # ---------------- 调查（v87.2） ----------------
    # v104 M24 P2-4：空参数也命中（help 写『调查』），handler 内给格式提示
    @filter.regex(r"^(?:\[At:[^\]]+\]\s*)?调查(?:\s+(.+?))?\s*$")
    @require_player()
    @no_prof_waiting()

    async def instance_investigate(self, event: AstrMessageEvent):
        """与当前层 POI 互动：开箱/点火/读碑/拉机关/拆陷阱(29 章 13.5)

        v137 副本地图化：从 SUBAREA_POIS 查当前房间挂载 POI（_handle_poi 已支持
        inst:<type> effect），消耗 rooms[cur_room].pois_left（资源池上限）+ 经
        _handle_poi 的 inst:loot 链路消耗 resources_pool（波次 3a 实现后）。
        """
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        inst_row = self._instance_battle_for(group_id, qq_id)
        if not inst_row:
            yield event.plain_result("你当前不在副本中！输入『副本』查看副本列表～")
            return
        st = inst_row["state"]
        if st.get("mode") != "map":
            yield event.plain_result("战斗进行中！先解决眼前的敌人～")
            return
        name = self._strip_cmd(event, "调查").strip()
        # v104 M24 P2-4：『调查』空参数无响应（help 写『调查』）→ 给格式提示
        if not name:
            yield event.plain_result("格式：『调查 <目标>』，如『调查 宝箱』『调查 篝火』～（『副本地图』查看当前层可调查目标）")
            return
        # v101.27 #390：通关后特殊搜刮 POI 优先（战利品堆/墙砖/密室宝箱），
        # 避免『调查 宝箱』误命中 Boss 房静态"陪葬宝箱"等 stage POI
        if st.get("cleared"):
            # v140 波2：通关后调查点（第①层）——cleared 专属，与战利品堆/暗格并行不冲突。
            # 命中链顺序：调查点名 → 战利品堆/墙砖/宝箱（旧搜刮）→ 房间 POI（现有）。
            # 调查点先判但仅"点名称"命中；战利品堆/墙砖/宝箱走旧链路不受每日上限限制。
            if not (name in ("战利品堆", "战利品", "墙砖", "松动的墙砖", "裂痕", "暗格", "宝箱", "暗格宝箱", "神秘宝箱")):
                _inv_text = self._instance_investigate_cleared(group_id, qq_id, player, st, name)
                if _inv_text is not None:
                    yield event.plain_result(_inv_text)
                    return
            if name in ("战利品堆", "战利品") and st.get("loot_pile"):
                yield event.plain_result(self._instance_loot_pile(group_id, qq_id, player, st))
                return
            if name in ("墙砖", "松动的墙砖", "裂痕", "暗格") and st.get("secret_crack"):
                yield event.plain_result(self._instance_secret_crack(group_id, qq_id, player, st))
                return
            if name in ("宝箱", "暗格宝箱", "神秘宝箱") and st.get("secret_chest"):
                yield event.plain_result(self._instance_secret_chest(group_id, qq_id, player, st))
                return
        # v137 副本地图化：优先按当前房间 SUBAREA_POIS 查（rooms 存档存在时）
        rooms = st.get("rooms")
        cur_sa_id = player.get("cur_subarea") or ""
        # v141 审计：副本大陆路径统一走 resolve_map_for（唯一入口契约）；
        # 大陆实例已销毁（world_id 残留 inst:）→ resolve_map_for None → 回退全局静态图
        cur_map = C.resolve_map_for(st.get("world_id") or "", _inst_map_id(st.get("inst_id") or "")) \
            or C.MAP_BY_ID.get(_inst_map_id(st.get("inst_id") or ""), {})
        cur_sa = None
        for _sa in (cur_map.get("subareas") or []):
            if _sa["id"] == cur_sa_id:
                cur_sa = _sa
                break
        poi = None
        poi_id = None
        if rooms:
            rstate = rooms.get(cur_sa_id) or {}
            _pois_left = rstate.get("pois_left")
            for _pid in (C.subarea_pois(cur_map.get("id", ""), cur_sa_id) or []):
                if _pois_left is not None and _pid not in _pois_left:
                    continue
                _p = C.POIS.get(_pid)
                if _p and (name == _p.get("name") or (name and name in _p.get("name", ""))):
                    poi = _p
                    poi_id = _pid
                    break
        # 旧 stages 路径（rooms 未实现时的过渡兼容）：层内联 POI
        stages = st.get("inst_stages") or []
        sidx = st.get("stage_idx", 0)
        stage = stages[sidx] if sidx < len(stages) else {}
        if poi is None and not rooms:
            poi = self._find_stage_poi(stage, name)
            # 隐藏房间 POI 也算
            secret = stage.get("secret")
            if not poi and secret and st.get("stage_secret_found") and not st.get("stage_secret_cleared"):
                for sp in secret.get("pois", []):
                    if sp.get("name") == name or (name and name in sp.get("name", "")):
                        poi = sp
                        break
        if poi is None:
            yield event.plain_result(f"这里没有『{name}』可以调查～『副本地图』看看周围有什么。")
            return
        if not rooms and self._poi_used(st, sidx, poi.get("id", "")):
            yield event.plain_result(f"{poi.get('name', '')}已经被处理过了。")
            return
        if rooms and _pois_left is not None:
            if poi_id in _pois_left:
                _pois_left.remove(poi_id)  # 资源池消费：探索完即空
            else:
                yield event.plain_result(f"{poi.get('name', '')}已经被搜刮一空了。")
                return
        # v87.2 复用世界地图 POI 处理（_handle_poi → inst:<type> 效果链路）
        text = self._handle_poi(group_id, qq_id, player, cur_sa or stage or cur_map, poi.get("id", "") or poi_id, poi, st=st)
        self._check_stage_secret_cond(st)
        # R3 P1-2：篝火回血/陷阱扣血只改 st 快照，须同步 DB——否则下次 _enter_stage_combat
        # 快照刷新从 DB 读旧值覆盖（回血丢失/伤害回滚），且『使用 治疗药水』满血误判复发
        self._sync_players_db(group_id, st)
        self._instance_save(group_id, st)
        yield event.plain_result(text)

    # ---------------- 撤退（v87.2） ----------------
    @filter.regex(r"^(?:\[At:[^\]]+\]\s*)?撤退\s*$")
    @require_player()
    @no_prof_waiting()

    async def instance_retreat(self, event: AstrMessageEvent):
        """v173.3 意见#87（鱼鱼拍板）：撤退 = 放弃进度（不可恢复）+ 二次确认。

        旧行为（v87.2）：撤退保留层进度（retreated=True），下次开本从原层继续。
        新行为：副本中途想走 = 清空本局进度（战利品/层数全弃），回入口可重新开本。
        防误触：第一次『撤退』只弹确认，回复『确认撤退』才真正放弃。
        通关后的离开请用『离开副本』（保留通关战利品，仅清战斗状态）。
        """
        import json as _json
        import time as _time
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        inst_row = self._instance_battle_for(group_id, qq_id)
        if not inst_row:
            yield event.plain_result("你当前不在副本中！")
            return
        st = inst_row["state"]
        if st.get("mode") != "map":
            # v101.25 #346：非 Boss 战不念 Boss 文案（playtest round71 影刃抓包：打精英也念"Boss 锁定退路"）
            if (st.get("enemy") or {}).get("is_boss"):
                yield event.plain_result("战斗中无法撤退！Boss 锁定了你们的退路——打赢或战败！")
            else:
                yield event.plain_result("战斗中无法撤退！先击败眼前的敌人再说！")
            return
        # 通关后（cleared）撤退 = 等同于离开（保留战利品），不需要确认放弃
        if st.get("cleared"):
            async for _r in self.instance_leave(event):
                yield _r
            return
        # 第一次撤退：弹二次确认（不真正放弃）
        _ck = f"retreat_confirm_{qq_id}"
        _pending = db.get_event_state(_ck)
        if not _pending:
            inst = C.INSTANCES.get(st["inst_id"], {})
            db.set_event_state(_ck, _json.dumps({"ts": int(_time.time()), "inst": st.get("inst_id", "")}, ensure_ascii=False))
            yield event.plain_result(
                f"🏳️ 你要从【{inst.get('name', '副本')}】撤退吗？\n"
                f"⚠️ 撤退 = 放弃当前进度（已拿的战利品保留，但层数/机关进度清空，重新开本从头打）！\n"
                f"💡 确认请回复『确认撤退』；反悔就继续冒险吧～"
            )
            return
        # 有挂起确认 → 提示用『确认撤退』（防把重复撤退当确认）
        try:
            _pd = _json.loads(_pending) if _pending else {}
        except Exception:
            _pd = {}
        if _pd.get("inst") != st.get("inst_id", ""):
            db.set_event_state(_ck, "")
        yield event.plain_result("已弹过确认啦～ 回复『确认撤退』放弃进度，或继续冒险！")

    @filter.regex(r"^(?:\[At:[^\]]+\]\s*)?确认撤退(?:\s*|$)")
    @require_player()
    @no_prof_waiting()

    async def instance_retreat_confirm(self, event: AstrMessageEvent):
        """v173.3 意见#87：确认撤退 = 真正放弃副本进度（不可恢复）。

        前置：玩家发过『撤退』弹了确认（retreat_confirm_{qq_id} 挂起）。
        执行：清 battle 状态 + 全员 world_id 回 mainlan + cur_map/cur_subarea 复位
        副本入口 + 销毁实例大陆（与 instance_leave 同款清理，但语义=放弃本局进度）。
        """
        import json as _json
        group_id, qq_id = self._uid(event)
        inst_row = self._instance_battle_for(group_id, qq_id)
        if not inst_row:
            yield event.plain_result("你当前不在副本中！")
            return
        st = inst_row["state"]
        _ck = f"retreat_confirm_{qq_id}"
        _pending = db.get_event_state(_ck)
        if not _pending:
            yield event.plain_result("还没有待确认的撤退～ 副本中发『撤退』会先弹确认。")
            return
        try:
            _pd = _json.loads(_pending) if _pending else {}
        except Exception:
            _pd = {}
        if _pd.get("inst") != st.get("inst_id", ""):
            db.set_event_state(_ck, "")
            yield event.plain_result("确认已过期（副本状态变化）～ 重新发『撤退』看看吧。")
            return
        inst = C.INSTANCES.get(st["inst_id"], {})
        cur = self._instance_current_members(group_id, st)
        # 清战斗锁 + battle 行
        for m in st["members"]:
            if str(m) in cur:
                self._unlock_battle(group_id, m)
                db.clear_battle(group_id, m)
        # 复位 cur_map/cur_subarea 到副本入口 + world_id 回 mainland + 销毁大陆实例
        if st.get("rooms"):
            _mid = (st.get("inst_id") or "").removeprefix("inst_")
            _entry_sa = C.map_entry_subarea(_mid)
            if _entry_sa:
                for m in st["members"]:
                    if str(m) in cur:
                        db.update_player(group_id, m, cur_map=_mid, cur_subarea=_entry_sa)
        _wid = st.get("world_id") or ""
        if _wid.startswith("inst:"):
            for m in st["members"]:
                if str(m) in cur:
                    db.update_player(group_id, m, world_id="mainland")
            C.destroy_instance_world(_wid)
        db.set_event_state(_ck, "")
        yield event.plain_result(
            f"🏳️ 你们放弃了【{inst.get('name', '副本')}】的进度，回到了入口。\n"
            f"📌 已拿到的战利品保留在背包；想再挑战就重新『副本 {inst.get('name', '')}』从头开始吧！"
        )

    # ---------------- 离开副本（v101.27 #390） ----------------
    @filter.regex(r"^(?:\[At:[^\]]+\]\s*)?离开副本\s*$")
    @require_player()
    @no_prof_waiting()

    async def instance_leave(self, event: AstrMessageEvent):
        """通关后主动传出副本：清 battle 状态（玩家本就在副本入口外，无需传送）"""
        group_id, qq_id = self._uid(event)
        inst_row = self._instance_battle_for(group_id, qq_id)
        if not inst_row:
            yield event.plain_result("你当前不在副本中！")
            return
        st = inst_row["state"]
        if st.get("mode") != "map":
            yield event.plain_result("战斗中无法离开！先解决眼前的敌人再说！")
            return
        inst = C.INSTANCES.get(st["inst_id"], {})
        # v104 P1（第二轮）：只清当前队伍成员——退队者可能已在别处战斗，不能动 TA 的锁/battle
        cur = self._instance_current_members(group_id, st)
        for m in st["members"]:
            if str(m) not in cur:
                continue
            self._unlock_battle(group_id, m)
            db.clear_battle(group_id, m)
        # v141 大陆隔离：离开副本 → 销毁大陆实例 + 全员 world_id 回主大陆
        _wid = st.get("world_id") or ""
        # v173.3 意见#166：离开副本须复位 cur_map/cur_subarea 到副本入口（与撤退 retreat
        # 同款 626-631）——此前只清 battle + world_id 回 mainland，玩家 cur_map 仍停
        # 在副本内部房间 → 移动被副本图逻辑拦（不在大陆 MAP_CONNECTIONS），体验=“跑不掉
        # 原地只能用传送”。
        if st.get("rooms"):
            _mid = (st.get("inst_id") or "").removeprefix("inst_")
            _entry_sa = C.map_entry_subarea(_mid)
            if _entry_sa:
                for m in st["members"]:
                    if str(m) in cur:
                        db.update_player(group_id, m, cur_map=_mid, cur_subarea=_entry_sa)
        if _wid.startswith("inst:"):
            for m in st["members"]:
                if str(m) in cur:
                    db.update_player(group_id, m, world_id="mainland")
            C.destroy_instance_world(_wid)
        yield event.plain_result(
            f"🏳️ 你带着战利品离开了{inst.get('name', '副本')}。冒险者的旅途还在继续～"
        )

    # ---------------- 副本探索（v87.2，由 combat.explore 路由） ----------------
    # v137 副本地图化：队长在副本地图模式下达『移动』= 副本内移动（world.move 副本分支），
    # 由 _instance_dungeon_move 负责：全队 cur_subarea 同步 + 遇怪判定 + Boss 房 Boss 战。
    # 注意：world.move 顶部有 _in_battle 全局拦截（battle_state 按 qq 全局 + 内存锁），
    # 副本地图模式（mode=map，st.boss=None）下战斗锁仍持有 → 先解锁再路由。
    # _instance_dungeon_move 定义在 world.py（async，副本分支用 async for 消费）。
    async def _instance_move_route(self, event, group_id, qq_id, player, dest):
        inst_row = self._instance_battle_for(group_id, qq_id)
        if not inst_row or inst_row["state"].get("mode") != "map" or not inst_row["state"].get("rooms"):
            return
        st = inst_row["state"]
        if str(qq_id) != str(st.get("leader")):
            yield event.plain_result("⏳ 副本内由队长带队移动！等待队长『移动 <房间>』～")
            return
        # v141 审计 #8（route 瘦身）：目标解析 + 队长校验由 _instance_dungeon_move
        # 统一执行（world.py:1655，逐字等价：序号优先/名字/id/目标 None 提示/已在原地/
        # 不相连），此处只做 inst_row 校验 + 解锁全队，玩家原始 dest 直接透传——
        # 不再重复解析（原 671-698 段删除，避免目标解析+队长校验各执行 2 遍）。
        # 解锁全队（副本内移动需解除战斗锁防双线；_instance_dungeon_move 推进后重新上锁）
        for m in st.get("members") or []:
            self._unlock_battle(group_id, m)
        # v141 审计 #8：_instance_dungeon_move 内部会再上锁（遇怪/到达都会 _lock_battle）；
        # 但其开头有 cleared/mode!=map/队长校验，route 已通过 inst_row 校验，此处直接透传 dest。
        async for _r in self._instance_dungeon_move(event, group_id, qq_id, player, inst_row, dest):
            yield _r
        # 兜底：若 _instance_dungeon_move 提前 return（如目标解析失败/已在原地/不相连），
        # 全队锁已在上方解锁——重新上锁防双线战斗（world.move 前置 _in_battle 拦截需要锁）。
        _st2 = inst_row["state"]
        for _m2 in _st2.get("members") or []:
            self._lock_battle(group_id, _m2)
        return

    async def _instance_explore(self, event, group_id, qq_id, inst_row):
        """副本内探索：POI 交互 → 遇怪 → 无事（v137 统一路径）。

        v137 副本地图化：副本探索与野外共用同一『探索』入口（combat.explore 分流），
        判定顺序与野外一致（先 POI 再遇怪），但：
          ① POI 触发概率 = dungeon.discovery_agro（0.85），且只从 rooms[cur_room].pois_left 抽
             （资源池上限，探索完即空；poi 效果经 _handle_poi 的 inst:<type> 链路消费）
          ② 遇怪概率 = discovery_agro，消耗 rooms[cur_room].monsters_left（打完不刷）
          ③ 无隐藏房间/精英保底/彩蛋等野外专属判定（副本内容=房间池）
        波次 3a 未实现 rooms/consume_* 时：只有 rooms 字段存在才消费；否则保持
        旧 inst_stages/stage_pending 行为（兼容过渡）。
        """
        st = inst_row["state"]
        # v101.27 #390：通关后探索无意义（已无敌人），引导搜刮/离开
        if st.get("cleared"):
            yield event.plain_result("副本已通关，没有敌人可探索了！『副本地图』看看战利品堆，或『离开副本』传出～")
            return
        player = self._player(group_id, qq_id)
        cur_sa_id = player.get("cur_subarea") or ""
        # v141 审计：副本大陆路径统一走 resolve_map_for（唯一入口契约）；
        # 大陆实例已销毁（world_id 残留 inst:）→ resolve_map_for None → 回退全局静态图
        cur_map = C.resolve_map_for(st.get("world_id") or "", _inst_map_id(st.get("inst_id") or "")) \
            or C.MAP_BY_ID.get(_inst_map_id(st.get("inst_id") or ""), {})
        cur_sa = None
        for _sa in (cur_map.get("subareas") or []):
            if _sa["id"] == cur_sa_id:
                cur_sa = _sa
                break
        rooms = st.get("rooms")
        if rooms:
            # ---- v137 dungeon 房间池消费 ----
            # v141 审计：遇怪概率统一走 core/encounter.encounter_chance（数据表驱动，
            # 读 dungeon.discovery_agro；与野外 _travel_ambush 等级差模型互为设计差异）
            from ..core.encounter import encounter_chance as _enc_chance
            _agro = _enc_chance(cur_map)
            rstate = rooms.get(cur_sa_id) or {}
            _left = rstate.get("monsters_left") or []
            _pois_left = rstate.get("pois_left")
            # ① POI（概率=discovery_agro，只从 pois_left 抽，消耗资源池）
            poi_ids = [pid for pid in (C.subarea_pois(cur_map.get("id", ""), cur_sa_id) or [])
                       if _pois_left is None or pid in _pois_left]
            if poi_ids and random.random() < _agro:
                poi_id = poi_ids[0]  # 确定性：取剩余列表首个（不新增 random 调用点）
                poi = C.POIS.get(poi_id, {})
                if _pois_left is not None and poi_id in _pois_left:
                    _pois_left.remove(poi_id)
                text = self._handle_poi(group_id, qq_id, player, cur_sa or cur_map, poi_id, poi, st=st)
                self._sync_players_db(group_id, st)
                self._instance_save(group_id, st)
                yield event.plain_result(f"🍃 你仔细搜索着这片区域……\n{text}")
                return
            # ② 遇怪（discovery_agro + monsters_left 非空 → 消耗 1 只 → 进战斗）
            if _left:
                if random.random() < _agro:
                    # v141 审计 #7：死代码接线——consume_monster 弹出（原 _left.pop(0) 内联）
                    _def = self.consume_monster(st, cur_sa_id)
                    if _def is None:
                        yield event.plain_result("🍃 这里已被肃清，没有敌人了。『副本地图』看看剩余可调查的 POI，或让队长『移动』去别的房间～")
                        return
                    self._enter_stage_combat(group_id, st, _def, cur_sa or cur_map)
                    self._instance_save(group_id, st)
                    yield event.plain_result(
                        f"🍃 你警惕地探索着，突然——{cur_sa.get('name', '') if cur_sa else cur_map.get('name', '')}里的怪物扑了上来！\n"
                        f"━━━━━━━━━━━━\n"
                        f"{self._instance_battle_footer(st, group_id)}\n"
                        f"⏳ 轮到 {self._instance_next_player_name(st, group_id)} 行动！『攻击』『技能 <名称>』『防御』"
                    )
                    return
                yield event.plain_result("🍃 你仔细搜索了这片区域，怪物没有发现你……")
                return
            # ③ 无怪可遇
            yield event.plain_result("🍃 这里已被肃清，没有敌人了。『副本地图』看看剩余可调查的 POI，或让队长『移动』去别的房间～")
            return
        # ---- 旧 stages 路径（波次 3a rooms 未实现前的过渡兼容，行为与现状一致） ----
        stages = st.get("inst_stages") or []
        sidx = st["stage_idx"]
        stage = stages[sidx] if sidx < len(stages) else {}
        pending = st.get("stage_pending") or []
        if pending:
            # 遇怪 → 进战斗
            nxt = pending.pop(0)
            self._enter_stage_combat(group_id, st, nxt, stage)
            self._instance_save(group_id, st)
            # v126 副本剧情化：Boss 战前台词（仅 role=boss 且 inst 有 boss_line 字段才渲染）
            _inst2 = C.INSTANCES.get(st.get("inst_id") or "", {})
            boss_line_note = f"💬 {_inst2['boss_line']}\n" if nxt[2] == "boss" and _inst2.get("boss_line") else ""
            yield event.plain_result(
                f"🍃 你警惕地探索着，突然——{stage.get('name', '')}里的怪物扑了上来！\n"
                f"━━━━━━━━━━━━\n"
                f"{boss_line_note}"
                f"{self._instance_battle_footer(st, group_id)}\n"
                f"⏳ 轮到 {self._instance_next_player_name(st, group_id)} 行动！『攻击』『技能 <名称>』『防御』"
            )
            return
        # 无怪：检查陷阱（未用的 trap POI）——50% 概率踩中
        for p in stage.get("pois") or []:
            if p.get("type") == "trap" and not self._poi_used(st, sidx, p.get("id", "")):
                if random.random() < C.INST_EVENT_CHANCE:
                    text = self._handle_poi(group_id, qq_id, player, stage, p.get("id", ""), p, st=st)
                    self._check_stage_secret_cond(st)
                    # R3 P1-2：陷阱扣血同步 DB（同调查路径，防快照刷新覆盖回滚）
                    self._sync_players_db(group_id, st)
                    self._instance_save(group_id, st)
                    yield event.plain_result("🍃 你小心翼翼地探索……\n" + text)
                    return
                break
        # 无事
        yield event.plain_result("🍃 你仔细搜索了这片区域，除了风声什么也没有发现。")

    def _instance_elite_scale(self, st: dict, mon: dict) -> dict:
        """v101.28l #423：副本精英按队伍人数缩放强度（超出 min_players 每人 +50% 血/攻/魔攻）。
        与 Boss 缩放（hp_mult + 0.65/人）同思路，幅度略低——精英不该比 Boss 还肉。"""
        inst2 = C.INSTANCES.get(st.get("inst_id") or "", {})
        n_extra = len(st.get("members") or []) - inst2.get("min_players", 1)
        if n_extra > 0:
            m = 1.0 + 0.5 * n_extra
            mon["max_hp"] = int(mon.get("max_hp", 0) * m)
            mon["hp"] = mon["max_hp"]
            mon["atk"] = int(mon.get("atk", 0) * m)
            mon["matk"] = int(mon.get("matk", 0) * m)
        return mon

    def _enter_stage_combat(self, group_id, st: dict, mon_def, stage: dict):
        """把层内怪物投入战斗（mode → battle，初始化战斗状态）
        若 mon_def 是层 Boss（role=boss）→ 应用血量缩放/mech/风神铭文"""
        # v95r76 #383 补充：层间推进时用 DB 当前血量刷新快照——层肃清后战斗外行为
        # （喝药/调查回血点等）只更新 DB 不更新快照，若不刷新，『深入』后玩家
        # 以旧快照残血开战（格温实测：肃清后喝药 364→564，快照仍是 364 药白喝）
        for m in st["members"]:
            p = self._player(group_id, m)
            if p:
                snap = st["players"][str(m)]
                snap["hp"] = min(int(p.get("hp", snap.get("hp", 0))), snap.get("max_hp", 1))
                snap["mp"] = min(int(p.get("mp", snap.get("mp", 0))), snap.get("max_mp", 1))
        st["mode"] = "battle"
        # v167.3（2026-09-03 鱼鱼拍板）副本开放宠物参战：野外/副本完全同一套逻辑——
        # 副本战斗带宠物（读条命中制、按 skill_interval 出手、伤害跟随玩家 buffs/装备），
        # 多人副本 = 当前行动者带自己的宠物（st["pets"] 按 DB 快照，_instance_act 构造
        # Battle 时传当前行动者宠物）。宠物经验/饱食度结算与野外一致：副本内击杀奖励
        # （_instance_kill_reward）与通关奖励（_instance_victory）按存活成员各结各宠。
        # （v104 M17 P2 旧设定『副本不携带宠物』已废弃，见 git log v167.3。）
        st["boss"] = C.build_monster(mon_def, {"id": st["inst_id"], "name": st["inst_id"], "area": "instance"})
        if mon_def[2] == "boss":
            inst2 = C.INSTANCES[st["inst_id"]]
            # v178 E1：副本 Boss 带 inst_id 上下文（供 _boss_cfg 按副本条目解析
            # phases/opening/triggers——旧逻辑按 b_xxx id 查 INSTANCES 命中不了）
            st["boss"]["_inst_id"] = st["inst_id"]
            # v178 E2：副本 mech 与 monster_mods mech 合并（去重，非覆盖）——
            # 旧逻辑整体覆盖把 MONSTER_MODS 配的 phase_open/player_low/summon 等剧本
            # token 吞掉（实测 5 例：b_om_shadow/b_moro/b_eter/b_goblin_chief/b_king_odric）
            if inst2.get("mech"):
                _mods_mech = (st["boss"].get("mech") or "").strip()
                _inst_mech = inst2["mech"].strip()
                if _mods_mech and _inst_mech:
                    _merged = ",".join(dict.fromkeys(
                        [x.strip() for x in (_mods_mech + "," + _inst_mech).split(",") if x.strip()]))
                    st["boss"]["mech"] = _merged
                else:
                    st["boss"]["mech"] = _inst_mech or _mods_mech
            hp_mult = inst2["hp_mult"] + 0.65 * (len(st["members"]) - inst2.get("min_players", 1))
            st["boss"]["max_hp"] = int(st["boss"]["max_hp"] * hp_mult)
            st["boss"]["hp"] = st["boss"]["max_hp"]
            st["boss"]["atk"] = int(st["boss"]["atk"] * inst2["atk_mult"])
            st["boss"]["matk"] = int(st["boss"]["matk"] * inst2["atk_mult"])
            # 风神铭文：Boss 战前全队 +10% 速度（boss_buff_next）
            if st.get("boss_buff_next"):
                for m in st["members"]:
                    pb = st["p_buffs"].setdefault(m, {})
                    pb["spd_up"] = max(pb.get("spd_up", 0), 2)
                st["boss_buff_next"] = False
        elif mon_def[2] == "elite":
            # v101.28l #423：精英按人数缩放（此前不缩放，2 人档与单人一样难）
            self._instance_elite_scale(st, st["boss"])
        st["enemy"] = st["boss"]
        st["round"] = 1
        st["e_minions"] = []  # v101.28m #438：新战斗开始清空旧援军（防止残留挡刀）
        for m in st["members"]:
            st["p_buffs"][m] = {}
            st["p_hot"][m] = {}
            st["p_food_effects"][m] = []
            st["p_defending"][m] = False
        st["turn"] = 0
        st["turn_time"] = int(time.time())
        st["threat"] = {str(m): 0 for m in st["members"]}  # 仇恨表（v49）
        # 锁全队（战斗重新上锁）
        for m in st["members"]:
            self._lock_battle(group_id, m)
        # Boss 层附加：boss_buff_next → 全队速度加成 1 战（风神铭文）
        if st.get("boss_buff_next") and stage.get("boss"):
            for m in st["members"]:
                pb = st["p_buffs"].setdefault(m, {})
                pb["spd_up"] = max(pb.get("spd_up", 0), 2)
            st["boss_buff_next"] = False
        # v2 多对多：战斗开始由 st["boss"] 构建敌方阵列 st["enemies"]（Boss+配置爪牙）
        st["enemies"] = self._instance_build_enemy_array(st, st["boss"])
        # v110 P0（#110）：新一场战斗清零上场的击杀账（_last_killed/killed_enemies），
        # 配合 _instance_enemies_compact 的『空结果不覆盖』语义——上一场死亡记录只在
        # 当刻被 _instance_kill_reward/_instance_victory 消费，绝不串场到新战斗。
        st["_last_killed"] = []
        st["killed_enemies"] = []
        # v110 P0（#136 副本护盾词条不生效）：副本每场战斗开始补 battle_start 词条链
        # （装备『护盾』/『奥术屏障』种子盾），与野外 Battle.__init__ 行为对齐。
        self._instance_seed_battle_start_affixes(st)
        # v121 审计修复：新战斗开始玩家 ct 与敌方同规则重置（-spd 播种对称）
        self._instance_reset_player_cts(st)

    # ---------------- v2 多对多阵列 helpers（§2.2 / §8.2） ----------------
    @staticmethod
    def _instance_affix_ids(snap: dict) -> list:
        """v110 P0（#136 副本护盾词条）：镜像 battle._equip_affix_ids（禁止改 battle.py）。
        读玩家快照装备 affixes + legendary，供副本战斗开始词条种子使用。"""
        ids = []
        for item in (snap.get("equipment") or {}).values():
            if not item:
                continue
            ids.extend(item.get("affixes", []) or [])
            if item.get("legendary"):
                ids.append(item["legendary"])
        return ids

    def _instance_seed_shield(self, snap: dict, st: dict, key: str, value: int, turns: int = 3):
        """v110 P0（#136 副本护盾词条不生效）：镜像 battle._add_shield 的种子逻辑——
        战斗开始词条护盾只在新开战斗 Battle.__init__(player=...) 发放；副本每场战斗经
        _instance_act 的 Battle.from_state（无 player 参数）重建，从不执行 battle_start 链，
        装备『护盾』/『奥术屏障』词条在副本内静默失效。此处按同源数据（affixes/legendary
        effect + shield_power 属性）逐成员种子到快照 p_shields，随快照持久化跨刻生效。"""
        try:
            if value <= 0:
                return
            try:
                _spv = min(float(E.player_final_stats(
                    snap.get("class_name", "战士"), snap.get("level", 1),
                    snap.get("equipment", {}), snap.get("class_tier", 0),
                    snap.get("attributes"), snap.get("evolve_path", 0),
                    None, snap.get("race")).get("shield_power", 0) or 0), 0.5)
                if _spv > 0:
                    value = int(value * (1 + _spv))
            except Exception:
                pass
            _now = float(st.get("now", 0.0) or 0.0)
            _exp = _now + max(1, int(turns or 1)) * (ACT_TICK or 2.0)
            shields = snap.setdefault("p_shields", {})
            cur = shields.get(key)
            if cur:
                cur["value"] = int(cur.get("value", 0) or 0) + value
                cur["expire_at"] = max(float(cur.get("expire_at", _exp) or _exp), _exp)
            else:
                shields[key] = {"value": value, "expire_at": _exp}
        except Exception:
            pass

    def _instance_seed_battle_start_affixes(self, st: dict):
        """v110 P0（#136）：副本每场战斗开始时，按野外同款 battle_start 词条链给各成员
        种子护盾（affix『护盾』+ 专属『奥术屏障』，数值读数据）。在 _enter_stage_combat
        新战斗入口调用一次；p_shields 随快照持久化，_instance_act 重建 Battle 时透传。"""
        try:
            for m in st.get("members") or []:
                snap = st.get("players", {}).get(str(m))
                if not snap:
                    continue
                ids = self._instance_affix_ids(snap)
                if "shield" in ids:
                    _se = (C.AFFIXES.get("shield") or {}).get("effect") or {}
                    self._instance_seed_shield(snap, st, "affix_shield",
                                               int(snap.get("max_hp", 100) * float(_se.get("shield_hp_pct", 0.10) or 0.10)),
                                               int(_se.get("turns", 3) or 3))
                if "arcane_ward" in ids:
                    self._instance_seed_shield(snap, st, "arcane_ward",
                                               int(snap.get("max_hp", 100) * 0.15), 3)
        except Exception:
            pass

    def _instance_reset_player_cts(self, st: dict) -> None:
        """v152 绝对时刻：新敌人入场时重置存活玩家 ct = 参考点 + 自身 cost。
        参考点 = min(存活敌方 ct, 存活玩家 ct)（= 当前时间轴最早行动时刻），保证
        重置后玩家 next_act_at 在参考点之后（不抢当前行动窗口），与入场播种一致。
        v121 旧语义 -spd 是相对时钟，与绝对时刻播种（ref+cost）混用会错乱。"""
        self._instance_ensure_player_fields(st)
        refs = []
        for u in st.get("enemies") or []:
            if u.get("hp", 0) > 0 and float(u.get("ct", 0) or 0) > 0:
                refs.append(float(u.get("ct", 0) or 0))
        for key, snap in (st.get("players") or {}).items():
            if st.get("alive", {}).get(str(key), True):
                _spd = snap.get("spd", 0)
                try:
                    _st0 = BT.Battle()._player_stats(snap)
                    _spd = _st0.get("spd", _spd) if _st0 else _spd
                except Exception:
                    pass
                _cost = BT.Battle()._ct_cost(_spd)
                ref = min(refs) if refs else 0.0
                snap["ct"] = ref + _cost

    def _scale_enemy_copy(self, m: dict, mult: float, uid: str, name: str,
                          rank: int, reach: int) -> dict:
        """按倍率复制主怪战斗属性派生一只站位独立的新单位（沿用 skills/drops/地图）。
        等价 drops._scale_monster 的确定性派生（不引入随机）。"""
        copy = dict(m)
        for k in ("hp", "max_hp", "atk", "def", "matk", "mdef", "spd"):
            if isinstance(copy.get(k), (int, float)):
                copy[k] = max(0, int(copy[k] * mult))
        copy["uid"] = uid
        copy["name"] = name
        copy["rank"] = rank
        copy["reach"] = reach
        copy["buffs"] = {}
        copy["stacks"] = {}
        copy["defending"] = False
        copy["charging"] = None
        # 爪牙不属于首领/精英本体（身份/奖励判定走主怪）
        copy["is_boss"] = False
        copy["is_elite"] = False
        copy["is_minion"] = True
        # 爪牙不携带主怪专属机制（防逐单位 _boss_mech 多怪多次召唤/回血）
        copy["mech"] = ""
        copy["mod"] = ""
        return copy


    def _mark_minion_copy(self, m: dict, uid: str, name: str) -> dict:
        """v163：把 build_monster 产物标记为爪牙（独立小怪模板路径）。
        改名/换 uid/打 is_minion + 清 mech/mod（防逐单位 _boss_mech 多怪重复机制）。
        数值保留 build_monster 的小怪模板值（鱼鱼拍板：爪牙=小怪，非 Boss 缩放）。"""
        copy = dict(m)
        copy["uid"] = uid
        copy["name"] = name
        copy["rank"] = 1  # 爪牙恒前排挡刀
        copy["reach"] = 1
        copy["buffs"] = {}
        copy["stacks"] = {}
        copy["defending"] = False
        copy["charging"] = None
        copy["is_boss"] = False
        copy["is_elite"] = False
        copy["is_minion"] = True
        copy["mech"] = ""
        copy["mod"] = ""
        return copy

    def _instance_build_enemy_array(self, st: dict, boss: dict) -> list:
        """v2：由主怪 st["boss"] 构建敌方阵列 st["enemies"]。
        Boss 主单位 = build_monster 产物（含 rank/reach/uid/buffs/stacks/defending/charging）；
        配置 minions 展开为 rank1 的爪牙（属性 ×0.5、名字"XX的{minion名}"、uid 唯一、is_boss/is_elite False）。
        精英/普通怪 → 单怪阵列 [boss]。缺省无 minions → 仅 Boss。
        v121 CTB：每个敌方单位补 ct = -spd（越小越先行动）。
        v152 绝对时刻：ct = 初始等待（BASE_DELAY/spd，即 cost，正数越大越晚行动）。"""
        boss = boss or {}
        if not boss:
            return []
        if not boss.get("is_boss"):
            boss.setdefault("ct", BT._ct_initial_wait(boss.get("spd", 0)))
            return [boss]
        enemies = [boss]
        boss.setdefault("ct", BT._ct_initial_wait(boss.get("spd", 0)))
        inst = C.INSTANCES.get(st.get("inst_id") or "", {})
        mcfg = inst.get("minions") or []
        base_name = boss.get("name", "BOSS")
        base_uid = boss.get("uid", "e_0")
        for mi, cfg in enumerate(mcfg):
            cnt = int(cfg.get("count", 1) or 1)
            mdef_tpl = cfg.get("monster")
            mname = cfg.get("name", "爪牙")
            for j in range(cnt):
                if mdef_tpl and isinstance(mdef_tpl, (list, tuple)) and len(mdef_tpl) >= 6:
                    # v163 爪牙=同图小怪模板（鱼鱼拍板）：build_monster 构建独立小怪数值
                    # （如哥布林守卫 lv15 ≈ 564HP），不从 Boss 按比例缩放。
                    _mo = C.build_monster(mdef_tpl, {"id": st.get("inst_id") or "x",
                                                    "name": st.get("inst_id") or "x", "area": "instance"})
                    sub = self._mark_minion_copy(_mo,
                                                  "{}-m{}_{}".format(base_uid, mi, j),
                                                  "{}的{}".format(base_name, mname))
                else:
                    # 旧格式兼容（name/role 无 monster 模板）：仍按 Boss ×0.5 派生（老数据兜底）
                    role = cfg.get("role", "dps")
                    mrank = 1  # 契约 §2.2：爪牙 rank1
                    mreach = 2 if role in ("caster", "healer") else 1
                    sub = self._scale_enemy_copy(
                        boss, 0.5, "{}-m{}_{}".format(base_uid, mi, j),
                        "{}的{}".format(base_name, mname), mrank, mreach)
                sub.setdefault("ct", BT._ct_initial_wait(sub.get("spd", 0)))
                enemies.append(sub)
        return enemies

    def _instance_enemies_alive(self, st: dict) -> bool:
        """v2：敌方阵列是否还有存活单位（hp>0）。单怪同 st["boss"].hp>0。"""
        return any(u.get("hp", 0) > 0 for u in (st.get("enemies") or []))

    def _instance_enemy_units(self, st: dict) -> list:
        """v2：敌方阵列存活单位列表。"""
        return [u for u in (st.get("enemies") or []) if u.get("hp", 0) > 0]

    def _instance_enemies_compact(self, st: dict) -> list:
        """v2：敌方阵列死亡单位移除 + 阵型压缩（formation.compact）。
        返回被移除（死亡）的单位列表，供击杀奖励/任务统计逐单位结算。
        st["boss"]/st["enemy"] 兼容键 → 存活首单位；若原 Boss 已死被移除则保留原 dict 引用
        （供胜利显示/多动按 is_boss 或 uid 判断——_instance_boss_turn 多动按 uid 在存活阵列
        中定位主 Boss，不依赖 st["boss"] 对象同一性）。"""
        from ..core import formation as FM
        enemies = st.setdefault("enemies", [])
        removed = FM.compact(enemies)
        # v110 P0（#110 海盗王任务卡死）：击杀账合并——battle._remove_unit 提前移出阵列的
        # 单位（_instance_act 已把 b.killed_enemies 并入 st["killed_enemies"]）也计入本刻
        # 死亡，防止 _last_killed 只含压缩残留、漏记 Boss。注意：同一次玩家行动 _instance_act
        # 内会连续调用本函数多次（行动后压缩 + 全灭分支压缩），第二次调用时阵列已空、
        # killed_enemies 已清——此时【不覆盖】_last_killed，避免把刚记下的 Boss 击杀冲掉
        # （旧实现每调用都 st["_last_killed"]=removed，removed=[] 时会把 Boss 账清零）。
        _bk_prev = st.get("killed_enemies") or []
        if removed or _bk_prev:
            merged = list(removed)
            for _k in _bk_prev:
                if _k not in merged:
                    merged.append(_k)
            st["_last_killed"] = merged  # 记录本刻死亡单位（击杀奖励/任务统计按单位结算）
            st["killed_enemies"] = []   # 已并入 _last_killed，清累计账（单刻账目语义）
        # 兼容主目标：仅当原 Boss（按 uid 识别）仍在存活阵列中时，才把 st["boss"]/st["enemy"]
        # 更新为活着的首单位；若原 Boss 已死/被移除（爪牙存活），保留原 dict 引用，避免
        # "Boss 先死、爪牙存活"时 st["boss"] 被错误重指向爪牙。
        if enemies:
            _orig_uid = (st.get("boss") or {}).get("uid")
            if _orig_uid and any(u.get("uid") == _orig_uid for u in enemies):
                st["boss"] = enemies[0]
                st["enemy"] = enemies[0]
        else:
            st.setdefault("boss", st.get("enemy"))
            st.setdefault("enemy", st.get("boss"))
        return removed

    def _instance_ensure_player_fields(self, st: dict) -> None:
        """v2：确保每玩家快照含站位字段（rank/reach/uid/buffs/stacks/defending/charging），
        老存档恢复时补缺。"""
        for key, snap in (st.get("players") or {}).items():
            cls = snap.get("class_name", "")
            cinfo = C.CLASSES.get(cls, {})
            snap.setdefault("rank", cinfo.get("default_rank", 2))
            snap.setdefault("reach", cinfo.get("reach", cinfo.get("default_rank", 2)))
            snap.setdefault("uid", "p_{}".format(key))
            snap.setdefault("buffs", {})
            snap.setdefault("stacks", {})
            snap.setdefault("defending", False)
            snap.setdefault("charging", None)
            # v121 CTB：玩家快照 ct 缺省 -spd（老存档恢复时兜底；越小越先行动）
            snap.setdefault("ct", -float(snap.get("spd", 0) or 0))

    def _instance_player_units(self, st: dict) -> list:
        """v2：我方阵列存活玩家单位列表（仅供参考 name/rank/reach）。"""
        self._instance_ensure_player_fields(st)
        return [snap for key, snap in (st.get("players") or {}).items()
                if st.get("alive", {}).get(str(key), True)]

    def _instance_extract_target(self, event, action: str, skill_name: str = None) -> str or None:
        """v2：从事件消息解析指定目标名（『攻击 <名字>』/『技能 <名> <目标名>』）。
        无法可靠解析 → 返回 None（引擎自动选择目标）。"""
        try:
            msg = event.get_message_str().strip()
            msg = re.sub(r"^\[At:[^\]]*\]\s*", "", msg)
            msg = re.sub(r"^\[At:全体成员\]\s*", "", msg)
            msg = re.sub(r"^\[引用消息[^\]]*\]\s*", "", msg)
        except Exception:
            return None
        if action == "attack":
            if msg.startswith("攻击"):
                rest = msg[len("攻击"):].strip()
                if not rest or "@" in rest or rest.isdigit():
                    return None
                return rest
            return None
        if action == "skill" and skill_name:
            # 『技能 <名> [目标名]』：去掉"技能"再尽可能去掉技能名，剩余即目标
            if not msg.startswith("技能"):
                return None
            rest = msg[len("技能"):].strip()
            # 去掉（前缀匹配的）技能名
            if rest.startswith(skill_name):
                rest = rest[len(skill_name):].strip()
            else:
                # 技能名未精确前缀命中 → 无法可靠剥离目标，交自动选择
                return None
            # v127.3：允许编号目标（a2/b2/纯数字2）——『技能 火球术 a2』
            if not rest or "@" in rest:
                return None
            import re as _re
            if _re.fullmatch(r"[ab]?\d+", rest.strip().lower()):
                return rest.strip().lower()
            return rest
        return None


    def _class_role_label(self, class_name) -> str:
        """职业定位标签：战士·坦克 / 牧师·治疗"""
        info = C.CLASSES.get(class_name, {})
        role = info.get("role", "")
        return f"{info.get('name', class_name)}{'·' + role if role else ''}"

    def _party_composition_hint(self, st: dict) -> list:
        """队伍构成提示(v49 意见#7 职业组队搭配)"""
        roles = [C.CLASSES.get(st["players"][str(m)].get("class_name", ""), {}).get("role", "")
                 for m in st["members"]]
        hints = []
        if "坦克" not in roles:
            hints.append("🛡️ 没有坦克：Boss 仇恨没人拉，输出容易被追着打")
        if "治疗" not in roles:
            hints.append("✨ 没有治疗：血线压力大，记得多带药水")
        if len(roles) >= 3 and "输出" not in roles:
            hints.append("⚔️ 没有输出：可能打到超时哦")
        return hints

    def _instance_battle_for(self, group_id, qq_id):
        """查找玩家（队长或队员）当前的副本战斗状态；无则 None
        v87.2：retreated（撤退保留进度）的副本不参与战斗判定（玩家可自由行动）
        v141 大陆隔离：优先从玩家 world_id 反查大陆实例（权威源）——队员退队后
        不再依赖 party 反查队长行，大陆实例成员快照即真相；battle_state 镜像兜底。
        """
        # v141：玩家 world_id 指向 inst: 前缀 → 直接查大陆实例
        try:
            _p = self._player(group_id, qq_id)
            _wid = (_p or {}).get("world_id") or ""
            if _wid.startswith("inst:"):
                _inst = C.get_instance_world(_wid)
                if _inst is not None:
                    _st = _inst.get("st")
                    # v141：cleared/over（通关后停留搜刮/已结束）不算战斗中，玩家可自由行动
                    if _st and _st.get("type") == "instance" and not _st.get("retreated") \
                            and not _st.get("cleared") and not _st.get("over") \
                            and not _st.get("_expired"):
                        return {"state": _st, "name": "", "updated_at": _inst.get("created_at", 0)}
        except Exception:
            pass
        b = db.get_battle(group_id, qq_id)
        if b and b["state"].get("type") == "instance" and not b["state"].get("retreated"):
            return b
        members = db.party_members(group_id, qq_id)
        if members and str(members[0]) != str(qq_id):
            lb = db.get_battle(group_id, members[0])
            if lb and lb["state"].get("type") == "instance" and not lb["state"].get("retreated"):
                return lb
        return None

    def _instance_retreated_row(self, group_id, qq_id):
        """查找队长名下已撤退(retreated)的副本记录(恢复进度用)"""
        b = db.get_battle(group_id, qq_id)
        if b and b["state"].get("type") == "instance" and b["state"].get("retreated"):
            return b
        return None

    def _instance_expired_hint(self, group_id, qq_id) -> str:
        """v104 M04 P2：副本超 24h 无行动被回收后给玩家过期提示（此前静默消失）。

        battle_state.get_battle 对过期副本行不再静默删除，而是打 _expired 标记保留，
        由本方法检出、清理并返回提示文案；队员的副本行存队长名下，故先查队伍队长。
        """
        leader = str(qq_id)
        members = db.party_members(group_id, qq_id)
        if members:
            leader = str(members[0])
        row = db.get_battle_raw(group_id, leader)
        if not row:
            return ""
        st = row["state"]
        if st.get("type") == "instance" and st.get("_expired"):
            # v141 审计（24h 过期回收）：清 battle 前先取 world_id，inst: 前缀 →
            # 全员 world_id 回主大陆 + 销毁大陆实例（battle_state.py:91-98 的
            # store 层兜底也会幂等销毁，命令层先行保证 DB 恢复一致）
            _wid = st.get("world_id") or ""
            if _wid.startswith("inst:"):
                for _m in (st.get("members") or []):
                    try:
                        db.update_player(group_id, _m, world_id="mainland")
                    except Exception:
                        pass
                C.destroy_instance_world(_wid)
            db.clear_battle(group_id, leader)
            return "⌛ 你之前的副本因超过 24 小时无人行动，已自动过期消失～"
        return ""

    def _instance_current_members(self, group_id, st) -> list:
        """v104 P1（M04/M05 同源）：当前仍在队伍中的副本成员（str 列表）。

        结算（击杀奖励/通关奖励/失败回城）/ Boss 目标选择 / 进度恢复一律用
        本方法过滤 st["members"]——退队成员不再白拿奖励、不被 Boss 攻击、
        不被全灭误杀。单人副本（无队伍）视为本人仍在。"""
        party = [str(m) for m in db.party_members(group_id, st["leader"])]
        if party:
            return [str(m) for m in st["members"] if str(m) in party]
        members = st.get("members") or []
        if len(members) == 1 and str(members[0]) == str(st["leader"]):
            return [str(members[0])]
        return []

    def _instance_list(self, player) -> str:
        lines = ["🏰 【组队副本】", "━━━━━━━━━━━━"]
        # v173.x 意见#162：副本列表按等级升序渲染（数据文件按主线/支线/外域分区登记，
        # 插入顺序≠等级序，低等级本会被排到后面）——排序在渲染层做，新增副本自动有序。
        for i, (kid, inst) in enumerate(
            sorted(C.INSTANCES.items(), key=lambda kv: (int(kv[1].get("lv", 0) or 0), kv[0])),
            1,
        ):
            locked = player["level"] < inst["lv"]
            mark = "🔒" if locked else "✅"
            mn = inst.get("min_players", 2)
            mx = inst.get("max_players", 3)
            if mx <= 1:
                size = "🕐 单人"
            elif mn == mx:
                size = f"👥 {mn}人"
            else:
                size = f"👥 {mn}-{mx}人"
            lines.append(f"{i}. {mark} {inst['icon']} {inst['name']}(Lv.{inst['lv']}+ · {size})")
            lines.append(f"   {inst['desc']}")
            mats = "、".join(
                C.display("materials", m) if m in C.MATERIALS else m
                for m in inst.get("materials", [])
            )
            lines.append(f"   👹 Boss：{inst['boss'][1]}(Lv.{inst['boss'][3]})· 掉落：{mats}")
            # v130.8 意见#31：钥匙需求引导——Boss 行下列出所需钥匙与获取途径
            ki = inst.get("key_item")
            if ki:
                lines.append(f"   🔑 需『{ki}』：{inst.get('key_source', '？？？')}")
            ent = inst.get("entry")
            if ent:
                _em = C.MAP_BY_ID.get(ent.get("map", ""), {}).get("name", ent.get("map", ""))
                _esa_n = ""
                for _esa2 in (C.MAP_BY_ID.get(ent.get("map", ""), {}).get("subareas") or []):
                    if _esa2.get("id") == ent.get("subarea"):
                        _esa_n = _esa2.get("name", "")
                        break
                lines.append(f"   📍 入口：{_em}·{_esa_n or ent.get('subarea', '')}")
        lines.append("━━━━━━━━━━━━")
        lines.append(self._tip("instance"))
        lines.append("💡 按顺序轮流出手，Boss 血量随人数上涨，配合好才能通关！")
        return "\n".join(lines)

    def _instance_status(self, group_id, qq_id, battle_row) -> str:
        st = battle_row["state"]
        # v87.2 副本地图化：地图模式显示层全景
        if st.get("mode") == "map":
            return self._instance_map_view(st, group_id)
        inst = C.INSTANCES.get(st["inst_id"], {})
        self._instance_ensure_player_fields(st)
        stages = st.get("inst_stages") or []
        stage_line = ""
        if stages:
            sidx = st.get("stage_idx", 0)
            sname = stages[sidx]["name"] if sidx < len(stages) else ""
            stage_line = f" 🚪 第 {sidx + 1} 层 · {sname}"
        # v164：战斗查看面板 = 完整 footer（站位/时刻/敌方血/全队血蓝/资源/状态），
        # 与每刻行动后弹的面板同款（对齐野外 _battle_footer 信息量），只补标题头。
        lines = [
            f"{inst.get('icon', '🏰')} 【{inst.get('name', st['inst_id'])}】 第 {st.get('round', 1)} 轮{stage_line}",
            "━━━━━━━━━━━━",
        ]
        lines.append(self._instance_battle_footer(st, group_id))
        # 行动提示（footer 不含轮到谁——由调用侧拼接；此处取当前轮转玩家）
        _cur = self._instance_current_members(group_id, st)
        turn_idx = st.get("turn", 0)
        if _cur:
            for _ in range(len(st["members"])):
                if str(st["members"][turn_idx]) in _cur:
                    break
                turn_idx = (turn_idx + 1) % len(st["members"])
        cur_key = str(st["members"][turn_idx])
        cur_p = self._player(group_id, cur_key)
        lines.append("━━━━━━━━━━━━")
        lines.append(f"⏳ 轮到 {cur_p['name'] if cur_p else cur_key} 行动！『攻击』『技能 <名称>』『防御』")
        return "\n".join(lines)

    def _instance_battle_footer(self, st: dict, group_id) -> str:
        """v164 副本战斗面板（对齐野外 _battle_footer 信息量）。

        副本每刻行动后的完整战况：双方站位图 + 时刻/行动队列 + 敌方血量 +
        全队成员血蓝 + 每人资源条 + buff/减伤/护盾状态 + 选敌引导。
        数据全部从 st（players/enemies/p_buffs/e_buffs/resources/...）取，
        与野外面板共用 _P_BUFF_NAMES/_E_BUFF_NAMES/_STACK_NAMES 显示名表
        （Main mixin 同时含 CombatCmds/InstanceCmds，getattr 兜底测试直用）。

        单人副本也走同一面板（我方一行 = 自己），保证观感与野外一致。
        """
        from ..core import formation as FM
        from ..core.formation import alive_units
        # 显示名表（CombatCmds mixin 提供；独立测试 InstanceCmds 时兜底空表）
        pbuf_names = getattr(self, "_P_BUFF_NAMES", {}) or {}
        ebuf_names = getattr(self, "_E_BUFF_NAMES", {}) or {}
        stack_names = getattr(self, "_STACK_NAMES", {}) or {}
        debuff_names = getattr(self, "_DEBUFF_NAMES", {}) or {}
        enemy_mech_stacks = getattr(self, "_ENEMY_MECH_STACKS", ()) or ()

        lines = []
        # ① 站位图：敌方阵列 + 我方存活玩家阵列（蓄力带标记，formation_view 处理）
        enemies = st.get("enemies") or []
        alive_enemies = alive_units(enemies)
        enemy_view = FM.formation_view(alive_enemies, side="enemy") if alive_enemies else []
        self._instance_ensure_player_fields(st)
        player_units = [snap for key, snap in (st.get("players") or {}).items()
                        if st.get("alive", {}).get(str(key), True)]
        ally_view = FM.formation_view(player_units, side="ally") if player_units else []
        lines.append("── 敌方 ──" if enemy_view else "")
        if enemy_view:
            lines.extend(f"  {l}" for l in enemy_view)
        lines.append("── 我方 ──")
        lines.extend(f"  {l}" for l in ally_view)

        # ② 时刻 / 行动顺序（CTB）
        _ctq = self._instance_ct_queue(st, group_id)
        if _ctq:
            lines.append(_ctq)

        # ③ 敌方血量已在站位图逐只带出（❤️当前/最大，v164.1）——不再重复汇总行

        # ④ 全队成员血蓝 + 每人资源条 + buff/减伤/护盾状态
        _cur = self._instance_current_members(group_id, st)
        shown = [m for m in st["members"] if str(m) in _cur] or st["members"]
        for m in shown:
            k = str(m)
            snap = st["players"].get(k, {})
            pname = snap.get("name") or (self._player(group_id, k) or {}).get("name", k)
            alive = st["alive"].get(k, True)
            mark = "✅" if alive else "💀"
            line = f"{mark} {pname}：❤️ {snap.get('hp', 0)}/{snap.get('max_hp', 1)} 💙 {snap.get('mp', 0)}/{snap.get('max_mp', 1)}"
            # 防御姿态标记（下一敌方行动减伤）
            if st.get("p_defending", {}).get(k):
                line += " 🛡️防御"
            lines.append(line)
            # v110 P0（#119 宠物不动）：各成员宠物战斗可用性提示（饿肚子/Lv 不足），
            # 与野外面板同款 pet_battle_status_note——副本带宠 v167.3 后玩家同样困惑
            # 『宠物怎么不出手』（饱食度 =0 技能失效是设计，但此前副本面板零提示）。
            try:
                from .combat import pet_battle_status_note as _pet_note
                _ppet = (st.get("pets") or {}).get(k) or {}
                _pn2 = _pet_note(_ppet)
                if _pn2:
                    lines.append(f"　{_pn2}")
            except Exception:
                pass
            # 资源条（读 st.resources[m]，与野外 _resource_line 同口径）
            rd = E.core_resource_def(snap.get("class_name", ""))
            if rd:
                res = (st.get("resources") or {}).get(k, {}) or {}
                key = rd.get("key", "")
                name = rd.get("name", key)
                if rd.get("type") == "switch":
                    cur_res = E.ELEMENT_CN.get(res.get(key, "fire"), "火")
                    lines.append(f"　🔮 {name}：{cur_res}系")
                else:
                    cur_res = res.get(key, 0)
                    cap = rd.get("max", 99)
                    lines.append(f"　⚡ {name}：{cur_res}/{cap}")
            # 玩家 buff（刻数>0）+ 叠层 + 护盾（读各玩家 p_buffs/mech_stacks/p_shields）
            pbuf = []
            pb = (st.get("p_buffs") or {}).get(k, {}) or {}
            for bk, bv in pb.items():
                if isinstance(bv, dict):  # 部分 buff 存 dict（阈值/值）→ 跳过
                    continue
                if bv and bv > 0 and bk in pbuf_names:
                    if bk in ("reduce_all",):  # reduce_all 存减伤百分比，特殊
                        continue
                    pbuf.append(f"{pbuf_names[bk]}(剩{bv}刻)")
            # 减伤（reduce_all 百分比 + reduce_all_left 刻数，副本 st 层级）
            _ral = int(st.get("reduce_all_left", 0) or 0)
            if _ral > 0 and pb.get("reduce_all"):
                pbuf.append(f"🛡️减伤{int(float(pb.get('reduce_all')) * 100)}%({_ral}刻)")
            stacks = (st.get("mech_stacks") or {}).get(k, {}) or {}
            for sk, sv in stacks.items():
                if sv and sv > 0 and sk in stack_names and sk not in enemy_mech_stacks:
                    pbuf.append(f"{stack_names[sk]}×{sv}")
            shields = (snap.get("p_shields") or {})
            # v167.3 显示修复（同 combat._status_line）：护盾实际按 expire_at 绝对时刻到期，
            # 旧 {turns} 兼容值 turns=0 时显示 (0刻) 很怪 → 只对真正剩余 >0 的盾显示剩余刻数。
            _now_sh = float(st.get("now", 0.0) or 0.0)
            for sname, s in shields.items():
                if (s or {}).get("value", 0) > 0:
                    _exp = (s or {}).get("expire_at")
                    _left_sec = None
                    if isinstance(_exp, (int, float)):
                        _left_sec = float(_exp) - _now_sh
                    if _left_sec is None and (s or {}).get("turns") is not None:
                        _left_sec = max(0.0, float(s.get("turns", 0) or 0)) * (ACT_TICK or 1.0)
                    if _left_sec is not None and _left_sec > 0:
                        _turns = max(1, int(round(_left_sec / (ACT_TICK or 1.0))))
                        pbuf.append(f"✨护盾{s['value']}({_turns}刻)")
                    else:
                        pbuf.append(f"✨护盾{s['value']}")
            if pbuf:
                lines.append(f"　🛡️「{' '.join(pbuf)}」")
        # 敌方单位级 buffs/stacks/debuffs（多对多阵列；v181 P3 收口：buffs 在每怪 actor dict，
        # 无共享 e_buffs——旧 st["e_buffs"] 冗余显示已删）
        ebuf = []
        for u in alive_enemies:
            for bk, bv in (u.get("buffs") or {}).items():
                # 单位 buff 可能是 dict（盾/bar 状态等）→ 跳过非刻数键
                if isinstance(bv, dict):
                    continue
                if bv and bv > 0 and bk in ebuf_names:
                    ebuf.append(f"{u.get('name', '敌')} {ebuf_names[bk]}(剩{bv}刻)")
            for dk, d in (u.get("debuffs") or {}).items():
                if dk in debuff_names:
                    _n = int((d or {}).get("n", 0) or 0)
                    if _n > 0:
                        ebuf.append(f"{u.get('name', '敌')} {debuff_names[dk]}×{_n}")
        if ebuf:
            lines.append(f"👹敌：「{' '.join(ebuf)}」")

        # ⑤ 分隔 + 提示
        lines.append("💡 选敌：『技能1 a2』打2号(纯数字同义)；治疗『技能 <名称> b1』奶自己")
        return "\n".join(lines)


    # ---------------- 副本地图化 helpers（v87.2，29 章十三节） ----------------
    def _stage_poi_state(self, st: dict, stage_idx: int) -> dict:
        """当前层 POI 使用状态表：{poi_id: {"used": bool}}"""
        return st.setdefault("stage_pois", {}).setdefault(str(stage_idx), {})

    def _poi_used(self, st: dict, stage_idx: int, poi_id: str) -> bool:
        return self._stage_poi_state(st, stage_idx).get(poi_id, {}).get("used", False)

    def _any_poi_used(self, st: dict, poi_id: str) -> bool:
        """任意层是否已用过某 POI(secret cond 跨层检查用)"""
        for _sidx_state in st.get("stage_pois", {}).values():
            if _sidx_state.get(poi_id, {}).get("used"):
                return True
        return False

    def _check_stage_secret_cond(self, st: dict):
        """当前层 secret 条件检查：cond.poi 已调查 → 隐藏房间解锁"""
        stages = st.get("inst_stages") or []
        sidx = st["stage_idx"]
        stage = stages[sidx] if sidx < len(stages) else {}
        secret = stage.get("secret")
        if secret and not st.get("stage_secret_found"):
            cond = secret.get("cond") or {}
            if cond.get("poi") and self._any_poi_used(st, cond["poi"]):
                st["stage_secret_found"] = True

    def _mark_poi_used(self, st: dict, stage_idx: int, poi_id: str):
        self._stage_poi_state(st, stage_idx)[poi_id] = {"used": True}

    def _find_stage_poi(self, stage: dict, name: str):
        """按名字找层 POI(先完全匹配，再包含匹配)"""
        pois = stage.get("pois") or []
        for p in pois:
            if p.get("name") == name:
                return p
        for p in pois:
            if name and name in p.get("name", ""):
                return p
        return None

    def _stage_virtual_map(self, st: dict) -> dict:
        """构造当前层"虚拟地图"(复用世界地图展示管线 _map_interactions)"""
        stages = st.get("inst_stages") or []
        sidx = st["stage_idx"]
        stage = stages[sidx] if sidx < len(stages) else {}
        pois = [p for p in (stage.get("pois") or []) if not self._poi_used(st, sidx, p.get("id", ""))]
        # 隐藏房间（已发现未清）并入可交互点
        secret = stage.get("secret")
        if secret and st.get("stage_secret_found") and not st.get("stage_secret_cleared"):
            for sp in secret.get("pois", []):
                if not self._poi_used(st, sidx, sp.get("id", "")):
                    pois.append(sp)
        return {
            "id": f"{st['inst_id']}:{sidx}",
            "name": stage.get("name", ""),
            "type": "副本",
            "desc": stage.get("desc", ""),
            "pois": pois,
            "inline_npcs": stage.get("npcs") or [],
            "monsters": stage.get("monsters") or [],
            "elite": stage.get("elite"),
            "boss": stage.get("boss"),
            "secret": secret,
        }

    def _instance_map_view(self, st: dict, group_id) -> str:
        """生成副本内小地图全景。

        v137 副本地图化：rooms 存档存在时按房间渲染（当前房间/可前往 LINKS/怪物剩余/
        POI 剩余/资源池），复用 world 的 _map_nav_body + _map_blocks 统一模板；否则
        回退旧层全景（_stage_virtual_map，兼容过渡）。
        """
        rooms = st.get("rooms")
        if rooms:
            cur_sa_id = st.get("cur_subarea") or ""
            # 队长名下的 st 无 cur_subarea；从队长玩家行读（开本落点已写）
            leader = st.get("leader")
            _lp = self._player(group_id, leader) if leader else None
            if not cur_sa_id and _lp:
                cur_sa_id = _lp.get("cur_subarea") or ""
            inst = C.INSTANCES.get(st["inst_id"], {})
            # v141 审计：副本大陆路径统一走 resolve_map_for（唯一入口契约）；
            # 大陆实例已销毁（world_id 残留 inst:）→ resolve_map_for None → 回退全局静态图
            cur_map = C.resolve_map_for(st.get("world_id") or "", _inst_map_id(st.get("inst_id") or "")) \
                or C.MAP_BY_ID.get(_inst_map_id(st.get("inst_id") or ""), {})
            sas = cur_map.get("subareas") or []
            cur_sa = next((s for s in sas if s["id"] == cur_sa_id), None)
            lines = []
            if _lp:
                # v141 审计 #6：_map_nav_body 第 5 参（qq_id）此前误传 group_id，
                # 导致 _visible_sas（reveal 隐藏房间判定）按群号查探索计数恒空——
                # 副本内隐藏房间（如海蚀洞窟 L3 藏宝密室）永不揭示。改传队长 qq_id。
                nav = self._map_nav_body(_lp, cur_map, cur_sa_id or "", group_id, str(leader), show_here=False, with_header=True)
                blocks = self._map_blocks(_lp, cur_map, cur_sa_id or "", group_id, str(leader))
                lines = nav + blocks
            else:
                lines.append(f"🗺️ 【{cur_map.get('name', '副本')} · {cur_sa.get('name', '') if cur_sa else ''}】")
            # 房间状态块：怪物剩余 / POI 剩余 / 资源池
            lines.append("━━━━━━━━━━━━")
            _dun = cur_map.get("dungeon") or {}
            if _dun.get("no_exit"):
                lines.append("🚪 副本内 · 无出口（没有通往外面的路）")
            _rstate = (rooms.get(cur_sa_id) or {}) if cur_sa_id else {}
            _ml = _rstate.get("monsters_left") or []
            _pl = _rstate.get("pois_left")
            _poi_names = []
            if _pl is not None:
                for _pid in _pl:
                    _p = C.POIS.get(_pid)
                    if _p and _p.get("name"):
                        _poi_names.append(_p["name"])
            if _ml:
                _names = "、".join(m[1] if isinstance(m, (list, tuple)) and len(m) > 1 else str(m) for m in _ml)
                lines.append(f"🐾 此房怪物剩余：{_names}（『探索』高概率遭遇）")
            else:
                lines.append("🐾 此房怪物已肃清。")
            if _poi_names:
                lines.append(f"🔎 此房可调查：{'、'.join(_poi_names[:6])}{'…' if len(_poi_names) > 6 else ''}(『调查 <名称>』)")
            _rp = st.get("resources_pool")
            if _rp:
                _gl = _rp.get("gold_left", 0)
                _mats = _rp.get("mats_left") or {}
                _mat_txt = "、".join(f"{k}×{v}" for k, v in _mats.items() if v)
                _pool_txt = f"💰 副本资源池剩余：{_gl} 金币" + (f" · {_mat_txt}" if _mat_txt else "")
                lines.append(_pool_txt)
            if _dun.get("boss_room") == cur_sa_id and (_rstate.get("boss_alive", False) if cur_sa_id else False):
                lines.append("👑 Boss 就在这个房间！『探索』进入战斗！")
            if st.get("cleared"):
                if st.get("loot_pile"):
                    lines.append("🎁 战利品堆：首领的遗物堆在角落（『调查 战利品堆』）")
                if st.get("secret_crack"):
                    lines.append("🧱 墙上有一块松动的墙砖……（『调查 墙砖』）")
                # v140 波2：通关后调查点层（cleared 专属；未调查完的列提示，已翻完的省略）
                _inv_pts = (C.INVESTIGATION_POINTS or {}).get(st.get("inst_id") or "", [])
                if _inv_pts:
                    _inv_done = set(st.get("investigated") or [])
                    _inv_remain = [p for p in _inv_pts if p.get("id") not in _inv_done]
                    if _inv_remain:
                        _names = "、".join(p["name"] for p in _inv_remain[:3]) + ("…" if len(_inv_remain) > 3 else "")
                        lines.append(f"🔍 通关后这里多了些可调查的痕迹：{_names}（『调查 <名称>』· 今日剩余 {max(0, INVESTIGATE_DAILY_LIMIT - self._instance_investigate_used_today(group_id, qq_id))} 次）")
            lines.append(self._tip("instance"))
            return "\n".join(lines)
        vmap = self._stage_virtual_map(st)
        stages = st.get("inst_stages") or []
        sidx = st["stage_idx"]
        stage = stages[sidx] if sidx < len(stages) else {}
        inst = C.INSTANCES.get(st["inst_id"], {})
        lines = [f"🗺️ 【{inst.get('icon', '🏰')}{inst.get('name', '')}】第 {sidx + 1} 层 · {stage.get('name', '')}"]
        lines.append("━━━━━━━━━━━━")
        desc = vmap.get("desc")
        if desc:
            lines.append(f"📜 {desc}")
        else:
            lines.append("📜 你环顾四周，准备迎接这里的敌人。")
        # 隐藏房间提示
        secret = vmap.get("secret")
        if secret and st.get("stage_secret_found") and not st.get("stage_secret_cleared"):
            lines.append(f"🔓 隐藏房间：{secret.get('desc', '')}")
        elif secret and not st.get("stage_secret_found"):
            lines.append("🤔 似乎有暗门/机关的气息……(线索可能藏在石碑或机关里)")
        # 复用世界地图展示管线：内联 POI / NPC（v87.13 场景函数）
        inter = self._map_scene(vmap, None)
        if inter:
            lines.append("━━━━━━━━━━━━")
            lines.append("✨ 场景：")
            lines.extend(f"  {l}" for l in inter)
        # v101.27 #390 通关后特殊搜刮 POI 显示（战利品堆必出 / 暗格墙砖概率 / 密室宝箱）
        if st.get("cleared"):
            if st.get("loot_pile"):
                lines.append("🎁 战利品堆：首领的遗物堆在角落（『调查 战利品堆』）")
            if st.get("secret_crack"):
                lines.append("🧱 墙上有一块松动的墙砖……（『调查 墙砖』）")
            if st.get("secret_chest"):
                lines.append("🔐 神秘宝箱：密室深处泛着微光（『调查 宝箱』）")
            # v140 波2：通关后调查点层（cleared 专属；未调查完的列提示，已翻完的省略）
            _inv_pts = (C.INVESTIGATION_POINTS or {}).get(st.get("inst_id") or "", [])
            if _inv_pts:
                _inv_done = set(st.get("investigated") or [])
                _inv_remain = [p for p in _inv_pts if p.get("id") not in _inv_done]
                if _inv_remain:
                    _names = "、".join(p["name"] for p in _inv_remain[:3]) + ("…" if len(_inv_remain) > 3 else "")
                    lines.append(f"🔍 通关后这里多了些可调查的痕迹：{_names}（『调查 <名称>』· 今日剩余 {max(0, INVESTIGATE_DAILY_LIMIT - self._instance_investigate_used_today(group_id, qq_id))} 次）")
        if st.get("cleared"):
            lines.append(self._tip("instance"))
        else:
            # 怪物
            mons = vmap.get("monsters") or []
            el = vmap.get("elite")
            if st.get("stage_cleared"):
                lines.append("━━━━━━━━━━━━")
                # #411: 肃清后明确列出剩余可调查交互物名（此前只说"调查剩余交互点"不列名，
                # 玩家不知道调查什么——vmap.pois 已过滤已用项）
                remain = [p for p in (vmap.get("pois") or []) if isinstance(p, dict) and p.get("name")]
                if remain:
                    names = "、".join(p["name"] for p in remain[:5]) + ("…" if len(remain) > 5 else "")
                    lines.append(f"✅ 本层敌人已肃清！剩余可调查：{names}(『调查 <名称>』)；『深入』前往下一层。")
                else:
                    lines.append("✅ 本层敌人已肃清！『深入』前往下一层。")
            elif vmap.get("boss"):
                lines.append("━━━━━━━━━━━━")
                lines.append(f"👑 Boss 就在前方：{vmap['boss'][1]}！『探索』进入战斗！")
            else:
                lines.append("━━━━━━━━━━━━")
                mstr = "、".join(m[1] for m in mons) + (f" ⭐精英·{el[1]}" if el else "")
                if mstr:
                    lines.append(f"🐾 敌人：{mstr}(『探索』遇怪)")
                else:
                    lines.append("🐾 这里暂时没有敌人。")
        lines.append("━━━━━━━━━━━━")
        lines.append(self._tip("instance"))
        return "\n".join(lines)

    def _stage_npcs(self, group_id, qq_id) -> list:
        """当前副本层内 NPC 列表(供『找』路由)"""
        st_row = self._instance_battle_for(group_id, qq_id)
        if not st_row:
            return []
        st = st_row["state"]
        stages = st.get("inst_stages") or []
        sidx = st.get("stage_idx", 0)
        stage = stages[sidx] if sidx < len(stages) else {}
        return stage.get("npcs") or []

    # ---------------- 开本 ----------------

    def _instance_build_state(self, kid, inst, members, boss, now, qq_id):
        """v103.7 B1-3：副本状态构建（stages 分层/地图模式判定/st 初始 dict），原 _instance_start 中段拆出"""
        stages = inst.get("stages") or []
        stage_idx = 0
        stage_pending = []  # 当前层剩余怪物（未出战）
        stage_cleared = False
        mode = "battle"  # 无 stages 老副本 / 单层 Boss 房 → 直接战斗
        if stages:
            first_stage = stages[0]
            s_mons = first_stage.get("monsters") or []
            el = first_stage.get("elite")
            if s_mons or el:
                # 地图化：首层有怪 → 进入地图模式，探索触发战斗
                mode = "map"
                stage_pending = list(s_mons)
                if el:
                    stage_pending.append(el)
                st_pre = {
                    "type": "instance",
                    "inst_id": kid,
                    "leader": str(qq_id),
                    "members": [str(m) for m in members],
                    "alive": {str(m): True for m in members},
                    "players": {},
                    "boss": None,
                    "enemy": None,
                    "turn": 0,
                    "round": 1,
                    "stage_idx": stage_idx,
                    "stage_pending": stage_pending,
                    "stage_cleared": stage_cleared,
                    "inst_stages": stages,
                    "mode": mode,
                    "stage_pois": {},
                    "stage_secret_found": False,
                    "stage_secret_cleared": False,
                    "poi_unlocks": {},
                    "skip_elite_next": False,
                    "skip_wave_next": False,
                    "boss_buff_next": False,
                    "p_buffs": {str(m): {} for m in members},
                    "p_hot": {str(m): {} for m in members},
                    "p_food_effects": {str(m): [] for m in members},
                    "p_defending": {str(m): False for m in members},
                    "mech_stacks": {str(m): {} for m in members},
                    "dot_pending": True,             # δ副本层：dot 结算闸门（首行动者结算）
                    "contribution": {},
                    "over": False,
                }
            elif first_stage.get("boss"):
                # 首层即 Boss 房（单层副本）→ 地图模式，探索触发 Boss 战
                mode = "map"
                st_pre = {
                    "type": "instance",
                    "inst_id": kid,
                    "leader": str(qq_id),
                    "members": [str(m) for m in members],
                    "alive": {str(m): True for m in members},
                    "players": {},
                    "boss": None,
                    "enemy": None,
                    "turn": 0,
                    "round": 1,
                    "stage_idx": stage_idx,
                    "stage_pending": [first_stage["boss"]],
                    "stage_cleared": stage_cleared,
                    "inst_stages": stages,
                    "mode": mode,
                    "stage_pois": {},
                    "stage_secret_found": False,
                    "stage_secret_cleared": False,
                    "poi_unlocks": {},
                    "skip_elite_next": False,
                    "skip_wave_next": False,
                    "boss_buff_next": False,
                    "p_buffs": {str(m): {} for m in members},
                    "p_hot": {str(m): {} for m in members},
                    "p_food_effects": {str(m): [] for m in members},
                    "p_defending": {str(m): False for m in members},
                    "mech_stacks": {str(m): {} for m in members},
                    "dot_pending": True,             # δ副本层：dot 结算闸门（首行动者结算）
                    "contribution": {},
                    "over": False,
                }
        if not stages:
            # 老副本（无 stages）→ 直接 Boss 战（现状）
            st_pre = None
        if st_pre is not None:
            st = st_pre
        else:
            st = {
            "type": "instance",
            "inst_id": kid,
            "leader": str(qq_id),
            "members": [str(m) for m in members],
            "alive": {str(m): True for m in members},
            "players": {},
            "boss": boss,
            "enemy": boss,
            "turn": 0,
            "round": 1,
            "stage_idx": stage_idx,
            "stage_pending": stage_pending,
            "stage_cleared": stage_cleared,
            "inst_stages": stages,
            "p_buffs": {str(m): {} for m in members},
            "p_hot": {str(m): {} for m in members},
            "p_food_effects": {str(m): [] for m in members},
            "mech_stacks": {str(m): {} for m in members},  # v59 副本叠层（按玩家持久化）
            "dot_pending": True,             # δ副本层：dot 结算闸门（首行动者结算）
            "p_defending": {str(m): False for m in members},
            "turn_time": now,
            "contribution": {},
            "threat": {str(m): 0 for m in members},
            "over": False,
        }
        # v2：由主怪构建敌方阵列 st["enemies"]（Boss+配置爪牙；怪区 map 模式 boss=None→空）
        st["enemies"] = self._instance_build_enemy_array(st, st.get("boss"))
        # v137 副本地图化：dungeon 房间池/资源池存档（开本时生成，波次 3a 消费端约定）——
        # 从 SUBAREAS[地图id] 房间的 monsters/elite/boss 槽生成 monsters_left（数量上限=
        # 配置数，打完不刷），从 SUBAREA_POIS 挂载 POI 生成 pois_left（资源池上限，探索完即空）。
        # resources_pool 由 POI loot（gold/materials/equip）+ 副本奖励配置（inst.gold/materials）
        # 汇总生成——开本时创建好资源总量，探索拾取逐次扣减（consume_poi_loot）。
        _map_id = kid[5:] if str(kid).startswith("inst_") else kid
        _dun_map = C.MAP_BY_ID.get(_map_id, {})
        _rooms_def = C.SUBAREAS.get(_map_id) or []
        if _dun_map.get("dungeon") and _rooms_def:
            _rooms = {}
            _pool_gold = 0
            _pool_mats = {}
            _pool_equip = []
            for _sa in _rooms_def:
                _sa_id = _sa.get("id", "")
                _ml = []
                for _ent in (_sa.get("monsters") or []):
                    if isinstance(_ent, (list, tuple)) and len(_ent) >= 2:
                        _ml.append(list(_ent))
                if _sa.get("elite") and isinstance(_sa["elite"], (list, tuple)) and len(_sa["elite"]) >= 2:
                    _ml.append(list(_sa["elite"]))
                # v137：Boss 房 Boss 也进怪物池（探索可遇 Boss；boss_alive 标记通关判定）
                if _sa.get("boss") and isinstance(_sa["boss"], (list, tuple)) and len(_sa["boss"]) >= 2:
                    _ml.append(list(_sa["boss"]))
                # 房间 POI 挂载（v137 dungeon_pois 已并入 SUBAREA_POIS，id 带前缀唯一）
                _poi_ids = list(C.subarea_pois(_map_id, _sa_id) or [])
                # 资源池汇总：本房间 POI loot（gold/materials/equip）
                for _pid in _poi_ids:
                    _p = C.POIS.get(_pid) or {}
                    _loot = _p.get("loot") or {}
                    _g = int(_loot.get("gold") or 0)
                    if _g > 0:
                        _pool_gold += _g
                    for _mn in (_loot.get("materials") or []):
                        _pool_mats[_mn] = _pool_mats.get(_mn, 0) + 1
                    _eq = _loot.get("equip")
                    if _eq:
                        if isinstance(_eq, list):
                            _pool_equip.extend(_eq)
                        else:
                            _pool_equip.append(_eq)
                _rooms[_sa_id] = {
                    "monsters_left": _ml,
                    "pois_left": _poi_ids,
                    "boss_alive": bool(_sa.get("boss")),
                    # v157 修复：显式记录是否为 Boss 房（普通房怪清空 + boss_alive=False
                    # 恒成立，此前被误判通关——鱼鱼实抓：入口房打小怪触发副本通关）
                    "_is_boss": bool(_sa.get("boss")),
                }
            st["rooms"] = _rooms
            # 资源池 = POI loot 总量 + 副本通关奖励配置（inst.gold / inst.materials，
            # 通关奖励走 _instance_victory 发放但池先记总量，防探索收益超配置上限）
            _inst_cfg = C.INSTANCES.get(kid) or {}
            _pool_gold += int(_inst_cfg.get("gold") or 0)
            for _mn in (_inst_cfg.get("materials") or []):
                _pool_mats[_mn] = _pool_mats.get(_mn, 0) + int(_inst_cfg.get("mat_count", 1) or 1)
            st["resources_pool"] = {
                "gold_left": _pool_gold,
                "mats_left": _pool_mats,
                "equip_left": _pool_equip,
            }
        return st

    # ---------------- v137 dungeon 房间池/资源池消耗（world 联动消费端） ----------------
    def consume_monster(self, st: dict, sa_id: str):
        """v137：从副本房间怪物池弹出 1 只怪物定义（rooms[sa_id].monsters_left 首项）。

        - sa_id 无效 / 房间无存档 / 池空 → 返回 None（调用方按"无怪可遇"处理）
        - 弹出的怪物定义保持 SUBAREAS 槽位形态：[
            mid, 名, role(boss/elite/tank/dps/healer/speedster), lv, [技能], [掉落]]
        - 仅修改 st["rooms"]，由调用方负责 db.save_battle 持久化

        v141 审计 #7（死代码接线）：本函数已接入两处消费端——
        ① world.py _instance_dungeon_move（移动遇怪弹出）
        ② instance.py _instance_explore（探索遇怪弹出）
        （原两处各自内联的 _left.pop(0) 已改调本函数，消费语义逐字等价）
        """
        rooms = st.get("rooms")
        if not rooms:
            return None
        rstate = rooms.get(sa_id)
        if not rstate:
            return None
        pool = rstate.get("monsters_left")
        if not pool:
            return None
        return pool.pop(0)

    def consume_poi_loot(self, st: dict, sa_id: str, poi_id: str):
        """v137：消费房间 POI 的 loot（从资源池扣减），返回奖励 dict 或 None。

        校验链：
          ① poi_id 必须仍在 rooms[sa_id].pois_left（探索完即空，重复调查返回 None）
          ② POI 定义从 C.POIS 查（dungeon_pois 已并入），无 loot 的 POI（篝火/石碑/机关/
             陷阱等非拾取型）→ 返回 {"gold": 0, "materials": [], "equip": []}（效果仍结算）
          ③ 资源池扣减：gold 从 resources_pool.gold_left 扣（不足则只发剩余）；
             materials 同名从 mats_left 扣（不足 1 件则跳过）；equip 从 equip_left 移出
             （不足则跳过）。
        成功（或 POI 无 loot 但已在池中）→ 从 pois_left 移除并返回奖励 dict；
        poi 不在池中 / 房间无存档 → None（调用方文案"已被搜刮一空"）。

        v141 审计 #7（死代码评估）：本函数当前仍**无调用方**（保留死代码）——
        房间 POI 的实际消费走 instance.py instance_investigate 的 ③ 层（_pois_left.remove
        直接移出 + _handle_poi 效果链路），因该路径同时要产出交互文案/效果文本，
        且 _handle_poi 的效果结算与资源池扣减是两段耦合逻辑，接入 consume_poi_loot
        会拆散交互文本与奖励发放（体验/代码耦合都更差）。保留本函数作公共 API：
        未来"拾取型 POI 独立结算"或跨命令复用资源池扣减时直接调用。不强行删。
        """
        rooms = st.get("rooms")
        if not rooms:
            return None
        rstate = rooms.get(sa_id)
        if not rstate:
            return None
        pois_left = rstate.get("pois_left")
        if pois_left is None or poi_id not in pois_left:
            return None
        pool = st.setdefault("resources_pool", {})
        gold_left = int(pool.get("gold_left", 0) or 0)
        mats_left = pool.setdefault("mats_left", {})
        equip_left = pool.setdefault("equip_left", [])
        poi = C.POIS.get(poi_id) or {}
        loot = poi.get("loot") or {}
        reward = {"gold": 0, "materials": [], "equip": []}
        # 金币：资源池扣减（不足则只发剩余）
        g = int(loot.get("gold") or 0)
        if g > 0:
            take = min(g, gold_left)
            if take > 0:
                gold_left -= take
                reward["gold"] = take
        # 材料：同名从 mats_left 扣（不足 1 件则跳过）
        for mn in (loot.get("materials") or []):
            if mats_left.get(mn, 0) > 0:
                mats_left[mn] -= 1
                reward["materials"].append(mn)
        # 装备：从 equip_left 移出（不足则跳过）
        for eq in (loot.get("equip") or []):
            try:
                equip_left.remove(eq)
                reward["equip"].append(eq)
            except ValueError:
                pass
        pool["gold_left"] = gold_left
        # 已消费 POI 移出剩余列表（探索完即空语义）
        pois_left.remove(poi_id)
        return reward


    async def _instance_start(self, event, group_id, qq_id, player, arg):
        kid = None
        for k, inst in C.INSTANCES.items():
            if inst["name"] == arg or k == arg:
                kid = k
                break
        if not kid:
            yield event.plain_result(f"没有『{arg}』这个副本！『副本』查看列表～")
            return
        inst = C.INSTANCES[kid]
        min_players = inst.get("min_players", 2)
        max_players = inst.get("max_players", 3)
        # 纯单人副本：无需组队，直接以自己开本
        if min_players <= 1 and max_players <= 1:
            members = [qq_id]
        else:
            members = db.party_members(group_id, qq_id)
            if not members:
                if min_players <= 1:
                    # v101.24 弹性副本（如哥布林营地 1-2 人）：无队可单人进
                    members = [qq_id]
                else:
                    yield event.plain_result(
                        f"『{inst['name']}』需要 {min_players}-{max_players} 人组队！先『组队 <对方名字>』～"
                    )
                    return
            else:
                if str(members[0]) != str(qq_id):
                    yield event.plain_result("只有队长才能开启副本！让队长来『副本 <名字>』吧～")
                    return
                if len(members) < min_players:
                    yield event.plain_result(
                        f"『{inst['name']}』至少需要 {min_players} 人！还差 {min_players - len(members)} 个队友，让队长『组队 <名字>』拉人～"
                    )
                    return
                if len(members) > max_players:
                    yield event.plain_result(
                        f"『{inst['name']}』最多 {max_players} 人！当前 {len(members)} 人太多了～"
                    )
                    return
        # 全队等级 / 战斗检查
        for m in members:
            p = self._player(group_id, m)
            if not p:
                yield event.plain_result("队友还没有角色！无法开本～")
                return
            if p["level"] < inst["lv"]:
                yield event.plain_result(
                    f"{p['name']} 才 Lv.{p['level']}，副本需要全队 Lv.{inst['lv']}+！"
                )
                return
            # v101.27 #393：0 血进本拦截——0 血被碰即倒体验极差，先恢复再来
            if int(p.get("hp", 0)) <= 0:
                yield event.plain_result(
                    f"💀 {p['name']} 生命值为 0！先去住宿或用药恢复，别拿命闯副本～"
                )
                return
            if self._in_battle(group_id, m):
                # v101.30d #O17：拦截时补队伍构成（playtest 影刃/小四：只报名字不知队伍现状）
                roster = "、".join(
                    (self._player(group_id, mm) or {}).get("name", mm) for mm in members
                )
                yield event.plain_result(
                    f"{p['name']} 正在战斗中，先打完再来！\n👥 当前队伍：{roster}（队友打完即可开本）"
                )
                return
            # v104 M04 P2：队员等待型副业（垂钓/采集/挖掘）中开本——此前无任何提示，
            # 队员被拉进副本锁战斗，等待结束物品照常入包（无死锁但体验突兀）。与
            # no_prof_waiting 对发起者的拦截同规则，对全队生效。
            _pw = self._prof_wait_state(group_id, m)
            if _pw and int(_pw.get("finish", 0)) > int(time.time()):
                _left = int(_pw["finish"]) - int(time.time())
                _pt = C.PROF_WAIT_BASE.get(_pw.get("type"), (0, 0, "副业"))[2]
                yield event.plain_result(
                    f"⏳ {p['name']} 还在{_pt}呢，再有 {_left} 秒完成！等 TA 忙完再开本吧～"
                )
                return
        # v86.3 入场钥匙检查（29 章 11 节）：队长持有 key_item 才能开本
        # v116 副本已通关免钥匙：已通关副本(首通记录 inst_clear_* )再进不扣钥匙、不拦门，
        # 并给出明确提示。判定复用存档成就体系（db.get_achievements），非凭空造存储。
        key_item = inst.get("key_item")
        key_free_note = ""  # 已通关免钥匙提示（有钥匙要求的副本通关过则显示）
        if key_item:
            # v141 审计 #9：钥匙三路匹配 + 通关豁免抽到 core/instance_gate.py
            # （world.py 门禁同源公共函数；开本不放行是设计——开本走完整校验，
            # 有钥匙且未通关才扣钥匙，已通关免钥匙入场）
            from ..core.instance_gate import find_instance_key_item, instance_cleared_qq
            key_entry = find_instance_key_item(group_id, qq_id, key_item)
            has_key = key_entry is not None
            cleared_before = instance_cleared_qq(group_id, qq_id, kid)
            if not has_key and not cleared_before:
                src = inst.get("key_source", "？？？")
                yield event.plain_result(
                    f"🔒 『{inst['name']}』被封印之门挡住！\n"
                    f"需要『{key_item}』才能进入(已通关副本可免钥匙)\n"
                    f"📜 获取途径：{src}"
                )
                return
            # 消耗钥匙（首通前）：已通关副本免钥匙，首通后才不扣
            if has_key and not cleared_before:
                db.remove_item(group_id, qq_id, key_entry["key"])
            else:
                key_free_note = "✅ 已通关副本，免钥匙入场！\n"
        # F2 副本入口设施化：走到入口才能开本（消费 F1 的 entry 字段 + funcs=instance 标记）
        # 兼容红线：entry 为空免校验；已通关免校验；cur_map 已在副本图视为已在入口；
        # 主线/支线 explore 目标 == 本副本图（任务内单人可进图）免校验。
        _entry_cfg = inst.get("entry")
        if _entry_cfg:
            _entry_map = _entry_cfg.get("map")
            _entry_sa = _entry_cfg.get("subarea")
            _leader_p = self._player(group_id, qq_id)
            _ok_pos = True
            if _entry_map and _entry_sa:
                _ok_pos = (str(_leader_p.get("cur_map") or "") == str(_entry_map)
                           and str(_leader_p.get("cur_subarea") or "") == str(_entry_sa))
                # 兼容红线：存量玩家 cur_map 已在副本图（旧存档徒步进图）→ 视为已在入口
                if not _ok_pos and str(_leader_p.get("cur_map") or "") == _inst_map_id(kid):
                    _ok_pos = True
            if not _ok_pos:
                # 兼容红线：已通关该副本 → 免位置校验（老玩家便利）
                from ..core.instance_gate import instance_cleared_qq
                _cleared = instance_cleared_qq(group_id, qq_id, kid)
                if not _cleared:
                    # 兼容红线：主线/支线 explore 目标 == 本副本图 → 任务内单人可进图，免校验
                    _quests = db.get_quests(group_id, qq_id)
                    _in_quest = False
                    if _quests.get("main_status") == "active":
                        _mq = next((q for q in C.MAIN_QUESTS if q["id"] == _quests.get("main_quest")), None)
                        if _mq and _mq.get("objective", {}).get("explore") == _inst_map_id(kid):
                            _in_quest = True
                    if not _in_quest:
                        _side = _quests.get("side") or {}
                        if any(
                            sq.get("status") == "active"
                            and next((q for q in C.SIDE_QUESTS if q["id"] == sid), {}).get("objective", {}).get("explore") == _inst_map_id(kid)
                            for sid, sq in _side.items()
                        ):
                            _in_quest = True
                    if not _in_quest:
                        _em_name = C.MAP_BY_ID.get(_entry_map, {}).get("name", _entry_map)
                        _esa_name = ""
                        for _esa in (C.MAP_BY_ID.get(_entry_map, {}).get("subareas") or []):
                            if _esa.get("id") == _entry_sa:
                                _esa_name = _esa.get("name", "")
                                break
                        yield event.plain_result(
                            f"📍 请先到【{_em_name}·{_esa_name or _entry_sa}】副本入口处（『前往』）再开本！\n"
                            f"（副本入口在 {_em_name} 的 {_esa_name or _entry_sa}，走到那里输入『副本 {inst['name']}』）"
                        )
                        return
        # v94 体力：开本消耗 20 体力（全队队长扣）
        _ok, _st = self._spend_stamina(group_id, qq_id, 20, player, "进入副本")
        if not _ok:
            yield event.plain_result(_st)
            return
        # 构建副本 Boss（血量按人数缩放：min_players 人数 = hp_mult，每多 1 人 +0.65；攻击 ×atk_mult）
        boss = C.build_monster(inst["boss"], {"id": kid, "name": inst["name"], "area": "instance"})
        if inst.get("mech"):
            boss["mech"] = inst["mech"]  # v58 Boss 专属机制
        hp_mult = inst["hp_mult"] + 0.65 * (len(members) - min_players)
        boss["max_hp"] = int(boss["max_hp"] * hp_mult)
        boss["hp"] = boss["max_hp"]
        boss["atk"] = int(boss["atk"] * inst["atk_mult"])
        boss["matk"] = int(boss["matk"] * inst["atk_mult"])
        now = int(time.time())
        # v86.2 副本分层（02 章 13.8）+ v87.2 副本地图化（29 章十三节）
        st = self._instance_build_state(kid, inst, members, boss, now, qq_id)
        stages = st.get("inst_stages") or []  # 恢复 stages 局部引用（输出段用）
        for m in members:
            p = self._player(group_id, m)
            # v95.19: 副本快照 max_hp/max_mp 用实时计算值（DB 字段换装备后过时），与普通战斗口径统一
            _st = E.player_final_stats(p["class_name"], p["level"], p.get("equipment", {}),
                                       p.get("class_tier", 0), p.get("attributes"),
                                       p.get("evolve_path", 0), None, p.get("race"))
            st["players"][str(m)] = {
                "name": p["name"], "qq_id": m,
                "class_name": p["class_name"], "level": p["level"],
                "hp": min(int(p.get("hp", 0)), int(_st.get("max_hp", p.get("max_hp", 100)))),
                "max_hp": int(_st.get("max_hp", p.get("max_hp", 100))),
                "mp": min(int(p.get("mp", 0)), int(_st.get("max_mp", p.get("max_mp", C.DEFAULT_MAX_MP)))),
                "max_mp": int(_st.get("max_mp", p.get("max_mp", C.DEFAULT_MAX_MP))),
                "atk": p.get("atk", 0), "def": p.get("def", 0),
                "matk": p.get("matk", 0), "mdef": p.get("mdef", 0),
                # v57：快照补算真实 spd（此前 p 无 spd 字段恒为 0，速度机制无从生效）
                "spd": E.player_final_stats(p["class_name"], p["level"], p.get("equipment", {}),
                                            p.get("class_tier", 0), p.get("attributes"),
                                            p.get("evolve_path", 0), None, p.get("race")).get("spd", 0),
                # v152 绝对时刻：玩家快照 ct = 初始等待（BASE_DELAY/spd，正数越大越晚行动）
                "ct": BT._ct_initial_wait(E.player_final_stats(p["class_name"], p["level"], p.get("equipment", {}),
                                            p.get("class_tier", 0), p.get("attributes"),
                                            p.get("evolve_path", 0), None, p.get("race")).get("spd", 0)),
                "equipment": p.get("equipment", {}),
                "skills": p.get("skills", []),
                "learned_skills": p.get("learned_skills", []),
                "class_tier": p.get("class_tier", 0),
                "evolve_path": p.get("evolve_path", 0),
                "attributes": p.get("attributes"),
                "title_bonus": self._title_bonus(group_id, m),
                # v101.24 #303：快照必须存 race——Battle 战斗内 v95.19 实时刷新用 player.get("race")
                # 重算 max_hp/max_mp，缺 race 会丢掉种族 hp 倍率（精灵月缺 ×0.95）→ 战斗内上限偏大
                # 且战斗结束写回污染 DB（实测影刃 520→548）
                "race": p.get("race"),
                # v2 多对多站位：玩家单位站位/射程/唯一 uid/单位级 buff 字段（§2.2 / §8.2）
                "rank": C.CLASSES.get(p["class_name"], {}).get("default_rank", 2),
                "reach": C.CLASSES.get(p["class_name"], {}).get("reach",
                                 C.CLASSES.get(p["class_name"], {}).get("default_rank", 2)),
                "uid": "p_{}".format(str(m)),
                "buffs": {},
                "stacks": {},
                "defending": False,
                "charging": None,
            }
        # v167.3 副本带宠物（鱼鱼拍板：野外/副本完全同一套逻辑）：每名成员按 DB 宠物挂载，
        # _instance_act 当前行动者 Battle 构造时取各自宠物（读条命中/技能节奏/伤害跟 buffs 全同野外）
        st["pets"] = {str(m): (db.pet_get(m) or {}) for m in members}
        # v2：全员站位归一（老存档恢复或字段缺省时补齐）
        self._instance_ensure_player_fields(st)
        # v57：副本行动序按速度降序（快者先出手）。真人轮流节奏不变，只是顺序由速度决定
        st["members"] = sorted(st["members"], key=lambda m: st["players"][str(m)].get("spd", 0), reverse=True)
        st["turn"] = 0
        # 锁全队
        for m in members:
            self._lock_battle(group_id, m)
        # v141 大陆隔离：开本前清理孤儿大陆实例——若全队 world_id 残留 inst: 前缀
        # （上次副本已 clear_battle 但大陆未销毁，如测试/异常路径），先销毁旧大陆，
        # 防止 _instance_battle_for 从旧大陆读到僵尸 st 拦截本次开本。
        try:
            _p0 = self._player(group_id, qq_id)
            _old_wid = (_p0 or {}).get("world_id") or ""
            if _old_wid.startswith("inst:"):
                C.destroy_instance_world(_old_wid)
        except Exception:
            pass
        # v141 大陆隔离：开本创建独立大陆实例，副本进度（st/rooms/resources_pool）
        # 挂在大陆实例上（权威源），battle_state 保留兼容镜像（读取时大陆优先）。
        # 全队 players.world_id = inst:<uuid>，位置同步到副本入口。
        _map_id = kid[5:] if str(kid).startswith("inst_") else kid
        _entry_sa = C.map_entry_subarea(_map_id)
        _world_id = C.create_instance_world(
            kid, members, boss, now=now, leader=qq_id,
            st=st,
            rooms=st.get("rooms") or {},
            resources_pool=st.get("resources_pool") or {},
        )
        st["world_id"] = _world_id
        for m in members:
            if st.get("mode") == "map" and st.get("rooms") and _entry_sa:
                db.update_player(group_id, m, cur_map=_map_id, cur_subarea=_entry_sa,
                                 world_id=_world_id)
            else:
                # 老副本（战斗模式）：只写 world_id，位置由战斗逻辑管理
                db.update_player(group_id, m, world_id=_world_id)
        self._instance_save(group_id, st)
        # v49 意见#7：队伍构成提示（单人副本跳过）
        comp = " + ".join(self._class_role_label(st["players"][str(m)]["class_name"]) for m in members)
        comp_hints = self._party_composition_hint(st) if min_players > 1 else []
        hint_lines = "\n".join(f"⚠️ {h}" for h in comp_hints)
        hint_msg = f"\n{hint_lines}" if hint_lines else ""
        if min_players > 1:
            size_tip = f"👥 队伍构成：{comp}{hint_msg}\n"
        else:
            size_tip = f"🕐 单人挑战：{comp}\n"
        stage_name = stages[0]["name"] if stages else "主厅"
        # v126 副本剧情化：入口叙事（inst 有 intro 字段才渲染，老数据无字段不显示）
        intro_note = f"\n📖 {inst['intro']}" if inst.get("intro") else ""
        # v87.2 副本地图化：地图模式显示层全景，战斗模式保持原样
        if st.get("mode") == "map":
            map_view = self._instance_map_view(st, group_id)
            yield event.plain_result(
                f"{inst['icon']} 【{inst['name']}】副本开启！你踏入了这片区域。\n"
                f"{key_free_note}"
                f"━━━━━━━━━━━━\n"
                f"{map_view}\n"
                f"━━━━━━━━━━━━\n"
                f"{size_tip}"
                f"{self._tip('instance')}\n"
                f"⏳ 副本内『移动』由队长带队；『探索』『调查』各人自由进行，遇怪全队合并进同一场战斗！"
                f"{intro_note}"
            )
            return
        stage_line = f"🚪 第 1 层 · {stage_name}\n" if stages else ""
        # v121 CTB：开本首行动者 = 存活玩家/敌方中 ct 最小者（首动玩家展示）
        _a = self._instance_next_actor(st, group_id)
        _first_actor_key = str(_a[1]) if _a[0] == "p" and _a[1] else None
        if _first_actor_key:
            first_actor_name = st["players"].get(_first_actor_key, {}).get("name", _first_actor_key)
            st["turn"] = st["members"].index(_first_actor_key)
        else:
            first_actor_name = _a[1] or "队伍"
            st["turn"] = 0
        st["turn_time"] = int(time.time())
        yield event.plain_result(
            f"{inst['icon']} 【{inst['name']}】副本开启！\n"
            f"{key_free_note}"
            f"━━━━━━━━━━━━\n"
            f"{stage_line}"
            f"📜 {inst['desc']}\n"
            f"━━━━━━━━━━━━\n"
            f"{size_tip}"
            f"{self._instance_battle_footer(st, group_id)}\n"
            f"⏳ 轮到 {first_actor_name} 行动！『攻击』『技能 <名称>』『防御』\n"
            f"💡 按 CTB 行动轴轮流出手，超时 60 秒自动防御；清光当前层怪物可『深入』下一层！"
            f"{intro_note}"
        )

    def _instance_battle_cb(self, evt: str, payload: dict):
        """v158 副本合并：battle 事件队列回调（_inst_cb 注入）。

        battle 的 _process_until 驱动敌方行动后调用。由于副本 enemies/allies 是引用
        传递（battle 改 hp 直接写回 st），这里只需处理副本层账务：
        - 敌方死亡压缩（battle 已 _remove_unit 清空 enemies，这里补 st 同步）
        - 玩家倒地标记（battle _damage_actor 扣血后，检查 alive 标记）
        - 仇恨/贡献（伤害 dealt 累加——由 _instance_act 主流程在玩家行动后统一算，
          这里不重复；回调只处理 battle 内部驱动的敌方行动带来的即时状态）
        """
        try:
            if evt == "enemy_acted":
                # 敌方行动已由 battle 结算（伤害打到 allies 引用），同步 st 存活标记。
                # b._st["players"]/["alive"] 是副本真实 st 的引用（构造时注入）。
                b = payload.get("battle")
                if not b:
                    return
                st = getattr(b, "_st", None) or {}
                players = st.get("players") or {}
                alive = st.setdefault("alive", {})
                changed = False
                for mk, snap in players.items():
                    k = str(mk)
                    if snap.get("hp", 0) <= 0 and alive.get(k, True):
                        alive[k] = False
                        changed = True
                if changed:
                    # 全员倒地 → 战斗失败（由 _instance_act 后续检测 over）
                    st["over"] = True
        except Exception:
            pass

    def _sync_players_db(self, group_id, st):
        """v95r76 #383：副本快照血量/魔力同步回 DB。

        副本战斗中玩家 hp/mp 只存在 st["players"] 快照，DB 保持开本时的值——
        战斗外逻辑（治疗满血判定 tpl_heal、『角色』面板）读 DB 会拿到过时数据：
        层肃清后『使用 治疗药水』误报"生命是满的"拒用、进 Boss 战残血开局
        （格温实测：DB 1003/1003 满血拒药，Boss 战第一刻实际 197/1003）。
        每个写回点（行动保存/切怪/层肃清）前调用，与普通战斗每刻 update_player 对齐。"""
        for m in st["members"]:
            snap = st["players"].get(str(m))
            if not snap:
                continue
            db.update_player(group_id, m,
                             hp=snap.get("hp", 0), mp=snap.get("mp", 0),
                             max_hp=snap.get("max_hp", 100), max_mp=snap.get("max_mp", 100))

    # ---------------- 行动核心 ----------------
    async def _instance_act(self, event, group_id, qq_id, player, st, action, skill_name=None, target=None):
        """副本刻行动(由攻击/技能/防御指令路由进来)

        v127.3：target 参数（『技能 <槽位> <编号>』指定目标）由 combat 层解析传入。
        """
        # v157 DEBUG：副本行动入口诊断（排查"无限回合/技能不结算"）
        try:
            import time as _t
            _dbg_cts = {str(k): round(float(v.get("ct", 0) or 0), 3) for k, v in (st.get("players") or {}).items()}
            _dbg_ects = [f"{u.get('name')}:{round(float(u.get('ct', 0) or 0), 3)}" for u in (st.get("enemies") or [])]
            _dbg_cur = self._instance_next_actor(st, group_id)
            print(f"[DBG_instance_act] qq={qq_id} action={action} skill={skill_name!r} target={target} "
                  f"turn={st.get('turn')} members={st.get('members')} p_cts={_dbg_cts} e_cts={_dbg_ects} "
                  f"next={_dbg_cur} alive={st.get('alive')} turn_time={st.get('turn_time')} now={int(_t.time())}")
        except Exception as _e:
            print(f"[DBG_instance_act] 诊断异常 {_e!r}")
        # v101.24 #301：某层肃清后进入地图模式(boss=None, stage_cleared)时，攻击/技能/防御/使用道具
        # 都会走到 st["boss"]["hp"] 对 None 下标 → 'NoneType' object is not subscriptable 裸错。
        # 层内无敌人时直接引导『深入』推进，不进入战斗刻逻辑。
        # v2 修复：判定基于 enemies 阵列存活（兼容键 st["boss"] 在阵列清空后保留引用，
        # 不能再用 not st.get("boss") 判断地图模式——否则肃清后攻击会进入空阵列战斗路径）。
        if not self._instance_enemies_alive(st) or not st.get("enemies"):
            # O111 修复：肃清提示与『深入』判定统一——层内还有未遭遇的怪物
            # （stage_pending 非空，如『深入』刚进入的新层）时不能说"已被肃清"，
            # 否则同层先提示"敌人已被肃清"又提示"还没肃清"（playtest O111 阿甘实测）。
            # 有 pending → 引导『探索』；无 pending 才是真肃清 → 引导『深入』。
            if st.get("stage_pending"):
                yield event.plain_result(
                    "当前区域还有敌人潜伏！『探索』找到它们～"
                )
                return
            nxt = ""
            stages = st.get("inst_stages") or []
            idx = st.get("stage_idx", 0)
            if stages and idx < len(stages) - 1:
                nxt = f"前方是【{stages[idx + 1]['name']}】……输入『深入』继续推进！"
            else:
                nxt = "这是最后一层，输入『深入』挑战 Boss！"
            yield event.plain_result(f"当前区域的敌人已被肃清！\n{nxt}")
            return
        members = st["members"]
        now = int(time.time())
        logs = []
        self._instance_ensure_player_fields(st)

        # 1. CTB 行动轴推进：敌我按 ct 最小者行动。
        #    v180G B7 统一 CTB：player_act = 出手登记 + advance_until_next_decision 统一推进，
        #    敌方行动（含 cast_done/宠物/DOT）由 battle 事件队列驱动，回调 _cb 同步血量/仇恨/贡献。
        #    本循环只负责：a) 确认下一个行动玩家（存活玩家 ct 最小者）b) 超时自动防御
        #    c) 无可行动玩家 → 失败结算
        while True:
            # 无可行动存活玩家（全灭/全退队）→ 直接失败结算
            if not self._instance_living_player_cts(st, group_id):
                st["over"] = True
                async for _r in self._instance_defeat(event, group_id, qq_id, player, st, logs):
                    yield _r
                return
            cts = self._instance_living_player_cts(st, group_id)
            if not cts:
                return
            cur_key = min(cts, key=lambda kk: cts[kk])
            # v157 DEBUG：轮转迭代诊断
            try:
                print(f"[DBG_loop] 迭代: 下一行动者={cur_key} 请求者={qq_id} 现有logs={len(logs)}")
            except Exception:
                pass
            if cur_key == str(qq_id):
                break
            # 非请求玩家：超时 → 自动防御（含 ct 结算）后重算；未超时 → 等待
            # v121 审计修复：auto-defend 后不刷新 turn_time——保持轮转计时起点不变，
            # 同一条指令内连续结算所有已超时者（原实现逐个 60s 消化，全队 AFK 需反复触发）
            if now - st.get("turn_time", now) > INSTANCE_TIMEOUT:
                logs += self._instance_auto_defend_player(st, group_id, cur_key)
                continue
            st["turn"] = members.index(cur_key)
            cur_name = (self._player(group_id, cur_key) or {}).get("name", cur_key)
            yield event.plain_result("\n".join(logs + [f"⏳ 现在是 {cur_name} 的刻，等待 TA 行动～"]))
            return

        # 2. 确认轮到当前玩家
        cur_idx = members.index(cur_key)
        st["turn"] = cur_idx
        st["turn_time"] = now

        # 3. 玩家行动（enemy_act=False，Boss 不立即反击）
        snap = st["players"][cur_key]
        # v121 审计修复：防御状态过期点 = 该玩家下次行动开始时（覆盖其间敌方段全部行动；
        # 若本次是防御行动，_do_defend 会重新置 True 并写回）
        st["p_defending"][cur_key] = False
        # v2 目标指定：从消息『攻击 <名字>』/『技能 <名> <目标名>』解析（None=自动）
        # v127.3：combat 层已解析好 target（『技能1 a2』槽位+编号）时优先使用
        target = target if target is not None else self._instance_extract_target(event, action, skill_name)
        # v2 敌我阵列归一（老存档恢复时补 enemies/站位字段）
        self._instance_ensure_player_fields(st)
        enemies = st["enemies"] if st.get("enemies") else [st["boss"]] if st.get("boss") else []
        if not enemies:
            # 无存活敌人（理论上不可达：入口已拦截 boss=None），防御兜底
            st["turn"] = (st["turn"] + 1) % len(members)
            st["turn_time"] = now
            self._sync_players_db(group_id, st)
            self._instance_save(group_id, st)
            yield event.plain_result("眼前已经没有敌人了！")
            return
        # v49 意见#6 仇恨：行动前记录全队血量（用于计算治疗仇恨）
        hp_before = sum(st["players"][m]["hp"] for m in members if st["alive"].get(str(m), True))
        # v2 行动前记录敌方阵列各单位血量（用于计算 dealt 贡献/仇恨）
        enemies_before = {str(u.get("uid")): int(u.get("hp", 0) or 0) for u in enemies}
        b = BT.Battle.from_state({
            "type": "instance",
            "enemy": st["boss"] or (enemies[0] if enemies else {}),
            "enemies": enemies,
            "p_buffs": st["p_buffs"].get(cur_key, {}),
            "p_hot": st.get("p_hot", {}).get(cur_key, {}),
            "p_food_effects": st.get("p_food_effects", {}).get(cur_key, []) or st.get("p_food_affixes", {}).get(cur_key, []),
            "p_defending": st["p_defending"].get(cur_key, False),
            "title_bonus": snap.get("title_bonus") or {},
            # v59：叠层/护盾随战斗持久化（副本按玩家存；v101.28d 盾 buff 化）
            "mech_stacks": st["mech_stacks"].get(cur_key, {}),
            "p_shields": snap.get("p_shields", {}) or {},
            # v101.28m #438 复测修复：副本战斗状态必须完整传递，否则召唤援军
            # （e_minions）刻结束蒸发、核心资源（resources）不持久化导致耗资源
            # 技能永不可用、round 恒 0 导致按刻 Boss 机制（召唤/回血）失序
            "round": st.get("round", 0),
            # v157 修复：透传绝对时刻 now（否则 _now 每次 0 → p_ct 不累积 → 无限出手）
            "now": st.get("now", 0.0) or 0.0,
            "e_minions": st.get("e_minions", []),
            "resources": st.get("resources", {}).get(cur_key, {}),
            "cooldown": st.get("cooldown", {}).get(cur_key, {}),
            "combo_seq": st.get("combo_seq", {}).get(cur_key, []),
            # v2 副本玩家蓄力持久化：跨刻恢复（蓄力技副本中跨刻生效）
            "charging": st.get("charging", {}).get(cur_key),
            # v121 CTB：透传玩家快照 ct（行动后 Battle 内部 _after_actor_ct("p") 推进并随写回转存）
            "p_ct": snap.get("ct", 0.0),
            "player_hit": st.get("player_hit", {}).get(cur_key, False),
            # v110 P0（#110 海盗王任务卡死）：透传击杀记录——battle._remove_unit 杀敌时
            # 即时把死亡单位快照进 b.killed_enemies（含 Boss 被最后打死的情形，此时该单位
            # 已不在 enemies 阵列，_instance_enemies_compact 无从记录）。此前未传该键，
            # 副本击杀账（_last_killed）漏记 Boss → 通关结算/主线击杀目标上报全部落空。
            "killed_enemies": st.get("killed_enemies", []) or [],
            # δ副本层：dot 结算闸门透传（A 在 Battle.from_state 读 st["dot_pending"]；
            # 全队共享敌减益，每轮只结算一次，行动后自动置 False 并写回）
            "dot_pending": st.get("dot_pending", True),
            # v122 治疗指定队友：存活成员快照引用（Battle 内改 hp 直接反映到 st["players"]）
            "allies": [st["players"][str(m)] for m in st.get("members", [])
                       if st.get("alive", {}).get(str(m), True)],
            # v158 副本合并：注入副本回调——battle 事件队列驱动敌方行动后同步副本状态。
            # 敌方伤害直接打到玩家快照（allies 引用），这里只需处理：死亡压缩/仇恨/贡献。
            # （battle 的 _enemy_turn 用 _damage_actor 扣血，allies 引用会同步；回调补副本层账务）
            "_cb": self._instance_battle_cb,
            # v158：回调需要访问真实副本 st 的 alive/players（构造 dict 只有子集）
            "players": st.get("players") or {},
            "alive": st.get("alive") or {},
            # v167.3 副本带宠物：当前行动者带自己的宠物（st["pets"] 开本/加入时按 DB 快照）。
            # 野外/副本同一套——pet_tick 由 battle 事件队列驱动，读条命中/技能节奏/伤害跟
            # buffs/装备全走与野外 Battle 相同代码（Battle.__init__ 不再按 btype 排除排程）。
            "pet": (st.get("pets") or {}).get(cur_key) or (db.pet_get(cur_key) or {}),
            # v180F 清2e：副本 tick 卡跨行动传递（行动后写回 st["tick_effects"]，此处读回
            # 由 from_state 恢复段重绑 actor——敌方 DOT/宠物卡跨行动不丢）
            "tick_effects": st.get("tick_effects") or [],
        })
        # v121 CTB：副本 Battle 由 from_state 构造未设 self.player，而 _after_actor_ct("p")
        # 按 self.player 的 _player_stats(spd) 结算玩家 ct——必须指向行动者快照，否则恒取 cost=100
        b.player = snap
        _pct_before = float(getattr(b, "p_ct", 0.0) or 0.0)
        # v180G B7 统一 CTB：player_act = 出手登记 + advance 推进到下一个真人决策点。
        # 与野外同一套代码（advance_until_next_decision 统一事件推进：怪行动/命中/dot）。
        # 返回 who = 下一个该行动的玩家（可能不是当前行动者——多玩家 CTB 交错）。
        act_logs, ended, _who_next = b.player_act(action, skill_name, snap, enemy_act=True, target=target)
        # v157 DEBUG：玩家行动后诊断（确认是否真的执行了 player_turn 且日志拼接）
        try:
            print(f"[DBG_instance_act] 行动后: action={action} skill={skill_name!r} ended={ended} "
                  f"pct_before={_pct_before:.3f} pct_after={float(b.p_ct):.3f} act_logs={len(act_logs)}条 "
                  f"敌hp={[(u.get('name'), u.get('hp')) for u in (st.get('enemies') or [])][:3]} "
                  f"result={getattr(b, 'result', None)} 玩家hp={snap.get('hp')} "
                  f"日志={act_logs[:4]}")
        except Exception:
            pass
        st["players"][cur_key] = snap
        # v180-B ①：玩家状态权威在玩家快照（b.player is snap）actor dict——写回从
        # player dict 读；st 顶层 per-player 键保留老格式供 from_state 兼容读取
        st["p_buffs"][cur_key] = b.player.get("buffs") or {}
        st.setdefault("p_hot", {})[cur_key] = b.player.get("hot") or {}
        st.setdefault("p_food_effects", {})[cur_key] = b.player.get("food_effects") or []
        st["mech_stacks"][cur_key] = b.player.get("stacks") or {}
        # v2：敌方阵列写回（逐单位 hp/buffs/stacks/defending/charging）→ 压缩死亡单位
        # v141 审计：b.enemies 与 st["enemies"] 是同一列表引用（from_state 直接传入），
        # _deal_damage 死亡单位即时 _remove_unit 移除；此处直接同步，无需再压缩。
        st["enemies"] = b.enemies
        # δ副本层：DOT 结算闸门——v152 时刻制下每个玩家行动 = 时刻推进一次，
        # 该行动者的 Battle 结算其 DOT（from_state 读 dot_pending=True）；不等待全员轮转。
        st["dot_pending"] = True
        # v101.28m #438 复测修复：战斗状态写回（援军/时刻/资源/冷却/连招持久化）
        # v152 时刻制：round 删除，st["round"] 改为展示用行动轮次（_tick_no()）
        st["round"] = b._tick_no()
        st["e_minions"] = b.e_minions
        st.setdefault("resources", {})[cur_key] = b.player.get("resources") or {}
        st.setdefault("cooldown", {})[cur_key] = b.player.get("cooldown") or {}
        st.setdefault("combo_seq", {})[cur_key] = b.player.get("combo_seq") or []
        # v180F 清2e：副本每行动重建 Battle——通用 tick 卡（DOT/宠物/武器特效周期）此前
        # 不写回 st → 下次重建全丢（敌方 DOT 跨行动不跳）。写回序列化格式（actor_ref），
        # 下次 from_state 由 battle 恢复段重绑。
        try:
            _te_ser = []
            for _e in (getattr(b, "tick_effects", None) or []):
                _actor = _e.get("actor")
                _ref = ""
                if _actor is b.player:
                    _ref = "player"
                elif _actor is b.pet:
                    _ref = "pet"
                elif any(c is _actor for c in (getattr(b, "companions", None) or [])):
                    _ref = "comp:" + str(_actor.get("uid", "") or _actor.get("name", ""))
                else:
                    for _u in b.enemies:
                        if _u is _actor:
                            _ref = str(_u.get("uid", ""))
                            break
                _te_ser.append({
                    "uid": _e.get("uid"), "kind": _e.get("kind"),
                    "interval": _e.get("interval"), "next_at": _e.get("next_at"),
                    "expire_at": _e.get("expire_at"), "data": _e.get("data") or {},
                    "source": _e.get("source", ""), "actor_ref": _ref,
                })
            st["tick_effects"] = _te_ser
        except Exception:
            pass
        # v167.3 副本带宠物：战斗宠物状态（读条限频窗口 _last_hit_at 等）写回 st["pets"]，
        # 下次该成员行动重建 Battle 时沿用——跨行动/跨怪/切层节奏不重置（野外/副本同一套）
        try:
            if b.pet:
                st.setdefault("pets", {})[cur_key] = dict(b.pet)
        except Exception:
            pass
        # v121 CTB：玩家 ct 写回快照（b.p_ct 已含该玩家行动后的 _after_actor_ct("p") 推进）
        # v152 绝对时刻制：snap["ct"] = b.p_ct（= 该玩家下次可行动绝对时刻）。
        # 其他玩家 ct 是各自独立绝对值，无需广播 -cost（绝对时刻下时间流逝由各自 next_act_at 体现）。
        # v158 副本合并：敌方 ct 不再手动流逝——battle 事件队列绝对时刻制自己管理
        # （敌方行动后 _after_actor_ct("e") 设 ct = now + cast，_process_until 按 ct 调度）。
        # 玩家 p_ct 累积（now 持久化），行动几次后自然超过敌方 ct → 敌方被队列驱动行动。
        # v157 旧补丁（敌方 ct -= 玩家耗时）与队列双算，导致敌方连续行动，已删。
        # v158 修复：写回 battle 绝对时刻 now——否则副本 from_state 每次 _now=0，
        # p_ct = 0 + cast 恒等于初始值（不累积）→ 玩家 ct 永远最小 → 无限出手/敌永不动
        # （2026-09-01 实抓根因，见 local_battle_sim 验证：透传 now 后 p_ct 正常累积、
        #  敌我 ct 交替，玩家 ct 超过敌方时敌方正常行动）
        st["now"] = getattr(b, "_now", 0.0) or 0.0
        snap["ct"] = b.p_ct
        st.setdefault("player_hit", {})[cur_key] = b._player_hit
        # v101.25 #323：防御状态必须写回——否则 Boss 反击时读 st["p_defending"] 永远是 False，
        # 副本防御减半完全不生效（playtest round67 影刃实测 93→75 仅约 -19%）
        st["p_defending"][cur_key] = bool(b.player.get("defending", False))
        # v2 副本玩家蓄力持久化：写回（含 None 表示蓄力已结束/未蓄力）
        st.setdefault("charging", {})[cur_key] = b.player.get("charging")
        snap["p_shields"] = b.player.get("shields") or {}
        # v2：敌方阵列写回（逐单位 hp/buffs/stacks/defending/charging）→ 压缩死亡单位
        st["enemies"] = b.enemies
        # v110 P0（#110 海盗王任务卡死）：battle._remove_unit 击杀即从 enemies 阵列移除
        # 单位并记入 b.killed_enemies（本次行动新击杀）——同步回 st，保证 _last_killed
        # 击杀账不漏 Boss（Boss 死时若爪牙仍存活/同刻死亡，压缩只能记录仍在阵列的单位，
        # 被 battle 提前移除的 Boss 若不在此合并即永久丢失）。与压缩返回的死亡单位去重合并。
        try:
            _bk_new = getattr(b, "killed_enemies", None) or []
            if _bk_new:
                _cur_killed = list(st.get("killed_enemies", []) or [])
                _cur_killed.extend(dict(u) for u in _bk_new if u not in _cur_killed)
                st["killed_enemies"] = _cur_killed
        except Exception:
            pass
        self._instance_enemies_compact(st)
        # v2 dealt = 全阵列 hp 减少总和（含爪牙，贡献/仇恨/击杀按单位）
        dealt_enemy = 0
        for _uid, _bh in enemies_before.items():
            cur = next((u for u in st["enemies"] if str(u.get("uid")) == _uid), None)
            if cur is not None:
                dealt_enemy += max(0, _bh - int(cur.get("hp", 0) or 0))
            else:
                # 单位已死并被压缩移除 → 原 hp 全部计入
                dealt_enemy += _bh
        dealt = dealt_enemy
        if dealt > 0:
            st["contribution"][cur_key] = st["contribution"].get(cur_key, 0) + dealt
        # v49 意见#6 仇恨：伤害/治疗积累仇恨，防御嘲讽拉仇恨
        threat = st.setdefault("threat", {})
        if dealt > 0:
            threat[cur_key] = threat.get(cur_key, 0) + dealt
        # v173.5 全层仇恨·仇恨技倍率（数据驱动）：技能定义配 hate_mult 字段的
        # （如盾卫士顿足/盾击·誓 hate_mult=4）→ 技能伤害仇恨额外 ×(hate_mult-1)；
        # 未配字段 = 普通技能，仇恨=伤害（×1）。
        # 守护姿态受击反击仇恨 ×0.5 在 battle 敌方行动段（_damage_actor 承伤链/回调）处理。
        if action == "skill" and skill_name and dealt > 0:
            _hm = 1.0
            try:
                _sk = self._find_skill_cfg(snap, str(skill_name))
                if _sk:
                    _hm = float(_sk.get("hate_mult", 1) or 1)
            except Exception:
                _hm = 1.0
            if _hm > 1:
                threat[cur_key] = threat.get(cur_key, 0) + int(dealt * (_hm - 1))
                logs.append(f"🛡️ 仇恨技！Boss 的注意力被你牢牢吸住！")
        hp_after = sum(st["players"][m]["hp"] for m in members if st["alive"].get(str(m), True))
        heal = max(0, hp_after - hp_before)
        if heal > 0:
            threat[cur_key] = threat.get(cur_key, 0) + int(heal * 0.8)
        if action == "defend":
            top = max(threat.values()) if threat else 0
            threat[cur_key] = max(threat.get(cur_key, 0), int(top * 1.3) + 50)
            # v101.25 #324：副本非 Boss 怪（精英/普通）不该念"Boss 的注意力"文案——
            # playtest round67 影刃抓包精英怪复用 Boss 挑衅台词
            _e_name = st["boss"].get("name", "怪物")
            if st["boss"].get("role") == "boss":
                logs.append(f"🛡️ 你大声挑衅，Boss 的注意力被你吸引过来！(仇恨飙升)")
            else:
                logs.append(f"🛡️ 你大声挑衅，【{_e_name}】的注意力被你吸引过来！(仇恨飙升)")
        logs += act_logs

        # O105 修复：玩家自身行动后 HP≤0（反伤/自伤/毒发等）→ 标记倒地并明确提示
        # "你已倒下，等待队友…"——此前 st["alive"] 不更新，轮转把 0 血玩家当行动者，
        # 一直显示"轮到 XX 行动"空等（playtest O105 洛洛 HP0 实测）
        if snap.get("hp", 0) <= 0 and st["alive"].get(cur_key, True):
            st["alive"][cur_key] = False
            threat[cur_key] = 0
            logs.append(f"💀 {snap.get('name', cur_key)} 倒下了！你已倒下，等待队友…")
            # 全员倒地（含同归于尽）→ 直接失败结算
            if not [mm for mm in members if st["alive"].get(str(mm), True)]:
                st["over"] = True
                if not self._instance_enemies_alive(st):
                    logs.append("⚔️ 同归于尽！你与敌人同时倒下了……")
                async for _r in self._instance_defeat(event, group_id, qq_id, player, st, logs):
                    yield _r
                return

        # v50 团队技能：广播到全队（治疗/增益/护盾/减伤/暴击/魔攻/速度）
        team_effects = getattr(b, "team_effects", None) or []
        for te in team_effects:
            if te.get("kind") == "taunt":
                # v51 嘲讽：仇恨拉满 + Boss 强制打嘲讽者
                # v173.5 全层仇恨参数（鱼鱼拍板 2026-09-04，数值模型验证）——数据驱动：
                #   嘲讽仇恨倍率 hate_taunt_mult（技能数据，默认 3）、强制锁定刻数 hate_lock_turns（默认 3）
                _tcfg = te.get("cfg") or {}
                _tm = float(_tcfg.get("hate_taunt_mult", 3) or 3)
                _tl = int(_tcfg.get("hate_lock_turns", 3) or 3)
                top = max(threat.values()) if threat else 0
                threat[cur_key] = max(threat.get(cur_key, 0), int(top * _tm) + 100)
                st["taunt_target"] = cur_key
                st["taunt_turns"] = _tl
                logs.append(f"📢 {snap.get('name', cur_key)} 大声挑衅，Boss 的仇恨被牢牢锁定！")
            else:
                logs += self._apply_team_effect(st, cur_key, te)

        # 4. 当前敌人死亡 → 分层判断（v86.2：清小怪→推进→Boss）
        # v141 审计：b.player_turn(enemy_act=False) 只改 st["enemies"] 各单位 hp，
        # 不压缩死亡单位（battle 内部 _enemy_phase 被跳过，_enemy_dead 只读存活）。
        # 副本侧全灭判定必须基于存活单位——先压缩一次（死亡单位移出，防占位误判）。
        self._instance_enemies_compact(st)
        if not self._instance_enemies_alive(st):
            # v101.27 #390 暗格守卫击杀：走精英击杀奖励 → 密室宝箱出现（不是通关）
            if st.get("secret_guard_pending"):
                st["secret_guard_pending"] = False
                kill_lines = self._instance_kill_reward(group_id, st)
                st["secret_chest"] = True
                st["mode"] = "map"
                st["boss"] = None
                st["enemy"] = None
                st["enemies"] = []
                # v167.3 副本带宠物：战斗结束回地图模式 → 重置宠物限频窗口（每场新战斗节奏独立）
                for _m0 in list((st.get("pets") or {}).keys()):
                    try:
                        (st["pets"][_m0]).pop("_last_hit_at", None)
                    except Exception:
                        pass
                for m in st["members"]:
                    self._unlock_battle(group_id, m)
                self._sync_players_db(group_id, st)
                self._instance_save(group_id, st)
                yield event.plain_result(
                    "\n".join(logs) +
                    (("\n" + "\n".join(kill_lines)) if kill_lines else "") +
                    "\n━━━━━━━━━━━━\n"
                    "✅ 精英守卫被击败了！密室深处露出一口【神秘宝箱】……\n"
                    "🔐 『调查 宝箱』看看里面藏着什么！"
                )
                return
            # v137 副本地图化：dungeon rooms 存档 → 敌人全灭后按当前房间判定
            # （Boss 房 → 通关；普通房 → 回地图模式，怪物池已消耗该房间剩余）
            if st.get("rooms"):
                cur_sa = self._player(group_id, st.get("leader") or "").get("cur_subarea", "") or ""
                _rstate = (st.get("rooms") or {}).get(cur_sa) or {}
                _kill_lines = self._instance_kill_reward(group_id, st)
                # v141 审计：Boss 房判定以"当前房间的 boss 是否已被击败"为准——
                # boss_alive 可能已被 dungeon_move 置 False（到达 Boss 房触发 Boss 战后
                # 未置 False 则保持 True），或 rooms 怪池消费后 Boss 从池中消失。
                # v157 修复：必须显式 _is_boss=True 才算 Boss 房——此前 "boss_alive=False
                # 且怪清空" 对普通房恒成立（普通房初始 boss_alive=False），导致入口房
                # 打小怪误触发通关（鱼鱼实抓 2026-09-01）。判定 Boss 已死 = 房间怪池清空
                # （Boss 从 monsters_left 消费后消失）且 _is_boss=True。
                # 老数据兜底：_is_boss 缺失时按副本配置 boss_room 推断（subarea id == boss_room）。
                _is_boss_r = bool(_rstate.get("_is_boss"))
                if not _is_boss_r:
                    _dun_cfg = (C.MAP_BY_ID.get(st.get("inst_id") or "") or {}).get("dungeon") or {}
                    _is_boss_r = (_dun_cfg.get("boss_room") or "") == cur_sa
                _room_boss = _is_boss_r and (
                    not (_rstate.get("monsters_left") or []) or bool(_rstate.get("_boss_room")))
                if _room_boss:
                    # Boss 房 Boss 被击败 → 标记 boss_alive=False + 通关（下段 _instance_victory）
                    _rstate["boss_alive"] = False
                    _rstate["_boss_room"] = True
                    # v141 审计：大陆 st 与镜像 battle 是不同对象（create 深拷贝）——
                    # 权威 st（大陆）也要同步 boss_alive/_boss_room，否则 _instance_victory
                    # 读大陆 st 时 rooms 仍是旧值（boss_alive=True）→ 通关判定失效。
                    _wid_a = st.get("world_id") or ""
                    if _wid_a.startswith("inst:"):
                        _st_inst = C.get_instance_st(_wid_a)
                        if _st_inst is not None:
                            _ra = (_st_inst.get("rooms") or {}).get(cur_sa) or {}
                            _ra["boss_alive"] = False
                            _ra["_boss_room"] = True
                st["stage_cleared"] = True
                st["over"] = False
                st["mode"] = "map"
                st["boss"] = None
                st["enemy"] = None
                st["enemies"] = []
                # v167.3 副本带宠物：肃清/Boss房战斗结束 → 重置宠物限频窗口（新一场战斗节奏独立）
                for _m0 in list((st.get("pets") or {}).keys()):
                    try:
                        (st["pets"][_m0]).pop("_last_hit_at", None)
                    except Exception:
                        pass
                for m in st["members"]:
                    self._unlock_battle(group_id, m)
                self._sync_players_db(group_id, st)
                self._instance_save(group_id, st)
                if _rstate.get("_boss_room"):
                    # Boss 房击败 → 走通关结算
                    # v141 审计：大陆 st 与镜像 battle_state 是不同对象（create 时深拷贝），
                    # 直接取 DB 行可能拿到旧 rooms（boss_alive 未清）——统一从大陆实例读权威 st。
                    _st_final = C.get_instance_st(st.get("world_id") or "") or st
                    _rstate_final = (_st_final.get("rooms") or {}).get(cur_sa) or {}
                    _rstate_final["boss_alive"] = False
                    _rstate_final["_boss_room"] = True
                    async for _r in self._instance_victory(event, group_id, qq_id, player, _st_final, logs + [f"👑 副本 Boss 已被击败！"]):
                        yield _r
                    return
                map_view = self._instance_map_view(st, group_id)
                yield event.plain_result(
                    "\n".join(logs) +
                    (("\n" + "\n".join(_kill_lines)) if _kill_lines else "") +
                    f"\n━━━━━━━━━━━━\n"
                    f"✅ 【{cur_sa}】的敌人被肃清了！\n"
                    f"{map_view}\n"
                    f"━━━━━━━━━━━━\n"
                    f"🧭 副本内可继续探索/移动，或『副本』查看进度！"
                )
                return
            stages = st.get("inst_stages") or []
            pending = st.get("stage_pending") or []
            if pending:
                # 当前层还有怪 → 切下一只
                # v95r77 #363：副本小怪/精英击杀奖励（此前击杀零播报）
                # v141 审计：dungeon rooms 副本（v137 副本地图化）的房间怪池与 stages 配置
                # 脱钩——rooms[当前房].monsters_left 才是权威池，stage_pending 只是开本时
                # 由 stages 生成的旧字段。Boss 房 Boss（从房间怪池消费）被击败后 stage_pending
                # 仍非空，但当前房间 boss_alive 已 False 且房间怪池已空 → 直接走通关结算，
                # 不再"切下一只"（否则打完 Boss 又出小怪，通关永远不触发）。
                _cur_sa_p = self._player(group_id, st.get("leader") or "").get("cur_subarea", "") or ""
                _rp = (st.get("rooms") or {}).get(_cur_sa_p) or {}
                if bool(st.get("rooms")) and not (_rp.get("monsters_left") or []) \
                        and not _rp.get("boss_alive", True):
                    _rp["_boss_room"] = True
                    _wid_p = st.get("world_id") or ""
                    if _wid_p.startswith("inst:"):
                        _sp = C.get_instance_st(_wid_p)
                        if _sp is not None:
                            _rp2 = (_sp.get("rooms") or {}).get(_cur_sa_p) or {}
                            _rp2["_boss_room"] = True
                    st["over"] = True
                    st["first_clear"] = not any(
                        a.get("ach_key") == f"inst_clear_{st['inst_id']}" and a.get("progress", 0) >= 1
                        for m in (self._instance_current_members(group_id, st) or [str(st["leader"])])
                        for a in (db.get_achievements(group_id, m) or [])
                    )
                    async for _r in self._instance_victory(event, group_id, qq_id, player, st, logs):
                        yield _r
                    return
                kill_lines = self._instance_kill_reward(group_id, st)
                nxt = pending.pop(0)
                st["boss"] = C.build_monster(nxt, {"id": st["inst_id"], "name": st["inst_id"], "area": "instance"})
                if nxt[2] == "elite":
                    # v101.28l #423：精英按人数缩放（切怪入口同样套用）
                    self._instance_elite_scale(st, st["boss"])
                st["enemy"] = st["boss"]
                # v2：重建敌方阵列（普通/精英 → 单怪阵列）
                st["enemies"] = self._instance_build_enemy_array(st, st["boss"])
                # v121 审计修复：切怪后玩家 ct 与敌方同规则重置（-spd 播种对称）
                self._instance_reset_player_cts(st)
                # v167.3 副本带宠物：肃清后敌人已清空（ended 段，切下一只）——重置宠物限频窗口
                # （新怪=新一场战斗；野外每场 Battle 新建节奏独立，副本等价对齐）
                for _m0 in list((st.get("pets") or {}).keys()):
                    try:
                        (st["pets"][_m0]).pop("_last_hit_at", None)
                    except Exception:
                        pass
                # δ副本层：切怪/换 Boss 清层——新怪无减益、新刻重新允许结算、
                # 玩家资源（叠层/护盾）不跨怪残留、轮次行动记录重置
                st["dot_pending"] = True
                st["boss"].pop("debuffs", None)                    # 新怪无减益
                st["boss"].pop("adapt", None)                      # δv1.2 §11.1：新怪无适应状态（与 debuffs 一起清）
                st["mech_stacks"] = {str(m): {} for m in st["members"]}   # 玩家资源不跨怪
                st["round"] = 1
                for i in st["members"]:
                    st["p_buffs"][i] = {}
                    st["p_defending"][i] = False
                st["turn"] = 0
                st["turn_time"] = now
                self._sync_players_db(group_id, st)  # v95r76 #383：切怪前同步快照血量
                self._instance_save(group_id, st)
                yield event.plain_result(
                    "\n".join(logs) +
                    (("\n" + "\n".join(kill_lines)) if kill_lines else "") +
                    f"\n━━━━━━━━━━━━\n"
                    f"⚔️ 又一只怪物挡在面前！\n"
                    f"{self._instance_battle_footer(st, group_id)}\n"
                    f"⏳ 轮到 {self._instance_next_player_name(st, group_id)} 行动！『攻击』『技能 <名称>』『防御』"
                )
                return
            if stages:
                last = st["stage_idx"] >= len(stages) - 1
                if not last:
                    # 清完非末层 → 地图模式（可调查剩余 POI / 深入）
                    # v95r77 #363：层肃清时最后一只怪的击杀奖励（须在 st["boss"] 置空前取）
                    kill_lines = self._instance_kill_reward(group_id, st)
                    st["stage_cleared"] = True
                    st["over"] = False
                    st["mode"] = "map"
                    st["boss"] = None
                    st["enemy"] = None
                    st["enemies"] = []
                    # v167.3 副本带宠物：肃清/层清 → 重置宠物限频窗口（新一场战斗节奏独立）
                    for _m0 in list((st.get("pets") or {}).keys()):
                        try:
                            (st["pets"][_m0]).pop("_last_hit_at", None)
                        except Exception:
                            pass
                    for m in st["members"]:
                        self._unlock_battle(group_id, m)
                    self._sync_players_db(group_id, st)  # v95r76 #383：层肃清后战斗外逻辑读 DB 须与快照一致
                    self._instance_save(group_id, st)
                    cur_name = stages[st["stage_idx"]]["name"]
                    nxt_name = stages[st["stage_idx"] + 1]["name"]
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
            # 最后一层 / 无 stages → 通关
            st["over"] = True
            # v101.27 #390 首通判断：必须在 _instance_victory 内 set_achievement 前判断，
            # 首通暗格概率 50%（复刷回落 20%）
            # v104 M04 P2：原用 st["members"][0]——该列表按速度降序(instance.py:956)不是队长，
            # 且未过滤退队者；成员[0] 是退队者时首通判定基于其成就记录。改按"任一当前成员"
            # 判定：当前成员有人通关过 → 非首通（防退队者成就误判暗格概率）。
            _fc_cur = self._instance_current_members(group_id, st) or [str(st["leader"])]
            st["first_clear"] = not any(
                a.get("ach_key") == f"inst_clear_{st['inst_id']}" and a.get("progress", 0) >= 1
                for m in _fc_cur
                for a in (db.get_achievements(group_id, m) or [])
            )
            # v141 审计：dungeon rooms 副本的 Boss 房判定——rooms 存档 + 当前房间
            # boss_alive（Boss 从房间怪池消费后为 False）时，`stage_pending` 仍非空
            # （房间怪池与 stages 配置脱钩，v137 副本地图化后 rooms 是权威池）。
            # 此时玩家实际击败的是 Boss 房 Boss，应走通关结算而非"切下一只"——补一次
            # 权威判定：当前房间 _is_boss=True 且 boss_alive 已 False 且房间怪池已空
            # → 标记通关路径（v157：必须显式 _is_boss，普通房怪清空不触发通关）。
            _cur_sa_v = self._player(group_id, st.get("leader") or "").get("cur_subarea", "") or ""
            _rv = (st.get("rooms") or {}).get(_cur_sa_v) or {}
            # v157 老数据兜底：_is_boss 缺失时按副本配置 boss_room 推断
            _is_boss_v = bool(_rv.get("_is_boss"))
            if not _is_boss_v:
                _dun_v = (C.MAP_BY_ID.get(st.get("inst_id") or "") or {}).get("dungeon") or {}
                _is_boss_v = (_dun_v.get("boss_room") or "") == _cur_sa_v
            _room_done = bool(st.get("rooms")) and not (_rv.get("monsters_left") or []) \
                and _is_boss_v
            if _room_done and st.get("rooms"):
                _rv["_boss_room"] = True
                _wid_v = st.get("world_id") or ""
                if _wid_v.startswith("inst:"):
                    _sv = C.get_instance_st(_wid_v)
                    if _sv is not None:
                        _rv2 = (_sv.get("rooms") or {}).get(_cur_sa_v) or {}
                        _rv2["_boss_room"] = True
                async for _r in self._instance_victory(event, group_id, qq_id, player, st, logs):
                    yield _r
                return
            async for _r in self._instance_victory(event, group_id, qq_id, player, st, logs):
                yield _r
            return

        # 5. v180G B7：敌方行动已由 player_act 内 advance_until_next_decision 统一驱动
        # （含读条 cast_done/召唤/DOT），血量经 _inst_cb 回调/引用同步——此处只做玩家侧收尾：
        # 倒地失败检测（battle 队列可能打死玩家）+ 下一行动玩家 = 存活玩家 ct 最小者。
        if not self._instance_living_player_cts(st, group_id):
            st["over"] = True
            if not self._instance_enemies_alive(st):
                logs.append("⚔️ 同归于尽！你与敌人同时倒下了……")
            async for _r in self._instance_defeat(event, group_id, qq_id, player, st, logs):
                yield _r
            return
        # 重算下一行动玩家 = 存活玩家中 ct 最小者（敌方由 battle 队列驱动，不参与轮转）
        cts = self._instance_living_player_cts(st, group_id)
        nxt_key = min(cts, key=lambda kk: cts[kk]) if cts else None
        if nxt_key and nxt_key in members:
            st["turn"] = members.index(nxt_key)
        else:
            st["turn"] = 0
        st["turn_time"] = now

        # 6. 保存状态（存到队长名下）并展示
        self._sync_players_db(group_id, st)  # v95r76 #383：每刻行动后同步快照血量（对齐普通战斗）
        self._instance_save(group_id, st)
        nxt_key = str(members[st["turn"]])
        nxt_p = self._player(group_id, nxt_key)
        yield event.plain_result(
            "\n".join(logs) +
            "\n━━━━━━━━━━━━\n"
            f"{self._instance_battle_footer(st, group_id)}\n"
            f"⏳ 轮到 {nxt_p['name'] if nxt_p else nxt_key} 行动！『攻击』『技能 <名称>』『防御』"
        )

    def _apply_team_effect(self, st: dict, source_key: str, te: dict) -> list:
        """v50 团队技能广播：heal_all / def_all / reduce_all / shield_all / matk_all / crit_all / spd_all / poison_all"""
        logs = []
        members = st["members"]
        alive = [str(m) for m in members if st["alive"].get(str(m), True)]
        kind = te.get("kind", "")
        eff = te.get("effect", "")
        lv = te.get("lv", 1)
        turns = E.skill_buff_turns(lv)
        stats = te.get("stats") or {}
        # 全队治疗
        if kind == "heal_all":
            heal = int(te.get("matk", 0) * te.get("power", 4.0) * E.skill_power_mult(lv))
            for k in alive:
                if k == source_key:
                    continue  # 施放者已由 Battle 内部治疗
                p = st["players"][k]
                p["hp"] = min(p.get("max_hp", p["hp"]), p.get("hp", 0) + heal)
                logs.append(f"✨ {p.get('name', k)} 恢复 {heal} 点生命！")
            return logs
        # 全队 buff（写入各自 p_buffs，Boss 刻按仇恨打时生效）
        buff_effects = {
            "def_all": "def_up", "atk_all": "atk_up",
            "matk_all": "matk_up_strong", "crit_all": "crit_up", "spd_all": "spd_up",
        }
        # v151 刻制审计：reduce_all 从映射表移除（原误映射 def_up，与单机 v113.1 口径分裂）——
        # 真·百分比减伤：p_buffs["reduce_all"]=减伤百分比（float），刻记 st["reduce_all_left"]
        if kind == "reduce_all":
            pct = float(te.get("reduce_all") or (stats or {}).get("reduce_all") or 0)
            st["reduce_all_left"] = max(int(st.get("reduce_all_left", 0) or 0), turns)
            for k in alive:
                pb = st["p_buffs"].setdefault(k, {})
                pb["reduce_all"] = pct
            logs.append(f"🛡️ 全队减伤 {int(pct * 100)}%（持续 {st['reduce_all_left']} 刻）")
            return logs
        if kind in buff_effects:
            be = buff_effects[kind]
            for k in alive:
                if k == source_key and eff:
                    continue  # 施放者已有自身 buff
                pb = st["p_buffs"].setdefault(k, {})
                pb[be] = max(pb.get(be, 0), turns)
            logs.append("🛡️ 全队获得增益效果！")
            return logs
        # 全队护盾（v101.28d 盾 buff 化：同源叠加 + 刷新 3 刻）
        if kind == "shield_all":
            src = st["players"][source_key]
            base = stats.get("matk") or stats.get("atk") or 0
            shield = int(base * 0.20)
            for k in alive:
                p = st["players"][k]
                sh = p.setdefault("p_shields", {})
                cur = sh.get("team_bless")
                if cur:
                    cur["value"] += shield
                    cur["turns"] = max(cur.get("turns", 0), 3)
                else:
                    sh["team_bless"] = {"value": shield, "turns": 3}
                logs.append(f"🛡️ {p.get('name', k)} 获得 {shield} 点护盾！")
            return logs
        # δ副本层：全队武器淬毒→对共享 Boss 挂毒（目标级 debuffs，每轮结算一次）
        if kind == "poison_all":
            boss = st.get("boss")
            if boss:
                deb = boss.setdefault("debuffs", {})
                cur = deb.get("poison") or {"n": 0, "mult": 1.0}
                cur["n"] = min(5, cur["n"] + 2)
                cur["last_round"] = st.get("round", 0) or 0  # 记录叠层刻
                deb["poison"] = cur
                # 适应机制：团队淬毒为持续施加，+0.04（cap 0.20），回落由结算侧按刻判定
                adapt = boss.setdefault("adapt", {})
                adapt["poison"] = min(0.20, float(adapt.get("poison", 0.0) or 0.0) + 0.04)
                logs.append("☠️ 全队武器淬毒！(毒层共享，每刻结算一次)")
            return logs
        return logs

    # ---------------- v121 CTB：副本行动轴 helpers ----------------
    def _instance_living_player_cts(self, st: dict, group_id) -> dict:
        """当前在场（仍组队且未倒下）玩家快照的 {member_key: ct}，用于最小 ct 判定。"""
        cur = self._instance_current_members(group_id, st)
        self._instance_ensure_player_fields(st)
        res = {}
        for key, snap in (st.get("players") or {}).items():
            k = str(key)
            if k in cur and st.get("alive", {}).get(k, True):
                res[k] = float(snap.get("ct", 0) or 0)
        return res

    def _instance_min_player_ct(self, st: dict, group_id):
        """存活玩家最小 ct（无存活 → None）。"""
        cts = self._instance_living_player_cts(st, group_id)
        return min(cts.values()) if cts else None

    def _instance_min_enemy_ct(self, st: dict):
        """存活敌方最小 ct（无存活 → None）。"""
        cts = [float(u.get("ct", 0) or 0) for u in self._instance_enemy_units(st)]
        return min(cts) if cts else None

    def _instance_next_actor(self, st: dict, group_id):
        """CTB 下一行动者 = 存活玩家与存活敌方中 ct 最小者。
        返回 ("p", member_key) 玩家 / ("e", None) 敌方 / ("none", None) 无可行动者。
        同 ct 时玩家先（保底与现状一致）。"""
        mp = self._instance_min_player_ct(st, group_id)
        me = self._instance_min_enemy_ct(st)
        if me is None and mp is None:
            return ("none", None)
        if me is not None and (mp is None or me < mp):
            return ("e", None)
        cts = self._instance_living_player_cts(st, group_id)
        k = min(cts, key=lambda kk: cts[kk]) if cts else None
        return ("p", k) if k else ("none", None)


    def _instance_auto_defend_player(self, st: dict, group_id: int, key: str) -> list:
        """CTB 超时自动防御：走现有自动防御路径（置 p_defending 防御），并结算一次 defend
        行动的 ct（v152 绝对时刻：自身 ct += 防御耗时，其他单位不动）。
        v121 审计修复：cost 用快照速度的 buffed 口径（_player_stats 与正常行动一致，
        此前 raw spd 使超时惩罚比正常行动重 ~2.3×）。绝对时刻下其他单位 next_act_at 独立。"""
        snap = st["players"][key]
        logs = [f"⏰ {snap.get('name', key)} 迟迟没有行动，自动进入防御姿态！"]
        st["p_defending"][key] = True
        try:
            cost = BT.Battle()._ct_cost(BT.Battle()._player_stats(snap).get("spd", 0) if snap else 0)
        except Exception:
            cost = BT.Battle()._ct_cost(snap.get("spd", 0))
        snap["ct"] = float(snap.get("ct", 0) or 0) + cost
        return logs

    def _instance_ct_queue(self, st: dict, group_id: int, limit: int = 8) -> str:
        """CTB 行动队列预览：按当前 ct 排序前 limit 名，玩家标注『我』、敌标注『敌』。"""
        self._instance_ensure_player_fields(st)
        cur = self._instance_current_members(group_id, st)
        entries = []
        for u in self._instance_enemy_units(st):
            entries.append((float(u.get("ct", 0) or 0), f"{u.get('name', '怪物')}(敌)"))
        for key, snap in (st.get("players") or {}).items():
            k = str(key)
            if k in cur and st.get("alive", {}).get(k, True):
                entries.append((float(snap.get("ct", 0) or 0), f"{snap.get('name', k)}(我)"))
        entries.sort(key=lambda x: x[0])
        # v163 全局时刻显示：st["now"] = 战斗绝对时刻（1 刻 = 1 游戏秒，ACT_TICK=1.0）。
        # 玩家参照读条命中/行动序需要当前时刻（出招 X.Xs 后命中 → 命中时刻 = now + X.X）。
        _now = float(st.get("now", 0.0) or 0.0)
        return f"🕐 时刻 {_now:.1f}s ｜ ⚡ 行动顺序：" + " → ".join(p[1] for p in entries[:limit])

    def _instance_next_player_name(self, st: dict, group_id: int, fallback_key=None) -> str:
        """v121 CTB：下一位玩家行动者名字（按存活玩家 ct 最小者；无则回退 fallback_key 或队伍第一人）。"""
        nxt = self._instance_next_actor(st, group_id)
        key = None
        if nxt[0] == "p" and nxt[1]:
            key = str(nxt[1])
        if key is None:
            key = str(fallback_key) if fallback_key else str(st.get("members", [None])[0])
        return (st.get("players", {}).get(key, {}) or {}).get("name", key)

    def _find_skill_cfg(self, player: dict, skill_name: str) -> dict | None:
        """v173.5 按技能名查技能配置（数据驱动：读 hate_mult 等字段）。
        遍历 PLAYER_SKILLS 基础表 + BRANCH_SKILLS 分支表 + TUTOR_SKILLS 导师表，
        递归拍平找 name==skill_name 或 key==skill_name 的技能 cfg。
        找不到返回 None。"""
        if not skill_name:
            return None
        cls = (player or {}).get("class_name", "")
        _want = str(skill_name)
        try:
            def _scan(node):
                """递归找技能 cfg：dict 值若含 'name'/'lv'/'desc' 视为技能条目，
                否则继续下钻。返回首个匹配技能名或 key 的 cfg。"""
                if not isinstance(node, dict):
                    return None
                # 本层 key 直接命中（技能名或 ID）
                for k, v in node.items():
                    if str(k) == _want and isinstance(v, dict) and "name" in v:
                        return v
                    if isinstance(v, dict):
                        nm = str(v.get("name", ""))
                        if nm == _want:
                            return v
                # 下钻
                for v in node.values():
                    if isinstance(v, dict):
                        r = _scan(v)
                        if r is not None:
                            return r
                return None
            # 依次扫三张表
            for tb in (C.PLAYER_SKILLS, C.BRANCH_SKILLS, C.TUTOR_SKILLS or {}):
                if not isinstance(tb, dict):
                    continue
                sub = tb.get(cls)
                if isinstance(sub, dict):
                    r = _scan(sub)
                    if r is not None:
                        return r
        except Exception:
            return None
        return None


    def _sync_enemy_unit(self, st: dict, unit: dict) -> None:
        """v2：把单怪 Battle 结算后的单位状态写回 st["enemies"] 原单位（按 uid 定位）。
        覆盖 hp/max_hp/buffs/stacks/defending/charging（引擎 _enemy_turn 可能改 buffs/stacks）。"""
        uid = str(unit.get("uid"))
        for u in st.get("enemies") or []:
            if str(u.get("uid")) == uid:
                for k in ("hp", "max_hp", "buffs", "stacks", "defending", "charging"):
                    if k in unit:
                        u[k] = unit[k]
                return

    # ---------------- 结算 ----------------
    def _instance_kill_reward(self, group_id, st):
        """v95r77 #363：副本小怪/精英击杀奖励（此前击杀零播报——无经验/金币/掉落反馈）。
        v2 多对多：按当刻死亡单位列表（st["_last_killed"]，缺省回退主怪）逐单位结算——
        主怪（is_boss/is_elite/阵列首）全量 exp/gold+掉落；爪牙 exp/gold ×0.5、无掉落。

        对照野外 _kill 的 v93 经济模式：经验入账 + 金币×1.5 折算成可卖材料
        （怪物掉落池优先，通用池兜底；精英 2 种普通 1 种）。v105 q7-4：数量类资源
        （经验/材料）按存活成员数分摊（总量 // 人数，余数给第一名），不再每人各得一整份；
        图纸/稀有 key 等概率类掉落仍每人独立判定。Boss 击杀走 _instance_victory 通关奖励，
        不在此列。
        注意：副本战斗内不做升级检查（check_player_level_up 会把 hp 回满，
        会破坏战斗节奏），经验攒到出副本后野外击杀时统一结算。"""
        killed = st.get("_last_killed") or ([st["boss"]] if st.get("boss") else [])
        killed = [k for k in killed if k]
        if not killed:
            return []
        lines = []
        cur = self._instance_current_members(group_id, st)
        # 归并：跨单位累计每成员的 exp 与材料
        per_member = {}
        for _m in st["members"]:
            if str(_m) not in cur:
                continue  # v104 P1：已退队成员不参与击杀奖励
            if not st["alive"].get(str(_m), True):
                continue
            p = self._player(group_id, _m)
            if not p:
                continue
            per_member[str(_m)] = {"exp": 0, "mats": [], "p": p}
        for mdef in killed:
            # 主怪（is_boss/is_elite 或普通主怪）全量；from _scale_enemy_copy/_summon_minions
            # 派生的爪牙（is_minion）→ exp/gold ×0.5 且不掉落（§2.2 / §8.2）
            slave = bool(mdef.get("is_minion"))
            mainlike = bool(mdef.get("is_boss") or mdef.get("is_elite"))
            ratio = 0.5 if slave else 1.0
            # v105 审计修复（q7-4 用户拍板）：组队掉落按存活成员数分摊——此前每名存活成员
            # 各得整份掉落，全队经济随人数 ×n。现按存活成员数 shares 分摊（数量类资源都必须
            # 分摊）：exp/掉落价值每份 = 总量 // shares，整除余数给第一名（per_member 首项，
            # 即 st["members"] 中最靠前且存活的成员），避免总量因整除向下丢。
            # 掉落概率类（图纸/稀有 key）走 else 分支每人独立判定、不在此分摊。
            shares = len(per_member)
            if shares < 1:
                continue
            for _i, (_key, acc) in enumerate(per_member.items()):
                p = acc["p"]
                snap = st["players"].get(_key) or {}
                raw_exp = int(mdef.get("exp", 0) * ratio)
                exp = raw_exp // shares + (raw_exp % shares if _i == 0 else 0)
                diff = mdef.get("lv", 0) - p.get("level", 0)
                if diff > 5:
                    exp = int(exp * max(0.10, 1.0 - (diff - 5) * 0.15))
                elif diff < -5:
                    exp = int(exp * max(0.10, 1.0 - (-diff - 5) * 0.20))
                acc["exp"] += exp
                # 掉落（仅主怪：爪牙不掉落）
                if not slave:
                    mat_value = int(mdef.get("gold", 0) * 1.5)
                    mat_share = mat_value // shares + (mat_value % shares if _i == 0 else 0)
                    if mat_share > 0:
                        drop_pool = [m for m in (mdef.get("drops") or []) if m]
                        if not drop_pool:
                            drop_pool = ["兽肉", "狼皮", "蛇皮", "野猪牙"]
                        is_hi = mdef.get("is_elite") or mdef.get("is_boss")
                        # 测试确定性铁律（v103）：不在这里用 random.sample——新增随机数消耗
                        # 会打乱全量回归的战斗随机序列（两次跑失败点不同=随机性证据）。
                        # 掉落种类按掉落池顺序取前 N 种（确定性），数量仍按价值折算。
                        picks = drop_pool[:min(2 if is_hi else 1, len(drop_pool))]
                        per_val = mat_share / len(picks)
                        for mat_name in picks:
                            mid = E.resolve_drop(mat_name)
                            if mid is None:
                                continue
                            if mid in C.MATERIALS:
                                mprice = C.MATERIALS[mid].get("price", 0)
                                if mprice <= 0:
                                    continue
                                # q7-5 审计：向下取整（原 round 会 ±1 抖动）
                                n = max(1, min(99, int(per_val / mprice)))
                                db.add_item(group_id, _key, mid,
                                            {"name": C.display("materials", mid), "type": "材料",
                                             "stackable": True, "price": mprice}, n)
                                acc["mats"].append(f"{C.display('materials', mid)} ×{n}")
                            else:
                                # v110 审计修复：副本掉落支持消耗品钥匙（i_key_* 发放链补全）
                                _it = C.ITEMS.get(mid, {})
                                db.add_item(group_id, _key, mid,
                                            {"name": _it.get("name", mat_name), "type": _it.get("type", "消耗品"),
                                             "stackable": True, "price": _it.get("price", 0)}, 1)
                                acc["mats"].append(f"{_it.get('name', mat_name)} ×1")
            # 统计/图鉴：主怪记精英/Boss，爪牙只记普通击杀
            for _key in per_member:
                db.init_stats(group_id, _key)
                db.bump_stats(group_id, _key, kills=1, day_kills=1)
                if mainlike:
                    if mdef.get("is_elite"):
                        db.bump_stats(group_id, _key, elite_kills=1)
                    elif mdef.get("is_boss") or mdef.get("role") == "boss":
                        db.bump_stats(group_id, _key, boss_kills=1)
                db.bump_bestiary(group_id, _key, mdef.get("name", ""))
        # 写入 DB 并生成播报
        for _key, acc in per_member.items():
            p = acc["p"]
            snap = st["players"].get(_key) or {}
            exp = int(acc["exp"])
            db.update_player(group_id, _key, exp=p["exp"] + exp,
                             hp=snap.get("hp", p.get("hp", 0)), mp=snap.get("mp", p.get("mp", 0)),
                             max_hp=snap.get("max_hp", p.get("max_hp", 0)),
                             max_mp=snap.get("max_mp", p.get("max_mp", 0)))
            line = f"  {p['name']}：经验 +{exp}"
            # v167.3 副本带宠物：宠物经验/饱食度结算与野外一致（野外路径见 combat._handle_victory：
            # 宠物分得击杀基础经验 20%、战斗扣饱食度 -2）。这里按野外等价口径逐成员结算各自宠物：
            # 经验 = 本场击杀基础经验（未乘分摊/等级差的原值 ×0.2，与野外一致），只对存活且带宠者生效。
            try:
                pet = (st.get("pets") or {}).get(str(_key)) or (db.pet_get(_key) or {})
                if pet and int(pet.get("level", 0) or 0) >= 1 and not snap.get("hp", 1) <= 0:
                    # 基础经验 = 本批击杀原始 exp 合计（主怪/爪牙 ratio 前），野外取 monster.exp 一次
                    _base_exp = sum(int(kd.get("exp", 0) or 0) for kd in killed)
                    _gain = max(1, int(_base_exp * 0.2))
                    pet = db.pet_decay_satiety(dict(pet))
                    _new_sat = max(0, int(pet.get("satiety", 0) or 0) - 2)
                    _p_exp = int(pet.get("exp", 0) or 0) + _gain
                    _p_lv = int(pet.get("level", 1) or 1)
                    _lvup = False
                    while _p_exp >= C.pet_exp_need(_p_lv):
                        _p_exp -= C.pet_exp_need(_p_lv)
                        _p_lv += 1
                        _lvup = True
                    db.pet_update(_key, satiety=max(0, _new_sat), exp=_p_exp, level=_p_lv,
                                  last_sat_time=pet.get("last_sat_time"))
                    st.setdefault("pets", {})[str(_key)] = dict(pet, satiety=max(0, _new_sat),
                                                                exp=_p_exp, level=_p_lv)
                    line += f"  🐾{(pet.get('name') or '宠物')} 分得经验 +{_gain}" + (
                        f"，升至 Lv.{_p_lv}！" if _lvup else "")
            except Exception:
                pass
            # 去重材料（同击杀多单位同材料时合并数量提示）
            seen = {}
            for _ms in acc["mats"]:
                seen[_ms] = True
            if seen:
                line += f"，拾取材料 {'、'.join(list(seen))}"
            lines.append(line)
            # v105 M19 P0：副本内击杀同步推进主线进度（组队玩家路线）——主线击杀目标
            # 只挂副本时，组队通关副本的击杀必须计入，否则副本路线玩家主线卡死
            for mdef in killed:
                _ql = self._instance_main_kill_progress(group_id, _key, mdef.get("name", ""))
                if _ql:
                    lines.append(f"  {p['name']}：{'；'.join(_ql)}")
                    break
        return lines

    def _instance_main_kill_progress(self, group_id, qq_id, monster_name):
        """v105 M19 P0：副本内击杀同步推进主线进度（组队玩家路线）。

        主线击杀目标只挂副本（q3_3 海盗王·独眼杰克 / q6_2 古王·奥德里克 / q9_4 恶魔祭司·赫尔加 /
        q10_1 封印守卫(腐蚀) / q12_1 深渊猎犬 / q12_2 蚀夜(真相形态)）时，副本内击杀/通关
        必须计入主线，否则组队玩家路线主线永远卡死。匹配规则与 combat._update_quests
        一致（精确匹配 / 目标名+"精英"后缀变体）。返回提示行列表（无匹配返回空）。"""
        try:
            quests = db.get_quests(group_id, qq_id)
        except Exception:
            return []
        if not quests or quests.get("main_status") != "active":
            return []
        mid = quests.get("main_quest")
        mq = next((q for q in C.MAIN_QUESTS if q["id"] == mid), None) if mid else None
        if not mq:
            return []
        obj = mq.get("objective") or {}
        target = obj.get("kill")
        if not target:
            return []
        # 匹配规则与 combat._update_quests 一致（v104 M20 P2 前缀精确：== 或 「目标·」开头）
        if monster_name != target and not monster_name.startswith(target + "·"):
            return []
        prog = dict(quests.get("main_progress", {}))
        prog[target] = prog.get(target, 0) + 1
        quests["main_progress"] = prog
        lines = []
        if prog[target] >= obj.get("count", 1):
            quests["main_status"] = "ready"
            _g = C.NPCS.get(mq["giver"]) or C.ALL_WILD.get(mq["giver"]) or {}
            lines.append(f"📜 主线『{mq['name']}』目标达成！回去找 {_g.get('name', '？')} 对话交付吧～")
        else:
            lines.append(f"📜 主线『{mq['name']}』：{prog[target]}/{obj.get('count', 1)}")
        db.save_quests(group_id, qq_id, quests)
        return lines

    # ---------------- 通关后搜刮（v101.27 #390） ----------------
    # ---------------- v140 波2：通关后调查点（cleared 专属调查层） ----------------
    def _instance_investigate_cleared(self, group_id, qq_id, player, st, name) -> str or None:
        """通关后调查点（第①层『调查 <目标>』命中链）。

        与 POI 调查/战利品堆/暗格并行不冲突：
        - 只查 INVESTIGATION_POINTS[inst_id]（cleared 专属数据，不挂 SUBAREAS/POIS/
          rooms 资源池），命中才消费；未命中返回 None → 调用方回落战利品堆/暗格/房间 POI。
        - 每日上限 INVESTIGATE_DAILY_LIMIT=3（玩家行 investigate_date/investigate_count，
          跨日归零；与 props_use 的日记录表并存互不干扰）。
        - 奖励四层：保底材料 / 图纸残页 25% / 蓝符 15%（Lv.60+）/ 收藏 3%。

        v141 审计 P0-1（调查点误锁房间 POI）：『调查 篝火』先被调查点"篝火余烬"的
        包含匹配吞掉，本可自由调查的房间 POI（如"将熄的篝火"）被误锁。修复：
        达上限/已翻两种"非真命中"情形返回 None 回落第②③层；且玩家输入更长/同长
        于调查点名时，包含匹配不算真命中（同样回落）。
        """
        inst_id = st.get("inst_id") or ""
        points = (C.INVESTIGATION_POINTS or {}).get(inst_id) or []
        if not points:
            return None
        # 名称命中：先完全匹配，再包含匹配（与 POI 命中规则一致）
        poi = None
        for p in points:
            if p.get("name") == name:
                poi = p
                break
        if poi is None:
            for p in points:
                if name and name in p.get("name", ""):
                    poi = p
                    break
        # v141 审计 P0-1：『调查 篝火』这类输入先被调查点"篝火余烬"的包含匹配吞掉，
        # 本可自由调查的房间 POI（如"将熄的篝火"）被误锁——玩家输入更长/同长的
        # 目标名时，调查点包含匹配不算真命中，返回 None 回落第②③层（房间 POI）。
        if poi is not None and poi.get("name") != name and len(name) >= len(poi.get("name", "")):
            return None
        if poi is None:
            return None
        # 每日上限校验（玩家行日期+次数；跨日归零）
        today = time.strftime("%Y-%m-%d")
        if player.get("investigate_date") != today:
            player["investigate_date"] = today
            player["investigate_count"] = 0
        used = int(player.get("investigate_count", 0) or 0)
        if used >= INVESTIGATE_DAILY_LIMIT:
            # v141 审计 P0-1：达上限/已翻不是"真命中"（玩家输入可能同时命中房间 POI），
            # 返回 None 回落第②③层——否则『调查 篝火』会被上限文案锁死，房间 POI 查不到。
            return None
        # 已调查过的点（本副本本局内）→ 不重复
        done = st.setdefault("investigated", [])  # v141 审计 P0-2：list 初始化防 set 落库成字符串
        if not isinstance(done, set):
            try:
                done = set(done)
                st["investigated"] = done
            except Exception:
                done = set()
        if poi["id"] in done:
            # 同上：已翻不是真命中——回落第②③层（房间 POI 可自由调查，互不冲突）
            return None
        # 奖励四层 roll
        inst = C.INSTANCES.get(inst_id) or {}
        lines = [f"🔍 你仔细调查了【{poi.get('name', '调查点')}】……"]
        reward = self._instance_investigate_reward(group_id, qq_id, player, st, poi, inst)
        if not reward:
            return f"{poi.get('name', '调查点')}里空空如也，什么也没发现。"
        lines += reward
        # 记账：每日次数 +1 + 本局已调查标记（persist）
        db.update_player(group_id, qq_id,
                         investigate_date=today, investigate_count=used + 1)
        done.add(poi["id"])
        st["investigated"] = sorted(done)  # set 不可 JSON 序列化 → 落库转 list
        self._instance_save(group_id, st)
        return "\n".join(lines)

    def _instance_investigate_reward(self, group_id, qq_id, player, st, poi, inst) -> list:
        """调查点奖励发放：四层（保底材料 / 图纸残页 / 蓝符 / 收藏），返回展示行列表。

        概率（数据层 INVESTIGATION_POINTS 逐点可覆盖，缺省用命令层常量）：
        - 收藏 3% → 图纸残页 25% → 蓝符 15%（仅 Lv.60+）→ 否则保底材料 1 件。
        蓝符只在副本 Lv.60+ 生效（低等级副本该档概率并入保底材料）；
        蓝符 = 蓝色品质 RUNES 符文（C.rune_item 构造，与 _instance_secret_chest 同款），
        按副本等级就近出符：Lv.60-74 → lvl 1-2，Lv.82+ → lvl 2-3。
        """
        from ..core import runes as _runes_core  # 延迟：rune_item 在 core.runes
        inst_lv = int(inst.get("lv", 0) or 0)
        bp_chance = float(poi.get("bp_chance", INVESTIGATE_BP_CHANCE))
        rune_chance = float(poi.get("rune_chance", INVESTIGATE_RUNE_CHANCE)) if inst_lv >= 60 else 0.0
        collect_chance = float(poi.get("collect_chance", INVESTIGATE_COLLECT_CHANCE))
        r = random.random()
        # ④ 收藏（最低概率，先判）
        if r < collect_chance:
            collect = poi.get("collect")
            if collect is None:
                collect = C.INVESTIGATE_COLLECT_SAMPLES
            if not isinstance(collect, (list, tuple)):
                collect = [collect]
            for cid in collect:
                mid = C.resolve("materials", cid) if cid else None
                if mid and mid in C.MATERIALS:
                    mname = C.display("materials", mid)
                    db.add_item(group_id, qq_id, mid, {
                        "name": mname, "type": "收藏", "stackable": True,
                        "price": C.MATERIALS[mid].get("price", 1),
                    })
                    return [f"✨ 你发现了一件稀罕的收藏品——【{mname}】！(图鉴『收藏』可查看)"]
            return []  # 收藏池空 → 放弃（不入保底，防刷稀有）
        # ③ 蓝符（Lv.60+）
        if inst_lv >= 60 and r < collect_chance + rune_chance:
            blue_runes = [k for k, rr in C.RUNES.items() if (rr.get("quality") or "") == "blue"]
            if blue_runes:
                rk = random.choice(blue_runes)
                r_def = C.RUNES[rk]
                lvl = random.randint(1, 2) if inst_lv < 82 else random.randint(2, 3)
                rune_data = C.rune_item(r_def["effect"], lvl)
                if rune_data:
                    db.add_item(group_id, qq_id, f"rune_{r_def['effect']}_{rune_data['lvl']}", rune_data)
                    return [f"✨ 你拾起一枚刻着符文的宝石——【{rune_data['name']}】！"]
            # 蓝符池空 → 落保底材料（不额外消耗随机）
            pass
        # ② 图纸残页（在蓝符未命中后判定；若蓝符档并入/未命中，r 落在 [collect+rune, collect+rune+bp)）
        if r < collect_chance + rune_chance + bp_chance:
            pages = random.randint(2, 3)
            db.add_item(group_id, qq_id, "mat_tu_zhi_can_ye",
                        {"name": "图纸残页", "type": "材料", "stackable": True, "price": 10},
                        count=pages)
            return [f"📜 你翻出一叠泛黄的纸页——图纸残页 ×{pages}！"]
        # ① 保底材料（默认/兜底层）
        mats = poi.get("materials") or inst.get("materials", [])
        mat = random.choice(mats) if mats else None
        mat_id = C.resolve("materials", mat) if mat else None
        if mat_id and mat_id in C.MATERIALS:
            mname = C.display("materials", mat_id)
            db.add_item(group_id, qq_id, mat_id, {
                "name": mname, "type": "材料", "stackable": True,
                "price": C.MATERIALS[mat_id]["price"],
            })
            return [f"🎒 你摸到了些材料——{mname} ×1！"]
        return [f"🎒 你翻了翻，只找到一点零碎。"]

    def _instance_investigate_used_today(self, group_id, qq_id) -> int:
        """今日已用副本调查次数（玩家行 investigate_count；跨日视为 0）。"""
        try:
            p = self._player(group_id, qq_id)
            if not p:
                return 0
            today = time.strftime("%Y-%m-%d")
            if p.get("investigate_date") != today:
                return 0
            return int(p.get("investigate_count", 0) or 0)
        except Exception:
            return 0

    def _instance_loot_pile(self, group_id, qq_id, player, st) -> str:
        """战利品堆（必出，保底搜刮）：金币 = 通关奖金×30% + 专属材料×1
        通胀核算：Lv.25 怪金≈253，海蚀洞窟 gold=220 → 66 金 ≈ 0.26 只怪/人，
        远低于普通刷怪收益，仅作通关仪式感，不构成金币水源。

        v174 统一抽象：掉落走 drop_engine roll('loot_pile:{inst_id}')。
        """
        inst = C.INSTANCES[st["inst_id"]]
        from game.drop_engine import roll as _drop_roll, _SimpleCtx as _DropCtx
        ctx = _DropCtx(inst_id=st["inst_id"], monster_lv=int(inst.get("lv", 0) or 0),
                       player_level=int(inst.get("lv", 0) or 0),
                       gold_base=int(inst.get("gold", 100) or 100))
        lines = []
        for r in _drop_roll(f"loot_pile:{st['inst_id']}", ctx):
            if r.get("type") == "gold":
                gold = r.get("count", 0)
                db.update_player(group_id, qq_id, gold=player["gold"] + gold)
                lines.append(f"🎁 你搜刮了战利品堆：金币 +{gold}")
            elif r.get("type") == "item":
                mat_id = r["item_id"]
                if mat_id and mat_id in C.MATERIALS:
                    mname = C.display("materials", mat_id)
                    db.add_item(group_id, qq_id, mat_id, {
                        "name": mname, "type": C.MATERIALS[mat_id].get("type", "材料"), "stackable": True,
                        "price": C.MATERIALS[mat_id]["price"],
                    })
                    lines.append(f"🎒 拾取：{mname} ×1")
        if not lines:  # 引擎兜底（数据异常时保底不给空）
            lines.append("🎁 你搜刮了战利品堆，但里面空空的……")
        st["loot_pile"] = False
        self._instance_save(group_id, st)
        return "\n".join(lines)

    def _instance_secret_crack(self, group_id, qq_id, player, st) -> str:
        """隐藏暗格：墙砖松动 → 精英守卫镇守的密室。触发守卫战。"""
        stages = st.get("inst_stages") or []
        sidx = st["stage_idx"]
        stage = stages[sidx] if sidx < len(stages) else {}
        # 守卫 = 当前层 elite（无则取第一只普通怪升格）；Boss 房通常只有 Boss，
        # 跨层兜底找全副本第一只 elite/普通怪
        guard = stage.get("elite")
        if not guard and stage.get("monsters"):
            guard = stage["monsters"][0]
        if not guard:
            for _s in stages:
                if _s.get("elite"):
                    guard = _s["elite"]
                    break
                if _s.get("monsters"):
                    guard = _s["monsters"][0]
                    break
        if not guard:
            st["secret_crack"] = False
            self._instance_save(group_id, st)
            return "🧱 墙砖松动了，但后面只有一堵死墙……（暗格消失了）"
        st["secret_crack"] = False
        st["secret_guard"] = guard  # 标记守卫战（击杀走宝箱分支不通关）
        st["secret_guard_pending"] = True
        self._enter_stage_combat(group_id, st, guard, stage)
        # 守卫精英化：补 is_elite 标记（掉落/播报走精英逻辑）
        st["boss"]["is_elite"] = True
        self._instance_save(group_id, st)
        return (
            "🧱 你扣住松动的墙砖用力一拉——暗门轰然打开！\n"
            "一个魁梧的身影挡在密室前……\n"
            "━━━━━━━━━━━━\n"
            f"{self._instance_battle_footer(st, group_id)}\n"
            f"⏳ 轮到 {self._instance_next_player_name(st, group_id)} 行动！『攻击』『技能 <名称>』『防御』"
        )

    def _instance_secret_chest(self, group_id, qq_id, player, st) -> str:
        """暗格宝箱：图纸残页 25% / 装备 40% / 稀有符文 20% / 专属材料 10% / 星灵蝶蛋 5%

        v140 波1（2026-09-03）：玩家抱怨『宝箱老是图纸』——图纸占比太高（原 50%）正是根源。
        鱼鱼拍板：装备占比必须压过图纸。v140 波2 定稿：图纸残页 50%→25%、新增装备档 40%
        （Boss 池 60% / Elite 池 40% 随机挑一池，均返回 None 则换另一池）、稀有符文 30%→20%、
        专属材料 15%→10%、星灵蝶蛋 5% 不动——合计恒 100%，档位无重叠无缝隙。
        装备品质天然以紫/橙为主（Boss 池），混合 Elite 池（蓝为主）后蓝紫橙皆有；
        双池全 None 才兜底专属材料——40% 装备档永不空开。

        v174 统一抽象：掉落判定走 drop_engine roll('secret_chest:{inst_id}')（table_choice
        互斥档策略，5 档 cutoff 与旧 elif 语义精确一致）；本层只负责入包与展示文案。
        """
        inst = C.INSTANCES[st["inst_id"]]
        from game.drop_engine import roll as _drop_roll, _SimpleCtx as _DropCtx
        ctx = _DropCtx(inst_id=st["inst_id"], monster_lv=int(inst.get("lv", 0) or 0),
                       player_level=int(inst.get("lv", 0) or 0))
        results = _drop_roll(f"secret_chest:{st['inst_id']}", ctx)
        text = ""
        for r in results:
            t = r.get("type")
            if t == "petegg" and r.get("data"):
                egg = r["data"]
                db.add_item(group_id, qq_id, "petegg_pet_starbutterfly", egg)
                text = f"🦋 宝箱深处泛着星光——是【{egg['name']}】！『使用 宠物蛋』孵化！"
            elif t == "item" and r.get("item_id") == "mat_tu_zhi_can_ye":
                pages = r.get("count", 3)
                db.add_item(group_id, qq_id, "mat_tu_zhi_can_ye",
                            {"name": "图纸残页", "type": "材料", "stackable": True, "price": 10},
                            count=pages)
                text = f"📜 宝箱里是泛黄的纸张——图纸残页 ×{pages}！"
            elif t == "equip" and r.get("data"):
                eq = r["data"]
                eq_key = f"eq_{uuid.uuid4().hex[:8]}"
                db.add_item(group_id, qq_id, eq_key, eq)
                _qmark = {"green": "🟢", "blue": "🔵", "purple": "✨🟣", "orange": "🌟🟠"}.get(
                    eq.get("quality", ""), "")
                text = f"{_qmark} 宝箱深处静静躺着一件装备——【{eq['name']}】！"
            elif t == "rune" and r.get("data"):
                rune_data = r["data"]
                # 引擎已构造 rune_item（带 effect/lvl），key 与战斗掉落一致可叠加
                db.add_item(group_id, qq_id,
                            f"rune_{rune_data.get('effect', '')}_{rune_data.get('lvl', 1)}",
                            rune_data)
                text = f"✨ 宝箱里泛起微光——符文【{rune_data['name']}】！"
            elif t == "item" and r.get("item_id") and r["item_id"] != "mat_tu_zhi_can_ye":
                mat_id = r["item_id"]
                if mat_id in C.MATERIALS:
                    n = r.get("count", 2)
                    db.add_item(group_id, qq_id, mat_id, {
                        "name": C.display("materials", mat_id), "type": "材料",
                        "stackable": True, "price": C.MATERIALS[mat_id]["price"],
                    }, count=n)
                    text = f"🎒 宝箱里是稀有材料——{C.display('materials', mat_id)} ×{n}！"
        if not text:  # 引擎空结果兜底（数据异常不吞奖励）
            mat = random.choice(inst.get("materials", ["兽肉"]))
            mat_id = C.resolve("materials", mat)
            db.add_item(group_id, qq_id, mat_id, {
                "name": C.display("materials", mat_id), "type": "材料",
                "stackable": True, "price": C.MATERIALS[mat_id]["price"],
            }, count=2)
            text = f"🎒 宝箱里是稀有材料——{C.display('materials', mat_id)} ×2！"
        st["secret_chest"] = None
        self._instance_save(group_id, st)
        return "🔐 你打开了密室宝箱！\n" + text

    async def _instance_victory(self, event, group_id, qq_id, player, st, logs):
        inst = C.INSTANCES[st["inst_id"]]
        # v137：Boss 可能已从 st["boss"] 置空（enemies 阵列承载），从阵列找 role=boss 或取首个
        boss = st.get("boss")
        if not boss or not isinstance(boss, dict):
            boss = next((u for u in (st.get("enemies") or []) if u.get("role") == "boss"), None) \
                or next((u for u in (st.get("enemies") or [])), None) or {}
        # v110 P0（#110 海盗王任务卡死）：副本 Rooms Boss 战击杀后 st["boss"] 已被清空、
        # enemies 阵列空——本场击杀账（_last_killed，经 _instance_enemies_compact 合并
        # battle 击杀记录）里取 Boss 单位兜底，保证通关播报/宠物经验/主线击杀目标上报
        # （_instance_main_kill_progress）能拿到 Boss 名。此前取 {} → 任务进度静默落空。
        if not boss.get("name"):
            _lk = st.get("_last_killed") or []
            boss = next((u for u in _lk if isinstance(u, dict) and
                         (u.get("role") == "boss" or u.get("is_boss"))), None) \
                or next((u for u in _lk if isinstance(u, dict) and u.get("name")), None) or boss
        lines = [x for x in logs if "你击败了" not in x]
        lines.append("")
        lines.append(f"🎉 【{boss.get('name', '副本首领')}】被击败了！{inst.get('icon', '🏰')}{inst.get('name', '')} 通关！")
        # v126 副本剧情化：通关叙事（inst 有 outro 字段才渲染，老数据无字段不显示）
        if inst.get("outro"):
            lines.append(f"📜 {inst['outro']}")
        # v101.27 #390：通关后允许停留搜刮（鱼鱼拍板）——不再 clear_battle，
        # 保留状态让玩家调查 Boss 房交互物/战利品堆/隐藏暗格，主动『离开副本』才清。
        # 解锁战斗锁（可自由行动），但 battle 记录保留供副本指令读取
        # v104 P1：只解锁当前队伍成员——退队者可能已在别处战斗，不能动 TA 的锁
        cur = self._instance_current_members(group_id, st)
        for m in st["members"]:
            if str(m) not in cur:
                continue
            self._unlock_battle(group_id, m)
        # 通关奖励
        for m in st["members"]:
            if str(m) not in cur:
                continue  # v104 P1：已退队成员不参与通关奖励
            if not st["alive"].get(str(m), True):
                lines.append(f"  💀 {st['players'].get(str(m), {}).get('name', m)} 已阵亡，未能获得奖励")
                continue
            p = self._player(group_id, m)
            if not p:
                continue
            gold = inst.get("gold", 100)
            exp = inst.get("exp", 150)
            snap = st["players"][str(m)]
            db.update_player(group_id, m, gold=p["gold"] + gold, exp=p["exp"] + exp,
                             hp=snap["hp"], mp=snap["mp"],
                             max_hp=snap["max_hp"], max_mp=snap["max_mp"])
            lines.append(f"  {p['name']}：金币 +{gold} 经验 +{exp}")
            # v167.3 副本带宠物：通关 Boss 击杀宠物分经验 + 扣饱食度（与野外 _handle_victory
            # 同口径：基础经验 20%、-2 饱食度）。Boss 血量按人数放大，经验按 Boss 原始 exp 计。
            try:
                pet = (st.get("pets") or {}).get(str(m)) or (db.pet_get(m) or {})
                if pet and not st["alive"].get(str(m), True) is False:
                    _gain = max(1, int(int(boss.get("exp", 0) or 0) * 0.2))
                    pet = db.pet_decay_satiety(dict(pet))
                    _new_sat = max(0, int(pet.get("satiety", 0) or 0) - 2)
                    _p_exp = int(pet.get("exp", 0) or 0) + _gain
                    _p_lv = int(pet.get("level", 1) or 1)
                    _lvup = False
                    while _p_exp >= C.pet_exp_need(_p_lv):
                        _p_exp -= C.pet_exp_need(_p_lv)
                        _p_lv += 1
                        _lvup = True
                    db.pet_update(m, satiety=max(0, _new_sat), exp=_p_exp, level=_p_lv,
                                  last_sat_time=pet.get("last_sat_time"))
                    st.setdefault("pets", {})[str(m)] = dict(pet, satiety=max(0, _new_sat),
                                                             exp=_p_exp, level=_p_lv)
                    lines.append(f"  🐾{(pet.get('name') or '宠物')} 分得经验 +{_gain}" + (
                        f"，升至 Lv.{_p_lv}！" if _lvup else ""))
            except Exception:
                pass
            # v105 M19 P0：副本 Boss 击杀同步推进主线进度（组队玩家路线，
            # 与 _instance_kill_reward 内小怪/精英击杀同款接入）
            _ql = self._instance_main_kill_progress(group_id, m, boss.get("name", ""))
            if _ql:
                lines.append(f"  {p['name']}：{'；'.join(_ql)}")
            # v135 副本全员图纸小概率：每名存活成员独立判定（首功图纸之外的全员奖励，
            # 概率 constants.INSTANCE_BP_CHANCE=10%）。已学图纸折算图纸残页，未学整张入包。
            if random.random() < C.INSTANCE_BP_CHANCE:
                bp2 = C.roll_blueprint(boss.get("lv", 1) or 1)
                if bp2:
                    _learned2 = (p.get("learned_blueprints") or [])
                    if bp2.get("blueprint_for") in _learned2:
                        _pages2 = {"white": 1, "green": 1, "blue": 2, "purple": 4, "orange": 6}.get(bp2.get("quality", "white"), 1)
                        db.add_item(group_id, m, "mat_tu_zhi_can_ye",
                                    {"name": "图纸残页", "type": "材料", "stackable": True, "price": 10},
                                    count=_pages2)
                        lines.append(f"  📜 {p['name']} 拾取图纸：{bp2['name']}（已学会，化作 {_pages2} 张图纸残页）")
                    else:
                        db.add_item(group_id, m, f"bp_{uuid.uuid4().hex[:8]}", bp2)
                        lines.append(f"  📜 {p['name']} 拾取图纸：{bp2['name']}")
            # v174 统一抽象：Boss 装备掉落判定走 drop_engine table 池（boss:{inst_id}）
            # 产出 equip 类型（主题装/专属）由本层入包；材料档保持原逻辑下方处理。
            try:
                from game.drop_engine import roll as _boss_roll, _SimpleCtx as _BossCtx
                _bctx = _BossCtx(inst_id=st.get("inst_id"), monster_lv=boss.get("lv", 1) or 1,
                                 player_level=boss.get("lv", 1) or 1)
                # 当前实例专属 rid（区分展示文案：👑专属 vs ⚔️珍藏）
                _boss_cfg = (getattr(C, "INSTANCE_BOSS_EQUIP_DROP", None) or {}).get(st.get("inst_id")) or {}
                _excl_rid = _boss_cfg.get("boss_equip") or _boss_cfg.get("equip")
                _eq_results = [x for x in _boss_roll(f"boss:{st.get('inst_id')}", _bctx)
                               if x.get("type") == "equip" and x.get("data")]
                for _r in _eq_results:
                    _be_eq = _r["data"]
                    db.add_item(group_id, m, f"eq_{uuid.uuid4().hex[:8]}", _be_eq)
                    _is_excl = bool(_excl_rid) and _be_eq.get("name") == C.EQUIP_ROSTER.get(_excl_rid, {}).get("name")
                    if _is_excl:
                        lines.append(f"  👑 {p['name']} 从Boss身上拾取稀有专属：【{_be_eq['name']}】！")
                    else:
                        lines.append(f"  ⚔️ {p['name']} 拾取 Boss 珍藏：【{_be_eq['name']}】！")
            except Exception:
                pass
            # 专属材料
            mats = inst.get("materials", [])
            for _ in range(inst.get("mat_count", 1)):
                mat = random.choice(mats) if mats else None
                mat_id = C.resolve("materials", mat) if mat else None  # v48：中文名 → ID
                if mat_id and mat_id in C.MATERIALS:
                    mname = C.display("materials", mat_id)
                    db.add_item(group_id, m, mat_id, {
                        "name": mname, "type": "材料", "stackable": True,
                        "price": C.MATERIALS[mat_id]["price"],
                    })
                    lines.append(f"  🎒 {p['name']} 拾取：{mname}")
        # 贡献最高 → 职业图纸
        # v136 副本 Boss 原石掉落（Phase 2 定稿：20% 掉 1 颗随机原石，3-10 层；Boss 专属
        # 固定属性倾向查 GEM_BOSS_FIXED[boss 名]——深海龙王·敖澜=pene_magi 法穿等）。
        # 每名存活成员独立判定；掉落只吃 1 次 random.random()，不影响副本其余随机序列。
        gem_drop_line = ""
        try:
            _gem = C.roll_gem_drop(boss)
            if _gem:
                db.add_item(group_id, m, f"gem_{uuid.uuid4().hex[:8]}", _gem)
                gem_drop_line = f"  💎 {p['name']} 获得幸运宝石：{_gem['name']}！(『原石』镶嵌到装备孔位)"
        except Exception:
            gem_drop_line = ""
        if gem_drop_line:
            lines.append(gem_drop_line)
        if inst.get("blueprint") and st.get("contribution"):
            top_key = max(st["contribution"], key=st["contribution"].get)
            if str(top_key) not in cur:
                top_key = None  # v104 P1：首功是退队者 → 图纸不发（避免白拿）
            if top_key:
                top_p = self._player(group_id, top_key)
                if top_p:
                    bp = C.roll_blueprint(boss.get("lv", 1) or 1)
                    # v101.25 #349：首功图纸奖励同规则——已学图纸折算为图纸残页
                    _learned = (top_p.get("learned_blueprints") or [])
                    if bp.get("blueprint_for") in _learned:
                        _pages = {"white": 1, "green": 1, "blue": 2, "purple": 4, "orange": 6}.get(bp.get("quality", "white"), 1)
                        db.add_item(group_id, top_key, "mat_tu_zhi_can_ye",
                                    {"name": "图纸残页", "type": "材料", "stackable": True, "price": 10},
                                    count=_pages)
                        lines.append(f"👑 首功 {top_p['name']} 额外获得图纸：{bp['name']}（已学会，化作 {_pages} 张图纸残页）")
                    else:
                        db.add_item(group_id, top_key, f"bp_{uuid.uuid4().hex[:8]}", bp)
                        lines.append(f"👑 首功 {top_p['name']} 额外获得图纸：{bp['name']}")
        # 首通记录（每人）+ 阶段九：副本次数 + 成就判定
        # v105 M18 P1：结算统计「全队未受伤」→ ach_flawless「完美主义者」解锁
        # （此前全仓 check_achievements 无一传 flawless，条件恒 False 永不可解锁）
        _flawless = all(
            st["alive"].get(str(m2), True)
            and not (st["players"].get(str(m2), {}) or {}).get("took_dmg")
            for m2 in st["members"] if str(m2) in cur
        )
        for m in st["members"]:
            if str(m) not in cur:
                continue  # v104 P1：已退队成员不记录首通成就/副本次数
            if st["alive"].get(str(m), True):
                db.set_achievement(group_id, m, f"inst_clear_{st['inst_id']}", 1)
                db.bump_stats(group_id, m, inst_clears=1)
                _extra = {"inst_id": st["inst_id"]}
                if _flawless:
                    _extra["flawless"] = True
                C.check_achievements(group_id, m, None, _extra)
        # v101.27 #390 隐藏奖励：通关后停留搜刮
        # ① 战利品堆（必出，保底搜刮体验）：金币=通关奖金×30% + 专属材料×1
        # ② 隐藏暗格（概率出）：20%（首通 50%）→ 墙上的裂痕 → 精英守卫 → 宝箱
        # v140 波1：宝箱内容分层同步（图纸残页 25% / 装备 40% / 稀有符文 20% / 专属材料 10% /
        # 星灵蝶蛋 5%，见 _instance_secret_chest docstring；v140 波2 鱼鱼拍板装备占比压过图纸）
        # v140 波2：通关后调查点层（cleared 专属，22 本 × 3-5 个）——_instance_map_view /
        #    调查命令 cleared 分支已接入，通关文案给一行入口提示
        st["cleared"] = True
        st["cleared_time"] = int(time.time())
        st["loot_pile"] = True
        # 隐藏暗格概率：首通 50%，复刷 20%（鱼鱼拍板：Boss 好刷→概率低，防通胀）
        _crack_rate = 0.50 if st.get("first_clear") else 0.20
        st["secret_crack"] = (random.random() < _crack_rate)
        st["secret_guard"] = None  # 暗格精英守卫（未触发）
        st["secret_chest"] = None  # 暗格宝箱奖励（守卫击败后生成）
        lines.append("")
        lines.append("🏆 副本已通关！你可以在副本内停留搜刮：")
        lines.append("  · 🎁 【战利品堆】—— 首领的遗物，搜刮一次（『调查 战利品堆』）")
        # v140 波2：通关调查点提示（未翻完时给入口）
        _inv_pts = (C.INVESTIGATION_POINTS or {}).get(st.get("inst_id") or "", [])
        if _inv_pts:
            lines.append(f"  · 🔍 通关后这里多了些可调查的痕迹（『副本地图』查看，每日限 {INVESTIGATE_DAILY_LIMIT} 次）")
        if st["secret_crack"]:
            lines.append("  · 🧱 墙上似乎有【松动的墙砖】……（『调查 墙砖』）")
        lines.append("搜刮完毕用『离开副本』传出～")
        lines.append("")
        lines.append("💡 『副本』可再次挑战，首通成就已记录～")
        st["mode"] = "map"
        st["boss"] = None
        st["enemy"] = None
        st["enemies"] = []
        self._instance_save(group_id, st)
        yield event.plain_result("\n".join(lines))

    async def _instance_defeat(self, event, group_id, qq_id, player, st, logs):
        lines = [x for x in logs if "毒发身亡" not in x]
        lines.append("")
        lines.append("💀 队伍全灭……副本失败！冒险者们被送回了最近的城镇。")
        # v104 P1：只结算当前队伍成员——已退队者不受副本失败牵连（不误杀）
        cur = self._instance_current_members(group_id, st)
        for m in st["members"]:
            if str(m) not in cur:
                continue
            self._unlock_battle(group_id, m)
            db.clear_battle(group_id, m)
            p = self._player(group_id, m)
            if p:
                # O104 修复：副本失败回城点=副本入口最近城镇（原固定回橡木镇 START_MAP——
                # 铁港城开本全灭也被送回 Lv.1 图，playtest O104 阿甘实测）。开本不占地图位置
                # （cur_map 仍是开本前所在图），按该图 BFS 最近城镇，落中心广场 subareas[0]，
                # 与野外战败 combat._handle_defeat(M22 P3) 同规则。
                _town_id = self._nearest_town(p.get("cur_map", ""))
                _town_sas = C.MAP_BY_ID.get(_town_id, {}).get("subareas") or []
                _town_sa = _town_sas[0]["id"] if _town_sas else ""
                _town_sa_name = _town_sas[0]["name"] if _town_sas else "广场"
                _town_name = C.MAP_BY_ID.get(_town_id, {}).get("name", "城镇")
                db.update_player(group_id, m, hp=0, mp=p.get("max_mp", 0),
                                 cur_map=_town_id, cur_subarea=_town_sa,
                                 world_id="mainland")
                lines.append(f"📍 {p['name']} 被送回了【{_town_name}·{_town_sa_name}】（HP 0，先休息恢复吧）")
        # v141 大陆隔离：副本失败 → 销毁大陆实例（进度作废）
        _wid = st.get("world_id") or ""
        if _wid.startswith("inst:"):
            C.destroy_instance_world(_wid)
        yield event.plain_result("\n".join(lines))
