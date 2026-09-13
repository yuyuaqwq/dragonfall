# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - social（social）

由 main.py 拆分而来，作为 Mixin 被 Main 继承。
"""
import functools
import inspect
import random
import re

from ._platform import AstrMessageEvent, MessageChain

from ._declared import declared

from .. import content as C
from .. import db
from ..content_rules.panel import player_final_stats
# v181 P4-5 拍卖状态机服务化（过期结算+清槽单点）——B12-L1 起 auction/bid 正文已进包，
# 过期结算改由包内 `content/social_cmds.py` 走宿主 `services.auction` 句柄调用，本文件不再 import。
from ..commands.base import CommandBase, require_player
# v116 公会成长纵深：新数据表/存取函数不经 __init__ 聚合导出，
# 直接本地 import，避免改动 data/__init__、store/__init__（与并行改动的 agent 冲突）。
# （B9-L3 起 `_G` 的三张公会表已进包，命令层不再直读 `game/data/guild.py`）
from ..store import social as _store_social  # noqa: F401  包门面注入用（模块本体）
from ..store.social import (
    guild_get_member, guild_set_role, guild_spend_contribute,
    market_sell_atomic,
)  # noqa: F401
from ..store.inventory import _snapshot_one  # noqa: F401  v126.4 单件回流快照裁剪

# ============================================================================
# ★ B9-L3：市场/摆摊 + 公会两族实现已进内容包，命令层只留「注册 + 取玩家 + 调包 + 渲染」。
#   · `content/social_stall.py` ← 原 `market` / `_stall_parse_args` / `_stall_resolve` /
#     `_stall_place` / `stall_view` / `换` 等族的解析与守卫（注入 db + MAP_BY_ID /
#     HOUSE_LEVELS / QUALITY / ECON_CONFIG / store.social）
#   · `content/social_guild.py` ← 原 `game/services/guild.py` 全文件 + 公会面板/商店/技能编排
#     （经服务层薄壳 `game/services/guild.py` 取包 = bind_host + 同名单 re-export）
# ★ B12-L1（2026-09-14 收口）：B9-L3 之后剩下的宿主独有实现也已进包 ——
#   · `content/social_cmds.py` ← 原 `_maybe_roll_event` / `world_event` / `auction` / `bid`
#     （世界事件惰性调度 + 事件面板 + 拍卖面板 + 竞拍状态机）全族逐字；
#   · `content/social_pet.py` ← 原 `pet_rename` / `pet_release`（`pet_rename_run` / `pet_release_run`）。
#   至此本文件全部命令 = 「注册 + 取玩家 + 一行转发 + 渲染」薄壳。
# ============================================================================
from .. import bootstrap as _bootstrap          # noqa: E402

_bootstrap.package_apply()                      # 包加载口（幂等；失败抛，不静默）
from content import social_stall as _SS         # noqa: E402
from content import social_pet as _SP           # noqa: E402
from content import social_cmds as _SC          # noqa: E402
from ..services import guild as _GSD            # noqa: E402

_SS.bind_host(db, maps=C.MAP_BY_ID, house_levels=C.HOUSE_LEVELS, quality=C.QUALITY,
              econ=C.ECON_CONFIG, store_social=_store_social)
_SP.bind_host(db, content=C, quality=C.QUALITY)
_SC.bind_host(db=db, content=C)


class SocialCmds(CommandBase):

    @declared("market")
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
        # B9-L3：面板主体在包内（行首编号直接用 DB id，与『购入 <编号>』『下架 <编号>』解析同基准；
        #   原双编号在有过删除/翻页后必然错位 —— report_12 P1-1：『购入 1』买不到第 1 行）。
        lines = _SS.market_view_lines(items, page_items, page, pages, self._player, group_id)
        lines.append(self._tip("market"))
        self._record_list_state(qq_id, "市场", page, pages)
        yield event.plain_result("\n".join(lines))

    @declared("market_sell")
    @require_player()

    async def market_sell(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        args = self._strip_cmd(event, "上架").rsplit(None, 1)
        if len(args) < 2 or not args[1].isdigit() or int(args[1]) < C.ECON_CONFIG["market_min_price"]:
            yield event.plain_result("格式：上架 <物品名> <价格>，如『上架 铁剑 500』；价格至少 1 金币")
            return
        item_name = args[0]
        price = int(args[1])
        # v104R3 P2：上架价格上限——防止 999999999 恶意占坑/诱导高价（上限远超任何物品价值）
        if price > C.ECON_CONFIG["market_price_cap"]:
            yield event.plain_result(f"价格太高啦！上架价最多 {C.ECON_CONFIG['market_price_cap']} 金币～")
            return
        # B9-L3：按名找背包物品 + 单事务原子上架在包内（真源 market_sell 的解析/落库段）
        ok, nm, err = _SS.market_sell_place(group_id, qq_id, item_name, price)
        if not ok:
            yield event.plain_result(err)
            return
        yield event.plain_result(f"📦 已上架【{nm}】，定价 {price} 金币！\n『市场』查看，『下架 <编号>』撤回")

    @declared("market_unsell")
    @require_player()

    async def market_unsell(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        args = self._strip_cmd(event, "下架").split()
        if not args or not args[0].isdigit():
            yield event.plain_result("格式：下架 <编号>，『市场』查看编号")
            return
        mid = int(args[0])
        # B9-L3：目标选取 + 所有权守卫在包内
        ok, it, err = _SS.market_unsell_pick(db.market_list(group_id), mid, qq_id)
        if not ok:
            yield event.plain_result(err)
            return
        db.market_remove(mid)
        # v126.4 审计 P1：下架回流按 1 件，快照只带 1 条个体（防旧整堆快照破坏不变量）
        db.add_item(group_id, qq_id, it["item_key"], _snapshot_one(it["item_data"]), count=1)
        yield event.plain_result(f"↩️ 已下架【{it['item_data'].get('name','?')}】，物品退回背包")

    @declared("market_buy")
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
        # B9-L3：自买/换摊/异地/金币守卫在包内
        ok, err = _SS.market_buy_check(it, player, qq_id)
        if not ok:
            yield event.plain_result(err)
            return
        # F1 P0-2：原子购入（事务内 校验→扣款→删单→发货），替代原 4 次独立 commit
        ok, err, item_name = db.market_buy_atomic(group_id, qq_id, mid)
        if not ok:
            yield event.plain_result(err)
            return
        yield event.plain_result(f"🛒 购入成功！【{item_name}】已放入背包(花费 {it['price']} 金币)")

    # ---------------- v66 摆摊系统（v167 拆分为 摆卖/摆换 两指令，鱼鱼拍板） ----------------
    # 『摆卖 <物/背包序号> <单价> [数量]』= 摆摊出售（金币）
    # 『摆换 <物/背包序号> [数量]』       = 摆摊以物换物（无金币价）
    # 『收摊』『摊位』『换 <编号> <物品>』 维持不变
    # 说明：v167 起废弃老『摆摊』一词（它同时承载卖/换两种语义靠有无价格区分，
    # 与数量参数互相歧义——一介散人『咕噜的皇冠』同名事件暴露按名匹配的坑）。
    # 现在卖/换动作词分开，参数互不冲突；物品支持背包全局序号（『背包』看到的序号）
    # 或名称；同名多件按名会列出候选。老『摆摊』仅作引导提示（v167.1 意见：不静默消失）。
    # ★ B9-L3：解析（`_stall_parse_args`）/按序名解析（`_stall_resolve`）/落位
    #   （`_stall_place`）/价格标签（`_stall_label`）已进包 `content/social_stall.py`。

    @declared("stall_deprecated", priority=5)
    @require_player()
    async def stall_deprecated(self, event: AstrMessageEvent):
        yield event.plain_result("『摆摊』已拆成两条指令啦：\n"
                                 "· 摆卖 = 卖金币：『摆卖 <物品/背包序号> <单价> [数量]』\n"
                                 "· 摆换 = 以物换物：『摆换 <物品/背包序号> [数量]』\n"
                                 "例：『摆卖 3 500 5』(背包第3件×5个，单价500)｜『摆换 铁剑』")

    @staticmethod
    def _stall_label(s):
        """摊位价格标签：price>0 → 'N 金币'；price=0 → '🔄 换'(以物换物)。

        B9-L3：实现已进包（`content/social_stall.py:stall_label`）；本方法只作薄委托 ——
        `game/commands/world.py:2418` 仍按 `self._stall_label(...)` 调用（命令层共用壳）。
        """
        return _SS.stall_label(s)

    @declared("stall_sell")
    @require_player()
    async def stall_sell(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        raw = self._strip_cmd(event, "摆卖").strip()
        parsed = _SS.stall_parse_args(raw, is_sell=True)
        if parsed[0] is None:
            yield event.plain_result(parsed[1])
            return
        item_name, (price, count) = parsed
        if price <= 0:
            yield event.plain_result("摆卖要带金币价！想以物换物用『摆换 <物品> [数量]』～")
            return
        ok, res = _SS.stall_place(group_id, qq_id, player, item_name, price, count)
        if not ok:
            yield event.plain_result(res)
            return
        item_nm, cnt_s, map_name, tip = res
        head = f"🏪 你在『{map_name}』支起了摊位，出售【{item_nm}{cnt_s}】定价 {price} 金币！{tip}\n"
        tail = "『收摊』收摊，『摊位』看看本地谁在摆摊"
        yield event.plain_result(head + tail)

    @declared("stall_exchange_pawn")
    @require_player()
    async def stall_exchange_pawn(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        raw = self._strip_cmd(event, "摆换").strip()
        parsed = _SS.stall_parse_args(raw, is_sell=False)
        if parsed[0] is None:
            yield event.plain_result(parsed[1])
            return
        item_name, (price, count) = parsed
        ok, res = _SS.stall_place(group_id, qq_id, player, item_name, 0, count)
        if not ok:
            yield event.plain_result(res)
            return
        item_nm, cnt_s, map_name, tip = res
        head = f"🔄 你在『{map_name}』支起了换摊——【{item_nm}{cnt_s}】只换不卖！{tip}\n"
        tail = "『收摊』收摊，别人可用『换 <编号> <物品名>』跟你交换"
        yield event.plain_result(head + tail)


    @declared("stall_close")
    @require_player()
    async def stall_close(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        removed = db.market_remove_by_seller(group_id, qq_id)
        if not removed:
            yield event.plain_result("你现在没有摊位。『摆摊 <物品> <价格>』支起摊位～")
            return
        for s in removed:
            # v126.4 审计 P1：收摊回流按 1 件，快照只带 1 条个体
            db.add_item(group_id, qq_id, s["item_key"], _snapshot_one(s["item_data"]), count=1)
        names = "、".join(s["item_data"].get("name", "?") for s in removed)
        yield event.plain_result(f"🏪 收摊！【{names}】退回背包")

    @declared("stall_view")
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
            # B9-L3：面板行在包内
            yield event.plain_result("\n".join(_SS.stall_view_player_lines(target, stalls)))
            return
        # 无参 → 当前地图所有摊位
        cur_map = player.get("cur_map", "")
        stalls = db.market_list(group_id, cur_map)
        if not stalls:
            yield event.plain_result("此地没有摊位。『摆摊 <物品> [价格]』支起你的小摊(不带价格 = 换摊)！")
            return
        yield event.plain_result("\n".join(_SS.stall_view_here_lines(cur_map, stalls, self._player, group_id)))

    @declared("stall_exchange")
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
        # B9-L3：寄售/异地/自己/出售中/背包守卫在包内
        ok, give, err = _SS.stall_exchange_check(it, player, qq_id, group_id, give_name)
        if not ok:
            yield event.plain_result(err)
            return
        # F1 P0-2：原子换摊（单事务：删摊主单→摊主货给买家→扣买家给物→给物送摊主），
        # 替代原 4 次独立 commit（并发双请求只首个成交）
        ok, _ename = db.market_exchange_atomic(group_id, qq_id, mid, give["key"], give["data"])
        if not ok:
            yield event.plain_result(_ename)
            return
        yield event.plain_result(
            f"🔄 交换成功！你用【{give['data']['name']}】换到了【{it['item_data'].get('name','?')}】！\n"
            f"对方的东西已放进你背包，你的【{give['data']['name']}】已送到对方背包～"
        )

    @declared("party")
    @require_player()

    async def party(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        raw_target = self._strip_cmd(event, "组队").strip()
        # P4-6：目标解析/战斗守卫/拉人落库收敛 services.party（resolve_party_target/
        # target_in_battle/party_join）；本命令只留解析后分派 + 文案壳。
        from ..services.party import (
            resolve_party_target, party_in_battle, target_in_battle,
            party_view_lines, party_join,
        )
        target_qq, err = resolve_party_target(group_id, qq_id, raw_target)
        members = db.party_members(group_id, qq_id)
        if target_qq is None and err is not None:
            yield event.plain_result(err)
            return
        if target_qq is None:
            # 面板（无目标）
            if members:
                lines = party_view_lines(group_id, members, get_player=self._player,
                                         final_stats=player_final_stats, display=C.display)
                yield event.plain_result("\n".join(lines))
            else:
                yield event.plain_result("你还没有队伍～『组队 <对方名字>』邀请同群玩家组队！\n💡 组队打怪经验＋10%（野外各自为战，仅经验加成，副本内才并肩作战）")
            return
        if str(target_qq) == str(qq_id):
            yield event.plain_result("不能和自己组队！")
            return
        tname = self._player(group_id, target_qq)
        tname_str = tname["name"] if tname else raw_target
        # v104 M04 P1：战斗/副本中禁止组队/拉人——防把副本队长/队员拉走（原队伍解散→副本僵尸化）、
        # 战斗中拉新人（新人未上锁可双线野外战斗）。队员的副本 battle 行存队长名下，
        # 须用 _instance_battle_for 查副本归属；retreated（撤退保留进度）不算战斗中。
        if party_in_battle(group_id, qq_id):
            yield event.plain_result("⚔️ 你正在战斗中！先打完再组队吧～")
            return
        _tb_state = target_in_battle(group_id, target_qq, inst_battle_hook=self._instance_battle_for)
        if _tb_state:
            if _tb_state == "instance":
                yield event.plain_result(f"⚔️ {tname_str} 正在副本战斗中！等 TA 打完再组队吧～")
            else:
                yield event.plain_result(f"⚔️ {tname_str} 正在战斗中！等 TA 打完再组队吧～")
            return
        # v49：已有队伍时，队长用『组队 <名字>』拉新人（上限 4 人）
        if members:
            if str(members[0]) != str(qq_id):
                yield event.plain_result("你已在队伍中，让队长『组队 <名字>』拉人吧～")
                return
            ok, lines, _my = party_join(group_id, qq_id, target_qq, tname_str, members,
                                        check_achievements=C.check_achievements)
            if ok:
                for ln in lines:
                    yield event.plain_result(ln)
            else:
                yield event.plain_result(lines[0])
            return
        # 无队伍：创建 2 人队（store.party_create 内做战斗/已有队伍闸）
        ok, lines, _my = party_join(group_id, qq_id, target_qq, tname_str, members,
                                    check_achievements=C.check_achievements)
        if ok:
            for ln in lines:
                yield event.plain_result(ln)
        else:
            yield event.plain_result(lines[0])

    @declared("party_leave")
    @require_player()

    async def party_leave(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        # P4-6：退队守卫/副本成员判定/清理落库收敛 services.party（party_leave_check/
        # party_leave_inst_member/party_leave_execute）；本命令只留文案壳。
        from ..services.party import (
            party_leave_check, party_leave_inst_member, party_leave_execute,
        )
        # v104 P1：副本进行中禁止退队——副本 battle 只存队长名下，队长退队会删光队伍行，
        # 之后 _instance_current_members 返回 [] → Boss 不再攻击、击杀/通关零奖励（副本僵尸化）。
        # 非队长（队员）不受限：v104 设计允许队员退队，结算自动剔除退队者。
        blocked, msg = party_leave_check(group_id, qq_id)
        if blocked:
            yield event.plain_result(msg)
            return
        # v104 P1：退队者若正挂在副本队伍中（战斗记录存队长名下）→ 退队后同步清其战斗锁
        # （内存锁 + 可能残留的 battle 行），防 24h 锁残留（_in_battle 自愈只在下次交互才触发）
        inst_member = party_leave_inst_member(group_id, qq_id)
        left, ok_lines, err_lines = party_leave_execute(
            group_id, qq_id, inst_member,
            unlock_battle_hook=self._unlock_battle, player_hook=self._player,
        )
        if left:
            yield event.plain_result(ok_lines[0])
        else:
            yield event.plain_result(err_lines[0])

    @declared("guild_create_cmd")
    @require_player()

    async def guild_create_cmd(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        name = self._strip_cmd(event, "创建公会").strip()[:8]  # 策划 11 章 3.1：公会名 1-8 字
        if not name:
            yield event.plain_result("格式：创建公会 <名字>，如『创建公会 屠龙勇士』")
            return
        if db.guild_get_by_member(qq_id):
            yield event.plain_result("你已经在一个公会里啦！先『退出公会』再加入新的～")
            return
        # B9-L3：等级/金币门槛 + 扣款建会在包内（content/social_guild.py）
        ok, err = _GSD.guild_create_check(player)
        if not ok:
            yield event.plain_result(err)
            return
        ok, gid, err = _GSD.guild_create(group_id, qq_id, player, name)
        if not ok:
            yield event.plain_result(err)
            return
        # v105 M18 P2：创建公会立即判定成就（ach_guild1「加入公会」无需等下次事件）
        C.check_achievements(group_id, qq_id)
        yield event.plain_result(
            f"🏰 【公会创建成功】『{name}』！\n"
            f"你成为了公会会长！\n"
            f"{self._tip('guild')}"
        )

    @declared("guild_join_cmd")
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
        # B9-L3：按名查会 + 入会在包内
        ok, g, err = _GSD.guild_join(group_id, qq_id, name)
        if not ok:
            yield event.plain_result(err)
            return
        # v105 M18 P2：加入公会立即判定成就（ach_guild1「加入公会」无需等下次事件）
        C.check_achievements(group_id, qq_id)
        yield event.plain_result(f"🏰 欢迎加入公会【{g['name']}】！\n{self._tip('guild')}")

    @declared("guild_leave_cmd")
    @require_player()

    async def guild_leave_cmd(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        g = db.guild_get_by_member(qq_id)
        if not g:
            yield event.plain_result("你不在任何公会里～")
            return
        # B9-L3：会长守卫 + 退会在包内
        blocked, msg = _GSD.guild_leave_check(g, qq_id)
        if blocked:
            yield event.plain_result(msg)
            return
        _GSD.guild_leave(g, qq_id)
        yield event.plain_result(f"👋 你已退出公会【{g['name']}】。江湖再见！")

    @declared("guild_disband_cmd")
    @require_player()

    async def guild_disband_cmd(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        g = db.guild_get_by_leader(qq_id)
        if not g:
            yield event.plain_result("只有会长才能解散公会！")
            return
        # B9-L3：解散落库在包内（leader 离开即解散）
        _GSD.guild_disband(g, qq_id)
        yield event.plain_result(f"🏚️ 公会【{g['name']}】已解散……")

    @declared("guild_info")
    @require_player()

    async def guild_info(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        g = db.guild_get_by_member(qq_id)
        if not g:
            yield event.plain_result("你还没有公会！『创建公会 <名字>』(30级＋1000金币)或『加入公会 <名字>』")
            return
        members = db.guild_members(g["gid"])
        page = self._parse_page(self._strip_cmd(event, "公会"))
        page_items, pages, page = self._page_items(members, page, per_page=5)
        # B9-L3：面板主体（头/加成/成员行）在包内；分页用引擎底座、tip 与列表记账是命令层 IO
        lines = _GSD.guild_info_lines(group_id, g, members, page_items, page, pages,
                                      self._player, g["level"] * C.GUILD_EXP_BASE)
        lines.append(self._tip("guild"))
        self._record_list_state(qq_id, "公会", page, pages)
        yield event.plain_result("\n".join(lines))

    @declared("guild_sign")
    @require_player()

    async def guild_sign(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        g = db.guild_get_by_member(qq_id)
        if not g:
            yield event.plain_result("你还没有公会！先『加入公会 <名字>』吧～")
            return
        # B9-L3：签到判定/落库在包内（含每日一次；数值全走 GUILD_CONFIG）
        ok, lines, err = _GSD.guild_sign(group_id, qq_id, g)
        if ok:
            yield event.plain_result(lines[0])
        else:
            yield event.plain_result(err)

    @declared("guild_task")
    @require_player()

    async def guild_task(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        g = db.guild_get_by_member(qq_id)
        if not g:
            yield event.plain_result("你还没有公会！先『加入公会 <名字>』吧～")
            return
        # B9-L3：任务进度（跨天重置）在包内
        ok, lines, err = _GSD.guild_task_view(group_id, qq_id, g)
        if ok:
            yield event.plain_result(lines[0])
        else:
            yield event.plain_result(err)

    @declared("guild_donate_cmd")
    @require_player()

    async def guild_donate_cmd(self, event: AstrMessageEvent):
        """公会捐献：上交材料为公会做贡献，每日一次。

        策划 11 章 4 种公会任务（讨伐/捐献/金币/副本）→ 简化落地：讨伐（击杀自动推进）+ 捐献（上交 3 份材料）。
        进度用 event_state 单独记录（key=guild_donate:{gid}:{qq_id}，值=日期），不与击杀任务共用 task_progress。
        """
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        g = db.guild_get_by_member(qq_id)
        if not g:
            yield event.plain_result("你还没有公会！先『加入公会 <名字>』吧～")
            return
        # B9-L3：捐献判定/扣料/落库在包内（不足文案里的 _tip('guild_donate') 是命令层随机提示壳）
        ok, lines, err, need, total = _GSD.guild_donate(group_id, qq_id, g)
        if ok:
            yield event.plain_result(lines[0])
            return
        if total is not None:
            # 材料不足（need/total 由包内带回）
            yield event.plain_result(err + f"{self._tip('guild_donate')}")
            return
        yield event.plain_result(err)

    @declared("guild_rank")

    async def guild_rank(self, event: AstrMessageEvent):
        # B9-L3：排行行在包内
        lines = _GSD.guild_rank_lines()
        if not lines:
            yield event.plain_result("还没有公会成立！『创建公会 <名字>』建立第一个公会吧～")
            return
        yield event.plain_result("\n".join(lines))

    # ---------------- v116 公会成长纵深：公会商店 / 公会技能 / 职位体系 ----------------

    @declared("guild_shop")
    @require_player()

    async def guild_shop(self, event: AstrMessageEvent):
        """公会商店：『公会商店』查看，『公会商店 <编号>』用公会积分购买。
        v116 公会成长纵深：积分 = 成员贡献（guild_members.contribute），
        由『公会签到』『公会捐献』获得。B9-L3 起面板/购买在包内（content/social_guild.py）。"""
        group_id, qq_id = self._uid(event)
        g = db.guild_get_by_member(qq_id)
        if not g:
            yield event.plain_result("你还没有公会！先『加入公会 <名字>』吧～")
            return
        member = guild_get_member(g["gid"], qq_id)
        raw = self._strip_cmd(event, "公会商店").strip()
        # 带编号 → 购买
        if raw.isdigit():
            for _line in _GSD.guild_shop_buy(group_id, qq_id, g, member, int(raw)):
                yield event.plain_result(_line)
            return
        if not member:
            yield event.plain_result("你不是公会正式成员～")
            return
        lines = _GSD.guild_shop_lines(g, member)
        lines.append(self._tip("guild_shop"))
        yield event.plain_result("\n".join(lines))

    @declared("guild_skill_view")
    @require_player()

    async def guild_skill_view(self, event: AstrMessageEvent):
        """公会技能：查看技能列表与等级门槛/积分价目。
        v116 说明：技能购买记录无处可靠持久化（guild_members 无通用 JSON 列，
        且本轮禁改 connection.py 表结构），故本轮只做【展示 + 数据】，购买落地留待下轮。
        战斗加成挂接同样延后（需在战斗结算统一钩取成员已学技能）。B9-L3 起面板在包内。"""
        group_id, qq_id = self._uid(event)
        g = db.guild_get_by_member(qq_id)
        if not g:
            yield event.plain_result("你还没有公会！先『加入公会 <名字>』吧～")
            return
        lines = _GSD.guild_skill_lines(g)
        lines.append("💡 技能经会长安排后逐步开放；战斗加成的挂接正在开发中～")
        yield event.plain_result("\n".join(lines))

    @declared("guild_appoint")
    @require_player()

    async def guild_appoint(self, event: AstrMessageEvent):
        """公会任命：会长任命成员为 副会长/精英。
        用法：『公会任命 <成员名> <职位>』；职位可选 副会长/精英。
        门槛：副会长需公会 Lv.3（GUILD_CONFIG.vice_leader_level），精英无门槛。"""
        group_id, qq_id = self._uid(event)
        g = db.guild_get_by_leader(qq_id)
        if not g:
            yield event.plain_result("只有会长才能任命职位！")
            return
        raw = self._strip_cmd(event, "公会任命").strip()
        parts = raw.rsplit(None, 1)
        if len(parts) < 2:
            yield event.plain_result("格式：公会任命 <成员名> <职位>，职位=副会长/精英")
            return
        name_arg, role_arg = parts
        # B9-L3：role 映射/等级门槛/成员校验/任命落库全在包内
        role = _GSD.guild_appoint_check_role(role_arg)
        if not role:
            yield event.plain_result("可任命职位：副会长、精英。成员是默认职，不需任命～")
            return
        ok, err = _GSD.guild_appoint_level_ok(g, role)
        if not ok:
            yield event.plain_result(err)
            return
        tm, target, err = _GSD.guild_find_member(g, name_arg)
        if err:
            yield event.plain_result(err)
            return
        if target["qq_id"] == qq_id:
            yield event.plain_result("会长不需要任命自己～")
            return
        if tm["role"] == role:
            yield event.plain_result(f"『{target['name']}』已经是{role_arg}了～")
            return
        _label, _icon = _GSD.guild_appoint(g, target, role)
        yield event.plain_result(f"{_icon} 任命成功！『{target['name']}』已晋升为公会【{_label}】！")

    @declared("guild_demote")
    @require_player()

    async def guild_demote(self, event: AstrMessageEvent):
        """公会免职：会长将 副会长/精英 降回成员。
        用法：『公会免职 <成员名>』"""
        group_id, qq_id = self._uid(event)
        g = db.guild_get_by_leader(qq_id)
        if not g:
            yield event.plain_result("只有会长才能免职！")
            return
        name_arg = self._strip_cmd(event, "公会免职").strip()
        if not name_arg:
            yield event.plain_result("格式：公会免职 <成员名>")
            return
        # B9-L3：成员校验/免职落库在包内
        tm, target, err = _GSD.guild_find_member(g, name_arg)
        if err:
            yield event.plain_result(err)
            return
        if tm["role"] not in ("vice_leader", "elite"):
            yield event.plain_result(f"『{target['name']}』是成员，无需免职～")
            return
        _GSD.guild_demote(g, target)
        yield event.plain_result(f"📉 已免去『{target['name']}』的职位，降回普通成员～")


    @declared("pet_view")
    @require_player()

    async def pet_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        # B9-L3：面板（含饱食度衰减结算+持久化 / 品质·出处 / 技能 / 亲密度 / 加成行）在包内
        lines, has_pet = _SP.pet_view(qq_id)
        if not has_pet:
            yield event.plain_result("\n".join(lines))
            return
        lines.append(self._tip("pet"))
        yield event.plain_result("\n".join(lines))

    @declared("pet_rename")
    @require_player()

    async def pet_rename(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        # B12-L1：存在守卫 / 取前 8 字 / 落库在包内（content/social_pet.py:pet_rename_run）
        raw_name = self._strip_cmd(event, "宠物改名")
        for _line in _SP.pet_rename_run(qq_id, raw_name):
            yield event.plain_result(_line)

    @declared("pet_feed")
    @require_player()

    async def pet_feed(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        mat_name = self._strip_cmd(event, "喂养").strip()
        # B9-L3：无参食物清单 / 批量双格式解析 / 食物白名单 / 喂养结算（含升级循环）全在包内
        for _line in _SP.pet_feed(group_id, qq_id, mat_name):
            yield event.plain_result(_line)

    @declared("pet_release")
    @require_player()

    async def pet_release(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        # B12-L1：存在守卫 + 放生落库 + 文案在包内（content/social_pet.py:pet_release_run）
        # 图鉴记录保留（24 章三：放生后宠物蛋可重新掉落，图鉴记录保留）
        for _line in _SP.pet_release_run(qq_id):
            yield event.plain_result(_line)

    @declared("mount_cmd")
    @require_player()

    async def mount_cmd(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        msg = event.get_message_str()
        raw = self._strip_cmd(event, "骑乘") if msg.startswith(("骑乘", "[At:")) else ""
        # B9-L3：骑乘/下马/面板三支的判定与文案全在包内；`_tip("mount")` 包内按需惰性取
        #（「有坐骑」分支才取随机提示 —— 提前取会多消耗一次 random 抽签）
        for _line in _SP.mount_run(group_id, qq_id, player, raw, msg, msg.strip(),
                                   lambda: self._tip("mount")):
            yield event.plain_result(_line)

    async def _maybe_roll_event(self, group_id: str) -> str:
        """（B12-L1 薄壳：转调包内 `content/social_cmds.maybe_roll_event`，实现真源已进包）"""
        return await _SC.maybe_roll_event(group_id, self._broadcast)

    @declared("world_event")
    @require_player()

    async def world_event(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        # B12-L1：惰性调度（含过期拍卖先结算后清槽）/ 事件面板 / DISPLAYS 展示全在包内
        notice = await self._maybe_roll_event(group_id)
        for _line in await _SC.world_event_run(group_id, notice, self._broadcast, self):
            yield event.plain_result(_line)

    @declared("auction")
    @require_player()

    async def auction(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        # B12-L1：面板主体 / 过期结算+广播全在包内；`_tip("auction")` 按真源**惰性**取
        #（只有「开张」分支才抽提示，提前取会多消耗一次 random 抽签）
        for _line in await _SC.auction_run(group_id, self._player,
                                           lambda: self._tip("auction"), self._broadcast):
            yield event.plain_result(_line)

    def _settle_auction(self, cur, group_id: str) -> str:
        """（v181 P4-5 兼容壳：转调 game/services/auction.settle_auction——拍卖到期结算本体已下沉 service）"""
        from ..services.auction import settle_auction as _sa
        return _sa(cur, group_id)

    @declared("bid")
    @require_player()

    async def bid(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        args = self._strip_cmd(event, "竞拍").split()
        # B12-L1：底价/金币/自己重复出价守卫 + 被超越退还 + 一口价成交 + 过期结算全在包内
        for _line in await _SC.bid_run(group_id, qq_id, player, args,
                                       self._player, self._broadcast):
            yield event.plain_result(_line)
