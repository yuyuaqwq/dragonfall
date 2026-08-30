# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - event_menu（v140 波3.7：地图随机事件菜单）

方案 3（deleg方案-2）：『今日事件』指令 = 全服总览三栏（今日奇遇/世界事件/彩蛋线索）；
『事件 <地图名>』深查 = 单图事件详情（今日奇遇 + POI 清单 + 彩蛋传闻）。
概率模糊带：只给档位不给数值（较高/较低/罕见），防止把随机当保底刷。

数据源：
- 今日奇遇：game/data/daily_events.py DAILY_MAP_EVENTS + core/daily_events.py today_map_event
- 世界事件：data/events.py WORLD_EVENT_POOL（当前进行中的由 social.py world_event 管理）
- 彩蛋线索：EXPLORE_EGG_EVENTS（探索彩蛋池，只给方向不给答案）

由 main.py 作为 Mixin 被 Main 继承（命令：『今日事件』『事件 <地图名>』）。
"""
import datetime

from ._platform import AstrMessageEvent, filter

from .. import content as C
from ..commands.base import CommandBase, require_player


def _fx_label(effects: dict) -> str:
    """今日奇遇效果 → 概率模糊带文案（只给档位不给数值，防把随机当保底刷）。"""
    notes = []
    _er = float(effects.get("encounter_rate", 0) or 0)
    if _er > 0.08:
        notes.append("遇怪率↑↑(较高)")
    elif _er > 0:
        notes.append("遇怪率↑(较低)")
    elif _er < -0.08:
        notes.append("遇怪率↓↓(较低)")
    elif _er < 0:
        notes.append("遇怪率↓(较低)")
    _ec = float(effects.get("event_chance", 0) or 0)
    if _ec > 0:
        notes.append("事件率↑")
    _el = float(effects.get("elite_chance", 0) or 0)
    if _el > 0:
        notes.append("精英出没")
    _lm = float(effects.get("loot_mult", 1.0) or 1.0)
    if _lm > 1.3:
        notes.append("掉落丰收")
    elif _lm > 1.0:
        notes.append("掉落略增")
    _mats = effects.get("mats") or []
    if _mats:
        notes.append(f"材料倾向：{'、'.join(str(m) for m in _mats[:3])}")
    return "，".join(notes) if notes else "风平浪静"


class EventMenuCmds(CommandBase):
    """今日事件：地图随机事件总览 / 单图深查"""

    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:今日事件|事件\s+.+|领取补给箱)$")
    @require_player()
    async def event_menu(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        # 『领取补给箱』：每日补给箱领取（SUPPLY_BOX 3 档限额）
        if "领取补给箱" in event.message_str:
            lines = self._claim_supply_box(group_id, qq_id)
            yield event.plain_result("\n".join(lines))
            return
        # 『今日事件』→ 总览；『事件 <地图名>』→ 深查（裸『事件』由 world_event 占用）
        if "今日事件" in event.message_str:
            raw = ""
        else:
            raw = self._strip_cmd(event, "事件").strip()
        # 『事件 <地图名>』深查
        if raw:
            map_name = raw.strip()
            _maps = getattr(C, "MAPS", None) or []
            target = next((m for m in _maps
                           if m.get("name") == map_name or map_name in str(m.get("name", ""))), None)
            if not target:
                yield event.plain_result(f"🗺️ 没找到地图『{map_name}』，试试『今日事件』看全部～")
                return
            lines = self._map_event_detail(group_id, qq_id, target)
            yield event.plain_result("\n".join(lines))
            return
        # 总览
        lines = self._overview(group_id, qq_id)
        yield event.plain_result("\n".join(lines))

    def _today_event_for(self, map_id: str):
        """取今日奇遇（getattr 兜底，数据未就绪返回 None）。"""
        fn = getattr(C, "today_map_event", None)
        if fn is None:
            return None
        try:
            return fn(map_id)
        except Exception:
            return None

    def _overview(self, group_id, qq_id):
        """全服总览：今日奇遇/世界事件/彩蛋线索三栏。"""
        lines = ["📅 【今日事件】", "━━━━━━━━━━━━"]
        # 一、今日奇遇（遍历全部配置了 DAILY_MAP_EVENTS 的野外图）
        daily_map = getattr(C, "DAILY_MAP_EVENTS", None) or {}
        ev_maps = []
        if daily_map:
            for mid, variants in daily_map.items():
                ev = self._today_event_for(mid)
                if not ev or not ev.get("name"):
                    continue
                mname = (getattr(C, "MAP_BY_ID", None) or {}).get(mid, {}).get("name", mid)
                note = _fx_label(ev.get("effects") or {})
                ev_maps.append(f"  🌤 {mname}：{ev['name']}——{ev.get('desc', '')}（{note}）")
        if ev_maps:
            lines.append("【今日奇遇】")
            lines.extend(ev_maps)
        else:
            lines.append("【今日奇遇】")
            lines.append("  今日风平浪静，暂无特别奇遇～")
        # 二、世界事件（当前进行中的，由 WORLD_EVENT_POOL + social 管理）
        lines.append("")
        lines.append("【世界事件】")
        wpool = getattr(C, "WORLD_EVENT_POOL", None) or []
        if isinstance(wpool, dict):
            wpool = list(wpool.values())
        active = [e for e in wpool if e.get("active")]
        if active:
            for e in active[:5]:
                lines.append(f"  🌋 {e.get('name', '未知事件')}：{e.get('desc', '')}")
        else:
            lines.append("  暂无世界事件进行中。")
        # 三、彩蛋线索（酒馆传闻式：只给方向不给答案）
        lines.append("")
        lines.append("【彩蛋线索】")
        egg_events = getattr(C, "EXPLORE_EGG_EVENTS", None) or []
        if egg_events:
            hints = [e for e in egg_events if e.get("hint")]
            shown = hints[:3] if hints else egg_events[:3]
            for e in shown:
                lines.append(f"  🥚 {e.get('hint') or e.get('desc', '有人在野外见过不寻常的东西…')}")
        else:
            lines.append("  旅人们传言，最近野外有些动静……")
        lines.append("")
        lines.append("💡 『事件 <地图名>』查看单图详情（如：事件 橡木平原）")
        return lines

    def _map_event_detail(self, group_id, qq_id, target):
        """单图事件详情：今日奇遇 + 探索事件池 + 彩蛋传闻。"""
        mid = target.get("id", "")
        lines = [f"🗺️ 【{target.get('name', mid)}】事件", "━━━━━━━━━━━━"]
        # 今日奇遇
        ev = self._today_event_for(mid)
        if ev and ev.get("name"):
            note = _fx_label(ev.get("effects") or {})
            lines.append(f"🌤 今日奇遇：{ev['name']}——{ev.get('desc', '')}（{note}）")
        else:
            lines.append("🌤 今日奇遇：无特别效果，风平浪静。")
        # 探索事件池（EXPLORE_EVENTS 该图可用事件——按地图匹配近似展示，只给档位）
        lines.append("")
        lines.append("📦 探索事件（随机触发，概率模糊带）：")
        explore = getattr(C, "EXPLORE_EVENTS", None) or []
        if explore:
            # 展示高频档位（weight 排序，不泄露精确概率）
            top = sorted(explore, key=lambda e: -e.get("weight", 0))[:6]
            for e in top:
                band = "较高" if e.get("weight", 0) >= 15 else ("普通" if e.get("weight", 0) >= 8 else "罕见")
                lines.append(f"  {e.get('name', '?')}（{band}）")
        else:
            lines.append("  （暂无探索事件配置）")
        # 彩蛋传闻
        lines.append("")
        lines.append("🥚 彩蛋传闻：")
        egg_events = getattr(C, "EXPLORE_EGG_EVENTS", None) or []
        if egg_events:
            hints = [e for e in egg_events if e.get("hint")]
            for e in (hints or egg_events)[:2]:
                lines.append(f"  {e.get('hint') or e.get('desc', '…')}")
        else:
            lines.append("  传闻这里埋着不寻常的东西……")
        return lines

    # ================= v140 波3.3：每日补给箱领取（SUPPLY_BOX） =================

    def _grant_items(self, group_id, qq_id, items, lines):
        """发放物品列表（兼容 items/materials 双表），返回实际发放清单。"""
        from .. import db
        got = []
        for iname in items:
            _iid = C.resolve("items", iname)
            if _iid in C.ITEMS:
                db.add_item(group_id, qq_id, _iid, C.ITEMS[_iid])
                got.append(iname)
            else:
                _imid = C.resolve("materials", iname)
                if _imid in C.MATERIALS:
                    db.add_item(group_id, qq_id, _imid, {
                        "name": C.display("materials", _imid),
                        "type": C.MATERIALS[_imid].get("type", "材料"),
                        "stackable": True, "price": C.MATERIALS[_imid]["price"]})
                    got.append(iname)
        return got

    def _claim_supply_box(self, group_id, qq_id):
        """领取每日补给箱（SUPPLY_BOX 3 档，限额用 event_state 记日期/周）。

        限额口径（方案 3.8）：
        - supply_mat 材料箱：每日 1 个
        - supply_tool 道具箱：每日 1 个（原设计累计 3 个每日任务，简化按日限）
        - supply_rich 豪华箱：每周 ≤2 个（原设计累计 7 个每日任务，简化按周限）
        """
        from .. import db
        today = datetime.date.today().isoformat()
        # 周起始（周一）
        monday = (datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())).isoformat()
        boxes = getattr(C, "SUPPLY_BOX", None) or []
        if not boxes:
            return ["📦 补给箱数据缺失，请联系管理～"]
        lines = ["📦 【每日补给箱】", "━━━━━━━━━━━━"]
        claimed_any = False
        for box in boxes:
            bid = box.get("id", "")
            limit = box.get("limit", "")
            # 限额判定
            if limit == "daily_1":
                key = f"supply_{bid}_{qq_id}_{today}"
                if db.get_event_state(key):
                    lines.append(f"  ⏳ {box.get('name', bid)}：今日已领取～")
                    continue
                db.set_event_state(key, "1")
            elif limit == "daily3":
                key = f"supply_{bid}_{qq_id}_{today}"
                if db.get_event_state(key):
                    lines.append(f"  ⏳ {box.get('name', bid)}：今日已领取～")
                    continue
                db.set_event_state(key, "1")
            elif limit == "weekly2_daily7":
                # 每周 ≤2：数本周已领次数
                wk = f"supply_{bid}_{qq_id}_wk_{monday}"
                cnt = int(db.get_event_state(wk) or 0)
                if cnt >= 2:
                    lines.append(f"  ⏳ {box.get('name', bid)}：本周已领 {cnt}/2～")
                    continue
                db.set_event_state(wk, str(cnt + 1))
            else:
                continue
            # 发放
            got = self._grant_items(group_id, qq_id, box.get("items", []), lines)
            claimed_any = True
            if got:
                lines.append(f"  🎁 {box.get('name', bid)}：{'、'.join(got)}！")
        if not claimed_any:
            lines.append("  今天/本周的补给箱都已领过啦，明天再来吧～")
        lines.append("")
        lines.append("💡 补给箱内容：图纸残页/淬火石/强化石/幸运符等（每日 0 点重置）")
        return lines
