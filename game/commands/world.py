# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - world（world）

由 main.py 拆分而来，作为 Mixin 被 Main 继承。
"""
import functools
import inspect
import json
import random
import re
import time

from ._platform import AstrMessageEvent, filter, MessageChain

from .. import content as C
from .. import db
from .. import engine as E
from ..core.stats import hp_stage_mult
from ..core.formation import formation_view, alive_units  # v2 多对多站位图文案行
from .. import battle as BT
from ..commands.base import CommandBase, no_prof_waiting, require_player

# 任务目标类型 → 进度展示行（v101.3：加新目标类型 = 加一行，quest_view 零改动）
def _kill_prog_count(obj, prog):
    """v105 M19 P2：击杀进度聚合读——兼容旧存档老 key（v95.7 之前进度记
    monster['name'] 而非 obj['kill']，如『精英森林狼』），面板不再显示 0/N 孤儿计数。
    目标 key 有值用目标 key；为 0 时汇总其余包含目标名的历史 key。"""
    v = prog.get(obj["kill"], 0)
    if v == 0:
        v = sum(c for k, c in prog.items() if k != obj["kill"] and obj["kill"] in k)
    return v


_OBJ_PROGRESS_LINES = {
    "kill":    lambda obj, prog: f"  进度：{_kill_prog_count(obj, prog)}/{obj['count']}",
    "collect": lambda obj, prog: f"  收集：{prog.get(obj['collect'], 0)}/{obj['count']}",
    "explore": lambda obj, prog: f"  前往：{C.MAP_BY_ID.get(obj['explore'], {}).get('name', '？')}",
    "talk":    lambda obj, prog: f"  交谈：与 {C.NPCS.get(obj['talk'], {}).get('name', '？')} 对话",
}

# v104 M23 修复：许愿井彩蛋概率独立常量（原先误用 MOVE_ENCOUNTER_CHANCE=0.25 移动撞怪概率，语义错用）
WISH_WELL_EGG_CHANCE = 0.05

# v116 任务系统定稿 §3.4：每日任务单日完成上限（防刷）——达到后『每日』不再抽新任务
DAILY_LIMIT = 10
# v116 每日任务重复衰减档位：第 N 次完成同任务 → 奖励乘数
# （0 = 首刷 100%，1 = 第 2 次 60%，2 = 第 3 次 30%，≥3 = 第 4 次起 10%）
_DAILY_REPEAT_FACTORS = (1.0, 0.6, 0.3, 0.1)
# daily 字典内保留元数据键（跨天字段/完成计数/重复计数），任务面板与抽取逻辑一律跳过
_DAILY_META_KEYS = ("_date", "_completed", "_repeat")


def _daily_repeat_pct(repeat):
    """重复完成同日常任务 → 衰减后的发奖比例（百分比）。repeat = 今日已完成的次数。
    第 1 次 100%、第 2 次 60%、第 3 次 30%、第 4 次起 10%（§3.4 板规则）。"""
    f = _DAILY_REPEAT_FACTORS[repeat] if repeat < len(_DAILY_REPEAT_FACTORS) else _DAILY_REPEAT_FACTORS[-1]
    return int(round(f * 100))


def _settle_daily_quest(inst, group_id, qq_id, daily, dq, lines=None):
    """v125.1 P2：每日任务达标结算单点（world._bump_daily_progress 与 combat._update_quests
    双副本收敛）。职责：完成计数(_completed)/重复衰减计数(_repeat)、经验金币发放、升级、
    通知行。调用方负责进度 +1 与达标判断，结算后自行 del 任务键；lines=None 时不输出通知。"""
    daily["_completed"] = int(daily.get("_completed", 0) or 0) + 1
    rpt = int(daily.get("_repeat", {}).get(dq["name"], 0) or 0)
    _rep = dict(daily.get("_repeat", {}) or {})
    _rep[dq["name"]] = rpt + 1
    daily["_repeat"] = _rep
    if lines is not None:
        _dec = dq.get("repeat", 0)
        if _dec:
            _pct = _daily_repeat_pct(_dec)
            lines.append(f"📜 每日『{dq['name']}』完成！重复完成，奖励衰减 {_pct}%：经验 +{dq['reward_exp']} 金币 +{dq['reward_gold']}")
        else:
            lines.append(f"📜 每日『{dq['name']}』完成！奖励：经验 +{dq['reward_exp']} 金币 +{dq['reward_gold']}")
    player = inst._player(group_id, qq_id)
    player["exp"] += dq["reward_exp"]
    player["gold"] += dq["reward_gold"]
    player["_title_bonus"] = inst._title_bonus(group_id, qq_id)
    lv_logs, player = E.check_player_level_up(group_id, qq_id, player)
    db.update_player(group_id, qq_id, exp=player["exp"], gold=player["gold"], level=player["level"], hp=player["hp"], mp=player["mp"], max_hp=player["max_hp"], max_mp=player["max_mp"], skills=player["skills"], attr_pts=player.get("attr_pts", 0), skill_points=player.get("skill_points", 0), learned_skills=player.get("learned_skills", []))
    if lines is not None and lv_logs:
        lines.append("")
        lines += lv_logs


def _daily_need(dq):
    """每日任务需求数（面板显示用）。objective 单键值即达标数（kill_any:10 等）。
    v125.1 P2：存档缺 objective 时回读 DAILY_QUESTS 定义；仍无定义返回 None，
    面板只显示实际进度，不再兜底假 99。"""
    dobj = (dq or {}).get("objective") or {}
    for _v in dobj.values():
        if isinstance(_v, int) and _v > 0:
            return _v
    _def = next((q for q in C.DAILY_QUESTS if q.get("name") == (dq or {}).get("name")), None)
    if _def:
        for _v in (_def.get("objective") or {}).values():
            if isinstance(_v, int) and _v > 0:
                return _v
    return None


class WorldCmds(CommandBase):

    def _map_facilities(self, cur_map: dict, player: dict = None, sa_id_override: str = None) -> list:
        """当前地图功能性设施清单（商店/旅店/铁匠/方碑/垂钓/篝火/矿脉/采集）。

        v87.13 与 _map_scene 拆分：设施 = 干事的功能入口；场景 = 氛围景物。
        v87.13b sa_id_override：移动到达展示时目标子区域还没写进 player，显式传入落点子区域 id。
        """
        lines = []
        mid = cur_map.get("id", "")
        portals = db.get_portals(player["qq_id"]) if player else []
        # v86 子区域：设施/NPC 按当前子区域过滤（无子区域/无标记则地图级）
        sa_obj = None
        sa_id = sa_id_override or (player or {}).get("cur_subarea") or ""
        for _sa in (cur_map.get("subareas") or []):
            if _sa["id"] == sa_id:
                sa_obj = _sa
                break
        sa_shop = sa_obj.get("shop") if sa_obj else None
        sa_healer = sa_obj.get("healer") if sa_obj else None
        # 设施
        if (sa_shop is not None and sa_shop) or (sa_shop is None and cur_map.get("shop")):
            lines.append("🏪 商店(『购买』)")
        if (sa_healer is not None and sa_healer) or (sa_healer is None and cur_map.get("healer")):
            lines.append("🏨 旅店(『住宿』恢复全状态)")
        if mid in C.ENHANCE_SMITH_MAPS:
            _sa_name = sa_obj.get("name", "") if sa_obj else ""
            _sa_funcs = (sa_obj.get("funcs") or []) if sa_obj else []
            # O94 修复：与 base._at_smith 同源——鹿角淬火坊(white_deer_8)补入强化可用区域，
            # 地图设施清单同步显示铁匠铺入口（否则设施显示与『强化』可用性矛盾）
            _smith = "craft" in _sa_funcs or C.SUBAREA_KIND.get(sa_id) in ("smith", "enhance")
            if _smith:
                lines.append("🔨 铁匠铺(『强化』『附魔』)")
        # 旅者方碑（只在中心广场/首个子区域提示）
        if mid in C.PORTALS:
            p = C.PORTALS[mid]
            if sa_obj is None or sa_obj is cur_map.get("subareas", [None])[0]:
                if mid in portals:
                    lines.append(f"🌌 {p['icon']}{p['name']}(已激活，『传送 <名称>』)")
                else:
                    lines.append(f"🌌 {p['icon']}{p['name']}(『激活』解锁传送点)")
        # F2 副本入口设施化：funcs 含 instance 的子区域 = 副本入口设施（消费 F1 标记）
        if sa_obj and "instance" in (sa_obj.get("funcs") or []):
            for _ik, _iv in C.INSTANCES.items():
                _ie = _iv.get("entry") or {}
                if _ie.get("map") == mid and _ie.get("subarea") == sa_id:
                    lines.append(f"🏰 此处是【{_iv.get('name', '副本')}】入口（『副本 {_iv.get('name', '')}』进入）")
                    break
        # 自然互动（9.3：垂钓点显示特色描述；v87.17 子区域绑定：不在对应子区域不显示）
        if mid in C.FISHING_SPOTS:
            _fi = C.FISHING_SPOTS[mid]
            _want_sa = _fi.get("subarea", "") if isinstance(_fi, dict) else ""
            if not (_want_sa and (sa_obj is None or sa_obj.get("id") != _want_sa)):
                _fname = _fi["name"] if isinstance(_fi, dict) else _fi
                _fneed = _fi.get("min_lv", 1) if isinstance(_fi, dict) else 1
                _flv = db.get_prof_level(player.get("group_id", "g"), player["qq_id"], "fishing") if player else 1
                _lock = " 🔒" if _flv < _fneed else ""
                _fdesc = _fi.get("desc", "") if isinstance(_fi, dict) else ""
                lines.append(f"🎣 垂钓点·{_fname}(垂钓Lv.{_fneed}){_lock}(『垂钓』){(' · ' + _fdesc) if _fdesc else ''}")
        if mid in C.CAMP_SPOTS:
            _cp = C.CAMP_SPOTS[mid]
            _cp_sa = _cp.get("subarea", "") if isinstance(_cp, dict) else ""
            if not (_cp_sa and (sa_obj is None or sa_obj.get("id") != _cp_sa)):
                _cp_name = _cp.get("name", "营地") if isinstance(_cp, dict) else str(_cp)
                lines.append(f"🔥 篝火营地·{_cp_name}(『休息』恢复一半生命)")
        # v105R3 M14 P3-3：城镇地图不显示矿脉（『挖掘』已被城镇拦截，防"⛏️ 矿脉"与"城镇安全区"观感冲突）
        if mid in C.MINE_SPOTS and cur_map.get("type") != "城镇区域":
            _mi = C.MINE_SPOTS[mid]
            _mi_sa = _mi.get("subarea", "") if isinstance(_mi, dict) else ""
            if not (_mi_sa and (sa_obj is None or sa_obj.get("id") != _mi_sa)):
                _mi_name = _mi.get("name", "矿脉") if isinstance(_mi, dict) else str(_mi)
                lines.append(f"⛏️ 矿脉·{_mi_name}(『挖掘』)")
        if cur_map.get("type") == "野外" and mid not in C.CAMP_SPOTS:
            lines.append("🌿 野地可采集(『采集』)")
        return lines

    def _map_scene(self, cur_map: dict, player: dict = None, sa_id_override: str = None) -> tuple:
        """当前子区域场景元素清单（POI 探索点 + PROPS 场景元素 + 副本内联 POI）。

        v87.13 从 _map_interactions 拆出：氛围/景物类，标题用「✨ 场景」。
        v87.13b sa_id_override：移动到达展示时目标子区域还没写进 player，显式传入落点子区域 id。
        v132 返回拆分：("🔎 可探索触发" POI 行列表, "✨ 可交互场景" PROPS 行列表)——
        鱼鱼拍板新排版：探索触发与直接交互分两区展示（城镇版/野外版同一套区块）。
        v137 副本地图化：副本内（玩家开本且当前房间）时，经 rooms[cur_room].pois_left
        过滤子区域挂载 POI——探索完即空的资源池语义；已消费的 POI 不再显示。
        """
        poi_lines, prop_lines = [], []
        mid = cur_map.get("id", "")
        sa_id = sa_id_override or (player or {}).get("cur_subarea") or ""
        # v87 02 章 7.6：探索点 POI 显示（子区域挂载）
        if player:
            poi_ids = C.subarea_pois(mid, sa_id)
            # v137 副本地图化：副本内 POI 显示受 rooms[cur_room].pois_left 过滤（资源池语义）
            _inst_row = None
            try:
                _inst_row = self._instance_battle_for(player.get("group_id", "g"), player.get("qq_id"))
            except Exception:
                _inst_row = None
            if _inst_row and (_inst_row["state"].get("mode") == "map" or _inst_row["state"].get("rooms")):
                _st = _inst_row["state"]
                _rooms = _st.get("rooms") or {}
                _rkey = sa_id or (player or {}).get("cur_subarea") or ""
                _rstate = _rooms.get(_rkey) or {}
                _left = _rstate.get("pois_left")
                if _left is not None:
                    poi_ids = [pid for pid in poi_ids if pid in _left]
            for _pid in poi_ids:
                _p = C.POIS.get(_pid)
                if _p:
                    # v137 副本 POI（dungeon_pois）无 icon 字段——用 type 映射或 ❓ 兜底
                    _icon = _p.get("icon")
                    if not _icon:
                        _icon = {"chest": "📦", "campfire": "🔥", "rune_stone": "🗿",
                                 "mechanism": "⚙️", "trap": "⚠️", "supply": "🎒",
                                 "corpse": "💀"}.get(_p.get("type"), "❓")
                    poi_lines.append(f"{_icon} {_p['name']}(『探索』有机会发现)")
        # v87.9 场景元素 PROPS 显示（子区域挂载，直接交互）
        # v87.11 支持专属名：挂载条目可为 (prop_id, 专属名) 元组
        if player:
            prop_ids = C.subarea_props(mid, sa_id)
            for _entry in prop_ids:
                _ppid, _label = C.prop_entry(_entry)
                _pp = C.PROPS.get(_ppid)
                if _pp:
                    _name = _label or _pp['name']
                    prop_lines.append(f"{_pp['icon']} {_name}(『交互 {_name}』)")
        # v87.2 副本地图化：内联 POI（副本层自带 pois → 直接显示，『调查 <名称>』互动）
        for _p in (cur_map.get("pois") or []):
            if isinstance(_p, dict) and _p.get("name"):
                poi_lines.append(f"{_p.get('icon', '❓')} {_p['name']}：{_p.get('hint', '')}(『调查 {_p['name']}』)")
        # v87.4 NPC 不再进场景（由地图面板「👥 这里的 NPC」统一显示，避免重复）
        return poi_lines, prop_lines

    def _visible_sas(self, player: dict, cur_map: dict, group_id: str, qq_id: str) -> list:
        """v115 当前位置地图中**可见**的子区域列表（供面板/移动统一使用）。

        隐藏房间（A 提供 is_hidden_room）未揭示（C.reveal_met）→ 不可见（不列出）。
        若 A 尚未装好网状/hidden 接口，用 getattr 兜底：is_hidden_room 缺失时全部可见。
        """
        sas = cur_map.get("subareas") or []
        map_id = cur_map.get("id", "")
        is_hidden = getattr(C, "is_hidden_room", None)
        reveal_met = getattr(C, "reveal_met", None)
        visible = []
        for sa in sas:
            sa_id = sa.get("id", "")
            if is_hidden is None or reveal_met is None:
                visible.append(sa)
                continue
            try:
                if is_hidden(map_id, sa_id) and not reveal_met(sa.get("reveal"), group_id, qq_id, map_id):
                    continue  # 隐藏未揭示 → 跳过
            except Exception:
                pass
            visible.append(sa)
        return visible

    @staticmethod
    def _conn_target(conn) -> tuple:
        """解析可前往连接项 → (目标地图 dict, 指定子区域 id 或 None)
        v87.5 支持两字段配置：'map_id' 或 ('map_id', 'subarea_id')"""
        if isinstance(conn, tuple):
            return C.MAP_BY_ID[conn[0]], conn[1]
        return C.MAP_BY_ID[conn], None

    @staticmethod
    def _conn_subarea_name(nm: dict, want_sa) -> str:
        """目标地图的落点子区域显示名(默认入口子区域，可指定)

        v87.16：无指定时用 map_entry_subarea（进城落点=出口/入口），不再是首个子区域
        """
        sas = nm.get("subareas") or []
        if not sas:
            return ""
        if want_sa:
            for s in sas:
                if s["id"] == want_sa:
                    return f" · {s['name']}"
            return ""
        # v87.16：跨图落点 = 城镇出口（镇郊）/ 野外入口，显示与实际到达一致
        entry_id = C.map_entry_subarea(nm.get("id", ""))
        if entry_id:
            for s in sas:
                if s["id"] == entry_id:
                    return f" · {s['name']}"
        return f" · {sas[0]['name']}"

    # ---------------- v68 地契房产 ----------------

    def _home_map_id(self, qq_id):
        return f"home_{qq_id}"

    @filter.regex(r"^(?:\[At:\d+\]\s*)?地契(?:[\s\S]*)$")
    @require_player()
    async def deed_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        # v84 『地契 升级』→ 房屋升级
        raw_arg = self._strip_cmd(event, "地契").strip()
        if raw_arg.startswith("升级"):
            async for _r in self._deed_upgrade(event, group_id, qq_id, player):
                yield _r
            return
        deed = player.get("deed", "") or ""
        lines = ["🏠 【地契大厅】", "━━━━━━━━━━━━"]
        if deed and deed in C.PROPERTIES:
            prop = C.PROPERTIES[deed]
            dlv = int(player.get("deed_lv", 1) or 1)
            hl = C.HOUSE_LEVELS.get(dlv, C.HOUSE_LEVELS[1])
            lines.append(f"✅ 我的地契：{prop['name']}({C.MAP_BY_ID.get(prop['map'], {}).get('name', '？')})")
            lines.append(f"   🏗️ {hl['name']} Lv.{dlv} ｜ 仓库 {hl['storage']} 格 ｜ 回家恢复 {int(hl['heal_pct'] * 100)}%")
            if dlv < C.HOUSE_MAX_LEVEL:
                nxt = C.HOUSE_LEVELS[dlv + 1]
                cost = f"{nxt['upgrade_cost']['gold']} 金币 + " + " + ".join(f"{C.display('materials', m)}×{c}" for m, c in nxt['upgrade_cost']['mats'].items())
                lines.append(f"   ⬆️ 升级 Lv.{dlv + 1}【{nxt['name']}】：{cost}(『地契 升级』)")
            else:
                lines.append("   ⭐ 已满级宅邸！")
            lines.append(f"   『回家』进入，『卖房』退契(返还 {int(C.HOUSE_REFUND.get(dlv, 0.5) * 100)}%)")
        else:
            lines.append("你还没有房产。以下地皮在出售：")
            for i, (pid, prop) in enumerate(C.PROPERTIES.items(), 1):
                mname = C.MAP_BY_ID.get(prop["map"], {}).get("name", "？")
                lines.append(f"{i:>2}. {prop['name']} ｜ {prop['price']} 金币 ｜ {mname}")
                lines.append(f"     {prop['desc']}")
            lines.append(self._tip("house"))
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?买房(?:[\s\S]*)$")
    @require_player()
    async def deed_buy(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if player.get("deed"):
            yield event.plain_result("你已经有一张地契了！『地契』查看，『卖房』可以退契～")
            return
        raw = self._strip_cmd(event, "买房").strip()
        if not raw.isdigit():
            yield event.plain_result("格式：买房 <编号>！『地契』查看在售地皮～")
            return
        idx = int(raw)
        props = list(C.PROPERTIES.items())
        if idx < 1 or idx > len(props):
            yield event.plain_result(f"没有第 {idx} 块地皮(共 {len(props)} 块)！『地契』查看～")
            return
        pid, prop = props[idx - 1]
        price = prop["price"]
        if player["gold"] < price:
            yield event.plain_result(f"买【{prop['name']}】需要 {price} 金币，你只有 {player['gold']}。攒够钱再来吧！")
            return
        # v104 M09 P1 修复：房产全服唯一·先到先得（25 章承诺）——买时登记房主，他人已持有则拦截
        _owner = db.get_event_state(f"deed_owner_{pid}")
        if _owner and str(_owner) != str(qq_id):
            yield event.plain_result(f"🏠 【{prop['name']}】已经被其他冒险者买下了！先到先得，看看其他地皮吧～")
            return
        db.update_player(group_id, qq_id, gold=player["gold"] - price, deed=pid)
        db.set_event_state(f"deed_owner_{pid}", str(qq_id))  # v104 M09 P1：登记房主（卖房时释放）
        yield event.plain_result(
            f"🏠 恭喜置业！你买下了【{prop['name']}】(花费 {price} 金币)\n"
            f"『回家』入住，『地契』查看详情，『仓库』管理家当～"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?卖房(?:[\s\S]*)$")
    @require_player()
    async def deed_sell(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        deed = player.get("deed", "") or ""
        if not deed or deed not in C.PROPERTIES:
            yield event.plain_result("你没有房产，卖不了～『地契』看看在售地皮！")
            return
        prop = C.PROPERTIES[deed]
        dlv = int(player.get("deed_lv", 1) or 1)
        refund_pct = C.HOUSE_REFUND.get(dlv, 0.5)
        refund = int(prop["price"] * refund_pct)
        db.update_player(group_id, qq_id, gold=player["gold"] + refund, deed="", deed_lv=1)
        db.set_event_state(f"deed_owner_{deed}", "")  # v104 M09 P1：卖房释放产权（先到先得）
        yield event.plain_result(f"🏠 你卖掉了【{prop['name']}】({C.HOUSE_LEVELS.get(dlv, C.HOUSE_LEVELS[1])['name']} Lv.{dlv})，退还 {refund} 金币({int(refund_pct * 100)}%)。")

    async def _deed_upgrade(self, event, group_id, qq_id, player):
        """v84 房屋升级(25 章三)：『地契 升级』消耗金币+材料升房屋等级"""
        deed = player.get("deed", "") or ""
        if not deed or deed not in C.PROPERTIES:
            yield event.plain_result("你没有房产，升级不了～『地契』看看在售地皮！")
            return
        dlv = int(player.get("deed_lv", 1) or 1)
        if dlv >= C.HOUSE_MAX_LEVEL:
            yield event.plain_result("你的房屋已经是满级宅邸啦！")
            return
        nxt = C.HOUSE_LEVELS[dlv + 1]
        cost = nxt["upgrade_cost"]
        # 金币检查
        if player["gold"] < cost["gold"]:
            yield event.plain_result(
                f"升级 Lv.{dlv + 1}【{nxt['name']}】需要 {cost['gold']} 金币，你只有 {player['gold']}。")
            return
        # 材料检查
        inv = db.get_inventory(group_id, qq_id)
        inv_map = {}
        for it in inv:
            nm = it["data"].get("name", "")
            inv_map[nm] = inv_map.get(nm, 0) + it.get("count", 1)
        for mid, need in cost["mats"].items():
            mname = C.display("materials", mid)
            if inv_map.get(mname, 0) < need:
                yield event.plain_result(
                    f"升级 Lv.{dlv + 1}【{nxt['name']}】需要 {mname}×{need}，你只有 {inv_map.get(mname, 0)}。去『挖掘』吧～")
                return
        # 扣材料 + 扣金币 + 升级
        for mid, need in cost["mats"].items():
            mname = C.display("materials", mid)
            for _ in range(need):
                found = next((it for it in inv if it["data"].get("name") == mname), None)
                if found:
                    db.remove_item(group_id, qq_id, found["key"], 1)
                    inv = db.get_inventory(group_id, qq_id)
        db.update_player(group_id, qq_id, gold=player["gold"] - cost["gold"], deed_lv=dlv + 1)
        hl = C.HOUSE_LEVELS[dlv + 1]
        yield event.plain_result(
            f"🔨 叮叮当当一阵敲打——房屋升级为【{hl['name']}】Lv.{dlv + 1}！\n"
            f"📦 仓库扩容至 {hl['storage']} 格 ｜ 回家恢复 {int(hl['heal_pct'] * 100)}%"
            + (f" ｜ 铺面挂机位 +{hl['stall_slots']}" if hl["stall_slots"] else "")
            + (f"\n💡 满级宅邸解锁专属传送点(『回家』可直达)" if dlv + 1 >= C.HOUSE_MAX_LEVEL else ""))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?回家(?:[\s\S]*)$")
    @require_player()
    @no_prof_waiting()
    async def go_home(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not (player.get("deed") or ""):
            yield event.plain_result("你没有房产！『地契』看看在售地皮，『买房 <编号>』置业～")
            return
        if self._in_battle(group_id, qq_id):
            yield event.plain_result("你正在战斗中！先解决眼前的敌人(攻击/逃跑)")
            return
        # v84 回家恢复（按房屋等级 heal_pct）
        dlv = int(player.get("deed_lv", 1) or 1)
        hl = C.HOUSE_LEVELS.get(dlv, C.HOUSE_LEVELS[1])
        heal_pct = hl.get("heal_pct", 0.5)
        new_hp = max(player.get("hp", 0), int(player.get("max_hp", 1) * heal_pct))
        new_mp = max(player.get("mp", 0), int(player.get("max_mp", 1) * heal_pct))
        db.update_player(group_id, qq_id, cur_map=self._home_map_id(qq_id), cur_subarea="", hp=new_hp, mp=new_mp)
        yield event.plain_result(
            f"🏠 你回到了自己的家({hl['name']})，炭火噼啪作响，安心～\n"
            f"💚 恢复至 {new_hp}/{player.get('max_hp', 1)} HP ｜ 💙 {new_mp}/{player.get('max_mp', 1)} MP")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?出门(?:[\s\S]*)$")
    @require_player()
    @no_prof_waiting()
    async def go_out(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        cur = player.get("cur_map", "")
        if not cur.startswith("home_"):
            yield event.plain_result("你不在家里，不需要出门～")
            return
        deed = player.get("deed", "") or ""
        prop = C.PROPERTIES.get(deed)
        target = prop["map"] if prop else C.START_MAP
        tgt_sas = C.MAP_BY_ID.get(target, {}).get("subareas") or []
        first_sa = tgt_sas[0] if tgt_sas else None
        db.update_player(group_id, qq_id, cur_map=target,
                         cur_subarea=first_sa["id"] if first_sa else "")
        yield event.plain_result(f"🚪 你走出家门，回到了{C.MAP_BY_ID.get(target, {}).get('name', '城镇')}。")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?拜访(?:[\s\S]*)$")
    @require_player()
    @no_prof_waiting()
    async def visit_home(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        raw = self._strip_cmd(event, "拜访").strip()
        if not raw:
            yield event.plain_result("格式：拜访 <玩家名>，去他家逛逛～(对方需要有房产)")
            return
        target = db.find_player_by_name(raw)
        if not target:
            yield event.plain_result(f"没找到玩家『{raw}』！")
            return
        tid = target["qq_id"]
        tp = db.get_player(group_id, tid)
        if not tp or not (tp.get("deed") or ""):
            yield event.plain_result(f"{target['name']} 还没有房产，去不了他家～")
            return
        if self._in_battle(group_id, qq_id):
            yield event.plain_result("你正在战斗中！先解决眼前的敌人(攻击/逃跑)")
            return
        db.update_player(group_id, qq_id, cur_map=self._home_map_id(tid), cur_subarea="")
        yield event.plain_result(f"🚪 你敲了敲门，走进了 {target['name']} 的家。『地图』看看他家有什么～")

    def _home_storage_key(self, group_id, qq_id):
        return f"home_storage_{group_id}_{qq_id}"

    def _home_storage_load(self, group_id, qq_id):
        raw = db.get_event_state(self._home_storage_key(group_id, qq_id))
        if not raw:
            return []
        try:
            lst = json.loads(raw)
            return lst if isinstance(lst, list) else []
        except (ValueError, TypeError):
            return []

    def _home_storage_save(self, group_id, qq_id, lst):
        db.set_event_state(self._home_storage_key(group_id, qq_id), json.dumps(lst, ensure_ascii=False))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?仓库(?:[\s\S]*)$")
    @require_player()
    async def home_storage(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player.get("cur_map", "").startswith("home_"):
            yield event.plain_result("仓库在家里！先『回家』吧～")
            return
        raw = self._strip_cmd(event, "仓库").strip()
        # 存：仓库 <物品名>
        if raw:
            # v84 仓库容量按房屋等级
            dlv = int(player.get("deed_lv", 1) or 1)
            hl = C.HOUSE_LEVELS.get(dlv, C.HOUSE_LEVELS[1])
            lst = self._home_storage_load(group_id, qq_id)
            if len(lst) >= hl["storage"]:
                yield event.plain_result(
                    f"📦 仓库满了({len(lst)}/{hl['storage']} 格)！升级房屋扩容(『地契 升级』)")
                return
            inv = db.get_inventory(group_id, qq_id)
            found = next((it for it in inv if it["data"].get("name") == raw), None)
            if not found:
                yield event.plain_result(f"背包里没有『{raw}』！")
                return
            # F1 P0-2：原子存仓（同事务：读-判容量→append→写回→扣背包），
            # 并发双请求只有首个成功（另一请求事务内重读 storage 已满 → 提示仓库满）
            _ok, _n = db.home_storage_deposit_atomic(
                group_id, qq_id, self._home_storage_key(group_id, qq_id),
                found["key"], found["data"], hl["storage"],
            )
            if not _ok:
                yield event.plain_result(
                    f"📦 仓库满了({_n}/{hl['storage']} 格)！升级房屋扩容(『地契 升级』)")
                return
            yield event.plain_result(f"📦 已存入仓库：【{found['data'].get('name', raw)}】({_n}/{hl['storage']})")
            return
        # 查看
        lst = self._home_storage_load(group_id, qq_id)
        if not lst:
            yield event.plain_result("仓库空空如也。『仓库 <物品名>』把背包里的宝贝存进来～")
            return
        lines = ["📦 【家中仓库】", "━━━━━━━━━━━━"]
        for i, it in enumerate(lst, 1):
            lines.append(f"{i:>2}. {it['data'].get('name', '?')} ×{it.get('count', 1)}")
        lines.append(self._tip("storage"))
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?取出(?:[\s\S]*)$")
    @require_player()
    async def home_storage_take(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player.get("cur_map", "").startswith("home_"):
            yield event.plain_result("仓库在家里！先『回家』吧～")
            return
        raw = self._strip_cmd(event, "取出").strip()
        if not raw.isdigit():
            yield event.plain_result("格式：取出 <编号>！『仓库』查看～")
            return
        idx = int(raw)
        # F1 P0-2：原子取出（单事务：读→pop→写回→加背包），并发双请求只有首个取出
        _ok, it = db.home_storage_take_atomic(
            group_id, qq_id, self._home_storage_key(group_id, qq_id), idx
        )
        if not _ok:
            lst = self._home_storage_load(group_id, qq_id)
            yield event.plain_result(f"仓库里没有第 {idx} 件(共 {len(lst)} 件)！")
            return
        yield event.plain_result(f"📦 取出【{it['data'].get('name', '?')}】，放入背包！")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:地图|周围)(?:\s*|$)")
    @require_player()

    async def map_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        # O114 修复：副本战斗中『地图』与副本状态同步——显示"副本战斗中"而非旧地点
        # （与『角色』位置显示同源，playtest O114 洛洛实测）
        # v137 副本地图化：副本 map 模式（mode=map，无战斗）→ 显示副本地图视图
        _inst_row = self._instance_battle_for(group_id, qq_id)
        if _inst_row:
            _st = _inst_row["state"]
            if _st.get("mode") == "map" or (_st.get("rooms") and not (_st.get("enemies") or _st.get("boss"))):
                # 副本内地图模式：显示副本地图（_instance_map_view 是 InstanceCmds 方法，
                # 通过主实例调用——Main 继承所有 Mixin，self 即 Main）
                if hasattr(self, "_instance_map_view"):
                    yield event.plain_result(self._instance_map_view(_st, group_id))
                    return
            yield event.plain_result(
                "🗺️ 【副本战斗中】\n"
                "你正在副本里与敌人作战，战斗结束前无法查看外界地图～\n"
                f"{self._tip('instance')}"
            )
            return
        cur = player["cur_map"]
        # v68 家地图：home_{qq_id} 不在 MAPS，定制展示
        if cur.startswith("home_"):
            yield event.plain_result(self._home_view(group_id, qq_id, cur))
            return
        cur_map = C.MAP_BY_ID[cur]
        cur_sa = player.get("cur_subarea") or ""
        sa_now = ""
        if cur_sa:
            for _sa in (cur_map.get("subareas") or []):
                if _sa["id"] == cur_sa:
                    sa_now = _sa["name"]
                    break
        # v87.3 标题修复：地图名 + 当前子区域（不再重复"橡木镇 · 橡木镇"）
        title = cur_map["name"]
        if sa_now:
            title = f"{cur_map['name']} · {sa_now}"
        # v87.13 描述优先显示当前子区域（子区域无 desc 时回退地图 desc）
        sa_desc = ""
        if cur_sa:
            for _sa in (cur_map.get("subareas") or []):
                if _sa["id"] == cur_sa:
                    sa_desc = _sa.get("desc", "") or ""
                    break
        lines = self._map_nav_body(player, cur_map, cur_sa, group_id, qq_id)
        # v134.3 赶路模式精简：move_mode 开启时『地图』只显示可前往；带 hurry_type
        # 参数才显示对应类型区（与 _subarea_arrive 同规则，鱼鱼拍板）
        # v161 意见#69：赶路模式也显示完整地图（玩家要看全局再决定去哪），
        # 仅移动（非赶路）时精简显示可前往。赶路模式 = nav + 完整 blocks + 赶路提示。
        _mv = bool(db.get_event_state(f"move_mode:{qq_id}"))
        _ht = db.get_event_state(f"hurry_type:{qq_id}") or ""
        if _mv:
            # 完整地图块（与普通地图一致）+ 赶路类型区 + 提示
            blocks = self._map_blocks(player, cur_map, cur_sa, group_id, qq_id)
            if blocks and lines and lines[-1]:
                lines.append("")
            lines += blocks
            if _ht:
                sec = self._hurry_section(player, cur_map, cur_sa, group_id, qq_id, _ht)
                if sec:
                    lines.append("")
                    lines.extend(sec)
            lines.append("")
            lines.append("💡 赶路模式中：回复序号直接赶路，回复 0 结束")
            yield event.plain_result("\n".join(lines))
            return
        # v134.2 排版修复：导航区与公共区块间补空行——_map_blocks 内部从空 lines 开始，
        # 首区块前无法感知调用方已拼好的 nav 内容（镇长办公处『✨ 可交互场景』紧贴『🧭 出城』）
        blocks = self._map_blocks(player, cur_map, cur_sa, group_id, qq_id)
        if blocks and lines and lines[-1]:
            lines.append("")
        lines += blocks
        yield event.plain_result("\n".join(lines))

    def _map_blocks(self, player: dict, cur_map: dict, cur_sa: str,
                    group_id=None, qq_id=None) -> list:
        """v132 从 map_view 抽取：位置导航之外的完整区块（今日奇遇/设施/场景/NPC/旅人/玩家/怪物/tip）。

        『地图』与 `_subarea_arrive`（到达视图）共用此方法 → 两处排版永不分裂
        （v101.25c 铁律：鱼鱼抓"前往不同区域提示模板不一样"）。
        cur_sa 传 sa id：到达视图时 player.cur_subarea 尚未更新为落点（v87.13b 同源处理）。
        """
        lines = []
        cur = cur_map.get("id", "")
        sas = cur_map.get("subareas") or []
        # v132.2 全地图紧凑模式（鱼鱼拍板：地图排版统一 ●横排模板，不再区分城镇/野外）
        _compact = True
        # v115 今日奇遇：面板底部一行（getattr 兜底，A/C 未就绪则不显示）
        _today_ev_fn = getattr(C, "today_map_event", None)
        if _today_ev_fn is not None:
            try:
                _ev = _today_ev_fn(cur)
                if _ev and _ev.get("name"):
                    _ev_fx = (_ev.get("effects") or {})
                    _ev_note = ""
                    if _ev_fx.get("encounter_rate", 0) > 0:
                        _ev_note = "(遇怪率↑)"
                    elif _ev_fx.get("event_chance", 0) > 0:
                        _ev_note = "(事件率↑)"
                    elif _ev_fx.get("loot_mult", 1.0) > 1.0:
                        _ev_note = f"(掉落×{_ev_fx.get('loot_mult', 1.0)})"
                    lines.append(f"🌤 今日奇遇：{_ev['name']}——{_ev.get('desc', '')}{_ev_note}")
            except Exception:
                pass
        # v87.4 区块间统一空行分隔（不再叠分隔线）
        if lines and lines[-1]:
            lines.append("")
        # 此地设施 + 场景（v87.13 拆分：设施=功能入口，场景=氛围景物）
        fac = self._map_facilities(cur_map, player, cur_sa)
        if fac:
            if lines and lines[-1]:
                lines.append("")
            lines.append("🏪 此地设施：")
            if _compact:
                lines.append("  ●" + " ●".join(fac))
            else:
                for l in fac:
                    lines.append(f"  {l}")
        # v132 场景两区：🔎 可探索触发（POI/调查）+ ✨ 可交互场景（PROPS）
        poi_lines, prop_lines = self._map_scene(cur_map, player, cur_sa)
        if poi_lines:
            if lines and lines[-1]:
                lines.append("")
            lines.append("🔎 可探索触发：")
            if _compact:
                names = []
                for l in poi_lines:
                    nm = l.split("(")[0].strip()
                    names.append(f"●{nm}")
                lines.append("  " + " ".join(names))
            else:
                for l in poi_lines:
                    lines.append(f"  {l}")
        if prop_lines:
            if lines and lines[-1]:
                lines.append("")
            lines.append("✨ 可交互场景：")
            if _compact:
                names = [f"●{i}. {l.split('(')[0].strip()}" for i, l in enumerate(prop_lines, 1)]
                lines.append("  " + " ".join(names))
            else:
                for l in prop_lines:
                    lines.append(f"  {l}")
        # 本地 NPC
        # v86 子区域：NPC 按当前子区域显示（无子区域则地图级）
        cur_sa_obj = None
        if cur_sa:
            for _sa in sas:
                if _sa["id"] == cur_sa:
                    cur_sa_obj = _sa
                    break
        npc_ids = (cur_sa_obj.get("npcs") if cur_sa_obj else None) or cur_map.get("npcs", [])
        if cur_map.get("inline_npcs"):
            npc_ids = cur_map["inline_npcs"]
        npcs = []
        for nid in npc_ids:
            if nid in C.HIDDEN_NPCS:
                npcs.append((nid, C.HIDDEN_NPCS[nid]))
            elif nid in C.NPCS:
                npcs.append((nid, C.NPCS[nid]))
        # v95.30 城镇 NPC 随机性：酱油 NPC 按 游走(roam)/概率(appear)/时段(period) 过滤显示
        # （功能 NPC 恒显示；隐藏 NPC 走副本层逻辑不参与；无子区域(地图级)不做过滤）
        npcs = [(nid, n) for nid, n in npcs
                if nid in C.HIDDEN_NPCS or not cur_sa or C.town_npc_visible(nid, n, cur_sa)]
        if npcs:
            if lines and lines[-1]:
                lines.append("")
            lines.append("👥 这里的 NPC：")
            if _compact:
                # 城镇紧凑：●1. 名 ●2. 名（无头衔，鱼鱼模板）
                _parts = [f"●{i}. {n['icon']}{n['name']}" for i, (_, n) in enumerate(npcs, 1)]
                lines.append("  " + " ".join(_parts))
            else:
                for i, (_, n) in enumerate(npcs, 1):
                    lines.append(f"  {i:>2}. {n['icon']}{n['name']}({n['title']})")
                lines.append(f"  {self._tip('talk')}")
        # v127.5 限时NPC：在场野外旅人（偶遇进入限时状态，带 ⏳ 剩余分钟，全图可见）
        # v127.5.1 不重复加 _tip('talk')——对上城镇 NPC 区已有同分类提示（AST 防重铁律）
        wild_lines = self._present_wild_hints(group_id, qq_id, cur) if group_id is not None and qq_id is not None else []
        if wild_lines:
            if lines and lines[-1]:
                lines.append("")
            lines.append("🧭 游历的旅人：")
            lines.extend(wild_lines)
        # v66 此地玩家（含摆摊标记；v132 加编号，鱼鱼新排版）
        # v134 #33：无其他玩家时不显示本段（连标题行一并省略，不留空行）
        # v134.1 #46：排除自己——"只有玩家一个人时"不再显示『👤 此地的玩家：●1. 自己』
        here_players = [p for p in db.get_group_players(group_id).values()
                        if p.get("cur_map") == cur and str(p.get("qq_id")) != str(qq_id)]
        if here_players:
            stall_sellers = {str(s["seller"]) for s in db.market_list(group_id, cur)}
            if lines and lines[-1]:
                lines.append("")
            lines.append("👤 此地的玩家：")
            if _compact:
                # 城镇紧凑：●1. 名 Lv.X ●2. 名 Lv.X（鱼鱼模板；摆摊标记保留——功能状态）
                _parts = [f"●{i}. {p['name']} Lv.{p['level']}"
                          + (" 🏪摆摊中" if str(p.get("qq_id")) in stall_sellers else "")
                          for i, p in enumerate(here_players, 1)]
                lines.append("  " + " ".join(_parts))
            else:
                for i, p in enumerate(here_players, 1):
                    stall_mark = " 🏪摆摊中" if str(p.get("qq_id")) in stall_sellers else ""
                    lines.append(f"  {i}. {p['name']} Lv.{p['level']}{stall_mark}")
        # v86 子区域：怪物按当前子区域（无则回退地图级）
        mons = (cur_sa_obj.get("monsters") if cur_sa_obj else None)
        if mons is None:
            mons = cur_map.get("monsters", [])
        # 精英/Boss（子区域优先）——先取值供去重判断与字段展示
        elite = (cur_sa_obj.get("elite") if cur_sa_obj else None) or cur_map.get("elite")
        boss = (cur_sa_obj.get("boss") if cur_sa_obj else None) or cur_map.get("boss")
        if mons:
            if lines and lines[-1]:
                lines.append("")
            # v101.25 #289：标题等级改用怪物实际 min-max——此前用子区域 lv+2 推断，
            # 与怪物真实等级差 2 级误导（round66 银风道口标 Lv.6-8 实际野狗 Lv.3）
            _mlvs = [lv for _m, _n, _r, lv, _s, _d in mons if lv]
            if _mlvs:
                _lo, _hi = min(_mlvs), max(_mlvs)
                lv_label = f"Lv.{_lo}" if _lo == _hi else f"Lv.{_lo}-{_hi}"
            else:
                base_lv = (cur_sa_obj.get("lv") if cur_sa_obj else None) or cur_map["lv"]
                lv_label = f"Lv.{base_lv}"
            lines.append(f"🐾 此地的怪物 ({lv_label})：")
            for mid, name, role, lv, skills, drops in mons:
                # v95r38 去重：池子条目与 elite/boss 字段重复时不重复显示（字段行会展示）
                if role == "elite" and elite and elite[0] == mid:
                    continue
                if role == "boss" and boss and boss[0] == mid:
                    continue
                mark = "👑" if role == "boss" else ("⭐" if role == "elite" else "")
                # v132 等级波动明示：普通怪 ±1（精英/Boss 不参与波动，不标注）
                jitter = "±1" if role not in ("elite", "boss") else ""
                lines.append(f"  {mark}{name} Lv.{lv}{jitter}")
        if elite:
            lines.append(f"  ⭐ 精英：{elite[1]}")
        if boss:
            lines.append(f"  👑 Boss：{boss[1]}")
        if lines and lines[-1]:
            lines.append("")
        lines.append(self._tip("map"))
        return lines

    def _map_nav_body(self, player: dict, cur_map: dict, cur_sa: str,
                      group_id=None, qq_id=None, show_here=True, with_header=True) -> list:
        """v128 地图导航主体（标题/描述/当前位置/可前往列表）——『地图』『位置』共用。

        返回 lines 列表（未 join），调用方按需追加其余区块。
        可前往编号与 move 解析一致（同图子区域 → 隐藏🔒 → 跨图邻居）。
        v132 with_header=False：跳过标题三行（🗺️/描述/分隔线）——到达视图自带标题时用。
        """
        sas = cur_map.get("subareas") or []
        sa_now = ""
        sa_desc = ""
        for _sa in sas:
            if _sa["id"] == cur_sa:
                sa_now = _sa["name"]
                sa_desc = _sa.get("desc", "") or ""
                break
        # v87.3 标题修复：地图名 + 当前子区域（不再重复"橡木镇 · 橡木镇"）
        title = cur_map["name"]
        if sa_now:
            title = f"{cur_map['name']} · {sa_now}"
        # v87.13 描述优先显示当前子区域（子区域无 desc 时回退地图 desc）
        lines = ([f"🗺️ 【{title}】", f"{sa_desc or cur_map['desc']}", "━━━━━━━━━━━━"]
                 if with_header else [])
        neighbors = C.MAP_CONNECTIONS.get(cur_map.get("id", ""), [])
        links = C.subarea_links(cur_map.get("id", ""), cur_sa)
        _v_ids = {vs["id"] for vs in self._visible_sas(player, cur_map, group_id, qq_id)}
        _v_links = [lid for lid in links if lid in _v_ids]
        shown = [(i + 1, next((s for s in sas if s["id"] == lid), None))
                 for i, lid in enumerate(_v_links)]
        shown = [(i, s) for i, s in shown if s]
        # 深度标记——v114.3 精简：只保留尽头标记 🔚（死胡同连接数==1 且非入口，提示此路到头需回头）
        _depth = getattr(C, "subarea_depth", None)
        _entry_id = C.map_entry_subarea(cur_map.get("id", ""))

        def _sa_mark(sa):
            if _depth is None:
                return ""
            # 死胡同（连接数==1 且非入口）
            try:
                if sa["id"] != _entry_id and len(C.subarea_links(cur_map.get("id", ""), sa["id"])) == 1:
                    return "🔚"
            except Exception:
                pass
            return ""

        if shown or neighbors:
            # v132.2 全地图紧凑模式（鱼鱼拍板）：●横排、无📍/无Lv/无🔚——模板统一，野外同款
            _compact = True
            # v128 位置面板（show_here=False）始终显示当前位置；『地图』保持原有 if sa_now 语义
            if not _compact and (sa_now or not show_here):
                lines.append(f"📍 当前位置：{sa_now or title}")
            elif not show_here:
                # v132.1 城镇紧凑：『位置』面板/到达视图仍显示 📍（精简导航核心信息）；
                # 仅『地图』面板（show_here=True）按鱼鱼模板隐藏（标题已含位置）
                lines.append(f"📍 当前位置：{sa_now or title}")
            lines.append("📮 可前往：")
            if _compact and shown:
                _parts = [f"●{i}. {sa['name']}" for i, sa in shown]
                lines.append("  " + " ".join(_parts))
            else:
                for i, sa in shown:
                    # v128 位置面板精简：不显示 "(你在这里)"（show_here=True 时保留）
                    mark = f" (你在这里)" if (show_here and sa["id"] == cur_sa) else ""
                    lv_mark = f" Lv.{sa['lv']}" if sa.get("lv") else ""
                    lines.append(f"  {i}. {_sa_mark(sa)}{sa['name']}{lv_mark}{mark}")
            # 隐藏未揭示房：显示 🔒？？？ 不编号（不可直接前往）
            _hidden_sas = [s for s in sas if s["id"] in links and s["id"] not in _v_ids]
            if _hidden_sas:
                for _hs in _hidden_sas:
                    lines.append("  🔒？？？(隐藏角落)")
            exit_sa_id = C.map_exit_subarea(cur_map.get("id", ""))
            at_exit = (not exit_sa_id) or (cur_sa == exit_sa_id)
            # v137 副本地图化：副本内（no_exit）不显示通往野外的连接——副本是封闭地图
            _dun = cur_map.get("dungeon") or {}
            if _dun.get("no_exit"):
                neighbors = []
            # v95.21 跨图连接只在出口子区域列出：普通场所不显示野外/他镇目的地，
            # 出城必须走城门（镇郊/野外入口），符合"出城走城门"铁律
            if at_exit:
                if _compact:
                    # v132.2 全地图紧凑：跨图邻居同样 ●横排（无 Lv，编号保留供『前往 N』直达）
                    _parts = []
                    for i, nid in enumerate(neighbors, len(_v_links) + 1):
                        nm, want_sa = self._conn_target(nid)
                        sa_lbl = self._conn_subarea_name(nm, want_sa)
                        lock = " (🔒隐藏)" if nm.get("hidden") else ""
                        _parts.append(f"●{i}. {nm['name']}{sa_lbl}{lock}")
                    lines.append("  " + " ".join(_parts))
                else:
                    for i, nid in enumerate(neighbors, len(_v_links) + 1):
                        nm, want_sa = self._conn_target(nid)
                        sa_lbl = self._conn_subarea_name(nm, want_sa)
                        lock = " (🔒隐藏)" if nm.get("hidden") else ""
                        lines.append(f"  {i}. {nm['name']}{sa_lbl} Lv.{nm['lv']}{lock}")
            else:
                # v95.25 #133：非出口子区域提示必经出口（与旧 _subarea_body 同口径，
                # v132 模板统一回归修复；街道链城镇在广场时提示必经之路）
                _exit_sa_name = next((s["name"] for s in sas if s["id"] == exit_sa_id), "出口")
                _hint = _exit_sa_name
                _center = sas[0] if sas else {}
                if _center.get("type") == C.SUB_TYPE_TOWN and cur_sa == _center.get("id", ""):
                    _chain = [s for s in sas if s.get("type") in (C.SUB_TYPE_STREET, C.SUB_TYPE_GATE)]
                    if _chain and _chain[0]["id"] != exit_sa_id:
                        _hint = _chain[0]["name"]
                lines.append(f"  🧭 出城需先到『{_hint}』")
            # v114.3 尽头标记图例（有深度数据才显示；城镇紧凑模式不显示——鱼鱼模板无此行）
            if _depth is not None and not _compact:
                lines.append("  💡 🔚=尽头（此路到头，需原路返回）")
        return lines

    @filter.regex(r"^(?:\[At:\d+\]\s*)?位置(?:\s*0)?(?:\s*|$)")
    @require_player()
    async def location_view(self, event: AstrMessageEvent):
        """v128.2 位置精简面板：当前位置 + 可前往列表 + 赶路入口提示。

        鱼鱼拍板：把『前往』指令拆成『位置』（精简）与『地图』（完整现状）。
        『位置』砍掉设施/场景/NPC/怪物等，只留导航。
        v128.2（鱼鱼拍板）：『位置 0』/发 0 进入赶路模式的旧捷径已移除——
        『位置 0』/『位置0』仍命中本面板（正则捕获 0 后缀）但不再切换赶路，
        面板统一提示用『赶路』指令进入（替代 v101.17 『前往开始/结束』）。
        """
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        # O114 同源：副本战斗中与『地图』一致显示"副本战斗中"而非旧地点
        _inst_row = self._instance_battle_for(group_id, qq_id)
        if _inst_row:
            yield event.plain_result(
                "🗺️ 【副本战斗中】\n"
                "你正在副本里与敌人作战，战斗结束前无法查看外界地图～\n"
                f"{self._tip('instance')}"
            )
            return
        cur = player["cur_map"]
        # v68 家地图：home_{qq_id} 不在 MAPS，定制展示（与『地图』同款）
        if cur.startswith("home_"):
            yield event.plain_result(self._home_view(group_id, qq_id, cur))
            return
        cur_map = C.MAP_BY_ID[cur]
        cur_sa = player.get("cur_subarea") or ""
        lines = self._map_nav_body(player, cur_map, cur_sa, group_id, qq_id, show_here=False)
        # v128.2 赶路模式提示：唯一入口=『赶路』指令（旧『位置 0』捷径已移除）
        if db.get_event_state(f"move_mode:{qq_id}"):
            lines.append("💡 赶路模式中：回复序号直接赶路，回复 0 结束")
        else:
            lines.append("💡 想赶路请发送『赶路』指令（可选『赶路 NPC/怪物/场景/设施』过滤）～")
        yield event.plain_result("\n".join(lines))

    _HURRY_ALIAS = {
        "npc": "npc",
        "怪物": "monster", "怪": "monster", "monster": "monster",
        "场景": "scene", "scene": "scene", "景物": "scene",
        "设施": "facility", "facility": "facility", "商店": "facility",
    }

    def _hurry_type(self, raw: str):
        """『赶路』可选参数归一：""=全量, None=无效；npc/monster/scene/facility=类型过滤。"""
        k = (raw or "").strip().lower()
        if k in ("", "全部", "全", "all"):
            return ""
        return self._HURRY_ALIAS.get(k)

    def _hurry_section(self, player: dict, cur_map: dict, cur_sa: str,
                       group_id, qq_id, ftype: str) -> list:
        """v128.1 类型过滤区（NPC/怪物/场景/设施）——赶路面板与移动落点过滤共用。

        返回 lines 列表（未 join）；无内容给"没有XX"提示行，保证赶路语境一致。
        """
        lines = []
        sas = cur_map.get("subareas") or []
        cur_sa_obj = None
        for _sa in sas:
            if _sa["id"] == cur_sa:
                cur_sa_obj = _sa
                break
        if ftype == "npc":
            npc_ids = (cur_sa_obj.get("npcs") if cur_sa_obj else None) or cur_map.get("npcs", [])
            if cur_map.get("inline_npcs"):
                npc_ids = cur_map["inline_npcs"]
            npcs = []
            for nid in npc_ids:
                if nid in C.HIDDEN_NPCS:
                    npcs.append((nid, C.HIDDEN_NPCS[nid]))
                elif nid in C.NPCS:
                    npcs.append((nid, C.NPCS[nid]))
            npcs = [(nid, n) for nid, n in npcs
                    if nid in C.HIDDEN_NPCS or not cur_sa or C.town_npc_visible(nid, n, cur_sa)]
            if npcs:
                lines.append("👥 这里的 NPC：")
                for i, (_, n) in enumerate(npcs, 1):
                    lines.append(f"  {i:>2}. {n['icon']}{n['name']}({n['title']})")
            else:
                lines.append("👥 这里附近没有可交谈的 NPC ～")
        elif ftype == "monster":
            mons = (cur_sa_obj.get("monsters") if cur_sa_obj else None)
            if mons is None:
                mons = cur_map.get("monsters", [])
            elite = (cur_sa_obj.get("elite") if cur_sa_obj else None) or cur_map.get("elite")
            boss = (cur_sa_obj.get("boss") if cur_sa_obj else None) or cur_map.get("boss")
            if mons:
                _mlvs = [lv for _m, _n, _r, lv, _s, _d in mons if lv]
                if _mlvs:
                    _lo, _hi = min(_mlvs), max(_mlvs)
                    lv_label = f"Lv.{_lo}" if _lo == _hi else f"Lv.{_lo}-{_hi}"
                else:
                    base_lv = (cur_sa_obj.get("lv") if cur_sa_obj else None) or cur_map["lv"]
                    lv_label = f"Lv.{base_lv}"
                lines.append(f"🐾 此地的怪物 ({lv_label})：")
                for mid, name, role, lv, skills, drops in mons:
                    if role == "elite" and elite and elite[0] == mid:
                        continue
                    if role == "boss" and boss and boss[0] == mid:
                        continue
                    mark = "👑" if role == "boss" else ("⭐" if role == "elite" else "")
                    lines.append(f"  {mark}{name} Lv.{lv}")
            if elite:
                lines.append(f"  ⭐ 精英：{elite[1]}")
            if boss:
                lines.append(f"  👑 Boss：{boss[1]}")
            if not mons and not elite and not boss:
                lines.append("🐾 这里没什么怪物，比较安全～")
        elif ftype == "scene":
            scene = self._map_scene(cur_map, player, cur_sa)
            if scene:
                lines.append("✨ 场景：")
                for l in scene:
                    lines.append(f"  {l}")
            else:
                lines.append("✨ 这里没什么特别的场景～")
        elif ftype == "facility":
            fac = self._map_facilities(cur_map, player, cur_sa)
            if fac:
                lines.append("🏪 此地设施：")
                for l in fac:
                    lines.append(f"  {l}")
            else:
                lines.append("🏪 这里没有商店/设施～")
        return lines

    def _hurry_panel(self, player: dict, cur_map: dict, cur_sa: str,
                     group_id, qq_id, ftype: str) -> str:
        """v128.1 赶路过滤面板：标题 + [类型清单] + 可前往通道 + 赶路提示。

        意见 #1（鱼鱼拍板合并为『赶路 <类型>』可选参数）：赶路时只看对应内容
        + 地图通道，省略其他信息，方便快速找 NPC/怪物/场景互动。ftype=""=全量。
        """
        nav = self._map_nav_body(player, cur_map, cur_sa, group_id, qq_id, show_here=False)
        lines = [nav[0], "━━━━━━━━━━━━"] if nav else []
        lines.extend(self._hurry_section(player, cur_map, cur_sa, group_id, qq_id, ftype))
        # 可前往通道（复用导航主体，跳过标题/desc/分隔线）
        rest = [x for x in nav[3:] if str(x).strip()]
        if rest:
            if ftype and lines and lines[-1]:  # v128.1 无参(full)无类型区不加分隔空行
                lines.append("")
            lines.extend(rest)
        lines.append("")
        lines.append("💡 赶路模式中：回复序号直接赶路，回复 0 结束")
        return "\n".join(lines)

    @filter.regex(r"^(?:\[At:\d+\]\s*)?赶路(?:[\s\S]*)$")
    @require_player()
    @no_prof_waiting()
    async def hurry_view(self, event: AstrMessageEvent):
        """v128.1 『赶路 [NPC/怪物/场景/设施]』过滤面板 + 进入赶路模式。

        意见 #1（赶路NPC/赶路怪物/赶路场景，鱼鱼拍板合并可选参数）：赶路时
        只看对应内容 + 地图通道，省略其他信息，方便快速找 NPC/怪物/场景互动。
        无参 = 当前位置全量可前往；全部形态进入赶路模式（0 结束）。
        """
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        _inst_row = self._instance_battle_for(group_id, qq_id)
        if _inst_row:
            yield event.plain_result(
                "🗺️ 【副本战斗中】\n"
                "你正在副本里与敌人作战，战斗结束前无法查看外界地图～\n"
                f"{self._tip('instance')}"
            )
            return
        raw = self._strip_cmd(event, "赶路").strip()
        ftype = self._hurry_type(raw)
        if ftype is None:
            yield event.plain_result(
                "『赶路』可选参数：NPC / 怪物 / 场景 / 设施（例：『赶路 NPC』；无参=看当前全部可前往）～")
            return
        # 进入赶路模式（0 结束；无参也进，方便直接回复序号走）
        db.set_event_state(f"move_mode:{qq_id}", "1")
        # v128.1 持久化过滤类型（移动落点也按该类型过滤）
        db.set_event_state(f"hurry_type:{qq_id}", ftype)
        cur = player["cur_map"]
        if cur.startswith("home_"):
            yield event.plain_result(self._home_view(group_id, qq_id, cur))
            return
        cur_map = C.MAP_BY_ID[cur]
        cur_sa = player.get("cur_subarea") or ""
        yield event.plain_result(self._hurry_panel(player, cur_map, cur_sa, group_id, qq_id, ftype))

    def _move_blocked_msg(self, cur_map: dict, player: dict, target_sa: dict) -> str:
        """v87.14 同图内不可直达时的提示(城镇星形 / 野外线性)。"""
        cur_sa_id = player.get("cur_subarea") or ""
        cur_name = cur_sa_id
        tgt_name = target_sa.get("name", target_sa.get("id", "？"))
        sas = cur_map.get("subareas") or []
        for s in sas:
            if s["id"] == cur_sa_id:
                cur_name = s["name"]
                break
        center = sas[0] if sas else {}
        if center.get("type") == C.SUB_TYPE_TOWN:
            # v87.16 街道链：在广场想去链上目标（东大街/镇郊）时提示必经之路
            if cur_sa_id == center.get("id", ""):
                chain = [s for s in sas if s.get("type") in (C.SUB_TYPE_STREET, C.SUB_TYPE_GATE)]
                # v95.12 防御：目标就是链首（无街道时链首=出口自身）不拦截，避免"先经过自己"
                if (any(s["id"] == target_sa.get("id") for s in chain)
                        and chain and chain[0]["id"] != target_sa.get("id")):
                    first = chain[0]["name"] if chain else center.get("name", "广场")
                    return (f"🧭 你身处【{cur_name}】，不能直接去【{tgt_name}】——"
                            f"路只有一条，需要先经过{first}。")
            # v95.12：非广场城镇子区域按空间连接提示必经路线（街道/出口链），
            # 不要一律"回广场"——镇郊去广场要先经过东大街，提示必须与真实路径一致
            links = C.subarea_links(cur_map.get("id", ""), cur_sa_id)
            link_names = [next((s["name"] for s in sas if s["id"] == lid), lid) for lid in links]
            return (f"🧭 你身处【{cur_name}】，不能直接去【{tgt_name}】——"
                    f"路只有一条，需要先经过{'、'.join(link_names)}。")
        links = C.subarea_links(cur_map.get("id", ""), cur_sa_id)
        link_names = [next((s["name"] for s in sas if s["id"] == lid), lid) for lid in links]
        return (f"🧭 你身处【{cur_name}】，不能直接去【{tgt_name}】——"
                f"路只有一条，需要先经过{'、'.join(link_names)}。")

    # v104 P2(M22): 『移动』=『前往』别名（23 章指令表主指令=『移动 <地名或序号>』），双名共存；
    # (?!开始|结束) 负向断言保留：v128 已删移动模式开关（改『位置』面板回复 0 切换赶路），
    # 旧指令『前往开始』『前往结束』仍不让 move 当目的地名吞掉
    # O74 『返回 <地名>』空回复修复（playtest 第 7 次复现，v101.25i 已删 move_back 但旧指令
    # 仍被玩家使用 → 注册提示 handler，不再只回标题零回复）：指引改用『前往』/『传送』
    @filter.regex(r"^(?:\[At:\d+\]\s*)?返回(?:[\s\S]*)$")
    @require_player()
    async def back_cmd(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        dest = self._strip_cmd(event, "返回").strip()
        if dest:
            yield event.plain_result(
                f"🧭 『返回 {dest}』已停用，请使用『前往 {dest}』赶路"
                f"(或『传送 <名称>』用已激活的方碑直达)～")
        else:
            yield event.plain_result("🧭 『返回』指令已停用，请使用『前往 <地名>』赶路～")

    # O115 『问路 <地名>』空回复修复：只回标题零内容（格温/血牙实测复现）——
    # 补路线指引：同图子区域直达提示 / 跨图按 MAP_CONNECTIONS 算最短路径
    @filter.regex(r"^(?:\[At:\d+\]\s*)?问路(?:[\s\S]*)$")
    @require_player()
    async def ask_way(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        raw = self._strip_cmd(event, "问路").strip()
        if not raw:
            yield event.plain_result("格式：问路 <地名>！比如『问路 海蚀洞窟』～")
            return
        cur = player.get("cur_map", "")
        cur_map = C.MAP_BY_ID.get(cur, {})
        # 1) 同图子区域名：直接给『前往』指引
        for sa in (cur_map.get("subareas") or []):
            if raw in (sa.get("name", ""), sa.get("id", "")):
                if sa.get("id") == player.get("cur_subarea"):
                    yield event.plain_result(f"你已经在【{cur_map.get('name', '')}·{sa.get('name', '')}】了～")
                else:
                    yield event.plain_result(
                        f"🧭 【{sa.get('name', '')}】就在{cur_map.get('name', '')}里，"
                        f"输入『前往 {sa.get('name', '')}』即可到达～")
                return
        # 2) 跨图目标：地图名/id/区域名/旧别名（与『前往』同口径）
        target = None
        for m in C.MAPS:
            if raw in (m["name"], m["id"]):
                target = m
                break
        if not target and raw in C.LEGACY_MAP_ALIAS:
            target = C.MAP_BY_ID.get(C.LEGACY_MAP_ALIAS[raw])
        if not target:
            for m in C.MAPS:
                if raw in m.get("area_name", ""):
                    target = m
                    break
        if not target:
            yield event.plain_result(f"没找到『{raw}』这个地方。输入『地图』看看周围，或『百科 地图』查询全大陆～")
            return
        if target["id"] == cur:
            yield event.plain_result(f"你已经在【{target['name']}】了～")
            return
        # 3) BFS 最短路径（MAP_CONNECTIONS 无向图）
        from collections import deque
        _conns = C.MAP_CONNECTIONS
        q = deque([(cur, [cur])])
        seen = {cur}
        route = None
        while q:
            _c, _path = q.popleft()
            if _c == target["id"]:
                route = _path
                break
            for _conn in _conns.get(_c, []):
                _nid = _conn[0] if isinstance(_conn, tuple) else _conn
                if _nid not in seen:
                    seen.add(_nid)
                    q.append((_nid, _path + [_nid]))
        if not route:
            yield event.plain_result(f"🧭 【{target['name']}】暂时没有通路抵达，去『地图』看看附近的路吧～")
            return
        names = [C.MAP_BY_ID.get(_i, {}).get("name", _i) for _i in route]
        yield event.plain_result(
            f"🧭 【{target['name']}】的路线：{' → '.join(names)}（{len(route) - 1} 段路程）。\n"
            f"{self._tip('move')}；方碑已激活的地区可用『传送 <名称>』直达～")

    def _instance_gate_block(self, player: dict, group_id: str, qq_id: str, target: dict) -> str:
        """q1-B 副本图门禁：徒步『前往/移动』不可直接进入副本图（type=副本）。

        否则终局副本旁路：ash_temple/abyss_gate 等副本图经 MAP_CONNECTIONS 连通可徒步
        到达，玩家走进即自动完成 explore 主线目标（q9_3/q10_3 目标 ash_temple，
        q12_3 目标 abyss_gate），绕过『副本 <名字>』开本流程的钥匙/等级/人数校验。
        准入判定有三档（任一满足即放行，返回值空串）：
          - 玩家正持有 active 且 explore 目标为本图的**主线或支线任务**（任务内进入不受影响）；
          - 背包持有该副本 key_item（如 ash_temple→烬火令，abyss_gate→深渊钥匙）；
          - 已通关该副本（inst_clear_* 首通记录，与 instance.py 免钥匙同口径）。

        v141 审计 #9：钥匙三路匹配 + 通关豁免抽到 core/instance_gate.py
        （find_instance_key_item / instance_cleared_qq），此处只做任务放行层 + 调用公共函数。
        设计语义：**徒步进图不扣钥匙**（只校验持有，钥匙由『副本 <名字>』开本时才扣），
        任务/钥匙两路放行；开本才扣（见 instance.py _instance_start 同款公共函数调用）。

        命中时返回拦截文案；非副本图直接放行。『副本 <名字>』开本入口不经过本方法，不受影响。
        """
        if target.get("type") != C.MAP_TYPE_INSTANCE:
            return ""
        kid = target.get("id", "")
        mid = f"inst_{kid}"
        inst = C.INSTANCES.get(mid)
        # 1) 任务内进入：active 主线或支线 explore 目标 == 本副本图 → 放行
        quests = db.get_quests(group_id, qq_id)
        if quests.get("main_status") == "active":
            mq = next((q for q in C.MAIN_QUESTS if q["id"] == quests.get("main_quest")), None)
            if mq and mq["objective"].get("explore") == kid:
                return ""
        side = quests.get("side") or {}
        if any(sq.get("status") == "active"
               and next((q for q in C.SIDE_QUESTS if q["id"] == sid), {}).get("objective", {}).get("explore") == kid
               for sid, sq in side.items()):
            return ""
        # 2) 持有钥匙（与 instance.py 开本钥匙判定同源，抽公共 core/instance_gate.py）
        from ..core.instance_gate import find_instance_key_item
        key_item = (inst or {}).get("key_item")
        if key_item and find_instance_key_item(group_id, qq_id, key_item) is not None:
            return ""
        # 3) 已通关副本 → 免钥匙放行（与 instance.py 同口径，抽公共 core/instance_gate.py）
        from ..core.instance_gate import instance_cleared_qq
        if instance_cleared_qq(group_id, qq_id, kid):
            return ""
        inst_name = (inst or {}).get("name") or C.MAP_BY_ID.get(kid, {}).get("name", "副本")
        return (f"🔒 此处为【{inst_name}】入口，需接取相应任务（或持有钥匙）才能进入。\n"
                f"{self._tip('instance')}；或先完成任务、收集所需钥匙～")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:前往|移动)(?!开始|结束)(?:\s*|$)")
    @require_player()
    @no_prof_waiting()

    async def move(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        dest = self._strip_cmd(event, "前往")
        if dest.startswith("移动"):
            dest = dest[2:].strip()  # v104 P2(M22): 『移动 <地名/序号>』别名参数剥离（双名共存）
        player = self._player(group_id, qq_id)
        # v87.13 对话中禁止移动：多轮对话进行时先回复 0 结束（v127.8 起『对话 0』亦拦截）
        # O99 修复：统一对话状态判定（_talk_active 会清除损坏残留键，防判定漂移）
        if self._talk_active(group_id, qq_id):
            yield event.plain_result("你还在和 NPC 交谈中！先回复 0 结束对话再动身吧。")
            return
        # v137 副本地图化：副本内移动（队长带队，房间连通）——必须先于 _in_battle 全局拦截：
        # 副本地图模式（mode=map，st.boss=None）下 battle 锁仍持有，_in_battle 会拦截所有移动。
        # _instance_move_route 内部校验副本状态并自行处理锁（解锁→推进→按需重新上锁）。
        _mv_dest = dest
        if _mv_dest.startswith("移动"):
            _mv_dest = _mv_dest[2:].strip()
        _routed = False
        async for _r in self._instance_move_route(event, group_id, qq_id, player, _mv_dest.strip()):
            yield _r
            _routed = True
        if _routed:
            return
        dest = _mv_dest
        # v95.17 #146：战斗中禁止移动（与传送/回家/拜访一致，防战斗挂起跨图/被撞怪覆盖）
        if self._in_battle(group_id, qq_id):
            yield event.plain_result("⚔️ 你正在战斗中！输入『攻击』/『技能 <名称>』继续战斗，『防御』『逃跑』『用药』可选——先解决眼前的敌人再说移动。")
            return
        dest = dest.strip()
        # v104 P1(M22)：空参数『前往』/『移动』不再静默移动——"" 是任意非空串的子串，
        # 此前会命中 area_name 首个非空地图静默跨图并扣体力，直接提示输入目标
        if not dest:
            yield event.plain_result("前往哪？输入『地图』查看～")
            return
        # v94 体力：同图子区域移动免费（城内溜达不算赶路）；跨图移动扣 1、体力不足拒绝
        cur = player["cur_map"]
        cur_map = C.MAP_BY_ID.get(cur, {})
        cur_sas = cur_map.get("subareas") or []
        # v86 子区域：『移动 <序号>』→ 同图可前往列表序号优先（v87.14 空间连接），再邻居地图序号
        # v104 P3(M24) 确认：全角数字兼容——Python str.isdigit()/int() 原生接受全角 ０-９(U+FF10-FF19)，
        # 『前往 １２』与『前往 12』等价（实测 2026-08-12：isdigit=True 且 int('１２')==12，无需 normalize）。
        # v115 网状：visible_links 用 _visible_sas 过滤（隐藏未揭示不可前往），与『地图』面板编号一致
        _raw_links = C.subarea_links(cur, player.get("cur_subarea") or "")
        _v_ids = {vs["id"] for vs in self._visible_sas(player, cur_map, group_id, qq_id)}
        links = [lid for lid in _raw_links if lid in _v_ids]
        if dest.isdigit():
            idx = int(dest)
            if 1 <= idx <= len(links):
                sa_id = links[idx - 1]
                sa = next((s for s in cur_sas if s["id"] == sa_id), None)
                if sa is None:
                    yield event.plain_result("目标子区域不存在！输入『地图』查看～")
                    return
                if sa["id"] == player.get("cur_subarea"):
                    yield event.plain_result(f"你已经在这里了({cur_map['name']}·{sa['name']})～")
                    return
                db.update_player(group_id, qq_id, cur_subarea=sa["id"])
                yield event.plain_result(self._subarea_arrive(player, cur_map, sa, group_id, qq_id))
                return
        # v86 子区域：『移动 <子区域名>』→ 同图子区域（免费切换）
        if dest:
            for sa in cur_sas:
                if dest in (sa["name"], sa["id"]):
                    if sa["id"] == player.get("cur_subarea"):
                        yield event.plain_result(f"你已经在这里了({cur_map['name']}·{sa['name']})～")
                        return
                    # v87.14 空间连接：同图只能移动到相邻子区域
                    # v115：隐藏未揭示房不能直接前往（提示需先探索揭开）
                    _is_hidden_fn = getattr(C, "is_hidden_room", None)
                    _reveal_met_fn = getattr(C, "reveal_met", None)
                    if _is_hidden_fn is not None and _reveal_met_fn is not None:
                        try:
                            if _is_hidden_fn(cur, sa["id"]) and not _reveal_met_fn(sa.get("reveal"), group_id, qq_id, cur):
                                _reveal_pr = getattr(C, "reveal_progress", None)
                                _progress_txt = ""
                                if _reveal_pr is not None:
                                    try:
                                        _ck, _nk = _reveal_pr(group_id, qq_id, cur)
                                        if _nk is not None:
                                            _progress_txt = f"（还差 {_nk - _ck} 次探索）"
                                    except Exception:
                                        pass
                                yield event.plain_result(
                                    f"🔒 这里似乎被什么遮挡着……（在本图继续『探索』可揭开它的面纱）{_progress_txt}")
                                return
                        except Exception:
                            pass
                    links2 = C.subarea_links(cur, player.get("cur_subarea") or "")
                    if sa["id"] not in links2:
                        yield event.plain_result(self._move_blocked_msg(cur_map, player, sa))
                        return
                    db.update_player(group_id, qq_id, cur_subarea=sa["id"])
                    yield event.plain_result(self._subarea_arrive(player, cur_map, sa, group_id, qq_id))
                    return
        # 查找目标地图：优先序号（相对当前地图邻居列表），其次地图名/ID/旧区域别名
        target = None
        want_sa = None
        if dest.isdigit():
            neighbors = C.MAP_CONNECTIONS.get(cur, [])
            idx = int(dest)
            offset = len(links)
            # #263: 与地图显示口径一致——跨图连接只在出口子区域有效（v95.21 出城走城门铁律），
            # 非出口子区域报错"可前往 N 处"此前无条件加邻居数（显示 1 处却报 5 处）
            exit_sa_id = C.map_exit_subarea(cur)
            at_exit = (not exit_sa_id) or (player.get("cur_subarea") == exit_sa_id)
            if not at_exit:
                neighbors = []
            if offset + 1 <= idx <= offset + len(neighbors):
                target, want_sa = self._conn_target(neighbors[idx - offset - 1])
            else:
                # #263 回归修复：不在出口子区域时序号命中邻居地图 → 引导去出口
                # （此前清空 neighbors 后直接"序号无效"，丢了 v87.14 出城走城门的路线引导；
                #   无效序号仍按实际可前往数量报错，保持 #263 口径一致）
                if not at_exit and offset + 1 <= idx <= offset + len(C.MAP_CONNECTIONS.get(cur, [])):
                    _exit_name = next((s["name"] for s in (cur_map.get("subareas") or []) if s["id"] == exit_sa_id), "出口")
                    _cur_sa_name = next((s["name"] for s in (cur_map.get("subareas") or []) if s["id"] == player.get("cur_subarea")), player.get("cur_subarea", ""))
                    yield event.plain_result(
                        f"🧭 你身处【{_cur_sa_name}】，还不能离开{cur_map.get('name', '此地')}——"
                        f"需要先到{_exit_name}(『前往 {_exit_name}』)才能出城/出图。"
                    )
                    return
                total = len(links) + len(neighbors)
                yield event.plain_result(f"序号无效！这里可前往 {total} 处，输入『地图』查看～")
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
            yield event.plain_result(f"找不到『{dest}』！输入『地图』查看可前往区域，或『传送 <名称>』用方碑快速旅行～")
            return
        # 隐藏图检查
        if target.get("hidden"):
            unlock = C.HIDDEN_MAP_UNLOCK.get(target["id"], {})
            if player["level"] < unlock.get("level", 99):
                yield event.plain_result("前方被无形的屏障阻挡……这里需要更强大的实力！(等级不足)")
                return
            # v87：物品型准入（H6 泛黄书页×3 / H7 烬火信标）
            item_req = unlock.get("item")
            if item_req:
                lack = [f"{name}×{need}" for name, need in item_req.items()
                        if db.count_item(group_id, qq_id, name) < need]
                if lack:
                    yield event.plain_result(
                        "入口被古老的力量封锁，似乎需要信物才能进入……\n"
                        f"🔒 缺少：{'、'.join(lack)}\n"
                        "💡 失落图书馆：集齐 3 张泛黄书页(探索彩蛋/圣堂地窖精英/符文石)\n"
                        "💡 灰烬回廊：找到老守墓人·灰须领取烬火信标"
                    )
                    return
            quests = db.get_quests(group_id, qq_id)
            if unlock.get("quest") not in quests.get("completed_main", []):
                yield event.plain_result("地图的入口被古老魔法封印，似乎只有完成主线任务才能解开……")
                return
        # 是否相邻
        cur = player["cur_map"]
        neighbors = C.MAP_CONNECTIONS.get(cur, [])
        nids = [c[0] if isinstance(c, tuple) else c for c in neighbors]
        # v104 P1(M22)：目标==当前图（输入本图地图名/区域名）→ 提示已在，不再原地白走扣体力
        # （同图子区域名分支 :676-678 已有同款提示，跨图路径此前漏了）
        if target["id"] == cur:
            yield event.plain_result(f"你已经在这里了！(当前：{cur_map.get('name', '此地')})")
            return
        if target["id"] != cur and target["id"] not in nids:
            yield event.plain_result(f"无法直接前往{target['name']}！需要先到相邻地图。看看『地图』～")
            return
        # v84 红名限制（26 章三 第一档）：红名不能进入城镇安全区（'城镇外郊' 数据不存在，v102.1 清理）
        if self._is_redname(qq_id) and target.get("type") == C.MAP_TYPE_TOWN:
            yield event.plain_result(
                "🛡️ 城门口的守卫拦住了你：\"你身上沾着血腥味！红名期间禁止进入城镇！\"\n"
                "(红名期间不能进入安全区，去野外避避风头吧)")
            return
        # 等级提示
        lv_msg = ""
        if player["level"] < target["lv"]:
            lv_msg = f"\n⚠️ 建议等级 Lv.{target['lv']}，你才 Lv.{player['level']}，小心行事！"
        # v87.14 出图必须在该图出口子区域（城镇=城门，野外=入口）
        exit_sa_id = C.map_exit_subarea(cur)
        if exit_sa_id and player.get("cur_subarea") != exit_sa_id:
            _exit_name = next((s["name"] for s in (cur_map.get("subareas") or []) if s["id"] == exit_sa_id), "出口")
            _cur_sa_name = next((s["name"] for s in (cur_map.get("subareas") or []) if s["id"] == player.get("cur_subarea")), player.get("cur_subarea", ""))
            yield event.plain_result(
                f"🧭 你身处【{_cur_sa_name}】，还不能离开{cur_map.get('name', '此地')}——"
                f"需要先到{_exit_name}(『前往 {_exit_name}』)才能出城/出图。"
            )
            return
        # q1-B 副本图门禁：副本图（type=副本）不可徒步直入（终局副本旁路修复）——
        # 需已接取对应 explore 主线/支线任务、或持有副本钥匙、或已通关该副本才能进入。
        _inst_gate = self._instance_gate_block(player, group_id, qq_id, target)
        if _inst_gate:
            yield event.plain_result(_inst_gate)
            return
        # v137 副本地图化：副本内移动（已开本 + 在副本图内）——队长带队、房间连通、
        # discovery_agro 遇怪、Boss 房 Boss 战。目标房间名/序号解析与野外同款，
        # 但只在本图连通表内移动（no_exit 无出口，不连野外）。
        # 注意：_instance_move_route 已在 move 顶部先行路由（副本地图模式持有战斗锁，
        # _in_battle 全局拦截在前）；此处副本分支保留以兼容直接调用/后续路径。
        inst_row = self._instance_battle_for(group_id, qq_id)
        if inst_row and inst_row["state"].get("inst_id") == target["id"] \
                and (inst_row["state"].get("mode") == "map" or inst_row["state"].get("rooms")):
            # v141 审计 #8：_instance_dungeon_move 去掉 target 死参数——地图目标
            # 在函数内按 inst_id 解析（大陆实例优先），此处只透传玩家原始 dest
            async for _r in self._instance_dungeon_move(event, group_id, qq_id, player, inst_row, dest):
                yield _r
            return
        # v86 子区域：跨图移动 → 落点：城镇=城门，野外=入口（v87.14）
        target_sas = target.get("subareas") or []
        first_sa = None
        entry_sa_id = C.map_entry_subarea(target["id"])
        for _s in target_sas:
            if _s["id"] == entry_sa_id:
                first_sa = _s
                break
        if first_sa is None and target_sas:
            first_sa = target_sas[0]
        if want_sa:
            for _s in target_sas:
                if _s["id"] == want_sa:
                    first_sa = _s
                    break
        # v94 体力：跨图移动扣 1；体力 0 拒绝（同图移动免费已在上方处理）；v101.13 坐骑 stamina_reduce 概率免费
        if self._stamina(player) < 1:
            yield event.plain_result(
                f"⚡ 你太累了，走不动了！(体力 {self._stamina(player)}/{self._stamina_max(player)})\n"
                "💡 恢复体力：野外营地『休息』/ 吃食物 / 旅店『住宿』，或等体力自然恢复(每1分钟+1)\n"
                "💡 也可以『传送』(已激活的方碑)或使用『回城卷轴』脱身～\n"
                "💡 新手建议：野外活动前先在城镇『商店』买点食物（烤肉串等），体力 0 才不会困在野外～"
            )
            return
        _mv_cost = 0 if random.random() < float(C.mount_effects(player).get("stamina_reduce", 0) or 0) else 1
        if _mv_cost > 0:
            self._spend_stamina(group_id, qq_id, _mv_cost, player, "移动")
        db.update_player(group_id, qq_id, cur_map=target["id"],
                         cur_subarea=first_sa["id"] if first_sa else "")
        # 记录到访（称号用）
        db.add_visited(group_id, qq_id, target["id"])
        # 阶段九：到访成就判定（14 章 2.4 探索成就）
        C.check_achievements(group_id, qq_id, self._player(group_id, qq_id))
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
        # v13：到达后显示可前往 + 设施/场景（v87.13 拆分）
        # v87.16 与地图面板一致：links 顺序号 + 邻居从 len(links)+1 编号
        target_sas = target.get("subareas") or []
        t_links = C.subarea_links(target["id"], first_sa["id"] if first_sa else "")
        t_shown = [(i + 1, next((s for s in target_sas if s["id"] == lid), None))
                   for i, lid in enumerate(t_links)]
        t_shown = [(i, s) for i, s in t_shown if s]
        neighbors = C.MAP_CONNECTIONS.get(target["id"], [])
        nav = ""
        # v101.25c 模板统一后：完整"可前往"列表已由 _subarea_body 输出，
        # 此处不再拼紧凑版（否则跨图移动出现两行重复列表，playtest #405）
        # v128 赶路模式提示统一由 _subarea_arrive 输出（回复 0 结束），此处不再重复。
        # v132：fac_msg/scene_msg 死代码已删（v101.25c 起跨图移动走 _subarea_arrive，
        # 此处拼装从未被消费；_map_scene 改返回 (poi, prop) 后旧 join 会直接崩）
        # v49 意见#4：移动撞怪（生物趋避利害——低级闯高级区容易撞怪，高级玩家威慑低级区）
        ambush = self._travel_ambush(player, target, group_id, qq_id)
        # v101.25c 模板统一：跨图移动也走 _subarea_arrive 完整模板（NPC/可互动/设施/场景/可前往）
        # 此前跨图是另一套精简拼接（fac_msg/scene_msg/nav），鱼鱼抓"前往不同区域提示模板不一样"
        if ambush:
            # v2 多对多：撞怪经 build_monster_group 生成敌方阵列（单只即可，伏击不引入随机双怪）
            _grp = C.build_monster_group(ambush, target, player)
            _nb = BT.Battle("monster", None, self._title_bonus(group_id, qq_id), player=player, pet=db.pet_get(qq_id), enemies=_grp)
            db.save_battle(group_id, qq_id, _nb.to_state())
            self._lock_battle(group_id, qq_id)
            arrive_txt = f"🚶 你来到了【{target['name']}】"
            if target.get("type") == C.MAP_TYPE_TOWN and first_sa:
                arrive_txt = f"🚶 你从野外方向来到了【{target['name']}】{first_sa['name']}"
            # 我方站位单机 = 玩家单位
            _cls = C.CLASSES.get(player.get("class_name", ""), {}) or {}
            _self_unit = {
                "uid": "p_self", "rank": int(_cls.get("default_rank", 2) or 2),
                "reach": int(_cls.get("reach", 2) or 2), "name": player.get("name", "你"),
                "hp": player.get("hp", 0), "max_hp": player.get("max_hp", 0),
            }
            _enemy_rows = formation_view(alive_units(_grp), side="enemy")
            _ally_rows = formation_view(alive_units([_self_unit]), side="ally")
            yield event.plain_result(
                f"{arrive_txt}\n{(first_sa.get('desc') if first_sa else '') or target.get('desc', '')}{lv_msg}{extra}{portal_msg}\n"
                f"━━━━━━━━━━━━\n"
                f"🛡️ 还没站稳，{ambush['name']} 就拦住了去路！\n"
                f"── 敌方 ──\n" + "\n".join(_enemy_rows) + "\n── 我方 ──\n" + "\n".join(_ally_rows) + "\n"
                f"🐾【{ambush['name']}】Lv.{ambush['lv']} ❤️ {ambush['hp']}/{ambush['max_hp']}\n"
                f"━━━━━━━━━━━━\n"
                f"你的行动：『攻击』『技能 <名称>』『防御』『逃跑』"
            )
            return
        # v87.3 必经之路：进入城镇时提示方向（从路图/野外进城）
        arrive_txt = f"🚶 你来到了【{target['name']}】"
        if target.get("type") == C.MAP_TYPE_TOWN and first_sa:
            arrive_txt = f"🚶 你从野外方向来到了【{target['name']}】{first_sa['name']}"
        # v97.5 行为彩蛋规则：进入新地图
        _rule_txt = self._rule_fire("move_enter", group_id, qq_id, player, target)
        arrive_view = self._subarea_arrive(player, target, first_sa, group_id, qq_id) if first_sa else \
            f"🚶 你来到了【{target['name']}】\n{target.get('desc', '')}"
        # 跨图特有信息插在主体前（等级提示/任务/方碑）
        _head_extra = f"{lv_msg}{extra}{portal_msg}"
        yield event.plain_result(
            f"{arrive_view}{_head_extra}"
            + (f"\n{_rule_txt}" if _rule_txt else "")
        )
    def _subarea_arrive(self, player: dict, cur_map: dict, sa: dict, group_id=None, qq_id=None) -> str:
        """v132 到达视图：🗺️ 标题 + 描述 + 完整区块（导航/奇遇/设施/场景/NPC/旅人/玩家/怪物/tip）。

        v86 子区域到达展示：位置 + 描述 + 本子区域可互动 + 可前往子区域。
        v6 修复：与跨图移动一致，展示本子区域 PROPS/POI 场景元素
        （鱼鱼验收：移动展示必须与『地图』面板一致）。
        v101.25c：主体复用 _subarea_body（与跨图移动/返回同模板）。
        v132：_subarea_body 移除，改为 _map_nav_body(without_header) + _map_blocks——
        与『地图』面板 100% 同源（鱼鱼拍板新排版：可前往带 Lv/尽头标记、场景分两区、
        玩家编号、怪物标 ±1 波动；移动面板与地图面板永不分裂）。
        v115：H 提供 exploration_record_visit 时，到达即记录 + 首访奖励文本追加。
        """
        title = cur_map["name"]
        if sa.get("name"):
            title = f"{cur_map['name']} · {sa['name']}"
        desc = sa.get("desc", "") or cur_map.get("desc", "")
        # v128.1 赶路类型过滤落点：hurry_type 非空时只显示该类型 + 可前往通道
        _ht = ""
        if group_id is not None and qq_id is not None:
            _ht = db.get_event_state(f"hurry_type:{qq_id}") or ""
        # v134.3 赶路模式精简：move_mode 开启时默认只显示可前往（不显示设施/场景/NPC
        # 等杂项），带 hurry_type 参数才显示对应类型——鱼鱼拍板"默认赶路状态不需要
        # 显示那么多，只显示可前往就行了，带参数才要显示别的"
        _mv = False
        if group_id is not None and qq_id is not None:
            _mv = bool(db.get_event_state(f"move_mode:{qq_id}"))
        if _ht or _mv:
            nav = self._map_nav_body(player, cur_map, sa["id"], group_id, qq_id,
                                     show_here=False, with_header=False)
            if _ht:
                sec = self._hurry_section(player, cur_map, sa["id"], group_id, qq_id, _ht)
            else:
                sec = []
            lines = [f"🗺️ 【{title}】", desc, "━━━━━━━━━━━━"] + sec
            rest = [x for x in nav if str(x).strip()]
            if rest:
                if sec:
                    lines.append("")
                lines.extend(rest)
            out = "\n".join(lines)
        else:
            nav = self._map_nav_body(player, cur_map, sa["id"], group_id, qq_id,
                                     show_here=False, with_header=False)
            blocks = self._map_blocks(player, cur_map, sa["id"], group_id, qq_id)
            out = "\n".join([f"🗺️ 【{title}】", desc, "━━━━━━━━━━━━"] + nav + blocks)
        # v115 探索见闻：到达子区域记录 + 首访奖励（H 提供，getattr 兜底）
        _rec = getattr(C, "exploration_record_visit", None)
        if _rec is not None and group_id is not None and qq_id is not None:
            try:
                _rv = _rec(group_id, qq_id, cur_map.get("id", ""), sa.get("id", ""))
            except Exception:
                _rv = None
            if _rv:
                if _rv.get("first"):
                    _rw = _rv.get("reward") or ""
                    if _rw:
                        out += f"\n🎉 {_rw}"
                else:
                    _rw = _rv.get("reward") or ""
                    if _rw:
                        out += f"\n{_rw}"

        # v128 赶路模式：移动落点统一提示（回复 0 结束），替代『前往结束』
        if group_id is not None and qq_id is not None and db.get_event_state(f"move_mode:{qq_id}"):
            out += "\n🚶 赶路模式中：回复序号直接赶路，回复 0 结束"
        return out

    async def _instance_dungeon_move(self, event, group_id, qq_id, player, inst_row, dest):
        """v137 副本内移动（world.move 副本分支）：队长带队 + 房间连通校验 + discovery_agro 遇怪 + Boss 房 Boss 战。

        与野外移动共用同一『前往/移动』入口（鱼鱼 v137：副本与野外共用一套代码机制），
        差异仅在：
          ① 仅队长可移动，全队 cur_subarea 同步（db.update_player 每个成员）
          ② 目标房间必须在本图 SUBAREA_LINKS_INDEX 连通表内（副本无出口，不连野外）
          ③ 遇怪概率 = dungeon.discovery_agro（core/encounter.encounter_chance 统一读，
             数据表驱动），消耗 rooms[cur_room].monsters_left
          ④ 到达 Boss 房 + boss_alive → 触发 Boss 战（走 _enter_stage_combat 现状战斗链路）

        dest：玩家原始输入（房间名/序号/图 id），内部统一解析（v141 审计 #8：
        本函数是目标解析唯一入口，_instance_move_route 直接透传，不再二次解析）。
        """
        st = inst_row["state"]
        if st.get("cleared"):
            yield event.plain_result("副本已通关，没有敌人了！『副本地图』看看战利品堆，或『离开副本』传出～")
            return
        # 战斗进行中（mode != map）→ 不能移动（与野外战斗中禁止移动同规则）
        if st.get("mode") != "map":
            yield event.plain_result("你正在战斗中！先解决眼前的敌人再说～")
            return
        # 队长带队：仅队长可移动
        members = st.get("members") or []
        if str(qq_id) != str(st.get("leader")):
            _lead = self._player(group_id, st.get("leader")) or {}
            yield event.plain_result(
                f"⏳ 副本内由队长【{_lead.get('name', st.get('leader'))}】带队移动！等待队长『移动 <房间>』～")
            return
        # 目标房间解析：序号（本图连通表）优先，其次房间名/id
        cur_sa = player.get("cur_subarea") or ""
        # v141 大陆隔离：优先从大陆实例读（克隆图），回退全局静态图
        _wid = st.get("world_id") or ""
        _inst = C.get_instance_world(_wid) if _wid.startswith("inst:") else None
        cur_map = (_inst or {}).get("maps", {}).get((st.get("inst_id") or "").removeprefix("inst_"), {}) or C.MAP_BY_ID.get((st.get("inst_id") or "").removeprefix("inst_"), {})
        sas = cur_map.get("subareas") or []
        links = C.subarea_links(cur_map.get("id", ""), cur_sa) if cur_sa else []
        # 副本内不隐藏房间（v137 房间全可见），直接取连通表
        target_sa = None
        if isinstance(dest, str) and dest.isdigit():
            idx = int(dest)
            if 1 <= idx <= len(links):
                tid = links[idx - 1]
                target_sa = next((s for s in sas if s["id"] == tid), None)
        else:
            for s in sas:
                if dest in (s["name"], s["id"]):
                    target_sa = s
                    break
        if target_sa is None:
            names = "、".join(
                f"{i + 1}. {next((s['name'] for s in sas if s['id'] == lid), lid)}"
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
        # 目标房间：rooms 存档（怪物池/资源池）——波次 3a 未实现则只做移动/展示
        rooms = st.get("rooms") or {}
        rstate = rooms.get(target_sa["id"]) or {}
        # 落点：全队 cur_subarea 同步
        for m in members:
            db.update_player(group_id, m, cur_subarea=target_sa["id"])
        db.save_battle(group_id, st["leader"], st)
        arrive_view = self._subarea_arrive(self._player(group_id, qq_id), cur_map, target_sa, group_id, qq_id)
        # v137 dungeon 修饰符：房间移动遇怪（消耗 monsters_left，打完不刷）
        # v164（鱼鱼拍板 2026-09-02）：移动遇怪改【必中】——房间怪物池非空就触发。
        # 原 discovery_agro 0.85 概率导致"走过房间没被拦"的观感（15% 落空），
        # 移动是副本推进主线，遇怪应确定；『探索』仍保持 discovery_agro 概率（主动探索可放空）。
        _left = rstate.get("monsters_left")
        _hit = False
        if isinstance(_left, list) and len(_left) > 0:
            _hit = True
        if _hit:
            # 遇怪 → 弹出 1 只 → 构建敌方阵列 → 进战斗（现状 _enter_stage_combat 链路）
            # v141 审计 #7：死代码接线——consume_monster 弹出（原 _left.pop(0) 内联）
            _def = self.consume_monster(st, target_sa["id"])
            if _def is None:
                yield event.plain_result(arrive_view)
                return
            self._enter_stage_combat(group_id, st, _def, target_sa)
            db.save_battle(group_id, st["leader"], st)
            _mon = st.get("boss") or {}
            yield event.plain_result(
                f"{arrive_view}\n"
                f"━━━━━━━━━━━━\n"
                f"🍃 刚踏进【{target_sa['name']}】，{_mon.get('name', '怪物')} 就扑了上来！\n"
                f"━━━━━━━━━━━━\n"
                f"{self._instance_battle_footer(st, group_id)}\n"
                f"⏳ 轮到 {self._instance_next_player_name(st, group_id)} 行动！『攻击』『技能 <名称>』『防御』"
            )
            return
        # Boss 房 + boss_alive → 触发 Boss 战（不消耗普通怪池）
        _dun = cur_map.get("dungeon") or {}
        _br = _dun.get("boss_room")
        _boss_alive = bool(rstate.get("boss_alive", False))
        if _br == target_sa["id"] and _boss_alive:
            boss_def = target_sa.get("boss")
            if boss_def:
                self._enter_stage_combat(group_id, st, boss_def, target_sa)
                rstate["boss_alive"] = False
                db.save_battle(group_id, st["leader"], st)
                _mon = st.get("boss") or {}
                yield event.plain_result(
                    f"{arrive_view}\n"
                    f"━━━━━━━━━━━━\n"
                    f"👑 踏入【{target_sa['name']}】，Boss【{_mon.get('name', '')}】Lv.{_mon.get('lv', '?')} 拦在面前！\n"
                    f"━━━━━━━━━━━━\n"
                    f"{self._instance_battle_footer(st, group_id)}\n"
                    f"⏳ 轮到 {self._instance_next_player_name(st, group_id)} 行动！『攻击』『技能 <名称>』『防御』"
                )
                return
        # 无事到达
        yield event.plain_result(arrive_view)

    def _travel_ambush(self, player: dict, target_map: dict, group_id=None, qq_id=None):
        """移动撞怪判定：返回撞到的怪物 dict 或 None。

        生物趋避利害：
        - 玩家等级 ≥ 地图等级+5：威慑低等级生物，不撞怪
        - 玩家等级 ≤ 地图等级-5：闯入强者地盘，30% 概率撞怪
        - 同级/略低：8~18% 概率
        城镇区域不撞怪（安全区）。'城镇外郊' 类型数据不存在，v102.1 清理。
        """
        mtype = target_map.get("type", C.MAP_TYPE_FIELD)
        if mtype == C.MAP_TYPE_TOWN:
            return None
        # v95.23 #247：副本区域不参与移动撞怪——副本 Boss 在入口子区域 monsters 池里，
        # 撞怪会绕过『副本 <名字>』开本流程的等级/人数校验，低等级玩家进副本入口被 Boss 秒杀。
        # 副本入口应显示地图信息，引导玩家走开本流程（'副本' 命令有完整校验）。
        # v105 M19 P0：主线击杀目标只挂副本时放行——撞怪池仅保留主线目标怪
        # （走下方统一概率判定，Boss 按等级差概率撞，不绕过任何校验之外的新增风险面）。
        if mtype == C.MAP_TYPE_INSTANCE:
            # v105 M19 P0：主线击杀目标只挂副本时放行——撞怪池仅保留主线目标怪
            # （走下方统一概率判定；group_id/qq_id 为空=既有测试直调场景，维持原跳过）
            _main_ent = None
            if group_id and qq_id:
                _main_ent = self._main_kill_target_on_map(group_id, qq_id, target_map)
            if not _main_ent:
                return None
            monsters = [_main_ent]
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
            return C.build_monster(random.choice(monsters), target_map, lv_jitter=1)
        # v87.6 内容下沉子区域：优先取落点入口子区域的怪；入口无怪才找最近有怪子区域
        # （M22 P3：原逻辑取"首个有怪子区域"，入口无怪时会抽到深处高等级怪，玩家刚进图就被深处怪秒）
        _sas = target_map.get("subareas") or []
        _entry_id = C.map_entry_subarea(target_map.get("id", ""))
        monsters = []
        for sa in _sas:
            if sa["id"] == _entry_id and sa.get("monsters"):
                monsters = sa["monsters"]
                break
        if not monsters:
            # 入口无怪：线性图按列表顺序扫描即离入口由近及远
            for sa in _sas:
                if sa.get("monsters"):
                    monsters = sa["monsters"]
                    break
        if not monsters:
            return None
        diff = target_map.get("lv", 1) - player["level"]
        if diff <= -5:
            return None
        # v130.7 意见#28 越级风险增强：比玩家高 5 级起，撞怪概率随等级差线性提升
        # （0.30 + (diff-5)*0.05；低 10 级 = 0.55，低 11 级+ = 0.60 封顶）
        if diff >= 5:
            chance = min(0.60, 0.30 + (diff - 5) * 0.05)
        elif diff >= 0:
            chance = 0.18
        else:
            chance = 0.08
        if random.random() >= chance:
            return None
        # v101.25c 移动撞怪也带等级波动（普通怪 ±1，精英/Boss 固定）
        # v130.8 意见#32：±1 感知弱 → 增强为 ±2；v132 鱼鱼拍板改回 ±1（面板明示 Lv.X±1）
        return C.build_monster(random.choice(monsters), target_map, lv_jitter=1)


    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:祭坛|方碑)(?:\s*|$)")
    @require_player()

    async def portal_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        portals = db.get_portals(qq_id)
        cur = player["cur_map"]
        lines = ["🌌 【旅者方碑】", "━━━━━━━━━━━━"]
        # 当前地图
        if cur in C.PORTALS:
            p = C.PORTALS[cur]
            if cur in portals:
                lines.append(f"📍 此地：{p['icon']}{p['name']}(已激活)")
            else:
                lines.append(f"📍 此地：{p['icon']}{p['name']}(未激活，『激活』解锁！)")
        else:
            lines.append("📍 此地没有方碑")
        lines.append("━━━━━━━━━━━━")
        if not portals:
            lines.append("你还没激活任何方碑……去大陆各处寻找方碑，『激活』解锁传送点吧！")
        else:
            lines.append("✨ 已激活方碑(『传送 <序号>』直达)：")
            # v101.30d #O26：坐骑折扣在列表标注（playtest 格温：显示 175 实际扣 140）
            mounts = player.get("mounts") or {}
            active_mk = mounts.get("active")
            disc = 0.0
            if active_mk and active_mk in C.MOUNT_BY_KEY:
                disc = float(C.MOUNT_BY_KEY[active_mk].get("discount", 0) or 0)
            for i, mid in enumerate(portals, 1):
                m = C.MAP_BY_ID.get(mid, {})
                p = C.PORTALS.get(mid, {})
                cost = C.portal_cost(m)
                shown = cost
                tag = ""
                if disc > 0:
                    shown = max(C.ECON_CONFIG["portal_min_cost"], int(cost * (1 - disc)))
                    tag = f"（骑乘坐骑 {int(disc*100)}% 折扣）"
                name = p.get("name", mid) if p else mid
                icon = p.get("icon", "🌌") if p else "🌌"
                lines.append(f" {i}. {icon}{name}({m.get('name', '?')} · {shown} 金币{tag})")
        lines.append("━━━━━━━━━━━━")
        lines.append(self._tip("portal"))
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:激活祭坛|激活)(?:\s*|$)")
    @require_player()

    async def portal_activate(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        cur = player["cur_map"]
        if cur not in C.PORTALS:
            yield event.plain_result("这里没有方碑……寻找大陆上古道上刻着符文的古老路标吧！")
            return
        # v87.17 子区域绑定：方碑矗立在首个子区域（广场），必须走到跟前才能激活
        _pm = C.MAP_BY_ID.get(cur, {})
        _first_sa = (_pm.get("subareas") or [None])[0]
        if _first_sa and player.get("cur_subarea") != _first_sa.get("id"):
            yield event.plain_result(
                f"🌌 {C.PORTALS[cur].get('icon', '')}{C.PORTALS[cur].get('name', '方碑')}矗立在"
                f"{_first_sa.get('name', '广场')}，你离得太远够不着！（『前往 {_first_sa.get('name', '广场')}』）"
            )
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
            f"📍 传送点已激活：{m.get('name', '?')}(✨ 经验 +{exp})\n"
            f"💡 输入『方碑』查看全部已激活方碑，『传送 {p['name']}』即可直达！"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?传送(?:\s*|$)")
    @require_player()
    @no_prof_waiting()

    async def portal_travel(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        dest = self._strip_cmd(event, "传送").strip()
        player = self._player(group_id, qq_id)
        if not dest:
            yield event.plain_result("传送到哪？『方碑』查看已激活方碑，『传送 <名称/序号>』直达～")
            return
        if self._in_battle(group_id, qq_id):
            yield event.plain_result("⚔️ 你正在战斗中！输入『攻击』/『技能 <名称>』继续战斗，『防御』『逃跑』『用药』可选——先解决眼前的敌人再说传送。")
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
            cost = max(C.ECON_CONFIG["portal_min_cost"], int(cost * (1 - disc)))
        if player["gold"] < cost:
            yield event.plain_result(f"传送需要 {cost} 金币(你只有 {player['gold']})！打怪攒点金币吧～")
            return
        # v86 子区域：传送落地目标图首个子区域
        tgt_sas = target.get("subareas") or []
        first_sa = tgt_sas[0] if tgt_sas else None
        db.update_player(group_id, qq_id, gold=player["gold"] - cost, cur_map=target["id"],
                         cur_subarea=first_sa["id"] if first_sa else "")
        db.add_visited(group_id, qq_id, target["id"])
        # v115 探索见闻：传送到达也记录子区域到访（H 提供，getattr 兜底）
        _rec_txt = ""
        _rec = getattr(C, "exploration_record_visit", None)
        if _rec is not None and first_sa is not None:
            try:
                _rv = _rec(group_id, qq_id, target["id"], first_sa.get("id", ""))
                if _rv:
                    _rwt = _rv.get("reward") or ""
                    if _rwt:
                        _rec_txt = f"\n🎉 {_rwt}"
            except Exception:
                _rec_txt = ""
        # v95 #142：传送落地后清除对话会话（否则对话状态跨图残留，『前往』被"还在交谈中"拦截）
        db.clear_talk_state(group_id, qq_id)
        quest_lines = self._update_explore_quests(group_id, qq_id, target["id"])
        extra = ""
        if quest_lines:
            extra = "\n\n" + "\n".join(quest_lines)
        p = C.PORTALS.get(target["id"], {})
        pname = p.get("name", "方碑") if p else "方碑"
        picon = p.get("icon", "🌌") if p else "🌌"
        yield event.plain_result(
            f"🌌 星辉流转，你踏入了传送通道……\n"
            f"✨ 你抵达了【{target['name']}】({picon}{pname}，花费 {cost} 金币)\n"
            f"{target['desc']}{extra}{_rec_txt}"
        )

    def _update_explore_quests(self, group_id, qq_id, map_id):
        """到达子区域时检查 explore 型任务(主线和支线)"""
        lines = []
        quests = db.get_quests(group_id, qq_id)
        changed = False
        # 主线 explore（v105：仅已接取(active)时触发——pending 未接取到达目标图不得自动完成+发奖）
        main_id = quests.get("main_quest")
        if main_id and quests.get("main_status") == "active":
            mq = next((q for q in C.MAIN_QUESTS if q["id"] == main_id), None)
            if mq and mq["objective"].get("explore") == map_id:
                # v124.3：奖励统一走 _grant_quest_rewards（exp/gold/升级 + reward_item 全格式
                # + reward_pet/reward_mount/unlock_class）——此前 explore 自动完成只有
                # reward_item 单值，reward_pet 配了也静默不发
                self._grant_quest_rewards(group_id, qq_id, mq, lines)
                completed = list(quests.get("completed_main", []))
                completed.append(main_id)
                quests["completed_main"] = completed
                quests["main_quest"] = mq["next"]
                # v105 M19 P1：explore 自动完成必须重置 main_status=pending（与 _take_main_quest
                # 交付分支一致）——此前遗留 "active" 导致任务面板显示"进行中"而非"未接取"、
                # 对话树 quest_pending 接取入口不亮（q1_5 完成后 q1_6 需 3-4 轮对话才兜底接取）
                quests["main_status"] = "pending"
                quests["main_progress"] = {}
                changed = True
                lines.append(f"📜 主线『{mq['name']}』达成！奖励：经验 +{mq['reward_exp']} 金币 +{mq['reward_gold']}")
                # v105 M19 P2：explore 自动完成补发声望（奖励本体已并入 _grant_quest_rewards）
                _rep = self._quest_reputation(group_id, qq_id, mq["giver"])
                if _rep:
                    lines.append(f"  {_rep}")
                if mq["next"]:
                    nq = next((q for q in C.MAIN_QUESTS if q["id"] == mq["next"]), None)
                    if nq:
                        lines.append(f"📜 新主线：『{nq['name']}』{nq['desc']}")
                else:
                    lines.append("🎊 恭喜！你完成了全部主线任务，成为奥兰迪亚的传说！")
        # 支线 explore
        side = dict(quests.get("side", {}))
        for sid, sq in list(side.items()):
            if sq.get("status") == "active":
                sqd = next((q for q in C.SIDE_QUESTS if q["id"] == sid), None)
                if sqd and sqd["objective"].get("explore") == map_id:
                    sq["status"] = "ready"
                    changed = True
                    _g = C.NPCS.get(sqd["giver"]) or C.ALL_WILD.get(sqd["giver"]) or {}
                    lines.append(f"📜 支线『{sqd['name']}』目标达成！回去找 {_g.get('name', '？')} {self._deliver_hint(sqd['giver'])}吧～")
        if changed:
            quests["side"] = side
            db.save_quests(group_id, qq_id, quests)
        return lines

    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:任务|主线)(?:\s*|$)")
    @require_player()

    async def quest_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if self._is_redname(qq_id):
            yield event.plain_result("☠️ 你是红名！守卫不让你靠近任务板……(等红名消退再来)")
            return
        quests = db.get_quests(group_id, qq_id)
        lines = ["📜 【冒险日志】", "━━━━━━━━━━━━"]
        # 主线
        main_id = quests.get("main_quest")
        if main_id:
            mq = next((q for q in C.MAIN_QUESTS if q["id"] == main_id), None)
            # v104 M19：旧存档 main_quest 指向已下线 id（如 "q1"）→ 面板主线空白。
            # 与 _take_main_quest 同样的存档容错：重置回主线起点并落库。
            if not mq:
                quests["main_quest"] = "q1_1"
                quests["main_status"] = "pending"
                quests["main_progress"] = {}
                main_id = "q1_1"
                mq = next((q for q in C.MAIN_QUESTS if q["id"] == main_id), None)
                db.save_quests(group_id, qq_id, quests)
            if mq:
                _ginfo = C.NPCS.get(mq["giver"]) or C.ALL_WILD.get(mq["giver"]) or {}
                giver = _ginfo.get("name", "？")
                giver_map = _ginfo.get("map", "")
                giver_map_name = C.MAP_BY_ID.get(giver_map, {}).get("name", "？")
                lines.append(f"【主线】『{mq['name']}』")
                lines.append(f"  {mq['desc']}")
                st = quests.get("main_status", "pending")
                if st == "pending":
                    lines.append(f"  ⏳ 未接取：去找 {giver}(在{giver_map_name})对话接取")
                elif st == "ready":
                    # v95.25 #47b：主线交付=找 NPC 自动触发（与『交付任务』指令并存），不写死交付方式
                    lines.append(f"  ✅ 目标达成！回去找 {giver} 交付")
                else:
                    prog = quests.get("main_progress", {})
                    obj = mq["objective"]
                    # v101.3：目标类型展示查表化（kill/collect/explore/talk，顺序与原 if-elif 一致）
                    for _k, _fn in _OBJ_PROGRESS_LINES.items():
                        if obj.get(_k):
                            lines.append(_fn(obj, prog))
                            break
        else:
            lines.append("【主线】已全部完成！🎊")
        # 支线（v101.25i3：已完成任务不进面板，鱼鱼：交了还显示）
        side = quests.get("side", {})
        side_items = [(sid, sq) for sid, sq in side.items() if sq.get("status", "active") != "done"]
        if side_items:
            lines.append("")
            lines.append("【支线】")
            raw = self._strip_cmd(event, "任务")
            page = self._parse_page(raw)
            page_items, pages, page = self._page_items(side_items, page, per_page=5)
            for i, (sid, sq) in enumerate(page_items, (page - 1) * 5 + 1):
                sqd = next((q for q in C.SIDE_QUESTS if q["id"] == sid), None)
                if not sqd:
                    continue
                giver = (C.NPCS.get(sqd["giver"]) or C.ALL_WILD.get(sqd["giver"]) or {}).get("name", "？")
                st = sq.get("status", "active")
                obj = sqd["objective"]
                # v95.12：已交付支线显示已完成（不占可交付位）
                if st == "done":
                    lines.append(f"{i:>2}. 『{sqd['name']}』[✅ 已完成]")
                    continue
                # v127.7 排版：任务名单独一行（名字+状态），描述缩进下一行，目标进度行统一再缩进
                # v116 §3.4：进行中支线可放弃（主线不可弃），放弃提示统一放面板底部（v123e 去行尾冗余）
                # 收集型：实时按背包材料判断（v104 补测：复合目标同时显示击杀进度防误导）
                if obj.get("collect"):
                    have = db.count_item(group_id, qq_id, obj["collect"])
                    need = obj.get("collect_count") or obj.get("count", 1)  # v125.1 P2：s64 等 collect_count 无 count 的复合目标不再 KeyError
                    prog = sq.get("progress", {})
                    kill_txt = ""
                    if obj.get("kill"):
                        kv = _kill_prog_count(obj, prog)  # v105 M19 P2：兼容旧档老 key 聚合
                        kill_txt = f"｜击杀：{kv}/{obj.get('count', 0)}"
                    if have >= need:
                        lines.append(f"{i:>2}. 『{sqd['name']}』[✅ 可交{kill_txt}]")
                        lines.append(f"    {sqd['desc']}")
                        lines.append(f"    材料已齐！回去找 {giver} {self._deliver_hint(sqd['giver'])}")
                    else:
                        lines.append(f"{i:>2}. 『{sqd['name']}』[⏳{kill_txt}]")
                        lines.append(f"    {sqd['desc']}")
                        lines.append(f"    收集：{obj['collect']} {have}/{need}{kill_txt}")
                    # v125.1 P2：复合目标（collect+use/find/explore，如 s53/s56/s64/s105）
                    # 补显其余目标行，与 find/use 分支的 _obj_text_lines 展示口径一致
                    # （收集/击杀行已在上方展示，过滤避免重复）
                    for _t in self._obj_text_lines(obj, st):
                        if _t.startswith(("收集", "击败")):
                            continue
                        lines.append(f"    {_t}")
                    continue
                # v104 M20 P2：find 型（告示委托等）面板提示机制——在 XX 探索有概率遇到
                # （此前走通用兜底只显示 desc+[⏳]，玩家不知如何推进）
                if obj.get("find"):
                    lines.append(f"{i:>2}. 『{sqd['name']}』[{'✅ 可交' if st == 'ready' else '⏳'}]")
                    lines.append(f"    {sqd['desc']}")
                    # v124.2 复合目标逐行显示（s18 kill+find 两行都展示）
                    for _t in self._obj_text_lines(obj, st):
                        lines.append(f"    {_t}")
                    if st == "ready":
                        lines.append(f"    回去找 {giver} {self._deliver_hint(sqd['giver'])}")
                    continue
                # v124 use 型（使用指定物品达成）——同 find 处理
                if obj.get("use"):
                    lines.append(f"{i:>2}. 『{sqd['name']}』[{'✅ 可交' if st == 'ready' else '⏳'}]")
                    lines.append(f"    {sqd['desc']}")
                    for _t in self._obj_text_lines(obj, st):
                        lines.append(f"    {_t}")
                    if st == "ready":
                        lines.append(f"    回去找 {giver} {self._deliver_hint(sqd['giver'])}")
                    continue
                mark = "✅ 可交" if st == "ready" else "⏳"
                lines.append(f"{i:>2}. 『{sqd['name']}』[{mark}]")
                lines.append(f"    {sqd['desc']}")
                if st == "ready":
                    lines.append(f"    回去找 {giver} {self._deliver_hint(sqd['giver'])}")
            # v127.7 翻页提示补全：上一页/下一页 + 总页数（此前只有下一页）
            if pages > 1:
                _nav = []
                if page > 1:
                    _nav.append(f"『任务 {page-1}』上一页")
                if page < pages:
                    _nav.append(f"『任务 {page+1}』下一页")
                lines.append(f"💡 {' | '.join(_nav)}(共 {pages} 页)")
            self._record_list_state(qq_id, "任务", page, pages)
        else:
            lines.append("")
            lines.append("【支线】暂无——找镇上的 NPC 聊聊可能有意外收获")
        # 每日
        # v116 §3.4：daily 含 _completed/_repeat 元数据（active 任务清空后仍在）——
        # 只剩元数据 = 今日全部完成，按"已完成"分支展示；_completed 超额时给出计数。
        # v127.7：玩家从未领取（daily 为空）→ 提示『每日』领取，不再误报"已完成"。
        daily = quests.get("daily", {})
        active_keys = [k for k in daily if k not in _DAILY_META_KEYS]
        if active_keys:
            lines.append("")
            lines.append("【每日】")
            _daily_n = 0  # v116 每日任务序号（仅计实际任务，跨元数据）
            for dkey, dq in daily.items():
                if dkey in _DAILY_META_KEYS:  # 跨天/计数元数据，跳过
                    continue
                _daily_n += 1
                # v125.1 P2：序号用 _daily_n（仅计实际任务）——原用 enumerate 的 i 会把
                # _date/_completed/_repeat 元数据占位算进去（面板显示 4./5.，『放弃』按 1..N 对不上）
                need = _daily_need(dq)
                # v127.7 排版：每日任务名单独一行，描述缩进下一行
                if need is None:
                    # v125.1 P2：无达标数定义时只显示实际进度，不再兜底假 99
                    lines.append(f"{_daily_n:>2}. 『{dq['name']}』")
                    lines.append(f"    {dq['desc']} (进度 {dq.get('progress', 0)})")
                else:
                    lines.append(f"{_daily_n:>2}. 『{dq['name']}』")
                    lines.append(f"    {dq['desc']} ({dq.get('progress',0)}/{need})")
        else:
            lines.append("")
            if not daily:
                # v127.7 修复：从未领取（新号/跨天清空）→ 引导领取，不显示"已完成"
                lines.append("【每日】今日还没领取任务——输入『每日』发布今日悬赏～")
            else:
                _done = int(daily.get("_completed", 0) or 0)
                if _done >= DAILY_LIMIT:
                    lines.append(f"【每日】今日已完成 {_done}/{DAILY_LIMIT} 个每日任务，明天再来！")
                else:
                    lines.append(f"【每日】今日已完成 {_done} 个每日任务——输入『每日』还能再接～")
        # v101.30d #O1：师门考验追踪——对话树进行中时面板显示（playtest 小红：考验无面板条目）
        _MASTER_IDS = ("npc_herb_master", "npc_mine_master", "npc_fish_master", "npc_cook_master",
                       "npc_alchemy_master", "npc_craft_master", "npc_enhance_master", "npc_rune_master")
        ts = db.get_talk_state(group_id, qq_id)
        if ts and ts.get("npc") in _MASTER_IDS:
            _tnpc = C.NPCS.get(ts["npc"]) or {}
            lines.append("")
            lines.append("【师门考验】")
            lines.append(f"  ⏳ 正在接受【{_tnpc.get('name', '导师')}】的拜师考验，回复『继续』接着进行")
        lines.append("")
        # v127.1 每面板只抽 1 条随机提示（v123e 放弃/接取引导并入随机池）
        lines.append(self._tip("quest"))
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?接取(?:\s*|$)")
    @require_player()

    async def quest_accept(self, event: AstrMessageEvent):
        """v95.7 #38：『接取任务』/『接取 <任务名>』——当前地图有发布 NPC 时直接接取，否则提示位置"""
        group_id, qq_id = self._uid(event)
        raw = self._strip_cmd(event, "接取").strip()
        player = self._player(group_id, qq_id)
        quests = db.get_quests(group_id, qq_id)
        # 主线（pending 可接）
        main_id = quests.get("main_quest")
        mq = next((q for q in C.MAIN_QUESTS if q["id"] == main_id), None) if main_id else None
        # v123d：『接取 <序号>』——先按无参数列表全局序号映射到任务名（参数统一铁律：
        # 列表展示序号即可选），映射后统一走下方名字分支（主线/支线都命中）
        if raw and raw.isdigit():
            _avail = self._available_quest_list(player, quests, mq)
            idx = int(raw)
            if 1 <= idx <= len(_avail):
                raw = _avail[idx - 1]["name"]
            else:
                yield event.plain_result(f"❌ 序号无效！当前可接取 {len(_avail)} 个任务，输入『接取』查看列表～")
                return
        if mq:
            st = quests.get("main_status", "pending")
            if st == "pending" and (not raw or raw in (mq["name"], "任务", "主线")):
                npc = C.NPCS.get(mq["giver"]) or C.ALL_WILD.get(mq["giver"]) or {}
                if npc.get("map") == player["cur_map"]:
                    lines = self._take_main_quest(group_id, qq_id, mq["giver"], npc)
                    yield event.plain_result("\n".join(lines))
                    return
                giver_map = C.MAP_BY_ID.get(npc.get("map", ""), {}).get("name", "？")
                yield event.plain_result(f"当前主线『{mq['name']}』由 {npc.get('name', '？')}(在{giver_map}) 发布，去找他对话接取～")
                return
            # v95.8 #47：主线进行中/待交付时，无参数『接取』不应静默去接支线
            # v95.14：『接取任务』/『接取 主线』（raw=任务/主线）等同无参数，同样提示主线状态
            if not raw or raw in ("任务", "主线"):
                if st == "ready":
                    yield event.plain_result(f"主线『{mq['name']}』已完成目标！回 {(C.NPCS.get(mq['giver']) or C.ALL_WILD.get(mq['giver']) or {}).get('name', '发布人')} 处对话领奖励～")
                else:
                    yield event.plain_result(f"主线『{mq['name']}』进行中！输入『任务』查看进度～")
                return
            # v95.20 #103：指名当前主线名但非 pending → 明确提示进行中/待交付
            # （此前会落到底部"可接取任务列表"分支，回显无关支线误导玩家）
            if raw == mq["name"]:
                if st == "ready":
                    yield event.plain_result(f"主线『{mq['name']}』已完成目标！回 {(C.NPCS.get(mq['giver']) or C.ALL_WILD.get(mq['giver']) or {}).get('name', '发布人')} 处对话领奖励～")
                else:
                    yield event.plain_result(f"主线『{mq['name']}』已在进行中，无需重复接取！输入『任务』查看进度～")
                return
        # 支线：必须指名道姓才接（v95.8 #47：无参数/『接取 任务』不再静默接支线）
        if raw and raw not in ("任务", "主线"):
            for sq in C.SIDE_QUESTS:
                if raw not in (sq["name"],):
                    continue
                # v95.27：先判已接（此前 continue 跳过后 raw 落到底部无关列表，提示不明确）
                if sq["id"] in (quests.get("side") or {}):
                    yield event.plain_result(f"『{sq['name']}』已接取！输入『任务』查看进度～")
                    return
                # v104 审计 P1-1：『接取』指令同样校验 min_level
                # （此前只有 _offer_side_quests 自动接取路径校验，Lv.1 可直接接走 Lv.40 雾中灯塔）
                if sq.get("min_level") and player["level"] < sq["min_level"]:
                    yield event.plain_result(
                        f"🛡️ 『{sq['name']}』需要 Lv.{sq['min_level']} 才能接取！（你当前 Lv.{player['level']}）"
                    )
                    return
                # v124 链式支线：unlock 前置未满足 → 提示前置未完成
                if not self._sq_unlocked(quests, sq):
                    _pre = sq.get("unlock")
                    _pn = []
                    if isinstance(_pre, list):
                        _pn = [next((q["name"] for q in C.SIDE_QUESTS if q["id"] == x.get("id")), "前置任务") for x in _pre if isinstance(x, dict)]
                    elif isinstance(_pre, dict):
                        _pn = [next((q["name"] for q in C.SIDE_QUESTS if q["id"] == _pre.get("id")), "前置任务")]
                    yield event.plain_result(
                        f"🔒 『{sq['name']}』的线索还没出现——先完成『{_pn[0] if _pn else '前置任务'}』再来看看吧。"
                    )
                    return
                # v124 隐藏线：require_stats 计数门槛
                if not self._sq_stats_met(player, sq):
                    _rs = sq.get("require_stats") or {}
                    _need = ", ".join(f"{k} {v}次" for k, v in _rs.items())
                    yield event.plain_result(
                        f"🔒 这条委托背后还藏着秘密……（需要 {_need} 后才会出现）"
                    )
                    return
                # v113 种族限制：require_race 指定血脉（隐藏线试炼）——非该种族拒绝接取
                if sq.get("require_race"):
                    _rr = sq["require_race"]
                    _cur = player.get("race") or "human"
                    if _cur != _rr:
                        _rcn = (C.RACES.get(_rr) or {}).get("name", "对应血脉")
                        _ccn = (C.RACES.get(_cur) or {}).get("name", "未知血脉")
                        yield event.plain_result(
                            f"⛔ 『{sq['name']}』需要{_rcn}的血脉才能接下——"
                            f"你身为{_ccn}，与这份传承无缘。"
                        )
                        return
                # v97.1 告示委托（board: true）：在告示板所在的子区域接取，不要求发布 NPC 在场
                if sq.get("board"):
                    prop_ids = C.subarea_props(player["cur_map"], player.get("cur_subarea") or "")
                    has_board = any(
                        C.prop_entry(e)[0] == "notice_board" for e in prop_ids
                    )
                    if not has_board:
                        yield event.plain_result(
                            f"告示委托『{sq['name']}』要去告示板前才能接取！输入『交互 告示板』看看～")
                        return
                    # v95.27 修复：告示板只接指定委托，不连带同 giver 的其他支线
                    # （此前走 _offer_side_quests 按 giver 全接，寻猫·虎斑顺带接了史莱姆果冻）
                    side = dict(quests.get("side", {}))
                    side[sq["id"]] = {"status": "active", "progress": {}}
                    quests["side"] = side
                    db.save_quests(group_id, qq_id, quests)
                    lines = [
                        f"📜 【支线】『{sq['name']}』{sq['desc']}",
                        f"  奖励：经验 +{sq['reward_exp']} 金币 +{sq['reward_gold']}",
                        f"  🎯 目标：{self._obj_text(sq['objective'])}",
                    ]
                    yield event.plain_result("\n".join(lines))
                    return
                npc = C.NPCS.get(sq["giver"]) or C.ALL_WILD.get(sq["giver"]) or {}
                if npc.get("map") == player["cur_map"]:
                    # v95r65 #295：指名接取只接该任务（此前调 _offer_side_quests 按 giver 全接，
                    # 会连带接取同 giver 的告示板委托——『接取 史莱姆果冻』顺带接走『寻猫·虎斑』）
                    side = dict(quests.get("side", {}))
                    side[sq["id"]] = {"status": "active", "progress": {}}
                    quests["side"] = side
                    db.save_quests(group_id, qq_id, quests)
                    lines = [
                        f"📜 【支线】『{sq['name']}』{sq['desc']}",
                        f"  奖励：经验 +{sq['reward_exp']} 金币 +{sq['reward_gold']}",
                        f"  🎯 目标：{self._obj_text(sq['objective'])}",
                    ]
                    yield event.plain_result("\n".join(lines))
                    return
                giver_map = C.MAP_BY_ID.get(npc.get("map", ""), {}).get("name", "？")
                yield event.plain_result(f"支线『{sq['name']}』由 {npc.get('name', '？')}(在{giver_map}) 发布，去找他对话接取～")
                return
        # 无参数 → 列出当前地图可接任务（主线 pending + 未接支线）
        available = self._available_quest_list(player, quests, mq)
        if available:
            lines = ["📜 【可接取任务】", "━━━━━━━━━━━━"]
            lines += [f"{i:>2}. 📜 {a['line']}" for i, a in enumerate(available, 1)]
            lines.append(self._tip("accept"))
            yield event.plain_result("\n".join(lines))
            return
        # v95.15 #70：指名接取但上面没匹配到 → 明确提示未找到/已接取
        if raw and raw not in ("任务", "主线"):
            all_names = [q["name"] for q in C.SIDE_QUESTS] + [q["name"] for q in C.MAIN_QUESTS]
            if raw in all_names:
                yield event.plain_result(f"任务『{raw}』已接取或已完成，输入『任务』查看进度～")
            else:
                yield event.plain_result(f"未找到名为『{raw}』的任务。输入『任务』查看进度～")
            return
        yield event.plain_result("没有可接取的任务。输入『任务』查看进度～")

    def _sq_unlocked(self, quests, sq):
        """v124 链式支线：unlock 前置解锁检查。unlock 支持单条或列表（全部满足）。
        格式：{"side": "s5"} 或 {"main": "q2_3"}（兼容 {"type":"side","id":"s5"} 写法）。
        无 unlock=天然解锁。"""
        u = sq.get("unlock")
        if not u:
            return True
        us = u if isinstance(u, list) else [u]
        for x in us:
            if not isinstance(x, dict):
                continue
            _typ = x.get("type") or ("side" if x.get("side") else "main" if x.get("main") else None)
            _tid = x.get("id") or x.get("side") or x.get("main") or ""
            if _typ == "side":
                # 支线完成 = side dict 中该任务 status==done
                _sq = (quests.get("side") or {}).get(_tid) or {}
                if _sq.get("status") != "done":
                    return False
            elif _typ == "main":
                _cm = quests.get("completed_main") or []
                if _tid not in _cm and quests.get("main_quest") != _tid:
                    return False
        return True

    def _sq_stats_met(self, player, sq):
        """v124 隐藏线/副业线：require_stats 动作计数门槛。达标才可接取。
        stats 表以 qq_id 为主键，group_id 参数为兼容占位。"""
        rs = sq.get("require_stats")
        if not rs:
            return True
        _qq = player.get("qq_id") or player.get("id", "")
        if not _qq:
            return False
        _st = db.get_stats("", _qq) or {}
        for k, v in rs.items():
            if int(_st.get(k, 0) or 0) < int(v):
                return False
        return True

    def _available_quest_list(self, player, quests, mq) -> list:
        """当前地图可接取任务列表（v123d 抽出，供『接取』无参渲染与『接取 <序号>』映射共用）。

        返回 [{"name": 任务名, "line": 渲染行（不含 📜 前缀）}, ...]——主线 pending 在前，
        支线按 C.SIDE_QUESTS 顺序；告示委托（board）不在此列（须去告示板指名接取）。
        """
        available = []
        if mq and quests.get("main_status") == "pending":
            giver = C.NPCS.get(mq["giver"]) or C.ALL_WILD.get(mq["giver"]) or {}
            if giver.get("map") == player["cur_map"]:
                available.append({
                    "name": mq["name"],
                    "line": f"主线『{mq['name']}』（{giver.get('name', '？')}发布）",
                })
        for sq in C.SIDE_QUESTS:
            if sq["id"] in (quests.get("side") or {}):
                continue
            # v124 链式支线：unlock 前置未满足不出现在可接列表
            if not self._sq_unlocked(quests, sq):
                continue
            # v124 隐藏线：require_stats 计数门槛未达不出现在可接列表
            if not self._sq_stats_met(player, sq):
                continue
            # v104 M20 P2：告示委托（board: true）只在告示板子区域指名接取，
            # 列入普通列表会误导玩家（点名接取被 world.py 告示板拦截逻辑挡下）
            if sq.get("board"):
                continue
            npc = C.NPCS.get(sq["giver"]) or C.ALL_WILD.get(sq["giver"]) or {}
            if npc.get("map") == player["cur_map"]:
                # v104 M19：接取列表显示支线等级门槛
                _lv = f"Lv.{sq['min_level']}+ " if sq.get("min_level") else ""
                available.append({
                    "name": sq["name"],
                    "line": f"支线『{sq['name']}』{_lv}（{npc.get('name', '？')}发布）",
                })
        return available


    # v116 §3.4：放弃进行中的支线/每日任务（释放接取位）。主线不可放弃。
    @filter.regex(r"^(?:\[At:\d+\]\s*)?放弃(?:\s*(\d+))?\s*$")

    async def quest_abandon(self, event: AstrMessageEvent):
        """『放弃 <序号>』——放弃进行中的支线/每日任务；主线走『任务』面板提示不可弃。

        序号与任务面板（quest_view）全局编号一致：侧支线 1..S，每日 S+1..S+D。
        已完成任务/序号越界/无任务 → 给明确提示。
        """
        group_id, qq_id = self._uid(event)
        raw = self._strip_cmd(event, "放弃").strip()
        quests = db.get_quests(group_id, qq_id)
        # 侧支线（按 dict 顺序，与面板一致；done 不算可放弃位）
        side = dict(quests.get("side", {}) or {})
        side_items = [(sid, sq) for sid, sq in side.items()
                      if sq.get("status", "active") != "done"]
        # 每日（剔除元数据键）
        daily = dict(quests.get("daily", {}) or {})
        daily_items = [(dk, dq) for dk, dq in daily.items() if dk not in _DAILY_META_KEYS]
        total = len(side_items) + len(daily_items)
        index_able = raw and raw.isdigit()
        if not index_able:
            # v116 §3.4：主线不可放弃——指名主线/『主线』字样给明确拒绝提示
            main_id = quests.get("main_quest")
            mq = next((q for q in C.MAIN_QUESTS if q["id"] == main_id), None) if main_id else None
            if raw in ("主线", "main") or (mq and raw == mq["name"]):
                yield event.plain_result("主线任务无法放弃！主线是奥兰迪亚之王赐下的使命～")
                return
            if total == 0:
                yield event.plain_result("🗑️ 当前没有可放弃的任务（进行中的支线或每日任务）～")
                return
            yield event.plain_result(f"🗑️ 请指定要放弃的任务序号（1-{total}），发『放弃 <序号>』～")
            return
        idx = int(raw)
        if not (1 <= idx <= total):
            yield event.plain_result(f"🗑️ 序号 {idx} 不存在！请输入 1-{total} 之间的序号～")
            return
        # 主线不可放弃：序号全部落在侧支线/每日，主线本来就不参与编号；单独拦截侧支线里的"主线位"不存在
        if 1 <= idx <= len(side_items):
            sid, sq = side_items[idx - 1]
            del side[sid]
            quests["side"] = side
            qname = next((q["name"] for q in C.SIDE_QUESTS if q["id"] == sid), "该支线")
            db.save_quests(group_id, qq_id, quests)
            yield event.plain_result(f"🗑️ 已放弃任务：『{qname}』")
            return
        # 每日任务
        dk, dq = daily_items[idx - len(side_items) - 1]
        del daily[dk]
        quests["daily"] = daily
        db.save_quests(group_id, qq_id, quests)
        yield event.plain_result(f"🗑️ 已放弃任务：『{dq.get('name', '该每日任务')}』")


    # v104 M24 P2-1：『每日副业』前缀误触『每日』面板——负向断言收窄（别名注册到 daily_prof）
    @filter.regex(r"^(?:\[At:\d+\]\s*)?每日(?!副业)(?:\s*|$)")
    @require_player()

    async def daily(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if self._is_redname(qq_id):
            yield event.plain_result("☠️ 你是红名！悬赏板上的任务都被守卫收走了……(等红名消退再来)")
            return
        quests = db.get_quests(group_id, qq_id)
        # v94 跨天清理：昨天的任务过期，先清空再判断（旧存档无 _date 视为过期）
        if db.expire_daily(quests):
            db.save_quests(group_id, qq_id, quests)
        daily = quests.get("daily") or {}
        # v116 §3.4 每日防刷：已完成任务（_completed 计数）≥ 上限 → 不再抽新任务
        completed = int(daily.get("_completed", 0) or 0)
        if completed >= DAILY_LIMIT:
            yield event.plain_result(
                f"⚠️ 今日已完成 {completed}/{DAILY_LIMIT} 个每日任务，明天再来吧！"
            )
            return
        if any(k not in _DAILY_META_KEYS for k in daily):
            yield event.plain_result("你已经有每日任务了！输入『任务』查看～")
            return
        # v116 保留今日已完成/重复计数（active 任务清空后重新抽取时不可归零，防刷衰减判定持续有效）
        base_completed = completed
        repeat = dict(daily.get("_repeat", {}) or {})
        # v94 随机抽 2 个每日任务（按等级过滤：低等级不抽打不到的任务）
        pool = [dq for dq in C.DAILY_QUESTS if self._daily_pool(player, dq)]
        chosen = random.sample(pool, min(2, len(pool)))
        import datetime as _dt
        daily = {"_date": _dt.date.today().isoformat(),
                 "_completed": base_completed, "_repeat": repeat}
        for i, dq in enumerate(chosen):
            rpt = int(repeat.get(dq["name"], 0) or 0)  # 今日已完成的同任务次数 → 衰减档
            factor = _DAILY_REPEAT_FACTORS[rpt] if rpt < len(_DAILY_REPEAT_FACTORS) else _DAILY_REPEAT_FACTORS[-1]
            daily[f"d{i}"] = {"name": dq["name"], "desc": dq["desc"], "objective": dq["objective"],
                              "reward_exp": int(dq["reward_exp"] * factor),
                              "reward_gold": int(dq["reward_gold"] * factor),
                              "repeat": rpt, "progress": 0}
        quests["daily"] = daily
        db.save_quests(group_id, qq_id, quests)
        lines = ["📜 今日任务已发布！", "━━━━━━━━━━━━"]
        _daily_n = 0  # v125.1 P2：序号仅计实际任务（跨 _date/_completed/_repeat 元数据键）
        for dkey, dq in daily.items():
            if dkey in _DAILY_META_KEYS:
                continue
            _daily_n += 1
            _dec = dq.get("repeat", 0)
            lines.append(f"{_daily_n:>2}. 『{dq['name']}』{dq['desc']}")
            if _dec:
                _pct = _daily_repeat_pct(_dec)
                lines.append(f"    ⚠️ 重复完成，奖励衰减 {_pct}%：经验 +{dq['reward_exp']} 金币 +{dq['reward_gold']}")
            else:
                lines.append(f"    奖励：经验 +{dq['reward_exp']} 金币 +{dq['reward_gold']}")
        if base_completed:
            lines.append(f"📌 今日已完成 {base_completed}/{DAILY_LIMIT} 个每日任务")
        yield event.plain_result("\n".join(lines))

    def _daily_pool(self, player, dq):
        """v94 每日任务按等级过滤：低等级不抽打不到的任务（修复 #45）。
        通用任意怪任务全等级可做；精英 Lv.6+、Boss Lv.10+；
        区域任务按奖励分档（reward_exp 与区域怪物等级强相关）。
        """
        lv = int(player.get("level") or 1)
        obj = dq.get("objective", {})
        exp = int(dq.get("reward_exp") or 0)
        if "kill_any" in obj:
            return True
        if "kill_elite" in obj:
            return lv >= 6
        if "kill_boss" in obj:
            return lv >= 10
        if lv < 3:
            return False
        cap = 400
        for min_lv, c in ((3, 400), (6, 800), (10, 1200), (15, 1600), (20, 2000), (25, 2600), (30, 1000000000)):
            if lv >= min_lv:
                cap = c
        return exp <= cap

    def _bump_daily_progress(self, group_id, qq_id, obj_key, lines=None):
        """v104 M20 修复：非击杀类每日任务进度推进（行会委托=完成支线 / 采集任务=采集材料）。

        与 combat.py 击杀分支（kill_any/kill_elite/kill_boss）互补：
        匹配 objective[obj_key] 的每日任务 +1，达标即发奖并从今日列表移除。
        调用点：_complete_side_quest（complete_side）、interact_prop 材料元素（collect_any）。
        """
        quests = db.get_quests(group_id, qq_id)
        daily = dict(quests.get("daily", {}) or {})
        if not daily:
            return
        changed = False
        for dkey, dq in list(daily.items()):
            if dkey in _DAILY_META_KEYS:  # 跨天/计数元数据，不是任务
                continue
            dobj = dq.get("objective") or {}
            need = dobj.get(obj_key)
            if not need:
                continue
            dq["progress"] = int(dq.get("progress", 0)) + 1
            changed = True
            if dq["progress"] >= need:
                # v125.1 P2：发奖结算统一走 _settle_daily_quest（与 combat._update_quests 同单点）
                _settle_daily_quest(self, group_id, qq_id, daily, dq, lines)
                del daily[dkey]
        if changed:
            # 保留 _date/_completed/_repeat（active 任务清空后仍须持续生效防刷/衰减计数）
            quests["daily"] = daily
            db.save_quests(group_id, qq_id, quests)

    def _home_view(self, group_id, qq_id, cur_map_id):
        """v68 家地图展示：home_{owner} → 家的定制面板"""
        owner_qid = cur_map_id[len("home_"):]
        owner = db.get_player(group_id, owner_qid)
        if not owner:
            return "这个家的主人已经离开了……(『出门』离开)"
        is_mine = str(owner_qid) == str(qq_id)
        deed = owner.get("deed", "") or ""
        prop = C.PROPERTIES.get(deed, {})
        lines = [f"🏠 【{('我的' if is_mine else owner['name'] + '的') + '家'}】"]
        if prop:
            dlv = int(owner.get("deed_lv", 1) or 1)
            hl = C.HOUSE_LEVELS.get(dlv, C.HOUSE_LEVELS[1])
            lines.append(f"{prop['name']}({hl['name']} Lv.{dlv})")
            lines.append(f"　{prop['desc']}")
        lines.append("━━━━━━━━━━━━")
        # 此地玩家
        here = [p for p in db.get_group_players(group_id).values() if p.get("cur_map") == cur_map_id]
        if here:
            lines.append("👤 屋里的人：")
            for p in here:
                lines.append(f"  {p['name']} Lv.{p['level']}")
        # 铺面摊位
        stalls = db.market_list(group_id, cur_map_id)
        if stalls:
            lines.append("🏪 铺面摊位上摆着：")
            for s in stalls:
                sname = "你" if str(s["seller"]) == str(qq_id) else (owner["name"] if str(s["seller"]) == str(owner_qid) else s["seller"])
                lines.append(f"  #{s['id']} {s['item_data'].get('name', '?')} ｜ {self._stall_label(s)} ｜ {sname}")
            lines.append(self._tip("home_stall"))
        else:
            # v104R3 P2：木屋(0 挂机位)不提示摆摊开张——与铺面挂机位实现对齐(25 章房产案)
            _odlv = int(owner.get("deed_lv", 1) or 1)
            _oslots = C.HOUSE_LEVELS.get(_odlv, C.HOUSE_LEVELS[1]).get("stall_slots", 0)
            if _oslots > 0:
                lines.append("🏪 铺面空着——房主可以『摆摊 <物品> [价格]』开张(不带价格 = 换摊)！")
            else:
                lines.append("🏪 铺面空着——房主升级房屋(『地契 升级』)可解锁铺面挂机位。")
        # 仓库（自己的家）
        if is_mine:
            storage = self._home_storage_load(group_id, qq_id)
            dlv = int(owner.get("deed_lv", 1) or 1)
            hl = C.HOUSE_LEVELS.get(dlv, C.HOUSE_LEVELS[1])
            lines.append(f"📦 家中仓库：{len(storage)}/{hl['storage']} 件(『仓库』管理)")
            if hl.get("stall_slots"):
                lines.append(f"🏪 铺面挂机位：{hl['stall_slots']} 个(『摆摊 <物品> [价格]』开张)")
        lines.append("━━━━━━━━━━━━")
        lines.append(self._tip("home"))
        return "\n".join(lines)

    def _current_npcs(self, player):
        """v86 子区域：当前所在位置可交互的 NPC 列表(子区域优先，回退地图级)。
        v95.30 随机性：酱油 NPC 按 游走/概率/时段 过滤（功能 NPC 恒在）。"""
        cur_map = player["cur_map"]
        m = C.MAP_BY_ID.get(cur_map, {})
        sa_id = player.get("cur_subarea") or ""
        for sa in (m.get("subareas") or []):
            if sa["id"] == sa_id:
                npc_ids = sa.get("npcs") or []
                return [C.NPCS[nid] for nid in npc_ids if nid in C.NPCS
                        and C.town_npc_visible(nid, C.NPCS[nid], sa_id)]
        return [C.NPCS[nid] for nid in m.get("npcs", []) if nid in C.NPCS]

    def _present_wild_hints(self, group_id, qq_id, cur_map) -> list:
        """v127.5 限时NPC：当前地图（map 级，全图都算）在场限时野外NPC 显示行。

        偶遇后挂 timed events，倒计时内地图/位置可见并带 ⏳ 剩余分钟；过期
        list_timed 惰性清除 → 天然消失（显示与对话同时，铁律）。
        返回例：["  🧭游商·老马 ⏳剩60分", ...]（2 空格缩进，与普通 NPC 行一致）。
        """
        lines = []
        evs = C.list_timed(group_id, qq_id, type_key="wild_npc",
                           data_match={"map": cur_map})
        for ev in evs:
            nid = ev.get("data", {}).get("npc_id") or ""
            wnpc = C.ALL_WILD.get(nid)
            if not wnpc:
                continue
            remain_min = max(1, -(-int(ev.get("remain", 0)) // 60))  # ceil(remain/60)
            lines.append(f"  {wnpc.get('icon', '')}{wnpc.get('name', nid)} ⏳剩{remain_min}分")
        return lines

    def _start_talk_list(self, group_id, qq_id) -> list:
        """当前地图 NPC 列表（带序号展示；交谈用『对话 <名字>』/『对话 <序号>』，v123a 起裸数字不再直接找 NPC）。『对话』空参共用。"""
        player = self._player(group_id, qq_id)
        if player and player["cur_map"].startswith("home_"):
            return ["家里没有 NPC 可以交谈～『出门』去镇上找人吧！"]
        npcs = self._current_npcs(player) if player else []
        # v127.5 限时NPC：在场野外旅人并入裸『对话』列表（排城镇 NPC 之后，带序号可对话）
        wild_evs = C.list_timed(group_id, qq_id, type_key="wild_npc",
                                data_match={"map": player["cur_map"]}) if player else []
        if not npcs and not wild_evs:
            return ["这里没有 NPC。输入『地图』看看哪里有 NPC～"]
        lines = ["👥 这里的 NPC："]
        for i, n in enumerate(npcs, 1):
            lines.append(f"{i:>2}. {n['icon']}{n['name']}({n['title']})")
        # 在场野外旅人：续在城镇 NPC 之后编号（带 ⏳ 剩余分钟）
        for j, ev in enumerate(wild_evs, len(npcs) + 1):
            nid = ev.get("data", {}).get("npc_id") or ""
            wnpc = C.ALL_WILD.get(nid)
            if not wnpc:
                continue
            remain_min = max(1, -(-int(ev.get("remain", 0)) // 60))  # ceil(remain/60)
            lines.append(f"{j:>2}. {wnpc.get('icon', '')}{wnpc.get('name', nid)} ⏳剩{remain_min}分")
        lines.append(self._tip("npc_list"))
        return lines

    def _find_npc_in_map(self, player, name_key):
        """在当前地图找 NPC(子区域优先，回退地图级)，返回 (npc_id, npc_dict) 或 (None, None)。

        v95.30 随机性：酱油 NPC 名字匹配但今天不可见（游走别处/概率未出/时段不符）
        → 仍返回 (nid, npc)（由调用方给"不在"提示），并置 player['_npc_absent'] 供提示。
        """
        cur_map = player["cur_map"]
        m = C.MAP_BY_ID.get(cur_map, {})
        sa_id = player.get("cur_subarea") or ""
        player.pop("_npc_absent", None)
        # 子区域 NPC 优先
        for sa in (m.get("subareas") or []):
            if sa["id"] == sa_id:
                for nid in sa.get("npcs", []):
                    npc = C.NPCS.get(nid)
                    if npc and (name_key in npc["name"] or name_key in nid):
                        if not C.town_npc_visible(nid, npc, sa_id):
                            player["_npc_absent"] = (nid, npc, sa_id)
                        return nid, npc
                break
        # 地图级 NPC（含其他子区域）
        for nid in m.get("npcs", []):
            npc = C.NPCS.get(nid)
            if npc and (name_key in npc["name"] or name_key in nid):
                if not C.town_npc_visible(nid, npc, sa_id):
                    player["_npc_absent"] = (nid, npc, sa_id)
                return nid, npc
        return None, None

    def _town_npc_absent_hint(self, nid, npc, sa_id):
        """v95.30：酱油 NPC 名字命中但当前不可见 → 解释原因（游走去向 / 时段 / 概率未出）。
        显示必须可触发铁律：『找』必须给出明确信息。"""
        name = npc.get("name", "他")
        # B 游走：今天在别的子区域 → 指路
        today_sa = C.town_npc_day_sa(nid, npc, sa_id)
        if today_sa != sa_id:
            m = self._player_map_name(sa_id) or ""
            sa_name = self._subarea_name(today_sa)
            if sa_name:
                return f"🧭 『{name}』今天不在这儿，在「{sa_name}」那边。过去找找看吧～"
        # D 时段
        per = npc.get("period")
        if per:
            period_cn = (C.PERIOD_CN.get(C.current_period(), "") or "").strip()
            return f"🌙 『{name}』现在({period_cn})不在这里，换个时间再来吧～"
        # C 概率未出
        return f"🍃 『{name}』今天没来这边，改天再来看看吧～"

    def _player_map_name(self, sa_id):
        """按子区域 id 找所属地图名（用于游走提示）"""
        for mid, m in C.MAP_BY_ID.items():
            for sa in (m.get("subareas") or []):
                if sa["id"] == sa_id:
                    return m.get("name", "")
        return ""

    def _subarea_name(self, sa_id):
        """按子区域 id 找显示名"""
        for mid, m in C.MAP_BY_ID.items():
            for sa in (m.get("subareas") or []):
                if sa["id"] == sa_id:
                    return sa.get("name", "")
        return ""

    def _find_wild_npc(self, player, name_key, group_id, qq_id):
        """9.4：在当前地图找野外 NPC（含 roam 定位 + 出现条件判定）。
        名字匹配但今天不在/条件不满足 → 返回 (None, None)，由调用方提示。"""
        cur = player["cur_map"]
        for nid, wnpc in C.ALL_WILD.items():
            # v95.4：与 _find_npc_in_map 一致的子串匹配（『找 游商』→『游商·老马』）
            if name_key not in (wnpc.get("name") or ""):
                continue
            if C.npc_map_id(nid, wnpc) != cur:
                return None, None
            if not C.wild_npc_findable(nid, wnpc, player, group_id, qq_id):
                return None, None
            wnpc = dict(wnpc)
            wnpc.setdefault("title", "游历于野外的旅人")
            return nid, wnpc
        return None, None

    def _wild_unseen_hint(self, player, name_key, group_id, qq_id):
        """v95.15 #71：野外 NPC 名字命中、在本图但当前条件(时段/季节/天气/解锁)不满足
        → 提示出现条件，区分『NPC 在但需定位』vs『当前时段 NPC 未出现』；无命中返回 None"""
        cur = player["cur_map"]
        for nid, wnpc in C.ALL_WILD.items():
            if name_key not in (wnpc.get("name") or "") and name_key not in nid:
                continue
            if C.npc_map_id(nid, wnpc) != cur:
                continue  # 今天不在这张图 → 交给方向提示
            if C.wild_npc_findable(nid, wnpc, player, group_id, qq_id):
                continue  # 条件满足（概率/保底问题），不归这里管
            label = self._wild_cond_label(wnpc)
            period = (C.PERIOD_CN.get(C.current_period(), "") or "").strip()
            return f"🧭 『{name_key}』{label}，现在({period})还没到出现的时候，换个时间再来找找吧～"
        return None

    def _npc_direction_hint(self, player, name_key):
        """v95.8 #51：当前地图没找到 NPC 时，全局搜位置给方向提示；找不到返回 None
        v59.#51：同名 NPC 分散多城镇时，玩家所在地图有命中 → 只列当前地图位置（单一方向），
        不再三城镇并列无方位（实测『找 城主』曾并列白鹿城/铁港城/珍珠城）"""
        cur = player["cur_map"]
        hits = []
        for nid, npc in C.NPCS.items():
            if name_key in (npc.get("name") or "") or name_key in nid:
                hits.append((nid, npc))
        for nid, wnpc in C.ALL_WILD.items():
            if name_key in (wnpc.get("name") or "") or name_key in nid:
                hits.append((nid, wnpc))
        # v101.29：野外精英/Boss 名也纳入搜索（任务目标常是强敌而非 NPC，
        # 如『找 铁牙』→ 丘陵狼王·铁牙在丘陵顶——旧代码只搜 NPC 表会命中同名
        # "地下守卫·铁牙/卫兵·铁牙" 给出错误方向）。精英/Boss 元组格式
        # (id, 显示名, role, lv, skills, drops)，伪 nid 用 "map:subarea" 便于定位。
        for mid, m in C.MAP_BY_ID.items():
            for sa in (m.get("subareas") or []):
                for ent in (sa.get("elite"), sa.get("boss")):
                    if not ent:
                        continue
                    ename = ent[1] if len(ent) > 1 else ""
                    if ename and (name_key in ename or ename in name_key):
                        hits.append((f"{mid}:{sa['id']}", {"name": ename, "map": mid}))
        if not hits:
            return None
        locs = []  # (map_id, subarea_id 或 None, 显示位置)
        for nid, npc in hits:
            m_id = npc.get("map") or ""
            m = C.MAP_BY_ID.get(m_id, {})
            m_name = m.get("name", m_id or "未知之地")
            sa_name = ""
            sa_id = None
            if ":" in nid:
                # v101.29 精英/Boss 条目：nid 格式 "map_id:subarea_id"
                _said = nid.split(":", 1)[1]
                sa_id = _said
                for sa in (m.get("subareas") or []):
                    if sa["id"] == _said:
                        sa_name = sa.get("name", "")
                        break
            else:
                for sa in (m.get("subareas") or []):
                    if nid in (sa.get("npcs") or []):
                        sa_name = sa.get("name", "")
                        sa_id = sa["id"]
                        break
            locs.append((m_id, sa_id, f"{m_name}·{sa_name}" if sa_name else m_name))
        cur_sa = player.get("cur_subarea") or ""
        in_here = cur in {m_id for m_id, _, _ in locs}
        # v95.25 #135：前缀明确"在/不在你所在的地图"，不再用误导性的"你所在的地图的…"
        # v113.5 O90：同图但目标在别的子区域时，原文案说"就在你所在的「目标子区域」一带"
        # 把目标位置说成玩家所在（误导定位）——同图不同子区域统一走"（你现在不在这里）"样式
        # （对齐地精商人版文案）；子区域未知的 NPC 按旧行为视为同处
        if in_here:
            same_sa = [l for m_id, sa_id, l in locs
                       if m_id == cur and (not sa_id or not cur_sa or sa_id == cur_sa)]
            if same_sa:
                here_uniq = list(dict.fromkeys(same_sa))
                return f"🧭 『{name_key}』就在你所在的「{'、'.join(here_uniq)}」一带。输入『地图』查看路线，到了地方用『对话』定位～"
        uniq = list(dict.fromkeys(l for _, _, l in locs))
        return f"🧭 『{name_key}』在「{'、'.join(uniq)}」一带（你现在不在这里）。输入『地图』查看路线，到了地方用『对话』定位～"

    def _npc_dialogue(self, group_id, qq_id, npc_id, npc):
        """按主线进度返回 NPC 对话(主线完成后不再重复初始台词)。
        v95.30 A 随机台词：酱油 NPC 配置了 lines 多条 → 每天换一条（日期哈希全服一致）。"""
        base = npc.get("dialogue", "……")
        # v95.30 酱油 NPC 随机台词（无功能 → 不参与主线逻辑）
        if not npc.get("funcs"):
            return C.town_npc_dialogue(npc_id, npc, base)
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
        player = self._player(group_id, qq_id)
        quests = db.get_quests(group_id, qq_id)
        main_id = quests.get("main_quest")
        if not main_id:
            lines.append("🎊 主线任务已全部完成，你已是奥兰迪亚的传说！")
            return lines
        mq = next((q for q in C.MAIN_QUESTS if q["id"] == main_id), None)
        # 存档容错：main_quest 指向已不存在的任务（旧存档/主线数据变更）→ 重置回主线起点
        if not mq and main_id:
            quests["main_quest"] = "q1_1"
            quests["main_status"] = "pending"
            quests["main_progress"] = {}
            main_id = "q1_1"
            mq = next((q for q in C.MAIN_QUESTS if q["id"] == main_id), None)
        if not mq or mq["giver"] != npc_id:
            # 不是这个 NPC 的任务
            need_npc = C.NPCS.get(mq["giver"], {}).get("name", "？") if mq else "？"
            lines.append(f"【{npc['name']}】我现在没有任务交给你。镇长/各地首领或许有安排……")
            if mq:
                lines.append(f"📜 当前主线『{mq['name']}』由 {need_npc} 发布。")
            return lines
        st = quests.get("main_status", "pending")
        # v105 P0：collect 型主线（q5_5 圣光百合）——背包材料足够即置 ready
        # （对齐支线逻辑 talk_actions.py:111-113 实时数背包；交付时再扣材料）
        # 放在状态分发前：pending 接取时材料已齐 → 直接可交付；active 回来找 NPC → 置 ready
        obj0 = mq["objective"]
        if obj0.get("collect") and st != "ready" and db.count_item(group_id, qq_id, obj0["collect"]) >= obj0.get("count", 1):
            quests["main_status"] = "ready"
            quests["main_progress"] = {obj0["collect"]: obj0.get("count", 1)}
            db.save_quests(group_id, qq_id, quests)
            st = "ready"
        if st == "pending":
            quests["main_status"] = "active"
            quests["main_progress"] = {}
            # talk 型任务：与发布 NPC 交谈即达成目标（对话即完成）
            obj = mq["objective"]
            if obj.get("talk") and obj["talk"] == npc_id:
                quests["main_status"] = "ready"
                quests["main_progress"] = {obj["talk"]: 1}
            # v105 P2：explore 型主线接取时已在目标地图 → 直接置 ready（免出图重进）
            if obj.get("explore") and player.get("cur_map") == obj["explore"]:
                quests["main_status"] = "ready"
                quests["main_progress"] = {obj["explore"]: 1}
            db.save_quests(group_id, qq_id, quests)
            lines.append(f"📜 【接取任务】『{mq['name']}』")
            if mq.get("story"):
                lines.append(f"  📖 {mq['story']}")
            lines.append(f"  🎯 目标：{self._obj_text(mq['objective'])}")
            lines.append(f"  奖励：经验 +{mq['reward_exp']} 金币 +{mq['reward_gold']}")
            # v95.25 #138：主线等级建议（软提示，不拦截接取）——suggest_lv 在 quests.py 数据里
            if mq.get("suggest_lv") and player["level"] < mq["suggest_lv"]:
                lines.append(f"  ⚠️ 建议等级 Lv.{mq['suggest_lv']}，你才 Lv.{player['level']}——可以先练练级再挑战！")
            if quests["main_status"] == "ready":
                lines.append("  ✨ 交谈完成！再与这位 NPC 对话即可交付任务。")
        elif st == "ready":
            # 交任务领奖
            obj = mq.get("objective") or {}
            # v105 P0：collect 型主线交付时扣材料（先复核背包，材料被消耗则回到进行中）
            if obj.get("collect"):
                need = obj.get("count", 1)
                if db.count_item(group_id, qq_id, obj["collect"]) < need:
                    quests["main_status"] = "active"
                    quests["main_progress"] = {}
                    db.save_quests(group_id, qq_id, quests)
                    lines.append(f"📜 交付『{mq['name']}』需要 {obj['collect']} ×{need}，你背包里不够了，先去凑齐吧～")
                    return lines
                db.remove_item(group_id, qq_id, obj["collect"], need)
                # v126.2：鱼获个体属性在 item_data.tags，remove_item 自动截断，无需额外同步
                lines.append(f"🎒 交出 {obj['collect']} ×{need}")
            # v124.3：奖励统一走 _grant_quest_rewards（exp/gold/升级 + reward_item 全格式
            # + reward_pet/reward_mount/unlock_class）——此前主线交付只支持 reward_item
            # 单值 + reward_pet，eq:/list 随机/坐骑/隐藏职业配了不发
            self._grant_quest_rewards(group_id, qq_id, mq, lines)
            completed = list(quests.get("completed_main", []))
            completed.append(main_id)
            quests["completed_main"] = completed
            quests["main_quest"] = mq["next"]
            quests["main_status"] = "pending"
            quests["main_progress"] = {}
            db.save_quests(group_id, qq_id, quests)
            lines.append(f"✅ 【任务完成】『{mq['name']}』！")
            if mq.get("ending"):
                # v105 M19 P1：主线抉择结局变体——q10_5 等任务按对话树选择的 flag 输出不同结尾
                _ending = mq["ending"]
                _endings = mq.get("endings") or {}
                if _endings:
                    try:
                        _flags = db.get_talk_flags(group_id, qq_id, mq["giver"]) or []
                    except Exception:
                        _flags = []
                    for _fk, _fv in _endings.items():
                        if _fk in _flags:
                            _ending = _fv
                            break
                lines.append(f"  📖 {_ending}")
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
                lines.append("🎊 恭喜！你完成了全部主线任务，成为奥兰迪亚的传说！")
        else:
            lines.append(f"📜 你已接取『{mq['name']}』：{mq['desc']}")
        return lines

    def _obj_text(self, obj):
        if obj.get("kill"):
            return f"击败 {obj['kill']} ×{obj['count']}"
        if obj.get("collect"):
            # v125.1 P2：s64 等 collect_count 无 count 的复合目标不再 KeyError
            return f"收集 {obj['collect']} ×{obj.get('collect_count') or obj.get('count', 1)}"
        if obj.get("explore"):
            return f"前往 {C.MAP_BY_ID.get(obj['explore'], {}).get('name', '？')}"
        if obj.get("find"):
            # v97.1 告示委托：在指定地图探索概率找到目标
            return f"在 {C.MAP_BY_ID.get(obj.get('map', ''), {}).get('name', '？')} 寻找 {obj['find']}(探索有概率遇到)"
        if obj.get("use"):
            # v124 use 目标：使用指定物品达成
            return f"使用 {obj['use']}"
        if obj.get("talk"):
            npc = C.NPCS.get(obj["talk"], {})
            return f"与 {npc.get('name', '？')} 交谈"
        return "？"

    def _obj_text_lines(self, obj, st=None):
        """v124.2 复合 objective 逐行渲染（如 s18 kill 腐牙萨满·嚎骨 + find 白桦 两行都显示）。
        find 行按任务状态标 已找到/未找到（find 无进度存档，以 ready 态为准）；
        纯 find 委托（有 map）保留『探索有概率遇到』机制提示，与原 _obj_text 文案一致。"""
        lines = []
        if obj.get("kill"):
            lines.append(f"击败 {obj['kill']} ×{obj['count']}")
        if obj.get("collect"):
            # v125.1 P2：s64 等 collect_count 无 count 的复合目标不再 KeyError
            lines.append(f"收集 {obj['collect']} ×{obj.get('collect_count') or obj.get('count', 1)}")
        if obj.get("explore"):
            lines.append(f"前往 {C.MAP_BY_ID.get(obj['explore'], {}).get('name', '？')}")
        if obj.get("find"):
            _mname = C.MAP_BY_ID.get(obj.get("map", ""), {}).get("name", "")
            if st == "ready":
                lines.append(f"{'在 ' + _mname + ' ' if _mname else ''}寻找 {obj['find']}（已找到）")
            elif _mname:
                lines.append(f"在 {_mname} 寻找 {obj['find']}(探索有概率遇到)")
            else:
                lines.append(f"寻找 {obj['find']}（未找到）")
        if obj.get("use"):
            lines.append(f"使用 {obj['use']}")
        if obj.get("talk"):
            npc = C.NPCS.get(obj["talk"], {})
            lines.append(f"与 {npc.get('name', '？')} 交谈")
        return lines or ["？"]

    def _quest_reputation(self, group_id, qq_id, npc_id):
        """完成任务时给对应势力加声望，返回提示行(如有)"""
        npc = C.NPCS.get(npc_id)
        if not npc:
            return ""
        m = C.MAP_BY_ID.get(npc["map"], {})
        area_key = m.get("area", npc["map"])
        faction = C.AREA_FACTION.get(area_key)
        if not faction:
            return ""
        db.add_reputation(group_id, qq_id, faction, 10)
        return f"🏛️ {C.FACTIONS[faction]['icon']} 声望＋10"

    def _wild_cond_label(self, npc: dict) -> str:
        """野外 NPC 出现条件 → 中文标签(见闻录/时间面板用)"""
        cond = npc.get("condition", {})
        labels = []
        t = cond.get("time")
        if t:
            tm = {"morning": "清晨", "day": "白天", "evening": "黄昏", "night": "夜晚"}
            labels.append("/".join(tm.get(x, x) for x in t) + "出现")
        s_ = cond.get("season")
        if s_:
            sm = {"spring": "春季", "summer": "夏季", "autumn": "秋季", "winter": "冬季"}
            labels.append("/".join(sm.get(x, x) for x in s_) + "限定")
        w = cond.get("weather")
        if w:
            wm = {"rain": "雨天", "storm": "暴风雨", "snow": "雪天", "fog": "雾天", "sunny": "晴夜"}
            labels.append(wm.get(w, w) + "出现")
        if cond.get("min_level"):
            labels.append(f"Lv.{cond['min_level']}+")
        if npc.get("cycle"):
            labels.append(f"每{npc['cycle']}天")
        if npc.get("chance"):
            labels.append(f"概率 {int(npc['chance']*100)}%")
        if npc.get("unlock"):
            labels.append("🔓 需解锁")
        return "，".join(labels) if labels else "随时可能出现"

    @filter.regex(r"^(?:\[At:\d+\]\s*)?时间(?:指令)?(?:\s*|$)")
    @require_player()

    async def time_cmd(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        cur = player["cur_map"]
        summary = C.time_weather_summary(cur)
        cur_map = C.MAP_BY_ID.get(cur, {})
        lines = [
            "🕰️ 【时间】",
            f"⏰ {summary}",
            f"📍 你在【{cur_map.get('name', '未知区域')}】",
            "━━━━━━━━━━━━",
        ]
        hints = C.nearby_hints(group_id, qq_id, player, cur)
        if hints:
            lines.append("🍃 附近似乎有人影出没：")
            for nid, npc in hints[:5]:
                lines.append(f"  {npc['icon']}{npc['name']}({self._wild_cond_label(npc)})")
            lines.append(self._tip("explore"))
        else:
            lines.append("🍃 附近没有特别的气息……")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?见闻录(?:\s*|$)")
    @require_player()

    async def wild_notes(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        met = C.met_wild(group_id, qq_id)
        if not met:
            yield event.plain_result(
                "📖 【见闻录】还是空白的……\n"
                "去野外走走，那些藏在角落里的旅人、隐士、夜行者，都在等着被遇见。"
            )
            return
        lines = [f"📖 【见闻录】你见过的人({len(met)}/{len(C.ALL_WILD)})：", "━━━━━━━━━━━━"]
        for nid in met:
            npc = C.ALL_WILD.get(nid)
            if not npc:
                continue
            lines.append(f"{npc['icon']}{npc['name']}")
            lines.append(f"　　{npc['desc']}")
            lines.append(f"　　🕐 {self._wild_cond_label(npc)}")
        lines.append("💡 集齐见闻是冒险者的浪漫——见过的人会记住你。")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?[0-9０-９]\d?$", priority=100)
    async def npc_quick_dialog(self, event: AstrMessageEvent):
        """裸数字消费链：对话树选项 > 物品查看 > 移动模式 > 放行快捷指令。

        v101.16：『对话』改版配套——地图/NPC 列表带序号，回复序号直接交谈。
        v123a（鱼鱼拍板）：移除「序号直接找 NPC」——裸数字不再触发找 NPC 对话，
        NPC 列表序号仅作展示，交谈须『对话 <名字>』/『对话 <序号>』；
        对话树中的选项回复（_talk_active）保留。
        v128.2（鱼鱼拍板）：『位置 0』/发 0 进入赶路模式的旧捷径已移除，
        赶路入口统一为『赶路』指令（hurry_view 进入）；0 仅在赶路模式中用于结束。
        priority=100 高于 shortcut_trigger(默认0)：命中即 stop_event 拦截快捷指令；
        无状态可消费时 return（不 yield）→ 放行给快捷指令。
        v127.4：去掉 @require_player()——裸数字是对话树/移动/快捷等"已注册玩家专属"的
        交互链，未注册用户发『1』『2』不应被"你还没有角色"打扰（鱼鱼反馈），
        改为函数内对未注册静默 return（不 yield、不提示），放行顺延。
        """
        group_id, qq_id = self._uid(event)
        # v127.4：未注册玩家无对话树/物品查看/移动模式/快捷绑定可消费 → 静默放行，免"未注册"打扰
        if not self._player(group_id, qq_id):
            return
        num = event.get_message_str().strip()
        num = re.sub(r"^\[At:[^\]]*\]\s*", "", num).strip()
        # v124.2 全角数字兼容：全角『１』等回复转半角再比较（分支交付/对话树选项/物品查看/移动共用）
        num = num.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
        # v124 分支交付：支线 ready + branch_wait 时，裸数字 = 分支选项（优先于对话树）
        _bw = self._branch_wait_sid(group_id, qq_id)
        if _bw and (num.isdigit() or num):
            lines = self._complete_side_quest(group_id, qq_id, _bw, branch_choice=num)
            yield event.plain_result("\n".join(lines))
            self._stop_event_safe(event)
            return
        # O99 修复：与 talk_choice/move 同源判定（_talk_active 清除损坏残留键）
        st = self._talk_active(group_id, qq_id)
        if st:
            # 对话树选项选择（复用 talk_choice 有状态分支：『对话 1』同款）
            async for r in self.talk_choice(event):
                yield r
            self._stop_event_safe(event)
            return
        # v101.21 物品查看模式：开启时裸数字优先查物品（改消息转发 item_detail）
        if db.get_event_state(f"item_view_mode:{qq_id}"):
            event.message_str = f"物品详情 {num}"
            async for r in self.item_detail(event):
                yield r
            self._stop_event_safe(event)
            return
        # v128 赶路模式：开启时裸数字赶路（改消息转发 move），0=关闭
        if db.get_event_state(f"move_mode:{qq_id}"):
            if num == "0":
                db.set_event_state(f"move_mode:{qq_id}", "")
                db.set_event_state(f"hurry_type:{qq_id}", "")  # v128.1 结束赶路同时清过滤
                yield event.plain_result("🚶 赶路模式已结束，回复数字不再自动赶路～")
                self._stop_event_safe(event)
                return
            event.message_str = f"前往 {num}"
            async for r in self.move(event):
                yield r
            self._stop_event_safe(event)
            return
        # v128.2：『位置 0』/发 0 进入赶路模式的旧捷径已移除——无状态可消费时
        # 回复 0 一律放行（不再开启赶路模式）；进入赶路唯一入口=『赶路』指令
        # （hurry_view）；0 仅在赶路模式中用于结束（见上）。
        # v123a：序号直接找 NPC 已移除——无对话/物品/移动状态时一律放行
        # （快捷指令由 shortcut_trigger 消费；未绑定则无响应）
        return

    # v127.8：『找』指令已删除（鱼鱼拍板）——find_npc 改为内部方法，
    # 仅被 talk_choice 『对话 <名字>』 内部调用；外部不再有『找 X』触发词。
    # 原 @filter.regex("找") + @require_player() 装饰器移除（talk_choice 前置已校验玩家）。
    async def find_npc(self, event: AstrMessageEvent):
        """『对话 <NPC名/序号>』内部查找链：被 talk_choice 无对话分支调用；不对外注册（v127.8）"""
        group_id, qq_id = self._uid(event)
        name_key = self._strip_cmd(event, "找")
        player = self._player(group_id, qq_id)
        if self._is_redname(qq_id):
            yield event.plain_result("☠️ 你是红名！城里的 NPC 都躲着你走……(等红名消退再来)")
            return
        name_key = name_key.strip()
        if not name_key:
            cur_m = player["cur_map"]
            if cur_m.startswith("home_"):
                yield event.plain_result("家里没有 NPC 可以交谈～『出门』去镇上找人吧！")
                return
            # v127.5 限时NPC：与『对话』空参同源——在场野外旅人也并入列表
            yield event.plain_result("\n".join(self._start_talk_list(group_id, qq_id)))
            return
        # 序号找：『找 1』→ 当前地图第 1 个 NPC（含 v127.5 在场野外旅人续号）
        if name_key.isdigit():
            if player["cur_map"].startswith("home_"):
                yield event.plain_result("家里没有 NPC 可以交谈～『出门』去镇上找人吧！")
                return
            npcs = self._current_npcs(player)
            wild_evs = C.list_timed(group_id, qq_id, type_key="wild_npc",
                                    data_match={"map": player["cur_map"]})
            total = len(npcs) + len(wild_evs)
            idx = int(name_key)
            if idx < 1 or idx > total:
                yield event.plain_result(f"这里没有第 {idx} 位 NPC(共 {total} 位)！『对话』查看列表～")
                return
            if idx <= len(npcs):
                npc = npcs[idx - 1]
                npc_id = next((nid for nid, n in C.NPCS.items() if n is npc), None)
            else:
                # v127.5 限时NPC：序号命中在场野外旅人（不在 C.NPCS，不能走反查）
                _ev = wild_evs[idx - len(npcs) - 1]
                npc_id = _ev.get("data", {}).get("npc_id") or ""
                _w = C.ALL_WILD.get(npc_id)
                if not _w:
                    yield event.plain_result("这位旅人似乎已经离开了……")
                    return
                npc = dict(_w)
                npc.setdefault("title", "游历于野外的旅人")  # 与 _find_wild_npc 一致
        else:
            npc_id, npc = self._find_npc_in_map(player, name_key)
            if npc and player.get("_npc_absent"):
                # v95.30 随机性：酱油 NPC 名字匹配但今天不在（游走/概率/时段）
                yield event.plain_result(self._town_npc_absent_hint(*player["_npc_absent"]))
                return
        if not npc:
            # v87.2 副本地图化：副本层内 NPC（HIDDEN_NPCS，按当前层 npcs 列表查）
            inst_row = self._instance_battle_for(group_id, qq_id)
            if inst_row and inst_row["state"].get("mode") == "map":
                stage_npcs = self._stage_npcs(group_id, qq_id)
                for nid in stage_npcs:
                    n = C.HIDDEN_NPCS.get(nid, {})
                    if n and (name_key in n.get("name", "") or name_key in nid):
                        npc_id, npc = nid, n
                        break
        if not npc:
            # 9.4：野外 NPC（当前地图 + 出现条件）
            npc_id, npc = self._find_wild_npc(player, name_key, group_id, qq_id)
            if npc:
                # v127.5 限时NPC：偶遇制——只在倒计时内在场可找；未偶遇/过期 → "今天没遇到"
                if not C.get_timed(group_id, qq_id, f"wild:{npc_id}"):
                    _ta = "她" if npc.get("gender") == "女" else "他"
                    yield event.plain_result(
                        f"🍃 『{name_key}』今天还没遇到……多『探索』几圈，{_ta}不定什么时候就路过这里啦～")
                    return
        if not npc:
            # v95.15 #71：名字命中但时段/条件不满足（NPC 在本图却找不到）→ 提示出现条件
            unseen = self._wild_unseen_hint(player, name_key, group_id, qq_id)
            if unseen:
                yield event.plain_result(unseen)
                return
            # v95.8 #51：不在当前子区域/地图时，全局搜位置给方向提示
            hint = self._npc_direction_hint(player, name_key)
            if hint:
                yield event.plain_result(hint)
                return
            yield event.plain_result(
                f"你在这里没找到『{name_key}』。他可能不在这里，或还没到出现的时候……(『时间』看看此刻谁在附近)")
            return
        dlg = C.get_dialogue(npc_id)
        if dlg:
            # v65：配置了多轮对话树 → 进入对话
            db.set_talk_state(group_id, qq_id, npc_id, dlg.get("start", ""))
            ctx = self._talk_ctx(group_id, qq_id, npc_id)
            node = C.dialogue_node(dlg, dlg.get("start", ""))
            lines = self._render_talk_node(npc, dlg, node, ctx)
        else:
            lines = [f"{npc['icon']}【{npc['name']}】{npc['title']}", f"“{self._npc_dialogue(group_id, qq_id, npc_id, npc)}”"]
        # 功能提示
        funcs = npc.get("funcs", [])
        if "quest" in funcs:
            # v95.11 #50：代词按 NPC 性别（玛莎等女性 NPC 用"她"）
            _ta = "她" if npc.get("gender") == "女" else "他"
            if dlg:
                # v95.9 对话式任务：有对话树的 NPC 通过对话选项接取/交付，这里只给引导
                _quests = db.get_quests(group_id, qq_id)
                _mid = _quests.get("main_quest")
                _mq = next((q for q in C.MAIN_QUESTS if q["id"] == _mid), None) if _mid else None
                if _mq and _mq["giver"] == npc_id:
                    _st = _quests.get("main_status", "pending")
                    if _st == "pending":
                        lines.append(f"📜 主线『{_mq['name']}』可接取——和{_ta}对话接下任务吧～")
                    elif _st == "ready":
                        lines.append(f"✅ 主线『{_mq['name']}』达成！和{_ta}对话交付领奖～")
                _side = _quests.get("side", {})
                # v127.6 预告全量：复用 _side_available_list（与对话菜单同源过滤）——
                # 把该 NPC 所有可接支线都列出来（此前 break 只显示第一条，与实际可接数对不上）
                for _av in self._side_available_list(group_id, qq_id, npc_id, npc):
                    lines.append(f"📜 支线『{_av['name']}』可接取——和{_ta}对话接下吧～")
                for _sid, _sq in list(_side.items()):
                    _sqd = next((q for q in C.SIDE_QUESTS if q["id"] == _sid), None)
                    if _sqd and _sqd["giver"] == npc_id and _sq.get("status") == "ready":
                        lines.append(f"✅ 支线『{_sqd['name']}』已完成！和{_ta}对话交付～")
                        break
                # v124 progress_text：该 NPC 名下有进行中的链式支线 → 输出推进台词（有对话树的 NPC 也显示）
                for _sid, _sq in list(_side.items()):
                    _sqd = next((q for q in C.SIDE_QUESTS if q["id"] == _sid), None)
                    if _sqd and _sqd["giver"] == npc_id and _sq.get("status") == "active":
                        _pt = _sqd.get("progress_text")
                        if _pt:
                            lines.append(f"  💬 {_pt}")
                            break
            else:
                # 无对话树的 NPC：保持自动接取/交付（对话选项不存在，指令与提示兜底）
                lines += self._take_main_quest(group_id, qq_id, npc_id, npc)
                lines += self._offer_side_quests(group_id, qq_id, npc_id, npc)
        if "shop" in funcs and self._at_shop(player, group_id, qq_id):
            lines.append("🏪 输入『商店』可以买东西")
        if "trade" in funcs:
            _ta = "她" if npc.get("gender") == "女" else "他"  # v95 #141：代词跟随 NPC 性别
            lines.append(f"🧭 输入『商店』看看{_ta}的货（行商有独家补给）")
        if "heal" in funcs and self._at_healer(player):
            lines.append("🏨 输入『住宿』恢复满血(需要金币)")
        if "daily" in funcs:
            lines.append("📜 输入『每日』领取今日悬赏")
        if "lore" in funcs:
            ta = "她" if npc.get("gender") == "女" else "他"
            # v101.25 #311：lore 空挂修复——提示"讲传说"却没有传说内容（world.py 注释
            # 曾承认翠羽/说书人·巴尔空挂）。现在直接输出 NPC dialogue 作为传说正文，
            # 不再只给一句空引导。
            _lore_txt = npc.get("lore") or npc.get("dialogue", "")
            if _lore_txt:
                lines.append(f"🎻 {ta}给你讲了一个传说：\n“{_lore_txt}”")
            else:
                lines.append(f"🎻 {ta}捋了捋胡子，说起一段大陆往事……(传说散落在各地，多去听听老人们的见闻吧)")
            lines.append(self._tip("encyclopedia"))
        if "teach" in funcs:
            # v104 P2（M21）teach 空挂修复：有对话树的教习 NPC 走对话树选项；
            # 无对话树的教习 NPC（龙语者·古尔/上古守卫者/墓王·静语）→ 按职业直接传授对应技能
            if dlg:
                lines.append("🗡️ 直接回复序号继续交谈，这位前辈或许能指点你一二")
            else:
                lines.extend(self._teach_by_npc(group_id, qq_id, player, npc_id))
        if "ency" in funcs:
            lines.append("📚 输入『百科 <材料/怪物/地图名>』查询世界知识(镇长藏书)")
        # v104 P1（M21）：隐藏 NPC 解锁 flag 设置点——与特定野外 NPC 交谈即授予（幂等）
        _granted = self._grant_wild_unlock_flags(group_id, qq_id, npc_id)
        if _granted:
            lines.append(_granted)
        yield event.plain_result("\n".join(lines))

    def _grant_wild_unlock_flags(self, group_id, qq_id, npc_id):
        """v104 P1（M21 隐藏 NPC 永久锁死修复）：与特定野外 NPC 交谈 → 授予隐藏 NPC 解锁 flag。

        v124.3（审计）：解锁链数据化——配置读 NPC 数据的 unlock_flags 字段
        （{"flag": "heard_owl_song", "notice": "…"}，见 wild_npcs.py 说书人·巴尔/
        流浪诗人·弦歌/老兵之魂），新增解锁型 NPC = 纯数据操作（加字段即可），
        本函数零改动。flag 存任意 NPC 桶即可，unlock_met 已改全桶扫描。
        返回首次授予的提示行；无授予返回 None。
        """
        npc = (C.ALL_WILD or {}).get(npc_id)
        if not isinstance(npc, dict):
            return None
        cfg = npc.get("unlock_flags") or {}
        flag = cfg.get("flag", "")
        if not flag:
            return None
        if flag in db.get_talk_flags(group_id, qq_id, npc_id):
            return None
        db.set_talk_flag(group_id, qq_id, npc_id, flag)
        return cfg.get("notice", "")

    # ---------------- v104 P2（M21）teach 空挂修复 ----------------
    # v112 D6：教习技能表下沉 wild_npcs.py NPC 定义（teach_skills/teach_hint），
    # 逻辑层只读数据——新增教习 NPC/职业 = 纯数据操作

    def _teach_by_npc(self, group_id, qq_id, player, npc_id):
        """v104 P2（M21）teach 空挂修复：无对话树的教习型 NPC（龙语者·古尔/上古守卫者/墓王·静语）
        按职业传授对应技能。参照对话树 tutor_skill 写法：等级门槛 + 金币学费 → 直接学会（不耗技能点）。
        返回提示行列表；NPC 不在映射表时返回空列表（保持原行为）。
        v112：配置读 NPC 数据（teach_skills/teach_hint），无配置返回空列表。
        """
        npc = (C.ALL_WILD or {}).get(npc_id, {})
        if not isinstance(npc, dict):
            npc = {}
        cfg_skills = npc.get("teach_skills") or {}
        hint = npc.get("teach_hint") or ""
        if not cfg_skills:
            return []
        cid = C.resolve("classes", player.get("class_name", ""))
        sname = cfg_skills.get(cid)
        if not sname:
            return [f"{hint}他打量了你片刻，摇了摇头：你这身本事，不在我能指点的路数上。"]
        info = E.skill_info(player.get("class_name", ""), sname)
        if not info:
            return []
        sname_cn = info.get("name", sname)
        need_lv = int(info.get("lv", 1))
        cost = max(500, need_lv * 100)
        if player.get("level", 0) < need_lv:
            return [f"{hint}这套本事要 Lv.{need_lv} 才学得动，你才 Lv.{player.get('level', 1)}，先练练基本功。"]
        if (player.get("gold", 0) or 0) < cost:
            return [f"{hint}想学？拿 {cost} 金币来，一分诚意一分本事。(你现在有 {player.get('gold', 0)} 金币)"]
        learned = list(player.get("learned_skills", []))
        if C.resolve("skills", sname) in [C.resolve("skills", s) for s in learned if s]:
            return [f"{hint}『{sname_cn}』你早已掌握，不必再学。"]
        db.update_player(group_id, qq_id, gold=(player.get("gold", 0) or 0) - cost,
                         learned_skills=learned + [sname_cn])
        return [
            f"{hint}",
            f"💰 你献上 {cost} 金币作为谢礼",
            f"✨ 前辈悉心传授，你学会了技能『{sname_cn}』！",
            f"「{info['desc']}」",
            self._tip("skill_set"),
        ]

    # ---------------- v87.9 场景元素交互 ----------------

    @filter.regex(r"^(?:\[At:\d+\]\s*)?交互(?:\s*|$)")
    @require_player()
    @no_prof_waiting()

    async def interact_prop(self, event: AstrMessageEvent):
        """与当前子区域的场景元素(喷泉/雕像/告示板等)交互。纯氛围 + 极小彩蛋。"""
        group_id, qq_id = self._uid(event)
        name_key = self._strip_cmd(event, "交互").strip()
        player = self._player(group_id, qq_id)
        if self._is_redname(qq_id):
            yield event.plain_result("☠️ 你是红名！城里的元素都绕着你走……(等红名消退再来)")
            return
        cur = player["cur_map"]
        cur_map = C.MAP_BY_ID.get(cur, {})
        sa_id = player.get("cur_subarea") or ""
        prop_ids = C.subarea_props(cur, sa_id)
        # v104 M23 修复：过滤孤儿 prop（SUBAREA_PROPS 挂载了但 PROPS 未定义）。
        # 显示列表与『交互 <序号>』按下标取条目必须同源，否则序号错位/取到空定义
        # 会在 pp['icon']/pp['name'] 处 KeyError 崩溃。
        prop_ids = [e for e in prop_ids if C.prop_entry(e)[0] in C.PROPS]
        if not name_key:
            # 无参：列出当前子区域的场景元素
            if not prop_ids:
                yield event.plain_result("这里没什么可交互的，风倒是挺大。")
                return
            lines = ["✨ 这里的场景元素："]
            for i, entry in enumerate(prop_ids, 1):
                pid, label = C.prop_entry(entry)
                pp = C.PROPS.get(pid, {})
                if pp:
                    name = label or pp['name']
                    lines.append(f"{i}. {pp['icon']}{name}：{pp.get('desc', '')}")
            lines.append(self._tip("interact"))
            yield event.plain_result("\n".join(lines))
            return
        # 序号交互：『交互 1』→ 当前子区域第 1 个元素
        if name_key.isdigit():
            idx = int(name_key)
            if idx < 1 or idx > len(prop_ids):
                yield event.plain_result(f"这里没有第 {idx} 个场景元素(共 {len(prop_ids)} 个)！『交互』查看列表～")
                return
            entry = prop_ids[idx - 1]
            pid, label = C.prop_entry(entry)
            found = (pid, C.PROPS.get(pid, {}), label)
        else:
            # 找 prop：专属名/默认名子串 / id 匹配
            found = None
            for entry in prop_ids:
                pid, label = C.prop_entry(entry)
                pp = C.PROPS.get(pid, {})
                name = label or pp.get("name", "")
                if pp and (name_key in name or name_key in pid):
                    found = (pid, pp, label)
                    break
            if not found:
                # v95.14：海象运算符只在 if 条件绑定 pid，label 未定义 → NameError；改用显式循环 + 去重
                _cand = []
                for _entry in prop_ids:
                    _pid, _lbl = C.prop_entry(_entry)
                    if _pid in C.PROPS:
                        _nm = _lbl or C.PROPS[_pid]["name"]
                        if _nm not in _cand:
                            _cand.append(_nm)
                names = "、".join(_cand) or "没有"
                yield event.plain_result(f"这里没有『{name_key}』可以交互～(这里有：{names})")
                return
        pid, pp, label = found
        name = label or pp['name']
        texts = pp.get("texts") or []
        text = random.choice(texts) if texts else pp.get("desc", "……")
        lines = [f"{pp['icon']}【{name}】", f"“{text}”"]
        # v97.1 告示板：附加展示当前地图的告示委托（board 型支线，未接取时）
        # v104 M20 修复：真正按当前地图过滤（原实现遍历全部 board 委托，注释与实现不符）——
        # board 委托取顶层 map 字段（发布地）；没有则按 giver NPC 所在区域兜底。
        # 注意：find 型委托的 objective.map 是搜寻地而非发布地，不可用于此过滤。
        if pid == "notice_board":
            quests = db.get_quests(group_id, qq_id)
            side = quests.get("side") or {}
            here_board = []
            for sq in C.SIDE_QUESTS:
                if not sq.get("board"):
                    continue
                qmap = sq.get("map")
                if not qmap:
                    _g = C.NPCS.get(sq.get("giver")) or C.ALL_WILD.get(sq.get("giver")) or {}
                    qmap = _g.get("map")
                if qmap and qmap != cur:
                    continue
                here_board.append(sq)
            board_lines = []
            for sq in here_board:
                if sq["id"] in side:
                    continue
                board_lines.append(f"  📜 {sq['name']}：{sq['desc']}")
            if board_lines:
                lines.append("━━━━━━━━━━━━")
                lines.append("🧾 【告示委托】")
                lines += board_lines
                lines.append(self._tip("notice_board"))
            else:
                done = any(
                    side.get(sq["id"], {}).get("status") == "done"
                    for sq in here_board
                )
                if done:
                    lines.append("(你已处理完这里的委托，告示板又恢复了平静。)")
        # 极小彩蛋（纯趣味，不破坏平衡）
        # v87.12 专属元素带小效果：dict effect = {"type": "material"/"heal", "daily": True}
        import datetime as _dt
        eff = pp.get("effect")
        if eff == "wish":
            # v105 M23 P2-2：许愿井每日 1 次（策划案 23 章『许愿井（每日一次彩蛋）』）——
            # 原实现零成本无限刷（5%×1-5 金币无冷却无每日次数），现按 props_use 每日计数
            today = _dt.date.today().isoformat()
            use_key = f"{cur}:{sa_id}:{pid}"
            used = db.get_props_use(qq_id)
            if used.get(use_key) == today:
                lines.append("⏳ 井水今天已经应过一次愿了……明日再来试试吧。")
            elif random.random() < WISH_WELL_EGG_CHANCE:
                gold = random.randint(1, 5)
                # F1 P1-4：原子认领——并发双请求只有首个真正占下并发放（后手见"已应过一次愿"）
                if db.props_use_claim_atomic(qq_id, use_key, today):
                    db.update_player(group_id, qq_id, gold=player["gold"] + gold)
                    lines.append(f"💰 井底传来一声轻响——你低头一看，水面上漂着 {gold} 枚铜币，像是井的谢礼。")
                else:
                    lines.append("⏳ 井水今天已经应过一次愿了……明日再来试试吧。")
        elif eff == "refresh":
            lines.append("💧 泉水入喉，神清气爽。旅途的疲惫仿佛也被这淙淙水声冲淡了一些。")
        elif isinstance(eff, dict) and eff.get("daily"):
            # 每日 1 次（按元素实例：地图:子区域:prop_id 独立计数，防刷）
            today = _dt.date.today().isoformat()
            use_key = f"{cur}:{sa_id}:{pid}"
            used = db.get_props_use(qq_id)
            if used.get(use_key) == today:
                lines.append("⏳ 今天已经在这里翻找过了……明天再来碰碰运气吧。")
            else:
                etype = eff.get("type")
                if etype == "material":
                    pool = eff.get("pool") or []
                    if pool:
                        # F1 P1-4：原子认领——并发双请求只有首个发放（后手提示已翻找过）
                        if not db.props_use_claim_atomic(qq_id, use_key, today):
                            lines.append("⏳ 今天已经在这里翻找过了……明天再来碰碰运气吧。")
                        else:
                            mid = random.choice(pool)
                            mname = C.display("materials", mid)
                            db.add_item(group_id, qq_id, mid, {
                                "name": mname, "type": "材料", "stackable": True,
                                "price": C.MATERIALS[mid]["price"],
                            }, 1)
                            lines.append(f"🎒 {eff.get('found_text', '你发现')}【{mname}】×1！")
                            # v104 M20：采集任务每日（collect_any）——场景元素获得材料 +1（主采集动作在 economy.py）
                            self._bump_daily_progress(group_id, qq_id, "collect_any", lines)
                elif etype == "heal":
                    pct = float(eff.get("pct", 0.1))
                    missing = player.get("max_hp", 1) - player.get("hp", 0)
                    # v104 M23 修复：满血时旧逻辑 max(1, int(0*pct))=1 会误走恢复分支、
                    # 白吞每日次数；改为满血只出氛围文案，不 mark_props_use
                    heal = max(1, int(missing * pct)) if missing > 0 else 0
                    if heal <= 0:
                        lines.append("🔥 暖意融融，但你精神饱满，用不上这份治愈～(明天再来也一样暖)")
                    else:
                        # F1 P1-4：原子认领——并发双请求只有首个恢复（后手提示今日已翻找过）
                        if not db.props_use_claim_atomic(qq_id, use_key, today):
                            lines.append("⏳ 今天已经在这里翻找过了……明天再来碰碰运气吧。")
                        else:
                            db.update_player(group_id, qq_id, hp=player["hp"] + heal)
                            lines.append(f"🔥 {eff.get('found_text', '暖意袭来')}——恢复 ❤️ {heal} 点生命({player['hp'] + heal}/{player.get('max_hp', 1)})！")
        yield event.plain_result("\n".join(lines))

    # ---------------- v65 NPC 多轮对话 ----------------

    def _talk_active(self, group_id, qq_id):
        """统一对话状态读取（O99 修复：统一对话结束状态判定）。

        对话结束判定（『对话 0』/移动拦截/副业材料保护）必须同源同判定：
        键存在但 JSON 损坏/非 dict（历史脏数据）时视为"无对话"并顺手清除残留键，
        杜绝『对话 0』提示"没有正在进行的对话"而移动仍被残留状态拦截的判定漂移。
        """
        st = db.get_talk_state(group_id, qq_id)
        if st is not None and not isinstance(st, dict):
            db.clear_talk_state(group_id, qq_id)
            return None
        if st is None:
            raw = db.get_event_state(db.talk_state_key(group_id, qq_id))
            if raw:
                db.clear_talk_state(group_id, qq_id)  # 损坏/无法解析的残留键 → 清除
        return st

    def _talk_ctx(self, group_id, qq_id, npc_id):
        """对话引擎上下文：player + quests + 该 NPC 已设 flag + 已拜师副业"""
        player = self._player(group_id, qq_id) or {}
        return {
            "player": player,
            "quests": db.get_quests(group_id, qq_id),
            "flags": db.get_talk_flags(group_id, qq_id, npc_id),
            "apprentices": player.get("apprentices", []),
            "npc_id": npc_id,
            "side_quests": C.SIDE_QUESTS,
            "item_counts": {m: db.count_item(group_id, qq_id, m) for m in {(o.get("objective") or {}).get("collect") for o in C.SIDE_QUESTS} if m},
            # v127.6 side_menu 动态菜单：core.visible_options 渲染时用该回调
            # 把『有活儿要交给我吗』类选项展开成『每个可接支线一个子选项』
            "side_menu_expand": lambda opt: self._side_menu_expand(group_id, qq_id, npc_id, opt),
        }

    def _side_menu_expand(self, group_id, qq_id, npc_id, opt) -> list:
        """v127.6：side_menu 选项的动态展开——每个可接支线一个子选项（玩家自选单接）。

        供 core.visible_options 的 side_menu_expand 回调调用；无任何可接支线 → 返回 []（菜单不出现）。
        子选项 next：side_menu.after（连串接，通常为该 NPC 对话树 start）→ 选项原 next → __end__。
        每条子选项 action: {"side_take_one": sid}，走 talk_actions.side_take_one 单条接取。
        """
        available = self._side_available_list(group_id, qq_id, npc_id, None)
        if not available:
            return []
        nxt = (opt.get("side_menu") or {}).get("after") or opt.get("next") or "__end__"
        subs = []
        for item in available:
            subs.append({
                "text": f"📜 接『{item['name']}』({item['objective_text']})",
                "next": nxt,
                "action": {"side_take_one": item["sid"]},
            })
        return subs

    def _render_talk_node(self, npc, dlg, node, ctx) -> list:
        """渲染一个对话节点：头像 + 台词 + 可见选项
        v101.23：台词走 C.node_text——支持 texts 条件变体（随主线进度切换）"""
        lines = [f"{npc['icon']}【{npc['name']}】{npc['title']}",
                 f"“{C.node_text(node, ctx)}”"]
        opts = C.visible_options(dlg, node, ctx)
        if opts:
            lines.append("━━━━━━━━━━━━")
            for i, opt in enumerate(opts, 1):
                lines.append(f"{i}. {opt['text']}")
            lines.append("0. 结束对话")
            lines.append(self._tip("talk_tree"))
        return lines

    def _branch_wait_sid(self, group_id, qq_id):
        """v124：查找处于分支等待状态的支线 sid（ready + branch_wait）。"""
        quests = db.get_quests(group_id, qq_id)
        for sid, sq in (quests.get("side") or {}).items():
            if sq.get("status") == "ready" and sq.get("branch_wait"):
                return sid
        return None

    def _update_use_quests(self, group_id, qq_id, item_name):
        """v124 use 目标支线：使用指定物品后支线置 ready（如 递麦酒/用月鳞/交信物）。
        v124.2 防跨图白嫖：objective.map 或任务自身 map 配置时，须玩家当前地图一致才推进；
        objective 无 map 且任务无 map 的保持原行为（不校验直接推进）。"""
        if not item_name:
            return ""
        quests = db.get_quests(group_id, qq_id)
        side = quests.get("side") or {}
        lines = []
        changed = False
        for sid, sq in list(side.items()):
            if sq.get("status") != "active":
                continue
            sqd = next((q for q in C.SIDE_QUESTS if q["id"] == sid), None)
            if not sqd:
                continue
            obj = sqd.get("objective") or {}
            if obj.get("use") and obj["use"] == item_name:
                _need_map = obj.get("map") or sqd.get("map")
                if _need_map:
                    _pm = self._player(group_id, qq_id) or {}
                    if _pm.get("cur_map") != _need_map:
                        continue
                side[sid] = {"status": "ready", "progress": {"use": item_name}}
                changed = True
                giver = C.NPCS.get(sqd["giver"]) or C.ALL_WILD.get(sqd["giver"]) or {}
                lines.append(f"✨ 『{sqd['name']}』目标达成！回去找 {giver.get('name', '发布人')} 交付吧～")
        if changed:
            quests["side"] = side
            db.save_quests(group_id, qq_id, quests)
        return "\n".join(lines)

    def _talk_quest_progress(self, group_id, qq_id, npc_id) -> list:
        """v95.11：talk 型主线与目标 NPC 对话即达成（active 空进度遗留态 → ready）。
        覆盖 v95.9 对话化之前接取、或接取瞬间未置 ready 的存量档，返回通知行。
        v105 P0/P2：collect 型主线对话时实时数背包（材料足够 → ready）；
        explore 型主线已在目标地图 → ready（免出图重进）。"""
        quests = db.get_quests(group_id, qq_id)
        if quests.get("main_status") != "active":
            return []
        mid = quests.get("main_quest")
        if not mid:
            return []
        mq = next((q for q in C.MAIN_QUESTS if q["id"] == mid), None)
        if not mq:
            return []
        obj = mq.get("objective", {})
        if obj.get("talk") == npc_id:
            quests["main_status"] = "ready"
            quests["main_progress"] = {npc_id: 1}
            db.save_quests(group_id, qq_id, quests)
            return ["✨ 交谈完成！再与这位 NPC 对话即可交付任务。"]
        if obj.get("collect") and mq.get("giver") == npc_id:
            need = obj.get("count", 1)
            if db.count_item(group_id, qq_id, obj["collect"]) >= need:
                quests["main_status"] = "ready"
                quests["main_progress"] = {obj["collect"]: need}
                db.save_quests(group_id, qq_id, quests)
                return [f"✨ 材料已齐（{obj['collect']} ×{need}）！再与这位 NPC 对话即可交付任务。"]
        if obj.get("explore") and mq.get("giver") == npc_id:
            player = self._player(group_id, qq_id)
            if player.get("cur_map") == obj["explore"]:
                quests["main_status"] = "ready"
                quests["main_progress"] = {obj["explore"]: 1}
                db.save_quests(group_id, qq_id, quests)
                return ["✨ 目标地点已到达！再与这位 NPC 对话即可交付任务。"]
        return []

    # ---------------- v95.23 职业就职 / 导师转职 ----------------

    def _do_join_class(self, group_id, qq_id, player, new_cls):
        """行会就职：见习冒险者 → 基础职业。
        属性按新职业重算（base+成长×等级+种族，自由点保留），赠送基础技能书（职业 Lv.1 技能）。
        返回通知行列表。"""
        lines = []
        if player.get("class_name") != C.CLASS_NOVICE:
            lines.append("你已经有正式职业了，冒险者行会只负责给新人就职。")
            return lines
        cls = C.CLASSES.get(new_cls)
        if not cls or cls.get("hidden"):
            lines.append("这个职业暂时无法就职……")
            return lines
        # 属性按新职业重算（参考隐藏职业传承的属性同步写法）
        st = E.player_final_stats(
            new_cls, player.get("level", 1), player.get("equipment", {}), 0,
            player.get("attributes"), 0,
            self._title_bonus(group_id, qq_id), player.get("race"))
        sk_table = C.PLAYER_SKILLS.get(new_cls, {})
        if isinstance(sk_table, dict) and "skills" in sk_table:
            sk_table = sk_table["skills"]
        init_skills = [s for s, info in sk_table.items() if info["lv"] <= 1]
        db.update_player(group_id, qq_id, class_name=new_cls,
                         max_hp=st["max_hp"], max_mp=st["max_mp"], hp=st["max_hp"], mp=st["max_mp"],
                         learned_skills=init_skills)
        bar = list(init_skills[:6])
        while len(bar) < 6:
            bar.append(None)
        db.set_skill_bar(qq_id, bar)
        names = "、".join(C.display("skills", s) for s in init_skills)
        lines.append(f"🎉 行会为你登记在册——就职【{cls['icon']} {cls['name']}】！")
        lines.append(f"『{cls['desc']}』")
        if names:
            lines.append(f"📖 行会赠送基础技能书，你学会了：{names}")
        lines.append(self._tip("skill_learn"))
        lines.append("💡 各城职业导师可学进阶技能；Lv.30/60/90 找导师转职")
        return lines

    def _do_evolve_via_npc(self, group_id, qq_id, player, next_tier, path):
        """导师转职：Lv.30/60/90 找对应职业导师对话转职（同步版，返回通知行）。"""
        lines = []
        cls = C.CLASSES.get(player.get("class_name", ""), {})
        cur_tier = player.get("class_tier", 0)
        need_lv = C.EVOLVE_LEVELS.get(next_tier)
        if not need_lv:
            lines.append("你已经完成了全部转职！")
            return lines
        if cur_tier != next_tier - 1:
            lines.append("时机未到，先提升自己的境界吧。")
            return lines
        if player.get("level", 0) < need_lv:
            lines.append(f"导师摇摇头：这一阶要 Lv.{need_lv} 才够格，你才 Lv.{player.get('level', 0)}。")
            return lines
        branches = cls.get("evolve_branches", {}).get(next_tier, [])
        if path < 1 or path > len(branches):
            path = 1
        old_title = self._tier_title(player["class_name"], cur_tier, player.get("evolve_path", 0))
        # v105 P1：转职同步重算属性并落库——TIER_GROWTH 成长加成随阶位跃升，
        # 仅写 class_tier 会让存档 max_hp/max_mp 长期与计算值脱节（战斗外休息/回家/
        # 药水/治疗全按存档上限回血，转职后回不满新上限）。参照 player.py 隐藏职业转职写法。
        new_evolve_path = path or player.get("evolve_path", 0)
        st = E.player_final_stats(
            player["class_name"], player.get("level", 1), player.get("equipment", {}),
            next_tier, player.get("attributes"), new_evolve_path,
            self._title_bonus(group_id, qq_id), player.get("race"))
        fields = {"class_tier": next_tier,
                  "max_hp": st["max_hp"], "max_mp": st["max_mp"],
                  "hp": st["max_hp"], "mp": st["max_mp"]}
        if path:
            fields["evolve_path"] = path
        db.update_player(group_id, qq_id, **fields)
        player = self._player(group_id, qq_id)
        new_title = self._branch_title(player["class_name"], next_tier, path or player.get("evolve_path", 0))
        bonus = int((E.TIER_GROWTH.get(next_tier, 1.0) - 1.0) * 100)
        branch_line = ""
        if path:
            tag = "⚔️ 进攻路线" if path == 1 else "🛡️ 防御路线"
            branch_line = f"\n🔀 {tag}"
        auto_skills = self._evolve_auto_skills(player, next_tier)
        if auto_skills:
            learned = player.get("learned_skills", [])
            learned = [s for s in learned if s not in auto_skills]
            learned += auto_skills
            db.update_player(group_id, qq_id, learned_skills=learned)
            player = self._player(group_id, qq_id)
        auto_line = ""
        if auto_skills:
            auto_line = f"\n🌟 领悟：{'、'.join(auto_skills)}"
        C.check_achievements(group_id, qq_id, player)
        lines.append("🌟 转职成功！")
        lines.append("━━━━━━━━━━━━")
        lines.append(f"{old_title}")
        lines.append("  ↓↓↓")
        lines.append(f"{cls['icon']} {new_title}{branch_line}")
        lines.append("")
        lines.append(f"✨ 成长加成 +{bonus}%(全属性)")
        lines.append(f"📜 新技能已解锁，输入『技能』查看！{auto_line}")
        lines.append("👑 已达成最终转职（Lv.90 三转）！" if next_tier >= 3 else "💪 继续历练，下一次转职在 Lv.60/90")
        return lines

    async def _apply_talk_action_async(self, group_id, qq_id, player, npc_id, action):
        """异步版对话动作执行（v113：支持 hidden_evolve 等 async 动作）——talk_choice 调用本方法。

        返回 (通知行, 路由提示)。路由提示由条件型动作（apprentice_check 等）设置：
          None    → 走选项 next
          "fail"  → 走选项 fail_next
          "__end__" → 直接结束对话
        v124.3（审计）：apprentice_check 注册表化后 talk_choice 主循环不再特判，
        只做本方法返回的通用路由分发；未知 action 键由 talk_actions.check_action_keys 告警。"""
        lines = []
        route = None
        self._talk_route = None
        self._talk_tail = None
        if not action:
            return lines, route
        import inspect
        from .talk_actions import ACTIONS, check_action_keys
        check_action_keys(action)
        for key, fn in ACTIONS.items():
            if not action.get(key):
                continue
            r = fn(self, group_id, qq_id, player, npc_id, action)
            if inspect.isawaitable(r):
                r = await r
            lines += r
            if self._talk_route is not None:
                # 条件型动作已判定：中断后续动作链（旧特判失败路径零动作执行——
                # 如 apprentice_check 失败时 consume_item 不扣料）
                route = self._talk_route
                break
        if self._talk_tail:
            lines += self._talk_tail
        return lines, route

    def _apply_talk_action(self, group_id, qq_id, player, npc_id, action) -> list:
        """执行选项动作(涉及 DB 的副作用统一在这落地)，返回通知行
        v101.23d：动作注册表化——commands/talk_actions.py 的 ACTIONS（与 CONDITIONS
        注册表对称），加新动作 = register 一个函数，本方法零改动。
        同步版：仅执行同步动作（测试/旧调用用）；对话主链路走 _apply_talk_action_async。
        v113：hidden_evolve 为异步动作，同步版会跳过它（返回空）——对话内转职走 async 版。
        v124.3（审计）：与 async 版同源——未知 action 键告警 + 条件型动作（apprentice_check）
        中断动作链；路由提示不入返回值（仅 async 版返回，供 talk_choice 分发）。"""
        lines = []
        self._talk_route = None
        self._talk_tail = None
        if not action:
            return lines
        import inspect
        from .talk_actions import ACTIONS, check_action_keys
        check_action_keys(action)
        for key, fn in ACTIONS.items():
            if not action.get(key):
                continue
            r = fn(self, group_id, qq_id, player, npc_id, action)
            if inspect.isawaitable(r):
                continue  # 异步动作（hidden_evolve）同步版跳过
            lines += r
            if self._talk_route is not None:
                break
        if self._talk_tail:
            lines += self._talk_tail
        return lines

    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:对话|继续|结束对话|再见|告辞)(?:[\s\S]*)$")
    @require_player()
    async def talk_choice(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        # O99 修复：统一对话状态判定（损坏残留键在 _talk_active 内清除，
        # 对话中『对话 0』亦拦截（v127.8b）与移动拦截同源同判定，不再出现"提示无对话但树仍在"的漂移）
        st = self._talk_active(group_id, qq_id)
        if not st:
            # v101.16 『找』→『对话』：无对话中时『对话 <名字/序号>』= 找 NPC 开始对话
            msg0 = event.get_message_str().strip()
            msg0 = re.sub(r"^\[At:[^\]]*\]\s*", "", msg0)
            if msg0.startswith("对话"):
                raw0 = msg0[len("对话"):].strip()
                if raw0:
                    # v105 O64：『对话 0』在无对话状态时明确提示（原实现被 find_npc 当 NPC 序号 0，
                    # 报"这里没有第 0 位 NPC"——玩家在单层 NPC 闲聊后想结束对话却得不到退出反馈）
                    # O99 修复：全角 ０ 与 ASCII 0 同判（此前全角 ０ 落入 find_npc 报"没有第 0 位"）
                    if raw0 in ("0", "０"):
                        yield event.plain_result("你现在没有正在进行的对话。输入『对话 <NPC名>』开始交谈～")
                        return
                    # 复用 find_npc 查找/渲染链（改写消息为『找 X』）
                    event.message_str = "找 " + raw0
                    async for r in self.find_npc(event):
                        yield r
                    return
                # 『对话』空参 = 显示当前 NPC 列表
                yield event.plain_result("\n".join(self._start_talk_list(group_id, qq_id)))
                return
            yield event.plain_result("你现在没有正在进行的对话。输入『对话 <NPC名>』开始交谈～")
            return
        npc_id = st.get("npc", "")
        npc = C.NPCS.get(npc_id) or C.ALL_WILD.get(npc_id)
        if not npc:
            db.clear_talk_state(group_id, qq_id)
            yield event.plain_result("这位 NPC 似乎已经离开了……")
            return
        npc = dict(npc)
        npc.setdefault("title", "游历于野外的旅人")  # v95.11：wild NPC 无 title，与 _find_wild_npc 一致
        # 惰性失效：NPC 不在当前地图 → 会话作废（wild NPC 按 roam 定位）
        if C.npc_map_id(npc_id, npc) != player.get("cur_map"):
            db.clear_talk_state(group_id, qq_id)
            _ta = "她" if npc.get("gender") == "女" else "他"  # v95 #141：代词跟随 NPC 性别
            yield event.plain_result(f"{npc['name']}不在这里了，对话只能作罢。去找{_ta}再聊聊吧～")
            return
        # v127.5 限时NPC：对话中野外NPC的在场的限时事件过期 → 会话作废
        # （倒计时结束显示与对话同时消失；与 npc_map_id 失效同位置、同文案风格）
        if npc_id in C.ALL_WILD and not C.get_timed(group_id, qq_id, f"wild:{npc_id}"):
            db.clear_talk_state(group_id, qq_id)
            _ta = "她" if npc.get("gender") == "女" else "他"  # v95 #141：代词跟随 NPC 性别
            yield event.plain_result(f"{npc['name']}已经离开了，对话只能作罢。去找{_ta}再聊聊吧～")
            return
        dlg = C.get_dialogue(npc_id)
        if not dlg:
            db.clear_talk_state(group_id, qq_id)
            yield event.plain_result(f"{npc['name']}似乎不想再多说了。")
            return
        # 剥指令名拿参数（对话/继续/结束对话/再见/告辞）
        msg = event.get_message_str().strip()
        msg = re.sub(r"^\[At:[^\]]*\]\s*", "", msg)
        raw = msg
        for cmd in ("结束对话", "对话", "继续", "再见", "告辞"):
            if msg.startswith(cmd):
                raw = msg[len(cmd):].strip()
                break
        # v127.8（鱼鱼拍板）：对话进行中『对话 <参数>』拦截——
        # ① 不能用于回复 NPC（选项回复走裸数字 1/2/3…，回复 0 结束对话）
        # ② 不能跳去别的 NPC（先回复 0 结束当前对话，才能『对话 <别的NPC>』）
        # 此前 v101.27 #412 的「『对话 数字』= 菜单选项 / 『对话 名字』= 找 NPC」规则整体作废。
        # 『对话』空参 → 重渲染当前节点（向下兼容）；v127.8 起对话中任何『对话 X』（含 0）一律拦截，结束统一回复 0。
        # v127.8b（鱼鱼拍板）：『对话 0』也不保留——对话中任何『对话 X』（含 0）
        # 一律拦截，结束对话统一回复裸数字 0（与选项回复同通道，无二义性）。
        if msg.startswith("对话") and raw:
            yield event.plain_result(
                f"你正在和 {npc['name']} 对话——直接回复数字选选项，回复 0 结束对话～\n"
                f"💡 想找别的 NPC？先回复 0 结束当前对话再说")
            return
        cur_node_id = st.get("node", dlg.get("start", ""))
        node = C.dialogue_node(dlg, cur_node_id)
        ctx = self._talk_ctx(group_id, qq_id, npc_id)
        opts = C.visible_options(dlg, node, ctx)
        if raw.isdigit():
            idx = int(raw)
            if idx == 0:
                db.clear_talk_state(group_id, qq_id)
                yield event.plain_result(f"{npc['name']}：那就再会了，冒险者。")
                return
            if idx < 1 or idx > len(opts):
                # v101.28l #426：单选项时不再显示"1-1"（越界文案）
                _sel_hint = "回复 1 选择" if len(opts) == 1 else f"回复 1-{len(opts)} 选择"
                yield event.plain_result(f"没有这个选项！{_sel_hint}，回复 0 结束。")
                return
            opt = opts[idx - 1]
            player = self._player(group_id, qq_id)
            action = opt.get("action") or {}
            nxt = opt.get("next", "__end__")
            # v124.3（审计）：apprentice_check 已注册为动作（talk_actions.py），
            # 主循环不再特判——条件型动作经 _apply_talk_action_async 返回的路由分发：
            #   "fail"（材料不足）→ 走选项 fail_next；"__end__"（副业未解锁 #101.29）→ 结束对话
            notices, _route = await self._apply_talk_action_async(group_id, qq_id, player, npc_id, action)
            if _route == "__end__":
                db.clear_talk_state(group_id, qq_id)
                lines = notices + [f"{npc['name']}：那就再会了，冒险者。"]
                yield event.plain_result("\n".join(lines))
                return
            if _route == "fail":
                nxt = opt.get("fail_next", nxt)
            # v95.11：talk 型主线与目标 NPC 对话即达成（active 空进度遗留态 → ready，修复主线卡死）
            notices += self._talk_quest_progress(group_id, qq_id, npc_id)
            # v105 P3：对话动作链落地后补成就判定（拜师/转职/任务交付等动作改 DB 后立即解锁——
            # 原实现无此调用，『拜师学艺/全知全能』等依赖学徒数的成就要等下次事件才判定，
            # 全知全能(第 8 条拜师)的全副业经验 +10% 加成也因此延迟生效）
            C.check_achievements(group_id, qq_id)
            if C.is_end(nxt):
                db.clear_talk_state(group_id, qq_id)
                lines = notices + [f"{npc['name']}：那就再会了，冒险者。"]
                yield event.plain_result("\n".join(lines))
                return
            db.set_talk_state(group_id, qq_id, npc_id, nxt)
            new_node = C.dialogue_node(dlg, nxt)
            ctx = self._talk_ctx(group_id, qq_id, npc_id)
            lines = notices + self._render_talk_node(npc, dlg, new_node, ctx)
            yield event.plain_result("\n".join(lines))
            return
        if not raw and any(c in msg for c in ("结束对话", "再见", "告辞")):
            db.clear_talk_state(group_id, qq_id)
            yield event.plain_result(f"{npc['name']}：那就再会了，冒险者。")
            return
        # 无参数/其他 → 重渲染当前节点
        lines = self._render_talk_node(npc, dlg, node, ctx)
        yield event.plain_result("\n".join(lines))

    def _deliver_hint(self, npc_id):
        """交付方式提示（v95.16 #75）：有对话树 NPC 走对话交付，无对话树 NPC 用『交付任务』"""
        if C.DIALOGUES.get(npc_id):
            return "对话交付"
        return "『交付任务』交付"

    def _side_available_list(self, group_id, qq_id, npc_id, npc) -> list:
        """v127.6：该 NPC 名下当前"可接"的支线清单（对话菜单/预告/全接三处同源过滤）。

        过滤条件与旧 _offer_side_quests 全部一致：giver == npc_id、非告示板委托(board)、
        未接取（不在 side）、_sq_unlocked 链式前置、_sq_stats_met 计数门槛、
        min_level 等级门槛、require_race 种族限制。每项返回
        {sid, name, desc, objective_text, reward_exp, reward_gold}，按 SIDE_QUESTS 定义顺序
        （保证对话菜单序号稳定）。npc 参数保留以与 _offer_side_quests 签名一致（此处未用到）。
        """
        player = self._player(group_id, qq_id) or {}
        quests = db.get_quests(group_id, qq_id)
        side = quests.get("side", {}) or {}
        out = []
        for sq in C.SIDE_QUESTS:
            if sq["giver"] != npc_id:
                continue
            if sq.get("board"):  # v95r65 #295：告示板委托只能在告示板接取，NPC 不自动发
                continue
            if sq["id"] in side:
                continue
            # v124 链式支线：unlock 前置未满足不自动发（如剧情线第二步等第一步完成）
            if not self._sq_unlocked(quests, sq):
                continue
            # v124 隐藏线/副业线：require_stats 计数门槛未达不自动发（如 H7 需垂钓 10 次）
            if not self._sq_stats_met(player, sq):
                continue
            # v101.30d #O52：支线等级门槛（min_level 字段）——等级不够不算可接
            if sq.get("min_level") and (player.get("level") or 0) < sq["min_level"]:
                continue
            # v113 种族限制：require_race 指定血脉（隐藏线试炼）——非该种族不算可接
            if sq.get("require_race"):
                _cur = player.get("race") or "human"
                if _cur != sq["require_race"]:
                    continue
            out.append({
                "sid": sq["id"],
                "name": sq["name"],
                "desc": sq.get("desc", ""),
                "objective_text": self._obj_text(sq.get("objective") or {}),
                "reward_exp": sq.get("reward_exp", 0),
                "reward_gold": sq.get("reward_gold", 0),
            })
        return out

    def _offer_side_quest(self, group_id, qq_id, npc_id, sid) -> list:
        """v127.6：单条支线接取（对话 side_menu 子选项 action: side_take_one）。

        校验 sid 必须在 _side_available_list 当前可接清单内才接（防越权/已接/等级不足），
        否则返回 [] 不落地。返回该任务的接取通知行列表。
        """
        item = next((a for a in self._side_available_list(group_id, qq_id, npc_id, None)
                     if a["sid"] == sid), None)
        if not item:
            return []
        sq = next((q for q in C.SIDE_QUESTS if q["id"] == sid), None)
        if not sq:
            return []
        quests = db.get_quests(group_id, qq_id)
        side = dict(quests.get("side", {}))
        side[sid] = {"status": "active", "progress": {}}
        quests["side"] = side
        db.save_quests(group_id, qq_id, quests)
        return [
            f"📜 【支线】『{sq['name']}』{sq['desc']}",
            f"  奖励：经验 +{sq['reward_exp']} 金币 +{sq['reward_gold']}",
            f"  🎯 目标：{item['objective_text']}",
        ]

    def _offer_side_quests(self, group_id, qq_id, npc_id, npc):
        """NPC 有未接的支线任务时自动接取，返回通知行列表

        v127.6 重构：可接清单统一走 _side_available_list（与对话 side_menu 菜单/预告同源过滤），
        逐条复用 _offer_side_quest 接取；不可接（min_level/require_race 被过滤掉）的
        原拒绝提示按 SIDE_QUESTS 顺序保留，全接+完成提示行为不变（旧 side_offer action 兼容，
        单支线 NPC 无感）。
        """
        player = self._player(group_id, qq_id) or {}
        lines = []
        quests = db.get_quests(group_id, qq_id)
        side = dict(quests.get("side", {}))
        available = self._side_available_list(group_id, qq_id, npc_id, npc)
        av_ids = {a["sid"] for a in available}
        changed = False
        for sq in C.SIDE_QUESTS:
            if sq["giver"] != npc_id or sq.get("board"):
                continue
            if sq["id"] in side:
                continue
            if sq["id"] in av_ids:
                side[sq["id"]] = {"status": "active", "progress": {}}
                changed = True
                lines.append(f"📜 【支线】『{sq['name']}』{sq['desc']}")
                lines.append(f"  奖励：经验 +{sq['reward_exp']} 金币 +{sq['reward_gold']}")
                lines.append(f"  🎯 目标：{self._obj_text(sq['objective'])}")
                continue
            # 不可接但符合其余条件的拒绝提示（与原始行为文案一致）
            if not self._sq_unlocked(quests, sq):
                continue
            if not self._sq_stats_met(player, sq):
                continue
            # v101.30d #O52：支线等级门槛——等级不够不自动接
            if sq.get("min_level") and (player.get("level") or 0) < sq["min_level"]:
                lines.append(
                    f"🛡️ {npc.get('name', '对方')}打量了你一眼：这活得有 Lv.{sq['min_level']}+ 的本事，你再去练练吧。"
                )
                continue
            # v113 种族限制：require_race 指定血脉——非该种族导师直接拒绝
            if sq.get("require_race"):
                _rr = sq["require_race"]
                _cur = player.get("race") or "human"
                if _cur != _rr:
                    _rcn = (C.RACES.get(_rr) or {}).get("name", "对应血脉")
                    lines.append(
                        f"⛔ {npc.get('name', '对方')}凝视着你，缓缓摇头：『这份传承只属于{_rcn}的血脉。"
                        f"你体内流淌的{(C.RACES.get(_cur) or {}).get('name', '血脉')}之血，与它无缘。』"
                    )
                    continue
        if changed:
            quests["side"] = side
            db.save_quests(group_id, qq_id, quests)
        # v95.4：该 NPC 有已完成支线 → 提示交付入口（反馈：可交任务找不到交付方式）
        # v95.15 #73：代词按 NPC 性别（迷路骑士等男性 NPC 用"他"）
        # v95.16 #75：按是否有对话树区分交付引导（无对话树 NPC 的『对话』没有交付选项）
        _ta = "她" if npc.get("gender") == "女" else "他"
        for sid, sq in list(quests.get("side", {}).items()):
            sqd = next((q for q in C.SIDE_QUESTS if q["id"] == sid), None)
            if sqd and sqd["giver"] == npc_id and sq.get("status") == "ready":
                if C.DIALOGUES.get(npc_id):
                    lines.append(f"✅ 『{sqd['name']}』已完成！与{_ta}对话即可交付～")
                else:
                    lines.append(f"✅ 『{sqd['name']}』已完成！输入『交付任务』即可交付～")
                break
        return lines

    # v104 M24 P2-2：『交任务』无命中（策划案 23 章:182 主指令）→ 补别名
    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:交付任务|交任务)(?:\s*|$)")
    @require_player()

    async def turn_in(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        quests = db.get_quests(group_id, qq_id)
        # v101.27 #341：夜晚 NPC 不在场不能隔空交付——用官方出现条件判定
        # （base_conditions_met 覆盖 period/condition.time/season/weather 等全部条件，
        # 采药女·小荨 condition.time=['morning','day'] 夜晚交付实锤）
        def _npc_absent(npc_id, npc):
            if not npc:
                return None
            if not C.base_conditions_met(npc_id, npc, player, group_id, qq_id):
                period_cn = (C.PERIOD_CN.get(C.current_period(), "") or "").strip()
                return f"🌙 {npc.get('name', '他')}现在({period_cn})不在这里，换个时间再来交付吧～"
            return None
        # 主线可交
        main_id = quests.get("main_quest")
        st = quests.get("main_status", "pending")
        if main_id and st == "ready":
            mq = next((q for q in C.MAIN_QUESTS if q["id"] == main_id), None)
            if mq:
                npc = C.NPCS.get(mq["giver"])
                if npc and npc["map"] == player["cur_map"]:
                    absent = _npc_absent(mq["giver"], npc)
                    if absent:
                        yield event.plain_result(absent)
                        return
                    lines = self._take_main_quest(group_id, qq_id, mq["giver"], npc)
                    yield event.plain_result("\n".join(lines))
                    return
                else:
                    giver = C.NPCS.get(mq["giver"], {}).get("name", "？")
                    giver_map = C.NPCS.get(mq["giver"], {}).get("map", "")
                    yield event.plain_result(f"你需要到 {C.MAP_BY_ID.get(giver_map, {}).get('name', '？')} 找 {giver} 交付任务！")
                    return
        # 支线可交
        # O100 修复：『交付任务』按当前 NPC/地图过滤——此前遍历 dict 顺序取第一个 ready
        # 支线，在城主处可能先命中"护送商货(需找老赵)"而忽略当场可交的"码头的猫"。
        # 现逻辑：① 当前地图有交付 NPC → 当场交付（过滤优先）；② 无当场可交但别处有
        # ready 支线 → 一次性列出全部可交付任务与位置（不再只报第一条误导玩家）。
        collect_missing = None  # 收集型材料还差的信息（用于最后提示）
        waiting = []  # O100：已达成但交付 NPC 不在当前地图的支线 [(任务名, NPC名, 地图名)]
        for sid, sq in list(quests.get("side", {}).items()):
            sqd = next((q for q in C.SIDE_QUESTS if q["id"] == sid), None)
            if not sqd:
                continue
            if sq.get("status") == "done":  # v95.12：已交付支线不重复接取/交付
                continue
            npc = C.NPCS.get(sqd["giver"]) or C.ALL_WILD.get(sqd["giver"]) or C.HIDDEN_NPCS.get(sqd["giver"])  # R3 P1-4：副本内 NPC（潮汐祭司）交付解析
            obj = sqd["objective"]
            # 收集型：实时检查背包材料（不依赖 ready 状态）
            if obj.get("collect"):
                # v104 审计 P1-3：复合目标（魔剑士试炼 collect_count=2/count=3）门槛统一按
                # collect_count 判定（此前用 obj["count"]=3 与 quest_view 的 2 不一致：
                # 面板显示"✅ 可交"、交付却拒"还差 ×1(背包 2/3)"）
                need = obj.get("collect_count") or obj.get("count", 1)  # v125.1 P2：s64 等 collect_count 无 count 不再 KeyError
                have = db.count_item(group_id, qq_id, obj["collect"])
                if have >= need:
                    if npc and npc["map"] == player["cur_map"]:
                        absent = _npc_absent(sqd["giver"], npc)
                        if absent:
                            yield event.plain_result(absent)
                            return
                        lines = self._complete_side_quest(group_id, qq_id, sid)
                        yield event.plain_result("\n".join(lines))
                        return
                    else:
                        giver = (C.NPCS.get(sqd["giver"]) or C.ALL_WILD.get(sqd["giver"]) or C.HIDDEN_NPCS.get(sqd["giver"]) or {}).get("name", "？")  # R3 P1-4
                        giver_map = C.MAP_BY_ID.get((C.NPCS.get(sqd["giver"]) or C.ALL_WILD.get(sqd["giver"]) or C.HIDDEN_NPCS.get(sqd["giver"]) or {}).get("map", ""), {}).get("name", "？")
                        waiting.append((sqd["name"], giver, giver_map))
                else:
                    collect_missing = (sqd["name"], obj["collect"], have, need)
                continue
            # 击杀/探索型：按 ready 状态
            if sq.get("status") == "ready":
                # v124 分支任务：输出选项等待玩家回复（不自动完成）
                if sqd.get("branch") and not sq.get("branch_wait"):
                    lines = self._complete_side_quest(group_id, qq_id, sid)
                    yield event.plain_result("\n".join(lines))
                    return
                if npc and npc["map"] == player["cur_map"]:
                    absent = _npc_absent(sqd["giver"], npc)
                    if absent:
                        yield event.plain_result(absent)
                        return
                    lines = self._complete_side_quest(group_id, qq_id, sid)
                    yield event.plain_result("\n".join(lines))
                    return
                else:
                    giver = (C.NPCS.get(sqd["giver"]) or C.ALL_WILD.get(sqd["giver"]) or C.HIDDEN_NPCS.get(sqd["giver"]) or {}).get("name", "？")  # R3 P1-4
                    giver_map = C.MAP_BY_ID.get((C.NPCS.get(sqd["giver"]) or C.ALL_WILD.get(sqd["giver"]) or C.HIDDEN_NPCS.get(sqd["giver"]) or {}).get("map", ""), {}).get("name", "？")
                    waiting.append((sqd["name"], giver, giver_map))
        # O100：无当场可交付时，列出全部"已达成待交付"任务（带位置），不再只报第一条
        if waiting:
            lines = ["📜 可交付任务："]
            for i, (qname, giver, giver_map) in enumerate(waiting, 1):
                lines.append(f"{i:>2}. 『{qname}』→ 找 {giver}(在{giver_map})")
            lines.append(self._tip("quest_deliver"))
            yield event.plain_result("\n".join(lines))
            return
        if collect_missing:
            name, mat, have, need = collect_missing
            yield event.plain_result(f"支线『{name}』还差 {mat} ×{need - have}(背包 {have}/{need})！")
            return
        yield event.plain_result("没有可交的任务。输入『任务』查看进度～")

    def _grant_quest_rewards(self, group_id, qq_id, qdef, lines):
        """v124.3 统一任务奖励发放（主线 explore 自动完成 / 主线交付 / 支线交付三处共用）。

        基准：支线 _complete_side_quest 原实现（v104 M20 + v124 全奖励类型）——
        reward_exp/reward_gold 入角色并结算升级；reward_item 支持单值 / 列表随机 /
        eq: 装备名册；reward_pet 宠物蛋 / reward_mount 坐骑缰绳入包；unlock_class
        解锁隐藏职业。声望 / 分支 flag / 每日计数等任务特有处理不入此函数，调用方各自保留。
        返回结算后的 player（调用方后续需要时使用，如 _complete_side_quest 的 _rule_fire）。"""
        player = self._player(group_id, qq_id)
        player["exp"] += qdef.get("reward_exp", 0)
        player["gold"] += qdef.get("reward_gold", 0)
        player["_title_bonus"] = self._title_bonus(group_id, qq_id)
        lv_logs, player = E.check_player_level_up(group_id, qq_id, player)
        db.update_player(group_id, qq_id, exp=player["exp"], gold=player["gold"], level=player["level"], hp=player["hp"], mp=player["mp"], max_hp=player["max_hp"], max_mp=player["max_mp"], skills=player["skills"], attr_pts=player.get("attr_pts", 0), skill_points=player.get("skill_points", 0), learned_skills=player.get("learned_skills", []))
        if lv_logs:
            if lines:
                lines.append("")
            lines += lv_logs
        # v104 M20 P1：列表型奖励（如 s17 随机符文）→ 随机抽一个发放
        ri = qdef.get("reward_item")
        if ri:
            if isinstance(ri, list):
                ri = random.choice(ri)
            # v104 M20 P1：eq: 前缀 = 装备奖励（s3 汉斯的手工武器）——名册精确生成入包
            if isinstance(ri, str) and ri.startswith("eq:"):
                eq_name = ri[3:]
                eq_ids = C.EQUIP_ROSTER_BY_NAME.get(eq_name, [])
                if eq_ids:
                    eq = C.generate_roster_equip(eq_ids[0])
                    db.add_item(group_id, qq_id, eq_ids[0], eq)
                    lines.append(f"  🎁 获得装备：{eq.get('name', eq_name)}")
                else:
                    print(f"[dragonfall][v104] 任务『{qdef.get('name', '')}』奖励装备缺失：{eq_name}（名册未收录），已跳过")
            else:
                # v104 M20 P3：先 items 后 materials（同名跨表实体发对表，如 s4「麦酒」）
                _iid = C.resolve("items", ri)
                if _iid in C.ITEMS:
                    _idata = C.ITEMS[_iid]
                    db.add_item(group_id, qq_id, _iid, _idata)
                    lines.append(f"  🎁 获得特殊道具：{ri}")
                else:
                    rimid = C.resolve("materials", ri)
                    if rimid in C.MATERIALS:
                        db.add_item(group_id, qq_id, rimid,
                                    {"name": C.display("materials", rimid),
                                     "type": C.MATERIALS[rimid].get("type", "材料"),
                                     "stackable": True, "price": C.MATERIALS[rimid]["price"]})
                        lines.append(f"  🎁 获得特殊道具：{ri}")
                    else:
                        # v104 M20 P1：奖励实体缺失时记录（此前静默不发，缺失项无从发现）
                        print(f"[dragonfall][v104] 任务『{qdef.get('name', '')}』奖励道具缺失：{ri}（未收录），已跳过")
        # v124 宠物蛋（reward_pet，如橡木镇新手任务铁壳龟蛋）入包——蛋入包后『使用 宠物蛋』孵化
        rp = qdef.get("reward_pet")
        if rp:
            _egg = C.make_pet_egg(rp)
            db.add_item(group_id, qq_id, f"petegg_{rp}", _egg)
            lines.append(f"  🥚 获得道具：{_egg['name']}！『使用 宠物蛋』孵化！")
        # v124 坐骑缰绳（reward_mount，如 hq7_3 雾羽候鸟）——『使用 缰绳』驯服解锁
        rm = qdef.get("reward_mount")
        if rm:
            _rein = C.make_mount_rein(rm)
            db.add_item(group_id, qq_id, f"mountrein_{rm}", _rein)
            lines.append(f"  🐾 获得道具：{_rein['name']}！『使用 缰绳』驯服坐骑！")
        # v87 隐藏职业：交任务解锁（unlock_class 写入 hidden_class_unlock）
        uc = qdef.get("unlock_class")
        if uc:
            player_now = self._player(group_id, qq_id)
            unlocks = list(player_now.get("hidden_class_unlock", []) or [])
            if uc not in unlocks:
                unlocks.append(uc)
                db.update_player(group_id, qq_id, hidden_class_unlock=unlocks)
                lines.append(f"  ⚔️ 传承达成！隐藏职业「{C.CLASSES.get(uc, {}).get('name', uc)}」已解锁！")
                # v112：档位门槛统一读 CLASSES["tier_levels"]（缺省 T1=40），删除 60/30 特例
                _need = (C.CLASSES.get(uc, {}).get("tier_levels") or {1: 40, 2: 60, 3: 90})[1]
                _cname = C.CLASSES.get(uc, {}).get("name", uc)
                lines.append(f"  💡 达到 {_need} 级后输入『转职 {_cname}』接受传承！")
        # v140 波3.6：任务奖励称号（title 字段 = titles.py id 或中文名；称号系统条件判定自动拥有，
        # 这里仅播报解锁——条件满足即生效，不满足也不阻塞任务完成）
        _tid = qdef.get("title")
        if _tid:
            _tinfo = next((t for t in C.TITLES if t.get("id") == _tid), None)
            if not _tinfo:
                # 兼容支线旧字段用中文名（如 "北境的恩人" → north_benefactor）
                _tinfo = next((t for t in C.TITLES if t.get("name") == _tid), None)
            if _tinfo:
                lines.append(f"  🏅 获得称号：「{_tinfo.get('name', _tid)}」！")
            else:
                print(f"[dragonfall][v140] 任务『{qdef.get('name', '')}』称号 id 缺失：{_tid}（titles.py 未登记），已跳过")
        return player

    def _complete_side_quest(self, group_id, qq_id, sid, branch_choice=None):
        """交支线任务，返回通知行列表
        v124：支持 branch 分支交付（第一次输出选项并置 branch_wait，玩家回复数字后执行）+
        deliver_text 交付剧情文本。"""
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
            # v87 复合目标：kill+collect（魔剑士试炼），collect_count 独立于 kill count
            need = obj.get("collect_count") or obj.get("count", 1)  # v125.1 P2：s64 等 collect_count 无 count 不再 KeyError
            _ckey = C.resolve("materials", obj["collect"])
            have = db.count_item(group_id, qq_id, _ckey)
            if have < need:
                return [f"材料不够！需要 {obj['collect']} ×{need}，你只有 {have} 个。"]
            # v87 复合目标：同时存在 kill 目标时，击杀进度也要满足
            if obj.get("kill"):
                kp = (sq.get("progress") or {}).get(obj["kill"], 0)
                if kp < obj["count"]:
                    return [f"还要击败 {obj['kill']} ×{obj['count'] - kp}(当前 {kp}/{obj['count']})！"]
        elif sq.get("status") != "ready":
            return ["这个任务还没完成呢。"]
        # v124 分支任务：第一次交付输出选项，等待玩家回复数字
        br = sqd.get("branch")
        if br and not branch_choice:
            opts = br.get("options") or []
            if sq.get("branch_wait"):
                return [f"{br.get('prompt', '')}\n{self._tip('quest_branch')}\n" + "\n".join(
                    f"  {o.get('key', str(i + 1))}. {o.get('label', '')}" for i, o in enumerate(opts))]
            quests["side"][sid] = {**sq, "status": "ready", "branch_wait": True}
            db.save_quests(group_id, qq_id, quests)
            _o = [f"  {o.get('key', str(i + 1))}. {o.get('label', '')}" for i, o in enumerate(opts)]
            return [f"{br.get('prompt', '')}\n{self._tip('quest_branch')}\n" + "\n".join(_o)]
        # v124 分支选择执行
        if br and branch_choice:
            opts = br.get("options") or []
            chosen = None
            if isinstance(branch_choice, str):
                for o in opts:
                    if branch_choice in (o.get("key"), o.get("label")):
                        chosen = o
                        break
            if chosen is None:
                return [f"没有这个选项～{br.get('prompt', '')}\n{self._tip('quest_branch')}\n" + "\n".join(
                    f"  {o.get('key', str(i + 1))}. {o.get('label', '')}" for i, o in enumerate(opts))]
            # 用分支选项覆盖奖励（顶层 reward 为 0 时以选项为准）
            lines.append(f"  📖 {chosen.get('text', '')}")
            sqd = {**sqd,
                   "reward_exp": chosen.get("reward_exp", sqd.get("reward_exp", 0)),
                   "reward_gold": chosen.get("reward_gold", sqd.get("reward_gold", 0)),
                   "reward_item": chosen.get("reward_item", sqd.get("reward_item"))}
            # v124 分支 flag：写入 giver NPC 的 flag 桶（称号/后续任务判定用）
            _cf = chosen.get("flag")
            if _cf:
                db.set_talk_flag(group_id, qq_id, sqd.get("giver", ""), _cf)
        # 收集类：扣除材料
        if obj.get("collect"):
            need = obj.get("collect_count") or obj.get("count", 1)  # v125.1 P2：s64 等 collect_count 无 count 不再 KeyError
            for _ in range(need):
                db.remove_item(group_id, qq_id, _ckey)
            # v126.2：鱼获个体属性在 item_data.tags，remove_item 自动截断，无需额外同步
        # v124 交付剧情文本（无分支时）
        dt = sqd.get("deliver_text")
        if dt and not br:
            lines.append(f"  📖 {dt}")
        # v124.3：奖励统一走 _grant_quest_rewards（exp/gold/升级 + reward_item 全格式 +
        # reward_pet/reward_mount/unlock_class）——逻辑与支线原实现完全一致（列表随机 /
        # eq: 名册 / items→materials 顺序），返回结算后 player 供下方 _rule_fire 使用
        player = self._grant_quest_rewards(group_id, qq_id, sqd, lines)
        # v95.12：交付后保留条目标记 done（无 completed_side 列），防止 _offer_side_quests 自动重接
        quests["side"][sid] = {"status": "done"}
        db.save_quests(group_id, qq_id, quests)
        # v104 M20：行会委托每日（complete_side）——支线交付完成 +1，达标发奖
        self._bump_daily_progress(group_id, qq_id, "complete_side", lines)
        lines.append(f"✅ 【支线完成】『{sqd['name']}』！")
        lines.append(f"  奖励：经验 +{sqd['reward_exp']} 金币 +{sqd['reward_gold']}")
        rep_line = self._quest_reputation(group_id, qq_id, sqd["giver"])
        if rep_line:
            lines.append(f"  {rep_line}")
        # v97.5 行为彩蛋规则：任务交付后
        _rule_txt = self._rule_fire("quest_deliver", group_id, qq_id, player,
                                    C.MAP_BY_ID.get(player.get("cur_map"), {}))
        if _rule_txt:
            lines.append(f"  {_rule_txt}")
        return lines

    @filter.regex(r"^(?:\[At:\d+\]\s*)?休息(?:\s*|$)")
    @require_player()

    async def rest_camp(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        cur_map = C.MAP_BY_ID.get(player["cur_map"], {})
        mid = cur_map.get("id", "")
        if mid not in C.CAMP_SPOTS:
            yield event.plain_result("这里没有篝火营地！找找野外地图的营地(地图上会显示🔥篝火营地)～")
            return
        # v87.17 子区域绑定：营地在指定子区域，不在那边够不着火堆
        _camp = C.CAMP_SPOTS[mid]
        _camp_sa = _camp.get("subarea", "") if isinstance(_camp, dict) else ""
        if _camp_sa and player.get("cur_subarea") != _camp_sa:
            _sa_name = ""
            for _s in (cur_map.get("subareas") or []):
                if _s["id"] == _camp_sa:
                    _sa_name = _s.get("name", "")
                    break
            _camp_name = _camp.get("name", "营地") if isinstance(_camp, dict) else str(_camp)
            yield event.plain_result(
                f"🔥 {_camp_name}在{_sa_name or _camp_sa}那边，这里够不着火堆！（『前往 {_sa_name or _camp_sa}』）"
            )
            return
        if self._in_battle(group_id, qq_id):
            yield event.plain_result("⚔️ 你正在战斗中！先解决眼前的敌人再说。")
            return
        # 30 秒冷却
        last = db.get_event_state(f"camp_{group_id}_{qq_id}")
        if last and int(time.time()) - int(last) < 30:
            left = 30 - (int(time.time()) - int(last))
            yield event.plain_result(f"⏳ 营地篝火需要添柴({left}秒后恢复)……")
            return
        # v94 体力：营地篝火恢复 50 体力（+ 原有半伤恢复）
        if player["hp"] >= player["max_hp"] and self._stamina(player) >= self._stamina_max(player):
            yield event.plain_result("你精神饱满，不需要休息～")
            return
        db.set_event_state(f"camp_{group_id}_{qq_id}", str(int(time.time())))
        heal = max(1, int((player["max_hp"] - player["hp"]) * 0.5))
        new_hp = min(player["max_hp"], player["hp"] + heal)
        _st_gain = self._add_stamina(group_id, qq_id, 50, player)
        db.update_player(group_id, qq_id, hp=new_hp)
        _p2 = self._player(group_id, qq_id)
        _st_line = f"\n⚡ 恢复 {_st_gain} 点体力({self._stamina(_p2)}/{self._stamina_max(_p2)})" if _st_gain > 0 else ""
        yield event.plain_result(
            f"🔥 你在{C.CAMP_SPOTS[mid]}的篝火旁歇了歇脚……\n"
            f"❤️ 恢复 {heal} 点生命({new_hp}/{player['max_hp']}){_st_line}\n"
            f"💡 营地只能恢复一半伤势，重伤请回旅店『住宿』～"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?住宿(?:\s*|$)")
    @require_player()

    async def rest(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if self._is_redname(qq_id):
            yield event.plain_result("☠️ 你是红名！旅店老板不敢收留你……(等红名消退再来)")
            return
        # v87.17 子区域化旅店：_at_healer 检查当前子区域，不在旅店给设施提示
        if not self._at_healer(player):
            hint = self._facility_hint(player, "healer")
            # v95.25 #134：示例不再写死"橡木镇旅店"——优先提示最近旅店（含当前城镇）
            if not hint:
                _cur_m = C.MAP_BY_ID.get(player.get("cur_map"), {})
                _near = []
                for _s in (_cur_m.get("subareas") or []):
                    if _s.get("healer"):
                        _near.append(f"{_cur_m.get('name', '')}·{_s.get('name', '')}")
                hint = "、".join(_near[:3]) if _near else ""
            yield event.plain_result(
                "这里没有旅店。"
                + (f"到有旅店的地方(如 {hint})输入『住宿』～" if hint else "到城镇旅店输入『住宿』恢复状态～")
            )
            return
        # v101.25i4 住宿费：Lv.≤15 保持 max(30, lv×5)（新手友好不动）；
        # Lv.16+ 纯等级线性 每级 5×2=10 金 并向下取整到百（鱼鱼拍板：凑整，Lv.100=1000金）
        # v131：解耦 hp_stage_mult——怪物曲线放缓后住宿跟随掉到 900，违反拍板 1000；
        #       费用按等级不按百分比（鱼鱼铁律），金币产出侧已由 monster_gold ×1.3 补偿。
        # v125.1：数值下沉 econ_config.ECON_CONFIG
        _ec = C.ECON_CONFIG
        lv = player.get("level") or 1
        if lv <= _ec["inn_cost_lv_cap"]:
            cost = max(_ec["inn_cost_min_low"], lv * _ec["inn_cost_per_lv"])
        else:
            cost = max(_ec["inn_cost_min_high"],
                       int(lv * _ec["inn_cost_per_lv"] * _ec["inn_cost_high_mult"])
                       // _ec["inn_cost_round"] * _ec["inn_cost_round"])
        if player["gold"] < cost:
            yield event.plain_result(f"住宿需要 {cost} 金币，你只有 {player['gold']} 金币。先去『探索』赚点钱吧～")
            return
        # v94 体力：住宿恢复满体力（+ 生命魔力）
        _st = self._stamina_max(player)
        db.update_player(group_id, qq_id, gold=player["gold"] - cost, hp=player["max_hp"], mp=player["max_mp"],
                         stamina=_st, stamina_ts=int(time.time()))
        yield event.plain_result(
            f"🏨 你在旅店美美地睡了一觉……\n"
            f"❤️ 生命全满！💙 魔力全满！{self._stamina_bar({**player, 'stamina': _st})}！\n"
            f"花费 {cost} 金币，当前余额：{player['gold'] - cost}"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?声望(?!商店)(?:\s*|$)")
    @require_player()

    async def reputation(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        rep = db.get_reputation(group_id, qq_id)
        lines = ["🏛️ 【七大势力 · 声望】", "━━━━━━━━━━━━"]
        for i, fid in enumerate(C.FACTION_ORDER, 1):
            f = C.FACTIONS[fid]
            pts = rep.get(fid, 0)
            tier = C.faction_reputation_tier(pts)
            lines.append(f"{i:>2}. {f['icon']} {f['name']}：{tier}({pts})")
        lines.append("")
        lines.append("💡 击杀各地怪物、完成当地任务可获得对应势力声望")
        # v105 M18 P2-7：声望消费侧入口（声望商店按等级解锁专属商品）
        lines.append(self._tip("rep_shop"))
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?声望商店(?:\s+\S+)?$")
    @require_player()

    async def rep_shop(self, event: AstrMessageEvent):
        """v105 M18 P2-7：势力声望商店——按声望等级解锁专属商品（声望只作门槛，金币购买）。

        用法：
          声望商店                       → 七势力总览（当前等级 + 可购商品数）
          声望商店 <势力名/序号>          → 查看该势力专属商品（🔒=声望不足）
          声望商店 <势力名/序号> 购买 <序号> → 购买商品（声望不足 → 提示所需等级）
        """
        from ..data.factions import FACTION_SHOP  # data/__init__ 未显式导出，局部导入避免动聚合层
        group_id, qq_id = self._uid(event)
        raw = self._strip_cmd(event, "声望商店").strip()
        rep = db.get_reputation(group_id, qq_id)
        player = self._player(group_id, qq_id)

        def _tier_name(th):
            for _t, _n in C.REPUTATION_TIERS:
                if th <= _t:
                    return _n
            return "崇拜"

        def _resolve_faction(arg):
            if not arg:
                return None
            if arg.isdigit():
                i = int(arg)
                if 1 <= i <= len(C.FACTION_ORDER):
                    return C.FACTION_ORDER[i - 1]
                return None
            for fid in C.FACTION_ORDER:
                if arg in C.FACTIONS[fid]["name"]:
                    return fid
            return None

        # 无参数：总览
        if not raw:
            lines = ["🏛️ 【势力声望商店】", "━━━━━━━━━━━━"]
            for i, fid in enumerate(C.FACTION_ORDER, 1):
                f = C.FACTIONS[fid]
                pts = rep.get(fid, 0)
                tier = C.faction_reputation_tier(pts)
                goods = FACTION_SHOP.get(fid, [])
                unlocked = sum(1 for g in goods if pts >= g["tier"])
                lines.append(f"{i:>2}. {f['icon']} {f['name']}：{tier}({pts}) 可购 {unlocked}/{len(goods)}")
            lines.append("")
            lines.append(self._tip("rep_shop"))
            yield event.plain_result("\n".join(lines))
            return

        parts = raw.split()
        if parts[0] == "购买":
            yield event.plain_result("格式：声望商店 <势力名/序号> 购买 <商品序号>（先『声望商店 <势力>』查看商品）")
            return
        fid = _resolve_faction(parts[0])
        if not fid:
            yield event.plain_result("没有这个势力！输入『声望商店』查看七个势力。")
            return
        f = C.FACTIONS[fid]
        pts = rep.get(fid, 0)
        tier = C.faction_reputation_tier(pts)
        goods = FACTION_SHOP.get(fid, [])
        if not goods:
            yield event.plain_result(f"{f['icon']} {f['name']} 暂时没有专属商品。")
            return
        # 购买分支：声望商店 <势力> 购买 <序号>
        if len(parts) >= 3 and parts[1] == "购买":
            if not parts[2].isdigit():
                yield event.plain_result("格式：声望商店 <势力名> 购买 <商品序号>")
                return
            idx = int(parts[2])
            if idx < 1 or idx > len(goods):
                yield event.plain_result(f"没有第 {idx} 号商品！『声望商店 {f['name']}』查看商品。")
                return
            g = goods[idx - 1]
            # 声望门槛拦截：不足 → 提示所需等级
            if pts < g["tier"]:
                need_name = _tier_name(g["tier"])
                yield event.plain_result(
                    f"🏛️ 声望不足！需要 {f['name']} 声望达到『{need_name}』({g['tier']})，当前 {tier}({pts})。\n"
                    f"💡 击杀当地怪物、完成当地任务可提升声望。"
                )
                return
            it = C.ITEMS[g["item"]]
            price = int(g.get("price", it["price"]))
            if player["gold"] < price:
                yield event.plain_result(f"金币不足！需要 {price} 金币。")
                return
            db.update_player(group_id, qq_id, gold=player["gold"] - price)
            itype = "材料" if g["item"] in C.MATERIALS else "消耗品"
            # v104 M09-P0 教训：全量拷贝定义字段（hot/effect 等），防丢字段
            db.add_item(group_id, qq_id, g["item"], {**it, "type": itype, "stackable": True, "price": price})
            yield event.plain_result(f"✅ 你用 {f['name']} 声望买到了【{it['name']}】！（花费 {price} 金币）")
            return
        # 商品列表
        lines = [f"🏛️ 【{f['icon']} {f['name']} · 声望商店】你的声望：{tier}({pts})", "━━━━━━━━━━━━"]
        for i, g in enumerate(goods, 1):
            it = C.ITEMS[g["item"]]
            need_name = _tier_name(g["tier"])
            price = int(g.get("price", it["price"]))
            if pts >= g["tier"]:
                mark, extra = "✅", f"—— {price} 金币"
            else:
                mark, extra = "🔒", f"—— 需『{need_name}』({g['tier']})"
            lines.append(f"{i:>2}. {mark} {it['name']}（{it['desc']}）{extra}")
        lines.append("")
        lines.append(f"💡 『声望商店 {f['name']} 购买 <序号>』购买商品（金币支付）")
        yield event.plain_result("\n".join(lines))

    # ================= v116 阵营国战最小闭环：四阵营选择/每日任务/贡献/商店/排行 =================
    # 数据在 game/data/factions.py（FACTION_CAMPS/FACTION_CAMP_SHOP/FACTION_CAMP_DAILY_TASKS）。
    # 玩家阵营存 players.faction；贡献/每日任务状态存 event_state 键 faction_camp_{gid}_{qq}
    # （JSON：contrib/tasks/done_today/done_total/join_ts），供成就判定（achievement_conds
    # 的 _faction_contribute 同款读法）与排行共用。全部在命令层闭环，不依赖 combat 击杀挂钩。
    def _camp_ctx(self, group_id, qq_id) -> dict:
        """读取玩家阵营数据（贡献 + 每日任务）。首次/无记录返回默认结构。"""
        raw = db.get_event_state(f"faction_camp_{group_id}_{qq_id}")
        data = {}
        if raw:
            try:
                data = json.loads(raw) if isinstance(raw, str) else {}
            except (ValueError, TypeError):
                data = {}
        data.setdefault("contrib", 0)
        data.setdefault("tasks", [])
        data.setdefault("done_today", 0)
        data.setdefault("done_total", 0)
        data.setdefault("join_ts", 0)
        data.setdefault("date", "")
        return data

    def _camp_save(self, group_id, qq_id, data: dict):
        db.set_event_state(f"faction_camp_{group_id}_{qq_id}", json.dumps(data, ensure_ascii=False))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?加入阵营(?:\s+\S+)?$")
    @require_player()

    async def camp_join(self, event: AstrMessageEvent):
        """v116：加入四大可选阵营（Lv.20 开放；可切换，缺省 7 天冷却（FACTION_CAMP_SWITCH_COOLDOWN））。

        用法：
          加入阵营           → 查看四大阵营列表 + 当前状态
          加入阵营 <编号>     → 加入对应阵营（如『加入阵营 1』）
        """
        from ..data.factions import FACTION_CAMPS, FACTION_CAMP_OPEN_LV, FACTION_CAMP_SWITCH_COOLDOWN
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        raw = self._strip_cmd(event, "加入阵营").strip()
        cur = (player.get("faction") or "").strip()
        camp_order = list(FACTION_CAMPS.keys())

        def _camp_line(i, cid):
            c = FACTION_CAMPS[cid]
            mark = "✅ 你在此" if cur == cid else ""
            return f"{i:>2}. {c['icon']} {c['name']}：{c['desc']}{mark and '　' + mark or ''}"

        # 列表/查看当前
        if not raw or raw == "查看":
            lines = ["🏛️ 【四大阵营 · 国战阵营选择】", "━━━━━━━━━━━━"]
            for i, cid in enumerate(camp_order, 1):
                lines.append(_camp_line(i, cid))
            lines.append("")
            if cur:
                ccur = FACTION_CAMPS[cur]
                lines.append(f"📛 你当前隶属：{ccur['icon']} {ccur['name']}")
                lines.append(f"💡 想改弦易辙？输入『加入阵营 <其他编号>』（切换有冷却 {FACTION_CAMP_SWITCH_COOLDOWN // 86400} 天）")
            else:
                lines.append(f"💡 Lv.{FACTION_CAMP_OPEN_LV} 起可选择阵营：『加入阵营 <编号>』")
                lines.append("   加入后解锁每日阵营任务与阵营商店。")
            yield event.plain_result("\n".join(lines))
            return

        # 加入指定阵营
        if not raw.isdigit():
            yield event.plain_result("格式：『加入阵营 <编号>』（输入『加入阵营』查看四大阵营列表）")
            return
        idx = int(raw)
        if idx < 1 or idx > len(camp_order):
            yield event.plain_result(f"没有第 {idx} 号阵营！输入『加入阵营』查看列表。")
            return
        target = camp_order[idx - 1]
        # 等级门槛
        lv = player.get("level") or 1
        if lv < FACTION_CAMP_OPEN_LV:
            yield event.plain_result(
                f"⚜️ 你需要达到 Lv.{FACTION_CAMP_OPEN_LV} 才能加入阵营！当前 Lv.{lv}。\n"
                f"💡 继续历练，国战之门终将为你敞开～")
            return
        # 已加入判定
        if cur == target:
            c = FACTION_CAMPS[target]
            yield event.plain_result(f"你已是 {c['icon']} {c['name']} 的成员，无需重复加入。")
            return
        # 切换冷却判定（有当前阵营时）
        if cur:
            data = self._camp_ctx(group_id, qq_id)
            spent = int(time.time()) - int(data.get("join_ts", 0))
            if spent < FACTION_CAMP_SWITCH_COOLDOWN:
                left = FACTION_CAMP_SWITCH_COOLDOWN - spent
                ccur = FACTION_CAMPS[cur]
                yield event.plain_result(
                    f"⏳ 你在 {ccur['icon']} {ccur['name']} 的军籍新立，还需 {left // 86400} 天才能换阵。\n"
                    f"💡 阵营切换冷却缺省 7 天（FACTION_CAMP_SWITCH_COOLDOWN 可配）。")
                return
        # 写入阵营
        db.update_player(group_id, qq_id, faction=target)
        data = self._camp_ctx(group_id, qq_id)
        data["join_ts"] = int(time.time())
        self._camp_save(group_id, qq_id, data)
        c = FACTION_CAMPS[target]
        # 成就判定：选择阵营（faction 非空）等
        C.check_achievements(group_id, qq_id)
        yield event.plain_result(
            f"⚔️ 你宣誓效忠【{c['icon']} {c['name']}】！({c['desc']})\n"
            f"━━━━━━━━━━━━\n"
            f"📜 现在可以『阵营任务』接取今日重任、『阵营商店』兑换军需物资！\n"
            f"{c['buff_text']}"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?阵营任务(?:\s+\S+)?$")
    @require_player()

    async def camp_task(self, event: AstrMessageEvent):
        """v116：每日阵营任务（收集型·主动交付闭环）。跨天自动重发，交付扣背包材料加贡献。

        用法：
          阵营任务           → 查看今日任务（跨天自动刷新分配）
          阵营任务 <序号>     → 交付对应任务（需背包有足够材料）
        说明：完成上限 FACTION_CAMP_DAILY_LIMIT（缺省 2）；击杀/Boss 型待 combat 挂钩二期。
        """
        from ..data.factions import FACTION_CAMPS, FACTION_CAMP_DAILY_TASKS, FACTION_CAMP_DAILY_LIMIT
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        cur = (player.get("faction") or "").strip()
        if not cur:
            yield event.plain_result("你还未加入任何阵营！先『加入阵营 <编号>』选择归宿，方能领受国战任务。")
            return
        c = FACTION_CAMPS[cur]
        raw = self._strip_cmd(event, "阵营任务").strip()

        # 取数据，跨天重置任务列表
        data = self._camp_ctx(group_id, qq_id)
        today = time.strftime("%Y-%m-%d")
        if data.get("date") != today:
            random.shuffle(FACTION_CAMP_DAILY_TASKS)
            data["tasks"] = [
                {"item": t["item"], "count": t["count"], "name": t["name"], "reward": t["reward"], "delivered": 0}
                for t in FACTION_CAMP_DAILY_TASKS[:FACTION_CAMP_DAILY_LIMIT]
            ]
            data["date"] = today
            data["done_today"] = 0
            self._camp_save(group_id, qq_id, data)

        tasks = data.get("tasks", [])
        # 查看
        if not raw:
            lines = [f"⚔️ 【{c['icon']} {c['name']} · 今日阵营任务】", "━━━━━━━━━━━━"]
            if not tasks:
                lines.append("今日暂无阵营任务。")
            else:
                for i, t in enumerate(tasks, 1):
                    have = db.count_item(group_id, qq_id, t["item"])
                    mark = "✅" if t["delivered"] >= t["count"] else "⏳"
                    need = t["count"]
                    lines.append(f"{i:>2}. {mark} {t['name']}：交付 {t['item']} ×{need} → 贡献 +{t['reward']}（背包 {have}）")
                lines.append(f"    本日已完成交付：{data.get('done_today', 0)}/{FACTION_CAMP_DAILY_LIMIT}")
            lines.append("")
            lines.append(f"ℹ️ 当前贡献：{data.get('contrib', 0)}　累计完成任务：{data.get('done_total', 0)} 次")
            lines.append(self._tip("faction_task"))
            yield event.plain_result("\n".join(lines))
            return

        # 交付
        if not raw.isdigit():
            yield event.plain_result("格式：『阵营任务 <序号>』交付；『阵营任务』查看今日任务。")
            return
        idx = int(raw)
        if idx < 1 or idx > len(tasks):
            yield event.plain_result(f"没有第 {idx} 号任务！『阵营任务』查看今日任务。")
            return
        t = tasks[idx - 1]
        if t["delivered"] >= t["count"]:
            yield event.plain_result(f"『{t['name']}』今日已完成！试试其他任务或『阵营任务』查看。")
            return
        # 每日完成上限
        if data.get("done_today", 0) >= FACTION_CAMP_DAILY_LIMIT:
            yield event.plain_result(
                f"📛 今日阵营任务完成数已达上限（{FACTION_CAMP_DAILY_LIMIT} 个），明天再来为国征战！")
            return
        # 扣背包材料（按收集型交付模式）
        have = db.count_item(group_id, qq_id, t["item"])
        if have < t["count"]:
            yield event.plain_result(
                f"📦 材料不足！『{t['name']}』需要 {t['item']} ×{t['count']}，你只有 {have} 个。\n"
                f"{self._tip('faction_task')}。")
            return
        db.remove_item(group_id, qq_id, t["item"], t["count"])
        t["delivered"] = t["count"]
        data["contrib"] = int(data.get("contrib", 0)) + t["reward"]
        data["done_today"] = int(data.get("done_today", 0)) + 1
        data["done_total"] = int(data.get("done_total", 0)) + 1
        self._camp_save(group_id, qq_id, data)
        # 成就判定：阵营贡献≥100/500（阵营先锋/大陆之柱）在此推进
        C.check_achievements(group_id, qq_id)
        yield event.plain_result(
            f"📜 你交付了『{t['name']}』（{t['item']} ×{t['count']}）！\n"
            f"🏅 阵营贡献 +{t['reward']}（当前 {data['contrib']}）\n"
            f"🎖️ 本日完成 {data['done_today']}/{FACTION_CAMP_DAILY_LIMIT}"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?阵营商店(?:\s+\S+)?$")
    @require_player()

    async def camp_shop(self, event: AstrMessageEvent):
        """v116：阵营商店——用阵营贡献兑换军需物资（不花金币）。

        用法：
          阵营商店                 → 列出全部商品（贡献门槛）
          阵营商店 <序号>           → 购买对应商品（扣贡献，物品入包）
        """
        from ..data.factions import FACTION_CAMPS, FACTION_CAMP_SHOP
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        cur = (player.get("faction") or "").strip()
        raw = self._strip_cmd(event, "阵营商店").strip()
        data = self._camp_ctx(group_id, qq_id)
        contrib = int(data.get("contrib", 0))
        head = "🏛️ 【阵营商店 · 军需物资】"
        if cur:
            c = FACTION_CAMPS[cur]
            head = f"🏛️ 【{c['icon']} {c['name']} · 阵营商店】你的贡献：{contrib}"
        curf = FACTION_CAMPS.get(cur) if cur else None
        if not cur:
            curf = None

        # 列表
        if not raw:
            lines = [head, "━━━━━━━━━━━━"]
            for i, g in enumerate(FACTION_CAMP_SHOP, 1):
                if contrib >= g["cost"]:
                    mark, extra = "✅", f"—— 花 {g['cost']} 贡献"
                else:
                    mark, extra = "🔒", f"—— 需 {g['cost']} 贡献"
                lines.append(f"{i:>2}. {mark} {g['name']} {extra}")
            lines.append("")
            if not cur:
                lines.append(self._tip("faction_shop"))
            else:
                lines.append(self._tip("faction_shop"))
            yield event.plain_result("\n".join(lines))
            return

        # 购买
        if not cur:
            yield event.plain_result("你还未加入任何阵营！先『加入阵营 <编号>』再兑换军需。")
            return
        if not raw.isdigit():
            yield event.plain_result("格式：『阵营商店 <序号>』购买；『阵营商店』查看列表。")
            return
        idx = int(raw)
        if idx < 1 or idx > len(FACTION_CAMP_SHOP):
            yield event.plain_result(f"没有第 {idx} 号商品！『阵营商店』查看列表。")
            return
        g = FACTION_CAMP_SHOP[idx - 1]
        if contrib < g["cost"]:
            yield event.plain_result(
                f"🏛️ 贡献不足！需 {g['cost']} 贡献，当前 {contrib}。\n"
                f"{self._tip('faction_task')}。")
            return
        # 扣贡献 + 发物品
        data["contrib"] = contrib - g["cost"]
        self._camp_save(group_id, qq_id, data)
        it = C.ITEMS.get(g["item"]) or {"name": g["name"], "price": 0, "desc": ""}
        itype = "材料" if g["item"] in C.MATERIALS else "消耗品"
        db.add_item(group_id, qq_id, g["item"], {**it, "type": itype, "stackable": True, "price": it.get("price", 0)})
        yield event.plain_result(
            f"🎁 你用 {g['cost']} 阵营贡献兑换了【{it.get('name', g['name'])}】！\n"
            f"📦 已收入背包，剩余贡献：{data['contrib']}"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?阵营排行(?:\s*|$)")
    @require_player()

    async def camp_rank(self, event: AstrMessageEvent):
        """v116：阵营排行——按阵营统计成员数与总贡献（从 players.faction + event_state contrib 聚合）。

        用法：阵营排行
        """
        from ..data.factions import FACTION_CAMPS
        group_id, qq_id = self._uid(event)
        # 全服玩家（players 全局，跨群共用；group_id 仅作贡献键前缀用）
        players = db.all_players(group_id)
        camp_contrib = {cid: 0 for cid in FACTION_CAMPS}
        camp_count = {cid: 0 for cid in FACTION_CAMPS}
        for p in players or []:
            fid = (p.get("faction") or "").strip()
            if not fid or fid not in FACTION_CAMPS:
                continue
            camp_count[fid] = camp_count.get(fid, 0) + 1
            try:
                raw = db.get_event_state(f"faction_camp_{group_id}_{p['qq_id']}")
                if raw:
                    d = json.loads(raw) if isinstance(raw, str) else {}
                    camp_contrib[fid] += int(d.get("contrib", 0) or 0)
            except (ValueError, TypeError):
                pass
        ranked = sorted(FACTION_CAMPS.keys(),
                        key=lambda cid: (camp_count.get(cid, 0), camp_contrib.get(cid, 0)),
                        reverse=True)
        lines = ["🏆 【阵营国战 · 排行】", "━━━━━━━━━━━━"]
        for i, cid in enumerate(ranked, 1):
            c = FACTION_CAMPS[cid]
            lines.append(
                f"{i}. {c['icon']} {c['name']}：成员 {camp_count.get(cid, 0)} 人 · 总贡献 {camp_contrib.get(cid, 0)}")
        lines.append("")
        lines.append(self._tip("faction"))
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?编年史(?:\s*|$)")
    @require_player()

    async def chronicle(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        c = random.choice(C.CHRONICLES)
        yield event.plain_result(
            f"📖 【{c['title']}】\n"
            f"━━━━━━━━━━━━\n"
            f"{c['text']}\n"
            f"━━━━━━━━━━━━\n"
            f"(奥兰迪亚编年史 · 输入『编年史』再听一段)"
        )
