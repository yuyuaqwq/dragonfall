# -*- coding: utf-8 -*-
"""《剑与魔法》命令层 - player（player）

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


class PlayerCmds(CommandBase):

    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:快捷绑定|快捷列表|快捷删除|快捷清除|快捷)(?:[\s\S]*)$")
    @require_player()

    async def shortcut(self, event: AstrMessageEvent):
        """快捷指令：绑定数字一键执行常用指令(如『快捷绑定 1 探索』，之后发『1』=探索)"""
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        shortcuts = player.get("shortcuts") or {}
        args = self._strip_cmd(event, "快捷").strip()
        # 子命令：绑定/列表/删除/清除
        sub = ""
        rest = args
        for s in ("绑定", "删除", "清除", "列表"):
            if args.startswith(s):
                sub = s
                rest = args[len(s):].strip()
                break
        if sub == "绑定":
            parts = rest.split(maxsplit=1)
            if len(parts) < 2 or not parts[0].isdigit():
                yield event.plain_result("📎 用法：『快捷绑定 <数字> <指令>』，如『快捷绑定 1 探索』\n发对应数字即可一键执行。")
                return
            num = parts[0]
            cmd_text = parts[1].strip()
            if len(cmd_text) > 30:
                yield event.plain_result("❌ 指令太长啦(≤30 字)～")
                return
            if cmd_text.isdigit():
                yield event.plain_result("❌ 不能绑定纯数字指令，防止连环跳转～")
                return
            if self._find_handler(cmd_text) is None:
                yield event.plain_result(f"❌ 『{cmd_text}』不是有效指令，先看看『帮助』确认指令名～")
                return
            shortcuts[num] = cmd_text
            db.update_player(group_id, qq_id, shortcuts=shortcuts)
            yield event.plain_result(f"✅ 快捷 {num} → 『{cmd_text}』 绑定成功！以后直接发『{num}』就行✂️")
            return
        if sub == "删除":
            num = rest.split()[0] if rest else ""
            if num and num in shortcuts:
                del shortcuts[num]
                db.update_player(group_id, qq_id, shortcuts=shortcuts)
                yield event.plain_result(f"🗑️ 快捷 {num} 已删除～")
            else:
                yield event.plain_result("❌ 没有这个快捷绑定。『快捷列表』看看～")
            return
        if sub == "清除":
            if not shortcuts:
                yield event.plain_result("还没有任何快捷绑定～")
                return
            db.update_player(group_id, qq_id, shortcuts={})
            yield event.plain_result("🧹 全部快捷已清除～")
            return
        # 默认：列表
        if not shortcuts:
            yield event.plain_result(
                "⚡ 快捷指令：把常用指令绑到数字，一键执行！\n"
                "用法：『快捷绑定 1 探索』→ 之后发『1』就是探索\n"
                "『快捷绑定 2 技能1』→ 发『2』= 技能栏第 1 格\n"
                "支持：快捷列表 / 快捷删除 <数字> / 快捷清除"
            )
            return
        lines = [f"⚡ {qq_id} 的快捷({len(shortcuts)} 个)："]
        for num in sorted(shortcuts.keys(), key=lambda x: int(x) if x.isdigit() else 999):
            lines.append(f"  {num} → {shortcuts[num]}")
        lines.append("『快捷绑定 <数字> <指令>』新增，『快捷删除 <数字>』删除")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?[0－9]\d?$")

    async def shortcut_trigger(self, event: AstrMessageEvent):
        """纯数字消息：查玩家的快捷绑定并转发执行"""
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            return
        shortcuts = player.get("shortcuts") or {}
        num = event.get_message_str().strip()
        num = re.sub(r"^\[At:[^\]]*\]\s*", "", num).strip()
        if num not in shortcuts:
            return
        cmd_text = shortcuts[num]
        async for r in self._run_shortcut(event, cmd_text):
            yield r

    @filter.regex(r"^(?:\[At:\d+\]\s*)?注册(?:\s*|$)")

    async def register(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        _args = self._strip_cmd(event, "注册").split(maxsplit=3)
        first = _args[0] if _args else ""
        rest = _args[1] if len(_args) > 1 else ""
        race_arg = _args[2] if len(_args) > 2 else ""
        gender_arg = _args[3] if len(_args) > 3 else ""
        if self._player(group_id, qq_id):
            yield event.plain_result("你已经注册过角色啦！输入『角色』查看～")
            return
        first = first.strip()
        # v95.23 双格式注册：
        #   旧格式 注册 <职业> <名字> [种族] —— 兼容保留（直接带职业）
        #   新格式 注册 <名字> [种族] —— 见习冒险者，去行会/导师处就职职业
        cls_id = C.resolve("classes", first)
        class_name = first
        name = rest
        if cls_id not in C.CLASSES:
            # 无空格注册兼容：职业名与角色名粘在一起（如"注册战士格温"）
            for cid, cinfo in C.CLASSES.items():
                cn = cinfo.get("name", cid)
                if first.startswith(cn):
                    name = first[len(cn):] + (" " + rest if rest else "")
                    cls_id = cid
                    class_name = cn
                    break
            else:
                # v95.23 新格式：名字 [种族] → 见习冒险者（剩余参数统一在下方解析种族/性别）
                cls_id = C.CLASS_NOVICE
                class_name = ""
                name = first
        if cls_id not in C.CLASSES:
            avail = "、".join(cinfo.get("name", cid) for cid, cinfo in C.CLASSES.items())
            yield event.plain_result(f"未知职业『{class_name}』！可选职业：{avail}")
            return
        # v83 22 章：隐藏职业不可直接注册（需传承解锁）
        if C.CLASSES.get(cls_id, {}).get("hidden"):
            avail = "、".join(cinfo.get("name", cid) for cid, cinfo in C.CLASSES.items())
            yield event.plain_result(
                f"『{class_name}』是传说中才会出现的隐藏职业，普通人无法选择……\n"
                f"💡 世界深处藏着它的线索(隐藏成就/隐藏区域)。可选职业：{avail}"
            )
            return
        # v95.24 性别系统：注册必选性别（男/女），种族从剩余参数中解析。
        #   旧格式 注册 <职业> <名字> [种族] <性别>；新格式 注册 <名字> <性别> [种族]。
        #   种族与性别可任意顺序，种族可省略（默认人类），性别必选（v95.26 强制），
        #   如『注册 格温 女 精灵』『注册 格温 女』『注册 战士 勇者 男』。
        GENDER_MAP = {"男": "male", "male": "male", "♂": "male", "m": "male",
                      "女": "female", "female": "female", "♀": "female", "f": "female"}
        race_id = "human"
        race_display = ""
        gender_id = ""
        _race_done = False
        # 新格式下 rest 可能是种族也可能是性别（如『注册 格温 男』）
        extra = [rest, race_arg, gender_arg] if cls_id == C.CLASS_NOVICE else [race_arg, gender_arg]
        for tok in extra:
            if not tok:
                continue
            if not _race_done:
                r = C.resolve("races", tok)
                if r not in C.RACES:
                    # 简称兼容：输入"精灵"匹配"银月精灵"
                    r = next((rid for rid, ri in C.RACES.items() if tok in ri["name"]), r)
                if r in C.RACES:
                    race_id = r
                    race_display = C.RACES[r]["name"]
                    _race_done = True
                    continue
            g = GENDER_MAP.get(tok.strip().lower())
            if g and not gender_id:
                gender_id = g
                continue
            races_avail = "、".join(ri.get("name", rid) for rid, ri in C.RACES.items())
            yield event.plain_result(
                f"未知种族或性别『{tok}』！可选种族：{races_avail}，性别：男/女\n"
                f"格式：注册 <名字> <性别> [种族]，如『注册 格温 女 精灵』"
            )
            return
        name = name.strip()[:12]
        if not name:
            yield event.plain_result("名字不能为空！格式：注册 <名字> <性别> [种族]，如『注册 格温 女 精灵』")
            return
        # v95.26 性别强制：注册必须选性别（男/女），无性别直接拒
        if not gender_id:
            yield event.plain_result(
                "请选择性别！格式：注册 <名字> <性别> [种族]，如『注册 格温 女 精灵』（男/女）"
            )
            return
        cls = C.CLASSES[cls_id]
        cls_display = cls.get("name", cls_id)
        db.create_player(group_id, qq_id, name, cls_id, cls["base"], cls["base"]["hp"], cls["base"]["mp"], race_id, gender_id)
        # v95 #47：注册送 1 技能点 → Lv.1 有 1 点、Lv.2 有 2 点正好学第一个技能（Lv.1/Lv.2 技能 cost=2），断层消除
        db.update_player(group_id, qq_id, skill_points=1)
        # v86 子区域：新手出生落中心广场
        db.update_player(group_id, qq_id, cur_map=C.START_MAP, cur_subarea=C.START_SUBAREA)
        db.init_stats(group_id, qq_id)
        db.add_portal(qq_id, C.START_MAP)  # v10：新手自动激活橡木镇方碑（v83：原维拉方碑旧地图）
        # v12：自动学会初始技能（职业 Lv.1 技能），后续技能用技能点学习
        sk_table = C.PLAYER_SKILLS.get(cls_id, {}).get("skills", {}) if isinstance(C.PLAYER_SKILLS.get(cls_id), dict) and "skills" in C.PLAYER_SKILLS.get(cls_id) else C.PLAYER_SKILLS.get(cls_id, {})
        init_skills = [s for s, info in sk_table.items() if info["lv"] <= 1]
        if init_skills:
            db.update_player(group_id, qq_id, learned_skills=init_skills)
            # v52 Build：初始技能自动装进技能栏前几格
            bar = list(init_skills[:6])
            while len(bar) < 6:
                bar.append(None)
            db.set_skill_bar(qq_id, bar)
        player = self._player(group_id, qq_id)
        # 阶段九：注册成就（14 章 2.3 冒险者起步）
        C.check_achievements(group_id, qq_id, player)
        init_display = "、".join(C.display("skills", s) for s in init_skills)
        race_line = f"种族：{C.RACES[race_id]['icon']} {C.RACES[race_id]['name']}({C.RACES[race_id]['desc']})\n" if race_id in C.RACES else ""
        gender_line = f"性别：{'♂ 男' if gender_id == 'male' else '♀ 女'}\n" if gender_id else ""
        if cls_id == C.CLASS_NOVICE:
            # v95.23 见习冒险者：无职业技能，引导去行会/导师就职
            yield event.plain_result(
                f"✨ 欢迎来到奥兰迪亚大陆，{name}！\n"
                f"职业：🧭 见习冒险者\n"
                f"{race_line}{gender_line}"
                f"你还没有正式职业，先四处走走、熟悉一下这个世界吧。\n"
                f"━━━━━━━━━━━━\n"
                f"📍 出生点：橡木镇中心广场\n"
                f"　· 输入『找 镇长』接取第一个任务\n"
                f"　· 『地图』查看周边\n"
                f"━━━━━━━━━━━━\n"
                f"🌅 广场中央的【橡木方碑】已为你激活！\n"
                f"　· 『方碑』查看详情\n"
                f"　· 『传送』可前往各地路标\n"
                f"━━━━━━━━━━━━\n"
                f"⚔️ 见习冒险者无法学习职业技能，就职后解锁！\n"
                f"　· 去广场找『行会接待员·小艾』就职职业（战士/法师/游侠/牧师/刺客/武僧）\n"
                f"　· 各城还藏着职业导师，可学进阶技能与转职\n"
                f"━━━━━━━━━━━━\n"
                f"冒险者，你的故事开始了！"
            )
            return
        yield event.plain_result(
            f"✨ 欢迎来到奥兰迪亚大陆，{name}！\n"
            f"职业：{cls['icon']} {cls_display}\n"
            f"{race_line}{gender_line}"
            f"『{cls['desc']}』\n"
            f"━━━━━━━━━━━━\n"
            f"📍 出生点：橡木镇中心广场\n"
            f"　· 输入『找 镇长』接取第一个任务\n"
            f"　· 『地图』查看周边\n"
            f"━━━━━━━━━━━━\n"
            f"🌅 广场中央的【橡木方碑】已为你激活！\n"
            f"　· 『方碑』查看详情\n"
            f"　· 『传送』可前往各地路标\n"
            f"━━━━━━━━━━━━\n"
            f"⚔️ 已学会初始技能：{init_display}\n"
            f"　· 升级获得技能点，『技能学习 <技能名>』学新技能\n"
            f"　· 各城职业导师可学进阶技能，Lv.30/60/90 可转职\n"
            f"━━━━━━━━━━━━\n"
            f"冒险者，你的故事开始了！"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:角色|我的角色)(?:\s*|$)")
    @require_player()

    async def profile(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        cls = C.CLASSES[player["class_name"]]
        # v55.2：属性也统一「总值(+加成)」格式，每项单独一行（与『属性』面板一致）
        st, sources = E.player_stats_detail(
            player["class_name"], player["level"], player["equipment"],
            player.get("class_tier", 0), player.get("attributes"), player.get("evolve_path", 0),
            self._title_bonus(group_id, qq_id), player.get("race"),
        )
        base = next((s["stats"] for s in sources if s["name"] == "基础"), {})
        cur_map = (C.MAP_BY_ID.get(player["cur_map"]) or C.MAP_BY_ID.get(C.START_MAP, {}))
        cur_map = cur_map.get("name", "橡木镇")
        # 装备展示（v33：固定部位顺序，空位显示 —）
        eq_lines = []
        for slot in ["weapon", "helm", "armor", "legs", "boots", "ring", "necklace"]:
            item = player["equipment"].get(slot)
            if item:
                q = C.QUALITY[item["quality"]]
                enh = item.get("enhance", 0)
                enh_str = f" +{enh}" if enh > 0 else ""
                eq_lines.append(f"  {C.EQUIP_SLOTS[slot]}：{q['color']}{item['name']}{enh_str}")
            else:
                eq_lines.append(f"  {C.EQUIP_SLOTS[slot]}：—")
        eq_str = "\n".join(eq_lines) if eq_lines else "  无"
        need = C.exp_to_next(player["level"])
        exp_pct = min(100, int(player["exp"] / need * 100)) if need else 0
        lines = [
            f"⚔️ 【{player['name']}】",
            f"🛡 Lv.{player['level']} {C.display('classes', player['class_name'])}",
            f"🧬 {E.race_name(player.get('race'))}",
        ]
        # v95.24 性别：角色面板显示（存量档未设置则隐藏）
        g = player.get("gender") or ""
        if g:
            lines.append(f"{'♂' if g == 'male' else '♀'} {'男' if g == 'male' else '女'}")
        lines.append("━━━━━━━━━━━━")
        # 阶段九：装备称号显示在角色名前（14 章 3.4）
        eq_title = player.get("equipped_title") or ""
        if eq_title:
            lines[0] = f"⚔️ [{eq_title}] 【{player['name']}】"
        stat_rows = [
            ("❤️", "hp", "max_hp", "生命", f"{player['hp']}/"),
            ("💙", "mp", "max_mp", "魔力", f"{player['mp']}/"),
            ("⚔️", "atk", "atk", "攻击", ""),
            ("🛡️", "def", "def", "防御", ""),
            ("🔥", "matk", "matk", "魔攻", ""),
            ("🧪", "mdef", "mdef", "魔防", ""),
            ("💨", "spd", "spd", "速度", ""),
            ("💥", "crit", "crit", "暴击", ""),
            ("🌀", "dodge", "dodge", "闪避", ""),
        ]
        for icon, skey, fkey, cname, prefix in stat_rows:
            final = st[fkey]
            bonus = final - base.get(skey, 0)
            if skey in C.PCT_STATS:
                lines.append(f"{icon} {cname} {prefix}{int(final*100)}%(+{int(bonus*100)}%)")
            else:
                lines.append(f"{icon} {cname} {prefix}{final}(+{int(bonus)})")
        # 资源块（金币/位置/技能点/EXP 独立成块，每项单独一行）
        lines.append("━━━━━━━━━━━━")
        lines.append(f"💰 金币：{player['gold']}")
        # v94 体力：角色面板显示体力
        lines.append(self._stamina_bar(player))
        lines.append(f"📍 位置：{cur_map}")
        lines.append(f"💡 技能点：{player.get('skill_points', 0)}")
        lines.append(f"✨ EXP：{player['exp']}/{need} ({exp_pct}%)")
        lines.append("━━━━━━━━━━━━")
        lines.append(f"装备：\n{eq_str}")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?排行(?:[\s\S]*)$")

    async def leaderboard(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        raw = self._strip_cmd(event, "排行").strip()
        # v83.1：『排行 副业』→ 副业排行（原『副业 排行』参数保留兼容）
        if "副业" in raw:
            yield event.plain_result(self._prof_rank_text(group_id))
            return
        tops = db.top_players(group_id, 10)
        if not tops:
            yield event.plain_result("还没有人注册角色，快来当第一名！『注册 <名字> <性别>』")
            return
        lines = ["🏆 【奥兰迪亚强者榜】 🏆", "━━━━━━━━━━━━"]
        medals = ["🥇", "🥈", "🥉", "4.", "5.", "6.", "7.", "8.", "9.", "10."]
        for i, p in enumerate(tops):
            lines.append(f"{medals[i]} Lv.{p['level']} {C.CLASSES[p['class_name']]['icon']}{p['name']} ({C.display('classes', p['class_name'])})")
        lines.append("")
        lines.append("💡 『排行 副业』看副业等级榜")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?种族(?:\s*|$)")

    async def races(self, event: AstrMessageEvent):
        """阶段九：种族一览(08 章，注册前查看 6 族天赋)"""
        lines = ["🧬 【种族】6 大种族各有取舍(注册时选择：注册 <名字> <性别> <种族>)", "━━━━━━━━━━━━"]
        for rid, r in C.RACES.items():
            t = r["talents"]
            tnames = r.get("talent_names", {})
            # v98.3：展示格式化全数据化 → core/race_talent_display.py
            from ..core.race_talent_display import format_talent
            parts = []
            for k, v in t.items():
                nm = tnames.get(k, k)
                text = format_talent(k, v, nm)
                if text is not None:
                    parts.append(text)
            lines.append(f"{r['icon']} {r['name']}：{'，'.join(parts)}")
        lines.append("━━━━━━━━━━━━")
        lines.append("💡 种族天赋 = 有得有失，负面已配正面补偿(净强度≈不变)，选取舍不选碾压！")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?转职(?:\s*|$)")
    @require_player()

    async def evolve(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        # v83 22 章：隐藏职业·吟游诗人（『转职 吟游诗人』）
        _raw0 = self._strip_cmd(event, "转职").strip()
        if "吟游诗人" in _raw0 or _raw0 == "诗人":
            async for r in self._evolve_bard(event, group_id, qq_id, player):
                yield r
            return
        # v87 09 章九：隐藏职业·魔剑士（『转职 魔剑士』）
        if "魔剑士" in _raw0 or _raw0 == "剑士":
            async for r in self._evolve_spellblade(event, group_id, qq_id, player):
                yield r
            return
        cls = C.CLASSES[player["class_name"]]
        tier = player.get("class_tier", 0)
        # 转职等级门槛：tier 1→30级 / tier 2→60级 / tier 3→90级（21 章三转体系）
        next_tier = tier + 1
        need_lv = C.EVOLVE_LEVELS.get(next_tier)
        branches = cls.get("evolve_branches", {}).get(next_tier, [])
        # 已满级转职
        if not need_lv:
            yield event.plain_result(
                f"👑 你已完成全部转职！{self._tier_title(player['class_name'], tier, player.get('evolve_path', 0))}\n"
                f"当前职业：{cls['icon']} {self._branch_title(player['class_name'], tier, player.get('evolve_path', 0))}(Lv.{player['level']})"
            )
            return
        # 等级不足
        if player["level"] < need_lv:
            line = f"{cls['icon']}{C.display('classes', player['class_name'])}"
            evo_lines = []
            for t, branch_list in cls.get("evolve_branches", {}).items():
                lv = C.EVOLVE_LEVELS[t]
                tagged = []
                for i, b in enumerate(branch_list):
                    tag = "攻" if i == 0 else "守"
                    tagged.append(f"{b}({tag})")
                evo_lines.append(f"Lv.{lv} → {' / '.join(tagged)}")
            yield event.plain_result(
                f"{line} 的进化之路：\n"
                f"━━━━━━━━━━━━\n"
                f"{chr(10).join(evo_lines)}\n\n"
                f"🔒 达到 {need_lv} 级可转职，当前 Lv.{player['level']}，继续加油！"
            )
            return
        # 可以转职：v95.23 改为找职业导师 NPC 转职（不再直接指令转职）
        tutor_map = {
            "cls_zhan_shi": ("老兵·格里姆", "白鹿城·白鹿广场"),
            "cls_fa_shi": ("大法师·艾德琳", "白鹿城·白鹿广场"),
            "cls_mu_shi": ("圣殿执事·莉亚", "白鹿城·白鹿广场"),
            "cls_you_xia": ("猎手·柯恩", "铁港城·港口广场"),
            "cls_ci_ke": ("暗影渡鸦", "铁港城·港口广场"),
            "cls_wu_seng": ("船帮武师·老陈", "铁港城·港口广场"),
        }
        tname, tloc = tutor_map.get(player["class_name"], ("职业导师", "对应城市"))
        branch_names = " / ".join(branches) if branches else "对应分支"
        yield event.plain_result(
            f"🌟 {cls['icon']}{C.display('classes', player['class_name'])} 达到了 {need_lv} 级，可以转职！\n"
            f"━━━━━━━━━━━━\n"
            f"🔀 可选路线：{branch_names}\n\n"
            f"🧭 去 {tloc} 找 {tname}，由导师为你举行转职仪式吧！\n"
            f"(『找 {tname}』→ 对话选择转职路线)"
        )
        return

    def _branch_title(self, class_name: str, tier: int, evolve_path: int = 0) -> str:
        """分支称号：优先返回所选分支的名字，否则默认第一条"""
        cls = C.CLASSES.get(class_name, {})
        branches = cls.get("evolve_branches", {})
        if tier > 0 and tier in branches and branches[tier]:
            idx = 0 if evolve_path in (0, 1) else 1
            lst = branches[tier]
            if 0 <= idx < len(lst):
                return lst[idx]
        evolve = cls.get("evolve", [])
        if tier - 1 < len(evolve):
            return evolve[tier - 1].split("(")[0]
        return C.display("classes", class_name) if isinstance(class_name, str) else class_name

    async def _evolve_bard(self, event, group_id, qq_id, player):
        """v83 22 章：隐藏职业·吟游诗人传承转职(30 级 + 已解锁 + 非诗人)"""
        unlocks = player.get("hidden_class_unlock", [])
        if "cls_bard" not in unlocks:
            yield event.plain_result(
                "🎻 吟游诗人的传承还未向你敞开……\n"
                "💡 线索：听完 3 位诗人的全部歌谣(成就「史诗聆听者」)，再到精灵歌剧院寻找传承。"
            )
            return
        if player["level"] < 30:
            yield event.plain_result(
                f"🎻 传承需要 30 级历练，当前 Lv.{player['level']}，先游历四方吧。")
            return
        if player["class_name"] == "cls_bard":
            yield event.plain_result("🎻 你已是吟游诗人了。")
            return
        cls = C.CLASSES["cls_bard"]
        sk_table = C.PLAYER_SKILLS.get("cls_bard", {}).get("skills", {})
        init_skills = [s for s, info in sk_table.items() if info["lv"] <= 1]
        st = E.player_final_stats(
            "cls_bard", player["level"], player.get("equipment", {}), 0,
            player.get("attributes"), 0,
            self._title_bonus(group_id, qq_id), player.get("race"))
        db.update_player(group_id, qq_id,
                         class_name="cls_bard", class_tier=0, evolve_path=0,
                         max_hp=st["hp"], max_mp=st["mp"], hp=st["hp"], mp=st["mp"],
                         learned_skills=init_skills)
        player = self._player(group_id, qq_id)
        C.check_achievements(group_id, qq_id, player)
        yield event.plain_result(
            f"🎻 传承完成！你成为了【{cls['icon']}吟游诗人】！\n"
            f"━━━━━━━━━━━━\n"
            f"琴弦轻拨，古老的歌谣在血脉中苏醒……\n"
            f"🌟 领悟：{'、'.join(C.display('skills', sk) for sk in init_skills)}\n"
            f"💡 你的歌声将成为队伍的力量(辅助定位，副本中尤为闪耀)！"
        )
        return

    async def _evolve_spellblade(self, event, group_id, qq_id, player):
        """v87 09 章九：隐藏职业·魔剑士传承转职(60 级 + 已解锁 + 非魔剑士)"""
        unlocks = player.get("hidden_class_unlock", [])
        if "cls_spellblade" not in unlocks:
            yield event.plain_result(
                "⚔️ 魔剑士的传承还未向你敞开……\n"
                "💡 线索：击败符文魔像收集符文碎片，集齐 3 张泛黄书页进入 H6 失落图书馆，找魔剑士残魂接受试炼「剑与书的誓约」。"
            )
            return
        if player["level"] < 60:
            yield event.plain_result(
                f"⚔️ 传承需要 60 级历练，当前 Lv.{player['level']}，先锤炼剑术与魔法吧。")
            return
        if player["class_name"] == "cls_spellblade":
            yield event.plain_result("⚔️ 你已是魔剑士了。")
            return
        cls = C.CLASSES["cls_spellblade"]
        sk_table = C.PLAYER_SKILLS.get("cls_spellblade", {}).get("skills", {})
        init_skills = [s for s, info in sk_table.items() if info["lv"] <= 60]
        st = E.player_final_stats(
            "cls_spellblade", player["level"], player.get("equipment", {}), 0,
            player.get("attributes"), 0,
            self._title_bonus(group_id, qq_id), player.get("race"))
        db.update_player(group_id, qq_id,
                         class_name="cls_spellblade", class_tier=0, evolve_path=0,
                         max_hp=st["hp"], max_mp=st["mp"], hp=st["hp"], mp=st["mp"],
                         learned_skills=init_skills)
        player = self._player(group_id, qq_id)
        C.check_achievements(group_id, qq_id, player)
        yield event.plain_result(
            f"⚔️ 传承完成！你成为了【{cls['icon']}魔剑士】！\n"
            f"━━━━━━━━━━━━\n"
            f"剑与书在血脉中共鸣，尘封的魔能重新流转……\n"
            f"🌟 领悟：{'、'.join(C.display('skills', sk) for sk in init_skills)}\n"
            f"💡 魔能斩命中叠魔能，符文刻印每回合充能——叠层→爆发，打出你的节奏！"
        )
        return

    def _evolve_auto_skills(self, player: dict, next_tier: int) -> list:
        """转职自动获得的技能(二转被动 60 级 / 三转奥义 90 级)"""
        if next_tier not in (2, 3):
            return []
        cls = player.get("class_name", "")
        path = player.get("evolve_path", 0)
        branches = C.BRANCH_SKILLS.get(cls, {}).get("branches", {})
        tier_branches = branches.get(next_tier, {})
        names = list(tier_branches.keys())
        if not names:
            return []
        idx = 0 if path == 1 else 1
        if idx >= len(names):
            return []
        target_lv = 60 if next_tier == 2 else 90
        out = []
        for sname, sinfo in tier_branches[names[idx]].items():
            if sinfo.get("lv") == target_lv:
                out.append(sinfo.get("name", sname))
        return out

    def _tier_title(self, class_name: str, tier: int, evolve_path: int = 0) -> str:
        """职业进阶称号(v25：按分支返回)"""
        return f"{C.CLASSES.get(class_name, {}).get('icon', '')} {self._branch_title(class_name, tier, evolve_path)}"

    @filter.regex(r"^(?:\[At:\d+\]\s*)?属性(?:\s*|$)")
    @require_player()

    async def attributes(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        # v55.2：每个属性单独一行，格式「总值(+加成)」——加成为基础以外全部来源之和
        st, sources = E.player_stats_detail(
            player["class_name"], player["level"], player["equipment"],
            player.get("class_tier", 0), player.get("attributes"), player.get("evolve_path", 0),
            self._title_bonus(group_id, qq_id), player.get("race"),
        )
        base = next((s["stats"] for s in sources if s["name"] == "基础"), {})
        attr = player.get("attributes", {})
        lines = [
            f"📊 【{player['name']} 属性面板】 Lv.{player['level']}",
            "━━━━━━━━━━━━",
        ]
        stat_rows = [
            ("❤️", "hp", "max_hp", "生命"),
            ("💙", "mp", "max_mp", "魔力"),
            ("⚔️", "atk", "atk", "攻击"),
            ("🛡️", "def", "def", "防御"),
            ("🔮", "matk", "matk", "魔攻"),
            ("✨", "mdef", "mdef", "魔防"),
            ("💨", "spd", "spd", "速度"),
            ("💥", "crit", "crit", "暴击"),
            ("🌀", "dodge", "dodge", "闪避"),
        ]
        for icon, skey, fkey, cname in stat_rows:
            final = st[fkey]
            bonus = final - base.get(skey, 0)
            if skey in C.PCT_STATS:
                lines.append(f"{icon} {cname} {int(final*100)}%(+{int(bonus*100)}%)")
            else:
                lines.append(f"{icon} {cname} {final}(+{int(bonus)})")
        lines.append("━━━━━━━━━━━━")
        lines.append(f"🎯 自由属性点：{player.get('attr_pts', 0)}")
        # 加点分配（每项单独一行）
        lines.append(f"💪 力量 {attr.get('str', 0)}(每点＋1.2 攻击)")
        lines.append(f"🏃 敏捷 {attr.get('agi', 0)}(每点＋0.8 速度 ＋ 0.4% 暴击)")
        lines.append(f"🧠 智力 {attr.get('int', 0)}(每点＋1.2 魔攻 ＋ 1.5 魔力)")
        lines.append(f"❤️‍🩹 耐力 {attr.get('vit', 0)}(每点＋8 生命)")
        lines.append("━━━━━━━━━━━━")
        lines.append("💡 『加点 力量 <点数>』分配属性点，『洗点』重置(500金币)")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?加点(?:\s*|$)")
    @require_player()

    async def add_attr(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        args = self._strip_cmd(event, "加点").split()
        if len(args) < 2 or not args[1].isdigit():
            yield event.plain_result("格式：加点 <力量/敏捷/智力/耐力> <点数>，如『加点 力量 5』")
            return
        key_map = {"力量": "str", "敏捷": "agi", "智力": "int", "耐力": "vit"}
        key = key_map.get(args[0])
        if not key:
            yield event.plain_result("可选：力量 / 敏捷 / 智力 / 耐力")
            return
        n = int(args[1])
        if n <= 0:
            yield event.plain_result("点数必须是正整数！")
            return
        pts = player.get("attr_pts", 0)
        if n > pts:
            yield event.plain_result(f"属性点不足！你只有 {pts} 点，需要 {n} 点。")
            return
        attr = dict(player.get("attributes", {}))
        attr[key] = attr.get(key, 0) + n
        import json
        db.update_player(group_id, qq_id, attr_pts=pts - n, attributes=json.dumps(attr, ensure_ascii=False))
        names = {"str": "力量", "agi": "敏捷", "int": "智力", "vit": "耐力"}
        yield event.plain_result(f"✅ 加点成功！{names[key]} +{n}，剩余属性点 {pts - n}\n『属性』查看效果～")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?技能洗点(?:\s*|$)")
    @require_player()

    async def reset_skill(self, event: AstrMessageEvent):
        """技能洗点(v27 独立指令)：花 500 金币返还全部已花费技能点(学习+升级)，清空已学技能与等级"""
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player.get("learned_skills"):
            yield event.plain_result("你还没有学习过任何技能，无需洗点～")
            return
        cost = C.RESET_SKILL_COST
        if player["gold"] < cost:
            yield event.plain_result(f"技能洗点需要 {cost} 金币，你只有 {player['gold']} 金币。")
            return
        spent = player.get("skill_spent", 0)
        cls = player["class_name"]
        init_skills = [C.display("skills", s) for s, info in E._sk_table(cls).items() if info["lv"] <= 1]
        db.update_player(group_id, qq_id, gold=player["gold"] - cost,
                         skill_points=player.get("skill_points", 0) + spent,
                         skill_spent=0,
                         learned_skills=init_skills,
                         skill_levels={})
        # v52 Build：洗点后技能栏重置为初始技能
        bar = list(init_skills[:6])
        while len(bar) < 6:
            bar.append(None)
        db.set_skill_bar(qq_id, bar)
        yield event.plain_result(
            f"🔄 技能洗点成功！返还 {spent} 技能点(花费 {cost} 金币)\n"
            f"已学技能清空(保留初始技能：{'、'.join(init_skills) or '无'})，技能等级已重置，『技能学习』重新规划 build 吧～"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?转职重置(?:[\s\S]*)$")
    @require_player()

    async def evolve_reset(self, event: AstrMessageEvent):
        """转职重置(21 章 §8)：付费清空转职分支，保留等级，可重新选择分支"""
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        tier = player.get("class_tier", 0)
        if tier <= 0:
            yield event.plain_result("你还没有转职过，无需重置～『转职』查看路线。")
            return
        cost = C.EVOLVE_FEES.get(tier, 500)
        if player["gold"] < cost:
            yield event.plain_result(f"转职重置需要 {cost} 金币(当前 {tier} 转)，你只有 {player['gold']} 金币。")
            return
        # 清除分支技能（learned_skills 中属于分支的）+ 分支技能等级
        cls = player["class_name"]
        learned = list(player.get("learned_skills", []))
        keep = []
        removed = []
        for s in learned:
            if E.branch_skill_owner(cls, s):
                removed.append(s)
            else:
                keep.append(s)
        slv = dict(player.get("skill_levels", {}) or {})
        for s in removed:
            slv.pop(s, None)
        db.update_player(group_id, qq_id,
                         gold=player["gold"] - cost,
                         class_tier=0,
                         evolve_path=0,
                         learned_skills=keep,
                         skill_levels=slv)
        # 技能栏清除被移除的分支技能
        try:
            bar = db.get_skill_bar(qq_id) or []
            nbar = [b if (b is None or b in keep) else None for b in bar]
            db.set_skill_bar(qq_id, nbar)
        except Exception:
            pass
        old_title = self._tier_title(cls, tier, player.get("evolve_path", 0))
        yield event.plain_result(
            f"🔄 转职重置成功！(花费 {cost} 金币)\n"
            f"━━━━━━━━━━━━\n"
            f"{old_title} → 回到基础职业\n"
            f"✨ 等级与基础技能保留，分支技能已清除({'、'.join(removed) or '无'})\n"
            f"💡 到 30/60/90 级可重新『转职』选择新分支！"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?洗点(?:\s*|$)")
    @require_player()

    async def reset_attr(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        raw = self._strip_cmd(event, "洗点").strip()
        player = self._player(group_id, qq_id)
        # v27：技能洗点已拆分为独立指令『技能洗点』，避免与属性洗点混淆
        if "技能" in raw:
            yield event.plain_result("技能洗点是独立指令：『技能洗点』(500金币返还技能点)～『洗点』只重置属性点。")
            return
        attr = player.get("attributes", {})
        used = sum(attr.values())
        if used == 0:
            yield event.plain_result("你还没有分配过属性点，无需洗点～")
            return
        cost = C.RESET_SKILL_COST
        if player["gold"] < cost:
            yield event.plain_result(f"洗点需要 {cost} 金币，你只有 {player['gold']} 金币。")
            return
        import json
        db.update_player(group_id, qq_id, gold=player["gold"] - cost,
                         attr_pts=player.get("attr_pts", 0) + used,
                         attributes=json.dumps({"str": 0, "agi": 0, "int": 0, "vit": 0}, ensure_ascii=False))
        yield event.plain_result(f"🔄 洗点成功！返还 {used} 点属性点(花费 {cost} 金币)\n『加点』重新分配～")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?战力(?:\s*|$)")
    @require_player()

    async def power(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        st = E.player_final_stats(player["class_name"], player["level"], player["equipment"], player.get("class_tier", 0), player.get("attributes"), player.get("evolve_path", 0), self._title_bonus(group_id, qq_id), player.get("race"))
        pw = int(st["atk"] * 2 + st["matk"] * 2 + st["def"] * 1.5 + st["mdef"] * 1.5
                + st["max_hp"] / 10 + st["max_mp"] / 10 + st["spd"] * 3)
        tier = player.get("class_tier", 0)
        title = self._tier_title(player["class_name"], tier)
        yield event.plain_result(
            f"⚡ 【战力】{player['name']}({title} Lv.{player['level']})\n"
            f"战斗力：{pw:,}\n"
            f"━━━━━━━━━━━━\n"
            f"❤️ {st['max_hp']} ｜ ⚔️ {st['atk']} ｜ 🔮 {st['matk']} ｜ 🛡️ {st['def']} ｜ 💨 {st['spd']}\n"
            f"💡 升级、装备、转职、加点都能提升战力！"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?技能详情(?:[\s\S]*)$")
    @require_player()

    async def skill_detail(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        skill_name = self._strip_cmd(event, "技能详情").strip()
        if not skill_name:
            yield event.plain_result("格式：技能详情 <技能名/序号>，如『技能详情 火球术』或『技能详情 5』")
            return
        # 序号查看：『技能详情 5』→ 技能列表第 5 个技能
        if skill_name.isdigit():
            skills = self._player_skill_table(player)
            skill_items = list(skills.keys())
            idx = int(skill_name)
            if idx < 1 or idx > len(skill_items):
                yield event.plain_result(f"你的职业只有 {len(skill_items)} 个技能！『技能列表』查看全部～")
                return
            skill_name = skill_items[idx - 1]
        info = E.skill_info(player["class_name"], skill_name)
        if not info:
            yield event.plain_result(f"你的职业没有『{skill_name}』技能！『技能列表』查看全部～")
            return
        # v56.1：显示一律用中文名（info 里带 name，序号查询进来的是 sk_xxx ID）
        display_name = info.get("name", skill_name)
        learned = player.get("learned_skills", [])
        is_learned = E.is_skill_learned(player["class_name"], player["level"], skill_name, learned)
        mx = E.skill_max_level(info)
        if is_learned:
            slv = E.skill_level_of(player, skill_name)  # #259：兼容 skill_levels key 为中文名
            status = f"✅ 已学会 Lv.{slv}/{mx}"
        elif info["lv"] <= player["level"]:
            status = f"📖 可学习(Lv.{info['lv']})"
        else:
            status = f"🔒 未学会(Lv.{info['lv']} 解锁)"
        lines = [
            f"📜 【{display_name}】｜{status}",
            f"━━━━━━━━━━━━",
            f"类型：{info.get('kind','')} ｜ 需求等级：Lv.{info['lv']} ｜ 消耗：{info['mp']} 魔力",
            f"效果：{info['desc']}",
        ]
        owner = E.branch_skill_owner(player["class_name"], skill_name)
        if owner:
            lines.append(f"专属：{owner[1]}(Lv.{C.EVOLVE_LEVELS[owner[0]]} 转职解锁)")
        if info.get("multi"):
            lines.append(f"连击：x{info['multi']}")
        if info.get("pierce"):
            lines.append("特性：无视防御")
        if info.get("effect"):
            lines.append(f"特效：{info['effect']}")
        if info.get("team"):
            team_cn = {"heal_all": "治疗全队", "def_all": "防御全队", "reduce_all": "减伤全队",
                       "shield_all": "护盾全队", "matk_all": "魔攻全队", "crit_all": "暴击全队",
                       "spd_all": "速度全队", "poison_all": "毒伤全队", "taunt": "嘲讽"}
            lines.append(f"团队：{team_cn.get(info['team'], info['team'])}(副本中广播全队)")
        if info.get("cond"):
            cond = info["cond"]
            ctype = cond.get("type")
            mult = cond.get("mult", 1.0)
            label = cond.get("label", "")
            # v101.2：条件显示文案数据化 → battle_conds.py COND_LABELS（加条件类型只改注册表一处）
            from ..core.battle_conds import COND_LABELS
            label_fn = COND_LABELS.get(ctype)
            ctext = label_fn(cond) if label_fn else ctype
            lines.append(f"⚔️ 条件转化：{ctext}时激活『{label}』(威力 ×{mult})")
        if not is_learned and info["lv"] <= player["level"]:
            cost = E.skill_learn_cost_for(player, info["lv"])
            lines.append(f"💡 『技能学习 {display_name}』消耗 {cost} 技能点学会(当前 {player.get('skill_points',0)} 点)")
        elif is_learned:
            slv = E.skill_level_of(player, skill_name)  # #259：兼容 skill_levels key 为中文名
            if slv < mx:
                cost = E.skill_upgrade_cost(slv, info)
                nxt = " · ".join(self._skill_upgrade_gains(info, slv + 1))
                lines.append(f"💡 『技能升级 {display_name}』花 {cost} 点升到 Lv.{slv + 1}({nxt}，当前 {player.get('skill_points',0)} 点)")
            else:
                lines.append("✨ 已满级！")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?技能学习(?:[\s\S]*)$")
    @require_player()

    async def skill_learn(self, event: AstrMessageEvent):
        """技能学习(v12)：等级门槛 + 消耗技能点学会，学会永久可用"""
        group_id, qq_id = self._uid(event)
        skill_name = self._strip_cmd(event, "技能学习")
        player = self._player(group_id, qq_id)
        yield event.plain_result(self._skill_learn_msg(group_id, player, skill_name))

    def _skill_learn_msg(self, group_id, player: dict, skill_name: str) -> str:
        """技能学习核心逻辑(v12：等级门槛 + 技能点学会，学会永久可用)"""
        skill_name = (skill_name or "").strip()
        # v95.23 见习冒险者：无职业技能，先就职
        if player.get("class_name") == C.CLASS_NOVICE:
            return "🧭 见习冒险者还没有职业技能！去广场找『行会接待员·小艾』就职后就能学习技能了～"
        if not skill_name:
            return "格式：技能学习 <技能名/序号>，如『技能学习 裂空斩』或『技能学习 3』"
        # 序号学习：『技能学习 3』→ 技能列表第 3 个技能（与『技能详情』一致）
        if skill_name.isdigit():
            skills = self._player_skill_table(player)
            skill_items = list(skills.keys())
            idx = int(skill_name)
            if idx < 1 or idx > len(skill_items):
                return f"你的职业只有 {len(skill_items)} 个技能！『技能列表』查看全部～"
            skill_name = skill_items[idx - 1]
        info = E.skill_info(player["class_name"], skill_name)
        if not info:
            return f"你的职业没有『{skill_name}』技能！『技能列表』查看全部～"
        # v56.1：显示一律用中文名（序号学习进来的是 sk_xxx ID）
        display_name = info.get("name", skill_name)
        learned = player.get("learned_skills", [])
        if E.is_skill_learned(player["class_name"], player["level"], skill_name, learned):
            return f"『{display_name}』你已学会了，去战斗里试试吧～"
        # v26 分支专属技能门槛：必须先转职到对应分支
        owner = E.branch_skill_owner(player["class_name"], skill_name)
        if owner:
            need_tier, bname = owner
            my_tier = player.get("class_tier", 0)
            my_path = player.get("evolve_path", 0)
            if my_tier < need_tier or not my_path:
                return f"『{display_name}』是 {bname} 的专属技能，需要先转职为 {bname} 才能学习！(Lv.30/60/90 可转职)"
            branches = C.CLASSES[player["class_name"]].get("evolve_branches", {}).get(need_tier, [])
            idx = 0 if my_path == 1 else 1
            my_branch = branches[idx] if idx < len(branches) else ""
            if my_branch != bname:
                return f"『{display_name}』是 {bname} 的专属技能，你走的是 {my_branch} 路线，学不了～"
        need_lv = info["lv"]
        if player["level"] < need_lv:
            return f"『{display_name}』需要 Lv.{need_lv} 才能学习，你才 Lv.{player['level']}——升级吧！(每级＋1 技能点)"
        cost = E.skill_learn_cost_for(player, need_lv)
        pts = player.get("skill_points", 0)
        if pts < cost:
            return (
                f"学习『{display_name}』需要 {cost} 技能点(技能 Lv.{need_lv})，你只有 {pts} 点——升级可获得技能点(每级＋1)～"
            )
        learned = list(learned) + [skill_name]
        spent = player.get("skill_spent", 0) + cost
        db.update_player(group_id, player["qq_id"], skill_points=pts - cost, learned_skills=learned, skill_spent=spent)
        # 阶段九：学习技能成就判定
        C.check_achievements(group_id, player["qq_id"], player)
        if info.get("kind") == "被动":
            return (
                f"✨ 消耗 {cost} 技能点，学会了被动技能『{display_name}』！\n"
                f"⚙️ 被动技能无需施放，战斗自动生效！剩余技能点 {pts - cost}\n"
                f"「{info['desc']}」"
            )
        return (
            f"✨ 消耗 {cost} 技能点，学会了『{display_name}』！\n"
            f"现在 Lv.{player['level']} 就能使用它了，剩余技能点 {pts - cost}\n"
            f"💡 记得『设置技能 <槽位> {display_name}』放入技能栏，战斗中『技能 <槽位>』即可施放～"
        )

    def _skill_upgrade_gains(self, info: dict, lv: int) -> list:
        """技能升级多维成长描述(v56.1)：按技能单独策划的成长配置列出各维度提升"""
        parts = []
        kind = info.get("kind", "")
        if info.get("power"):
            label = "治疗" if kind == "治疗" else "伤害"
            parts.append(f"{label} {int(E.skill_power_mult(lv, info) * 100)}%")
        if kind in ("增益", "嘲讽"):
            parts.append(f"持续 {E.skill_buff_turns(lv)} 回合")
        if info.get("cond"):
            parts.append(f"条件 ×{E.skill_cond_mult(info['cond'], lv, info):g}")
        if info.get("mech_val"):
            parts.append(f"叠层 {E.skill_mech_val(info, lv)}")
        if info.get("effect") == "lifesteal":
            parts.append(f"吸血 {int(E.skill_lifesteal_pct(info, lv) * 100)}%")
        return parts

    @filter.regex(r"^(?:\[At:\d+\]\s*)?技能升级(?:[\s\S]*)$")
    @require_player()

    async def skill_upgrade(self, event: AstrMessageEvent):
        """技能升级(v27)：已学技能花技能点升级，攻击/治疗 power 提升、增益回合延长"""
        group_id, qq_id = self._uid(event)
        skill_name = self._strip_cmd(event, "技能升级").strip()
        player = self._player(group_id, qq_id)
        if not skill_name:
            yield event.plain_result("格式：技能升级 <技能名/序号>，如『技能升级 火球术』或『技能升级 3』")
            return
        # 序号升级：『技能升级 3』→ 技能列表第 3 个技能（与『技能详情/学习』一致）
        if skill_name.isdigit():
            skills = self._player_skill_table(player)
            skill_items = list(skills.keys())
            idx = int(skill_name)
            if idx < 1 or idx > len(skill_items):
                yield event.plain_result(f"你的职业只有 {len(skill_items)} 个技能！『技能列表』查看全部～")
                return
            skill_name = skill_items[idx - 1]
        info = E.skill_info(player["class_name"], skill_name)
        if not info:
            yield event.plain_result(f"你的职业没有『{skill_name}』技能！『技能列表』查看全部～")
            return
        learned = player.get("learned_skills", [])
        if not E.is_skill_learned(player["class_name"], player["level"], skill_name, learned):
            yield event.plain_result(f"『{skill_name}』还没学会！先『技能学习 {skill_name}』学会后才能升级～")
            return
        # v64 被动技能：不可升级（learned 后即满效果）
        if info.get("kind") == "被动":
            yield event.plain_result(
                f"⚙️ 『{info.get('name', skill_name)}』是被动技能，无需升级——学会后战斗自动生效！"
            )
            return
        levels = dict(player.get("skill_levels") or {})
        cur_lv = E.skill_level_of(player, skill_name)  # #259：兼容 key 为中文名，升级判定/写入统一
        mx = E.skill_max_level(info)
        if cur_lv >= mx:
            yield event.plain_result(f"『{skill_name}』已经是满级 Lv.{mx} 啦，不能再升了～")
            return
        cost = E.skill_upgrade_cost(cur_lv, info)
        pts = player.get("skill_points", 0)
        if pts < cost:
            yield event.plain_result(
                f"升级『{skill_name}』到 Lv.{cur_lv + 1} 需要 {cost} 技能点，你只有 {pts} 点——升级可获得技能点(每级＋1)～"
            )
            return
        levels[C.resolve("skills", skill_name)] = cur_lv + 1  # #259：key 统一 ID（写库 resolve 幂等，防中文/ID 双 key）
        spent = player.get("skill_spent", 0) + cost
        db.update_player(group_id, player["qq_id"], skill_points=pts - cost,
                         skill_levels=levels, skill_spent=spent)
        display_name = info.get("name", skill_name)
        gains = self._skill_upgrade_gains(info, cur_lv + 1)
        desc = " · ".join(gains)
        next_cost = E.skill_upgrade_cost(cur_lv + 1, info)
        tail = f"｜ 升到 Lv.{cur_lv + 2} 需 {next_cost} 点" if next_cost else "｜ 已满级！"
        yield event.plain_result(
            f"⬆️ 『{display_name}』升级到 Lv.{cur_lv + 1}({desc})！消耗 {cost} 技能点，剩余 {pts - cost} 点{tail}"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?技能栏(?:\s*|$)")
    @require_player()

    async def skill_bar_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        bar = db.get_skill_bar(qq_id)
        lines = ["🎛️ 【技能栏】(战斗中『技能 <槽位>』快捷施放)", "━━━━━━━━━━━━"]
        for i in range(6):
            sname = bar[i] if i < len(bar) else None
            if sname:
                info = E.skill_info(player["class_name"], sname)
                kind = info.get("kind", "") if info else ""
                lines.append(f" {i+1}. {C.display('skills', sname)}({kind})")
            else:
                lines.append(f" {i+1}. (空)")
        lines.append("━━━━━━━━━━━━")
        lines.append("💡 『设置技能 <槽位> <技能名>』配置，如：设置技能 1 火球术(须先学会)")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?设置技能(?:\s*|$)")
    @require_player()

    async def skill_bar_set(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        raw = self._strip_cmd(event, "设置技能").strip()
        player = self._player(group_id, qq_id)
        parts = raw.split(maxsplit=1)
        if len(parts) < 2 or not parts[0].isdigit():
            yield event.plain_result("格式：设置技能 <槽位1－6> <技能名>，如『设置技能 1 火球术』")
            return
        slot = int(parts[0])
        if slot < 1 or slot > 6:
            yield event.plain_result("技能栏只有 6 个槽位(1~6)！")
            return
        sname = parts[1].strip()
        info = E.skill_info(player["class_name"], sname)
        if not info:
            yield event.plain_result(f"你的职业没有『{sname}』技能！『技能列表』查看～")
            return
        if not E.is_skill_learned(player["class_name"], player["level"], sname, player.get("learned_skills", [])):
            yield event.plain_result(f"『{sname}』还没学会！『技能学习 {sname}』消耗技能点学会后再设置～")
            return
        bar = db.get_skill_bar(qq_id)
        while len(bar) < 6:
            bar.append(None)
        bar[slot - 1] = sname
        db.set_skill_bar(qq_id, bar)
        yield event.plain_result(f"✅ 技能栏 {slot} 号位 → 『{sname}』！战斗中『技能 {slot}』即可施放～")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?流派(?:[\s\S]*)$")
    @require_player()

    async def build_view(self, event: AstrMessageEvent):
        """流派(v52 Build 系统)：查看本职业流派 / 一键配置技能栏"""
        group_id, qq_id = self._uid(event)
        raw = self._strip_cmd(event, "流派").strip()
        player = self._player(group_id, qq_id)
        cid = player["class_name"]
        builds = C.BUILDS.get(cid, {})
        if not builds:
            yield event.plain_result("你的职业暂时没有流派方案～")
            return
        # 无参 → 流派列表
        if not raw:
            lines = [f"⚔️ 【{C.display('classes', cid)}流派】—— 同一职业，不同打法！", "━━━━━━━━━━━━"]
            for name, info in builds.items():
                learned_cnt = sum(1 for s in info["skills"] if E.is_skill_learned(cid, player["level"], s, player.get("learned_skills", [])))
                lines.append(f"{info.get('icon','')} {name}(已学 {learned_cnt}/6)")
                lines.append(f"    {info['desc']}")
            lines.append("━━━━━━━━━━━━")
            lines.append("💡 『流派 <名称>』一键配置技能栏，如『流派 狂暴流』")
            yield event.plain_result("\n".join(lines))
            return
        # 配置指定流派
        name = raw
        if name not in builds:
            yield event.plain_result(f"没有『{name}』流派！你的流派：{'、'.join(builds.keys())}")
            return
        info = builds[name]
        bar = []
        missing = []
        for sname in info["skills"]:
            if E.is_skill_learned(cid, player["level"], sname, player.get("learned_skills", [])):
                bar.append(sname)
            else:
                need = E.skill_info(cid, sname)
                need_lv = need["lv"] if need else 0
                missing.append(f"『{sname}』(Lv.{need_lv})")
        while len(bar) < 6:
            bar.append(None)
        db.set_skill_bar(qq_id, bar)
        lines = [f"✅ 已切换为【{info.get('icon','')} {name}】流派！技能栏已配置："]
        for i, sname in enumerate(info["skills"], 1):
            if sname in bar:
                lines.append(f"  {i}. ⚔️ {sname}")
            else:
                lines.append(f"  {i}. 🔒 {sname}(未学会)")
        if missing:
            lines.append(f"⚠️ 还没学会：{'、'.join(missing)}——『技能学习 <名称>』学会后重新『流派 {name}』即可补上")
        lines.append(f"💡 打法：{info['desc']}")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?注销(?:[\s\S]*)$")
    @require_player()

    async def delete_account(self, event: AstrMessageEvent):
        """注销角色：删除全部数据，可重新注册（v62 群友想切职业）。

        两步确认防误删：『注销』→ 提示确认；10 分钟内『注销 确认』才真正删除。
        确认状态存 event_state（key: del_confirm_<qq_id>），过期自动失效。
        """
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        arg = self._strip_cmd(event, "注销").strip()
        # 『注销 确认』：执行删除（10 分钟内有效）
        if arg == "确认":
            key = f"del_confirm_{qq_id}"
            state = db.get_event_state(key)
            if not state:
                yield event.plain_result("没有待确认的注销请求。输入『注销』发起注销～")
                return
            try:
                if int(time.time()) - int(state) > 600:
                    db.delete_event_state(key)
                    yield event.plain_result("注销确认已过期，请重新输入『注销』发起～")
                    return
            except (TypeError, ValueError):
                pass
            db.delete_player(qq_id)
            db.delete_event_state(key)
            yield event.plain_result(
                f"🗡️ 冒险者 {player['name']} 的故事就此落幕……\n"
                f"所有角色数据已删除，可以重新『注册 <名字> <性别>』开始新旅程！"
            )
            return
        # 发起注销：写确认状态（10 分钟有效）
        db.set_event_state(f"del_confirm_{qq_id}", int(time.time()))
        yield event.plain_result(
            f"⚠️ 真的要注销角色【{player['name']}】吗？\n"
            f"删除后将失去：等级/装备/背包/金币/技能/副业/宠物/公会 全部数据！\n"
            f"━━━━━━━━━━━━\n"
            f"确认请回复：『注销 确认』(10 分钟内有效)\n"
            f"想切职业也可以直接注销后重新注册～"
        )
