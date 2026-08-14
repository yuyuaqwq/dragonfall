# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - core_resources.py（v102.4：从 engine.py 下沉）

v2.0 核心资源系统（12 章 1.2 战斗资源总览）
每职业一个独立战斗资源 dict，随战斗序列化（同 mech_stacks 机制）。
阶段五先建引擎，技能数据落地（阶段六）后按技能表挂载获取/消耗。
"""
# ============================================================
# v2.0 核心资源系统（12 章 1.2 战斗资源总览）
# 每职业一个独立战斗资源 dict，随战斗序列化（同 mech_stacks 机制）。
# 阶段五先建引擎，技能数据落地（阶段六）后按技能表挂载获取/消耗。
# ============================================================
CORE_RESOURCES = {
    "cls_zhan_shi": {
        "key": "rage", "name": "怒气", "max": 10, "regen": 0,
        "desc": "攻击/受击＋1－2，终结技消耗，越战越勇",
        "on_attack": 1, "on_hit": 1, "on_skill": 2,
    },
    "cls_fa_shi": {
        "key": "element", "name": "元素亲和", "max": 1, "regen": 0,
        "desc": "火/冰/雷三系切换，施法触发元素反应",
        "on_attack": 0, "on_hit": 0, "on_skill": 0, "type": "switch",
    },
    "cls_you_xia": {
        "key": "energy", "name": "精力", "max": 100, "regen": 30,
        "desc": "每回合回 30 点，技能消耗 15－40，不耗魔力（林语印记命中额外回 10）",
        "on_attack": 0, "on_hit": 0, "on_skill": 0,
    },
    "cls_mu_shi": {
        "key": "faith", "name": "信仰值", "max": 10, "regen": 0,
        "desc": "治疗/圣光技/受击＋1，神迹技消耗",
        "on_attack": 0, "on_hit": 1, "on_skill": 1, "on_heal": 2,
    },
    "cls_ci_ke": {
        "key": "cp", "name": "连击点", "max": 5, "regen": 0,
        "desc": "攒点技积累，终结技消耗，潜行爆发",
        "on_attack": 1, "on_hit": 0, "on_skill": 1,
    },
    "cls_wu_seng": {
        "key": "chi", "name": "气", "max": 10, "regen": 0,
        "desc": "连招/受击＋1，终结技/气力消耗",
        "on_attack": 1, "on_hit": 1, "on_skill": 1,
    },
    # ================= v112 隐藏线核心资源（主题线制，6 线各 1 专属资源） =================
    # 设计文档：design/new_world/09_职业体系.md §3 —— 深度来源：同一资源，不同打法
    # 战斗内获取/消耗全走 E.core_resource_* 通用管线（battle.py 零改动）
    "cls_dragon_oath": {
        # 注：原名"龙威"与龙裔技能「龙威」(敌方减攻) 撞名，v112 改名"龙力"防战斗日志歧义
        "key": "dragon_might", "name": "龙力", "max": 10, "regen": 0,
        "desc": "攻击/受击＋1－2，龙息终结技消耗，越战越勇（怒气的进阶形态）",
        "on_attack": 1, "on_hit": 1, "on_skill": 2,
    },
    "cls_chronomancer": {
        # v112.5：时咒法师（法师新增隐藏线）——时之沙；深渊/血咒流派共用
        "key": "time_sand", "name": "时之沙", "max": 5, "regen": 0,
        "desc": "施法/回合积攒，时停技消耗——时间的节拍",
        "on_attack": 0, "on_hit": 0, "on_skill": 1,
    },
    "cls_wild_hunter": {
        "key": "hunt_mark", "name": "猎印", "max": 5, "regen": 0,
        "desc": "命中/暴击积攒，终结技消耗——猎杀节奏",
        "on_attack": 1, "on_hit": 0, "on_skill": 1,
    },
    "cls_hymn": {
        # v112.1：圣歌线改暗影神谕，资源随线改名"悼咏"（key 保持稳定）
        "key": "canticle", "name": "悼咏", "max": 10, "regen": 0,
        "desc": "治疗/技能积攒，神迹技消耗——信仰的进阶形态",
        "on_attack": 0, "on_hit": 1, "on_skill": 1, "on_heal": 2,
    },
    "cls_shadow_blade": {
        "key": "shadow_step", "name": "影步", "max": 5, "regen": 0,
        "desc": "暴击/闪避积攒，终结技消耗——潜行与刺杀的节拍",
        "on_attack": 1, "on_hit": 0, "on_skill": 1,
    },
    "cls_wu_sheng": {
        "key": "zen", "name": "禅意", "max": 10, "regen": 0,
        "desc": "连击/受击积攒，终结技消耗——气的进阶形态",
        "on_attack": 1, "on_hit": 1, "on_skill": 1,
    },
}
