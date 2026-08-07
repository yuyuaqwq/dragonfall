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
from ..commands.base import CommandBase, no_prof_waiting

INSTANCE_TIMEOUT = 120  # 副本行动超时（秒）


class InstanceCmds(CommandBase):

    @filter.regex(r"^(?:\[At:\d+\]\s*)?副本(?:[\s\S]*)$")
    @no_prof_waiting()

    async def instance_cmd(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        # 已在副本战斗中 → 显示状态
        inst_row = self._instance_battle_for(group_id, qq_id)
        if inst_row:
            yield event.plain_result(self._instance_status(group_id, qq_id, inst_row))
            return
        arg = self._strip_cmd(event, "副本").strip()
        if not arg:
            yield event.plain_result(self._instance_list(player))
            return
        # 队长开本：『副本 <名字>』
        async for _r in self._instance_start(event, group_id, qq_id, player, arg):
            yield _r

    # ---------------- 查询 ----------------
    def _class_role_label(self, class_name) -> str:
        """职业定位标签：战士·坦克 / 牧师·治疗"""
        info = C.CLASSES.get(class_name, {})
        role = info.get("role", "")
        return f"{info.get('name', class_name)}{'·' + role if role else ''}"

    def _party_composition_hint(self, st: dict) -> list:
        """队伍构成提示（v49 意见#7 职业组队搭配）"""
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
        """查找玩家（队长或队员）当前的副本战斗状态；无则 None"""
        b = db.get_battle(group_id, qq_id)
        if b and b["state"].get("type") == "instance":
            return b
        members = db.party_members(group_id, qq_id)
        if members and str(members[0]) != str(qq_id):
            lb = db.get_battle(group_id, members[0])
            if lb and lb["state"].get("type") == "instance":
                return lb
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
            lines.append(f"{i}. {mark} {inst['icon']} {inst['name']}（Lv.{inst['lv']}+ · {size}）")
            lines.append(f"   {inst['desc']}")
            mats = "、".join(
                C.display("materials", m) if m in C.MATERIALS else m
                for m in inst.get("materials", [])
            )
            lines.append(f"   👹 Boss：{inst['boss'][1]}（Lv.{inst['boss'][3]}）· 掉落：{mats}")
        lines.append("━━━━━━━━━━━━")
        lines.append("💡 单人副本直接『副本 <名字>』开本！多人副本先『组队 <对方名字>』（上限 4 人），队长『副本 <名字>』开本！")
        lines.append("💡 按顺序轮流出手，Boss 血量随人数上涨，配合好才能通关！")
        return "\n".join(lines)

    def _instance_status(self, group_id, qq_id, battle_row) -> str:
        st = battle_row["state"]
        inst = C.INSTANCES.get(st["inst_id"], {})
        boss = st["boss"]
        pct = max(0, int(boss["hp"] / max(1, boss["max_hp"]) * 100))
        lines = [
            f"{inst.get('icon', '🏰')} 【{inst.get('name', st['inst_id'])}】 第 {st.get('round', 1)} 轮",
            "━━━━━━━━━━━━",
            f"👹【{boss['name']}】❤️ {max(0, boss['hp']):,} / {boss['max_hp']:,}（{pct}%）",
        ]
        for m in st["members"]:
            p = self._player(group_id, m)
            pname = p["name"] if p else m
            snap = st["players"].get(str(m), {})
            alive = st["alive"].get(str(m), True)
            mark = "✅" if alive else "💀"
            cls_label = self._class_role_label(snap.get("class_name", ""))
            lines.append(
                f"{mark} {pname}（{cls_label}）：❤️ {snap.get('hp', 0)}/{snap.get('max_hp', 1)} "
                f"💙 {snap.get('mp', 0)}/{snap.get('max_mp', 1)}"
            )
        cur_key = str(st["members"][st["turn"]])
        cur_p = self._player(group_id, cur_key)
        lines.append("━━━━━━━━━━━━")
        lines.append(f"⏳ 轮到 {cur_p['name'] if cur_p else cur_key} 行动！『攻击』『技能 <名称>』『防御』")
        return "\n".join(lines)

    # ---------------- 开本 ----------------
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
        # 单人副本：无需组队，直接以自己开本
        if min_players <= 1:
            members = [qq_id]
        else:
            members = db.party_members(group_id, qq_id)
            if not members:
                yield event.plain_result(
                    f"『{inst['name']}』需要 {min_players}-{max_players} 人组队！先『组队 <对方名字>』～"
                )
                return
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
            if self._in_battle(group_id, m):
                yield event.plain_result(f"{p['name']} 正在战斗中，先打完再来！")
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
            "acted": [False] * len(members),
            "p_buffs": {str(m): {} for m in members},
            "e_buffs": {},
            "mech_stacks": {str(m): {} for m in members},  # v59 副本叠层（按玩家持久化）
            "p_defending": {str(m): False for m in members},
            "turn_time": now,
            "contribution": {},
            "threat": {str(m): 0 for m in members},
            "over": False,
        }
        for m in members:
            p = self._player(group_id, m)
            st["players"][str(m)] = {
                "name": p["name"], "qq_id": m,
                "class_name": p["class_name"], "level": p["level"],
                "hp": p["hp"], "max_hp": p["max_hp"],
                "mp": p["mp"], "max_mp": p["max_mp"],
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
        yield event.plain_result(
            f"{inst['icon']} 【{inst['name']}】副本开启！\n"
            f"━━━━━━━━━━━━\n"
            f"👹【{boss['name']}】Lv.{boss['lv']} ❤️ {boss['max_hp']:,}\n"
            f"📜 {inst['desc']}\n"
            f"━━━━━━━━━━━━\n"
            f"{size_tip}"
            f"⚡ 行动顺序（按速度）：{' → '.join(st['players'][m].get('name', m) for m in st['members'])}\n"
            f"⏳ 轮到 {st['players'][st['members'][0]].get('name', st['members'][0])} 行动！『攻击』『技能 <名称>』『防御』\n"
            f"💡 按顺序轮流出手，超时 2 分钟自动防御；Boss 锁定无法逃跑！"
        )

    # ---------------- 行动核心 ----------------
    async def _instance_act(self, event, group_id, qq_id, player, st, action, skill_name=None):
        """副本回合行动（由攻击/技能/防御指令路由进来）"""
        members = st["members"]
        now = int(time.time())
        logs = []
        acted = st.setdefault("acted", [False] * len(members))

        # 1. 超时推进：轮到的人 120 秒没动 → 自动防御并转到下一位（可能连续多人超时）
        while True:
            cur_idx = st["turn"]
            cur_key = str(members[cur_idx])
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
            "e_buffs": st["e_buffs"],
            "p_defending": st["p_defending"].get(cur_key, False),
            "e_defending": False,
            "title_bonus": snap.get("title_bonus") or {},
            # v59：叠层/护盾随战斗持久化（副本按玩家存）
            "mech_stacks": st["mech_stacks"].get(cur_key, {}),
            "shield": snap.get("shield", 0),
        })
        boss_before = st["boss"]["hp"]
        act_logs, ended = b.player_turn(action, skill_name, snap, enemy_act=False)
        st["players"][cur_key] = snap
        st["p_buffs"][cur_key] = b.p_buffs
        st["e_buffs"] = b.e_buffs
        st["mech_stacks"][cur_key] = b.mech_stacks
        snap["shield"] = b.shield
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
            logs.append("🛡️ 你大声挑衅，Boss 的注意力被你吸引过来！（仇恨飙升）")
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

        # 4. Boss 死亡 → 通关
        if st["boss"]["hp"] <= 0:
            st["over"] = True
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
            # 全灭 → 失败
            if not [m for m in members if st["alive"].get(str(m), True)]:
                st["over"] = True
                async for _r in self._instance_defeat(event, group_id, qq_id, player, st, logs):
                    yield _r
                return
            # 转到下一个存活者
            nxt = next((i for i in alive_idx if st["alive"].get(str(members[i]), True)), 0)
            st["turn"] = nxt
            st["turn_time"] = now

        # 7. 保存状态（存到队长名下）并展示
        db.save_battle(group_id, st["leader"], st)
        nxt_key = str(members[st["turn"]])
        nxt_p = self._player(group_id, nxt_key)
        boss = st["boss"]
        pct = max(0, int(boss["hp"] / max(1, boss["max_hp"]) * 100))
        yield event.plain_result(
            "\n".join(logs) +
            f"\n━━━━━━━━━━━━\n"
            f"👹【{boss['name']}】❤️ {max(0, boss['hp']):,} / {boss['max_hp']:,}（{pct}%）\n"
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
        # 全队护盾（直接加 shield 值）
        if kind == "shield_all":
            src = st["players"][source_key]
            base = stats.get("matk") or stats.get("atk") or 0
            shield = int(base * 0.20)
            for k in alive:
                p = st["players"][k]
                p["shield"] = p.get("shield", 0) + shield
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
        """Boss 单次行动：打仇恨最高（或嘲讽目标）的存活队员"""
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
    async def _instance_victory(self, event, group_id, qq_id, player, st, logs):
        inst = C.INSTANCES[st["inst_id"]]
        boss = st["boss"]
        lines = [x for x in logs if "你击败了" not in x]
        lines.append("")
        lines.append(f"🎉 【{boss['name']}】被击败了！{inst.get('icon', '🏰')}{inst.get('name', '')} 通关！")
        # 解锁全队 + 清战斗
        for m in st["members"]:
            self._unlock_battle(group_id, m)
            db.clear_battle(group_id, m)
        # 存活者奖励
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
                             hp=snap["hp"], mp=snap["mp"])
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
                db.add_item(group_id, top_key, f"bp_{uuid.uuid4().hex[:8]}", bp)
                lines.append(f"👑 首功 {top_p['name']} 额外获得图纸：{bp['name']}")
        # 首通记录（每人）+ 阶段九：副本次数 + 成就判定
        for m in st["members"]:
            if st["alive"].get(str(m), True):
                db.set_achievement(group_id, m, f"inst_clear_{st['inst_id']}", 1)
                db.bump_stats(group_id, m, inst_clears=1)
                C.check_achievements(group_id, m, None, {"inst_id": st["inst_id"]})
        lines.append("\n💡 副本通关！『副本』可再次挑战，首通成就已记录～")
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
                db.update_player(group_id, m, hp=0, mp=p.get("max_mp", 0), cur_map="oak_town")
        yield event.plain_result("\n".join(lines))
