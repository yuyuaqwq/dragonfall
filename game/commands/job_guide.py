# -*- coding: utf-8 -*-
"""命令层 - job_guide（v130.2g 新功能：『职业』/『职业 <名称>』职业速查指令）

落地玩家意见 #1（zerc）「增加查看职业信息的功能」：
- 『职业』：12 职业速查一览（基础六 + 隐藏六分组，名称 + 定位一句话）
- 『职业 <名称>』：单职业详情（基础名/档位路线/核心资源机制/转职条件/隐藏线解锁方式）

名称解析见 data/job_guide.py resolve_job：显示名（含 v130.2 新名 淬势者）→ classes.py
aliases（苦修士/武僧→淬势者）→ 兼容名（歌者→牧师）→ 分支名（吟游诗人→牧师）→ 模糊兜底。
纯信息查询：不 require_player（注册前可查，与『种族』『图鉴』同款）。
"""
from ._platform import AstrMessageEvent, filter
from ..data.job_guide import (
    JOB_GUIDE, BASE_ORDER, HIDDEN_ORDER, HIDDEN_SUCCESSORS,
    EXTRA_RESOURCES, resolve_job,
)
from ..data.core_resources import CORE_RESOURCES
from ..commands.base import CommandBase


class JobGuideCmds(CommandBase):
    """『职业』速查：12 职业一览 + 单职业详情（玩家意见 #1）"""

    @filter.regex(r"^(?:\[At:\d+\]\s*)?职业(?:\s+(\S+))?\s*$")
    async def job_guide(self, event: AstrMessageEvent):
        raw = self._strip_cmd(event, "职业").strip()
        if not raw:
            yield event.plain_result(self._overview())
            return
        hit = resolve_job(raw)
        if isinstance(hit, str):
            yield event.plain_result(self._detail(hit))
            return
        if isinstance(hit, list):
            yield event.plain_result(
                "🤔 『{}』 匹配到多个职业，试试精确名称：{}".format(
                    raw, "、".join(f"『职业 {JOB_GUIDE[c]['name']}』" for c in hit)))
            return
        yield event.plain_result(
            f"⚠️ 未找到职业『{raw}』！输入『职业』可查看全部 12 职业速查。")

    # ---------------- 一览 ----------------

    def _overview(self) -> str:
        lines = ["⚔️ 【职业】12 职业速查 · 『职业 <名称>』看详情", "━━━━━━━━━━━━"]
        lines.append("🟦 基础六职业（30 级转职，各分攻/守双线）")
        for cid in BASE_ORDER:
            g = JOB_GUIDE[cid]
            lines.append(f"{g['icon']} {g['name']}：{g['position']}")
        lines.append("")
        lines.append("🟪 隐藏六职业（40 级起完成对应任务链解锁）")
        for cid in HIDDEN_ORDER:
            g = JOB_GUIDE[cid]
            lines.append(f"{g['icon']} {g['name']}：{g['position']}")
        lines.append("")
        lines.append("💡 详情含转职分支/核心资源/解锁条件：『职业 战士』『职业 淬势者』")
        return "\n".join(lines)

    # ---------------- 详情 ----------------

    def _detail(self, cid: str) -> str:
        g = JOB_GUIDE[cid]
        kind = "隐藏职业" if g["hidden"] else "基础职业"
        lines = [f"{g['icon']} 【{g['name']}】（{kind}）", "━━━━━━━━━━━━"]
        lines.append(f"📖 {g['desc']}")
        lines.append(self._tier_line(g))
        lines.append(self._resource_line(g))
        melee = "近战" if g["reach"] == 1 else "远程"
        role = g["role"] + (" · " + g["rank_label"] if g["rank_label"] else "")
        lines.append(f"🎯 定位：{role} · {melee}")
        if g["hidden"]:
            lines.append(self._unlock_line(g))
        else:
            for s in HIDDEN_SUCCESSORS.get(cid, []):
                sg = JOB_GUIDE[s]
                lines.append(
                    f"🔮 隐藏传承：{sg['icon']}{sg['name']}（{self._unlock_line(sg, short=True)}）")
        return "\n".join(lines)

    def _tier_line(self, g: dict) -> str:
        """档位路线：T1(Lv.30) 攻线·狂战士 / 守线·盾卫士（基础双线，index0=攻线）"""
        lines = ["🔀 档位路线："]
        tlv = g["tier_levels"]
        for t in sorted(g.get("tiers") or {}):
            names = g["tiers"][t]
            lv = tlv.get(int(t), 30)
            if g["hidden"] or len(names) <= 1:
                lines.append(f"  T{t}(Lv.{lv}) 流派·{' / '.join(names)}" if g["hidden"]
                             else f"  T{t}(Lv.{lv}) {' / '.join(names)}")
            else:
                atk = names[0] if len(names) > 0 else "?"
                dfn = names[1] if len(names) > 1 else "?"
                lines.append(f"  T{t}(Lv.{lv}) 攻线·{atk} / 守线·{dfn}")
        return "\n".join(lines)

    def _resource_line(self, g: dict) -> str:
        """核心资源与机制一句话（core_resources.py desc 原文）+ 转职分支专属资源"""
        lines = [f"⚡ 核心资源·{g['resource_name']}（上限 {g['resource_max']}）：{g['resource_desc']}"]
        for rk in EXTRA_RESOURCES.get(g["cls_id"], []):
            r = CORE_RESOURCES.get(rk)
            if r:
                lines.append(f"　↳ 转职分支专属·{r.get('name', rk)}（上限 {r.get('max')}）：{r.get('desc')}")
        return "\n".join(lines)

    def _unlock_line(self, g: dict, short: bool = False) -> str:
        """隐藏线解锁方式：任务链 + 档位门槛 + 种族血缘限制 + 线索（详情）"""
        tlv = g["tier_levels"]
        tk = g.get("task_name") or "专属试炼"
        if short:
            line = f"完成「{tk}」任务链 Lv.{tlv.get(1, 40)} 解锁"
            if g.get("src_race"):
                line += f"，限{g['race_name']}血脉"
            return line
        lines = [f"🗝️ 解锁：完成「{tk}」任务链（Lv.{tlv.get(1, 40)} 起，档位 "
                 f"{tlv.get(1, 40)}/{tlv.get(2, 60)}/{tlv.get(3, 90)}）"]
        if g.get("src_race"):
            lines.append(f"🧬 血脉：仅限{g['race_name']}方可传承")
        if g.get("src_base"):
            lines.append(f"🌱 渊源：由{JOB_GUIDE[g['src_base']]['name']}一脉传承")
        if g.get("hint"):
            lines.append(g["hint"])
        return "\n".join(lines)