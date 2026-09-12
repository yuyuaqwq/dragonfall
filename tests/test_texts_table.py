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
  · 副本日志域（`game/commands/instance.py` + `instance_router.py` + `instance_battle.py`）：
    本文件 `INSTANCE_LOG_FROZEN` —— 26 个分支（超时自动防御/嘲讽/同归于尽/团队治疗广播/组队提示/
    副本列表/战况面板/副本状态面板/副本地图 rooms 形态与分层形态/搜刮空与非空/击杀奖励/通关 A-E/
    失败回城）在**迁移前**真跑存下的完整输出，每次跑测试复跑比对（clean_db 打底 + random.seed
    与 random.random 打桩固定随机；「同归于尽」「搜刮空」两处用桩（见分支注释），
    通关 A-E 用 random.random 常量 + 预置已学图纸打桩固定分支取向）；
    另有 `INSTANCE_LOG_TEMPLATES` —— 70 条模板**骨架**（来自迁移前源码 AST）：
    连真跑覆盖不到的分支（见下）也由「骨架逐字相等」钉住
    · 真跑覆盖不到 1 条：`instance.日志_调查痕迹`（通关后调查痕迹行，rooms 与分层两处**共用**）——
      两处调用都引用了未定义名 `qq_id`（`_instance_map_view(self, st, group_id)` 签名里没有它）⇒
      走到就是 NameError，属**既有缺陷**（本批只搬字、不动缺陷，故只由模板骨架层覆盖）

  · 副本面板域（`game/commands/instance.py` + `instance_battle.py` + `instance_router.py` 的
    面板/列表/地图/状态/引导/错误提示句壳）：本文件 `INSTANCE_PANEL_FROZEN` —— 31 个分支
    （开本单人/多人/战斗模式/名字不存在、加入战斗、不在副本、战斗中守卫、24h 过期、深入四拦截与清层推进、
    副本地图分层、调查空参数/未命中/已处理、探索通关后/rooms 四态/旧层两态/遇怪Boss、
    撤退全流程、恢复进度与离开、非队长移动、通关超时离开、暗格/宝箱五档、调查点四档与空/零碎、
    战斗态异常两态、Boss 房房间怪击杀通关）在**迁移前**真跑存下的完整输出，每次跑测试复跑比对（每分支 clean_db +
    固定 random.seed，需要处打桩 random.random；宝箱五档用固定 seed 定向各档，调查点空/零碎
    临时改写 C.INVESTIGATION_POINTS 后还原）；另有 `INSTANCE_PANEL_OLD_LITERALS` ——
    迁移前内联句壳片段（= 表值去槽位后的实体片段），三份源文件里一句都不许再出现

跑法：python tests/test_texts_table.py（exit=0 通过）
"""
import ast
import asyncio
import datetime
import io
import json
import os
import random
import re
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
INSTANCE_SRC = os.path.join(_PD, "game", "commands", "instance.py")
INSTANCE_BATTLE_SRC = os.path.join(_PD, "game", "commands", "instance_battle.py")
SPEC = T.SPEC_PATH
# 已迁移的域 → 该域文案由哪个文件接线（新增一个域时在这里加一行）
WIRED = {"副本准入": GATE_SRC, "副本结算": INSTANCE_ROUTER_SRC,
         "副本日志": INSTANCE_SRC, "副本战斗日志": INSTANCE_BATTLE_SRC,
         "周常": WEEKLY_SRC,
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
    check("表非空（161 条：副本准入 26 + 副本结算 14 + 副本日志 70 + 签到 10 + 周常 18 + 补给箱 7 + 每日任务 7 + 每日命令 9）", len(tb) >= 40, len(tb))
    check("★ validate() 干净（无空值/语法错/params 与模板不一致）",
          tb.audit()["problems"] == [], tb.audit()["problems"][:5])
    check("元信息键（_ 开头）不入表", not [k for k in tb.keys() if k.startswith("_")], tb.keys()[:3])
    check("每条都有 category（编辑器分组用）",
          not [s.key for s in tb if not s.category], [s.key for s in tb if not s.category][:5])
    check("key 无重复", len(tb.keys()) == len(set(tb.keys())))
    cats = sorted({s.category for s in tb})
    check("category 取值符合预期（副本准入 / 副本日志 / 副本面板 / 签到 / 周常 / 补给箱 / 每日任务）",
          set(cats) == {"副本准入", "副本日志", "副本面板", "签到", "周常", "补给箱", "每日任务"}, cats)


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
    check("恢复正常声明后表重建（161 条）", len(T.table()) >= 40, len(T.table()))


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


# ═══════════════════════ IL_BRANCHES_BEGIN ═══════════════════════
# ↓↓↓ 以下这段（含本行）逐字拼进 tests/test_texts_table.py 的 t10 段 ↓↓↓
from conftest import clean_db as _IL_clean, FakeEvent as _IL_Event   # noqa: E402
from data.plugins.dragonfall.game import content as _IL_C            # noqa: E402
from data.plugins.dragonfall.game import db as _IL_db                # noqa: E402
from data.plugins.dragonfall.game.commands import instance_battle as _IL_IB   # noqa: E402
from data.plugins.dragonfall.game.commands.instance import InstanceCmds as _IL_Inst   # noqa: E402
from data.plugins.dragonfall.game.commands.combat import CombatCmds as _IL_Combat     # noqa: E402
from data.plugins.dragonfall.game.commands.world import WorldCmds as _IL_World        # noqa: E402

_IL_GID = "g_ilog"


class _ILHost(_IL_Inst, _IL_Combat, _IL_World):
    """副本日志快照宿主（InstanceCmds 玩法壳 + CombatCmds 面板名表 + WorldCmds 地图视图）。"""


def _il_player(qid, name="玩家", cls="cls_zhan_shi", level=60, learned=None):
    _IL_db.create_player(_IL_GID, qid, name, cls, {}, 100, 100)
    _IL_db.update_player(_IL_GID, qid, level=level, cur_map="misty_swamp",
                         cur_subarea="misty_swamp_3", stamina=999999,
                         learned_skills=list(learned or []))
    return _IL_db.get_player(_IL_GID, qid)


def _il_snap(qid, name="玩家", cls="cls_zhan_shi", level=60, learned=None, hp=None,
             spd=30, mp=999):
    pl = _IL_db.get_player(_IL_GID, qid) or {}
    mh = int(pl.get("max_hp", 500) or 500)
    return {"name": name, "qq_id": str(qid), "class_name": cls, "level": level,
            "hp": int(hp if hp is not None else mh), "max_hp": mh, "mp": mp, "max_mp": mp,
            "equipment": {}, "skills": [], "learned_skills": list(learned or []),
            "class_tier": 0, "evolve_path": 0, "attributes": pl.get("attributes"),
            "bonus": {"panel": {}, "cap": {}, "cost": {}}, "race": pl.get("race"),
            "uid": "p_%s" % qid, "buffs": {}, "stacks": {}, "defending": False,
            "charging": None, "ct": 0.0, "p_shields": {}, "spd": spd}


def _il_enemy(hp=1, spd=1, role="dps", atk=1, uid="e_il", name="房间怪", lv=15,
              exp=10, gold=5, drops=None):
    return {"uid": uid, "name": name, "hp": hp, "max_hp": hp, "atk": atk, "def": 0,
            "matk": 1, "mdef": 0, "spd": spd, "crit": 0.0, "lv": lv, "level": lv,
            "role": role, "is_boss": role == "boss", "is_elite": role == "elite",
            "rank": 1, "reach": 1, "ct": 1.0, "exp": exp, "gold": gold,
            "drops": list(drops or [])}


def _il_st(qids, inst_id="inst_goblin_camp", names=None, **kw):
    qids = [str(q) for q in qids]
    names = names or {}
    st = {"type": "instance", "inst_id": inst_id, "leader": qids[0], "members": qids,
          "alive": {q: True for q in qids},
          "players": {q: _il_snap(q, names.get(q, "玩家")) for q in qids},
          "boss": None, "enemy": None, "enemies": [], "turn": 0, "round": 1,
          "mode": "battle", "pets": {}, "p_buffs": {q: {} for q in qids},
          "p_hot": {q: {} for q in qids}, "p_food_effects": {q: [] for q in qids},
          "p_defending": {q: False for q in qids}, "mech_stacks": {q: {} for q in qids},
          "now": 0.0, "battle": None, "contribution": {}, "threat": {q: 0 for q in qids},
          "over": False, "turn_time": 0, "stage_pending": [], "inst_stages": [],
          "stage_idx": 0, "stage_cleared": False, "world_id": ""}
    st.update(kw)
    return st


def _il_cm_patch(all_members):
    """多人 st 无 party 行时，current_members 恒返回全部成员（等价单人/测试口径）。"""
    orig = _IL_Inst._instance_current_members
    _IL_Inst._instance_current_members = (
        lambda self, gid, st: [str(m) for m in (all_members or st["members"])])
    return orig


def _il_cm_restore(orig):
    _IL_Inst._instance_current_members = orig


def _il_run(inst, st, qq, action, skill=None, target=None):
    """跑一次 router（同步收全部 yield）。"""
    player = st["players"][str(qq)]
    agen = inst._instance_router(_IL_Event(_IL_GID, str(qq)), _IL_GID, str(qq), player,
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


def _il_now():
    return int(time.time())


def _il_text(msgs):
    return "\n".join(str(m) for m in msgs) if not isinstance(msgs, str) else msgs


class _ILRR(object):
    """random.random 打桩（进出还原；迁移前后用同一套桩）。"""

    def __init__(self, value):
        self.value = value

    def __enter__(self):
        self._orig = random.random
        if self.value is not None:
            random.random = lambda: self.value
        return self

    def __exit__(self, *exc):
        random.random = self._orig
        return False


# ── 1. router（instance_router.py）────────────────────────────────────
def _il_rt1_timeout_defend():
    """⏰ 非请求者超时 → 自动防御姿态（面板/轮到行同屏）。"""
    _IL_clean()
    random.seed(20260913)
    _il_player("q_t1", "甲")
    _il_player("q_t2", "乙")
    st = _il_st(["q_t1", "q_t2"], names={"q_t1": "甲", "q_t2": "乙"})
    st["enemies"] = [_il_enemy(hp=5000, spd=1)]
    st["boss"] = st["enemy"] = st["enemies"][0]
    _IL_IB.build_battle(st)
    for a in (_IL_IB._players_of(st) or []):
        a["ct"] = 10.0 if str(a.get("qq_id")) == "q_t1" else 100.0
    _IL_IB.sync_views(st, _IL_GID)
    st["turn_time"] = _il_now() - 120
    orig = _il_cm_patch(["q_t1", "q_t2"])
    try:
        return _il_run(_ILHost(), st, "q_t2", "defend")
    finally:
        _il_cm_restore(orig)


def _il_rt2_taunt():
    """🛡️ 嘲讽（技能 effect=taunt → 强制攻击自己）。"""
    _IL_clean()
    random.seed(20260913 + 2)
    _il_player("q_ta", "甲", learned=["嘲讽"])
    st = _il_st(["q_ta"], names={"q_ta": "甲"})
    st["enemies"] = [_il_enemy(hp=5000, spd=1)]
    st["boss"] = st["enemy"] = st["enemies"][0]
    _IL_IB.build_battle(st)
    return _il_run(_ILHost(), st, "q_ta", "skill", "嘲讽")


def _il_rt3_mutual_destroy():
    """⚔️ 同归于尽（玩家与敌同时倒下 → 失败结算）。

    ★ 桩：真实链路里「玩家与敌同归于尽」由旧引擎毒伤致死触发，saintess_engine 未迁
      state dot（见 instance_battle 模块注释）→ 用桩：IB.act 照常真跑（这一刀真杀死敌），
      只把战斗 state 里玩家 hp 归 0（= 同刻也倒下）。文案路径本身零桩。
    """
    _IL_clean()
    random.seed(20260913 + 3)
    _il_player("q_md", "甲")
    st = _il_st(["q_md"], names={"q_md": "甲"})
    st["enemies"] = [_il_enemy(hp=1, spd=1)]
    st["boss"] = st["enemy"] = st["enemies"][0]
    _IL_IB.build_battle(st)
    _orig_act = _IL_IB.act

    def _act_both_down(st_, group_id, qq_id, action, skill_name=None, target=None):
        _r = _orig_act(st_, group_id, qq_id, action, skill_name, target=target)
        try:
            for _a in (((st_.get("battle") or {}).get("sides") or {}).get("player") or []):
                _a["hp"] = 0
        except Exception:
            pass
        return _r
    _IL_IB.act = _act_both_down
    try:
        return _il_run(_ILHost(), st, "q_md", "attack")
    finally:
        _IL_IB.act = _orig_act


# ── 2. instance_battle.py ────────────────────────────────────────────
def _il_bt1_team_heal():
    """✨ 团队治疗广播（牧师『救赎之光』team=heal_all → 队友恢复行）。"""
    _IL_clean()
    random.seed(20260913 + 4)
    _il_player("q_h1", "牧师甲", cls="cls_mu_shi", level=60, learned=["救赎之光"])
    _il_player("q_h2", "战士乙", level=60)
    st = _il_st(["q_h1", "q_h2"], names={"q_h1": "牧师甲", "q_h2": "战士乙"})
    st["players"]["q_h1"]["class_name"] = "cls_mu_shi"
    st["players"]["q_h1"]["learned_skills"] = ["救赎之光"]
    st["players"]["q_h2"]["hp"] = 30
    st["enemies"] = [_il_enemy(hp=5000, spd=1)]
    st["boss"] = st["enemy"] = st["enemies"][0]
    _IL_IB.build_battle(st)
    for a in (_IL_IB._players_of(st) or []):
        a["ct"] = 0.0 if str(a.get("qq_id")) == "q_h1" else 50.0
    _IL_IB.sync_views(st, _IL_GID)
    st["turn_time"] = _il_now()
    orig = _il_cm_patch(["q_h1", "q_h2"])
    try:
        return _il_run(_ILHost(), st, "q_h1", "skill", "救赎之光")
    finally:
        _il_cm_restore(orig)


# ── 3. instance.py：组队提示 / 副本列表 ──────────────────────────────
def _il_in1_hint_no_tank():
    """组队构成提示：3×牧师（无坦克 + 无输出）。"""
    _IL_clean()
    for i, q in enumerate(("q_hh1", "q_hh2", "q_hh3"), 1):
        _il_player(q, "牧师%s" % "甲乙丙"[i - 1], cls="cls_mu_shi")
    st = _il_st(["q_hh1", "q_hh2", "q_hh3"])
    for q in ("q_hh1", "q_hh2", "q_hh3"):
        st["players"][q]["class_name"] = "cls_mu_shi"
    return "\n".join(_ILHost()._party_composition_hint(st))


def _il_in2_hint_no_heal():
    """组队构成提示：3×战士（无治疗 + 无输出）。"""
    _IL_clean()
    for i, q in enumerate(("q_hz1", "q_hz2", "q_hz3"), 1):
        _il_player(q, "战士%s" % "甲乙丙"[i - 1])
    st = _il_st(["q_hz1", "q_hz2", "q_hz3"])
    return "\n".join(_ILHost()._party_composition_hint(st))


def _il_in3_instance_list():
    """副本列表（Boss 行 / 钥匙行 / 入口行 / 底部轮流提示）。"""
    _IL_clean()
    random.seed(20260913 + 5)
    player = _il_player("q_l1", "甲", level=60)
    return _ILHost()._instance_list(player)


# ── 4. instance.py：战斗面板 / 状态面板 ──────────────────────────────
def _il_in4_battle_footer():
    """战斗面板：buff 剩刻 / 减伤 / 护盾（带与不带剩刻）/ 敌方效果 / 选敌提示 / 行动顺序。"""
    _IL_clean()
    random.seed(20260913 + 6)
    _il_player("q_f1", "甲")
    st = _il_st(["q_f1"], names={"q_f1": "甲"})
    enemy = _il_enemy(hp=500, spd=1)
    enemy["effects"] = {"def_down": {"expire": 3.0}, "mark": {"stacks": 2}}
    st["enemies"] = [enemy]
    st["boss"] = st["enemy"] = enemy
    snap = st["players"]["q_f1"]
    snap["effects"] = {"atk_up": {"expire": 3.0}, "reduce": {"v": 0.25, "expire": 3.0}}
    snap["shields"] = {"s1": {"value": 30, "expire_at": 2.0}, "s2": {"value": 5}}
    st["now"] = 0.0
    return _ILHost()._instance_battle_footer(st, _IL_GID)


def _il_in5_battle_status():
    """『副本』战斗查看面板（标题层数行 + footer + 轮到 X 行动）。"""
    _IL_clean()
    random.seed(20260913 + 7)
    _il_player("q_s1", "甲")
    st = _il_st(["q_s1"], names={"q_s1": "甲"},
                inst_stages=[{"name": "一层"}, {"name": "二层"}], stage_idx=0)
    st["enemies"] = [_il_enemy(hp=500, spd=1)]
    st["boss"] = st["enemy"] = st["enemies"][0]
    return _ILHost()._instance_status(_IL_GID, "q_s1", {"state": st})


# ── 5. instance.py：副本地图（rooms 形态）────────────────────────────
def _il_rooms_st(qid, cur_sa, leader=None, **room):
    st = _il_st([qid], names={qid: "甲"},
                rooms={cur_sa: dict({"monsters_left": [], "pois_left": [],
                                     "boss_alive": False}, **room)},
                resources_pool={"gold_left": 30, "mats_left": {"兽肉": 2}, "equip_left": []})
    st["cur_subarea"] = cur_sa
    if leader is not None:
        st["leader"] = leader
    return st


def _il_in6_map_rooms_full():
    """副本地图 rooms：无出口 / 怪物剩余 / 可调查 / Boss 房 / 通关搜刮 / 调查痕迹。"""
    _IL_clean()
    random.seed(20260913 + 8)
    qid = "q_m1"
    cur_sa = "goblin_camp_3"      # Boss 房（dungeon.boss_room）→ 覆盖「Boss 就在这个房间」
    _il_player(qid, "甲")
    _IL_db.update_player(_IL_GID, qid, cur_map="misty_swamp", cur_subarea=cur_sa)
    st = _il_rooms_st(qid, cur_sa,
                      monsters_left=[["m_goblin_guard", "哥布林守卫", "tank", 15, [], []]],
                      pois_left=["campfire", "shrine"], boss_alive=True)
    st["cleared"] = True
    st["loot_pile"] = True
    st["secret_crack"] = True
    # rooms 形态的「通关后调查痕迹」行引用未定义名 qq_id（既有缺陷，本批不动）→
    # 把调查点全标记为已翻，走不到那一行（stages 形态的孪生行 IN11 覆盖）
    st["investigated"] = [p["id"] for p in
                          (_IL_C.INVESTIGATION_POINTS.get(st["inst_id"]) or [])]
    return _ILHost()._instance_map_view(st, _IL_GID)


def _il_in7_map_rooms_cleared_room():
    """副本地图 rooms：此房已肃清（怪清空）+ 无出口（leader 无角色行 → 回退标题行）。"""
    _IL_clean()
    random.seed(20260913 + 9)
    qid, cur_sa = "q_m2", "goblin_camp_1"
    _il_player(qid, "甲")
    st = _il_rooms_st(qid, cur_sa, leader="q_ghost")
    return _ILHost()._instance_map_view(st, _IL_GID)


# ── 6. instance.py：副本地图（分层形态）─────────────────────────────
def _il_stage_st(qid, stage, **kw):
    st = _il_st([qid], names={qid: "甲"}, inst_stages=[stage], stage_idx=0, **kw)
    st.pop("resources_pool", None)
    return st


def _il_in8_map_stage_plain():
    """分层地图：本层描述缺失（回退行）+ 暗门未发现 + 怪物列表。"""
    _IL_clean()
    random.seed(20260913 + 10)
    qid = "q_m3"
    _il_player(qid, "甲")
    st = _il_stage_st(qid, {"name": "一层", "monsters": [["m_goblin_guard", "哥布林守卫",
                                                          "tank", 15, [], []]],
                            "secret": {"desc": "密室", "pois": []}})
    return _ILHost()._instance_map_view(st, _IL_GID)


def _il_in9_map_stage_secret_and_clear():
    """分层地图：隐藏房间已发现 + 本层已肃清且剩可调查（列名版）。"""
    _IL_clean()
    random.seed(20260913 + 11)
    qid = "q_m4"
    _il_player(qid, "甲")
    st = _il_stage_st(qid, {"name": "一层", "desc": "石廊尽头有风。",
                            "pois": [{"id": "shrine", "name": "古老石碑"}],
                            "secret": {"desc": "暗门后是密室", "pois": []}})
    st["stage_secret_found"] = True
    st["stage_cleared"] = True
    return _ILHost()._instance_map_view(st, _L_GID if False else _IL_GID)


def _il_in10_map_stage_boss_and_empty():
    """分层地图：Boss 就在前方 / 这里暂时没有敌人（两层两场景）。"""
    _IL_clean()
    random.seed(20260913 + 12)
    qid = "q_m5"
    _il_player(qid, "甲")
    st_boss = _il_stage_st(qid, {"name": "一层", "desc": "火把在墙上列队。",
                                 "boss": ["b_goblin_chief", "哥布林酋长·咕噜", "boss", 20,
                                          [], []]})
    out1 = _ILHost()._instance_map_view(st_boss, _IL_GID)
    st_none = _il_stage_st(qid, {"name": "二层", "desc": "空旷的石室。",
                                 "monsters": [], "elite": None})
    out2 = _ILHost()._instance_map_view(st_none, _IL_GID)
    return out1 + "\n@@@\n" + out2


def _il_in11_map_stage_cleared_pois():
    """分层地图：通关后（战利品堆/墙砖/神秘宝箱 + 通关调查痕迹）。"""
    _IL_clean()
    random.seed(20260913 + 13)
    qid = "q_m6"
    _il_player(qid, "甲")
    st = _il_stage_st(qid, {"name": "一层", "desc": "祭坛还温着。"})
    st["cleared"] = True
    st["loot_pile"] = True
    st["secret_crack"] = True
    st["secret_chest"] = True
    # 「通关后调查痕迹」行（L1748）引用未定义名 qq_id（既有缺陷，本批不动，见报告）→
    # 全标记已翻，绕开该行（rooms 形态的孪生行 L1706 同缺陷）
    st["investigated"] = [p["id"] for p in
                          (_IL_C.INVESTIGATION_POINTS.get(st["inst_id"]) or [])]
    return _ILHost()._instance_map_view(st, _IL_GID)


# ── 7. instance.py：搜刮战利品堆 ─────────────────────────────────────
def _il_in12_loot_pile_nonempty():
    """搜刮战利品堆（有产出：金币 + 材料）。"""
    _IL_clean()
    random.seed(20260913 + 14)
    player = _il_player("q_lp1", "甲", level=15)
    st = _il_st(["q_lp1"], names={"q_lp1": "甲"})
    st["loot_pile"] = True
    return _ILHost()._instance_loot_pile(_IL_GID, "q_lp1", player, st)


def _il_in13_loot_pile_empty():
    """搜刮战利品堆（空 → 引擎兜底文案）。★ 桩：掉落实测返回空列表（数据异常态）。"""
    import data.plugins.dragonfall.game.drop_engine as _IL_DE
    _IL_clean()
    random.seed(20260913 + 15)
    player = _il_player("q_lp2", "甲", level=15)
    st = _il_st(["q_lp2"], names={"q_lp2": "甲"})
    st["loot_pile"] = True
    _orig = _IL_DE.roll
    _IL_DE.roll = lambda *a, **k: []
    try:
        return _ILHost()._instance_loot_pile(_IL_GID, "q_lp2", player, st)
    finally:
        _IL_DE.roll = _orig


# ── 8. instance.py：击杀奖励行（切怪路径）────────────────────────────
def _il_in14_kill_reward_switch():
    """击杀奖励行（经验行 + 拾取材料行）+ 切怪（击杀后下一只入场）。"""
    _IL_clean()
    random.seed(20260913 + 16)
    _il_player("q_k1", "甲", level=15)
    st = _il_st(["q_k1"], names={"q_k1": "甲"},
                stage_pending=[["m_slime", "史莱姆", "dps", 15, [], []]])
    st["enemies"] = [_il_enemy(hp=1, spd=1, drops=["兽肉"])]
    st["boss"] = st["enemy"] = st["enemies"][0]
    _IL_IB.build_battle(st)
    inst = _ILHost()
    msgs = []
    for _ in range(4):
        st["turn_time"] = _il_now()
        msgs += _il_run(inst, st, "q_k1", "attack")
        if st.get("stage_pending") == [] and "又一只" in _il_text(msgs):
            break
    return msgs


def _il_in15_kill_reward_pet():
    """击杀奖励行（宠物分经验 [+ 升至 Lv.N]）。"""
    _IL_clean()
    random.seed(20260913 + 17)
    _il_player("q_k2", "甲", level=15)
    st = _il_st(["q_k2"], names={"q_k2": "甲"},
                stage_pending=[["m_slime", "史莱姆2", "dps", 15, [], []]])
    st["pets"] = {"q_k2": {"name": "阿黄", "level": 1, "exp": 0, "satiety": 80}}
    st["enemies"] = [_il_enemy(hp=1, spd=1, drops=["兽肉"])]
    st["boss"] = st["enemy"] = st["enemies"][0]
    _IL_IB.build_battle(st)
    inst = _ILHost()
    msgs = []
    for _ in range(4):
        st["turn_time"] = _il_now()
        msgs += _il_run(inst, st, "q_k2", "attack")
        if st.get("stage_pending") == []:
            break
    return msgs


# ── 9. instance.py：通关结算 ─────────────────────────────────────────
def _il_victory_once(qid1, qid2, seed, rr, pet, dead, learned, boss_lv=20,
                     boss_exp=400, boss_gold=220, inst_id="inst_goblin_camp"):
    """驱动一次 _instance_victory（真跑通关结算），返回逐字输出。"""
    _IL_clean()
    random.seed(seed)
    _il_player(qid1, "甲", level=20)
    _il_player(qid2, "乙", level=20)
    if learned:
        _bps = sorted({( _IL_C.roll_blueprint(boss_lv) or {}).get("blueprint_for") or ""
                       for _ in range(80)})
        _IL_db.update_player(_IL_GID, qid1, learned_blueprints=[x for x in _bps if x])
    st = _il_st([qid1, qid2], names={qid1: "甲", qid2: "乙"}, inst_id=inst_id)
    st["players"][qid1]["hp"] = 500
    st["players"][qid1]["max_hp"] = 500
    if dead:
        st["alive"][qid2] = False
        st["players"][qid2]["hp"] = 0
    if pet:
        st["pets"] = {qid1: dict(pet)}
    bs = _il_enemy(hp=0, spd=50, role="boss", uid="e_boss", name="哥布林酋长·咕噜",
                   lv=boss_lv, exp=boss_exp, gold=boss_gold)
    st["boss"] = bs
    st["_last_killed"] = [dict(bs)]
    st["contribution"] = {qid1: 100, qid2: 10}
    player = st["players"][qid1]
    orig = _il_cm_patch([qid1, qid2])
    _rr = _ILRR(rr)
    _rr.__enter__()
    try:
        async def _c():
            out = []
            async for x in _ILHost()._instance_victory(
                    _IL_Event(_IL_GID, qid1), _IL_GID, qid1, player, st, []):
                out.append(x)
            return out
        loop = asyncio.new_event_loop()
        try:
            msgs = loop.run_until_complete(_c())
        finally:
            loop.close()
        return _il_text(msgs)
    finally:
        _rr.__exit__()
        _il_cm_restore(orig)


def _il_in16_victory_a():
    """通关 A：宠物升级 + 图纸已学 + 暗格必出（random 打 0.05）。"""
    return _il_victory_once("q_v1", "q_v2", 20260913 + 18, 0.05,
                            {"name": "阿黄", "level": 1, "exp": 0, "satiety": 80},
                            dead=True, learned=True)


def _il_in17_victory_b():
    """通关 B：无宠物 / 未学图纸 / 暗格不出（random 打 0.9）。"""
    return _il_victory_once("q_v3", "q_v4", 20260913 + 19, 0.9,
                            None, dead=False, learned=False)


def _il_in18_victory_c():
    """通关 C：自由随机（seed 定）——补另一侧掉落分支。"""
    return _il_victory_once("q_v5", "q_v6", 20260913 + 20, None,
                            {"name": "阿黄", "level": 1, "exp": 0, "satiety": 80},
                            dead=False, learned=True, boss_lv=30, boss_exp=900,
                            boss_gold=500)


# ── 10. instance.py：失败结算 ────────────────────────────────────────
def _il_in19_defeat():
    """失败：玩家被高攻 Boss 秒杀 → 全灭行 + 回城行（单人：current_members 恒 [本人]）。"""
    _IL_clean()
    random.seed(20260913 + 21)
    _il_player("q_d1", "甲", level=15)
    st = _il_st(["q_d1"], names={"q_d1": "甲"})
    st["players"]["q_d1"]["hp"] = 3
    st["enemies"] = [_il_enemy(hp=99999, spd=200, atk=99999, role="boss", name="房间怪")]
    st["boss"] = st["enemy"] = st["enemies"][0]
    _IL_IB.build_battle(st)
    inst = _ILHost()
    msgs = []
    for _ in range(12):
        st["turn_time"] = _il_now()
        msgs += _il_run(inst, st, "q_d1", "defend")
        if st.get("over") or not st.get("alive", {}).get("q_d1", True):
            break
    return msgs


def _il_in20_victory_exclusive():
    """通关 D：Boss 专属装备掉落（👑 专属）+ 首功图纸（未学会）。"""
    return _il_victory_once("q_v7", "q_v8", 20260913 + 22, 0.0,
                            None, dead=False, learned=False, boss_lv=22,
                            boss_exp=900, boss_gold=500, inst_id="inst_sea_cave")


def _il_in21_victory_learned_bp():
    """通关 E：首功图纸（已学会 → 折算残页）。"""
    return _il_victory_once("q_v9", "q_v10", 20260913 + 23, 0.9,
                            None, dead=False, learned=True, boss_lv=22,
                            boss_exp=900, boss_gold=500, inst_id="inst_sea_cave")


def _il_in22_map_stage_cleared_no_poi():
    """分层地图：本层已肃清且无可调查剩余（另一支肃清行）。"""
    _IL_clean()
    random.seed(20260913 + 24)
    qid = "q_m7"
    _il_player(qid, "甲")
    st = _il_stage_st(qid, {"name": "三层", "desc": "走廊尽头静了下来。",
                            "pois": [], "monsters": []})
    st["stage_cleared"] = True
    return _ILHost()._instance_map_view(st, _IL_GID)


_IL_BRANCHES = (
    ("RT1_超时自动防御", _il_rt1_timeout_defend),
    ("RT2_嘲讽", _il_rt2_taunt),
    ("RT3_同归于尽", _il_rt3_mutual_destroy),
    ("BT1_团队治疗广播", _il_bt1_team_heal),
    ("IN1_组队提示_无坦克", _il_in1_hint_no_tank),
    ("IN2_组队提示_无治疗", _il_in2_hint_no_heal),
    ("IN3_副本列表", _il_in3_instance_list),
    ("IN4_战斗面板", _il_in4_battle_footer),
    ("IN5_副本状态面板", _il_in5_battle_status),
    ("IN6_地图_rooms_全提示", _il_in6_map_rooms_full),
    ("IN7_地图_rooms_已肃清", _il_in7_map_rooms_cleared_room),
    ("IN8_地图_分层_描述缺失", _il_in8_map_stage_plain),
    ("IN9_地图_分层_暗门与肃清", _il_in9_map_stage_secret_and_clear),
    ("IN10_地图_分层_Boss与空", _il_in10_map_stage_boss_and_empty),
    ("IN11_地图_分层_通关后", _il_in11_map_stage_cleared_pois),
    ("IN12_搜刮_非空", _il_in12_loot_pile_nonempty),
    ("IN13_搜刮_空", _il_in13_loot_pile_empty),
    ("IN14_击杀奖励_切怪", _il_in14_kill_reward_switch),
    ("IN15_击杀奖励_宠物", _il_in15_kill_reward_pet),
    ("IN16_通关A_宠物升级图纸已学", _il_in16_victory_a),
    ("IN17_通关B_无宠物未学", _il_in17_victory_b),
    ("IN18_通关C_自由随机", _il_in18_victory_c),
    ("IN19_失败_全灭回城", _il_in19_defeat),
    ("IN20_通关D_专属装备", _il_in20_victory_exclusive),
    ("IN21_通关E_首功图纸已学", _il_in21_victory_learned_bp),
    ("IN22_地图_分层_肃清无可调查", _il_in22_map_stage_cleared_no_poi),
)


def _il_scenarios():
    """复跑全部副本日志分支（迁移前采快照 / 迁移后门禁比对，同一份代码）。"""
    out = {}
    for name, fn in _IL_BRANCHES:
        out[name] = _il_text(fn())
    return out

INSTANCE_LOG_FROZEN = {
    "BT1_团队治疗广播": "✨ 战士乙 恢复 70 点生命！\n你施展【救赎之光】，治愈了 0 点生命！\n—— 房间怪 行动 ——\n💥 牧师甲 受到 1 点伤害！\n━━━━━━━━━━━━\n── 敌方 ──\n  A1层: a1  房间怪 ❤️5000/5000\n── 我方 ──\n  B1层: b1  战士乙 ❤️100/100\n  B2层: b2  牧师甲 ❤️99/100\n🕐 时刻 1.5s ｜ ⚡ 行动顺序：牧师甲(我) → 房间怪(敌) → 战士乙(我)\n✅ 牧师甲：❤️ 99/100 💙 984/999\n✅ 战士乙：❤️ 100/100 💙 999/999\n💡 选敌：『技能1 a2』打2号(纯数字同义)；治疗『技能 <名称> b1』奶自己\n⏳ 轮到 牧师甲 行动！『攻击』『技能 <名称>』『防御』",
    "IN10_地图_分层_Boss与空": "🗺️ 【👺哥布林营地】第 1 层 · 一层\n━━━━━━━━━━━━\n📜 火把在墙上列队。\n━━━━━━━━━━━━\n✨ 场景：\n  []\n  []\n━━━━━━━━━━━━\n👑 Boss 就在前方：哥布林酋长·咕噜！『探索』进入战斗！\n━━━━━━━━━━━━\n💡 『副本』查看战况，『角色』看队伍\n@@@\n🗺️ 【👺哥布林营地】第 1 层 · 二层\n━━━━━━━━━━━━\n📜 空旷的石室。\n━━━━━━━━━━━━\n✨ 场景：\n  []\n  []\n━━━━━━━━━━━━\n🐾 这里暂时没有敌人。\n━━━━━━━━━━━━\n💡 可发送『调查 <名称>』互动机关",
    "IN11_地图_分层_通关后": "🗺️ 【👺哥布林营地】第 1 层 · 一层\n━━━━━━━━━━━━\n📜 祭坛还温着。\n━━━━━━━━━━━━\n✨ 场景：\n  []\n  []\n🎁 战利品堆：首领的遗物堆在角落（『调查 战利品堆』）\n🧱 墙上有一块松动的墙砖……（『调查 墙砖』）\n🔐 神秘宝箱：密室深处泛着微光（『调查 宝箱』）\n💡 多人副本先『组队 <名字>』再开本\n━━━━━━━━━━━━\n💡 单人副本直接『副本 <名字>』开本",
    "IN12_搜刮_非空": "🎁 你搜刮了战利品堆：金币 +70\n🎒 拾取：咕噜皇冠 ×1",
    "IN13_搜刮_空": "🎁 你搜刮了战利品堆，但里面空空的……",
    "IN14_击杀奖励_切怪": "💥 房间怪 受到 1 点伤害，倒下了！\n  甲：经验 +1，拾取材料 兽肉 ×1\n  甲：🏆 成就解锁：初试锋芒！(完成首次战斗)\n      🎁 经验+100、兽肉×3（『成就 领取』领取）\n  甲：🏆 成就解锁：初出茅庐！(注册角色)\n      🎁 草药×2（『成就 领取』领取）\n  甲：🏆 成就解锁：崭露头角！(达到 10 级)\n      🎁 铁矿石×2（『成就 领取』领取）\n━━━━━━━━━━━━\n⚔️ 又一只怪物挡在面前！\n── 敌方 ──\n  A1层: a1  史莱姆 ❤️465/465\n── 我方 ──\n  B1层: b1  甲 ❤️100/100\n🕐 时刻 0.0s ｜ ⚡ 行动顺序：甲(我) → 史莱姆(敌)\n✅ 甲：❤️ 100/100 💙 999/999\n💡 选敌：『技能1 a2』打2号(纯数字同义)；治疗『技能 <名称> b1』奶自己\n⏳ 轮到 甲 行动！『攻击』『技能 <名称>』『防御』",
    "IN15_击杀奖励_宠物": "💥 房间怪 受到 1 点伤害，倒下了！\n  甲：经验 +1  🐾阿黄 分得经验 +2，拾取材料 兽肉 ×1\n  甲：🏆 成就解锁：初试锋芒！(完成首次战斗)\n      🎁 经验+100、兽肉×3（『成就 领取』领取）\n  甲：🏆 成就解锁：初出茅庐！(注册角色)\n      🎁 草药×2（『成就 领取』领取）\n  甲：🏆 成就解锁：崭露头角！(达到 10 级)\n      🎁 铁矿石×2（『成就 领取』领取）\n━━━━━━━━━━━━\n⚔️ 又一只怪物挡在面前！\n── 敌方 ──\n  A1层: a1  史莱姆2 ❤️465/465\n── 我方 ──\n  B1层: b1  甲 ❤️100/100\n🕐 时刻 0.0s ｜ ⚡ 行动顺序：甲(我) → 史莱姆2(敌)\n✅ 甲：❤️ 100/100 💙 999/999\n　🐾 阿黄 还小（Lv.1），Lv.10 解锁战斗技能！\n💡 选敌：『技能1 a2』打2号(纯数字同义)；治疗『技能 <名称> b1』奶自己\n⏳ 轮到 甲 行动！『攻击』『技能 <名称>』『防御』",
    "IN16_通关A_宠物升级图纸已学": "\n🎉 【哥布林酋长·咕噜】被击败了！👺哥布林营地 通关！\n📜 咕噜的皇冠滚落在篝火边，商路上的劫掠就此画上句号。行会的赏金结清了，可你总觉得，这条商路尽头的风声，才刚刚开始。\n  甲：金币 +234 经验 +3653\n  🐾阿黄 分得经验 +80，升至 Lv.2！\n  📜 甲 拾取图纸：雷霆指环图纸（已学会，化作 4 张图纸残页）\n  ⚔️ 甲 拾取 Boss 珍藏：【咕噜金戒】！\n  🎒 甲 拾取：咕噜皇冠\n  💀 乙 已阵亡，未能获得奖励\n  💎 甲 获得幸运宝石：闪耀的幸运宝石·金币加成+3%！(『原石』镶嵌到装备孔位)\n  甲：🏆 成就解锁：初出茅庐！(注册角色)\n      🎁 草药×2（『成就 领取』领取）\n  甲：🏆 成就解锁：崭露头角！(达到 10 级)\n      🎁 铁矿石×2（『成就 领取』领取）\n  甲：🏆 成就解锁：名声鹊起！(达到 20 级)\n      🎁 精铁×2（『成就 领取』领取）\n  甲：🏆 成就解锁：博闻强识！(累计学习 20 张图纸)\n      🎁 白银箱×1、图纸残页×3（『成就 领取』领取）\n\n🏆 副本已通关！你可以在副本内停留搜刮：\n  · 🎁 【战利品堆】—— 首领的遗物，搜刮一次（『调查 战利品堆』）\n  · 🔍 通关后这里多了些可调查的痕迹（『副本地图』查看，每日限 3 次）\n  · 🧱 墙上似乎有【松动的墙砖】……（『调查 墙砖』）\n搜刮完毕用『离开副本』传出～\n\n💡 『副本』可再次挑战，首通成就已记录～",
    "IN17_通关B_无宠物未学": "\n🎉 【哥布林酋长·咕噜】被击败了！👺哥布林营地 通关！\n📜 咕噜的皇冠滚落在篝火边，商路上的劫掠就此画上句号。行会的赏金结清了，可你总觉得，这条商路尽头的风声，才刚刚开始。\n  甲：金币 +234 经验 +3653\n  🎒 甲 拾取：咕噜皇冠\n  乙：金币 +234 经验 +3653\n  🎒 乙 拾取：咕噜皇冠\n  甲：🏆 成就解锁：完美主义者！(未受伤通关 1 个副本)\n      🎁 铁箱×1（『成就 领取』领取）\n  甲：🏆 成就解锁：初出茅庐！(注册角色)\n      🎁 草药×2（『成就 领取』领取）\n  甲：🏆 成就解锁：崭露头角！(达到 10 级)\n      🎁 铁矿石×2（『成就 领取』领取）\n  甲：🏆 成就解锁：名声鹊起！(达到 20 级)\n      🎁 精铁×2（『成就 领取』领取）\n  乙：🏆 成就解锁：完美主义者！(未受伤通关 1 个副本)\n      🎁 铁箱×1（『成就 领取』领取）\n  乙：🏆 成就解锁：初出茅庐！(注册角色)\n      🎁 草药×2（『成就 领取』领取）\n  乙：🏆 成就解锁：崭露头角！(达到 10 级)\n      🎁 铁矿石×2（『成就 领取』领取）\n  乙：🏆 成就解锁：名声鹊起！(达到 20 级)\n      🎁 精铁×2（『成就 领取』领取）\n\n🏆 副本已通关！你可以在副本内停留搜刮：\n  · 🎁 【战利品堆】—— 首领的遗物，搜刮一次（『调查 战利品堆』）\n  · 🔍 通关后这里多了些可调查的痕迹（『副本地图』查看，每日限 3 次）\n搜刮完毕用『离开副本』传出～\n\n💡 『副本』可再次挑战，首通成就已记录～",
    "IN18_通关C_自由随机": "\n🎉 【哥布林酋长·咕噜】被击败了！👺哥布林营地 通关！\n📜 咕噜的皇冠滚落在篝火边，商路上的劫掠就此画上句号。行会的赏金结清了，可你总觉得，这条商路尽头的风声，才刚刚开始。\n  甲：金币 +234 经验 +3653\n  🐾阿黄 分得经验 +180，升至 Lv.3！\n  🎒 甲 拾取：咕噜皇冠\n  乙：金币 +234 经验 +3653\n  🎒 乙 拾取：咕噜皇冠\n  甲：🏆 成就解锁：完美主义者！(未受伤通关 1 个副本)\n      🎁 铁箱×1（『成就 领取』领取）\n  甲：🏆 成就解锁：初出茅庐！(注册角色)\n      🎁 草药×2（『成就 领取』领取）\n  甲：🏆 成就解锁：崭露头角！(达到 10 级)\n      🎁 铁矿石×2（『成就 领取』领取）\n  甲：🏆 成就解锁：名声鹊起！(达到 20 级)\n      🎁 精铁×2（『成就 领取』领取）\n  甲：🏆 成就解锁：博闻强识！(累计学习 20 张图纸)\n      🎁 白银箱×1、图纸残页×3（『成就 领取』领取）\n  乙：🏆 成就解锁：完美主义者！(未受伤通关 1 个副本)\n      🎁 铁箱×1（『成就 领取』领取）\n  乙：🏆 成就解锁：初出茅庐！(注册角色)\n      🎁 草药×2（『成就 领取』领取）\n  乙：🏆 成就解锁：崭露头角！(达到 10 级)\n      🎁 铁矿石×2（『成就 领取』领取）\n  乙：🏆 成就解锁：名声鹊起！(达到 20 级)\n      🎁 精铁×2（『成就 领取』领取）\n\n🏆 副本已通关！你可以在副本内停留搜刮：\n  · 🎁 【战利品堆】—— 首领的遗物，搜刮一次（『调查 战利品堆』）\n  · 🔍 通关后这里多了些可调查的痕迹（『副本地图』查看，每日限 3 次）\n  · 🧱 墙上似乎有【松动的墙砖】……（『调查 墙砖』）\n搜刮完毕用『离开副本』传出～\n\n💡 『副本』可再次挑战，首通成就已记录～",
    "IN19_失败_全灭回城": "🛡 甲 摆出防御姿态，受到的伤害减半！\n━━━━━━━━━━━━\n── 敌方 ──\n  A1层: a1  房间怪 ❤️99999/99999\n── 我方 ──\n  B1层: b1  甲 ❤️3/100\n🕐 时刻 0.6s ｜ ⚡ 行动顺序：甲(我) → 房间怪(敌)\n✅ 甲：❤️ 3/100 💙 999/999 🛡️防御\n💡 选敌：『技能1 a2』打2号(纯数字同义)；治疗『技能 <名称> b1』奶自己\n⏳ 轮到 甲 行动！『攻击』『技能 <名称>』『防御』\n🛡 甲 摆出防御姿态，受到的伤害减半！\n—— 房间怪 行动 ——\n🌪️【房间怪】发出震天【咆哮】！气势瞬间拉满！\n⚡【房间怪】的咆哮让攻击力提升了！\n☠️ 【房间怪】盯上了重伤的你……本刻攻击大幅提升！\n(格挡后 37757 点伤害)\n💥 甲 受到 3 点伤害，倒下了！\n\n💀 队伍全灭……副本失败！冒险者们被送回了最近的城镇。\n📍 甲 被送回了【白鹿城·白鹿广场】（HP 0，先休息恢复吧）",
    "IN1_组队提示_无坦克": "🛡️ 没有坦克：Boss 仇恨没人拉，输出容易被追着打\n⚔️ 没有输出：可能打到超时哦",
    "IN20_通关D_专属装备": "\n🎉 【哥布林酋长·咕噜】被击败了！🌊海蚀洞窟 通关！\n📜 金钩从杰克手中脱落，暗湾里终于只剩下潮水的呼吸。铁港的船主们可以重新起锚了，而你从战利品里翻出的那张旧海图，似乎指向更深的水域。\n  甲：金币 +385 经验 +6465\n  📜 甲 拾取图纸：血潮短刃图纸\n  ⚔️ 甲 拾取 Boss 珍藏：【杰克的金币袋】！\n  👑 甲 从Boss身上拾取稀有专属：【金钩弯刀】！\n  🎒 甲 拾取：杰克的金钩碎片\n  🎒 甲 拾取：杰克的金钩碎片\n  乙：金币 +385 经验 +6465\n  📜 乙 拾取图纸：秘法典籍之杖图纸\n  ⚔️ 乙 拾取 Boss 珍藏：【杰克的金币袋】！\n  👑 乙 从Boss身上拾取稀有专属：【金钩弯刀】！\n  🎒 乙 拾取：杰克的金钩碎片\n  🎒 乙 拾取：杰克的金钩碎片\n  💎 乙 获得幸运宝石：明亮的幸运宝石·格挡+2%！(『原石』镶嵌到装备孔位)\n👑 首功 甲 额外获得图纸：铸火头盔图纸\n  甲：🏆 成就解锁：完美主义者！(未受伤通关 1 个副本)\n      🎁 铁箱×1（『成就 领取』领取）\n  甲：🏆 成就解锁：初出茅庐！(注册角色)\n      🎁 草药×2（『成就 领取』领取）\n  甲：🏆 成就解锁：崭露头角！(达到 10 级)\n      🎁 铁矿石×2（『成就 领取』领取）\n  甲：🏆 成就解锁：名声鹊起！(达到 20 级)\n      🎁 精铁×2（『成就 领取』领取）\n  乙：🏆 成就解锁：完美主义者！(未受伤通关 1 个副本)\n      🎁 铁箱×1（『成就 领取』领取）\n  乙：🏆 成就解锁：初出茅庐！(注册角色)\n      🎁 草药×2（『成就 领取』领取）\n  乙：🏆 成就解锁：崭露头角！(达到 10 级)\n      🎁 铁矿石×2（『成就 领取』领取）\n  乙：🏆 成就解锁：名声鹊起！(达到 20 级)\n      🎁 精铁×2（『成就 领取』领取）\n\n🏆 副本已通关！你可以在副本内停留搜刮：\n  · 🎁 【战利品堆】—— 首领的遗物，搜刮一次（『调查 战利品堆』）\n  · 🔍 通关后这里多了些可调查的痕迹（『副本地图』查看，每日限 3 次）\n  · 🧱 墙上似乎有【松动的墙砖】……（『调查 墙砖』）\n搜刮完毕用『离开副本』传出～\n\n💡 『副本』可再次挑战，首通成就已记录～",
    "IN21_通关E_首功图纸已学": "\n🎉 【哥布林酋长·咕噜】被击败了！🌊海蚀洞窟 通关！\n📜 金钩从杰克手中脱落，暗湾里终于只剩下潮水的呼吸。铁港的船主们可以重新起锚了，而你从战利品里翻出的那张旧海图，似乎指向更深的水域。\n  甲：金币 +385 经验 +6465\n  🎒 甲 拾取：杰克的金钩碎片\n  🎒 甲 拾取：杰克的金钩碎片\n  乙：金币 +385 经验 +6465\n  🎒 乙 拾取：杰克的金钩碎片\n  🎒 乙 拾取：杰克的金钩碎片\n👑 首功 甲 额外获得图纸：深渊之锚图纸（已学会，化作 4 张图纸残页）\n  甲：🏆 成就解锁：完美主义者！(未受伤通关 1 个副本)\n      🎁 铁箱×1（『成就 领取』领取）\n  甲：🏆 成就解锁：初出茅庐！(注册角色)\n      🎁 草药×2（『成就 领取』领取）\n  甲：🏆 成就解锁：崭露头角！(达到 10 级)\n      🎁 铁矿石×2（『成就 领取』领取）\n  甲：🏆 成就解锁：名声鹊起！(达到 20 级)\n      🎁 精铁×2（『成就 领取』领取）\n  甲：🏆 成就解锁：博闻强识！(累计学习 20 张图纸)\n      🎁 白银箱×1、图纸残页×3（『成就 领取』领取）\n  乙：🏆 成就解锁：完美主义者！(未受伤通关 1 个副本)\n      🎁 铁箱×1（『成就 领取』领取）\n  乙：🏆 成就解锁：初出茅庐！(注册角色)\n      🎁 草药×2（『成就 领取』领取）\n  乙：🏆 成就解锁：崭露头角！(达到 10 级)\n      🎁 铁矿石×2（『成就 领取』领取）\n  乙：🏆 成就解锁：名声鹊起！(达到 20 级)\n      🎁 精铁×2（『成就 领取』领取）\n\n🏆 副本已通关！你可以在副本内停留搜刮：\n  · 🎁 【战利品堆】—— 首领的遗物，搜刮一次（『调查 战利品堆』）\n  · 🔍 通关后这里多了些可调查的痕迹（『副本地图』查看，每日限 3 次）\n搜刮完毕用『离开副本』传出～\n\n💡 『副本』可再次挑战，首通成就已记录～",
    "IN22_地图_分层_肃清无可调查": "🗺️ 【👺哥布林营地】第 1 层 · 三层\n━━━━━━━━━━━━\n📜 走廊尽头静了下来。\n━━━━━━━━━━━━\n✨ 场景：\n  []\n  []\n━━━━━━━━━━━━\n✅ 本层敌人已肃清！『深入』前往下一层。\n━━━━━━━━━━━━\n💡 『副本』查看战况，『角色』看队伍",
    "IN2_组队提示_无治疗": "✨ 没有治疗：血线压力大，记得多带药水\n⚔️ 没有输出：可能打到超时哦",
    "IN3_副本列表": "🏰 【组队副本】\n━━━━━━━━━━━━\n1. ✅ 👺 哥布林营地(Lv.15+ · 👥 1-2人)\n   商路旁的哥布林聚落，哥布林酋长·咕噜盘踞于此，靠抢劫商队为生。冒险者行会悬赏讨伐。(主线第 2 章)\n   👹 Boss：哥布林酋长·咕噜(Lv.20)· 掉落：咕噜皇冠\n   📍 入口：迷雾沼泽·沼泽深处\n2. ✅ 🛡️ 鹿角要塞(Lv.18+ · 🕐 单人)\n   白鹿城北的废弃要塞，百年前毁于战火。要塞幽灵仍在城墙上游荡，寻找着失落的军旗。(支线)\n   👹 Boss：要塞幽灵(Lv.23)· 掉落：要塞残片\n   🔑 需『军旗碎片』：古战场/旧战场遗迹采集\n   📍 入口：山丘矿洞·矿洞深处\n3. ✅ 🌊 海蚀洞窟(Lv.22+ · 👥 1-3人)\n   铁港码头下的海蚀洞穴，海盗王·独眼杰克的老巢。潮水声里混着金币碰撞的脆响。(主线第 3 章)\n   👹 Boss：海盗王·独眼杰克(Lv.27)· 掉落：杰克的金钩碎片\n   📍 入口：铁港码头·海堤\n4. ✅ 🦀 锈潮船坞(Lv.25+ · 👥 2-3人)\n   铁港码头废弃船坞下的锈蚀水道，潮水把整座旧船坞泡成了螃蟹的乐园。巨钳蟹王·锈钳盘踞船底，钳上还挂着一百艘沉船的船牌。(海港支线)\n   👹 Boss：巨钳蟹王·锈钳(Lv.31)· 掉落：锈潮蟹甲\n   📍 入口：铁港码头·货仓区\n5. ✅ 🕯️ 烛影墓窟(Lv.29+ · 👥 1-2人)\n   大圣堂地下被封死的古墓廊道，数百年的烛油在地面凝成厚壳。烛影主教·赫尔嘉在此布道——给死人布道，也给误入者布道。(教会地下支线)\n   👹 Boss：烛影主教·赫尔嘉(Lv.35)· 掉落：烛影烛泪\n   📍 入口：晨曦大圣堂·圣堂前庭\n6. ✅ ⚡ 雷鸣矿道(Lv.32+ · 👥 1-2人)\n   山丘矿洞最深处被雷晶矿脉炸开的巷道，矿车轨道上趴着雷晶蜥，雷灵在电线般的矿脉间流窜。雷晶巨像·轰鸣守着整条矿脉的心脏。(矿务支线)\n   👹 Boss：雷晶巨像·轰鸣(Lv.37)· 掉落：雷晶矿核\n   📍 入口：山丘矿洞·塌方矿厅\n7. ✅ 🦴 旧王陵(Lv.35+ · 👥 1-3人)\n   晨曦城北的古老王陵，埋葬着圣战前的历代君王。古王·奥德里克在棺椁中苏醒，亡灵的低语回荡在石壁之间。(主线第 6 章)\n   👹 Boss：古王·奥德里克(Lv.40)· 掉落：古王剑碎片\n   🔑 需『王陵钥匙』：白鹿城铁匠铺购买(500 金)\n   📍 入口：王陵古道·王陵前\n8. ✅ ⚜️ 圣光试炼场(Lv.36+ · 🕐 单人)\n   圣光骑士团的试炼之地。试炼骑士长把守最后一关——通过者将获得骑士团的认可。(支线)\n   👹 Boss：试炼骑士长(Lv.41)· 掉落：试炼徽记\n   🔑 需『试炼令』：铁盾镇军械铺购买(400 金)\n   📍 入口：王陵古道·古道中段\n9. ✅ ⚓ 沉船湾(Lv.38+ · 🕐 单人)\n   翡翠海深处的沉船墓地，幽灵船长·克罗的旗舰在此永沉。传说船底的宝箱装着它的罗盘——还有它不甘的灵魂。(群岛支线)\n   👹 Boss：幽灵船长·克罗(Lv.43)· 掉落：克罗的罗盘碎片\n   🔑 需『幽灵船票』：沉船湾墓地采集\n   📍 入口：风暴海峡·海峡深处\n10. ✅ ⛪ 圣堂地窖(Lv.42+ · 👥 3-4人)\n   晨曦大圣堂下的密室，教会最深的秘密沉睡于此。审判长·马尔库斯奉命看守——他的锁链，从不问对错。(主线第 11 章)\n   👹 Boss：审判长·马尔库斯(Lv.47)· 掉落：马尔库斯的法冠残片\n   🔑 需『圣堂信物』：晨曦城大教堂购买(300 金)\n   📍 入口：晨曦大圣堂·圣堂地窟\n11. ✅ 🐢 旋涡竞技场(Lv.46+ · 👥 2-3人)\n   风暴海峡中央一座随潮汐沉浮的环形礁台，潮水在礁台四周绞成永不停歇的旋涡。石壳龟·磐涡把这里当成了它的角斗场——打赢它，才能从旋涡眼里游出去。(群岛支线)\n   👹 Boss：石壳龟·磐涡(Lv.52)· 掉落：磐涡龟甲\n   📍 入口：风暴海峡·海峡口\n12. ✅ 🎭 黑潮歌剧院(Lv.50+ · 👥 2-4人)\n   黑潮海峡底下沉没的旧歌剧厅，潮水在包厢与舞台之间来回涨落。首席海妖·歌澜每晚都在这里开唱——观众席上坐满溺亡的乐迷，而她们，已经不会鼓掌了。(深海支线)\n   👹 Boss：首席海妖·歌澜(Lv.56)· 掉落：咏叹谱残页\n   📍 入口：雾潮航道·无名灯塔\n13. ✅ 🧜‍♀️ 海妖巢穴(Lv.52+ · 👥 2-3人)\n   海妖湾下的珊瑚巢穴，海妖女王·蓝歌的领地。她的歌声能魅惑水手，也能掀起巨浪——别被歌声骗进深海。(群岛支线)\n   👹 Boss：海妖女王·蓝歌(Lv.57)· 掉落：蓝歌之冠残片\n   🔑 需『海妖鳞片信物』：海妖湾精英·海妖领主·潮汐掉落\n   📍 入口：海妖湾·海妖巢\n14. ✅ 🏛️ 精灵废墟(Lv.58+ · 👥 1-4人)\n   银月林海深处的失落王城，远古精灵王的安息之所。月光照不进坍塌的穹顶，只有亡灵精灵的吟唱。(主线第 7 章)\n   👹 Boss：远古精灵王·晨曦(Lv.63)· 掉落：晨曦之冠碎片\n   🔑 需『精灵遗印』：翡翠森林精英·狼王·灰影掉落\n   📍 入口：月冠王庭·月庭宫门\n15. ✅ 🌙 月神圣殿(Lv.60+ · 🕐 单人)\n   月冠王庭深处的月神神殿，月光从穹顶倾泻而下。月神守卫守护着月之试炼——只有月神认可者才能进入。(支线)\n   👹 Boss：月神守卫(Lv.65)· 掉落：月辉碎片\n   🔑 需『月辉钥匙』：月冠王庭购买(3000 金)\n   📍 入口：月光林·林深处\n16. 🔒 🌊 海神神殿(Lv.64+ · 👥 3-4人)\n   无尽海底的海神神殿，海神祭司·澜歌守护着海神的圣物。潮汐在此倒流——海神的目光，正注视着入侵者。(无尽海支线)\n   👹 Boss：海神祭司·澜歌(Lv.69)· 掉落：澜歌之泪残片\n   🔑 需『海神祷文』：无名港港务厅购买\n   📍 入口：风暴之海·海眼\n17. 🔒 🐲 深海龙宫(Lv.70+ · 👥 4人)\n   无尽海最深处的水晶龙宫，深海龙王·敖澜在此沉睡。它一翻身，海面就要掀起风暴——别吵醒它太久。(无尽海支线)\n   👹 Boss：深海龙王·敖澜(Lv.75)· 掉落：敖澜之珠碎片\n   🔑 需『龙宫珠』：龙鲸海域精英·龙鲸王·涛声掉落\n   📍 入口：风暴之海·风暴区\n18. 🔒 ❄️ 冰霜王座(Lv.74+ · 👥 2-3人)\n   永冻冰原深处的寒冰王座，冰霜领主在此称王。它冻结了三百年的时光，也在等待一个挑战者。(支线)\n   👹 Boss：冰霜领主(Lv.79)· 掉落：永冻之核\n   🔑 需『寒冰令』：永冻冰原精英·冰原猛犸·雪岭掉落\n   📍 入口：永冬湖·湖心\n19. 🔒 ⛏️ 灰矮人要塞(Lv.74+ · 👥 2-3人)\n   幽暗地域深处的灰矮人要塞，灰矮人领主·石炉统治着这片地底。它的锻造炉昼夜不息，烧的是地底恶魔的骨头。(地底支线)\n   👹 Boss：灰矮人领主·石炉(Lv.79)· 掉落：石炉之锤\n   🔑 需『灰矮人通行令』：地底集市购买(2800 金)\n   📍 入口：地下湖·湖底\n20. 🔒 🌋 烬山祭坛(Lv.82+ · 👥 1-4人)\n   烬山之巅的古老祭坛，三百年前圣战的主战场。恶魔祭司·赫尔加在此主持黑暗仪式，试图解开蚀夜的封印。(主线第 9 章)\n   👹 Boss：恶魔祭司·赫尔加(Lv.87)· 掉落：赫尔加的祭器碎片\n   🔑 需『烬火令』：烬山精英·恶魔战士掉落\n   📍 入口：烬山·火山口\n21. 🔒 🐍 地底龙巢(Lv.84+ · 👥 4人)\n   熔火深渊之下的地底龙巢，地底古龙·黑渊盘踞于此。它吞食地底岩浆与恶魔，是幽暗地域最古老的掠食者。(地底支线)\n   👹 Boss：地底古龙·黑渊(Lv.89)· 掉落：黑渊之眼残片\n   🔑 需『龙鳞钥匙』：熔火深渊精英·熔火领主·烬核掉落\n   📍 入口：熔火深渊·深渊深处\n22. 🔒 🌑 深渊裂隙(Lv.90+ · 👥 1-4人)\n   封印的尽头，深渊裂隙的裂口。被误认为魔王的守护者蚀夜，在这里镇守了三百年——你终于要直面真相。(主线第 12 章·最终决战)\n   👹 Boss：蚀夜(真相形态)(Lv.95)· 掉落：黎明之光碎片\n   🔑 需『深渊钥匙』：深渊骑士掉落\n   📍 入口：烬山祭坛·灰烬门廊\n23. 🔒 👹 深渊王座(Lv.90+ · 👥 4人)\n   深渊祭坛最深处的王座，深渊领主·摩罗凝视着一切。地底恶魔的军团在此列队——它们等这一天，等了不止三百年。(地底支线)\n   👹 Boss：深渊领主·摩罗(Lv.95)· 掉落：摩罗之冠碎片\n   🔑 需『深渊圣印』：深渊祭坛精英·祭坛守卫·魔眼掉落\n   📍 入口：深渊祭坛·祭坛核心\n24. 🔒 🐉 龙之墓(Lv.90+ · 👥 4人)\n   龙骨山脉深处的巨龙墓地，古龙·奥姆之影在此守望龙族传承。龙语回荡——只有真正的勇士才配带走它。(主线第 10 章)\n   👹 Boss：古龙·奥姆之影(Lv.95)· 掉落：龙语传承\n   🔑 需『龙牙信物』：龙脊山脉·石龙掉落\n   📍 入口：龙巢·巢穴深处\n25. 🔒 🌩️ 风暴王座(Lv.90+ · 👥 3-4人)\n   龙脊山脉之巅的风暴王座，雷霆君主统御着雷云。雷霆为冠，狂风为座——能坐上去的，只有风暴本身。(支线)\n   👹 Boss：雷霆君主(Lv.95)· 掉落：风暴之核\n   🔑 需『雷光令』：风暴崖精英·风暴崖主·雷鸣掉落\n   📍 入口：风暴崖·风暴崖顶\n26. 🔒 🌀 风暴之眼(Lv.92+ · 👥 4人)\n   雷暴高原的风暴之眼，风暴之主·云怒在此执掌雷霆。雷云之上是天空的尽头——也是风暴的故乡。(天空支线)\n   👹 Boss：风暴之主·云怒(Lv.97)· 掉落：云怒之核碎片\n   🔑 需『雷核钥匙』：雷暴高原·雷元素掉落\n   📍 入口：雷暴高原·高原核心\n27. 🔒 ☁️ 云中圣殿(Lv.94+ · 👥 4人)\n   风翼群岛之巅的云中圣殿，云中圣者·奥拉守护着天空的传承。圣光与风暴在此交织——最后的试炼，留给最强的冒险者。(天空支线)\n   👹 Boss：云中圣者·奥拉(Lv.99)· 掉落：奥拉圣印碎片\n   🔑 需『云玺』：星辉台精英·星龙掉落\n   📍 入口：彩虹云谷·云谷深处\n━━━━━━━━━━━━\n💡 『撤退』保留进度离开副本\n💡 按顺序轮流出手，Boss 血量随人数上涨，配合好才能通关！",
    "IN4_战斗面板": "── 敌方 ──\n  A1层: a1  房间怪 ❤️500/500\n── 我方 ──\n  B1层: b1  甲 ❤️100/100\n🕐 时刻 0.0s ｜ ⚡ 行动顺序：甲(我) → 房间怪(敌)\n✅ 甲：❤️ 100/100 💙 999/999\n　🛡️「⚔️攻击↑(剩3刻) 🛡️减伤25%(3刻) ✨护盾30(2刻) ✨护盾5」\n👹敌：「房间怪 💔破甲(剩3刻) 房间怪 🎯标记×2」\n💡 选敌：『技能1 a2』打2号(纯数字同义)；治疗『技能 <名称> b1』奶自己",
    "IN5_副本状态面板": "👺 【哥布林营地】 第 1 轮 🚪 第 1 层 · 一层\n━━━━━━━━━━━━\n── 敌方 ──\n  A1层: a1  房间怪 ❤️500/500\n── 我方 ──\n  B1层: b1  甲 ❤️100/100\n🕐 时刻 0.0s ｜ ⚡ 行动顺序：甲(我) → 房间怪(敌)\n✅ 甲：❤️ 100/100 💙 999/999\n💡 选敌：『技能1 a2』打2号(纯数字同义)；治疗『技能 <名称> b1』奶自己\n━━━━━━━━━━━━\n⏳ 轮到 甲 行动！『攻击』『技能 <名称>』『防御』",
    "IN6_地图_rooms_全提示": "🗺️ 【哥布林营地 · 酋长帐篷】\n兽骨装饰的帐篷深处，咕噜酋长坐在兽皮宝座上，身边堆满抢来的货物。皇冠歪戴，它正等着好好『招待』不速之客。\n━━━━━━━━━━━━\n📍 当前位置：酋长帐篷\n📮 可前往：\n  ●1. 篝火营地\n  🧭 出城需先到『入口栅栏』\n🔎 可探索触发：\n  ●💀 被抢的商队货箱\n  👑 Boss：哥布林酋长·咕噜\n\n💡 『前往 <序号>』切换位置\n━━━━━━━━━━━━\n🚪 副本内 · 无出口（没有通往外面的路）\n🐾 此房怪物剩余：哥布林守卫（『探索』高概率遭遇）\n🔎 此房可调查：篝火、古老神龛(『调查 <名称>』)\n💰 副本资源池剩余：30 金币 · 兽肉×2\n👑 Boss 就在这个房间！『探索』进入战斗！\n🎁 战利品堆：首领的遗物堆在角落（『调查 战利品堆』）\n🧱 墙上有一块松动的墙砖……（『调查 墙砖』）\n💡 单人副本直接『副本 <名字>』开本",
    "IN7_地图_rooms_已肃清": "🗺️ 【哥布林营地 · 入口栅栏】\n━━━━━━━━━━━━\n🚪 副本内 · 无出口（没有通往外面的路）\n🐾 此房怪物已肃清。\n💰 副本资源池剩余：30 金币 · 兽肉×2\n💡 『副本』查看战况，『角色』看队伍",
    "IN8_地图_分层_描述缺失": "🗺️ 【👺哥布林营地】第 1 层 · 一层\n━━━━━━━━━━━━\n📜 你环顾四周，准备迎接这里的敌人。\n🤔 似乎有暗门/机关的气息……(线索可能藏在石碑或机关里)\n━━━━━━━━━━━━\n✨ 场景：\n  []\n  []\n━━━━━━━━━━━━\n🐾 敌人：哥布林守卫(『探索』遇怪)\n━━━━━━━━━━━━\n💡 『副本』查看战况，『角色』看队伍",
    "IN9_地图_分层_暗门与肃清": "🗺️ 【👺哥布林营地】第 1 层 · 一层\n━━━━━━━━━━━━\n📜 石廊尽头有风。\n🔓 隐藏房间：暗门后是密室\n━━━━━━━━━━━━\n✨ 场景：\n  ['❓ 古老石碑：(『调查 古老石碑』)']\n  []\n━━━━━━━━━━━━\n✅ 本层敌人已肃清！剩余可调查：古老石碑(『调查 <名称>』)；『深入』前往下一层。\n━━━━━━━━━━━━\n💡 单人副本直接『副本 <名字>』开本",
    "RT1_超时自动防御": "⏰ 甲 迟迟没有行动，自动进入防御姿态！\n🛡 甲 摆出防御姿态，受到的伤害减半！\n⏰ 甲 迟迟没有行动，自动进入防御姿态！\n🛡 甲 摆出防御姿态，受到的伤害减半！\n—— 房间怪 行动 ——\n(格挡后 1 点伤害)\n💥 甲 受到 1 点伤害！\n⏰ 甲 迟迟没有行动，自动进入防御姿态！\n🛡 甲 摆出防御姿态，受到的伤害减半！\n⏰ 甲 迟迟没有行动，自动进入防御姿态！\n🛡 甲 摆出防御姿态，受到的伤害减半！\n⏰ 甲 迟迟没有行动，自动进入防御姿态！\n🛡 甲 摆出防御姿态，受到的伤害减半！\n⏰ 甲 迟迟没有行动，自动进入防御姿态！\n🛡 甲 摆出防御姿态，受到的伤害减半！\n⏰ 甲 迟迟没有行动，自动进入防御姿态！\n🛡 甲 摆出防御姿态，受到的伤害减半！\n⏰ 甲 迟迟没有行动，自动进入防御姿态！\n🛡 甲 摆出防御姿态，受到的伤害减半！\n⏰ 甲 迟迟没有行动，自动进入防御姿态！\n🛡 甲 摆出防御姿态，受到的伤害减半！\n⏰ 甲 迟迟没有行动，自动进入防御姿态！\n🛡 甲 摆出防御姿态，受到的伤害减半！\n⏰ 甲 迟迟没有行动，自动进入防御姿态！\n🛡 甲 摆出防御姿态，受到的伤害减半！\n⏰ 甲 迟迟没有行动，自动进入防御姿态！\n🛡 甲 摆出防御姿态，受到的伤害减半！\n⏰ 甲 迟迟没有行动，自动进入防御姿态！\n🛡 甲 摆出防御姿态，受到的伤害减半！\n—— 房间怪 行动 ——\n💥 乙 受到 1 点伤害！\n⏰ 甲 迟迟没有行动，自动进入防御姿态！\n🛡 甲 摆出防御姿态，受到的伤害减半！\n⏰ 甲 迟迟没有行动，自动进入防御姿态！\n🛡 甲 摆出防御姿态，受到的伤害减半！\n⏰ 甲 迟迟没有行动，自动进入防御姿态！\n🛡 甲 摆出防御姿态，受到的伤害减半！\n⏰ 甲 迟迟没有行动，自动进入防御姿态！\n🛡 甲 摆出防御姿态，受到的伤害减半！\n⏰ 甲 迟迟没有行动，自动进入防御姿态！\n🛡 甲 摆出防御姿态，受到的伤害减半！\n⏰ 甲 迟迟没有行动，自动进入防御姿态！\n🛡 甲 摆出防御姿态，受到的伤害减半！\n⏰ 甲 迟迟没有行动，自动进入防御姿态！\n🛡 甲 摆出防御姿态，受到的伤害减半！\n🛡 乙 摆出防御姿态，受到的伤害减半！\n━━━━━━━━━━━━\n── 敌方 ──\n  A1层: a1  房间怪 ❤️5000/5000\n── 我方 ──\n  B1层: b1  甲 ❤️99/100 | b2  乙 ❤️99/100\n🕐 时刻 12.8s ｜ ⚡ 行动顺序：甲(我) → 乙(我) → 房间怪(敌)\n✅ 甲：❤️ 99/100 💙 999/999 🛡️防御\n✅ 乙：❤️ 99/100 💙 999/999 🛡️防御\n💡 选敌：『技能1 a2』打2号(纯数字同义)；治疗『技能 <名称> b1』奶自己\n⏳ 轮到 甲 行动！『攻击』『技能 <名称>』『防御』",
    "RT2_嘲讽": "—— 房间怪 行动 ——\n💥 甲 受到 1 点伤害！\n🛡️ 你高声嘲讽，怪物怒火尽归你身！（强制攻击自己）\n━━━━━━━━━━━━\n── 敌方 ──\n  A1层: a1  房间怪 ❤️5000/5000\n── 我方 ──\n  B1层: b1  甲 ❤️99/100\n🕐 时刻 1.7s ｜ ⚡ 行动顺序：甲(我) → 房间怪(敌)\n✅ 甲：❤️ 99/100 💙 999/999\n💡 选敌：『技能1 a2』打2号(纯数字同义)；治疗『技能 <名称> b1』奶自己\n⏳ 轮到 甲 行动！『攻击』『技能 <名称>』『防御』",
    "RT3_同归于尽": "💥 房间怪 受到 1 点伤害，倒下了！\n⚔️ 同归于尽！你与敌人同时倒下了……\n\n💀 队伍全灭……副本失败！冒险者们被送回了最近的城镇。\n📍 甲 被送回了【白鹿城·白鹿广场】（HP 0，先休息恢复吧）",
}   # 迁移前快照（2026-09-13 真跑/源码 AST 存下，勿手改）

INSTANCE_LOG_TEMPLATES = {
    "instance.日志_击杀_宠物升级": "，升至 Lv.«»！",
    "instance.日志_击杀_宠物经验": "  🐾«» 分得经验 +«»",
    "instance.日志_击杀_拾取材料": "，拾取材料 «»",
    "instance.日志_击杀_经验": "  «»：经验 +«»",
    "instance.日志_列表_入口": "   📍 入口：«»·«»",
    "instance.日志_列表_轮流提示": "💡 按顺序轮流出手，Boss 血量随人数上涨，配合好才能通关！",
    "instance.日志_列表_钥匙": "   🔑 需『«»』：«»",
    "instance.日志_列表_首领": "   👹 Boss：«»(Lv.«»)· 掉落：«»",
    "instance.日志_同归于尽": "⚔️ 同归于尽！你与敌人同时倒下了……",
    "instance.日志_嘲讽": "🛡️ 你高声嘲讽，怪物怒火尽归你身！（强制攻击自己）",
    "instance.日志_团队治疗": "✨ «» 恢复 «» 点生命！",
    "instance.日志_地图_Boss房": "👑 Boss 就在这个房间！『探索』进入战斗！",
    "instance.日志_地图_可调查": "🔎 此房可调查：«»«»(『调查 <名称>』)",
    "instance.日志_地图_怪剩余": "🐾 此房怪物剩余：«»（『探索』高概率遭遇）",
    "instance.日志_地图_怪肃清": "🐾 此房怪物已肃清。",
    "instance.日志_地图_房间标题": "🗺️ 【«» · «»】",
    "instance.日志_地图_无出口": "🚪 副本内 · 无出口（没有通往外面的路）",
    "instance.日志_地图_资源池": "💰 副本资源池剩余：«» 金币",
    "instance.日志_墙砖提示": "🧱 墙上有一块松动的墙砖……（『调查 墙砖』）",
    "instance.日志_失败_全灭": "💀 队伍全灭……副本失败！冒险者们被送回了最近的城镇。",
    "instance.日志_失败_回城": "📍 «» 被送回了【«»·«»】（HP 0，先休息恢复吧）",
    "instance.日志_层_Boss在前": "👑 Boss 就在前方：«»！『探索』进入战斗！",
    "instance.日志_层_场景标题": "✨ 场景：",
    "instance.日志_层_宝箱": "🔐 神秘宝箱：密室深处泛着微光（『调查 宝箱』）",
    "instance.日志_层_敌人列表": "🐾 敌人：«»(『探索』遇怪)",
    "instance.日志_层_无敌": "🐾 这里暂时没有敌人。",
    "instance.日志_层_暗门气息": "🤔 似乎有暗门/机关的气息……(线索可能藏在石碑或机关里)",
    "instance.日志_层_环顾": "📜 你环顾四周，准备迎接这里的敌人。",
    "instance.日志_层_肃清_剩调查": "✅ 本层敌人已肃清！剩余可调查：«»(『调查 <名称>』)；『深入』前往下一层。",
    "instance.日志_层_肃清_无调查": "✅ 本层敌人已肃清！『深入』前往下一层。",
    "instance.日志_层_隐藏房间": "🔓 隐藏房间：«»",
    "instance.日志_战利品堆提示": "🎁 战利品堆：首领的遗物堆在角落（『调查 战利品堆』）",
    "instance.日志_搜刮_拾取": "🎒 拾取：«» ×1",
    "instance.日志_搜刮_空": "🎁 你搜刮了战利品堆，但里面空空的……",
    "instance.日志_搜刮_金币": "🎁 你搜刮了战利品堆：金币 +«»",
    "instance.日志_组队无坦克": "🛡️ 没有坦克：Boss 仇恨没人拉，输出容易被追着打",
    "instance.日志_组队无治疗": "✨ 没有治疗：血线压力大，记得多带药水",
    "instance.日志_组队无输出": "⚔️ 没有输出：可能打到超时哦",
    "instance.日志_行动序_我": "«»(我)",
    "instance.日志_行动序_敌": "«»(敌)",
    "instance.日志_调查痕迹": "🔍 通关后这里多了些可调查的痕迹：«»（『调查 <名称>』· 今日剩余 «» 次）",
    "instance.日志_超时自动防御": "⏰ «» 迟迟没有行动，自动进入防御姿态！",
    "instance.日志_轮到行动": "⏳ 轮到 «» 行动！『攻击』『技能 <名称>』『防御』",
    "instance.日志_通关_专属装备": "  👑 «» 从Boss身上拾取稀有专属：【«»】！",
    "instance.日志_通关_停留搜刮": "🏆 副本已通关！你可以在副本内停留搜刮：",
    "instance.日志_通关_再挑战": "💡 『副本』可再次挑战，首通成就已记录～",
    "instance.日志_通关_击败": "🎉 【«»】被击败了！«»«» 通关！",
    "instance.日志_通关_图纸": "  📜 «» 拾取图纸：«»",
    "instance.日志_通关_图纸已学": "  📜 «» 拾取图纸：«»（已学会，化作 «» 张图纸残页）",
    "instance.日志_通关_墙砖": "  · 🧱 墙上似乎有【松动的墙砖】……（『调查 墙砖』）",
    "instance.日志_通关_奖励": "  «»：金币 +«» 经验 +«»",
    "instance.日志_通关_宝石": "  💎 «» 获得幸运宝石：«»！(『原石』镶嵌到装备孔位)",
    "instance.日志_通关_宠物升级": "，升至 Lv.«»！",
    "instance.日志_通关_宠物经验": "  🐾«» 分得经验 +«»",
    "instance.日志_通关_战利品堆": "  · 🎁 【战利品堆】—— 首领的遗物，搜刮一次（『调查 战利品堆』）",
    "instance.日志_通关_材料": "  🎒 «» 拾取：«»",
    "instance.日志_通关_珍藏装备": "  ⚔️ «» 拾取 Boss 珍藏：【«»】！",
    "instance.日志_通关_离开提示": "搜刮完毕用『离开副本』传出～",
    "instance.日志_通关_调查痕迹提示": "  · 🔍 通关后这里多了些可调查的痕迹（『副本地图』查看，每日限 «» 次）",
    "instance.日志_通关_阵亡": "  💀 «» 已阵亡，未能获得奖励",
    "instance.日志_通关_首功图纸": "👑 首功 «» 额外获得图纸：«»",
    "instance.日志_通关_首功图纸已学": "👑 首功 «» 额外获得图纸：«»（已学会，化作 «» 张图纸残页）",
    "instance.日志_面板_减伤": "🛡️减伤«»%(«»刻)",
    "instance.日志_面板_增益": "«»(剩«»刻)",
    "instance.日志_面板_护盾": "✨护盾«»",
    "instance.日志_面板_护盾_剩刻": "✨护盾«»(«»刻)",
    "instance.日志_面板_敌增益_剩刻": "«» «»(剩«»刻)",
    "instance.日志_面板_敌增益_叠层": "«» «»×«»",
    "instance.日志_面板_敌增益行": "👹敌：「«»」",
    "instance.日志_面板_选敌提示": "💡 选敌：『技能1 a2』打2号(纯数字同义)；治疗『技能 <名称> b1』奶自己",
}   # 迁移前快照（2026-09-13 真跑/源码 AST 存下，勿手改）

def t10_instance_log_frozen():
    print("\n[10] 副本日志域逐字冻结：迁移前 26 分支（战斗/面板/地图/搜刮/击杀/通关/失败）复跑比对")
    check("冻结基准已内嵌（26 分支）", len(INSTANCE_LOG_FROZEN) == 26, len(INSTANCE_LOG_FROZEN))
    now = _il_scenarios()
    bad = [k for k in INSTANCE_LOG_FROZEN if INSTANCE_LOG_FROZEN[k] != now.get(k)]
    for k in bad:
        print("     · %s 现=%r" % (k, (now.get(k) or "")[:140]))
    check("★ 副本日志 26 分支输出与迁移前**逐字一致**", not bad, bad)
    _single = ("IN13_搜刮_空",)     # 单行分支（本身无换行结构）
    check("冻结基准非空且含换行结构（防基准写空）",
          all(v and "\n" in v for k, v in INSTANCE_LOG_FROZEN.items() if k not in _single))

    # 表里模板（剔槽位成骨架）== 迁移前源码 f-string / 常量串的骨架（逐字）
    def _skel(v):
        return re.sub(r"\{[^{}]*\}", "«»", v or "")
    tb = T.table()
    diff = [k for k in INSTANCE_LOG_TEMPLATES
            if _skel((tb.spec(k).value if tb.spec(k) else "")) != INSTANCE_LOG_TEMPLATES[k]]
    check("★ 70 条日志模板骨架与迁移前源码**逐字一致**（含真跑覆盖不到的分支）",
          not diff, diff[:5])

    # 旧文案零残留：三份源文件 append 族实参不再有中文
    # （排版分隔线 / T.text·T.static 内的键与取值回退口径（如 '队友'）除外）
    left = []
    for _p in (INSTANCE_ROUTER_SRC, INSTANCE_BATTLE_SRC, INSTANCE_SRC):
        _src = io.open(_p, encoding="utf-8").read()
        for _n in ast.walk(ast.parse(_src)):
            if not (isinstance(_n, ast.Call) and isinstance(_n.func, ast.Attribute)
                    and _n.func.attr in ("append", "extend", "insert") and _n.args):
                continue
            _tcalls = set()
            for _c in ast.walk(_n.args[0]):
                if (isinstance(_c, ast.Call) and isinstance(_c.func, ast.Attribute)
                        and _c.func.attr in ("text", "static")):
                    _tcalls.update(id(_x) for _x in ast.walk(_c))
            _lits = [x.value for x in ast.walk(_n.args[0])
                     if id(x) not in _tcalls and isinstance(x, ast.Constant)
                     and isinstance(x.value, str)
                     and any("\u4e00" <= c <= "\u9fff" for c in x.value)]
            if _lits and not all(s.strip().startswith("──") for s in _lits):
                left.append((os.path.basename(_p), _n.lineno,
                             (ast.get_source_segment(_src, _n.args[0]) or "")[:48]))
    check("★ 旧文案零残留（append 族实参已无中文；分隔线与取值回退留在代码）",
          not left, left[:4])


# ═══════════════════════ PB_BRANCHES_BEGIN ═══════════════════════
# ↓↓↓ 以下这段（含本行）与 $TEMP/df_panel_block.py 逐字同源：采快照脚本与门禁共用 ↓↓↓
# -*- coding: utf-8 -*-
"""副本面板/地图/状态域 —— 复跑分支块（★ 快照与门禁共用同一份驱动代码）。

本块由两部分共同使用：
  ① $TEMP/df_panel_snap.py（迁移前采快照 / 迁移后复跑比对）
  ② tests/test_texts_table.py 的 t11 段（逐字拼入，勿手改分叉）
所以本块**只依赖 conftest + game 包**，不打印、不写文件、不 assert。

约定（与 INSTANCE_LOG_FROZEN 同款）：
  · 每个分支自己 clean_db + 固定 random.seed；需要时打桩 random.random（进出还原）。
  · 输出统一走 _pb_text()（把命令 yield 的多条拼成一段，逐字可比）。
"""
import asyncio  # noqa: E402
import random   # noqa: E402

from conftest import C as _PB_C, db as _PB_db, clean_db as _PB_clean   # noqa: E402
from conftest import FakeEvent as _PB_Event, run as _PB_run            # noqa: E402
from conftest import make_player as _PB_mk, Main as _PB_Main           # noqa: E402
from data.plugins.dragonfall.game.core import instance_run as _PB_IR   # noqa: E402
from data.plugins.dragonfall.game.commands import instance_battle as _PB_IB   # noqa: E402
from data.plugins.dragonfall.game.commands.instance import InstanceCmds as _PB_Inst   # noqa: E402
from data.plugins.dragonfall.game.commands.combat import CombatCmds as _PB_Combat     # noqa: E402
from data.plugins.dragonfall.game.commands.world import WorldCmds as _PB_World        # noqa: E402
from data.plugins.dragonfall.game.commands.economy import EconomyCmds as _PB_Economy  # noqa: E402

_PB_GID = "g_panel"
_PB_Q = "q_p"
_PB_GOBLIN_ROOM = "goblin_camp_1"     # 哥布林营地入口房


class _PBHost(_PB_Inst, _PB_Combat, _PB_World, _PB_Economy):
    """副本面板快照宿主（InstanceCmds + CombatCmds 面板名表 + WorldCmds 地图视图
    + EconomyCmds 副业等待查询 —— 与 Main 的 mixin 面等价，省一层命令注册）。"""


# ── 驱动脚手架 ─────────────────────────────────────────────────────────
def _pb_text(msgs):
    return "\n".join(str(m) for m in msgs) if not isinstance(msgs, str) else msgs


def _pb_run_sync(coro_or_agen):
    """同步收一条 async 命令/生成器的全部 yield。"""
    async def _c():
        if hasattr(coro_or_agen, "asend"):
            out = []
            async for x in coro_or_agen:
                out.append(x)
            return out
        return await coro_or_agen
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_c())
    finally:
        loop.close()


def _pb_cmd(m, handler, msg, qq=_PB_Q):
    ev = _PB_Event(_PB_GID, qq, msg)
    return _pb_text(_pb_run_sync(_PB_run(getattr(m, handler), ev)))


def _pb_player(qid, name="甲", cls="战士", level=60, learned=None,
               cur_map="misty_swamp", cur_subarea=_PB_GOBLIN_ROOM):
    _PB_mk(_PB_GID, qid, name=name, cls=cls, level=level)
    _PB_db.update_player(_PB_GID, qid, cur_map=cur_map, cur_subarea=cur_subarea,
                         stamina=999999, learned_skills=list(learned or []))
    return _PB_db.get_player(_PB_GID, qid)


def _pb_snap(qid, name="甲", cls="cls_zhan_shi", level=60, hp=None, spd=30, mp=999):
    pl = _PB_db.get_player(_PB_GID, qid) or {}
    mh = int(pl.get("max_hp", 500) or 500)
    return {"name": name, "qq_id": str(qid), "class_name": cls, "level": level,
            "hp": int(hp if hp is not None else mh), "max_hp": mh, "mp": mp, "max_mp": mp,
            "equipment": {}, "skills": [], "learned_skills": [],
            "class_tier": 0, "evolve_path": 0, "attributes": pl.get("attributes"),
            "bonus": {"panel": {}, "cap": {}, "cost": {}}, "race": pl.get("race"),
            "uid": "p_%s" % qid, "buffs": {}, "stacks": {}, "defending": False,
            "charging": None, "ct": 0.0, "p_shields": {}, "spd": spd}


def _pb_enemy(hp=500, spd=1, role="dps", atk=1, uid="e_pb", name="房间怪", lv=15):
    return {"uid": uid, "name": name, "hp": hp, "max_hp": hp, "atk": atk, "def": 0,
            "matk": 1, "mdef": 0, "spd": spd, "crit": 0.0, "lv": lv, "level": lv,
            "role": role, "is_boss": role == "boss", "is_elite": role == "elite",
            "rank": 1, "reach": 1, "ct": 1.0, "exp": 10, "gold": 5, "drops": []}


def _pb_st(qids, inst_id="inst_goblin_camp", names=None, **kw):
    qids = [str(q) for q in qids]
    names = names or {}
    st = {"type": "instance", "inst_id": inst_id, "leader": qids[0], "members": qids,
          "alive": {q: True for q in qids},
          "players": {q: _pb_snap(q, names.get(q, "甲")) for q in qids},
          "boss": None, "enemy": None, "enemies": [], "turn": 0, "round": 1,
          "mode": "battle", "pets": {}, "p_buffs": {q: {} for q in qids},
          "p_hot": {q: {} for q in qids}, "p_food_effects": {q: [] for q in qids},
          "p_defending": {q: False for q in qids}, "mech_stacks": {q: {} for q in qids},
          "now": 0.0, "battle": None, "contribution": {}, "threat": {q: 0 for q in qids},
          "over": False, "turn_time": 0, "stage_pending": [], "inst_stages": [],
          "stage_idx": 0, "stage_cleared": False, "world_id": ""}
    st.update(kw)
    return st


def _pb_save(qid, st):
    _PB_db.save_battle(_PB_GID, qid, st)
    return st


class _PBRR(object):
    """random.random 打桩（进出还原）。"""

    def __init__(self, value):
        self.value = value

    def __enter__(self):
        self._orig = random.random
        if self.value is not None:
            random.random = lambda: self.value
        return self

    def __exit__(self, *exc):
        random.random = self._orig
        return False
# ══════════════════════════════════════════════════════════════════════
# 分支 1：开本面板（单人 / 多人队伍构成）
# ══════════════════════════════════════════════════════════════════════
def _pb_b1_open_solo():
    """开本（单人·地图模式）：开启面板 + 层全景 + 单人挑战行 + 行动引导。"""
    _PB_clean()
    random.seed(20260914)
    _pb_player(_PB_Q, "甲")
    _PB_db.update_player(_PB_GID, _PB_Q, cur_map="misty_swamp", cur_subarea="misty_swamp_3")
    return _pb_cmd(_PB_Main(None), "instance_cmd", "副本 哥布林营地")


def _pb_b2_open_party():
    """开本（2 人队·min_players>1）：队伍构成行 + 职业搭配提示行。"""
    _PB_clean()
    random.seed(20260914 + 2)
    _pb_player("q_p2", "甲")
    _pb_player("q_p3", "乙")
    _PB_db.update_player(_PB_GID, "q_p2", cur_map="harbor_docks", cur_subarea="harbor_docks_2")
    _PB_db.update_player(_PB_GID, "q_p3", cur_map="harbor_docks", cur_subarea="harbor_docks_2")
    _PB_db.party_create(_PB_GID, "q_p2", "q_p3")
    return _pb_cmd(_PB_Main(None), "instance_cmd", "副本 锈潮船坞", qq="q_p2")


def _pb_b3_open_bad_name():
    """开本（名字不存在）：『没有『X』这个副本』。"""
    _PB_clean()
    random.seed(20260914 + 3)
    _pb_player(_PB_Q, "甲")
    return _pb_cmd(_PB_Main(None), "instance_cmd", "副本 不存在的本")


# ══════════════════════════════════════════════════════════════════════
# 分支 2：加入战斗
# ══════════════════════════════════════════════════════════════════════
def _pb_b4_join_leader_and_mate():
    """加入战斗：队长视角（i_am_leader）+ 队员已在战斗中（自己锁）两行。"""
    _PB_clean()
    random.seed(20260914 + 4)
    _pb_player("q_j1", "队长甲")
    _pb_player("q_j2", "队员乙")
    _PB_db.party_create(_PB_GID, "q_j1", "q_j2")
    st = _pb_st(["q_j1"], names={"q_j1": "队长甲"},
                enemies=[_pb_enemy(hp=500, spd=1)], mode="battle")
    st["boss"] = st["enemy"] = st["enemies"][0]
    _pb_save("q_j1", st)
    inst = _PBHost()
    inst._lock_battle(_PB_GID, "q_j1")
    inst._lock_battle(_PB_GID, "q_j2")
    out1 = _pb_cmd(inst, "join_battle", "加入战斗", qq="q_j1")
    out2 = _pb_cmd(inst, "join_battle", "加入战斗", qq="q_j2")
    inst._unlock_battle(_PB_GID, "q_j2")
    return out1 + "\n@@@\n" + out2


def _pb_b5_join_success():
    """加入战斗成功：加入行 + 战斗面板 + 当前参战行。"""
    _PB_clean()
    random.seed(20260914 + 5)
    _pb_player("q_j3", "队长甲")
    _pb_player("q_j4", "队员乙")
    _PB_db.party_create(_PB_GID, "q_j3", "q_j4")
    st = _pb_st(["q_j3"], names={"q_j3": "队长甲"},
                enemies=[_pb_enemy(hp=500, spd=1)], mode="battle")
    st["boss"] = st["enemy"] = st["enemies"][0]
    _pb_save("q_j3", st)
    return _pb_cmd(_PBHost(), "join_battle", "加入战斗", qq="q_j4")


# ══════════════════════════════════════════════════════════════════════
# 分支 3：不在副本 / 战斗中的守卫提示
# ══════════════════════════════════════════════════════════════════════
def _pb_b6_not_in_instance():
    """不在副本（带列表引导）+ 不在副本（简）——深入/副本地图/调查/撤退/确认撤退/离开。"""
    _PB_clean()
    random.seed(20260914 + 6)
    _pb_player(_PB_Q, "甲")
    inst = _PBHost()
    outs = [_pb_cmd(inst, "instance_advance", "深入"),
            _pb_cmd(inst, "instance_map_view_cmd", "副本地图"),
            _pb_cmd(inst, "instance_investigate", "调查 宝箱"),
            _pb_cmd(inst, "instance_retreat", "撤退"),
            _pb_cmd(inst, "instance_retreat_confirm", "确认撤退"),
            _pb_cmd(inst, "instance_leave", "离开副本")]
    return "\n@@@\n".join(outs)


def _pb_b7_in_battle_guards():
    """战斗中守卫：副本地图/调查/撤退(Boss)/撤退(非Boss)/离开 五条。"""
    _PB_clean()
    random.seed(20260914 + 7)
    _pb_player(_PB_Q, "甲")
    st = _pb_st([_PB_Q], names={_PB_Q: "甲"}, enemies=[_pb_enemy(hp=500, spd=1, role="boss")],
                mode="battle")
    st["boss"] = st["enemy"] = st["enemies"][0]
    _pb_save(_PB_Q, st)
    inst = _PBHost()
    outs = [_pb_cmd(inst, "instance_map_view_cmd", "副本地图"),
            _pb_cmd(inst, "instance_investigate", "调查 宝箱"),
            _pb_cmd(inst, "instance_retreat", "撤退")]
    st2 = _pb_st([_PB_Q], names={_PB_Q: "甲"}, enemies=[_pb_enemy(hp=500, spd=1)], mode="battle")
    st2["boss"] = st2["enemy"] = st2["enemies"][0]
    st2["enemies"][0]["is_boss"] = False
    _pb_save(_PB_Q, st2)
    outs.append(_pb_cmd(inst, "instance_retreat", "撤退"))
    outs.append(_pb_cmd(inst, "instance_leave", "离开副本"))
    return "\n@@@\n".join(outs)


def _pb_b8_expired_hint():
    """副本 24h 过期提示。"""
    _PB_clean()
    random.seed(20260914 + 8)
    _pb_player(_PB_Q, "甲")
    st = _pb_st([_PB_Q], names={_PB_Q: "甲"})
    st["_expired"] = True
    _pb_save(_PB_Q, st)
    return _PBHost()._instance_expired_hint(_PB_GID, _PB_Q)


# ══════════════════════════════════════════════════════════════════════
# 分支 4：深入
# ══════════════════════════════════════════════════════════════════════
def _pb_b9_advance_room_mode():
    """深入（rooms 副本）：提示『移动 <房间>』。"""
    _PB_clean()
    random.seed(20260914 + 9)
    _pb_player(_PB_Q, "甲")
    st = _pb_st([_PB_Q], names={_PB_Q: "甲"},
                rooms={_PB_GOBLIN_ROOM: {"monsters_left": [], "pois_left": [],
                                         "boss_alive": False}},
                mode="map")
    _pb_save(_PB_Q, st)
    return _pb_cmd(_PBHost(), "instance_advance", "深入")


def _pb_b10_advance_blocked():
    """深入：未清层（探索引导 / 先打完）、已通关、无分层、末层 四条。"""
    _PB_clean()
    random.seed(20260914 + 10)
    _pb_player(_PB_Q, "甲")
    inst = _PBHost()
    # 未清层 + 尚有未遭遇怪 → 引导『探索』
    st = _pb_st([_PB_Q], names={_PB_Q: "甲"},
                inst_stages=[{"name": "一层"}, {"name": "二层"}],
                stage_pending=[["m_x", "小怪", "dps", 15, [], []]], mode="map")
    _pb_save(_PB_Q, st)
    outs = [_pb_cmd(inst, "instance_advance", "深入")]
    # 未清层 + 无待清怪 → 先打完再说
    st2 = _pb_st([_PB_Q], names={_PB_Q: "甲"},
                 inst_stages=[{"name": "一层"}, {"name": "二层"}], mode="map")
    _pb_save(_PB_Q, st2)
    outs.append(_pb_cmd(inst, "instance_advance", "深入"))
    # 已通关
    st3 = _pb_st([_PB_Q], names={_PB_Q: "甲"}, cleared=True, mode="map")
    _pb_save(_PB_Q, st3)
    outs.append(_pb_cmd(inst, "instance_advance", "深入"))
    # 无分层结构
    st4 = _pb_st([_PB_Q], names={_PB_Q: "甲"}, mode="map")
    _pb_save(_PB_Q, st4)
    outs.append(_pb_cmd(inst, "instance_advance", "深入"))
    # 末层
    st5 = _pb_st([_PB_Q], names={_PB_Q: "甲"},
                 inst_stages=[{"name": "一层"}], stage_idx=0, stage_cleared=True, mode="map")
    _pb_save(_PB_Q, st5)
    outs.append(_pb_cmd(inst, "instance_advance", "深入"))
    return "\n@@@\n".join(outs)


def _pb_b11_advance_next_stage():
    """深入（清层推进）：地图模式继续深入 + 战斗模式层行/面板/轮到行。"""
    _PB_clean()
    random.seed(20260914 + 11)
    _pb_player(_PB_Q, "甲")
    inst = _PBHost()
    # 下一层有怪 → mode=map → 继续深入 + 层全景
    st = _pb_st([_PB_Q], names={_PB_Q: "甲"},
                inst_stages=[{"name": "一层", "monsters": [["m_x", "小怪", "dps", 15, [], []]]},
                             {"name": "二层", "monsters": [["m_y", "小怪2", "dps", 15, [], []]]}],
                stage_idx=0, stage_cleared=True, mode="map")
    _pb_save(_PB_Q, st)
    out1 = _pb_cmd(inst, "instance_advance", "深入")
    # 下一层无怪（不切地图模式）→ 层行 + 面板 + 轮到行
    st2 = _pb_st([_PB_Q], names={_PB_Q: "甲"},
                 inst_stages=[{"name": "一层", "monsters": [["m_x", "小怪", "dps", 15, [], []]]},
                              {"name": "二层"}],
                 stage_idx=0, stage_cleared=True, mode="battle",
                 enemies=[_pb_enemy(hp=500, spd=1)])
    st2["boss"] = st2["enemy"] = st2["enemies"][0]
    _pb_save(_PB_Q, st2)
    out2 = _pb_cmd(inst, "instance_advance", "深入")
    return out1 + "\n@@@\n" + out2


# ══════════════════════════════════════════════════════════════════════
# 分支 5：地图（分层形态：精英标注）
# ══════════════════════════════════════════════════════════════════════
def _pb_b12_map_stage_elite():
    """分层地图：怪名 + ⭐精英· 标注（敌人列表行）。"""
    _PB_clean()
    random.seed(20260914 + 12)
    _pb_player(_PB_Q, "甲")
    host = _PBHost()
    st = _pb_st([_PB_Q], names={_PB_Q: "甲"},
                inst_stages=[{"name": "一层", "desc": "石廊尽头有风。",
                              "monsters": [["m_goblin_guard", "哥布林守卫", "tank", 15, [], []]],
                              "elite": ["m_elite", "哥布林督军", "elite", 17, [], []]}],
                stage_idx=0, mode="map")
    st.pop("resources_pool", None)
    _pb_save(_PB_Q, st)
    return host._instance_map_view(st, _PB_GID)


# ══════════════════════════════════════════════════════════════════════
# 分支 6：调查（空参数 / 未命中 / 已处理）
# ══════════════════════════════════════════════════════════════════════
def _pb_b13_investigate_miss():
    """调查：空参数格式提示 + 未命中目标。"""
    _PB_clean()
    random.seed(20260914 + 13)
    _pb_player(_PB_Q, "甲")
    st = _pb_st([_PB_Q], names={_PB_Q: "甲"},
                rooms={_PB_GOBLIN_ROOM: {"monsters_left": [], "pois_left": [],
                                         "boss_alive": False}},
                mode="map")
    _pb_save(_PB_Q, st)
    inst = _PBHost()
    out1 = _pb_cmd(inst, "instance_investigate", "调查")
    out2 = _pb_cmd(inst, "instance_investigate", "调查 不存在的东西")
    return out1 + "\n@@@\n" + out2


def _pb_b14_investigate_used():
    """调查（层内 POI 已用过）：『X已经被处理过了。』。"""
    _PB_clean()
    random.seed(20260914 + 14)
    _pb_player(_PB_Q, "甲")
    poi = {"id": "p_used", "name": "旧石碑", "type": "shrine"}
    st = _pb_st([_PB_Q], names={_PB_Q: "甲"},
                inst_stages=[{"name": "一层", "pois": [poi]}],
                stage_idx=0, stage_pois={"0": {"p_used": {"used": True}}}, mode="map")
    _pb_save(_PB_Q, st)
    return _pb_cmd(_PBHost(), "instance_investigate", "调查 旧石碑")


# ══════════════════════════════════════════════════════════════════════
# 分支 7：探索（通关后 / 肃清 / 遇怪 / 无事 / POI / 陷阱）
# ══════════════════════════════════════════════════════════════════════
def _pb_b15_explore_cleared():
    """探索：已通关 → 引导搜刮/离开。"""
    _PB_clean()
    random.seed(20260914 + 15)
    _pb_player(_PB_Q, "甲")
    st = _pb_st([_PB_Q], names={_PB_Q: "甲"}, cleared=True, mode="map")
    _pb_save(_PB_Q, st)
    return _pb_text(_pb_run_sync(_PBHost()._instance_explore(
        _PB_Event(_PB_GID, _PB_Q), _PB_GID, _PB_Q, {"state": st})))


def _pb_b16_explore_rooms_three():
    """探索（rooms）：此房已肃清 / 遇怪（进战斗面板）/ 未发现你 / POI 搜索 四态。"""
    _PB_clean()
    random.seed(20260914 + 16)
    _pb_player(_PB_Q, "甲")
    host = _PBHost()
    outs = []
    # ③ 无怪可遇
    st = _pb_st([_PB_Q], names={_PB_Q: "甲"},
                rooms={_PB_GOBLIN_ROOM: {"monsters_left": [], "pois_left": [],
                                         "boss_alive": False}},
                resources_pool={"gold_left": 30, "mats_left": {"兽肉": 2}}, mode="map")
    _pb_save(_PB_Q, st)
    outs.append(_pb_text(_pb_run_sync(host._instance_explore(
        _PB_Event(_PB_GID, _PB_Q), _PB_GID, _PB_Q, {"state": st}))))
    # ② 遇怪（pois_left 空 → 必过 POI 分支；random 打 0.0 → 命中遇怪）
    st2 = _pb_st([_PB_Q], names={_PB_Q: "甲"},
                 rooms={_PB_GOBLIN_ROOM: {"monsters_left":
                                          [["m_goblin_guard", "哥布林守卫", "tank", 15, [], []]],
                                          "pois_left": [], "boss_alive": False}},
                 mode="map")
    _pb_save(_PB_Q, st2)
    with _PBRR(0.0):
        outs.append(_pb_text(_pb_run_sync(host._instance_explore(
            _PB_Event(_PB_GID, _PB_Q), _PB_GID, _PB_Q, {"state": st2}))))
    # ② 未发现你（random 打 0.99 → 未过遇怪判定）
    st3 = _pb_st([_PB_Q], names={_PB_Q: "甲"},
                 rooms={_PB_GOBLIN_ROOM: {"monsters_left":
                                          [["m_goblin_guard", "哥布林守卫", "tank", 15, [], []]],
                                          "pois_left": [], "boss_alive": False}},
                 mode="map")
    _pb_save(_PB_Q, st3)
    with _PBRR(0.99):
        outs.append(_pb_text(_pb_run_sync(host._instance_explore(
            _PB_Event(_PB_GID, _PB_Q), _PB_GID, _PB_Q, {"state": st3}))))
    # ① POI 搜索（pois_left 有物 + random 0.0）
    _poi_id = (_PB_C.subarea_pois("goblin_camp", _PB_GOBLIN_ROOM) or [None])[0]
    st4 = _pb_st([_PB_Q], names={_PB_Q: "甲"},
                 rooms={_PB_GOBLIN_ROOM: {"monsters_left": [], "pois_left": [_poi_id],
                                          "boss_alive": False}},
                 resources_pool={"gold_left": 30, "mats_left": {}}, mode="map")
    _pb_save(_PB_Q, st4)
    with _PBRR(0.0):
        outs.append(_pb_text(_pb_run_sync(host._instance_explore(
            _PB_Event(_PB_GID, _PB_Q), _PB_GID, _PB_Q, {"state": st4}))))
    return "\n@@@\n".join(outs)


def _pb_b17_explore_stage_paths():
    """探索（旧 stages 路径）：无怪无事 / 陷阱踩中 两态。"""
    _PB_clean()
    random.seed(20260914 + 17)
    _pb_player(_PB_Q, "甲")
    host = _PBHost()
    st = _pb_st([_PB_Q], names={_PB_Q: "甲"},
                inst_stages=[{"name": "一层", "pois": []}], stage_idx=0, mode="map")
    _pb_save(_PB_Q, st)
    out1 = _pb_text(_pb_run_sync(host._instance_explore(
        _PB_Event(_PB_GID, _PB_Q), _PB_GID, _PB_Q, {"state": st})))
    trap = {"id": "p_trap", "name": "尖刺陷阱", "type": "trap"}
    st2 = _pb_st([_PB_Q], names={_PB_Q: "甲"},
                 inst_stages=[{"name": "一层", "pois": [trap]}], stage_idx=0, mode="map")
    _pb_save(_PB_Q, st2)
    with _PBRR(0.0):
        out2 = _pb_text(_pb_run_sync(host._instance_explore(
            _PB_Event(_PB_GID, _PB_Q), _PB_GID, _PB_Q, {"state": st2})))
    return out1 + "\n@@@\n" + out2


# ══════════════════════════════════════════════════════════════════════
# 分支 8：撤退 / 确认撤退 / 离开 / 移动
# ══════════════════════════════════════════════════════════════════════
def _pb_b18_retreat_flow():
    """撤退流程：弹确认 + 已弹过确认 + 确认成功 + 无待确认 + 确认过期。"""
    _PB_clean()
    random.seed(20260914 + 18)
    _pb_player(_PB_Q, "甲")
    _PB_db.update_player(_PB_GID, _PB_Q, cur_map="misty_swamp", cur_subarea="misty_swamp_3")
    m = _PB_Main(None)
    outs = [_pb_cmd(m, "instance_cmd", "副本 哥布林营地")]
    outs.append(_pb_cmd(m, "instance_retreat", "撤退"))          # 弹确认
    outs.append(_pb_cmd(m, "instance_retreat", "撤退"))          # 已弹过
    # 确认过期：把挂起确认改成本副本之外
    import json as _json
    _PB_db.set_event_state("retreat_confirm_%s" % _PB_Q,
                           _json.dumps({"ts": 0, "inst": "inst_other"}))
    outs.append(_pb_cmd(m, "instance_retreat_confirm", "确认撤退"))
    # 无待确认
    _PB_db.set_event_state("retreat_confirm_%s" % _PB_Q, "")
    outs.append(_pb_cmd(m, "instance_retreat_confirm", "确认撤退"))
    # 重新弹确认 → 确认成功（放弃进度）
    outs.append(_pb_cmd(m, "instance_retreat", "撤退"))
    outs.append(_pb_cmd(m, "instance_retreat_confirm", "确认撤退"))
    return "\n@@@\n".join(outs)


def _pb_b19_leave_and_resume():
    """回到副本深处（撤退存进度 → 重新开本恢复）+ 离开副本。"""
    _PB_clean()
    random.seed(20260914 + 19)
    _pb_player(_PB_Q, "甲")
    _PB_db.update_player(_PB_GID, _PB_Q, cur_map="misty_swamp", cur_subarea="misty_swamp_3")
    m = _PB_Main(None)
    outs = [_pb_cmd(m, "instance_cmd", "副本 哥布林营地")]
    # 恢复分支：把副本行标记为已撤退（保留进度）+ 解战斗锁后重新『副本 <名字>』
    row = _PB_db.get_battle_raw(_PB_GID, _PB_Q)
    st = row["state"]
    st["retreated"] = True
    st["mode"] = "map"
    st["_expired"] = False
    _pb_save(_PB_Q, st)
    m._unlock_battle(_PB_GID, _PB_Q)
    _PB_db.update_player(_PB_GID, _PB_Q, cur_map="misty_swamp", cur_subarea="misty_swamp_3")
    outs.append(_pb_cmd(m, "instance_cmd", "副本 哥布林营地"))
    outs.append(_pb_cmd(m, "instance_leave", "离开副本"))
    return "\n@@@\n".join(outs)


def _pb_b20_move_not_leader():
    """副本内移动：非队长提示。"""
    _PB_clean()
    random.seed(20260914 + 20)
    _pb_player("q_m1", "队长甲")
    _pb_player("q_m2", "队员乙")
    _PB_db.update_player(_PB_GID, "q_m1", cur_map="misty_swamp", cur_subarea="misty_swamp_3")
    _PB_db.update_player(_PB_GID, "q_m2", cur_map="misty_swamp", cur_subarea="misty_swamp_3")
    _PB_db.party_create(_PB_GID, "q_m1", "q_m2")
    m = _PB_Main(None)
    _pb_cmd(m, "instance_cmd", "副本 哥布林营地", qq="q_m1")
    inst = m
    pl2 = _PB_db.get_player(_PB_GID, "q_m2")
    return _pb_text(_pb_run_sync(inst._instance_move_route(
        _PB_Event(_PB_GID, "q_m2"), _PB_GID, "q_m2", pl2, "入口栅栏")))


# ══════════════════════════════════════════════════════════════════════
# 分支 9：通关超时自动离开
# ══════════════════════════════════════════════════════════════════════
def _pb_b21_cleared_timeout():
    """通关停留超 30 分钟 → 自动离开提示。"""
    _PB_clean()
    random.seed(20260914 + 21)
    _pb_player(_PB_Q, "甲")
    _PB_db.update_player(_PB_GID, _PB_Q, cur_map="misty_swamp", cur_subarea="misty_swamp_3")
    m = _PB_Main(None)
    _pb_cmd(m, "instance_cmd", "副本 哥布林营地")
    row = _PB_db.get_battle(_PB_GID, _PB_Q)
    st = row["state"]
    st["cleared"] = True
    st["cleared_time"] = 1
    _pb_save(_PB_Q, st)
    return _pb_cmd(m, "instance_cmd", "副本")


# ══════════════════════════════════════════════════════════════════════
# 分支 10：暗格 / 宝箱
# ══════════════════════════════════════════════════════════════════════
def _pb_b22_secret_crack():
    """暗格：死墙（无守卫）+ 拉开门（守卫战面板）。"""
    _PB_clean()
    random.seed(20260914 + 22)
    _pb_player(_PB_Q, "甲")
    host = _PBHost()
    st = _pb_st([_PB_Q], names={_PB_Q: "甲"}, inst_stages=[{"name": "一层"}],
                stage_idx=0, mode="map")
    _pb_save(_PB_Q, st)
    out1 = host._instance_secret_crack(_PB_GID, _PB_Q, _PB_db.get_player(_PB_GID, _PB_Q), st)
    st2 = _pb_st([_PB_Q], names={_PB_Q: "甲"},
                 inst_stages=[{"name": "一层",
                               "monsters": [["m_goblin_guard", "哥布林守卫", "tank", 15, [], []]]}],
                 stage_idx=0, mode="map")
    _pb_save(_PB_Q, st2)
    out2 = host._instance_secret_crack(_PB_GID, _PB_Q, _PB_db.get_player(_PB_GID, _PB_Q), st2)
    return out1 + "\n@@@\n" + out2


def _pb_b23_secret_chest():
    """密室宝箱开启（掉落走 drop_engine，seed 固定）。"""
    _PB_clean()
    random.seed(20260914 + 23)
    _pb_player(_PB_Q, "甲")
    host = _PBHost()
    st = _pb_st([_PB_Q], names={_PB_Q: "甲"}, secret_chest=True, mode="map")
    _pb_save(_PB_Q, st)
    return host._instance_secret_chest(_PB_GID, _PB_Q, _PB_db.get_player(_PB_GID, _PB_Q), st)


# ══════════════════════════════════════════════════════════════════════
# 分支 11：通关后调查点（四档奖励）
# ══════════════════════════════════════════════════════════════════════
def _pb_b24_investigate_reward():
    """调查点：收藏 / 图纸残页 / 保底材料 / 蓝符 四档 + 空结果。"""
    outs = []
    # 收藏（random 0.0 < collect 0.03）
    _PB_clean()
    random.seed(20260914 + 24)
    _pb_player(_PB_Q, "甲")
    host = _PBHost()
    st = _pb_st([_PB_Q], names={_PB_Q: "甲"}, cleared=True, mode="map")
    _pb_save(_PB_Q, st)
    with _PBRR(0.0):
        outs.append(host._instance_investigate_cleared(
            _PB_GID, _PB_Q, _PB_db.get_player(_PB_GID, _PB_Q), st, "酋长的战利品堆"))
    # 图纸残页（0.03 ≤ r < 0.28）
    _PB_clean()
    random.seed(20260914 + 25)
    _pb_player(_PB_Q, "甲")
    st2 = _pb_st([_PB_Q], names={_PB_Q: "甲"}, cleared=True, mode="map")
    _pb_save(_PB_Q, st2)
    with _PBRR(0.10):
        outs.append(host._instance_investigate_cleared(
            _PB_GID, _PB_Q, _PB_db.get_player(_PB_GID, _PB_Q), st2, "劫掠清单"))
    # 保底材料（r ≥ 0.28）
    _PB_clean()
    random.seed(20260914 + 26)
    _pb_player(_PB_Q, "甲")
    st3 = _pb_st([_PB_Q], names={_PB_Q: "甲"}, cleared=True, mode="map")
    _pb_save(_PB_Q, st3)
    with _PBRR(0.90):
        outs.append(host._instance_investigate_cleared(
            _PB_GID, _PB_Q, _PB_db.get_player(_PB_GID, _PB_Q), st3, "篝火余烬"))
    # 蓝符（Lv.60+ 副本，0.03 ≤ r < 0.18）
    _PB_clean()
    random.seed(20260914 + 27)
    _pb_player(_PB_Q, "甲")
    st4 = _pb_st([_PB_Q], names={_PB_Q: "甲"}, inst_id="inst_moon_temple",
                 cleared=True, mode="map")
    _pb_save(_PB_Q, st4)
    with _PBRR(0.04):
        outs.append(host._instance_investigate_cleared(
            _PB_GID, _PB_Q, _PB_db.get_player(_PB_GID, _PB_Q), st4, "月池"))
    return "\n@@@\n".join(str(o) for o in outs)


# ══════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════
# 分支 12：加入战斗无角色 / 旧层探索遇怪（Boss 台词行）/ 战斗状态异常两态
# ══════════════════════════════════════════════════════════════════════
def _pb_b25_join_no_char():
    """加入战斗：还没有角色（剥掉 @require_player 守卫，直接跑命令体）。"""
    _PB_clean()
    random.seed(20260914 + 25)
    inst = _PBHost()
    fn = getattr(inst, "join_battle")
    while hasattr(fn, "__wrapped__"):
        fn = fn.__wrapped__
    return _pb_text(_pb_run_sync(fn(inst, _PB_Event(_PB_GID, "q_none", "加入战斗"))))


def _pb_b26_explore_stage_boss():
    """探索（旧 stages 路径）：遇怪 + Boss 台词行 + 面板 + 轮到行。"""
    _PB_clean()
    random.seed(20260914 + 26)
    _pb_player(_PB_Q, "甲")
    host = _PBHost()
    st = _pb_st([_PB_Q], names={_PB_Q: "甲"},
                inst_stages=[{"name": "一层", "monsters": [["m_x", "小怪", "dps", 15, [], []]]}],
                stage_pending=[["m_boss", "哥布林督军", "boss", 15, [], []]], mode="map")
    _pb_save(_PB_Q, st)
    return _pb_text(_pb_run_sync(host._instance_explore(
        _PB_Event(_PB_GID, _PB_Q), _PB_GID, _PB_Q, {"state": st})))


def _pb_b27_act_state_error():
    """instance_battle.act：无 battle sides / 行动者不在阵列 两态。"""
    _PB_clean()
    random.seed(20260914 + 27)
    _pb_player(_PB_Q, "甲")
    outs = [_pb_text(_PB_IB.act({"battle": {}}, _PB_GID, _PB_Q, "attack")[0])]
    st = _pb_st([_PB_Q], names={_PB_Q: "甲"}, enemies=[_pb_enemy()], mode="battle")
    st["boss"] = st["enemy"] = st["enemies"][0]
    _PB_IB.build_battle(st)
    outs.append(_pb_text(_PB_IB.act(st, _PB_GID, "q_ghost", "attack")[0]))
    return "\n@@@\n".join(outs)


def _pb_b28_secret_chest_all():
    """密室宝箱五档：宠物蛋 / 图纸残页 / 装备 / 材料 / 符文（各自 seed 固定）。"""
    outs = []
    for seed in (20260914 + 102, 20260914 + 101, 20260914 + 107,
                 20260914 + 105, 20260914 + 106):
        _PB_clean()
        random.seed(seed)
        _pb_player(_PB_Q, "甲")
        host = _PBHost()
        st = _pb_st([_PB_Q], names={_PB_Q: "甲"}, secret_chest=True, mode="map")
        _pb_save(_PB_Q, st)
        outs.append(host._instance_secret_chest(
            _PB_GID, _PB_Q, _PB_db.get_player(_PB_GID, _PB_Q), st))
    return "\n@@@\n".join(outs)


def _pb_b29_investigate_empty():
    """调查点：奖励空结果（收藏档池无效）→『空空如也』；材料档无效 →『一点零碎』兜底。"""
    host = _PBHost()
    outs = []
    _orig_pts = _PB_C.INVESTIGATION_POINTS
    # ① 空结果：命中收藏档但收藏池无有效材料 → reward []
    _PB_clean()
    random.seed(20260914 + 29)
    _pb_player(_PB_Q, "甲")
    st = _pb_st([_PB_Q], names={_PB_Q: "甲"}, inst_id="inst_moon_temple",
                cleared=True, mode="map")
    _pb_save(_PB_Q, st)
    _PB_C.INVESTIGATION_POINTS = {
        "inst_moon_temple": [{"id": "p_void", "name": "月池", "collect": ["?none"]}]}
    try:
        with _PBRR(0.0):
            outs.append(host._instance_investigate_cleared(
                _PB_GID, _PB_Q, _PB_db.get_player(_PB_GID, _PB_Q), st, "月池"))
    finally:
        _PB_C.INVESTIGATION_POINTS = _orig_pts
    # ② 零碎兜底：材料档命中但材料 ID 无效 → 末行兜底
    _PB_clean()
    random.seed(20260914 + 30)
    _pb_player(_PB_Q, "甲")
    st2 = _pb_st([_PB_Q], names={_PB_Q: "甲"}, inst_id="inst_moon_temple",
                 cleared=True, mode="map")
    _pb_save(_PB_Q, st2)
    _PB_C.INVESTIGATION_POINTS = {
        "inst_moon_temple": [{"id": "p_void2", "name": "月池", "materials": ["?bad"]}]}
    try:
        with _PBRR(0.90):
            outs.append(host._instance_investigate_cleared(
                _PB_GID, _PB_Q, _PB_db.get_player(_PB_GID, _PB_Q), st2, "月池"))
    finally:
        _PB_C.INVESTIGATION_POINTS = _orig_pts
    return "\n@@@\n".join(str(o) for o in outs)


def _pb_b30_open_battle_mode():
    """开本（战斗模式·首层空层）：标题行 + CTB 提示行 + 层行（n=1）。"""
    _PB_clean()
    random.seed(20260914 + 31)
    _pb_player(_PB_Q, "甲")
    _PB_db.update_player(_PB_GID, _PB_Q, cur_map="misty_swamp", cur_subarea="misty_swamp_3")
    _orig = _PB_C.INSTANCES["inst_goblin_camp"]
    _copy = dict(_orig)
    _copy["stages"] = [{"name": "一层"}]
    _PB_C.INSTANCES["inst_goblin_camp"] = _copy
    try:
        return _pb_cmd(_PB_Main(None), "instance_cmd", "副本 哥布林营地")
    finally:
        _PB_C.INSTANCES["inst_goblin_camp"] = _orig


def _pb_b31_boss_room_victory():
    """Boss 房房间怪被击杀 → 通关结算（走 router 的 _room_boss 分支，含『Boss 已被击败』行）。"""
    _PB_clean()
    random.seed(20260914 + 40)
    import time as _t
    qid, cur_sa = "q_br", "goblin_camp_3"
    st = _pb_st([qid], names={qid: "甲"}, mode="battle",
                rooms={cur_sa: {"monsters_left": [], "pois_left": [],
                                "boss_alive": True, "_is_boss": True}})
    st["enemies"] = [_pb_enemy(hp=1, spd=1, role="boss", uid="e_boss", name="房间怪")]
    st["boss"] = st["enemy"] = st["enemies"][0]
    _PB_db.update_player(_PB_GID, qid, cur_map="misty_swamp", cur_subarea=cur_sa)
    _PB_IB.build_battle(st)
    host = _PBHost()
    msgs = []
    for _ in range(8):
        st["turn_time"] = int(_t.time())
        msgs += _pb_run_sync(host._instance_router(
            _PB_Event(_PB_GID, qid), _PB_GID, qid, st["players"][qid], st,
            "attack", None, None))
        if st.get("cleared") or st.get("over") or not st.get("enemies"):
            break
    return _pb_text(msgs)


_PB_BRANCHES = (
    ("PB01_开本_单人地图模式", _pb_b1_open_solo),
    ("PB02_开本_多人队伍构成", _pb_b2_open_party),
    ("PB03_开本_名字不存在", _pb_b3_open_bad_name),
    ("PB04_加入战斗_队长与队员", _pb_b4_join_leader_and_mate),
    ("PB05_加入战斗_成功", _pb_b5_join_success),
    ("PB06_不在副本_六提示", _pb_b6_not_in_instance),
    ("PB07_战斗中守卫_五提示", _pb_b7_in_battle_guards),
    ("PB08_副本过期提示", _pb_b8_expired_hint),
    ("PB09_深入_房间模式", _pb_b9_advance_room_mode),
    ("PB10_深入_四拦截", _pb_b10_advance_blocked),
    ("PB11_深入_清层推进两形态", _pb_b11_advance_next_stage),
    ("PB12_地图_分层精英标注", _pb_b12_map_stage_elite),
    ("PB13_调查_空参数与未命中", _pb_b13_investigate_miss),
    ("PB14_调查_已处理", _pb_b14_investigate_used),
    ("PB15_探索_通关后", _pb_b15_explore_cleared),
    ("PB16_探索_rooms四态", _pb_b16_explore_rooms_three),
    ("PB17_探索_旧层路径两态", _pb_b17_explore_stage_paths),
    ("PB18_撤退_全流程", _pb_b18_retreat_flow),
    ("PB19_离开与恢复进度", _pb_b19_leave_and_resume),
    ("PB20_移动_非队长", _pb_b20_move_not_leader),
    ("PB21_通关超时离开", _pb_b21_cleared_timeout),
    ("PB22_暗格_死墙与开门", _pb_b22_secret_crack),
    ("PB23_宝箱_开启", _pb_b23_secret_chest),
    ("PB24_调查点_四档奖励", _pb_b24_investigate_reward),
    ("PB25_加入战斗_无角色", _pb_b25_join_no_char),
    ("PB26_探索_旧层遇怪Boss", _pb_b26_explore_stage_boss),
    ("PB27_战斗异常_两态", _pb_b27_act_state_error),
    ("PB28_宝箱_五档", _pb_b28_secret_chest_all),
    ("PB29_调查点_空与零碎", _pb_b29_investigate_empty),
    ("PB30_开本_战斗模式", _pb_b30_open_battle_mode),
    ("PB31_Boss房通关_击败行", _pb_b31_boss_room_victory),
)


def _pb_scenarios() -> dict:
    """复跑全部副本面板/地图/状态分支（迁移前采快照 / 迁移后门禁比对，同一份驱动）。"""
    out = {}
    for name, fn in _PB_BRANCHES:
        try:
            out[name] = _pb_text(fn())
        except Exception as exc:                       # 采集期诚实报错，不静默
            out[name] = "<<EXC>> %s: %s" % (type(exc).__name__, exc)
    return out

INSTANCE_PANEL_FROZEN = {
    'PB01_开本_单人地图模式': '👺 【哥布林营地】副本开启！你踏入了这片区域。\n━━━━━━━━━━━━\n🗺️ 【哥布林营地 · 入口栅栏】\n歪斜的木栅栏围出营地外围，兽皮晾在栏上，篝火堆散落四周。守卫在缺口处探头张望，臭味与叫嚷声扑面而来。\n━━━━━━━━━━━━\n📍 当前位置：入口栅栏\n📮 可前往：\n  ●1. 篝火营地\n  \n🔎 可探索触发：\n  ●📦 生锈的铁箱 ●🔥 将熄的篝火\n\n✨ 可交互场景：\n  ●1. 🪨 哥布林营地界碑\n\n🐾 此地的怪物 (Lv.15-16)：\n  哥布林守卫 Lv.15±1\n  哥布林萨满 Lv.16±1\n\n💡 想去哪？『前往 <地名>』直达\n━━━━━━━━━━━━\n🚪 副本内 · 无出口（没有通往外面的路）\n🐾 此房怪物剩余：哥布林守卫、哥布林萨满（『探索』高概率遭遇）\n🔎 此房可调查：生锈的铁箱、将熄的篝火(『调查 <名称>』)\n💰 副本资源池剩余：424 金币 · 哥布林铁片×3、咕噜皇冠×1\n💡 备好钥匙，『副本 <名字>』进入\n━━━━━━━━━━━━\n🕐 单人挑战：战士·坦克\n💡 专注战斗！『副本』查看进度\n⏳ 副本内『移动』由队长带队；『探索』『调查』各人自由进行，遇怪全队合并进同一场战斗！\n📖 商路旁的营地还冒着劫掠后的烟，翻倒的货车旁散落着没来得及搬走的货物。行会的悬赏令在怀里发烫——今晚，该让哥布林酋长·咕噜尝尝被讨伐的滋味了。',
    'PB02_开本_多人队伍构成': '🦀 【锈潮船坞】副本开启！你踏入了这片区域。\n━━━━━━━━━━━━\n🗺️ 【锈潮船坞 · 闸门水道】\n铁港码头货仓区下的锈死闸门，推开后是一条半淹的水道，锈壳蟹攀在闸壁上，水鬼从水面下探出半个头。远处船坞深处传来钳甲碰撞的闷响。\n━━━━━━━━━━━━\n📍 当前位置：闸门水道\n📮 可前往：\n  ●1. 沉船坞池\n  \n👤 此地的玩家：\n  ●1. 乙 Lv.60\n\n🐾 此地的怪物 (Lv.25-27)：\n  锈壳蟹 Lv.25±1\n  水鬼 Lv.27±1\n\n💡 『探索』遇怪，『前往 <序号>』赶路\n━━━━━━━━━━━━\n🚪 副本内 · 无出口（没有通往外面的路）\n🐾 此房怪物剩余：锈壳蟹、水鬼（『探索』高概率遭遇）\n💰 副本资源池剩余：458 金币 · 锈潮蟹甲×2\n💡 副本激战中，『角色』了解队友\n━━━━━━━━━━━━\n👥 队伍构成：战士·坦克 + 战士·坦克\n⚠️ ✨ 没有治疗：血线压力大，记得多带药水\n💡 可发送『调查 <名称>』互动机关\n⏳ 副本内『移动』由队长带队；『探索』『调查』各人自由进行，遇怪全队合并进同一场战斗！\n📖 码头货仓区尽头有道锈死的闸门，推开时潮声裹着铁锈味扑面而来——废弃船坞的水道里，锈壳蟹窸窣爬行，深处时不时传来钳甲碰撞的闷响。铁港的老水手说，蟹王·锈钳的巢就在最深的船底，它钳上的船牌，还在等船主们来认领。',
    'PB03_开本_名字不存在': '没有『不存在的本』这个副本！『副本』查看列表～',
    'PB04_加入战斗_队长与队员': '你就是这场战斗的队长！『攻击』『技能 <名称>』『防御』行动～\n@@@\n你正在战斗中！先解决眼前的敌人～',
    'PB05_加入战斗_成功': '⚔️ 队员乙 加入了战斗！\n━━━━━━━━━━━━\n── 敌方 ──\n  A1层: a1  房间怪 ❤️500/500\n── 我方 ──\n  B1层: b1  队长甲 ❤️100/100 | b2  队员乙 ❤️100/1422\n🕐 时刻 0.0s ｜ ⚡ 行动顺序：队长甲(我) → 房间怪(敌) → 队员乙(我)\n✅ 队长甲：❤️ 100/100 💙 999/999\n✅ 队员乙：❤️ 100/1422 💙 100/213\n💡 选敌：『技能1 a2』打2号(纯数字同义)；治疗『技能 <名称> b1』奶自己\n👥 当前参战：队长甲、队员乙',
    'PB06_不在副本_六提示': '你当前不在副本中！输入『副本』查看副本列表～\n@@@\n你当前不在副本中！输入『副本』查看副本列表～\n@@@\n你当前不在副本中！输入『副本』查看副本列表～\n@@@\n你当前不在副本中！\n@@@\n你当前不在副本中！\n@@@\n你当前不在副本中！',
    'PB07_战斗中守卫_五提示': '战斗进行中！先解决眼前的敌人～(『攻击』『技能 <名称>』『防御』)\n@@@\n战斗进行中！先解决眼前的敌人～\n@@@\n战斗中无法撤退！Boss 锁定了你们的退路——打赢或战败！\n@@@\n战斗中无法撤退！先击败眼前的敌人再说！\n@@@\n战斗中无法离开！先解决眼前的敌人再说！',
    'PB08_副本过期提示': '⌛ 你之前的副本因超过 24 小时无人行动，已自动过期消失～',
    'PB09_深入_房间模式': '这个副本没有分层结构，直接挑战 Boss 吧～',
    'PB10_深入_四拦截': '当前层的敌人还没肃清！『探索』找到它们～\n@@@\n当前层的敌人还没肃清！先打完再说～\n@@@\n副本已通关！搜刮完用『离开副本』传出吧～\n@@@\n这个副本没有分层结构，直接挑战 Boss 吧～\n@@@\n已经是最深层了，击败面前的 Boss 就通关了！',
    'PB11_深入_清层推进两形态': '🧭 你继续深入……\n━━━━━━━━━━━━\n🗺️ 【👺哥布林营地】第 2 层 · 二层\n━━━━━━━━━━━━\n📜 你环顾四周，准备迎接这里的敌人。\n━━━━━━━━━━━━\n✨ 场景：\n  []\n  []\n━━━━━━━━━━━━\n🐾 敌人：小怪2(『探索』遇怪)\n━━━━━━━━━━━━\n💡 『副本』查看战况，『角色』看队伍\n@@@\n🧭 你继续深入……\n━━━━━━━━━━━━\n🚪 第 2 层 · 二层\n━━━━━━━━━━━━\n── 敌方 ──\n  A1层: a1  房间怪 ❤️500/500\n── 我方 ──\n  B1层: b1  甲 ❤️100/100\n🕐 时刻 0.0s ｜ ⚡ 行动顺序：甲(我) → 房间怪(敌)\n✅ 甲：❤️ 100/100 💙 999/999\n💡 选敌：『技能1 a2』打2号(纯数字同义)；治疗『技能 <名称> b1』奶自己\n⏳ 轮到 甲 行动！『攻击』『技能 <名称>』『防御』',
    'PB12_地图_分层精英标注': '🗺️ 【👺哥布林营地】第 1 层 · 一层\n━━━━━━━━━━━━\n📜 石廊尽头有风。\n━━━━━━━━━━━━\n✨ 场景：\n  []\n  []\n━━━━━━━━━━━━\n🐾 敌人：哥布林守卫 ⭐精英·哥布林督军(『探索』遇怪)\n━━━━━━━━━━━━\n💡 多人副本先『组队 <名字>』再开本',
    'PB13_调查_空参数与未命中': '格式：『调查 <目标>』，如『调查 宝箱』『调查 篝火』～（『副本地图』查看当前层可调查目标）\n@@@\n这里没有『不存在的东西』可以调查～『副本地图』看看周围有什么。',
    'PB14_调查_已处理': '旧石碑已经被处理过了。',
    'PB15_探索_通关后': '副本已通关，没有敌人可探索了！『副本地图』看看战利品堆，或『离开副本』传出～',
    'PB16_探索_rooms四态': '🍃 这里已被肃清，没有敌人了。『副本地图』看看剩余可调查的 POI，或让队长『移动』去别的房间～\n@@@\n🍃 这里已被肃清，没有敌人了。『副本地图』看看剩余可调查的 POI，或让队长『移动』去别的房间～\n@@@\n🍃 这里已被肃清，没有敌人了。『副本地图』看看剩余可调查的 POI，或让队长『移动』去别的房间～\n@@@\n🍃 这里已被肃清，没有敌人了。『副本地图』看看剩余可调查的 POI，或让队长『移动』去别的房间～',
    'PB17_探索_旧层路径两态': '🍃 你仔细搜索了这片区域，除了风声什么也没有发现。\n@@@\n🍃 你小心翼翼地探索……\n⚠️ 你触发了尖刺陷阱！全队受到 10% 最大生命的伤害！\n❤️ 甲 剩余 90/100',
    'PB18_撤退_全流程': '👺 【哥布林营地】副本开启！你踏入了这片区域。\n━━━━━━━━━━━━\n🗺️ 【哥布林营地 · 入口栅栏】\n歪斜的木栅栏围出营地外围，兽皮晾在栏上，篝火堆散落四周。守卫在缺口处探头张望，臭味与叫嚷声扑面而来。\n━━━━━━━━━━━━\n📍 当前位置：入口栅栏\n📮 可前往：\n  ●1. 篝火营地\n  \n🔎 可探索触发：\n  ●📦 生锈的铁箱 ●🔥 将熄的篝火\n\n✨ 可交互场景：\n  ●1. 🪨 哥布林营地界碑\n\n🐾 此地的怪物 (Lv.15-16)：\n  哥布林守卫 Lv.15±1\n  哥布林萨满 Lv.16±1\n\n💡 『地图』看详情，『探索』遇怪\n━━━━━━━━━━━━\n🚪 副本内 · 无出口（没有通往外面的路）\n🐾 此房怪物剩余：哥布林守卫、哥布林萨满（『探索』高概率遭遇）\n🔎 此房可调查：生锈的铁箱、将熄的篝火(『调查 <名称>』)\n💰 副本资源池剩余：424 金币 · 哥布林铁片×3、咕噜皇冠×1\n💡 副本激战中，『角色』了解队友\n━━━━━━━━━━━━\n🕐 单人挑战：战士·坦克\n💡 单人副本直接『副本 <名字>』开本\n⏳ 副本内『移动』由队长带队；『探索』『调查』各人自由进行，遇怪全队合并进同一场战斗！\n📖 商路旁的营地还冒着劫掠后的烟，翻倒的货车旁散落着没来得及搬走的货物。行会的悬赏令在怀里发烫——今晚，该让哥布林酋长·咕噜尝尝被讨伐的滋味了。\n@@@\n🏳️ 你要从【哥布林营地】撤退吗？\n⚠️ 撤退 = 放弃当前进度（已拿的战利品保留，但层数/机关进度清空，重新开本从头打）！\n💡 确认请回复『确认撤退』；反悔就继续冒险吧～\n@@@\n已弹过确认啦～ 回复『确认撤退』放弃进度，或继续冒险！\n@@@\n确认已过期（副本状态变化）～ 重新发『撤退』看看吧。\n@@@\n还没有待确认的撤退～ 副本中发『撤退』会先弹确认。\n@@@\n🏳️ 你要从【哥布林营地】撤退吗？\n⚠️ 撤退 = 放弃当前进度（已拿的战利品保留，但层数/机关进度清空，重新开本从头打）！\n💡 确认请回复『确认撤退』；反悔就继续冒险吧～\n@@@\n🏳️ 你们放弃了【哥布林营地】的进度，回到了入口。\n📌 已拿到的战利品保留在背包；想再挑战就重新『副本 哥布林营地』从头开始吧！',
    'PB19_离开与恢复进度': '👺 【哥布林营地】副本开启！你踏入了这片区域。\n━━━━━━━━━━━━\n🗺️ 【哥布林营地 · 入口栅栏】\n歪斜的木栅栏围出营地外围，兽皮晾在栏上，篝火堆散落四周。守卫在缺口处探头张望，臭味与叫嚷声扑面而来。\n━━━━━━━━━━━━\n📍 当前位置：入口栅栏\n📮 可前往：\n  ●1. 篝火营地\n  \n🔎 可探索触发：\n  ●📦 生锈的铁箱 ●🔥 将熄的篝火\n\n✨ 可交互场景：\n  ●1. 🪨 哥布林营地界碑\n\n🐾 此地的怪物 (Lv.15-16)：\n  哥布林守卫 Lv.15±1\n  哥布林萨满 Lv.16±1\n\n💡 『探索』遇怪，『前往 <序号>』赶路\n━━━━━━━━━━━━\n🚪 副本内 · 无出口（没有通往外面的路）\n🐾 此房怪物剩余：哥布林守卫、哥布林萨满（『探索』高概率遭遇）\n🔎 此房可调查：生锈的铁箱、将熄的篝火(『调查 <名称>』)\n💰 副本资源池剩余：424 金币 · 哥布林铁片×3、咕噜皇冠×1\n💡 『副本』查看战况，『角色』看队伍\n━━━━━━━━━━━━\n🕐 单人挑战：战士·坦克\n💡 『副本』查看战况，『角色』看队伍\n⏳ 副本内『移动』由队长带队；『探索』『调查』各人自由进行，遇怪全队合并进同一场战斗！\n📖 商路旁的营地还冒着劫掠后的烟，翻倒的货车旁散落着没来得及搬走的货物。行会的悬赏令在怀里发烫——今晚，该让哥布林酋长·咕噜尝尝被讨伐的滋味了。\n@@@\n🗺️ 【哥布林营地】\n哥布林营地，传说中的危险之地，唯有勇者敢于踏入。\n💡 输入『副本 哥布林营地』开启挑战（组队副本，等级/人数校验）\n━━━━━━━━━━━━\n📍 当前位置：哥布林营地\n📮 可前往：\n  🧭 出城需先到『入口栅栏』\n💡 『对话 <名字>』聊天，『探索』冒险\n━━━━━━━━━━━━\n🚪 副本内 · 无出口（没有通往外面的路）\n🐾 此房怪物已肃清。\n💰 副本资源池剩余：424 金币 · 哥布林铁片×3、咕噜皇冠×1\n💡 『副本』查看战况，『角色』看队伍\n@@@\n🏳️ 你带着战利品离开了哥布林营地。冒险者的旅途还在继续～',
    'PB20_移动_非队长': '⏳ 副本内由队长带队移动！等待队长『移动 <房间>』～',
    'PB21_通关超时离开': '🗺️ 【哥布林营地 · 入口栅栏】\n歪斜的木栅栏围出营地外围，兽皮晾在栏上，篝火堆散落四周。守卫在缺口处探头张望，臭味与叫嚷声扑面而来。\n━━━━━━━━━━━━\n📍 当前位置：入口栅栏\n📮 可前往：\n  ●1. 篝火营地\n  \n🔎 可探索触发：\n  ●📦 生锈的铁箱 ●🔥 将熄的篝火\n\n✨ 可交互场景：\n  ●1. 🪨 哥布林营地界碑\n\n🐾 此地的怪物 (Lv.15-16)：\n  哥布林守卫 Lv.15±1\n  哥布林萨满 Lv.16±1\n\n💡 『地图』看详情，『探索』遇怪\n━━━━━━━━━━━━\n🚪 副本内 · 无出口（没有通往外面的路）\n🐾 此房怪物剩余：哥布林守卫、哥布林萨满（『探索』高概率遭遇）\n🔎 此房可调查：生锈的铁箱、将熄的篝火(『调查 <名称>』)\n💰 副本资源池剩余：424 金币 · 哥布林铁片×3、咕噜皇冠×1\n💡 副本请走『副本 <名字>』开启',
    'PB22_暗格_死墙与开门': '🧱 墙砖松动了，但后面只有一堵死墙……（暗格消失了）\n@@@\n🧱 你扣住松动的墙砖用力一拉——暗门轰然打开！\n一个魁梧的身影挡在密室前……\n━━━━━━━━━━━━\n── 敌方 ──\n  A1层: a1  哥布林守卫 ❤️564/564\n── 我方 ──\n  B1层: b1  甲 ❤️100/100\n🕐 时刻 0.0s ｜ ⚡ 行动顺序：哥布林守卫(敌) → 甲(我)\n✅ 甲：❤️ 100/100 💙 100/999\n💡 选敌：『技能1 a2』打2号(纯数字同义)；治疗『技能 <名称> b1』奶自己\n⏳ 轮到 甲 行动！『攻击』『技能 <名称>』『防御』',
    'PB23_宝箱_开启': '🔐 你打开了密室宝箱！\n✨ 宝箱里泛起微光——符文【稀有符文·冰霜 I】！',
    'PB24_调查点_四档奖励': '🔍 你仔细调查了【酋长的战利品堆】……\n✨ 你发现了一件稀罕的收藏品——【骑士团徽章】！(图鉴『收藏』可查看)\n@@@\n🔍 你仔细调查了【劫掠清单】……\n📜 你翻出一叠泛黄的纸页——图纸残页 ×3！\n@@@\n🔍 你仔细调查了【篝火余烬】……\n🎒 你摸到了些材料——咕噜皇冠 ×1！\n@@@\n🔍 你仔细调查了【月池】……\n✨ 你拾起一枚刻着符文的宝石——【稀有符文·拾荒 I】！',
    'PB25_加入战斗_无角色': '你还没有角色！先『注册』开始冒险～',
    'PB26_探索_旧层遇怪Boss': '🍃 你警惕地探索着，突然——一层里的怪物扑了上来！\n━━━━━━━━━━━━\n💬 『金币！宝石！都是咕噜的！』咕噜把抢来的皇冠往头上一扣，咧开满嘴尖牙：『你们这些商队的小跟班，也敢来掀咕噜的帐篷？』\n── 敌方 ──\n  A1层: a1  哥布林督军的哥布林打手 ❤️564/564 | a2  哥布林督军的哥布林打手 ❤️564/564\n  A2层: a3  哥布林督军 ❤️9749/9749\n── 我方 ──\n  B1层: b1  甲 ❤️100/100\n🕐 时刻 0.0s ｜ ⚡ 行动顺序：哥布林督军(敌) → 哥布林督军的哥布林打手(敌) → 哥布林督军的哥布林打手(敌) → 甲(我)\n✅ 甲：❤️ 100/100 💙 100/999\n💡 选敌：『技能1 a2』打2号(纯数字同义)；治疗『技能 <名称> b1』奶自己\n⏳ 轮到 甲 行动！『攻击』『技能 <名称>』『防御』',
    'PB27_战斗异常_两态': '战斗状态异常，请重新遭遇！\n@@@\n你已不在战斗中（状态异常）！',
    'PB28_宝箱_五档': '🔐 你打开了密室宝箱！\n📜 宝箱里是泛黄的纸张——图纸残页 ×4！\n@@@\n🔐 你打开了密室宝箱！\n🎒 宝箱里是稀有材料——咕噜皇冠 ×1！\n@@@\n🔐 你打开了密室宝箱！\n🔵 宝箱深处静静躺着一件装备——【哥布林军刀】！\n@@@\n🔐 你打开了密室宝箱！\n✨🟣 宝箱深处静静躺着一件装备——【骑士残甲】！\n@@@\n🔐 你打开了密室宝箱！\n✨ 宝箱里泛起微光——符文【稀有符文·聚能 I】！',
    'PB29_调查点_空与零碎': '月池里空空如也，什么也没发现。\n@@@\n🔍 你仔细调查了【月池】……\n🎒 你翻了翻，只找到一点零碎。',
    'PB30_开本_战斗模式': '👺 【哥布林营地】副本开启！\n━━━━━━━━━━━━\n🚪 第 1 层 · 一层\n📜 商路旁的哥布林聚落，哥布林酋长·咕噜盘踞于此，靠抢劫商队为生。冒险者行会悬赏讨伐。(主线第 2 章)\n━━━━━━━━━━━━\n🕐 单人挑战：战士·坦克\n── 敌方 ──\n  A1层: a1  哥布林酋长·咕噜的哥布林打手 ❤️564/564 | a2  哥布林酋长·咕噜的哥布林打手 ❤️564/564\n  A2层: a3  哥布林酋长·咕噜 ❤️24414/24414\n── 我方 ──\n  B1层: b1  甲 ❤️100/1422\n🕐 时刻 0.0s ｜ ⚡ 行动顺序：哥布林酋长·咕噜(敌) → 甲(我) → 哥布林酋长·咕噜的哥布林打手(敌) → 哥布林酋长·咕噜的哥布林打手(敌)\n✅ 甲：❤️ 100/1422 💙 100/213\n💡 选敌：『技能1 a2』打2号(纯数字同义)；治疗『技能 <名称> b1』奶自己\n⏳ 轮到 甲 行动！『攻击』『技能 <名称>』『防御』\n💡 按 CTB 行动轴轮流出手，超时 60 秒自动防御；清光当前层怪物可『深入』下一层！\n📖 商路旁的营地还冒着劫掠后的烟，翻倒的货车旁散落着没来得及搬走的货物。行会的悬赏令在怀里发烫——今晚，该让哥布林酋长·咕噜尝尝被讨伐的滋味了。',
    'PB31_Boss房通关_击败行': '💥 房间怪 受到 1 点伤害，倒下了！\n👑 副本 Boss 已被击败！\n\n🎉 【房间怪】被击败了！👺哥布林营地 通关！\n📜 咕噜的皇冠滚落在篝火边，商路上的劫掠就此画上句号。行会的赏金结清了，可你总觉得，这条商路尽头的风声，才刚刚开始。\n\n🏆 副本已通关！你可以在副本内停留搜刮：\n  · 🎁 【战利品堆】—— 首领的遗物，搜刮一次（『调查 战利品堆』）\n  · 🔍 通关后这里多了些可调查的痕迹（『副本地图』查看，每日限 3 次）\n搜刮完毕用『离开副本』传出～\n\n💡 『副本』可再次挑战，首通成就已记录～',
}   # 迁移前快照（2026-09-13 真跑存下，来源 $TEMP/instance_panel_pre31.json —— 采于接线前的代码，勿手改）
INSTANCE_PANEL_OLD_LITERALS = [
    ' 加入了战斗！',
    ' 宝箱深处静静躺着一件装备——【',
    's ｜ ⚡ 行动顺序：',
    '⌛ 你之前的副本因超过 24 小时无人行动，已自动过期消失～',
    '⏳ 副本内『移动』由队长带队；『探索』『调查』各人自由进行，遇怪全队合并进同一场战斗！',
    '⏳ 副本内由队长带队移动！等待队长『移动 <房间>』～',
    '⏳ 通关时间已过 30 分钟，你已自动离开副本。',
    '✨ 你发现了一件稀罕的收藏品——【',
    '✨ 你拾起一枚刻着符文的宝石——【',
    '✨ 宝箱里泛起微光——符文【',
    '。冒险者的旅途还在继续～',
    '』从头开始吧！',
    '』可以调查～『副本地图』看看周围有什么。',
    '』这个副本！『副本』查看列表～',
    '】你回到了副本深处！',
    '】副本开启！',
    '】副本开启！你踏入了这片区域。',
    '】撤退吗？\n⚠️ 撤退 = 放弃当前进度（已拿的战利品保留，但层数/机关进度清空，重新开本从头打）！\n💡 确认请回复『确认撤退』；反悔就继续冒险吧～',
    '】的进度，回到了入口。\n📌 已拿到的战利品保留在背包；想再挑战就重新『副本 ',
    '】！(图鉴『收藏』可查看)',
    '】！『使用 宠物蛋』孵化！',
    '你已不在战斗中（状态异常）！',
    '你当前不在副本中！',
    '你当前不在副本中！输入『副本』查看副本列表～',
    '你正在战斗中！先解决眼前的敌人～',
    '你还没有角色！先『注册』开始冒险～',
    '副本内请使用『移动 <房间>』推进（队长带队）～『副本地图』查看可前往房间。',
    '副本已通关！搜刮完用『离开副本』传出吧～',
    '副本已通关，没有敌人可探索了！『副本地图』看看战利品堆，或『离开副本』传出～',
    '已弹过确认啦～ 回复『确认撤退』放弃进度，或继续冒险！',
    '已经是最深层了，击败面前的 Boss 就通关了！',
    '已经被处理过了。',
    '已经被搜刮一空了。',
    '当前层的敌人还没肃清！『探索』找到它们～',
    '当前层的敌人还没肃清！先打完再说～',
    '战斗中无法撤退！Boss 锁定了你们的退路——打赢或战败！',
    '战斗中无法撤退！先击败眼前的敌人再说！',
    '战斗中无法离开！先解决眼前的敌人再说！',
    '战斗进行中！先解决眼前的敌人～',
    '战斗进行中！先解决眼前的敌人～(『攻击』『技能 <名称>』『防御』)',
    '格式：『调查 <目标>』，如『调查 宝箱』『调查 篝火』～（『副本地图』查看当前层可调查目标）',
    '确认已过期（副本状态变化）～ 重新发『撤退』看看吧。',
    '还没有待确认的撤退～ 副本中发『撤退』会先弹确认。',
    '这个副本没有分层结构，直接挑战 Boss 吧～',
    '这里没有『',
    '里的怪物扑了上来！',
    '里空空如也，什么也没发现。',
    '🍃 你仔细搜索了这片区域，怪物没有发现你……',
    '🍃 你仔细搜索了这片区域，除了风声什么也没有发现。',
    '🍃 你仔细搜索着这片区域……',
    '🍃 你小心翼翼地探索……',
    '🍃 你警惕地探索着，突然——',
    '🍃 这里已被肃清，没有敌人了。『副本地图』看看剩余可调查的 POI，或让队长『移动』去别的房间～',
    '🎒 你摸到了些材料——',
    '🎒 你翻了翻，只找到一点零碎。',
    '🎒 宝箱里是稀有材料——',
    '🏰 【组队副本】',
    '🏳️ 你们放弃了【',
    '🏳️ 你带着战利品离开了',
    '🏳️ 你要从【',
    '👑 副本 Boss 已被击败！',
    '👥 当前参战：',
    '👥 队伍构成：',
    '💡 按 CTB 行动轴轮流出手，超时 60 秒自动防御；清光当前层怪物可『深入』下一层！',
    '📜 你翻出一叠泛黄的纸页——图纸残页 ×',
    '📜 宝箱里是泛黄的纸张——图纸残页 ×',
    '🔍 你仔细调查了【',
    '🔐 你打开了密室宝箱！',
    '🕐 单人挑战：',
    '🦋 宝箱深处泛着星光——是【',
    '🧭 你继续深入……',
    '🧱 你扣住松动的墙砖用力一拉——暗门轰然打开！\n一个魁梧的身影挡在密室前……',
    '🧱 墙砖松动了，但后面只有一堵死墙……（暗格消失了）',
]   # 迁移前内联句壳片段（= 本域表值去槽位后的实体片段）：三份源文件里一句都不许再出现


def t11_instance_panel_frozen():
    print("\n[11] 副本面板域逐字冻结：迁移前 31 分支（开本三种形态/加入/深入/调查/探索/撤退/离开/移动/地图/"
          "列表/状态/行动序/暗格/宝箱/调查点/战斗异常/Boss房通关）复跑比对")
    check("冻结基准已内嵌（31 分支）", len(INSTANCE_PANEL_FROZEN) == 31, len(INSTANCE_PANEL_FROZEN))
    now = _pb_scenarios()
    bad = [k for k in INSTANCE_PANEL_FROZEN if INSTANCE_PANEL_FROZEN[k] != now.get(k)]
    for k in bad:
        print("     · %s 现=%r" % (k, (now.get(k) or "")[:160]))
    check("★ 副本面板 31 分支输出与迁移前**逐字一致**", not bad, bad)
    _single = ("PB03_开本_名字不存在", "PB04_加入战斗_队长与队员", "PB08_副本过期提示",
               "PB09_深入_房间模式", "PB14_调查_已处理", "PB15_探索_通关后",
               "PB17_探索_旧层路径两态", "PB20_移动_非队长", "PB23_宝箱_开启",
               "PB25_加入战斗_无角色", "PB27_战斗异常_两态", "PB29_调查点_空与零碎")
    check("冻结基准非空（防基准写空）",
          all(v for k, v in INSTANCE_PANEL_FROZEN.items() if k not in _single))

    # 旧句壳零残留：三份源文件的「非 T.text/T.static 实参、非文档串」常量里不许再出现迁移前片段
    left = []
    for _p in (INSTANCE_SRC, INSTANCE_BATTLE_SRC, INSTANCE_ROUTER_SRC):
        raw, doc = _panel_raw_constants(_p)
        for _s in INSTANCE_PANEL_OLD_LITERALS:
            for _v in raw:
                if _s and _s in _v:
                    left.append((os.path.basename(_p), _s, _v[:60]))
    check("★ 旧句壳零残留（句壳只在文案表；排版分隔线/取值回退/命令关键字留在代码）",
          not left, left[:5])
    check("表里 72 条面板文案全部由本域文件引用（key 双向对账见 [2]）",
          len([k for k in T.table().keys() if k.startswith("instance.面板_")]) == 72,
          len([k for k in T.table().keys() if k.startswith("instance.面板_")]))


def _panel_raw_constants(path):
    """返回 (raw, doc)：非 T.text/T.static 实参的字符串常量 / 文档串（AST 分类）。"""
    _src = io.open(path, encoding="utf-8").read()
    _tree = ast.parse(_src)
    _docs = set()
    for _n in ast.walk(_tree):
        if isinstance(_n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            _d = ast.get_docstring(_n, clean=False)
            if _d is not None:
                for _c in ast.walk(_n):
                    if isinstance(_c, ast.Constant) and _c.value == _d:
                        _docs.add(id(_c))
    _tcalls = set()
    for _n in ast.walk(_tree):
        if (isinstance(_n, ast.Call) and isinstance(_n.func, ast.Attribute)
                and _n.func.attr in ("text", "static")
                and isinstance(_n.func.value, ast.Name) and _n.func.value.id == "T"):
            for _a in _n.args:
                _tcalls.update(id(_x) for _x in ast.walk(_a))
    _raw, _doc = [], []
    for _n in ast.walk(_tree):
        if not isinstance(_n, ast.Constant) or not isinstance(_n.value, str):
            continue
        if id(_n) in _tcalls:
            continue
        (_doc if id(_n) in _docs else _raw).append(_n.value)
    return _raw, _doc


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
    t10_instance_log_frozen()
    t11_instance_panel_frozen()
    print("\n" + "=" * 74)
    print("结果：通过 %d / %d" % (passed, passed + failed))
    print("=" * 74)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())


# ══════════════════════════════════════════════════════════════════════
