#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""文案表（消息模板）门禁 —— `game/data/text_specs.json` + `game/core/texts.py`。

**这一层要防的四件事**（每件都由断言钉死）：
  ① 声明与调用脱节：表里有、代码不用（死文案）｜代码用、表里没有（运行时缺 key）
  ② 槽位对不上：模板写 `{foo}`，调用点传 `name` ⇒ 玩家会看到 `{foo}` 原样露出来
  ③ 静默降级：缺 key 时悄悄退回旧串/空串 —— 本层刻意**不静默**（ERROR 日志 + 返回 key 本身）
  ④ 声明文件坏了没人知道：语法错/空值/params 与模板不一致（引擎 `validate()` 只报告不抛 → 这里必须查）

**逐字一致**（"迁移没改玩家看到的字"）由两层证据扛：
  · 副本域：`tests/test_v185_instance_admission.py` 的 **805 格逐格冻结比对**（对照物 = 旧实现冻结体）
  · 周常 / 签到 / 补给箱 / 每日域：本文件 `WEEKLY_FROZEN` / `SIGNIN_FROZEN` / `SUPPLY_FROZEN` /
    `DAILY_FROZEN`（面板段）/ `QUEST_FROZEN`（『每日』命令） —— **迁移前真跑各分支存下来的完整输出**，
    每次跑测试复跑比对（签到分支用 random 打桩保证可复现）
  · 副本结算域（`game/commands/instance_router.py`）：本文件 `INSTANCE_SETTLE_FROZEN` ——
    11 个分支（探索/肃清/等待/嘲讽/异常/密室/房间清空/切怪/层清空/普通轮转）在**迁移前**真跑存下的
    完整输出，每次跑测试复跑比对（每次 clean_db + random.seed 固定随机；「战斗状态异常」一支用桩
    让 build_battle 抛错触发，见 `_is_b6_battle_broken`）

跑法：python tests/test_texts_table.py（exit=0 通过）
"""
import ast
import asyncio
import datetime
import io
import json
import os
import random
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from conftest import C, db, clean_db, FakeEvent, run, Main  # noqa: E402
from data.plugins.dragonfall.game.core import texts as T  # noqa: E402
from data.plugins.dragonfall.game.services.weekly_progress import (  # noqa: E402
    _week_state, _save_week_state,
)
from data.plugins.dragonfall.game.commands import instance_battle as _IB  # noqa: E402
from data.plugins.dragonfall.game.commands.combat import CombatCmds as _CombatCmds  # noqa: E402
from data.plugins.dragonfall.game.commands.instance import InstanceCmds as _InstCmds  # noqa: E402
from data.plugins.dragonfall.game.commands.world import WorldCmds as _WorldCmds  # noqa: E402

_PD = os.path.dirname(_HERE)
WEEKLY_SRC = os.path.join(_PD, "game", "commands", "weekly.py")
MISC_SRC = os.path.join(_PD, "game", "commands", "misc.py")
EVENT_SRC = os.path.join(_PD, "game", "commands", "event_menu.py")
WORLD_SRC = os.path.join(_PD, "game", "commands", "world.py")
QUESTS_SRC = os.path.join(_PD, "game", "services", "quests.py")
GATE_SRC = os.path.join(_PD, "game", "core", "instance_gate.py")
INSTANCE_ROUTER_SRC = os.path.join(_PD, "game", "commands", "instance_router.py")
SPEC = T.SPEC_PATH
# 已迁移的域 → 该域文案由哪个文件接线（新增一个域时在这里加一行）
WIRED = {"副本准入": GATE_SRC, "副本结算": INSTANCE_ROUTER_SRC, "周常": WEEKLY_SRC,
         "签到": MISC_SRC, "补给箱": EVENT_SRC, "每日任务": WORLD_SRC, "每日命令": QUESTS_SRC}

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print("  ✅ %s" % name)
    else:
        failed += 1
        print("  ❌ %s %s" % (name, str(detail)[:400]))


# ══════════════════════════════════════════════════════════════════════════
# 迁移前行为快照（真跑『周常』『周常列表』6 个分支，逐字冻结）
# ══════════════════════════════════════════════════════════════════════════
WEEKLY_FROZEN = {
    "A_locked": "🏮 悬赏板还蒙着布——上面的委托要 Lv.50 的冒险者才接得动。\n💡 先完成『每日』任务和主线提升等级，到了 Lv.50 再来看看～",
    "B_first": "🏮 【本周悬赏】已发布！\n━━━━━━━━━━━━\n1. 『边境肃清令』击败 30 只任意怪物\n    目标：讨伐任意怪物 30 只｜赏金：经验 +155000 金币 +38000\n2. 『深林猎手悬赏』击败 40 只任意怪物\n    目标：讨伐任意怪物 40 只｜赏金：经验 +175000 金币 +44000\n3. 『剿灭魔裔』击败 5 只精英怪物\n    目标：讨伐精英怪物 5 只｜赏金：经验 +190000 金币 +48000\n\n💡 击杀自动计数，达标立即发奖！『周常』随时查进度，『周常列表』看全池悬赏",
    "C_progress": "🏮 【本周悬赏】1/3 已完成\n━━━━━━━━━━━━\n1. 『边境肃清令』 ✅ 已完成\n2. 『深林猎手悬赏』 ⏳ 0/40\n    目标：讨伐任意怪物 40 只｜赏金：经验 +175000 金币 +44000\n3. 『剿灭魔裔』 ⏳ 0/5\n    目标：讨伐精英怪物 5 只｜赏金：经验 +190000 金币 +48000\n\n💡 击杀自动计数，达标立即发奖——悬赏每周一刷新",
    "D_pool_p1": "🏮 【周常悬赏池】第 1/3 页（每周自动发布 3 条）\n━━━━━━━━━━━━\n· 『边境肃清令』(Lv.50+) 击败 30 只任意怪物\n    经验 +155000 金币 +38000\n· 『深林猎手悬赏』(Lv.50+) 击败 40 只任意怪物\n    经验 +175000 金币 +44000\n· 『剿灭魔裔』(Lv.50+) 击败 5 只精英怪物\n    经验 +190000 金币 +48000\n· 『破阵斩将』(Lv.50+) 击败 6 只精英怪物\n    经验 +210000 金币 +53000\n\n💡 每周一刷新自动抽取适合你等级的悬赏；『周常』查看本周任务\n📄 『周常列表 2』翻页",
    "E_pool_p2": "🏮 【周常悬赏池】第 2/3 页（每周自动发布 3 条）\n━━━━━━━━━━━━\n· 『讨伐区域首领』(Lv.50+) 击败 2 个区域 Boss\n    经验 +230000 金币 +58000\n· 『诛灭祸乱之源』(Lv.50+) 击败 3 个区域 Boss\n    经验 +250000 金币 +64000\n· 『龙脊清扫令』(Lv.70+ 🔒) 击败 35 只任意怪物\n    经验 +400000 金币 +100000\n· 『深渊行者试炼』(Lv.70+ 🔒) 击败 45 只任意怪物\n    经验 +450000 金币 +115000\n\n💡 每周一刷新自动抽取适合你等级的悬赏；『周常』查看本周任务\n📄 『周常列表 3』翻页",
    "F_all_done": "🏮 【本周悬赏】3/3 已完成\n━━━━━━━━━━━━\n1. 『边境肃清令』 ✅ 已完成\n2. 『深林猎手悬赏』 ✅ 已完成\n3. 『剿灭魔裔』 ✅ 已完成"
}   # 迁移前快照（2026-09-12 真跑存下，勿手改）

# 迁移前行为快照（真跑『签到』5 个分支，逐字冻结；random 打桩保证可复现）
SIGNIN_FROZEN = {
    "A_first_bad": "📅 【签到成功】第 1 次签到！连续 1 天！\n💰 获得 25 金币\n🌧️ 今日运势：小凶(今日金币－10%)\n💡 今日小凶金币收益 -10%……别灰心！用『使用 幸运符』可消解，或明日签到重roll运势～",
    "B_first_big": "📅 【签到成功】第 1 次签到！连续 1 天！\n💰 获得 25 金币\n🌟 今日运势：大吉(今日经验＋10%)",
    "C_dup": "今天已经签过到啦！明天再来～",
    "D_streak7": "📅 【签到成功】第 7 次签到！连续 7 天！\n💰 获得 55 金币\n🌟 今日运势：大吉(今日经验＋10%)\n🎁 连续 7 天奖励：🟣【龙鳞战甲】！",
    "E_festival": "📅 【签到成功】第 1 次签到！连续 1 天！\n💰 获得 50 金币\n🌟 今日运势：大吉(今日经验＋10%)\n🎉 节日庆典：签到奖励翻倍！"
}   # 迁移前快照（2026-09-12 真跑存下，勿手改）

SUPPLY_FROZEN = {
    "A_first": "📦 【每日补给箱】\n━━━━━━━━━━━━\n  🎁 每日材料箱：图纸残页、淬火石、烤肉串！\n  🎁 每日道具箱：强化石、双倍金币符、炖菜！\n  🎁 每日豪华箱：白银箱、精炼强化石、幸运符！\n\n💡 补给箱内容：图纸残页/淬火石/强化石/幸运符等（每日 0 点重置）",
    "B_second": "📦 【每日补给箱】\n━━━━━━━━━━━━\n  ⏳ 每日材料箱：今日已领取～\n  ⏳ 每日道具箱：今日已领取～\n  🎁 每日豪华箱：白银箱、精炼强化石、幸运符！\n\n💡 补给箱内容：图纸残页/淬火石/强化石/幸运符等（每日 0 点重置）",
    "C_third": "📦 【每日补给箱】\n━━━━━━━━━━━━\n  ⏳ 每日材料箱：今日已领取～\n  ⏳ 每日道具箱：今日已领取～\n  ⏳ 每日豪华箱：本周已领 2/2～\n  今天/本周的补给箱都已领过啦，明天再来吧～\n\n💡 补给箱内容：图纸残页/淬火石/强化石/幸运符等（每日 0 点重置）"
}   # 迁移前快照（2026-09-12 真跑存下，勿手改）

# 迁移前行为快照（真跑『任务』面板 4 种状态：从未领取/进行中/完成未满额/满额，逐字冻结）
DAILY_FROZEN = {
    "A_never": "📜 【冒险日志】\n━━━━━━━━━━━━\n【主线】已全部完成！🎊\n\n【支线】暂无——找镇上的 NPC 聊聊可能有意外收获\n\n【每日】今日还没领取任务——输入『每日』发布今日悬赏～\n\n💡 进行中可弃：『放弃 <序号>』",
    "B_active": "📜 【冒险日志】\n━━━━━━━━━━━━\n【主线】已全部完成！🎊\n\n【支线】暂无——找镇上的 NPC 聊聊可能有意外收获\n\n【每日】\n 1. 『边境警戒』\n    击杀 10 只任意怪物 (3/10)\n 2. 『神秘委托』\n    未知目标（无达标数定义） (进度 1)\n\n💡 『对话 <NPC名>』接取任务",
    "C_done_part": "📜 【冒险日志】\n━━━━━━━━━━━━\n【主线】已全部完成！🎊\n\n【支线】暂无——找镇上的 NPC 聊聊可能有意外收获\n\n【每日】今日已完成 2 个每日任务——输入『每日』还能再接～\n\n💡 『对话 <NPC名>』接取任务",
    "D_done_full": "📜 【冒险日志】\n━━━━━━━━━━━━\n【主线】已全部完成！🎊\n\n【支线】暂无——找镇上的 NPC 聊聊可能有意外收获\n\n【每日】今日已完成 10/10 个每日任务，明天再来！\n\n💡 『每日』领取今日任务"
}   # 迁移前快照（2026-09-12 真跑存下，勿手改；比对时剔除 💡 随机提示行）

# 迁移前行为快照（真跑『每日』命令 7 分支：首发/已有/满额/重抽/衰减/达标/重复达标）
QUEST_FROZEN = {
    "A_publish": "ok=True\n📜 今日任务已发布！\n━━━━━━━━━━━━\n 1. 『大扫除』击败 15 只任意怪物\n    奖励：经验 +1500 金币 +400\n 2. 『日常讨伐』击败 10 只任意怪物\n    奖励：经验 +1200 金币 +270",
    "B_have": "ok=False\n你已经有每日任务了！输入『任务』查看～",
    "C_limit": "ok=False\n⚠️ 今日已完成 10/10 个每日任务，明天再来吧！",
    "D_republish": "ok=True\n📜 今日任务已发布！\n━━━━━━━━━━━━\n 1. 『大扫除』击败 15 只任意怪物\n    奖励：经验 +1500 金币 +400\n 2. 『日常讨伐』击败 10 只任意怪物\n    奖励：经验 +1200 金币 +270\n📌 今日已完成 3/10 个每日任务",
    "E_decay": "ok=True\n📜 今日任务已发布！\n━━━━━━━━━━━━\n 1. 『大扫除』击败 15 只任意怪物\n    ⚠️ 重复完成，奖励衰减 60%：经验 +900 金币 +240\n 2. 『日常讨伐』击败 10 只任意怪物\n    ⚠️ 重复完成，奖励衰减 60%：经验 +720 金币 +162",
    "F_settle": "📜 每日『边境警戒』完成！奖励：经验 +100 金币 +50",
    "G_settle_decay": "📜 每日『边境警戒』完成！重复完成，奖励衰减 60%：经验 +100 金币 +50"
}   # 迁移前快照（2026-09-12 真跑存下，勿手改；抽签用 random.seed(11)）

# 迁移前行为快照（2026-09-12 真跑 instance_router.py 的 11 个结算分支，逐字冻结；
# 来源 $TEMP/instance_settle_before.json —— 采于**接线前**的代码，勿手改）
INSTANCE_SETTLE_FROZEN = {
    "B1_无敌人_探索": "当前区域还有敌人潜伏！『探索』找到它们～",
    "B2_无敌人_已肃清_下一层": "当前区域的敌人已被肃清！\n前方是【二层】……输入『深入』继续推进！",
    "B3_无敌人_已肃清_最后一层": "当前区域的敌人已被肃清！\n这是最后一层，输入『深入』挑战 Boss！",
    "B4_等待行动": "⏳ 现在是 队友甲 的刻，等待 TA 行动～",
    "B5_嘲讽结束": "……嘲讽效果结束，怪物恢复了本能仇恨！\n当前区域还有敌人潜伏！『探索』找到它们～",
    "B6_战斗异常": "战斗状态异常，请重新遭遇！",
    "B7_密室宝箱": "💥 房间怪 受到 1 点伤害，倒下了！\n  玩家：经验 +1，拾取材料 兽肉 ×1\n  玩家：🏆 成就解锁：初试锋芒！(完成首次战斗)\n      🎁 经验+100、兽肉×3（『成就 领取』领取）\n  玩家：🏆 成就解锁：初出茅庐！(注册角色)\n      🎁 草药×2（『成就 领取』领取）\n  玩家：🏆 成就解锁：崭露头角！(达到 10 级)\n      🎁 铁矿石×2（『成就 领取』领取）\n  玩家：🏆 成就解锁：名声鹊起！(达到 20 级)\n      🎁 精铁×2（『成就 领取』领取）\n  玩家：🏆 成就解锁：小有名气！(达到 30 级)\n      🎁 木箱×1（『成就 领取』领取）\n  玩家：🏆 成就解锁：资深冒险者！(达到 40 级)\n      🎁 淬火石×2（『成就 领取』领取）\n  玩家：🏆 成就解锁：大陆精英！(达到 50 级)\n      🎁 白银箱×1（『成就 领取』领取）\n  玩家：🏆 成就解锁：传奇之路！(达到 60 级)\n      🎁 白银箱×1、图纸残页×1（『成就 领取』领取）\n━━━━━━━━━━━━\n✅ 精英守卫被击败了！密室深处露出一口【神秘宝箱】……\n🔐 『调查 宝箱』看看里面藏着什么！",
    "B8_房间清空": "💥 房间怪 受到 1 点伤害，倒下了！\n  玩家：经验 +1，拾取材料 兽肉 ×1\n  玩家：🏆 成就解锁：初试锋芒！(完成首次战斗)\n      🎁 经验+100、兽肉×3（『成就 领取』领取）\n  玩家：🏆 成就解锁：初出茅庐！(注册角色)\n      🎁 草药×2（『成就 领取』领取）\n  玩家：🏆 成就解锁：崭露头角！(达到 10 级)\n      🎁 铁矿石×2（『成就 领取』领取）\n  玩家：🏆 成就解锁：名声鹊起！(达到 20 级)\n      🎁 精铁×2（『成就 领取』领取）\n  玩家：🏆 成就解锁：小有名气！(达到 30 级)\n      🎁 木箱×1（『成就 领取』领取）\n  玩家：🏆 成就解锁：资深冒险者！(达到 40 级)\n      🎁 淬火石×2（『成就 领取』领取）\n  玩家：🏆 成就解锁：大陆精英！(达到 50 级)\n      🎁 白银箱×1（『成就 领取』领取）\n  玩家：🏆 成就解锁：传奇之路！(达到 60 级)\n      🎁 白银箱×1、图纸残页×1（『成就 领取』领取）\n━━━━━━━━━━━━\n✅ 【misty_swamp_1】的敌人被肃清了！\n🗺️ 【哥布林营地】\n哥布林营地，传说中的危险之地，唯有勇者敢于踏入。\n💡 输入『副本 哥布林营地』开启挑战（组队副本，等级/人数校验）\n━━━━━━━━━━━━\n📍 当前位置：哥布林营地\n📮 可前往：\n  🧭 出城需先到『入口栅栏』\n💡 『前往 <序号>』切换位置\n━━━━━━━━━━━━\n🚪 副本内 · 无出口（没有通往外面的路）\n🐾 此房怪物已肃清。\n💡 专注战斗！『副本』查看进度\n━━━━━━━━━━━━\n🧭 副本内可继续探索/移动，或『副本』查看进度！",
    "B9_切怪": "💥 房间怪 受到 1 点伤害，倒下了！\n  玩家：经验 +1，拾取材料 兽肉 ×1\n  玩家：🏆 成就解锁：初试锋芒！(完成首次战斗)\n      🎁 经验+100、兽肉×3（『成就 领取』领取）\n  玩家：🏆 成就解锁：初出茅庐！(注册角色)\n      🎁 草药×2（『成就 领取』领取）\n  玩家：🏆 成就解锁：崭露头角！(达到 10 级)\n      🎁 铁矿石×2（『成就 领取』领取）\n  玩家：🏆 成就解锁：名声鹊起！(达到 20 级)\n      🎁 精铁×2（『成就 领取』领取）\n  玩家：🏆 成就解锁：小有名气！(达到 30 级)\n      🎁 木箱×1（『成就 领取』领取）\n  玩家：🏆 成就解锁：资深冒险者！(达到 40 级)\n      🎁 淬火石×2（『成就 领取』领取）\n  玩家：🏆 成就解锁：大陆精英！(达到 50 级)\n      🎁 白银箱×1（『成就 领取』领取）\n  玩家：🏆 成就解锁：传奇之路！(达到 60 级)\n      🎁 白银箱×1、图纸残页×1（『成就 领取』领取）\n━━━━━━━━━━━━\n⚔️ 又一只怪物挡在面前！\n── 敌方 ──\n  A1层: a1  史莱姆 ❤️465/465\n── 我方 ──\n  B2层: b1  玩家 ❤️500/500\n🕐 时刻 0.0s ｜ ⚡ 行动顺序：玩家(我) → 史莱姆(敌)\n✅ 玩家：❤️ 500/500 💙 50/50\n💡 选敌：『技能1 a2』打2号(纯数字同义)；治疗『技能 <名称> b1』奶自己\n⏳ 轮到 玩家 行动！『攻击』『技能 <名称>』『防御』",
    "B10_层清空": "💥 房间怪 受到 1 点伤害，倒下了！\n  玩家：经验 +1，拾取材料 兽肉 ×1\n  玩家：🏆 成就解锁：初试锋芒！(完成首次战斗)\n      🎁 经验+100、兽肉×3（『成就 领取』领取）\n  玩家：🏆 成就解锁：初出茅庐！(注册角色)\n      🎁 草药×2（『成就 领取』领取）\n  玩家：🏆 成就解锁：崭露头角！(达到 10 级)\n      🎁 铁矿石×2（『成就 领取』领取）\n  玩家：🏆 成就解锁：名声鹊起！(达到 20 级)\n      🎁 精铁×2（『成就 领取』领取）\n  玩家：🏆 成就解锁：小有名气！(达到 30 级)\n      🎁 木箱×1（『成就 领取』领取）\n  玩家：🏆 成就解锁：资深冒险者！(达到 40 级)\n      🎁 淬火石×2（『成就 领取』领取）\n  玩家：🏆 成就解锁：大陆精英！(达到 50 级)\n      🎁 白银箱×1（『成就 领取』领取）\n  玩家：🏆 成就解锁：传奇之路！(达到 60 级)\n      🎁 白银箱×1、图纸残页×1（『成就 领取』领取）\n━━━━━━━━━━━━\n✅ 【一层】的敌人被肃清了！\n🗺️ 【👺哥布林营地】第 1 层 · 一层\n━━━━━━━━━━━━\n📜 你环顾四周，准备迎接这里的敌人。\n━━━━━━━━━━━━\n✨ 场景：\n  []\n  []\n━━━━━━━━━━━━\n✅ 本层敌人已肃清！『深入』前往下一层。\n━━━━━━━━━━━━\n💡 『副本』查看战况，『角色』看队伍\n━━━━━━━━━━━━\n🧭 前方是【二层】……输入『深入』继续推进！",
    "B11_普通轮转": "💥 房间怪 受到 463 点伤害！\n—— 房间怪 行动 ——\n💥 玩家 受到 1 点伤害！\n━━━━━━━━━━━━\n── 敌方 ──\n  A1层: a1  房间怪 ❤️4537/5000\n── 我方 ──\n  B2层: b1  玩家 ❤️499/500\n🕐 时刻 1.1s ｜ ⚡ 行动顺序：玩家(我) → 房间怪(敌)\n✅ 玩家：❤️ 499/500 💙 50/50\n💡 选敌：『技能1 a2』打2号(纯数字同义)；治疗『技能 <名称> b1』奶自己\n⏳ 轮到 玩家 行动！『攻击』『技能 <名称>』『防御』",
}

_GID, _QID = "g_txt", "q_txt"
_SID = "g_si"


async def _inv(m, name, msg):
    ev = FakeEvent(_GID, _QID, msg)
    res = await run(getattr(m, name), ev)
    return res[-1] if res else ""


async def _weekly_scenarios() -> dict:
    """复跑迁移前的 6 个分支（步骤与快照脚本逐行一致）。"""
    clean_db()
    m = Main(None)
    out = {}
    db.create_player(_GID, _QID, "文案", C.resolve("classes", "战士"), {}, 100, 100)
    db.update_player(_GID, _QID, level=49, stamina=100)
    out["A_locked"] = await _inv(m, "weekly_cmd", "周常")
    db.update_player(_GID, _QID, level=50, stamina=100)
    out["B_first"] = await _inv(m, "weekly_cmd", "周常")
    st = dict(_week_state(_QID) or {})
    tasks = st.get("tasks") or {}
    for i, (tn, t) in enumerate(tasks.items()):
        t["prog"] = 1 if i == 0 else 0
        t["done"] = (i == 0)
    st["done_n"] = 1 if tasks else 0
    _save_week_state(_QID, st)
    out["C_progress"] = await _inv(m, "weekly_cmd", "周常")
    out["D_pool_p1"] = await _inv(m, "weekly_list", "周常列表")
    out["E_pool_p2"] = await _inv(m, "weekly_list", "周常列表 2")
    st2 = dict(_week_state(_QID) or {})
    for t in (st2.get("tasks") or {}).values():
        t["done"] = True
        t["prog"] = int(t.get("need") or 1)
    st2["done_n"] = len(st2.get("tasks") or {})
    _save_week_state(_QID, st2)
    out["F_all_done"] = await _inv(m, "weekly_cmd", "周常")
    clean_db()
    return out


async def _signin_scenarios() -> dict:
    """复跑『签到』迁移前的 5 个分支（步骤与快照脚本逐行一致；random 打桩保证可复现）。"""
    clean_db()
    m = Main(None)
    out = {}
    _rnd = random.random

    def _mk(qid):
        db.create_player(_SID, qid, "签到", C.resolve("classes", "战士"), {}, 100, 100)
        db.update_player(_SID, qid, level=10, gold=1000)

    async def _sign(qid):
        ev = FakeEvent(_SID, qid, "签到")
        res = await run(m.signin, ev)
        return res[-1] if res else ""

    def _pre(qid, days):
        today = datetime.date.today()
        for i in range(days, 0, -1):
            d = today - datetime.timedelta(days=i)
            db.signin_claim(_SID, qid, d.isoformat(),
                            (d - datetime.timedelta(days=1)).isoformat())

    try:
        _mk("q_a")
        random.seed(42)
        random.random = lambda: 0.05          # < fortune_bad_th 0.15 → 小凶
        out["A_first_bad"] = await _sign("q_a")
        _mk("q_b")
        random.seed(42)
        random.random = lambda: 0.9           # ≥ 0.55 → 大吉
        out["B_first_big"] = await _sign("q_b")
        out["C_dup"] = await _sign("q_b")     # 同人再签 → 已签分支
        _mk("q_d")
        _pre("q_d", 6)                        # 昨天刚签 + 连续 6 天 → 本次第 7 天
        random.seed(7)
        random.random = lambda: 0.9
        out["D_streak7"] = await _sign("q_d")
        _mk("q_e")
        db.save_world_event("festival", int(time.time()) + 86400, {"name": "测试庆典"})
        random.seed(42)
        random.random = lambda: 0.9
        out["E_festival"] = await _sign("q_e")
        db.clear_world_event()
    finally:
        random.random = _rnd
        clean_db()
    return out


async def _supply_scenarios() -> dict:
    """复跑『领取补给箱』迁移前的 3 个分支（步骤与快照脚本逐行一致）。"""
    clean_db()
    m = Main(None)
    db.create_player("g_sp", "q_sp", "补给", C.resolve("classes", "战士"), {}, 100, 100)
    out = {}
    for k in ("A_first", "B_second", "C_third"):
        ev = FakeEvent("g_sp", "q_sp", "领取补给箱")
        res = await run(m.event_menu, ev)
        out[k] = res[-1] if res else ""
    clean_db()
    return out


def _strip_tips(text):
    """剔掉面板底部随机提示行（`💡 ` 开头的整行）——提示池随机抽，不属于任何域。"""
    return "\n".join(ln for ln in (text or "").splitlines() if not ln.startswith("💡 "))


async def _daily_scenarios() -> dict:
    """复跑『任务』面板的 4 个状态（步骤与快照脚本逐行一致）。"""
    today = datetime.date.today().isoformat()
    base = {"main_quest": "", "main_status": "", "main_progress": {},
            "completed_main": [], "side": {}}
    states = {
        "A_never": {},
        "B_active": {"边境警戒": {"name": "边境警戒", "desc": "击杀 10 只任意怪物",
                                "objective": {"kill_any": 10}, "progress": 3},
                     "神秘委托": {"name": "神秘委托", "desc": "未知目标（无达标数定义）",
                                "objective": {"mystery": "?"}, "progress": 1},
                     "_date": today, "_completed": 0},
        "C_done_part": {"_date": today, "_completed": 2},
        "D_done_full": {"_date": today, "_completed": 10},
    }
    clean_db()
    m = Main(None)
    db.create_player("g_dl", "q_dl", "每日", C.resolve("classes", "战士"), {}, 100, 100)
    out = {}
    for k, daily in states.items():
        st = dict(base)
        st["daily"] = daily
        db.save_quests("g_dl", "q_dl", st)
        ev = FakeEvent("g_dl", "q_dl", "任务")
        res = await run(m.quest_view, ev)
        out[k] = res[-1] if res else ""
    clean_db()
    return out


async def _quests_scenarios() -> dict:
    """复跑『每日』命令（services/quests.py）的 7 个分支（步骤与快照脚本逐行一致）。"""
    from data.plugins.dragonfall.game.services.quests import (
        draw_daily, settle_daily_quest, DAILY_LIMIT as _LIM,
    )
    today = datetime.date.today().isoformat()
    base = {"main_quest": "", "main_status": "", "main_progress": {},
            "completed_main": [], "side": {}}

    def _st(daily):
        st = dict(base)
        st["daily"] = daily
        return st

    clean_db()
    m = Main(None)
    db.create_player("g_dq", "q_dq", "每日", C.resolve("classes", "战士"), {}, 100, 100)
    p = db.get_player("g_dq", "q_dq")
    out = {}
    random.seed(11)
    ok, text = draw_daily("g_dq", "q_dq", p)
    out["A_publish"] = ("ok=%s\n" % ok) + text
    ok, text = draw_daily("g_dq", "q_dq", p)
    out["B_have"] = ("ok=%s\n" % ok) + text
    db.save_quests("g_dq", "q_dq", _st({"_date": today, "_completed": _LIM}))
    ok, text = draw_daily("g_dq", "q_dq", p)
    out["C_limit"] = ("ok=%s\n" % ok) + text
    db.save_quests("g_dq", "q_dq", _st({"_date": today, "_completed": 3, "_repeat": {}}))
    random.seed(11)
    ok, text = draw_daily("g_dq", "q_dq", p)
    out["D_republish"] = ("ok=%s\n" % ok) + text
    rep_all = {q["name"]: 1 for q in C.DAILY_QUESTS}
    db.save_quests("g_dq", "q_dq", _st({"_date": today, "_completed": 0, "_repeat": rep_all}))
    random.seed(11)
    ok, text = draw_daily("g_dq", "q_dq", p)
    out["E_decay"] = ("ok=%s\n" % ok) + text
    lines = []
    dq = {"name": "边境警戒", "desc": "击杀 10 只任意怪物", "objective": {"kill_any": 10},
          "reward_exp": 100, "reward_gold": 50, "repeat": 0}
    settle_daily_quest("g_dq", "q_dq", {"_completed": 0, "_repeat": {}}, dq, lines)
    out["F_settle"] = "\n".join(lines)
    lines2 = []
    settle_daily_quest("g_dq", "q_dq", {"_completed": 0, "_repeat": {"边境警戒": 1}},
                       dict(dq, repeat=1), lines2)
    out["G_settle_decay"] = "\n".join(lines2)
    clean_db()
    return out


# ══════════════════════════════════════════════════════════════════════════
# 副本结算域复跑器（`game/commands/instance_router.py`）—— 与迁移前快照脚本逐行一致
# ══════════════════════════════════════════════════════════════════════════
_IS_GID = "g_settle"


class _ISHost(_InstCmds, _CombatCmds, _WorldCmds):
    """router 测试宿主（InstanceCmds 玩法壳 + CombatCmds + WorldCmds 地图视图）。"""


def _is_mk_snap(qid, name="玩家", cls="战士", level=60):
    db.create_player(_IS_GID, qid, name, cls, {}, 100, 100)
    db.update_player(_IS_GID, qid, level=level, cur_map="mainland", cur_subarea="", stamina=999)
    pl = db.get_player(_IS_GID, qid)
    return {"name": name, "qq_id": qid, "class_name": cls, "level": level,
            "hp": 500, "max_hp": 500, "mp": 50, "max_mp": 50, "equipment": {},
            "skills": [], "learned_skills": [], "class_tier": 0, "evolve_path": 0,
            "attributes": pl.get("attributes"), "bonus": {"panel": {}, "cap": {}, "cost": {}},
            "race": pl.get("race"), "uid": "p_%s" % qid, "buffs": {}, "stacks": {},
            "defending": False, "charging": None, "ct": 0.0, "p_shields": {}, "spd": 30}


def _is_mk_enemy(hp=1, spd=1, role="dps", atk=1, uid="e_room", name="房间怪"):
    return {"uid": uid, "name": name, "hp": hp, "max_hp": hp, "atk": atk, "def": 0,
            "matk": 1, "mdef": 0, "spd": spd, "crit": 0.0, "lv": 15, "level": 15,
            "role": role, "is_boss": role == "boss", "is_elite": role == "elite",
            "rank": 1, "reach": 1, "ct": 1.0, "exp": 10, "gold": 5, "drops": []}


def _is_mk_st(qids, inst_id="inst_goblin_camp", names=None, **kw):
    qids = [str(q) for q in qids]
    names = names or {}
    st = {"type": "instance", "inst_id": inst_id, "leader": qids[0], "members": qids,
          "alive": {q: True for q in qids},
          "players": {q: _is_mk_snap(q, names.get(q, "玩家")) for q in qids},
          "boss": None, "enemy": None, "enemies": [], "turn": 0, "round": 1,
          "mode": "battle", "pets": {}, "p_buffs": {q: {} for q in qids},
          "p_hot": {q: {} for q in qids}, "p_food_effects": {q: [] for q in qids},
          "p_defending": {q: False for q in qids}, "mech_stacks": {q: {} for q in qids},
          "now": 0.0, "battle": None, "contribution": {},
          "threat": {q: 0 for q in qids}, "over": False, "turn_time": 0,
          "stage_pending": [], "inst_stages": [], "stage_idx": 0,
          "stage_cleared": False, "world_id": ""}
    st.update(kw)
    return st


def _is_patch_cm(all_members):
    """多人副本 st 无 party 行时，current_members 恒返回全部成员（等价单人/测试口径）。"""
    orig = _InstCmds._instance_current_members
    _InstCmds._instance_current_members = (
        lambda self, gid, st: [str(m) for m in (all_members or st["members"])])
    return orig


def _is_restore_cm(orig):
    _InstCmds._instance_current_members = orig


def _is_run(inst, st, qq, action, skill=None, target=None):
    """跑一次 router（同步收全部 yield）。"""
    player = st["players"][str(qq)]
    agen = inst._instance_router(FakeEvent(_IS_GID, str(qq)), _IS_GID, str(qq), player,
                                 st, action, skill, target)

    async def _c():
        out = []
        async for x in agen:
            out.append(x)
        return out
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_c())
    finally:
        loop.close()


def _is_now():
    return int(time.time())


def _is_b1_no_enemy_pending():
    """L56 探索引导。"""
    clean_db()
    st = _is_mk_st(["q_b1"])
    st["stage_pending"] = [["m_x", "小怪", "dps", 15, [], []]]
    return _is_run(_ISHost(), st, "q_b1", "attack")


def _is_b2_no_enemy_next_stage():
    """L64 肃清 + L61 下一层行（非末层）。"""
    clean_db()
    st = _is_mk_st(["q_b2"], inst_stages=[{"name": "一层"}, {"name": "二层"}], stage_idx=0)
    return _is_run(_ISHost(), st, "q_b2", "attack")


def _is_b3_no_enemy_last_stage():
    """L64 肃清 + L63 最后一层行（末层）。"""
    clean_db()
    st = _is_mk_st(["q_b3"], inst_stages=[{"name": "一层"}, {"name": "二层"}], stage_idx=1)
    return _is_run(_ISHost(), st, "q_b3", "attack")


def _is_b4_wait_hint():
    """L73 现在是 X 的刻（非请求者未超时）。"""
    clean_db()
    st = _is_mk_st(["q_b41", "q_b42"], names={"q_b41": "队友甲", "q_b42": "请求者乙"},
                   enemies=[_is_mk_enemy(hp=500, spd=1)])
    st["boss"] = st["enemies"][0]
    st["enemy"] = st["enemies"][0]
    _IB.build_battle(st)
    for a in (_IB._players_of(st) or []):
        a["ct"] = 0.0 if str(a.get("qq_id")) == "q_b41" else 50.0
    _IB.sync_views(st, _IS_GID)
    st["turn_time"] = _is_now()
    orig = _is_patch_cm(["q_b41", "q_b42"])
    try:
        return _is_run(_ISHost(), st, "q_b42", "attack")
    finally:
        _is_restore_cm(orig)


def _is_b5_taunt_end():
    """L145 嘲讽结束（taunt_left 递减到 0）。"""
    clean_db()
    st = _is_mk_st(["q_b5"])
    st["taunt_left"] = 1
    st["taunt_target"] = "q_b5"
    st["stage_pending"] = [["m_x", "小怪", "dps", 15, [], []]]
    return _is_run(_ISHost(), st, "q_b5", "attack")


def _is_b6_battle_broken():
    """L172 战斗状态异常 —— 桩：让 build_battle 抛错（真实链路只能靠引擎内部失败触发）。"""
    clean_db()
    st = _is_mk_st(["q_b6"], enemies=[_is_mk_enemy(hp=1, spd=1)])
    orig = _IB.build_battle

    def _boom(_st):
        raise RuntimeError("snapshot-stub: build_battle boom")
    _IB.build_battle = _boom
    try:
        return _is_run(_ISHost(), st, "q_b6", "attack")
    finally:
        _IB.build_battle = orig


def _is_b7_secret_guard():
    """L326 密室精英守卫被击败 → 宝箱。"""
    clean_db()
    random.seed(20260912 + 7)
    st = _is_mk_st(["q_b7"], secret_guard_pending=True, mode="battle")
    st["enemies"] = [_is_mk_enemy(hp=1, spd=1)]
    st["boss"] = st["enemies"][0]
    st["enemy"] = st["enemies"][0]
    _IB.build_battle(st)
    inst = _ISHost()
    msgs = []
    for _ in range(8):
        st["turn_time"] = _is_now()
        msgs += _is_run(inst, st, "q_b7", "attack")
        if st.get("secret_chest") or not st.get("enemies"):
            break
    return msgs


def _is_b8_room_clear():
    """L383 房间怪清空（非 Boss 房 → 回地图模式）。"""
    clean_db()
    random.seed(20260912 + 8)
    qid, cur_sa = "q_b8", "goblin_camp_1"
    st = _is_mk_st([qid], rooms={cur_sa: {"monsters_left": [], "pois_left": [],
                                          "boss_alive": False}})
    st["enemies"] = [_is_mk_enemy(hp=1, spd=1)]
    st["boss"] = st["enemies"][0]
    st["enemy"] = st["enemies"][0]
    db.update_player(_IS_GID, qid, cur_map="misty_swamp", cur_subarea=cur_sa)
    _IB.build_battle(st)
    inst = _ISHost()
    msgs = []
    for _ in range(8):
        st["turn_time"] = _is_now()
        msgs += _is_run(inst, st, qid, "attack")
        if st.get("cleared") or st.get("over") or not st.get("enemies"):
            break
    return msgs


def _is_b9_switch_monster():
    """L418 切怪（stage_pending 剩怪）+ L424 轮到 X 行动。"""
    clean_db()
    random.seed(20260912 + 9)
    st = _is_mk_st(["q_b9"], stage_pending=[["m_slime", "史莱姆", "dps", 15, [], []],
                                            ["m_slime2", "史莱姆2", "dps", 15, [], []]])
    st["enemies"] = [_is_mk_enemy(hp=1, spd=1)]
    st["boss"] = st["enemies"][0]
    st["enemy"] = st["enemies"][0]
    _IB.build_battle(st)
    inst = _ISHost()
    msgs = []
    for _ in range(8):
        st["turn_time"] = _is_now()
        msgs += _is_run(inst, st, "q_b9", "attack")
        if "⚔️ 又一只怪物挡在面前！" in "\n".join(msgs):
            break
    return msgs


def _is_b10_stage_cleared():
    """L441 分层清空（非末层）+ L448 前方是 X。"""
    clean_db()
    random.seed(20260912 + 10)
    st = _is_mk_st(["q_b10"], inst_stages=[{"name": "一层"}, {"name": "二层"}], stage_idx=0)
    st["enemies"] = [_is_mk_enemy(hp=1, spd=1)]
    st["boss"] = st["enemies"][0]
    st["enemy"] = st["enemies"][0]
    _IB.build_battle(st)
    inst = _ISHost()
    msgs = []
    for _ in range(8):
        st["turn_time"] = _is_now()
        msgs += _is_run(inst, st, "q_b10", "attack")
        if "的敌人被肃清了" in "\n".join(msgs):
            break
    return msgs


def _is_b11_normal_rotation():
    """L475 普通轮转（未结束 → footer + 轮到 X）。"""
    clean_db()
    random.seed(20260912 + 11)
    st = _is_mk_st(["q_b11"])
    st["enemies"] = [_is_mk_enemy(hp=5000, spd=1)]
    st["boss"] = st["enemies"][0]
    st["enemy"] = st["enemies"][0]
    _IB.build_battle(st)
    st["turn_time"] = _is_now()
    return _is_run(_ISHost(), st, "q_b11", "attack")


_IS_BRANCHES = (("B1_无敌人_探索", _is_b1_no_enemy_pending),
                ("B2_无敌人_已肃清_下一层", _is_b2_no_enemy_next_stage),
                ("B3_无敌人_已肃清_最后一层", _is_b3_no_enemy_last_stage),
                ("B4_等待行动", _is_b4_wait_hint),
                ("B5_嘲讽结束", _is_b5_taunt_end),
                ("B6_战斗异常", _is_b6_battle_broken),
                ("B7_密室宝箱", _is_b7_secret_guard),
                ("B8_房间清空", _is_b8_room_clear),
                ("B9_切怪", _is_b9_switch_monster),
                ("B10_层清空", _is_b10_stage_cleared),
                ("B11_普通轮转", _is_b11_normal_rotation))


def _instance_settle_scenarios() -> dict:
    """复跑迁移前的 11 个副本结算分支（步骤与快照脚本逐行一致）。"""
    out = {}
    for name, fn in _IS_BRANCHES:
        msgs = fn()
        out[name] = "\n".join(str(m) for m in msgs) if not isinstance(msgs, str) else msgs
    return out


# ══════════════════════════════════════════════════════════════════════════
def _scan_calls(path):
    """AST 扫模块：

    ① `T.text("k", **kw)` / `T.static("k")` → (key, frozenset(kwarg 名), kind)（直接调用点）
    ② 模块里出现过的字符串字面量集合 → 「键在映射表里」这类用法（如运势键 → 文案键的 dict）
       也算被引用，否则会被当成死文案误报。

    ②只用于「有没有引用」，槽位对账仍只认①的直接调用实参。
    """
    tree = ast.parse(io.open(path, encoding="utf-8").read())
    calls, lits = [], set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            lits.add(node.value)
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in ("text", "static")
                and isinstance(node.func.value, ast.Name) and node.func.value.id == "T"):
            k = node.args[0].value if (node.args and isinstance(node.args[0], ast.Constant)) else None
            if k is None:
                continue          # 动态键（如 T.static(_FORTUNE_TEXT.get(fortune))）静态扫不出：
                                  # 交给②「字面量也算引用」兜，避免误报成「调用了未声明的 None」
            calls.append((k, frozenset(kw.arg for kw in node.keywords if kw.arg), node.func.attr))
    return calls, lits


def t1_table_selfcheck():
    print("\n[1] 装载与自检（引擎 validate/audit）")
    tb = T.reload()
    check("声明文件存在且路径正确", os.path.exists(SPEC) and SPEC.endswith("text_specs.json"), SPEC)
    check("装载无错（load_error 为空）", T.load_error() == "", T.load_error())
    check("表非空（91 条：副本准入 26 + 副本结算 14 + 签到 10 + 周常 18 + 补给箱 7 + 每日任务 7 + 每日命令 9）", len(tb) >= 40, len(tb))
    check("★ validate() 干净（无空值/语法错/params 与模板不一致）",
          tb.audit()["problems"] == [], tb.audit()["problems"][:5])
    check("元信息键（_ 开头）不入表", not [k for k in tb.keys() if k.startswith("_")], tb.keys()[:3])
    check("每条都有 category（编辑器分组用）",
          not [s.key for s in tb if not s.category], [s.key for s in tb if not s.category][:5])
    check("key 无重复", len(tb.keys()) == len(set(tb.keys())))
    cats = sorted({s.category for s in tb})
    check("category 取值符合预期（副本准入 / 签到 / 周常 / 补给箱 / 每日任务）",
          set(cats) == {"副本准入", "签到", "周常", "补给箱", "每日任务"}, cats)


def t2_key_and_params_accounting():
    print("\n[2] 声明 ↔ 调用点对账（双向；AST 扫真实调用）")
    declared = set(T.table().keys())
    used, mismatch, lits = set(), [], set()
    for name, path in WIRED.items():
        calls, l = _scan_calls(path)
        lits |= (l & declared)
        for key, kwargs, kind in calls:
            used.add(key)
            spec = T.table().spec(key)
            if spec is None:
                mismatch.append("%s: 调用了未声明的 %s" % (os.path.basename(path), key))
                continue
            slots = set(spec.slots)                       # 声明优先，缺省自动抽取
            if kind == "static" and kwargs:
                mismatch.append("%s: T.static(%s) 不该带槽位" % (os.path.basename(path), key))
            if set(kwargs) != slots:
                mismatch.append("%s: %s 槽位不符（调用 %s / 声明 %s）"
                                % (os.path.basename(path), key, sorted(kwargs), sorted(slots)))
    used |= lits                                          # 映射表里的键也算被引用
    check("★ 代码里每一处调用都能在表里找到（否则运行时缺 key）", not mismatch, mismatch[:5])
    dead = sorted(declared - used)
    check("★ 表里没有死文案（每条声明都被真实调用）", not dead, dead)
    check("★ 槽位名与调用实参逐条对得上（防模板写出 {foo} 露给玩家）", not mismatch)
    doms = {k.split(".")[0] for k in used}
    check("调用点覆盖全部已迁移域（副本准入 + 副本结算 + 周常 + 签到 + 补给箱 + 每日任务 + 每日命令）",
          {"instance", "weekly", "signin", "supply", "daily", "quests"} <= doms,
          sorted(doms))


def t3_no_silent_fallback():
    print("\n[3] 缺 key 不静默（不打回旧串、不吞成空串）")
    tb = T.table()
    got = tb.render("nope.not_declared")
    check("★ 未声明的 key → 返回 key 本身（玩家/日志双可见）", got == "nope.not_declared", repr(got))
    check("★ 记账：missing() 记下了这个缺 key", "nope.not_declared" in tb.missing(), tb.missing())
    tb.reset_stats()

    # 坏声明文件：不抛、不静默，空表 + 错误可见
    bad = os.path.join(os.environ.get("LOCALAPPDATA", _HERE), "Temp", "_bad_text_specs.json")
    with io.open(bad, "w", encoding="utf-8") as fh:
        fh.write("{ this is not json ")
    real = T.SPEC_PATH
    try:
        T.SPEC_PATH = bad
        T.reload()
        check("★ 声明文件语法坏 → 不抛异常，且 load_error 有原因",
              bool(T.load_error()), T.load_error())
        check("★ 坏文件下渲染不静默（返回 key，不是空串）",
              T.text("instance.leader_only") == "instance.leader_only")
    finally:
        T.SPEC_PATH = real
        T.reload()
    os.remove(bad)
    check("恢复正常声明后表重建（91 条）", len(T.table()) >= 40, len(T.table()))


def t4_weekly_frozen():
    print("\n[4] 周常域逐字冻结：迁移前 6 分支行为快照复跑比对")
    check("冻结基准已内嵌（6 场景）", len(WEEKLY_FROZEN) == 6, len(WEEKLY_FROZEN))
    now = asyncio.run(_weekly_scenarios())
    bad = [k for k in WEEKLY_FROZEN if WEEKLY_FROZEN[k] != now.get(k)]
    for k in bad:
        print("     · %s 现=%r" % (k, now.get(k, "")[:120]))
    check("★ 周常『周常』『周常列表』6 分支输出与迁移前**逐字一致**", not bad, bad)
    check("冻结基准非空且含换行结构（防基准写空）",
          all(v and "\n" in v for v in WEEKLY_FROZEN.values()))


def t5_signin_frozen():
    print("\n[5] 签到域逐字冻结：迁移前 5 分支行为快照复跑比对")
    check("冻结基准已内嵌（5 场景）", len(SIGNIN_FROZEN) == 5, len(SIGNIN_FROZEN))
    now = asyncio.run(_signin_scenarios())
    bad = [k for k in SIGNIN_FROZEN if SIGNIN_FROZEN[k] != now.get(k)]
    for k in bad:
        print("     · %s 现=%r" % (k, now.get(k, "")[:120]))
    check("★『签到』5 分支输出与迁移前**逐字一致**", not bad, bad)


def t6_supply_frozen():
    print("\n[6] 补给箱域逐字冻结：迁移前 3 分支（首发/日限/周限）复跑比对")
    check("冻结基准已内嵌（3 场景）", len(SUPPLY_FROZEN) == 3, len(SUPPLY_FROZEN))
    now = asyncio.run(_supply_scenarios())
    bad = [k for k in SUPPLY_FROZEN if SUPPLY_FROZEN[k] != now.get(k)]
    for k in bad:
        print("     · %s 现=%r" % (k, now.get(k, "")[:120]))
    check("★『领取补给箱』3 分支输出与迁移前**逐字一致**", not bad, bad)


def t7_daily_frozen():
    print("\n[7] 每日任务域（任务面板段）逐字冻结：4 状态复跑比对（剔除随机提示行）")
    check("冻结基准已内嵌（4 状态）", len(DAILY_FROZEN) == 4, len(DAILY_FROZEN))
    now = asyncio.run(_daily_scenarios())
    bad = [k for k in DAILY_FROZEN if _strip_tips(DAILY_FROZEN[k]) != _strip_tips(now.get(k))]
    for k in bad:
        print("     · %s 现=%r" % (k, _strip_tips(now.get(k, ""))[:140]))
    check("★『任务』面板每日段 4 状态输出与迁移前**逐字一致**（随机提示行除外）", not bad, bad)


def t8_quests_frozen():
    print("\n[8] 每日任务域后半（『每日』命令）逐字冻结：7 分支复跑比对")
    check("冻结基准已内嵌（7 分支）", len(QUEST_FROZEN) == 7, len(QUEST_FROZEN))
    now = asyncio.run(_quests_scenarios())
    bad = [k for k in QUEST_FROZEN if QUEST_FROZEN[k] != now.get(k)]
    for k in bad:
        print("     · %s 现=%r" % (k, (now.get(k) or "")[:140]))
    check("★『每日』命令 7 分支（首发/已有/满额/重抽/衰减/达标/重复达标）与迁移前**逐字一致**",
          not bad, bad)


def t9_instance_settle_frozen():
    print("\n[9] 副本结算域逐字冻结：迁移前 11 分支（探索/肃清/等待/嘲讽/异常/密室/房间/切怪/层/轮转）复跑比对")
    check("冻结基准已内嵌（11 分支）", len(INSTANCE_SETTLE_FROZEN) == 11,
          len(INSTANCE_SETTLE_FROZEN))
    now = _instance_settle_scenarios()
    bad = [k for k in INSTANCE_SETTLE_FROZEN if INSTANCE_SETTLE_FROZEN[k] != now.get(k)]
    for k in bad:
        print("     · %s 现=%r" % (k, (now.get(k) or "")[:140]))
    check("★ 副本结算 11 分支输出与迁移前**逐字一致**", not bad, bad)
    _single = ("B1_无敌人_探索", "B4_等待行动", "B6_战斗异常")   # 单行分支（本身无换行结构）
    check("冻结基准非空且含换行结构（防基准写空）",
          all(v and "\n" in v for k, v in INSTANCE_SETTLE_FROZEN.items() if k not in _single))


def main():
    print("=" * 74)
    print("文案表门禁：game/data/text_specs.json + game/core/texts.py")
    print("=" * 74)
    t1_table_selfcheck()
    t2_key_and_params_accounting()
    t3_no_silent_fallback()
    t4_weekly_frozen()
    t5_signin_frozen()
    t6_supply_frozen()
    t7_daily_frozen()
    t8_quests_frozen()
    t9_instance_settle_frozen()
    print("\n" + "=" * 74)
    print("结果：通过 %d / %d" % (passed, passed + failed))
    print("=" * 74)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
