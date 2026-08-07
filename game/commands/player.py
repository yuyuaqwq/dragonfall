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
from ..commands.base import CommandBase


class PlayerCmds(CommandBase):

    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:快捷绑定|快捷列表|快捷删除|快捷清除|快捷)(?:[\s\S]*)$")

    async def shortcut(self, event: AstrMessageEvent):
        """快捷指令：绑定数字一键执行常用指令（如『快捷绑定 1 探索』，之后发『1』=探索）"""
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("❌ 还没注册角色哦，先发『注册 <名字> <职业>』～")
            return
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
                yield event.plain_result("❌ 指令太长啦（≤30 字）～")
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
        lines = [f"⚡ {qq_id} 的快捷（{len(shortcuts)} 个）："]
        for num in sorted(shortcuts.keys(), key=lambda x: int(x) if x.isdigit() else 999):
            lines.append(f"  {num} → {shortcuts[num]}")
        lines.append("『快捷绑定 <数字> <指令>』新增，『快捷删除 <数字>』删除")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?[0-9]\d?$")

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
        _args = self._strip_cmd(event, "注册").split(maxsplit=2)
        class_name = _args[0] if _args else ""
        name = _args[1] if len(_args) > 1 else ""
        race_arg = _args[2] if len(_args) > 2 else ""
        if self._player(group_id, qq_id):
            yield event.plain_result("你已经注册过角色啦！输入『角色』查看～")
            return
        class_name = class_name.strip()
        # v48：职业输入（中文或 ID）→ resolve 转 cls ID
        cls_id = C.resolve("classes", class_name)
        if cls_id not in C.CLASSES:
            # 无空格注册兼容：职业名与角色名粘在一起（如"注册战士格温"）
            for cid, cinfo in C.CLASSES.items():
                cn = cinfo.get("name", cid)
                if class_name.startswith(cn):
                    name = class_name[len(cn):] + (" " + name if name else "")
                    cls_id = cid
                    class_name = cn
                    break
            else:
                class_name = ""
        if cls_id not in C.CLASSES:
            avail = "、".join(cinfo.get("name", cid) for cid, cinfo in C.CLASSES.items())
            yield event.plain_result(f"未知职业『{class_name}』！可选职业：{avail}")
            return
        # 阶段九：种族解析（08 章，可选，缺省人类；支持简称如"精灵"→"银月精灵"）
        race_id = "human"
        race_display = ""
        if race_arg:
            r = C.resolve("races", race_arg)
            if r not in C.RACES:
                # 简称兼容：输入"精灵"匹配"银月精灵"
                r = next((rid for rid, ri in C.RACES.items() if race_arg in ri["name"]), r)
            if r not in C.RACES:
                races_avail = "、".join(ri.get("name", rid) for rid, ri in C.RACES.items())
                yield event.plain_result(f"未知种族『{race_arg}』！可选种族：{races_avail}（格式：注册 <职业> <名字> <种族>）")
                return
            race_id = r
            race_display = C.RACES[r]["name"]
        name = name.strip()[:12]
        if not name:
            yield event.plain_result("名字不能为空！格式：注册 <职业> <名字> [种族]")
            return
        cls = C.CLASSES[cls_id]
        cls_display = cls.get("name", cls_id)
        db.create_player(group_id, qq_id, name, cls_id, cls["base"], cls["base"]["hp"], cls["base"]["mp"], race_id)
        db.init_stats(group_id, qq_id)
        db.add_portal(qq_id, "vila_square")  # v10：新手自动激活维拉方碑
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
        init_display = "、".join(C.display("skills", s) for s in init_skills)
        race_line = f"种族：{C.RACES[race_id]['icon']} {C.RACES[race_id]['name']}（{C.RACES[race_id]['desc']}）\n" if race_id in C.RACES else ""
        yield event.plain_result(
            f"✨ 欢迎来到维斯特兰大陆，{name}！\n"
            f"职业：{cls['icon']} {cls_display}\n"
            f"{race_line}"
            f"『{cls['desc']}』\n\n"
            f"你出生在维拉镇中心广场，输入『找 镇长』接取第一个任务，『地图』查看周边。\n"
            f"🌅 你注意到广场中央矗立着一座【维拉方碑】，已为你激活！输入『方碑』查看，以后可以『传送』到各地路标。\n"
            f"⚔️ 你已学会初始技能：{init_display}（升级获得技能点，『技能学习 <技能名>』学新技能）\n"
            f"冒险者，你的故事开始了！"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:角色|我的角色)(?:\s*|$)")

    async def profile(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        cls = C.CLASSES[player["class_name"]]
        # v55.2：属性也统一「总值(+加成)」格式，每项单独一行（与『属性』面板一致）
        st, sources = E.player_stats_detail(
            player["class_name"], player["level"], player["equipment"],
            player.get("class_tier", 0), player.get("attributes"), player.get("evolve_path", 0),
            self._title_bonus(group_id, qq_id), player.get("race"),
        )
        base = next((s["stats"] for s in sources if s["name"] == "基础"), {})
        cur_map = C.MAP_BY_ID.get(player["cur_map"], {}).get("name", "维拉镇")
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
            "━━━━━━━━━━━━",
        ]
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
            if skey in ("crit", "dodge"):
                lines.append(f"{icon} {cname} {prefix}{int(final*100)}%(+{int(bonus*100)}%)")
            else:
                lines.append(f"{icon} {cname} {prefix}{final}(+{int(bonus)})")
        # 资源块（金币/位置/技能点/EXP 独立成块，每项单独一行）
        lines.append("━━━━━━━━━━━━")
        lines.append(f"💰 金币：{player['gold']}")
        lines.append(f"📍 位置：{cur_map}")
        lines.append(f"💡 技能点：{player.get('skill_points', 0)}")
        lines.append(f"✨ EXP：{player['exp']}/{need} ({exp_pct}%)")
        lines.append("━━━━━━━━━━━━")
        lines.append(f"装备：\n{eq_str}")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:排行|排行榜)(?:\s*|$)")

    async def leaderboard(self, event: AstrMessageEvent):
        group_id, _ = self._uid(event)
        tops = db.top_players(group_id, 10)
        if not tops:
            yield event.plain_result("还没有人注册角色，快来当第一名！『注册 战士 名字』")
            return
        lines = ["🏆 【维斯特兰强者榜】 🏆", "━━━━━━━━━━━━"]
        medals = ["🥇", "🥈", "🥉", "4.", "5.", "6.", "7.", "8.", "9.", "10."]
        for i, p in enumerate(tops):
            lines.append(f"{medals[i]} Lv.{p['level']} {C.CLASSES[p['class_name']]['icon']}{p['name']} ({C.display('classes', p['class_name'])})")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?种族(?:\s*|$)")

    async def races(self, event: AstrMessageEvent):
        """阶段九：种族一览（08 章，注册前查看 6 族天赋）"""
        lines = ["🧬 【种族】6 大种族各有取舍（注册时选择：注册 <职业> <名字> <种族>）", "━━━━━━━━━━━━"]
        for rid, r in C.RACES.items():
            t = r["talents"]
            tnames = r.get("talent_names", {})
            parts = []
            for k, v in t.items():
                nm = tnames.get(k, k)
                if k in ("hp_mult", "growth_mult", "spd_mult"):
                    pct = int((v - 1) * 100)
                    parts.append(f"{'🔻' if v < 1 else ''}{nm} {pct:+d}%")
                elif k == "crit_add":
                    parts.append(f"{nm} 暴击+{int(v*100)}%")
                elif k in ("phys_reduce", "magic_reduce"):
                    if v > 0:
                        parts.append(f"{nm} -{int(v*100)}%")
                    else:
                        parts.append(f"🔻{nm} +{int(-v*100)}%")
                elif k == "heal_received":
                    if v > 0:
                        parts.append(f"{nm} 受疗+{int(v*100)}%")
                    else:
                        parts.append(f"🔻{nm} 受疗{int(v*100)}%")
                elif k == "berserk_hp":
                    parts.append(f"{nm} 残血攻+20%")
                elif k == "timid_hp":
                    parts.append(f"🔻{nm} 残血攻-10%")
                elif k == "first_hit":
                    parts.append(f"{nm} 首击+{int(v*100)}%")
                elif k == "learn_discount":
                    parts.append(f"{nm} 学习-{int(v*100)}%")
                elif k == "gold_bonus":
                    parts.append(f"{nm} 金币+{int(v*100)}%")
                elif k == "item_effect":
                    parts.append(f"{nm} 消耗品+{int(v*100)}%")
                elif k == "craft_bonus":
                    parts.append(f"{nm} 锻造经验+{int(v*100)}%")
                elif k == "explore_item":
                    parts.append(f"{nm} 探索物品+{int(v*100)}%")
            lines.append(f"{r['icon']} {r['name']}：{'，'.join(parts)}")
        lines.append("━━━━━━━━━━━━")
        lines.append("💡 种族天赋 = 有得有失，负面已配正面补偿（净强度≈不变），选取舍不选碾压！")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?转职(?:\s*|$)")

    async def evolve(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        cls = C.CLASSES[player["class_name"]]
        tier = player.get("class_tier", 0)
        # 转职等级门槛：tier 1→30级 / tier 2→60级 / tier 3→90级（21 章三转体系）
        next_tier = tier + 1
        need_lv = {1: 30, 2: 60, 3: 90}.get(next_tier)
        branches = cls.get("evolve_branches", {}).get(next_tier, [])
        # 已满级转职
        if not need_lv:
            yield event.plain_result(
                f"👑 你已完成全部转职！{self._tier_title(player['class_name'], tier, player.get('evolve_path', 0))}\n"
                f"当前职业：{cls['icon']} {self._branch_title(player['class_name'], tier, player.get('evolve_path', 0))}（Lv.{player['level']}）"
            )
            return
        # 等级不足
        if player["level"] < need_lv:
            line = f"{cls['icon']}{C.display('classes', player['class_name'])}"
            evo_lines = []
            for t, branch_list in cls.get("evolve_branches", {}).items():
                lv = t * 30
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
        # 可以转职：需要选择分支
        raw = self._strip_cmd(event, "转职").strip()
        path = player.get("evolve_path", 0)
        # 无参数 → 显示分支选择（若尚未选择）
        if not raw and not path:
            if len(branches) < 2:
                # 该职业该 tier 没有分支（兼容），直接转
                async for r in self._do_evolve(event, group_id, qq_id, player, cls, tier, next_tier, 0):
                    yield r
                return
            descs = {
                0: "🔀 请选择进化路线：",
            }
            lines = [f"🌟 {cls['icon']}{C.display('classes', player['class_name'])} 达到了 {need_lv} 级，可以选择进化方向！", ""]
            for i, b in enumerate(branches):
                tag = "⚔️ 进攻" if i == 0 else "🛡️ 防御"
                lines.append(f"  {i+1}. {b}（{tag}）")
            lines.append("")
            lines.append("💡 输入『转职 <序号/名字>』选择路线（如：转职 1 或 转职 圣骑士）")
            yield event.plain_result("\n".join(lines))
            return
        # 带参数或已有路径 → 解析分支
        if not path:
            chosen = None
            if raw.isdigit():
                idx = int(raw) - 1
                if 0 <= idx < len(branches):
                    chosen = idx
            else:
                for i, b in enumerate(branches):
                    if raw == b or raw in b:
                        chosen = i
                        break
            if chosen is None:
                opts = "、".join(f"{i+1}.{b}" for i, b in enumerate(branches))
                yield event.plain_result(f"请选择正确的转职路线：{opts}")
                return
            path = chosen + 1  # 1=左(进攻) 2=右(防御)
        else:
            # 已有路径：后续转职自动走同分支
            path = path
        async for r in self._do_evolve(event, group_id, qq_id, player, cls, tier, next_tier, path):
            yield r
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

    async def _do_evolve(self, event, group_id, qq_id, player, cls, tier, next_tier, path):
        """执行转职（path: 0=默认, 1=左进攻, 2=右防御）"""
        old_title = self._tier_title(player["class_name"], tier, player.get("evolve_path", 0))
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
        # v2.1（21 章）：转职自动获得二转被动（tier2 lv.60）/ 三转奥义（tier3 lv.90）
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
        is_final = next_tier >= 3
        yield event.plain_result(
            f"🌟 转职成功！\n"
            f"━━━━━━━━━━━━\n"
            f"{old_title}\n"
            f"  ↓↓↓\n"
            f"{cls['icon']} {new_title}{branch_line}\n\n"
            f"✨ 成长加成 +{bonus}%（全属性）\n"
            f"📜 新技能已解锁，输入『技能』查看！{auto_line}\n"
            f"{'👑 已达成最终转职（Lv.90 三转）！' if is_final else '💪 继续历练，下一次转职在 Lv.60/90'}"
        )
        return

    def _evolve_auto_skills(self, player: dict, next_tier: int) -> list:
        """转职自动获得的技能（二转被动 60 级 / 三转奥义 90 级）"""
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
        """职业进阶称号（v25：按分支返回）"""
        return f"{C.CLASSES.get(class_name, {}).get('icon', '')} {self._branch_title(class_name, tier, evolve_path)}"

    @filter.regex(r"^(?:\[At:\d+\]\s*)?属性(?:\s*|$)")

    async def attributes(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
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
            if skey in ("crit", "dodge"):
                lines.append(f"{icon} {cname} {int(final*100)}%(+{int(bonus*100)}%)")
            else:
                lines.append(f"{icon} {cname} {final}(+{int(bonus)})")
        lines.append("━━━━━━━━━━━━")
        lines.append(f"🎯 自由属性点：{player.get('attr_pts', 0)}")
        # 加点分配（每项单独一行）
        lines.append(f"💪 力量 {attr.get('str', 0)}(每点 +1.2 攻击)")
        lines.append(f"🏃 敏捷 {attr.get('agi', 0)}(每点 +0.8 速度 ＋ 0.4% 暴击)")
        lines.append(f"🧠 智力 {attr.get('int', 0)}(每点 +1.2 魔攻 ＋ 1.5 魔力)")
        lines.append(f"❤️‍🩹 耐力 {attr.get('vit', 0)}(每点 +8 生命)")
        lines.append("━━━━━━━━━━━━")
        lines.append("💡 『加点 力量 <点数>』分配属性点，『洗点』重置（500金币）")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?加点(?:\s*|$)")

    async def add_attr(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
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

    async def reset_skill(self, event: AstrMessageEvent):
        """技能洗点（v27 独立指令）：花 500 金币返还全部已花费技能点（学习+升级），清空已学技能与等级"""
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        if not player.get("learned_skills"):
            yield event.plain_result("你还没有学习过任何技能，无需洗点～")
            return
        cost = 500
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
            f"🔄 技能洗点成功！返还 {spent} 技能点（花费 {cost} 金币）\n"
            f"已学技能清空（保留初始技能：{'、'.join(init_skills) or '无'}），技能等级已重置，『技能学习』重新规划 build 吧～"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?转职重置(?:[\s\S]*)$")

    async def evolve_reset(self, event: AstrMessageEvent):
        """转职重置（21 章 §8）：付费清空转职分支，保留等级，可重新选择分支"""
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        tier = player.get("class_tier", 0)
        if tier <= 0:
            yield event.plain_result("你还没有转职过，无需重置～『转职』查看路线。")
            return
        cost = {1: 500, 2: 2000, 3: 5000}.get(tier, 500)
        if player["gold"] < cost:
            yield event.plain_result(f"转职重置需要 {cost} 金币（当前 {tier} 转），你只有 {player['gold']} 金币。")
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
            f"🔄 转职重置成功！（花费 {cost} 金币）\n"
            f"━━━━━━━━━━━━\n"
            f"{old_title} → 回到基础职业\n"
            f"✨ 等级与基础技能保留，分支技能已清除（{'、'.join(removed) or '无'}）\n"
            f"💡 到 30/60/90 级可重新『转职』选择新分支！"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?洗点(?:\s*|$)")

    async def reset_attr(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        raw = self._strip_cmd(event, "洗点").strip()
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        # v27：技能洗点已拆分为独立指令『技能洗点』，避免与属性洗点混淆
        if "技能" in raw:
            yield event.plain_result("技能洗点是独立指令：『技能洗点』（500金币返还技能点）～『洗点』只重置属性点。")
            return
        attr = player.get("attributes", {})
        used = sum(attr.values())
        if used == 0:
            yield event.plain_result("你还没有分配过属性点，无需洗点～")
            return
        cost = 500
        if player["gold"] < cost:
            yield event.plain_result(f"洗点需要 {cost} 金币，你只有 {player['gold']} 金币。")
            return
        import json
        db.update_player(group_id, qq_id, gold=player["gold"] - cost,
                         attr_pts=player.get("attr_pts", 0) + used,
                         attributes=json.dumps({"str": 0, "agi": 0, "int": 0, "vit": 0}, ensure_ascii=False))
        yield event.plain_result(f"🔄 洗点成功！返还 {used} 点属性点（花费 {cost} 金币）\n『加点』重新分配～")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?战力(?:\s*|$)")

    async def power(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        st = E.player_final_stats(player["class_name"], player["level"], player["equipment"], player.get("class_tier", 0), player.get("attributes"), player.get("evolve_path", 0), self._title_bonus(group_id, qq_id), player.get("race"))
        pw = int(st["atk"] * 2 + st["matk"] * 2 + st["def"] * 1.5 + st["mdef"] * 1.5
                + st["max_hp"] / 10 + st["max_mp"] / 10 + st["spd"] * 3)
        tier = player.get("class_tier", 0)
        title = self._tier_title(player["class_name"], tier)
        yield event.plain_result(
            f"⚡ 【战力】{player['name']}（{title} Lv.{player['level']}）\n"
            f"战斗力：{pw:,}\n"
            f"━━━━━━━━━━━━\n"
            f"❤️ {st['max_hp']} ｜ ⚔️ {st['atk']} ｜ 🔮 {st['matk']} ｜ 🛡️ {st['def']} ｜ 💨 {st['spd']}\n"
            f"💡 升级、装备、转职、加点都能提升战力！"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?技能详情(?:[\s\S]*)$")

    async def skill_detail(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
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
            slv = int((player.get("skill_levels") or {}).get(skill_name, 1) or 1)
            status = f"✅ 已学会 Lv.{slv}/{mx}"
        elif info["lv"] <= player["level"]:
            status = f"📖 可学习（Lv.{info['lv']}）"
        else:
            status = f"🔒 未学会（Lv.{info['lv']} 解锁）"
        lines = [
            f"📜 【{display_name}】｜{status}",
            f"━━━━━━━━━━━━",
            f"类型：{info.get('kind','')} ｜ 需求等级：Lv.{info['lv']} ｜ 消耗：{info['mp']} 魔力",
            f"效果：{info['desc']}",
        ]
        owner = E.branch_skill_owner(player["class_name"], skill_name)
        if owner:
            lines.append(f"专属：{owner[1]}（Lv.{owner[0]*30} 转职解锁）")
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
            lines.append(f"团队：{team_cn.get(info['team'], info['team'])}（副本中广播全队）")
        if info.get("cond"):
            cond = info["cond"]
            ctype = cond.get("type")
            pct = int(cond.get("hp_pct", 0.4) * 100)
            mult = cond.get("mult", 1.0)
            label = cond.get("label", "")
            stacks = cond.get("stacks", 0)
            ctype_map = {
                "enemy_hp_low": f"敌方血量<{pct}%",
                "player_hp_low": f"自身血量<{pct}%",
                "enemy_hp_high": f"敌方血量>{pct}%",
                "player_hp_high": f"自身血量>{pct}%",
                "enemy_full_hp": "敌方满血",
                "enemy_frozen": "敌方被冻结",
                "enemy_stunned": "敌方被眩晕",
                "enemy_poison_stacks": f"敌方中毒≥{stacks}层",
                "enemy_marked": "敌方被标记",
                "enemy_debuff": "敌方有减益",
                "enemy_slowed": "敌方减速中",
                "element_marks": f"敌方{cond.get('element','')}印记≥{stacks}层",
                "speed_ratio": f"速度比≥{cond.get('ratio',1.5)}x",
                "player_shield": "自身有护盾",
                "player_spd_up": "自身加速中",
                "player_chi_stacks": f"自身气力≥{stacks}点",
                "player_res_stacks": f"自身{cond.get('res_key','')}≥{stacks}",
                "player_first": "先手行动",
                "player_untouched": "本场未受击",
                "player_buffed": "自身有增益",
            }
            ctext = ctype_map.get(ctype, ctype)
            lines.append(f"⚔️ 条件转化：{ctext}时激活『{label}』（威力 ×{mult}）")
        if not is_learned and info["lv"] <= player["level"]:
            cost = E.skill_learn_cost(player["level"], info["lv"])
            lines.append(f"💡 『技能学习 {display_name}』消耗 {cost} 技能点学会（当前 {player.get('skill_points',0)} 点）")
        elif is_learned:
            slv = int((player.get("skill_levels") or {}).get(skill_name, 1) or 1)
            if slv < mx:
                cost = E.skill_upgrade_cost(slv, info)
                nxt = " · ".join(self._skill_upgrade_gains(info, slv + 1))
                lines.append(f"💡 『技能升级 {display_name}』花 {cost} 点升到 Lv.{slv + 1}（{nxt}，当前 {player.get('skill_points',0)} 点）")
            else:
                lines.append("✨ 已满级！")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?技能学习(?:[\s\S]*)$")

    async def skill_learn(self, event: AstrMessageEvent):
        """技能学习（v12）：等级门槛 + 消耗技能点学会，学会永久可用"""
        group_id, qq_id = self._uid(event)
        skill_name = self._strip_cmd(event, "技能学习")
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        yield event.plain_result(self._skill_learn_msg(group_id, player, skill_name))

    def _skill_learn_msg(self, group_id, player: dict, skill_name: str) -> str:
        """技能学习核心逻辑（v12：等级门槛 + 技能点学会，学会永久可用）"""
        skill_name = (skill_name or "").strip()
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
                return f"『{display_name}』是 {bname} 的专属技能，需要先转职为 {bname} 才能学习！（Lv.30/60/90 可转职）"
            branches = C.CLASSES[player["class_name"]].get("evolve_branches", {}).get(need_tier, [])
            idx = 0 if my_path == 1 else 1
            my_branch = branches[idx] if idx < len(branches) else ""
            if my_branch != bname:
                return f"『{display_name}』是 {bname} 的专属技能，你走的是 {my_branch} 路线，学不了～"
        need_lv = info["lv"]
        if player["level"] < need_lv:
            return f"『{display_name}』需要 Lv.{need_lv} 才能学习，你才 Lv.{player['level']}——升级吧！（每级 +1 技能点）"
        cost = E.skill_learn_cost(player["level"], need_lv)
        # 阶段九：人类多才多艺——学习技能点 -8%
        if E.race_stats(player.get("race")).get("learn_discount"):
            cost = max(1, int(cost * (1 - E.race_stats(player.get("race"))["learn_discount"])))
        pts = player.get("skill_points", 0)
        if pts < cost:
            return (
                f"学习『{display_name}』需要 {cost} 技能点（技能 Lv.{need_lv}），你只有 {pts} 点——升级可获得技能点（每级 +1）～"
            )
        learned = list(learned) + [skill_name]
        spent = player.get("skill_spent", 0) + cost
        db.update_player(group_id, player["qq_id"], skill_points=pts - cost, learned_skills=learned, skill_spent=spent)
        if info.get("kind") == "被动":
            return (
                f"✨ 消耗 {cost} 技能点，学会了被动技能『{display_name}』！\n"
                f"⚙️ 被动技能无需施放，战斗自动生效！剩余技能点 {pts - cost}\n"
                f"「{info['desc']}」"
            )
        return (
            f"✨ 消耗 {cost} 技能点，学会了『{display_name}』！\n"
            f"现在 Lv.{player['level']} 就能使用它了，剩余技能点 {pts - cost}"
        )

    def _skill_upgrade_gains(self, info: dict, lv: int) -> list:
        """技能升级多维成长描述（v56.1）：按技能单独策划的成长配置列出各维度提升"""
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

    async def skill_upgrade(self, event: AstrMessageEvent):
        """技能升级（v27）：已学技能花技能点升级，攻击/治疗 power 提升、增益回合延长"""
        group_id, qq_id = self._uid(event)
        skill_name = self._strip_cmd(event, "技能升级").strip()
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
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
        cur_lv = int(levels.get(skill_name, 1) or 1)
        mx = E.skill_max_level(info)
        if cur_lv >= mx:
            yield event.plain_result(f"『{skill_name}』已经是满级 Lv.{mx} 啦，不能再升了～")
            return
        cost = E.skill_upgrade_cost(cur_lv, info)
        pts = player.get("skill_points", 0)
        if pts < cost:
            yield event.plain_result(
                f"升级『{skill_name}』到 Lv.{cur_lv + 1} 需要 {cost} 技能点，你只有 {pts} 点——升级可获得技能点（每级 +1）～"
            )
            return
        levels[skill_name] = cur_lv + 1
        spent = player.get("skill_spent", 0) + cost
        db.update_player(group_id, player["qq_id"], skill_points=pts - cost,
                         skill_levels=levels, skill_spent=spent)
        display_name = info.get("name", skill_name)
        gains = self._skill_upgrade_gains(info, cur_lv + 1)
        desc = " · ".join(gains)
        next_cost = E.skill_upgrade_cost(cur_lv + 1, info)
        tail = f"｜ 升到 Lv.{cur_lv + 2} 需 {next_cost} 点" if next_cost else "｜ 已满级！"
        yield event.plain_result(
            f"⬆️ 『{display_name}』升级到 Lv.{cur_lv + 1}（{desc}）！消耗 {cost} 技能点，剩余 {pts - cost} 点{tail}"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?技能栏(?:\s*|$)")

    async def skill_bar_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        bar = db.get_skill_bar(qq_id)
        lines = ["🎛️ 【技能栏】（战斗中『技能 <槽位>』快捷施放）", "━━━━━━━━━━━━"]
        for i in range(6):
            sname = bar[i] if i < len(bar) else None
            if sname:
                info = E.skill_info(player["class_name"], sname)
                kind = info.get("kind", "") if info else ""
                lines.append(f" {i+1}. {sname}（{kind}）")
            else:
                lines.append(f" {i+1}. （空）")
        lines.append("━━━━━━━━━━━━")
        lines.append("💡 『设置技能 <槽位> <技能名>』配置，如：设置技能 1 火球术（须先学会）")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?设置技能(?:\s*|$)")

    async def skill_bar_set(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        raw = self._strip_cmd(event, "设置技能").strip()
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        parts = raw.split(maxsplit=1)
        if len(parts) < 2 or not parts[0].isdigit():
            yield event.plain_result("格式：设置技能 <槽位1-6> <技能名>，如『设置技能 1 火球术』")
            return
        slot = int(parts[0])
        if slot < 1 or slot > 6:
            yield event.plain_result("技能栏只有 6 个槽位（1~6）！")
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

    async def build_view(self, event: AstrMessageEvent):
        """流派（v52 Build 系统）：查看本职业流派 / 一键配置技能栏"""
        group_id, qq_id = self._uid(event)
        raw = self._strip_cmd(event, "流派").strip()
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
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
                lines.append(f"{info.get('icon','')} {name}（已学 {learned_cnt}/6）")
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
                lines.append(f"  {i}. 🔒 {sname}（未学会）")
        if missing:
            lines.append(f"⚠️ 还没学会：{'、'.join(missing)}——『技能学习 <名称>』学会后重新『流派 {name}』即可补上")
        lines.append(f"💡 打法：{info['desc']}")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?注销(?:[\s\S]*)$")

    async def delete_account(self, event: AstrMessageEvent):
        """注销角色：删除全部数据，可重新注册（v62 群友想切职业）。

        两步确认防误删：『注销』→ 提示确认；10 分钟内『注销 确认』才真正删除。
        确认状态存 event_state（key: del_confirm_<qq_id>），过期自动失效。
        """
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色，不用注销～输入『注册 战士 名字』创建吧！")
            return
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
                f"所有角色数据已删除，可以重新『注册 <职业> <名字>』开始新旅程！"
            )
            return
        # 发起注销：写确认状态（10 分钟有效）
        db.set_event_state(f"del_confirm_{qq_id}", int(time.time()))
        yield event.plain_result(
            f"⚠️ 真的要注销角色【{player['name']}】吗？\n"
            f"删除后将失去：等级/装备/背包/金币/技能/副业/宠物/公会 全部数据！\n"
            f"━━━━━━━━━━━━\n"
            f"确认请回复：『注销 确认』（10 分钟内有效）\n"
            f"想切职业也可以直接注销后重新注册～"
        )
