# -*- coding: utf-8 -*-
"""《剑与魔法》命令层 - instance（组队副本）

2 人组队轮流回合 Boss 战：
- 队长『副本 <名字>』开本（需已组队），队员自动参战
- 轮流出手：队员A行动 → 队员B行动 → Boss行动 → 下一轮
- 超时自动防御（事件驱动惰性检测，非定时器）：轮到的人 120 秒不动，
  任何人再发指令时自动把 TA 的回合带过去
- 战斗中不能逃跑（Boss 锁定）；副本失败全队回城
"""
import random
import time
import uuid

from astrbot.api import star
from astrbot.api.event import AstrMessageEvent, filter

from .. import content as C
from .. import db
from .. import engine as E
from .. import battle as BT
from ..commands.base import CommandBase, no_prof_waiting, require_player

INSTANCE_TIMEOUT = 120  # 副本行动超时（秒）


class InstanceCmds(CommandBase):

    @filter.regex(r"^(?:\[At:\d+\]\s*)?副本(?:[\s\S]*)$")
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
                for _m in _st["members"]:
                    self._unlock_battle(group_id, _m)
                    db.clear_battle(group_id, _m)
                yield event.plain_result("⏳ 通关时间已过 30 分钟，你被自动传送出了副本。")
                return
            yield event.plain_result(self._instance_status(group_id, qq_id, inst_row))
            return
        arg = self._strip_cmd(event, "副本").strip()
        if not arg:
            yield event.plain_result(self._instance_list(player))
            return
        # 队长开本：『副本 <名字>』
        # v87.2：若存在已撤退（retreated）的同副本记录 → 恢复进度继续
        old_row = self._instance_retreated_row(group_id, qq_id)
        if old_row:
            old_st = old_row["state"]
            if old_st.get("inst_id") and (old_st["inst_id"] == arg or
                                          C.INSTANCES.get(old_st["inst_id"], {}).get("name") == arg):
                old_st["retreated"] = False
                old_st["mode"] = "map"
                for m in old_st["members"]:
                    self._lock_battle(group_id, m)
                db.save_battle(group_id, qq_id, old_st)
                inst = C.INSTANCES.get(old_st["inst_id"], {})
                yield event.plain_result(
                    f"{inst.get('icon', '🏰')} 【{inst.get('name', '')}】你回到了副本深处！\n"
                    f"━━━━━━━━━━━━\n"
                    f"{self._instance_map_view(old_st, group_id)}"
                )
                return
        async for _r in self._instance_start(event, group_id, qq_id, player, arg):
            yield _r

    @filter.regex(r"^(?:\[At:\d+\]\s*)?深入(?:第\s*(\d+)\s*层)?(?:[层进]\s*)?$")
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
            yield event.plain_result("当前层的敌人还没肃清！先打完再说～")
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
            st["stage_secret_found"] = False
            st["stage_secret_cleared"] = False
            self._check_stage_secret_cond(st)  # 新层 secret cond 检查（如海蚀洞窟 L3 藏宝密室）
        st["enemy"] = st["boss"]
        st["e_buffs"] = {}
        st["round"] = 1
        for m in st["members"]:
            st["p_buffs"][m] = {}
            st["p_hot"][m] = {}
            st["p_food_effects"][m] = []
            st["p_defending"][m] = False
        st["turn"] = 0
        st["acted"] = [False] * len(st["members"])
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
        yield event.plain_result(
            f"🧭 你继续深入……\n"
            f"━━━━━━━━━━━━\n"
            f"🚪 第 {st['stage_idx'] + 1} 层 · {next_stage['name']}\n"
            f"{role}【{st['boss']['name']}】Lv.{st['boss']['lv']} ❤️ {st['boss']['hp']:,}\n"
            f"━━━━━━━━━━━━\n"
            f"⏳ 轮到 {st['players'][st['members'][0]].get('name', st['members'][0])} 行动！『攻击』『技能 <名称>』『防御』"
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
    @filter.regex(r"^(?:\[At:\d+\]\s*)?调查\s*(\S+)\s*$")
    @require_player()
    @no_prof_waiting()

    async def instance_investigate(self, event: AstrMessageEvent):
        """与当前层 POI 互动：开箱/点火/读碑/拉机关/拆陷阱(29 章 13.5)"""
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
        stages = st.get("inst_stages") or []
        sidx = st["stage_idx"]
        stage = stages[sidx] if sidx < len(stages) else {}
        # v101.27 #390：通关后特殊搜刮 POI 优先（战利品堆/墙砖/密室宝箱），
        # 避免『调查 宝箱』误命中 Boss 房静态"陪葬宝箱"等 stage POI
        if st.get("cleared"):
            if name in ("战利品堆", "战利品") and st.get("loot_pile"):
                yield event.plain_result(self._instance_loot_pile(group_id, qq_id, player, st))
                return
            if name in ("墙砖", "松动的墙砖", "裂痕", "暗格") and st.get("secret_crack"):
                yield event.plain_result(self._instance_secret_crack(group_id, qq_id, player, st))
                return
            if name in ("宝箱", "暗格宝箱", "神秘宝箱") and st.get("secret_chest"):
                yield event.plain_result(self._instance_secret_chest(group_id, qq_id, player, st))
                return
        poi = self._find_stage_poi(stage, name)
        # 隐藏房间 POI 也算
        secret = stage.get("secret")
        if not poi and secret and st.get("stage_secret_found") and not st.get("stage_secret_cleared"):
            for sp in secret.get("pois", []):
                if sp.get("name") == name or (name and name in sp.get("name", "")):
                    poi = sp
                    break
        if not poi:
            yield event.plain_result(f"这里没有『{name}』可以调查～『副本地图』看看周围有什么。")
            return
        if self._poi_used(st, sidx, poi.get("id", "")):
            yield event.plain_result(f"{poi.get('name', '')}已经被处理过了。")
            return
        # v87.2 复用世界地图 POI 处理（_handle_poi → _handle_inst_poi）
        text = self._handle_poi(group_id, qq_id, player, stage, poi.get("id", ""), poi, st=st)
        self._check_stage_secret_cond(st)
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
        for m in st["members"]:
            self._unlock_battle(group_id, m)
            db.clear_battle(group_id, m)
        yield event.plain_result(
            f"🏳️ 你带着战利品离开了{inst.get('name', '副本')}。冒险者的旅途还在继续～"
        )

    # ---------------- 副本探索（v87.2，由 combat.explore 路由） ----------------
    async def _instance_explore(self, event, group_id, qq_id, inst_row):
        """副本内探索：优先遇怪(进入战斗)，未触发陷阱概率踩中，否则无事。"""
        st = inst_row["state"]
        # v101.27 #390：通关后探索无意义（已无敌人），引导搜刮/离开
        if st.get("cleared"):
            yield event.plain_result("副本已通关，没有敌人可探索了！『副本地图』看看战利品堆，或『离开副本』传出～")
            return
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
            yield event.plain_result(
                f"🍃 你警惕地探索着，突然——{stage.get('name', '')}里的怪物扑了上来！\n"
                f"━━━━━━━━━━━━\n"
                f"{role}【{st['boss']['name']}】Lv.{st['boss']['lv']} ❤️ {st['boss']['hp']:,}\n"
                f"━━━━━━━━━━━━\n"
                f"⏳ 轮到 {st['players'][st['members'][0]].get('name', st['members'][0])} 行动！『攻击』『技能 <名称>』『防御』"
            )
            return
        # 无怪：检查陷阱（未用的 trap POI）——50% 概率踩中
        player = self._player(group_id, qq_id)
        for p in stage.get("pois") or []:
            if p.get("type") == "trap" and not self._poi_used(st, sidx, p.get("id", "")):
                if random.random() < C.INST_EVENT_CHANCE:
                    text = self._handle_poi(group_id, qq_id, player, stage, p.get("id", ""), p, st=st)
                    self._check_stage_secret_cond(st)
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
        for m in st["members"]:
            st["p_buffs"][m] = {}
            st["p_hot"][m] = {}
            st["p_food_effects"][m] = []
            st["p_defending"][m] = False
        st["turn"] = 0
        st["acted"] = [False] * len(st["members"])
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
        lines.append("━━━━━━━━━━━━")
        lines.append("💡 单人副本直接『副本 <名字>』开本！多人副本先『组队 <对方名字>』(上限 4 人)，队长『副本 <名字>』开本！")
        lines.append("💡 按顺序轮流出手，Boss 血量随人数上涨，配合好才能通关！")
        return "\n".join(lines)

    def _instance_status(self, group_id, qq_id, battle_row) -> str:
        st = battle_row["state"]
        # v87.2 副本地图化：地图模式显示层全景
        if st.get("mode") == "map":
            return self._instance_map_view(st, group_id)
        inst = C.INSTANCES.get(st["inst_id"], {})
        boss = st["boss"]
        pct = max(0, int(boss["hp"] / max(1, boss["max_hp"]) * 100))
        stages = st.get("inst_stages") or []
        stage_line = ""
        if stages:
            sidx = st.get("stage_idx", 0)
            sname = stages[sidx]["name"] if sidx < len(stages) else ""
            stage_line = f" 🚪 第 {sidx + 1} 层 · {sname}"
        lines = [
            f"{inst.get('icon', '🏰')} 【{inst.get('name', st['inst_id'])}】 第 {st.get('round', 1)} 轮{stage_line}",
            "━━━━━━━━━━━━",
            f"👹【{boss['name']}】❤️ {max(0, boss['hp']):,} / {boss['max_hp']:,}({pct}%)",
        ]
        for m in st["members"]:
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
        cur_key = str(st["members"][st["turn"]])
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
        """生成当前层小地图全景(desc + 复用 _map_interactions + 怪物/隐藏房间)"""
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
            lines.append("━━━━━━━━━━━━")
            if st.get("loot_pile"):
                lines.append("🎁 战利品堆：首领的遗物堆在角落（『调查 战利品堆』）")
            if st.get("secret_crack"):
                lines.append("🧱 墙上有一块松动的墙砖……（『调查 墙砖』）")
            if st.get("secret_chest"):
                lines.append("🔐 神秘宝箱：密室深处泛着微光（『调查 宝箱』）")
            lines.append("💡 搜刮完毕用『离开副本』传出～")
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
        lines.append("💡 『探索』遇怪 · 『调查 <名称>』互动 · 『深入』推进 · 『副本地图』查看全景 · 『撤退』离开")
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
                    "acted": [False] * len(members),
                    "p_buffs": {str(m): {} for m in members},
                    "p_hot": {str(m): {} for m in members},
                    "p_food_effects": {str(m): [] for m in members},
                    "e_buffs": {},
                    "p_defending": {str(m): False for m in members},
                    "mech_stacks": {str(m): {} for m in members},
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
                    "acted": [False] * len(members),
                    "p_buffs": {str(m): {} for m in members},
                    "p_hot": {str(m): {} for m in members},
                    "p_food_effects": {str(m): [] for m in members},
                    "e_buffs": {},
                    "p_defending": {str(m): False for m in members},
                    "mech_stacks": {str(m): {} for m in members},
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
            "acted": [False] * len(members),
            "p_buffs": {str(m): {} for m in members},
            "p_hot": {str(m): {} for m in members},
            "p_food_effects": {str(m): [] for m in members},
            "e_buffs": {},
            "mech_stacks": {str(m): {} for m in members},  # v59 副本叠层（按玩家持久化）
            "p_defending": {str(m): False for m in members},
            "turn_time": now,
            "contribution": {},
            "threat": {str(m): 0 for m in members},
            "over": False,
        }
        return st


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
                yield event.plain_result(f"{p['name']} 正在战斗中，先打完再来！")
                return
        # v86.3 入场钥匙检查（29 章 11 节）：队长持有 key_item 才能开本
        key_item = inst.get("key_item")
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
            # 消耗钥匙（首通前）
            if has_key and not cleared_before:
                db.remove_item(group_id, qq_id, key_entry["key"])
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
            }
        # v57：副本行动序按速度降序（快者先出手）。真人轮流节奏不变，只是顺序由速度决定
        st["members"] = sorted(st["members"], key=lambda m: st["players"][str(m)].get("spd", 0), reverse=True)
        st["acted"] = [False] * len(st["members"])
        st["turn"] = 0
        # 锁全队
        for m in members:
            self._lock_battle(group_id, m)
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
        # v87.2 副本地图化：地图模式显示层全景，战斗模式保持原样
        if st.get("mode") == "map":
            map_view = self._instance_map_view(st, group_id)
            yield event.plain_result(
                f"{inst['icon']} 【{inst['name']}】副本开启！你踏入了这片区域。\n"
                f"━━━━━━━━━━━━\n"
                f"{map_view}\n"
                f"━━━━━━━━━━━━\n"
                f"{size_tip}"
                f"💡 先『探索』看看有什么，或『调查』周围的交互点！"
            )
            return
        stage_line = f"🚪 第 1 层 · {stage_name}\n" if stages else ""
        yield event.plain_result(
            f"{inst['icon']} 【{inst['name']}】副本开启！\n"
            f"━━━━━━━━━━━━\n"
            f"{stage_line}"
            f"👹【{boss['name']}】Lv.{boss['lv']} ❤️ {boss['max_hp']:,}\n"
            f"📜 {inst['desc']}\n"
            f"━━━━━━━━━━━━\n"
            f"{size_tip}"
            f"⚡ 行动顺序(按速度)：{' → '.join(st['players'][m].get('name', m) for m in st['members'])}\n"
            f"⏳ 轮到 {st['players'][st['members'][0]].get('name', st['members'][0])} 行动！『攻击』『技能 <名称>』『防御』\n"
            f"💡 按顺序轮流出手，超时 2 分钟自动防御；清光当前层怪物可『深入』下一层！"
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
    async def _instance_act(self, event, group_id, qq_id, player, st, action, skill_name=None):
        """副本回合行动(由攻击/技能/防御指令路由进来)"""
        # v101.24 #301：某层肃清后进入地图模式(boss=None, stage_cleared)时，攻击/技能/防御/使用道具
        # 都会走到 st["boss"]["hp"] 对 None 下标 → 'NoneType' object is not subscriptable 裸错。
        # 层内无敌人时直接引导『深入』推进，不进入战斗回合逻辑。
        if not st.get("boss"):
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
        acted = st.setdefault("acted", [False] * len(members))

        # 1. 超时推进：轮到的人 120 秒没动 → 自动防御并转到下一位（可能连续多人超时）
        # v55 轮：已退队的成员不再参与轮转（退队后不卡队友回合，否则每轮白等 120s 超时）
        party_now = [str(m) for m in db.party_members(group_id, st["leader"])]
        # v55 轮（#281）：全灭/全退队预判——最后一个存活者被反击打死、其余成员倒下或退队时，
        # 超时推进循环会无限空转卡死 worker（曾实测：小蓝+格温全倒、小芽退队 → 轮转死循环）。
        # 无任何可行动成员 → 直接失败结算。
        actionable = [i for i, m in enumerate(members)
                      if (not party_now or str(m) in party_now) and st["alive"].get(str(m), True)]
        if not actionable:
            st["over"] = True
            async for _r in self._instance_defeat(event, group_id, qq_id, player, st, logs):
                yield _r
            return
        while True:
            cur_idx = st["turn"]
            cur_key = str(members[cur_idx])
            if party_now and cur_key not in party_now:
                acted[cur_idx] = True
                st["turn"] = (cur_idx + 1) % len(members)
                st["turn_time"] = now
                continue
            if not st["alive"].get(cur_key, True):
                acted[cur_idx] = True
                st["turn"] = (cur_idx + 1) % len(members)
                st["turn_time"] = now
                continue
            if now - st.get("turn_time", now) > INSTANCE_TIMEOUT and cur_key != str(qq_id):
                pname = (self._player(group_id, cur_key) or {}).get("name", cur_key)
                logs.append(f"⏰ {pname} 迟迟没有行动，自动进入防御姿态！")
                st["p_defending"][cur_key] = True
                acted[cur_idx] = True
                st["turn"] = (cur_idx + 1) % len(members)
                st["turn_time"] = now
                continue
            break

        # 2. 确认轮到当前玩家
        cur_idx = st["turn"]
        cur_key = str(members[cur_idx])
        if str(qq_id) != cur_key:
            cur_name = (self._player(group_id, cur_key) or {}).get("name", cur_key)
            yield event.plain_result("\n".join(logs + [f"⏳ 现在是 {cur_name} 的回合，等待 TA 行动～"]))
            return

        # 3. 玩家行动（enemy_act=False，Boss 不立即反击）
        snap = st["players"][cur_key]
        # v49 意见#6 仇恨：行动前记录全队血量（用于计算治疗仇恨）
        hp_before = sum(st["players"][m]["hp"] for m in members if st["alive"].get(str(m), True))
        b = BT.Battle.from_state({
            "type": "instance",
            "enemy": st["boss"],
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
        })
        boss_before = st["boss"]["hp"]
        act_logs, ended = b.player_turn(action, skill_name, snap, enemy_act=False)
        st["players"][cur_key] = snap
        st["p_buffs"][cur_key] = b.p_buffs
        st.setdefault("p_hot", {})[cur_key] = b.p_hot
        st.setdefault("p_food_effects", {})[cur_key] = b.p_food_effects
        st["e_buffs"] = b.e_buffs
        st["mech_stacks"][cur_key] = b.mech_stacks
        # v101.25 #323：防御状态必须写回——否则 Boss 反击时读 st["p_defending"] 永远是 False，
        # 副本防御减半完全不生效（playtest round67 影刃实测 93→75 仅约 -19%）
        st["p_defending"][cur_key] = bool(getattr(b, "p_defending", False))
        snap["p_shields"] = b.p_shields
        dealt = max(0, boss_before - st["boss"]["hp"])
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
        if st["boss"]["hp"] <= 0:
            # v101.27 #390 暗格守卫击杀：走精英击杀奖励 → 密室宝箱出现（不是通关）
            if st.get("secret_guard_pending"):
                st["secret_guard_pending"] = False
                kill_lines = self._instance_kill_reward(group_id, st)
                st["secret_chest"] = True
                st["mode"] = "map"
                st["boss"] = None
                st["enemy"] = None
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
                st["e_buffs"] = {}
                st["round"] = 1
                for i in st["members"]:
                    st["p_buffs"][i] = {}
                    st["p_defending"][i] = False
                st["turn"] = 0
                st["acted"] = [False] * len(st["members"])
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
                    f"⏳ 轮到 {st['players'][st['members'][0]].get('name', st['members'][0])} 行动！『攻击』"
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
            st["first_clear"] = not any(
                a.get("ach_key") == f"inst_clear_{st['inst_id']}" and a.get("progress", 0) >= 1
                for a in (db.get_achievements(group_id, st["members"][0]) or [])
            )
            async for _r in self._instance_victory(event, group_id, qq_id, player, st, logs):
                yield _r
            return

        # 5. 标记本轮已行动，推进
        acted[cur_idx] = True
        st["turn"] = (cur_idx + 1) % len(members)
        st["turn_time"] = now

        # 6. 本轮所有存活者都行动过 → Boss 行动
        alive_idx = [i for i, m in enumerate(members) if st["alive"].get(str(m), True)]
        if alive_idx and all(acted[i] for i in alive_idx):
            logs += self._instance_boss_turn(st, group_id)
            st["round"] += 1
            for i in alive_idx:
                acted[i] = False
            # 全灭 → 失败（v101.27 鱼鱼拍板：失败=副本直接销毁，重进=全新开本）
            if not [m for m in members if st["alive"].get(str(m), True)]:
                st["over"] = True
                # v101.27 同归于尽判定：Boss 也同时阵亡 → 提示"同归于尽"（仍按失败销毁）
                if st["boss"].get("hp", 1) <= 0:
                    logs.append("⚔️ 同归于尽！你与敌人同时倒下了……")
                async for _r in self._instance_defeat(event, group_id, qq_id, player, st, logs):
                    yield _r
                return
            # 转到下一个存活者
            nxt = next((i for i in alive_idx if st["alive"].get(str(members[i]), True)), 0)
            st["turn"] = nxt
            st["turn_time"] = now

        # 7. 保存状态（存到队长名下）并展示
        self._sync_players_db(group_id, st)  # v95r76 #383：每回合行动后同步快照血量（对齐普通战斗）
        db.save_battle(group_id, st["leader"], st)
        nxt_key = str(members[st["turn"]])
        nxt_p = self._player(group_id, nxt_key)
        boss = st["boss"]
        pct = max(0, int(boss["hp"] / max(1, boss["max_hp"]) * 100))
        yield event.plain_result(
            "\n".join(logs) +
            f"\n━━━━━━━━━━━━\n"
            f"👹【{boss['name']}】❤️ {max(0, boss['hp']):,} / {boss['max_hp']:,}({pct}%)\n"
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
        # 全队武器淬毒：给每个存活成员 mech_stacks.poison（下回合攻击叠毒，v59 存副本状态）
        if kind == "poison_all":
            for k in alive:
                ms = st["mech_stacks"].setdefault(k, {})
                ms["poison"] = E.mech_stack_gain("poison", ms, 2)
            logs.append("☠️ 全队武器淬毒！")
            return logs
        return logs

    def _instance_boss_turn(self, st: dict, group_id: int) -> list:
        """Boss 行动（v49 意见#6 仇恨制）：打仇恨最高的存活队员；防御者仇恨已拉高优先被选中（伤害减半）
        v57：速度机制——Boss 速度 ≥ 全队平均 ×1.5 时每轮多动 1 次、×2 时多动 2 次"""
        logs = []
        members = st["members"]
        alive = [m for m in members if st["alive"].get(str(m), True)]
        if not alive:
            return logs
        # v57：算 Boss 多动次数（基于存活队员平均速度）
        avg_spd = sum(st["players"][str(m)].get("spd", 0) for m in alive) / max(1, len(alive))
        boss_spd = max(1, st["boss"].get("spd", 0) or 1)
        extra = 0
        if boss_spd >= avg_spd * 2.0 and avg_spd > 0:
            extra = 2
        elif boss_spd >= avg_spd * 1.5 and avg_spd > 0:
            extra = 1
        boss_acts = 1 + extra
        for _ in range(boss_acts):
            if not [m for m in members if st["alive"].get(str(m), True)]:
                break
            logs += self._instance_boss_one_turn(st, group_id)
            if extra and st["boss"].get("hp", 1) > 0:
                logs.append(f"⚡【{st['boss'].get('name', 'Boss')}】速度惊人，再次出手！")
        return logs

    def _instance_boss_one_turn(self, st: dict, group_id: int) -> list:
        """Boss 单次行动：打仇恨最高(或嘲讽目标)的存活队员"""
        logs = []
        members = st["members"]
        alive = [m for m in members if st["alive"].get(str(m), True)]
        if not alive:
            return logs
        threat = st.setdefault("threat", {})
        # v51 嘲讽：Boss 优先攻击嘲讽目标（若存活），否则按仇恨最高
        taunt_key = str(st.get("taunt_target", ""))
        if taunt_key and st.get("taunt_turns", 0) > 0 and st["alive"].get(taunt_key, False):
            target = next((m for m in alive if str(m) == taunt_key), None)
            if target is None:
                target = taunt_key
            st["taunt_turns"] = max(0, int(st.get("taunt_turns", 0)) - 1)
            logs.append(f"📢 嘲讽生效！Boss 怒视着 {st['players'][taunt_key].get('name', target)}！")
            if st["taunt_turns"] <= 0:
                st.pop("taunt_target", None)
        else:
            if taunt_key:
                st.pop("taunt_target", None)
            # 仇恨最高者（同仇恨随机）
            top = max(threat.get(str(m), 0) for m in alive)
            candidates = [m for m in alive if threat.get(str(m), 0) == top]
            target = random.choice(candidates) if len(candidates) > 1 else candidates[0]
        tkey = str(target)
        snap = st["players"][tkey]
        tname = snap.get("name", target)
        b = BT.Battle.from_state({
            "type": "instance",
            "enemy": st["boss"],
            "p_buffs": st["p_buffs"].get(tkey, {}),
            "e_buffs": st["e_buffs"],
        })
        mlogs, dmg = b._enemy_turn(snap)
        st["e_buffs"] = b.e_buffs
        if st["p_defending"].get(tkey):
            dmg = max(1, int(dmg * 0.5))
            # v101.25 #345：防御减伤后日志同步修正——玩家看到的伤害数字与实际扣血一致
            # （round71 影刃抓包：日志显示 111/71/78/140，实际扣血 55/35/39/70 正好减半）
            import re as _re
            mlogs = [_re.sub(r"造成 (\d+) 点伤害",
                             lambda m: f"造成 {max(1, int(int(m.group(1)) * 0.5))} 点伤害(格挡)",
                             x) for x in mlogs]
            logs.append(f"🛡️ {tname} 举盾格挡！")
        logs += mlogs
        if dmg > 0:
            snap["hp"] = max(0, snap["hp"] - dmg)
            logs.append(f"❤️ {tname} 剩余 {snap['hp']}/{snap['max_hp']}")
        if snap["hp"] <= 0:
            st["alive"][tkey] = False
            threat[tkey] = 0  # 死亡清仇恨
            logs.append(f"💀 {tname} 倒下了！")
        st["p_defending"][tkey] = False  # 防御只挡一次
        return logs

    # ---------------- 结算 ----------------
    def _instance_kill_reward(self, group_id, st):
        """v95r77 #363：副本小怪/精英击杀奖励（此前击杀零播报——无经验/金币/掉落反馈）。

        对照野外 _kill 的 v93 经济模式：经验入账 + 金币×1.5 折算成可卖材料
        （怪物掉落池优先，通用池兜底；精英 2 种普通 1 种）。组队存活成员各一份。
        Boss 击杀走 _instance_victory 通关奖励，不在此列。
        注意：副本战斗内不做升级检查（check_player_level_up 会把 hp 回满，
        会破坏战斗节奏），经验攒到出副本后野外击杀时统一结算。"""
        mdef = st.get("boss")
        if not mdef:
            return []
        lines = []
        for _m in st["members"]:
            if not st["alive"].get(str(_m), True):
                continue
            p = self._player(group_id, _m)
            if not p:
                continue
            snap = st["players"].get(str(_m)) or {}
            exp = mdef.get("exp", 0)
            diff = mdef.get("lv", 0) - p.get("level", 0)
            if diff > 5:
                exp = int(exp * max(0.10, 1.0 - (diff - 5) * 0.15))
            elif diff < -5:
                exp = int(exp * max(0.10, 1.0 - (-diff - 5) * 0.20))
            # v93 经济改革：金币不入账，折算成可卖材料
            mats = []
            mat_value = int(mdef.get("gold", 0) * 1.5)
            if mat_value > 0:
                drop_pool = [m for m in (mdef.get("drops") or []) if m]
                if not drop_pool:
                    drop_pool = ["兽肉", "狼皮", "蛇皮", "野猪牙"]
                is_hi = mdef.get("is_elite") or mdef.get("is_boss")
                # 测试确定性铁律（v103）：不在这里用 random.sample——新增随机数消耗
                # 会打乱全量回归的战斗随机序列（两次跑失败点不同=随机性证据）。
                # 掉落种类按掉落池顺序取前 N 种（确定性），数量仍按价值折算。
                picks = drop_pool[:min(2 if is_hi else 1, len(drop_pool))]
                per_val = mat_value / len(picks)
                for mat_name in picks:
                    mid = C.resolve("materials", mat_name)
                    if mid not in C.MATERIALS:
                        continue
                    mprice = C.MATERIALS[mid].get("price", 0)
                    if mprice <= 0:
                        continue
                    n = max(1, min(30, round(per_val / mprice)))
                    db.add_item(group_id, _m, mid,
                                {"name": C.display("materials", mid), "type": "材料",
                                 "stackable": True, "price": mprice}, n)
                    mats.append(f"{C.display('materials', mid)} ×{n}")
            db.init_stats(group_id, _m)
            db.bump_stats(group_id, _m, kills=1, day_kills=1)
            if mdef.get("is_elite"):
                db.bump_stats(group_id, _m, elite_kills=1)
            elif mdef.get("is_boss"):
                db.bump_stats(group_id, _m, boss_kills=1)
            db.bump_bestiary(group_id, _m, mdef.get("name", ""))
            db.update_player(group_id, _m, exp=p["exp"] + exp,
                             hp=snap.get("hp", p.get("hp", 0)), mp=snap.get("mp", p.get("mp", 0)),
                             max_hp=snap.get("max_hp", p.get("max_hp", 0)),
                             max_mp=snap.get("max_mp", p.get("max_mp", 0)))
            line = f"  {p['name']}：经验 +{exp}"
            if mats:
                line += f"，拾取材料 {'、'.join(mats)}"
            lines.append(line)
        return lines

    # ---------------- 通关后搜刮（v101.27 #390） ----------------
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
                    "name": mname, "type": "材料", "stackable": True,
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
            f"⏳ 轮到 {st['players'][st['members'][0]].get('name', st['members'][0])} 行动！『攻击』『技能 <名称>』『防御』"
        )

    def _instance_secret_chest(self, group_id, qq_id, player, st) -> str:
        """暗格宝箱：图纸残页 50% / 稀有符文 30% / 专属材料 20%（稀缺品低概率，防通胀）"""
        roll = random.random()
        inst = C.INSTANCES[st["inst_id"]]
        if roll < 0.50:
            pages = random.randint(2, 4)
            db.add_item(group_id, qq_id, "mat_tu_zhi_can_ye",
                        {"name": "图纸残页", "type": "材料", "stackable": True, "price": 10},
                        count=pages)
            text = f"📜 宝箱里是泛黄的纸张——图纸残页 ×{pages}！"
        elif roll < 0.80:
            # 稀有符文池（blue 品质符文，v101.25i6 品质统一后 quality=blue）
            blue_runes = [k for k, r in C.RUNES.items() if (r.get("quality") or "") == "blue"]
            if blue_runes:
                rk = random.choice(blue_runes)
                rune = C.RUNES[rk]
                db.add_item(group_id, qq_id, rk, {
                    "name": rune.get("name", rk), "type": "符文",
                    "stackable": True, "price": rune.get("price", 50),
                    "quality": "blue", "desc": rune.get("desc", ""),
                })
                text = f"✨ 宝箱里泛起微光——符文【{rune.get('name', rk)}】！"
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
        boss = st["boss"]
        lines = [x for x in logs if "你击败了" not in x]
        lines.append("")
        lines.append(f"🎉 【{boss['name']}】被击败了！{inst.get('icon', '🏰')}{inst.get('name', '')} 通关！")
        # v101.27 #390：通关后允许停留搜刮（鱼鱼拍板）——不再 clear_battle，
        # 保留状态让玩家调查 Boss 房交互物/战利品堆/隐藏暗格，主动『离开副本』才清。
        # 解锁战斗锁（可自由行动），但 battle 记录保留供副本指令读取
        for m in st["members"]:
            self._unlock_battle(group_id, m)
        # 通关奖励
        for m in st["members"]:
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
        if inst.get("blueprint") and st.get("contribution"):
            top_key = max(st["contribution"], key=st["contribution"].get)
            top_p = self._player(group_id, top_key)
            if top_p:
                bp = C.roll_blueprint(boss["lv"])
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
        for m in st["members"]:
            if st["alive"].get(str(m), True):
                db.set_achievement(group_id, m, f"inst_clear_{st['inst_id']}", 1)
                db.bump_stats(group_id, m, inst_clears=1)
                C.check_achievements(group_id, m, None, {"inst_id": st["inst_id"]})
        # v101.27 #390 隐藏奖励：通关后停留搜刮
        # ① 战利品堆（必出，保底搜刮体验）：金币=通关奖金×30% + 专属材料×1
        # ② 隐藏暗格（概率出）：20%（首通 50%）→ 墙上的裂痕 → 精英守卫 → 宝箱
        #    宝箱内容分层：图纸残页 50% / 稀有符文 30% / 专属材料 20%（稀缺品走低概率，防通胀）
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
        if st["secret_crack"]:
            lines.append("  · 🧱 墙上似乎有【松动的墙砖】……（『调查 墙砖』）")
        lines.append("搜刮完毕用『离开副本』传出～")
        lines.append("")
        lines.append("💡 『副本』可再次挑战，首通成就已记录～")
        st["mode"] = "map"
        st["boss"] = None
        st["enemy"] = None
        db.save_battle(group_id, st["leader"], st)
        yield event.plain_result("\n".join(lines))

    async def _instance_defeat(self, event, group_id, qq_id, player, st, logs):
        lines = [x for x in logs if "毒发身亡" not in x]
        lines.append("")
        lines.append("💀 队伍全灭……副本失败！冒险者们被送回了城镇。")
        for m in st["members"]:
            self._unlock_battle(group_id, m)
            db.clear_battle(group_id, m)
            p = self._player(group_id, m)
            if p:
                db.update_player(group_id, m, hp=0, mp=p.get("max_mp", 0), cur_map=C.START_MAP, cur_subarea=C.START_SUBAREA)
        yield event.plain_result("\n".join(lines))
