# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - combat（combat）—— B10 L5 **薄壳**

由 main.py 拆分而来，作为 Mixin 被 Main 继承。**B10 L5（2026-09-13）薄壳化**后本文件只剩：

    命令注册（@declared 装饰器）· 守卫 · 取玩家/取参（self._uid / self._player / self._strip_cmd）
    · 调用内容包（一行转发）· 渲染（yield）

真源（实现本体）全在内容包：`content/combat_cmds.py`（74 个方法逐字搬过去，见那边的头注）。
本文件保留的方法只有两类：

  · **命令入口**（15 个）：装饰器 + 取玩家/取参 + `async for _r in _CC.<名>(...)` 转发；
    名字/装饰器/注册序与改造前逐行相同（`@declared` 是宿主侧的**注册**动作：正则来自
    `game/data/command_specs.json`，框架注册表 + `_registry` 都从它派生）。
  · **委托桩**（59 个）：非命令私有方法，`(*args, **kwargs)` 原样转发给包内同名函数
    （async generator 用 `async for` 转发、sync generator 用 `yield from`、`@staticmethod`
    保持静态）。执行 `self._<名>(...)` 的调用方（本文件、其它 Mixin、测试）**零改动**：
    名字集合与改造前**逐名相同** → Main 的 MRO 解析结果不变。

★ 两处**故意留在宿主**（不是遗漏）：
  · `from ..core.wild_king import (` 模块级 import —— 包内 `explore`/`wild_king_chest` 经
    **本模块属性**动态解析野王四函数；`tests/test_v1307_zone_risk.py:65` 与
    `tests/test_v1308_lv_jitter.py:70` 会 monkeypatch `game.commands.combat.explore_king`
    屏蔽野王（绑死 = 测试假红）。
  · 类级常量表（`_MECH_CN` / `_EFFECT_CN` / `_P_BUFF_NAMES` / `_E_BUFF_NAMES` / `_STACK_NAMES` /
    `_ENEMY_MECH_STACKS` / `_DEBUFF_NAMES` / `_RAIN_WINDOW` / `_EXPLORE_RECENT_*` /
    `_DF139_CLASS_FORMS` / `_FINISHER139_OPTIONS` / `_ARCANE_FIELD_OPTIONS`）—— 包内实现体经
    `self._X` 读**同一份**（单源，不复制）。

宿主替身注入：`db` / `C`（内容聚合层）+ 本模块自身（野王 seam）。其余宿主面（battle_bridge /
battle_settlement / player_event_bus / battle_worldboss_procs / core.* / log_setup …）由包内在
**原调用点**惰性解析 —— 时序与改造前逐点相同，不提前 import（避免改变 rule/action 注册顺序）。
"""
from ._platform import AstrMessageEvent

from ._declared import declared

from .. import content as C
from .. import db
from ..commands.base import CommandBase, no_prof_waiting, require_player, require_battle

# v140 波2：野王体系（探索命中/结算/摸宝箱）—— 包内实现经本模块属性动态解析（测试 monkeypatch 面）
from ..core.wild_king import (
    explore_king, build_king_monster, open_chest,
    wild_king_summary,
)
# v181 P4-1 试点：每日元数据键 + 达标结算单点已收敛至 services.quests（兼容再导出：原顶层名照旧）
from ..services.quests import DAILY_META_KEYS, settle_daily_quest  # noqa: F401

from .. import bootstrap as _bootstrap                       # noqa: E402

_bootstrap.package_apply()                                   # 本进程唯一包加载口（幂等；失败抛）
from content import combat_cmds as _CC                        # noqa: E402

import sys as _sys                                           # noqa: E402
_CC.bind_host(db=db, content=C,
              **{"commands.combat": _sys.modules[__name__]})  # 宿主替身注入（正文 `db.`/`C.` 不改）

# ---- 搬迁再导出（模块级名字集合与改造前逐名相同；消费者零改动）----
# game/commands/instance.py:1484 / :1495
pet_battle_status_note = _CC.pet_battle_status_note
resource_stack_text = _CC.resource_stack_text
# tests/test_v104_explore_map.py:42
WORLD_BOSS_DROPS = _CC.WORLD_BOSS_DROPS
# 其余原顶层名（无外部消费者，保名字集合一致）
RESOURCE_STACK_CN = _CC.RESOURCE_STACK_CN
WORLD_BOSS_DOT_INTERVAL = _CC.WORLD_BOSS_DOT_INTERVAL
_curve_vals = _CC._curve_vals
_fmt_mult = _CC._fmt_mult
_res_display_name = _CC._res_display_name
_battle_locks = _CC._battle_locks


class CombatCmds(CommandBase):
    """命令层（B10 L5 薄壳）：注册 + 守卫 + 取玩家/取参 + 调包 + 渲染；实现全在包内
    `content/combat_cmds.py`。"""
    def _b_enemy(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._b_enemy`（B10 L5 薄壳）。"""
        return _CC._b_enemy(self, *args, **kwargs)

    @declared("explore")
    @require_player()
    @no_prof_waiting()
    async def explore(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _CC.explore(self, event, group_id, qq_id, player):
            yield _r

    @declared("wild_king_chest")
    @require_player()
    async def wild_king_chest(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _CC.wild_king_chest(self, event, group_id, qq_id, player):
            yield _r

    def _main_kill_target_on_map(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._main_kill_target_on_map`（B10 L5 薄壳）。"""
        return _CC._main_kill_target_on_map(self, *args, **kwargs)

    def _in_battle(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._in_battle`（B10 L5 薄壳）。"""
        return _CC._in_battle(self, *args, **kwargs)

    def _lock_battle(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._lock_battle`（B10 L5 薄壳）。"""
        return _CC._lock_battle(self, *args, **kwargs)

    def _unlock_battle(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._unlock_battle`（B10 L5 薄壳）。"""
        return _CC._unlock_battle(self, *args, **kwargs)

    # ---- N5b4-2：saintess_engine 战斗构造/恢复统一入口（命令层不手拼 sides）----

    def _open_battle(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._open_battle`（B10 L5 薄壳）。"""
        return _CC._open_battle(self, *args, **kwargs)

    def _restore_battle(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._restore_battle`（B10 L5 薄壳）。"""
        return _CC._restore_battle(self, *args, **kwargs)

    def _sync_battle_player(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._sync_battle_player`（B10 L5 薄壳）。"""
        return _CC._sync_battle_player(self, *args, **kwargs)

    def _mount_explore_bonus(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._mount_explore_bonus`（B10 L5 薄壳）。"""
        return _CC._mount_explore_bonus(self, *args, **kwargs)

    def _roll_hidden_monster(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._roll_hidden_monster`（B10 L5 薄壳）。"""
        return _CC._roll_hidden_monster(self, *args, **kwargs)

    @declared("wish")
    @require_player()
    async def wish(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        opt = self._strip_cmd(event, "许愿").strip()
        async for _r in _CC.wish(self, event, group_id, qq_id, player, opt):
            yield _r

    @declared("trader_confirm")
    @require_player()
    async def trader_confirm(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        async for _r in _CC.trader_confirm(self, event, group_id, qq_id):
            yield _r

    @declared("revive_confirm")
    @require_player()
    async def revive_confirm(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        async for _r in _CC.revive_confirm(self, event, group_id, qq_id):
            yield _r

    def _roll_find_quest_events(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._roll_find_quest_events`（B10 L5 薄壳）。"""
        return _CC._roll_find_quest_events(self, *args, **kwargs)

    # ---------- v104 M23：雨事件消费（rain_{gid}_{qid} 只写不读修复）----------

    _RAIN_WINDOW = 1800  # 30 分钟

    def _rain_boost(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._rain_boost`（B10 L5 薄壳）。"""
        return _CC._rain_boost(self, *args, **kwargs)

    def _handle_explore_event(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._handle_explore_event`（B10 L5 薄壳）。"""
        return _CC._handle_explore_event(self, *args, **kwargs)

    # ---------- v101.30d #O22/O42：探索事件短间隔去重（策划案 02 章 7.6）----------
    # v104 修复 M20：模板占位符 {qid} 与 .format(gid=..., qq_id=...) 不匹配 →
    # _handle_explore_event 35% 探索事件路径必抛 KeyError 'qid'，改为 {qq_id}

    _EXPLORE_RECENT_KEY = "explore_recent_{gid}_{qq_id}"

    _EXPLORE_RECENT_MAX = 3

    def _recent_explore_events(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._recent_explore_events`（B10 L5 薄壳）。"""
        return _CC._recent_explore_events(self, *args, **kwargs)

    def _remember_explore_event(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._remember_explore_event`（B10 L5 薄壳）。"""
        return _CC._remember_explore_event(self, *args, **kwargs)

    def _poi_daily_used(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._poi_daily_used`（B10 L5 薄壳）。"""
        return _CC._poi_daily_used(self, *args, **kwargs)

    def _handle_poi(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._handle_poi`（B10 L5 薄壳）。"""
        return _CC._handle_poi(self, *args, **kwargs)

    @declared("attack")
    @require_player()
    async def attack(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        target_arg = self._strip_cmd(event, "攻击").strip()
        async for _r in _CC.attack(self, event, group_id, qq_id, player, target_arg):
            yield _r

    @declared("skill")
    @require_player()
    async def skill(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        skill_name = self._strip_cmd(event, "技能")
        player = self._player(group_id, qq_id)
        async for _r in _CC.skill(self, event, group_id, qq_id, player, skill_name):
            yield _r

    def _skill_panel(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._skill_panel`（B10 L5 薄壳）。"""
        return _CC._skill_panel(self, *args, **kwargs)

    def _branch_skills_for(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._branch_skills_for`（B10 L5 薄壳）。"""
        return _CC._branch_skills_for(self, *args, **kwargs)

    def _player_skill_table(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._player_skill_table`（B10 L5 薄壳）。"""
        return _CC._player_skill_table(self, *args, **kwargs)

    # v56.3：技能功能标签（<kind><功能> 双标签，参考鱼鱼排版示例）
    # v63/#99 汉化补全：全量 effect/mech key → 中文展示名（原表只覆盖部分 →
    # 诗人旋律/战意/元素印记等英文 tag 泄漏到 <xx> 技能列表）。语义见
    # game/core/battle_mech.py 4.7 旋律注释 + SKILL_BUFF_EFFECTS 消费端。

    _MECH_CN = {"rage": "狂暴", "burn": "灼烧", "freeze": "冰冻", "poison": "中毒", "mark": "标记",
                "shadow": "影袭", "chi": "气力", "wind": "风印", "judge": "审判", "bless": "神恩",
                "iron": "铁壁", "shield": "圣盾", "arcane": "奥术", "cleanse": "净化", "stun": "眩晕",
                "spd_down": "减速", "mark_burst": "引爆", "arcane_burst": "奥爆",
                "bleed": "流血", "bone_rush": "骸骨", "corros": "腐蚀", "curse": "诅咒",
                "curse_refresh": "诅咒刷新", "element_burst": "元素引爆", "element_burst_3": "三系引爆",
                "element_burst_all": "全系引爆", "element_multi_mark": "多系印记", "faith_unload": "卸负",
                "finisher": "终结", "fire_mark": "火印", "guard_core_burst": "磐核爆发",
                "hunt_mark": "猎印", "ice_mark": "冰印", "lian_duan": "连段", "melody": "旋律",
                "melody_chant": "吟唱", "poison_burst": "毒爆", "poison_burst_finisher": "毒爆终结",
                "sacrifice": "献祭", "silence": "沉默", "soul_mark": "魂印", "thunder_mark": "雷印",
                "zhan_yi": "战意", "zhan_yi_cash": "战意兑换", "zhan_yi_fury": "战意狂暴"}

    _EFFECT_CN = {"atk_up": "攻击", "def_up": "防御", "matk_up": "魔攻", "spd_up": "速度", "crit_up": "暴击",
                  "atk_up_strong": "强攻", "matk_up_strong": "强魔攻", "mon_atk_down": "威压", "lifesteal": "吸血",
                  "counter": "反击", "rage_burst": "爆发", "burn_burst": "引爆", "bless_shield": "护盾",
                  "all_stat_cc": "全属性", "arcane_field": "奥术力场", "arcane_matrix": "奥术矩阵",
                  "arcane_shield": "相位盾", "atk_all": "全队攻击", "atk_matk_all": "全队攻魔",
                  "block_reflect": "格挡反伤", "cc_immune": "免控", "cleanse": "净化", "cleanse_all": "净化全队",
                  "crit_all": "全队暴击", "crit_hit_buff": "暴击命中", "disengage_dodge": "脱战闪避",
                  "dodge_buff": "闪避", "dodge_reduce_all": "全队闪避", "element_switch": "换系",
                  "hunt_team_dmg": "猎杀增伤", "matk_all": "全队魔攻", "protect": "守护",
                  "reduce": "减伤", "reduce_all": "全队减伤", "reduce_shield_all": "减伤护盾",
                  "shadow_dance": "影舞", "shield_all": "全队护盾", "shield_all_reduce": "护盾减伤",
                  "shield_block": "格挡盾", "shield_self": "护盾", "spd_all": "全队速度",
                  "spd_buff": "加速", "star_lock": "星轨锁定", "stealth": "潜行", "stealth_cc": "影遁",
                  "taunt": "嘲讽", "vuln": "死亡标记"}

    def _skill_tag(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._skill_tag`（B10 L5 薄壳）。"""
        return _CC._skill_tag(self, *args, **kwargs)

    def _skill_range_label(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._skill_range_label`（B10 L5 薄壳）。"""
        return _CC._skill_range_label(self, *args, **kwargs)

    def _skill_list_gains(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._skill_list_gains`（B10 L5 薄壳）。"""
        return _CC._skill_list_gains(self, *args, **kwargs)

    def _skill_gains_curve(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._skill_gains_curve`（B10 L5 薄壳）。"""
        return _CC._skill_gains_curve(self, *args, **kwargs)

    def _skill_list_page(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._skill_list_page`（B10 L5 薄壳）。"""
        return _CC._skill_list_page(self, *args, **kwargs)

    @declared("defend")
    @require_player()
    @require_battle()
    async def defend(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _CC.defend(self, event, group_id, qq_id, player):
            yield _r

    @declared("flee")
    @require_player()
    @require_battle()
    async def flee(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _CC.flee(self, event, group_id, qq_id, player):
            yield _r

    # ---------------- 战斗状态展示（v59） ----------------
    # 玩家 buff key → 显示名（v63 加 眩晕/冻结/沉默 控制状态）

    _P_BUFF_NAMES = {
        "atk_up": "⚔️攻击↑", "atk_up_strong": "⚔️攻击↑↑", "matk_up": "🔮魔攻↑",
        "matk_up_strong": "🔮魔攻↑↑", "def_up": "🛡️防御↑", "spd_up": "💨速度↑",
        "crit_up": "💥暴击↑", "counter": "🔄反击", "mon_atk_down": "😵敌攻↓",
        "food_atk_up": "🍖攻↑", "food_def_up": "🍖防↑", "food_spd_up": "🍖速↑",
        "food_crit_up": "🍖暴击↑", "food_matk_up": "🍖魔攻↑",
        # v101.28f 药水强度分档 + 特殊效果
        "atk_up_big": "⚔️攻击↑↑", "atk_up_small": "⚔️攻击↑", "spd_up_small": "💨速度↑",
        "crit_up_small": "💥暴击↑", "crit_up_big": "💥暴击↑↑",
        "next_atk_up": "⚔️蓄力", "heal_up": "✨治疗↑", "magic_resist": "🛡️魔抗↑",
        "thorns_pot": "🌵反伤", "dodge_pot": "💨闪避", "cc_immune": "🗿免疫控制",
        "execute_pot": "💀处决",
        "stun": "🌀眩晕", "freeze": "❄️冻结", "silence": "🤐沉默",
        "mortal_wound": "🤕重伤",
        # v125.1 P2-4：补漏显键（对照 BUFF_MULT 24 键 + 全量 p_buffs 写入点）
        "echo_bless": "✨回声祝福", "matk_up_pot": "🔮魔攻↑", "food_spd_up_small": "🍖速↑",
        "pene_pot": "🗡️物穿", "pene_magi_pot": "🔮法穿", "lifesteal_pot": "🩸吸血",
        "crit_dmg_pot": "💥暴伤", "block_pot": "🧱格挡",
        "spd_down": "💨减速", "atk_down": "😵攻↓", "revenge_atk": "⚔️复仇",
        "spellblade_surge": "🔮魔涌", "stealth": "🌫️潜行", "dodge_up": "💨闪避↑",
        # 注：atk_down 由 Boss 开场技『低吼削弱』写入（battle_mech.py _b_opening），
        # 目前无属性消费端（死键）——状态栏照实显示作透明标注，待数值接入
        # 注：reduce_all 存减伤百分比（float）且刻数由 _reduce_all_left 单独计时，
        # 无刻数可显示，故意不进本表（避免"剩0.3 刻"误导）
    }

    # 敌方状态 key → 显示名（v63 加 眩晕/沉默）

    _E_BUFF_NAMES = {
        "freeze": "❄️冻结", "stun": "🌀眩晕", "silence": "🤐沉默",
        "mon_atk_down": "😵攻↓", "mon_atk_up": "⚔️攻↑",
        "mon_atk_up_strong": "⚔️攻↑↑", "mon_def_up": "🛡️防↑", "def_down": "💔破甲",
        "spd_down": "💨减速", "poison": "☠️中毒", "mark": "🎯标记", "burn": "🔥灼烧",
        "summon": "👥召唤", "mortal_wound": "🤕重伤",
        # v125.1 P2-4：补漏显键（对照全量 e_buffs 写入点：Boss 盾/速/睡眠/减速 + 元素印记）
        "shield": "🛡️护盾", "spd_up": "💨速↑", "sleep": "😴睡眠",
        "mon_spd_down": "💨减速", "fire_mark": "🔥火印", "ice_mark": "❄️冰印",
        "thunder_mark": "⚡雷印",
    }

    # 玩家叠层 key → 显示名

    _STACK_NAMES = {
        "burn": "🔥灼烧", "poison": "☠️毒层", "rage": "🔥狂暴", "shadow": "🌑影袭",
        "chi": "🌀气力", "judge": "⚖️审判", "mark": "🎯标记", "wind": "💨风印",
        "iron": "🪨铁壁", "shield": "🛡️圣盾", "bless": "✨神恩",
    }

    # DOT/减益重构（契约 §7）：敌方持续减益（毒/灼烧/标记/流血）已从玩家侧 mech_stacks
    # 迁为敌方目标级状态 enemy["debuffs"]（层数=剩余结算次数），玩家状态栏不再显示它们，
    # 敌方状态栏改读 enemy["debuffs"]。此集合仅用于从玩家叠层中排除旧残留键（向前兼容）。

    _ENEMY_MECH_STACKS = ("burn", "poison", "mark", "bleed")

    # 敌方 debuffs 层 key → 显示名（契约 §7：☠️毒/🔥灼烧/🎯标记/🩸流血）

    _DEBUFF_NAMES = {
        "poison": "☠️毒", "burn": "🔥灼烧", "mark": "🎯标记", "bleed": "🩸流血",
    }

    @staticmethod
    def _buff_left_ticks(*args, **kwargs):
        """委托包内 `content/combat_cmds._buff_left_ticks`（B10 L5 薄壳）。"""
        return _CC._buff_left_ticks(*args, **kwargs)

    def _status_line(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._status_line`（B10 L5 薄壳）。"""
        return _CC._status_line(self, *args, **kwargs)

    def _resource_line(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._resource_line`（B10 L5 薄壳）。"""
        return _CC._resource_line(self, *args, **kwargs)

    def _player_unit_for_formation(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._player_unit_for_formation`（B10 L5 薄壳）。"""
        return _CC._player_unit_for_formation(self, *args, **kwargs)

    def _battle_formation_panel(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._battle_formation_panel`（B10 L5 薄壳）。"""
        return _CC._battle_formation_panel(self, *args, **kwargs)

    def _battle_footer(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._battle_footer`（B10 L5 薄壳）。"""
        return _CC._battle_footer(self, *args, **kwargs)

    def _handle_victory(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._handle_victory`（B10 L5 薄壳）。"""
        yield from _CC._handle_victory(self, *args, **kwargs)

    def _next_step_hint(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._next_step_hint`（B10 L5 薄壳）。"""
        return _CC._next_step_hint(self, *args, **kwargs)

    def _nearest_town(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._nearest_town`（B10 L5 薄壳）。"""
        return _CC._nearest_town(self, *args, **kwargs)

    def _handle_defeat(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._handle_defeat`（B10 L5 薄壳）。"""
        yield from _CC._handle_defeat(self, *args, **kwargs)

    @declared("hunt_boss")
    @require_player()
    @no_prof_waiting()
    async def hunt_boss(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _CC.hunt_boss(self, event, group_id, qq_id, player):
            yield _r

    def _grant_worldboss_drop(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._grant_worldboss_drop`（B10 L5 薄壳）。"""
        return _CC._grant_worldboss_drop(self, *args, **kwargs)

    async def _worldboss_act(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._worldboss_act`（B10 L5 薄壳）。"""
        async for _r in _CC._worldboss_act(self, *args, **kwargs):
            yield _r

    def _parse_target_qq(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._parse_target_qq`（B10 L5 薄壳）。"""
        return _CC._parse_target_qq(self, *args, **kwargs)

    def _red_until(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._red_until`（B10 L5 薄壳）。"""
        return _CC._red_until(self, *args, **kwargs)

    def _is_redname(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._is_redname`（B10 L5 薄壳）。"""
        return _CC._is_redname(self, *args, **kwargs)

    def _get_honor(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._get_honor`（B10 L5 薄壳）。"""
        return _CC._get_honor(self, *args, **kwargs)

    def _pvp_meta_qqs(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._pvp_meta_qqs`（B10 L5 薄壳）。"""
        return _CC._pvp_meta_qqs(self, *args, **kwargs)

    def _pvp_snapshot(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._pvp_snapshot`（B10 L5 薄壳）。"""
        return _CC._pvp_snapshot(self, *args, **kwargs)

    def _pvp_handle_timeout(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._pvp_handle_timeout`（B10 L5 薄壳）。"""
        return _CC._pvp_handle_timeout(self, *args, **kwargs)

    def _set_pvp_cd(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._set_pvp_cd`（B10 L5 薄壳）。"""
        return _CC._set_pvp_cd(self, *args, **kwargs)

    def _pvp_cd_left(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._pvp_cd_left`（B10 L5 薄壳）。"""
        return _CC._pvp_cd_left(self, *args, **kwargs)

    # ---------------- v84 荣誉商店（26 章 3.3；v99.4 数据化 → data/honor_shop.py） ----------------

    @declared("honor_shop")
    @require_player()
    async def honor_shop(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        raw = self._strip_cmd(event, "荣誉").strip()
        async for _r in _CC.honor_shop(self, event, group_id, qq_id, player, raw):
            yield _r

    async def _honor_buy(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._honor_buy`（B10 L5 薄壳）。"""
        async for _r in _CC._honor_buy(self, *args, **kwargs):
            yield _r

    async def _pvp_start(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._pvp_start`（B10 L5 薄壳）。"""
        async for _r in _CC._pvp_start(self, *args, **kwargs):
            yield _r

    async def _pvp_act(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._pvp_act`（B10 L5 薄壳）。"""
        async for _r in _CC._pvp_act(self, *args, **kwargs):
            yield _r

    async def _pvp_finish(self, *args, **kwargs):
        """委托包内 `content/combat_cmds._pvp_finish`（B10 L5 薄壳）。"""
        async for _r in _CC._pvp_finish(self, *args, **kwargs):
            yield _r

    # ============================================================
    # v139 战前指令（职业融合：双形态预设 / 终结阈值 / 查看）
    # 存储：player["battle_prefs"]（JSON dict，随玩家存档持久化）
    # ============================================================
    # 双形态职业 → 形态名（与 classes.py dual_form.form 对齐）

    _DF139_CLASS_FORMS = {
        "cls_zhan_shi": ("狂暴", "fury"),
    }

    # 刺客终结阈值四档（classes.py finisher_threshold.options）

    _FINISHER139_OPTIONS = ("快刀", "满刃", "残血", "满段")

    @declared("battle_prefs_form")
    @require_player()
    async def battle_prefs_form(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        text = (event.get_message_str() or "").strip()
        arg = text.split("战前形态", 1)[1].strip() if "战前形态" in text else ""
        async for _r in _CC.battle_prefs_form(self, event, group_id, qq_id, player, arg):
            yield _r

    @declared("battle_prefs_finisher")
    @require_player()
    async def battle_prefs_finisher(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        text = (event.get_message_str() or "").strip()
        arg = text.split("战前阈值", 1)[1].strip() if "战前阈值" in text else ""
        async for _r in _CC.battle_prefs_finisher(self, event, group_id, qq_id, player, arg):
            yield _r

    # 奥术力场两档（奥术力场 desc「选择护盾或利刃」——2026-09-11 交互落地）

    _ARCANE_FIELD_OPTIONS = ("盾", "刃")

    @declared("battle_prefs_arcane_field")
    @require_player()
    async def battle_prefs_arcane_field(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        text = (event.get_message_str() or "").strip()
        arg = text.split("战前力场", 1)[1].strip() if "战前力场" in text else ""
        async for _r in _CC.battle_prefs_arcane_field(self, event, group_id, qq_id, player, arg):
            yield _r

    @declared("battle_prefs_view")
    @require_player()
    async def battle_prefs_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _CC.battle_prefs_view(self, event, group_id, qq_id, player):
            yield _r
