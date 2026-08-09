# -*- coding: utf-8 -*-
"""《剑与魔法》命令层 - economy（economy）

由 main.py 拆分而来，作为 Mixin 被 Main 继承。
"""
import asyncio
import functools
import inspect
import json
import random
import re
import time

from astrbot.api import star
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.core.message.message_event_result import MessageChain
from astrbot.core.message.components import Plain

from .. import content as C
from .. import db
from .. import engine as E
from .. import battle as BT
from ..commands.base import CommandBase


class EconomyCmds(CommandBase):
    """背包/装备/锻造/强化/商店/采集/垂钓/炼金"""

    BAG_FILTER_TYPES = ["装备", "材料", "消耗品", "符文", "宠物蛋", "坐骑", "图纸", "鱼"]

    def _gather_roll(self, level: int, prof_lv: int = 1) -> list:
        """按等级采集材料：价格区间匹配等级段；副业等级提高产出数量与稀有度"""
        import random as _rnd
        # 材料按价格分档（价格 ~ 等级*6 附近）
        cand = [name for name, m in C.MATERIALS.items()
                if 3 + level * 4 <= m["price"] <= 20 + level * 8]
        if not cand:
            cand = list(C.MATERIALS.keys())
        # 副业等级加成：Lv.3+ 概率采到 2 份材料；Lv.6+ 概率 3 份
        n = _rnd.randint(1, 2)
        if prof_lv >= 3 and _rnd.random() < 0.3:
            n += 1
        if prof_lv >= 6 and _rnd.random() < 0.25:
            n += 1
        return [_rnd.choice(cand) for _ in range(n)]

    # ---------------- 等待型副业（v55：垂钓/采集/挖掘） ----------------
    # 基准等待（秒）随机范围：fish/gather 45~75，mining 65~115；副业等级每级 -5%（上限 -50%），保底 10 秒
    _PROF_WAIT_BASE = {
        "fishing": (45, 75, "垂钓"),
        "gather": (45, 75, "采集"),
        "mining": (65, 115, "挖掘"),
    }

    def _prof_wait_key(self, group_id, qq_id):
        # v83: 去掉 group_id —— 等待型副业按玩家全局互斥，防止跨群双开多刷
        return f"prof_wait_{qq_id}"

    def _prof_wait_state(self, group_id, qq_id):
        """读取进行中的等待型副业状态(无/损坏返回 None)"""
        raw = db.get_event_state(self._prof_wait_key(group_id, qq_id))
        if not raw:
            return None
        try:
            st = json.loads(raw)
        except (ValueError, TypeError):
            return None
        if not isinstance(st, dict) or not st.get("finish"):
            return None
        return st

    def _prof_wait_clear(self, group_id, qq_id):
        db.set_event_state(self._prof_wait_key(group_id, qq_id), "")

    def _prof_wait_duration(self, prof_type, prof_lv):
        """等待时长：基准随机范围 ±25%，副业等级每级－5%(上限－50%)，保底 10 秒"""
        low, high, _ = self._PROF_WAIT_BASE[prof_type]
        wait = random.randint(low, high)
        wait = int(wait * (1 - 0.05 * min(prof_lv, 10)))
        return max(wait, 10)

    def _prof_wait_begin(self, event, group_id, qq_id, prof_type, extra=None):
        """开始一轮等待型副业：存完成时间戳 + 尽力而为的延迟推送(失败由惰性结算兜底)"""
        prof_lv = db.get_prof_level(group_id, qq_id, prof_type)
        wait = self._prof_wait_duration(prof_type, prof_lv)
        finish = int(time.time()) + wait
        st = {"finish": finish, "type": prof_type}
        if extra:
            st.update(extra)
        db.set_event_state(self._prof_wait_key(group_id, qq_id), json.dumps(st, ensure_ascii=False))
        try:
            asyncio.get_running_loop()
            asyncio.create_task(self._prof_delayed_push(event, group_id, qq_id, st, wait))
        except Exception:
            pass  # 无事件循环（测试环境）或任务创建失败 → 惰性结算兜底
        return wait

    async def _prof_delayed_push(self, event, group_id, qq_id, st, wait):
        """延迟结算并主动推送结果(尽力而为；进程重启/推送失败由惰性结算兜底)"""
        try:
            await asyncio.sleep(wait)
            cur = self._prof_wait_state(group_id, qq_id)
            if not cur or cur.get("finish") != st.get("finish"):
                return  # 已被惰性结算
            text = self._prof_settle(group_id, qq_id, cur)
            if text and hasattr(event, "send"):
                await event.send(MessageChain([Plain(text)]))
        except Exception:
            pass

    def _prof_settle(self, group_id, qq_id, st):
        """结算等待型副业(入包/经验/每日任务)，返回结果文本；先清状态防双结算"""
        self._prof_wait_clear(group_id, qq_id)
        prof_type = st.get("type")
        if prof_type == "fishing":
            return self._settle_fishing(group_id, qq_id, st)
        if prof_type == "gather":
            return self._settle_gather(group_id, qq_id, st)
        if prof_type == "mining":
            return self._settle_mining(group_id, qq_id, st)
        return None

    def _settle_fishing(self, group_id, qq_id, st):
        player = db.get_player(group_id, qq_id)
        if not player:
            return None
        prof_lv = db.get_prof_level(group_id, qq_id, "fishing")
        spot = st.get("spot", "水边")
        # v83 16 章 4.x：彩蛋收藏鱼（独立判定，纯收藏惊喜）
        _cf = C.roll_collect_fish(st.get("spot_map"), C.current_period() == "night")
        # 9.3：钓点差异化（禁出档位 + 品种限定水域），roll_fish 按 16 章五档权重表
        fish = C.roll_fish(prof_lv, st.get("spot_map"))
        db.bump_fishing(group_id, qq_id)
        fname = fish["name"]
        fq = fish.get("quality", "white")
        # 品质标记：白档不显示，绿/蓝/紫/橙 ✦品质（16 章 1.1 定稿）
        q_mark = "" if fq == "white" else f"✦{C.FISH_QUALITY_CN.get(fq, fq)}"
        q_name = f"{q_mark}·{fname}" if q_mark else fname
        # 垂钓经验：白 1 / 绿 1 / 蓝 2 / 紫 3 / 橙 5（16 章 2.6）
        f_exp = C.FISH_EXP.get(fq, 1)
        # 出货文案按档位（16 章 2.6）
        _catch_line = {
            "blue": "水面泛起奇异的光晕…",
            "purple": "鱼线猛地绷紧！",
            "orange": "一道金光破水而出——",
        }.get(fq, "")
        catch_pre = f"{_catch_line}\n" if _catch_line else ""
        # 鱼王：全服公告 + 鱼王计数
        if fish["type"] == "鱼王":
            db.bump_fish_king(group_id, qq_id)
            gold = 300 + player["level"] * 10
            db.update_player(group_id, qq_id, gold=player["gold"] + gold)
            new_lv, leveled = db.add_prof_exp(group_id, qq_id, "fishing", f_exp)
            lv_msg = f"\n🌟 垂钓等级提升到 Lv.{new_lv}！" if leveled else ""
            # 阶段九：垂钓次数 + 鱼王成就
            db.bump_stats(group_id, qq_id, fish_count=1)
            C.check_achievements(group_id, qq_id, player, {"fish_king": True})
            _cf_line = self._collect_bonus_line(group_id, qq_id, player, _cf)
            return (f"🐉 天啊！你在{spot}钓上了【{q_name}】！！\n"
                    f"鱼王出水，水波震荡，岸边的旅人都看呆了！\n"
                    f"💰 获得 {gold} 金币的赏金！{lv_msg}\n"
                    f"📜 你的图鉴记下了这传说的一笔……{_cf_line}")
        # 宝物宝箱：立即开
        if fish["type"] == "宝物":
            import uuid
            gold = random.randint(30, 80) + player["level"] * 3
            db.update_player(group_id, qq_id, gold=player["gold"] + gold)
            new_lv, leveled = db.add_prof_exp(group_id, qq_id, "fishing", f_exp)
            lv_msg = f"\n🌟 垂钓等级提升到 Lv.{new_lv}！" if leveled else ""
            db.bump_stats(group_id, qq_id, fish_count=1)
            C.check_achievements(group_id, qq_id, player)
            extra = ""
            if random.random() < 0.5:
                bp = C.roll_blueprint(max(1, player["level"]))
                db.add_item(group_id, qq_id, f"eq_{uuid.uuid4().hex[:8]}", bp)
                extra = f"\n📜 宝箱里还有：{bp['name']}！"
            _cf_line = self._collect_bonus_line(group_id, qq_id, player, _cf)
            return (f"{catch_pre}🎣 你在{spot}钓上来了一个【{q_name}】！\n"
                    f"打开一看：💰 {gold} 金币！{extra}{lv_msg}{_cf_line}")
        if fish["type"] == "垃圾":
            new_lv, leveled = db.add_prof_exp(group_id, qq_id, "fishing", f_exp)
            lv_msg = f"\n🌟 垂钓等级提升到 Lv.{new_lv}！" if leveled else ""
            db.bump_stats(group_id, qq_id, fish_count=1)
            C.check_achievements(group_id, qq_id, player)
            _cf_line = self._collect_bonus_line(group_id, qq_id, player, _cf)
            return f"🎣 你在{spot}钓上来一个【{q_name}】……唉，今天的运气不太好。{lv_msg}{_cf_line}"
        # 鱼/材料入背包（9.3：mat_ ID 入包 + quality 字段，16 章 2.7 禁动态中文 key）
        mat_key = C.resolve("materials", fname)
        db.add_item(group_id, qq_id, mat_key,
                    {"name": fname, "type": fish["type"], "stackable": True,
                     "price": fish["price"], "quality": fq})
        new_lv, leveled = db.add_prof_exp(group_id, qq_id, "fishing", f_exp)
        lv_msg = f"\n🌟 垂钓等级提升到 Lv.{new_lv}！" if leveled else ""
        _done, _msg = self._daily_prof_bump(group_id, qq_id, "fishing")
        lv_msg += _msg
        # 阶段九：垂钓次数 + 成就判定
        db.bump_stats(group_id, qq_id, fish_count=1)
        C.check_achievements(group_id, qq_id, player)
        _cf_line = self._collect_bonus_line(group_id, qq_id, player, _cf)
        # 24 章二：月光兔蛋特殊渠道——垂钓传说档（orange）15% 概率（真稀有原则）
        _pet_egg_line = ""
        if fq == "orange" and random.random() < 0.15:
            egg = C.make_pet_egg("pet_rabbit")
            db.add_item(group_id, qq_id, f"petegg_pet_rabbit", egg)
            _pet_egg_line = f"\n🥚 咦？鱼肚子里藏着一枚【{egg['name']}】！『使用 宠物蛋』孵化！"
        return (f"{catch_pre}🎣 你在{spot}钓上来一条【{q_name}】！\n"
                f"📦 {fish['desc']}(可『出售 {fname}』，价值 {fish['price']} 金币){lv_msg}{_cf_line}{_pet_egg_line}")

    def _collect_bonus_line(self, group_id, qq_id, player, cf):
        """彩蛋收藏鱼入包 + 计数 + 成就，返回提示行(未命中返回空串)"""
        if not cf:
            return ""
        db.add_item(group_id, qq_id, cf["id"],
                    {"name": cf["name"], "type": "收藏", "stackable": True, "price": 1})
        db.bump_stats(group_id, qq_id, catch_collect=1)
        C.check_achievements(group_id, qq_id, player, {"collect_fish": cf["id"]})
        return (f"\n🌈 水面忽然泛起奇异的光——【{cf['name']}】跃出水面！\n"
                f"　它美得不像凡物，你小心翼翼地收进了图鉴(彩蛋收藏品，回收仅 1 金币)")

    def _settle_gather(self, group_id, qq_id, st):
        player = db.get_player(group_id, qq_id)
        if not player:
            return None
        prof = db.get_prof_level(group_id, qq_id, "gather")
        mats = self._gather_roll(player["level"], prof)
        got = []
        for mat in mats:
            mname = C.display("materials", mat)
            db.add_item(group_id, qq_id, mat, {"name": mname, "type": "材料", "stackable": True, "price": C.MATERIALS[mat]["price"]})
            got.append(f"{mname}x1")
        new_lv, leveled = db.add_prof_exp(group_id, qq_id, "gather", 1)
        lv_msg = f"\n🌟 采集等级提升到 Lv.{new_lv}！" if leveled else ""
        _done, _msg = self._daily_prof_bump(group_id, qq_id, "gather")
        lv_msg += _msg
        # 阶段九：采集次数 + 成就判定
        db.bump_stats(group_id, qq_id, gather_count=1)
        C.check_achievements(group_id, qq_id, player)
        cur_map = C.MAP_BY_ID.get(player["cur_map"], {})
        # 24 章二：月光兔蛋特殊渠道——采集稀有产出 10% 概率（稀有材料判定参考 _gather_roll 的高价段）
        _pet_egg_line = ""
        rare_hit = any(C.MATERIALS[m].get("price", 0) >= 150 for m in mats)
        if rare_hit and random.random() < 0.10:
            egg = C.make_pet_egg("pet_rabbit")
            db.add_item(group_id, qq_id, "petegg_pet_rabbit", egg)
            _pet_egg_line = f"\n🥚 草丛深处有一枚【{egg['name']}】！『使用 宠物蛋』孵化！"
        return (f"🌿 采集完成！你在【{cur_map.get('name', '？')}】采到了：\n"
                f"{'、'.join(got)}\n"
                f"💡 『背包』查看，『出售 <名称>』变现～{lv_msg}{_pet_egg_line}")

    def _settle_mining(self, group_id, qq_id, st):
        player = db.get_player(group_id, qq_id)
        if not player:
            return None
        prof = db.get_prof_level(group_id, qq_id, "mining")
        ores = [m for m, mm in C.MATERIALS.items()
                if any(k in mm.get("name", "") for k in ["矿石", "秘银", "精钢", "结晶", "核心", "碎片", "石", "精华"])]
        if not ores:
            ores = list(C.MATERIALS.keys())
        if prof >= 4:
            rare = [m for m in ores if C.MATERIALS[m]["price"] >= 150]
            if rare and random.random() < (0.15 if prof < 7 else 0.30):
                ore = random.choice(rare)
            else:
                ore = random.choice(ores)
        else:
            ore = random.choice(ores)
        n = random.randint(1, 2)
        if prof >= 5 and random.random() < 0.3:
            n += 1
        oname = C.display("materials", ore)
        db.add_item(group_id, qq_id, ore, {"name": oname, "type": "材料", "stackable": True, "price": C.MATERIALS[ore]["price"]})
        new_lv, leveled = db.add_prof_exp(group_id, qq_id, "mining", 1)
        lv_msg = f"\n🌟 挖掘等级提升到 Lv.{new_lv}！" if leveled else ""
        _done, _msg = self._daily_prof_bump(group_id, qq_id, "mining")
        lv_msg += _msg
        # 阶段九：挖掘次数 + 成就判定
        db.bump_stats(group_id, qq_id, mine_count=1)
        C.check_achievements(group_id, qq_id, player)
        return f"⛏️ 矿脉敲开了！你获得了 {oname} x{n}！(『背包』查看){lv_msg}"

    def _prof_wait_flow(self, event, group_id, qq_id, prof_type, extra=None, begin_text=""):
        """等待型副业统一流程：进行中→提示剩余；到期→先结算再开新一轮；无→开新一轮。
        返回 (回复文本, 是否开启新一轮)。"""
        st = self._prof_wait_state(group_id, qq_id)
        now = int(time.time())
        if st and st["finish"] > now:
            left = st["finish"] - now
            tname = self._PROF_WAIT_BASE.get(st["type"], (0, 0, "副业"))[2]
            return f"⏳ 你还在{tname}呢，再有 {left} 秒就完成啦～(完成会自动入包)", False
        settle_text = None
        if st:
            settle_text = self._prof_settle(group_id, qq_id, st)
        wait = self._prof_wait_begin(event, group_id, qq_id, prof_type, extra)
        head = f"{settle_text}\n" if settle_text else ""
        return f"{head}{begin_text}{wait} 秒后完成，自动入包～", True

    @filter.regex(r"^(?:\[At:\d+\]\s*)?采集(?:\s*|$)")

    async def gather(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        ok, act_msg = self._prof_active_check(group_id, qq_id, "gather")
        if not ok:
            yield event.plain_result(act_msg)
            return
        cur_map = C.MAP_BY_ID.get(player["cur_map"], {})
        if cur_map.get("type") == "城镇区域":
            yield event.plain_result("城镇里没有可采集的野生物资，去野外吧（『前往 <地图名>』）！")
            return
        # v94 体力：采集消耗 5 体力
        _ok, _st = self._spend_stamina(group_id, qq_id, 5, player, "采集")
        if not _ok:
            yield event.plain_result(_st)
            return
        # v55 等待制（原 60 秒 CD 改为随机等待，自动入包，等级减时）
        text, _ok = self._prof_wait_flow(
            event, group_id, qq_id, "gather",
            begin_text=f"🌿 你俯身开始采集【{cur_map.get('name', '？')}】的野生物资……预计 ",
        )
        yield event.plain_result(act_msg + text)

    @filter.regex(r"^(?:\[At:\d+\]\s*)?挖掘(?:\s*|$)")

    async def mining(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        ok, act_msg = self._prof_active_check(group_id, qq_id, "mining")
        if not ok:
            yield event.plain_result(act_msg)
            return
        cur_map = C.MAP_BY_ID.get(player["cur_map"], {})
        # 矿脉点（v13：明确配置，地图上显示⛏️）
        if cur_map.get("id") not in C.MINE_SPOTS:
            yield event.plain_result("这里没有矿脉！地图上会显示⛏️矿脉的位置，去那边『挖掘』吧～")
            return
        # v87.17 子区域绑定：矿脉在指定子区域，不在那边挖不了
        _mine = C.MINE_SPOTS[cur_map.get("id")]
        _mine_sa = _mine.get("subarea", "") if isinstance(_mine, dict) else ""
        if _mine_sa and player.get("cur_subarea") != _mine_sa:
            _sa_name = ""
            for _s in (cur_map.get("subareas") or []):
                if _s["id"] == _mine_sa:
                    _sa_name = _s.get("name", "")
                    break
            _mine_name = _mine.get("name", "矿脉") if isinstance(_mine, dict) else str(_mine)
            yield event.plain_result(
                f"⛏️ {_mine_name}在{_sa_name or _mine_sa}那边，这里没有矿！（『前往 {_sa_name or _mine_sa}』）"
            )
            return
        # v94 体力：挖掘消耗 5 体力
        _ok, _st = self._spend_stamina(group_id, qq_id, 5, player, "挖掘")
        if not _ok:
            yield event.plain_result(_st)
            return
        # v55 等待制（原 90 秒 CD 改为随机等待，自动入包，等级减时）
        text, _ok = self._prof_wait_flow(
            event, group_id, qq_id, "mining",
            begin_text=f"⛏️ 你举起镐子凿向【{cur_map.get('name', '？')}】的矿脉……预计 ",
        )
        yield event.plain_result(act_msg + text)

    @filter.regex(r"^(?:\[At:\d+\]\s*)?炼金(?:[\s\S]*)$")

    async def alchemy(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        raw = self._strip_cmd(event, "炼金").strip()
        page = int(raw) if raw.isdigit() else 1
        prof_lv = db.get_prof_level(group_id, qq_id, "alchemy")
        recs = [(k, r) for k, r in C.ALCHEMY_RECIPES.items()]
        recs.sort(key=lambda x: x[1].get("need_prof_lv", 1))
        page_items, pages, page = self._page_items(recs, page, per_page=5)
        lines = [f"🧪 【炼金工坊】(炼金 Lv.{prof_lv})材料合成配方：", "━━━━━━━━━━━━"]
        base = (page - 1) * 5
        for i, (rname, r) in enumerate(page_items, 1):
            def _mname(k):
                return C.display("materials", k) if k.startswith("mat_") else C.display("items", k)
            cost = " + ".join(f"{_mname(m)}×{c}" for m, c in r["cost"].items())
            pname = next(iter(r["product"]))
            pname2 = _mname(pname)
            need = r.get("need_prof_lv", 1)
            mark = "✅" if prof_lv >= need else "🔒"
            lines.append(f"{base + i:>2}. {mark} {C.display('alchemy', rname)}：{cost} → {pname2}  [炼金Lv.{need}]")
            lines.append(f"    {r['desc']}")
        lines.append("━━━━━━━━━━━━")
        lines.append(f"📄 第 {page}/{pages} 页" + (f"｜『炼金 {page + 1}』下一页" if page < pages else ""))
        lines.append("💡 『合成 <配方名>』，如『合成 治疗药水』；🔒 = 炼金等级不够")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?合成(?:\s*|$)")

    async def alchemy_craft(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        ok, act_msg = self._prof_active_check(group_id, qq_id, "alchemy")
        if not ok:
            yield event.plain_result(act_msg)
            return
        rname = self._strip_cmd(event, "合成").strip()
        if not rname:
            yield event.plain_result("格式：合成 <配方名>！『炼金』查看全部配方～")
            return
        # v48：配方 key 已是 ID，用户输入中文名需 resolve
        rkey = C.resolve("alchemy", rname)
        r = C.ALCHEMY_RECIPES.get(rkey)
        if not r:
            yield event.plain_result(f"没有『{rname}』这个配方！『炼金』查看全部～")
            return
        # v54 副业等级限制
        prof_lv = db.get_prof_level(group_id, qq_id, "alchemy")
        need = r.get("need_prof_lv", 1)
        if prof_lv < need:
            yield event.plain_result(
                f"【{C.display('alchemy', rkey)}】需要炼金 Lv.{need}，你才 Lv.{prof_lv}！多合成低级配方升级炼金吧～"
            )
            return
        # v94 体力：炼金合成消耗 10 体力
        _ok, _st = self._spend_stamina(group_id, qq_id, 10, player, "炼金")
        if not _ok:
            yield event.plain_result(_st)
            return
        items = db.get_inventory(group_id, qq_id)
        # 检查材料是否够（背包 data.name 存中文，r.cost key 是 ID）
        for mat, cnt in r["cost"].items():
            mname = C.display("materials", mat)
            have = sum(it["count"] for it in items if it["data"].get("name") == mname)
            if have < cnt:
                yield event.plain_result(f"材料不足！需要 {mname}×{cnt}(你有 {have})")
                return
        # 扣除材料
        for mat, cnt in r["cost"].items():
            mname = C.display("materials", mat)
            remain = cnt
            for it in items:
                if remain <= 0:
                    break
                if it["data"].get("name") == mname:
                    take = min(it["count"], remain)
                    db.remove_item(group_id, qq_id, it["key"], take)
                    remain -= take
        # 发放产物（v48：product key 已是 ID，直接按 ID 入库）
        lines = []
        for pkey, pcnt in r["product"].items():
            if pkey.startswith("mat_"):
                mname = C.display("materials", pkey)
                db.add_item(group_id, qq_id, pkey, {"name": mname, "type": "材料", "stackable": True, "price": C.MATERIALS.get(pkey, {}).get("price", 150)})
                lines.append(f"  🎒 获得材料：{mname} ×{pcnt}")
            else:
                itdef = C.ITEMS.get(pkey, {})
                db.add_item(group_id, qq_id, pkey, {"name": itdef.get("name", pkey), "type": "消耗品", "stackable": True, "price": itdef.get("price", 100), **({k: v for k, v in itdef.items() if k in ("heal", "mana", "effect")})}, count=pcnt)
                lines.append(f"  🎒 获得：{itdef.get('name', pkey)} ×{pcnt}")
        # 副业经验（炼金成功 +1）
        new_lv, leveled = db.add_prof_exp(group_id, qq_id, "alchemy", 1)
        lv_msg = ""
        if leveled:
            lv_msg = f"\n🌟 炼金等级提升到 Lv.{new_lv}！"
        # 每日任务推进
        _done, _msg = self._daily_prof_bump(group_id, qq_id, "alchemy")
        lv_msg += _msg
        # 阶段九：炼金次数 + 成就判定
        db.bump_stats(group_id, qq_id, alchemy_count=1)
        C.check_achievements(group_id, qq_id, player)
        yield event.plain_result(act_msg + f"🧪 【炼金成功】合成了【{C.display('alchemy', rkey)}】！\n" + "\n".join(lines) + lv_msg)

    @filter.regex(r"^(?:\[At:\d+\]\s*)?烹饪列表(?:\s*|$)")

    async def cooking_list(self, event: AstrMessageEvent):
        """烹饪配方列表(按烹饪等级解锁)"""
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        cook_lv = db.get_prof_level(group_id, qq_id, "cooking")
        lines = ["🍳 【烹饪灶台】料理配方：", "━━━━━━━━━━━━"]
        for i, (rkey, r) in enumerate(C.COOKING_RECIPES.items(), 1):
            lock = "" if cook_lv >= r["min_lv"] else " 🔒"
            def _mname(k):
                return C.display("materials", k) if k.startswith("mat_") else C.display("fish", k)
            cost = " + ".join(f"{_mname(m)}×{c}" for m, c in r["cost"].items())
            lines.append(f"{i:>2}. {r['name']}(烹饪Lv.{r['min_lv']}){lock}")
            lines.append(f"    {cost} → {C.display('items', next(iter(r['product'])))}")
        lines.append("")
        lines.append(f"💡 你当前烹饪等级 Lv.{cook_lv}，『烹饪 <料理名>』制作(如：烹饪 鱼汤)")
        lines.append("💡 烹饪等级：采集植物 + 垂钓 → 料理，成功制作＋1 经验")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?烹饪(?:\s*|$)")

    async def cooking(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        ok, act_msg = self._prof_active_check(group_id, qq_id, "cooking")
        if not ok:
            yield event.plain_result(act_msg)
            return
        raw = self._strip_cmd(event, "烹饪").strip()
        if not raw or raw == "列表":
            yield event.plain_result("发『烹饪列表』查看全部料理配方～(如：烹饪 鱼汤)")
            return
        rkey = C.resolve("cooking", raw)
        r = C.COOKING_RECIPES.get(rkey)
        if not r:
            yield event.plain_result(f"没有『{raw}』这道料理！『烹饪列表』查看全部～")
            return
        cook_lv = db.get_prof_level(group_id, qq_id, "cooking")
        if cook_lv < r["min_lv"]:
            yield event.plain_result(f"【{r['name']}】需要烹饪 Lv.{r['min_lv']}，你才 Lv.{cook_lv}。多做简单料理提升吧！")
            return
        # 检查材料（鱼 key 是 fish_<中文名>，材料是 mat_id）
        lack = []
        for m, cnt in r["cost"].items():
            have = db.count_item(group_id, qq_id, m)
            if have < cnt:
                mname = C.display("materials", m) if m.startswith("mat_") else C.display("fish", m)
                lack.append(f"{mname}×{cnt}(你有{have})")
        if lack:
            yield event.plain_result(f"食材不足！做【{r['name']}】还缺：{'、'.join(lack)}。垂钓/采集收集食材～")
            return
        # 扣食材
        for m, cnt in r["cost"].items():
            items = db.get_inventory(group_id, qq_id)
            for it in items:
                if it["key"] == m or it["data"].get("name") == C.display("materials", m):
                    db.remove_item(group_id, qq_id, it["key"], cnt)
                    break
        # 发料理（读 ITEMS 定义）
        pkey = next(iter(r["product"]))
        itdef = C.ITEMS.get(pkey, {})
        db.add_item(group_id, qq_id, pkey, {"name": itdef.get("name", pkey), "type": "消耗品", "stackable": True, "price": itdef.get("price", 10), **({k: v for k, v in itdef.items() if k in ("heal", "mana", "effect")})})
        # 副业经验
        new_lv, leveled = db.add_prof_exp(group_id, qq_id, "cooking", 1)
        lv_msg = ""
        if leveled:
            lv_msg = f"\n🌟 烹饪等级提升到 Lv.{new_lv}！"
        # 每日任务推进
        _done, _msg = self._daily_prof_bump(group_id, qq_id, "cooking")
        lv_msg += _msg
        # 阶段九：烹饪次数 + 成就判定
        db.bump_stats(group_id, qq_id, cook_count=1)
        C.check_achievements(group_id, qq_id, player)
        yield event.plain_result(act_msg + f"🍳 灶火升腾，香气四溢……\n"
            f"✅ 烹饪成功！【{itdef.get('name', pkey)}】({itdef.get('desc', '')})已放入背包！{lv_msg}"
        )

    def _prof_active_check(self, group_id, qq_id, key):
        """v67 双副业上限：动作前检查副业是否激活。

        未激活 → 有位置自动激活（提示）；已满 → 拦截。
        老玩家兼容：已有等级（>1）未激活 → 自动激活无感迁移。
        返回 (ok, 提示消息)
        """
        lst = db.get_activated_profs(group_id, qq_id)
        if key in lst:
            return True, ""
        # 位置满：有等级也拦截（严格双副业上限，玩家自己遗忘取舍）
        if len(lst) >= db.MAX_ACTIVE_PROFS:
            names = "、".join(db.PROF_FIELDS[k] for k in lst)
            return False, (
                f"你的副业位已满({len(lst)}/{db.MAX_ACTIVE_PROFS}：{names})！"
                f"想发展新副业，先『遗忘副业 <名称>』放弃一条吧～"
            )
        # 老玩家兼容：位置有空 + 已有等级（>1）未激活 → 自动激活无感迁移
        lv = db.get_prof_level(group_id, qq_id, key)
        if lv > 1:
            db.activate_prof(group_id, qq_id, key)
            return True, ""
        db.activate_prof(group_id, qq_id, key)
        new_lst = db.get_activated_profs(group_id, qq_id)
        return True, f"\n🔓 你选择了「{db.PROF_FIELDS.get(key, key)}」作为副业({len(new_lst)}/{db.MAX_ACTIVE_PROFS})！"

    @filter.regex(r"^(?:\[At:\d+\]\s*)?副业(?:[\s\S]*)$")

    async def profession_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        raw = self._strip_cmd(event, "副业").strip()
        if "排行" in raw:
            yield event.plain_result(self._prof_rank_text(group_id))
            return
        profs = db.get_professions(group_id, qq_id)
        activated = db.get_activated_profs(group_id, qq_id)
        lines = [f"🧵 【副业面板】(已激活 {len(activated)}/{db.MAX_ACTIVE_PROFS})", "━━━━━━━━━━━━"]
        icons = {"gather": "🌿", "mining": "⛏️", "fishing": "🎣", "alchemy": "🧪", "craft": "🔨", "cooking": "🍳"}
        total = 0
        for key, p in profs.items():
            total += p["lv"]
            need = p["lv"] * 20
            bar_len = min(10, p["exp"] // (need // 10 + 1))
            bar = "█" * bar_len + "░" * (10 - bar_len)
            mark = "✅" if key in activated else "🔒"
            lines.append(f"{icons.get(key, '·')} {p['name']}：Lv.{p['lv']}  {bar} {p['exp']}/{need} 经验 {mark}")
        lines.append("")
        lines.append(f"📊 副业总分：{total}(已激活副业计入，最多发展 {db.MAX_ACTIVE_PROFS} 条)")
        lines.append("💡 每人只能发展 2 条副业，练满再选新的需『遗忘副业 <名称>』(等级清零)")
        lines.append("💡 『副业 排行』看群友等级，『烹饪列表』看料理配方～")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?遗忘副业(?:[\s\S]*)$")
    async def prof_forget(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        raw = self._strip_cmd(event, "遗忘副业").strip()
        if not raw:
            yield event.plain_result("格式：遗忘副业 <名称>，如『遗忘副业 采集』(等级清零，请慎重！)")
            return
        key = None
        for k, name in db.PROF_FIELDS.items():
            if raw in name or raw in k:
                key = k
                break
        if not key:
            yield event.plain_result(f"没有『{raw}』这个副业！可选：{'、'.join(db.PROF_FIELDS.values())}")
            return
        old_lv = db.forget_prof(group_id, qq_id, key)
        if old_lv is None:
            yield event.plain_result(f"{db.PROF_FIELDS[key]} 本来就没激活，不用遗忘～")
            return
        yield event.plain_result(
            f"📦 你遗忘了「{db.PROF_FIELDS[key]}」(原 Lv.{old_lv}，已清零)！\n"
            f"副业位空出({len(db.get_activated_profs(group_id, qq_id))}/{db.MAX_ACTIVE_PROFS})，下次做副业时自动占位。"
        )

    def _prof_rank_text(self, group_id):
        tops = db.prof_top(group_id, 10)
        if not tops:
            return "🏆 【副业排行】\n━━━━━━━━━━━━\n还没有人练副业，快来当第一名！"
        lines = ["🏆 【副业排行】(总分 = 6 条副业等级之和)", "━━━━━━━━━━━━"]
        names = {}
        for t in tops:
            p = self._player(group_id, t["qq_id"])
            names[t["qq_id"]] = p["name"] if p else t["qq_id"]
        for i, t in enumerate(tops, 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, "  ")
            lines.append(f"{medal} {i:>2}. {names.get(t['qq_id'], t['qq_id'])}：{t['total']} 分")
        lines.append("")
        lines.append("💡 『副业』查看自己的等级面板")
        return "\n".join(lines)

    # ---------------- 每日副业任务 ----------------
    DAILY_PROF_TASKS = {
        "gather": ("采集", 5, 30),
        "mining": ("挖掘", 3, 30),
        "fishing": ("垂钓", 5, 30),
        "alchemy": ("炼金合成", 2, 25),
        "craft": ("锻造装备", 1, 40),
        "cooking": ("烹饪料理", 2, 25),
    }

    def _daily_prof_key(self, group_id, qq_id):
        today = time.strftime("%Y-%m-%d")
        return f"prof_daily_{group_id}_{qq_id}_{today}"

    def _daily_prof_state(self, group_id, qq_id):
        """返回 (task_key, name, need, reward_gold, done_count, claimed)"""
        raw = db.get_event_state(self._daily_prof_key(group_id, qq_id))
        if raw:
            parts = raw.split("|")
            if len(parts) >= 5:
                return parts[0], parts[1], int(parts[2]), int(parts[3]), int(parts[4]), parts[5] == "1"
        # 随机选一个任务
        import random as _rnd
        tkey = _rnd.choice(list(self.DAILY_PROF_TASKS.keys()))
        name, need, gold = self.DAILY_PROF_TASKS[tkey]
        db.set_event_state(self._daily_prof_key(group_id, qq_id), f"{tkey}|{name}|{need}|{gold}|0|0")
        return tkey, name, need, gold, 0, False

    def _daily_prof_bump(self, group_id, qq_id, tkey):
        """副业动作推进每日任务，返回 (完成了吗, 消息)"""
        tkey2, name, need, gold, cnt, claimed = self._daily_prof_state(group_id, qq_id)
        if tkey2 != tkey or claimed:
            return False, ""
        cnt += 1
        done = cnt >= need
        db.set_event_state(self._daily_prof_key(group_id, qq_id), f"{tkey2}|{name}|{need}|{gold}|{cnt}|{1 if done else 0}")
        if done:
            player = self._player(group_id, qq_id)
            if player:
                db.update_player(group_id, qq_id, gold=player["gold"] + gold)
            return True, f"\n🎯 今日副业任务完成！【{name}×{need}】奖励 {gold} 金币！"
        return False, ""

    @filter.regex(r"^(?:\[At:\d+\]\s*)?副业任务(?:\s*|$)")

    async def daily_prof(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        tkey, name, need, gold, cnt, claimed = self._daily_prof_state(group_id, qq_id)
        mark = "✅" if claimed else f"({cnt}/{need})"
        lines = [
            "🎯 【今日副业任务】",
            "━━━━━━━━━━━━",
            f"目标：{name} ×{need} {mark}",
            f"奖励：{gold} 金币",
            "",
            "💡 完成对应副业动作自动推进，明天刷新新任务！",
        ]
        if claimed:
            lines.append("✨ 今日任务已完成，明天再来～")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?垂钓(?:选择|点)?(?:\s*|$)")

    async def fishing(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        ok, act_msg = self._prof_active_check(group_id, qq_id, "fishing")
        if not ok:
            yield event.plain_result(act_msg)
            return
        if self._in_battle(group_id, qq_id):
            yield event.plain_result("你正在战斗中！先解决眼前的敌人(攻击/逃跑)")
            return
        cur = player["cur_map"]
        spot_info = C.FISHING_SPOTS.get(cur)
        if not spot_info:
            yield event.plain_result("这里没有水域！找有水的地方垂钓：橡木溪流、星语湖、铁港码头、银铃河、迷雾沼泽、霜原冰湖")
            return
        # v87.17 子区域绑定：钓点在指定子区域，不在那边没钓位
        _want_sa = spot_info.get("subarea", "") if isinstance(spot_info, dict) else ""
        if _want_sa and player.get("cur_subarea") != _want_sa:
            _sa_name = ""
            for _s in (C.MAP_BY_ID.get(cur, {}).get("subareas") or []):
                if _s["id"] == _want_sa:
                    _sa_name = _s.get("name", "")
                    break
            yield event.plain_result(
                f"🎣 {spot_info.get('name', '水域')}在{_sa_name or _want_sa}那边，这里没有好钓位！（『前往 {_sa_name or _want_sa}』）"
            )
            return
        spot = spot_info["name"] if isinstance(spot_info, dict) else spot_info
        # 垂钓点分级：副业等级不足不能去高级水域
        prof_lv = db.get_prof_level(group_id, qq_id, "fishing")
        need = spot_info.get("min_lv", 1) if isinstance(spot_info, dict) else 1
        if prof_lv < need:
            yield event.plain_result(f"🌊 {spot}是高级水域(需垂钓 Lv.{need}，你 Lv.{prof_lv})……先在低阶水域练练吧！")
            return
        # v94 体力：垂钓消耗 5 体力
        _ok, _st = self._spend_stamina(group_id, qq_id, 5, player, "垂钓")
        if not _ok:
            yield event.plain_result(_st)
            return
        # v55 等待制（原 60 秒 CD 改为随机等待，自动入包，等级减时；spot 存状态供结算消息用）
        # 9.3：extra 带 spot_map 供 roll_fish 钓点差异化（禁出档位 + 品种限定水域）
        text, _ok = self._prof_wait_flow(
            event, group_id, qq_id, "fishing",
            extra={"spot": spot, "spot_map": cur},
            begin_text=f"🎣 你在{spot}抛出鱼竿，开始垂钓……预计 ",
        )
        yield event.plain_result(act_msg + text)

    @filter.regex(r"^(?:\[At:\d+\]\s*)?锻造(?:[\s\S]*)$")

    async def craft(self, event: AstrMessageEvent):
        """锻造装备：消耗材料 + 金币 → 获得指定装备（铁匠铺）
        v41：按职业分组展示；套装需要精英/Boss 掉的图纸"""
        group_id, qq_id = self._uid(event)
        raw = self._strip_cmd(event, "锻造")
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        ok, act_msg = self._prof_active_check(group_id, qq_id, "craft")
        if not ok:
            yield event.plain_result(act_msg)
            return
        if not self._at_smith(player):
            yield event.plain_result("需要到铁匠铺/锻造坊才能锻造装备！(先『地图』移动到铁匠铺)")
            return
        text = raw.strip()
        # 『锻造列表 [N]』：列表指令（翻页），与『锻造 N』锻造序号分离
        if text.startswith("列表"):
            t2 = text[2:].strip()
            page = int(t2) if t2.isdigit() else 1
            yield event.plain_result(self._craft_list_available(player, page))
            return
        # 『锻造 N』：锻造可锻造列表第 N 个配方（序号与列表显示一致，1-based）
        if text.isdigit():
            idx = int(text)
            recs = self._craft_recs_filtered(player)
            if idx < 1 or idx > len(recs):
                yield event.plain_result(f"没有第 {idx} 个可锻造配方(当前可锻造 {len(recs)} 件)！『锻造列表』查看～")
                return
            text = recs[idx - 1][0]
        # 无参数：只列当前可锻造的配方（无需图纸 + 已学习图纸），翻页用『锻造列表 N』
        if not text:
            yield event.plain_result(self._craft_list_available(player, 1))
            return
        # 『锻造 全部 [N]』：全部配方（未达标标记），翻页
        if text.startswith("全部"):
            t2 = text[2:].strip()
            page = int(t2) if t2.isdigit() else 1
            yield event.plain_result(self._craft_list_all(player, page))
            return
        # 『锻造 <职业> [N]』：该职业可锻造列表
        cls = C.resolve("classes", text)
        if cls in C.CLASSES:
            yield event.plain_result(self._craft_list_class(player, cls, 1))
            return
        # 锻造指定装备（20 章 4.3：『锻造 <装备名> <词条倾向>』指定词条池）
        affinity = None
        parts = text.split()
        if len(parts) >= 2:
            last = parts[-1]
            if last in C.AFFIX_AFFINITY_CN:
                affinity = C.AFFIX_AFFINITY_CN[last]
                text = " ".join(parts[:-1])
        rec_name = C.craft_recipe_search(text)
        if not rec_name:
            # 可能是查看配方详情
            if text.startswith("配方") or text.startswith("详情"):
                t2 = text[2:].strip()
                rn = C.craft_recipe_search(t2)
                if rn:
                    yield event.plain_result(self._recipe_detail(rn))
                    return
            # #24 材料关键词联想：没找到配方名 → 按材料名联想
            mat_recs = C.craft_recipes_by_material(text)
            if mat_recs:
                lines = [f"🔍 没找到『{text}』配方，但按材料联想到了 {len(mat_recs)} 个：", ""]
                for name, rec in mat_recs:
                    q = C.QUALITY[rec["quality"]]
                    bp = " 📜" if rec.get("blueprint") else ""
                    mats_show = " + ".join("%s×%s" % (C.display("materials", m), n) for m, n in rec["mats"].items())
                    if rec.get("blueprint"):
                        mats_show += " + %s×1" % rec["blueprint"]
                    lines.append(f"{q['color']}【{C.display('recipes', name)}】Lv.{rec['lv']} {C.EQUIP_SLOTS[rec['slot']]}{bp}｜{mats_show}｜{rec['gold']}金")
                lines.append("")
                lines.append("💡 输入『锻造 <装备名>』直接锻造，『锻造 配方 <装备名>』看详情～")
                yield event.plain_result("\n".join(lines))
                return
            yield event.plain_result(f"没有找到『{text}』的锻造配方！『锻造』看职业分组，『锻造 配方 <装备名>』看详情～")
            return
        rec = C.CRAFT_RECIPES[rec_name]
        rec_disp = C.display("recipes", rec_name)
        # 检查等级门槛（装备等级比玩家高太多不能锻造）
        if rec["lv"] > player["level"] + 6:
            yield event.plain_result(f"【{rec_disp}】需要 Lv.{rec['lv']} 的锻造技艺，你才 Lv.{player['level']}，先练练级再来吧！")
            return
        # v54 副业等级限制
        prof_lv = db.get_prof_level(group_id, qq_id, "craft")
        need_prof = self._craft_prof_need(rec["lv"])
        if prof_lv < need_prof:
            yield event.plain_result(
                f"【{rec_disp}】需要锻造副业 Lv.{need_prof}，你才 Lv.{prof_lv}！多锻造装备升级副业吧～\n"
                f"💡 赶时间可以找铁匠『代工 <装备名>』：3 倍金币，不需要副业等级(单人玩家的救星)"
            )
            return
        # v54 图纸学习制：需图纸配方必须已学习（不再每件消耗图纸）
        if rec.get("blueprint"):
            bp_name = rec["blueprint"]
            if bp_name not in (player.get("learned_blueprints") or []):
                # 懒迁移：背包有图纸 → 提示先学习
                have_bp = db.count_item(group_id, qq_id, bp_name)
                if have_bp >= 1:
                    yield event.plain_result(
                        f"你背包里有『{bp_name}』！输入『学习 {bp_name}』解锁配方后就能永久锻造了～"
                    )
                else:
                    yield event.plain_result(
                        f"【{rec_disp}】需要先学习图纸『{bp_name}』(精英/Boss 掉落)！『学习 <图纸名>』永久解锁。"
                    )
                return
        # v94 体力：锻造消耗 10 体力
        _ok, _st = self._spend_stamina(group_id, qq_id, 10, player, "锻造")
        if not _ok:
            yield event.plain_result(_st)
            return
        # 检查材料（毕业套图纸已学习，无需再检查图纸）
        lack = []
        for m, n in rec["mats"].items():
            have = db.count_item(group_id, qq_id, m)
            if have < n:
                lack.append(f"{C.display('materials', m)}×{n}(你有{have})")
        if lack:
            yield event.plain_result(f"材料不足！锻造【{rec_disp}】还缺：{'、'.join(lack)}。打对应怪物收集材料！")
            return
        # 20 章 4.3：词条倾向额外消耗（+50% 金币）
        gold_need = rec["gold"]
        if affinity:
            gold_need = int(gold_need * 1.5)
        if player["gold"] < gold_need:
            yield event.plain_result(f"金币不足！锻造【{rec_disp}】需要 {gold_need} 金币，你只有 {player['gold']}。")
            return
        # 扣材料 + 扣金币 + 发装备（v48：背包 data.name 存中文，mats key 是 ID）
        for m, n in rec["mats"].items():
            mname = C.display("materials", m)
            items = db.get_inventory(group_id, qq_id)
            for it in items:
                d = it["data"]
                if d.get("name") == mname:
                    db.remove_item(group_id, qq_id, it["key"], n)
                    break
        db.update_player(group_id, qq_id, gold=player["gold"] - gold_need)
        equip = C.craft_recipe_make(rec_name, affinity)
        import uuid
        key = f"eq_{uuid.uuid4().hex[:8]}"
        db.add_item(group_id, qq_id, key, equip)
        q = C.QUALITY[equip["quality"]]
        afs = equip.get("affixes", [])
        af_str = ""
        if afs:
            parts = [C.affix_label(a) for a in afs if isinstance(a, str)]
            if parts:
                af_str = f"\n    ✨ 词条：{'  '.join(parts)}"
        if equip.get("legendary"):
            lg = C.LEGENDARY_EFFECTS[equip["legendary"]]
            af_str += f"\n    ✨ 专属：{lg['name']}"
        set_str = ""
        if equip.get("set"):
            set_str = f"\n    🎴 套装：{equip['set']}"
        # 副业经验（锻造成功 +1；阶段九：矮人熔炉之心——锻造经验 +1）
        prof_gain = 1 + (1 if E.race_stats(player.get("race")).get("craft_bonus") else 0)
        new_lv, leveled = db.add_prof_exp(group_id, qq_id, "craft", prof_gain)
        lv_msg = ""
        if leveled:
            lv_msg = f"\n🌟 锻造等级提升到 Lv.{new_lv}！"
        # 每日任务推进
        _done, _msg = self._daily_prof_bump(group_id, qq_id, "craft")
        lv_msg += _msg
        # 阶段九：锻造次数 + 成就判定
        db.bump_stats(group_id, qq_id, craft_count=1)
        C.check_achievements(group_id, qq_id, player)
        affinity_str = f"({affinity}倾向)" if affinity else ""
        yield event.plain_result(act_msg + f"🔨 铁匠挥锤敲打，火星四溅……\n"
            f"✅ 锻造成功！{q['color']}【{equip['name']}】({C.EQUIP_SLOTS[equip['slot']]}) Lv.{equip['lv']} {affinity_str}"
            f"{af_str}{set_str}\n"
            f"💰 消耗 {gold_need} 金币，装备已放入背包！{lv_msg}"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?代工(?:[\s\S]*)$")
    async def craft_commission(self, event: AstrMessageEvent):
        """铁匠代工：图纸+材料＋3倍金币 → 装备(v67 单人补偿，不需要锻造副业等级)"""
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        if not self._at_smith(player):
            yield event.plain_result("需要到铁匠铺/锻造坊才能找铁匠代工！(先『地图』移动到铁匠铺)")
            return
        text = self._strip_cmd(event, "代工").strip()
        if not text:
            yield event.plain_result(
                "格式：代工 <装备名>，如『代工 铁皮长剑』\n"
                "铁匠代工 = 图纸 + 材料＋3倍金币，不需要锻造副业等级(单人玩家也能拿高级装备)"
            )
            return
        rec_name = C.craft_recipe_search(text)
        if not rec_name:
            yield event.plain_result(f"没有找到『{text}』的锻造配方！『锻造 配方 <装备名>』查看详情～")
            return
        rec = C.CRAFT_RECIPES[rec_name]
        rec_disp = C.display("recipes", rec_name)
        if rec["lv"] > player["level"] + 6:
            yield event.plain_result(f"【{rec_disp}】需要 Lv.{rec['lv']} 的锻造技艺，你才 Lv.{player['level']}，先练练级再来吧！")
            return
        # 图纸检查（与锻造一致：需图纸配方必须已学习）
        if rec.get("blueprint"):
            bp_name = rec["blueprint"]
            if bp_name not in (player.get("learned_blueprints") or []):
                have_bp = db.count_item(group_id, qq_id, bp_name)
                if have_bp >= 1:
                    yield event.plain_result(f"你背包里有『{bp_name}』！输入『学习 {bp_name}』解锁配方后就能代工了～")
                else:
                    yield event.plain_result(f"【{rec_disp}】需要先学习图纸『{bp_name}』(精英/Boss 掉落)！")
                return
        # 材料检查
        lack = []
        for m, n in rec["mats"].items():
            have = db.count_item(group_id, qq_id, m)
            if have < n:
                lack.append(f"{C.display('materials', m)}×{n}(你有{have})")
        if lack:
            yield event.plain_result(f"材料不足！代工【{rec_disp}】还缺：{'、'.join(lack)}。打对应怪物收集材料！")
            return
        cost = rec["gold"] * 3
        if player["gold"] < cost:
            yield event.plain_result(f"金币不足！铁匠代工【{rec_disp}】要 {cost} 金币(锻造价×3)，你只有 {player['gold']}。")
            return
        # 扣材料 + 扣金币 + 发装备
        for m, n in rec["mats"].items():
            mname = C.display("materials", m)
            items = db.get_inventory(group_id, qq_id)
            for it in items:
                if it["data"].get("name") == mname:
                    db.remove_item(group_id, qq_id, it["key"], n)
                    break
        db.update_player(group_id, qq_id, gold=player["gold"] - cost)
        equip = C.craft_recipe_make(rec_name)
        import uuid
        key = f"eq_{uuid.uuid4().hex[:8]}"
        db.add_item(group_id, qq_id, key, equip)
        q = C.QUALITY[equip["quality"]]
        yield event.plain_result(
            f"🔨 铁匠接过材料，替你挥锤……\n"
            f"✅ 代工完成！{q['color']}【{equip['name']}】({C.EQUIP_SLOTS[equip['slot']]}) Lv.{equip['lv']}\n"
            f"💰 代工费 {cost} 金币(锻造价×3)，装备已放入背包！"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?学习(?:[\s\S]*)$")

    async def learn(self, event: AstrMessageEvent):
        """『学习 <图纸名>』：消耗 1 张图纸，永久解锁对应套装配方(v54 图纸学习制)"""
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        bp_name = self._strip_cmd(event, "学习").strip()
        if not bp_name:
            yield event.plain_result("格式：『学习 <图纸名>』，如『学习 铁皮图纸』！图纸由精英/Boss 掉落。")
            return
        # 背包找图纸（type=图纸）
        items = db.get_inventory(group_id, qq_id)
        target = next((it for it in items if it["data"].get("type") == "图纸" and bp_name in it["data"].get("name", "")), None)
        if not target:
            yield event.plain_result(f"背包里没有『{bp_name}』图纸！精英/Boss 掉落，『背包 图纸』查看～")
            return
        bp_disp = target["data"].get("name")
        learned = list(player.get("learned_blueprints") or [])
        if bp_disp in learned:
            yield event.plain_result(f"『{bp_disp}』你已经学会了，不需要重复学习～")
            return
        # 消耗图纸 + 记录
        db.remove_item(group_id, qq_id, target["key"], 1)
        learned.append(bp_disp)
        db.update_player(group_id, qq_id, learned_blueprints=learned)
        # 统计解锁的配方数
        unlocked = [rk for rk, rec in C.CRAFT_RECIPES.items() if rec.get("blueprint") == bp_disp]
        lines = [
            f"📜 你研读了【{bp_disp}】，图纸化作点点光芒融入记忆！",
            f"🧠 永久解锁 {len(unlocked)} 个配方(锻造时不再消耗图纸)！",
            "━━━━━━━━━━━━",
        ]
        for rk in sorted(unlocked, key=lambda x: C.CRAFT_RECIPES[x]["slot"]):
            rec = C.CRAFT_RECIPES[rk]
            lines.append(f"  {C.QUALITY[rec['quality']]['color']}【{rec['name']}】Lv.{rec['lv']} {C.EQUIP_SLOTS[rec['slot']]}")
        lines.append("━━━━━━━━━━━━")
        lines.append("💡 『锻造』查看可锻造的配方，『锻造 <装备名>』直接锻造！")
        yield event.plain_result("\n".join(lines))

    def _craft_prof_need(self, rec_lv: int) -> int:
        """锻造配方副业等级门槛(v54：按装备等级折算)"""
        if rec_lv <= 10:
            return 1
        if rec_lv <= 30:
            return 2
        if rec_lv <= 50:
            return 3
        if rec_lv <= 70:
            return 4
        if rec_lv <= 90:
            return 5
        return 6

    def _rec_learned(self, player, rec) -> bool:
        """图纸是否已学习(v54 图纸学习制：无图纸配方恒 True)"""
        bp = rec.get("blueprint")
        if not bp:
            return True
        return bp in (player.get("learned_blueprints") or [])

    def _craft_mats_str(self, rec) -> str:
        mats_str = " + ".join(f"{C.display('materials', m)}×{n}" for m, n in rec["mats"].items())
        return mats_str

    def _craft_recs_filtered(self, player) -> list:
        """当前玩家可锻造的配方列表(玩家等级 + 副业等级 + 图纸已学)"""
        prof_lv = db.get_prof_level(player.get("group_id", ""), player["qq_id"], "craft")
        out = []
        for rk, rec in C.CRAFT_RECIPES.items():
            if rec["lv"] > player["level"] + 6:
                continue
            if self._craft_prof_need(rec["lv"]) > prof_lv:
                continue
            if not self._rec_learned(player, rec):
                continue
            out.append((rk, rec))
        out.sort(key=lambda x: (x[1]["lv"], x[1]["slot"]))
        return out

    def _craft_line(self, rec, idx: int) -> str:
        q = C.QUALITY[rec["quality"]]
        bp = " 📜" if rec.get("blueprint") else ""
        return (f"{idx}. {q['color']}【{rec['name']}】Lv.{rec['lv']} {C.EQUIP_SLOTS[rec['slot']]}"
                f" 锻造Lv.{self._craft_prof_need(rec['lv'])}{bp}\n"
                f"    {self._craft_mats_str(rec)}｜{rec['gold']}金")

    def _craft_list_available(self, player, page: int = 1) -> str:
        """『锻造』：只列当前可锻造的配方(翻页 10/页)"""
        recs = self._craft_recs_filtered(player)
        page_items, pages, page = self._page_items(recs, page, per_page=5)
        lines = [f"🔨 铁匠铺·当前可锻造(共 {len(recs)} 件)", "━━━━━━━━━━━━"]
        base = (page - 1) * 5
        for i, (rk, rec) in enumerate(page_items, 1):
            lines.append(self._craft_line(rec, base + i))
        lines.append("━━━━━━━━━━━━")
        lines.append(f"📄 第 {page}/{pages} 页" + (f"｜『锻造列表 {page + 1}』下一页" if page < pages else ""))
        lines.append("💡 『锻造 <序号>』锻造 ｜『锻造 <装备名>』锻造 ｜『锻造 全部』看全部 ｜『锻造 <职业>』看职业")
        lines.append("💡 📜 套装需图纸：『学习 <图纸名>』解锁后永久可造")
        return "\n".join(lines)

    def _craft_list_all(self, player, page: int = 1) -> str:
        """『锻造 全部』：全部配方，未达标标记"""
        prof_lv = db.get_prof_level(player.get("group_id", ""), player["qq_id"], "craft")
        recs = []
        for rk, rec in C.CRAFT_RECIPES.items():
            marks = []
            if rec["lv"] > player["level"] + 6:
                marks.append("🔒等级")
            if self._craft_prof_need(rec["lv"]) > prof_lv:
                marks.append("🛠️锻造Lv")
            if not self._rec_learned(player, rec):
                marks.append("📜未学")
            recs.append((rk, rec, marks))
        recs.sort(key=lambda x: (x[1]["lv"], x[1]["slot"]))
        page_items, pages, page = self._page_items(recs, page, per_page=5)
        lines = [f"🔨 铁匠铺·全部配方(共 {len(recs)} 件)", "━━━━━━━━━━━━"]
        base = (page - 1) * 5
        for i, (rk, rec, marks) in enumerate(page_items, 1):
            q = C.QUALITY[rec["quality"]]
            mark_str = " ".join(marks) if marks else "✅"
            lines.append(f"{base + i}. {q['color']}【{rec['name']}】Lv.{rec['lv']} {C.EQUIP_SLOTS[rec['slot']]} {mark_str}")
            lines.append(f"    {self._craft_mats_str(rec)}｜{rec['gold']}金")
        lines.append("━━━━━━━━━━━━")
        lines.append(f"📄 第 {page}/{pages} 页" + (f"｜『锻造 全部 {page + 1}』下一页" if page < pages else ""))
        lines.append("💡 未达标的配方：🔒等级不够 ｜ 🛠️锻造副业等级不够 ｜ 📜图纸未学习")
        return "\n".join(lines)

    def _craft_list_class(self, player, cls: str, page: int = 1) -> str:
        """『锻造 <职业>』：该职业可锻造列表"""
        cls_name = C.display("classes", cls)
        wt = C.CLASSES[cls].get("weapon_type", "sword")
        recs = [(rk, rec) for rk, rec in self._craft_recs_filtered(player)
                if rec.get("class") == cls or rec.get("weapon_type") == wt]
        page_items, pages, page = self._page_items(recs, page, per_page=5)
        lines = [f"{C.CLASSES[cls].get('icon', '⚔️')} 【{cls_name}】当前可锻造({len(recs)} 件)", "━━━━━━━━━━━━"]
        base = (page - 1) * 5
        for i, (rk, rec) in enumerate(page_items, 1):
            lines.append(self._craft_line(rec, base + i))
        lines.append("━━━━━━━━━━━━")
        lines.append(f"📄 第 {page}/{pages} 页" + (f"｜『锻造 {cls_name} {page + 1}』下一页" if page < pages else ""))
        lines.append(f"💡 『锻造 <装备名>』锻造 ｜『锻造 全部』看全部配方")
        return "\n".join(lines)

    def _recipe_detail(self, rec_name: str) -> str:
        """配方详情文本(v41 供锻造/配方命令复用)"""
        rec = C.CRAFT_RECIPES[rec_name]
        q = C.QUALITY[rec["quality"]]
        rec_disp = C.display("recipes", rec_name)
        mats_str = "、".join(f"{C.display('materials', m)}×{n}" for m, n in rec["mats"].items())
        if rec.get("blueprint"):
            mats_str += f"、{rec['blueprint']}×1"
        lines = [
            f"📜 配方：{q['color']}【{rec_disp}】",
            f"🏷️ 类型：{C.EQUIP_SLOTS[rec['slot']]}  Lv.{rec['lv']}  {q['name']}",
            f"🧰 材料：{mats_str}",
            f"💰 费用：{rec['gold']} 金币",
        ]
        if rec.get("class"):
            lines.append(f"🎭 职业：{C.display('classes', rec['class'])}  套装：{rec.get('set', '')}")
        if rec.get("blueprint"):
            lines.append(f"📜 需要图纸：{rec['blueprint']}(精英/Boss 掉落)")
        if rec.get("desc"):
            lines.append(f"📖 {rec['desc']}")
        lines.append("")
        lines.append("💡 到铁匠铺输入『锻造 装备名』制作！")
        return "\n".join(lines)

    @filter.regex(r"^(?:\[At:\d+\]\s*)?配方(?:\s*|$)")

    async def recipe_list(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        raw = self._strip_cmd(event, "配方")
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        text = raw.strip()
        # 无参数：按职业分组列出全部配方
        if not text or text == "列表":
            lines = ["📜 铁匠锻造配方(『锻造 <职业>』看该职业，『锻造 配方 <装备名>』看详情)：", ""]
            for cls in C.CLASSES:
                icon = C.CLASSES[cls].get("icon", "⚔️")
                cls_recs = [(n, r) for n, r in C.CRAFT_RECIPES.items()
                            if r.get("class") == cls or r.get("weapon_type") == C.CLASSES[cls].get("weapon_type")]
                lines.append(f"{icon} {C.display('classes', cls)}：{'、'.join(C.display('recipes', n) for n, _ in sorted(cls_recs, key=lambda x: x[1]['lv']))}")
            lines.append("")
            lines.append("💡 锻造：到铁匠铺『锻造 <职业>』查看，『锻造 <装备名>』制作")
            yield event.plain_result("\n".join(lines))
            return
        # 带参数：查看指定配方详情
        rec_name = C.craft_recipe_search(text)
        if not rec_name:
            yield event.plain_result(f"没有找到『{text}』的配方！")
            return
        yield event.plain_result(self._recipe_detail(rec_name))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?强化(?:\s*|$)")

    async def enhance(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        item_name = self._strip_cmd(event, "强化")
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        if not self._at_smith(player):
            yield event.plain_result("需要到铁匠铺/锻造坊才能强化装备！(先『地图』移动到铁匠铺)")
            return
        item_name = item_name.strip()
        if not item_name:
            yield event.plain_result("强化哪件装备？输入『强化 <装备名>』或『强化 <背包序号>』(如：强化 铁剑 / 强化 3)")
            return
        items = db.get_inventory(group_id, qq_id)
        target = None
        # 序号强化：『强化 3』→ 背包第 3 件（与『物品详情 3』同语义，全背包连续编号）
        if item_name.isdigit():
            idx = int(item_name)
            if idx < 1 or idx > len(items):
                yield event.plain_result(f"背包里没有第 {idx} 件物品(共 {len(items)} 件)！『背包』查看全部～")
                return
            target = items[idx - 1]
            if not target["data"].get("slot"):
                yield event.plain_result(f"背包第 {idx} 件『{target['data']['name']}』不是装备，不能强化！『背包』看装备序号～")
                return
        else:
            for it in items:
                d = it["data"]
                if d.get("slot") and item_name in d["name"]:
                    target = it
                    break
            if not target:
                yield event.plain_result(f"背包里没有叫『{item_name}』的装备！")
                return
        d = target["data"]
        cur_enh = d.get("enhance", 0)
        if cur_enh >= C.MAX_ENHANCE:
            yield event.plain_result(f"【{d['name']}】已经强化到极限 +{cur_enh} 了！")
            return
        info = C.ENHANCE_TABLE[cur_enh]
        # v94 体力：强化消耗 10 体力
        _ok, _st = self._spend_stamina(group_id, qq_id, 10, player, "强化")
        if not _ok:
            yield event.plain_result(_st)
            return
        # v67 强化归位锻造 → 导师进修后强化为独立副业（19 章第八章）：强化 +N 需要强化副业 Lv.N
        ok, act_msg = self._prof_active_check(group_id, qq_id, "enhance")
        if not ok:
            yield event.plain_result(act_msg)
            return
        prof_lv = db.get_prof_level(group_id, qq_id, "enhance")
        need = min(cur_enh + 1, 10)
        if prof_lv < need:
            yield event.plain_result(
                f"强化 +{cur_enh} → +{cur_enh+1} 需要强化副业 Lv.{need}(你 Lv.{prof_lv})！多强化装备升级吧～"
            )
            return
        if player["gold"] < info["cost"]:
            yield event.plain_result(f"强化 +{cur_enh} → +{cur_enh+1} 需要 {info['cost']} 金币，你只有 {player['gold']}。")
            return
        db.update_player(group_id, qq_id, gold=player["gold"] - info["cost"])
        # 掷强化
        if random.random() < info["rate"]:
            d["enhance"] = cur_enh + 1
            db.remove_item(group_id, qq_id, target["key"])
            db.add_item(group_id, qq_id, target["key"], d, 1)
            lines = [f"🔨 强化成功！【{d['name']}】+{cur_enh} → +{cur_enh+1}！"]
            # 阶段九：强化次数 + 成就判定
            db.bump_stats(group_id, qq_id, enhance_count=1)
            C.check_achievements(group_id, qq_id, player)
            if cur_enh + 1 == 5:
                lines.append("⚡ 装备绽放出耀眼的光芒！")
            elif cur_enh + 1 == 9:
                lines.append("🌟 传说级的光芒冲天而起！你听见了铁匠们的惊叹！")
            yield event.plain_result("\n".join(lines))
        else:
            drop = C.ENHANCE_FAIL_DROP.get(cur_enh, 1)
            new_enh = max(0, cur_enh - drop)
            if new_enh != cur_enh:
                d["enhance"] = new_enh
                db.remove_item(group_id, qq_id, target["key"])
                db.add_item(group_id, qq_id, target["key"], d, 1)
                yield event.plain_result(f"💥 强化失败！【{d['name']}】降级到 +{new_enh}。铁匠摇摇头：『下次一定行！』")
            else:
                yield event.plain_result(f"💥 强化失败！好在【{d['name']}】保住了等级(+{new_enh})。再试一次？")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?附魔(?:\s*|$)")

    async def enchant(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        raw = self._strip_cmd(event, "附魔")
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        if not self._at_smith(player):
            yield event.plain_result("需要到铁匠铺/锻造坊才能附魔装备！(先『地图』移动到铁匠铺)")
            return
        parts = raw.strip().split()
        if not parts:
            yield event.plain_result(
                "附魔哪件装备？输入『附魔 <装备名> <属性/符文>』\n"
                f"属性附魔：{'、'.join(r['label'] for r in C.ENCHANT_RECIPES.values())}\n"
                f"符文(MC 式，独特效果+等级)：{'、'.join(C.RUNES.keys())}\n"
                "例：『附魔 烈焰之刃 攻击』『附魔 烈焰之刃 史诗符文·残忍 II』\n"
                "💡 打怪掉落符文，『物品详情 <符文名>』查看效果"
            )
            return
        item_name = parts[0]
        stat_label = parts[1] if len(parts) > 1 else ""
        # v94 体力：附魔消耗 10 体力
        _ok, _st = self._spend_stamina(group_id, qq_id, 10, player, "附魔")
        if not _ok:
            yield event.plain_result(_st)
            return
        # v67 附魔归位炼金 → 导师进修后附魔为独立副业（19 章第八章）：附魔需要附魔副业 Lv.2
        ok, act_msg = self._prof_active_check(group_id, qq_id, "enchant")
        if not ok:
            yield event.plain_result(act_msg)
            return
        prof_lv = db.get_prof_level(group_id, qq_id, "enchant")
        if prof_lv < 2:
            yield event.plain_result(
                f"附魔需要附魔副业 Lv.2(你 Lv.{prof_lv})！多附魔升级吧～"
            )
            return
        # ---- v34 符文路径：第二参数含"符文"则走符文附魔 ----
        if "符文" in stat_label:
            items = db.get_inventory(group_id, qq_id)
            rune = None
            for it in items:
                dd = it["data"]
                if dd.get("type") == "符文" and stat_label in dd.get("name", ""):
                    rune = it
                    break
            if not rune:
                yield event.plain_result(f"背包里没有『{stat_label}』！打怪有概率掉落符文～")
                return
            rd = rune["data"]
            target = None
            for it in items:
                d = it["data"]
                if d.get("slot") and item_name in d["name"]:
                    target = it
                    break
            if not target:
                yield event.plain_result(f"背包里没有叫『{item_name}』的装备！")
                return
            d = target["data"]
            slots = C.ENCHANT_SLOTS.get(d.get("quality", ""), 0)
            if slots <= 0:
                yield event.plain_result(f"【{d['name']}】({C.QUALITY[d['quality']]['name']})没有符文槽，只有蓝/紫/橙装备可以附魔！")
                return
            enchanted = d.get("enchant", [])
            if len(enchanted) >= slots:
                yield event.plain_result(f"【{d['name']}】的 {slots} 个符文槽已满！先『卸下』旧装备换新的吧～")
                return
            # v34 冲突检查：新符文与已有效果冲突则拒绝
            conflict_hit = None
            for en in enchanted:
                if en.get("effect") and C.rune_conflict(rd["effect"], en["effect"]):
                    conflict_hit = C.RUNE_EFFECT_NAMES.get(en["effect"], en["effect"])
                    break
            if conflict_hit:
                yield event.plain_result(f"符文冲突！『{rd['name']}』与『{conflict_hit}』效果相斥，不能共存于同一件装备～")
                return
            if rd.get("effect") in [e.get("effect") for e in enchanted]:
                yield event.plain_result(f"【{d['name']}】已经有『{rd['name']}』的效果了！")
                return
            # 消耗符文（无需金币，符文本身就是价值）
            db.remove_item(group_id, qq_id, rune["key"], 1)
            enchanted.append({"effect": rd["effect"], "lvl": rd.get("lvl", 1)})
            d["enchant"] = enchanted
            db.remove_item(group_id, qq_id, target["key"])
            db.add_item(group_id, qq_id, target["key"], d, 1)
            yield event.plain_result(
                f"💎 符文刻印成功！【{d['name']}】获得『{rd['name']}』({rd['desc']})\n"
                f"(已用 {len(enchanted)}/{slots} 槽)"
            )
            return
        # ---- 原属性附魔路径（v10） ----
        # 属性标签 → stat 键
        stat_key = None
        for k, r in C.ENCHANT_RECIPES.items():
            if r["label"] == stat_label:
                stat_key = k
                break
        if not stat_key:
            yield event.plain_result(f"没有『{stat_label}』这个附魔属性！可用：{'、'.join(r['label'] for r in C.ENCHANT_RECIPES.values())}")
            return
        items = db.get_inventory(group_id, qq_id)
        target = None
        for it in items:
            d = it["data"]
            if d.get("slot") and item_name in d["name"]:
                target = it
                break
        if not target:
            yield event.plain_result(f"背包里没有叫『{item_name}』的装备！")
            return
        d = target["data"]
        slots = C.ENCHANT_SLOTS.get(d.get("quality", ""), 0)
        if slots <= 0:
            yield event.plain_result(f"【{d['name']}】({C.QUALITY[d['quality']]['name']})没有附魔槽，只有蓝/紫/橙装备可以附魔！")
            return
        enchanted = d.get("enchant", [])
        if len(enchanted) >= slots:
            yield event.plain_result(f"【{d['name']}】的 {slots} 个附魔槽已满！先『出售』旧装备，或等新装备吧～")
            return
        rec = C.ENCHANT_RECIPES[stat_key]
        mat_name = C.enchant_match_material(stat_key, items)
        if not mat_name:
            yield event.plain_result(
                f"背包里没有{rec['label']}系材料(需要含有：{'/'.join(rec['mats'])}的材料)！打怪掉落材料～"
            )
            return
        if player["gold"] < rec["cost"]:
            yield event.plain_result(f"附魔需要 {rec['cost']} 金币，你只有 {player['gold']}。")
            return
        # 消耗材料 + 金币
        for it in items:
            dd = it["data"]
            if dd.get("name") == mat_name:
                db.remove_item(group_id, qq_id, it["key"], 1)
                break
        db.update_player(group_id, qq_id, gold=player["gold"] - rec["cost"])
        # 附魔：5% 大成功 1.5x
        big = random.random() < C.ENCHANT_CRIT_CHANCE
        v = C.enchant_value(d["slot"], d["lv"], stat_key, big=big)
        enchanted.append({"stat": stat_key, "value": v})
        d["enchant"] = enchanted
        db.remove_item(group_id, qq_id, target["key"])
        db.add_item(group_id, qq_id, target["key"], d, 1)
        sn = {"atk": "攻击", "matk": "魔攻", "def": "防御", "mdef": "魔防", "hp": "生命", "spd": "速度", "crit": "暴击"}
        val_str = f"+{int(v * 100)}%" if stat_key in ("crit", "dodge") else f"+{v}"
        big_str = "🌟 大成功！" if big else ""
        # 阶段九：附魔次数 + 成就判定
        db.bump_stats(group_id, qq_id, enchant_count=1)
        C.check_achievements(group_id, qq_id, player)
        yield event.plain_result(
            f"🔮 附魔成功！【{d['name']}】获得 {sn.get(stat_key, stat_key)} {val_str}{big_str}\n"
            f"(消耗 {mat_name} x1 + {rec['cost']} 金币；已用 {len(enchanted)}/{slots} 槽)"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?套装(?:\s*|$)")

    async def set_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        equipment = player.get("equipment") or {}
        counts = {}
        for slot, item in equipment.items():
            if item and item.get("set"):
                counts[item["set"]] = counts.get(item["set"], 0) + 1
        if not counts:
            yield event.plain_result("你还没有穿戴任何套装部件！打怪掉落的蓝以上装备可能带套装(同前缀 = 同套装)，穿 2 件起生效～")
            return
        lines = ["🎴 【套装状态】", "━━━━━━━━━━━━"]
        any_active = False
        for sname, cnt in counts.items():
            info = E._set_info(sname)
            if not info:
                continue
            b2 = "  ".join(
                f"{sn} +{int(v * 100)}%"
                for k, v in info.get("bonus_2", {}).items()
                for sn in [{"atk": "攻击", "def": "防御", "matk": "魔攻", "mdef": "魔防", "hp": "生命", "spd": "速度", "crit": "暴击", "dodge": "闪避", "heal": "治疗"}.get(k, k)]
            )
            # 阶段八：4 件效果 = 属性加成（bonus_4_stats）或特效（bonus_4.effect）
            b4_parts = []
            for k, v in info.get("bonus_4_stats", {}).items():
                sn = {"atk": "攻击", "def": "防御", "matk": "魔攻", "mdef": "魔防", "hp": "生命", "spd": "速度", "crit": "暴击", "dodge": "闪避"}.get(k, k)
                b4_parts.append(f"{sn} +{int(v * 100)}%")
            b4_desc = info.get("bonus_4", {}).get("desc", "")
            if b4_desc:
                b4_parts.append(b4_desc)
            b4 = "  ".join(b4_parts) or "(待解锁)"
            # 阶段八：5 件效果（数据先行）
            b5 = info.get("bonus_5", {}).get("desc", "")
            active_2 = cnt >= 2
            active_4 = cnt >= 4
            active_5 = cnt >= 5
            if active_2 or active_4 or active_5:
                any_active = True
            lines.append(
                f"{info['icon']}{sname}({cnt}/5 件)"
                + (" ✅" if active_2 else "")
                + (" ⭐" if active_4 else "")
                + (" 👑" if active_5 else "")
            )
            lines.append(f"  2件：{b2}" + ("(已激活)" if active_2 else ""))
            lines.append(f"  4件：{b4}" + ("(已激活)" if active_4 else ""))
            if b5:
                lines.append(f"  5件：{b5}" + ("(已激活)" if active_5 else ""))
        if not any_active:
            lines.append("穿满 2 件同套装即激活 2 件效果，4 件激活 4 件效果！继续收集吧～")
        lines.append("━━━━━━━━━━━━")
        lines.append("💡 套装部件：打怪掉落的蓝/紫/橙装备有概率带套装前缀(如『寒霜』『诸神』)")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?图鉴(?:\s*|$)")

    async def bestiary(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        raw = self._strip_cmd(event, "图鉴")
        page = self._parse_page(raw)
        rows = db.get_bestiary(group_id, qq_id)
        if not rows:
            yield event.plain_result("📖 图鉴还是空的……去『探索』击败怪物收集吧！")
            return
        total = sum(r["kills"] for r in rows)
        page_items, pages, page = self._page_items(rows, page, per_page=5)
        lines = [f"📖 【怪物图鉴】已收录 {len(rows)} 种 · 累计击杀 {total}(第 {page}/{pages} 页)", "━━━━━━━━━━━━"]
        for i, r in enumerate(page_items, (page - 1) * 5 + 1):
            lines.append(f"{i:>2}. {r['monster']} ×{r['kills']}")
        lines.append("")
        if pages > 1:
            lines.append(f"💡 『图鉴 {page+1}』看下一页(共 {pages} 页)")
        lines.append("💡 击败新怪物会自动收录图鉴")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?百科(?:\s*|$)")

    async def encyclopedia(self, event: AstrMessageEvent):
        """百科：查材料掉落来源 / 怪物分布 / 地图怪物(v33)"""
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        raw = self._strip_cmd(event, "百科").strip()
        if not raw:
            lines = [
                "📚 【世界百科】想知道什么？输入『百科 <名称>』",
                "━━━━━━━━━━━━",
                "🔍 可查询：材料 / 怪物 / 地图",
                "例：『百科 狼皮』→ 狼皮在哪掉",
                "　　『百科 光耀狼』→ 光耀狼在哪出现",
                "　　『百科 远境草甸』→ 地图里的怪物",
                "💡 符文：『史诗符文·残忍』『传说符文·壁垒』(打怪掉落)",
            ]
            yield event.plain_result("\n".join(lines))
            return
        # 1. 符文查询
        stone_name = None
        for nm in C.RUNES:
            if nm in raw or f"符文·{nm}" in raw:
                stone_name = nm
                break
        if stone_name or "符文" in raw:
            if stone_name:
                st = C.RUNES[stone_name]
                lines = [
                    f"💎 【{st['quality']}符文·{stone_name}】",
                    "━━━━━━━━━━━━",
                    f"效果：{st['desc']}",
                    f"品质：{st['quality']}",
                    f"等级：I / II / III(等级越高效果越强，高等级更稀有)",
                    f"冲突：{'、'.join(C.RUNE_EFFECT_NAMES.get(x, x) for x, y in C.RUNE_CONFLICTS if y == st['effect'] or x == st['effect'])}(不能共存)" if any(y == st['effect'] or x == st['effect'] for x, y in C.RUNE_CONFLICTS) else "冲突：无",
                    f"获取：打怪概率掉落(精英/Boss 概率更高)",
                    f"使用：『附魔 <装备名> {st['quality']}符文·{stone_name}』",
                ]
                yield event.plain_result("\n".join(lines))
                return
            yield event.plain_result("没找到这颗符文！可用：\n" + "\n".join(f"  💎 {s['quality']}符文·{nm}({s['desc']})" for nm, s in C.RUNES.items()))
            return
        # 2. 材料查询（含词条材料来源）
        if raw in C.MATERIALS or any(kw in raw for kw in C.MATERIALS):
            # 精确匹配优先
            mat_key = raw if raw in C.MATERIALS else next((k for k in C.MATERIALS if k in raw), raw)
            srcs = C.ENCY_MATERIAL_SOURCE.get(mat_key, [])
            lines = [f"🧪 【{mat_key}】", "━━━━━━━━━━━━"]
            mat = C.MATERIALS.get(mat_key)
            if mat and mat.get("desc"):
                lines.append(f"描述：{mat['desc']}")
            if srcs:
                lines.append("掉落来源：")
                for mname, mstr in srcs:
                    lines.append(f"  🗺️ {mname} → {mstr}")
            else:
                lines.append("掉落来源：暂无(可能是任务/NPC 奖励)")
            lines.append("")
            lines.append(f"💡 出售价 {mat['price']} 金币" if mat else "")
            yield event.plain_result("\n".join(l for l in lines if l))
            return
        # 3. 地图查询
        if raw in C.ENCY_MAP_MONSTERS:
            entries = C.ENCY_MAP_MONSTERS[raw]
            mdef = next((m for m in C.MAPS if m["name"] == raw), None)
            lines = [f"🗺️ 【{raw}】", "━━━━━━━━━━━━"]
            if mdef and mdef.get("desc"):
                lines.append(f"{mdef['desc']}")
            if entries:
                lines.append("怪物：")
                for mstr, lv, mtype in entries:
                    lines.append(f"  {mtype}·Lv.{lv} {mstr}")
            yield event.plain_result("\n".join(lines))
            return
        # 4. 怪物查询
        if raw in C.ENCY_MONSTER_MAP:
            locs = C.ENCY_MONSTER_MAP[raw]
            lines = [f"👹 【{raw}】", "━━━━━━━━━━━━"]
            lines.append("出现地点：")
            for mname, mtype in locs:
                lines.append(f"  {mtype} · {mname}")
            yield event.plain_result("\n".join(lines))
            return
        # 5. 怪物名模糊匹配
        fuzzy = [k for k in C.ENCY_MONSTER_MAP if raw in k][:5]
        if fuzzy:
            yield event.plain_result(f"你是不是要找：{'、'.join(fuzzy)}？输入『百科 <完整名>』查看～")
            return
        yield event.plain_result(f"百科里没有『{raw}』！试试查材料(如『百科 狼皮』)、怪物(如『百科 光耀狼』)或地图(如『百科 远境草甸』)～")

    def _earned_titles(self, group_id, qq_id, player):
        """计算已获得的称号，返回 (已获列表, 未获列表)"""
        stats = db.get_stats(group_id, qq_id) or {}
        rep = db.get_reputation(group_id, qq_id)
        quests = db.get_quests(group_id, qq_id)
        earned = []
        for t in C.TITLES:
            tid = t["id"]
            ok = False
            if tid == "novice":
                ok = True
            elif tid == "lv10":
                ok = player["level"] >= 10
            elif tid == "lv20":
                ok = player["level"] >= 20
            elif tid == "lv30":
                ok = player["level"] >= 30
            elif tid == "kill10":
                ok = stats.get("kills", 0) >= 10
            elif tid == "kill100":
                ok = stats.get("kills", 0) >= 100
            elif tid == "kill500":
                ok = stats.get("kills", 0) >= 500
            elif tid == "elite5":
                ok = stats.get("elite_kills", 0) >= 5
            elif tid == "boss1":
                ok = stats.get("boss_kills", 0) >= 1
            elif tid == "boss3":
                ok = stats.get("boss_kills", 0) >= 3
            elif tid == "rep_honor":
                ok = any(C.faction_reputation_tier(v) in ("崇敬", "崇拜") for v in rep.values())
            elif tid == "rep_legend":
                ok = any(C.faction_reputation_tier(v) == "崇拜" for v in rep.values())
            elif tid == "quest10":
                ok = len(quests.get("completed_main", [])) >= 10
            elif tid == "wealthy":
                ok = player["gold"] >= 5000
            elif tid == "explorer":
                ok = db.get_visited_count(group_id, qq_id) >= 10
            elif tid == "fish10":
                ok = db.get_fishing_total(group_id, qq_id) >= 10
            elif tid == "enhance5":
                ok = self._has_enhanced(group_id, qq_id, 5)
            elif tid == "enhance9":
                ok = self._has_enhanced(group_id, qq_id, 9)
            elif tid == "hidden":
                ok = db.get_visited_count(group_id, qq_id) >= 10 and "mithril_hall" in self._visited_maps(group_id, qq_id)
            elif tid == "final":
                ok = quests.get("main_quest") is None and len(quests.get("completed_main", [])) >= 10
            elif tid.startswith("pro_"):
                # 副业称号：pro_<prof><lv>（如 pro_gather3）→ 副业等级达标
                import re as _re
                _mm = _re.match(r"^pro_([a-z]+)(\d+)$", tid)
                if _mm:
                    prof_key = _mm.group(1)
                    need_lv = int(_mm.group(2))
                    if prof_key in ("gather", "mining", "fishing", "alchemy", "craft", "cooking"):
                        ok = db.get_prof_level(group_id, qq_id, prof_key) >= need_lv
            elif tid == "fish_king":
                ok = db.get_fish_king(group_id, qq_id) >= 1
            elif tid == "pvp_hero":
                # 荣誉商店兑换过荣誉勋章（event_state honor_medal_<qq_id> = 1）
                ok = int(db.get_event_state(f"honor_medal_{qq_id}") or 0) >= 1
            earned.append(ok)
        return earned

    def _visited_maps(self, group_id, qq_id):
        import sqlite3
        try:
            conn = sqlite3.connect(db.DB_PATH)
            rows = conn.execute("SELECT map_id FROM visited WHERE qq_id=?", (qq_id,)).fetchall()
            conn.close()
            return [r[0] for r in rows]
        except Exception:
            return []

    def _has_enhanced(self, group_id, qq_id, level):
        items = db.get_inventory(group_id, qq_id)
        for it in items:
            if it["data"].get("enhance", 0) >= level:
                return True
        return False

    @filter.regex(r"^(?:\[At:\d+\]\s*)?称号(?:\s*|$)")

    async def titles(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        raw = self._strip_cmd(event, "称号").strip()
        # 装备/卸下称号
        if raw.startswith("装备") or raw.startswith("佩戴"):
            tname = raw[2:].strip()
            async for r in self._equip_title(event, group_id, qq_id, player, tname):
                yield r
            return
        if raw in ("卸下", "取消"):
            db.update_player(group_id, qq_id, equipped_title="")
            yield event.plain_result("🏅 已卸下称号。")
            return
        earned = self._earned_titles(group_id, qq_id, player)
        got = [C.TITLES[i]["name"] for i in range(len(C.TITLES)) if earned[i]]
        # 阶段九：成就称号合并（14 章：达成成就自动获得称号）
        try:
            got += C.achievement_titles(qq_id)
        except Exception:
            pass
        got = list(dict.fromkeys(got))  # 去重保序
        cur = player.get("equipped_title") or ""
        if not got:
            yield event.plain_result("🏅 【称号】\n━━━━━━━━━━━━\n还没有称号……提升等级、击杀怪物、解锁成就可以获得！")
            return
        if raw and raw.isdigit():
            page = int(raw)
        else:
            page = 1
        page_items, pages, page = self._page_items(got, page, per_page=8)
        lines = [f"🏅 【称号】已获得 {len(got)} 个(第 {page}/{pages} 页)", "━━━━━━━━━━━━"]
        for i, n in enumerate(page_items, (page - 1) * 8 + 1):
            mark = "👑" if n == cur else "  "
            lines.append(f"{mark}{i:>2}. {n}")
        lines.append("")
        if pages > 1:
            lines.append(f"💡 『称号 {page+1}』看下一页")
        lines.append(f"💡 『称号 装备 <名称>』佩戴展示(显示在角色名前)，『称号 卸下』取消")
        if not cur:
            lines.append("💡 当前未佩戴称号")
        yield event.plain_result("\n".join(lines))

    async def _equip_title(self, event, group_id, qq_id, player, tname):
        """装备称号(必须是已获得称号)"""
        if not tname:
            yield event.plain_result("格式：『称号 装备 <称号名>』～")
            return
        earned = self._earned_titles(group_id, qq_id, player)
        got = [C.TITLES[i]["name"] for i in range(len(C.TITLES)) if earned[i]]
        try:
            got += C.achievement_titles(qq_id)
        except Exception:
            pass
        got = list(dict.fromkeys(got))
        hit = next((n for n in got if tname in n), None)
        if not hit:
            yield event.plain_result(f"还没获得称号『{tname}』！『称号』查看已获得列表～")
            return
        db.update_player(group_id, qq_id, equipped_title=hit)
        yield event.plain_result(f"👑 你佩戴上了称号【{hit}】！现在别人会称你为 [{hit}] 冒险者～")

    @staticmethod
    def _item_category(d: dict) -> str:
        """物品大类：装备(有 slot)→ 装备；其余按 type 字段归类"""
        if d.get("slot"):
            return "装备"
        return d.get("type") or "其他"

    @staticmethod
    def _parse_bag_filter(text: str):
        """解析背包筛选参数：返回 (category, page)
        支持带空格（『材料 2』）与无空格（『材料2』）两种形式"""
        category = None
        page = 1
        text = (text or "").strip()
        # 带空格形式：『材料』『材料 2』『2』
        for p in text.split():
            if p in EconomyCmds.BAG_FILTER_TYPES:
                category = p
            elif p.isdigit():
                page = int(p)
        # 无空格形式：『材料2』『2』
        if category is None:
            for t in EconomyCmds.BAG_FILTER_TYPES:
                if text.startswith(t):
                    category = t
                    rest = text[len(t):].strip()
                    if rest.isdigit():
                        page = int(rest)
                    break
            else:
                if text.isdigit():
                    page = int(text)
        return category, page

    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:背包|物品)(?!详情|筛选)(?:\s*.*)?$")

    async def inventory(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        raw = self._strip_cmd(event, "背包")
        result = self._bag_view(group_id, qq_id, raw)
        yield event.plain_result(result)

    @filter.regex(r"^(?:\[At:\d+\]\s*)?背包筛选(?:[\s\S]*)$")

    async def bag_filter(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        raw = self._strip_cmd(event, "背包筛选")
        result = self._bag_view(group_id, qq_id, raw, filter_only=True)
        yield event.plain_result(result)

    def _bag_view(self, group_id, qq_id, raw, filter_only: bool = False) -> str:
        """背包列表渲染（v42：inventory 与背包筛选共用）
        filter_only=True 时无筛选参数给出提示而不是显示全部"""
        category, page = self._parse_bag_filter(raw)
        if filter_only and category is None:
            return "🎒 背包筛选：『背包筛选 <类型>』，如『背包筛选 材料』『筛选装备』\n" \
                   "类型：装备/材料/消耗品/符文/宠物蛋/坐骑/图纸/鱼；支持翻页『背包筛选 材料 2』"
        items = db.get_inventory(group_id, qq_id)
        if category:
            items = [it for it in items if self._item_category(it["data"]) == category]
            if not items:
                return f"背包里没有『{category}』类物品～『背包』看全部"
        if not items:
            return "你的背包空空如也……去『探索』打点东西吧！"
        page_items, pages, page = self._page_items(items, page, per_page=5)
        title = f"🎒 【背包·{category}】" if category else "🎒 【背包】"
        lines = [f"{title}(第 {page}/{pages} 页 · 共 {len(items)} 件)", "━━━━━━━━━━━━"]
        for i, it in enumerate(page_items, (page - 1) * 5 + 1):
            d = it["data"]
            if d.get("type") == "材料":
                lines.append(f"{i:>2}. {d['name']} ×{it['count']} (材料，可出售)")
            elif d.get("type") == "图纸":
                lines.append(f"{i:>2}. 📜 {d['name']} ×{it['count']} (锻造套装用)")
            elif d.get("slot"):
                q = C.QUALITY[d["quality"]]
                enh = d.get("enhance", 0)
                enh_str = f" +{enh}" if enh > 0 else ""
                lines.append(f"{i:>2}. {q['color']}【{d['name']}{enh_str}】({C.EQUIP_SLOTS[d['slot']]}) Lv.{d['lv']}")
            else:
                lines.append(f"{i:>2}. {d['name']} ×{it['count']}")
        lines.append("")
        if pages > 1:
            lines.append(f"💡 『背包 {page+1}』看下一页；筛选+翻页：『背包 材料 2』(共 {pages} 页)")
        lines.append("💡 『背包 <类型>』筛选(装备/材料/消耗品/符文/宠物蛋/坐骑/图纸/鱼)，支持『背包材料』『背包材料2』『背包筛选 材料』")
        lines.append("💡 『装备 <名称>』『使用 <名称>』『物品详情 <名称>』『出售 <名称>』")
        return "\n".join(lines)

    @filter.regex(r"^(?:\[At:\d+\]\s*)?物品详情(?:[\s\S]*)$")

    async def item_detail(self, event: AstrMessageEvent):
        """查看物品详细信息：装备属性/材料/消耗品/宠物蛋"""
        group_id, qq_id = self._uid(event)
        item_name = self._strip_cmd(event, "物品详情")
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        item_name = item_name.strip()
        if not item_name:
            yield event.plain_result("格式：物品详情 <名称/序号>，如『物品详情 雷霆之锤』或『物品详情 1』")
            return
        items = db.get_inventory(group_id, qq_id)
        target = None
        equipped = False
        # 序号查看：『物品详情 1』→ 背包第 1 件（与『背包』列表序号一致）
        if item_name.isdigit():
            idx = int(item_name)
            if idx < 1 or idx > len(items):
                yield event.plain_result(f"背包里没有第 {idx} 件物品(共 {len(items)} 件)！『背包』查看全部～")
                return
            target = items[idx - 1]
        else:
            for it in items:
                d = it["data"]
                if item_name in d["name"]:
                    target = it
                    break
        # 背包没有 → 查已装备的（仅名称查找时）
        if not target and not item_name.isdigit():
            for slot, item in (player.get("equipment") or {}).items():
                if item and item_name in item["name"]:
                    target = {"data": item}
                    equipped = True
                    break
        if not target:
            yield event.plain_result(f"背包里没有叫『{item_name}』的物品！『背包』查看全部～")
            return
        d = target["data"]
        lines = []
        if d.get("slot"):
            # ===== 装备 =====
            q = C.QUALITY[d["quality"]]
            enh = d.get("enhance", 0)
            enh_str = f" +{enh}" if enh > 0 else ""
            equip_state = "(已装备)" if equipped else ""
            lines.append(f"{q['color']}【{d['name']}{enh_str}】({C.EQUIP_SLOTS[d['slot']]}){equip_state}")
            lines.append("━━━━━━━━━━━━")
            lines.append(f"品质：{q['name']} ｜ 需求等级：Lv.{d['lv']}")
            if d.get("weapon_type"):
                # 阶段八：武器不锁职业，只显示类型（20 章装备只限属性）
                lines.append(f"类型：{C.display('weapon_types', d['weapon_type'])}")
                flavor_desc = C.WEAPON_FLAVOR.get(d["weapon_type"], {}).get("desc", "")
                if flavor_desc:
                    lines.append(f"✦ {flavor_desc}")
            st = d.get("stats", {})
            stat_names = {"atk": "攻击", "def": "防御", "matk": "魔攻", "mdef": "魔防",
                          "hp": "生命", "mp": "魔力", "spd": "速度", "crit": "暴击", "dodge": "闪避"}
            stat_lines = []
            for k, v in st.items():
                if v:
                    label = stat_names.get(k, k)
                    stat_lines.append(f"{label} +{int(v * 100)}%" if k in ("crit", "dodge") else f"{label} +{v}")
            if stat_lines:
                lines.append("属性：" + "  ".join(stat_lines))
            # 阶段八：特效词条 v2（ID 列表 → 名称+描述）+ 传说专属
            aff_lines = []
            for af in d.get("affixes", []):
                if isinstance(af, dict):  # 旧结构兼容
                    k, v = af.get("stat"), af.get("value", 0)
                    label = stat_names.get(k, k)
                    aff_lines.append(f"{label} +{int(v * 100)}%" if k in ("crit", "dodge") else f"{label} +{v}")
                    continue
                info = C.AFFIXES.get(af)
                if info:
                    aff_lines.append(f"{info['name']}({info['desc']})")
            if aff_lines:
                lines.append("✨ 词条：" + "  ".join(aff_lines))
            if d.get("legendary"):
                lg = C.LEGENDARY_EFFECTS.get(d["legendary"])
                if lg:
                    lines.append(f"✨ 专属·{lg['name']}：{lg['desc']}")
            # 阶段八：属性需求（不锁职业，只锁力量/智力/敏捷/耐力）
            req = d.get("req")
            if req:
                req_names = {"str": "力量", "agi": "敏捷", "int": "智力", "vit": "耐力"}
                req_str = " + ".join(f"{req_names.get(k, k)} {v}" for k, v in req.items())
                lines.append(f"需求：{req_str}")
            # v10：附魔（v34：符文效果词条，带等级）
            ench_lines = []
            for en in d.get("enchant", []):
                if en.get("effect"):
                    eff_name = C.RUNE_EFFECT_NAMES.get(en["effect"], en["effect"])
                    lvl = int(en.get("lvl", 1) or 1)
                    roman = C.RUNE_LEVEL_ROMAN.get(lvl, "")
                    ench_lines.append(f"『{eff_name}{roman}』")
                else:
                    k, v = en.get("stat"), en.get("value", 0)
                    label = stat_names.get(k, k)
                    ench_lines.append(f"{label} +{int(v * 100)}%" if k in ("crit", "dodge") else f"{label} +{v}")
            if ench_lines:
                lines.append("🔮 符文： " + "  ".join(ench_lines))
            # v10：套装归属
            if d.get("set"):
                sinfo = C.SETS.get(d["set"])
                if sinfo:
                    b4_desc = sinfo.get("bonus_4", {}).get("desc", "")
                    lines.append(f"🎴 套装：{sinfo['icon']}{d['set']}({b4_desc})")
            if enh > 0:
                info = C.ENHANCE_TABLE.get(enh)
                lines.append(f"强化：+{enh}" + (f"(属性 {int(info['mult'] * 100)}%)" if info else ""))
            if d.get("desc"):
                lines.append(f"描述：{d['desc']}")
            lines.append("")
            lines.append(f"💡 『装备 {d['name']}』穿上它 ｜ 出售价 {d.get('price', 0)} 金币")
        elif d.get("type") == "材料":
            # ===== 材料 =====
            lines.append(f"🧪 【{d['name']}】")
            lines.append("━━━━━━━━━━━━")
            lines.append("类型：材料")
            mat = C.MATERIALS.get(d["name"])
            if mat and mat.get("desc"):
                lines.append(f"描述：{mat['desc']}")
            lines.append("")
            lines.append(f"💡 出售价 {d.get('price', 0)} 金币 ｜ 『出售 {d['name']}』变现 ｜ 『喂养 {d['name']}』喂宠物")
        elif d.get("type") == "符文":
            # ===== 符文（v34） =====
            lines.append(f"💎 【{d['name']}】")
            lines.append("━━━━━━━━━━━━")
            lines.append(f"类型：符文 ｜ 品质：{d.get('quality', '')} ｜ 等级：{C.RUNE_LEVEL_ROMAN.get(int(d.get('lvl', 1) or 1), '')}")
            if d.get("desc"):
                lines.append(f"效果：{d['desc']}")
            lines.append("")
            lines.append(f"💡 『附魔 <装备名> {d['name']}』刻印到装备 ｜ 出售价 {d.get('price', 0)} 金币")
        elif d.get("type") == "图纸":
            # ===== 图纸（v41 毕业套锻造材料） =====
            lines.append(f"📜 【{d['name']}】")
            lines.append("━━━━━━━━━━━━")
            lines.append(f"类型：图纸 ｜ 阶段：{d.get('stage', '')} ｜ 职业：{d.get('class', '')}")
            if d.get("desc"):
                lines.append(f"描述：{d['desc']}")
            lines.append("")
            lines.append(f"💡 到铁匠铺『锻造 {d.get('blueprint_for', '')}』系列装备 ｜ 出售价 {d.get('price', 0)} 金币")
        elif d.get("type") == "宠物蛋":
            # ===== 宠物蛋 =====
            lines.append(f"🥚 【{d['name']}】")
            lines.append("━━━━━━━━━━━━")
            pdef = next((p for p in C.PET_POOL if p["key"] == d.get("pet_key")), None)
            if pdef:
                lines.append(f"可孵化：{pdef['icon']}{pdef['name']}(怪物 Lv.{pdef['lv']} 及以上掉落)")
                lines.append(f"描述：{pdef['desc']}")
            else:
                lines.append("神秘的蛋，『使用 宠物蛋』孵化试试？")
            lines.append("")
            lines.append("💡 『使用 宠物蛋』孵化")
        else:
            # ===== 消耗品/道具 =====
            lines.append(f"📦 【{d['name']}】")
            lines.append("━━━━━━━━━━━━")
            if d.get("type"):
                lines.append(f"类型：{d['type']}")
            if d.get("desc"):
                lines.append(f"效果：{d['desc']}")
            elif d.get("heal"):
                lines.append(f"效果：恢复 {d['heal']} 点生命")
            elif d.get("mana"):
                lines.append(f"效果：恢复 {d['mana']} 点魔力")
            lines.append("")
            if d.get("price"):
                lines.append(f"💡 出售价 {d['price']} 金币")
            lines.append(f"💡 『使用 {d['name']}』使用它")
        yield event.plain_result("\n".join(lines))

    def _req_check(self, player: dict, d: dict):
        """阶段八：装备属性需求检查。返回 (通过, 提示文本)。"""
        # v95.4：新手武器（橡木系列 Lv.2-3）需求已从名册移除，旧存量装备快照仍带 req → 一并豁免
        if d.get("slot") == "weapon" and d.get("lv", 99) <= 3:
            return True, ""
        # v95.7 #27：v93 商店装饰品（毛皮帽/橡木戒指/橡木项链）名册已去 req，旧存量快照仍带 → 豁免
        if d.get("slot") in ("ring", "necklace", "helm") and d.get("lv", 99) <= 4:
            return True, ""
        req = d.get("req")
        if not req:
            return True, ""
        attr = player.get("attributes") or {}
        names = {"str": "力量", "agi": "敏捷", "int": "智力", "vit": "耐力"}
        missing = []
        for k, need in req.items():
            cur = attr.get(k, 0)
            if cur < need:
                missing.append(f"{names.get(k, k)} {cur}/{need}")
        if missing:
            req_str = "、".join(f"{names.get(k, k)} {v}" for k, v in req.items())
            return False, f"需求：{req_str}(你当前 {'、'.join(missing)})"
        return True, ""

    def _buy_weapon(self, wname: str, wtype: str, wlv: int, wq: str) -> dict:
        """阶段八：商店武器生成。名册名走名册精确生成（正确 req + 固定词条），
        非名册武器名（兜底）走随机生成再覆盖名。"""
        ids = C.EQUIP_ROSTER_BY_NAME.get(wname, [])
        if ids:
            return C.generate_roster_equip(ids[0])
        eq = C.generate_equip("weapon", wlv, wq, wtype)
        eq["name"] = wname
        return eq

    @filter.regex(r"^(?:\[At:\d+\]\s*)?装备(?:\s*|$)")

    async def equip(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        item_name = self._strip_cmd(event, "装备")
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        if self._in_battle(group_id, qq_id):
            yield event.plain_result("战斗中不能更换装备！先解决眼前的敌人吧～")
            return
        item_name = item_name.strip()
        items = db.get_inventory(group_id, qq_id)
        # 找装备
        target = None
        if item_name.isdigit():
            # 序号装备：『装备 1』→ 背包第 1 件物品（须为装备，与『背包』序号一致）
            idx = int(item_name)
            if idx < 1 or idx > len(items):
                yield event.plain_result(f"背包里没有第 {idx} 件物品(共 {len(items)} 件)！『背包』查看～")
                return
            if not items[idx - 1]["data"].get("slot"):
                yield event.plain_result(f"背包第 {idx} 件『{items[idx-1]['data']['name']}』不是装备！『背包』查看～")
                return
            target = items[idx - 1]
        else:
            # 名字查找：收集所有同名/包含名字的装备，多个时提示用序号精确选择
            matches = []
            for it in items:
                d = it["data"]
                if d.get("slot") and (item_name in d["name"]):
                    matches.append(it)
            if len(matches) > 1:
                lines = [f"❓ 找到 {len(matches)} 件『{item_name}』，用序号指定穿哪件(『背包』看序号)："]
                for i, it in enumerate(matches, 1):
                    d = it["data"]
                    q = C.QUALITY[d["quality"]]
                    enh = d.get("enhance", 0)
                    enh_str = f" +{enh}" if enh > 0 else ""
                    lines.append(f"  {i}. {q['color']}【{d['name']}{enh_str}】({C.EQUIP_SLOTS[d['slot']]}) Lv.{d['lv']}")
                lines.append(f"💡 『装备 <背包序号>』直接穿，如『装备 {matches[0]['data']['name']}』会优先穿第一件")
                yield event.plain_result("\n".join(lines))
                return
            if matches:
                target = matches[0]
        if not target:
            yield event.plain_result(f"背包里没有叫『{item_name}』的装备！")
            return
        d = target["data"]
        # 阶段八：武器不锁职业（20 章），改为属性需求检查（力量/智力/敏捷/耐力）
        ok_req, req_msg = self._req_check(player, d)
        if not ok_req:
            yield event.plain_result(f"属性不够，穿不上【{d['name']}】！{req_msg}\n加点后属性达标才能装备(『属性』查看、『加点 力量 N』加点)")
            return
        # 等级限制
        if player["level"] < d["lv"]:
            yield event.plain_result(f"需要 Lv.{d['lv']} 才能装备【{d['name']}】，你才 Lv.{player['level']}")
            return
        equipment = dict(player["equipment"])
        old = equipment.get(d["slot"])
        # v95.7 #28：无论槽位是否有旧装备都计算穿前属性——空槽穿第一件时 old 为 None，
        # 旧代码 old_stats 保持 None 导致 diff 显示"(无变化)"；title_bonus 与穿后一致
        old_stats = E.player_final_stats(player["class_name"], player["level"], equipment,
                                         player.get("class_tier", 0), player.get("attributes"), player.get("evolve_path", 0), self._title_bonus(group_id, qq_id), player.get("race"))
        # 卸下旧装备回背包
        if old:
            import uuid
            db.add_item(group_id, qq_id, f"eq_{uuid.uuid4().hex[:8]}", old)
        equipment[d["slot"]] = d
        db.update_player(group_id, qq_id, equipment=equipment)
        db.remove_item(group_id, qq_id, target["key"])
        q = C.QUALITY[d["quality"]]
        st = E.player_final_stats(player["class_name"], player["level"], equipment, player.get("class_tier", 0), player.get("attributes"), player.get("evolve_path", 0), self._title_bonus(group_id, qq_id), player.get("race"))
        # v16：属性变化对比（对比穿上前后的差值）
        diff_parts = []
        if old_stats is not None:
            keys = [("atk", "攻击"), ("def", "防御"), ("matk", "魔攻"), ("mdef", "魔防"),
                    ("spd", "速度"), ("max_hp", "生命"), ("max_mp", "魔力"), ("crit", "暴击"), ("dodge", "闪避")]
            for k, label in keys:
                diff = st[k] - old_stats[k]
                if abs(diff) >= 1e-9:
                    if k in ("crit", "dodge"):
                        diff_parts.append(f"{label} {'+' if diff > 0 else ''}{int(diff*100)}%")
                    else:
                        diff_parts.append(f"{label} {'+' if diff > 0 else ''}{diff}")
        diff_str = "  ".join(diff_parts) if diff_parts else "(无变化)"
        yield event.plain_result(
            f"✅ 你装备了 {q['color']}【{d['name']}】！\n"
            f"📊 属性变化：{diff_str}\n"
            f"当前属性：攻击 {st['atk']} 防御 {st['def']} 魔攻 {st['matk']} 魔防 {st['mdef']}"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?卸下(?:\s*|$)")

    async def unequip(self, event: AstrMessageEvent):
        """卸下装备回背包(v33)"""
        group_id, qq_id = self._uid(event)
        raw = self._strip_cmd(event, "卸下").strip()
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        if self._in_battle(group_id, qq_id):
            yield event.plain_result("战斗中不能更换装备！先解决眼前的敌人吧～")
            return
        equipment = dict(player["equipment"])
        # 匹配部位：中文部位名或装备名
        slot = None
        slot_by_name = {v: k for k, v in C.EQUIP_SLOTS.items()}
        if raw in slot_by_name:
            slot = slot_by_name[raw]
        else:
            for s, item in equipment.items():
                if item and raw and raw in item.get("name", ""):
                    slot = s
                    break
        if not slot:
            yield event.plain_result(
                f"没找到『{raw}』对应装备！用『卸下 <部位/装备名>』，如『卸下 头盔』『卸下 烈焰之刃』。\n"
                f"部位：{'、'.join(C.EQUIP_SLOTS.values())}"
            )
            return
        item = equipment.get(slot)
        if not item:
            yield event.plain_result(f"{C.EQUIP_SLOTS[slot]}位置没有装备！")
            return
        # 属性变化对比（复用 equip 逻辑；v95.7 #28：title_bonus 与卸后一致）
        old_stats = E.player_final_stats(player["class_name"], player["level"], equipment,
                                         player.get("class_tier", 0), player.get("attributes"), player.get("evolve_path", 0), self._title_bonus(group_id, qq_id), player.get("race"))
        import uuid
        db.add_item(group_id, qq_id, f"eq_{uuid.uuid4().hex[:8]}", item)
        equipment[slot] = None
        db.update_player(group_id, qq_id, equipment=equipment)
        st = E.player_final_stats(player["class_name"], player["level"], equipment, player.get("class_tier", 0), player.get("attributes"), player.get("evolve_path", 0), self._title_bonus(group_id, qq_id), player.get("race"))
        diff_parts = []
        keys = [("atk", "攻击"), ("def", "防御"), ("matk", "魔攻"), ("mdef", "魔防"),
                ("spd", "速度"), ("max_hp", "生命"), ("max_mp", "魔力"), ("crit", "暴击"), ("dodge", "闪避")]
        for k, label in keys:
            diff = st[k] - old_stats[k]
            if abs(diff) >= 1e-9:
                if k in ("crit", "dodge"):
                    diff_parts.append(f"{label} {'+' if diff > 0 else ''}{int(diff*100)}%")
                else:
                    diff_parts.append(f"{label} {'+' if diff > 0 else ''}{diff}")
        diff_str = "  ".join(diff_parts) if diff_parts else "(无变化)"
        q = C.QUALITY[item["quality"]]
        enh = item.get("enhance", 0)
        enh_str = f" +{enh}" if enh > 0 else ""
        yield event.plain_result(
            f"✅ 你卸下了 {q['color']}【{item['name']}{enh_str}】({C.EQUIP_SLOTS[slot]})\n"
            f"📊 属性变化：{diff_str}\n"
            f"当前属性：攻击 {st['atk']} 防御 {st['def']} 魔攻 {st['matk']} 魔防 {st['mdef']}"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?使用(?:\s*|$)")

    async def use(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        item_name = self._strip_cmd(event, "使用")
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        item_name = item_name.strip()
        items = db.get_inventory(group_id, qq_id)
        target = None
        if item_name.isdigit():
            # 序号使用：『使用 1』→ 背包第 1 件物品（须非装备，与『背包』序号一致）
            idx = int(item_name)
            if idx < 1 or idx > len(items):
                yield event.plain_result(f"背包里没有第 {idx} 件物品(共 {len(items)} 件)！『背包』查看～")
                return
            if items[idx - 1]["data"].get("slot"):
                yield event.plain_result(f"背包第 {idx} 件是装备，用『装备 {idx}』穿上！")
                return
            target = items[idx - 1]
        else:
            for it in items:
                d = it["data"]
                if not d.get("slot") and (item_name in d["name"]):
                    target = it
                    break
        if not target:
            yield event.plain_result(f"背包里没有『{item_name}』！")
            return
        d = target["data"]
        # 战斗中：只允许恢复类 + 战斗药水，且算一回合（敌方会行动）
        buff_eff = d.get("effect", "")
        is_buff = buff_eff in ("buff_atk", "buff_def", "buff_spd", "buff_crit", "buff_matk", "buff_atk_def")
        if self._in_battle(group_id, qq_id):
            # v94 体力：体力食物也算战斗可用恢复类
            if not (d.get("heal") or d.get("mana") or d.get("stamina") or is_buff):
                yield event.plain_result("战斗中只能使用恢复类道具或战斗药水！战斗结束才能用其他物品～")
                return
            battle = db.get_battle(group_id, qq_id)
            if not battle:
                yield event.plain_result("你不在战斗中！")
                return
            if battle["state"].get("type") == "pvp":
                yield event.plain_result("PVP 战斗无法使用道具！")
                return
            b = BT.Battle.from_state(battle["state"])
            heal = d.get("heal", 0)
            mana = d.get("mana", 0)
            if heal <= 0 and mana <= 0 and not d.get("stamina") and not is_buff:
                yield event.plain_result("该道具没有恢复/增益效果，战斗中无法使用～")
                return
            # 扣物品（战斗回合使用）
            db.remove_item(group_id, qq_id, target["key"])
            # v94 体力：战斗中使用食物恢复体力（不占回合结算显示）
            if d.get("stamina"):
                self._add_stamina(group_id, qq_id, int(d["stamina"]), player)
            # 生命/魔力恢复（先恢复再走回合，怪物行动可能打掉）
            # v82 阶段四：heal/mana < 1 视为百分比（新世界 13 章），>=1 视为固定值（旧物品兼容）
            if heal:
                if heal < 1:
                    heal = int(player["max_hp"] * heal)
                new_hp = min(player["max_hp"], player["hp"] + heal)
                player["hp"] = new_hp
            if mana:
                if mana < 1:
                    mana = int(player["max_mp"] * mana)
                new_mp = min(player["max_mp"], player["mp"] + mana)
                player["mp"] = new_mp
            # v54 战斗药水：传 buff:<p_buffs key>（atk_up/def_up/spd_up/crit_up）
            # 9.3：buff_matk → matk_up_pot（鲛人之泪）、buff_atk_def → 复合（龙涎药剂）
            _BF = {"buff_atk": "atk_up", "buff_def": "def_up", "buff_spd": "spd_up",
                   "buff_crit": "crit_up", "buff_matk": "matk_up_pot",
                   "buff_atk_def": "atk_up,def_up"}
            payload = f"buff:{_BF[buff_eff]}" if is_buff else str(heal)
            logs, ended = b.player_turn("use_item", payload, player)
            db.update_player(group_id, qq_id, hp=player["hp"], mp=player["mp"])
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
            log_str = "\n".join(logs)
            yield event.plain_result(
                f"{log_str}\n━━━━━━━━━━━━\n"
                f"❤️ HP {player['hp']}/{player['max_hp']}  💙 MP {player['mp']}/{player['max_mp']}\n"
                f"你的行动：『攻击』『技能 <名称>』『防御』『逃跑』"
            )
            return
        # 消耗品（v82 阶段四：heal/mana < 1 视为百分比）
        # v94 体力：食物恢复体力（可与 hp/mp 同物品叠加显示）
        st_gain = 0
        st_msg = ""
        if d.get("stamina"):
            st_gain = self._add_stamina(group_id, qq_id, int(d["stamina"]), player)
            if st_gain > 0:
                _p3 = self._player(group_id, qq_id)
                st_msg = f"\n⚡ 恢复 {st_gain} 点体力({self._stamina(_p3)}/{self._stamina_max(_p3)})"
        if d.get("heal"):
            heal_v = d["heal"]
            if heal_v < 1:
                heal_v = int(player["max_hp"] * heal_v)
            new_hp = min(player["max_hp"], player["hp"] + heal_v)
            db.update_player(group_id, qq_id, hp=new_hp)
            db.remove_item(group_id, qq_id, target["key"])
            yield event.plain_result(f"💊 你使用了【{d['name']}】，恢复 {heal_v} 点生命！\n❤️ {new_hp}/{player['max_hp']}{st_msg}")
        elif d.get("mana"):
            mana_v = d["mana"]
            if mana_v < 1:
                mana_v = int(player["max_mp"] * mana_v)
            new_mp = min(player["max_mp"], player["mp"] + mana_v)
            db.update_player(group_id, qq_id, mp=new_mp)
            db.remove_item(group_id, qq_id, target["key"])
            yield event.plain_result(f"💙 你使用了【{d['name']}】，恢复 {mana_v} 点魔力！\n💙 {new_mp}/{player['max_mp']}{st_msg}")
        elif d.get("stamina") is not None:
            if st_gain > 0:
                db.remove_item(group_id, qq_id, target["key"])
                yield event.plain_result(f"🍖 你吃下了【{d['name']}】！{st_msg}")
            else:
                _p4 = self._player(group_id, qq_id)
                yield event.plain_result(f"🍖 你肚子还饱着呢(体力 {self._stamina(_p4)}/{self._stamina_max(_p4)})，先活动活动再吃吧～")
        elif d.get("effect") == "return_vila":
            db.remove_item(group_id, qq_id, target["key"])
            db.update_player(group_id, qq_id, cur_map="oak_town", cur_subarea="oak_town_1")
            yield event.plain_result("🧭 卷轴展开，光芒闪过——你回到了橡木镇中心广场！")
        elif d.get("effect") == "lucky":
            # v54 幸运护符：10 分钟打怪金币 ×1.5、材料 +1
            db.remove_item(group_id, qq_id, target["key"])
            db.update_player(group_id, qq_id, lucky_until=int(time.time()) + 600)
            yield event.plain_result(
                "🍀 幸运护符泛起微光，你的气息变得祥和……\n"
                "💡 10 分钟内打怪金币＋50%、材料掉落＋1！"
            )
        elif d.get("effect") == "clear_red":
            # v84 红名清除券（26 章 3.3）：立即消除红名
            if not self._is_redname(qq_id):
                yield event.plain_result("你现在不是红名，用不着这张券～(留着防身吧)")
                return
            db.remove_item(group_id, qq_id, target["key"])
            db.set_event_state(f"red_{qq_id}", "0")
            yield event.plain_result("🎫 券面符文亮起，笼罩你的杀气消散了！你不再是红名了。")
        elif d.get("effect") == "open_chest":
            import uuid
            db.remove_item(group_id, qq_id, target["key"])
            gold = random.randint(30, 80) + player["level"] * 3
            db.update_player(group_id, qq_id, gold=player["gold"] + gold)
            lines = [f"🎁 你打开了【{d['name']}】！", f"💰 获得 {gold} 金币！"]
            # v41：宝箱不再掉成品装备，改为掉图纸（装备统一走锻造）
            if random.random() < 0.5:
                bp = C.roll_blueprint(max(1, player["level"]))
                db.add_item(group_id, qq_id, f"eq_{uuid.uuid4().hex[:8]}", bp)
                lines.append(f"📜 宝箱里还有：{bp['name']}！")
            yield event.plain_result("\n".join(lines))
        elif d.get("type") == "宠物蛋":
            # 孵化宠物（24 章三：使用宠物蛋 → 获得对应品种宠物，首次孵化自动命名）
            pet_key = d.get("pet_key")
            if not pet_key:
                yield event.plain_result("这枚宠物蛋有点奇怪……")
                return
            pet = db.pet_get(qq_id)
            # 饱食度自然衰减先结算（防止换了很久的宠物面板数据过期）
            pet = db.pet_decay_satiety(pet)
            if pet:
                db.pet_update(qq_id, satiety=pet["satiety"], last_sat_time=pet["last_sat_time"])
            if pet:
                same = pet.get("pet_key") == pet_key
                if same:
                    yield event.plain_result("你已经有一只【该品种】宠物啦！可以『出售』这颗蛋，或『放生』后重新孵化(图鉴记录保留)。")
                else:
                    yield event.plain_result("你已经有一只宠物啦！先『放生』再孵化新品种吧～")
                return
            pdef = next((p for p in C.PET_POOL if p["key"] == pet_key), None)
            if not pdef:
                yield event.plain_result("宠物蛋里的生命气息微弱……")
                return
            db.remove_item(group_id, qq_id, target["key"])
            db.pet_create(qq_id, pet_key, pdef["name"])
            db.pet_dex_add(qq_id, pet_key)
            dex_count = len(db.pet_dex_get(qq_id))
            yield event.plain_result(
                f"🥚 宠物蛋微微颤动……裂开了！\n"
                f"🎉 {pdef['icon']} 【{pdef['name']}】破壳而出，成为了你的伙伴！(图鉴 {dex_count}/4)\n"
                f"💡 输入『宠物』查看，『喂养 <食材>』恢复饱食度，升到 Lv.10 解锁宠物技能！"
            )
        elif d.get("type") == "坐骑":
            # 坐骑缰绳：解锁坐骑
            mk = d.get("mount_key")
            mdef = C.MOUNT_BY_KEY.get(mk) if mk else None
            if not mdef:
                yield event.plain_result("这缰绳上的气息有点古怪……")
                return
            mounts = player.get("mounts") or {}
            owned = list(mounts.get("owned") or [])
            if mk in owned:
                yield event.plain_result(f"你已经拥有『{mdef['name']}』了！")
                return
            owned.append(mk)
            mounts["owned"] = owned
            db.update_player(group_id, qq_id, mounts=mounts)
            db.remove_item(group_id, qq_id, target["key"])
            yield event.plain_result(
                f"🐾 缰绳上的封印解开，{mdef['icon']}【{mdef['name']}】顺从地蹭了蹭你！\n"
                f"💡 输入『骑乘 {mdef['name']}』骑上它，『坐骑』查看全部！"
            )
        else:
            yield event.plain_result(f"『{d['name']}』不能使用。")

    def _cur_subarea(self, player: dict) -> dict:
        """当前所在子区域 dict（无则 {}）。"""
        cur_map = player.get("cur_map", "")
        sa_id = player.get("cur_subarea") or ""
        cm = C.MAP_BY_ID.get(cur_map, {})
        for sa in (cm.get("subareas") or []):
            if sa["id"] == sa_id:
                return sa
        return {}

    def _is_smith_shop(self, player: dict) -> bool:
        """v92 铁匠类商店：craft 场所只卖武器+锻造材料。
        炼金工坊除外（炼金卖药剂合理，dawn_city_5）。"""
        sa = self._cur_subarea(player)
        if not sa:
            return False
        if "炼金" in sa.get("name", ""):
            return False
        funcs = sa.get("funcs") or []
        if "craft" in funcs:
            return True
        return any(k in sa.get("name", "") for k in ("铁匠", "锻造", "军械", "工坊", "强化"))

    def _pawn_rate(self, player: dict, d: dict):
        """v93 材料回收价：铁匠/工坊 0.9（矿石金属）、炼金工坊 0.9（草药粉尘）、普通商店 0.8（杂货）；非设施 None（材料不可售）。"""
        if d.get("type", "") != "材料":
            return 1.0
        sa = self._cur_subarea(player)
        if not sa:
            return None
        name = sa.get("name", "")
        funcs = sa.get("funcs") or []
        if "炼金" in name or "alchemy" in funcs:
            return 0.9
        if self._is_smith_shop(player):
            return 0.9
        if self._at_shop(player):
            return 0.8
        return None

    def _sell_one(self, group_id, qq_id, player, it, rate):
        """出售单件物品（按回收价），返回 (名称, 数量, 金币) 或 None。"""
        d = it["data"]
        price = int(d.get("price", 0) * rate)
        if price <= 0:
            return None
        db.update_player(group_id, qq_id, gold=player["gold"] + price * it["count"])
        db.remove_item(group_id, qq_id, it["key"], it["count"])
        return (d["name"], it["count"], price * it["count"])

    @filter.regex(r"^(?:\[At:\d+\]\s*)?出售(?:\s*|$)")

    async def sell(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        item_name = self._strip_cmd(event, "出售")
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        item_name = item_name.strip()
        items = db.get_inventory(group_id, qq_id)
        # 批量出售模式：『出售 全部』/『出售 材料』/『出售 装备』
        if item_name in ("全部", "所有", "全部物品"):
            mode = "all"
        elif item_name in ("材料", "材料 全部", "全部材料"):
            mode = "mat"
        elif item_name in ("装备", "装备 全部", "全部装备"):
            mode = "equip"
        else:
            mode = None
        if mode:
            blocked = 0
            total = 0
            sold = []
            for it in items:
                d = it["data"]
                if mode == "mat" and d.get("type", "") != "材料":
                    continue
                if mode == "equip" and not d.get("slot"):
                    continue
                rate = self._pawn_rate(player, d)
                if rate is None:
                    blocked += 1
                    continue
                r = self._sell_one(group_id, qq_id, player, it, rate)
                if r:
                    sold.append(f"{r[0]} ×{r[1]}（{r[2]} 金）")
                    total += r[2]
                    player = self._player(group_id, qq_id)
            if not sold:
                tip = "（材料要去城镇商店/铁匠铺/炼金工坊才能卖）" if blocked else ""
                yield event.plain_result(f"没有可出售的物品！{tip}")
                return
            head = "全部" if mode == "all" else ("材料" if mode == "mat" else "装备")
            lines = [f"💰 批量出售{head}完成，共 {len(sold)} 种物品，获得 {total} 金币！"]
            for s in sold[:8]:
                lines.append(f"  · {s}")
            if len(sold) > 8:
                lines.append(f"  · ……等 {len(sold)} 种")
            if blocked:
                lines.append(f"💡 有 {blocked} 种材料需要到城镇商店/铁匠铺/炼金工坊出售～")
            yield event.plain_result("\n".join(lines))
            return
        target = None
        if item_name.isdigit():
            # 序号出售：『出售 1』→ 背包第 1 件物品（与『背包』序号一致）
            idx = int(item_name)
            if idx < 1 or idx > len(items):
                yield event.plain_result(f"背包里没有第 {idx} 件物品（共 {len(items)} 件）！『背包』查看～")
                return
            target = items[idx - 1]
        else:
            for it in items:
                d = it["data"]
                if item_name in d["name"]:
                    target = it
                    break
        if not target:
            yield event.plain_result(f"背包里没有『{item_name}』！")
            return
        d = target["data"]
        rate = self._pawn_rate(player, d)
        if rate is None:
            yield event.plain_result(f"『{d['name']}』是材料，要到城镇的商店（杂货）/铁匠铺/炼金工坊才能回收成金币～")
            return
        r = self._sell_one(group_id, qq_id, player, target, rate)
        if not r:
            yield event.plain_result(f"『{d['name']}』不能出售。")
            return
        name, cnt, gold = r
        tip = "" if rate >= 1.0 else f"（回收价 {int(rate * 100)}%）"
        yield event.plain_result(f"💰 你出售了 {name} ×{cnt}，获得 {gold} 金币！{tip}")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?商店(?:\s*|$)")

    async def shop(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        if self._is_redname(qq_id):
            yield event.plain_result("☠️ 你是红名！商店老板把你轰了出来……（等红名消退再来）")
            return
        cur = player["cur_map"]
        cur_map = C.MAP_BY_ID.get(cur, {})
        if not self._at_shop(player, group_id, qq_id):
            hint = self._facility_hint(player, "shop")
            yield event.plain_result(
                f"这里没有商店！到有商店的地方（如 {hint}）再输入『商店』吧～" if hint else "这里没有商店！去城镇里找找商铺吧～"
            )
            return
        area_id = cur_map.get("area", cur)
        is_smith = self._is_smith_shop(player)
        subarea = self._cur_subarea(player)
        shop_title = (subarea.get("name") or cur_map.get("name") or cur)
        lines = []
        entries = []
        if is_smith:
            # 铁匠类商店：只卖武器 + 锻造材料 + 全套装备，不卖消耗品
            materials = C.SHOP_SMITH_MATERIALS.get(cur) or C.SHOP_SMITH_MATERIALS.get(area_id, [])
            for mid in materials:
                mt = C.MATERIALS[mid]
                entries.append((mid, f"{mt['name']} —— {mt['price']} 金币（锻造材料）"))
            # v94 图纸经济：铁匠铺兜底卖图纸（随机一张，价格 = 图纸价×3 = (lv×3+20)×3）
            bp_price = int((max(1, player["level"]) * 3 + 20) * 3)
            entries.append(("bp:rand", f"📜 神秘锻造图纸（随机一张）—— {bp_price} 金币"))
            equip_items = C.SHOP_EQUIP.get(cur) or C.SHOP_EQUIP.get(area_id, [])
            for rid in equip_items:
                r = C.EQUIP_ROSTER[rid]
                q = C.QUALITY[r["quality"]]
                entries.append((f"e:{rid}", f"{q['color']}{r['name']}（{C.EQUIP_SLOTS[r['slot']]}）Lv.{r['lv']} —— {int((8 + r['lv'] * 6) * q['mult'])} 金币"))
            weapons = C.SHOP_WEAPONS.get(cur) or C.SHOP_WEAPONS.get(area_id, [])
            for wname, wtype, wlv, wq in weapons:
                q = C.QUALITY[wq]
                entries.append((f"w:{wname}", f"{q['color']}{wname}（{C.display('weapon_types', wtype)}）Lv.{wlv} —— {int((8 + wlv * 6) * q['mult'])} 金币"))
        else:
            # 普通商店：消耗品 + 武器
            shop_items = C.SHOP_ITEMS.get(cur) or C.SHOP_ITEMS.get(area_id, [])
            if not shop_items and self._wild_trader_here(player, group_id, qq_id):
                shop_items = C.SHOP_WILD_TRADE  # v95.4：野外行商货物
                shop_title = "🧭 游商·老马的货摊"
            for iid in shop_items:
                it = C.ITEMS[iid]
                entries.append((iid, f"{it['name']} —— {it['price']} 金币（{it['desc']}）"))
            weapons = C.SHOP_WEAPONS.get(cur) or C.SHOP_WEAPONS.get(area_id, [])
            for wname, wtype, wlv, wq in weapons:
                q = C.QUALITY[wq]
                entries.append((f"w:{wname}", f"{q['color']}{wname}（{C.display('weapon_types', wtype)}）Lv.{wlv} —— {int((8 + wlv * 6) * q['mult'])} 金币"))
        raw = self._strip_cmd(event, "商店")
        page = self._parse_page(raw)
        page_items, pages, page = self._page_items(entries, page, per_page=5)
        lines = [f"🏪 【{shop_title} 商店】（第 {page}/{pages} 页 · 共 {len(entries)} 件）", "━━━━━━━━━━━━"]
        for i, (key, row) in enumerate(page_items, (page - 1) * 5 + 1):
            lines.append(f"{i:>2}. {row}")
        lines.append("")
        if pages > 1:
            lines.append(f"💡 『商店 {page+1}』看下一页（共 {pages} 页）")
        lines.append(f"💰 你的金币：{player['gold']}")
        lines.append("💡 『购买 <名称>』或『购买 <序号>』")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?购买(?:\s*|$)")

    async def buy(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        item_name = self._strip_cmd(event, "购买")
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        if self._is_redname(qq_id):
            yield event.plain_result("☠️ 你是红名！商店老板不敢卖你东西……（等红名消退再来）")
            return
        cur = player["cur_map"]
        cur_map = C.MAP_BY_ID.get(cur, {})
        if not self._at_shop(player, group_id, qq_id):
            hint = self._facility_hint(player, "shop")
            yield event.plain_result(
                f"这里没有商店！到有商店的地方（如 {hint}）再输入『购买』吧～" if hint else "这里没有商店！去城镇里找找商铺吧～"
            )
            return
        area_id = cur_map.get("area", cur)
        is_smith = self._is_smith_shop(player)
        shop_items = [] if is_smith else (C.SHOP_ITEMS.get(cur) or C.SHOP_ITEMS.get(area_id, []))
        if not shop_items and not is_smith and self._wild_trader_here(player, group_id, qq_id):
            shop_items = C.SHOP_WILD_TRADE  # v95.4：野外行商货物
        materials = (C.SHOP_SMITH_MATERIALS.get(cur) or C.SHOP_SMITH_MATERIALS.get(area_id, [])) if is_smith else []
        item_name = item_name.strip()
        # 商队集市事件：商店 8 折
        discount = 1.0
        cur_evt = db.get_world_event()
        if cur_evt and cur_evt["etype"] == "merchant":
            discount = 0.8
        weapons = C.SHOP_WEAPONS.get(cur) or C.SHOP_WEAPONS.get(area_id, [])
        equip_items = C.SHOP_EQUIP.get(cur) or C.SHOP_EQUIP.get(area_id, [])
        # 序号购买：『购买 3』→ 与商店列表一致的第 3 件商品（顺序：材料→装备→武器，与 shop 面板一致）
        if item_name.isdigit():
            entries = list(shop_items) + [f"m:{m}" for m in materials] + (["bp:rand"] if is_smith else []) + [f"e:{rid}" for rid in equip_items] + [f"w:{w[0]}" for w in weapons]
            idx = int(item_name)
            if idx < 1 or idx > len(entries):
                yield event.plain_result(f"没有第 {idx} 号商品！『商店』查看商品列表。")
                return
            key = entries[idx - 1]
            if key == "bp:rand":
                # v94 图纸经济：铁匠铺随机图纸（价格 = 图纸价×3，商队集市 8 折）
                bp_price = int((max(1, player["level"]) * 3 + 20) * 3 * discount)
                if player["gold"] < bp_price:
                    yield event.plain_result(f"金币不足！需要 {bp_price} 金币。")
                    return
                db.update_player(group_id, qq_id, gold=player["gold"] - bp_price)
                bp = C.roll_blueprint(max(1, player["level"]))
                import uuid
                db.add_item(group_id, qq_id, f"eq_{uuid.uuid4().hex[:8]}", bp)
                tip = "（商队集市 8 折！）" if discount < 1 else ""
                yield event.plain_result(f"✅ 你买到一张【{bp['name']}】！{tip}")
                return
            if str(key).startswith("m:"):
                # 锻造材料购买
                mid = str(key)[2:]
                mt = C.MATERIALS[mid]
                price = int(mt["price"] * discount)
                if player["gold"] < price:
                    yield event.plain_result(f"金币不足！需要 {price} 金币。")
                    return
                db.update_player(group_id, qq_id, gold=player["gold"] - price)
                db.add_item(group_id, qq_id, mid, {"name": mt["name"], "type": "材料", "stackable": True, "price": price})
                tip = "（商队集市 8 折！）" if discount < 1 else ""
                yield event.plain_result(f"✅ 你购买了【{mt['name']}】！{tip}")
                return
            if str(key).startswith("w:"):
                wname = str(key)[2:]
                wt = next((w for w in weapons if w[0] == wname), None)
                if not wt:
                    yield event.plain_result(f"商店里没有『{wname}』！输入『商店』查看商品。")
                    return
                wname, wtype, wlv, wq = wt
                price = int((8 + wlv * 6) * C.QUALITY[wq]["mult"] * discount)
                if player["gold"] < price:
                    yield event.plain_result(f"金币不足！需要 {price} 金币。")
                    return
                # 阶段八：武器不锁职业（20 章），名册名走名册精确生成
                db.update_player(group_id, qq_id, gold=player["gold"] - price)
                equip_item = self._buy_weapon(wname, wtype, wlv, wq)
                # v21 防刷钱：商店装备卖出价 = 买入价一半（否则属性推导价远高于买入价，可无限倒卖刷钱）
                equip_item["price"] = int(price * 0.5)
                import uuid
                db.add_item(group_id, qq_id, f"eq_{uuid.uuid4().hex[:8]}", equip_item)
                yield event.plain_result(f"✅ 你购买了【{wname}】！放到背包了，输入『装备 {wname}』使用。")
                return
            if str(key).startswith("e:"):
                # 名册装备购买（铁匠铺全套装备）
                rid = str(key)[2:]
                r = C.EQUIP_ROSTER[rid]
                q = C.QUALITY[r["quality"]]
                price = int((8 + r["lv"] * 6) * q["mult"] * discount)
                if player["gold"] < price:
                    yield event.plain_result(f"金币不足！需要 {price} 金币。")
                    return
                db.update_player(group_id, qq_id, gold=player["gold"] - price)
                equip_item = C.generate_roster_equip(rid)
                # v21 防刷钱：商店装备卖出价 = 买入价一半
                equip_item["price"] = int(price * 0.5)
                import uuid
                db.add_item(group_id, qq_id, f"eq_{uuid.uuid4().hex[:8]}", equip_item)
                yield event.plain_result(f"✅ 你购买了【{r['name']}】！放到背包了，输入『装备 {r['name']}』使用。")
                return
            else:
                iid = key
                it = C.ITEMS[iid]
                price = int(it["price"] * discount)
                if player["gold"] < price:
                    yield event.plain_result(f"金币不足！需要 {price} 金币。")
                    return
                db.update_player(group_id, qq_id, gold=player["gold"] - price)
                # v21 防刷钱：消耗品卖出价 = 实际支付价（商队 8 折时不能原价卖出套利）
                db.add_item(group_id, qq_id, iid, {"name": it["name"], "type": "消耗品", "stackable": True, "heal": it.get("heal", 0), "mana": it.get("mana", 0), "price": price, "effect": it.get("effect")})
                tip = "（商队集市 8 折！）" if discount < 1 else ""
                yield event.plain_result(f"✅ 你购买了【{it['name']}】！{tip}")
                return
        # 找补给品（按名称）
        for iid in shop_items:
            it = C.ITEMS[iid]
            if item_name in it["name"]:
                price = int(it["price"] * discount)
                if player["gold"] < price:
                    yield event.plain_result(f"金币不足！需要 {price} 金币。")
                    return
                db.update_player(group_id, qq_id, gold=player["gold"] - price)
                # v21 防刷钱：消耗品卖出价 = 实际支付价（商队 8 折时不能原价卖出套利）
                db.add_item(group_id, qq_id, iid, {"name": it["name"], "type": "消耗品", "stackable": True, "heal": it.get("heal", 0), "mana": it.get("mana", 0), "price": price, "effect": it.get("effect")})
                tip = "（商队集市 8 折！）" if discount < 1 else ""
                yield event.plain_result(f"✅ 你购买了【{it['name']}】！{tip}")
                return
        # 找材料（按名称）
        for mid in materials:
            mt = C.MATERIALS[mid]
            if item_name in mt["name"]:
                price = int(mt["price"] * discount)
                if player["gold"] < price:
                    yield event.plain_result(f"金币不足！需要 {price} 金币。")
                    return
                db.update_player(group_id, qq_id, gold=player["gold"] - price)
                db.add_item(group_id, qq_id, mid, {"name": mt["name"], "type": "材料", "stackable": True, "price": price})
                tip = "（商队集市 8 折！）" if discount < 1 else ""
                yield event.plain_result(f"✅ 你购买了【{mt['name']}】！{tip}")
                return
        # 找武器（按名称）
        for wname, wtype, wlv, wq in weapons:
            if item_name in wname:
                price = int((8 + wlv * 6) * C.QUALITY[wq]["mult"] * discount)
                if player["gold"] < price:
                    yield event.plain_result(f"金币不足！需要 {price} 金币。")
                    return
                # 阶段八：武器不锁职业（20 章），名册名走名册精确生成
                db.update_player(group_id, qq_id, gold=player["gold"] - price)
                equip_item = self._buy_weapon(wname, wtype, wlv, wq)
                # v21 防刷钱：商店装备卖出价 = 买入价一半
                equip_item["price"] = int(price * 0.5)
                import uuid
                db.add_item(group_id, qq_id, f"eq_{uuid.uuid4().hex[:8]}", equip_item)
                yield event.plain_result(f"✅ 你购买了【{wname}】！放到背包了，输入『装备 {wname}』使用。")
                return
        # 找装备（按名称）
        for rid in equip_items:
            r = C.EQUIP_ROSTER[rid]
            if item_name in r["name"]:
                q = C.QUALITY[r["quality"]]
                price = int((8 + r["lv"] * 6) * q["mult"] * discount)
                if player["gold"] < price:
                    yield event.plain_result(f"金币不足！需要 {price} 金币。")
                    return
                db.update_player(group_id, qq_id, gold=player["gold"] - price)
                equip_item = C.generate_roster_equip(rid)
                equip_item["price"] = int(price * 0.5)
                import uuid
                db.add_item(group_id, qq_id, f"eq_{uuid.uuid4().hex[:8]}", equip_item)
                yield event.plain_result(f"✅ 你购买了【{r['name']}】！放到背包了，输入『装备 {r['name']}』使用。")
                return
        # v39 坐骑：橡木镇马厩买老马（新世界 oak 区域，旧 vila 判断已随旧世界废弃）
        if "老马" in item_name or "马" == item_name.strip():
            if area_id != "oak" or cur != "oak_town":
                yield event.plain_result("橡木镇的商人才能买到老马！去橡木镇『商店』看看～")
                return
            mdef = C.MOUNT_BY_KEY["mount_horse"]
            mounts = player.get("mounts") or {}
            if "mount_horse" in (mounts.get("owned") or []):
                yield event.plain_result("你已经拥有老马了！")
                return
            price = int(mdef["price"] * discount)
            if player["gold"] < price:
                yield event.plain_result(f"金币不足！老马要 {price} 金币。")
                return
            db.update_player(group_id, qq_id, gold=player["gold"] - price)
            mounts = dict(player.get("mounts") or {})
            owned = list(mounts.get("owned") or [])
            owned.append("mount_horse")
            mounts["owned"] = owned
            db.update_player(group_id, qq_id, mounts=mounts)
            yield event.plain_result(f"🐴 你买了一匹老马！缰绳交到你手里，它打了个响鼻。\n💡 『骑乘 老马』骑上它，『坐骑』查看全部！")
            return
        yield event.plain_result(f"商店里没有『{item_name}』！输入『商店』查看商品。")
