# -*- coding: utf-8 -*-
"""v9 统一战斗引擎 —— 遇怪 / 世界BOSS / PVP 共用

核心：Battle 状态机
  - 持久化：db.save_battle 存 state dict（battle_state.state 字段）
  - buff 系统：玩家/敌方各自 buff 表 {effect: 剩余回合}，每回合递减
  - 技能特效全部落地：旧 engine.player_attack 的 extra（破甲降防/寒冰减速/毒箭中毒/
    标记猎杀/处决残血/吸血）此前被 main.py 丢弃，这里真正写入战斗状态并生效
  - 敌方增益也落地：monster_turn 的 mextra（mon_atk_up/mon_def_up）此前被丢弃

btype:
  - monster   : 探索遇怪（可逃跑）
  - worldboss : 世界 Boss（v9.1 启用，不可逃跑）
  - pvp       : 玩家对战（v9.2 启用，不可逃跑，enemy 为对方玩家快照）
"""
import random

from . import content as C
from . import engine as E


# 增益倍率映射：effect -> (修正属性, 倍率/加成)
BUFF_MULT = {
    "atk_up":         ("atk", 1.30),
    "atk_up_strong":  ("atk", 1.75),
    "matk_up":        ("matk", 1.35),
    "matk_up_strong": ("matk", 1.80),
    "def_up":         ("def", 1.45),
    "spd_up":         ("spd", 1.40),
    "crit_up":        ("crit", 0.20),      # 暴击率 +20%
    "mon_atk_up":     ("atk", 1.30),
    "mon_atk_up_strong": ("atk", 1.70),
    "mon_def_up":     ("def", 1.40),
    "mon_atk_down":   ("atk", 0.70),   # v51 挫志怒吼：敌方攻击 -30%
}
# 负面效果
DEF_DOWN_MULT = 0.5   # 破甲斩：敌方防御减半
SPD_DOWN_MULT = 0.5   # 寒冰箭：敌方速度减半（暂不影响结算，留接口）
POISON_PCT = 0.05     # 毒箭：每回合扣敌方 max_hp 5%
MARK_EXTRA = 0.30     # 标记猎杀：敌方受击伤害 +30%
DEFEND_REDUCE = 0.5   # 防御：敌方伤害减半
BUFF_TURNS = 3        # 增益默认持续回合
DEBUFF_TURNS = 2      # 减益默认持续回合


class Battle:
    def __init__(self, btype: str = "monster", enemy: dict | None = None, title_bonus: dict = None, player: dict | None = None):
        self.btype = btype                 # monster | worldboss | pvp
        self.round = 0
        self.enemy = enemy or {}           # 敌方单位 dict（怪物 / Boss / 玩家快照）
        self.p_buffs: dict = {}            # 玩家增益 {effect: turns}
        self.e_buffs: dict = {}            # 敌方状态 {effect: turns}（含减益）
        self.p_defending = False           # 玩家本回合是否防御
        self.e_defending = False
        self.result = None                 # None | victory | defeat | fled
        self.title_bonus = title_bonus or {}  # 副业大师称号属性加成
        self.team_effects: list = []         # v50 团队技能效果（副本全队广播用）
        self.mech_stacks: dict = {}          # v59 分支机制叠层（随战斗持久化，不再挂 player 避免每回合丢失）
        self.shield: int = 0                     # v59 护盾值（随战斗持久化，player 无此列会每回合丢）
        # v2.0 核心资源（12 章 1.2：怒气/元素亲和/精力/信仰/连击点/气）
        # 随战斗序列化，同 mech_stacks 机制；阶段五引擎先挂载，技能数据落地后消费
        self.resources: dict = {}          # v2.0 核心资源（怒气/元素亲和/精力/信仰/连击点/气），随战斗序列化
        self.cooldown: dict = {}           # v2.0 技能冷却（技能名 → 剩余回合数），随战斗序列化；回合结束递减
        if player:
            self._init_resources(player)
        # v61 进度条速度机制：每回合双方进度 + 各自速度，差距攒够慢方速度 → 快方额外行动
        self.p_progress: float = 0.0          # 玩家行动进度
        self.e_progress: float = 0.0          # 敌方行动进度
        self.p_extra_left: int = 0            # 玩家本回合剩余额外行动次数（自由选择出手）
        self.e_extra_left: int = 0            # 敌方本回合剩余额外行动次数
        self.e_first: bool = False            # 敌方是否先手（速度更快）

    # ---------------- 序列化 ----------------
    def to_state(self) -> dict:
        return {
            "type": self.btype,
            "round": self.round,
            "enemy": self.enemy,
            "p_buffs": self.p_buffs,
            "e_buffs": self.e_buffs,
            "p_defending": self.p_defending,
            "e_defending": self.e_defending,
            "title_bonus": self.title_bonus,
            "mech_stacks": self.mech_stacks,
            "shield": self.shield,
            "resources": self.resources,
            "cooldown": self.cooldown,
            "p_progress": self.p_progress,
            "e_progress": self.e_progress,
            "p_extra_left": self.p_extra_left,
            "e_extra_left": self.e_extra_left,
            "e_first": self.e_first,
        }

    @classmethod
    def from_state(cls, st: dict):
        b = cls(st.get("type", "monster"), st.get("enemy", {}), st.get("title_bonus") or {})
        b.round = st.get("round", 0)
        b.p_buffs = st.get("p_buffs", {}) or {}
        b.e_buffs = st.get("e_buffs", {}) or {}
        b.p_defending = st.get("p_defending", False)
        b.e_defending = st.get("e_defending", False)
        b.mech_stacks = st.get("mech_stacks", {}) or {}
        b.shield = int(st.get("shield", 0) or 0)
        b.resources = st.get("resources", {}) or {}
        b.cooldown = st.get("cooldown", {}) or {}
        b.team_effects = []
        # v61 进度条字段（老存档用 .get 兜底为 0）
        b.p_progress = float(st.get("p_progress", 0) or 0)
        b.e_progress = float(st.get("e_progress", 0) or 0)
        b.p_extra_left = int(st.get("p_extra_left", 0) or 0)
        b.e_extra_left = int(st.get("e_extra_left", 0) or 0)
        b.e_first = bool(st.get("e_first", False))
        return b

    # ---------------- 核心资源（v2.0） ----------------
    def _init_resources(self, player: dict):
        """战斗开始：按职业初始化核心资源 dict。
        元素亲和（法师）默认 fire；游侠精力满 100；其余 0。"""
        cls = player.get("class_name", "")
        rd = E.core_resource_def(cls)
        if not rd:
            return
        k = rd["key"]
        if k == "element":
            self.resources[k] = "fire"
        elif k == "energy":
            self.resources[k] = rd.get("max", 100)
        else:
            self.resources[k] = 0

    def _resource_label(self, player: dict) -> str:
        """战斗状态栏显示核心资源（如 ⚡ 怒气 3/10）。"""
        cls = player.get("class_name", "")
        rd = E.core_resource_def(cls)
        if not rd:
            return ""
        k = rd["key"]
        v = self.resources.get(k, 0)
        if k == "element":
            return f"✦ {E.ELEMENT_CN.get(v, '?')}系"
        return f"✦ {rd['name']} {v}/{rd['max']}"

    # ---------------- 技能冷却（v2.0） ----------------
    def _skill_cd_left(self, skill_name: str) -> int:
        """技能剩余冷却回合数（0 = 可用）。"""
        return int(self.cooldown.get(skill_name, 0) or 0)

    def _skill_on_cd(self, skill_name: str) -> bool:
        return self._skill_cd_left(skill_name) > 0

    def _set_skill_cd(self, skill_name: str, cd: int):
        """设置技能冷却（cd 回合，1 表示下一回合即可用）。"""
        if cd > 0:
            self.cooldown[skill_name] = cd

    def _tick_cooldowns(self):
        """回合结束：所有冷却 -1，归零清除。"""
        for k in list(self.cooldown):
            self.cooldown[k] -= 1
            if self.cooldown[k] <= 0:
                del self.cooldown[k]

    # ---------------- 玩家行动入口 ----------------
    def player_turn(self, action: str, skill_name: str | None, player: dict, enemy_act: bool = True) -> tuple:
        """执行玩家行动。返回 (日志列表, 是否结束)
        action: attack | skill | defend | flee | use_item
        player: 玩家 dict（战斗内会修改 hp/mp，由调用方负责存库）
        enemy_act: 是否在玩家行动后立即结算敌方回合（PVP 传 False，由对方真人操作）
        v61：进度条速度机制——双方进度各+速度，攒够慢方速度获得额外行动。
        玩家额外行动可自由选择出手方式（攻击/技能/道具），不再自动普攻。
        """
        logs = []
        # v63 额外行动阶段被控：眩晕/冻结跳过（消耗额外行动但不执行动作）
        if self.p_extra_left > 0 and ("stun" in self.p_buffs or "freeze" in self.p_buffs):
            logs.append("🌀 你被控制，无法出手！")
            self.p_extra_left = 0
            self.p_buffs.pop("stun", None)
            self.p_buffs.pop("freeze", None)
            return self._enemy_phase(player, logs, enemy_act)
        # 额外行动阶段（上回合速度优势还没用完）：不结算新回合，直接自由出手
        if self.p_extra_left > 0 and action in ("attack", "skill", "use_item"):
            self.p_extra_left -= 1
            if action == "use_item":
                logs += self._do_use_item(skill_name or "", player)
            elif action == "skill":
                logs += self._do_player_skill(skill_name, player)
            else:
                logs += self._player_attack(self._player_stats(player), player)
            if self._enemy_dead():
                self.result = "victory"
                self._end_round()
                return logs, True
            if self.p_extra_left > 0:
                logs.append(f"⚡ 速度优势！你还可以行动 {self.p_extra_left} 次（『攻击』『技能 <名称>』『使用 <道具>』）")
                return logs, False
            # 额外行动用完 → 敌方行动
            return self._enemy_phase(player, logs, enemy_act)
        # 额外行动阶段选择防御/逃跑：放弃剩余速度优势，直接进入防御/逃跑（不开新回合）
        if self.p_extra_left > 0 and action in ("defend", "flee"):
            self.p_extra_left = 0
            if action == "defend":
                logs.append("🛡️ 你架起防御姿态，受到的伤害减半！")
                self.p_defending = True
                return self._enemy_phase(player, logs, enemy_act, defend=True)
            return self._do_flee(player, logs, self.e_extra_left)

        # ---- 正常回合开始 ----
        self.round += 1
        logs += self._turn_start(player)
        # v61 进度条速度机制（PVP 保持真人轮流，不介入）
        p_extra = e_extra = 0
        e_first = False
        if self.btype != "pvp":
            p_extra, e_extra, e_first = self._speed_plan(player)
        # v63 玩家被控：眩晕/冻结 → 跳过本回合行动（敌方照常行动）
        if "stun" in self.p_buffs:
            logs.append("🌀 你被眩晕，无法行动！")
            self.p_buffs.pop("stun", None)
            return self._enemy_phase(player, logs, enemy_act)
        if "freeze" in self.p_buffs:
            logs.append("❄️ 你被冻结，无法行动！")
            self.p_buffs.pop("freeze", None)
            return self._enemy_phase(player, logs, enemy_act)
        # v63 玩家被沉默：技能类行动被拦截，只能普攻/防御/道具
        if "silence" in self.p_buffs and action == "skill":
            logs.append("🤐 你被沉默，无法使用技能！（只能普攻/防御/道具）")
            action = "attack"

        if action == "defend":
            return self._do_defend(player, logs, enemy_act, e_extra)
        if action == "flee":
            return self._do_flee(player, logs, e_extra)
        if action == "use_item":
            logs += self._do_use_item(skill_name or "", player)
            if self._enemy_dead():
                self.result = "victory"
                self._end_round()
                return logs, True
            # 用道具后速度优势仍在 → 留给玩家自由选择
            if self.p_extra_left > 0:
                logs.append(f"⚡ 速度优势！你还可以行动 {self.p_extra_left} 次（『攻击』『技能 <名称>』『使用 <道具>』）")
                return logs, False
            return self._enemy_phase(player, logs, enemy_act)

        st = self._player_stats(player)
        # v61：敌方先手 → 先挨一下再行动
        if e_first and enemy_act:
            mlogs, dmg = self._enemy_turn(player)
            logs += mlogs
            self._damage_player(player, dmg, logs)
            if self._player_dead(player):
                self.result = "defeat"
                self._end_round()
                return logs, True
        if action == "skill":
            logs += self._do_player_skill(skill_name, player)
        else:
            logs += self._player_attack(st, player)

        if self._enemy_dead():
            self.result = "victory"
            self._end_round()
            return logs, True

        # v61：玩家速度优势 → 额外行动留给玩家自由选择（不再自动普攻）
        if self.p_extra_left > 0:
            logs.append(f"⚡ 速度优势！你获得了 {self.p_extra_left} 次额外行动，可自由出手（『攻击』『技能 <名称>』『使用 <道具>』）")
            return logs, False

        # 玩家无额外行动 → 敌方行动
        return self._enemy_phase(player, logs, enemy_act)

    def _enemy_phase(self, player: dict, logs: list, enemy_act: bool, defend: bool = False) -> tuple:
        """敌方行动阶段：行动 1 次 + 额外次数（先手时先手一击已打，只补额外）
        defend=True 时敌方伤害减半（额外行动阶段防御用）"""
        if enemy_act:
            e_acts = self.e_extra_left if self.e_first else (1 + self.e_extra_left)
            self.e_extra_left = 0
            for _ in range(e_acts):
                if self._player_dead(player):
                    break
                mlogs, dmg = self._enemy_turn(player)
                logs += mlogs
                if defend and dmg > 0:
                    dmg = max(1, int(dmg * DEFEND_REDUCE))
                    logs.append(f"（格挡后 {dmg} 点伤害）")
                self._damage_player(player, dmg, logs)
                if self._player_dead(player):
                    self.result = "defeat"
        self._end_round()
        return logs, self.result is not None

    def _do_use_item(self, payload: str, player: dict) -> list:
        """战斗中使用消耗品：恢复/增益（v61 抽公共，普通回合与额外行动共用）"""
        logs = []
        if payload.startswith("buff:"):
            # v54 战斗药水：effect → p_buffs 增益 3 回合
            kind = payload[5:]
            _cn = {"atk_up": "攻击", "def_up": "防御", "spd_up": "速度", "crit_up": "暴击"}
            self.p_buffs[kind] = max(self.p_buffs.get(kind, 0), 3)
            logs.append(f"🧪 你饮下战斗药水，{_cn.get(kind, kind)}大幅提升！（3 回合）")
        else:
            heal = int(payload or 0)  # 复用 skill_name 传恢复量
            if heal > 0:
                before = player["hp"]
                player["hp"] = min(player.get("max_hp", player["hp"]), player["hp"] + heal)
                logs.append(f"💊 你使用了战斗道具，恢复 {player['hp'] - before} 点生命！（{player['hp']}/{player['max_hp']}）")
            else:
                logs.append("💊 你使用了战斗道具！")
        return logs

    def _do_player_skill(self, skill_name: str, player: dict) -> list:
        """玩家施放技能（v61 抽公共，普通回合与额外行动共用）"""
        logs = []
        st = self._player_stats(player)
        info = E.skill_info(player["class_name"], skill_name)
        if not info:
            logs.append(f"没有技能『{skill_name}』！")
            return logs
        if not E.is_skill_learned(player["class_name"], player["level"], skill_name,
                                  player.get("learned_skills", [])):
            logs.append(f"该技能需要 Lv.{info['lv']} 才能使用，你才 Lv.{player['level']}（或『技能学习 {skill_name}』提前学习）")
            return logs
        # v2.0 冷却：CD 未结束拦截（强控/终结技等）
        if self._skill_on_cd(skill_name):
            left = self._skill_cd_left(skill_name)
            logs.append(f"⏳【{skill_name}】还在冷却中（剩余 {left} 回合）！")
            return logs
        if player["mp"] < info["mp"]:
            logs.append("💙 魔力不足！")
            return logs
        # v34 符文·聚能：MP 消耗 -x%
        mana_lvl = self._enchant_lvl(self._enchant_effects(player), "mana_flow")
        mp_cost = info["mp"]
        if mana_lvl:
            mp_cost = max(1, int(mp_cost * (1 - C.rune_value("mana_flow", mana_lvl))))
        player["mp"] -= mp_cost
        logs += self._player_skill(st, skill_name, info, player)
        # v2.0 冷却：技能表 cd 字段（回合），施放后进入冷却
        cd = info.get("cd", 0)
        if cd:
            self._set_skill_cd(skill_name, cd)
        return logs

    # ---------------- 防御 / 逃跑 ----------------
    def _speed_plan(self, player: dict) -> tuple:
        """v61 进度条速度机制：每回合双方进度 + 各自速度，
        进度差攒够「慢方速度」→ 快方获得 1 次额外行动（余数保留，无阈值跳跃）。
        返回 (玩家额外次数, 敌方额外次数, 敌方是否先手)。PVP 不介入。
        例：10速 vs 11速 → 每回合差 1 点，第 10 回合敌方进度超 10 → 敌方 +1 行动。
        """
        if self.btype == "pvp":
            return 0, 0, False
        pst = self._player_stats(player)
        est = self._enemy_stats()
        p_spd = max(1, pst.get("spd", 0) or 1)
        e_spd = max(1, est.get("spd", 0) or 1)
        # 进度条累计
        self.p_progress = float(self.p_progress or 0) + p_spd
        self.e_progress = float(self.e_progress or 0) + e_spd
        # 玩家领先 → 玩家获得额外行动（每攒够敌方速度 1 次；余数保留）
        # 每回合封顶 2 次额外（最多 3 次行动/回合），防速度碾压连击爆炸（v61 平衡）
        while self.p_progress - self.e_progress >= e_spd and self.p_extra_left < 2:
            self.p_extra_left += 1
            self.p_progress -= e_spd
        # 敌方领先 → 敌方获得额外行动（每攒够玩家速度 1 次；余数保留）
        while self.e_progress - self.p_progress >= p_spd and self.e_extra_left < 2:
            self.e_extra_left += 1
            self.e_progress -= p_spd
        # 先手：速度快者先，同速玩家先（保底）
        e_first = e_spd > p_spd
        self.e_first = e_first
        return self.p_extra_left, self.e_extra_left, e_first

    def _do_defend(self, player: dict, logs: list, enemy_act: bool = True, e_extra: int = 0) -> tuple:
        logs.append("🛡️ 你架起防御姿态，受到的伤害减半！")
        self.p_defending = True
        if enemy_act:
            mlogs, dmg = self._enemy_turn(player)
            logs += mlogs
            if dmg > 0:
                dmg = max(1, int(dmg * DEFEND_REDUCE))
                logs.append(f"（格挡后 {dmg} 点伤害）")
            self._damage_player(player, dmg, logs)
            if self._player_dead(player):
                self.result = "defeat"
            # v57：敌方速度优势 → 连续追击（防御姿态同样减半）
            for _ in range(e_extra):
                if self._player_dead(player):
                    break
                mlogs, dmg = self._enemy_turn(player)
                logs += mlogs
                if dmg > 0:
                    dmg = max(1, int(dmg * DEFEND_REDUCE))
                    logs.append(f"（格挡后 {dmg} 点伤害）")
                self._damage_player(player, dmg, logs)
                if self._player_dead(player):
                    self.result = "defeat"
        self._end_round()
        return logs, self.result is not None

    def _do_flee(self, player: dict, logs: list, e_extra: int = 0) -> tuple:
        if self.btype in ("worldboss", "pvp"):
            logs.append("💨 这里无法逃跑！背水一战吧！")
            if self.btype == "pvp":
                # PVP：不触发 AI 反击，等对方真人行动
                return logs, False
            mlogs, dmg = self._enemy_turn(player)
            logs += mlogs
            self._damage_player(player, dmg, logs)
            if self._player_dead(player):
                self.result = "defeat"
            for _ in range(e_extra):
                if self._player_dead(player):
                    break
                mlogs, dmg = self._enemy_turn(player)
                logs += mlogs
                self._damage_player(player, dmg, logs)
                if self._player_dead(player):
                    self.result = "defeat"
            self._end_round()
            return logs, self.result is not None
        if random.random() < 0.75:
            logs.append("💨 你成功脱离了战斗！")
            self.result = "fled"
            return logs, True
        logs.append("逃跑失败！被追上了！")
        mlogs, dmg = self._enemy_turn(player)
        logs += mlogs
        self._damage_player(player, dmg, logs)
        if self._player_dead(player):
            self.result = "defeat"
        for _ in range(e_extra):
            if self._player_dead(player):
                break
            mlogs, dmg = self._enemy_turn(player)
            logs += mlogs
            self._damage_player(player, dmg, logs)
            if self._player_dead(player):
                self.result = "defeat"
        self._end_round()
        return logs, self.result is not None

    # ---------------- 玩家行动结算 ----------------
    def _enchant_effects(self, player: dict) -> dict:
        """v34：读取玩家已装备符文效果 → {effect: 最高等级}"""
        effects = {}
        for slot, item in (player.get("equipment") or {}).items():
            if not item:
                continue
            for en in item.get("enchant", []):
                if en.get("effect"):
                    lvl = int(en.get("lvl", 1) or 1)
                    effects[en["effect"]] = max(effects.get(en["effect"], 0), lvl)
        return effects

    def _enchant_lvl(self, effs: dict, effect: str) -> int:
        """符文效果等级（无则 0）"""
        return int(effs.get(effect, 0) or 0)

    def _player_stats(self, player: dict) -> dict:
        st = E.player_final_stats(player["class_name"], player["level"],
                                  player.get("equipment", {}),
                                  player.get("class_tier", 0),
                                  player.get("attributes"),
                                  player.get("evolve_path", 0),
                                  getattr(self, "title_bonus", None) or {})
        st = self._apply_buffs(st, self.p_buffs)
        # v33/v34 符文属性：疾风(速度+) / 铁壁(防御+)
        effs = self._enchant_effects(player)
        if self._enchant_lvl(effs, "swift"):
            st["spd"] = int(st.get("spd", 0) * (1 + C.rune_value("swift", effs["swift"])))
        if self._enchant_lvl(effs, "ironwall"):
            st["def"] = int(st.get("def", 0) * (1 + C.rune_value("ironwall", effs["ironwall"])))
        # v64 被动属性：魔力涌动/风行步/疾影/鹰眼（百分比属性被动）
        pb = E.player_passive_stats(player["class_name"], player.get("learned_skills", []))
        if pb.get("mp_mult", 1.0) != 1.0:
            st["max_mp"] = int(st.get("max_mp", 0) * pb["mp_mult"])
            st["mp"] = int(st.get("mp", 0) * pb["mp_mult"])
        if pb.get("spd_mult", 1.0) != 1.0:
            st["spd"] = int(st.get("spd", 0) * pb["spd_mult"])
        if pb.get("crit_add", 0.0):
            st["crit"] = min(st.get("crit", 0) + pb["crit_add"], 0.6)
        return st

    def _player_attack(self, st: dict, player: dict) -> list:
        """普攻（含标记加成 + v10 套装攻击特效 + v34 符文效果）"""
        logs = []
        est = self._enemy_stats()
        effs = self._enchant_effects(player)
        # v34 破甲：无视 x% 防御（按等级）
        ap_lvl = self._enchant_lvl(effs, "armor_pierce")
        if ap_lvl:
            est = dict(est)
            est["def"] = int(est["def"] * (1 - C.rune_value("armor_pierce", ap_lvl)))
        is_crit = random.random() < st["crit"]
        dmg = E.calc_damage(st["atk"], est["def"], is_crit)
        # v34 残忍：暴击伤害 +x%（按等级）
        brutal_lvl = self._enchant_lvl(effs, "brutal")
        if brutal_lvl and is_crit:
            dmg = int(dmg * (1 + C.rune_value("brutal", brutal_lvl)))
        dmg = self._apply_mark(dmg)
        self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - dmg)
        tag = " 💥暴击" if is_crit else ""
        logs.append(f"你挥剑攻击，造成 {dmg} 点伤害！{tag}")
        # v34 符文攻击特效（灼烧/冻结/吸血/连锁/虚弱/破魔）
        self._apply_enchant_attack(effs, dmg, st, player, logs)
        self._set_attack_proc(player, dmg, logs)
        # v2.0 核心资源：普攻获取（战士怒气/刺客连击点/拳师气）
        self._resource_on_attack(player)
        return logs

    def _resource_on_attack(self, player: dict):
        """v2.0 核心资源：普攻/技能命中自动获取（on_attack/on_skill）。"""
        cls = player.get("class_name", "")
        rd = E.core_resource_def(cls)
        if not rd:
            return
        k = rd["key"]
        gain = rd.get("on_attack", 0)
        if gain:
            self.resources[k] = E.core_resource_gain(cls, self.resources, gain)

    def _apply_enchant_attack(self, effs: dict, dmg: int, st: dict, player: dict, logs: list):
        """v34：攻击后符文效果结算（灼烧/冻结/吸血/连锁/虚弱/破魔）"""
        if not effs:
            return
        p_mech = self.mech_stacks
        # 灼热：攻击附带灼烧 n 层
        burn_lvl = self._enchant_lvl(effs, "burn")
        if burn_lvl:
            p_mech["burn"] = E.mech_stack_gain("burn", p_mech, int(C.rune_value("burn", burn_lvl)))
            logs.append(f"🔥 符文灼热：敌人灼烧层数 {p_mech['burn']}")
        # 冰霜：x% 概率冻结 1 回合
        freeze_lvl = self._enchant_lvl(effs, "freeze")
        if freeze_lvl and random.random() < C.rune_value("freeze", freeze_lvl):
            self.e_buffs["freeze"] = 1
            logs.append("❄️ 符文冰霜：敌人被冻结，跳过下回合！")
        # 吸血：造成伤害的 x% 回复生命
        ls_lvl = self._enchant_lvl(effs, "lifesteal")
        if ls_lvl and dmg > 0:
            heal = int(dmg * C.rune_value("lifesteal", ls_lvl))
            player["hp"] = min(player.get("max_hp", player["hp"]), player.get("hp", 0) + heal)
            logs.append(f"🩸 符文吸血：回复 {heal} 点生命！")
        # 连锁：x% 概率额外雷击 y% 攻击伤害
        chain_lvl = self._enchant_lvl(effs, "chain")
        if chain_lvl:
            prob, mult = C.rune_value("chain", chain_lvl)
            if random.random() < prob:
                cd = int(st.get("atk", 0) * mult)
                self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - cd)
                logs.append(f"⚡ 符文连锁：雷击造成 {cd} 点额外伤害！")
        # 虚弱：攻击使敌人攻击 -x%（3 回合）
        weak_lvl = self._enchant_lvl(effs, "weaken")
        if weak_lvl:
            self.e_buffs["mon_atk_down"] = 3
            self.e_buffs["_weaken_val"] = C.rune_value("weaken", weak_lvl)
            logs.append(f"😵 符文虚弱：敌人攻击力下降！")
        # 破魔：魔法伤害 +x%（对普攻无加成，技能路径处理）
        mb_lvl = self._enchant_lvl(effs, "magic_break")
        if mb_lvl:
            pass  # 在技能魔法伤害里处理

    def _player_skill(self, st: dict, skill_name: str, info: dict, player: dict) -> list:
        """施放技能：治疗/增益/攻击 + 特效全部落地（v27 技能等级 + v29 分支机制）"""
        logs = []
        lv = int((player.get("skill_levels") or {}).get(skill_name, 1) or 1)
        kind = info["kind"]
        mech = info.get("mech", "")
        # v56：叠层随技能等级成长（每 2 级 +1 层）
        mval = E.skill_mech_val(info, lv)
        # 分支专属状态层（玩家侧：狂暴/圣盾/风印/影袭/气力/神恩/毒层）
        p_mech = self.mech_stacks
        if kind == "治疗":
            # v32 条件转化：治疗技能也吃战场状态（如神谕者自身低血时治疗量提升）
            cond_mult = self._cond_mult(info, player, lv)
            cond_label = info.get("cond", {}).get("label", "") if cond_mult > 1.0 else ""
            heal = int(st["matk"] * info["power"] * E.skill_power_mult(lv, info) * cond_mult)
            # v64 被动·神恩：治疗技能效果 +10%
            pv = E.passive_skills_learned(player["class_name"], player.get("learned_skills", []))
            if "神恩" in pv:
                heal = int(heal * 1.10)
            over = 0
            player["hp"] = min(player.get("max_hp", player["hp"]), player.get("hp", 0) + heal)
            # v64 被动·庇护之光：治疗溢出 20% 转为护盾
            if "庇护之光" in pv and player.get("hp", 0) >= player.get("max_hp", player["hp"]):
                overflow = player.get("hp", 0) - (player.get("max_hp", player["hp"]) - player.get("hp", 0))
                if overflow > 0:
                    shield_gain = int(overflow * 0.20)
                    self.shield = self.shield + shield_gain
                    logs.append(f"🛡️ 庇护之光：治疗溢出转化为 {shield_gain} 点护盾！")
            if player.get("hp", 0) >= player.get("max_hp", player["hp"]) and mech == "bless":
                over = heal - (player["hp"] - (player.get("max_hp", player["hp"]) - player.get("hp", 0)))
                p_mech["bless"] = E.mech_stack_gain("bless", p_mech, mval)
            logs.append(f"你施展【{skill_name}】，圣光治愈了你 {heal} 点生命！" + (f" ⚔️{cond_label} x{round(cond_mult, 1)}！" if cond_label else ""))
            if mech == "bless":
                logs.append(f"✨ 神恩凝聚：{p_mech.get('bless', 0)} 层（下次『神圣之光』转化护盾）")
            # v50 团队治疗：记录全队效果（副本广播）
            if info.get("team"):
                self.team_effects.append({"kind": "heal_all", "power": info["power"], "lv": lv, "matk": st["matk"]})
                logs.append(f"🌟【团队】圣光笼罩全队，所有人恢复 {heal} 点生命！")
            return logs
        if kind == "增益":
            eff = info.get("effect")
            if eff:
                if eff == "mon_atk_down":
                    # v51 挫志怒吼：敌方攻击下降（写 e_buffs 而非 p_buffs）
                    self.e_buffs["mon_atk_down"] = E.skill_buff_turns(lv)
                else:
                    self.p_buffs[eff] = E.skill_buff_turns(lv)
            # v30 条件转化：增益型引爆也吃战场状态（如元素狂暴残血引爆）
            cond_mult = self._cond_mult(info, player, lv)
            cond_label = info.get("cond", {}).get("label", "") if cond_mult > 1.0 else ""
            # v29：effect 型机制（引爆/转化类增益技能）
            if eff == "burn_burst":
                n = p_mech.get("burn", 0)
                st2 = self._player_stats(player)
                if st2 and n:
                    d = int(st2["matk"] * 0.30 * n * cond_mult)
                    self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - d)
                    logs.append(f"🔥 灼烧引爆！{n} 层造成 {d} 点伤害" + (f" ⚔️{cond_label} x{round(cond_mult, 1)}！" if cond_label else ""))
                p_mech["burn"] = 0
            elif eff == "rage_burst":
                n = p_mech.get("rage", 0)
                if n:
                    self.p_buffs["atk_up_strong"] = E.skill_buff_turns(1)
                    logs.append(f"🔥 狂战之魂！{n} 层狂暴 → 攻击大幅提升")
                p_mech["rage"] = 0
            elif eff == "bless_shield":
                n = p_mech.get("bless", 0)
                st2 = self._player_stats(player)
                if st2 and n:
                    shield = int(st2["matk"] * 0.08 * n)
                    self.shield = self.shield + shield
                    logs.append(f"✨ 神恩护盾！{n} 层转化为 {shield} 点护盾")
                p_mech["bless"] = 0
            self._apply_mech_gain(mech, mval, p_mech, logs, skill_name)
            logs.append(f"你施展【{skill_name}】！")
            # v50 团队增益：记录全队效果（副本广播）
            team = info.get("team")
            if team:
                st2 = self._player_stats(player)
                self.team_effects.append({"kind": team, "effect": eff, "lv": lv, "stats": st2})
                logs.append(f"🌟【团队】{info.get('name', skill_name)} 笼罩全队！")
            return logs

        if kind == "嘲讽":
            # v51 挑衅怒吼：嘲讽（单人=敌方降攻+叠狂暴；副本=instance 层拉仇恨）
            self.e_buffs["mon_atk_down"] = E.skill_buff_turns(lv)
            self._apply_mech_gain("rage", 1, p_mech, logs, skill_name)
            logs.append(f"📢 你大声挑衅【{self.enemy.get('name', '敌人')}】！敌人恼羞成怒，攻击力下降！")
            if info.get("team"):
                self.team_effects.append({"kind": "taunt", "lv": lv})
                logs.append(f"🌟【团队】{info.get('name', skill_name)}：Boss 的注意力被牢牢锁定！")
            return logs

        est = self._enemy_stats()
        is_crit = random.random() < st["crit"]
        # v34 符文：装备效果（破甲/暴伤/破魔/攻击特效）
        effs = self._enchant_effects(player)
        ap_lvl = self._enchant_lvl(effs, "armor_pierce")
        if ap_lvl:
            est = dict(est)
            est["def"] = int(est["def"] * (1 - C.rune_value("armor_pierce", ap_lvl)))
            est["mdef"] = int(est["mdef"] * (1 - C.rune_value("armor_pierce", ap_lvl)))
        # 机制：影袭（满血必暴）
        if mech == "shadow" and self.enemy.get("hp", 0) >= self.enemy.get("max_hp", 1):
            is_crit = True
        # 机制：冰霜（冻结目标碎冰增伤）
        frozen_bonus = 1.5 if (mech == "freeze" and "freeze" in self.e_buffs) else 1.0
        # 机制：圣光/毒/影/气/审判/狂暴 层数加成
        stack_bonus = self._mech_stack_bonus(mech, p_mech, info)
        # v30 条件转化：按战场状态变形态（残血斩杀/背水一战）
        cond_mult = self._cond_mult(info, player, lv)
        cond_label = ""
        if cond_mult > 1.0:
            cond_label = info.get("cond", {}).get("label", "")
        multi = info.get("multi", 1)
        # 机制：风印 → 连击次数增加
        if mech == "wind":
            multi += p_mech.get("wind", 0)
        # v34 破魔：魔法伤害 +x%
        mb_lvl = self._enchant_lvl(effs, "magic_break")
        magic_bonus = (1 + C.rune_value("magic_break", mb_lvl)) if mb_lvl and kind == "魔法" else 1.0
        # v64 被动：破甲本能（破防技能伤害+10%）/ 烈焰亲和（火系伤害+10%）
        pv = E.passive_skills_learned(player["class_name"], player.get("learned_skills", []))
        passive_bonus = 1.0
        if "破甲本能" in pv and info.get("pierce"):
            passive_bonus *= 1.10
        if "烈焰亲和" in pv and "火" in (skill_name or "") and kind == "魔法":
            passive_bonus *= 1.10
        # v2.0 元素反应：当前系 × 目标印记（技能带 element 字段时判定）
        element = info.get("element", "")
        reaction_mult = 1.0
        reaction_log = ""
        if element and E.ELEMENT_MARKS.get(element):
            marks = {k: v for k, v in self.e_buffs.items() if k in E.ELEMENT_MARKS.values()}
            r = E.element_reaction(element, marks)
            if r:
                reaction_mult = r["mult"]
                reaction_log = f"💥{r['name']}！"
                # 超载：额外全体伤害（对非当前目标模拟为追加单体伤害的 20%）
                if r["extra"] == "aoe":
                    aoe_dmg = int(st["matk"] * 1.2 * reaction_mult)
                    self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - aoe_dmg)
                    reaction_log = f"💥超载爆发！额外 {aoe_dmg} 点全体伤害！"
                # 冻结：目标冻结 1 回合
                elif r["extra"] == "freeze":
                    self.e_buffs["freeze"] = 1
                    reaction_log = "❄️冻结！目标被冰封 1 回合！"
                # 感电：连击 +1（追加一次伤害）
                elif r["extra"] == "chain":
                    multi += 1
                    reaction_log = "⚡感电连锁！追加一次攻击！"
                # 清除印记（感电保留）
                if r["clear"]:
                    for mk in E.ELEMENT_MARKS.values():
                        self.e_buffs.pop(mk, None)
        total = 0
        pmult = E.skill_power_mult(lv, info) * frozen_bonus * stack_bonus * cond_mult * magic_bonus * passive_bonus * reaction_mult
        for _ in range(multi):
            if kind == "物理":
                if info.get("pierce"):
                    dmg_i = E.calc_damage(int(st["atk"] * info["power"] * pmult), 0, is_crit, pierce=True)
                else:
                    dmg_i = E.calc_damage(int(st["atk"] * info["power"] * pmult), est["def"], is_crit)
            else:
                dmg_i = E.calc_damage(int(st["matk"] * info["power"] * pmult), est["mdef"], is_crit)
            # v34 残忍：暴击伤害 +x%（按等级）
            brutal_lvl = self._enchant_lvl(effs, "brutal")
            if brutal_lvl and is_crit:
                dmg_i = int(dmg_i * (1 + C.rune_value("brutal", brutal_lvl)))
            dmg_i = self._apply_mark(dmg_i)
            total += dmg_i
        self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - total)
        if multi > 1:
            logs.append(f"你施展【{skill_name}】，连击 {multi} 次，共造成 {total} 点伤害！")
        else:
            logs.append(f"你施展【{skill_name}】，造成 {total} 点伤害！")
        # 特效合并成紧凑标签（避免一行堆满长后缀）
        tags = []
        if is_crit:
            tags.append("💥暴击")
        if mech == "shadow" and self.enemy.get("hp", 0) >= self.enemy.get("max_hp", 1):
            tags.append("满血影袭必暴")
        if frozen_bonus > 1.0:
            tags.append("❄️碎冰增伤")
        if stack_bonus > 1.0:
            tags.append(f"⚡增幅x{round(stack_bonus, 2)}")
        if cond_mult > 1.0 and cond_label:
            tags.append(f"⚔️{cond_label}x{round(cond_mult, 1)}")
        if mb_lvl:
            tags.append(f"🔮破魔x{round(magic_bonus, 2)}")
        if tags:
            logs[-1] += " " + "·".join(tags)
        if reaction_log:
            logs.append(reaction_log)
        # v2.0 元素印记：施放带 element 的技能后给目标挂印记 + 法师切换当前系
        if element and E.ELEMENT_MARKS.get(element):
            E.element_mark_apply(self.e_buffs, element, 1)
            if self.resources.get("element") is not None:
                self.resources["element"] = element
        # v34 符文攻击特效（灼烧/冻结/吸血/连锁/虚弱）
        self._apply_enchant_attack(effs, total, st, player, logs)

        # ---- 分支机制结算（v29） ----
        self._last_player = player
        self._apply_mech_effect(mech, mval, p_mech, total, logs, skill_name, is_crit)
        # v63 额外控制效果（cc 字段，独立于 mech 叠层）：眩晕/沉默/净化
        cc = info.get("cc")
        if cc and cc in ("stun", "silence", "cleanse"):
            self._apply_mech_effect(cc, 1, p_mech, total, logs, skill_name, is_crit)

        # ---- 技能特效（v9 落地）----
        if skill_name == "处决":
            bonus = int(total * (1 - self.enemy.get("hp", 0) / max(1, self.enemy.get("max_hp", 1))))
            self.enemy["hp"] = max(0, self.enemy["hp"] - bonus)
            logs[-1] = f"你施展【{skill_name}】，造成 {total + bonus} 点伤害（残血加成 {bonus}）！"
        if skill_name == "破甲斩":
            self.e_buffs["def_down"] = E.skill_buff_turns(lv)
            logs[-1] += " 敌防下降！"
        if skill_name == "寒冰箭":
            self.e_buffs["spd_down"] = E.skill_buff_turns(lv)
            logs[-1] += " 敌速下降！"
        if skill_name == "毒箭":
            self.e_buffs["poison"] = E.skill_buff_turns(lv)
            logs[-1] += " 敌人中毒了！"
        if skill_name in ("标记猎杀", "猎杀标记"):
            self.e_buffs["mark"] = E.skill_buff_turns(lv)
            logs[-1] += " 目标被标记！"
        if info.get("effect") == "lifesteal":
            heal = int(total * E.skill_lifesteal_pct(info, lv))
            player["hp"] = min(player.get("max_hp", player["hp"]), player.get("hp", 0) + heal)
            logs.append(f"💉 『{skill_name}』汲取了 {heal} 点生命！")
        # ---- v10 套装攻击特效 ----
        if total > 0:
            self._set_attack_proc(player, total, logs)
        return logs

    # ---------------- v29 分支机制 ----------------
    def _mech_stack_bonus(self, mech: str, p_mech: dict, info: dict) -> float:
        """层数型机制对本次伤害的倍率"""
        if mech in ("rage", "shadow", "chi"):
            n = p_mech.get(mech, 0)
            if n:
                return 1.0 + n * 0.12
        return 1.0

    def _cond_mult(self, info: dict, player: dict, lv: int = 1) -> float:
        """条件转化（v30）：按战场状态返回伤害倍率。
        cond 结构：{"type": "...", "hp_pct": 0.4, "mult": 1.6, "label": "处决狙击"}
        倍率随技能等级成长（v56）：每级 +0.05，lv 默认 1 保持向后兼容。
        type:
          enemy_hp_low  敌方血量低于 hp_pct
          player_hp_low 自身血量低于 hp_pct
          enemy_hp_high 敌方血量高于 hp_pct
          player_hp_high 自身血量高于 hp_pct
          enemy_full_hp 敌方满血
          enemy_frozen  敌方被冻结
          enemy_poison_stacks 敌方中毒层数 ≥ stacks
          player_shield 自身有护盾
          player_spd_up 自身有加速增益
          player_chi_stacks 自身气力 ≥ stacks
        """
        cond = info.get("cond")
        if not cond:
            return 1.0
        ctype = cond.get("type")
        mult = E.skill_cond_mult(cond, lv, info)
        if ctype == "enemy_hp_low":
            if self.enemy.get("hp", 0) < self.enemy.get("max_hp", 1) * cond.get("hp_pct", 0.4):
                return mult
        elif ctype == "player_hp_low":
            if player.get("hp", 0) < player.get("max_hp", 1) * cond.get("hp_pct", 0.3):
                return mult
        elif ctype == "enemy_hp_high":
            if self.enemy.get("hp", 0) > self.enemy.get("max_hp", 1) * cond.get("hp_pct", 0.7):
                return mult
        elif ctype == "player_hp_high":
            if player.get("hp", 0) > player.get("max_hp", 1) * cond.get("hp_pct", 0.8):
                return mult
        elif ctype == "enemy_full_hp":
            if self.enemy.get("hp", 0) >= self.enemy.get("max_hp", 1):
                return mult
        elif ctype == "enemy_frozen":
            if "freeze" in self.e_buffs:
                return mult
        elif ctype == "enemy_stunned":
            # v63 联动：目标被眩晕时增伤（晕杀）
            if "stun" in self.e_buffs:
                return mult
        elif ctype == "enemy_silenced":
            # v63 联动：目标被沉默时增伤（静默处决）
            if "silence" in self.e_buffs:
                return mult
        elif ctype == "enemy_poison_stacks":
            p_mech = self.mech_stacks
            if p_mech.get("poison", 0) >= cond.get("stacks", 3):
                return mult
        elif ctype == "enemy_marked":
            p_mech = self.mech_stacks
            if "mark" in self.e_buffs or p_mech.get("mark", 0) > 0:
                return mult
        elif ctype == "player_shield":
            if self.shield > 0:
                return mult
        elif ctype == "player_spd_up":
            if "spd_up" in self.p_buffs:
                return mult
        elif ctype == "player_chi_stacks":
            p_mech = self.mech_stacks
            if p_mech.get("chi", 0) >= cond.get("stacks", 3):
                return mult
        return 1.0

    def _apply_mech_gain(self, mech: str, mval: int, p_mech: dict, logs: list, skill_name: str):
        """增益类技能叠层（v59：封顶）"""
        if mech and mval and mech in ("rage", "shield", "wind", "shadow", "chi", "bless", "judge", "iron", "mark", "burn", "poison", "freeze"):
            p_mech[mech] = E.mech_stack_gain(mech, p_mech, mval)

    def _apply_mech_effect(self, mech: str, mval: int, p_mech: dict, total: int, logs: list, skill_name: str, is_crit: bool = False):
        """攻击技能施放后的机制结算"""
        # 狂暴：叠层
        if mech == "rage" and mval:
            p_mech["rage"] = E.mech_stack_gain("rage", p_mech, mval)
            logs.append(f"🔥 狂暴层数 {p_mech['rage']}（每层 +12% 伤害）")
        # 圣盾：叠层
        elif mech == "shield" and mval:
            p_mech["shield"] = E.mech_stack_gain("shield", p_mech, mval)
            logs.append(f"🛡️ 圣盾层数 {p_mech['shield']}（每层减伤）")
        # 圣盾爆发：消耗层数转伤害
        elif mech == "shield_burst":
            n = p_mech.get("shield", 0)
            bonus = int(total * n * 0.12)
            self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - bonus)
            logs.append(f"🛡️ 圣盾爆发！{n} 层额外 {bonus} 伤害")
            p_mech["shield"] = 0
        # 狂暴爆发：消耗层数加攻击 buff
        elif mech == "rage_burst":
            n = p_mech.get("rage", 0)
            if n:
                self.p_buffs["atk_up_strong"] = E.skill_buff_turns(1)
                logs.append(f"🔥 狂战之魂！{n} 层狂暴 → 攻击大幅提升")
            p_mech["rage"] = 0
        # 灼烧：叠层（每层每回合掉 3% 生命）
        elif mech == "burn" and mval:
            p_mech["burn"] = E.mech_stack_gain("burn", p_mech, mval)
            logs.append(f"🔥 灼烧层数 {p_mech['burn']}（每回合 {p_mech['burn'] * 3}% 生命）")
        # 灼烧引爆：每层立即 30% 魔攻
        elif mech == "burn_burst":
            n = p_mech.get("burn", 0)
            st2 = self._player_stats(self._last_player) if hasattr(self, "_last_player") else None
            if st2 and n:
                d = int(st2["matk"] * 0.30 * n)
                self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - d)
                logs.append(f"🔥 灼烧引爆！{n} 层造成 {d} 点伤害")
            p_mech["burn"] = 0
            self.e_buffs.pop("burn", None)
        # 冻结：概率冻结 1 回合
        elif mech == "freeze" and mval:
            chance = min(0.75, 0.25 + mval * 0.15)
            if random.random() < chance:
                self.e_buffs["freeze"] = 1
                logs.append("❄️ 敌人被冻结，跳过下回合！")
        # v63 眩晕：概率眩晕 1 回合（物理系控制）
        elif mech == "stun" and mval:
            chance = min(0.60, 0.20 + mval * 0.15)
            if random.random() < chance:
                self.e_buffs["stun"] = 1
                logs.append("🌀 敌人被眩晕，跳过下回合！")
        # v63 沉默：稳定沉默 2 回合（禁技能）
        elif mech == "silence" and mval:
            self.e_buffs["silence"] = 2
            logs.append("🤐 敌人被沉默，2 回合内无法使用技能！")
        # v63 净化：清除敌方增益（mon_atk_up/mon_def_up/狂暴/召唤）
        elif mech == "cleanse" and mval:
            removed = []
            for k in ("mon_atk_up", "mon_atk_up_strong", "mon_def_up", "summon", "enraged"):
                if k in self.e_buffs or (k == "enraged" and self.enemy.get("enraged")):
                    self.e_buffs.pop(k, None)
                    self.enemy["enraged"] = False
                    removed.append(k)
            if removed:
                logs.append("✨ 圣光净化！敌人的增益被驱散！")
            else:
                logs.append("✨ 圣光净化，敌人没有增益可驱散。")
        # 标记：叠层（层数供 mark_burst 消费，同时挂 e_buffs 供 _apply_mark 增伤）
        elif mech == "mark" and mval:
            p_mech["mark"] = E.mech_stack_gain("mark", p_mech, mval)
            self.e_buffs["mark"] = DEBUFF_TURNS
            logs.append(f"🎯 目标被标记！标记层数 {p_mech['mark']}")
        # 标记爆发：每层 +20%
        elif mech == "mark_burst":
            n = p_mech.get("mark", 0)
            bonus = int(total * n * 0.20)
            self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - bonus)
            logs.append(f"🎯 猎杀标记！{n} 层额外 {bonus} 伤害")
            p_mech["mark"] = 0
        # 风印：叠层（连击次数 +1/层，已在伤害循环处理）
        elif mech == "wind" and mval:
            p_mech["wind"] = E.mech_stack_gain("wind", p_mech, mval)
            logs.append(f"💨 风印层数 {p_mech['wind']}（连击次数 +{p_mech['wind']}）")
        # 风印爆发：层数转连击
        elif mech == "wind_burst":
            n = p_mech.get("wind", 0)
            logs.append(f"💨 风印爆发！{n} 层转化为连击")
            p_mech["wind"] = 0
        # 审判：叠层（暴击时）
        elif mech == "judge" and mval:
            if is_crit:
                p_mech["judge"] = E.mech_stack_gain("judge", p_mech, mval)
                logs.append(f"⚖️ 审判层数 {p_mech['judge']}（每层 +15%）")
        # 审判爆发
        elif mech == "judge_burst":
            n = p_mech.get("judge", 0)
            bonus = int(total * n * 0.15)
            self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - bonus)
            logs.append(f"⚖️ 审判裁决！{n} 层额外 {bonus} 伤害")
            p_mech["judge"] = 0
        # 影袭：叠层
        elif mech == "shadow" and mval:
            p_mech["shadow"] = E.mech_stack_gain("shadow", p_mech, mval)
            logs.append(f"🌑 影袭层数 {p_mech['shadow']}（每层 +12%）")
        # 影袭爆发
        elif mech == "shadow_burst":
            n = p_mech.get("shadow", 0)
            bonus = int(total * n * 0.18)
            self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - bonus)
            logs.append(f"🌑 致命突袭！{n} 层额外 {bonus} 伤害")
            p_mech["shadow"] = 0
        # 毒层：叠层（每层每回合 3% 生命）
        elif mech == "poison" and mval:
            p_mech["poison"] = E.mech_stack_gain("poison", p_mech, mval)
            logs.append(f"☠️ 毒层 {p_mech['poison']}（每回合 {p_mech['poison'] * 3}% 生命）")
        # 毒爆：每层立即 15% 攻击
        elif mech == "poison_burst":
            n = p_mech.get("poison", 0)
            bonus = int(total * n * 0.15)
            self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - bonus)
            logs.append(f"☠️ 毒爆！{n} 层额外 {bonus} 伤害")
            p_mech["poison"] = 0
        # 气力：攒层
        elif mech == "chi" and mval:
            p_mech["chi"] = E.mech_stack_gain("chi", p_mech, mval)
            logs.append(f"🌀 气力 {p_mech['chi']}（每点 +12%）")
        # 气力爆发
        elif mech == "chi_burst":
            n = p_mech.get("chi", 0)
            bonus = int(total * n * 0.15)
            self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - bonus)
            logs.append(f"🌀 拳法奥义！{n} 点气力额外 {bonus} 伤害")
            p_mech["chi"] = 0
        # 金身：叠层（减伤，在 _damage_player 生效）
        elif mech == "iron" and mval:
            p_mech["iron"] = E.mech_stack_gain("iron", p_mech, mval)
            logs.append(f"🪷 金身层数 {p_mech['iron']}（每层减伤 4%）")
        # 金身爆发：层数转伤害
        elif mech == "iron_burst":
            n = p_mech.get("iron", 0)
            bonus = int(total * n * 0.12)
            self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - bonus)
            logs.append(f"🪷 不坏金身！{n} 层额外 {bonus} 伤害")
            p_mech["iron"] = 0
        # 神恩护盾：层数转护盾
        elif mech == "bless_shield":
            n = p_mech.get("bless", 0)
            st2 = self._player_stats(self._last_player) if hasattr(self, "_last_player") else None
            player = self._last_player
            if st2 and n and player is not None:
                shield = int(st2["matk"] * 0.08 * n)
                self.shield = self.shield + shield
                logs.append(f"✨ 神恩护盾！{n} 层转化为 {shield} 点护盾")
            p_mech["bless"] = 0

    # ---------------- v10 套装攻击特效 ----------------
    def _set_attack_proc(self, player: dict, dmg: int, logs: list):
        """玩家攻击后触发已激活套装的 4 件攻击特效"""
        effs = E.set_bonus_4(player.get("equipment", {}))
        if not effs:
            return
        pst = self._player_stats(player)
        for eff in effs:
            if eff == "frost" and random.random() < 0.30:
                self.e_buffs["spd_down"] = DEBUFF_TURNS
                logs.append("❄️ 寒霜之力！敌人速度下降！")
            elif eff == "burn" and random.random() < 0.30:
                self.e_buffs["poison"] = DEBUFF_TURNS
                logs.append("🔥 烈焰之力！敌人被灼烧！")
            elif eff == "thunder" and random.random() < 0.25:
                est = self._enemy_stats()
                tdmg = E.calc_damage(int(pst["atk"] * 0.6), est["def"])
                self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - tdmg)
                logs.append(f"⚡ 雷霆一击！追加 {tdmg} 点伤害！")
            elif eff == "pierce" and random.random() < 0.30:
                self.e_buffs["def_down"] = DEBUFF_TURNS
                logs.append("👑 诸神之力！敌人护甲破碎！")
            elif eff == "lifesteal_set" and random.random() < 0.30:
                heal = int(dmg * 0.15)
                player["hp"] = min(player.get("max_hp", player["hp"]), player.get("hp", 0) + heal)
                logs.append(f"🌑 深渊之力！汲取 {heal} 点生命！")
            elif eff == "execute":
                ratio = self.enemy.get("hp", 0) / max(1, self.enemy.get("max_hp", 1))
                if ratio < 0.30:
                    bonus = int(dmg * 0.25)
                    self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - bonus)
                    logs.append(f"💀 灭世之力！处决追加 {bonus} 点伤害！")

    # ---------------- 敌方回合 ----------------
    def _boss_mech(self, logs: list):
        """v58 Boss 专属机制：enrage 低血狂暴 / summon 定期召唤 / heal 定期自愈
        状态存 enemy dict（随战斗序列化持久化）"""
        mech = self.enemy.get("mech")
        if not mech or self.btype == "pvp":
            return
        r = self.round
        if mech == "enrage":
            ratio = self.enemy.get("hp", 1) / max(1, self.enemy.get("max_hp", 1))
            if ratio < 0.30 and not self.enemy.get("enraged"):
                self.enemy["enraged"] = True
                logs.append(f"😡【{self.enemy['name']}】陷入狂暴！攻击大幅提升！")
        elif mech == "summon":
            if r > 1 and r % 3 == 0 and self.enemy.get("summoned_round") != r:
                self.enemy["summoned_round"] = r
                self.e_buffs["mon_atk_up"] = max(self.e_buffs.get("mon_atk_up", 0), 2)
                logs.append(f"👥【{self.enemy['name']}】召唤了援军！攻击提升！")
        elif mech == "heal":
            if r > 1 and r % 4 == 0 and self.enemy.get("healed_round") != r:
                self.enemy["healed_round"] = r
                heal = int(self.enemy.get("max_hp", 1) * 0.08)
                self.enemy["hp"] = min(self.enemy.get("max_hp", 1), self.enemy.get("hp", 0) + heal)
                logs.append(f"💚【{self.enemy['name']}】汲取力量，恢复了 {heal} 点生命！")

    def _enemy_turn(self, player: dict) -> tuple:
        """敌方行动。返回 (日志列表, 对玩家伤害)"""
        if self.btype == "pvp":
            return self._pvp_enemy_turn(player)
        logs = []
        self._boss_mech(logs)
        est = self._enemy_stats()
        pst = self._player_stats(player)
        dmg = 0
        # v29 冻结：跳过敌方回合
        if "freeze" in self.e_buffs:
            logs.append("❄️ 敌人被冻结，无法行动！")
            self.e_buffs.pop("freeze", None)
            return logs, 0
        # v63 眩晕：跳过敌方回合（物理系控制，与冻结同机制不同来源）
        if "stun" in self.e_buffs:
            logs.append("🌀 敌人被眩晕，无法行动！")
            self.e_buffs.pop("stun", None)
            return logs, 0
        # 30% 概率使用技能（v63：沉默时只能普攻）
        skill = None
        silenced = "silence" in self.e_buffs
        if self.enemy.get("skills") and random.random() < 0.3 and not silenced:
            skill = random.choice(self.enemy["skills"])
            sinfo = C.MONSTER_SKILLS.get(skill)
            if sinfo:
                sname = sinfo.get("name", skill)  # 显示中文名（技能池可能存 ID）
                kind = sinfo.get("kind")
                if kind == "增益":
                    eff = sinfo.get("effect")
                    if eff == "atk_up":
                        self.e_buffs["mon_atk_up"] = BUFF_TURNS
                        logs.append(f"【{self.enemy['name']}】使用了【{sname}】，攻击力提升了！")
                    elif eff == "atk_up_strong":
                        self.e_buffs["mon_atk_up_strong"] = BUFF_TURNS
                        logs.append(f"【{self.enemy['name']}】使用了【{sname}】，攻击力大幅提升了！")
                    elif eff == "def_up":
                        self.e_buffs["mon_def_up"] = BUFF_TURNS
                        logs.append(f"【{self.enemy['name']}】使用了【{sname}】，防御提升了！")
                    elif eff == "heal_self":
                        heal = int(self.enemy.get("max_hp", 1) * 0.15)
                        self.enemy["hp"] = min(self.enemy.get("max_hp", 1), self.enemy.get("hp", 0) + heal)
                        logs.append(f"【{self.enemy['name']}】使用了【{sname}】，恢复了 {heal} 点生命！")
                    elif eff == "summon":
                        self.e_buffs["summon"] = BUFF_TURNS
                        logs.append(f"【{self.enemy['name']}】使用了【{sname}】，召唤了援军！")
                    return logs, 0
                power = sinfo.get("power", 1.0)
                is_crit = random.random() < 0.1
                if kind == "物理":
                    dmg = E.calc_damage(int(est["atk"] * power), pst["def"], is_crit)
                else:
                    dmg = E.calc_damage(int(est["matk"] * power), pst["mdef"], is_crit)
                logs.append(f"【{self.enemy['name']}】使用了【{sname}】，对你造成 {dmg} 点伤害！" + (" 💥暴击！" if is_crit else ""))
                # v63 怪物技能机制：眩晕/沉默/冻结 等控制
                mmech = sinfo.get("mech")
                if mmech and mmech in ("stun", "silence", "freeze"):
                    mval = int(sinfo.get("mech_val", 1) or 1)
                    if mmech == "freeze":
                        chance = min(0.75, 0.25 + mval * 0.15)
                        if random.random() < chance:
                            self.p_buffs["freeze"] = 1
                            logs.append("❄️ 你被冻结，下回合无法行动！")
                    elif mmech == "stun":
                        chance = min(0.60, 0.20 + mval * 0.15)
                        if random.random() < chance:
                            self.p_buffs["stun"] = 1
                            logs.append("🌀 你被眩晕，下回合无法行动！")
                    elif mmech == "silence":
                        self.p_buffs["silence"] = 2
                        logs.append("🤐 你被沉默，2 回合内无法使用技能！")
                return logs, dmg
        dmg = E.calc_damage(est["atk"], pst["def"])
        logs.append(f"【{self.enemy['name']}】攻击你，造成 {dmg} 点伤害！")
        return logs, dmg

    def _pvp_enemy_turn(self, player: dict) -> tuple:
        """PVP：敌方玩家行动（v9.2 启用；先实现 AI 普攻）"""
        est = self._enemy_stats()
        pst = self._player_stats(player)
        logs = []
        is_crit = random.random() < est.get("crit", 0.05)
        dmg = E.calc_damage(est["atk"], pst["def"], is_crit)
        logs.append(f"【{self.enemy['name']}】向你发起攻击，造成 {dmg} 点伤害！" + (" 💥暴击！" if is_crit else ""))
        return logs, dmg

    # ---------------- 状态修正 ----------------
    def _apply_buffs(self, st: dict, buffs: dict) -> dict:
        st = dict(st)
        for eff, turns in buffs.items():
            if eff in BUFF_MULT:
                attr, val = BUFF_MULT[eff]
                if attr == "crit":
                    st["crit"] = min(1.0, st.get("crit", 0) + val)
                else:
                    st[attr] = int(st.get(attr, 0) * val)
        return st

    def _enemy_stats(self) -> dict:
        """敌方当前属性（应用敌方增益/减益）"""
        e = self.enemy
        est = {
            "atk": e.get("atk", 0), "def": e.get("def", 0),
            "matk": e.get("matk", 0), "mdef": e.get("mdef", 0),
            "spd": e.get("spd", 0), "crit": e.get("crit", 0.05),
        }
        est = self._apply_buffs(est, self.e_buffs)
        # v58 Boss 狂暴：血量 <30% 触发后攻击 +35%
        if e.get("enraged"):
            est["atk"] = int(est["atk"] * 1.35)
            est["matk"] = int(est["matk"] * 1.35)
        if "def_down" in self.e_buffs:
            est["def"] = int(est["def"] * DEF_DOWN_MULT)
        if "spd_down" in self.e_buffs:
            est["spd"] = int(est["spd"] * SPD_DOWN_MULT)
        # v34 符文虚弱：敌人攻击 -x%
        if "mon_atk_down" in self.e_buffs:
            wv = float(self.e_buffs.get("_weaken_val", 0.15) or 0.15)
            est["atk"] = int(est["atk"] * (1 - wv))
            est["matk"] = int(est["matk"] * (1 - wv))
        return est

    def _apply_mark(self, dmg: int) -> int:
        if "mark" in self.e_buffs:
            return int(dmg * (1 + MARK_EXTRA))
        return dmg

    def _turn_start(self, player: dict) -> list:
        """回合开始：持续伤害结算 + v10 套装每回合回复"""
        logs = []
        # v29 灼烧：每层 3% 生命（层数存战斗 mech_stacks）
        mech = self.mech_stacks
        burn_n = int(mech.get("burn", 0) or 0)
        if burn_n > 0:
            p = int(self.enemy.get("max_hp", 1) * 0.03 * burn_n)
            self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - p)
            logs.append(f"🔥 【{self.enemy['name']}】被灼烧，损失 {p} 点生命！")
            if self._enemy_dead():
                self.result = "victory"
                logs.append(f"🎉 你击败了【{self.enemy['name']}】！（灼烧致死）")
        # v29 毒层：每层 3% 生命（优先战斗层数；老毒箭仍用 e_buffs 布尔标记）
        mech = self.mech_stacks
        poison_n = int(mech.get("poison", 0) or 0)
        if poison_n > 0:
            p = int(self.enemy.get("max_hp", 1) * POISON_PCT * poison_n)
            self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - p)
            logs.append(f"☠️ 【{self.enemy['name']}】中毒发作，损失 {p} 点生命！")
            if self._enemy_dead():
                self.result = "victory"
                logs.append(f"🎉 你击败了【{self.enemy['name']}】！（毒发身亡）")
        elif "poison" in self.e_buffs:
            p = int(self.enemy.get("max_hp", 1) * POISON_PCT)
            self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - p)
            logs.append(f"☠️ 【{self.enemy['name']}】中毒发作，损失 {p} 点生命！")
            if self._enemy_dead():
                self.result = "victory"
                logs.append(f"🎉 你击败了【{self.enemy['name']}】！（毒发身亡）")
        # 圣光/永恒套：每回合开始回复生命
        for eff in E.set_bonus_4(player.get("equipment", {})):
            if eff in ("regen", "regen_strong") and player.get("hp", 0) < player.get("max_hp", 1):
                pct = 0.05 if eff == "regen" else 0.08
                heal = int(player.get("max_hp", player.get("hp", 1)) * pct)
                player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
                logs.append(f"✨ 套装祝福生效，你回复了 {heal} 点生命！")
                break
        # v34 符文·治愈：每回合回复 x% 生命
        regen_lvl = self._enchant_lvl(self._enchant_effects(player), "regen")
        if regen_lvl and player.get("hp", 0) < player.get("max_hp", 1):
            heal = int(player.get("max_hp", player.get("hp", 1)) * C.rune_value("regen", regen_lvl))
            player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
            logs.append(f"✨ 符文治愈生效，你回复了 {heal} 点生命！")
        # v64 被动·气息调和：每回合回复 2% 生命
        if "气息调和" in E.passive_skills_learned(player["class_name"], player.get("learned_skills", [])) \
                and player.get("hp", 0) < player.get("max_hp", 1):
            heal = int(player.get("max_hp", player.get("hp", 1)) * 0.02)
            player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
            logs.append(f"🍃 气息调和生效，你回复了 {heal} 点生命！")
        # v2.0 核心资源：回合回复（游侠精力 +25/回合）
        cls = player.get("class_name", "")
        rd = E.core_resource_def(cls)
        if rd and rd.get("regen", 0) > 0:
            k = rd["key"]
            old = self.resources.get(k, 0)
            self.resources[k] = E.core_resource_regen(cls, self.resources)
            new = self.resources[k]
            if new > old:
                logs.append(f"🍃 {rd['name']}回复 {new - old} 点（{new}/{rd['max']}）")
        return logs

    def _end_round(self):
        """回合结束：buff 剩余回合递减 + v2.0 技能冷却递减"""
        for tbl in (self.p_buffs, self.e_buffs):
            for k in list(tbl):
                tbl[k] -= 1
                if tbl[k] <= 0:
                    del tbl[k]
        self._tick_cooldowns()

    def _damage_player(self, player: dict, dmg: int, logs: list):
        if dmg <= 0:
            return
        # v64 被动·铁壁之心/磐石体：受到伤害时减伤 5%
        pv = E.passive_skills_learned(player.get("class_name", ""), player.get("learned_skills", []))
        if "铁壁之心" in pv or "磐石体" in pv:
            reduce = int(dmg * 0.05)
            dmg = max(1, dmg - reduce)
            logs.append(f"🛡️ 被动减伤 {reduce} 点（铁壁之心/磐石体）")
        # v51 盾牌反击：被攻击时 60% 概率反击 120% 伤害
        if self.p_buffs.get("counter", 0) > 0 and self.enemy.get("hp", 0) > 0:
            if random.random() < 0.6:
                pst2 = self._player_stats(player)
                est2 = self._enemy_stats()
                cd = E.calc_damage(int(pst2["atk"] * 1.2), est2.get("def", 0))
                self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - cd)
                logs.append(f"🛡️ 盾牌反击！对【{self.enemy.get('name', '敌人')}】造成 {cd} 点伤害！")
        # 龙鳞套：被攻击时 25% 概率反弹 25% 伤害
        if "reflect" in E.set_bonus_4(player.get("equipment", {})) and self.enemy.get("hp", 0) > 0:
            if random.random() < 0.25:
                rd = int(dmg * 0.25)
                self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - rd)
                logs.append(f"🐉 龙鳞反震！反弹 {rd} 点伤害！")
        # v29 金身：每层减伤 4%
        mech = self.mech_stacks
        iron = int(mech.get("iron", 0) or 0)
        if iron > 0:
            reduce = int(dmg * 0.04 * iron)
            dmg = max(1, dmg - reduce)
            logs.append(f"🪷 金身减伤 {reduce} 点（{iron} 层）")
        # v34 符文·壁垒：受击时 x% 概率获得护盾（y% 生命值）；荆棘：受击反弹 x% 伤害
        effs = self._enchant_effects(player)
        barrier_lvl = self._enchant_lvl(effs, "barrier")
        if barrier_lvl:
            prob, pct = C.rune_value("barrier", barrier_lvl)
            if random.random() < prob:
                shield_gain = int(player.get("max_hp", player.get("hp", 1)) * pct)
                self.shield = self.shield + shield_gain
                logs.append(f"🛡️ 符文壁垒：获得 {shield_gain} 点护盾！")
        thorns_lvl = self._enchant_lvl(effs, "thorns")
        if thorns_lvl and self.enemy.get("hp", 0) > 0:
            rd = int(dmg * C.rune_value("thorns", thorns_lvl))
            self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - rd)
            logs.append(f"🌵 符文荆棘：反弹 {rd} 点伤害！")
        # v29 神恩护盾：优先吸收（v59：护盾存战斗状态）
        shield = self.shield
        if shield > 0:
            absorb = min(shield, dmg)
            dmg -= absorb
            self.shield = shield - absorb
            logs.append(f"✨ 护盾吸收 {absorb} 点伤害（剩余 {self.shield}）")
            if dmg <= 0:
                return
        player["hp"] = max(0, player.get("hp", 0) - dmg)
        # v2.0 核心资源：受击获取（战士怒气/牧师信仰/拳师气）
        cls = player.get("class_name", "")
        rd = E.core_resource_def(cls)
        if rd and rd.get("on_hit"):
            k = rd["key"]
            self.resources[k] = E.core_resource_gain(cls, self.resources, rd["on_hit"])
        # v64 被动·神圣坚韧：受击后 20% 概率回复 5% 生命
        if player["hp"] > 0 and "神圣坚韧" in pv:
            if random.random() < 0.20:
                heal = int(player.get("max_hp", player.get("hp", 1)) * 0.05)
                player["hp"] = min(player.get("max_hp", player["hp"]), player["hp"] + heal)
                logs.append(f"✨ 神圣坚韧：回复 {heal} 点生命！")

    def _enemy_dead(self) -> bool:
        return self.enemy.get("hp", 1) <= 0

    def _player_dead(self, player: dict) -> bool:
        return player.get("hp", 1) <= 0
