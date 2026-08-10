# -*- coding: utf-8 -*-
"""《剑与魔法》命令层 - world（world）

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
from ..commands.base import CommandBase, no_prof_waiting


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
            _smith = "craft" in _sa_funcs or any(k in _sa_name for k in ("铁匠", "锻造", "军械", "工坊", "强化"))
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
        if mid in C.MINE_SPOTS:
            _mi = C.MINE_SPOTS[mid]
            _mi_sa = _mi.get("subarea", "") if isinstance(_mi, dict) else ""
            if not (_mi_sa and (sa_obj is None or sa_obj.get("id") != _mi_sa)):
                _mi_name = _mi.get("name", "矿脉") if isinstance(_mi, dict) else str(_mi)
                lines.append(f"⛏️ 矿脉·{_mi_name}(『挖掘』)")
        if cur_map.get("type") == "野外" and mid not in C.CAMP_SPOTS:
            lines.append("🌿 野地可采集(『采集』)")
        return lines

    def _map_scene(self, cur_map: dict, player: dict = None, sa_id_override: str = None) -> list:
        """当前子区域场景元素清单（POI 探索点 + PROPS 场景元素 + 副本内联 POI）。

        v87.13 从 _map_interactions 拆出：氛围/景物类，标题用「✨ 场景」。
        v87.13b sa_id_override：移动到达展示时目标子区域还没写进 player，显式传入落点子区域 id。
        """
        lines = []
        mid = cur_map.get("id", "")
        sa_id = sa_id_override or (player or {}).get("cur_subarea") or ""
        # v87 02 章 7.6：探索点 POI 显示（子区域挂载）
        if player:
            poi_ids = C.subarea_pois(mid, sa_id)
            for _pid in poi_ids:
                _p = C.POIS.get(_pid)
                if _p:
                    lines.append(f"{_p['icon']} {_p['name']}(『探索』有机会发现)")
        # v87.9 场景元素 PROPS 显示（子区域挂载，直接交互）
        # v87.11 支持专属名：挂载条目可为 (prop_id, 专属名) 元组
        if player:
            prop_ids = C.subarea_props(mid, sa_id)
            for _entry in prop_ids:
                _ppid, _label = C.prop_entry(_entry)
                _pp = C.PROPS.get(_ppid)
                if _pp:
                    _name = _label or _pp['name']
                    lines.append(f"{_pp['icon']} {_name}(『交互 {_name}』)")
        # v87.2 副本地图化：内联 POI（副本层自带 pois → 直接显示，『调查 <名称>』互动）
        for _p in (cur_map.get("pois") or []):
            if isinstance(_p, dict) and _p.get("name"):
                lines.append(f"{_p.get('icon', '❓')} {_p['name']}：{_p.get('hint', '')}(『调查 {_p['name']}』)")
        # v87.4 NPC 不再进场景（由地图面板「👥 这里的 NPC」统一显示，避免重复）
        return lines

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
    async def deed_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
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
            lines.append("💡 『买房 <编号>』购下心仪的地皮(一人一张)")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?买房(?:[\s\S]*)$")
    async def deed_buy(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
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
        db.update_player(group_id, qq_id, gold=player["gold"] - price, deed=pid)
        yield event.plain_result(
            f"🏠 恭喜置业！你买下了【{prop['name']}】(花费 {price} 金币)\n"
            f"『回家』入住，『地契』查看详情，『仓库』管理家当～"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?卖房(?:[\s\S]*)$")
    async def deed_sell(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        deed = player.get("deed", "") or ""
        if not deed or deed not in C.PROPERTIES:
            yield event.plain_result("你没有房产，卖不了～『地契』看看在售地皮！")
            return
        prop = C.PROPERTIES[deed]
        dlv = int(player.get("deed_lv", 1) or 1)
        refund_pct = C.HOUSE_REFUND.get(dlv, 0.5)
        refund = int(prop["price"] * refund_pct)
        db.update_player(group_id, qq_id, gold=player["gold"] + refund, deed="", deed_lv=1)
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
    @no_prof_waiting()
    async def go_home(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
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
    @no_prof_waiting()
    async def go_out(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
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
    @no_prof_waiting()
    async def visit_home(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
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
    async def home_storage(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
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
            lst.append({"key": found["key"], "data": found["data"], "count": 1})
            self._home_storage_save(group_id, qq_id, lst)
            db.remove_item(group_id, qq_id, found["key"], 1)
            yield event.plain_result(f"📦 已存入仓库：【{found['data'].get('name', raw)}】({len(lst)}/{hl['storage']})")
            return
        # 查看
        lst = self._home_storage_load(group_id, qq_id)
        if not lst:
            yield event.plain_result("仓库空空如也。『仓库 <物品名>』把背包里的宝贝存进来～")
            return
        lines = ["📦 【家中仓库】", "━━━━━━━━━━━━"]
        for i, it in enumerate(lst, 1):
            lines.append(f"{i:>2}. {it['data'].get('name', '?')} ×{it.get('count', 1)}")
        lines.append("💡 『仓库 <物品名>』存入，『取出 <编号>』取出")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?取出(?:[\s\S]*)$")
    async def home_storage_take(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        if not player.get("cur_map", "").startswith("home_"):
            yield event.plain_result("仓库在家里！先『回家』吧～")
            return
        raw = self._strip_cmd(event, "取出").strip()
        if not raw.isdigit():
            yield event.plain_result("格式：取出 <编号>！『仓库』查看～")
            return
        idx = int(raw)
        lst = self._home_storage_load(group_id, qq_id)
        if idx < 1 or idx > len(lst):
            yield event.plain_result(f"仓库里没有第 {idx} 件(共 {len(lst)} 件)！")
            return
        it = lst.pop(idx - 1)
        self._home_storage_save(group_id, qq_id, lst)
        db.add_item(group_id, qq_id, it["key"], it["data"], it.get("count", 1))
        yield event.plain_result(f"📦 取出【{it['data'].get('name', '?')}】，放入背包！")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:地图|位置|周围)(?:\s*|$)")

    async def map_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
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
        lines = [f"🗺️ 【{title}】", f"{sa_desc or cur_map['desc']}", "━━━━━━━━━━━━"]
        # v87.4 合并显示：子区域 + 相邻地图统一连续编号（『移动 <序号>』直接可用）
        # v87.16 空间连接：只列相邻可达子区域（subarea_links），序号与 move 解析一致
        sas = cur_map.get("subareas") or []
        neighbors = C.MAP_CONNECTIONS.get(cur, [])
        links = C.subarea_links(cur, cur_sa)
        shown = [(i + 1, next((s for s in sas if s["id"] == lid), None))
                 for i, lid in enumerate(links)]
        shown = [(i, s) for i, s in shown if s]
        if shown or neighbors:
            if sa_now:
                lines.append(f"📍 当前位置：{sa_now}")
            lines.append("📮 可前往：")
            for i, sa in shown:
                mark = " (你在这里)" if sa["id"] == cur_sa else ""
                lv_mark = f" Lv.{sa['lv']}" if sa.get("lv") else ""
                lines.append(f"  {i}. {sa['name']}{lv_mark}{mark}")
            exit_sa_id = C.map_exit_subarea(cur)
            at_exit = (not exit_sa_id) or (cur_sa == exit_sa_id)
            # v95.21 跨图连接只在出口子区域列出：普通场所（镇长办公处等）不显示野外/他镇目的地，
            # 出城必须走城门（镇郊/野外入口），符合"出城走城门"铁律
            if at_exit:
                for i, nid in enumerate(neighbors, len(links) + 1):
                    nm, want_sa = self._conn_target(nid)
                    sa_lbl = self._conn_subarea_name(nm, want_sa)
                    lock = " (🔒隐藏)" if nm.get("hidden") else ""
                    lines.append(f"  {i}. {nm['name']}{sa_lbl} Lv.{nm['lv']}{lock}")
        # v87.4 区块间统一空行分隔（不再叠分隔线）
        if lines and lines[-1]:
            lines.append("")
        # 此地设施 + 场景（v87.13 拆分：设施=功能入口，场景=氛围景物）
        fac = self._map_facilities(cur_map, player)
        if fac:
            if lines and lines[-1]:
                lines.append("")
            lines.append("🏪 此地设施：")
            for l in fac:
                lines.append(f"  {l}")
        scene = self._map_scene(cur_map, player)
        if scene:
            if lines and lines[-1]:
                lines.append("")
            lines.append("✨ 场景：")
            for l in scene:
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
                npcs.append(C.HIDDEN_NPCS[nid])
            elif nid in C.NPCS:
                npcs.append(C.NPCS[nid])
        if npcs:
            if lines and lines[-1]:
                lines.append("")
            lines.append("👥 这里的 NPC：")
            for n in npcs:
                lines.append(f"  {n['icon']}{n['name']}({n['title']})")
        # v66 此地玩家（含摆摊标记）
        mid = cur_map.get("id", "")
        here_players = [p for p in db.get_group_players(group_id).values() if p.get("cur_map") == mid]
        if here_players:
            stall_sellers = {str(s["seller"]) for s in db.market_list(group_id, mid)}
            if lines and lines[-1]:
                lines.append("")
            lines.append("👤 此地的玩家：")
            for p in here_players:
                stall_mark = " 🏪摆摊中" if str(p.get("qq_id")) in stall_sellers else ""
                lines.append(f"  {p['name']} Lv.{p['level']}{stall_mark}")
        # v86 子区域：怪物按当前子区域（无则回退地图级）
        mons = (cur_sa_obj.get("monsters") if cur_sa_obj else None)
        if mons is None:
            mons = cur_map.get("monsters", [])
        if mons:
            if lines and lines[-1]:
                lines.append("")
            base_lv = (cur_sa_obj.get("lv") if cur_sa_obj else None) or cur_map["lv"]
            lines.append(f"🐾 此地的怪物 (Lv.{base_lv}-{base_lv+2})：")
            for mid, name, role, lv, skills, drops in mons:
                mark = "👑" if role == "boss" else ("⭐" if role == "elite" else "")
                lines.append(f"  {mark}{name} Lv.{lv}")
        # 精英/Boss（子区域优先）
        elite = (cur_sa_obj.get("elite") if cur_sa_obj else None) or cur_map.get("elite")
        boss = (cur_sa_obj.get("boss") if cur_sa_obj else None) or cur_map.get("boss")
        if elite:
            lines.append(f"  ⭐ 精英：{elite[1]}")
        if boss:
            lines.append(f"  👑 Boss：{boss[1]}")
        if lines and lines[-1]:
            lines.append("")
        lines.append("输入『探索』遇怪，『前往 序号』前往他处，『找 <NPC名>』交谈")
        yield event.plain_result("\n".join(lines))

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
        if center.get("type") == "城镇":
            # v87.16 街道链：在广场想去链上目标（东大街/镇郊）时提示必经之路
            if cur_sa_id == center.get("id", ""):
                chain = [s for s in sas if s.get("type") in ("城镇街道", "城镇出口")]
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

    @filter.regex(r"^(?:\[At:\d+\]\s*)?前往(?:\s*|$)")
    @no_prof_waiting()

    async def move(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        dest = self._strip_cmd(event, "前往")
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        # v87.13 对话中禁止移动：多轮对话进行时先『对话 0』结束
        if db.get_talk_state(group_id, qq_id):
            yield event.plain_result("你还在和 NPC 交谈中！先『对话 0』结束谈话再动身吧。")
            return
        # v95.17 #146：战斗中禁止移动（与传送/回家/拜访一致，防战斗挂起跨图/被撞怪覆盖）
        if self._in_battle(group_id, qq_id):
            yield event.plain_result("⚔️ 你正在战斗中！输入『攻击』/『技能 <名称>』继续战斗，『防御』『逃跑』『用药』可选——先解决眼前的敌人再说移动。")
            return
        dest = dest.strip()
        # v94 体力：同图子区域移动免费（城内溜达不算赶路）；跨图移动扣 2、体力不足拒绝
        cur = player["cur_map"]
        cur_map = C.MAP_BY_ID.get(cur, {})
        cur_sas = cur_map.get("subareas") or []
        # v86 子区域：『移动 <序号>』→ 同图可前往列表序号优先（v87.14 空间连接），再邻居地图序号
        links = C.subarea_links(cur, player.get("cur_subarea") or "")
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
                yield event.plain_result(self._subarea_arrive(player, cur_map, sa))
                return
        # v86 子区域：『移动 <子区域名>』→ 同图子区域（免费切换）
        if dest:
            for sa in cur_sas:
                if dest in (sa["name"], sa["id"]):
                    if sa["id"] == player.get("cur_subarea"):
                        yield event.plain_result(f"你已经在这里了({cur_map['name']}·{sa['name']})～")
                        return
                    # v87.14 空间连接：同图只能移动到相邻子区域
                    links = C.subarea_links(cur, player.get("cur_subarea") or "")
                    if sa["id"] not in links:
                        yield event.plain_result(self._move_blocked_msg(cur_map, player, sa))
                        return
                    db.update_player(group_id, qq_id, cur_subarea=sa["id"])
                    yield event.plain_result(self._subarea_arrive(player, cur_map, sa))
                    return
        # 查找目标地图：优先序号（相对当前地图邻居列表），其次地图名/ID/旧区域别名
        target = None
        want_sa = None
        if dest.isdigit():
            neighbors = C.MAP_CONNECTIONS.get(cur, [])
            idx = int(dest)
            offset = len(links)
            if offset + 1 <= idx <= offset + len(neighbors):
                target, want_sa = self._conn_target(neighbors[idx - offset - 1])
            else:
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
        if target["id"] != cur and target["id"] not in nids:
            yield event.plain_result(f"无法直接前往{target['name']}！需要先到相邻地图。看看『地图』～")
            return
        # v84 红名限制（26 章三 第一档）：红名不能进入城镇安全区
        if self._is_redname(qq_id) and target.get("type") in ("城镇区域", "城镇外郊"):
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
        # v94 体力：跨图移动扣 1；体力 0 拒绝（同图移动免费已在上方处理）
        if self._stamina(player) < 1:
            yield event.plain_result(
                f"⚡ 你太累了，走不动了！(体力 {self._stamina(player)}/{self._stamina_max(player)})\n"
                "💡 恢复体力：野外营地『休息』/ 吃食物 / 旅店『住宿』，或等体力自然恢复(每10分钟+1)\n"
                "💡 也可以『传送』(已激活的方碑)或使用『回城卷轴』脱身～\n"
                "💡 新手建议：野外活动前先在城镇『商店』买点食物（烤肉串等），体力 0 才不会困在野外～"
            )
            return
        self._spend_stamina(group_id, qq_id, 1, player, "移动")
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
        nav_items = [f"{i}.{s['name']}" for i, s in t_shown]
        nav_items += [f"{i}.{self._conn_target(c)[0]['name']}"
                      for i, c in enumerate(neighbors, len(t_links) + 1)]
        if nav_items:
            nav = "\n\n📮 可前往：" + "  ".join(nav_items[:8])
        fac = self._map_facilities(target, player, first_sa["id"] if first_sa else "")
        fac_msg = ""
        if fac:
            fac_msg = "\n\n🏪 此地设施：\n  " + "\n  ".join(fac)
        scene = self._map_scene(target, player, first_sa["id"] if first_sa else "")
        scene_msg = ""
        if scene:
            scene_msg = "\n\n✨ 场景：\n  " + "\n  ".join(scene)
        inter_msg = fac_msg + scene_msg
        # v49 意见#4：移动撞怪（生物趋避利害——低级闯高级区容易撞怪，高级玩家威慑低级区）
        ambush = self._travel_ambush(player, target)
        if ambush:
            db.save_battle(group_id, qq_id, BT.Battle("monster", ambush, self._title_bonus(group_id, qq_id), player=player, pet=db.pet_get(qq_id)).to_state())
            self._lock_battle(group_id, qq_id)
            sub_line = f"\n📍 当前：{first_sa['name']}" if first_sa else ""
            # v87.13b 到达描述优先子区域 desc（与『地图』展示一致）
            arrive_desc = (first_sa.get("desc") if first_sa else "") or target.get("desc", "")
            yield event.plain_result(
                f"🚶 你来到了【{target['name']}】\n{arrive_desc}{sub_line}{lv_msg}{extra}{portal_msg}\n"
                f"━━━━━━━━━━━━\n"
                f"🛡️ 还没站稳，{ambush['name']} 就拦住了去路！\n"
                f"🐾【{ambush['name']}】Lv.{ambush['lv']} ❤️ {ambush['hp']}/{ambush['max_hp']}\n"
                f"━━━━━━━━━━━━\n"
                f"你的行动：『攻击』『技能 <名称>』『防御』『逃跑』"
            )
            return
        sub_line = f"\n📍 当前：{first_sa['name']}" if first_sa else ""
        # v87.13b 到达描述优先子区域 desc（与『地图』展示一致）
        arrive_desc = (first_sa.get("desc") if first_sa else "") or target.get("desc", "")
        # v87.3 必经之路：进入城镇时提示方向（从路图/野外进城）
        arrive_txt = f"🚶 你来到了【{target['name']}】"
        if target.get("type") == "城镇区域" and first_sa:
            arrive_txt = f"🚶 你从野外方向来到了【{target['name']}】{first_sa['name']}"
            sub_line = ""
        # v97.5 行为彩蛋规则：进入新地图
        _rule_txt = self._rule_fire("move_enter", group_id, qq_id, player, target)
        yield event.plain_result(
            f"{arrive_txt}\n{arrive_desc}{sub_line}{lv_msg}{extra}{portal_msg}{nav}{inter_msg}"
            + (f"\n{_rule_txt}" if _rule_txt else "")
        )

    def _subarea_arrive(self, player: dict, cur_map: dict, sa: dict) -> str:
        """v86 子区域到达展示：位置 + 描述 + 本子区域可互动 + 可前往子区域。

        v6 修复：与跨图移动一致，展示本子区域 PROPS/POI 场景元素
        （鱼鱼验收：移动展示必须与『地图』面板一致）。
        """
        lines = [
            f"🚶 你来到了【{cur_map['name']}·{sa['name']}】",
            f"{sa.get('desc', '')}",
            f"━━━━━━━━━━━━",
        ]
        # 本子区域 NPC
        npcs = [C.NPCS[nid] for nid in sa.get("npcs", []) if nid in C.NPCS]
        if npcs:
            lines.append("👥 这里的 NPC：")
            for n in npcs:
                lines.append(f"  {n['icon']}{n['name']}({n['title']})")
        # 功能提示
        funcs = sa.get("funcs") or []
        func_cn = {"shop": "商店", "heal": "住宿", "quest": "任务", "craft": "铁匠",
                   "stall": "摆摊", "auction": "拍卖", "fish": "垂钓", "lore": "听故事",
                   "apprentice": "副业", "enhance": "强化", "portal": "方碑"}
        show_funcs = [func_cn.get(f, f) for f in funcs if f not in ("explore", "instance")]
        # v95.25 #137：可互动提示与实际设施一致——funcs 有 shop/heal 但布尔未开时过滤
        if "shop" in funcs and not sa.get("shop"):
            show_funcs = [f for f in show_funcs if f != "商店"]
        if "heal" in funcs and not sa.get("healer"):
            show_funcs = [f for f in show_funcs if f != "住宿"]
        if show_funcs:
            lines.append(f"🏷️ 可互动：{'、'.join(show_funcs)}(『商店』『住宿』『找 <NPC名>』等)")
        # v6：设施 + 场景（与『地图』面板一致）
        fac = self._map_facilities(cur_map, player, sa["id"])
        if fac:
            lines.append("🏪 此地设施：")
            lines.append("  " + "  ".join(fac))
        scene = self._map_scene(cur_map, player, sa["id"])
        if scene:
            lines.append("✨ 场景：")
            lines.append("  " + "  ".join(scene))
        # 子区域间切换（同图免费，v87.14 只列相邻可达子区域，序号与地图面板/move 一致）
        sas = cur_map.get("subareas") or []
        links = C.subarea_links(cur_map.get("id", ""), sa["id"])
        others = [(i + 1, next((x for x in sas if x["id"] == lid), None))
                  for i, lid in enumerate(links)]
        others = [(i, x) for i, x in others if x]
        if others:
            lines.append("📮 可前往：")
            for i, x in others:
                lines.append(f"  {i}. {x['name']}")
        # v87.16 与地图面板一致：邻居地图从 len(links)+1 编号
        # v95.25 #133/#144/#148：非出口子区域不列跨图目的地（与『地图』一致），避免列出但被拦
        neighbors = C.MAP_CONNECTIONS.get(cur_map.get("id", ""), [])
        if neighbors:
            _exit_sa_id = C.map_exit_subarea(cur_map.get("id", ""))
            at_exit = (not _exit_sa_id) or (sa["id"] == _exit_sa_id)
            if at_exit:
                if not others:
                    lines.append("📮 可前往：")
                for i, nid in enumerate(neighbors, len(links) + 1):
                    nm, _ = self._conn_target(nid)
                    lines.append(f"  {i}. {nm['name']}")
            else:
                _exit_sa_name = next((s["name"] for s in sas if s["id"] == _exit_sa_id), "出口")
                lines.append(f"🧭 出城需先到『{_exit_sa_name}』")
        lines.append("")
        lines.append("💡 『前往 <子区域名/序号>』切换位置，『地图』查看详情")
        return "\n".join(lines)

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
        # v87.6 内容下沉子区域：从目标图子区域取怪（优先落点首个子区域）
        monsters = []
        for sa in (target_map.get("subareas") or []):
            if sa.get("monsters"):
                monsters = sa["monsters"]
                break
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

    @filter.regex(r"^(?:\[At:\d+\]\s*)?返回(?:\s*|$)")
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
        # v95.17 #146：战斗中禁止回城（与传送/移动一致）
        if self._in_battle(group_id, qq_id):
            yield event.plain_result("⚔️ 你正在战斗中！输入『攻击』/『技能 <名称>』继续战斗，『防御』『逃跑』『用药』可选——先解决眼前的敌人再说回城。")
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
            yield event.plain_result("🛡️ 城门口的守卫拦住了你：\"你身上沾着血腥味！红名期间禁止进入城镇！\"\n(红名期间不能进入安全区，去野外避避风头吧)")
            return
        if self._stamina(player) < 1:
            yield event.plain_result(
                f"⚡ 你太累了，走不动了！(体力 {self._stamina(player)}/{self._stamina_max(player)})\n"
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
        extra = ("\n\n" + "\n".join(quest_lines)) if quest_lines else ""
        yield event.plain_result(f"🧭 你一路疾行，回到了{target['name']}！(『地图』查看位置){extra}")


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
            for i, mid in enumerate(portals, 1):
                m = C.MAP_BY_ID.get(mid, {})
                p = C.PORTALS.get(mid, {})
                cost = C.portal_cost(m)
                name = p.get("name", mid) if p else mid
                icon = p.get("icon", "🌌") if p else "🌌"
                lines.append(f" {i}. {icon}{name}({m.get('name', '?')} · {cost} 金币)")
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
            cost = max(1, int(cost * (1 - disc)))
        if player["gold"] < cost:
            yield event.plain_result(f"传送需要 {cost} 金币(你只有 {player['gold']})！打怪攒点金币吧～")
            return
        # v86 子区域：传送落地目标图首个子区域
        tgt_sas = target.get("subareas") or []
        first_sa = tgt_sas[0] if tgt_sas else None
        db.update_player(group_id, qq_id, gold=player["gold"] - cost, cur_map=target["id"],
                         cur_subarea=first_sa["id"] if first_sa else "")
        db.add_visited(group_id, qq_id, target["id"])
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
            f"{target['desc']}{extra}"
        )

    def _update_explore_quests(self, group_id, qq_id, map_id):
        """到达子区域时检查 explore 型任务(主线和支线)"""
        lines = []
        quests = db.get_quests(group_id, qq_id)
        changed = False
        # 主线 explore
        main_id = quests.get("main_quest")
        if main_id:
            mq = next((q for q in C.MAIN_QUESTS if q["id"] == main_id), None)
            if mq and mq["objective"].get("explore") == map_id:
                player = self._player(group_id, qq_id)
                player["exp"] += mq["reward_exp"]
                player["gold"] += mq["reward_gold"]
                player["_title_bonus"] = self._title_bonus(group_id, qq_id)
                lv_logs, player = E.check_player_level_up(group_id, qq_id, player)
                db.update_player(group_id, qq_id, exp=player["exp"], gold=player["gold"], level=player["level"], hp=player["hp"], mp=player["mp"], max_hp=player["max_hp"], max_mp=player["max_mp"], skills=player["skills"], attr_pts=player.get("attr_pts", 0), skill_points=player.get("skill_points", 0), learned_skills=player.get("learned_skills", []))
                if lv_logs:
                    lines.append("")
                    lines += lv_logs
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

    async def quest_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        if self._is_redname(qq_id):
            yield event.plain_result("☠️ 你是红名！守卫不让你靠近任务板……(等红名消退再来)")
            return
        quests = db.get_quests(group_id, qq_id)
        lines = ["📜 【冒险日志】", "━━━━━━━━━━━━"]
        # 主线
        main_id = quests.get("main_quest")
        if main_id:
            mq = next((q for q in C.MAIN_QUESTS if q["id"] == main_id), None)
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
                    if obj.get("kill"):
                        cur = prog.get(obj["kill"], 0)
                        lines.append(f"  进度：{cur}/{obj['count']}")
                    elif obj.get("collect"):
                        cur = prog.get(obj["collect"], 0)
                        lines.append(f"  收集：{cur}/{obj['count']}")
                    elif obj.get("explore"):
                        lines.append(f"  前往：{C.MAP_BY_ID.get(obj['explore'], {}).get('name', '？')}")
                    elif obj.get("talk"):
                        npc = C.NPCS.get(obj["talk"], {}).get("name", "？")
                        lines.append(f"  交谈：与 {npc} 对话")
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
                giver = (C.NPCS.get(sqd["giver"]) or C.ALL_WILD.get(sqd["giver"]) or {}).get("name", "？")
                st = sq.get("status", "active")
                obj = sqd["objective"]
                # v95.12：已交付支线显示已完成（不占可交付位）
                if st == "done":
                    lines.append(f"{i:>2}. 『{sqd['name']}』[✅ 已完成]")
                    continue
                # 收集型：实时按背包材料判断
                if obj.get("collect"):
                    have = db.count_item(group_id, qq_id, obj["collect"])
                    need = obj.get("collect_count", obj["count"])
                    if have >= need:
                        lines.append(f"{i:>2}. 『{sqd['name']}』{sqd['desc']} [✅ 可交]")
                        lines.append(f"    材料已齐！回去找 {giver} {self._deliver_hint(sqd['giver'])}")
                    else:
                        lines.append(f"{i:>2}. 『{sqd['name']}』{sqd['desc']} [⏳]")
                        lines.append(f"    收集：{obj['collect']} {have}/{need}")
                    continue
                mark = "✅ 可交" if st == "ready" else "⏳"
                lines.append(f"{i:>2}. 『{sqd['name']}』{sqd['desc']} [{mark}]")
                if st == "ready":
                    lines.append(f"    回去找 {giver} {self._deliver_hint(sqd['giver'])}")
            if pages > 1:
                lines.append(f"💡 『任务 {page+1}』看下一页(共 {pages} 页)")
        else:
            lines.append("")
            lines.append("【支线】暂无——找镇上的 NPC 聊聊可能有意外收获")
        # 每日
        daily = quests.get("daily", {})
        if daily:
            lines.append("")
            lines.append("【每日】")
            for i, (dkey, dq) in enumerate(daily.items(), 1):
                if dkey == "_date":  # v94 跨天字段，跳过
                    continue
                dobj = dq["objective"]
                need = dobj.get("kill_any", dobj.get("kill_elite", dobj.get("kill_boss", dobj.get("count", 99))))
                lines.append(f"{i:>2}. 『{dq['name']}』{dq['desc']} ({dq.get('progress',0)}/{need})")
        else:
            lines.append("")
            lines.append("【每日】今日任务已完成，明天再来！")
        lines.append("")
        lines.append("💡 输入『每日』领取今日任务，『找 <NPC名>』接取任务")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?接取(?:\s*|$)")

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
                if sq["id"] in (quests.get("side") or {}):
                    continue
                if raw in (sq["name"],):
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
                        lines = self._offer_side_quests(group_id, qq_id, sq["giver"], {"map": player["cur_map"], "gender": ""})
                        yield event.plain_result("\n".join(lines))
                        return
                    npc = C.NPCS.get(sq["giver"]) or C.ALL_WILD.get(sq["giver"]) or {}
                    if npc.get("map") == player["cur_map"]:
                        lines = self._offer_side_quests(group_id, qq_id, sq["giver"], npc)
                        yield event.plain_result("\n".join(lines))
                        return
                    giver_map = C.MAP_BY_ID.get(npc.get("map", ""), {}).get("name", "？")
                    yield event.plain_result(f"支线『{sq['name']}』由 {npc.get('name', '？')}(在{giver_map}) 发布，去找他对话接取～")
                    return
        # 无参数 → 列出当前地图可接任务（主线 pending + 未接支线）
        available = []
        if mq and quests.get("main_status") == "pending":
            giver = C.NPCS.get(mq["giver"]) or C.ALL_WILD.get(mq["giver"]) or {}
            if giver.get("map") == player["cur_map"]:
                available.append(f"📜 主线『{mq['name']}』（{giver.get('name', '？')}发布）")
        for sq in C.SIDE_QUESTS:
            if sq["id"] in (quests.get("side") or {}):
                continue
            npc = C.NPCS.get(sq["giver"]) or C.ALL_WILD.get(sq["giver"]) or {}
            if npc.get("map") == player["cur_map"]:
                available.append(f"📜 支线『{sq['name']}』（{npc.get('name', '？')}发布）")
        if available:
            lines = ["📜 【可接取任务】", "━━━━━━━━━━━━"]
            lines += [f"{i:>2}. {a}" for i, a in enumerate(available, 1)]
            lines.append("💡 输入『接取 <任务名>』接取指定任务～")
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


    @filter.regex(r"^(?:\[At:\d+\]\s*)?每日(?:\s*|$)")

    async def daily(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        if self._is_redname(qq_id):
            yield event.plain_result("☠️ 你是红名！悬赏板上的任务都被守卫收走了……(等红名消退再来)")
            return
        quests = db.get_quests(group_id, qq_id)
        # v94 跨天清理：昨天的任务过期，先清空再判断（旧存档无 _date 视为过期）
        if db.expire_daily(quests):
            db.save_quests(group_id, qq_id, quests)
        if quests.get("daily"):
            yield event.plain_result("你已经有每日任务了！输入『任务』查看～")
            return
        # v94 随机抽 2 个每日任务（按等级过滤：低等级不抽打不到的任务）
        pool = [dq for dq in C.DAILY_QUESTS if self._daily_pool(player, dq)]
        chosen = random.sample(pool, min(2, len(pool)))
        import datetime as _dt
        daily = {"_date": _dt.date.today().isoformat()}
        for i, dq in enumerate(chosen):
            daily[f"d{i}"] = {"name": dq["name"], "desc": dq["desc"], "objective": dq["objective"], "reward_exp": dq["reward_exp"], "reward_gold": dq["reward_gold"], "progress": 0}
        quests["daily"] = daily
        db.save_quests(group_id, qq_id, quests)
        lines = ["📜 今日任务已发布！", "━━━━━━━━━━━━"]
        for i, (dkey, dq) in enumerate(daily.items(), 1):
            if dkey == "_date":
                continue
            lines.append(f"{i:>2}. 『{dq['name']}』{dq['desc']}")
            lines.append(f"    奖励：经验 +{dq['reward_exp']} 金币 +{dq['reward_gold']}")
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
            lines.append("💡 『购入 <编号>』买下，标 🔄 的用『换 <编号> <物品名>』交换")
        else:
            lines.append("🏪 铺面空着——房主可以『摆摊 <物品> [价格]』开张(不带价格 = 换摊)！")
        # 仓库（自己的家）
        if is_mine:
            storage = self._home_storage_load(group_id, qq_id)
            dlv = int(owner.get("deed_lv", 1) or 1)
            hl = C.HOUSE_LEVELS.get(dlv, C.HOUSE_LEVELS[1])
            lines.append(f"📦 家中仓库：{len(storage)}/{hl['storage']} 件(『仓库』管理)")
            if hl.get("stall_slots"):
                lines.append(f"🏪 铺面挂机位：{hl['stall_slots']} 个(『摆摊 <物品> [价格]』开张)")
        lines.append("━━━━━━━━━━━━")
        lines.append("💡 『出门』回到城镇")
        return "\n".join(lines)

    def _current_npcs(self, player):
        """v86 子区域：当前所在位置可交互的 NPC 列表(子区域优先，回退地图级)。"""
        cur_map = player["cur_map"]
        m = C.MAP_BY_ID.get(cur_map, {})
        sa_id = player.get("cur_subarea") or ""
        for sa in (m.get("subareas") or []):
            if sa["id"] == sa_id:
                npc_ids = sa.get("npcs") or []
                return [C.NPCS[nid] for nid in npc_ids if nid in C.NPCS]
        return [C.NPCS[nid] for nid in m.get("npcs", []) if nid in C.NPCS]

    def _find_npc_in_map(self, player, name_key):
        """在当前地图找 NPC(子区域优先，回退地图级)，返回 (npc_id, npc_dict) 或 (None, None)"""
        cur_map = player["cur_map"]
        m = C.MAP_BY_ID.get(cur_map, {})
        sa_id = player.get("cur_subarea") or ""
        # 子区域 NPC 优先
        for sa in (m.get("subareas") or []):
            if sa["id"] == sa_id:
                for nid in sa.get("npcs", []):
                    npc = C.NPCS.get(nid)
                    if npc and (name_key in npc["name"] or name_key in nid):
                        return nid, npc
                break
        # 地图级 NPC（含其他子区域）
        for nid in m.get("npcs", []):
            npc = C.NPCS.get(nid)
            if npc and (name_key in npc["name"] or name_key in nid):
                return nid, npc
        return None, None

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
        """v95.8 #51：当前地图没找到 NPC 时，全局搜位置给方向提示；找不到返回 None"""
        cur = player["cur_map"]
        hits = []
        for nid, npc in C.NPCS.items():
            if name_key in (npc.get("name") or "") or name_key in nid:
                hits.append((nid, npc))
        for nid, wnpc in C.ALL_WILD.items():
            if name_key in (wnpc.get("name") or "") or name_key in nid:
                hits.append((nid, wnpc))
        if not hits:
            return None
        locs = []
        for nid, npc in hits:
            m_id = npc.get("map") or ""
            m = C.MAP_BY_ID.get(m_id, {})
            m_name = m.get("name", m_id or "未知之地")
            sa_name = ""
            for sa in (m.get("subareas") or []):
                if nid in (sa.get("npcs") or []):
                    sa_name = sa.get("name", "")
                    break
            if sa_name:
                locs.append(f"{m_name}·{sa_name}")
            else:
                locs.append(m_name)
        uniq = list(dict.fromkeys(locs))
        in_here = cur in {npc.get("map") for _, npc in hits}
        # v95.25 #135：前缀明确"在/不在你所在的地图"，不再用误导性的"你所在的地图的…"
        if in_here:
            return f"🧭 『{name_key}』就在你所在的「{'、'.join(uniq)}」一带。输入『地图』查看路线，到了地方用『找』定位～"
        return f"🧭 『{name_key}』在「{'、'.join(uniq)}」一带（你现在不在这里）。输入『地图』查看路线，到了地方用『找』定位～"

    def _npc_dialogue(self, group_id, qq_id, npc_id, npc):
        """按主线进度返回 NPC 对话(主线完成后不再重复初始台词)"""
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
        if st == "pending":
            quests["main_status"] = "active"
            quests["main_progress"] = {}
            # talk 型任务：与发布 NPC 交谈即达成目标（对话即完成）
            obj = mq["objective"]
            if obj.get("talk") and obj["talk"] == npc_id:
                quests["main_status"] = "ready"
                quests["main_progress"] = {obj["talk"]: 1}
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
            player = self._player(group_id, qq_id)
            player["exp"] += mq["reward_exp"]
            player["gold"] += mq["reward_gold"]
            player["_title_bonus"] = self._title_bonus(group_id, qq_id)
            lv_logs, player = E.check_player_level_up(group_id, qq_id, player)
            db.update_player(group_id, qq_id, exp=player["exp"], gold=player["gold"], level=player["level"], hp=player["hp"], mp=player["mp"], max_hp=player["max_hp"], max_mp=player["max_mp"], skills=player["skills"], attr_pts=player.get("attr_pts", 0), skill_points=player.get("skill_points", 0), learned_skills=player.get("learned_skills", []))
            if lv_logs:
                lines.append("")
                lines += lv_logs
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
                lines.append("🎊 恭喜！你完成了全部主线任务，成为奥兰迪亚的传说！")
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
        if obj.get("find"):
            # v97.1 告示委托：在指定地图探索概率找到目标
            return f"在 {C.MAP_BY_ID.get(obj.get('map', ''), {}).get('name', '？')} 寻找 {obj['find']}(探索有概率遇到)"
        if obj.get("talk"):
            npc = C.NPCS.get(obj["talk"], {})
            return f"与 {npc.get('name', '？')} 交谈"
        return "？"

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

    async def time_cmd(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        cur = player["cur_map"]
        summary = C.time_weather_summary(cur)
        cur_map = C.MAP_BY_ID.get(cur, {})
        lines = [
            f"🕰️ 【时间】{summary}",
            f"📍 你在【{cur_map.get('name', '未知区域')}】",
            "━━━━━━━━━━━━",
        ]
        hints = C.nearby_hints(group_id, qq_id, player, cur)
        if hints:
            lines.append("🍃 附近似乎有人影出没：")
            for nid, npc in hints[:5]:
                lines.append(f"  {npc['icon']}{npc['name']}({self._wild_cond_label(npc)})")
            lines.append("💡 『探索』碰碰运气，『找 <名字>』直接寻找")
        else:
            lines.append("🍃 附近没有特别的气息……")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?见闻录(?:\s*|$)")

    async def wild_notes(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
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

    @filter.regex(r"^(?:\[At:\d+\]\s*)?找(?:\s*|$)")

    async def find_npc(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        name_key = self._strip_cmd(event, "找")
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        if self._is_redname(qq_id):
            yield event.plain_result("☠️ 你是红名！城里的 NPC 都躲着你走……(等红名消退再来)")
            return
        name_key = name_key.strip()
        if not name_key:
            cur_m = player["cur_map"]
            if cur_m.startswith("home_"):
                yield event.plain_result("家里没有 NPC 可以交谈～『出门』去镇上找人吧！")
                return
            npcs = self._current_npcs(player)
            if not npcs:
                yield event.plain_result("这里没有 NPC。输入『地图』看看哪里有 NPC～")
            else:
                lines = ["👥 这里的 NPC："]
                for i, n in enumerate(npcs, 1):
                    lines.append(f"{i:>2}. {n['icon']}{n['name']}({n['title']})")
                lines.append("💡 输入『找 <名字>』或『找 <序号>』交谈")
                yield event.plain_result("\n".join(lines))
            return
        # 序号找：『找 1』→ 当前地图第 1 个 NPC
        if name_key.isdigit():
            if player["cur_map"].startswith("home_"):
                yield event.plain_result("家里没有 NPC 可以交谈～『出门』去镇上找人吧！")
                return
            npcs = self._current_npcs(player)
            idx = int(name_key)
            if idx < 1 or idx > len(npcs):
                yield event.plain_result(f"这里没有第 {idx} 位 NPC(共 {len(npcs)} 位)！『找』查看列表～")
                return
            npc = npcs[idx - 1]
            npc_id = next((nid for nid, n in C.NPCS.items() if n is npc), None)
        else:
            npc_id, npc = self._find_npc_in_map(player, name_key)
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
                for _sq in C.SIDE_QUESTS:
                    if _sq["giver"] != npc_id or _sq["id"] in _side:
                        continue
                    lines.append(f"📜 支线『{_sq['name']}』可接取——和{_ta}对话接下吧～")
                    break
                for _sid, _sq in list(_side.items()):
                    _sqd = next((q for q in C.SIDE_QUESTS if q["id"] == _sid), None)
                    if _sqd and _sqd["giver"] == npc_id and _sq.get("status") == "ready":
                        lines.append(f"✅ 支线『{_sqd['name']}』已完成！和{_ta}对话交付～")
                        break
            else:
                # 无对话树的 NPC：保持自动接取/交付（对话选项不存在，指令与提示兜底）
                lines += self._take_main_quest(group_id, qq_id, npc_id, npc)
                lines += self._offer_side_quests(group_id, qq_id, npc_id, npc)
        if "shop" in funcs:
            lines.append("🏪 输入『商店』可以买东西")
        if "trade" in funcs:
            _ta = "她" if npc.get("gender") == "女" else "他"  # v95 #141：代词跟随 NPC 性别
            lines.append(f"🧭 输入『商店』看看{_ta}的货（行商有独家补给）")
        if "heal" in funcs:
            lines.append("🏨 输入『住宿』恢复满血(需要金币)")
        if "daily" in funcs:
            lines.append("📜 输入『每日』领取今日悬赏")
        if "lore" in funcs:
            ta = "她" if npc.get("gender") == "女" else "他"
            lines.append(f"🎻 {ta}给你讲了一个关于大陆的传说……(输入『任务』看看支线)")
        if "teach" in funcs:
            lines.append("🗡️ 输入『对话 <序号>』继续交谈，这位前辈或许能指点你一二")
        if "ency" in funcs:
            lines.append("📚 输入『百科 <材料/怪物/地图名>』查询世界知识(镇长藏书)")
        yield event.plain_result("\n".join(lines))

    # ---------------- v87.9 场景元素交互 ----------------

    @filter.regex(r"^(?:\[At:\d+\]\s*)?交互(?:\s*|$)")
    @no_prof_waiting()

    async def interact_prop(self, event: AstrMessageEvent):
        """与当前子区域的场景元素(喷泉/雕像/告示板等)交互。纯氛围 + 极小彩蛋。"""
        group_id, qq_id = self._uid(event)
        name_key = self._strip_cmd(event, "交互").strip()
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        if self._is_redname(qq_id):
            yield event.plain_result("☠️ 你是红名！城里的元素都绕着你走……(等红名消退再来)")
            return
        cur = player["cur_map"]
        cur_map = C.MAP_BY_ID.get(cur, {})
        sa_id = player.get("cur_subarea") or ""
        prop_ids = C.subarea_props(cur, sa_id)
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
            lines.append("💡 输入『交互 <名称>』或『交互 <序号>』互动")
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
        if pid == "notice_board":
            quests = db.get_quests(group_id, qq_id)
            side = quests.get("side") or {}
            board_lines = []
            for sq in C.SIDE_QUESTS:
                if not sq.get("board"):
                    continue
                if sq["id"] in side:
                    continue
                board_lines.append(f"  📜 {sq['name']}：{sq['desc']}")
            if board_lines:
                lines.append("━━━━━━━━━━━━")
                lines.append("🧾 【告示委托】")
                lines += board_lines
                lines.append("💡 输入『接取 <委托名>』接下委托～")
            else:
                done = any(
                    side.get(sq["id"], {}).get("status") == "done"
                    for sq in C.SIDE_QUESTS if sq.get("board")
                )
                if done:
                    lines.append("(你已处理完这里的委托，告示板又恢复了平静。)")
        # 极小彩蛋（纯趣味，不破坏平衡）
        # v87.12 专属元素带小效果：dict effect = {"type": "material"/"heal", "daily": True}
        import datetime as _dt
        eff = pp.get("effect")
        if eff == "wish":
            if random.random() < C.MOVE_ENCOUNTER_CHANCE:
                gold = random.randint(1, 5)
                db.update_player(group_id, qq_id, gold=player["gold"] + gold)
                lines.append(f"💰 井底传来一声轻响——你低头一看，水面上漂着 {gold} 枚铜币，像是井的谢礼。")
        elif eff == "refresh":
            lines.append("💧 泉水入喉，神清气爽。旅途的疲惫仿佛也被这淙淙水声冲淡了一些。")
        elif isinstance(eff, dict) and eff.get("daily"):
            # 每日 1 次（按元素实例：地图:子区域:prop_id 独立计数，防刷）
            today = _dt.date.today().isoformat()
            use_key = f"{cur}:{sa_id}:{pid}"
            used = db.get_props_use(group_id, qq_id)
            if used.get(use_key) == today:
                lines.append("⏳ 今天已经在这里翻找过了……明天再来碰碰运气吧。")
            else:
                etype = eff.get("type")
                if etype == "material":
                    pool = eff.get("pool") or []
                    if pool:
                        mid = random.choice(pool)
                        mname = C.display("materials", mid)
                        db.add_item(group_id, qq_id, mid, {
                            "name": mname, "type": "材料", "stackable": True,
                            "price": C.MATERIALS[mid]["price"],
                        }, 1)
                        db.mark_props_use(group_id, qq_id, use_key, today)
                        lines.append(f"🎒 {eff.get('found_text', '你发现')}【{mname}】×1！")
                elif etype == "heal":
                    pct = float(eff.get("pct", 0.1))
                    heal = max(1, int((player.get("max_hp", 1) - player.get("hp", 0)) * pct))
                    if heal <= 0:
                        lines.append("🔥 暖意融融，但你精神饱满，用不上这份治愈～(明天再来也一样暖)")
                    else:
                        db.update_player(group_id, qq_id, hp=player["hp"] + heal)
                        db.mark_props_use(group_id, qq_id, use_key, today)
                        lines.append(f"🔥 {eff.get('found_text', '暖意袭来')}——恢复 ❤️ {heal} 点生命({player['hp'] + heal}/{player.get('max_hp', 1)})！")
        yield event.plain_result("\n".join(lines))

    # ---------------- v65 NPC 多轮对话 ----------------

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
        }

    def _render_talk_node(self, npc, dlg, node, ctx) -> list:
        """渲染一个对话节点：头像 + 台词 + 可见选项"""
        lines = [f"{npc['icon']}【{npc['name']}】{npc['title']}",
                 f"“{node.get('text', '……')}”"]
        opts = C.visible_options(dlg, node, ctx)
        if opts:
            lines.append("━━━━━━━━━━━━")
            for i, opt in enumerate(opts, 1):
                lines.append(f"{i}. {opt['text']}")
            lines.append("0. 结束对话")
            lines.append("💡 『对话 <序号>』继续交谈")
        return lines

    def _talk_quest_progress(self, group_id, qq_id, npc_id) -> list:
        """v95.11：talk 型主线与目标 NPC 对话即达成（active 空进度遗留态 → ready）。
        覆盖 v95.9 对话化之前接取、或接取瞬间未置 ready 的存量档，返回通知行。"""
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
        if obj.get("talk") != npc_id:
            return []
        quests["main_status"] = "ready"
        quests["main_progress"] = {npc_id: 1}
        db.save_quests(group_id, qq_id, quests)
        return ["✨ 交谈完成！再与这位 NPC 对话即可交付任务。"]

    # ---------------- v95.23 职业就职 / 导师转职 ----------------

    def _do_join_class(self, group_id, qq_id, player, new_cls):
        """行会就职：见习冒险者 → 基础职业。
        属性按新职业重算（base+成长×等级+种族，自由点保留），赠送基础技能书（职业 Lv.1 技能）。
        返回通知行列表。"""
        lines = []
        if player.get("class_name") != "cls_novice":
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
                         max_hp=st["hp"], max_mp=st["mp"], hp=st["hp"], mp=st["mp"],
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
        lines.append("💡 升级获得技能点，『技能学习 <技能名>』学更多技能")
        lines.append("💡 各城职业导师可学进阶技能；Lv.30/60/90 找导师转职")
        return lines

    def _do_evolve_via_npc(self, group_id, qq_id, player, next_tier, path):
        """导师转职：Lv.30/60/90 找对应职业导师对话转职（同步版，返回通知行）。"""
        lines = []
        cls = C.CLASSES.get(player.get("class_name", ""), {})
        cur_tier = player.get("class_tier", 0)
        need_lv = {1: 30, 2: 60, 3: 90}.get(next_tier)
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
        fields = {"class_tier": next_tier}
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

    def _apply_talk_action(self, group_id, qq_id, player, npc_id, action) -> list:
        """执行选项动作(涉及 DB 的副作用统一在这落地)，返回通知行"""
        lines = []
        if not action:
            return lines
        if "set_flag" in action:
            db.set_talk_flag(group_id, qq_id, npc_id, action["set_flag"])
        if "give_gold" in action:
            gold = int(action["give_gold"])
            db.update_player(group_id, qq_id, gold=(player.get("gold", 0) or 0) + gold)
            lines.append(f"💰 获得金币 ×{gold}")
        if "give_exp" in action:
            exp = int(action["give_exp"])
            db.update_player(group_id, qq_id, exp=(player.get("exp", 0) or 0) + exp)
            lines.append(f"✨ 获得经验 +{exp}")
        if "give_item" in action:
            item = action["give_item"]
            key = item.get("key", "")
            count = int(item.get("count", 1))
            if key:
                db.add_item(group_id, qq_id, key, {}, count)
                lines.append(f"🎒 获得 {key} ×{count}")
        if action.get("open_shop"):
            lines.append("🏪 输入『商店』可以买东西")
        if action.get("hint"):
            lines.append(action["hint"])
        # ---- v95.9 对话式任务接取/交付（取代『交任务』『接取任务』指令的引导）----
        if action.get("quest_take"):
            # 主线：pending → 接取；ready → 交付领奖（_take_main_quest 自动分流）
            npc = C.NPCS.get(npc_id) or C.ALL_WILD.get(npc_id) or {}
            if npc:
                lines += self._take_main_quest(group_id, qq_id, npc_id, npc)
        if action.get("side_take"):
            # 支线：交付该 NPC 名下第一个可交支线
            quests = db.get_quests(group_id, qq_id)
            for sid, sq in list((quests.get("side") or {}).items()):
                sqd = next((q for q in C.SIDE_QUESTS if q["id"] == sid), None)
                if not sqd or sqd.get("giver") != npc_id:
                    continue
                if sq.get("status") == "done":  # v95.12：已交付支线不再提示/交付
                    continue
                obj = sqd.get("objective", {})
                if obj.get("collect"):
                    if db.count_item(group_id, qq_id, obj["collect"]) >= obj.get("count", 1):
                        lines += self._complete_side_quest(group_id, qq_id, sid)
                        break
                elif sq.get("status") == "ready":
                    lines += self._complete_side_quest(group_id, qq_id, sid)
                    break
        # ---- v81 导师进修动作 ----
        if "consume_item" in action:
            ci = action["consume_item"]
            key = ci.get("item", "")
            count = int(ci.get("count", 1))
            if key:
                db.remove_item(group_id, qq_id, key, count)
                lines.append(f"🎒 交出 {key} ×{count}")
        if "unlock_prof" in action:
            prof = action["unlock_prof"]
            appr = list(player.get("apprentices", []))
            if prof in appr:
                lines.append(f"你已经拜过{db.PROF_FIELDS.get(prof, prof)}的导师了。")
            else:
                ok, act_msg = self._prof_active_check(group_id, qq_id, prof)
                if not ok:
                    lines.append(act_msg)
                else:
                    appr.append(prof)
                    db.update_player(group_id, qq_id, apprentices=appr)
                    # 入门礼：副业经验（unlock_prof 配套 give_prof_exp 时由命令层统一给）
                    exp = action.get("give_prof_exp")
                    if exp:
                        lv, _ = db.add_prof_exp(group_id, qq_id, prof, int(exp))
                        lines.append(f"🎓 拜师成功！解锁副业「{db.PROF_FIELDS.get(prof, prof)}」(副业经验 +{exp})")
                    else:
                        lines.append(f"🎓 拜师成功！解锁副业「{db.PROF_FIELDS.get(prof, prof)}」")
                    lines.append("💡 『副业』查看你的生活职业面板")
        # ---- v95.23 职业就职/进阶/转职动作 ----
        if "unlock_class" in action:
            # 行会就职：见习冒险者 → 基础职业（属性按新职业重算 + 初始技能）
            new_cls = action["unlock_class"]
            lines += self._do_join_class(group_id, qq_id, player, new_cls)
        if "tutor_skill" in action:
            # 导师进阶技能教学：等级门槛 + 金币学费 → 直接学会（不耗技能点）
            ts = action["tutor_skill"]
            sk_id = ts.get("skill", "")
            cost = int(ts.get("cost", 0))
            need_lv = int(ts.get("need_lv", 1))
            info = E.skill_info(player.get("class_name", ""), sk_id)
            if not info:
                lines.append("这位导师似乎还没准备好教你……")
            elif player.get("level", 0) < need_lv:
                lines.append(f"导师摇摇头：这套本事要 Lv.{need_lv} 才学得动，你才 Lv.{player.get('level', 1)}，先练练基本功。")
            elif (player.get("gold", 0) or 0) < cost:
                lines.append(f"导师伸出三根手指：学费 {cost} 金币，少一个子儿都不行。(你现在有 {player.get('gold', 0)} 金币)")
            else:
                learned = list(player.get("learned_skills", []))
                sname = info.get("name", sk_id)
                if C.resolve("skills", sname) in [C.resolve("skills", s) for s in learned if s]:
                    lines.append(f"『{sname}』你已经学会了，再多练练吧。")
                else:
                    db.update_player(group_id, qq_id, gold=(player.get("gold", 0) or 0) - cost,
                                     learned_skills=learned + [sname])
                    lines.append(f"💰 支付学费 {cost} 金币")
                    lines.append(f"✨ 导师悉心传授，你学会了进阶技能『{sname}』！")
                    lines.append(f"「{info['desc']}」")
                    lines.append("💡 记得『设置技能 <槽位> <技能名>』放入技能栏～")
        if "evolve_class" in action:
            # 导师转职：Lv.30/60/90 找对应职业导师对话转职
            ev = action["evolve_class"]
            next_tier = int(ev.get("tier", 1))
            path = int(ev.get("path", 1))
            lines += self._do_evolve_via_npc(group_id, qq_id, player, next_tier, path)
        return lines

    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:对话|继续|结束对话|再见|告辞)(?:[\s\S]*)$")
    async def talk_choice(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        st = db.get_talk_state(group_id, qq_id)
        if not st:
            yield event.plain_result("你现在没有正在进行的对话。输入『找 <NPC名>』开始交谈～")
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
                yield event.plain_result(f"没有这个选项！输入『对话 1-{len(opts)}』选择，『对话 0』结束。")
                return
            opt = opts[idx - 1]
            player = self._player(group_id, qq_id)
            action = opt.get("action") or {}
            # v81 导师进修：apprentice_check 判定（检查背包材料）
            if "apprentice_check" in action:
                check = action["apprentice_check"]
                have = db.count_item(group_id, qq_id, check.get("item", ""))
                need = int(check.get("count", 1))
                if have >= need:
                    nxt = opt.get("next", "__end__")
                    notices = self._apply_talk_action(group_id, qq_id, player, npc_id, action)
                    notices.append(f"✅ {npc['name']}满意地点了点头。")
                else:
                    nxt = opt.get("fail_next", opt.get("next", "__end__"))
                    notices = [f"{npc['name']}摇头：还差 {need-have} 份{check.get('item', '材料')}，备齐了再来。"]
            else:
                nxt = opt.get("next", "__end__")
                notices = self._apply_talk_action(group_id, qq_id, player, npc_id, action)
            # v95.11：talk 型主线与目标 NPC 对话即达成（active 空进度遗留态 → ready，修复主线卡死）
            notices += self._talk_quest_progress(group_id, qq_id, npc_id)
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

    @filter.regex(r"^(?:\[At:\d+\]\s*)?交付任务(?:\s*|$)")

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
                    yield event.plain_result(f"你需要到 {C.MAP_BY_ID.get(giver_map, {}).get('name', '？')} 找 {giver} 交付任务！")
                    return
        # 支线可交
        collect_missing = None  # 收集型材料还差的信息（用于最后提示）
        for sid, sq in list(quests.get("side", {}).items()):
            sqd = next((q for q in C.SIDE_QUESTS if q["id"] == sid), None)
            if not sqd:
                continue
            if sq.get("status") == "done":  # v95.12：已交付支线不重复接取/交付
                continue
            npc = C.NPCS.get(sqd["giver"]) or C.ALL_WILD.get(sqd["giver"])
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
                        giver = (C.NPCS.get(sqd["giver"]) or C.ALL_WILD.get(sqd["giver"]) or {}).get("name", "？")
                        giver_map = C.MAP_BY_ID.get((C.NPCS.get(sqd["giver"]) or C.ALL_WILD.get(sqd["giver"]) or {}).get("map", ""), {}).get("name", "？")
                        yield event.plain_result(f"支线『{sqd['name']}』材料齐了！需要找 {giver}(在{giver_map}) 交付任务！")
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
                    giver = (C.NPCS.get(sqd["giver"]) or C.ALL_WILD.get(sqd["giver"]) or {}).get("name", "？")
                    giver_map = C.MAP_BY_ID.get((C.NPCS.get(sqd["giver"]) or C.ALL_WILD.get(sqd["giver"]) or {}).get("map", ""), {}).get("name", "？")
                    yield event.plain_result(f"支线『{sqd['name']}』已达成，需要找 {giver}(在{giver_map}) 交付任务！")
                    return
        if collect_missing:
            name, mat, have, need = collect_missing
            yield event.plain_result(f"支线『{name}』还差 {mat} ×{need - have}(背包 {have}/{need})！")
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
            # v87 复合目标：kill+collect（魔剑士试炼），collect_count 独立于 kill count
            need = obj.get("collect_count", obj["count"])
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
        # 收集类：扣除材料
        if obj.get("collect"):
            need = obj.get("collect_count", obj["count"])
            for _ in range(need):
                db.remove_item(group_id, qq_id, _ckey)
        player = self._player(group_id, qq_id)
        player["exp"] += sqd["reward_exp"]
        player["gold"] += sqd["reward_gold"]
        player["_title_bonus"] = self._title_bonus(group_id, qq_id)
        lv_logs, player = E.check_player_level_up(group_id, qq_id, player)
        db.update_player(group_id, qq_id, exp=player["exp"], gold=player["gold"], level=player["level"], hp=player["hp"], mp=player["mp"], max_hp=player["max_hp"], max_mp=player["max_mp"], skills=player["skills"], attr_pts=player.get("attr_pts", 0), skill_points=player.get("skill_points", 0), learned_skills=player.get("learned_skills", []))
        if lv_logs:
            lines.append("")
            lines += lv_logs
        # v87 隐藏任务：奖励道具（reward_item）入包
        ri = sqd.get("reward_item")
        if ri:
            rimid = C.resolve("materials", ri)
            if rimid in C.MATERIALS:
                db.add_item(group_id, qq_id, rimid, {"name": C.display("materials", rimid), "type": "材料", "stackable": True, "price": C.MATERIALS[rimid]["price"]})
                lines.append(f"  🎁 获得特殊道具：{ri}")
        # v87 隐藏职业：交任务解锁（unlock_class 写入 hidden_class_unlock）
        uc = sqd.get("unlock_class")
        if uc:
            player_now = self._player(group_id, qq_id)
            unlocks = list(player_now.get("hidden_class_unlock", []) or [])
            if uc not in unlocks:
                unlocks.append(uc)
                db.update_player(group_id, qq_id, hidden_class_unlock=unlocks)
                lines.append(f"  ⚔️ 传承达成！隐藏职业「{C.CLASSES.get(uc, {}).get('name', uc)}」已解锁！")
                lines.append("  💡 达到 60 级后输入『转职 魔剑士』接受传承！")
        # v95.12：交付后保留条目标记 done（无 completed_side 列），防止 _offer_side_quests 自动重接
        quests["side"][sid] = {"status": "done"}
        db.save_quests(group_id, qq_id, quests)
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

    async def rest_camp(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
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

    async def rest(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        if self._is_redname(qq_id):
            yield event.plain_result("☠️ 你是红名！旅店老板不敢收留你……(等红名消退再来)")
            return
        cur_map = C.MAP_BY_ID.get(player["cur_map"])
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
        cost = max(30, (player.get("level") or 1) * 5)
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
            lines.append(f"{i:>2}. {f['icon']} {f['name']}：{tier}({pts})")
        lines.append("")
        lines.append("💡 击杀各地怪物、完成当地任务可获得对应势力声望")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?编年史(?:\s*|$)")

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
            f"(奥兰迪亚编年史 · 输入『传说』再听一段)"
        )
