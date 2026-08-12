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

# v95.4 普攻文案按职业区分（玩家反馈：全职业"你挥剑攻击"违和）
_ATK_VERB = {
    "cls_zhan_shi": "挥剑斩击",
    "cls_fa_shi": "凝聚魔力轰出法球",
    "cls_you_xia": "弯弓搭箭",
    "cls_mu_shi": "圣光冲击",
    "cls_ci_ke": "匕首突刺",
    "cls_wu_seng": "挥拳轰击",
    "cls_bard": "拨弦激荡音波",
    "cls_spellblade": "魔能斩击",
}


def _basic_attack_verb(player: dict) -> str:
    """普攻动作文案（按职业；未知职业 fallback 挥剑攻击）"""
    return _ATK_VERB.get(player.get("class_name", ""), "挥剑攻击")


# 增益倍率映射：effect -> (修正属性, 倍率/加成)
BUFF_MULT = {
    "atk_up":         ("atk", 1.30),
    "atk_up_strong":  ("atk", 1.75),
    "echo_bless":     ("atk", 1.05),   # v97.4 回音洞穴祝福：本场攻击 +5%（一次性，探索事件写入）
    "matk_up":        ("matk", 1.50),   # #244a：与技能描述 matk＋50% 对齐（原 1.35 与 desc 不符）
    "matk_up_strong": ("matk", 1.80),
    "matk_up_pot":    ("matk", 1.30),   # 9.3 鲛人之泪：本回合魔攻 +30%
    "def_up":         ("def", 1.45),
    "spd_up":         ("spd", 1.40),
    "crit_up":        ("crit", 0.20),      # 暴击率 +20%
    # v101.28b 食物增益（战斗料理线：数值约为药水 1/3，价格低+带战斗外恢复）
    "food_atk_up":    ("atk", 1.10),
    "food_def_up":    ("def", 1.15),
    "food_spd_up":    ("spd", 1.12),
    "food_crit_up":   ("crit", 0.08),
    "food_matk_up":   ("matk", 1.10),
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
    def __init__(self, btype: str = "monster", enemy: dict | None = None, title_bonus: dict = None, player: dict | None = None, pet: dict | None = None, dmg_mult: float = 1.0):
        self.btype = btype                 # monster | worldboss | pvp
        self.dmg_mult = dmg_mult           # v93 GM 世界 Boss 伤害倍率（gm_伤害 设置，仅 worldboss 生效）
        self.pet = pet or {}               # 24 章宠物：{pet_key,name,level,satiety}（战斗内宠物技能用）
        self.round = 0
        self.enemy = enemy or {}           # 敌方单位 dict（怪物 / Boss / 玩家快照）
        self.p_buffs: dict = {}            # 玩家增益 {effect: turns}
        self.p_hot: dict = {}              # v101.28 食物持续恢复 {"heal": 比例, "mana": 比例, "turns": 剩余回合}
        self.p_food_affixes: list = []     # v101.28c 食物词条（战斗中吃料理获得的临时词条 ID，本场有效）
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
        self.combo_seq: list = []          # v2.0 拳师连招序列（拳/踢/掌 tag 记录，满 3 触发三连）
        if player:
            # v95.19: 战斗内属性统一用实时计算值——DB max_hp/max_mp 是注册/升级快照，换装备后过时，
            # 会导致战斗内血量上限/治疗 clamp/护盾与『角色』面板不一致（装备 HP 加成战斗内不生效）
            try:
                _st = self._player_stats(player)
                player["max_hp"] = int(_st.get("max_hp", player.get("max_hp", 100)))
                player["max_mp"] = int(_st.get("max_mp", player.get("max_mp", C.DEFAULT_MAX_MP)))
            except Exception:
                pass
            # v97.4 回音洞穴祝福：探索事件写入 event_state bless_{qid}（玩家级，players 表全局无 group_id），本场攻击 +5%，一次性
            if player.get("qq_id") and not self.p_buffs.get("echo_bless"):
                try:
                    import json as _json
                    from . import db as _db
                    _key = f"bless_{player['qq_id']}"
                    _raw = _db.get_event_state(_key)
                    if _raw:
                        self.p_buffs["echo_bless"] = 1
                        _db.set_event_state(_key, "")
                except Exception:
                    pass
            self._init_resources(player)
        # 阶段八：战斗开始词条——护盾（获得 10% 生命护盾）
        if player and "shield" in self._equip_affix_ids(player):
            self.shield = int(player.get("max_hp", 100) * 0.10)
        # v61 进度条速度机制：每回合双方进度 + 各自速度，差距攒够慢方速度 → 快方额外行动
        self.p_progress: float = 0.0          # 玩家行动进度
        self.e_progress: float = 0.0          # 敌方行动进度
        self.p_extra_left: int = 0            # 玩家本回合剩余额外行动次数（自由选择出手）
        self.e_extra_left: int = 0            # 敌方本回合剩余额外行动次数
        self.e_first: bool = False            # 敌方是否先手（速度更快）
        self._player_hit: bool = False        # 本场玩家是否受过击（v2.1 条件：未受击增伤）
        self.first_attack_done: bool = False  # 阶段九：龙之吐息首击标记（每场首次攻击 +15%）

    # ---------------- 序列化 ----------------
    def to_state(self) -> dict:
        return {
            "type": self.btype,
            "round": self.round,
            "enemy": self.enemy,
            "pet": self.pet,
            "p_buffs": self.p_buffs,
            "p_hot": self.p_hot,
            "p_food_affixes": self.p_food_affixes,
            "e_buffs": self.e_buffs,
            "p_defending": self.p_defending,
            "e_defending": self.e_defending,
            "title_bonus": self.title_bonus,
            "mech_stacks": self.mech_stacks,
            "shield": self.shield,
            "resources": self.resources,
            "cooldown": self.cooldown,
            "combo_seq": self.combo_seq,
            "p_progress": self.p_progress,
            "e_progress": self.e_progress,
            "p_extra_left": self.p_extra_left,
            "e_extra_left": self.e_extra_left,
            "e_first": self.e_first,
            "player_hit": self._player_hit,
            "first_attack_done": self.first_attack_done,
        }

    @classmethod
    def from_state(cls, st: dict):
        b = cls(st.get("type", "monster"), st.get("enemy", {}), st.get("title_bonus") or {}, pet=st.get("pet") or {})
        b.round = st.get("round", 0)
        b.p_buffs = st.get("p_buffs", {}) or {}
        b.p_hot = st.get("p_hot", {}) or {}
        b.p_food_affixes = st.get("p_food_affixes", []) or []
        b.e_buffs = st.get("e_buffs", {}) or {}
        b.p_defending = st.get("p_defending", False)
        b.e_defending = st.get("e_defending", False)
        b.mech_stacks = st.get("mech_stacks", {}) or {}
        b.shield = int(st.get("shield", 0) or 0)
        b.resources = st.get("resources", {}) or {}
        b.cooldown = st.get("cooldown", {}) or {}
        b.combo_seq = st.get("combo_seq", []) or []
        b.team_effects = []
        # v61 进度条字段（老存档用 .get 兜底为 0）
        b.p_progress = float(st.get("p_progress", 0) or 0)
        b.e_progress = float(st.get("e_progress", 0) or 0)
        b.p_extra_left = int(st.get("p_extra_left", 0) or 0)
        b.e_extra_left = int(st.get("e_extra_left", 0) or 0)
        b.e_first = bool(st.get("e_first", False))
        b._player_hit = bool(st.get("player_hit", False))
        b.first_attack_done = bool(st.get("first_attack_done", False))
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
        """战斗状态栏显示核心资源(如 ⚡ 怒气 3/10)。"""
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
        """技能剩余冷却回合数(0 = 可用)。"""
        return int(self.cooldown.get(skill_name, 0) or 0)

    def _skill_on_cd(self, skill_name: str) -> bool:
        return self._skill_cd_left(skill_name) > 0

    def _set_skill_cd(self, skill_name: str, cd: int):
        """设置技能冷却(cd 回合，1 表示下一回合即可用)。"""
        if cd > 0:
            self.cooldown[skill_name] = cd

    def _tick_cooldowns(self):
        """回合结束：所有冷却－1，归零清除。"""
        for k in list(self.cooldown):
            self.cooldown[k] -= 1
            if self.cooldown[k] <= 0:
                del self.cooldown[k]

    # ---------------- 连招序列（v2.0，拳师） ----------------
    # 连招顺序：拳 → 踢 → 掌 →（三连触发）→ 重新开始
    COMBO_ORDER = ["拳", "踢", "掌"]

    def _combo_push(self, tag: str) -> bool:
        """记录连招 tag（拳/踢/掌）。返回是否触发三连。
        非连招 tag 不清空序列（只有非连招技能打断不重置）。"""
        if tag not in self.COMBO_ORDER:
            return False
        expect = self.COMBO_ORDER[len(self.combo_seq)]
        if tag == expect:
            self.combo_seq.append(tag)
        else:
            # 顺序不对：从该 tag 重新开始（如果 tag 是起手拳则开始新序列）
            self.combo_seq = [tag] if tag == self.COMBO_ORDER[0] else []
        if len(self.combo_seq) == len(self.COMBO_ORDER):
            self.combo_seq = []
            return True
        return False

    def _combo_label(self) -> str:
        """当前连招进度显示(如 拳→踢→_)。"""
        if not self.combo_seq:
            return ""
        parts = list(self.combo_seq)
        while len(parts) < len(self.COMBO_ORDER):
            parts.append("_")
        return "→".join(parts)

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
        # v95.19: 战斗内上限统一实时值——覆盖 from_state 恢复的战斗（恢复时不传 player，
        # __init__ 刷新不到；DB max_hp/max_mp 换装备后过时，会导致战斗内上限与面板不一致）
        try:
            _st = self._player_stats(player)
            player["max_hp"] = int(_st.get("max_hp", player.get("max_hp", 100)))
            player["max_mp"] = int(_st.get("max_mp", player.get("max_mp", C.DEFAULT_MAX_MP)))
        except Exception:
            pass
        # v63 额外行动阶段被控：眩晕/冻结跳过（消耗额外行动但不执行动作）
        if self.p_extra_left > 0 and ("stun" in self.p_buffs or "freeze" in self.p_buffs):
            logs.append("🌀 你被控制，无法出手！")
            self.p_extra_left = 0
            self.p_buffs.pop("stun", None)
            self.p_buffs.pop("freeze", None)
            # v101.28 被控制回合 hot 照常结算（被动效果，正好救命）
            if self.p_hot and self.p_hot.get("turns", 0) > 0:
                logs += self._apply_hot(player)
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
                logs.append(f"⚡ 速度优势！你还可以行动 {self.p_extra_left} 次(『攻击』『技能 <名称>』『使用 <道具>』)")
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
        # v101.28 食物持续恢复：正常回合开始结算 hot（每回合一次，含眩晕/冻结回合）
        if self.p_hot and self.p_hot.get("turns", 0) > 0:
            logs += self._apply_hot(player)
        # 24 章宠物技能：回合开始自动触发（宠物击杀直接胜利）
        if self.pet:
            logs = self._pet_skill_turn(player, logs)
            if self.result == "victory":
                self._end_round()
                return logs, True
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
            logs.append("🤐 你被沉默，无法使用技能！(只能普攻/防御/道具)")
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
                logs.append(f"⚡ 速度优势！你还可以行动 {self.p_extra_left} 次(『攻击』『技能 <名称>』『使用 <道具>』)")
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
            logs.append(f"⚡ 速度优势！你获得了 {self.p_extra_left} 次额外行动，可自由出手(『攻击』『技能 <名称>』『使用 <道具>』)")
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
                    logs.append(f"(格挡后 {dmg} 点伤害)")
                self._damage_player(player, dmg, logs)
                if self._player_dead(player):
                    self.result = "defeat"
        self._end_round()
        return logs, self.result is not None

    def _do_use_item(self, payload: str, player: dict) -> list:
        """战斗中使用消耗品：恢复/增益(v61 抽公共，普通回合与额外行动共用)"""
        logs = []
        if payload.startswith("affix:"):
            # v101.28c 食物词条：affix:词条ID,词条ID（本场战斗有效）
            aids = [a for a in payload[6:].split(",") if a]
            for a in aids:
                if a not in self.p_food_affixes:
                    self.p_food_affixes.append(a)
            # 护盾词条特判：词条效果是'战斗开始获得护盾'，战斗中吃立即给
            if "shield" in aids:
                gain = int(player.get("max_hp", 100) * 0.10)
                self.shield = max(self.shield, gain)
            names = [((C.AFFIXES.get(a) or C.LEGENDARY_EFFECTS.get(a) or {}).get("name") or a)
                     for a in aids]
            logs.append(f"🍲 你吃下了料理，获得【{'、'.join(names)}】效果！(本场战斗)")
            return logs
        if payload.startswith("hot:"):
            # v101.28 食物持续恢复：hot:回血比例,回蓝比例,回合数（模板 tpl_food 生成）
            _p = payload[4:].split(",")
            hpct = float(_p[0]) if _p and _p[0] else 0.0
            mpct = float(_p[1]) if len(_p) > 1 and _p[1] else 0.0
            turns = int(_p[2]) if len(_p) > 2 and _p[2] else 3
            self.p_hot = {"heal": hpct, "mana": mpct, "turns": turns}
            _desc = []
            if hpct > 0:
                _desc.append(f"每回合恢复 {int(hpct * 100)}% 生命")
            if mpct > 0:
                _desc.append(f"每回合恢复 {int(mpct * 100)}% 魔力")
            logs.append(f"🍲 你吃下了食物，{('、'.join(_desc))}！({turns} 回合)")
            return logs
        if payload.startswith("mana:"):
            # v101.27：魔力药水战斗内回显数字（tpl_mana payload="mana:N"）
            mv = int(payload[5:])
            before = player["mp"]
            player["mp"] = min(player.get("max_mp", player["mp"]), player["mp"] + mv)
            logs.append(f"💙 你使用了战斗道具，恢复 {player['mp'] - before} 点魔力！({player['mp']}/{player.get('max_mp', '?')})")
            return logs
        if payload.startswith("buff:"):
            # v54 战斗药水：effect → p_buffs 增益 3 回合
            # 9.3：支持逗号分隔复合 buff（如龙涎药剂 buff:atk_up,def_up）
            kind = payload[5:]
            _cn = {"atk_up": "攻击", "def_up": "防御", "spd_up": "速度", "crit_up": "暴击",
                   "matk_up_pot": "魔攻",
                   "food_atk_up": "攻击", "food_def_up": "防御", "food_spd_up": "速度",
                   "food_crit_up": "暴击", "food_matk_up": "魔攻"}
            for _k in kind.split(","):
                self.p_buffs[_k] = max(self.p_buffs.get(_k, 0), 3)
            _names = '、'.join(_cn.get(k, k) for k in kind.split(','))
            # v101.28b 食物 buff（food_ 前缀键）播报区分：料理 vs 药水
            if any(k.startswith("food_") for k in kind.split(",")):
                logs.append(f"🍖 你吃下了料理，{_names}提升！(3 回合)")
            else:
                logs.append(f"🧪 你饮下战斗药水，{_names}大幅提升！(3 回合)")
        else:
            heal = int(payload or 0)  # 复用 skill_name 传恢复量
            # 阶段九：半身人灵巧双手——消耗品效果 +10%
            rr = E.race_stats(player.get("race")).get("item_effect")
            if rr:
                heal = max(1, int(heal * (1 + rr)))
            if heal > 0:
                before = player["hp"]
                player["hp"] = min(player.get("max_hp", player["hp"]), player["hp"] + heal)
                logs.append(f"💊 你使用了战斗道具，恢复 {player['hp'] - before} 点生命！({player['hp']}/{player['max_hp']})")
            else:
                logs.append("💊 你使用了战斗道具！")
        return logs

    def _apply_hot(self, player: dict) -> list:
        """v101.28 食物持续恢复：每回合开始结算（回血/回蓝，回合数递减）。"""
        h = self.p_hot
        logs = []
        max_hp = player.get("max_hp", player.get("hp", 100))
        max_mp = player.get("max_mp", player.get("mp", 100))
        if h.get("heal"):
            gain = int(max_hp * h["heal"])
            if gain > 0:
                before = player.get("hp", 0)
                player["hp"] = min(max_hp, before + gain)
                logs.append(f"🍲 持续恢复生效，恢复 {player['hp'] - before} 点生命！({player['hp']}/{max_hp})")
        if h.get("mana"):
            gain = int(max_mp * h["mana"])
            if gain > 0:
                before = player.get("mp", 0)
                player["mp"] = min(max_mp, before + gain)
                logs.append(f"🍲 持续恢复生效，恢复 {player['mp'] - before} 点魔力！({player['mp']}/{max_mp})")
        h["turns"] -= 1
        if h["turns"] <= 0:
            self.p_hot = {}
        else:
            logs.append(f"（剩余 {h['turns']} 回合）")
        return logs

    def _do_player_skill(self, skill_name: str, player: dict) -> list:
        """玩家施放技能(v61 抽公共，普通回合与额外行动共用)"""
        logs = []
        st = self._player_stats(player)
        info = E.skill_info(player["class_name"], skill_name)
        if not info:
            logs.append(f"没有技能『{skill_name}』！")
            return logs
        if not E.is_skill_learned(player["class_name"], player["level"], skill_name,
                                  player.get("learned_skills", [])):
            logs.append(f"该技能需要 Lv.{info['lv']} 才能使用，你才 Lv.{player['level']}(或『技能学习 {skill_name}』提前学习)")
            return logs
        # v2.0 冷却：CD 未结束拦截（强控/终结技等）
        if self._skill_on_cd(skill_name):
            left = self._skill_cd_left(skill_name)
            logs.append(f"⏳【{skill_name}】还在冷却中(剩余 {left} 回合)！")
            return logs
        # v2.0 核心资源：技能消耗检查（res_cost，如怒气/连击点/信仰/气）
        res_cost = info.get("res_cost") or {}
        if res_cost:
            for rk, rv in res_cost.items():
                if not E.core_resource_spend(player["class_name"], self.resources, rv, key=rk):
                    rd = E.core_resource_def(player["class_name"])
                    rname = rd.get("name", rk)
                    cur = self.resources.get(rk, 0)
                    logs.append(f"⚡ {rname}不足！需要 {rv}，当前 {cur}(『攻击』攒资源)")
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
                logs.append(f"(格挡后 {dmg} 点伤害)")
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
                    logs.append(f"(格挡后 {dmg} 点伤害)")
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
        if random.random() < C.FLEE_CHANCE:
            logs.append("💨 你成功脱离了战斗！")
            self.result = "fled"
            return logs, True
        logs.append("💨 逃跑失败！被追上了！(可以再『逃跑』，或『防御』『用药』撑住)" )
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
        """符文效果等级(无则 0)"""
        return int(effs.get(effect, 0) or 0)

    def _player_stats(self, player: dict) -> dict:
        st = E.player_final_stats(player["class_name"], player["level"],
                                  player.get("equipment", {}),
                                  player.get("class_tier", 0),
                                  player.get("attributes"),
                                  player.get("evolve_path", 0),
                                  getattr(self, "title_bonus", None) or {},
                                  player.get("race"))
        st = self._apply_buffs(st, self.p_buffs)
        # #245: 玩家减速生效（与 _enemy_stats 的 spd_down 处理对称）——此前 p_buffs["spd_down"]
        # 只被挂载从未应用，减速玩家仍按原速度先手/触发速度优势
        if "spd_down" in self.p_buffs:
            st["spd"] = int(st.get("spd", 0) * SPD_DOWN_MULT)
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
        """普攻(含标记加成 + v10 套装攻击特效 + v34 符文效果)"""
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
        # 阶段八：装备被动词条伤害加成（处决/追猎/精准/龙语印记等）
        affix_mult, affix_tags = self._affix_dmg_mult(player)
        dmg = int(dmg * affix_mult)
        # 阶段九：种族攻击天赋（无畏/怯战 残血、龙之吐息 首击）
        race_mult, race_tags = self._race_attack_mult(player)
        dmg = int(dmg * race_mult)
        if race_tags:
            affix_tags = list(affix_tags) + race_tags
        # v34 残忍：暴击伤害 +x%（按等级）
        brutal_lvl = self._enchant_lvl(effs, "brutal")
        if brutal_lvl and is_crit:
            dmg = int(dmg * (1 + C.rune_value("brutal", brutal_lvl)))
        # 阶段八：暴击伤害词条（crit_dmg +20%）
        if "crit_dmg" in self._equip_affix_ids(player) and is_crit:
            dmg = int(dmg * 1.20)
        dmg = self._apply_mark(dmg)
        dmg = self._boss_dmg_filter(dmg, player, logs)
        self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - dmg)
        tag = " 💥暴击" if is_crit else ""
        if affix_tags:
            tag += " " + "·".join(affix_tags)
        logs.append(f"你{_basic_attack_verb(player)}，造成 {dmg} 点伤害！{tag}")
        # v34 符文攻击特效（灼烧/冻结/吸血/连锁/虚弱/破魔）
        self._apply_enchant_attack(effs, dmg, st, player, logs)
        # 阶段八：攻击命中后词条触发（流血/破甲/连击/元素附加等）
        self._affix_on_hit(player, dmg, logs)
        self._set_attack_proc(player, dmg, logs)
        # v2.0 核心资源：普攻获取（战士怒气/刺客连击点/拳师气）
        self._resource_on_attack(player)
        return logs

    def _resource_on_attack(self, player: dict):
        """v2.0 核心资源：普攻/技能命中自动获取(on_attack/on_skill)。"""
        cls = player.get("class_name", "")
        rd = E.core_resource_def(cls)
        if not rd:
            return
        k = rd["key"]
        gain = rd.get("on_attack", 0)
        if gain:
            self.resources[k] = E.core_resource_gain(cls, self.resources, gain)

    def _resource_on_skill(self, player: dict, info: dict = None):
        """v2.0 核心资源：技能命中获取（on_skill 或技能 res_gain 覆盖）。
        牧师治疗获取信仰（on_heal）。有 res_cost 的终结技不获取（消耗型）。"""
        cls = player.get("class_name", "")
        rd = E.core_resource_def(cls)
        if not rd:
            return
        k = rd["key"]
        # 终结技（有 res_cost）不获取资源
        if info and info.get("res_cost"):
            return
        # 技能自带 res_gain 覆盖默认（如终结技 0 获取）
        gain = 0
        if info and info.get("res_gain") is not None:
            gain = info["res_gain"]
        elif rd.get("on_skill"):
            gain = rd["on_skill"]
        if gain:
            self.resources[k] = E.core_resource_gain(cls, self.resources, gain)

    def _apply_enchant_attack(self, effs: dict, dmg: int, st: dict, player: dict, logs: list):
        """v34：攻击后符文效果结算(灼烧/冻结/吸血/连锁/虚弱/破魔)"""
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

    # ---------------- 阶段八：装备特效词条触发（20 章） ----------------
    def _equip_affix_ids(self, player: dict) -> list:
        """玩家已装备的全部词条 ID(affixes + legendary 专属)"""
        ids = []
        for item in (player.get("equipment") or {}).values():
            if not item:
                continue
            ids.extend(item.get("affixes", []) or [])
            if item.get("legendary"):
                ids.append(item["legendary"])
        # v101.28c 食物词条（战斗料理本场有效）
        ids.extend(getattr(self, "p_food_affixes", []) or [])
        return ids

    def _set_bonus_5(self, player: dict) -> list:
        """已激活 5 件套的套装名列表(10 章五节 5 件效果，战斗特效型)"""
        return [sname for sname, cnt in E.active_sets(player.get("equipment") or {}).items()
                if cnt >= 5]

    def _race_bonus(self, player: dict) -> dict:
        """种族天赋表(08 章，battle 消费战斗型天赋)"""
        return E.race_stats(player.get("race"))

    def _race_attack_mult(self, player: dict) -> tuple:
        """种族对玩家攻击的伤害倍率（无畏/怯战 残血攻击、龙之吐息 首击）。
        返回 (倍率, 标签列表)。"""
        rt = self._race_bonus(player)
        if not rt:
            return 1.0, []
        mult = 1.0
        tags = []
        ratio = player.get("hp", 0) / max(1, player.get("max_hp", 1))
        bz = rt.get("berserk_hp")
        if bz and ratio < bz:
            mult *= 1.20
            tags.append("🔥无畏")
        tm = rt.get("timid_hp")
        if tm and ratio < tm:
            mult *= 0.90
            tags.append("😰怯战")
        fh = rt.get("first_hit")
        if fh and not self.first_attack_done:
            mult *= 1 + fh
            tags.append(f"🐲龙之吐息x{round(1 + fh, 2)}")
            self.first_attack_done = True
        return mult, tags

    def _affix_dmg_mult(self, player: dict) -> tuple:
        """被动词条/专属对本次伤害的倍率。返回 (倍率, 标签列表)。

        处决（低血增伤）/追猎（标记）/破魔（魔法系）/龙威（龙系）/黎明之光（深渊系）
        /精准（命中强化近似 +10%）/龙语印记（每层 +2% 伤害）。
        """
        ids = self._equip_affix_ids(player)
        # 套装 5 件对敌增伤不依赖词条（10 章五节，复用龙威/黎明破晓的关键词模式）
        mult = 1.0
        tags = []
        s5names = "|".join(self._set_bonus_5(player))
        ename = self.enemy.get("name", "")
        if "圣光" in s5names and any(k in ename for k in ("暗", "影", "亡", "鬼", "骨", "骷髅")):
            mult *= 1.10
            tags.append("✨圣光克暗")
        if "龙脊" in s5names and "龙" in ename:
            mult *= 1.10
            tags.append("🐉龙息追猎")
        if "地底" in s5names and "深渊" in ename:
            mult *= 1.10
            tags.append("🕳️深渊共鸣")
        if not ids:
            return mult, tags
        e = self.enemy
        hp_ratio = e.get("hp", 0) / max(1, e.get("max_hp", 1))
        if "execute" in ids and hp_ratio < 0.30:
            mult *= 1.30
            tags.append("💀处决")
        if "jack_hook" in ids and hp_ratio < 0.30:
            mult *= 1.80
            tags.append("💀处决狂潮")
        if "ancient_king" in ids and hp_ratio < 0.35:
            mult *= 1.35
            tags.append("👑王权处决")
        if "hunt" in ids and "mark" in self.e_buffs:
            mult *= 1.20
            tags.append("🎯追猎")
        if "break_magic" in ids and e.get("role") == "caster":
            mult *= 1.25
            tags.append("🔮破魔")
        if "dragon_aw" in ids and "龙" in e.get("name", ""):
            mult *= 1.25
            tags.append("🐉龙威")
        if "dawn_light" in ids and "深渊" in e.get("name", ""):
            mult *= 1.50
            tags.append("🌅黎明破晓")
        if "precise" in ids:
            mult *= 1.10
            tags.append("🎯精准")
        dm = int(self.mech_stacks.get("dragon_mark", 0) or 0)
        if dm:
            mult *= 1 + 0.02 * dm
        return mult, tags

    def _affix_element_dmg(self, player: dict, element: str) -> float:
        """元素伤害加成（冰/雷属性伤害 +x%）：技能带对应 element 时生效
        来源：专属词条（LEGENDARY_EFFECTS ice_dmg/thunder_dmg，澜歌之泪/奥拉圣印等）
             + 套装 5 件（10 章五节：月语/海神=冰系 +10%、苍穹=雷系 +10%）"""
        if not element:
            return 1.0
        bonus = 0.0
        for aid in self._equip_affix_ids(player):
            info = C.LEGENDARY_EFFECTS.get(aid)
            if not info:
                continue
            eff = info.get("effect") or {}
            if element == "ice":
                bonus += eff.get("ice_dmg", 0) or 0
            elif element == "thunder":
                bonus += eff.get("thunder_dmg", 0) or 0
        # 套装 5 件元素增伤（月语=寒月冰、海神=水属落地冰、苍穹=雷）
        s5 = "|".join(self._set_bonus_5(player))
        if element == "ice" and ("月语" in s5 or "海神" in s5):
            bonus += 0.10
        if element == "thunder" and "苍穹" in s5:
            bonus += 0.10
        return 1.0 + bonus

    def _affix_on_hit(self, player: dict, dmg: int, logs: list):
        """攻击命中后词条触发：流血/破甲/连击/吸血/元素附加/贯穿/蓄力/净化/龙语印记/审判之链
        v98.5：效果数据化 → core/affix_effects.py HIT_EFFECTS（并列 if 语义，顺序遍历）"""
        ids = self._equip_affix_ids(player)
        if not ids or self.enemy.get("hp", 0) <= 0:
            return
        from .core.affix_effects import HIT_EFFECTS
        for fn in HIT_EFFECTS.values():
            fn(self, player, dmg, logs)

    def _affix_on_taken(self, player: dict, dmg: int, logs: list) -> int:
        """受击词条：减伤/格挡/坚韧/反击/反伤/深渊腐蚀。返回结算后的伤害。
        v98.5：效果数据化 → core/affix_effects.py TAKEN_EFFECTS（ctx 顺序结算）"""
        ids = self._equip_affix_ids(player)
        if not ids:
            return dmg
        from .core.affix_effects import TAKEN_EFFECTS
        ctx = {"dmg": dmg, "out": dmg}
        for fn in TAKEN_EFFECTS.values():
            fn(self, player, ctx, logs)
        return ctx["out"]

    def _affix_turn_start(self, player: dict, logs: list):
        """回合开始词条：回春(1% 生命)/冥想(1% 魔力)/晨曦祝福(2% 生命)
        v98.5：效果数据化 → core/affix_effects.py TURN_START_EFFECTS"""
        ids = self._equip_affix_ids(player)
        if not ids:
            return
        from .core.affix_effects import TURN_START_EFFECTS
        for fn in TURN_START_EFFECTS.values():
            fn(self, player, logs)


    def _skill_heal(self, st, skill_name, info, player, lv, mech, mval, p_mech, logs):
        """治疗分支（v103.6 从 _player_skill 拆出）"""
        # v32 条件转化：治疗技能也吃战场状态（如神谕者自身低血时治疗量提升）
        cond_mult = self._cond_mult(info, player, lv)
        cond_label = info.get("cond", {}).get("label", "") if cond_mult > 1.0 else ""
        # v95r38：power<1 的治疗技能按 max_hp 百分比结算（如拳师气息调息 15% HP），
        # power>=1 保持原有"魔攻×power"模式（治愈术 200% 等），与消耗品 heal<1 百分比语义一致
        if info.get("power", 0) < 1:
            heal = int(player.get("max_hp", 0) * info["power"] * E.skill_power_mult(lv, info) * cond_mult)
        else:
            heal = int(st["matk"] * info["power"] * E.skill_power_mult(lv, info) * cond_mult)
        # v64 被动·神恩：治疗技能效果 +10%
        pv = E.passive_skills_learned(player["class_name"], player.get("learned_skills", []))
        if "神恩" in pv:
            heal = int(heal * 1.10)
        # 阶段八：圣光套 2 件效果——治疗 +10%
        if E.has_set(player.get("equipment", {}), "圣光套"):
            heal = int(heal * 1.10)
        # 阶段九：种族受疗天赋（人类圣光亲和 +10% / 龙裔孤傲之血 -10%）
        hr = self._race_bonus(player).get("heal_received", 0) or 0
        if hr:
            heal = max(1, int(heal * (1 + hr)))
            if hr > 0:
                logs.append(f"✨ 圣光亲和：治疗效果 +{int(hr*100)}%！")
            else:
                logs.append(f"🐉 孤傲之血：治疗效果 -{int(-hr*100)}%！")
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
            logs.append(f"✨ 神恩凝聚：{p_mech.get('bless', 0)} 层(下次『神圣之光』转化护盾)")
        # v50 团队治疗：记录全队效果（副本广播）
        if info.get("team"):
            self.team_effects.append({"kind": "heal_all", "power": info["power"], "lv": lv, "matk": st["matk"]})
            logs.append(f"🌟【团队】圣光笼罩全队，所有人恢复 {heal} 点生命！")
        # v2.0 核心资源：治疗获取信仰（on_heal=2）
        self._resource_on_skill(player, info)
        return logs


    def _skill_buff(self, st, skill_name, info, player, lv, mech, mval, p_mech, logs):
        """增益分支（v103.6 从 _player_skill 拆出）"""
        eff = info.get("effect")
        if eff:
            if eff == "mon_atk_down":
                # v51 挫志怒吼：敌方攻击下降（写 e_buffs 而非 p_buffs）
                self.e_buffs["mon_atk_down"] = E.skill_buff_turns(lv)
            elif eff == "element_shift":
                # v2.1 元素跃迁：切换当前元素亲和系（火→冰→雷→火），下次元素技能伤害 +20%
                cur = self.resources.get("element", "fire")
                nxt = {"fire": "ice", "ice": "thunder", "thunder": "fire"}.get(cur, "fire")
                self.resources["element"] = nxt
                self.p_buffs["matk_up"] = E.skill_buff_turns(lv)
                self._shifted_element = nxt
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
        if eff == "element_shift" and getattr(self, "_shifted_element", None):
            logs.append(f"✦ 元素跃迁！切换到 {E.ELEMENT_CN.get(self._shifted_element, '?')}系(下次元素技能伤害＋20%)")
            self._shifted_element = None
        # v50 团队增益：记录全队效果（副本广播）
        team = info.get("team")
        if team:
            st2 = self._player_stats(player)
            self.team_effects.append({"kind": team, "effect": eff, "lv": lv, "stats": st2})
            logs.append(f"🌟【团队】{info.get('name', skill_name)} 笼罩全队！")
        # v2.0 核心资源：增益技能获取（如战吼怒气+3）
        self._resource_on_skill(player, info)
        return logs
    def _player_skill(self, st: dict, skill_name: str, info: dict, player: dict) -> list:
        """施放技能：治疗/增益/攻击 + 特效全部落地(v27 技能等级 + v29 分支机制)"""
        logs = []
        lv = E.skill_level_of(player, skill_name)  # #259：兼容 skill_levels key 为中文名（战斗内等级此前恒 Lv.1）
        kind = info["kind"]
        mech = info.get("mech", "")
        # v56：叠层随技能等级成长（每 2 级 +1 层）
        mval = E.skill_mech_val(info, lv)
        # 分支专属状态层（玩家侧：狂暴/圣盾/风印/影袭/气力/神恩/毒层）
        p_mech = self.mech_stacks
        if kind == "治疗":
            return self._skill_heal(st, skill_name, info, player, lv, mech, mval, p_mech, logs)
        if kind == "增益":
            return self._skill_buff(st, skill_name, info, player, lv, mech, mval, p_mech, logs)
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
        # v87 被动·双修精通：力量/智力同时增加时，额外 +5% 攻击（魔剑士专属）
        if "双修精通" in pv:
            st_full = self._player_stats(player)
            if st_full.get("atk") and st_full.get("matk"):
                passive_bonus *= 1.05
        # v2.0 元素反应：当前系 × 目标印记（技能带 element 字段时判定；"current"=当前元素亲和系）
        element = info.get("element", "")
        if element == "current":
            element = self.resources.get("element", "fire")
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
        # 阶段八：装备被动词条伤害加成（处决/追猎/精准/龙语印记等）+ 专属元素伤害
        affix_mult, affix_tags = self._affix_dmg_mult(player)
        elem_mult = self._affix_element_dmg(player, element)
        # 阶段九：种族攻击天赋（无畏/怯战 残血、龙之吐息 首击）
        race_mult, race_tags = self._race_attack_mult(player)
        if race_tags:
            affix_tags = list(affix_tags) + race_tags
        pmult = (E.skill_power_mult(lv, info) * frozen_bonus * stack_bonus * cond_mult
                 * magic_bonus * passive_bonus * reaction_mult * affix_mult * elem_mult * race_mult)
        for _ in range(multi):
            if kind == "物理":
                if info.get("pierce"):
                    dmg_i = E.calc_damage(int(st["atk"] * info["power"] * pmult), 0, is_crit, pierce=True)
                else:
                    dmg_i = E.calc_damage(int(st["atk"] * info["power"] * pmult), est["def"], is_crit)
                # v87 魔剑士·混合伤害：magic_add 追加魔法段（魔能斩 130% 物 + 30% 魔）
                if info.get("magic_add"):
                    dmg_m = E.calc_damage(int(st["matk"] * info["magic_add"] * pmult), est["mdef"], is_crit)
                    dmg_i += dmg_m
            else:
                dmg_i = E.calc_damage(int(st["matk"] * info["power"] * pmult), est["mdef"], is_crit)
            # v87 魔剑士·魔力涌动：消耗 buff，本次攻击追加 80% 魔法伤害
            if self.p_buffs.get("spellblade_surge"):
                surge_dmg = E.calc_damage(int(st["matk"] * 0.80 * pmult), est["mdef"], is_crit)
                dmg_i += surge_dmg
                del self.p_buffs["spellblade_surge"]
            # v34 残忍：暴击伤害 +x%（按等级）
            brutal_lvl = self._enchant_lvl(effs, "brutal")
            if brutal_lvl and is_crit:
                dmg_i = int(dmg_i * (1 + C.rune_value("brutal", brutal_lvl)))
            # 阶段八：暴击伤害词条（crit_dmg +20%）
            if "crit_dmg" in self._equip_affix_ids(player) and is_crit:
                dmg_i = int(dmg_i * 1.20)
            dmg_i = self._apply_mark(dmg_i)
            total += dmg_i
        total = self._boss_dmg_filter(total, player, logs)
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
        # 阶段八：词条伤害标签（处决/追猎/精准等）
        if affix_tags:
            tags.extend(affix_tags)
        if elem_mult > 1.0:
            tags.append(f"✨元素x{round(elem_mult, 2)}")
        if tags:
            logs[-1] += " " + "·".join(tags)
        if reaction_log:
            logs.append(reaction_log)
        # v2.0 元素印记：施放带 element 的技能后给目标挂印记 + 法师切换当前系
        if element and E.ELEMENT_MARKS.get(element):
            E.element_mark_apply(self.e_buffs, element, 1)
            if self.resources.get("element") is not None:
                self.resources["element"] = element
        # v2.0 连招序列：拳师 combo 字段推进（拳→踢→掌 三连触发额外效果）
        combo_tag = info.get("combo", "")
        if combo_tag:
            combo_full = self._combo_push(combo_tag)
            if combo_full:
                combo_bonus = int(total * 0.30)
                self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - combo_bonus)
                logs.append(f"🥊 三连击破！拳-踢-掌完美连招，追加 {combo_bonus} 点伤害！(下次斗气技＋20%)")
                self.resources["combo_ready"] = 1
            else:
                logs.append(f"🥊 连招 {self._combo_label()}")
        # v34 符文攻击特效（灼烧/冻结/吸血/连锁/虚弱）
        self._apply_enchant_attack(effs, total, st, player, logs)
        # 阶段八：攻击命中后词条触发（流血/破甲/连击/元素附加等）
        self._affix_on_hit(player, total, logs)

        # ---- 分支机制结算（v29） ----
        self._last_player = player
        self._apply_mech_effect(mech, mval, p_mech, total, logs, skill_name, is_crit)
        # v63 额外控制效果（cc 字段，独立于 mech 叠层）：眩晕/沉默/净化
        cc = info.get("cc")
        if cc and cc in ("stun", "silence", "cleanse"):
            self._apply_mech_effect(cc, 1, p_mech, total, logs, skill_name, is_crit)

        # ---- 技能特效（v9 落地）----
        # v2.0：技能名硬编码特效已废弃（12 章技能全数据驱动，mech/effect/cond 在 _apply_mech_effect 覆盖）
        if info.get("effect") == "lifesteal":
            heal = int(total * E.skill_lifesteal_pct(info, lv))
            player["hp"] = min(player.get("max_hp", player["hp"]), player.get("hp", 0) + heal)
            logs.append(f"💉 『{skill_name}』汲取了 {heal} 点生命！")
        # v2.0 破防（pierce 数据字段）：直接给敌方降防
        if info.get("pierce") and self.enemy.get("hp", 0) > 0:
            self.e_buffs["def_down"] = E.skill_buff_turns(lv)
        # v2.0 核心资源：攻击技能获取（战士怒气/刺客连击点/拳师气，res_gain 覆盖默认）
        self._resource_on_skill(player, info)
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
        if mech == "spellblade":
            n = p_mech.get("spellblade", 0)
            if n:
                return 1.0 + n * 0.08
        return 1.0

    def _cond_mult(self, info: dict, player: dict, lv: int = 1) -> float:
        """条件转化（v30）：按战场状态返回伤害倍率。
        cond 结构：{"type": "...", "hp_pct": 0.4, "mult": 1.6, "label": "处决狙击"}
        倍率随技能等级成长（v56）：每级 +0.05，lv 默认 1 保持向后兼容。
        v98.4：判定逻辑数据化 → core/battle_conds.py COND_CHECKS 注册表
        （23 种条件类型；未知 type 安全降级 1.0，与旧 elif 链兜底一致）
        """
        cond = info.get("cond")
        if not cond:
            return 1.0
        from .core.battle_conds import COND_CHECKS
        check = COND_CHECKS.get(cond.get("type"))
        if check and check(self, player, cond):
            return E.skill_cond_mult(cond, lv, info)
        return 1.0

    def _apply_mech_gain(self, mech: str, mval: int, p_mech: dict, logs: list, skill_name: str):
        """增益类技能叠层(v59：封顶)"""
        if mech and mval and mech in ("rage", "shield", "wind", "shadow", "chi", "bless", "judge", "iron", "mark", "burn", "poison", "freeze", "arcane", "spellblade"):
            p_mech[mech] = E.mech_stack_gain(mech, p_mech, mval)

    def _apply_mech_effect(self, mech: str, mval: int, p_mech: dict, total: int, logs: list, skill_name: str, is_crit: bool = False):
        """攻击技能施放后的机制结算（v98.4：数据化 → core/battle_mech.py MECH_EFFECTS）"""
        from .core.battle_mech import MECH_EFFECTS
        handler = MECH_EFFECTS.get(mech)
        if handler:
            handler(self, mval, p_mech, total, logs, skill_name, is_crit)

    # ---------------- v10 套装攻击特效 ----------------
    def _set_attack_proc(self, player: dict, dmg: int, logs: list):
        """玩家攻击后触发已激活套装的 4 件攻击特效
        v98.5：效果数据化 → core/affix_effects.py SET_PROC_EFFECTS"""
        effs = E.set_bonus_4(player.get("equipment", {}))
        if not effs:
            return
        from .core.affix_effects import SET_PROC_EFFECTS
        for eff in effs:
            fn = SET_PROC_EFFECTS.get(eff)
            if fn:
                fn(self, player, dmg, logs)

    # ---------------- 敌方回合 ----------------
    def _boss_dmg_filter(self, dmg: int, player: dict, logs: list) -> int:
        """v83 04 章 2.5：Boss 护盾/反伤过滤（挂在玩家伤害结算主路径）。
        shield：护盾存在期间受伤 -50%，先扣盾再扣血（破盾提示）。
        reflect：血量 <25% 反弹 15% 伤害给玩家。
        v93：worldboss 应用 GM 伤害倍率（gm_伤害 设置）。"""
        if self.btype == "worldboss" and self.dmg_mult != 1.0:
            dmg = int(dmg * self.dmg_mult)
            if dmg < 1:
                dmg = 1
        mech = self.enemy.get("mech")
        if not mech or self.btype == "pvp":
            return dmg
        mechs = [x.strip() for x in mech.split(",") if x.strip()]
        e = self.enemy
        if "shield" in mechs:
            sh = e.get("boss_shield", 0)
            if sh > 0:
                real = int(dmg * 0.5)
                absorbed = min(sh, real)
                e["boss_shield"] = sh - absorbed
                if e["boss_shield"] <= 0:
                    e.pop("boss_shield", None)
                    logs.append("💥 护盾破碎！")
                dmg = real
        if "reflect" in mechs:
            ratio = e.get("hp", 0) / max(1, e.get("max_hp", 1))
            if ratio < 0.25:
                rb = int(dmg * 0.15)
                if rb > 0:
                    player["hp"] = max(1, player.get("hp", 1) - rb)
                    logs.append(f"🩸【{e['name']}】龙鳞反伤！你受到 {rb} 点反弹伤害！")
        return dmg

    def _boss_mech(self, logs: list):
        """v58/v83 Boss 专属机制（04 章 2.5）：enrage/summon/heal/shield/phase/stacks/reflect
        支持逗号分隔多机制（如 "enrage,summon"）。状态存 enemy dict（随战斗序列化持久化）
        v98.4：机制实现数据化 → core/battle_mech.py BOSS_MECHS（reflect 仍是被动，在 _boss_dmg_filter）"""
        mech = self.enemy.get("mech")
        if not mech or self.btype == "pvp":
            return
        from .core.battle_mech import BOSS_MECHS
        mechs = [x.strip() for x in mech.split(",") if x.strip()]
        r = self.round
        e = self.enemy
        for m in mechs:
            handler = BOSS_MECHS.get(m)
            if handler:
                handler(self, logs, e, r)

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
        if self.enemy.get("skills") and random.random() < C.MON_SKILL_CHANCE and not silenced:
            skill = random.choice(self.enemy["skills"])
            sinfo = C.MONSTER_SKILLS.get(skill)
            if sinfo:
                sname = sinfo.get("name", skill)  # 显示中文名（技能池可能存 ID）
                kind = sinfo.get("kind")
                if kind == "增益":
                    from .core.battle_mech import MON_BUFF_EFFECTS
                    eff = sinfo.get("effect")
                    eff_fn = MON_BUFF_EFFECTS.get(eff)
                    if eff_fn:
                        eff_fn(self, logs, sname)
                    return logs, 0
                power = sinfo.get("power", 1.0)
                is_crit = random.random() < C.MON_SKILL_CRIT
                if kind == "物理":
                    dmg = E.calc_damage(int(est["atk"] * power), pst["def"], is_crit)
                else:
                    dmg = E.calc_damage(int(est["matk"] * power), pst["mdef"], is_crit)
                # 阶段九：种族受击天赋（龙鳞 魔伤-10% / 鲁莽之心 魔伤+5%，魔法技能段）
                if kind != "物理":
                    rt = self._race_bonus(player)
                    mr = rt.get("magic_reduce", 0) or 0
                    if mr:
                        red = max(1, int(dmg * mr))
                        dmg = max(1, dmg - red)
                        if mr > 0:
                            logs.append(f"🐲 龙鳞抗魔，减免 {red} 点伤害！")
                        else:
                            logs.append(f"🔥 鲁莽之心，额外受到 {-red} 点伤害！")
                # 阶段八.1：怪物元素技能 → 玩家元素抗性减免（elem_resist 火/冰/雷 -8%、abyss_resist 暗影 -10%）
                melem = sinfo.get("element", "")
                if melem:
                    resist = 0.0
                    pids = self._equip_affix_ids(player)
                    if melem in ("fire", "ice", "thunder") and "elem_resist" in pids:
                        resist += 0.08
                    elif melem == "dark" and "abyss_resist" in pids:
                        resist += 0.10
                    if resist > 0:
                        red = max(1, int(dmg * resist))
                        dmg = max(1, dmg - red)
                        logs.append(f"🛡️ 元素抗性减免 {red} 点伤害！")
                logs.append(f"【{self.enemy['name']}】使用了【{sname}】，对你造成 {dmg} 点伤害！" + (" 💥暴击！" if is_crit else ""))
                # v63 怪物技能机制：眩晕/沉默/冻结 等控制（v98.4：数据化 → core/battle_mech.py MON_CTRL_EFFECTS）
                mmech = sinfo.get("mech")
                if mmech:
                    from .core.battle_mech import MON_CTRL_EFFECTS
                    ctrl_fn = MON_CTRL_EFFECTS.get(mmech)
                    if ctrl_fn:
                        mval = int(sinfo.get("mech_val", 1) or 1)
                        ctrl_fn(self, player, logs, mval)
                return logs, dmg
        dmg = E.calc_damage(est["atk"], pst["def"])
        # 阶段九：种族受击天赋（石肤 物理伤害-10%，普攻段）
        rt = self._race_bonus(player)
        pr = rt.get("phys_reduce", 0) or 0
        if pr:
            red = max(1, int(dmg * pr))
            dmg = max(1, dmg - red)
            logs.append(f"🪨 石肤护体，减免 {red} 点物理伤害！")
        logs.append(f"【{self.enemy['name']}】攻击你，造成 {dmg} 点伤害！")
        return logs, dmg

    def _pvp_enemy_turn(self, player: dict) -> tuple:
        """PVP：敌方玩家行动(v9.2 启用；先实现 AI 普攻)"""
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
        """敌方当前属性(应用敌方增益/减益)"""
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
        # v83 04 章 2.5：多阶段（每阶段 +20%）/ 叠层强化（每层 +8%）
        if e.get("phase_count"):
            pm = 1 + 0.20 * e["phase_count"]
            est["atk"] = int(est["atk"] * pm)
            est["matk"] = int(est["matk"] * pm)
        if e.get("mech_stacks_n"):
            sm = 1 + 0.08 * e["mech_stacks_n"]
            est["atk"] = int(est["atk"] * sm)
        if "def_down" in self.e_buffs:
            # 阶段八：词条破甲 15%（_armor_break_pct），旧技能破甲减半兜底
            pct = float(self.e_buffs.get("_armor_break_pct", DEF_DOWN_MULT) or DEF_DOWN_MULT)
            est["def"] = int(est["def"] * (1 - pct))
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

    def _pet_skill_turn(self, player: dict, logs: list) -> list:
        """24 章宠物技能：每 N 回合自动触发（不占玩家行动、不消耗 MP）。
        撕咬(atk_pct)/龙息(matk_pct)/月光祝福(heal_pct) 在玩家回合开始触发；
        影袭(block) 在 _damage_player 前拦截（见 _pet_block_check）。
        Lv.10 解锁；饱食度 =0 时技能失效。
        """
        pet = self.pet or {}
        if not pet:
            return logs
        if int(pet.get("level", 0)) < 10:
            return logs
        if int(pet.get("satiety", 0)) <= 0:
            return logs
        pdef = next((p for p in C.PET_POOL if p["key"] == pet.get("pet_key")), None)
        if not pdef:
            return logs
        interval = int(pdef.get("skill_interval", 0) or 0)
        if interval <= 0 or self.round % interval != 0:
            return logs
        stype = pdef.get("skill_type")
        pname = pet.get("name") or pdef["name"]
        sname = pdef["skill_name"]
        line = C.pet_line(pdef["key"])  # v101.11 宠物战斗台词
        if stype in ("atk_pct", "lifesteal", "pierce"):
            st = self._player_stats(player)
            est = self._enemy_stats()
            dmg = E.calc_damage(int(st["atk"] * pdef["skill_value"]), est.get("def", 0))
            self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - dmg)
            logs.append(f"🐾 {pname}的【{sname}】造成 {dmg} 点伤害！" + (f"({line})" if line else ""))
            if stype == "lifesteal":
                heal = max(1, int(dmg * 0.5))
                player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
                logs.append(f"🩸 {pname}汲取了 {heal} 点生命归还给你！")
            elif stype == "pierce":
                self.e_buffs["def_down"] = max(int(self.e_buffs.get("def_down", 0) or 0), 2)
                logs.append(f"🛡️ {pname}的【{sname}】击碎了敌人的护甲！(防御减半 2 回合)")
            if self._enemy_dead():
                self.result = "victory"
                logs.append(f"🎉 你击败了【{self.enemy.get('name', '敌人')}】！(宠物击杀)")
        elif stype == "matk_pct":
            st = self._player_stats(player)
            est = self._enemy_stats()
            dmg = E.calc_damage(int(st["matk"] * pdef["skill_value"]), est.get("mdef", 0))
            self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - dmg)
            logs.append(f"🐾 {pname}的【{sname}】造成 {dmg} 点伤害！" + (f"({line})" if line else ""))
            if self._enemy_dead():
                self.result = "victory"
                logs.append(f"🎉 你击败了【{self.enemy.get('name', '敌人')}】！(宠物击杀)")
        elif stype == "heal_pct":
            if player.get("hp", 0) < player.get("max_hp", 1):
                heal = int(player.get("max_hp", player.get("hp", 1)) * pdef["skill_value"])
                player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
                logs.append(f"🐾 {pname}的【{sname}】为你回复了 {heal} 点生命！" + (f"({line})" if line else ""))
        elif stype == "buff_atk":
            self.p_buffs["atk_up"] = max(int(self.p_buffs.get("atk_up", 0) or 0), 2)
            logs.append(f"🐾 {pname}的【{sname}】为你加持攻击强化！(攻击 +30%，2 回合)" + (f"（{line}）" if line else ""))
        elif stype == "crit_up":
            self.p_buffs["crit_up"] = max(int(self.p_buffs.get("crit_up", 0) or 0), 2)
            logs.append(f"🐾 {pname}的【{sname}】为你加持暴击提升！(暴击 +20%，2 回合)" + (f"（{line}）" if line else ""))
        return logs

    def _pet_block_check(self, dmg: int, logs: list) -> int:
        """24 章宠物技能·影袭：每 N 回合 value 概率替主人挡一次攻击(敌方伤害结算前)。"""
        if dmg <= 0:
            return dmg
        pet = self.pet or {}
        if not pet:
            return dmg
        if int(pet.get("level", 0)) < 10:
            return dmg
        if int(pet.get("satiety", 0)) <= 0:
            return dmg
        pdef = next((p for p in C.PET_POOL if p["key"] == pet.get("pet_key")), None)
        if not pdef or pdef.get("skill_type") != "block":
            return dmg
        interval = int(pdef.get("skill_interval", 0) or 0)
        if interval <= 0 or self.round % interval != 0:
            return dmg
        if random.random() < pdef.get("skill_value", 0):
            pname = pet.get("name") or pdef["name"]
            logs.append(f"🐾 {pname}的【{pdef['skill_name']}】替你挡下了这次攻击！")
            return 0
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
                logs.append(f"🎉 你击败了【{self.enemy['name']}】！(灼烧致死)")
        # v29 毒层：每层 3% 生命（优先战斗层数；老毒箭仍用 e_buffs 布尔标记）
        mech = self.mech_stacks
        poison_n = int(mech.get("poison", 0) or 0)
        if poison_n > 0:
            p = int(self.enemy.get("max_hp", 1) * POISON_PCT * poison_n)
            self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - p)
            logs.append(f"☠️ 【{self.enemy['name']}】中毒发作，损失 {p} 点生命！")
            if self._enemy_dead():
                self.result = "victory"
                logs.append(f"🎉 你击败了【{self.enemy['name']}】！(毒发身亡)")
        elif "poison" in self.e_buffs:
            p = int(self.enemy.get("max_hp", 1) * POISON_PCT)
            self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - p)
            logs.append(f"☠️ 【{self.enemy['name']}】中毒发作，损失 {p} 点生命！")
            if self._enemy_dead():
                self.result = "victory"
                logs.append(f"🎉 你击败了【{self.enemy['name']}】！(毒发身亡)")
        # 阶段八：流血词条（每回合 5% 生命，e_buffs["bleed"] = 剩余回合数，回合递减交给 _end_round）
        bleed_n = int(self.e_buffs.get("bleed", 0) or 0)
        if bleed_n > 0:
            p = int(self.enemy.get("max_hp", 1) * 0.05)
            self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - p)
            logs.append(f"🩸 【{self.enemy['name']}】流血不止，损失 {p} 点生命！")
            if self._enemy_dead():
                self.result = "victory"
                logs.append(f"🎉 你击败了【{self.enemy['name']}】！(失血过多)")
        # 阶段八：词条回合开始回复（回春/冥想/晨曦祝福）
        self._affix_turn_start(player, logs)
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
        # v2.1 被动·奥术直觉：每回合开始奥术充能 +1（奥术法师自动蓄能）
        if "奥术直觉" in E.passive_skills_learned(player["class_name"], player.get("learned_skills", [])):
            self.mech_stacks["arcane"] = E.mech_stack_gain("arcane", self.mech_stacks, 1)
            logs.append(f"📖 奥术直觉：充能自动＋1(当前 {self.mech_stacks['arcane']} 层)")
        # v87 被动·符文刻印：魔剑士每回合自动获得 1 层魔能（上限 5）
        if "符文刻印" in E.passive_skills_learned(player["class_name"], player.get("learned_skills", [])):
            self.mech_stacks["spellblade"] = E.mech_stack_gain("spellblade", self.mech_stacks, 1)
            logs.append(f"⚔️ 符文刻印：魔能自动＋1(当前 {self.mech_stacks['spellblade']} 层)")
        # v2.0 核心资源：回合回复（游侠精力 +25/回合）
        cls = player.get("class_name", "")
        rd = E.core_resource_def(cls)
        if rd and rd.get("regen", 0) > 0:
            k = rd["key"]
            old = self.resources.get(k, 0)
            self.resources[k] = E.core_resource_regen(cls, self.resources)
            new = self.resources[k]
            if new > old:
                logs.append(f"🍃 {rd['name']}回复 {new - old} 点({new}/{rd['max']})")
        return logs

    def _end_round(self):
        """回合结束：buff 剩余回合递减 + v2.0 技能冷却递减"""
        for tbl in (self.p_buffs, self.e_buffs):
            for k in list(tbl):
                # v95.24 #252: 控制类 buff（stun/freeze）是"行动级"控制——由行动消费点
                # （_enemy_turn 1295-1303 / player_turn 314-321 / 额外行动 265-271）负责 pop，
                # 不能在回合结束时递减：否则施放当回合若敌方无行动（副本 enemy_act=False、
                # 敌方先手 e_extra_left=0、敌方施放眩晕给玩家）会被直接吞掉，眩晕永远不生效。
                if k in ("stun", "freeze"):
                    continue
                tbl[k] -= 1
                if tbl[k] <= 0:
                    del tbl[k]
        self._tick_cooldowns()

    def _damage_player(self, player: dict, dmg: int, logs: list):
        if dmg <= 0:
            return
        # 24 章宠物技能·影袭：替主人挡一次攻击（拦截后直接结束本次伤害）
        dmg = self._pet_block_check(dmg, logs)
        if dmg <= 0:
            return
        self._player_hit = True  # v2.1 条件：记录本场受击（未受击增伤判定）
        # 阶段八：受击词条（减伤/格挡/反击/反伤/腐蚀/坚韧）
        dmg = self._affix_on_taken(player, dmg, logs)
        # v64 被动·铁壁之心/磐石体：受到伤害时减伤 5%
        pv = E.passive_skills_learned(player.get("class_name", ""), player.get("learned_skills", []))
        if "铁壁之心" in pv or "磐石体" in pv:
            reduce = int(dmg * 0.05)
            dmg = max(1, dmg - reduce)
            logs.append(f"🛡️ 被动减伤 {reduce} 点(铁壁之心/磐石体)")
        # v51 盾牌反击：被攻击时 60% 概率反击 120% 伤害
        if self.p_buffs.get("counter", 0) > 0 and self.enemy.get("hp", 0) > 0:
            if random.random() < C.SHIELD_COUNTER_CHANCE:
                pst2 = self._player_stats(player)
                est2 = self._enemy_stats()
                cd = E.calc_damage(int(pst2["atk"] * 1.2), est2.get("def", 0))
                self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - cd)
                logs.append(f"🛡️ 盾牌反击！对【{self.enemy.get('name', '敌人')}】造成 {cd} 点伤害！")
        # 龙鳞套：被攻击时 25% 概率反弹 25% 伤害
        if "reflect" in E.set_bonus_4(player.get("equipment", {})) and self.enemy.get("hp", 0) > 0:
            if random.random() < C.REFLECT_CHANCE:
                rd = int(dmg * 0.25)
                self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - rd)
                logs.append(f"🐉 龙鳞反震！反弹 {rd} 点伤害！")
        # v29 金身：每层减伤 4%
        mech = self.mech_stacks
        iron = int(mech.get("iron", 0) or 0)
        if iron > 0:
            reduce = int(dmg * 0.04 * iron)
            dmg = max(1, dmg - reduce)
            logs.append(f"🪷 金身减伤 {reduce} 点({iron} 层)")
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
            logs.append(f"✨ 护盾吸收 {absorb} 点伤害(剩余 {self.shield})")
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
            if random.random() < C.HOLY_TENACITY_CHANCE:
                heal = int(player.get("max_hp", player.get("hp", 1)) * 0.05)
                player["hp"] = min(player.get("max_hp", player["hp"]), player["hp"] + heal)
                logs.append(f"✨ 神圣坚韧：回复 {heal} 点生命！")

    def _enemy_dead(self) -> bool:
        return self.enemy.get("hp", 1) <= 0

    def _player_dead(self, player: dict) -> bool:
        return player.get("hp", 1) <= 0
