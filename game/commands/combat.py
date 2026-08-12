# -*- coding: utf-8 -*-
"""《剑与魔法》命令层 - combat（combat）

由 main.py 拆分而来，作为 Mixin 被 Main 继承。
"""
import functools
import inspect
import json
import random
import re
import time

from astrbot.api import star
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.core.message.message_event_result import MessageChain

from .. import content as C
from .. import db
from .. import engine as E
from .. import battle as BT
from ..commands.base import CommandBase, no_prof_waiting, require_player, require_battle

# 全局战斗锁（简单并发保护：同一玩家同一时间只能一场战斗）
_battle_locks = set()


class CombatCmds(CommandBase):

    @filter.regex(r"^(?:\[At:\d+\]\s*)?探索(?:\s*|$)")
    @require_player()
    @no_prof_waiting()

    async def explore(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        # v87.2 副本地图化：副本地图模式（mode=map）→ 副本内探索
        inst_row = self._instance_battle_for(group_id, qq_id)
        if inst_row and inst_row["state"].get("mode") == "map":
            async for _r in self._instance_explore(event, group_id, qq_id, inst_row):
                yield _r
            return
        if self._in_battle(group_id, qq_id):
            yield event.plain_result("你正在战斗中！先解决眼前的敌人(攻击/逃跑)")
            return
        cur = player["cur_map"]
        if cur.startswith("home_"):
            yield event.plain_result("在家里安心休息吧，没有怪物会闯进来～(『出门』去冒险)")
            return
        cur_map = C.MAP_BY_ID[cur]
        # 城镇区域（安全区）：可触发 POI，无怪
        if cur_map.get("type") == C.MAP_TYPE_TOWN:
            cur_sa_id_poi = player.get("cur_subarea") or ""
            poi_hit = C.roll_poi(group_id, qq_id, cur, cur_sa_id_poi, chance=0.15)
            if poi_hit:
                poi_id, poi = poi_hit
                poi_text = self._handle_poi(group_id, qq_id, player, cur_map, poi_id, poi)
                yield event.plain_result(poi_text)
                return
            yield event.plain_result(
                f"🏘️ 你在{cur_map['name']}里闲逛，这里是安全的城镇。\n"
                f"👥 输入『对话 <NPC名>』与这里的 NPC 交谈，『商店』购买补给。\n"
                f"🧭 前往『地图』查看周边可去的地方。"
            )
            return
        # v95.26 #265：副本区域探索不触发普通战斗——副本怪按组队强度设计（如海蚀洞窟
        # 入口子区域怪物池含 Lv.26 海盗精锐），单人遭遇必死；且探索打赢也不计入副本进度
        # （#247 只修了 Boss 混池/精英判定，普通怪池仍会单人遭遇副本怪）。
        # 副本入口应引导玩家走『副本 <名字>』开本流程（等级/人数校验 + 组队轮流 + 通关结算）。
        if cur_map.get("type") == C.MAP_TYPE_INSTANCE:
            inst_name = cur_map.get("name", "这个副本")
            yield event.plain_result(
                f"🏰 【{inst_name}】是组队副本区域，这里的敌人按队伍强度设计！\n"
                f"💡 组好队伍后输入『副本 {inst_name}』开本挑战——按顺序轮流出手，Boss 血量随人数上涨！\n"
                f"（『副本』查看全部副本列表）"
            )
            return
        # 9.4：野外 NPC 偶遇（满足条件 → 偶遇提示，不消耗探索；30 分钟冷却防刷）
        wild = C.roll_wild_encounter(group_id, qq_id, player, cur)
        if wild:
            nid, wnpc = wild
            _ta = "她" if wnpc.get("gender") == "女" else "他"  # v95 #141：代词跟随 NPC 性别
            yield event.plain_result(
                f"🍃 你在{cur_map['name']}偶遇了【{wnpc['icon']}{wnpc['name']}】！\n"
                f"　　{wnpc.get('desc', '')}\n"
                f"“{wnpc.get('dialogue', '……')}”\n"
                f"━━━━━━━━━━━━\n"
                f"💡 『对话 {wnpc['name']}』与{_ta}交谈——{_ta}今天在这里，错过就要等下次了！"
            )
            return
        # v87 02 章 7.6：POI 探索点独立判定（15%）
        # v87.9 修复：放在随机事件之前——事件命中直接 return 会吞掉 POI 判定，导致挂载了却探索不到
        # v94 体力：野外探索消耗 1 体力（偶遇 NPC 不消耗）；v101.13 坐骑 stamina_reduce 概率免费（流程照常，只免体力）
        _stam_cost = 0 if random.random() < float(C.mount_effects(player).get("stamina_reduce", 0) or 0) else 1
        if _stam_cost > 0:
            _ok, _st = self._spend_stamina(group_id, qq_id, _stam_cost, player, "探索")
            if not _ok:
                yield event.plain_result(_st)
                return
        cur_sa_id_poi = player.get("cur_subarea") or ""
        poi_hit = C.roll_poi(group_id, qq_id, cur, cur_sa_id_poi, chance=0.15)
        if poi_hit:
            poi_id, poi = poi_hit
            poi_text = self._handle_poi(group_id, qq_id, player, cur_map, poi_id, poi)
            yield event.plain_result(poi_text)
            return
        # 探索随机事件（野外/外郊/核心区 35% 概率，事件优先于遇怪）
        if random.random() < C.ENCOUNTER_EVENT_CHANCE:
            handled, ev_text = self._handle_explore_event(group_id, qq_id, player, cur_map)
            if handled:
                yield event.plain_result(ev_text)
                return
        # 探索事件池（v86 子区域：用当前子区域的怪物，无则回退地图级）
        cur_sa = None
        cur_sa_id = player.get("cur_subarea") or ""
        for _sa in (cur_map.get("subareas") or []):
            if _sa["id"] == cur_sa_id:
                cur_sa = _sa
                break
        events = []
        mon_src = (cur_sa.get("monsters") if cur_sa else None)
        if mon_src is None:
            mon_src = cur_map.get("monsters", [])
        for mid, name, role, lv, skills, drops in mon_src:
            # v95.23 #247：role=boss 条目不进普通怪池（boss 字段有独立判定 SA_BOSS_CHANCE），
            # 否则副本入口等区域探索 random.choice 会抽中 Boss → 无法逃跑被秒杀
            if role == "boss":
                continue
            events.append(("monster", (mid, name, role, lv, skills, drops)))
        # 精英/Boss：子区域优先，回退地图级
        sa_elite = (cur_sa.get("elite") if cur_sa else None) or cur_map.get("elite")
        sa_boss = (cur_sa.get("boss") if cur_sa else None) or cur_map.get("boss")
        # v95.23 #247：副本区域探索不触发精英/Boss 独立判定——副本 Boss 只能走『副本 <名字>』
        # 开本流程（有等级/人数校验和通关结算），探索撞 Boss 打赢也不计入副本进度，纯坑玩家
        if cur_map.get("type") == C.MAP_TYPE_INSTANCE:
            sa_elite = None
            sa_boss = None
        # v102.1 移除：'城镇外郊' 类型不存在于数据（maps.py 仅 城镇区域/副本/野外/隐藏区域），
        # 该分支恒 False 从未执行（历史遗留自 82abbde 红名系统，数据层重写后成孤儿）
        # v95r38 空池保护：纯精英/Boss 房（如野猪王巢）探索不报"什么也没发现"，由下方必遇逻辑接管
        if not events and not sa_elite and not sa_boss:
            _rule_txt = self._rule_fire('explore_done', group_id, qq_id, player, cur_map, {'event': 'empty'})
            yield event.plain_result("你四处搜寻，什么也没发现……"
                                     + (f"\n{_rule_txt}" if _rule_txt else ""))
            return
        # v87 04 章十六节：隐藏怪物独立判定（低概率彩蛋怪，优先级最高）
        hm = self._roll_hidden_monster(group_id, qq_id, player, cur_map)
        if hm:
            monster, tag, flavor = hm
            b = BT.Battle("monster", monster, self._title_bonus(group_id, qq_id), player=player, pet=db.pet_get(qq_id))
            db.save_battle(group_id, qq_id, b.to_state())
            self._lock_battle(group_id, qq_id)
            bless_note = "✨ 回声祝福生效：本场攻击力 +5%！\n" if b.p_buffs.get("echo_bless") else ""
            yield event.plain_result(
                f"✨ 遭遇隐藏怪物！\n"
                f"{tag}【{monster['name']}】Lv.{monster['lv']}\n"
                f"　　{flavor}\n"
                f"❤️ HP {monster['hp']}/{monster['max_hp']}\n"
                + (f"{self._resource_line(player, b)}\n" if self._resource_line(player, b) else "")
                + f"{bless_note}━━━━━━━━━━━━\n"
                f"你的行动：『攻击』『技能 <名称>』『防御』『逃跑』"
            )
            return
        # 随机遇怪：精英/首领独立保底判定（不混进普通怪池子玄学抽）
        monster = None
        tag = ""
        stam_warn = ""
        eb = self._mount_explore_bonus(player)
        if sa_elite and (random.random() < (0.08 + eb) or not events):
            monster = C.build_monster(sa_elite, cur_map)
            tag = "⭐ 精英"
        elif sa_boss and (random.random() < C.SA_BOSS_CHANCE or not events):
            monster = C.build_monster(sa_boss, cur_map)
            tag = "👑 BOSS"
            # v95.20 #101：Boss 战无法逃跑且每回合耗体力，体力低时预警，避免中途耗尽被困
            if (player.get("stamina") or 0) < 20:
                stam_warn = f"\n⚠️ 当前体力 {player.get('stamina')} 点！Boss 战每回合耗 1 点体力且无法逃跑，体力耗尽将被困战斗——建议备好食物或先恢复再战！"
        elif events:
            # v101.25c 怪物等级波动：普通怪 ±1 级（精英/Boss 固定）——同图练级不单调
            # v101.25i3：曾试 ±2 被鱼鱼否（"加减2太多了"）→ 保持 ±1
            monster = C.build_monster(random.choice(events)[1], cur_map, lv_jitter=1)
        else:
            # v95r38 兜底（上面空池+无 elite/boss 已提前 return，理论不可达）
            _rule_txt = self._rule_fire('explore_done', group_id, qq_id, player, cur_map, {'event': 'empty'})
            yield event.plain_result("你四处搜寻，什么也没发现……"
                                     + (f"\n{_rule_txt}" if _rule_txt else ""))
            return
        # 遇普通怪但此地有精英/Boss → 提示气息（刷精英的方向感）
        hint = ""
        if not tag:
            if sa_elite:
                # #242: 精英气息提示 10 分钟冷却——迷雾沼泽等地图此前连续 6 次探索全刷提示
                _hint_key = f"elite_hint_{group_id}_{qq_id}"
                _last_hint = 0
                try:
                    _last_hint = int(db.get_event_state(_hint_key) or 0)
                except Exception:
                    pass
                if time.time() - _last_hint > 600:
                    hint = f"\n💨 空气中有不寻常的气息……⭐ 此地精英【{sa_elite[1]}】似乎在附近徘徊，继续『探索』有机会遇到！"
                    try:
                        db.set_event_state(_hint_key, str(int(time.time())))
                    except Exception:
                        pass
            elif sa_boss:
                hint = f"\n💨 隐约感到强大的威压……👑 此地首领【{sa_boss[1]}】蛰伏于深处，继续『探索』有机会遇到！"
        # 保存战斗状态（v9 统一引擎）
        b = BT.Battle("monster", monster, self._title_bonus(group_id, qq_id), player=player, pet=db.pet_get(qq_id))
        db.save_battle(group_id, qq_id, b.to_state())
        self._lock_battle(group_id, qq_id)
        bless_note = "✨ 回声祝福生效：本场攻击力 +5%！\n" if b.p_buffs.get("echo_bless") else ""
        role_mark = tag or ("👑 BOSS" if monster["is_boss"] else ("⭐ 精英" if monster["is_elite"] else "🐾"))
        yield event.plain_result(
            f"⚔️ 遭遇战斗！\n"
            f"{role_mark}【{monster['name']}】Lv.{monster['lv']}\n"
            f"❤️ HP {monster['hp']}/{monster['max_hp']}\n"
            + (f"{self._resource_line(player, b)}\n" if self._resource_line(player, b) else "")
            + f"{bless_note}━━━━━━━━━━━━\n"
            f"你的行动：『攻击』『技能 <名称>』『防御』『逃跑』"
            f"{hint}{stam_warn}"
        )

    def _in_battle(self, group_id, qq_id):
        # v28：锁按 qq_id 全局维度（玩家数据已全局化，群/临时会话共用同一角色）。
        # 自愈：db 无战斗记录但内存锁残留时自动清除（跨群打完/异常中断导致）。
        # v87.2：副本撤退后（retreated）保留进度但不算战斗中
        db_battle = db.get_battle(group_id, qq_id)
        db_in_battle = db_battle is not None
        if db_battle and db_battle["state"].get("type") == "instance" and db_battle["state"].get("retreated"):
            db_in_battle = False
        key = str(qq_id)
        if not db_in_battle and key in _battle_locks:
            _battle_locks.discard(key)
            return False
        return key in _battle_locks or db_in_battle

    def _lock_battle(self, group_id, qq_id):
        _battle_locks.add(str(qq_id))

    def _unlock_battle(self, group_id, qq_id):
        _battle_locks.discard(str(qq_id))

    def _mount_explore_bonus(self, player) -> float:
        """v39 坐骑：骑乘中探索精英率提升"""
        mounts = player.get("mounts") or {}
        active_mk = mounts.get("active")
        if active_mk and active_mk in C.MOUNT_BY_KEY:
            return C.MOUNT_BY_KEY[active_mk].get("elite_bonus", 0)
        return 0.0

    def _roll_hidden_monster(self, group_id, qq_id, player, cur_map):
        """v87 04 章十六节：隐藏怪物独立判定。

        按 HIDDEN_MONSTERS 表的 cond 匹配当前地图环境，chance 概率触发。
        返回 (monster, tag, flavor) 或 None。
        """
        mid = cur_map.get("id", "")
        # 时间系统时段（night 判定：用 time_weather.current_period）
        is_night = False
        try:
            from ..core.time_weather import current_period
            is_night = current_period() in ("night", "深夜", "夜晚")
        except Exception:
            pass
        # 地图环境分类（v98.3：数据化 → core/hidden_cond.py ENV_KEYWORDS）
        from ..core.hidden_cond import envs_of, check_cond, HiddenCtx
        envs = envs_of(mid)
        if cur_map.get("type") == C.MAP_TYPE_TOWN:
            return None  # 城镇不出隐藏怪
        hctx = HiddenCtx(mid, cur_map, is_night, envs)
        for hid, hdef in C.HIDDEN_MONSTERS.items():
            # v97.6 区域限定：maps 字段指定地图 id 列表，当前图不在其中则跳过
            if hdef.get("maps") and mid not in hdef["maps"]:
                continue
            cond = hdef.get("cond", "any")
            if not check_cond(cond, hctx):
                continue
            # any / 未知：无限制
            if random.random() >= hdef.get("chance", 0.004):
                continue
            # 命中：构造怪物（等级 = 地图等级 + 偏移，clamp ≥1）
            base_lv = cur_map.get("lv", 1)
            lv = max(1, base_lv + hdef.get("lv_off", 0))
            monster_def = (hid, hdef["name"], hdef.get("role", "elite"), lv,
                           hdef.get("skills", []), hdef.get("drops", []))
            monster = C.build_monster(monster_def, cur_map)
            # 隐藏怪金币加成（gold_mult 倍）
            gold_extra = monster.get("gold", 0) * hdef.get("gold_mult", 1)
            monster["gold"] = gold_extra
            return monster, hdef.get("tag", "✨ 隐藏"), hdef.get("flavor", "")
        return None

    @filter.regex(r"^(?:\[At:\d+\]\s*)?许愿(?:[\s\S]*)$")
    @require_player()

    async def wish(self, event: AstrMessageEvent):
        """流星许愿(02 章 7.5 探索彩蛋)：三选一祝福"""
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        import json as _json, time as _time
        raw = db.get_event_state(f"wish_{group_id}_{qq_id}")
        if not raw:
            yield event.plain_result("没有流星在等你许愿……(野外『探索』偶遇流星许愿彩蛋时才能许愿)")
            return
        try:
            st = _json.loads(raw)
        except Exception:
            st = {"ts": 0}
        if not isinstance(st, dict):
            # v95.39 #216：v83 曾把 value 写成 "wish_ts" 字符串（set_state 只认 "ts"），
            # 旧状态残留字符串会在这里崩 AttributeError——统一按过期处理
            st = {"ts": 0}
        if _time.time() - st.get("ts", 0) > 120:
            db.set_event_state(f"wish_{group_id}_{qq_id}", "")
            yield event.plain_result("流星已经划过天际，你的愿望随风消散了……(下次探索再碰碰运气)")
            return
        opt = self._strip_cmd(event, "许愿").strip()
        if opt not in ("经验", "金币", "材料"):
            yield event.plain_result("『许愿 经验』『许愿 金币』『许愿 材料』——快选一个吧！")
            return
        db.set_event_state(f"wish_{group_id}_{qq_id}", "")
        if opt == "经验":
            need = C.exp_to_next(player["level"]) - player["exp"]
            gain = max(20, int(need * 0.2))
            db.update_player(group_id, qq_id, exp=player["exp"] + gain)
            player = self._player(group_id, qq_id)
            player["_title_bonus"] = self._title_bonus(group_id, qq_id)
            lv_logs, _ = E.check_player_level_up(group_id, qq_id, player)
            tail = ("\n" + "\n".join(lv_logs)) if lv_logs else ""
            msg = f"✨ 流星回应了你的愿望！经验 +{gain}{tail}"
        elif opt == "金币":
            gain = 80 + player["level"] * 8
            db.update_player(group_id, qq_id, gold=player["gold"] + gain)
            msg = f"💰 流星回应了你的愿望！金币 +{gain}"
        else:
            # v101.4：流星愿望材料池数据化 → data/poi_pools.py WISH_POOL
            mat = random.choice(C.WISH_POOL)
            mid = C.resolve("materials", mat)
            if mid in C.MATERIALS:
                db.add_item(group_id, qq_id, mid,
                            {"name": C.display("materials", mid), "type": "材料",
                             "stackable": True, "price": C.MATERIALS[mid]["price"]})
            msg = f"🎒 流星回应了你的愿望！获得材料：{C.display('materials', mid)}"
        C.check_achievements(group_id, qq_id, player, {"wish_met": True})
        yield event.plain_result(f"🌠 【许愿成真】{msg}")

    def _roll_find_quest_events(self, group_id, qq_id, player, cur_map):
        """v97.1 条件探索事件：进行中的 find 型任务，在指定地图探索按 chance 触发。
        返回触发文案(列表)或 None。机制：告示委托→探索概率遇到目标(鱼鱼示例：找猫)。"""
        import json as _json
        cur_id = cur_map.get("id", "")
        quests = db.get_quests(group_id, qq_id)
        side = quests.get("side", {}) or {}
        for sid, sq in list(side.items()):
            if sq.get("status") != "active":
                continue
            sqd = next((q for q in C.SIDE_QUESTS if q["id"] == sid), None)
            if not sqd:
                continue
            obj = sqd.get("objective") or {}
            if not obj.get("find"):
                continue
            if obj.get("map") != cur_id:
                continue
            chance = float(obj.get("chance", 0.1))
            if random.random() >= chance:
                continue
            # 命中：任务推进到 ready(交付阶段)
            sq["status"] = "ready"
            side[sid] = sq
            quests["side"] = side
            db.save_quests(group_id, qq_id, quests)
            target = obj["find"]
            mname = cur_map.get("name", "此地")
            giver = C.NPCS.get(sqd["giver"]) or C.ALL_WILD.get(sqd["giver"]) or {}
            gname = giver.get("name", "发布人")
            return (
                f"🐱【找到目标】你在{mname}的灌木丛里听到一声细弱的『喵——』！\n"
                f"一只{target}怯生生地探出头，你小心翼翼地靠近，用食物引诱，一把将它抱了起来！\n"
                f"━━━━━━━━━━━━\n"
                f"📜 『{sqd['name']}』目标达成！回去找 {gname} {self._deliver_hint(sqd['giver'])}吧～"
            )
        return None

    def _handle_explore_event(self, group_id, qq_id, player, cur_map):
        """处理探索随机事件；返回 (handled, 文本)
        v97.3：事件全部走模板引擎（core/event_templates.py），数据在 data/events.py。"""
        # v97.1 条件探索事件优先：find 型任务(告示委托)命中则不再 roll 常规事件
        find_lines = self._roll_find_quest_events(group_id, qq_id, player, cur_map)
        if find_lines:
            return True, find_lines
        name = cur_map.get("name", "此地")
        from ..core.event_templates import EventContext, execute_event_template
        # v83 02 章 7.5：探索彩蛋（独立判定，不占常规权重；v97.6 区域彩蛋按地图过滤）
        egg = C.roll_explore_egg(cur_map.get("id"))
        if egg:
            ctx = EventContext(group_id, qq_id, player, cur_map,
                               params=egg.get("params", {}), name=name,
                               hooks={"title_bonus": lambda q: self._title_bonus(group_id, q)})
            text = execute_event_template(egg["template"], ctx)
            if text:
                return True, text
        ev = C.roll_explore_event()
        ctx = EventContext(group_id, qq_id, player, cur_map,
                           params=ev.get("params", {}), name=name,
                           hooks={"title_bonus": lambda q: self._title_bonus(group_id, q)})
        text = execute_event_template(ev["template"], ctx)
        if text:
            return True, text
        return False, ""

    def _handle_poi(self, group_id, qq_id, player, cur_map, poi_id, poi, st=None):
        """v87 02 章 7.6：处理 POI 探索点交互；返回展示文本。
        v87.2 副本地图化：支持副本层内联 POI（poi 带 type 字段 + st 战斗上下文）。"""
        import uuid as _uuid
        # ---- v87.2 副本内联 POI（宝箱/篝火/石碑/机关/陷阱/补给/遗骸）----
        if poi.get("type"):
            return self._handle_inst_poi(group_id, qq_id, st, poi)
        name = cur_map.get("name", "此地")
        sub_name = ""
        cur_sa_id = player.get("cur_subarea") or ""
        for _sa in (cur_map.get("subareas") or []):
            if _sa["id"] == cur_sa_id:
                sub_name = _sa.get("name", "")
                break
        loc = f"{name}·{sub_name}" if sub_name else name
        icon = poi.get("icon", "🌿")
        pname = poi.get("name", "探索点")
        eff = poi.get("effect", "")
        # 篝火：恢复 30% 生命/魔力 + 随机烹饪食材
        if eff == "recover":
            hp_gain = int(player["max_hp"] * 0.30)
            mp_gain = int(player["max_mp"] * 0.30)
            db.update_player(group_id, qq_id, hp=min(player["max_hp"], player["hp"] + hp_gain), mp=min(player["max_mp"], player["mp"] + mp_gain))
            # v101.4：篝火食材池数据化 → data/poi_pools.py CAMPFIRE_FOOD_POOL
            fd = random.choice(C.CAMPFIRE_FOOD_POOL)
            mid = C.resolve("materials", fd)
            got = ""
            if mid in C.MATERIALS:
                db.add_item(group_id, qq_id, mid, {"name": C.display("materials", mid), "type": "材料", "stackable": True, "price": C.MATERIALS[mid]["price"]})
                got = C.display("materials", mid)
            return (f"{icon} 【{pname}】你在{loc}的篝火旁坐下烤火。\n"
                    f"❤️ 恢复 {hp_gain} 生命！💙 恢复 {mp_gain} 魔力！\n"
                    f"🍖 篝火上还烤着一份{got}，顺手带走了。")
        # 神龛：随机 buff（攻击/防御/速度 +10% 持续 5 次战斗）
        if eff == "buff":
            buffs = [("攻击", "atk"), ("防御", "def"), ("速度", "spd")]
            bname, bkey = random.choice(buffs)
            db.set_event_state(f"poi_buff_{group_id}_{qq_id}", json.dumps({"stat": bkey, "mult": 1.10, "left": 5}))
            return (f"{icon} 【{pname}】你向{loc}的神龛虔诚祈愿，石像仿佛亮了一瞬。\n"
                    f"✨ 获得祝福：{bname}＋10%(持续 5 次战斗)！")
        # 草药丛：1-2 份炼金材料
        if eff == "herb":
            # v101.4：草药丛材料池数据化 → data/poi_pools.py HERB_POOL
            got = []
            for _ in range(random.randint(1, 2)):
                h = random.choice(C.HERB_POOL)
                mid = C.resolve("materials", h)
                if mid in C.MATERIALS:
                    db.add_item(group_id, qq_id, mid, {"name": C.display("materials", mid), "type": "材料", "stackable": True, "price": C.MATERIALS[mid]["price"]})
                    got.append(C.display("materials", mid))
            return (f"{icon} 【{pname}】你在{loc}的草丛里仔细翻找，采到了一些好材料。\n"
                    f"🎒 获得：{'、'.join(got)}！")
        # 可疑包裹：金币 / 装备 / 陷阱
        if eff == "loot":
            r = random.random()
            if r < 0.6:
                gold = random.randint(20, 80) + player["level"] * 3
                db.update_player(group_id, qq_id, gold=player["gold"] + gold)
                return (f"{icon} 【{pname}】你打开{loc}路边的可疑包裹——里面是金币！\n"
                        f"💰 获得 {gold} 金币！")
            if r < 0.85:
                bp = C.roll_blueprint(max(1, player["level"]))
                # v101.25 #293：探索掉落已学图纸不再重复入包——与战斗掉落同款折算
                # （playtest round66+ 抓包：探索反复掉落已学图纸）
                _learned = player.get("learned_blueprints") or []
                if bp.get("blueprint_for") in _learned:
                    _bpq = bp.get("quality", "white")
                    _pages = {"white": 1, "green": 1, "blue": 2, "purple": 4, "orange": 6}.get(_bpq, 1)
                    db.add_item(group_id, qq_id, "mat_tu_zhi_can_ye", {
                        "name": "图纸残页", "type": "材料", "stackable": True, "price": 10}, count=_pages)
                    return (f"{icon} 【{pname}】包裹里卷着一张泛黄的图纸……{bp['name']}！\n"
                            f"📜 这张图纸你已经学会了，化作 {_pages} 张图纸残页（『出售 图纸残页』变现）")
                db.add_item(group_id, qq_id, f"eq_{_uuid.uuid4().hex[:8]}", bp)
                return (f"{icon} 【{pname}】包裹里卷着一张泛黄的图纸：{bp['name']}！\n"
                        f"📜 看来是某位锻造师遗失的手稿。")
            dmg = int(player["max_hp"] * 0.10) + 5
            new_hp = max(1, player["hp"] - dmg)
            db.update_player(group_id, qq_id, hp=new_hp)
            # #256: 陷阱触发文案带先兆（包裹缝隙的寒光）——此前无任何提示直接扣血
            return (f"💥 【{pname}】包裹的缝隙里隐约闪过一道金属寒光——你还没来得及缩手，一只发条咬人夹弹了出来！\n"
                    f"你被夹了一下，损失 {dmg} 生命(当前 ❤️ {new_hp}/{player['max_hp']})")
        # 符文石：图鉴/隐藏线索
        if eff == "rune":
            from ..data.pois import RUNE_POOL
            txt = random.choice(RUNE_POOL)
            db.set_talk_flag(group_id, qq_id, "poi_rune_read", "read_rune")
            return (f"{icon} 【{pname}】你伸手轻触{loc}的符文石，碑面泛起幽光。\n"
                    f"📖 {txt}")
        # 鱼群聚集：免费垂钓次数
        if eff == "fish":
            db.set_event_state(f"poi_fish_{group_id}_{qq_id}", json.dumps({"ts": time.time()}))
            return (f"{icon} 【{pname}】水面泛起细密的涟漪，鱼群正聚在{loc}的水面下！\n"
                    f"🎣 你赶紧甩杆——『垂钓』吧，这次不消耗次数(30 分钟内有效)！")
        # 神秘字条：隐藏线索
        if eff == "note":
            from ..data.pois import NOTE_POOL
            txt = random.choice(NOTE_POOL)
            db.set_talk_flag(group_id, qq_id, "poi_note_found", "found_note")
            return (f"{icon} 【{pname}】你摘下{loc}树干上的字条，墨迹已有些褪色。\n"
                    f"📜 {txt}")
        # v87.9 风景 POI：纯氛围观景（无数值收益）
        if eff == "sight":
            from ..data.pois import SIGHT_POOL
            txt = random.choice(SIGHT_POOL)
            return (f"{icon} 【{pname}】你停住脚步，抬头望向{loc}的风景。\n"
                    f"🌄 {txt}")
        return f"{icon} 【{pname}】你打量了一下{loc}的{poi.get('desc', '这处探索点')}，似乎没什么特别的。"

    def _handle_inst_poi(self, group_id, qq_id, st, poi) -> str:
        """v87.2 副本层内联 POI 效果结算（29 章 13.3）。

        宝箱/补给/遗骸→loot；篝火→回血；石碑→lore+解锁；机关→effect；
        陷阱→可拆解（有石碑线索）或全队受伤。st 为副本战斗状态（含 POI used 记录）。
        """
        logs = []
        sidx = st["stage_idx"]
        pid = poi.get("id", "")
        ptype = poi.get("type", "")
        pname = poi.get("name", "")
        # 需要前置条件（need）
        need = poi.get("need") or {}
        if need:
            if need.get("poi_read") and not st.get("poi_unlocks", {}).get(need["poi_read"]):
                return f"🔒 {pname}纹丝不动——需要先找到某种启示/线索。"
            if need.get("unlock") and not st.get("poi_unlocks", {}).get(need["unlock"]):
                return f"🔒 {pname}还没准备好——似乎缺少某样东西。"
        # 宝箱 / 补给 / 遗骸：给 loot
        if ptype in ("chest", "supply", "corpse"):
            loot = poi.get("loot") or {}
            gold = loot.get("gold", 0)
            mats = loot.get("materials") or []
            p = self._player(group_id, qq_id)
            if gold > 0 and p:
                db.update_player(group_id, qq_id, gold=p["gold"] + gold)
                logs.append(f"💰 你从{pname}里摸出了 {gold} 金币！")
            for mn in mats:
                mid = C.resolve("materials", mn)
                if mid in C.MATERIALS:
                    mname = C.display("materials", mid)
                    db.add_item(group_id, qq_id, mid, {
                        "name": mname, "type": "材料", "stackable": True,
                        "price": C.MATERIALS[mid]["price"],
                    })
                    logs.append(f"🎒 拾取：{mname}")
            self._mark_poi_used(st, sidx, pid)
            head = f"💀 你蹲下搜刮{pname}……" if ptype == "corpse" else f"📦 {pname}："
            return "\n".join([head] + logs)
        # 篝火：回血
        if ptype == "campfire":
            for m in st["members"]:
                if not st["alive"].get(str(m), True):
                    continue
                snap = st["players"].get(str(m), {})
                if snap.get("hp") is not None:
                    heal = max(1, int(snap.get("max_hp", snap["hp"]) * 0.2))
                    snap["hp"] = min(snap.get("max_hp", snap["hp"]), snap["hp"] + heal)
                    logs.append(f"🔥 {snap.get('name', m)} 在{pname}旁烤火，恢复 {heal} 点生命！")
            self._mark_poi_used(st, sidx, pid)
            return "\n".join(logs)
        # 石碑：读 lore（可反复读，不标 used；effect.unlock 记录）
        if ptype == "rune_stone":
            lore = poi.get("lore", "碑文模糊不清，似乎被岁月磨平了。")
            logs.append(f"🗿 你阅读{pname}：")
            logs.append(f"  “{lore}”")
            eff = poi.get("effect") or {}
            if eff.get("unlock"):
                st.setdefault("poi_unlocks", {})[eff["unlock"]] = True
                logs.append("✨ 碑文的内容似乎触发了什么……(某个机关被解锁了！)")
            if eff.get("avoid_trap"):
                st.setdefault("poi_unlocks", {})[f"avoid_{eff['avoid_trap']}"] = True
                logs.append("✨ 你记住了避开陷阱的路线。")
            if eff.get("boss_buff"):
                st["boss_buff_next"] = True
                logs.append("✨ 风神的祝福涌入体内——Boss 战前将获得速度加持！")
            return "\n".join(logs)
        # 机关：按 effect 处理
        if ptype == "mechanism":
            eff = poi.get("effect") or {}
            desc = poi.get("desc", f"你扳动了{pname}。")
            logs.append(f"⚙️ {desc}")
            if eff.get("open_secret"):
                st["stage_secret_found"] = True
                logs.append("🔓 隐藏房间出现了！『副本地图』查看详情。")
            if eff.get("skip_elite"):
                st["skip_elite_next"] = True
                logs.append("🧭 机关打通了一条捷径——下一层的精英被绕开了！")
            if eff.get("skip_wave"):
                st["skip_wave_next"] = True
                logs.append("🧭 援兵被引开了一部分——下一层的敌人减少了！")
            if eff.get("unlock"):
                st.setdefault("poi_unlocks", {})[eff["unlock"]] = True
                logs.append("✨ 机关启动，某种封锁被解除了！")
            self._mark_poi_used(st, sidx, pid)
            return "\n".join(logs)
        # 陷阱：可拆解（有石碑线索）或踩中受伤
        if ptype == "trap":
            if st.get("poi_unlocks", {}).get(f"avoid_{pid}"):
                self._mark_poi_used(st, sidx, pid)
                return f"⚠️ 你记得石碑上的提示，小心地拆除了{pname}！"
            logs.append(f"⚠️ 你触发了{pname}！全队受到 10% 最大生命的伤害！")
            for m in st["members"]:
                if not st["alive"].get(str(m), True):
                    continue
                snap = st["players"].get(str(m), {})
                if snap.get("hp") is not None:
                    dmg = max(1, int(snap.get("max_hp", snap["hp"]) * 0.1))
                    snap["hp"] = max(0, snap["hp"] - dmg)
                    if snap["hp"] <= 0:
                        st["alive"][str(m)] = False
                        logs.append(f"💀 {snap.get('name', m)} 被陷阱击倒了！")
                    else:
                        logs.append(f"❤️ {snap.get('name', m)} 剩余 {snap['hp']}/{snap['max_hp']}")
            self._mark_poi_used(st, sidx, pid)
            return "\n".join(logs)
        return f"你检查了{pname}，没发现特别之处。"

    @filter.regex(r"^(?:\[At:\d+\]\s*)?攻击(?:\s*|$)")
    @require_player()

    async def attack(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        # 带参 → PVP 发起（『攻击 @QQ』『攻击 QQ』『攻击 名字』）
        target_arg = self._strip_cmd(event, "攻击").strip()
        if target_arg:
            async for _r in self._pvp_start(event, group_id, qq_id, player, target_arg):
                yield _r
            return
        battle = db.get_battle(group_id, qq_id)
        if not battle:
            inst_row = self._instance_battle_for(group_id, qq_id)
            if inst_row:
                battle = inst_row
        if not battle:
            yield event.plain_result("你附近没有敌人！输入『探索』寻找敌人～")
            return
        if battle["state"].get("type") == "instance":
            async for _r in self._instance_act(event, group_id, qq_id, player, battle["state"], "attack", None):
                yield _r
            return
        if battle["state"].get("type") == "pvp":
            if self._pvp_handle_timeout(battle, group_id, qq_id):
                yield event.plain_result("⏰ PVP 战斗超过 5 分钟无人行动，自动解除！")
                return
            async for _r in self._pvp_act(event, group_id, qq_id, player, battle["state"], "attack", None):
                yield _r
            return
        b = BT.Battle.from_state(battle["state"])
        # v94.2 体力：每次攻击扣 1（普通/世界Boss通用；instance/pvp 已在上方分流）
        _ok, _st = self._spend_stamina(group_id, qq_id, 1, player, "攻击")
        if not _ok:
            if b.enemy.get("is_boss"):
                # v95.20 #101：Boss 战无法逃跑，体力耗尽=被困战斗——提示必须说清出路
                yield event.plain_result(_st + "\n👑 Boss 战无法逃跑！『防御』不耗体力可拖延等待自然恢复，或吃食物(『使用 <食物>』)立即恢复～")
            else:
                yield event.plain_result(_st + "\n🍖 战斗中『使用 <食物>』恢复体力继续战斗，或『逃跑』脱离战斗～")
            return
        if b.btype == "worldboss":
            async for _r in self._worldboss_act(event, group_id, qq_id, player, b, "attack", None):
                yield _r
            return
        logs, ended = b.player_turn("attack", None, player)
        db.update_player(group_id, qq_id, hp=player["hp"], mp=player["mp"], max_hp=player["max_hp"], max_mp=player["max_mp"])
        if ended:
            if b.result == "victory":
                for _r in self._handle_victory(event, group_id, qq_id, player, b.enemy, "\n".join(logs)):
                    yield _r
                return
            if b.result == "defeat":
                for _r in self._handle_defeat(event, group_id, qq_id, player, b.enemy, "\n".join(logs)):
                    yield _r
                return
            if b.result == "fled":
                self._unlock_battle(group_id, qq_id)
                db.clear_battle(group_id, qq_id)
                yield event.plain_result("\n".join(logs))
                return
        # 保存战斗状态（v9）
        db.save_battle(group_id, qq_id, b.to_state())
        monster = b.enemy
        result = "\n".join(logs)
        yield event.plain_result(
            f"{result}\n━━━━━━━━━━━━\n"
            f"{self._battle_footer(player, b, monster)}"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?技能(?!详情|学习|升级|洗点|栏)(?:[\s\S]*)$")
    @require_player()

    async def skill(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        skill_name = self._strip_cmd(event, "技能")
        player = self._player(group_id, qq_id)
        # v52 Build 懒迁移：技能栏全空的老玩家，自动把已学技能装进前几格
        bar = db.get_skill_bar(qq_id)
        if not any(bar or []):
            learned = [C.display("skills", s) for s in (player.get("learned_skills") or []) if s]
            if learned:
                new_bar = list(learned[:6])
                while len(new_bar) < 6:
                    new_bar.append(None)
                db.set_skill_bar(qq_id, new_bar)
                bar = new_bar
        skill_name = skill_name.strip()
        parts = skill_name.split()
        first = parts[0] if parts else ""
        # 无参 → 技能系统面板
        if not skill_name:
            yield event.plain_result(self._skill_panel(player))
            return
        # 『技能 学习 <名称>』委托给学习逻辑
        if first == "学习" and len(parts) >= 2:
            yield event.plain_result(self._skill_learn_msg(group_id, player, "".join(parts[1:])))
            return
        # 『技能 列表 <页>』→ 技能列表（翻页，每页10带序号），支持免空格『技能列表2』
        if first.startswith("列表") or first.startswith("list"):
            rest = first[2:] if first.startswith("列表") else first[4:]
            page = 1
            if rest.isdigit():
                page = int(rest)
            elif len(parts) >= 2 and parts[1].isdigit():
                page = int(parts[1])
            yield event.plain_result(self._skill_list_page(player, page))
            return
        # 『技能 <数字>』→ 技能栏槽位（v52：必须已设置，不再 fallback 全列表）
        if skill_name.isdigit():
            idx = int(skill_name)
            bar = db.get_skill_bar(qq_id)
            if 1 <= idx <= 6 and bar and idx <= len(bar) and bar[idx - 1]:
                skill_name = bar[idx - 1]
            else:
                yield event.plain_result(
                    f"技能栏 {idx} 号位是空的！『技能栏』查看，『设置技能 {idx} <技能名>』配置后才能在战斗中使用～"
                )
                return
        # 其他 → 战斗中施放
        battle = db.get_battle(group_id, qq_id)
        if not battle:
            inst_row = self._instance_battle_for(group_id, qq_id)
            if inst_row:
                battle = inst_row
        if not battle:
            # v101.25 #300：治疗类技能脱战可直接施放（回复生命），不再误导"找敌人"。
            # 战斗外治疗不要求技能栏配置（技能栏是战斗配置），但必须已学会。
            info = E.skill_info(player["class_name"], skill_name)
            if info and info.get("kind") == "治疗" and E.is_skill_learned(
                player["class_name"], player["level"], skill_name, player.get("learned_skills", [])
            ):
                if player["mp"] < info["mp"]:
                    yield event.plain_result("💙 魔力不足！休息一下或使用魔力药水吧～")
                    return
                if player.get("hp", 0) >= player.get("max_hp", 1):
                    yield event.plain_result(f"你精神饱满，不需要治疗～(当前 {player['hp']}/{player['max_hp']})")
                    return
                st = E.player_final_stats(player["class_name"], player["level"],
                                          player.get("equipment", {}), player.get("class_tier", 0),
                                          player.get("attributes"), player.get("evolve_path", 0),
                                          self._title_bonus(group_id, qq_id), player.get("race"))
                # 与 battle.py _skill_heal 同款结算：power<1 按 max_hp 百分比，power>=1 按魔攻×power
                if info.get("power", 0) < 1:
                    heal = int(player.get("max_hp", 0) * info["power"] * E.skill_power_mult(player["level"], info))
                else:
                    heal = int(st["matk"] * info["power"] * E.skill_power_mult(player["level"], info))
                pv = E.passive_skills_learned(player["class_name"], player.get("learned_skills", []))
                if "神恩" in pv:
                    heal = int(heal * 1.10)
                new_hp = min(player.get("max_hp", 1), player.get("hp", 0) + heal)
                db.update_player(group_id, qq_id, hp=new_hp, mp=player["mp"] - info["mp"])
                yield event.plain_result(
                    f"✨ 你施展【{skill_name}】，圣光治愈了你 {heal} 点生命！({new_hp}/{player['max_hp']})\n"
                    f"💡 脱战施放不消耗体力～(『使用 <食物>』也能恢复)"
                )
                return
            yield event.plain_result("你附近没有敌人！输入『探索』寻找敌人～(『技能列表』查看技能)")
            return
        skill_name = skill_name.strip()
        info = E.skill_info(player["class_name"], skill_name)
        if not info:
            # v95.25 #145：报错读 learned_skills（v52 后 skills 列不再更新），并引流『技能列表』
            learned = [C.display("skills", s) for s in (player.get("learned_skills") or [])]
            learned_str = "、".join(learned) if learned else "无（『技能列表』查看可学技能）"
            yield event.plain_result(
                f"没有技能『{skill_name}』！你当前的技能：{learned_str}"
            )
            return
        if not E.is_skill_learned(player["class_name"], player["level"], skill_name, player.get("learned_skills", [])):
            need_lv = info["lv"]
            if player["level"] < need_lv:
                yield event.plain_result(
                    f"『{skill_name}』需要 Lv.{need_lv} 才能学习，你才 Lv.{player['level']}！"
                )
            else:
                cost = E.skill_learn_cost_for(player, need_lv)
                yield event.plain_result(
                    f"『{skill_name}』还没学会！『技能学习 {skill_name}』消耗 {cost} 技能点学会后再使用～"
                )
            return
        # v64 被动技能：无需施放，学习后战斗自动生效
        if info.get("kind") == "被动":
            yield event.plain_result(
                f"⚙️ 『{skill_name}』是被动技能，学会后战斗自动生效，无需施放！\n"
                f"『技能列表』查看效果，『技能详情 {skill_name}』看说明～"
            )
            return
        # v52 Build 系统：战斗中只能使用技能栏里设置的技能
        bar = db.get_skill_bar(qq_id)
        if skill_name not in (bar or []):
            yield event.plain_result(
                f"『{skill_name}』没放进技能栏！『技能栏』查看，『设置技能 1 {skill_name}』(或任意空槽)配置后才能在战斗中使用～\n"
                f"💡 想快速搭配？试试『流派』一键配置技能组合！"
            )
            return
        if player["mp"] < info["mp"]:
            yield event.plain_result("💙 魔力不足！休息一下或使用魔力药水吧～")
            return
        if battle["state"].get("type") == "instance":
            async for _r in self._instance_act(event, group_id, qq_id, player, battle["state"], "skill", skill_name):
                yield _r
            return
        b = BT.Battle.from_state(battle["state"])
        if battle["state"].get("type") == "pvp":
            if self._pvp_handle_timeout(battle, group_id, qq_id):
                yield event.plain_result("⏰ PVP 战斗超过 5 分钟无人行动，自动解除！")
                return
            async for _r in self._pvp_act(event, group_id, qq_id, player, battle["state"], "skill", skill_name):
                yield _r
            return
        # v94.2 体力：施放技能扣 1（instance/pvp 已在上方分流）
        _ok, _st = self._spend_stamina(group_id, qq_id, 1, player, "施放技能")
        if not _ok:
            if b.enemy.get("is_boss"):
                # v95.20 #101：Boss 战无法逃跑，体力耗尽=被困战斗——提示必须说清出路
                yield event.plain_result(_st + "\n👑 Boss 战无法逃跑！『防御』不耗体力可拖延等待自然恢复，或吃食物(『使用 <食物>』)立即恢复～")
            else:
                yield event.plain_result(_st + "\n🍖 战斗中『使用 <食物>』恢复体力继续战斗，或『逃跑』脱离战斗～")
            return
        if b.btype == "worldboss":
            async for _r in self._worldboss_act(event, group_id, qq_id, player, b, "skill", skill_name):
                yield _r
            return
        logs, ended = b.player_turn("skill", skill_name, player)
        db.update_player(group_id, qq_id, hp=player["hp"], mp=player["mp"], max_hp=player["max_hp"], max_mp=player["max_mp"])
        if ended:
            if b.result == "victory":
                for _r in self._handle_victory(event, group_id, qq_id, player, b.enemy, "\n".join(logs)):
                    yield _r
                return
            if b.result == "defeat":
                for _r in self._handle_defeat(event, group_id, qq_id, player, b.enemy, "\n".join(logs)):
                    yield _r
                return
        db.save_battle(group_id, qq_id, b.to_state())
        monster = b.enemy
        result = "\n".join(logs)
        yield event.plain_result(
            f"{result}\n━━━━━━━━━━━━\n"
            f"{self._battle_footer(player, b, monster)}"
        )

    def _skill_panel(self, player: dict) -> str:
        """技能系统面板(无参『技能』)"""
        cls = player["class_name"]
        cls_info = C.CLASSES.get(cls, {})
        total = len(E._sk_table(cls))
        learned = player.get("learned_skills", [])
        # v101.20：已学导师专属技能计入总数（避免"已学>总数"怪相）
        _tutor = (C.TUTOR_SKILLS or {}).get(cls, {}) or {}
        _tutor_learned = sum(1 for _sid in _tutor if _sid in [C.resolve("skills", s) for s in learned if s])
        total += _tutor_learned
        have = len(learned)
        pts = player.get("skill_points", 0)
        lines = [
            f"⚔️ 【技能系统】 {cls_info.get('icon','')}{C.display('classes', cls)} Lv.{player['level']}",
            "━━━━━━━━━━━━",
            f"💡 技能点：{pts}(每升 1 级＋1)",
            f"✅ 已学：{have}/{total} ｜ 🔒 未学：{total - have}",
            "━━━━━━━━━━━━",
            "『技能列表』查看全部技能(可翻页)",
            "『技能详情 <名称/序号>』查看单个技能",
            "『技能学习 <名称>』消耗技能点学会技能",
            "『技能升级 <名称>』消耗技能点升级(满级 Lv.5)",
            "『技能栏』查看 / 『设置技能 <槽位> <技能名>』配置快捷栏",
            "『技能洗点』重置技能(500金币返还技能点)",
            "战斗中『技能 <槽位>』或『技能 <技能名>』施放",
            "⚙️ 被动技能无需施放，学会后战斗自动生效(『技能列表』可见<被动>标签)",
        ]
        return "\n".join(lines)

    def _branch_skills_for(self, player: dict) -> dict:
        """玩家已解锁分支的专属技能表 {技能名: info}(v26：按 tier 升序合并，只含已转职分支)"""
        cls = C.BRANCH_SKILLS.get(player["class_name"], {})
        if isinstance(cls, dict) and "branches" in cls:
            cls = cls["branches"]
        tier = player.get("class_tier", 0)
        path = player.get("evolve_path", 0)
        out = {}
        if not path or tier <= 0:
            return out
        for t in sorted(cls.keys()):
            if t > tier:
                continue
            branches = cls[t]
            names = list(branches.keys())
            idx = 0 if path == 1 else 1
            if idx < len(names):
                out.update(branches[names[idx]])
        return out

    def _player_skill_table(self, player: dict) -> dict:
        """玩家完整技能表：基础职业技能 + 已解锁分支专属技能（基础在前，序号稳定）

        v48：PLAYER_SKILLS[cls] 结构为 {"name": 中文名, "skills": {技能表}}
        """
        cls_skills = C.PLAYER_SKILLS.get(player["class_name"], {})
        if isinstance(cls_skills, dict) and "skills" in cls_skills:
            table = dict(cls_skills["skills"])
        else:
            table = dict(cls_skills)
        table.update(self._branch_skills_for(player))
        # v101.20 职业导师专属技能：未学会不进列表（保持神秘感），学会后追加（序号稳定在尾部）
        learned = player.get("learned_skills", [])
        _tutor = (C.TUTOR_SKILLS or {}).get(player["class_name"], {}) or {}
        for _sid, _info in _tutor.items():
            if _sid in [C.resolve("skills", s) for s in learned if s]:
                table[_sid] = _info
        return table

    # v56.3：技能功能标签（<kind><功能> 双标签，参考鱼鱼排版示例）
    _MECH_CN = {"rage": "狂暴", "burn": "灼烧", "freeze": "冰冻", "poison": "中毒", "mark": "标记",
                "shadow": "影袭", "chi": "气力", "wind": "风印", "judge": "审判", "bless": "神恩",
                "iron": "铁壁", "shield": "圣盾", "arcane": "奥术", "cleanse": "净化", "stun": "眩晕",
                "spd_down": "减速", "mark_burst": "引爆", "arcane_burst": "奥爆",
                "spellblade": "魔刃", "spellblade_burst": "魔爆", "spellblade_meteor": "陨星",
                "spellblade_storm": "风暴", "spellblade_surge": "魔涌"}
    _EFFECT_CN = {"atk_up": "攻击", "def_up": "防御", "matk_up": "魔攻", "spd_up": "速度", "crit_up": "暴击",
                  "atk_up_strong": "强攻", "matk_up_strong": "强魔攻", "mon_atk_down": "威压", "lifesteal": "吸血",
                  "counter": "反击", "rage_burst": "爆发", "burn_burst": "引爆", "bless_shield": "护盾"}

    def _skill_tag(self, info: dict) -> str:
        """功能标签：被动优先，其次 effect/mech/cond"""
        if info.get("kind") == "被动":
            return "被动"
        if info.get("effect"):
            return self._EFFECT_CN.get(info["effect"], info["effect"])
        if info.get("mech"):
            return self._MECH_CN.get(info["mech"], info["mech"])
        if info.get("cond"):
            label = info["cond"].get("label", "")
            return label[:2] if label else ""
        return ""

    def _skill_list_page(self, player: dict, page: int = 1) -> str:
        """技能列表翻页(每页 5 条带序号，序号与『技能 N』释放一致；未学显示 Lv.0)"""
        skills = self._player_skill_table(player)
        skill_items = list(skills.items())
        learned = player.get("learned_skills", [])
        # 分支技能名 → 分支名标记
        branch_tags = {}
        for sname in skills:
            owner = E.branch_skill_owner(player["class_name"], sname)
            if owner:
                branch_tags[sname] = owner[1]
        page_items, pages, page = self._page_items(skill_items, page, per_page=5)
        lines = ["技能列表"]
        lines.append("━━━━━━━━━━━━")
        for i, (sname, info) in enumerate(page_items, (page - 1) * 5 + 1):
            # v49：key 是技能 ID（sk_xxx），显示用中文名
            disp_name = info.get("name", sname) if isinstance(info, dict) else sname
            learned_now = E.is_skill_learned(player["class_name"], player["level"], sname, learned)
            if learned_now:
                slv = E.skill_level_of(player, sname)  # #259：兼容 skill_levels key 为中文名（store 读库转换）
                lv_str = f"Lv.{slv}/{E.skill_max_level(info)}"  # v56.4：每技能独立满级
            else:
                slv = 0  # v56.3：未学显示 0 级
                need_lv = info.get("lv", 99)
                if player["level"] >= need_lv:
                    # v95.7 #36：已达解锁等级 → 显示"可学(X技能点)"而非静态"未学(Lv.X解锁)"
                    # v95.7 修复：cost 用 skill_learn_cost_for（含种族折扣），与『技能学习』实际扣点一致
                    cost = E.skill_learn_cost_for(player, need_lv)
                    lv_str = f"可学({cost}技能点)"
                else:
                    lv_str = f"未学(Lv.{need_lv}解锁)"  # v95.4：标注解锁等级
            tags = [info.get("kind", "")]
            ftag = self._skill_tag(info)
            if ftag and ftag != info.get("kind", ""):
                tags.append(ftag)
            if info.get("team"):
                tags.append("团队")  # v56.4：团队标记放标签，不进描述
            if sname in branch_tags:
                tags.append(branch_tags[sname])
            tag_str = "".join(f"<{t}>" for t in tags)
            # v101.25d 技能列表排版（鱼鱼拍板模板）：编号行 / 标签行 / 描述行 / 消耗行，
            # 每条之间 ━━ 分隔线，参考属性面板四维的分区感
            lines.append(f"{i}.{disp_name} [{lv_str}]")
            if tag_str:
                lines.append(f"  · {tag_str}")
            lines.append(f"  · {info['desc']}")
            _cost = []
            _mp = info.get("mp", 0)
            if _mp:
                _cost.append(f"{_mp} 魔力")
            _rc = info.get("res_cost") or {}
            _rd = E.core_resource_def(player["class_name"])
            _rcn = _rd.get("name", "") if _rd else ""
            for _k, _v in _rc.items():
                _cn = _rcn or _k
                _cost.append(f"{_cn} -{_v}")
            _rg = info.get("res_gain") or 0
            if _rg:
                _cost.append(f"{_rcn or '资源'} +{_rg}")
            _cd = info.get("cd") or 0
            if _cd:
                _cost.append(f"冷却 {_cd} 回合")
            if _cost:
                lines.append(f"  · 消耗：{' ｜ '.join(_cost)}")
            else:
                lines.append("  · 消耗：免费")
            lines.append("━━━━━━━━━━━━")
        lines.append(f"页数：{page}/{pages}")
        if pages > 1 and page < pages:
            lines.append(f"『技能列表 {page+1}』看下一页")
        lines.append("『技能学习 <名称>』消耗技能点学会；战斗中『技能 <槽位>』或『技能 <名称>』施放")
        return "\n".join(lines)

    @filter.regex(r"^(?:\[At:\d+\]\s*)?防御(?:\s*|$)")
    @require_player()
    @require_battle()

    async def defend(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        battle = db.get_battle(group_id, qq_id)
        if not battle:
            inst_row = self._instance_battle_for(group_id, qq_id)
            if inst_row:
                battle = inst_row
        if battle["state"].get("type") == "instance":
            async for _r in self._instance_act(event, group_id, qq_id, player, battle["state"], "defend", None):
                yield _r
            return
        b = BT.Battle.from_state(battle["state"])
        if battle["state"].get("type") == "pvp":
            if self._pvp_handle_timeout(battle, group_id, qq_id):
                yield event.plain_result("⏰ PVP 战斗超过 5 分钟无人行动，自动解除！")
                return
            async for _r in self._pvp_act(event, group_id, qq_id, player, battle["state"], "defend", None):
                yield _r
            return
        if b.btype == "worldboss":
            async for _r in self._worldboss_act(event, group_id, qq_id, player, b, "defend", None):
                yield _r
            return
        logs, ended = b.player_turn("defend", None, player)
        db.update_player(group_id, qq_id, hp=player["hp"], mp=player["mp"], max_hp=player["max_hp"], max_mp=player["max_mp"])
        if ended and b.result == "defeat":
            for _r in self._handle_defeat(event, group_id, qq_id, player, b.enemy, "\n".join(logs)):
                yield _r
            return
        db.save_battle(group_id, qq_id, b.to_state())
        monster = b.enemy
        result = "\n".join(logs)
        yield event.plain_result(
            f"{result}\n━━━━━━━━━━━━\n"
            f"{self._battle_footer(player, b, monster)}"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?逃跑(?:\s*|$)")
    @require_player()
    @require_battle()

    async def flee(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        battle = db.get_battle(group_id, qq_id)
        if not battle:
            inst_row = self._instance_battle_for(group_id, qq_id)
            if inst_row:
                battle = inst_row
        if battle["state"].get("type") == "instance":
            yield event.plain_result("🏰 副本 Boss 锁定了战场，无法逃跑！背水一战吧！")
            return
        if battle["state"].get("type") == "pvp":
            # PVP 逃跑 = 脱离战斗（双方解除，互不追究），避免被锁死/被骚扰
            st = battle["state"]
            opp_qq = st["attacker"]["qq_id"] if str(st["defender"]["qq_id"]) == str(qq_id) else st["defender"]["qq_id"]
            # 攻击方获得袭击 CD（无论谁逃跑，防反复骚扰）
            self._set_pvp_cd(st.get("attacker_qq", st["attacker"]["qq_id"]))
            self._unlock_battle(group_id, qq_id)
            db.clear_battle(group_id, qq_id)
            self._unlock_battle(group_id, opp_qq)
            db.clear_battle(group_id, opp_qq)
            yield event.plain_result("💨 你脱离了 PVP 战斗！双方原地休整，互不追究。")
            return
        if battle["state"].get("enemy", {}).get("is_boss"):
            yield event.plain_result("👑 Boss 锁定了你，无法逃跑！背水一战吧！")
            return
        b = BT.Battle.from_state(battle["state"])
        logs, ended = b.player_turn("flee", None, player)
        db.update_player(group_id, qq_id, hp=player["hp"], mp=player["mp"], max_hp=player["max_hp"], max_mp=player["max_mp"])
        if ended:
            if b.result == "fled":
                self._unlock_battle(group_id, qq_id)
                db.clear_battle(group_id, qq_id)
                yield event.plain_result("\n".join(logs))
                return
            if b.result == "defeat":
                for _r in self._handle_defeat(event, group_id, qq_id, player, b.enemy, "\n".join(logs)):
                    yield _r
                return
        db.save_battle(group_id, qq_id, b.to_state())
        monster = b.enemy
        result = "\n".join(logs)
        yield event.plain_result(
            f"{result}\n"
            f"你：❤️ {player['hp']}/{player['max_hp']} 💙 {player['mp']}/{player['max_mp']}"
        )

    # ---------------- 战斗状态展示（v59） ----------------
    # 玩家 buff key → 显示名（v63 加 眩晕/冻结/沉默 控制状态）
    _P_BUFF_NAMES = {
        "atk_up": "⚔️攻击↑", "atk_up_strong": "⚔️攻击↑↑", "matk_up": "🔮魔攻↑",
        "matk_up_strong": "🔮魔攻↑↑", "def_up": "🛡️防御↑", "spd_up": "💨速度↑",
        "crit_up": "💥暴击↑", "counter": "🔄反击", "mon_atk_down": "😵敌攻↓",
        "food_atk_up": "🍖攻↑", "food_def_up": "🍖防↑", "food_spd_up": "🍖速↑",
        "food_crit_up": "🍖暴击↑", "food_matk_up": "🍖魔攻↑",
        "stun": "🌀眩晕", "freeze": "❄️冻结", "silence": "🤐沉默",
    }
    # 敌方状态 key → 显示名（v63 加 眩晕/沉默）
    _E_BUFF_NAMES = {
        "freeze": "❄️冻结", "stun": "🌀眩晕", "silence": "🤐沉默",
        "mon_atk_down": "😵攻↓", "mon_atk_up": "⚔️攻↑",
        "mon_atk_up_strong": "⚔️攻↑↑", "mon_def_up": "🛡️防↑", "def_down": "💔破甲",
        "spd_down": "💨减速", "poison": "☠️中毒", "mark": "🎯标记", "burn": "🔥灼烧",
        "summon": "👥召唤",
    }
    # 玩家叠层 key → 显示名
    _STACK_NAMES = {
        "burn": "🔥灼烧", "poison": "☠️毒层", "rage": "🔥狂暴", "shadow": "🌑影袭",
        "chi": "🌀气力", "judge": "⚖️审判", "mark": "🎯标记", "wind": "💨风印",
        "iron": "🪷金身", "shield": "🛡️圣盾", "bless": "✨神恩",
    }

    def _status_line(self, player: dict, b) -> str:
        """战斗状态行：玩家 buff/叠层 + 敌方状态。无状态返回空串。"""
        parts = []
        # 玩家 buff（p_buffs 回合数 >0）
        pbuf = []
        for k, v in (b.p_buffs or {}).items():
            if v and v > 0 and k in self._P_BUFF_NAMES:
                pbuf.append(f"{self._P_BUFF_NAMES[k]}(剩{v}回合)")  # #244c: ×N 是回合数，标注避免误读倍率
        # 玩家叠层（v59：叠层随战斗持久化，读 b.mech_stacks）
        stacks = (b.mech_stacks or {})
        for k, v in stacks.items():
            if v and v > 0 and k in self._STACK_NAMES:
                pbuf.append(f"{self._STACK_NAMES[k]}×{v}")
        # 玩家护盾（v59：随战斗持久化；v101.28d 多来源盾，显示各来源值+剩余回合）
        shields = getattr(b, "p_shields", {}) or {}
        for sname, s in shields.items():
            if (s or {}).get("value", 0) > 0:
                turns = s.get("turns", 0)
                pbuf.append(f"✨护盾{s['value']}" + (f"({turns}回合)" if turns < 999 else ""))
        # 玩家金身减伤（iron 在 stacks 里已显示）
        if pbuf:
            parts.append(f"🛡️你：「{' '.join(pbuf)}」")
        # 敌方状态（e_buffs 回合数 >0）
        ebuf = []
        for k, v in (b.e_buffs or {}).items():
            if v and v > 0 and k in self._E_BUFF_NAMES:
                ebuf.append(f"{self._E_BUFF_NAMES[k]}(剩{v}回合)")  # #244c: 同上，回合数标注
        # 敌方狂暴（v58 mech）
        if b.enemy.get("enraged"):
            ebuf.append("😡狂暴")
        if ebuf:
            parts.append(f"👹敌：「{' '.join(ebuf)}」")
        return "\n".join(parts)

    def _resource_line(self, player: dict, b) -> str:
        """v95.4：核心资源条（怒气/元素亲和/精力/信仰/连击点/气）——反馈：资源体系无界面显示"""
        rd = E.core_resource_def(player["class_name"])
        if not rd:
            return ""
        res = getattr(b, "resources", {}) or {}
        key = rd["key"]
        name = rd.get("name", key)
        if rd.get("type") == "switch":
            cur = E.ELEMENT_CN.get(res.get(key, "fire"), "火")
            return f"🔮 {name}：{cur}系"
        cur = res.get(key, 0)
        cap = rd.get("max", 99)
        return f"⚡ {name}：{cur}/{cap}"

    def _battle_footer(self, player: dict, b, monster: dict) -> str:
        """战斗底部：血蓝 + 状态行(有状态才追加)+ 速度优势提示(v61)"""
        status = self._status_line(player, b)
        lines = [
            f"🐾【{monster['name']}】❤️ {max(0, monster['hp'])}/{monster['max_hp']}",
            f"你：❤️ {player['hp']}/{player['max_hp']} 💙 {player['mp']}/{player['max_mp']}",
        ]
        rl = self._resource_line(player, b)
        if rl:
            lines.append(rl)
        if status:
            lines.append(status)
        # v61：玩家还有剩余额外行动时提示自由出手
        if getattr(b, "p_extra_left", 0) > 0:
            lines.append(f"⚡ 速度优势！你还可以行动 {b.p_extra_left} 次(『攻击』『技能 <名称>』『使用 <道具>』)")
        return "\n".join(lines)

    def _handle_victory(self, event, group_id, qq_id, player, monster, result):
        """击败怪物：经验/金币/掉落/任务进度"""
        self._unlock_battle(group_id, qq_id)
        db.clear_battle(group_id, qq_id)
        exp = monster["exp"]
        gold = monster["gold"]
        # v28 等级差惩罚：打高太多/低太多的怪经验衰减，杜绝一天40级刷法
        diff = monster["lv"] - player["level"]
        if diff > 5:
            # 越级打怪：每高 1 级 -15%，最低剩 10%（等级差≥11 时几乎无收益）
            mult = max(0.10, 1.0 - (diff - 5) * 0.15)
            exp = int(exp * mult)
        elif diff < -5:
            # 低等级怪：碾压无收益，每低 1 级 -20%，最低剩 10%
            mult = max(0.10, 1.0 - (-diff - 5) * 0.20)
            exp = int(exp * mult)
        # 组队经验 +10%
        if db.party_members(group_id, qq_id):
            exp = int(exp * 1.1)
        # 公会经验加成（等级越高加成越多，上限 20%）
        guild_bonus = []
        g = db.guild_get_by_member(qq_id)
        if g:
            gb = min(g["level"] * C.GUILD_CONFIG["exp_bonus_per_level"], C.GUILD_CONFIG["max_bonus"])
            if gb > 0:
                exp = int(exp * (1 + gb))
                guild_bonus.append(f"🏰 公会加成：经验 +{int(gb*100)}%")
        # 宠物经验加成（24 章五：等级/10 上限 50%；饱食度 >0 全额，=0 减半）
        pet_bonus = []
        pet = db.pet_get(qq_id)
        pet = db.pet_decay_satiety(pet)
        if pet:
            pb = min(pet["level"] / 10, 0.5)
            if pet["satiety"] <= 0:
                pb = pb / 2  # 饱食度 =0：经验加成减半
            if pb > 0:
                exp = int(exp * (1 + pb))
                ptag = "🐾 陪伴(饱食度归零，加成减半)" if pet["satiety"] <= 0 else "🐾 陪伴"
                pet_bonus.append(f"{ptag}：经验 +{int(pb*100)}%")
            # 战斗消耗饱食度 -2（先自然衰减再扣战斗消耗）
            db.pet_update(qq_id, satiety=max(0, pet["satiety"] - 2), last_sat_time=pet["last_sat_time"])
            # 宠物分得经验（24 章四：击杀怪宠物分得经验，取怪物基础经验 20%）
            p_gain = max(1, int(monster["exp"] * 0.2))
            p_exp = pet["exp"] + p_gain
            p_lv = pet["level"]
            p_lvup = False
            while p_exp >= C.pet_exp_need(p_lv):
                p_exp -= C.pet_exp_need(p_lv)
                p_lv += 1
                p_lvup = True
            db.pet_update(qq_id, exp=p_exp, level=p_lv)
            if p_lvup:
                pet_bonus.append(f"🎉 宠物升到 Lv.{p_lv}！(Lv.10 解锁宠物技能)" if p_lv >= 10 else f"🎉 宠物升到 Lv.{p_lv}！")
        # v101.13 坐骑 exp_mult：骑乘加成类坐骑战斗经验加成（幽灵马/狮鹫/炎蹄战马）
        mount_bonus = []
        meff = C.mount_effects(player)
        em = float(meff.get("exp_mult", 0) or 0)
        if em > 0:
            exp = int(exp * (1 + em))
            mount_bonus.append(f"🐎 坐骑疾驰：经验 +{int(em*100)}%")
        # 世界事件加成：元素异象 经验金币+50%；兽潮 经验+30% 声望双倍；庆典 金币+50%
        evt_bonus = []
        cur_evt = db.get_world_event()
        if cur_evt:
            if cur_evt["etype"] == "omen":
                exp = int(exp * 1.5); gold = int(gold * 1.5)
                evt_bonus.append("🌧️ 元素异象：收益 +50%")
            elif cur_evt["etype"] == "swarm":
                exp = int(exp * 1.3)
                evt_bonus.append("⚔️ 兽潮：经验 +30%")
            elif cur_evt["etype"] == "festival":
                gold = int(gold * 1.5)
                evt_bonus.append("🎉 庆典：掉落价值 +50%")
        # v87 02 章 7.6：每日运势加成（大吉 经验+10% / 小凶 金币-10%）
        fortune_line = ""
        try:
            import json as _j
            _fstate = db.get_event_state(f"daily_fortune_{group_id}_{qq_id}")
            if _fstate:
                _f = _j.loads(_fstate)
                import datetime as _dt
                if _f.get("date") == _dt.date.today().isoformat():
                    if _f.get("fortune") == "大吉":
                        exp = int(exp * 1.10)
                        fortune_line = "🌟 今日大吉：经验 +10%！"
                    elif _f.get("fortune") == "小凶":
                        gold = int(gold * 0.90)
                        fortune_line = "🌧️ 今日小凶：掉落价值 -10%……"
        except Exception:
            pass
        if fortune_line:
            evt_bonus.append(fortune_line)
        # 任务统计
        db.init_stats(group_id, qq_id)
        if monster.get("is_boss"):
            db.bump_stats(group_id, qq_id, boss_kills=1)
        elif monster.get("is_elite"):
            db.bump_stats(group_id, qq_id, elite_kills=1)
        db.bump_stats(group_id, qq_id, kills=1, day_kills=1)
        # 图鉴记录 + 击杀对应势力声望
        db.bump_bestiary(group_id, qq_id, monster["name"])
        rep_lines = []
        area_key = monster.get("map_area")
        if area_key and area_key in C.AREA_FACTION:
            faction = C.AREA_FACTION[area_key]
            rep_gain = 5 if monster.get("is_boss") else (3 if monster.get("is_elite") else 1)
            # 兽潮事件声望双倍
            cur_evt2 = db.get_world_event()
            if cur_evt2 and cur_evt2["etype"] == "swarm":
                rep_gain *= 2
            db.add_reputation(group_id, qq_id, faction, rep_gain)
            if rep_gain > 1:
                rep_lines.append(f"🏛️ {C.FACTIONS[faction]['icon']} 声望 +{rep_gain}")
        # 掉落（v93 经济改革：怪物永不掉装备——装备走铁匠铺购买 + 图纸锻造）
        drop_equip, drop_bp, _drop_gold, _drop_exp = C.roll_drop(monster["lv"], monster["role"])
        # 阶段九：半身人幸运儿——金币掉落 +15%
        if E.race_stats(player.get("race")).get("gold_bonus"):
            gold = int(gold * (1 + E.race_stats(player.get("race"))["gold_bonus"]))
        drop_lines = []
        if drop_bp:
            # v94 图纸经济：已学过的图纸自动折算图纸残页（普通1/优秀1/稀有2/史诗4/传说6）
            _learned = player.get("learned_blueprints") or []
            if drop_bp.get("blueprint_for") in _learned:
                _bpq = drop_bp.get("quality", "white")
                _pages = {"white": 1, "green": 1, "blue": 2, "purple": 4, "orange": 6}.get(_bpq, 1)
                db.add_item(group_id, qq_id, "mat_tu_zhi_can_ye",
                            {"name": "图纸残页", "type": "材料", "stackable": True, "price": 10},
                            count=_pages)
                drop_lines.append(f"📜 图纸已学会，化作 {_pages} 张图纸残页（『出售 图纸残页』变现）")
            else:
                import uuid
                bp_key = f"eq_{uuid.uuid4().hex[:8]}"
                db.add_item(group_id, qq_id, bp_key, drop_bp)
                # v56.4：掉落提示只显示名字，不把 desc 整段塞进括号（曾漏内部 ID）
                drop_lines.append(f"📜 掉落图纸：{drop_bp['name']}")
        # 材料掉落（v95.7 #45：v23 旧路径与 v93 折算路径重复掉落同一材料 → 删除旧路径，
        # 统一走下方 v93 折算（掉落池优先 + 数量按价值），修复『拾取材料X』+『拾取材料X ×N』双行）
        pet_egg_line = ""
        # v101.11 蛋掉落表数据化（data/pets.py PET_EGG_ROLL，加宠物/改概率不动代码）
        egg_key = None
        for rule in C.PET_EGG_ROLL:
            ok = True
            if rule.get("role") and monster.get("role") != rule["role"]:
                ok = False
            if ok and rule.get("is_elite") and not monster.get("is_elite"):
                ok = False
            if ok and rule.get("is_boss") and not monster.get("is_boss"):
                ok = False
            if ok and rule.get("name_kw") and not any(k in monster.get("name", "") for k in rule["name_kw"]):
                ok = False
            if ok and random.random() < rule.get("rate", 0):
                egg_key = rule["key"]
                break
        if egg_key:
            egg = C.make_pet_egg(egg_key)
            db.add_item(group_id, qq_id, f"petegg_{egg_key}", egg)
            pet_egg_line = f"🥚 咦？【{egg['name']}】从怪物身上掉下来了！『使用 宠物蛋』孵化！"
        # v39 坐骑缰绳掉落（精英/Boss 概率，背包『使用』解锁坐骑）
        mount_line = ""
        mk = C.roll_mount_drop(monster.get("role", ""))
        if mk:
            rein = C.make_mount_rein(mk)
            db.add_item(group_id, qq_id, f"mountrein_{mk}", rein)
            mount_line = f"🐾 战利品里有【{rein['name']}】！『使用 缰绳』驯服坐骑！"
        # v34 符文掉落（精英/Boss 概率 x3，品质越高越稀有，等级随品质浮动）
        # v101.25i5 分层：普通怪只掉稀有；史诗/传说仅精英/Boss（鱼鱼：低级怪爆传说 III 不合理）
        rune_line = ""
        roll = random.random()
        rune_quality = None
        is_elite_boss = monster.get("is_boss") or monster.get("is_elite")
        if is_elite_boss:
            for rq, w in sorted(C.RUNE_DROP.items(), key=lambda x: -x[1]):
                if roll < w * 3:
                    rune_quality = rq
                    break
                roll -= w * 3
        else:
            if roll < C.RUNE_DROP["blue"]:
                rune_quality = "blue"
        if rune_quality:
            cand_runes = [n for n, r in C.RUNES.items() if r["quality"] == rune_quality]
            if cand_runes:
                rname = random.choice(cand_runes)
                r_def = C.RUNES[rname]
                # 等级：稀有 1-2 级，史诗 1-3 级，传说 2-3 级（高等级更稀有）
                if rune_quality == "blue":
                    r_lvl = random.randint(1, 2)
                elif rune_quality == "purple":
                    r_lvl = random.randint(1, 3)
                else:
                    r_lvl = random.randint(2, 3)
                rune_data = C.rune_item(r_def["effect"], r_lvl)
                db.add_item(group_id, qq_id, f"rune_{r_def['effect']}_{r_lvl}", rune_data)
                rune_line = f"💎 掉落了【{rune_data['name']}】！({rune_data['desc']})『附魔 <装备> {rune_data['name']}』使用"
        # v34 符文收益：拾荒(金币+%) / 睿智(经验+%)——直接从已装备读符文
        _rune_effs = {}
        for _slot, _it in (player.get("equipment") or {}).items():
            if _it:
                for _en in _it.get("enchant", []):
                    if _en.get("effect"):
                        _lvl = int(_en.get("lvl", 1) or 1)
                        _rune_effs[_en["effect"]] = max(_rune_effs.get(_en["effect"], 0), _lvl)
        if _rune_effs.get("scavenger"):
            gold = int(gold * (1 + C.rune_value("scavenger", _rune_effs["scavenger"])))
        if _rune_effs.get("exp_bless"):
            exp = int(exp * (1 + C.rune_value("exp_bless", _rune_effs["exp_bless"])))
        # v54 幸运护符：10 分钟内打怪掉落价值 +50%（v93：金币改折算材料后，加成落在材料价值上）
        lucky_line = ""
        if int(player.get("lucky_until") or 0) > int(time.time()):
            gold = int(gold * 1.5)
            lucky_line = "\n🍀 幸运护符生效：掉落价值 +50%！"
        # v93 经济改革：金币不再入账，按 原金币×1.5 折算成 1-2 种可卖材料（怪物掉落池优先，通用池兜底）
        mat_value = int(gold * 1.5)
        if mat_value > 0:
            drop_pool = [m for m in (monster.get("drops") or []) if m and "图纸" not in str(m)]
            if not drop_pool:
                drop_pool = list(("兽肉", "狼皮", "蛇皮", "野猪牙"))
            is_hi = monster.get("is_elite") or monster.get("is_boss")
            picks = random.sample(drop_pool, min(2 if is_hi else 1, len(drop_pool)))
            per_val = mat_value / len(picks)
            for mat_name in picks:
                mid = C.resolve("materials", mat_name)
                if mid not in C.MATERIALS:
                    continue
                mprice = C.MATERIALS[mid].get("price", 0)
                if mprice <= 0:
                    continue
                n = max(1, min(30, round(per_val / mprice)))
                db.add_item(group_id, qq_id, mid,
                            {"name": C.display("materials", mid), "type": "材料",
                             "stackable": True, "price": mprice}, n)
                drop_lines.append(f"🎒 拾取材料：{C.display('materials', mid)} ×{n}（可到城镇商店/铁匠铺出售）")
        # 经验/金币（v93：只入经验，金币已折算成材料）
        # v95.19: 顺带同步 DB max_hp/max_mp 实时值（player 已由 Battle 刷新，防 get_player clamp 误伤）
        # #262: 先更新 player dict 再落库——此前直接写库导致进度条显示旧值、
        #       _rule_fire 的 exp_gain 在旧基数上覆盖 DB（三连胜经验延迟到下一场才入账）
        player["exp"] = int(player.get("exp", 0)) + exp
        db.update_player(group_id, qq_id, exp=player["exp"], max_hp=player["max_hp"], max_mp=player["max_mp"])
        player = self._player(group_id, qq_id)
        # v95.19: 结算面板与战斗内口径一致（DB max_hp/max_mp 是注册/升级快照，换装备后过时）
        try:
            _st = E.player_final_stats(player["class_name"], player["level"], player.get("equipment", {}),
                                       player.get("class_tier", 0), player.get("attributes"),
                                       player.get("evolve_path", 0), player.get("_title_bonus") or {}, player.get("race"))
            player["max_hp"] = int(_st.get("max_hp", player.get("max_hp", 100)))
            player["max_mp"] = int(_st.get("max_mp", player.get("max_mp", C.DEFAULT_MAX_MP)))
        except Exception:
            pass
        # #262: 行为规则(三连胜等)提前到进度条显示前触发——exp_gain 模板会同步 player["exp"]，
        # 进度条与公告口径一致（此前公告在面板之后才写库，玩家感知为经验延迟到下一场）
        _rule_txt = self._rule_fire("battle_win", group_id, qq_id, player,
                                    C.MAP_BY_ID.get(player.get("cur_map"), {}),
                                    {"event": "win", "enemy": monster})
        need = C.exp_to_next(player["level"])
        exp_pct = min(100, int(player["exp"] / need * 100)) if need else 0
        lines = [result, f"🎉 你击败了【{monster['name']}】！",
                 f"✨ 经验 +{exp}",
                 f"📈 经验进度 {player['exp']}/{need} ({exp_pct}%)"]
        if lucky_line:
            lines.append(lucky_line.strip())
        lines += drop_lines
        if rune_line:
            lines.append(rune_line)
        if pet_egg_line:
            lines.append(pet_egg_line)
        if mount_line:
            lines.append(mount_line)
        if rep_lines:
            lines += rep_lines
        if guild_bonus:
            lines += guild_bonus
        if pet_bonus:
            lines += pet_bonus
        if mount_bonus:
            lines += mount_bonus
        if evt_bonus:
            lines += evt_bonus
        # 公会任务推进（每日击杀 5 只；v43 修复：跨天重置而非跳过）
        g2 = db.guild_get_by_member(qq_id)
        if g2:
            import datetime as _dt
            tdate, tprog = db.guild_get_task(g2["gid"], qq_id)
            today = _dt.date.today().isoformat()
            if tdate != today:
                tprog = 0  # 新的一天/新成员：重置进度
            if tprog < C.GUILD_CONFIG["kill_task"]:
                tprog += 1
                db.guild_set_task(g2["gid"], qq_id, today, tprog)
                if tprog >= C.GUILD_CONFIG["kill_task"]:
                    cfg = C.GUILD_CONFIG
                    db.guild_add_exp(g2["gid"], cfg["task_exp"], member_qq=qq_id, contribute=cfg["task_contribute"])
                    db.update_player(group_id, qq_id, gold=player["gold"] + cfg["task_gold"])
                    lines.append(f"🎯 【公会任务完成】击杀 {cfg['kill_task']} 只达成！公会经验 +{cfg['task_exp']} 贡献 +{cfg['task_contribute']} 金币 +{cfg['task_gold']}")
                else:
                    lines.append(f"🎯 公会任务进度 {tprog}/{C.GUILD_CONFIG['kill_task']}")
        # 升级
        player["_title_bonus"] = self._title_bonus(group_id, qq_id)
        lv_logs, player = E.check_player_level_up(group_id, qq_id, player)
        if lv_logs:
            if lines:
                lines.append("")
            lines += lv_logs
            db.update_player(group_id, qq_id, level=player["level"], exp=player["exp"], hp=player["hp"], mp=player["mp"], max_hp=player["max_hp"], max_mp=player["max_mp"], skills=player["skills"], attr_pts=player.get("attr_pts", 0), skill_points=player.get("skill_points", 0), learned_skills=player.get("learned_skills", []))
        # 任务进度
        quest_lines = self._update_quests(group_id, qq_id, monster)
        if quest_lines:
            if lines:
                lines.append("")
            lines += quest_lines
        # 阶段九：成就判定（击杀/等级/精英/Boss/分类怪）
        ach_lines = []
        # v87：隐藏怪击杀累计（成就·传说猎人）
        hm_defeated = set()
        try:
            _hm_st = db.get_event_state(f"hm_defeated_{group_id}_{qq_id}")
            if _hm_st:
                hm_defeated = set(_hm_st.split(",")) if _hm_st else set()
            if monster.get("id") in C.HIDDEN_MONSTERS:
                hm_defeated.add(monster["id"])
                db.set_event_state(f"hm_defeated_{group_id}_{qq_id}", ",".join(sorted(hm_defeated)))
        except Exception:
            pass
        new_achs = C.check_achievements(group_id, qq_id, player, {"defeated_hidden_monsters": hm_defeated})
        for a in new_achs:
            rw_txt = f"\n      🎁 {a['_reward_txt']}" if a.get("_reward_txt") else ""
            ach_lines.append(f"🏆 成就解锁：{a['name']}！({a['desc']}){rw_txt}")
        if ach_lines:
            lines += [""] + ach_lines
        # v97.5 行为彩蛋规则：战斗胜利后（#262：触发已提前到进度条生成前，这里只保留公告行位置）
        if _rule_txt:
            lines.append(_rule_txt)
        lines.append("━━━━━━━━━━━━")
        lines.append(f"你：❤️ {player['hp']}/{player['max_hp']} 💙 {player['mp']}/{player['max_mp']}")
        yield event.plain_result("\n".join(lines))

    def _handle_defeat(self, event, group_id, qq_id, player, monster, result):
        """战败：扣金币/回城"""
        self._unlock_battle(group_id, qq_id)
        db.clear_battle(group_id, qq_id)
        db.init_stats(group_id, qq_id)
        db.bump_stats(group_id, qq_id, deaths=1)
        lost = int(player["gold"] * 0.1)
        new_gold = max(0, player["gold"] - lost)
        lines = [f"{result}", f"💀 你倒下了……被【{monster['name']}】击败。"]
        # v84 红名死亡惩罚（26 章三 第二档）：红名期间死亡额外掉 10%（上限 2000）
        if self._is_redname(qq_id):
            extra = min(int(player["gold"] * 0.1), 2000)
            new_gold = max(0, new_gold - extra)
            lines.append(f"☠️ 红名期间死亡：额外损失 {extra} 金币(上限 2000)！")
        # 回城并满血（新手保护；v86 子区域：落中心广场）
        # v95.19: max_hp/max_mp 同步实时值（player 已由 Battle 刷新），DB 字段不再过时
        db.update_player(group_id, qq_id, gold=new_gold, hp=player["max_hp"], mp=player["max_mp"],
                         max_hp=player["max_hp"], max_mp=player["max_mp"],
                         cur_map=C.START_MAP, cur_subarea=C.START_SUBAREA)
        lines.append(
            f"你丢失了 {lost} 金币（战败损失 10% 金币），被好心人送回了橡木镇中心广场。\n"
            f"休息后满血复活！下次要小心啊，冒险者。"
        )
        # v97.5 行为彩蛋规则：战败（用于清零连胜等计数，不产出彩蛋）
        self._rule_fire("battle_win", group_id, qq_id, player,
                        C.MAP_BY_ID.get(player.get("cur_map"), {}),
                        {"event": "lose"})
        yield event.plain_result("\n".join(lines))

    def _update_quests(self, group_id, qq_id, monster):
        """战斗后更新任务进度，返回通知行
        主线任务流程：未接 → (找NPC) 进行中 → 目标达成(可交) → (找NPC) 交任务领奖
        """
        lines = []
        quests = db.get_quests(group_id, qq_id)
        changed = False
        # 主线（仅处理已接且进行中的任务；击杀达到目标则变为可交状态）
        main_id = quests.get("main_quest")
        if main_id:
            mq = next((q for q in C.MAIN_QUESTS if q["id"] == main_id), None)
            if mq and quests.get("main_status") == "active":
                prog = dict(quests.get("main_progress", {}))
                obj = mq["objective"]
                if obj.get("kill") and (obj["kill"] == monster["name"] or obj["kill"] in monster["name"]):
                    # v95.7 #33：精英/头目变体名包含目标怪名（如『野猪』←『精英野猪』）也计入任务进度
                    prog[monster["name"]] = prog.get(monster["name"], 0) + 1
                    quests["main_progress"] = prog
                    changed = True
                    if prog.get(monster["name"], 0) >= obj["count"]:
                        quests["main_status"] = "ready"
                        _g = C.NPCS.get(mq["giver"]) or C.ALL_WILD.get(mq["giver"]) or {}
                        lines.append(f"📜 主线『{mq['name']}』目标达成！回去找 {_g.get('name', '？')} {self._deliver_hint(mq['giver'])}吧～")
                    else:
                        lines.append(f"📜 主线『{mq['name']}』：{prog[monster['name']]}/{obj['count']}")
        # 每日
        # v94：先清跨天任务（daily 里 _date 不是今天 → 清空），避免旧任务残留
        if db.expire_daily(quests):
            changed = True
        daily = dict(quests.get("daily", {}))
        for dkey, dq in list(daily.items()):
            if dkey == "_date":  # 跨天字段，不是任务
                continue
            dobj = dq["objective"]
            prog = dq.get("progress", 0)
            if dobj.get("kill_any"):
                prog += 1
            elif dobj.get("kill_elite") and monster.get("is_elite"):
                prog += 1
            elif dobj.get("kill_boss") and monster.get("is_boss"):
                prog += 1
            dq["progress"] = prog
            changed = True
            if prog >= dobj.get("kill_any", dobj.get("kill_elite", dobj.get("kill_boss", 99))):
                lines.append(f"📜 每日『{dq['name']}』完成！奖励：经验 +{dq['reward_exp']} 金币 +{dq['reward_gold']}")
                player = self._player(group_id, qq_id)
                player["exp"] += dq["reward_exp"]
                player["gold"] += dq["reward_gold"]
                player["_title_bonus"] = self._title_bonus(group_id, qq_id)
                lv_logs, player = E.check_player_level_up(group_id, qq_id, player)
                db.update_player(group_id, qq_id, exp=player["exp"], gold=player["gold"], level=player["level"], hp=player["hp"], mp=player["mp"], max_hp=player["max_hp"], max_mp=player["max_mp"], skills=player["skills"], attr_pts=player.get("attr_pts", 0), skill_points=player.get("skill_points", 0), learned_skills=player.get("learned_skills", []))
                if lv_logs:
                    lines.append("")
                    lines += lv_logs
                del daily[dkey]
        # 无条件写回：即使全部完成（daily 为空）也要清空 quests，否则任务残留会无限重复发奖励
        quests["daily"] = daily
        # 支线（击杀型）
        side = dict(quests.get("side", {}))
        for sid, sq in list(side.items()):
            if sq.get("status") != "active":
                continue
            sqd = next((q for q in C.SIDE_QUESTS if q["id"] == sid), None)
            if not sqd:
                continue
            obj = sqd["objective"]
            if obj.get("kill_any"):
                # v95.13 修复：kill_any 支线（护送商货等）此前无计数分支，任务永久卡死
                prog = dict(sq.get("progress", {}))
                prog["any"] = prog.get("any", 0) + 1
                sq["progress"] = prog
                changed = True
                if prog["any"] >= obj["kill_any"]:
                    sq["status"] = "ready"
                    _g = C.NPCS.get(sqd["giver"]) or C.ALL_WILD.get(sqd["giver"]) or {}
                    lines.append(f"📜 支线『{sqd['name']}』目标达成！回去找 {_g.get('name', '？')} {self._deliver_hint(sqd['giver'])}吧～")
                else:
                    lines.append(f"📜 支线『{sqd['name']}』：{prog['any']}/{obj['kill_any']}")
            elif obj.get("kill") == monster["name"]:
                prog = dict(sq.get("progress", {}))
                prog[monster["name"]] = prog.get(monster["name"], 0) + 1
                sq["progress"] = prog
                changed = True
                if prog.get(monster["name"], 0) >= obj["count"]:
                    sq["status"] = "ready"
                    _g = C.NPCS.get(sqd["giver"]) or C.ALL_WILD.get(sqd["giver"]) or {}
                    lines.append(f"📜 支线『{sqd['name']}』目标达成！回去找 {_g.get('name', '？')} {self._deliver_hint(sqd['giver'])}吧～")
                else:
                    lines.append(f"📜 支线『{sqd['name']}』：{prog[monster['name']]}/{obj['count']}")
        if side:
            quests["side"] = side
        if changed:
            db.save_quests(group_id, qq_id, quests)
        return lines

    @filter.regex(r"^(?:\[At:\d+\]\s*)?讨伐(?:\s*|$)")
    @require_player()
    @no_prof_waiting()

    async def hunt_boss(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        cur = db.get_world_event()
        now = int(time.time())
        if not cur:
            # 是否有过期的 Boss 事件待清除
            expired = db.get_world_event(include_expired=True)
            if expired and expired["etype"] == "boss" and now >= expired["ends_at"]:
                db.clear_world_event()
                yield event.plain_result("👹 世界 Boss 已经撤离……下次再战！")
                return
            yield event.plain_result("👹 没有世界 Boss 入侵！等『世界Boss入侵』事件出现时再来吧！")
            return
        if cur["etype"] != "boss":
            yield event.plain_result("👹 没有世界 Boss 入侵！等『世界Boss入侵』事件出现时再来吧！")
            return
        b = cur["data"].get("boss", {})
        # v49 意见#5：世界 Boss 指定地点，必须到达该地图才能讨伐
        boss_map = b.get("map", "")
        if boss_map and player["cur_map"] != boss_map:
            cur_map_name = C.MAP_BY_ID.get(player["cur_map"], {}).get("name", player["cur_map"])
            yield event.plain_result(
                f"👹 世界 Boss【{b.get('name', '?')}】出现在【{b.get('map_name', '未知之地')}】！\n"
                f"📍 你当前在【{cur_map_name}】，不在 Boss 出没地！\n"
                f"🧭 用『前往 <地图名>』前往指定地点才能讨伐！"
            )
            return
        # 已有世界BOSS战斗状态 → 显示当前状态
        battle = db.get_battle(group_id, qq_id)
        if battle and battle["state"].get("type") == "worldboss":
            b2 = battle["state"].get("enemy", {})
            pct = max(0, int(b2.get("hp", 0) / max(1, b2.get("max_hp", 1)) * 100))
            yield event.plain_result(
                f"⚔️ 你已加入讨伐！\n"
                f"👹【{b2.get('name', '?')}】❤️ {max(0, b2.get('hp', 0)):,} / {b2.get('max_hp', 0):,}({pct}%)\n"
                f"你：❤️ {player['hp']}/{player['max_hp']} 💙 {player['mp']}/{player['max_mp']}\n"
                f"━━━━━━━━━━━━\n你的行动：『攻击』『技能 <名称/序号>』『防御』"
            )
            return
        # 第一次进入：创建世界BOSS战斗（Boss 没技能则按等级配 2 个攻击技能）
        import random as _rnd
        boss = dict(b)
        if not boss.get("skills"):
            cand = [s for s, si in C.MONSTER_SKILLS.items() if si.get("kind") in ("物理", "魔法")]
            boss["skills"] = _rnd.sample(cand, min(2, len(cand)))
        nb = BT.Battle("worldboss", boss, self._title_bonus(group_id, qq_id), player=player, pet=db.pet_get(qq_id), dmg_mult=db.get_boss_dmg_mult(qq_id))
        db.save_battle(group_id, qq_id, nb.to_state())
        self._lock_battle(group_id, qq_id)
        pct = max(0, int(boss["hp"] / max(1, boss["max_hp"]) * 100))
        yield event.plain_result(
            f"⚔️ 你冲向【{boss['name']}】，讨伐开始！\n"
            f"👹 Lv.{boss.get('lv', 30)} ❤️ {boss['hp']:,} / {boss['max_hp']:,}({pct}%)\n"
            f"━━━━━━━━━━━━\n你的行动：『攻击』『技能 <名称/序号>』『防御』\n"
            f"💡 造成伤害计入讨伐贡献，Boss 倒下后按贡献分奖励！"
        )

    async def _worldboss_act(self, event, group_id, qq_id, player, b, action, skill_name=None):
        """世界BOSS战斗行动（attack/skill/defend 共用）
        1. 同步全局 Boss 血量（其他玩家可能也打了）
        2. 玩家行动 → 贡献累积 → 同步回世界事件
        3. Boss 死亡 → 按贡献结算奖励并广播；玩家死亡 → 走死亡结算
        """
        cur_evt = db.get_world_event()
        if not cur_evt or cur_evt["etype"] != "boss":
            self._unlock_battle(group_id, qq_id)
            db.clear_battle(group_id, qq_id)
            yield event.plain_result("👹 世界 Boss 已经撤离……下次再战！")
            return
        gboss = cur_evt["data"]["boss"]
        b.enemy["hp"] = gboss.get("hp", b.enemy.get("hp", 0))  # 同步全局血量
        before = b.enemy["hp"]
        logs, ended = b.player_turn(action, skill_name, player)
        db.update_player(group_id, qq_id, hp=player["hp"], mp=player["mp"], max_hp=player["max_hp"], max_mp=player["max_mp"])
        dealt = max(0, before - b.enemy["hp"])
        contrib = gboss.setdefault("contrib", {})
        contrib[str(qq_id)] = contrib.get(str(qq_id), 0) + dealt
        lines = [x for x in logs if "你击败了" not in x and "毒发身亡" not in x]

        if ended and b.result == "victory":
            # Boss 死亡结算（先于玩家死亡判断）
            lines.append("")
            lines.append(f"🎉 【{gboss['name']}】被击败了！")
            total = sum(contrib.values())
            for qq2, d in sorted(contrib.items(), key=lambda x: -x[1]):
                p2 = self._player(group_id, qq2)
                if not p2:
                    continue
                ratio = d / max(1, total)
                g = int(gboss["reward"]["gold"] * ratio * 3)
                e = int(gboss["reward"]["exp"] * ratio * 3)
                db.update_player(group_id, qq2, gold=p2["gold"] + g, exp=p2["exp"] + e)
                lines.append(f"  {p2['name']} 贡献 {d:,}({int(ratio*100)}%)→ 金币 +{g} 经验 +{e}")
            top_qq = max(contrib, key=contrib.get)
            tp = self._player(group_id, top_qq)
            if tp:
                lines.append(f"👑 首功：{tp['name']}！")
            db.clear_world_event()
            self._unlock_battle(group_id, qq_id)
            db.clear_battle(group_id, qq_id)
            try:
                await self._broadcast("\n".join(lines))
            except Exception:
                pass
            if player["hp"] <= 0:
                # 同归于尽：奖励已发，玩家仍走死亡结算
                player["hp"] = 0
                for _r in self._handle_defeat(event, group_id, qq_id, player,
                                              {"name": gboss["name"], "lv": gboss.get("lv", 30)},
                                              "\n".join(lines)):
                    yield _r
                return
            yield event.plain_result("\n".join(lines))
            return

        if ended and b.result == "defeat":
            # 玩家阵亡（Boss 未死）：贡献已记，同步血量，走死亡结算
            gboss["hp"] = b.enemy["hp"]
            db.save_world_event(cur_evt["etype"], cur_evt["ends_at"], cur_evt["data"])
            self._unlock_battle(group_id, qq_id)
            db.clear_battle(group_id, qq_id)
            player["hp"] = 0
            for _r in self._handle_defeat(event, group_id, qq_id, player,
                                          {"name": gboss["name"], "lv": gboss.get("lv", 30)},
                                          "\n".join(lines)):
                yield _r
            return

        # Boss 未死：更新贡献 + 全局血量 + 战斗状态
        gboss["hp"] = b.enemy["hp"]
        db.save_world_event(cur_evt["etype"], cur_evt["ends_at"], cur_evt["data"])
        db.save_battle(group_id, qq_id, b.to_state())
        pct = max(0, int(gboss["hp"] / max(1, gboss["max_hp"]) * 100))
        body = "\n".join(lines)
        status = self._status_line(player, b)
        yield event.plain_result(
            f"{body}\n━━━━━━━━━━━━\n"
            f"👹【{gboss['name']}】❤️ {gboss['hp']:,} / {gboss['max_hp']:,}({pct}%)｜你的贡献 {contrib[str(qq_id)]:,}\n"
            f"你：❤️ {player['hp']}/{player['max_hp']} 💙 {player['mp']}/{player['max_mp']}"
            + (f"\n{status}" if status else "")
        )

    def _parse_target_qq(self, target_arg: str):
        """解析攻击目标参数：@QQ / [At:QQ] / QQ / @名字(QQ) / 名字(QQ) / 名字。返回 (qq_id, name) 或 None"""
        t = target_arg.strip()
        # [At:123]
        m = re.match(r"^\[At:(\d+)\]$", t)
        if m:
            return m.group(1), None
        # @123 或 123
        m = re.match(r"^@?(\d+)$", t)
        if m:
            return m.group(1), None
        # @名字(123) 或 名字(123) —— QQ @ 消息的文本格式（括号内是 QQ 号）
        m = re.match(r"^@?[^()()]*[((](\d+)[))]$", t)
        if m:
            return m.group(1), None
        tp = db.find_player_by_name(t)
        if tp:
            return str(tp["qq_id"]), tp["name"]
        return None

    def _red_until(self, qq_id) -> int:
        try:
            return int(db.get_event_state(f"red_{qq_id}") or 0)
        except (ValueError, TypeError):
            return 0

    def _is_redname(self, qq_id) -> bool:
        return time.time() < self._red_until(qq_id)

    def _get_honor(self, qq_id) -> int:
        try:
            return int(db.get_event_state(f"honor_{qq_id}") or 0)
        except (ValueError, TypeError):
            return 0

    def _pvp_snapshot(self, p: dict, group_id: str = "", qq_id: str = "") -> dict:
        """玩家快照(PVP 战斗状态用)"""
        st = E.player_final_stats(p["class_name"], p["level"], p.get("equipment", {}), p.get("class_tier", 0), p.get("attributes"), p.get("evolve_path", 0), self._title_bonus(group_id, qq_id), p.get("race"))
        return {
            "qq_id": str(p["qq_id"]), "name": p["name"],
            "class_name": p["class_name"], "level": p["level"],
            "hp": p["hp"], "mp": p["mp"], "max_hp": st["max_hp"], "max_mp": st["max_mp"],
            "equipment": p.get("equipment", {}), "class_tier": p.get("class_tier", 0),
            "attributes": p.get("attributes", {}),
            "evolve_path": p.get("evolve_path", 0), "race": p.get("race"),
        }

    def _pvp_handle_timeout(self, battle, group_id, qq_id) -> bool:
        """PVP 超时检查：5 分钟无行动自动解除(防对方离线卡死)。返回 True=已解除"""
        if time.time() - battle.get("updated_at", 0) > C.PVP_TIMEOUT_SEC:
            st = battle["state"]
            opp_qq = st["attacker"]["qq_id"] if str(st["defender"]["qq_id"]) == str(qq_id) else st["defender"]["qq_id"]
            # 攻击方获得袭击 CD，防脱离后立刻再骚扰
            self._set_pvp_cd(st.get("attacker_qq", st["attacker"]["qq_id"]))
            self._unlock_battle(group_id, qq_id)
            db.clear_battle(group_id, qq_id)
            self._unlock_battle(group_id, opp_qq)
            db.clear_battle(group_id, opp_qq)
            return True
        return False

    def _set_pvp_cd(self, qq_id):
        """PVP 结束后主动攻击方 2 分钟袭击冷却(防打一下逃跑反复骚扰)"""
        db.set_event_state(f"pvp_cd_{qq_id}", str(int(time.time()) + 120))

    def _pvp_cd_left(self, qq_id) -> int:
        try:
            return max(0, int(db.get_event_state(f"pvp_cd_{qq_id}") or 0) - int(time.time()))
        except (ValueError, TypeError):
            return 0

    # ---------------- v84 荣誉商店（26 章 3.3；v99.4 数据化 → data/honor_shop.py） ----------------

    @filter.regex(r"^(?:\[At:\d+\]\s*)?荣誉(?:[\s\S]*)$")
    @require_player()
    async def honor_shop(self, event: AstrMessageEvent):
        """荣誉商店：『荣誉』查看，『荣誉 兑换 <编号>』兑换"""
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        raw = self._strip_cmd(event, "荣誉").strip()
        if raw.startswith("兑换"):
            num = raw[2:].strip()
            if not num.isdigit():
                yield event.plain_result("格式：『荣誉 兑换 <编号>』！『荣誉』查看商店～")
                return
            async for _r in self._honor_buy(event, group_id, qq_id, player, int(num)):
                yield _r
            return
        honor = self._get_honor(qq_id)
        lines = [f"⚜️ 【荣誉商店】(荣誉：{honor})", "━━━━━━━━━━━━"]
        for i, item in C.HONOR_SHOP.items():
            lines.append(f"{i}. {item['name']} ｜ {item['cost']} 荣誉")
            lines.append(f"   {item['desc']}")
        lines.append("━━━━━━━━━━━━")
        lines.append("💡 荣誉获取：击杀红名玩家＋50；『荣誉 兑换 <编号>』兑换")
        if self._is_redname(qq_id):
            lines.append(f"☠️ 你当前红名中(剩余 {max(0, self._red_until(qq_id) - int(time.time())) // 60} 分钟)！")
        yield event.plain_result("\n".join(lines))

    async def _honor_buy(self, event, group_id, qq_id, player, num):
        """荣誉兑换：扣荣誉 → 按 reward 类型发放（v99.4 数据化 → data/honor_shop.py）"""
        item = C.HONOR_SHOP.get(num)
        if not item:
            yield event.plain_result(f"没有第 {num} 件商品！『荣誉』查看商店～")
            return
        honor = self._get_honor(qq_id)
        if honor < item["cost"]:
            yield event.plain_result(f"荣誉不足！兑换【{item['name']}】需要 {item['cost']} 荣誉，你只有 {honor}。")
            return
        db.set_event_state(f"honor_{qq_id}", str(honor - item["cost"]))
        reward = item.get("reward") or {}
        import uuid as _uuid
        if reward.get("type") == "title":
            db.set_event_state(f"honor_{reward['title_id']}_{qq_id}", "1")
            yield event.plain_result(
                f"⚜️ 你兑换了【{reward['label']}】称号！(花费 {item['cost']} 荣誉)\n"
                f"{reward.get('msg', '')}")
        elif reward.get("type") == "item":
            db.add_item(group_id, qq_id, f"{reward.get('item_prefix', 'h_')}{_uuid.uuid4().hex[:8]}", reward["item"])
            yield event.plain_result(f"⚜️ 你兑换了【{item['name']}】！(花费 {item['cost']} 荣誉)\n{reward.get('msg', '')}")
        else:
            yield event.plain_result(f"⚜️ 兑换失败：商品没有配置 reward 类型！请找 GM 检查数据～")

    async def _pvp_start(self, event, group_id, qq_id, player, target_arg):
        """PVP 发起：『攻击 @目标』(安全区/等级保护/灰名/袭击CD)"""
        cd = self._pvp_cd_left(qq_id)
        if cd > 0:
            yield event.plain_result(f"⏳ 你刚结束一场 PVP，{cd} 秒后才能再次袭击玩家！")
            return
        parsed = self._parse_target_qq(target_arg)
        if not parsed:
            yield event.plain_result(f"找不到玩家『{target_arg}』！用『攻击 @对方』发起决斗。")
            return
        target_qq, _tname = parsed
        if str(target_qq) == str(qq_id):
            yield event.plain_result("你不能攻击自己！")
            return
        target_player = db.get_player(group_id, target_qq)
        if not target_player:
            yield event.plain_result("对方还没有角色！")
            return
        if self._in_battle(group_id, qq_id):
            yield event.plain_result("你正在战斗中！先解决眼前的敌人。")
            return
        if self._in_battle(group_id, target_qq):
            yield event.plain_result(f"【{target_player['name']}】正在战斗中，无法应战！")
            return
        # v84 新手保护（26 章二）：Lv.<10 不能被攻击
        if target_player["level"] < 10:
            yield event.plain_result(f"【{target_player['name']}】才 Lv.{target_player['level']}，处于新手保护期(Lv.<10 不能被攻击)！")
            return
        if player["level"] < 10:
            yield event.plain_result(f"你才 Lv.{player['level']}，处于新手保护期(Lv.<10 不能攻击玩家)！去野外打怪练练级吧～")
            return
        # 安全区检查（城镇区域不可 PK；'城镇外郊' 类型数据不存在，v102.1 清理）
        cur_map = C.MAP_BY_ID.get(player["cur_map"], {})
        tgt_map = C.MAP_BY_ID.get(target_player["cur_map"], {})
        if cur_map.get("type") == C.MAP_TYPE_TOWN or tgt_map.get("type") == C.MAP_TYPE_TOWN:
            yield event.plain_result("🏘️ 这里是安全区，禁止攻击玩家！去野外地图才能 PK。")
            return
        # 等级保护：等级差 > 10 不能主动攻击
        if abs(player["level"] - target_player["level"]) > 10:
            yield event.plain_result(f"等级差超过 10 级，无法发起攻击！(你 {player['level']} 级 vs 对方 {target_player['level']} 级)")
            return
        # 创建 PVP 战斗状态（双方各存一份）
        state = {
            "type": "pvp",
            "actor": "attacker",
            "attacker_qq": str(qq_id),
            "attacker": self._pvp_snapshot(player, group_id, qq_id),
            "defender": self._pvp_snapshot(target_player, group_id, target_qq),
            "a_buffs": {}, "b_buffs": {},
        }
        db.save_battle(group_id, qq_id, state)
        db.save_battle(group_id, target_qq, state)
        self._lock_battle(group_id, qq_id)
        self._lock_battle(group_id, target_qq)
        # 主动攻击 → 灰名 10 分钟
        db.set_event_state(f"grey_{qq_id}", str(int(time.time()) + 600))
        a, d = state["attacker"], state["defender"]
        yield event.plain_result(
            f"⚔️ 你向【{target_player['name']}】发起攻击！\n"
            f"━━━━━━━━━━━━\n"
            f"你：❤️ {a['hp']}/{a['max_hp']} 💙 {a['mp']}/{a['max_mp']} ｜ Lv.{a['level']}\n"
            f"对方：❤️ {d['hp']}/{d['max_hp']} 💙 {d['mp']}/{d['max_mp']} ｜ Lv.{d['level']}\n"
            f"━━━━━━━━━━━━\n你先手！输入『攻击』『技能 <名称/序号>』『防御』"
        )

    async def _pvp_act(self, event, group_id, qq_id, player, state, action, skill_name=None):
        """PVP 行动：轮流操作，胜者结算"""
        my_key = "attacker" if str(state["attacker"]["qq_id"]) == str(qq_id) else "defender"
        if state.get("actor") != my_key:
            yield event.plain_result("⏳ 还没轮到你行动！等对方出手……")
            return
        opp_key = "defender" if my_key == "attacker" else "attacker"
        opp = state[opp_key]
        # PVP 战斗中血量/蓝量以快照为准（战斗内扣血不写回 db，避免被重置）
        player["hp"] = state[my_key].get("hp", player["hp"])
        player["mp"] = state[my_key].get("mp", player["mp"])
        # 重建 Battle：我是 player，对方是 enemy 快照（PVP 不自动反击）
        b = BT.Battle("pvp", enemy=dict(opp), title_bonus=self._title_bonus(group_id, qq_id), player=player, pet=db.pet_get(qq_id))
        b.p_buffs = dict(state.get(f"{my_key[0]}_buffs", {}))
        b.e_buffs = dict(state.get(f"{opp_key[0]}_buffs", {}))
        if action == "skill":
            info = E.skill_info(player["class_name"], skill_name)
            if not info:
                yield event.plain_result(f"没有技能『{skill_name}』！")
                return
            if not E.is_skill_learned(player["class_name"], player["level"], skill_name, player.get("learned_skills", [])):
                yield event.plain_result(f"该技能需要 Lv.{info['lv']} 才能使用，你才 Lv.{player['level']}")
                return
            if player["mp"] < info["mp"]:
                yield event.plain_result("💙 魔力不足！")
                return
        logs, ended = b.player_turn(action, skill_name, player, enemy_act=False)
        # 同步快照与 buffs
        opp["hp"] = b.enemy["hp"]
        opp["mp"] = b.enemy.get("mp", opp.get("mp", 0))
        state[my_key]["hp"] = player["hp"]
        state[my_key]["mp"] = player["mp"]
        state[f"{my_key[0]}_buffs"] = b.p_buffs
        state[f"{opp_key[0]}_buffs"] = b.e_buffs
        db.save_battle(group_id, qq_id, state)
        db.save_battle(group_id, opp["qq_id"], state)
        if ended and b.result == "victory":
            # 行动者胜：胜者受伤状态写回 db
            db.update_player(group_id, qq_id, hp=state[my_key]["hp"], mp=state[my_key]["mp"])
            self._unlock_battle(group_id, qq_id)
            self._unlock_battle(group_id, opp["qq_id"])
            db.clear_battle(group_id, qq_id)
            db.clear_battle(group_id, opp["qq_id"])
            async for _r in self._pvp_finish(event, group_id, qq_id, opp["qq_id"], state.get("attacker_qq", qq_id), "\n".join(logs)):
                yield _r
            return
        if ended and b.result == "defeat":
            # PVP 无敌方回合，正常不会走到；保险处理
            self._unlock_battle(group_id, qq_id)
            self._unlock_battle(group_id, opp["qq_id"])
            db.clear_battle(group_id, qq_id)
            db.clear_battle(group_id, opp["qq_id"])
            yield event.plain_result("\n".join(logs))
            return
        state["actor"] = opp_key
        db.save_battle(group_id, qq_id, state)
        db.save_battle(group_id, opp["qq_id"], state)
        body = "\n".join(logs)
        yield event.plain_result(
            f"{body}\n━━━━━━━━━━━━\n"
            f"【{opp['name']}】❤️ {max(0, opp['hp'])}/{opp['max_hp']} 💙 {opp['mp']}/{opp['max_mp']}\n"
            f"你：❤️ {player['hp']}/{player['max_hp']} 💙 {player['mp']}/{player['max_mp']}\n"
            f"━━━━━━━━━━━━\n已轮到对方行动！(对方输入『攻击』『技能』『防御』)"
        )

    async def _pvp_finish(self, event, group_id, winner_qq, loser_qq, attacker_qq, log_body):
        """PVP 结算：败者掉 10% 金币给胜者 + 回城 HP=1；红名/荣誉"""
        loser = db.get_player(group_id, loser_qq)
        winner = db.get_player(group_id, winner_qq)
        lost = int(loser["gold"] * 0.1)
        db.update_player(group_id, winner_qq, gold=winner["gold"] + lost)
        db.update_player(group_id, loser_qq, gold=loser["gold"] - lost, hp=1, cur_map=C.START_MAP, cur_subarea=C.START_SUBAREA)
        db.init_stats(group_id, loser_qq)
        db.bump_stats(group_id, loser_qq, deaths=1)
        # 攻击方袭击 CD（防击杀后立刻蹲尸再打）
        self._set_pvp_cd(str(attacker_qq))
        now = int(time.time())
        lines = [log_body, "", f"💀 【{loser['name']}】被击败了！"]
        if lost > 0:
            lines.append(f"💰 你夺走了 {lost} 金币！")
        lines.append(f"🏥 对方被送回橡木镇疗养(HP 1)。")
        if self._is_redname(loser_qq):
            honor = self._get_honor(winner_qq) + 50
            db.set_event_state(f"honor_{winner_qq}", str(honor))
            lines.append(f"⚜️ 你讨伐了红名玩家！荣誉＋50(当前 {honor})")
        else:
            if str(winner_qq) == str(attacker_qq):
                red_until = self._red_until(winner_qq)
                new_red = max(red_until, now) + 1800
                db.set_event_state(f"red_{winner_qq}", str(new_red))
                lines.append("☠️ 你击杀了玩家，红名 30 分钟！(红名期间无法进入安全区)")
        yield event.plain_result("\n".join(lines))
