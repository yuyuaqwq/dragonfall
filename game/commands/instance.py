# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - instance（组队副本）

2 人组队轮流回合 Boss 战：
- 队长『副本 <名字>』开本（需已组队），队员自动参战
- 轮流出手：队员A行动 → 队员B行动 → Boss行动 → 下一轮
- 超时自动防御（事件驱动惰性检测，非定时器）：轮到的人 60 秒不动，
  任何人再发指令时自动把 TA 的回合带过去
- 战斗中不能逃跑（Boss 锁定）；副本失败全队回城
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

    # ---------------- v137 『加入战斗』：同队伍成员并入正在进行中的副本战斗 ----------------
    # 设计依据：docs/RESEARCH_join_battle.md §四.2/§五/§九（CTB 播种 = 参考点 + 自身 cost；
    # 战斗结束/PVP/满员/重复/0血/异地拒绝；只改状态不推进行动轴）。
    # 本期范围：仅支持『副本战斗』（battle 存队长名下，st["type"]=="instance"）；
    # 野外同场战斗（方案 B 队长键）与『副本锁拆分为战斗锁+副本锁』留待后续 Phase。

    @filter.regex(r"^(?:\[At:\d+\]\s*)?加入战斗(?:\s*|$)")
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
        # 7. 持久化 + 锁 + 广播
        try:
            db.save_battle(group_id, st["leader"], st)
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
            f"{self._instance_ct_queue(st, group_id)}\n"
            f"👥 当前参战：{'、'.join(str(st.get('players', {}).get(m2, {}).get('name', m2)) for m2 in st.get('members', []))}"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?副本(?!地图)(?:[\s\S]*)$")
    @require_player()
    @no_prof_waiting()

    async def instance_cmd(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
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
                # R3 P3-1：文案与行为对齐——开本不占地图位置，超时只解除战斗锁/
                # 清 battle（v101.27 #390），玩家从未被\"传送\"；沿用『离开副本』口径
                yield event.plain_result("⏳ 通关时间已过 30 分钟，你已自动离开副本。")
                return
            yield event.plain_result(self._instance_status(group_id, qq_id, inst_row))
            return
        arg = self._strip_cmd(event, "副本").strip()
        if not arg:
            # v104 M04 P2：副本超 24h 无行动被回收 → 不再静默消失，先给过期提示
            _hint = self._instance_expired_hint(group_id, qq_id)
            yield event.plain_result((_hint + "\n" if _hint else "") + self._instance_list(player))
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
                    db.save_battle(group_id, qq_id, old_st)
                    yield event.plain_result(
                        f"{inst.get('icon', '🏰')} 【{inst.get('name', '')}】你回到了副本深处！\n"
                        f"━━━━━━━━━━━━\n"
                        f"{self._instance_map_view(old_st, group_id)}"
                    )
                    return
        async for _r in self._instance_start(event, group_id, qq_id, player, arg):
            yield _r

    @filter.regex(r"^(?:\[At:\d+\]\s*)?深入(?:(?:第\s*)?(\d+)\s*层)?(?:[层进]\s*)?$")
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
            _dun_map = C.MAP_BY_ID.get(_inst_map_id(st.get("inst_id") or ""), {})
            _dun = _dun_map.get("dungeon") or {}
            _br = _dun.get("boss_room")
            _rooms = st["rooms"]
            if _br and _br in _rooms:
                # 队长移动到 Boss 房（触发 _instance_dungeon_move 的 Boss 战链路）
                _cur = (self._player(group_id, st.get("leader")) or {}).get("cur_subarea") or ""
                _links = C.subarea_links(_inst_map_id(st.get("inst_id") or ""), _cur)
                if _cur != _br and _br in _links:
                    async for _r in self._instance_dungeon_move(event, group_id, qq_id, player,
                                                                inst_row, _dun_map, _br):
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
        st["e_buffs"] = {}
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
        db.save_battle(group_id, st["leader"], st)
        if st.get("mode") == "map":
            # 新层地图模式：显示层全景
            map_view = self._instance_map_view(st, group_id)
            yield event.plain_result(
                f"🧭 你继续深入……\n"
                f"━━━━━━━━━━━━\n"
                f"{map_view}"
            )
            return
        role = "👑 BOSS" if next_stage.get("boss") else ("⭐ 精英" if next_stage.get("elite") and not s_mons else "🐾")
        # R3 P2-7：非 map 分支空层防御（stage_cleared 仅 map 模式置位，当前不可达；
        # 防未来改动后 st['boss'] 为 None 时裸崩 TypeError）
        _b = st.get("boss") or {}
        yield event.plain_result(
            f"🧭 你继续深入……\n"
            f"━━━━━━━━━━━━\n"
            f"🚪 第 {st['stage_idx'] + 1} 层 · {next_stage['name']}\n"
            f"{role}【{_b.get('name', '未知敌人')}】Lv.{_b.get('lv', '?')} ❤️ {_b.get('hp', 0):,}\n"
            f"━━━━━━━━━━━━\n"
            f"⏳ 轮到 {self._instance_next_player_name(st, group_id)} 行动！『攻击』『技能 <名称>』『防御』"
        )

    # ---------------- 副本地图（v87.2） ----------------
    @filter.regex(r"^(?:\[At:\d+\]\s*)?副本地图\s*$")
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
    @filter.regex(r"^(?:\[At:\d+\]\s*)?调查(?:\s+(\S+))?\s*$")
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
            # 第②层：现有战利品堆/暗格（互不干扰：调查点未命中才回落）
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
        cur_map = C.MAP_BY_ID.get(_inst_map_id(st.get("inst_id") or ""), {})
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
        db.save_battle(group_id, st["leader"], st)
        yield event.plain_result(text)

    # ---------------- 撤退（v87.2） ----------------
    @filter.regex(r"^(?:\[At:\d+\]\s*)?撤退\s*$")
    @require_player()
    @no_prof_waiting()

    async def instance_retreat(self, event: AstrMessageEvent):
        """退出副本：解锁战斗，保留层进度与 POI 状态(29 章 13.6)"""
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
        st["retreated"] = True
        # v137 副本地图化：撤退保留 rooms/resources_pool（下次恢复继续），
        # 同时把全队 cur_map + cur_subarea 复位到入口房间（下次『副本 <名>』恢复路径同步）
        if st.get("rooms"):
            _mid = (st.get("inst_id") or "").removeprefix("inst_")
            _entry_sa = C.map_entry_subarea(_mid)
            if _entry_sa:
                for _m in st["members"]:
                    db.update_player(group_id, _m, cur_map=_mid, cur_subarea=_entry_sa)
        db.save_battle(group_id, st["leader"], st)
        for m in st["members"]:
            self._unlock_battle(group_id, m)
        inst = C.INSTANCES.get(st["inst_id"], {})
        stages = st.get("inst_stages") or []
        sidx = st.get("stage_idx", 0)
        sname = stages[sidx]["name"] if sidx < len(stages) else ""
        yield event.plain_result(
            f"🏳️ 你们决定撤退……副本进度已保留。\n"
            f"📌 下次『副本 {inst.get('name', '')}』将从【第 {sidx + 1} 层 · {sname}】继续！"
        )

    # ---------------- 离开副本（v101.27 #390） ----------------
    @filter.regex(r"^(?:\[At:\d+\]\s*)?离开副本\s*$")
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
        cur_map = C.MAP_BY_ID.get(_inst_map_id(st.get("inst_id") or ""), {})
        cur_sa = player.get("cur_subarea") or ""
        links = C.subarea_links(cur_map.get("id", ""), cur_sa) if cur_sa else []
        # 目标房间解析（序号优先，其次名字/id）
        target_sa = None
        if dest.isdigit():
            idx = int(dest)
            if 1 <= idx <= len(links):
                tid = links[idx - 1]
                target_sa = next((s for s in (cur_map.get("subareas") or []) if s["id"] == tid), None)
        else:
            for s in (cur_map.get("subareas") or []):
                if dest in (s["name"], s["id"]):
                    target_sa = s
                    break
        if target_sa is None:
            names = "、".join(
                f"{i + 1}. {next((s['name'] for s in (cur_map.get('subareas') or []) if s['id'] == lid), lid)}"
                for i, lid in enumerate(links)
            ) or "（无）"
            yield event.plain_result(
                f"🧭 从当前房间可前往：{names}。输入『移动 <房间名/序号>』～"
                f"（『副本地图』查看全景）")
            return
        if target_sa["id"] == cur_sa:
            yield event.plain_result(f"你已经在这里了({cur_map.get('name', '')}·{target_sa['name']})～")
            return
        if target_sa["id"] not in links:
            yield event.plain_result(
                f"🧭 【{target_sa['name']}】与当前房间不相连！副本内只能移动到相邻房间（『副本地图』查看可前往）～")
            return
        # 副本内移动：先解锁战斗锁（副本地图模式持有锁防双线战斗），world.move 前置
        # _in_battle 拦截依赖锁状态——解锁后 move 正常进入副本分支 _instance_dungeon_move。
        for m in st.get("members") or []:
            self._unlock_battle(group_id, m)
        # world.move 到达副本分支后再次上锁（遇怪/到达都会 _lock_battle），
        # 此处直接调 _instance_dungeon_move 等价推进（含遇怪/Boss 房链路与重新上锁）。
        # 注意：_instance_dungeon_move 的 dest 参数是房间名字符串（在连通表内做 `in (name,id)`
        # 匹配），这里传目标房间名（world.move 原分支传玩家输入 dest，语义相同）。
        async for _r in self._instance_dungeon_move(event, group_id, qq_id, player, inst_row, cur_map, target_sa["name"]):
            yield _r
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
        cur_map = C.MAP_BY_ID.get(_inst_map_id(st.get("inst_id") or ""), {})
        cur_sa = None
        for _sa in (cur_map.get("subareas") or []):
            if _sa["id"] == cur_sa_id:
                cur_sa = _sa
                break
        rooms = st.get("rooms")
        if rooms:
            # ---- v137 dungeon 房间池消费 ----
            _dun = cur_map.get("dungeon") or {}
            _agro = float(_dun.get("discovery_agro", 0.85) or 0.85)
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
                db.save_battle(group_id, st["leader"], st)
                yield event.plain_result(f"🍃 你仔细搜索着这片区域……\n{text}")
                return
            # ② 遇怪（discovery_agro + monsters_left 非空 → 消耗 1 只 → 进战斗）
            if _left:
                if random.random() < _agro:
                    _def = _left.pop(0)
                    self._enter_stage_combat(group_id, st, _def, cur_sa or cur_map)
                    db.save_battle(group_id, st["leader"], st)
                    _mon = st.get("boss") or {}
                    _role = "👑 BOSS" if _def[2] == "boss" else ("⭐ 精英" if _def[2] == "elite" else "🐾")
                    yield event.plain_result(
                        f"🍃 你警惕地探索着，突然——{cur_sa.get('name', '') if cur_sa else cur_map.get('name', '')}里的怪物扑了上来！\n"
                        f"━━━━━━━━━━━━\n"
                        f"{_role}【{_mon.get('name', '')}】Lv.{_mon.get('lv', '?')} ❤️ {_mon.get('hp', 0):,}\n"
                        f"━━━━━━━━━━━━\n"
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
            db.save_battle(group_id, st["leader"], st)
            if nxt[2] == "boss":
                role = "👑 BOSS"
            elif nxt[2] == "elite":
                role = "⭐ 精英"
            else:
                role = "🐾"
            # v126 副本剧情化：Boss 战前台词（仅 role=boss 且 inst 有 boss_line 字段才渲染）
            _inst2 = C.INSTANCES.get(st.get("inst_id") or "", {})
            boss_line_note = f"💬 {_inst2['boss_line']}\n" if nxt[2] == "boss" and _inst2.get("boss_line") else ""
            yield event.plain_result(
                f"🍃 你警惕地探索着，突然——{stage.get('name', '')}里的怪物扑了上来！\n"
                f"━━━━━━━━━━━━\n"
                f"{role}【{st['boss']['name']}】Lv.{st['boss']['lv']} ❤️ {st['boss']['hp']:,}\n"
                f"{boss_line_note}"
                f"━━━━━━━━━━━━\n"
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
                    db.save_battle(group_id, st["leader"], st)
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
        # v104 M17 P2（设计取舍确认）：副本战斗不携带宠物——宠物技能/经验加成/饱食度
        # 消耗均不参与副本。副本奖励走 _instance_kill_reward/通关奖励链路，不经过
        # combat._handle_victory 的宠物结算（宠物不参战 ⇒ 饱食度不扣、宠物不分经验），
        # 与 _instance_act 中 Battle.from_state 不传 pet 一致。若未来开放宠物参战，
        # 需同步：①副本怪物平衡（hp_mult/atk_mult/mech 均按无宠物调参）②宠物经验/饱食度结算。
        st["boss"] = C.build_monster(mon_def, {"id": st["inst_id"], "name": st["inst_id"], "area": "instance"})
        if mon_def[2] == "boss":
            inst2 = C.INSTANCES[st["inst_id"]]
            if inst2.get("mech"):
                st["boss"]["mech"] = inst2["mech"]
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
        st["e_buffs"] = {}
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
        # v121 审计修复：新战斗开始玩家 ct 与敌方同规则重置（-spd 播种对称）
        self._instance_reset_player_cts(st)

    # ---------------- v2 多对多阵列 helpers（§2.2 / §8.2） ----------------
    def _instance_reset_player_cts(self, st: dict) -> None:
        """v121 审计修复：新敌人入场时重置存活玩家 ct = -spd（与敌方
        _instance_build_enemy_array 的 -spd 播种对称）——此前玩家 ct 跨场残留
        （多为正数），换怪/换层后新敌人以 -spd 开局直接碾压先手。"""
        self._instance_ensure_player_fields(st)
        for key, snap in (st.get("players") or {}).items():
            if st.get("alive", {}).get(str(key), True):
                snap["ct"] = -float(snap.get("spd", 0) or 0)

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

    def _instance_build_enemy_array(self, st: dict, boss: dict) -> list:
        """v2：由主怪 st["boss"] 构建敌方阵列 st["enemies"]。
        Boss 主单位 = build_monster 产物（含 rank/reach/uid/buffs/stacks/defending/charging）；
        配置 minions 展开为 rank1 的爪牙（属性 ×0.5、名字"XX的{minion名}"、uid 唯一、is_boss/is_elite False）。
        精英/普通怪 → 单怪阵列 [boss]。缺省无 minions → 仅 Boss。
        v121 CTB：每个敌方单位补 ct = -spd（越小越先行动）。"""
        boss = boss or {}
        if not boss:
            return []
        if not boss.get("is_boss"):
            boss.setdefault("ct", -float(boss.get("spd", 0) or 0))
            return [boss]
        enemies = [boss]
        boss.setdefault("ct", -float(boss.get("spd", 0) or 0))
        inst = C.INSTANCES.get(st.get("inst_id") or "", {})
        mcfg = inst.get("minions") or []
        base_name = boss.get("name", "BOSS")
        base_uid = boss.get("uid", "e_0")
        for mi, cfg in enumerate(mcfg):
            cnt = int(cfg.get("count", 1) or 1)
            role = cfg.get("role", "dps")
            mrank = 1  # 契约 §2.2：爪牙 rank1
            mreach = 2 if role in ("caster", "healer") else 1
            mname = cfg.get("name", "爪牙")
            for j in range(cnt):
                sub = self._scale_enemy_copy(
                    boss, 0.5, "{}-m{}_{}".format(base_uid, mi, j),
                    "{}的{}".format(base_name, mname), mrank, mreach)
                sub.setdefault("ct", -float(sub.get("spd", 0) or 0))
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
        st["_last_killed"] = removed  # 记录本回合死亡单位（击杀奖励/任务统计按单位结算）
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
        v87.2：retreated（撤退保留进度）的副本不参与战斗判定（玩家可自由行动）"""
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
        for i, (kid, inst) in enumerate(C.INSTANCES.items(), 1):
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
        boss = st.get("boss") or (st["enemies"][0] if st.get("enemies") else {})
        pct = max(0, int((boss or {}).get("hp", 0) / max(1, (boss or {}).get("max_hp", 1)) * 100))
        stages = st.get("inst_stages") or []
        stage_line = ""
        if stages:
            sidx = st.get("stage_idx", 0)
            sname = stages[sidx]["name"] if sidx < len(stages) else ""
            stage_line = f" 🚪 第 {sidx + 1} 层 · {sname}"
        lines = [
            f"{inst.get('icon', '🏰')} 【{inst.get('name', st['inst_id'])}】 第 {st.get('round', 1)} 轮{stage_line}",
            "━━━━━━━━━━━━",
            f"👹【{(boss or {}).get('name', '怪物')}】❤️ {max(0, (boss or {}).get('hp', 0)):,} / {(boss or {}).get('max_hp', 0):,}({pct}%)",
        ]
        # v2 站位图（§4）：敌方阵列 + 我方存活玩家阵列，蓄力单位带标记
        from ..core import formation as FM
        enemy_view = FM.formation_view(st.get("enemies") or [], side="enemy")
        player_units = [snap for key, snap in (st.get("players") or {}).items()
                        if st.get("alive", {}).get(str(key), True)]
        ally_view = FM.formation_view(player_units, side="ally")
        if enemy_view:
            lines.append("── 敌方 ──")
            lines.extend(f"  {l}" for l in enemy_view)
        if ally_view:
            lines.append("── 我方 ──")
            lines.extend(f"  {l}" for l in ally_view)
        # v104 M04 P2：状态视图按当前队伍过滤——退队者不显示血量行，
        # 且退队者不再是"轮到 TA 行动"（原地等 TA 行动会让全队干等）
        _cur = self._instance_current_members(group_id, st)
        shown = [m for m in st["members"] if str(m) in _cur] or st["members"]
        for m in shown:
            p = self._player(group_id, m)
            pname = p["name"] if p else m
            snap = st["players"].get(str(m), {})
            alive = st["alive"].get(str(m), True)
            mark = "✅" if alive else "💀"
            cls_label = self._class_role_label(snap.get("class_name", ""))
            lines.append(
                f"{mark} {pname}({cls_label})：❤️ {snap.get('hp', 0)}/{snap.get('max_hp', 1)} "
                f"💙 {snap.get('mp', 0)}/{snap.get('max_mp', 1)}"
            )
        turn_idx = st["turn"]
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
            cur_map = C.MAP_BY_ID.get(_inst_map_id(st.get("inst_id") or ""), {})
            sas = cur_map.get("subareas") or []
            cur_sa = next((s for s in sas if s["id"] == cur_sa_id), None)
            lines = []
            if _lp:
                nav = self._map_nav_body(_lp, cur_map, cur_sa_id or "", group_id, group_id, show_here=False, with_header=True)
                blocks = self._map_blocks(_lp, cur_map, cur_sa_id or "", group_id, group_id)
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
                    "e_buffs": {},
                    "p_defending": {str(m): False for m in members},
                    "mech_stacks": {str(m): {} for m in members},
                    "round_acted": [],            # δ副本层：本轮已行动玩家（列表持久化防 set 转 list）
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
                    "e_buffs": {},
                    "p_defending": {str(m): False for m in members},
                    "mech_stacks": {str(m): {} for m in members},
                    "round_acted": [],            # δ副本层：本轮已行动玩家（列表持久化防 set 转 list）
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
            "e_buffs": {},
            "mech_stacks": {str(m): {} for m in members},  # v59 副本叠层（按玩家持久化）
            "round_acted": [],               # δ副本层：本轮已行动玩家（列表持久化防 set 转 list）
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
            inv = db.get_inventory(group_id, qq_id)
            # 找到匹配的钥匙（按物品名匹配）
            key_entry = None
            for it in (inv or []):
                it_name = (it.get("data") or {}).get("name", "")
                if it_name == key_item or it.get("key") == key_item or C.ITEMS.get(it.get("key"), {}).get("name") == key_item:
                    key_entry = it
                    break
            has_key = key_entry is not None and (key_entry.get("count") or 0) >= 1
            cleared_before = any(a.get("ach_key") == f"inst_clear_{kid}" and a.get("progress", 0) >= 1
                                 for a in (db.get_achievements(group_id, qq_id) or []))
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
                # v121 CTB：玩家快照 ct = -spd（快者更负 → 先行动）
                "ct": -E.player_final_stats(p["class_name"], p["level"], p.get("equipment", {}),
                                            p.get("class_tier", 0), p.get("attributes"),
                                            p.get("evolve_path", 0), None, p.get("race")).get("spd", 0),
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
        # v2：全员站位归一（老存档恢复或字段缺省时补齐）
        self._instance_ensure_player_fields(st)
        # v57：副本行动序按速度降序（快者先出手）。真人轮流节奏不变，只是顺序由速度决定
        st["members"] = sorted(st["members"], key=lambda m: st["players"][str(m)].get("spd", 0), reverse=True)
        st["turn"] = 0
        # 锁全队
        for m in members:
            self._lock_battle(group_id, m)
        # v137 副本地图化：开本落点 = 副本入口子区域（全队 cur_map + cur_subarea 同步）
        _map_id = kid[5:] if str(kid).startswith("inst_") else kid
        _entry_sa = C.map_entry_subarea(_map_id)
        if st.get("mode") == "map" and st.get("rooms") and _entry_sa:
            for m in members:
                db.update_player(group_id, m, cur_map=_map_id, cur_subarea=_entry_sa)
        db.save_battle(group_id, qq_id, st)
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
            f"👹【{boss['name']}】Lv.{boss['lv']} ❤️ {boss['max_hp']:,}\n"
            f"📜 {inst['desc']}\n"
            f"━━━━━━━━━━━━\n"
            f"{size_tip}"
            f"{self._instance_ct_queue(st, group_id)}\n"
            f"⏳ 轮到 {first_actor_name} 行动！『攻击』『技能 <名称>』『防御』\n"
            f"💡 按 CTB 行动轴轮流出手，超时 60 秒自动防御；清光当前层怪物可『深入』下一层！"
            f"{intro_note}"
        )

    def _sync_players_db(self, group_id, st):
        """v95r76 #383：副本快照血量/魔力同步回 DB。

        副本战斗中玩家 hp/mp 只存在 st["players"] 快照，DB 保持开本时的值——
        战斗外逻辑（治疗满血判定 tpl_heal、『角色』面板）读 DB 会拿到过时数据：
        层肃清后『使用 治疗药水』误报"生命是满的"拒用、进 Boss 战残血开局
        （格温实测：DB 1003/1003 满血拒药，Boss 战第一回合实际 197/1003）。
        每个写回点（行动保存/切怪/层肃清）前调用，与普通战斗每回合 update_player 对齐。"""
        for m in st["members"]:
            snap = st["players"].get(str(m))
            if not snap:
                continue
            db.update_player(group_id, m,
                             hp=snap.get("hp", 0), mp=snap.get("mp", 0),
                             max_hp=snap.get("max_hp", 100), max_mp=snap.get("max_mp", 100))

    # ---------------- 行动核心 ----------------
    async def _instance_act(self, event, group_id, qq_id, player, st, action, skill_name=None, target=None):
        """副本回合行动(由攻击/技能/防御指令路由进来)

        v127.3：target 参数（『技能 <槽位> <编号>』指定目标）由 combat 层解析传入。
        """
        # v101.24 #301：某层肃清后进入地图模式(boss=None, stage_cleared)时，攻击/技能/防御/使用道具
        # 都会走到 st["boss"]["hp"] 对 None 下标 → 'NoneType' object is not subscriptable 裸错。
        # 层内无敌人时直接引导『深入』推进，不进入战斗回合逻辑。
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

        # 1. v121 CTB 行动轴推进：敌我按 ct 最小者行动。
        #    不再用"全员行动过 → Boss 行动"——敌方行动由 ct 判定，
        #    无需等全员行动过。此处循环：先结算一次敌方段（若有敌方 ct 领先），随后处理
        #    超时自动防御（含该玩家 defend 行动的 ct 结算），直到本应行动者为请求玩家或等待未超时者。
        while True:
            # 无可行动存活玩家（全灭/全退队）→ 直接失败结算
            if not self._instance_living_player_cts(st, group_id):
                st["over"] = True
                async for _r in self._instance_defeat(event, group_id, qq_id, player, st, logs):
                    yield _r
                return
            nxt = self._instance_next_actor(st, group_id)
            if nxt[0] == "e":
                elogs, ok = self._instance_enemy_ct_acts(st, group_id)
                logs += elogs
                if not ok:
                    # 敌方段打满上限（8 动）仍有敌方 ct 领先 → 本轮敌方行动暂停，回退下一玩家，
                    # 防极端配速与外部循环死锁；但敌方段可能已把玩家全灭（ok=False 同源）——
                    # 必须在此重新检查全灭并走失败结算，否则静默 return（无 yield）卡死战斗
                    if not self._instance_living_player_cts(st, group_id):
                        st["over"] = True
                        async for _r in self._instance_defeat(event, group_id, qq_id, player, st, logs):
                            yield _r
                        return
                    cts = self._instance_living_player_cts(st, group_id)
                    nxt = ("p", min(cts, key=lambda kk: cts[kk]) if cts else None)
                else:
                    continue
            if nxt[0] != "p" or not nxt[1]:
                # 无玩家可行动（仅剩敌方且已处理）→ 等待外部触发重算
                return
            cur_key = nxt[1]
            cur_idx = members.index(cur_key)
            if cur_key == str(qq_id):
                # 本玩家应行动
                st["turn"] = cur_idx
                st["turn_time"] = now
                break
            # 非请求玩家：超时 → 自动防御（含 ct 结算）后重算；未超时 → 等待
            # v121 审计修复：auto-defend 后不刷新 turn_time——保持轮转计时起点不变，
            # 同一条指令内连续结算所有已超时者（原实现逐个 60s 消化，全队 AFK 需反复触发）
            if now - st.get("turn_time", now) > INSTANCE_TIMEOUT:
                logs += self._instance_auto_defend_player(st, group_id, cur_key)
                continue
            st["turn"] = cur_idx
            cur_name = (self._player(group_id, cur_key) or {}).get("name", cur_key)
            yield event.plain_result("\n".join(logs + [f"⏳ 现在是 {cur_name} 的回合，等待 TA 行动～"]))
            return

        # 2. 确认轮到当前玩家
        cur_idx = st["turn"]
        cur_key = str(members[cur_idx])
        if str(qq_id) != cur_key:
            cur_name = (self._player(group_id, cur_key) or {}).get("name", cur_key)
            yield event.plain_result("\n".join(logs + [f"⏳ 现在是 {cur_name} 的回合，等待 TA 行动～"]))
            return

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
            db.save_battle(group_id, st["leader"], st)
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
            "e_buffs": st["e_buffs"],
            "p_defending": st["p_defending"].get(cur_key, False),
            "e_defending": False,
            "title_bonus": snap.get("title_bonus") or {},
            # v59：叠层/护盾随战斗持久化（副本按玩家存；v101.28d 盾 buff 化）
            "mech_stacks": st["mech_stacks"].get(cur_key, {}),
            "p_shields": snap.get("p_shields", {}) or {},
            # v101.28m #438 复测修复：副本战斗状态必须完整传递，否则召唤援军
            # （e_minions）回合结束蒸发、核心资源（resources）不持久化导致耗资源
            # 技能永不可用、round 恒 0 导致按回合 Boss 机制（召唤/回血）失序
            "round": st.get("round", 0),
            "e_minions": st.get("e_minions", []),
            "resources": st.get("resources", {}).get(cur_key, {}),
            "cooldown": st.get("cooldown", {}).get(cur_key, {}),
            "combo_seq": st.get("combo_seq", {}).get(cur_key, []),
            # v2 副本玩家蓄力持久化：跨回合恢复（蓄力技副本中跨回合生效）
            "charging": st.get("charging", {}).get(cur_key),
            # v121 CTB：透传玩家快照 ct（行动后 Battle 内部 _after_actor_ct("p") 推进并随写回转存）
            "p_ct": snap.get("ct", 0.0),
            "player_hit": st.get("player_hit", {}).get(cur_key, False),
            # δ副本层：dot 结算闸门透传（A 在 Battle.from_state 读 st["dot_pending"]；
            # 全队共享敌减益，每轮只结算一次，行动后自动置 False 并写回）
            "dot_pending": st.get("dot_pending", True),
            # v122 治疗指定队友：存活成员快照引用（Battle 内改 hp 直接反映到 st["players"]）
            "allies": [st["players"][str(m)] for m in st.get("members", [])
                       if st.get("alive", {}).get(str(m), True)],
        })
        # v121 CTB：副本 Battle 由 from_state 构造未设 self.player，而 _after_actor_ct("p")
        # 按 self.player 的 _player_stats(spd) 结算玩家 ct——必须指向行动者快照，否则恒取 cost=100
        b.player = snap
        act_logs, ended = b.player_turn(action, skill_name, snap, enemy_act=False, target=target)
        st["players"][cur_key] = snap
        st["p_buffs"][cur_key] = b.p_buffs
        st.setdefault("p_hot", {})[cur_key] = b.p_hot
        st.setdefault("p_food_effects", {})[cur_key] = b.p_food_effects
        st["e_buffs"] = b.e_buffs
        st["mech_stacks"][cur_key] = b.mech_stacks
        # δ副本层：本轮已结算——本行动者是本轮第一个（或唯一）动作，Boss 敌减益只在此结算
        # 一次；后续同一轮其他行动者 from_state 读到 dot_pending=False 不再 tick（Battle._dot_pending）
        st["dot_pending"] = False
        # δ副本层轮次推进：记录本玩家本轮已行动，全部存活成员都行动过 → 新一轮开始。
        # 顺序保证：先置 False（行动者已结算）→ 再判轮满 → 轮满则清集合并置 True（下一轮
        # 下一行动者 from_state 读取时恢复结算）。round_acted 用列表存放（battle_state 存 JSON，
        # set 会被转成 list，统一用 list 免得类型错乱）；老存档无该键用 setdefault 兜底。
        acted = st.setdefault("round_acted", [])
        if not isinstance(acted, list):
            acted = list(acted)          # 兼容老存档 set → 列表
            st["round_acted"] = acted
        if cur_key not in acted:
            acted.append(str(cur_key))
        _alive_keys = [str(m) for m in members if st.get("alive", {}).get(str(m), True)]
        if _alive_keys and set(acted) >= set(_alive_keys):
            st["round_acted"] = []
            st["dot_pending"] = True
        # v101.28m #438 复测修复：战斗状态写回（援军/回合数/资源/冷却/连招持久化）
        st["round"] = b.round
        st["e_minions"] = b.e_minions
        st.setdefault("resources", {})[cur_key] = b.resources
        st.setdefault("cooldown", {})[cur_key] = b.cooldown
        st.setdefault("combo_seq", {})[cur_key] = b.combo_seq
        # v121 CTB：玩家 ct 写回快照（b.p_ct 已含该玩家行动后的 _after_actor_ct("p") 推进）
        snap["ct"] = b.p_ct
        # v121 审计修复：多玩家时间流逝对称——玩家行动后，其余存活玩家同步 -cost
        # （敌方 ct 已由 Battle 内部 _after_actor_ct("p") 推进；队友 ct 不在 Battle 内，
        # 必须在此广播，否则敌方相对未行动玩家行动偏快——与 _instance_apply_enemy_act_ct 对称）
        try:
            _cur2 = self._instance_current_members(group_id, st)
            _p_cost = b._ct_cost(b._player_stats(snap).get("spd", 0) if snap else 0)
            for _k2, _s2 in (st.get("players") or {}).items():
                if str(_k2) != cur_key and str(_k2) in _cur2 \
                        and st.get("alive", {}).get(str(_k2), True):
                    _s2["ct"] = float(_s2.get("ct", 0) or 0) - _p_cost
        except Exception:
            pass
        st.setdefault("player_hit", {})[cur_key] = b._player_hit
        # v101.25 #323：防御状态必须写回——否则 Boss 反击时读 st["p_defending"] 永远是 False，
        # 副本防御减半完全不生效（playtest round67 影刃实测 93→75 仅约 -19%）
        st["p_defending"][cur_key] = bool(getattr(b, "p_defending", False))
        # v2 副本玩家蓄力持久化：写回（含 None 表示蓄力已结束/未蓄力）
        st.setdefault("charging", {})[cur_key] = b.charging
        snap["p_shields"] = b.p_shields
        # v2：敌方阵列写回（逐单位 hp/buffs/stacks/defending/charging）→ 压缩死亡单位
        st["enemies"] = b.enemies
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
                # v51 嘲讽：仇恨拉满 + Boss 强制打嘲讽者 2 回合
                top = max(threat.values()) if threat else 0
                threat[cur_key] = max(threat.get(cur_key, 0), int(top * 2) + 100)
                st["taunt_target"] = cur_key
                st["taunt_turns"] = 2
                logs.append(f"📢 {snap.get('name', cur_key)} 大声挑衅，Boss 的仇恨被牢牢锁定！")
            else:
                logs += self._apply_team_effect(st, cur_key, te)

        # 4. 当前敌人死亡 → 分层判断（v86.2：清小怪→推进→Boss）
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
                for m in st["members"]:
                    self._unlock_battle(group_id, m)
                self._sync_players_db(group_id, st)
                db.save_battle(group_id, st["leader"], st)
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
                if _rstate.get("boss_alive"):
                    # Boss 房 Boss 被击败 → 标记 boss_alive=False + 通关（下段 _instance_victory）
                    _rstate["boss_alive"] = False
                    _rstate["_boss_room"] = True
                st["stage_cleared"] = True
                st["over"] = False
                st["mode"] = "map"
                st["boss"] = None
                st["enemy"] = None
                st["enemies"] = []
                for m in st["members"]:
                    self._unlock_battle(group_id, m)
                self._sync_players_db(group_id, st)
                db.save_battle(group_id, st["leader"], st)
                if _rstate.get("_boss_room"):
                    # Boss 房击败 → 走通关结算
                    st = db.get_battle(group_id, st["leader"])["state"]
                    async for _r in self._instance_victory(event, group_id, qq_id, player, st, logs + [f"👑 副本 Boss 已被击败！"]):
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
                st["e_buffs"] = {}
                # δ副本层：切怪/换 Boss 清层——新怪无减益、新回合重新允许结算、
                # 玩家资源（叠层/护盾）不跨怪残留、轮次行动记录重置
                st["dot_pending"] = True
                st["boss"].pop("debuffs", None)                    # 新怪无减益
                st["boss"].pop("adapt", None)                      # δv1.2 §11.1：新怪无适应状态（与 debuffs 一起清）
                st["mech_stacks"] = {str(m): {} for m in st["members"]}   # 玩家资源不跨怪
                st["round_acted"] = []                              # 新一轮行动记录重置
                st["round"] = 1
                for i in st["members"]:
                    st["p_buffs"][i] = {}
                    st["p_defending"][i] = False
                st["turn"] = 0
                st["turn_time"] = now
                self._sync_players_db(group_id, st)  # v95r76 #383：切怪前同步快照血量
                db.save_battle(group_id, st["leader"], st)
                yield event.plain_result(
                    "\n".join(logs) +
                    (("\n" + "\n".join(kill_lines)) if kill_lines else "") +
                    f"\n━━━━━━━━━━━━\n"
                    f"⚔️ 又一只怪物挡在面前！\n"
                    f"👹【{st['boss']['name']}】Lv.{st['boss']['lv']} ❤️ {st['boss']['hp']:,}\n"
                    f"━━━━━━━━━━━━\n"
                    f"{self._instance_ct_queue(st, group_id)}\n"
                    f"⏳ 轮到 {self._instance_next_player_name(st, group_id)} 行动！『攻击』"
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
                    for m in st["members"]:
                        self._unlock_battle(group_id, m)
                    self._sync_players_db(group_id, st)  # v95r76 #383：层肃清后战斗外逻辑读 DB 须与快照一致
                    db.save_battle(group_id, st["leader"], st)
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
            async for _r in self._instance_victory(event, group_id, qq_id, player, st, logs):
                yield _r
            return

        # 5. v121 CTB：玩家行动完 → 结算一次敌方段（按 ct 判定，无需等全员行动过），随后重算下一行动者
        elogs, _ok = self._instance_enemy_ct_acts(st, group_id)
        logs += elogs
        # 敌方段可能打死最后一名存活玩家（含同归于尽）→ 全灭失败
        if not self._instance_living_player_cts(st, group_id):
            st["over"] = True
            if not self._instance_enemies_alive(st):
                logs.append("⚔️ 同归于尽！你与敌人同时倒下了……")
            async for _r in self._instance_defeat(event, group_id, qq_id, player, st, logs):
                yield _r
            return
        # 重算下一行动者 = 存活玩家与存活敌方中 ct 最小者
        nxt = self._instance_next_actor(st, group_id)
        if nxt[0] == "e":
            # 敌方段打满上限（8 动）仍有敌方领先 → 回退到 ct 最小的存活玩家
            cts = self._instance_living_player_cts(st, group_id)
            nxt = ("p", min(cts, key=lambda kk: cts[kk]) if cts else None)
        if nxt[0] == "p" and nxt[1] in members:
            st["turn"] = members.index(nxt[1])
        else:
            st["turn"] = 0
        st["turn_time"] = now

        # 6. 保存状态（存到队长名下）并展示
        self._sync_players_db(group_id, st)  # v95r76 #383：每回合行动后同步快照血量（对齐普通战斗）
        db.save_battle(group_id, st["leader"], st)
        nxt_key = str(members[st["turn"]])
        nxt_p = self._player(group_id, nxt_key)
        boss = st["boss"] or (st["enemies"][0] if st.get("enemies") else {})
        pct = max(0, int(boss.get("hp", 0) / max(1, boss.get("max_hp", 1)) * 100))
        yield event.plain_result(
            "\n".join(logs) +
            f"\n━━━━━━━━━━━━\n"
            f"{self._instance_ct_queue(st, group_id)}\n"
            f"👹【{boss.get('name', '怪物')}】❤️ {max(0, boss.get('hp', 0)):,} / {boss.get('max_hp', 0):,}({pct}%)\n"
            f"⏳ 轮到 {nxt_p['name'] if nxt_p else nxt_key} 行动！"
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
        # 全队 buff（写入各自 p_buffs，Boss 回合按仇恨打时生效）
        buff_effects = {
            "def_all": "def_up", "reduce_all": "def_up", "atk_all": "atk_up",
            "matk_all": "matk_up_strong", "crit_all": "crit_up", "spd_all": "spd_up",
        }
        if kind in buff_effects:
            be = buff_effects[kind]
            for k in alive:
                if k == source_key and eff:
                    continue  # 施放者已有自身 buff
                pb = st["p_buffs"].setdefault(k, {})
                pb[be] = max(pb.get(be, 0), turns)
            logs.append("🛡️ 全队获得增益效果！")
            return logs
        # 全队护盾（v101.28d 盾 buff 化：同源叠加 + 刷新 3 回合）
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
                cur["last_round"] = st.get("round", 0) or 0  # 记录叠层回合
                deb["poison"] = cur
                # 适应机制：团队淬毒为持续施加，+0.04（cap 0.20），回落由结算侧按回合判定
                adapt = boss.setdefault("adapt", {})
                adapt["poison"] = min(0.20, float(adapt.get("poison", 0.0) or 0.0) + 0.04)
                logs.append("☠️ 全队武器淬毒！(毒层共享，每回合结算一次)")
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

    def _instance_apply_enemy_act_ct(self, st: dict, group_id: int, unit: dict) -> None:
        """v121 CTB：敌方单位行动后结算 ct（与 battle._after_actor_ct("e") 同语义）：
        行动者 ct += cost；其余存活敌方 + 存活玩家 ct -= cost（时间流逝）。
        v121 审计修复：cost 用 buffed spd（_enemy_stats 应用 spd_down 等，与 battle 一致）；
        玩家遍历按存活+在场（退队者不参与）过滤。"""
        try:
            _btmp = BT.Battle("instance", unit, enemies=[unit])
            _espd = _btmp._enemy_stats().get("spd", 0)
        except Exception:
            _espd = unit.get("spd", 0)
        cost = BT.Battle()._ct_cost(_espd)
        unit.setdefault("ct", -float(unit.get("spd", 0) or 0))
        unit["ct"] = float(unit.get("ct", 0) or 0) + cost
        self._sync_enemy_unit(st, unit)
        uid = str(unit.get("uid"))
        for u in st.get("enemies") or []:
            if str(u.get("uid")) == uid or u.get("hp", 0) <= 0:
                continue
            u.setdefault("ct", -float(u.get("spd", 0) or 0))
            u["ct"] = float(u.get("ct", 0) or 0) - cost
        self._instance_ensure_player_fields(st)
        cur = self._instance_current_members(group_id, st)
        for key, snap in (st.get("players") or {}).items():
            if str(key) in cur and st.get("alive", {}).get(str(key), True):
                snap["ct"] = float(snap.get("ct", 0) or 0) - cost

    def _instance_enemy_ct_acts(self, st: dict, group_id: int) -> tuple:
        """v121 CTB 副本敌方行动段（取代 v57 _instance_boss_turn 的多动逻辑）：
        while 敌方存活单位中最小 ct < 玩家侧最小 ct → 该单位 _instance_enemy_one_act →
        结算其 ct（_instance_apply_enemy_act_ct）→ 循环。
        已死亡的敌方单位即时移出候选（alive 判定）；玩家全灭则提前终止。
        硬上限 8 动防极端配速死循环。
        返回 (logs, ok)：ok=True 敌方段正常消解（敌全灭或玩家更先）；ok=False 打满上限（仍有敌方领先）。"""
        logs = []
        self._instance_ensure_player_fields(st)
        _guard = 0
        while _guard < 8:
            me = self._instance_min_enemy_ct(st)
            if me is None:
                break
            mp = self._instance_min_player_ct(st, group_id)
            if mp is not None and me >= mp:
                break
            unit = min(self._instance_enemy_units(st),
                       key=lambda u: float(u.get("ct", 0) or 0))
            logs += self._instance_enemy_one_act(st, group_id, unit)
            self._instance_apply_enemy_act_ct(st, group_id, unit)
            if not self._instance_living_player_cts(st, group_id):
                # 玩家全灭（含同归于尽）→ 敌方段提前终止
                break
            _guard += 1
        self._instance_enemies_compact(st)
        me = self._instance_min_enemy_ct(st)
        mp = self._instance_min_player_ct(st, group_id)
        ok = not (me is not None and (mp is None or me < mp))
        return logs, ok

    def _instance_auto_defend_player(self, st: dict, group_id: int, key: str) -> list:
        """CTB 超时自动防御：走现有自动防御路径（置 p_defending 防御），并结算一次 defend
        行动的 ct（自身 +cost、其余存活玩家与敌方 -cost 时间流逝）。
        v121 审计修复：cost 用快照速度的 buffed 口径（_player_stats 与正常行动一致，
        此前 raw spd 使超时惩罚比正常行动重 ~2.3×）；队友 ct 同步 -cost（时间流逝对称）。"""
        snap = st["players"][key]
        logs = [f"⏰ {snap.get('name', key)} 迟迟没有行动，自动进入防御姿态！"]
        st["p_defending"][key] = True
        try:
            cost = BT.Battle()._ct_cost(BT.Battle()._player_stats(snap).get("spd", 0) if snap else 0)
        except Exception:
            cost = BT.Battle()._ct_cost(snap.get("spd", 0))
        snap["ct"] = float(snap.get("ct", 0) or 0) + cost
        cur = self._instance_current_members(group_id, st)
        for _k, _s2 in (st.get("players") or {}).items():
            if str(_k) != key and str(_k) in cur and st.get("alive", {}).get(str(_k), True):
                _s2["ct"] = float(_s2.get("ct", 0) or 0) - cost
        for u in st.get("enemies") or []:
            if u.get("hp", 0) > 0:
                u.setdefault("ct", -float(u.get("spd", 0) or 0))
                u["ct"] = float(u.get("ct", 0) or 0) - cost
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
        return "⚡ 行动顺序：" + " → ".join(p[1] for p in entries[:limit])

    def _instance_next_player_name(self, st: dict, group_id: int, fallback_key=None) -> str:
        """v121 CTB：下一位玩家行动者名字（按存活玩家 ct 最小者；无则回退 fallback_key 或队伍第一人）。"""
        nxt = self._instance_next_actor(st, group_id)
        key = None
        if nxt[0] == "p" and nxt[1]:
            key = str(nxt[1])
        if key is None:
            key = str(fallback_key) if fallback_key else str(st.get("members", [None])[0])
        return (st.get("players", {}).get(key, {}) or {}).get("name", key)

    def _instance_enemy_one_act(self, st: dict, group_id: int, unit: dict) -> list:
        """v2：敌方阵列单个单位行动一次（目标 = 射程内前排 + 仇恨/嘲讽）。
        防御/格挡/闪避/减伤对目标玩家逐次结算（沿用旧 _instance_boss_one_turn 骨架）。"""
        from ..core import formation as FM
        logs = []
        members = st["members"]
        cur = self._instance_current_members(group_id, st)
        alive = [m for m in members if str(m) in cur and st["alive"].get(str(m), True)]
        if not alive or unit.get("hp", 0) <= 0:
            return logs
        ename = unit.get("name", "怪物")
        # 敌方单位蓄力由引擎处理：_enemy_turn(player, unit) 内部 left-1 / 归零释放（§6）
        # 我方存活玩家阵列（含站位字段）
        self._instance_ensure_player_fields(st)
        player_units = [snap for key, snap in (st["players"] or {}).items()
                        if st.get("alive", {}).get(str(key), True)]
        threat_by_uid = {}
        for snap in player_units:
            _q = str(snap.get("qq_id") or snap.get("uid", ""))
            threat_by_uid[str(snap.get("uid", ""))] = st.get("threat", {}).get(_q, 0)
        # 嘲讽优先：嘲讽目标存活且在射程内 → 强制选它（否则正常仇恨/射程选择）
        taunt_key = str(st.get("taunt_target", ""))
        target = None
        if taunt_key and st.get("taunt_turns", 0) > 0 and st["alive"].get(taunt_key, False) \
                and taunt_key in cur:
            for snap in player_units:
                if str(snap.get("qq_id")) == taunt_key \
                        and int(snap.get("rank", 1) or 1) <= int(unit.get("reach", 1) or 1):
                    target = snap
                    break
            if target is not None:
                st["taunt_turns"] = max(0, int(st.get("taunt_turns", 0)) - 1)
                logs.append(f"📢 嘲讽生效！{ename} 怒视着 {target.get('name', taunt_key)}！")
                if st["taunt_turns"] <= 0:
                    st.pop("taunt_target", None)
            else:
                # 嘲讽目标已死/不在射程 → 视为无效，走正常选择
                if taunt_key:
                    st.pop("taunt_target", None)
        if target is None:
            target = FM.select_target(unit, player_units, threat=threat_by_uid)
        if target is None:
            return logs
        tkey = str(target.get("qq_id") or target.get("uid", ""))
        snap = st["players"].get(tkey) or target
        tname = snap.get("name", tkey)
        # 构造单怪 Battle：enemies=[该单位]（自身含 buffs/stacks/defending/charging）
        b = BT.Battle.from_state({
            "type": "instance",
            "enemy": unit,
            "enemies": [unit],
            "p_buffs": st["p_buffs"].get(tkey, {}),
            "e_buffs": unit.get("buffs") or {},
            "round": st.get("round", 0),
            "e_minions": st.get("e_minions", []),
            "resources": st.get("resources", {}).get(tkey, {}),
            "cooldown": st.get("cooldown", {}).get(tkey, {}),
            "combo_seq": st.get("combo_seq", {}).get(tkey, []),
            "p_ct": st.get("players", {}).get(tkey, {}).get("ct", 0.0),
            "player_hit": st.get("player_hit", {}).get(tkey, False),
        })
        mlogs, dmg = b._enemy_turn(snap, unit)
        # O116：受击伤害文案暂存 pending，本层不走 _damage_player 需手动取出拼进日志
        try:
            _pend = b._drain_pending_dmg()
            if _pend:
                mlogs = mlogs + _pend
        except Exception:
            pass
        # 敌方单位状态写回 st["enemies"]（按 uid 定位原单位；unit 本身即 st 对象，兜底同步）
        self._sync_enemy_unit(st, unit)
        st["e_buffs"] = unit.get("buffs") or {}
        st["round"] = b.round
        # 引擎可能召唤援军入 b.enemies（多怪整体 Battle 才生效；单怪 Battle 不产生）
        if b.enemies and any(str(u2.get("uid")) != str(unit.get("uid")) for u2 in b.enemies):
            exist = {str(u2.get("uid")) for u2 in st.get("enemies") or []}
            for u2 in b.enemies:
                if str(u2.get("uid")) != str(unit.get("uid")) and str(u2.get("uid")) not in exist:
                    st.setdefault("enemies", []).append(u2)
        # 敌方援军镜像同步（旧兼容字段 e_minions 并入 enemies 后保留 is_minion 引用）
        st["e_minions"] = [u for u in st.get("enemies") or [] if u.get("is_minion")]
        st.setdefault("resources", {})[tkey] = b.resources
        st.setdefault("cooldown", {})[tkey] = b.cooldown
        st.setdefault("combo_seq", {})[tkey] = b.combo_seq
        # v121 CTB：敌方行动不改变玩家 ct（时间流逝由 _instance_apply_enemy_act_ct 另行结算），
        # 此处仅保持既有值（_enemy_turn 不触碰 p_ct）
        st.get("players", {}).get(tkey, {})["ct"] = b.p_ct
        st.setdefault("player_hit", {})[tkey] = b._player_hit
        if st["p_defending"].get(tkey):
            dmg = max(1, int(dmg * 0.5))
            # v101.25 #345：防御减伤后日志同步修正（伤害数字与实际扣血一致）
            import re as _re
            mlogs = [_re.sub(r"造成 (\d+) 点伤害",
                             lambda m: f"造成 {max(1, int(int(m.group(1)) * 0.5))} 点伤害(格挡)",
                             x) for x in mlogs]
            logs.append(f"🛡️ {tname} 举盾格挡！")
        logs += mlogs
        if dmg > 0:
            snap["hp"] = max(0, snap["hp"] - dmg)
            snap["took_dmg"] = True  # v105 M18 P1：无伤通关(ach_flawless)受损标记
            logs.append(f"❤️ {tname} 剩余 {snap['hp']}/{snap['max_hp']}")
        if snap["hp"] <= 0:
            st["alive"][tkey] = False
            st.setdefault("threat", {})[tkey] = 0
            # O105：Boss 行动后死亡同样明确提示"你已倒下，等待队友…"
            logs.append(f"💀 {tname} 倒下了！你已倒下，等待队友…")
        # v121 审计修复：防御状态不在此重置——防御应覆盖"防御后到该玩家下次行动前"
        # 的全部敌方行动（与单机 _enemy_phase defend=True 每次行动减半一致）；
        # 过期点 = 该玩家下次行动开始时（_instance_act 玩家行动段重置）
        return logs

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
        v2 多对多：按当回合死亡单位列表（st["_last_killed"]，缺省回退主怪）逐单位结算——
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
        if poi is None:
            return None
        # 每日上限校验（玩家行日期+次数；跨日归零）
        today = time.strftime("%Y-%m-%d")
        if player.get("investigate_date") != today:
            player["investigate_date"] = today
            player["investigate_count"] = 0
        used = int(player.get("investigate_count", 0) or 0)
        if used >= INVESTIGATE_DAILY_LIMIT:
            return "⏳ 今日副本调查已达上限（3 次）！明天再来吧～（『调查 战利品堆』等搜刮不受影响）"
        # 已调查过的点（本副本本局内）→ 不重复
        done = st.setdefault("investigated", set())
        if not isinstance(done, set):
            try:
                done = set(done)
                st["investigated"] = done
            except Exception:
                done = set()
        if poi["id"] in done:
            return f"{poi.get('name', '调查点')}已经被你翻遍了。"
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
        db.save_battle(group_id, st["leader"], st)
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
        远低于普通刷怪收益，仅作通关仪式感，不构成金币水源。"""
        inst = C.INSTANCES[st["inst_id"]]
        gold = max(10, int(inst.get("gold", 100) * 0.30))
        db.update_player(group_id, qq_id, gold=player["gold"] + gold)
        lines = [f"🎁 你搜刮了战利品堆：金币 +{gold}"]
        mats = inst.get("materials", [])
        if mats:
            mat = random.choice(mats)
            mat_id = C.resolve("materials", mat) if mat else None
            if mat_id and mat_id in C.MATERIALS:
                mname = C.display("materials", mat_id)
                db.add_item(group_id, qq_id, mat_id, {
                    "name": mname, "type": C.MATERIALS[mat_id].get("type", "材料"), "stackable": True,
                    "price": C.MATERIALS[mat_id]["price"],
                })
                lines.append(f"🎒 拾取：{mname} ×1")
        st["loot_pile"] = False
        db.save_battle(group_id, st["leader"], st)
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
            db.save_battle(group_id, st["leader"], st)
            return "🧱 墙砖松动了，但后面只有一堵死墙……（暗格消失了）"
        st["secret_crack"] = False
        st["secret_guard"] = guard  # 标记守卫战（击杀走宝箱分支不通关）
        st["secret_guard_pending"] = True
        self._enter_stage_combat(group_id, st, guard, stage)
        # 守卫精英化：补 is_elite 标记（掉落/播报走精英逻辑）
        st["boss"]["is_elite"] = True
        db.save_battle(group_id, st["leader"], st)
        gname = st["boss"]["name"]
        return (
            "🧱 你扣住松动的墙砖用力一拉——暗门轰然打开！\n"
            "一个魁梧的身影挡在密室前……\n"
            "━━━━━━━━━━━━\n"
            f"⭐ 精英守卫【{gname}】Lv.{st['boss']['lv']} ❤️ {st['boss']['hp']:,}\n"
            "━━━━━━━━━━━━\n"
            f"⏳ 轮到 {self._instance_next_player_name(st, group_id)} 行动！『攻击』『技能 <名称>』『防御』"
        )

    def _instance_secret_chest(self, group_id, qq_id, player, st) -> str:
        """暗格宝箱：图纸残页 50% / 稀有符文 30% / 专属材料 15% / 星灵蝶蛋 5%（稀缺品低概率，防通胀）"""
        roll = random.random()
        inst = C.INSTANCES[st["inst_id"]]
        # v104 M17 P2-4：实装星灵蝶蛋渠道（pets.py source『传说级垂钓稀有产出/神秘宝箱』后半句）
        if roll >= 0.95:
            egg = C.make_pet_egg("pet_starbutterfly")
            db.add_item(group_id, qq_id, "petegg_pet_starbutterfly", egg)
            text = f"🦋 宝箱深处泛着星光——是【{egg['name']}】！『使用 宠物蛋』孵化！"
        elif roll < 0.50:
            pages = random.randint(2, 4)
            db.add_item(group_id, qq_id, "mat_tu_zhi_can_ye",
                        {"name": "图纸残页", "type": "材料", "stackable": True, "price": 10},
                        count=pages)
            text = f"📜 宝箱里是泛黄的纸张——图纸残页 ×{pages}！"
        elif roll < 0.80:
            # 稀有符文池（blue 品质符文，v101.25i6 品质统一后 quality=blue）
            blue_runes = [k for k, r in C.RUNES.items() if (r.get("quality") or "") == "blue"]
            if blue_runes:
                # v105 M11 P1：改用 C.rune_item 构造——补 effect/lvl 字段（否则背包
                # 『附魔』刻印时 economy.py:2035/2059 读 rd["effect"] 必 KeyError 崩溃），
                # 顺带修复 desc 带字面 {v} 占位符 / 售价恒 50（战斗掉落版 cost//2=400）/
                # 名字无品质前缀与等级（掉落版"稀有符文·灼热 I"）三个倒挂
                rk = random.choice(blue_runes)
                r_def = C.RUNES[rk]
                rune_data = C.rune_item(r_def["effect"], random.randint(1, 2))
                if rune_data:
                    # key 与战斗掉落一致（rune_<effect>_<lvl>，同键可叠加）
                    db.add_item(group_id, qq_id, f"rune_{r_def['effect']}_{rune_data['lvl']}", rune_data)
                    text = f"✨ 宝箱里泛起微光——符文【{rune_data['name']}】！"
                else:
                    mat = random.choice(inst.get("materials", ["兽肉"]))
                    mat_id = C.resolve("materials", mat)
                    db.add_item(group_id, qq_id, mat_id, {
                        "name": C.display("materials", mat_id), "type": "材料",
                        "stackable": True, "price": C.MATERIALS[mat_id]["price"],
                    }, count=2)
                    text = f"🎒 宝箱里是稀有材料——{C.display('materials', mat_id)} ×2！"
            else:
                mat = random.choice(inst.get("materials", ["兽肉"]))
                mat_id = C.resolve("materials", mat)
                db.add_item(group_id, qq_id, mat_id, {
                    "name": C.display("materials", mat_id), "type": "材料",
                    "stackable": True, "price": C.MATERIALS[mat_id]["price"],
                }, count=2)
                text = f"🎒 宝箱里是稀有材料——{C.display('materials', mat_id)} ×2！"
        else:
            mat = random.choice(inst.get("materials", ["兽肉"]))
            mat_id = C.resolve("materials", mat)
            db.add_item(group_id, qq_id, mat_id, {
                "name": C.display("materials", mat_id), "type": "材料",
                "stackable": True, "price": C.MATERIALS[mat_id]["price"],
            }, count=2)
            text = f"🎒 宝箱里是稀有材料——{C.display('materials', mat_id)} ×2！"
        st["secret_chest"] = None
        db.save_battle(group_id, st["leader"], st)
        return "🔐 你打开了密室宝箱！\n" + text

    async def _instance_victory(self, event, group_id, qq_id, player, st, logs):
        inst = C.INSTANCES[st["inst_id"]]
        # v137：Boss 可能已从 st["boss"] 置空（enemies 阵列承载），从阵列找 role=boss 或取首个
        boss = st.get("boss")
        if not boss or not isinstance(boss, dict):
            boss = next((u for u in (st.get("enemies") or []) if u.get("role") == "boss"), None) \
                or next((u for u in (st.get("enemies") or [])), None) or {}
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
        #    宝箱内容分层：图纸残页 50% / 稀有符文 30% / 专属材料 20%（稀缺品走低概率，防通胀）
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
        db.save_battle(group_id, st["leader"], st)
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
                                 cur_map=_town_id, cur_subarea=_town_sa)
                lines.append(f"📍 {p['name']} 被送回了【{_town_name}·{_town_sa_name}】（HP 0，先休息恢复吧）")
        yield event.plain_result("\n".join(lines))
