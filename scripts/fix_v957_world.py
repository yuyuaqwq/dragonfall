# -*- coding: utf-8 -*-
"""v95.7 world.py：#31 返回指令 + #38 接取指令 插入（按锚点行号插入）"""
import io

PATH = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\commands\world.py"
src = io.open(PATH, encoding="utf-8").read()
lines = src.split("\n")

# ---------- #31 返回指令：插在 portal_view 的 @filter.regex 行前 ----------
anchor = '    @filter.regex(r"^(?:\\[At:\\d+\\]\\s*)?(?:祭坛|方碑)(?:\\s*|$)")'
idxs = [i for i, l in enumerate(lines) if l.rstrip("\r") == anchor]
assert len(idxs) == 1, f"portal 锚点匹配数: {len(idxs)}"
portal_i = idxs[0]

move_back = '''    @filter.regex(r"^(?:\\[At:\\d+\\]\\s*)?返回(?:\\s*|$)")
    @no_prof_waiting()

    async def move_back(self, event: AstrMessageEvent):
        """v95.7 #31：『返回 <城镇名>』快捷回城——无视出口限制直接回城（消耗 1 体力），
        解决野外残血回城被『需先到出口』卡住的问题(#35 配套)。"""
        group_id, qq_id = self._uid(event)
        dest = self._strip_cmd(event, "返回").strip()
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        if db.get_talk_state(group_id, qq_id):
            yield event.plain_result("你还在和 NPC 交谈中！先『对话 0』结束谈话再动身吧。")
            return
        target = None
        if dest:
            for m in C.MAPS:
                if m.get("type") == "城镇区域" and dest in (m["name"], m["id"]):
                    target = m
                    break
        if not target:
            towns = "、".join(m["name"] for m in C.MAPS if m.get("type") == "城镇区域")
            yield event.plain_result(f"找不到城镇『{dest}』！可返回：{towns}(例：『返回 橡木镇』)")
            return
        if player["cur_map"] == target["id"]:
            yield event.plain_result(f"你已经在{target['name']}了～")
            return
        if self._is_redname(qq_id):
            yield event.plain_result("🛡️ 城门口的守卫拦住了你：\\"你身上沾着血腥味！红名期间禁止进入城镇！\\"\\n(红名期间不能进入安全区，去野外避避风头吧)")
            return
        if self._stamina(player) < 1:
            yield event.plain_result(
                f"⚡ 你太累了，走不动了！(体力 {self._stamina(player)}/{self._stamina_max(player)})\\n"
                "💡 恢复体力：野外营地『休息』/ 吃食物 / 旅店『住宿』，或等体力自然恢复(每10分钟+1)"
            )
            return
        self._spend_stamina(group_id, qq_id, 1, player, "返回")
        entry_sa_id = C.map_entry_subarea(target["id"])
        target_sas = target.get("subareas") or []
        first_sa = next((s for s in target_sas if s["id"] == entry_sa_id), None) or (target_sas[0] if target_sas else None)
        db.update_player(group_id, qq_id, cur_map=target["id"],
                         cur_subarea=first_sa["id"] if first_sa else "")
        db.add_visited(group_id, qq_id, target["id"])
        try:
            C.check_achievements(group_id, qq_id, self._player(group_id, qq_id))
        except Exception:
            pass
        quest_lines = self._update_explore_quests(group_id, qq_id, target["id"])
        extra = ("\\n\\n" + "\\n".join(quest_lines)) if quest_lines else ""
        yield event.plain_result(f"🧭 你一路疾行，回到了{target['name']}！(『地图』查看位置){extra}")

'''
lines[portal_i:portal_i] = move_back.split("\n")

# ---------- #38 接取指令：插在 quest_view 方法结束后（每日指令前） ----------
anchor2 = '    @filter.regex(r"^(?:\\[At:\\d+\\]\\s*)?每日(?:\\s*|$)")'
idxs2 = [i for i, l in enumerate(lines) if l.rstrip("\r") == anchor2]
assert len(idxs2) == 1, f"每日锚点匹配数: {len(idxs2)}"
daily_i = idxs2[0]

quest_accept = '''    @filter.regex(r"^(?:\\[At:\\d+\\]\\s*)?接取(?:\\s*|$)")

    async def quest_accept(self, event: AstrMessageEvent):
        """v95.7 #38：『接取任务』/『接取 <任务名>』——当前地图有发布 NPC 时直接接取，否则提示位置"""
        group_id, qq_id = self._uid(event)
        raw = self._strip_cmd(event, "接取").strip()
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        quests = db.get_quests(group_id, qq_id)
        # 主线（pending 可接）
        main_id = quests.get("main_quest")
        mq = next((q for q in C.MAIN_QUESTS if q["id"] == main_id), None) if main_id else None
        if mq and quests.get("main_status") == "pending":
            if not raw or raw in (mq["name"], "任务", "主线"):
                npc = C.NPCS.get(mq["giver"], {})
                if npc.get("map") == player["cur_map"]:
                    lines = self._take_main_quest(group_id, qq_id, mq["giver"], npc)
                    yield event.plain_result("\\n".join(lines))
                    return
                giver_map = C.MAP_BY_ID.get(npc.get("map", ""), {}).get("name", "？")
                yield event.plain_result(f"当前主线『{mq['name']}』由 {npc.get('name', '？')}(在{giver_map}) 发布，去找他对话接取～")
                return
        # 支线（未接的）
        for sq in C.SIDE_QUESTS:
            if sq["id"] in (quests.get("side") or {}):
                continue
            if not raw or raw in (sq["name"], "任务"):
                npc = C.NPCS.get(sq["giver"]) or C.ALL_WILD.get(sq["giver"]) or {}
                if npc.get("map") == player["cur_map"]:
                    lines = self._offer_side_quests(group_id, qq_id, sq["giver"], npc)
                    yield event.plain_result("\\n".join(lines))
                    return
                giver_map = C.MAP_BY_ID.get(npc.get("map", ""), {}).get("name", "？")
                yield event.plain_result(f"支线『{sq['name']}』由 {npc.get('name', '？')}(在{giver_map}) 发布，去找他对话接取～")
                return
        yield event.plain_result("没有可接取的任务。输入『任务』查看进度～")

'''
lines[daily_i:daily_i] = quest_accept.split("\n")

out = "\n".join(lines)
io.open(PATH, "w", encoding="utf-8", newline="").write(out)
print("OK: #31 返回 + #38 接取 插入完成")
