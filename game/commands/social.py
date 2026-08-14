# -*- coding: utf-8 -*-
"""《剑与魔法》命令层 - social（social）

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
from ..commands.base import CommandBase, require_player


class SocialCmds(CommandBase):

    @filter.regex(r"^(?:\[At:\d+\]\s*)?市场(?:\s*|$)")
    @require_player()

    async def market(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        items = db.market_list(group_id)
        if not items:
            yield event.plain_result("🏪 市场空空如也。『上架 <物品> <价格>』寄售你的宝贝！")
            return
        raw = self._strip_cmd(event, "市场")
        page = self._parse_page(raw)
        page_items, pages, page = self._page_items(items, page, per_page=5)
        lines = [f"🏪 【群友市场】(第 {page}/{pages} 页 · 共 {len(items)} 件)", "━━━━━━━━━━━━"]
        for it in page_items:
            seller = self._player(group_id, it["seller"])
            sname = seller["name"] if seller else it["seller"]
            d = it["item_data"]
            # F2-1：行首编号直接用 DB id（与『购入 <编号>』『下架 <编号>』解析同基准，
            #   风格与摊位列表 #id 统一）。不再显示位置序号——原双编号在
            #   有过删除/翻页后必然错位（report_12 P1-1：『购入 1』买不到第 1 行）。
            lines.append(f"#{it['id']} {d.get('name','?')} ｜ {it['price']} 金币 ｜ 卖家 {sname}")
        lines.append("")
        if pages > 1 and page < pages:
            lines.append(f"💡 『市场 {page+1}』看下一页(共 {pages} 页)")
        lines.append("💡 『购入 <编号>』购买，『上架 <物品> <价格>』寄售")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?上架(?:\s*|$)")
    @require_player()

    async def market_sell(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        args = self._strip_cmd(event, "上架").rsplit(None, 1)
        if len(args) < 2 or not args[1].isdigit() or int(args[1]) < 1:
            yield event.plain_result("格式：上架 <物品名> <价格>，如『上架 铁剑 500』；价格至少 1 金币")
            return
        item_name = args[0]
        price = int(args[1])
        # v104R3 P2：上架价格上限——防止 999999999 恶意占坑/诱导高价（上限远超任何物品价值）
        if price > 999999:
            yield event.plain_result("价格太高啦！上架价最多 999999 金币～")
            return
        inv = db.get_inventory(group_id, qq_id)
        found = None
        for it in inv:
            if it["data"].get("name") == item_name:
                found = (it["key"], it["data"])
                break
        if not found:
            yield event.plain_result(f"背包里没有『{item_name}』！『背包』查看～")
            return
        item_key, data = found
        db.market_add(group_id, qq_id, item_key, data, price)
        db.remove_item(group_id, qq_id, item_key, count=1)
        yield event.plain_result(f"📦 已上架【{data['name']}】，定价 {price} 金币！\n『市场』查看，『下架 <编号>』撤回")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?下架(?:\s*|$)")
    @require_player()

    async def market_unsell(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        args = self._strip_cmd(event, "下架").split()
        if not args or not args[0].isdigit():
            yield event.plain_result("格式：下架 <编号>，『市场』查看编号")
            return
        mid = int(args[0])
        items = db.market_list(group_id)
        it = next((x for x in items if x["id"] == mid), None)
        if not it:
            yield event.plain_result("没有这个上架物品！")
            return
        if str(it["seller"]) != str(qq_id):
            yield event.plain_result("只能下架自己的物品！")
            return
        db.market_remove(mid)
        db.add_item(group_id, qq_id, it["item_key"], it["item_data"], count=1)
        yield event.plain_result(f"↩️ 已下架【{it['item_data'].get('name','?')}】，物品退回背包")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?购入(?:\s*|$)")
    @require_player()

    async def market_buy(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        args = self._strip_cmd(event, "购入").split()
        if not args or not args[0].isdigit():
            yield event.plain_result("格式：购入 <编号>，『市场』查看编号")
            return
        mid = int(args[0])
        it = db.market_get(mid)
        if not it:
            yield event.plain_result("没有这个物品！可能已被买走。")
            return
        if str(it["seller"]) == str(qq_id):
            yield event.plain_result("不能买自己的物品！")
            return
        # 换摊（price=0）：不走金币购买
        if (it.get("price") or 0) <= 0:
            yield event.plain_result(
                f"【{it['item_data'].get('name','?')}】是换摊(只换不卖)——用『换 {mid} <物品名>』提出交换！"
            )
            return
        # v66：摊位货必须当面买（摆摊在当前位置，需要同地图）
        if it.get("map_id"):
            if player.get("cur_map") != it["map_id"]:
                map_name = C.MAP_BY_ID.get(it["map_id"], {}).get("name", "那里")
                yield event.plain_result(f"这是【{it['item_data'].get('name','?')}】的摊位货，需要到『{map_name}』当面购入～(『摊位』看看谁在摆摊)")
                return
        if player["gold"] < it["price"]:
            yield event.plain_result(f"金币不足！需要 {it['price']} 金币。")
            return
        db.update_player(group_id, qq_id, gold=player["gold"] - it["price"])
        seller = self._player(group_id, it["seller"])
        if seller:
            db.update_player(group_id, it["seller"], gold=seller["gold"] + it["price"])
        db.market_remove(mid)
        db.add_item(group_id, qq_id, it["item_key"], it["item_data"], count=1)
        yield event.plain_result(f"🛒 购入成功！【{it['item_data'].get('name','?')}】已放入背包(花费 {it['price']} 金币)")

    # ---------------- v66 摆摊系统 ----------------

    @filter.regex(r"^(?:\[At:\d+\]\s*)?摆摊(?:[\s\S]*)$")
    @require_player()
    async def stall(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        args = self._strip_cmd(event, "摆摊").rsplit(None, 1)
        if len(args) == 1:
            item_name, price = args[0], 0  # 不带价格 = 以物换物
        elif args[1].isdigit():
            item_name, price = args[0], int(args[1])
            if price < 1:
                yield event.plain_result("价格至少 1 金币！")
                return
            # v104R3 P2：摆摊价格上限（与『上架』一致，防恶意占坑/诱导）
            if price > 999999:
                yield event.plain_result("价格太高啦！摆摊价最多 999999 金币～")
                return
        else:
            yield event.plain_result("格式：摆摊 <物品名> [价格]，不带价格 = 以物换物，如『摆摊 铁剑』或『摆摊 铁剑 500』")
            return
        inv = db.get_inventory(group_id, qq_id)
        found = next((it for it in inv if it["data"].get("name") == item_name), None)
        if not found:
            yield event.plain_result(f"背包里没有『{item_name}』！『背包』查看～")
            return
        cur_map = player.get("cur_map", "")
        map_obj = C.MAP_BY_ID.get(cur_map, {})
        if not map_obj and not cur_map.startswith("home_"):
            yield event.plain_result("这里没法摆摊……换个地方试试。")
            return
        # v68：家里摆摊 = 铺面（map 名显示为"家里"）
        if cur_map.startswith("home_"):
            map_name = "家里"
        else:
            map_name = map_obj.get("name", cur_map)
        # 已有摊位 → 自动收旧摊（物品退回；仅公共地图单摊语义）
        old = [s for s in db.market_list_by_seller(group_id, qq_id) if s.get("map_id")]
        # v104R3 P2：家里摆摊 = 铺面，受房屋等级挂机位限制（25 章房产案：
        # 木屋 0 位 / 石屋 1 位 / 庄园 2 位 / 宅邸 3 位——此前恒 1 摊且不校验；
        # 铺面多摊并存：位未满时不再自动收旧摊）
        _home_stall = cur_map.startswith("home_")
        if _home_stall:
            dlv = int(player.get("deed_lv", 1) or 1)
            hl = C.HOUSE_LEVELS.get(dlv, C.HOUSE_LEVELS[1])
            slots = hl.get("stall_slots", 0)
            if slots <= 0:
                yield event.plain_result("🏠 木屋没有铺面挂机位！『地契 升级』到石屋解锁 1 个挂机位～")
                return
            if len(old) >= slots:
                yield event.plain_result(
                    f"🏪 铺面挂机位已满({len(old)}/{slots})！先『收摊』腾位置，或升级房屋获得更多挂机位～")
                return
        if not _home_stall:
            for s in old:
                db.market_remove(s["id"])
                db.add_item(group_id, qq_id, s["item_key"], s["item_data"], count=1)
        db.market_add(group_id, qq_id, found["key"], found["data"], price, map_id=cur_map)
        db.remove_item(group_id, qq_id, found["key"], count=1)
        tip = f"(旧摊位已收摊，{len(old)} 件物品退回背包)" if (old and not _home_stall) else ""
        if price > 0:
            head = f"🏪 你在『{map_name}』支起了摊位，出售【{found['data']['name']}】定价 {price} 金币！{tip}\n"
            tail = "『收摊』收摊，『摊位』看看本地谁在摆摊"
        else:
            head = f"🔄 你在『{map_name}』支起了换摊——【{found['data']['name']}】只换不卖！{tip}\n"
            tail = "『收摊』收摊，别人可用『换 <编号> <物品名>』跟你交换"
        yield event.plain_result(head + tail)

    @filter.regex(r"^(?:\[At:\d+\]\s*)?收摊(?:[\s\S]*)$")
    @require_player()
    async def stall_close(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        removed = db.market_remove_by_seller(group_id, qq_id)
        if not removed:
            yield event.plain_result("你现在没有摊位。『摆摊 <物品> <价格>』支起摊位～")
            return
        for s in removed:
            db.add_item(group_id, qq_id, s["item_key"], s["item_data"], count=1)
        names = "、".join(s["item_data"].get("name", "?") for s in removed)
        yield event.plain_result(f"🏪 收摊！【{names}】退回背包")

    @staticmethod
    def _stall_label(s):
        """摊位价格标签：price>0 → 'N 金币'；price=0 → '🔄 换'(以物换物)"""
        price = s.get("price") or 0
        return f"{price} 金币" if price > 0 else "🔄 换"

    @filter.regex(r"^(?:\[At:\d+\]\s*)?摊位(?:[\s\S]*)$")
    @require_player()
    async def stall_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        raw = self._strip_cmd(event, "摊位").strip()
        # 指定玩家 → 看他的摊位
        if raw:
            target = db.find_player_by_name(raw)
            if not target:
                yield event.plain_result(f"没找到玩家『{raw}』！")
                return
            target_id = target["qq_id"]
            tp = db.get_player(group_id, target_id)
            if tp:
                db.market_sync_stall(target_id, tp.get("cur_map", ""))  # 摊位惰性跟随
            stalls = [s for s in db.market_list_by_seller(group_id, target_id) if s.get("map_id")]
            if not stalls:
                yield event.plain_result(f"{target['name']} 没有在摆摊。")
                return
            lines = [f"🏪 【{target['name']} 的摊位】", "━━━━━━━━━━━━"]
            for s in stalls:
                map_name = C.MAP_BY_ID.get(s.get("map_id", ""), {}).get("name", "？")
                lines.append(f"#{s['id']} {s['item_data'].get('name','?')} ｜ {self._stall_label(s)} ｜ 在 {map_name}")
            lines.append("💡 标 🔄 的是换摊：『换 <编号> <物品名>』当面交换；其他『购入 <编号>』(需在同一位置)")
            yield event.plain_result("\n".join(lines))
            return
        # 无参 → 当前地图所有摊位
        cur_map = player.get("cur_map", "")
        stalls = db.market_list(group_id, cur_map)
        if not stalls:
            yield event.plain_result("此地没有摊位。『摆摊 <物品> [价格]』支起你的小摊(不带价格 = 换摊)！")
            return
        lines = [f"🏪 【此地摊位】({C.MAP_BY_ID.get(cur_map, {}).get('name', '这里')})", "━━━━━━━━━━━━"]
        for s in stalls:
            seller = db.get_player(group_id, s["seller"])
            sname = seller["name"] if seller else s["seller"]
            lines.append(f"#{s['id']} {s['item_data'].get('name','?')} ｜ {self._stall_label(s)} ｜ {sname}")
        lines.append("💡 标 🔄 的是换摊：『换 <编号> <物品名>』当面交换；其他『购入 <编号>』，『摊位 <玩家名>』看指定摊位")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?换(?:[\s\S]*)$")
    @require_player()
    async def stall_exchange(self, event: AstrMessageEvent):
        """以物换物：『换 <摊位编号> <物品名>』——对方摆摊不带价格(换摊)时，用背包物品当面交换"""
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        args = self._strip_cmd(event, "换").split(None, 1)
        if len(args) < 2 or not args[0].isdigit():
            yield event.plain_result("格式：换 <摊位编号> <物品名>，如『换 3 狼皮』(对方摆摊不带价格 = 换摊)")
            return
        mid, give_name = int(args[0]), args[1].strip()
        it = db.market_get(mid)
        if not it:
            yield event.plain_result(f"没有编号 {mid} 的摊位！『摊位』看看～")
            return
        if not it.get("map_id"):
            yield event.plain_result("这是群市场寄售，不参与交换——用『购入 <编号>』金币购买～")
            return
        # 当面交换：双方必须同地图
        if player.get("cur_map", "") != it["map_id"]:
            map_name = C.MAP_BY_ID.get(it["map_id"], {}).get("name", "那里")
            yield event.plain_result(
                f"这是【{it['item_data'].get('name','?')}】的换摊，需要到『{map_name}』当面交换～"
            )
            return
        if str(it["seller"]) == str(qq_id):
            yield event.plain_result("不能和自己交换！")
            return
        if (it.get("price") or 0) > 0:
            yield event.plain_result(
                f"【{it['item_data'].get('name','?')}】是出售中的({it['price']} 金币)，用『购入 {mid}』购买～"
            )
            return
        inv = db.get_inventory(group_id, qq_id)
        give = next((x for x in inv if x["data"].get("name") == give_name), None)
        if not give:
            yield event.plain_result(f"背包里没有『{give_name}』！『背包』查看～")
            return
        # 成交：摊主的货给买家，买家的货送到摊主背包
        db.market_remove(mid)
        db.add_item(it.get("group_id") or group_id, qq_id, it["item_key"], it["item_data"], count=1)
        db.remove_item(group_id, qq_id, give["key"], count=1)
        db.add_item(it.get("group_id") or group_id, str(it["seller"]), give["key"], give["data"], count=1)
        yield event.plain_result(
            f"🔄 交换成功！你用【{give['data']['name']}】换到了【{it['item_data'].get('name','?')}】！\n"
            f"对方的东西已放进你背包，你的【{give['data']['name']}】已送到对方背包～"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:组队|队伍)(?:[\s\S]*)$")
    @require_player()

    async def party(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        target = self._strip_cmd(event, "组队").strip()
        # v104 M04 P2：『队伍甲』免空格拉人失效——正则同时接受 组队|队伍 前缀，
        # 但 _strip_cmd 只剥"组队"，"队伍甲" 被当玩家名查找报"找不到玩家"。
        # 与『组队甲』同规则：剥掉"队伍"前缀（『队伍』= 查看面板，空参同义）。
        if target.startswith("队伍"):
            target = target[2:].strip()
        members = db.party_members(group_id, qq_id)
        if not target:
            if members:
                lines = [f"🤝 【队伍】({len(members)}人)", "━━━━━━━━━━━━"]
                # v104 M04 P2：面板补"位置"（模块卡审计点 7：成员/等级/职业/位置）——
                # 副本内按速度降序决定出手顺序（instance.py:956），面板标注每人行动位次，
                # 让玩家知道下副本时谁先出手（出手位≠入队序号，速度排序）
                _order = []
                for _m in members:
                    _p = self._player(group_id, _m)
                    _spd = 0
                    if _p:
                        _spd = E.player_final_stats(
                            _p["class_name"], _p["level"], _p.get("equipment", {}),
                            _p.get("class_tier", 0), _p.get("attributes"),
                            _p.get("evolve_path", 0), None, _p.get("race")
                        ).get("spd", 0) or 0
                    _order.append((_spd, str(_m)))
                _rank = {mid: i + 1 for i, (_s, mid) in enumerate(sorted(_order, key=lambda x: -x[0]))}
                for i, m in enumerate(members, 1):
                    p = self._player(group_id, m)
                    # v104 M04 P2：面板补 等级/职业（对齐『角色』面板写法 C.display('classes', ...)）
                    cls_str = (
                        f" Lv.{p.get('level', '?')} {C.display('classes', p.get('class_name') or C.CLASS_NOVICE)}"
                        if p else ""
                    )
                    pos_str = f" · 出手位{_rank.get(str(m), '?')}" if len(members) > 1 else ""
                    lines.append(f"{i}. {p['name'] if p else m}{cls_str}{pos_str}" + ("(队长)" if m == members[0] else ""))
                lines.append("💡 组队打怪经验＋10%（野外各自为战，仅经验加成；副本内才并肩作战）！队长『组队 <名字>』可再拉人(上限 4 人)；『退队』离开")
                yield event.plain_result("\n".join(lines))
            else:
                yield event.plain_result("你还没有队伍～『组队 <对方名字>』邀请同群玩家组队！\n💡 组队打怪经验＋10%（野外各自为战，仅经验加成，副本内才并肩作战）")
            return
        # 找目标玩家
        all_players = db.get_group_players(group_id)
        target_qq = None
        for q, p in all_players.items():
            if p.get("name") == target or q == target:
                target_qq = q
                break
        if not target_qq:
            yield event.plain_result(f"找不到玩家『{target}』！确保对方已『注册』角色～")
            return
        if str(target_qq) == str(qq_id):
            yield event.plain_result("不能和自己组队！")
            return
        tname = self._player(group_id, target_qq)
        tname_str = tname["name"] if tname else target
        # v104 M04 P1：战斗/副本中禁止组队/拉人——防把副本队长/队员拉走（原队伍解散→副本僵尸化）、
        # 战斗中拉新人（新人未上锁可双线野外战斗）。队员的副本 battle 行存队长名下，
        # 须用 _instance_battle_for 查副本归属；retreated（撤退保留进度）不算战斗中。
        _lb = db.get_battle(group_id, qq_id)
        _tb = db.get_battle(group_id, target_qq)
        if _lb and not (_lb["state"].get("type") == "instance" and _lb["state"].get("retreated")):
            yield event.plain_result("⚔️ 你正在战斗中！先打完再组队吧～")
            return
        if _tb and not (_tb["state"].get("type") == "instance" and _tb["state"].get("retreated")):
            yield event.plain_result(f"⚔️ {tname_str} 正在战斗中！等 TA 打完再组队吧～")
            return
        if self._instance_battle_for(group_id, target_qq):
            yield event.plain_result(f"⚔️ {tname_str} 正在副本战斗中！等 TA 打完再组队吧～")
            return
        # v49：已有队伍时，队长用『组队 <名字>』拉新人（上限 3 人）
        if members:
            if str(members[0]) != str(qq_id):
                yield event.plain_result("你已在队伍中，让队长『组队 <名字>』拉人吧～")
                return
            if db.party_add(group_id, qq_id, target_qq):
                # v104 M04 P2：拉人同样记组队次数（设计 29 章 2.1「组队成功双方各记
                # party_count」）——此前只 party_create 计数，常玩 3-4 人队成就进度慢
                db.bump_stats(group_id, qq_id, party_count=1)
                db.bump_stats(group_id, target_qq, party_count=1)
                C.check_achievements(group_id, qq_id)
                C.check_achievements(group_id, target_qq)
                my_name = self._player(group_id, qq_id)
                yield event.plain_result(
                    f"🤝 {tname_str} 加入了你的队伍！(当前 {len(db.party_members(group_id, qq_id))} 人，上限 4 人)\n"
                    f"💡 组队打怪经验＋10%！\n"
                    f"🔔 {tname_str}：{my_name['name'] if my_name else qq_id} 将你拉入了队伍！"
                )
            else:
                # v104 M04 P2：P1-1 吞并修复后此文案名副其实——party_add 拒绝=目标已在队伍/别队/满员
                yield event.plain_result(f"无法拉入 {tname_str}：TA 已在队伍中(含其他队伍)，或队伍已满(4 人)～")
            return
        if not db.party_create(group_id, qq_id, target_qq):
            yield event.plain_result(f"无法与 {tname_str} 组队：TA 已有队伍，或正在战斗中～")
            return
        # 阶段九：组队次数 + 成就判定（双方）
        db.bump_stats(group_id, qq_id, party_count=1)
        db.bump_stats(group_id, target_qq, party_count=1)
        C.check_achievements(group_id, qq_id)
        C.check_achievements(group_id, target_qq)
        yield event.plain_result(f"🤝 组队成功！你和 {tname_str} 成为队友\n💡 组队打怪经验＋10%！『组队 <名字>』可再拉人(上限 4 人)")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?退队(?:\s*|$)")
    @require_player()

    async def party_leave(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        # v104 P1：副本进行中禁止退队——副本 battle 只存队长名下，队长退队会删光队伍行，
        # 之后 _instance_current_members 返回 [] → Boss 不再攻击、击杀/通关零奖励（副本僵尸化）。
        # 非队长（队员）不受限：v104 设计允许队员退队，结算自动剔除退队者。
        b = db.get_battle(group_id, qq_id)
        if b and b["state"].get("type") == "instance" and not b["state"].get("retreated") \
                and str(b["state"].get("leader", qq_id)) == str(qq_id):
            yield event.plain_result("⚔️ 副本进行中不能退队！先『撤退』保留进度，或通关/『离开副本』后再退队～")
            return
        # v104 P1：退队者若正挂在副本队伍中（战斗记录存队长名下）→ 退队后同步清其战斗锁
        # （内存锁 + 可能残留的 battle 行），防 24h 锁残留（_in_battle 自愈只在下次交互才触发）
        inst_member = False
        members = db.party_members(group_id, qq_id)
        if members and str(members[0]) != str(qq_id):
            lb = db.get_battle(group_id, members[0])
            if lb and lb["state"].get("type") == "instance" and not lb["state"].get("retreated") \
                    and str(qq_id) in [str(m) for m in lb["state"].get("members", [])]:
                inst_member = True
        if db.party_leave(group_id, qq_id):
            if inst_member:
                self._unlock_battle(group_id, qq_id)
                db.clear_battle(group_id, qq_id)
            # v104 M04 P2：队长退队=队伍解散，其名下撤退保留的副本进度行一并清理
            # （队伍已散，进度无法恢复；此前该行驻留到被新开本覆盖，长期占一行数据）
            if not db.party_members(group_id, qq_id):
                _lb = db.get_battle(group_id, qq_id)
                if _lb and _lb["state"].get("type") == "instance" and _lb["state"].get("retreated"):
                    db.clear_battle(group_id, qq_id)
            yield event.plain_result("👋 你已退出队伍！(队长退队将解散队伍)")
        else:
            yield event.plain_result("你还没有队伍～")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?创建公会(?:\s*|$)")
    @require_player()

    async def guild_create_cmd(self, event: AstrMessageEvent):
        import datetime
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        name = self._strip_cmd(event, "创建公会").strip()[:8]  # 策划 11 章 3.1：公会名 1-8 字
        if not name:
            yield event.plain_result("格式：创建公会 <名字>，如『创建公会 屠龙勇士』")
            return
        if db.guild_get_by_member(qq_id):
            yield event.plain_result("你已经在一个公会里啦！先『退出公会』再加入新的～")
            return
        cfg = C.GUILD_CONFIG
        if player["level"] < cfg["create_level"]:
            yield event.plain_result(f"创建公会需要 {cfg['create_level']} 级！你才 {player['level']} 级，先去冒险吧～")
            return
        if player["gold"] < cfg["create_cost"]:
            yield event.plain_result(f"创建公会需要 {cfg['create_cost']} 金币！你只有 {player['gold']} 金币。")
            return
        gid = db.guild_create(name, qq_id, desc=f"{player['name']} 创立的公会")
        if not gid:
            yield event.plain_result(f"公会『{name}』已存在！换个名字吧～")
            return
        db.update_player(group_id, qq_id, gold=player["gold"] - cfg["create_cost"])
        # v105 M18 P2：创建公会立即判定成就（ach_guild1「加入公会」无需等下次事件）
        C.check_achievements(group_id, qq_id)
        yield event.plain_result(
            f"🏰 【公会创建成功】『{name}』！\n"
            f"你成为了公会会长！\n"
            f"💡 『公会』查看信息，『公会签到』『公会任务』『公会捐献』为公会贡献力量！"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?加入公会(?:\s*|$)")
    @require_player()

    async def guild_join_cmd(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        name = self._strip_cmd(event, "加入公会").strip()
        if not name:
            yield event.plain_result("格式：加入公会 <公会名>，如『加入公会 屠龙勇士』")
            return
        if db.guild_get_by_member(qq_id):
            yield event.plain_result("你已经在一个公会里啦！")
            return
        g = db.guild_get_by_name(name)
        if not g:
            yield event.plain_result(f"找不到公会『{name}』！输入『公会排行』看看有哪些公会～")
            return
        db.guild_join(g["gid"], qq_id)
        # v105 M18 P2：加入公会立即判定成就（ach_guild1「加入公会」无需等下次事件）
        C.check_achievements(group_id, qq_id)
        yield event.plain_result(f"🏰 欢迎加入公会【{g['name']}】！\n💡 『公会』查看信息，『公会签到』每日报到！")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?退出公会(?:\s*|$)")
    @require_player()

    async def guild_leave_cmd(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        g = db.guild_get_by_member(qq_id)
        if not g:
            yield event.plain_result("你不在任何公会里～")
            return
        if g["leader"] == qq_id:
            # v105 M18 P2：全仓无『转让会长』命令，提示只指向真实命令，避免误导
            yield event.plain_result("你是会长！会长不能直接退会，请『解散公会』（公会随之解散）～")
            return
        db.guild_leave(g["gid"], qq_id)
        yield event.plain_result(f"👋 你已退出公会【{g['name']}】。江湖再见！")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?解散公会(?:\s*|$)")
    @require_player()

    async def guild_disband_cmd(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        g = db.guild_get_by_leader(qq_id)
        if not g:
            yield event.plain_result("只有会长才能解散公会！")
            return
        db.guild_leave(g["gid"], qq_id)  # leader 离开即解散
        yield event.plain_result(f"🏚️ 公会【{g['name']}】已解散……")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?公会(?!签到|任务|捐献|排行|创建|加入|退出|解散)(?:\s*.*|$)")
    @require_player()

    async def guild_info(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        g = db.guild_get_by_member(qq_id)
        if not g:
            yield event.plain_result("你还没有公会！『创建公会 <名字>』(30级＋1000金币)或『加入公会 <名字>』")
            return
        members = db.guild_members(g["gid"])
        count = len(members)
        exp_need = g["level"] * C.GUILD_EXP_BASE
        raw = self._strip_cmd(event, "公会")
        page = self._parse_page(raw)
        page_items, pages, page = self._page_items(members, page, per_page=5)
        lines = [
            f"{g['icon']} 【{g['name']}】Lv.{g['level']}",
            f"━━━━━━━━━━━━",
            f"👥 成员 {count} 人 ｜ 经验 {g['exp']}/{exp_need}",
            f"📜 {g['desc'] or '暂无宣言'}",
            f"💡 公会加成：打怪经验 +{min(int(g['level'] * C.GUILD_CONFIG['exp_bonus_per_level'] * 100), int(C.GUILD_CONFIG['max_bonus'] * 100))}%",
            f"━━━━━━━━━━━━",
            f"成员(第 {page}/{pages} 页)：",
        ]
        for i, m in enumerate(page_items, (page - 1) * 5 + 1):
            p = self._player(group_id, m["qq_id"])
            role = "👑" if m["role"] == "leader" else "⚔️"
            name = p["name"] if p else m["qq_id"]
            lines.append(f"{i:>2}. {role} {name} Lv.{p['level'] if p else '?'} ｜ 贡献 {m['contribute']}")
        lines.append("")
        if pages > 1 and page < pages:
            lines.append(f"💡 『公会 {page+1}』看下一页(共 {pages} 页)")
        lines.append("💡 『公会签到』『公会任务』『公会捐献』为公会赚经验！")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?公会签到(?:\s*|$)")
    @require_player()

    async def guild_sign(self, event: AstrMessageEvent):
        import datetime
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        g = db.guild_get_by_member(qq_id)
        if not g:
            yield event.plain_result("你还没有公会！先『加入公会 <名字>』吧～")
            return
        today = datetime.date.today().isoformat()
        if db.guild_get_sign(g["gid"], qq_id) == today:
            yield event.plain_result("今天已经公会签过到啦！明天再来～")
            return
        cfg = C.GUILD_CONFIG
        db.guild_set_sign(g["gid"], qq_id, today)
        db.guild_add_exp(g["gid"], cfg["sign_exp"], member_qq=qq_id, contribute=cfg["sign_contribute"])
        db.update_player(group_id, qq_id, gold=player["gold"] + cfg["sign_gold"])
        yield event.plain_result(
            f"📅 【公会签到】在【{g['name']}】报到！\n"
            f"🏰 公会经验 +{cfg['sign_exp']} ｜ 个人贡献 +{cfg['sign_contribute']}\n"
            f"💰 金币 +{cfg['sign_gold']}"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?公会任务(?:\s*|$)")
    @require_player()

    async def guild_task(self, event: AstrMessageEvent):
        import datetime
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        g = db.guild_get_by_member(qq_id)
        if not g:
            yield event.plain_result("你还没有公会！先『加入公会 <名字>』吧～")
            return
        today = datetime.date.today().isoformat()
        tdate, tprog = db.guild_get_task(g["gid"], qq_id)
        if tdate != today:
            tdate, tprog = today, 0
        need = C.GUILD_CONFIG["kill_task"]
        if tprog >= need:
            yield event.plain_result("今天的公会任务已完成！明天再来～")
            return
        yield event.plain_result(
            f"🎯 【公会任务】击杀 {need} 只怪物(当前 {tprog}/{need})\n"
            f"💡 击杀会自动结算奖励！"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?公会捐献(?:\s*|$)")
    @require_player()

    async def guild_donate_cmd(self, event: AstrMessageEvent):
        """公会捐献：上交材料为公会做贡献，每日一次。

        策划 11 章 4 种公会任务（讨伐/捐献/金币/副本）→ 简化落地：讨伐（击杀自动推进）+ 捐献（上交 3 份材料）。
        进度用 event_state 单独记录（key=guild_donate:{gid}:{qq_id}，值=日期），不与击杀任务共用 task_progress。
        """
        import datetime
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        g = db.guild_get_by_member(qq_id)
        if not g:
            yield event.plain_result("你还没有公会！先『加入公会 <名字>』吧～")
            return
        cfg = C.GUILD_CONFIG
        need = cfg["donate_items"]
        today = datetime.date.today().isoformat()
        key = f"guild_donate:{g['gid']}:{qq_id}"
        if db.get_event_state(key) == today:
            yield event.plain_result("今天的公会捐献已完成！明天再来～")
            return
        # 材料 = 背包中 mat_ 前缀物品（v46 起材料统一存 mat_ 拼音/英文 id）
        # v104R3 P1-3：排除任务道具——隐藏线/主线交付物（烬火信标/星尘沙漏/灰烬之核等）
        # 也是 mat_ 前缀，误捐后无再获取途径 → 隐藏线断链（与批量出售保护 economy.py 对齐）
        mats = [it for it in db.get_inventory(group_id, qq_id)
                if it["key"].startswith("mat_") and it["data"].get("type") != "任务道具"]
        total = sum(it["count"] for it in mats)
        if total < need:
            yield event.plain_result(
                f"🎯 【公会捐献】需要上交 {need} 份材料(当前 {total}/{need})！\n"
                f"💡 打怪掉落/采集可获得材料，凑齐后『公会捐献』再来～"
            )
            return
        # 扣材料（从背包靠前的材料开始扣）
        remain = need
        for it in mats:
            if remain <= 0:
                break
            take = min(it["count"], remain)
            db.remove_item(group_id, qq_id, it["key"], take)
            remain -= take
        db.guild_add_exp(g["gid"], cfg["task_exp"], member_qq=qq_id, contribute=cfg["task_contribute"])
        db.update_player(group_id, qq_id, gold=player["gold"] + cfg["task_gold"])
        db.set_event_state(key, today)
        yield event.plain_result(
            f"🎁 【公会捐献完成】上交 {need} 份材料，为公会贡献力量！\n"
            f"🏰 公会经验 +{cfg['task_exp']} ｜ 个人贡献 +{cfg['task_contribute']}\n"
            f"💰 金币 +{cfg['task_gold']}"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?公会排行(?:\s*|$)")

    async def guild_rank(self, event: AstrMessageEvent):
        tops = db.guild_top(10)
        if not tops:
            yield event.plain_result("还没有公会成立！『创建公会 <名字>』建立第一个公会吧～")
            return
        lines = ["🏆 【公会排行榜】", "━━━━━━━━━━━━"]
        for i, g in enumerate(tops, 1):
            lines.append(f"{i}. {g['icon']} {g['name']} Lv.{g['level']}({g['members']}人)")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?宠物(?!改名)(?:\s*|$)")
    @require_player()

    async def pet_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        pet = db.pet_get(qq_id)
        # 饱食度自然衰减（每小时 -1）先结算再展示
        pet = db.pet_decay_satiety(pet)
        if not pet:
            dex = db.pet_dex_get(qq_id)
            dex_line = ""
            if dex:
                names = [next((p["name"] for p in C.PET_POOL if p["key"] == k), k) for k in dex]
                dex_line = f"\n📖 图鉴收集：{'、'.join(names)}"
            yield event.plain_result(f"你还没有宠物！打怪有概率掉落宠物蛋，『使用 宠物蛋』孵化～{dex_line}")
            return
        pdef = next((p for p in C.PET_POOL if p["key"] == pet["pet_key"]), None)
        icon = pdef["icon"] if pdef else "🐾"
        # 饱食度衰减持久化
        db.pet_update(qq_id, satiety=pet["satiety"], last_sat_time=pet["last_sat_time"])
        sat = pet["satiety"]
        # v104 M17 P2：面板加成按饱食度显示实际值（与战斗实算一致：饱食度=0 减半）
        _pb = min(pet["level"] / 10, 0.5)
        if sat <= 0:
            _pb = _pb / 2
        bonus = int(_pb * 100)
        skill_line = ""
        if pdef:
            skill_line = f"\n🎯 技能：{C.pet_skill_label(pet['pet_key'])}(Lv.10 解锁)"
        if sat <= 0:
            skill_line = "\n😵 技能失效(饱食度归零)"
        lines = [
            f"{icon} 【宠物 · {pdef['name'] if pdef else pet['name']}】",
            f"━━━━━━━━━━━━",
            f"名字：{pet['name']} | Lv.{pet['level']}",
        ]
        # v101.14 品质/出处展示
        if pdef:
            ql = C.pet_quality_label(pet["pet_key"])
            if ql:
                lines.append(f"📖 品质：{ql}")
            if pdef.get("source"):
                lines.append(f"📍 出处：{pdef['source']}")
        if skill_line:
            lines.append(skill_line.lstrip("\n"))
        lines.append(f"❤️ 饱食度：{sat}/100")
        # v104 M17 P3：亲密度展示（bond 原本只写不读）
        bond = pet.get("bond", 0)
        bond_line = f"💕 亲密度：{bond}/100"
        if bond >= 50:
            bond_line += "（羁绊生效：战斗经验 +5%）"
        lines.append(bond_line)
        lines.append(f"✨ 经验加成：+{bonus}%(主人战斗经验)" + ("(饱食度归零，加成减半)" if sat <= 0 else ""))
        lines.append("━━━━━━━━━━━━")
        lines.append("💡 『喂养 <材料>』恢复饱食度，『宠物改名 <名字>』改名，『放生』告别")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?宠物改名(?:\s*|$)")
    @require_player()

    async def pet_rename(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        pet = db.pet_get(qq_id)
        if not pet:
            yield event.plain_result("你还没有宠物！")
            return
        new_name = self._strip_cmd(event, "宠物改名").strip()[:8]
        if not new_name:
            yield event.plain_result("格式：宠物改名 <名字>")
            return
        db.pet_update(qq_id, name=new_name)
        yield event.plain_result(f"🐾 你的宠物改名为【{new_name}】！")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?喂养(?:\s*|$)")
    @require_player()

    async def pet_feed(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        pet = db.pet_get(qq_id)
        # 饱食度自然衰减先结算
        pet = db.pet_decay_satiety(pet)
        if not pet:
            yield event.plain_result("你还没有宠物！打怪有概率掉落宠物蛋，『使用 宠物蛋』孵化～")
            return
        db.pet_update(qq_id, satiety=pet["satiety"], last_sat_time=pet["last_sat_time"])
        mat_name = self._strip_cmd(event, "喂养").strip()
        if not mat_name:
            yield event.plain_result("格式：喂养 <材料名/序号>，如『喂养 狼皮』或『喂养 1』(打怪/采集可获得材料)")
            return
        # 找背包里的食材（材料/鱼/草药均可，24 章四）
        items = db.get_inventory(group_id, qq_id)
        target = None
        FOOD_TYPES = {"材料", "鱼"}
        if mat_name.isdigit():
            mats = [it for it in items if it["data"].get("type") in FOOD_TYPES]
            idx = int(mat_name)
            if idx < 1 or idx > len(mats):
                yield event.plain_result(f"背包里没有第 {idx} 个食材(共 {len(mats)} 个)！打怪、『采集』、『垂钓』可获得食材。")
                return
            target = mats[idx - 1]
        else:
            for it in items:
                d = it["data"]
                if d.get("type") in FOOD_TYPES and mat_name in d["name"]:
                    target = it
                    break
        if not target:
            yield event.plain_result(f"背包里没有食材『{mat_name}』！打怪、『采集』、『垂钓』可获得食材。")
            return
        # 喂食：饱食度 +30（24 章四），亲密度 +5，经验 +10
        db.remove_item(group_id, qq_id, target["key"])
        sat = min(100, pet["satiety"] + 30)
        # v105 M17 P3-6：亲密度封顶 100（面板显示 x/100，此前 99→104 显示 104/100）
        bond = min(100, pet["bond"] + 5)
        exp = pet["exp"] + 10
        lv = pet["level"]
        while exp >= C.pet_exp_need(lv):
            exp -= C.pet_exp_need(lv)
            lv += 1
        db.pet_update(qq_id, satiety=sat, bond=bond, exp=exp, level=lv)
        lv_str = f"\n🎉 宠物升级到 Lv.{lv}！" if lv > pet["level"] else ""
        yield event.plain_result(f"🍖 你喂了【{pet['name']}】一份{target['data']['name']}！\n😋 饱食度 +30 ｜ 💕 亲密度 +5 ｜ ✨ 经验 +10{lv_str}")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?放生(?:\s*|$)")
    @require_player()

    async def pet_release(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        pet = db.pet_get(qq_id)
        if not pet:
            yield event.plain_result("你还没有宠物～")
            return
        db.pet_delete(qq_id)
        # 图鉴记录保留（24 章三：放生后宠物蛋可重新掉落，图鉴记录保留）
        yield event.plain_result(f"🕊️ 你放生了【{pet['name']}】……它会记得你的。\n📖 图鉴记录已保留，之后还有机会遇到它！")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:坐骑|骑乘|下马)(?:\s*|$)")
    @require_player()

    async def mount_cmd(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        raw = self._strip_cmd(event, "骑乘") if event.get_message_str().startswith(("骑乘", "[At:")) else ""
        cmd = event.get_message_str().strip()
        # 下马
        if cmd.startswith("下马") or raw.startswith("下马"):
            mounts = player.get("mounts") or {}
            if mounts.get("active"):
                mounts["active"] = None
                db.update_player(group_id, qq_id, mounts=mounts)
                yield event.plain_result("🛑 你翻身下马，坐骑回到了马厩。")
            else:
                yield event.plain_result("你现在没有骑乘任何坐骑～")
            return
        # 骑乘/购买（带参数）
        if event.get_message_str().startswith(("骑乘", "[At:")) or raw:
            name = (raw or "").strip()
            mounts = player.get("mounts") or {}
            owned = mounts.get("owned") or []
            # 骑乘
            if name:
                target = None
                for mk in owned:
                    m = C.MOUNT_BY_KEY.get(mk)
                    if m and name in (m["name"], mk):
                        target = m
                        break
                if not target:
                    # 未拥有的坐骑 → 提示
                    for m in C.MOUNT_POOL:
                        if name in (m["name"], m["key"]):
                            # v105 M17 P3-4：提示按真实渠道（商店直购/desc 括号渠道），
                            # 此前驼马/驯鹿/独角兽等生活渠道坐骑也提示打精英/Boss，误导玩家
                            if (m.get("price") or 0) > 0:
                                _tip = f"去商店『购买 {m['name']}』"
                            else:
                                _d = m.get("desc", "")
                                _ch = _d[_d.rindex("(") + 1:] if "(" in _d else ""
                                if "『" in _ch:
                                    _ch = _ch.split("『")[0]
                                _tip = f"{_ch or '打精英/Boss 掉缰绳'}后用『使用 缰绳』解锁"
                            yield event.plain_result(f"你还没有『{m['name']}』！{_tip}～")
                            return
                    yield event.plain_result(f"没有叫『{name}』的坐骑～『坐骑』查看全部")
                    return
                if player["level"] < target["lv"]:
                    yield event.plain_result(f"『{target['name']}』需要 Lv.{target['lv']} 才能骑乘，你才 Lv.{player['level']}！")
                    return
                mounts["active"] = target["key"]
                db.update_player(group_id, qq_id, mounts=mounts)
                yield event.plain_result(f"{target['icon']} 你骑上了【{target['name']}】！{target['desc']}")
                return
        # 坐骑面板
        mounts = player.get("mounts") or {}
        owned = mounts.get("owned") or []
        active = mounts.get("active")
        from ..data.equipment import QUALITY as _Q
        def _q_label(m):
            q = _Q.get(m.get("quality", "white"), {})
            return f"{q.get('color', '⚪')}{q.get('name', '普通')}"
        lines = ["🐾 【坐骑】", "━━━━━━━━━━━━"]
        if not owned:
            lines.append("你还没有坐骑。去橡木镇商店『购买 老马』，或者打精英/Boss 碰碰运气！")
        for mk in owned:
            m = C.MOUNT_BY_KEY.get(mk)
            if not m:
                continue
            mark = " 🟢 骑乘中" if active == mk else ""
            lines.append(f"{_q_label(m)} {m['icon']} {m['name']}{mark} — {m['desc']}")
        if owned:
            lines.append("")
            lines.append("💡 『骑乘 <名称>』骑上坐骑，『下马』下来")
        else:
            lines.append("")
            lines.append("💡 可获得的坐骑：" + "、".join(f"{_q_label(m)}{m['name']}" for m in C.MOUNT_POOL))
        yield event.plain_result("\n".join(lines))

    async def _maybe_roll_event(self, group_id: str) -> str:
        """惰性事件调度：无事件且冷却到期 → 概率触发新事件。返回公告文本(无则空串)"""
        import random as _rnd
        cur = db.get_world_event(include_expired=True)
        now = int(time.time())
        # 当前事件过期 → 清除（v104R3 P1-1：过期拍卖必须先走 _settle_auction 结算——
        # 否则出价金币随 bids 记录一起销毁，永久丢失；Boss 事件由各自指令处理）
        if cur and now >= cur["ends_at"]:
            if cur["etype"] == "auction":
                try:
                    _lines = self._settle_auction(cur, group_id)
                    if _lines:
                        await self._broadcast(f"🏪 【拍卖行 · 落槌结算】\n{_lines}")
                except Exception as _e:
                    pass
            db.clear_world_event()
            cur = None
        if cur:
            return ""
        # 冷却检查：上次事件结束时间 + 随机 30~90 分钟
        last_end = db.get_event_state("last_event_end")
        cooldown = 1800 + _rnd.randint(0, 3600)
        if last_end and now < int(last_end) + cooldown:
            return ""
        # 60% 概率触发
        if _rnd.random() > 0.6:
            db.set_event_state("last_event_end", str(now))
            return ""
        evt = _rnd.choice(C.WORLD_EVENT_POOL)
        ends = now + evt["duration"]
        # v100.2：事件 data 初始化数据化 → core/world_event_templates.py INITIALIZERS
        from ..core.world_event_templates import INITIALIZERS
        init_fn = INITIALIZERS.get(evt["type"])
        data = init_fn(_rnd) if init_fn else {}
        db.save_world_event(evt["type"], ends, data)
        db.set_event_state("last_event_end", str(ends))
        return f"\n🌍 【世界事件】{evt['icon']} {evt['name']}！\n{evt['desc']}"

    @filter.regex(r"^(?:\[At:\d+\]\s*)?事件(?:\s*|$)")
    @require_player()

    async def world_event(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        notice = await self._maybe_roll_event(group_id)
        # 新事件刚触发 → 广播到所有注册群（当前群已通过 yield 看到）
        if notice.strip():
            try:
                await self._broadcast(notice.strip(), exclude_group=group_id)
            except Exception as _e:
                pass
        cur = db.get_world_event()
        now = int(time.time())
        if not cur:
            yield event.plain_result("🌍 大陆风平浪静……\n" + notice)
            return
        evt = next((e for e in C.WORLD_EVENT_POOL if e["type"] == cur["etype"]), None)
        left = max(0, cur["ends_at"] - now)
        mm, ss = divmod(left, 60)
        lines = [f"🌍 【世界事件】{evt['icon']} {evt['name']}(剩余 {mm}分{ss}秒)" if evt else "🌍 世界事件",
                 f"━━━━━━━━━━━━"]
        if evt:
            lines.append(evt["desc"])
        lines.append("")
        # v98.5：etype 展示数据化 → core/world_event_templates.py DISPLAYS
        from ..core.world_event_templates import DISPLAYS
        disp_fn = DISPLAYS.get(cur["etype"])
        if disp_fn:
            disp_fn(self, cur, lines, group_id)
        lines.append("")
        lines.append(notice)
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?拍卖(?:\s*|$)")
    @require_player()

    async def auction(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        cur = db.get_world_event()
        now = int(time.time())
        if not cur:
            # 是否有过期的拍卖待结算
            expired = db.get_world_event(include_expired=True)
            if expired and expired["etype"] == "auction" and now >= expired["ends_at"]:
                lines = self._settle_auction(expired, group_id)
                db.clear_world_event()
                broadcast_text = f"🏪 【拍卖行 · 落槌结算】\n{lines}"
                try:
                    await self._broadcast(broadcast_text)
                except Exception:
                    pass
                yield event.plain_result(broadcast_text)
                return
            yield event.plain_result("🏪 拍卖行暂未开张。世界事件出现『神秘拍卖行』时再来吧！(『事件』查看)")
            return
        if cur["etype"] != "auction":
            yield event.plain_result("🏪 拍卖行暂未开张。世界事件出现『神秘拍卖行』时再来吧！(『事件』查看)")
            return
        items = cur["data"].get("items", [])
        left = cur["ends_at"] - now
        mm, ss = divmod(left, 60)
        lines = [f"🏪 【神秘拍卖行】(剩余 {mm}分{ss}秒)", "━━━━━━━━━━━━"]
        for it in items:
            top = max(it["bids"].values()) if it["bids"] else 0
            top_name = "无人出价"
            if it["bids"]:
                top_qq = max(it["bids"], key=it["bids"].get)
                tp = self._player(group_id, top_qq)
                top_name = f"{tp['name'] if tp else top_qq}({top})"
            lines.append(f"📦 {it['id']}. {it['name']}")
            lines.append(f"   底价 {it['base']} ｜ 最高：{top_name} ｜ 一口价 {it['buyout']}")
            lines.append(f"   『竞拍 {it['id']} <金币>』出价")
        lines.append("")
        lines.append("💡 出价立即扣款；被超越自动退还；结束最高价者得！")
        yield event.plain_result("\n".join(lines))

    def _settle_auction(self, cur, group_id: str) -> str:
        """拍卖到期结算：最高价者得物品，其余退还。返回结算文本"""
        if not cur or cur["etype"] != "auction":
            return "拍卖行已关闭。"
        items = cur["data"].get("items", [])
        lines = []
        for it in items:
            if it["bids"]:
                top_qq = max(it["bids"], key=it["bids"].get)
                amount = it["bids"][top_qq]
                # 发放装备（v48：品质档英文 ID；key 用唯一 id 而非装备名）
                # v104 P1：直接发放初始化时存好的完整 equip（展示什么发什么），
                # 不再以 lv30/purple 重新生成；旧数据(无 equip)按存字段兜底
                import uuid as _uuid
                equip = it.get("equip") or C.generate_equip(it["slot"], it.get("lv", 30), it.get("quality", "purple"))
                db.add_item(group_id, top_qq, f"eq_{_uuid.uuid4().hex[:8]}", equip, count=1)
                p = self._player(group_id, top_qq)
                name = p["name"] if p else top_qq
                lines.append(f"🎉 {name} 以 {amount} 金币拍得【{it['name']}】！")
                # 退还其他出价者
                for qq2, amt2 in it["bids"].items():
                    if qq2 != top_qq:
                        p2 = self._player(group_id, qq2)
                        if p2:
                            db.update_player(group_id, qq2, gold=p2["gold"] + amt2)
                            lines.append(f"↩️ 退还 {p2['name']} {amt2} 金币")
            else:
                lines.append(f"💤 【{it['name']}】无人出价，流拍。")
        # v104R3 P2：落槌价去向说明（复验点12：赢家金币为系统回收，无文案说明）
        if any(it.get("bids") for it in items):
            lines.append("💰 落槌价已由拍卖行收讫(系统回收)，未成交者的出价已全额退还。")
        return "\n".join(lines)

    @filter.regex(r"^(?:\[At:\d+\]\s*)?竞拍(?:\s*|$)")
    @require_player()

    async def bid(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        args = self._strip_cmd(event, "竞拍").split()
        cur = db.get_world_event()
        now = int(time.time())
        if not cur:
            # 过期的拍卖待结算
            expired = db.get_world_event(include_expired=True)
            if expired and expired["etype"] == "auction" and now >= expired["ends_at"]:
                lines = self._settle_auction(expired, group_id)
                db.clear_world_event()
                broadcast_text = f"🏪 【拍卖行 · 落槌结算】\n{lines}"
                try:
                    await self._broadcast(broadcast_text)
                except Exception:
                    pass
                yield event.plain_result(broadcast_text)
                return
            yield event.plain_result("🏪 拍卖行暂未开张。")
            return
        if cur["etype"] != "auction":
            yield event.plain_result("🏪 拍卖行暂未开张。")
            return
        if len(args) < 2 or not args[0].isdigit() or not args[1].isdigit():
            yield event.plain_result("格式：竞拍 <编号> <金币>，如『竞拍 1 5000』(『拍卖』查看编号)")
            return
        item_id = int(args[0])
        amount = int(args[1])
        items = cur["data"].get("items", [])
        it = next((x for x in items if x["id"] == item_id), None)
        if not it:
            yield event.plain_result("没有这个拍卖品！『拍卖』查看当前物品～")
            return
        if amount < it["base"]:
            yield event.plain_result(f"出价不能低于底价 {it['base']} 金币！")
            return
        if player["gold"] < amount:
            yield event.plain_result(f"你只有 {player['gold']} 金币，出不起 {amount}！")
            return
        # 自己重复出价：新价不能低于自己当前出价（防刷金币：先退旧价再扣新价 = 净赚差价）
        if str(qq_id) in it["bids"] and amount < it["bids"][str(qq_id)]:
            yield event.plain_result(f"不能低于自己当前出价 {it['bids'][str(qq_id)]} 金币！")
            return
        # v104R3 P2：新出价必须严格超过当前最高价（同价出价无意义且锁金币到结算——先到者胜，
        # 后到者金币被冻结直到结算/被超越；直接拒绝，复验点5）
        if it["bids"] and str(qq_id) not in it["bids"]:
            _top_qq = max(it["bids"], key=it["bids"].get)
            if it["bids"][_top_qq] >= amount:
                _tp = self._player(group_id, _top_qq)
                _top_name = _tp["name"] if _tp else _top_qq
                yield event.plain_result(
                    f"当前最高出价是 {_top_name} 的 {it['bids'][_top_qq]} 金币——出价必须超过最高价！")
                return
        # 被超越 → 退还当前最高出价者（并移除其出价记录）
        if it["bids"]:
            top_qq = max(it["bids"], key=it["bids"].get)
            if it["bids"][top_qq] < amount and top_qq != str(qq_id):
                p_top = self._player(group_id, top_qq)
                if p_top:
                    db.update_player(group_id, top_qq, gold=p_top["gold"] + it["bids"][top_qq])
                del it["bids"][top_qq]
        # 自己重复出价 → 退还自己的先前出价
        if str(qq_id) in it["bids"]:
            prev = it["bids"][str(qq_id)]
            db.update_player(group_id, qq_id, gold=player["gold"] + prev)
            del it["bids"][str(qq_id)]
            player = self._player(group_id, qq_id)
        # 扣款并记录
        db.update_player(group_id, qq_id, gold=player["gold"] - amount)
        it["bids"][str(qq_id)] = amount
        db.save_world_event(cur["etype"], cur["ends_at"], cur["data"])
        # 一口价立即成交
        if amount >= it["buyout"]:
            # 退还其他出价者
            for qq2, amt2 in it["bids"].items():
                if qq2 != str(qq_id):
                    p2 = self._player(group_id, qq2)
                    if p2:
                        db.update_player(group_id, qq2, gold=p2["gold"] + amt2)
            equip = it.get("equip") or C.generate_equip(it["slot"], it.get("lv", 30), it.get("quality", "purple"))
            import uuid as _uuid2
            db.add_item(group_id, qq_id, f"eq_{_uuid2.uuid4().hex[:8]}", equip, count=1)
            it["bids"] = {str(qq_id): amount}
            cur["data"]["items"] = [x for x in items if x["id"] != item_id]
            db.save_world_event(cur["etype"], cur["ends_at"], cur["data"])
            yield event.plain_result(f"💰 一口价成交！你以 {amount} 金币拍得【{it['name']}】！\n📦 装备已放入背包(『背包』查看)")
            return
        # v104 P1：出价后如实提示——未超过当前最高(含同价被先到者压)则提示"当前最高仍是 X"，
        # 不再无条件谎报"当前最高"
        _top_qq = max(it["bids"], key=it["bids"].get)
        if _top_qq == str(qq_id):
            yield event.plain_result(f"💰 出价成功！你在【{it['name']}】上出价 {amount} 金币，当前最高！\n(若被超越将自动退还)")
        else:
            _tp = self._player(group_id, _top_qq)
            _top_name = _tp["name"] if _tp else _top_qq
            yield event.plain_result(f"💰 出价成功！你在【{it['name']}】上出价 {amount} 金币，当前最高仍是 {_top_name}({it['bids'][_top_qq]})。\n(若被超越将自动退还)")
