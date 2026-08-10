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
        "key": "energy", "name": "精力", "max": 100, "regen": 25,
        "desc": "每回合回 25 点，技能消耗 15－40，不耗魔力",
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
        "desc": "连招/受击＋1，终结技/斗气消耗",
        "on_attack": 1, "on_hit": 1, "on_skill": 1,
    },
}
