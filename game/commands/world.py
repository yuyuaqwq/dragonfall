# -*- coding: utf-8 -*-
"""《剑与魔法》命令层 - world（world）

由 main.py 拆分而来，作为 Mixin 被 Main 继承。
"""
import functools
import inspect
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
from ..commands.base import CommandBase, no_prof_waiting


class WorldCmds(CommandBase):

    def _map_interactions(self, cur_map: dict, player: dict = None) -> list:
        """当前地图可互动元素清单（v13：互动直接显示）"""
        lines = []
        mid = cur_map.get("id", "")
        portals = db.get_portals(player["qq_id"]) if player else []
        # 设施
        if cur_map.get("shop"):
            lines.append("🏪 商店（『购买』）")
        if cur_map.get("healer"):
            lines.append("🏨 旅店（『住宿』恢复全状态）")
        if mid in C.ENHANCE_SMITH_MAPS:
            lines.append("🔨 铁匠铺（『强化』『附魔』）")
        # 旅者方碑
        if mid in C.PORTALS:
            p = C.PORTALS[mid]
            if mid in portals:
                lines.append(f"🌌 {p['icon']}{p['name']}（已激活，『传送 <名称>』）")
            else:
                lines.append(f"🌌 {p['icon']}{p['name']}（『激活』解锁传送点）")
        # 自然互动
        if mid in C.FISHING_SPOTS:
            _fi = C.FISHING_SPOTS[mid]
            _fname = _fi["name"] if isinstance(_fi, dict) else _fi
            _fneed = _fi.get("min_lv", 1) if isinstance(_fi, dict) else 1
            _flv = db.get_prof_level(player.get("group_id", "g"), player["qq_id"], "fishing") if player else 1
            _lock = " 🔒" if _flv < _fneed else ""
            lines.append(f"🎣 钓鱼点·{_fname}（钓鱼Lv.{_fneed}）{_lock}（『钓鱼』）")
        if mid in C.CAMP_SPOTS:
            lines.append(f"🔥 篝火营地·{C.CAMP_SPOTS[mid]}（『休息』恢复一半生命）")
        if mid in C.MINE_SPOTS:
            lines.append(f"⛏️ 矿脉·{C.MINE_SPOTS[mid]}（『采矿』）")
        if cur_map.get("type") == "野外" and mid not in C.CAMP_SPOTS:
            lines.append("🌿 野地可采集（『采集』）")
        # NPC（含功能）
        npcs = [C.NPCS[nid] for nid in cur_map.get("npcs", []) if nid in C.NPCS]
        for n in npcs:
            funcs = "、".join(self._npc_func_label(f) for f in n.get("funcs", []))
            lines.append(f"{n['icon']}{n['name']}（『找 {n['name']}』{funcs}）")
        return lines

    @staticmethod
    def _npc_func_label(f: str) -> str:
        return {"quest": "接任务", "shop": "交易", "heal": "治疗", "daily": "每日委托", "lore": "情报", "ency": "百科"}.get(f, f)

    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:地图|位置)(?:\s*|$)")

    async def map_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        cur = player["cur_map"]
        cur_map = C.MAP_BY_ID[cur]
        cur_area = cur_map.get("area_name", cur_map["name"])
        lines = [f"🗺️ 【{cur_area} · {cur_map['name']}】", f"{cur_map['desc']}", "━━━━━━━━━━━━"]
        # 本区域其他子区域
        same_area = [m for m in C.MAPS if m.get("area_name") == cur_area and m["id"] != cur]
        if same_area:
            lines.append(f"🏘️ 同区域：{'、'.join(m['name'] for m in same_area)}")
        # 周边子区域（带序号，支持『移动 序号』）
        neighbors = C.MAP_CONNECTIONS.get(cur, [])
        if neighbors:
            lines.append("📮 可前往：")
            for i, nid in enumerate(neighbors, 1):
                nm = C.MAP_BY_ID[nid]
                lock = ""
                if nm.get("hidden"):
                    lock = " (🔒隐藏)"
                lines.append(f"  {i}. {nm['name']} Lv.{nm['lv']}{lock}")
        # 此地可互动（v13）
        inter = self._map_interactions(cur_map, player)
        if inter:
            lines.append("━━━━━━━━━━━━")
            lines.append("📜 此地可互动：")
            for l in inter:
                lines.append(f"  {l}")
        # 本地 NPC
        npcs = [C.NPCS[nid] for nid in cur_map.get("npcs", []) if nid in C.NPCS]
        if npcs:
            lines.append("👥 这里的 NPC：")
            for n in npcs:
                lines.append(f"  {n['icon']}{n['name']}（{n['title']}）")
        # 当前地图怪物
        if cur_map.get("monsters"):
            lines.append(f"🐾 此地的怪物 (Lv.{cur_map['lv']}-{cur_map['lv']+2})：")
            for mid, name, role, lv, skills, drops in cur_map["monsters"]:
                mark = "👑" if role == "boss" else ("⭐" if role == "elite" else "")
                lines.append(f"  {mark}{name} Lv.{lv}")
        # 精英/Boss
        if cur_map.get("elite"):
            ename = cur_map["elite"][1]
            lines.append(f"  ⭐ 精英：{ename}")
        if cur_map.get("boss"):
            bname = cur_map["boss"][1]
            lines.append(f"  👑 Boss：{bname}")
        lines.append(f"\n输入『探索』遇怪，『移动 序号』前往他处，『找 <NPC名>』交谈")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:移动|前往)(?:\s*|$)")
    @no_prof_waiting()

    async def move(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        dest = self._strip_cmd(event, "移动")
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        dest = dest.strip()
        # 查找目标地图：优先序号（相对当前地图邻居列表），其次地图名/ID/旧区域别名
        target = None
        if dest.isdigit():
            cur = player["cur_map"]
            neighbors = C.MAP_CONNECTIONS.get(cur, [])
            idx = int(dest)
            if 1 <= idx <= len(neighbors):
                target = C.MAP_BY_ID[neighbors[idx - 1]]
            else:
                yield event.plain_result(f"序号无效！可前往 {len(neighbors)} 张地图，输入『地图』查看～")
                return
        else:
            for m in C.MAPS:
                if dest in (m["name"], m["id"]):
                    target = m
                    break
            if not target and dest in C.LEGACY_MAP_ALIAS:
                target = C.MAP_BY_ID.get(C.LEGACY_MAP_ALIAS[dest])
            if not target:
                # 区域名 → 区域入口
                for m in C.MAPS:
                    if dest in m.get("area_name", ""):
                        target = m
                        break
        if not target:
            names = "、".join([m["name"] for m in C.MAPS])
            yield event.plain_result(f"找不到『{dest}』！大陆上有：{names}")
            return
        # 隐藏图检查
        if target.get("hidden"):
            unlock = C.HIDDEN_MAP_UNLOCK.get(target["id"], {})
            if player["level"] < unlock.get("level", 99):
                yield event.plain_result("前方被无形的屏障阻挡……这里需要更强大的实力！（等级不足）")
                return
            quests = db.get_quests(group_id, qq_id)
            if unlock.get("quest") not in quests.get("completed_main", []):
                yield event.plain_result("地图的入口被古老魔法封印，似乎只有完成主线任务才能解开……")
                return
        # 是否相邻
        cur = player["cur_map"]
        neighbors = C.MAP_CONNECTIONS.get(cur, [])
        if target["id"] != cur and target["id"] not in neighbors:
            yield event.plain_result(f"无法直接前往{target['name']}！需要先到相邻地图。看看『地图』～")
            return
        # 等级提示
        lv_msg = ""
        if player["level"] < target["lv"]:
            lv_msg = f"\n⚠️ 建议等级 Lv.{target['lv']}，你才 Lv.{player['level']}，小心行事！"
        db.update_player(group_id, qq_id, cur_map=target["id"])
        # 记录到访（称号用）
        db.add_visited(group_id, qq_id, target["id"])
        # 探索型任务触发（到达目标子区域自动完成）
        quest_lines = self._update_explore_quests(group_id, qq_id, target["id"])
        extra = ""
        if quest_lines:
            extra = "\n\n" + "\n".join(quest_lines)
        # 旅者方碑提示（未激活时）
        portal_msg = ""
        if target["id"] in C.PORTALS and target["id"] not in db.get_portals(qq_id):
            p = C.PORTALS[target["id"]]
            portal_msg = f"\n\n🌌 一座{p['icon']}{p['name']}矗立在此！『激活』可解锁传送点～"
        # v13：到达后显示可前往 + 此地可互动
        neighbors = C.MAP_CONNECTIONS.get(target["id"], [])
        nav = ""
        if neighbors:
            nav = "\n\n📮 可前往：" + "  ".join(
                f"{i}.{C.MAP_BY_ID[nid]['name']}" for i, nid in enumerate(neighbors[:6], 1)
            )
        inter = self._map_interactions(target, player)
        inter_msg = ""
        if inter:
            inter_msg = "\n\n📜 此地可互动：\n  " + "\n  ".join(inter)
        # v49 意见#4：移动撞怪（生物趋避利害——低级闯高级区容易撞怪，高级玩家威慑低级区）
        ambush = self._travel_ambush(player, target)
        if ambush:
            db.save_battle(group_id, qq_id, BT.Battle("monster", ambush, self._title_bonus(group_id, qq_id)).to_state())
            self._lock_battle(group_id, qq_id)
            yield event.plain_result(
                f"🚶 你来到了【{target['name']}】\n{target['desc']}{lv_msg}{extra}{portal_msg}\n"
                f"━━━━━━━━━━━━\n"
                f"🛡️ 还没站稳，{ambush['name']} 就拦住了去路！\n"
                f"🐾【{ambush['name']}】Lv.{ambush['lv']} ❤️ {ambush['hp']}/{ambush['max_hp']}\n"
                f"━━━━━━━━━━━━\n"
                f"你的行动：『攻击』『技能 <名称>』『防御』『逃跑』"
            )
            return
        yield event.plain_result(
            f"🚶 你来到了【{target['name']}】\n{target['desc']}{lv_msg}{extra}{portal_msg}{nav}{inter_msg}"
        )

    def _travel_ambush(self, player: dict, target_map: dict):
        """移动撞怪判定：返回撞到的怪物 dict 或 None。

        生物趋避利害：
        - 玩家等级 ≥ 地图等级+5：威慑低等级生物，不撞怪
        - 玩家等级 ≤ 地图等级-5：闯入强者地盘，30% 概率撞怪
        - 同级/略低：8~18% 概率
        城镇区域/外郊不撞怪（安全区）。
        """
        mtype = target_map.get("type", "野外")
        if mtype in ("城镇区域", "城镇外郊"):
            return None
        monsters = target_map.get("monsters") or []
        if not monsters:
            return None
        diff = target_map.get("lv", 1) - player["level"]
        if diff <= -5:
            return None
        if diff >= 5:
            chance = 0.30
        elif diff >= 0:
            chance = 0.18
        else:
            chance = 0.08
        if random.random() >= chance:
            return None
        return C.build_monster(random.choice(monsters), target_map)

    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:祭坛|方碑)(?:\s*|$)")

    async def portal_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        portals = db.get_portals(qq_id)
        cur = player["cur_map"]
        lines = ["🌌 【旅者方碑】", "━━━━━━━━━━━━"]
        # 当前地图
        if cur in C.PORTALS:
            p = C.PORTALS[cur]
            if cur in portals:
                lines.append(f"📍 此地：{p['icon']}{p['name']}（已激活）")
            else:
                lines.append(f"📍 此地：{p['icon']}{p['name']}（未激活，『激活』解锁！）")
        else:
            lines.append("📍 此地没有方碑")
        lines.append("━━━━━━━━━━━━")
        if not portals:
            lines.append("你还没激活任何方碑……去大陆各处寻找方碑，『激活』解锁传送点吧！")
        else:
            lines.append("✨ 已激活方碑（『传送 <序号>』直达）：")
            for i, mid in enumerate(portals, 1):
                m = C.MAP_BY_ID.get(mid, {})
                p = C.PORTALS.get(mid, {})
                cost = C.portal_cost(m)
                name = p.get("name", mid) if p else mid
                icon = p.get("icon", "🌌") if p else "🌌"
                lines.append(f" {i}. {icon}{name}（{m.get('name', '?')} · {cost} 金币）")
        lines.append("━━━━━━━━━━━━")
        lines.append("💡 『传送 <名称/序号>』付费传送；到新地图发现方碑就『激活』吧～")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:激活祭坛|激活)(?:\s*|$)")

    async def portal_activate(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        cur = player["cur_map"]
        if cur not in C.PORTALS:
            yield event.plain_result("这里没有方碑……寻找大陆上古道上刻着符文的古老路标吧！")
            return
        p = C.PORTALS[cur]
        if cur in db.get_portals(qq_id):
            yield event.plain_result(f"🌌 {p['icon']}{p['name']} 已经激活过了！『方碑』查看传送列表～")
            return
        db.add_portal(qq_id, cur)
        m = C.MAP_BY_ID.get(cur, {})
        exp = max(20, int(m.get("lv", 1)) * 20)
        db.update_player(group_id, qq_id, exp=player["exp"] + exp)
        yield event.plain_result(
            f"✨ 星辉流转，{p['icon']}{p['name']} 与你建立了链接！\n"
            f"📍 传送点已激活：{m.get('name', '?')}（✨ 经验 +{exp}）\n"
            f"💡 输入『方碑』查看全部已激活方碑，『传送 {p['name']}』即可直达！"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?传送(?:\s*|$)")
    @no_prof_waiting()

    async def portal_travel(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        dest = self._strip_cmd(event, "传送").strip()
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        if not dest:
            yield event.plain_result("传送到哪？『方碑』查看已激活方碑，『传送 <序号/名称>』直达～")
            return
        if self._in_battle(group_id, qq_id):
            yield event.plain_result("⚔️ 你正在战斗中！先解决眼前的敌人再说传送。")
            return
        portals = db.get_portals(qq_id)
        if not portals:
            yield event.plain_result("你还没激活任何方碑！输入『方碑』查看，去大陆上找找方碑吧～")
            return
        target = None
        if dest.isdigit():
            idx = int(dest)
            if 1 <= idx <= len(portals):
                target = C.MAP_BY_ID.get(portals[idx - 1])
            else:
                yield event.plain_result(f"序号无效！你有 {len(portals)} 座已激活方碑，『方碑』查看～")
                return
        else:
            for mid in portals:
                m = C.MAP_BY_ID.get(mid, {})
                p = C.PORTALS.get(mid, {})
                if dest in p.get("name", "") or dest in m.get("name", ""):
                    target = m
                    break
            if not target:
                # 未激活的祭坛名 → 提示未激活
                for mid, p in C.PORTALS.items():
                    if dest in p.get("name", ""):
                        yield event.plain_result(f"🌌 {p['icon']}{p['name']} 还没激活！先亲自前往该地图『激活』吧～")
                        return
                yield event.plain_result(f"找不到方碑『{dest}』！『方碑』查看已激活列表～")
                return
        if target["id"] == player["cur_map"]:
            yield event.plain_result("你已经在这座方碑所在的地图了！")
            return
        cost = C.portal_cost(target)
        # v39 坐骑：骑乘中传送折扣
        mounts = player.get("mounts") or {}
        active_mk = mounts.get("active")
        if active_mk and active_mk in C.MOUNT_BY_KEY:
            disc = C.MOUNT_BY_KEY[active_mk].get("discount", 0)
            cost = max(1, int(cost * (1 - disc)))
        if player["gold"] < cost:
            yield event.plain_result(f"传送需要 {cost} 金币（你只有 {player['gold']}）！打怪攒点金币吧～")
            return
        db.update_player(group_id, qq_id, gold=player["gold"] - cost, cur_map=target["id"])
        db.add_visited(group_id, qq_id, target["id"])
        quest_lines = self._update_explore_quests(group_id, qq_id, target["id"])
        extra = ""
        if quest_lines:
            extra = "\n\n" + "\n".join(quest_lines)
        p = C.PORTALS.get(target["id"], {})
        pname = p.get("name", "方碑") if p else "方碑"
        picon = p.get("icon", "🌌") if p else "🌌"
        yield event.plain_result(
            f"🌌 星辉流转，你踏入了传送通道……\n"
            f"✨ 你抵达了【{target['name']}】（{picon}{pname}，花费 {cost} 金币）\n"
            f"{target['desc']}{extra}"
        )

    def _update_explore_quests(self, group_id, qq_id, map_id):
        """到达子区域时检查 explore 型任务（主线和支线）"""
        lines = []
        quests = db.get_quests(group_id, qq_id)
        changed = False
        # 主线 explore
        main_id = quests.get("main_quest")
        if main_id:
            mq = next((q for q in C.MAIN_QUESTS if q["id"] == main_id), None)
            if mq and mq["objective"].get("explore") == map_id:
                player = self._player(group_id, qq_id)
                db.update_player(group_id, qq_id, exp=player["exp"] + mq["reward_exp"], gold=player["gold"] + mq["reward_gold"])
                completed = list(quests.get("completed_main", []))
                completed.append(main_id)
                quests["completed_main"] = completed
                quests["main_quest"] = mq["next"]
                quests["main_progress"] = {}
                changed = True
                lines.append(f"📜 主线『{mq['name']}』达成！奖励：经验 +{mq['reward_exp']} 金币 +{mq['reward_gold']}")
                if mq["next"]:
                    nq = next((q for q in C.MAIN_QUESTS if q["id"] == mq["next"]), None)
                    if nq:
                        lines.append(f"📜 新主线：『{nq['name']}』{nq['desc']}")
                else:
                    lines.append("🎊 恭喜！你完成了全部主线任务，成为维斯特兰的传说！")
        # 支线 explore
        side = dict(quests.get("side", {}))
        for sid, sq in list(side.items()):
            if sq.get("status") == "active":
                sqd = next((q for q in C.SIDE_QUESTS if q["id"] == sid), None)
                if sqd and sqd["objective"].get("explore") == map_id:
                    sq["status"] = "ready"
                    changed = True
                    lines.append(f"📜 支线『{sqd['name']}』目标达成！回去找 {C.NPCS[sqd['giver']]['name']} 交任务吧～")
        if changed:
            quests["side"] = side
            db.save_quests(group_id, qq_id, quests)
        return lines

    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:任务|主线)(?:\s*|$)")

    async def quest_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        if self._is_redname(qq_id):
            yield event.plain_result("☠️ 你是红名！守卫不让你靠近任务板……（等红名消退再来）")
            return
        quests = db.get_quests(group_id, qq_id)
        lines = ["📜 【冒险日志】", "━━━━━━━━━━━━"]
        # 主线
        main_id = quests.get("main_quest")
        if main_id:
            mq = next((q for q in C.MAIN_QUESTS if q["id"] == main_id), None)
            if mq:
                giver = C.NPCS.get(mq["giver"], {}).get("name", "？")
                giver_map = C.NPCS.get(mq["giver"], {}).get("map", "")
                giver_map_name = C.MAP_BY_ID.get(giver_map, {}).get("name", "？")
                lines.append(f"【主线】『{mq['name']}』")
                lines.append(f"  {mq['desc']}")
                st = quests.get("main_status", "pending")
                if st == "pending":
                    lines.append(f"  ⏳ 未接取：去找 {giver}（在{giver_map_name}）接取任务")
                elif st == "ready":
                    lines.append(f"  ✅ 目标达成！回去找 {giver} 交任务（『交任务』）")
                else:
                    prog = quests.get("main_progress", {})
                    obj = mq["objective"]
                    if obj.get("kill"):
                        cur = prog.get(obj["kill"], 0)
                        lines.append(f"  进度：{cur}/{obj['count']}")
                    elif obj.get("collect"):
                        cur = prog.get(obj["collect"], 0)
                        lines.append(f"  收集：{cur}/{obj['count']}")
                    elif obj.get("explore"):
                        lines.append(f"  前往：{C.MAP_BY_ID.get(obj['explore'], {}).get('name', '？')}")
        else:
            lines.append("【主线】已全部完成！🎊")
        # 支线
        side = quests.get("side", {})
        if side:
            lines.append("")
            lines.append("【支线】")
            raw = self._strip_cmd(event, "任务")
            page = self._parse_page(raw)
            side_items = list(side.items())
            page_items, pages, page = self._page_items(side_items, page, per_page=5)
            for i, (sid, sq) in enumerate(page_items, (page - 1) * 5 + 1):
                sqd = next((q for q in C.SIDE_QUESTS if q["id"] == sid), None)
                if not sqd:
                    continue
                giver = C.NPCS.get(sqd["giver"], {}).get("name", "？")
                st = sq.get("status", "active")
                obj = sqd["objective"]
                # 收集型：实时按背包材料判断
                if obj.get("collect"):
                    have = db.count_item(group_id, qq_id, obj["collect"])
                    need = obj["count"]
                    if have >= need:
                        lines.append(f"{i:>2}. 『{sqd['name']}』{sqd['desc']} [✅ 可交]")
                        lines.append(f"    材料已齐！回去找 {giver} 交任务")
                    else:
                        lines.append(f"{i:>2}. 『{sqd['name']}』{sqd['desc']} [⏳]")
                        lines.append(f"    收集：{obj['collect']} {have}/{need}")
                    continue
                mark = "✅ 可交" if st == "ready" else "⏳"
                lines.append(f"{i:>2}. 『{sqd['name']}』{sqd['desc']} [{mark}]")
                if st == "ready":
                    lines.append(f"    回去找 {giver} 交任务")
            if pages > 1:
                lines.append(f"💡 『任务 {page+1}』看下一页（共 {pages} 页）")
        else:
            lines.append("")
            lines.append("【支线】暂无——找镇上的 NPC 聊聊可能有意外收获")
        # 每日
        daily = quests.get("daily", {})
        if daily:
            lines.append("")
            lines.append("【每日】")
            for i, (dkey, dq) in enumerate(daily.items(), 1):
                dobj = dq["objective"]
                need = dobj.get("kill_any", dobj.get("kill_elite", dobj.get("kill_boss", 99)))
                lines.append(f"{i:>2}. 『{dq['name']}』{dq['desc']} ({dq.get('progress',0)}/{need})")
        else:
            lines.append("")
            lines.append("【每日】今日任务已完成，明天再来！")
        lines.append("")
        lines.append("💡 输入『每日』领取今日任务，『找 <NPC名>』接取任务")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?每日(?:\s*|$)")

    async def daily(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        if self._is_redname(qq_id):
            yield event.plain_result("☠️ 你是红名！悬赏板上的任务都被守卫收走了……（等红名消退再来）")
            return
        quests = db.get_quests(group_id, qq_id)
        if quests.get("daily"):
            yield event.plain_result("你已经有每日任务了！输入『任务』查看～")
            return
        # 随机抽 2 个每日任务
        chosen = random.sample(C.DAILY_QUESTS, min(2, len(C.DAILY_QUESTS)))
        daily = {}
        for i, dq in enumerate(chosen):
            daily[f"d{i}"] = {"name": dq["name"], "desc": dq["desc"], "objective": dq["objective"], "reward_exp": dq["reward_exp"], "reward_gold": dq["reward_gold"], "progress": 0}
        quests["daily"] = daily
        db.save_quests(group_id, qq_id, quests)
        lines = ["📜 今日任务已发布！", "━━━━━━━━━━━━"]
        for i, (dkey, dq) in enumerate(daily.items(), 1):
            lines.append(f"{i:>2}. 『{dq['name']}』{dq['desc']}")
            lines.append(f"    奖励：经验 +{dq['reward_exp']} 金币 +{dq['reward_gold']}")
        yield event.plain_result("\n".join(lines))

    def _find_npc_in_map(self, player, name_key):
        """在当前地图找 NPC，返回 (npc_id, npc_dict) 或 (None, None)"""
        cur_map = player["cur_map"]
        for nid in C.MAP_BY_ID[cur_map].get("npcs", []):
            npc = C.NPCS.get(nid)
            if npc and (name_key in npc["name"] or name_key in nid):
                return nid, npc
        return None, None

    def _npc_dialogue(self, group_id, qq_id, npc_id, npc):
        """按主线进度返回 NPC 对话（主线完成后不再重复初始台词）"""
        base = npc.get("dialogue", "……")
        # 只对发布主线的 NPC 动态化
        if "quest" not in npc.get("funcs", []):
            return base
        quests = db.get_quests(group_id, qq_id)
        main_id = quests.get("main_quest")
        # 主线全部完成（main_quest=None 且有完成记录）→ 用完成台词
        if not main_id and quests.get("completed_main"):
            return npc.get("dialogue_done", base)
        # 当前主线不是这位 NPC 发布的 → 保持初始台词（提示语会在任务逻辑里给出）
        mq = next((q for q in C.MAIN_QUESTS if q["id"] == main_id), None)
        if mq and mq["giver"] != npc_id:
            return base
        # 主线已接取或进行中 → 初始台词（任务提示在 _take_main_quest 里）
        return base

    def _take_main_quest(self, group_id, qq_id, npc_id, npc):
        """从 NPC 接主线任务；返回通知行列表"""
        lines = []
        quests = db.get_quests(group_id, qq_id)
        main_id = quests.get("main_quest")
        if not main_id:
            lines.append("🎊 主线任务已全部完成，你已是维斯特兰的传说！")
            return lines
        mq = next((q for q in C.MAIN_QUESTS if q["id"] == main_id), None)
        if not mq or mq["giver"] != npc_id:
            # 不是这个 NPC 的任务
            need_npc = C.NPCS.get(mq["giver"], {}).get("name", "？") if mq else "？"
            lines.append(f"【{npc['name']}】我现在没有任务交给你。镇长/各地首领或许有安排……")
            if mq:
                lines.append(f"📜 当前主线『{mq['name']}』由 {need_npc} 发布。")
            return lines
        st = quests.get("main_status", "pending")
        if st == "pending":
            quests["main_status"] = "active"
            quests["main_progress"] = {}
            db.save_quests(group_id, qq_id, quests)
            lines.append(f"📜 【接取任务】『{mq['name']}』")
            if mq.get("story"):
                lines.append(f"  📖 {mq['story']}")
            lines.append(f"  🎯 目标：{self._obj_text(mq['objective'])}")
            lines.append(f"  奖励：经验 +{mq['reward_exp']} 金币 +{mq['reward_gold']}")
        elif st == "ready":
            # 交任务领奖
            player = self._player(group_id, qq_id)
            db.update_player(group_id, qq_id, exp=player["exp"] + mq["reward_exp"], gold=player["gold"] + mq["reward_gold"])
            completed = list(quests.get("completed_main", []))
            completed.append(main_id)
            quests["completed_main"] = completed
            quests["main_quest"] = mq["next"]
            quests["main_status"] = "pending"
            quests["main_progress"] = {}
            db.save_quests(group_id, qq_id, quests)
            lines.append(f"✅ 【任务完成】『{mq['name']}』！")
            if mq.get("ending"):
                lines.append(f"  📖 {mq['ending']}")
            lines.append(f"  奖励：经验 +{mq['reward_exp']} 金币 +{mq['reward_gold']}")
            rep_line = self._quest_reputation(group_id, qq_id, mq["giver"])
            if rep_line:
                lines.append(f"  {rep_line}")
            if mq["next"]:
                nq = next((q for q in C.MAIN_QUESTS if q["id"] == mq["next"]), None)
                if nq:
                    lines.append(f"📜 新主线：『{nq['name']}』{nq['desc']}")
                    lines.append(f"  🎯 去找 {C.NPCS[nq['giver']]['name']} 接取新任务")
            else:
                lines.append("🎊 恭喜！你完成了全部主线任务，成为维斯特兰的传说！")
        else:
            lines.append(f"📜 你已接取『{mq['name']}』：{mq['desc']}")
        return lines

    def _obj_text(self, obj):
        if obj.get("kill"):
            return f"击败 {obj['kill']} ×{obj['count']}"
        if obj.get("collect"):
            return f"收集 {obj['collect']} ×{obj['count']}"
        if obj.get("explore"):
            return f"前往 {C.MAP_BY_ID.get(obj['explore'], {}).get('name', '？')}"
        return "？"

    def _quest_reputation(self, group_id, qq_id, npc_id):
        """完成任务时给对应势力加声望，返回提示行（如有）"""
        npc = C.NPCS.get(npc_id)
        if not npc:
            return ""
        m = C.MAP_BY_ID.get(npc["map"], {})
        area_key = m.get("area", npc["map"])
        faction = C.AREA_FACTION.get(area_key)
        if not faction:
            return ""
        db.add_reputation(group_id, qq_id, faction, 10)
        return f"🏛️ {C.FACTIONS[faction]['icon']} 声望 +10"

    @filter.regex(r"^(?:\[At:\d+\]\s*)?找(?:\s*|$)")

    async def find_npc(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        name_key = self._strip_cmd(event, "找")
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        if self._is_redname(qq_id):
            yield event.plain_result("☠️ 你是红名！城里的 NPC 都躲着你走……（等红名消退再来）")
            return
        name_key = name_key.strip()
        if not name_key:
            npcs = [C.NPCS[nid] for nid in C.MAP_BY_ID[player["cur_map"]].get("npcs", []) if nid in C.NPCS]
            if not npcs:
                yield event.plain_result("这里没有 NPC。输入『地图』看看哪里有 NPC～")
            else:
                lines = ["👥 这里的 NPC："]
                for i, n in enumerate(npcs, 1):
                    lines.append(f"{i:>2}. {n['icon']}{n['name']}（{n['title']}）")
                lines.append("💡 输入『找 <名字>』或『找 <序号>』交谈")
                yield event.plain_result("\n".join(lines))
            return
        # 序号找：『找 1』→ 当前地图第 1 个 NPC
        if name_key.isdigit():
            npcs = [C.NPCS[nid] for nid in C.MAP_BY_ID[player["cur_map"]].get("npcs", []) if nid in C.NPCS]
            idx = int(name_key)
            if idx < 1 or idx > len(npcs):
                yield event.plain_result(f"这里没有第 {idx} 位 NPC（共 {len(npcs)} 位）！『找』查看列表～")
                return
            npc = npcs[idx - 1]
            npc_id = next((nid for nid, n in C.NPCS.items() if n is npc), None)
        else:
            npc_id, npc = self._find_npc_in_map(player, name_key)
        if not npc:
            yield event.plain_result(f"你在这里没找到『{name_key}』。输入『地图』看看哪里有 NPC～")
            return
        lines = [f"{npc['icon']}【{npc['name']}】{npc['title']}", f"“{self._npc_dialogue(group_id, qq_id, npc_id, npc)}”"]
        # 功能提示
        funcs = npc.get("funcs", [])
        if "quest" in funcs:
            lines += self._take_main_quest(group_id, qq_id, npc_id, npc)
        lines += self._offer_side_quests(group_id, qq_id, npc_id, npc)
        if "shop" in funcs:
            lines.append("🏪 输入『商店』可以买东西")
        if "heal" in funcs:
            lines.append("🏨 输入『住宿』恢复满血（需要金币）")
        if "daily" in funcs:
            lines.append("📜 输入『每日』领取今日悬赏")
        if "lore" in funcs:
            lines.append("🎻 他给你讲了一个关于大陆的传说……（输入『任务』看看支线）")
        if "ency" in funcs:
            lines.append("📚 输入『百科 <材料/怪物/地图名>』查询世界知识（镇长藏书）")
        yield event.plain_result("\n".join(lines))

    def _offer_side_quests(self, group_id, qq_id, npc_id, npc):
        """NPC 有未接的支线任务时自动接取，返回通知行列表"""
        lines = []
        quests = db.get_quests(group_id, qq_id)
        side = dict(quests.get("side", {}))
        changed = False
        for sq in C.SIDE_QUESTS:
            if sq["giver"] != npc_id:
                continue
            if sq["id"] in side:
                continue
            side[sq["id"]] = {"status": "active", "progress": {}}
            changed = True
            lines.append(f"📜 【支线】『{sq['name']}』{sq['desc']}")
            lines.append(f"  奖励：经验 +{sq['reward_exp']} 金币 +{sq['reward_gold']}")
            lines.append(f"  🎯 目标：{self._obj_text(sq['objective'])}")
        if changed:
            quests["side"] = side
            db.save_quests(group_id, qq_id, quests)
        return lines

    @filter.regex(r"^(?:\[At:\d+\]\s*)?交任务(?:\s*|$)")

    async def turn_in(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        quests = db.get_quests(group_id, qq_id)
        # 主线可交
        main_id = quests.get("main_quest")
        st = quests.get("main_status", "pending")
        if main_id and st == "ready":
            mq = next((q for q in C.MAIN_QUESTS if q["id"] == main_id), None)
            if mq:
                npc = C.NPCS.get(mq["giver"])
                if npc and npc["map"] == player["cur_map"]:
                    lines = self._take_main_quest(group_id, qq_id, mq["giver"], npc)
                    yield event.plain_result("\n".join(lines))
                    return
                else:
                    giver = C.NPCS.get(mq["giver"], {}).get("name", "？")
                    giver_map = C.NPCS.get(mq["giver"], {}).get("map", "")
                    yield event.plain_result(f"你需要到 {C.MAP_BY_ID.get(giver_map, {}).get('name', '？')} 找 {giver} 交任务！")
                    return
        # 支线可交
        collect_missing = None  # 收集型材料还差的信息（用于最后提示）
        for sid, sq in list(quests.get("side", {}).items()):
            sqd = next((q for q in C.SIDE_QUESTS if q["id"] == sid), None)
            if not sqd:
                continue
            npc = C.NPCS.get(sqd["giver"])
            obj = sqd["objective"]
            # 收集型：实时检查背包材料（不依赖 ready 状态）
            if obj.get("collect"):
                have = db.count_item(group_id, qq_id, obj["collect"])
                if have >= obj["count"]:
                    if npc and npc["map"] == player["cur_map"]:
                        lines = self._complete_side_quest(group_id, qq_id, sid)
                        yield event.plain_result("\n".join(lines))
                        return
                    else:
                        giver = C.NPCS.get(sqd["giver"], {}).get("name", "？")
                        yield event.plain_result(f"支线『{sqd['name']}』材料齐了！需要找 {giver} 交任务！")
                        return
                else:
                    collect_missing = (sqd["name"], obj["collect"], have, obj["count"])
                continue
            # 击杀/探索型：按 ready 状态
            if sq.get("status") == "ready":
                if npc and npc["map"] == player["cur_map"]:
                    lines = self._complete_side_quest(group_id, qq_id, sid)
                    yield event.plain_result("\n".join(lines))
                    return
                else:
                    giver = C.NPCS.get(sqd["giver"], {}).get("name", "？")
                    yield event.plain_result(f"支线『{sqd['name']}』已达成，需要找 {giver} 交任务！")
                    return
        if collect_missing:
            name, mat, have, need = collect_missing
            yield event.plain_result(f"支线『{name}』还差 {mat} ×{need - have}（背包 {have}/{need}）！")
            return
        yield event.plain_result("没有可交的任务。输入『任务』查看进度～")

    def _complete_side_quest(self, group_id, qq_id, sid):
        """交支线任务，返回通知行列表"""
        lines = []
        quests = db.get_quests(group_id, qq_id)
        sqd = next((q for q in C.SIDE_QUESTS if q["id"] == sid), None)
        if not sqd:
            return ["未知支线任务。"]
        sq = quests.get("side", {}).get(sid)
        if not sq:
            return ["这个任务还没完成呢。"]
        obj = sqd["objective"]
        # 收集型：实时检查背包材料（不依赖 ready 状态）
        if obj.get("collect"):
            have = db.count_item(group_id, qq_id, obj["collect"])
            if have < obj["count"]:
                return [f"材料不够！需要 {obj['collect']} ×{obj['count']}，你只有 {have} 个。"]
        elif sq.get("status") != "ready":
            return ["这个任务还没完成呢。"]
        # 收集类：扣除材料
        if obj.get("collect"):
            for _ in range(obj["count"]):
                db.remove_item(group_id, qq_id, f"mat_{obj['collect']}")
        player = self._player(group_id, qq_id)
        db.update_player(group_id, qq_id, exp=player["exp"] + sqd["reward_exp"], gold=player["gold"] + sqd["reward_gold"])
        del quests["side"][sid]
        db.save_quests(group_id, qq_id, quests)
        lines.append(f"✅ 【支线完成】『{sqd['name']}』！")
        lines.append(f"  奖励：经验 +{sqd['reward_exp']} 金币 +{sqd['reward_gold']}")
        rep_line = self._quest_reputation(group_id, qq_id, sqd["giver"])
        if rep_line:
            lines.append(f"  {rep_line}")
        return lines

    @filter.regex(r"^(?:\[At:\d+\]\s*)?休息(?:\s*|$)")

    async def rest_camp(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        cur_map = C.MAP_BY_ID.get(player["cur_map"], {})
        mid = cur_map.get("id", "")
        if mid not in C.CAMP_SPOTS:
            yield event.plain_result("这里没有篝火营地！找找野外地图的营地（地图上会显示🔥篝火营地）～")
            return
        if self._in_battle(group_id, qq_id):
            yield event.plain_result("⚔️ 你正在战斗中！先解决眼前的敌人再说。")
            return
        # 30 秒冷却
        last = db.get_event_state(f"camp_{group_id}_{qq_id}")
        if last and int(time.time()) - int(last) < 30:
            left = 30 - (int(time.time()) - int(last))
            yield event.plain_result(f"⏳ 营地篝火需要添柴（{left}秒后恢复）……")
            return
        if player["hp"] >= player["max_hp"]:
            yield event.plain_result("你精神饱满，不需要休息～")
            return
        db.set_event_state(f"camp_{group_id}_{qq_id}", str(int(time.time())))
        heal = max(1, int((player["max_hp"] - player["hp"]) * 0.5))
        new_hp = min(player["max_hp"], player["hp"] + heal)
        db.update_player(group_id, qq_id, hp=new_hp)
        yield event.plain_result(
            f"🔥 你在{C.CAMP_SPOTS[mid]}的篝火旁歇了歇脚……\n"
            f"❤️ 恢复 {heal} 点生命（{new_hp}/{player['max_hp']}）\n"
            f"💡 营地只能恢复一半伤势，重伤请回旅店『住宿』～"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?住宿(?:\s*|$)")

    async def rest(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        if self._is_redname(qq_id):
            yield event.plain_result("☠️ 你是红名！旅店老板不敢收留你……（等红名消退再来）")
            return
        cur_map = C.MAP_BY_ID.get(player["cur_map"])
        if not cur_map or not cur_map.get("healer"):
            yield event.plain_result("这里没有旅店。到有旅店的地方（如维拉镇旅店）输入『住宿』～")
            return
        cost = 30
        if player["gold"] < cost:
            yield event.plain_result(f"住宿需要 {cost} 金币，你只有 {player['gold']} 金币。先去『探索』赚点钱吧～")
            return
        db.update_player(group_id, qq_id, gold=player["gold"] - cost, hp=player["max_hp"], mp=player["max_mp"])
        yield event.plain_result(
            f"🏨 你在旅店美美地睡了一觉……\n"
            f"❤️ 生命全满！💙 魔力全满！\n"
            f"花费 {cost} 金币，当前余额：{player['gold'] - cost}"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?声望(?:\s*|$)")

    async def reputation(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        rep = db.get_reputation(group_id, qq_id)
        lines = ["🏛️ 【六大势力 · 声望】", "━━━━━━━━━━━━"]
        for i, fid in enumerate(C.FACTION_ORDER, 1):
            f = C.FACTIONS[fid]
            pts = rep.get(fid, 0)
            tier = C.faction_reputation_tier(pts)
            lines.append(f"{i:>2}. {f['icon']} {f['name']}：{tier}（{pts}）")
        lines.append("")
        lines.append("💡 击杀各地怪物、完成当地任务可获得对应势力声望")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:传说|编年史)(?:\s*|$)")

    async def chronicle(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        c = random.choice(C.CHRONICLES)
        yield event.plain_result(
            f"📖 【{c['title']}】\n"
            f"━━━━━━━━━━━━\n"
            f"{c['text']}\n"
            f"━━━━━━━━━━━━\n"
            f"（维斯特兰编年史 · 输入『传说』再听一段）"
        )
