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

★ B8.2 线3（2026-09-13）命令层薄壳化：本模块只留「注册 + 解析参数 + 取玩家 + 调包 + 拼文案」。
  · **读表改从内容包取**（`content/event_menu.py`，真源 `game/data/maps.py` / `events.py` /
    `items.py`，单向导出为包内 `worlds`/`events`/`items` 域）：
        `C.MAPS`→`_EM.MAPS`、`C.MAP_BY_ID`→`_EM.MAP_BY_ID`、`C.EXPLORE_EVENTS`→`_EM.EXPLORE_EVENTS`、
        `C.EXPLORE_EGG_EVENTS`→`_EM.EXPLORE_EGG_EVENTS`、`C.ITEMS`/`C.resolve("items",…)`→
        `_EM.ITEMS`/`_EM.resolve_item(...)`。
  · **今日奇遇的纯逻辑**（`core/daily_events.py:21 today_map_event`）也搬进包
    （`content/event_menu.py:daily_event_for`），表由本模块注入。
  · **三张未进包的表**（父任务：不许新建未预声明的域）仍由本模块直读宿主 data 层：
        `DAILY_MAP_EVENTS`（`game/data/daily_events.py:18`，20 图）
        `WORLD_EVENT_POOL`（`game/data/world.py:8`，14 条）
        `SUPPLY_BOX`（`game/data/quest_add_v140.py:121`，3 档）
    —— 报告 §缺口已点名「需要新域 daily_events / world_events / supply_box」。
  · 文案表口径**不动**：`supply.*` 的 `T.static/T.text` 调用点必须留本文件
    （`tests/test_texts_table.py:81 WIRED` 按本文件 AST 做「声明 ↔ 调用点」双向对账）。
  · 渲染文案**一字未改**（拼串、档位带、emoji、缩进全部原样）。
"""
import datetime

from ._platform import AstrMessageEvent

from ._declared import declared

from .. import db
from ..core import texts as T
from ..commands.base import CommandBase, require_player

# ★ B8.2 线3：读包（宿主 `..content` 聚合层不再被本命令 import）。
# `package_apply()` = 本进程唯一的包加载口（包根进 sys.path → `content` 成命名空间包），幂等；
# 失败**大声抛**（读不到域 = 事件面板空转，比报错难查）。
from .. import bootstrap as _bootstrap          # noqa: E402

_bootstrap.package_apply()
from content import event_menu as _EM           # noqa: E402

# ★ 未进包的三张表（缺口见报告）：宿主 data 层直读
from ..data.daily_events import DAILY_MAP_EVENTS as _DAILY_MAP_EVENTS      # noqa: E402
from ..data.quest_add_v140 import SUPPLY_BOX as _SUPPLY_BOX                # noqa: E402
from ..data.world import WORLD_EVENT_POOL as _WORLD_EVENT_POOL             # noqa: E402


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

    @declared("event_menu")
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
            _maps = _EM.MAPS
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
        """取今日奇遇（逻辑在包 `content/event_menu.py:daily_event_for`；表未进包 → 本模块注入）。"""
        try:
            return _EM.daily_event_for(map_id, _DAILY_MAP_EVENTS)
        except Exception:
            return None

    def _overview(self, group_id, qq_id):
        """全服总览：今日奇遇/世界事件/彩蛋线索三栏。"""
        lines = ["📅 【今日事件】", "━━━━━━━━━━━━"]
        # 一、今日奇遇（遍历全部配置了 DAILY_MAP_EVENTS 的野外图）
        daily_map = _DAILY_MAP_EVENTS or {}
        ev_maps = []
        if daily_map:
            for mid, variants in daily_map.items():
                ev = self._today_event_for(mid)
                if not ev or not ev.get("name"):
                    continue
                mname = (_EM.MAP_BY_ID or {}).get(mid, {}).get("name", mid)
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
        wpool = _WORLD_EVENT_POOL or []
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
        egg_events = _EM.EXPLORE_EGG_EVENTS or []
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
        explore = _EM.EXPLORE_EVENTS or []
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
        egg_events = _EM.EXPLORE_EGG_EVENTS or []
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
        got = []
        for iname in items:
            _iid = _EM.resolve_item(iname)
            if _iid in _EM.ITEMS:
                db.add_item(group_id, qq_id, _iid, _EM.ITEMS[_iid])
                got.append(iname)
            else:
                # 材料兜底：真源 `C.MATERIALS`（材料域未进包 —— 见报告 §缺口）。
                # 该分支在真源数据下**结构性不可达**（证明见 `content/event_menu.py` ③）：
                # 实测 SUPPLY_BOX 三档 9/9 物品名都命中上面的 ITEMS 分支。
                _imid = _EM.resolve_material(iname)
                if _imid in _EM.MATERIALS:
                    db.add_item(group_id, qq_id, _imid, {
                        "name": _EM.display_material(_imid),
                        "type": _EM.MATERIALS[_imid].get("type", "材料"),
                        "stackable": True, "price": _EM.MATERIALS[_imid]["price"]})
                    got.append(iname)
        return got

    def _claim_supply_box(self, group_id, qq_id):
        """领取每日补给箱（SUPPLY_BOX 3 档，限额用 event_state 记日期/周）。

        限额口径（方案 3.8）：
        - supply_mat 材料箱：每日 1 个
        - supply_tool 道具箱：每日 1 个（原设计累计 3 个每日任务，简化按日限）
        - supply_rich 豪华箱：每周 ≤2 个（原设计累计 7 个每日任务，简化按周限）
        """
        today = datetime.date.today().isoformat()
        # 周起始（周一）
        monday = (datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())).isoformat()
        boxes = _SUPPLY_BOX or []
        if not boxes:
            return [T.static("supply.missing")]
        lines = [T.static("supply.title"), "━━━━━━━━━━━━"]
        claimed_any = False
        for box in boxes:
            bid = box.get("id", "")
            limit = box.get("limit", "")
            # 限额判定
            if limit == "daily_1":
                key = f"supply_{bid}_{qq_id}_{today}"
                if db.get_event_state(key):
                    lines.append(T.text("supply.daily_done", name=box.get("name", bid)))
                    continue
                db.set_event_state(key, "1")
            elif limit == "daily3":
                key = f"supply_{bid}_{qq_id}_{today}"
                if db.get_event_state(key):
                    lines.append(T.text("supply.daily_done", name=box.get("name", bid)))
                    continue
                db.set_event_state(key, "1")
            elif limit == "weekly2_daily7":
                # 每周 ≤2：数本周已领次数
                wk = f"supply_{bid}_{qq_id}_wk_{monday}"
                cnt = int(db.get_event_state(wk) or 0)
                if cnt >= 2:
                    lines.append(T.text("supply.weekly_done", name=box.get("name", bid),
                                         cnt=cnt))
                    continue
                db.set_event_state(wk, str(cnt + 1))
            else:
                continue
            # 发放
            got = self._grant_items(group_id, qq_id, box.get("items", []), lines)
            claimed_any = True
            if got:
                lines.append(T.text("supply.granted", name=box.get("name", bid),
                                     items="、".join(got)))
        if not claimed_any:
            lines.append(T.static("supply.all_done"))
        lines.append("")
        lines.append(T.static("supply.tip"))
        return lines
