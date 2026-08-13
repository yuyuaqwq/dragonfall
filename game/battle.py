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
import time

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


# v105 P3(M01)：种族残血攻倍率常量——battle 结算与 race_talent_display 展示共用，
# 调数值只改这里（此前两处各自硬编码 1.20/0.90，调值会文案失配）
RACE_BERSERK_MULT = 1.20   # 无畏：HP 低于 berserk_hp 阈值时攻击 ×1.20（展示文案 +20%）
RACE_TIMID_MULT = 0.90     # 怯战：HP 低于 timid_hp 阈值时攻击 ×0.90（展示文案 -10%）


def _basic_attack_verb(player: dict) -> str:
    """普攻动作文案（按职业；未知职业 fallback 挥剑攻击）"""
    return _ATK_VERB.get(player.get("class_name", ""), "挥剑攻击")


# 增益倍率映射：effect -> (修正属性, 倍率/加成)
BUFF_MULT = {
    "atk_up":         ("atk", 1.30),
    "atk_up_strong":  ("atk", 1.75),
    "echo_bless":     ("atk", 1.05),   # v97.4 回音洞穴祝福：本场攻击 +5%（一次性，探索事件写入）
    "matk_up":        ("matk", 1.50),   # #244a：与技能描述 matk+50% 对齐（原 1.35 与 desc 不符）
    "matk_up_strong": ("matk", 1.80),
    "matk_up_pot":    ("matk", 1.30),   # 9.3 鲛人之泪：本回合魔攻 +30%
    "def_up":         ("def", 1.45),
    "spd_up":         ("spd", 1.40),
    "crit_up":        ("crit", 0.20),      # 暴击率 +20%
    # v101.28f 药水强度分档（名字不同效果不同的真实落地：战吼/龙力 +40%、蛮力 +20%、风灵 +20%、致命 +30%、锐目 +15%）
    "atk_up_big":     ("atk", 1.40),
    "atk_up_small":   ("atk", 1.20),
    "spd_up_small":   ("spd", 1.20),
    "crit_up_small":  ("crit", 0.15),
    "crit_up_big":    ("crit", 0.30),
    # v101.28b 食物增益（战斗料理线：数值约为药水 1/3，价格低+带战斗外恢复）
    "food_atk_up":    ("atk", 1.10),
    "food_def_up":    ("def", 1.15),
    "food_spd_up":    ("spd", 1.12),
    "food_crit_up":   ("crit", 0.08),
    "food_matk_up":   ("matk", 1.10),
    "food_spd_up_small": ("spd", 1.10),  # v105 M16 精灵果酱：战斗中本场速度+10%（策划 19:129）
    "mon_atk_up":     ("atk", 1.30),
    "mon_atk_up_strong": ("atk", 1.70),
    "mon_def_up":     ("def", 1.40),
    "mon_atk_down":   ("atk", 0.70),   # v51 挫志怒吼：敌方攻击 -30%
}
# v104 M02 P1-4：团队增益 effect=xx_all → 施放者自身有效 buff 键（与 instance.py buff_effects 同口径）
TEAM_BUFF_KEYS = {
    "def_all": "def_up", "reduce_all": "def_up", "atk_all": "atk_up",
    "matk_all": "matk_up_strong", "crit_all": "crit_up", "spd_all": "spd_up",
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
        self.player = player or {}         # v105 攻击方属性读取（_monster_dodge_check 需要玩家精准）
        self.p_buffs: dict = {}            # 玩家增益 {effect: turns}
        self.poi_buff: dict | None = None  # v104 M23 神龛祝福：{stat,mult,name}，持久 5 次战斗，battle 开始时消费 1 次
        self.p_hot: dict = {}              # v101.28 食物持续恢复 {"heal": 比例, "mana": 比例, "turns": 剩余回合}
        self.p_food_effects: list = []     # v101.28e 食物效果（战斗中吃料理获得，本场有效；独立于装备词条体系）
        self.p_shields: dict = {}          # v101.28d 护盾 buff 化：来源 → {"value": 盾值, "turns": 剩余回合}，同源可叠厚，异源并存
        self.e_minions: list = []          # v101.28l #438 真召唤：敌方援军实体 [{name,hp,max_hp,atk,matk}]
        self.e_buffs: dict = {}            # 敌方状态 {effect: turns}（含减益）
        self.p_defending = False           # 玩家本回合是否防御
        self.e_defending = False
        self.result = None                 # None | victory | defeat | fled
        self.title_bonus = title_bonus or {}  # 副业大师称号属性加成
        self.team_effects: list = []         # v50 团队技能效果（副本全队广播用）
        self.mech_stacks: dict = {}          # v59 分支机制叠层（随战斗持久化，不再挂 player 避免每回合丢失）
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
            # v104 M23 神龛祝福（探索 POI 写入，玩家级键 poi_buff_{qq_id}——battle 无 group_id
            # 上下文，与 echo_bless bless_{qq_id} 同款全局键）：战斗开始时读取 → 本场对应属性
            # ×1.10，left-1；用完删除 key（flee 也算消耗 1 次，按文案「持续 5 次战斗」计）
            if player.get("qq_id") and not getattr(self, "poi_buff", None):
                try:
                    import json as _json
                    from . import db as _db
                    _key = f"poi_buff_{player['qq_id']}"
                    _raw = _db.get_event_state(_key)
                    if _raw:
                        _pb = _json.loads(_raw)
                        if isinstance(_pb, dict) and _pb.get("stat") in ("atk", "def", "spd") \
                                and int(_pb.get("left", 0) or 0) > 0:
                            self.poi_buff = {"stat": _pb["stat"],
                                             "mult": float(_pb.get("mult", 1.10)),
                                             "name": _pb.get("name", _pb["stat"])}
                            _pb["left"] = int(_pb["left"]) - 1
                            if _pb["left"] <= 0:
                                _db.delete_event_state(_key)
                            else:
                                _db.set_event_state(_key, _json.dumps(_pb, ensure_ascii=False))
                except Exception:
                    pass
            self._init_resources(player)
        # 阶段八：战斗开始词条——护盾（获得 10% 生命护盾，3 回合；v101.28d 盾 buff 化）
        if player and "shield" in self._equip_affix_ids(player):
            self._add_shield("affix_shield", int(player.get("max_hp", 100) * 0.10), 3)
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
            "poi_buff": getattr(self, "poi_buff", None),
            "p_hot": self.p_hot,
            "p_food_effects": self.p_food_effects,
            "p_shields": self.p_shields,
            "e_minions": self.e_minions,
            "e_buffs": self.e_buffs,
            "p_defending": self.p_defending,
            "e_defending": self.e_defending,
            "title_bonus": self.title_bonus,
            "mech_stacks": self.mech_stacks,
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
            # v104 M02 P2-9：断线恢复后 burst 机制（灼烧引爆/剑刃风暴/神恩护盾）与
            # 元素跃迁日志依赖 _last_player/_shifted_element，必须随战斗状态持久化
            "last_player": getattr(self, "_last_player", None),
            "shifted_element": getattr(self, "_shifted_element", None),
        }

    @classmethod
    def from_state(cls, st: dict):
        b = cls(st.get("type", "monster"), st.get("enemy", {}), st.get("title_bonus") or {}, pet=st.get("pet") or {})
        b.round = st.get("round", 0)
        b.p_buffs = st.get("p_buffs", {}) or {}
        b.poi_buff = st.get("poi_buff")
        b.p_hot = st.get("p_hot", {}) or {}
        b.p_food_effects = st.get("p_food_effects", []) or st.get("p_food_affixes", []) or []
        b.p_shields = st.get("p_shields", {}) or {}
        b.e_minions = st.get("e_minions", []) or []
        b.e_buffs = st.get("e_buffs", {}) or {}
        b.p_defending = st.get("p_defending", False)
        b.e_defending = st.get("e_defending", False)
        b.mech_stacks = st.get("mech_stacks", {}) or {}
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
        # v104 M02 P2-9：恢复 _last_player/_shifted_element；_last_player 为空保持
        # 未设置（hasattr=False，避免 battle_mech 对 None 调 _player_stats 崩溃）
        _lp = st.get("last_player")
        if _lp:
            b._last_player = _lp
        b._shifted_element = st.get("shifted_element")
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
        # v104 R3 P1-1：致命预谋被动——战斗开始 +1 连击点（刺客爆发前置）
        if k == "cp" and "致命预谋" in E.passive_skills_learned(
                player.get("class_name", ""), player.get("learned_skills", [])):
            self.resources[k] = 1

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

    def _add_shield(self, key: str, value: int, turns: int = 3):
        """v101.28d 护盾 buff 化：同源叠加盾值 + 刷新回合（取 max），异源并存各计各的回合。"""
        if value <= 0:
            return
        cur = self.p_shields.get(key)
        if cur:
            cur["value"] += value
            cur["turns"] = max(cur["turns"], turns)
        else:
            self.p_shields[key] = {"value": value, "turns": turns}

    def _do_use_item(self, payload: str, player: dict) -> list:
        """战斗中使用消耗品：恢复/增益(v61 抽公共，普通回合与额外行动共用)"""
        logs = []
        if payload.startswith("foodfx:"):
            # v101.28e 食物效果：foodfx:效果ID,效果ID（本场战斗有效，独立于装备词条）
            aids = [a for a in payload[7:].split(",") if a]
            for a in aids:
                if a not in self.p_food_effects:
                    self.p_food_effects.append(a)
            # 护盾效果特判：立即获得 10% 生命护盾（3 回合）
            if "shield" in aids:
                self._add_shield("food_shield", int(player.get("max_hp", 100) * 0.10), 3)
            from .core.food_effects import FOOD_EFFECT_NAMES
            names = [FOOD_EFFECT_NAMES.get(a, a) for a in aids]
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
        if payload.startswith("hm:"):
            # v104R3 M16 P2-3：复合药水（heal+mana）战斗内双恢复（tpl_heal_mana payload="hm:hp,mp"）
            _p = payload[3:].split(",")
            hv = int(_p[0]) if _p and _p[0] else 0
            mv = int(_p[1]) if len(_p) > 1 and _p[1] else 0
            msgs = []
            if hv > 0:
                before = player["hp"]
                player["hp"] = min(player.get("max_hp", player["hp"]), player["hp"] + hv)
                msgs.append(f"恢复 {player['hp'] - before} 点生命")
            if mv > 0:
                before = player["mp"]
                player["mp"] = min(player.get("max_mp", player["mp"]), player["mp"] + mv)
                msgs.append(f"恢复 {player['mp'] - before} 点魔力")
            logs.append(f"💊 你使用了战斗道具，{'、'.join(msgs)}！")
            return logs
        if payload.startswith("special:"):
            # v101.28f 药水特殊效果（next_atk_up/heal_up/magic_resist/thorns_pot/dodge_pot/cc_immune/execute_pot/def_down/shield）
            kind = payload[8:]
            return self._apply_potion_special(kind, player, logs)
        if payload.startswith("buff:"):
            # v54 战斗药水：effect → p_buffs 增益 3 回合
            # 9.3：支持逗号分隔复合 buff（如龙涎药剂 buff:atk_up,def_up）
            kind = payload[5:]
            _cn = {"atk_up": "攻击", "def_up": "防御", "spd_up": "速度", "crit_up": "暴击",
                   "matk_up_pot": "魔攻",
                   "food_atk_up": "攻击", "food_def_up": "防御", "food_spd_up": "速度",
                   "food_spd_up_small": "速度",
                   "food_crit_up": "暴击", "food_matk_up": "魔攻",
                   # v101.28f 药水强度分档
                   "atk_up_big": "攻击", "atk_up_small": "攻击", "spd_up_small": "速度",
                   "crit_up_small": "暴击", "crit_up_big": "暴击",
                   "matk_up": "魔攻", "matk_up_strong": "魔攻"}
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

    def _apply_potion_special(self, kind: str, player: dict, logs: list) -> list:
        """v101.28f 药水特殊效果分发（非属性 buff 类，3 回合制；next_atk_up 一次性）。"""
        if kind == "next_atk_up":
            self.p_buffs["next_atk_up"] = 1
            logs.append("⚔️ 你蓄势待发！下一次攻击+50%！")
        elif kind == "heal_up":
            self.p_buffs["heal_up"] = 3
            logs.append("✨ 治疗增幅！治疗技能效果+20%！(3 回合)")
        elif kind == "magic_resist":
            self.p_buffs["magic_resist"] = 3
            logs.append("🛡️ 魔鳞护体！受到魔法伤害－15%！(3 回合)")
        elif kind == "thorns_pot":
            self.p_buffs["thorns_pot"] = 3
            logs.append("🌵 荆棘附体！受击反弹 30% 伤害！(3 回合)")
        elif kind == "dodge_pot":
            self.p_buffs["dodge_pot"] = 3
            logs.append("💨 身法飘忽！15% 概率闪避攻击！(3 回合)")
        elif kind == "cc_immune":
            self.p_buffs["cc_immune"] = 3
            logs.append("🗿 不动如山！免疫眩晕/冻结/减速！(3 回合)")
        elif kind == "execute_pot":
            self.p_buffs["execute_pot"] = 3
            logs.append("💀 死神凝视！对生命<30%的敌人+30%伤害！(3 回合)")
        elif kind == "def_down":
            self.e_buffs["def_down"] = max(self.e_buffs.get("def_down", 0), 2)
            self.e_buffs["_armor_break_pct"] = 0.15
            logs.append("🛡️ 破甲！敌人防御下降 15%！(2 回合)")
        elif kind == "shield_small":
            gain = int(player.get("max_hp", 100) * 0.10)
            self._add_shield("potion", gain, 3)
            logs.append(f"🛡️ 岩盾护体！获得 {gain} 点护盾！(3 回合)")
        elif kind == "shield_big":
            gain = int(player.get("max_hp", 100) * 0.15)
            self._add_shield("potion", gain, 3)
            logs.append(f"🛡️ 圣盾护体！获得 {gain} 点护盾！(3 回合)")
        else:
            logs.append("🧪 你饮下了药剂！")
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
        # v104 R3 P1-4 修复：先验蓝再扣资源（原实现先扣 res_cost 后查 mp，蓝不足时怒气/连击点白扣）
        if player["mp"] < info["mp"]:
            logs.append("💙 魔力不足！")
            return logs
        # v104 R3 P1-6 修复：『消耗全部』终结技（consume_all）动态结算——资源不满也可施放，
        # 按剩余资源算倍率（power = 1 + per×当前值，满资源恰等于数据表 power），并扣光该资源
        consume_all = info.get("consume_all") or {}
        if consume_all:
            ck = consume_all.get("key", "")
            cur = self.resources.get(ck, 0)
            if cur < 1:
                rd = E.core_resource_def(player["class_name"])
                rname = rd.get("name", ck)
                logs.append(f"⚡ {rname}不足！需要至少 1 点，当前 0(『攻击』攒资源)")
                return logs
            info = dict(info)
            info["power"] = round(1.0 + float(consume_all.get("per", 0.0)) * cur, 3)
            self.resources[ck] = 0
        else:
            res_cost = info.get("res_cost") or {}
            if res_cost:
                for rk, rv in res_cost.items():
                    if not E.core_resource_spend(player["class_name"], self.resources, rv, key=rk):
                        rd = E.core_resource_def(player["class_name"])
                        rname = rd.get("name", rk)
                        cur = self.resources.get(rk, 0)
                        logs.append(f"⚡ {rname}不足！需要 {rv}，当前 {cur}(『攻击』攒资源)")
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
        st = E.player_final_stats(player.get("class_name", "战士"), player.get("level", 1),
                                  player.get("equipment", {}),
                                  player.get("class_tier", 0),
                                  player.get("attributes"),
                                  player.get("evolve_path", 0),
                                  getattr(self, "title_bonus", None) or {},
                                  player.get("race"))
        st = self._apply_buffs(st, self.p_buffs)
        # v104 M23 神龛祝福：持久 buff（stat ×1.10，5 次战斗），战斗开始时已消费 1 次
        _pb = getattr(self, "poi_buff", None)
        if _pb and _pb.get("stat") in st:
            st[_pb["stat"]] = int(st.get(_pb["stat"], 0) * float(_pb.get("mult", 1.10)))
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
        pb = E.player_passive_stats(player.get("class_name", "战士"), player.get("learned_skills", []))
        if pb.get("mp_mult", 1.0) != 1.0:
            st["max_mp"] = int(st.get("max_mp", 0) * pb["mp_mult"])
            st["mp"] = int(st.get("mp", 0) * pb["mp_mult"])
        if pb.get("spd_mult", 1.0) != 1.0:
            st["spd"] = int(st.get("spd", 0) * pb["spd_mult"])
        if pb.get("crit_add", 0.0):
            st["crit"] = min(st.get("crit", 0) + pb["crit_add"], 0.6)
        # v104 R3 P1-1：条件属性被动战斗内结算（12 章 §12.2：战意高涨/战争咆哮/死战/厚土）
        # engine.py 面板只结算无 cond 属性，条件型（rage>=5/hp 阈值/battle_start）在此按战场状态动态生效
        pm = self._passive_map(player)
        _hp_ratio = player.get("hp", 0) / max(1, player.get("max_hp", 1))
        for _pn, _ps in pm.get("stat", []):
            _st = _ps.get("stat")
            _cond = _ps.get("cond")
            _ok = False
            if _cond == "rage>=5":
                _ok = (self.resources.get("rage", 0) or 0) >= 5
            elif _cond == "hp_low_50":
                _ok = _hp_ratio < 0.5
            elif _cond == "hp_high_70":
                _ok = _hp_ratio >= 0.7
            elif _cond == "battle_start":
                _ok = getattr(self, "round", 1) <= 1
            if _ok and _st in ("atk", "def", "matk", "mdef"):
                st[_st] = int(st.get(_st, 0) * (1 + float(_ps.get("mult", 0))))
        return st

    def _passive_map(self, player: dict) -> dict:
        """v104 R3 P1-1：已学被动按 proc/stat 聚合（数据驱动，替代名字硬匹配）。
        返回 {\"proc\": {proc名: [(被动名, passive字段), ...]}, \"stat\": [(被动名, passive字段), ...]}"""
        out = {"proc": {}, "stat": []}
        cls = player.get("class_name", "")
        for ps_name in E.passive_skills_learned(cls, player.get("learned_skills", [])):
            info = E.skill_info(cls, ps_name)
            ps = (info or {}).get("passive") or {}
            if ps.get("proc"):
                out["proc"].setdefault(ps["proc"], []).append((ps_name, ps))
            elif ps.get("stat"):
                out["stat"].append((ps_name, ps))
        return out

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
        # v106 穿透：玩家物穿/固定物穿削减怪物有效防御
        _pp, _pf = self._pene_vals(st)
        dmg = E.calc_damage(st["atk"], est["def"], is_crit, pene_pct=_pp, pene_flat=_pf)
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
        # v105 怪物闪避：闪避成功跳过本次伤害结算/符文特效/词条触发/资源获取
        if not self._monster_dodge_check(logs):
            self._damage_enemy(dmg, logs)
            tag = " 💥暴击" if is_crit else ""
            if affix_tags:
                tag += " " + "·".join(affix_tags)
            logs.append(f"你{_basic_attack_verb(player)}，造成 {dmg} 点伤害！{tag}")
            # v34 符文攻击特效（灼烧/冻结/吸血/连锁/虚弱/破魔）
            self._apply_enchant_attack(effs, dmg, st, player, logs)
            # 阶段八：攻击命中后词条触发（流血/破甲/连击/元素附加等）
            self._affix_on_hit(player, dmg, logs)
            self._food_on_hit(player, dmg, logs)
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
        # v104 R3 P1-1：斗气凝聚（气获取+1）/ 狂战之魂·斗气之心（资源获取+1）被动加成
        pm = self._passive_map(player)
        for _pn, _ps in pm["stat"]:
            if _ps.get("stat") == "chi_gain" and k == "chi":
                gain += int(_ps.get("mult", 1))
        for _pn, _ps in pm["proc"].get("res_gain_bonus", []):
            if k in ("rage", "chi", "cp", "faith"):
                gain += 1
        # v104 R3 P1-1：神圣狂热——攻击获得信仰 +2（牧师攻击型分支）
        for _pn, _ps in pm["proc"].get("attack_res", []):
            if k == _ps.get("res", "faith") and _ps.get("gain"):
                gain += int(_ps.get("gain", 0))
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
                self._damage_enemy(cd, logs)
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
        # v101.28e 食物效果独立成体系，不再合并进装备词条（p_food_effects 由 food 挂点消费）
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
            mult *= RACE_BERSERK_MULT
            tags.append("🔥无畏")
        tm = rt.get("timid_hp")
        if tm and ratio < tm:
            mult *= RACE_TIMID_MULT
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
        e = self.enemy
        hp_ratio = e.get("hp", 0) / max(1, e.get("max_hp", 1))
        if "圣光" in s5names and any(k in ename for k in ("暗", "影", "亡", "鬼", "骨", "骷髅")):
            mult *= 1.10
            tags.append("✨圣光克暗")
        if "龙脊" in s5names and "龙" in ename:
            mult *= 1.10
            tags.append("🐉龙息追猎")
        if "地底" in s5names and "深渊" in ename:
            mult *= 1.10
            tags.append("🕳️深渊共鸣")
        # v104 M07 修复 P1/P2：灰烬守卫（残血增攻）与迷雾（沼泽/毒腐系增伤）5 件效果
        p_ratio = player.get("hp", 0) / max(1, player.get("max_hp", 1))
        if "灰烬守卫" in s5names and p_ratio < 0.30:
            mult *= 1.20
            tags.append("🔥灰烬之怒")
        if "迷雾" in s5names and any(k in ename for k in ("沼泽", "毒", "腐", "瘴")):
            mult *= 1.10
            tags.append("🌫️迷雾侵染")
        if not ids:
            # v101.28e/f：无词条时不能提前返回——食物/药水倍率（处决/精准/狂怒/死神）仍要结算
            return self._extra_dmg_mult(hp_ratio, mult, tags)
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
        # v101.28e/f：食物+药水额外倍率（处决/精准/狂怒/死神），与词条是否为空无关
        mult, tags = self._extra_dmg_mult(hp_ratio, mult, tags)
        return mult, tags

    def _extra_dmg_mult(self, hp_ratio: float, mult: float, tags: list) -> tuple:
        """v101.28e/f 食物效果 + 药水特殊效果的伤害倍率（独立于装备词条）。

        食物：处决（<30% +30%）/ 精准（+10%）。
        药水：死神药剂（<30% +30%）/ 狂怒药剂（下次攻击 +50%，一次性消耗）。
        龙语印记：每层 +2% 伤害（v104 移入此处——此前 _affix_dmg_mult 在无词条时提前
        return 会漏结算该倍率，有词条路径在调用后单独结算，两路径行为不一致）。
        """
        foods = getattr(self, "p_food_effects", []) or []
        if "execute" in foods and hp_ratio < 0.30:
            mult *= 1.30
            tags.append("💀处决")
        if "precise" in foods:
            mult *= 1.10
            tags.append("🎯精准")
        if self.p_buffs.get("execute_pot") and hp_ratio < 0.30:
            mult *= 1.30
            tags.append("💀处决")
        if self.p_buffs.get("next_atk_up"):
            mult *= 1.50
            del self.p_buffs["next_atk_up"]
            tags.append("⚔️狂怒")
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

    # ---------------- v101.28e 食物效果挂点（独立于装备词条） ----------------
    def _food_on_hit(self, player: dict, dmg: int, logs: list):
        """攻击命中后料理效果触发（吸血/流血/破甲/连击/龙语印记/元素/贯穿/蓄力）。"""
        if not self.p_food_effects or self.enemy.get("hp", 0) <= 0:
            return
        from .core.food_effects import FOOD_HIT_EFFECTS
        for key in self.p_food_effects:
            fn = FOOD_HIT_EFFECTS.get(key)
            if fn:
                fn(self, player, dmg, logs)

    def _food_on_taken(self, player: dict, dmg: int, logs: list) -> int:
        """受击料理效果（反击/反伤）。返回结算后伤害（当前食物效果不改减伤，透传）。"""
        if not self.p_food_effects:
            return dmg
        from .core.food_effects import FOOD_TAKEN_EFFECTS
        ctx = {"dmg": dmg, "out": dmg}
        for key in self.p_food_effects:
            fn = FOOD_TAKEN_EFFECTS.get(key)
            if fn:
                fn(self, player, ctx, logs)
        return ctx["out"]

    def _food_turn_start(self, player: dict, logs: list):
        """回合开始料理效果（回春/冥想/晨曦祝福）。"""
        if not self.p_food_effects:
            return
        from .core.food_effects import FOOD_TURN_START_EFFECTS
        for key in self.p_food_effects:
            fn = FOOD_TURN_START_EFFECTS.get(key)
            if fn:
                fn(self, player, logs)


    def _skill_heal(self, st, skill_name, info, player, lv, mech, mval, p_mech, logs):
        """治疗分支（v103.6 从 _player_skill 拆出）"""
        # v32 条件转化：治疗技能也吃战场状态（如神谕者自身低血时治疗量提升）
        cond_mult = self._cond_mult(info, player, lv)
        # v104 R3 P2-18：条件满足即显示标签（含 mult=1.0 的纯条件技，如符文护体"魔能≥3"）
        cond_label = info.get("cond", {}).get("label", "") if self._cond_active(info, player) else ""
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
        # v104 R3 P1-1：神圣恩典（治疗+10%）/ 圣祷（20% 概率治疗+30%）
        _pm = self._passive_map(player)
        for _pn, _ps in _pm["stat"]:
            if _ps.get("stat") == "heal":
                heal = int(heal * (1 + float(_ps.get("mult", 0))))
        for _pn, _ps in _pm["proc"].get("heal_crit", []):
            if random.random() < float(_ps.get("chance", 0.2)):
                heal = int(heal * (1 + float(_ps.get("mult", 0))))
                logs.append(f"✨ {_pn}：治疗暴击！治疗量提升！")
        # 阶段八：圣光套 2 件效果——治疗 +10%
        if E.has_set(player.get("equipment", {}), "圣光套"):
            heal = int(heal * 1.10)
        # v101.28f 圣光药剂：治疗技能效果 +20%（3 回合）
        if self.p_buffs.get("heal_up"):
            heal = int(heal * 1.20)
        # 阶段九：种族受疗天赋（人类圣光亲和 +10% / 龙裔孤傲之血 -10%）
        hr = self._race_bonus(player).get("heal_received", 0) or 0
        if hr:
            heal = max(1, int(heal * (1 + hr)))
            if hr > 0:
                logs.append(f"✨ 圣光亲和：治疗效果 +{int(hr*100)}%！")
            else:
                logs.append(f"🐉 孤傲之血：治疗效果 -{int(-hr*100)}%！")
        hp_before = player.get("hp", 0)
        player["hp"] = min(player.get("max_hp", player["hp"]), hp_before + heal)
        # v104 M02 P2-4：庇护之光按“真实治疗溢出量”结算（此前 clamp 后按
        # hp-(max_hp-hp) 计算，任意治疗补满都误给 ≈20% max_hp 护盾）
        if "庇护之光" in pv:
            overflow = hp_before + heal - player.get("max_hp", player["hp"])
            if overflow > 0:
                shield_gain = int(overflow * 0.20)
                self._add_shield("overflow", shield_gain, 2)
                logs.append(f"🛡️ 庇护之光：治疗溢出转化为 {shield_gain} 点护盾！")
        if player.get("hp", 0) >= player.get("max_hp", player["hp"]) and mech == "bless":
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
            elif eff == "stealth":
                # v104 R3 P1-10：潜行状态实装——下次攻击必暴（desc 对齐），暴击率 +20% 持续回合
                self.p_buffs["stealth"] = 1
                self.p_buffs["crit_up"] = E.skill_buff_turns(lv)
            elif eff == "mark":
                # v104 M02 P1-2：死亡标记是目标易伤——挂敌方侧 e_buffs（_apply_mark 只认 e_buffs）
                self.e_buffs["mark"] = E.skill_buff_turns(lv)
            elif eff == "shield_all":
                # v104 M02 P1-4：全队护盾施放者自身同样获得（与 instance.py 广播口径一致：matk 20% 3 回合）
                st2 = self._player_stats(player)
                base = (st2 or {}).get("matk") or (st2 or {}).get("atk") or 0
                self._add_shield("team_bless", int(base * 0.20), 3)
            else:
                # v104 M02 P1-4：团队增益 effect=xx_all 映射为施放者自身有效键（def_all→def_up 等）
                key = TEAM_BUFF_KEYS.get(eff, eff)
                # v104 M02 P2-11：同 effect 不同技能 buff 覆盖取高（与药水路径一致）
                self.p_buffs[key] = max(self.p_buffs.get(key, 0), E.skill_buff_turns(lv))
        # v30 条件转化：增益型引爆也吃战场状态（如元素狂暴残血引爆）
        cond_mult = self._cond_mult(info, player, lv)
        # v104 R3 P2-18：条件满足即显示标签（含 mult=1.0 的纯条件技）
        cond_label = info.get("cond", {}).get("label", "") if self._cond_active(info, player) else ""
        # v29：effect 型机制（引爆/转化类增益技能）
        if eff == "burn_burst":
            n = p_mech.get("burn", 0)
            st2 = self._player_stats(player)
            if st2 and n:
                d = int(st2["matk"] * 0.30 * n * cond_mult)
                self._damage_enemy(d, logs)
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
                self._add_shield("bless", shield, 2)
                logs.append(f"✨ 神恩护盾！{n} 层转化为 {shield} 点护盾")
            p_mech["bless"] = 0
        self._apply_mech_gain(mech, mval, p_mech, logs, skill_name)
        logs.append(f"你施展【{skill_name}】！")
        if eff == "element_shift" and getattr(self, "_shifted_element", None):
            logs.append(f"✦ 元素跃迁！切换到 {E.ELEMENT_CN.get(self._shifted_element, '?')}系(下次元素技能伤害+20%)")
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
        # v104 R3 P1-1：猎手本能——对标记目标暴击 +10%（e_buffs["mark"] 为目标易伤标记）
        if "mark" in self.e_buffs:
            for _pn, _ps in self._passive_map(player)["stat"]:
                if _ps.get("stat") == "crit_mark" and random.random() < float(_ps.get("mult", 0.1)):
                    is_crit = True
        # v104 R3 P1-10：潜行状态（stealth）——下次攻击必暴，攻击后消耗
        if self.p_buffs.get("stealth"):
            is_crit = True
            del self.p_buffs["stealth"]
            logs.append("🌙 潜行生效！本次攻击必定暴击！")
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
        # v104 R3 P2-18：条件满足即显示标签（含 mult=1.0 的纯条件技）
        cond_label = info.get("cond", {}).get("label", "") if self._cond_active(info, player) else ""
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
        # 技能元素（"current"=当前元素亲和系）——提前解析供 proc 型被动判定
        element = info.get("element", "")
        if element == "current":
            element = self.resources.get("element", "fire")
        # v104 R3 P1-1：分支/基础 proc 型被动伤害挂点（数据驱动：万象亲和/元素之心/毒师/淬毒之心/
        # 追猎者/猎魔之眼/奥术之心/武技/疾驰/审判之心/暗影之心/暗影之舞/元素共鸣）
        _pm = self._passive_map(player)
        _procs = _pm["proc"]
        # 元素伤害类（元素系技能）
        for _pn, _ps in _procs.get("element_dmg", []):
            if element and E.ELEMENT_MARKS.get(element):
                passive_bonus *= (1 + float(_ps.get("mult", 0)))
        # 毒系技能伤害（毒刃/毒爆等 mech=poison 或名字含毒）
        for _pn, _ps in _procs.get("poison_dmg", []):
            if mech == "poison" or "毒" in (skill_name or ""):
                passive_bonus *= (1 + float(_ps.get("mult", 0)))
        # 对标记目标伤害（追猎者/猎魔之眼：e_buffs["mark"] 为目标易伤标记）
        for _pn, _ps in _procs.get("mark_dmg", []):
            if "mark" in self.e_buffs:
                passive_bonus *= (1 + float(_ps.get("mult", 0)))
        # 奥术系伤害（奥术之心）
        for _pn, _ps in _procs.get("arcane_dmg", []):
            if mech == "arcane":
                passive_bonus *= (1 + float(_ps.get("mult", 0)))
        # 连招技能伤害（武技）
        for _pn, _ps in _procs.get("combo_dmg", []):
            if info.get("combo"):
                passive_bonus *= (1 + float(_ps.get("mult", 0)))
        # 速度优势增伤（疾驰）
        for _pn, _ps in _procs.get("speed_dmg", []):
            if st.get("spd", 0) > est.get("spd", 0):
                passive_bonus *= (1 + float(_ps.get("mult", 0)))
        # 机制型 stat 被动（审判之心 judge / 暗影之心 shadow）：对应 mech 技能伤害加成
        for _pn, _ps in _pm["stat"]:
            if _ps.get("stat") == "judge" and mech == "judge":
                passive_bonus *= (1 + float(_ps.get("mult", 0)))
            elif _ps.get("stat") == "shadow" and mech == "shadow":
                passive_bonus *= (1 + float(_ps.get("mult", 0)))
            elif _ps.get("stat") == "stealth_crit_dmg" and self.p_buffs.get("stealth"):
                passive_bonus *= (1 + float(_ps.get("mult", 0)))
        # v104 R3 P1-1：复仇被动消费——受击后下次攻击 +30%（挨打反打，一次后清除）
        if self.p_buffs.get("revenge_atk"):
            for _pn, _ps in _procs.get("counter", []):
                passive_bonus *= float(_ps.get("mult", 1.3))
            del self.p_buffs["revenge_atk"]
        # 元素反应增伤（元素共鸣：触发反应时 +15%）
        for _pn, _ps in _procs.get("reaction", []):
            self._elem_reaction_boost = float(_ps.get("mult", 1.15))
        # 元素反应：当前系 × 目标印记（技能带 element 字段时判定；"current"=当前元素亲和系）
        reaction_mult = 1.0
        reaction_log = ""
        if element and E.ELEMENT_MARKS.get(element):
            marks = {k: v for k, v in self.e_buffs.items() if k in E.ELEMENT_MARKS.values()}
            r = E.element_reaction(element, marks)
            if r:
                reaction_mult = r["mult"]
                # v104 R3 P1-1：元素共鸣被动——元素反应伤害 +15%（在基础反应倍率上叠加）
                if getattr(self, "_elem_reaction_boost", 1.0) > 1.0:
                    reaction_mult *= self._elem_reaction_boost
                    self._elem_reaction_boost = 1.0
                reaction_log = f"💥{r['name']}！"
                # 超载：额外全体伤害（对非当前目标模拟为追加单体伤害的 20%）
                if r["extra"] == "aoe":
                    aoe_dmg = int(st["matk"] * 1.2 * reaction_mult)
                    self._damage_enemy(aoe_dmg, logs)
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
        # v106 穿透：物理技能用物穿/固定物穿，魔法技能用法穿/固定法穿
        _pp_phys, _pf_phys = self._pene_vals(st, magic=False)
        _pp_magi, _pf_magi = self._pene_vals(st, magic=True)
        for _ in range(multi):
            if kind == "物理":
                if info.get("pierce"):
                    dmg_i = E.calc_damage(int(st["atk"] * info["power"] * pmult), 0, is_crit, pierce=True)
                else:
                    dmg_i = E.calc_damage(int(st["atk"] * info["power"] * pmult), est["def"], is_crit,
                                          pene_pct=_pp_phys, pene_flat=_pf_phys)
                # v87 魔剑士·混合伤害：magic_add 追加魔法段（魔能斩 130% 物 + 30% 魔）
                if info.get("magic_add"):
                    dmg_m = E.calc_damage(int(st["matk"] * info["magic_add"] * pmult), est["mdef"], is_crit,
                                          pene_pct=_pp_magi, pene_flat=_pf_magi)
                    dmg_i += dmg_m
            else:
                dmg_i = E.calc_damage(int(st["matk"] * info["power"] * pmult), est["mdef"], is_crit,
                                      pene_pct=_pp_magi, pene_flat=_pf_magi)
            # v87 魔剑士·魔力涌动：消耗 buff，本次攻击追加 80% 魔法伤害
            if self.p_buffs.get("spellblade_surge"):
                surge_dmg = E.calc_damage(int(st["matk"] * 0.80 * pmult), est["mdef"], is_crit,
                                          pene_pct=_pp_magi, pene_flat=_pf_magi)
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
        # v105 怪物闪避：技能主伤害判定一次（闪避成功 total 归零，日志自然显示 0 伤害）
        if self._monster_dodge_check(logs):
            total = 0
        else:
            self._damage_enemy(total, logs)
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
        elif cond_mult == 1.0 and cond_label:
            # v104 R3 P2-18：mult=1.0 的纯条件技（如符文护体"魔能≥3"）条件满足时也提示
            tags.append(f"⚔️{cond_label}")
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
            extra_layers = 1
            # v104 R3 P1-1：追踪印记——30% 概率额外叠 1 印记（游侠基础被动）
            for _pn, _ps in _procs.get("mark_extra", []):
                if random.random() < float(_ps.get("chance", 0.3)):
                    extra_layers += 1
            E.element_mark_apply(self.e_buffs, element, extra_layers)
            # v104 R3 P1-1：寒霜亲和——冰系技能命中附带减速 2 回合
            if element == "ice":
                for _pn, _ps in _procs.get("ice_slow", []):
                    self.e_buffs["spd_down"] = max(self.e_buffs.get("spd_down", 0), 2)
                    logs.append("❄️ 寒霜亲和：敌人被减速！")
            if self.resources.get("element") is not None:
                self.resources["element"] = element
        # v2.0 连招序列：拳师 combo 字段推进（拳→踢→掌 三连触发额外效果）
        combo_tag = info.get("combo", "")
        if combo_tag:
            combo_full = self._combo_push(combo_tag)
            if combo_full:
                combo_bonus = int(total * 0.30)
                # v104 R3 P1-1：连招精通——三连击破追加伤害提升 50%（0.30 → 0.45）
                for _pn, _ps in _procs.get("combo_boost", []):
                    combo_bonus = int(total * 0.45)
                    break
                self._damage_enemy(combo_bonus, logs)
                logs.append(f"🥊 三连击破！拳-踢-掌完美连招，追加 {combo_bonus} 点伤害！(下次斗气技+20%)")
                self.resources["combo_ready"] = 1
            else:
                logs.append(f"🥊 连招 {self._combo_label()}")
        # v34 符文攻击特效（灼烧/冻结/吸血/连锁/虚弱）
        self._apply_enchant_attack(effs, total, st, player, logs)
        # 阶段八：攻击命中后词条触发（流血/破甲/连击/元素附加等）
        self._affix_on_hit(player, total, logs)
        # v101.28e 攻击命中后料理效果触发
        self._food_on_hit(player, total, logs)

        # ---- 分支机制结算（v29） ----
        self._last_player = player
        self._apply_mech_effect(mech, mval, p_mech, total, logs, skill_name, is_crit)
        # v63 额外控制效果（cc 字段，独立于 mech 叠层）：眩晕/沉默/净化
        cc = info.get("cc")
        if cc and cc in ("stun", "silence", "cleanse"):
            self._apply_mech_effect(cc, 1, p_mech, total, logs, skill_name, is_crit)

        # ---- 技能特效（v9 落地）----
        # v2.0：技能名硬编码特效已废弃（12 章技能全数据驱动，mech/effect/cond 在 _apply_mech_effect 覆盖）
        # v104 R3 P2-10 修复：吸血改按 lifesteal 数据字段触发（原只认 effect=="lifesteal"，
        # 全表无技能带此 effect → 嗜血斩 lifesteal:0.25 实机 0 吸血）；数值由 skill_lifesteal_pct 读字段
        if info.get("lifesteal"):
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
        （22 种条件类型；未知 type 安全降级 1.0，与旧 elif 链兜底一致）
        """
        cond = info.get("cond")
        if not cond:
            return 1.0
        from .core.battle_conds import COND_CHECKS
        check = COND_CHECKS.get(cond.get("type"))
        if check and check(self, player, cond):
            return E.skill_cond_mult(cond, lv, info)
        return 1.0

    def _cond_active(self, info: dict, player: dict) -> bool:
        """v104 R3 P2-18：条件是否当前满足（与 _cond_mult 同判定，不关心倍率数值）。
        用于条件标签显示——mult=1.0 的纯条件技（如符文护体"魔能≥3"）此前因
        cond_mult>1.0 判定永不显示标签，玩家看不到条件存在。"""
        cond = info.get("cond")
        if not cond:
            return False
        from .core.battle_conds import COND_CHECKS
        check = COND_CHECKS.get(cond.get("type"))
        return bool(check and check(self, player, cond))

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
                    # R3 P2-3：反伤保底 1 HP（永不致死）——设计取舍：反伤是"代价"不是
                    # "处决"，避免残血玩家被反弹伤害补刀造成挫败；04 章机制表仅写"反弹 15%"
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
        # v101.28l #438：援军出手（召唤的爪牙每回合攻击一次，独立于 Boss 行动）
        minion_dmg = 0
        if self.e_minions:
            _pst0 = self._player_stats(player)
            for m in list(self.e_minions):
                md = E.calc_damage(int(m.get("atk", 0)), _pst0["def"])
                minion_dmg += md
                logs.append(f"👹 援军【{m['name']}】扑向你，造成 {md} 点伤害！")
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
                    return logs, minion_dmg
                power = sinfo.get("power", 1.0)
                # v104 M02 P2-10：怪物技能暴击按自身 crit 判定（此前固定 MON_SKILL_CRIT 0.1，高 crit 怪技能不暴击）
                # v106 韧性：被暴击率 × (1 - 玩家韧性)
                is_crit = random.random() < est.get("crit", C.MON_SKILL_CRIT) * self._tenacity_mult(pst)
                if kind == "物理":
                    _pp, _pf = self._pene_vals(est)
                    dmg = E.calc_damage(int(est["atk"] * power), pst["def"], is_crit, pene_pct=_pp, pene_flat=_pf)
                else:
                    _pp, _pf = self._pene_vals(est, magic=True)
                    dmg = E.calc_damage(int(est["matk"] * power), pst["mdef"], is_crit, pene_pct=_pp, pene_flat=_pf)
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
                    # v101.28f 龙鳞药剂：魔法伤害 -15%（3 回合）
                    if self.p_buffs.get("magic_resist"):
                        red = max(1, int(dmg * 0.15))
                        dmg = max(1, dmg - red)
                        logs.append(f"🛡️ 魔鳞护体，减免 {red} 点魔法伤害！")
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
                return logs, dmg + minion_dmg
        # v104 M02 P2：怪物普攻按 crit 属性判定暴击（此前完全忽略 est["crit"]，与玩家/PVP 同款逻辑）
        # v106 韧性：被暴击率 × (1 - 玩家韧性)；穿透：怪物物穿削减玩家防御
        is_crit = random.random() < est.get("crit", 0.05) * self._tenacity_mult(pst)
        _pp, _pf = self._pene_vals(est)
        dmg = E.calc_damage(est["atk"], pst["def"], is_crit, pene_pct=_pp, pene_flat=_pf)
        # 阶段九：种族受击天赋（石肤 物理伤害-10%，普攻段）
        rt = self._race_bonus(player)
        pr = rt.get("phys_reduce", 0) or 0
        if pr:
            red = max(1, int(dmg * pr))
            dmg = max(1, dmg - red)
            logs.append(f"🪨 石肤护体，减免 {red} 点物理伤害！")
        logs.append(f"【{self.enemy['name']}】攻击你，造成 {dmg} 点伤害！" + (" 💥暴击！" if is_crit else ""))
        return logs, dmg + minion_dmg

    def _pvp_enemy_turn(self, player: dict) -> tuple:
        """PVP：敌方玩家行动(v9.2 启用；先实现 AI 普攻)"""
        est = self._enemy_stats()
        pst = self._player_stats(player)
        logs = []
        # v106 韧性：被暴击率 × (1 - 玩家韧性)；穿透：PVP 敌方玩家快照的物穿生效（双向）
        is_crit = random.random() < est.get("crit", 0.05) * self._tenacity_mult(pst)
        _pp, _pf = self._pene_vals(est)
        dmg = E.calc_damage(est["atk"], pst["def"], is_crit, pene_pct=_pp, pene_flat=_pf)
        logs.append(f"【{self.enemy['name']}】向你发起攻击，造成 {dmg} 点伤害！" + (" 💥暴击！" if is_crit else ""))
        return logs, dmg

    # ---------------- 状态修正 ----------------
    def _apply_buffs(self, st: dict, buffs: dict) -> dict:
        st = dict(st)
        for eff, turns in buffs.items():
            if eff in BUFF_MULT:
                attr, val = BUFF_MULT[eff]
                # v104 M17 P2-5：宠物 buff（buff_atk/crit_up）实读 PET_POOL skill_value，
                # 覆盖 BUFF_MULT 常量（此前日志 25% 实际 30%，数据层承诺"加宠物=加一行"失效）
                if attr in ("atk", "crit"):
                    _pv = getattr(self, "_pet_buff_vals", {}).get(attr)
                    if _pv is not None:
                        val = 1.0 + _pv if attr == "atk" else _pv
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
            self._damage_enemy(dmg, logs)
            logs.append(f"🐾 {pname}的【{sname}】造成 {dmg} 点伤害！" + (f"「{line}」" if line else ""))
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
            self._damage_enemy(dmg, logs)
            logs.append(f"🐾 {pname}的【{sname}】造成 {dmg} 点伤害！" + (f"「{line}」" if line else ""))
            if self._enemy_dead():
                self.result = "victory"
                logs.append(f"🎉 你击败了【{self.enemy.get('name', '敌人')}】！(宠物击杀)")
        elif stype == "heal_pct":
            if player.get("hp", 0) < player.get("max_hp", 1):
                heal = int(player.get("max_hp", player.get("hp", 1)) * pdef["skill_value"])
                player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
                logs.append(f"🐾 {pname}的【{sname}】为你回复了 {heal} 点生命！" + (f"「{line}」" if line else ""))
        elif stype == "buff_atk":
            self.p_buffs["atk_up"] = max(int(self.p_buffs.get("atk_up", 0) or 0), 2)
            # v104 M17 P2-5：buff 数值实读 PET_POOL skill_value（_apply_buffs 用 _pet_buff_vals 覆盖常量 1.30）
            _pbv = getattr(self, "_pet_buff_vals", {})
            _pbv["atk"] = max(float(_pbv.get("atk", 0.0) or 0.0), float(pdef["skill_value"]))
            self._pet_buff_vals = _pbv
            # v104 M17 P3：日志百分比读 skill_value 动态拼接（不再硬编码 30%）
            logs.append(f"🐾 {pname}的【{sname}】为你加持攻击强化！(攻击 +{int(pdef['skill_value'] * 100)}%，2 回合)" + (f"「{line}」" if line else ""))
        elif stype == "crit_up":
            self.p_buffs["crit_up"] = max(int(self.p_buffs.get("crit_up", 0) or 0), 2)
            # v104 M17 P2-5：同上——暴击加成实读 skill_value（覆盖常量 0.20）
            _pbv = getattr(self, "_pet_buff_vals", {})
            _pbv["crit"] = max(float(_pbv.get("crit", 0.0) or 0.0), float(pdef["skill_value"]))
            self._pet_buff_vals = _pbv
            # v104 M17 P3：日志百分比读 skill_value 动态拼接（不再硬编码 20%）
            logs.append(f"🐾 {pname}的【{sname}】为你加持暴击提升！(暴击 +{int(pdef['skill_value'] * 100)}%，2 回合)" + (f"「{line}」" if line else ""))
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
            self._damage_enemy(p, logs)
            logs.append(f"🔥 【{self.enemy['name']}】被灼烧，损失 {p} 点生命！")
            if self._enemy_dead():
                self.result = "victory"
                logs.append(f"🎉 你击败了【{self.enemy['name']}】！(灼烧致死)")
        # v29 毒层：每层 3% 生命（优先战斗层数；老毒箭仍用 e_buffs 布尔标记）
        mech = self.mech_stacks
        poison_n = int(mech.get("poison", 0) or 0)
        # v104 R3 P1-1：剧毒亲和——毒层每层伤害 +20%
        _poison_mult = 1.0
        for _pn, _ps in self._passive_map(player)["proc"].get("poison", []):
            _poison_mult *= float(_ps.get("mult", 1.2))
        if poison_n > 0:
            p = int(self.enemy.get("max_hp", 1) * POISON_PCT * poison_n * _poison_mult)
            self._damage_enemy(p, logs)
            logs.append(f"☠️ 【{self.enemy['name']}】中毒发作，损失 {p} 点生命！")
            if self._enemy_dead():
                self.result = "victory"
                logs.append(f"🎉 你击败了【{self.enemy['name']}】！(毒发身亡)")
        elif "poison" in self.e_buffs:
            p = int(self.enemy.get("max_hp", 1) * POISON_PCT * _poison_mult)
            self._damage_enemy(p, logs)
            logs.append(f"☠️ 【{self.enemy['name']}】中毒发作，损失 {p} 点生命！")
            if self._enemy_dead():
                self.result = "victory"
                logs.append(f"🎉 你击败了【{self.enemy['name']}】！(毒发身亡)")
        # 阶段八：流血词条（每回合 5% 生命，e_buffs["bleed"] = 剩余回合数，回合递减交给 _end_round）
        bleed_n = int(self.e_buffs.get("bleed", 0) or 0)
        if bleed_n > 0:
            p = int(self.enemy.get("max_hp", 1) * 0.05)
            self._damage_enemy(p, logs)
            logs.append(f"🩸 【{self.enemy['name']}】流血不止，损失 {p} 点生命！")
            if self._enemy_dead():
                self.result = "victory"
                logs.append(f"🎉 你击败了【{self.enemy['name']}】！(失血过多)")
        # 阶段八：词条回合开始回复（回春/冥想/晨曦祝福）
        self._affix_turn_start(player, logs)
        self._food_turn_start(player, logs)
        # 圣光/永恒套：每回合开始回复生命
        for eff in E.set_bonus_4(player.get("equipment", {})):
            if eff in ("regen", "regen_strong") and player.get("hp", 0) < player.get("max_hp", 1):
                pct = 0.05 if eff == "regen" else 0.08
                heal = int(player.get("max_hp", player.get("hp", 1)) * pct)
                player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
                logs.append(f"✨ 套装祝福生效，你回复了 {heal} 点生命！")
                break
        # v104 M07 修复 P1：星尘套 5 件——夜间每回合回蓝 5%（10 章五节；夜间 = 19:00-06:00 服务器本地时间）
        if "星尘" in "|".join(self._set_bonus_5(player)) and player.get("mp", 0) < player.get("max_mp", 1):
            _hour = time.localtime().tm_hour
            if _hour >= 19 or _hour < 6:
                gain = int(player.get("max_mp", player.get("mp", 1)) * 0.05)
                player["mp"] = min(player.get("max_mp", player.get("mp", 1)), player.get("mp", 0) + gain)
                logs.append(f"🌙 星尘祝福：夜风拂过，你回复了 {gain} 点魔力！({player['mp']}/{player.get('max_mp', '?')})")
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
        # v104 R3 P1-1：生命之泉——全队每回合回血 5%（单人战斗=自身，副本由 instance 广播）
        for _pn, _ps in self._passive_map(player)["proc"].get("team_regen", []):
            if player.get("hp", 0) < player.get("max_hp", 1):
                heal = int(player.get("max_hp", player.get("hp", 1)) * float(_ps.get("mult", 0.05)))
                player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
                logs.append(f"💧 {_pn}：生命之泉涌动，你回复了 {heal} 点生命！")
            break
        # v2.1 被动·奥术直觉：每回合开始奥术充能 +1（奥术法师自动蓄能）
        if "奥术直觉" in E.passive_skills_learned(player["class_name"], player.get("learned_skills", [])):
            self.mech_stacks["arcane"] = E.mech_stack_gain("arcane", self.mech_stacks, 1)
            logs.append(f"📖 奥术直觉：充能自动+1(当前 {self.mech_stacks['arcane']} 层)")
        # v87 被动·符文刻印：魔剑士每回合自动获得 1 层魔能（上限 5）
        if "符文刻印" in E.passive_skills_learned(player["class_name"], player.get("learned_skills", [])):
            self.mech_stacks["spellblade"] = E.mech_stack_gain("spellblade", self.mech_stacks, 1)
            logs.append(f"⚔️ 符文刻印：魔能自动+1(当前 {self.mech_stacks['spellblade']} 层)")
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
        # v101.28d 护盾回合递减：各来源独立计时，到 0 消失
        for key in list(self.p_shields):
            self.p_shields[key]["turns"] -= 1
            if self.p_shields[key]["turns"] <= 0:
                del self.p_shields[key]
        self._tick_cooldowns()

    def _attacker_precise(self) -> float:
        """攻击方精准（v105 精准体系）：PVP 时攻击方是对方玩家快照（用 _player_stats 计算装备/词条精准），
        PVE 怪物无精准=0（玩家闪避不被削减）。任何异常按 0 处理。"""
        try:
            en = self.enemy or {}
            if self.mode == "pvp" and en.get("equipment"):
                return float(self._player_stats(en).get("precise", 0) or 0)
            return float(en.get("precise", 0) or 0)
        except Exception:
            return 0.0

    def _pene_vals(self, st: dict, magic: bool = False) -> tuple:
        """v106 穿透取值：返回 (百分比穿透, 固定穿透)。
        magic=True 取法穿对 mdef，否则取物穿对 def。百分比 cap 0.6（聚合层已 cap，这里兜底防脏值）。"""
        try:
            if magic:
                return (min(float(st.get("pene_magi", 0) or 0), 0.6),
                        max(int(st.get("pene_mflat", 0) or 0), 0))
            return (min(float(st.get("pene_phys", 0) or 0), 0.6),
                    max(int(st.get("pene_flat", 0) or 0), 0))
        except Exception:
            return (0.0, 0)

    @staticmethod
    def _tenacity_mult(pst: dict) -> float:
        """v106 韧性：被暴击率 × (1 - 韧性)，韧性 cap 50%"""
        try:
            return 1.0 - min(float(pst.get("tenacity", 0) or 0), 0.5)
        except Exception:
            return 1.0

    def _monster_dodge_check(self, logs: list) -> bool:
        """v105 怪物闪避判定：怪物闪避率 × (1 - 我方精准)（精准上限 60%），闪避率上限 30%。
        命中判定成功追加闪避日志并返回 True（调用方跳过本次伤害结算）。"""
        try:
            mon_dodge = min(float((self.enemy or {}).get("dodge", 0) or 0), 0.30)
            if mon_dodge <= 0:
                return False
            my_hit = 0.0
            try:
                my_hit = min(float(self._player_stats(self.player).get("precise", 0) or 0), 0.60)
            except Exception:
                my_hit = 0.0
            eff = mon_dodge * (1 - my_hit)
            if eff > 0 and random.random() < eff:
                logs.append(f"💨 {self.enemy.get('name', '怪物')} 闪避了攻击！")
                return True
        except Exception:
            pass
        return False

    def _damage_enemy(self, dmg: int, logs: list) -> int:
        """v101.28l #438：真召唤援军——伤害先扣援军（挡刀），援军死光才扣 Boss。
        返回对 Boss 实际造成的伤害（援军吸收部分不计入）。"""
        if not self.e_minions or dmg <= 0:
            self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - dmg)
            return dmg
        m = self.e_minions[0]
        absorb = min(m["hp"], dmg)
        m["hp"] -= absorb
        rest = dmg - absorb
        if rest > 0:
            self.enemy["hp"] = max(0, self.enemy.get("hp", 0) - rest)
        logs.append(f"🛡️ 援军【{m['name']}】挡下了 {absorb} 点伤害！")
        if m["hp"] <= 0:
            self.e_minions.pop(0)
            logs.append(f"💥 援军【{m['name']}】被击倒了！")
        return rest

    def _summon_minions(self, n: int = 1) -> list:
        """v101.28l #438：生成援军实体（血量=Boss 20%、攻击=Boss 40%）"""
        e = self.enemy or {}
        created = []
        for i in range(n):
            m = {
                "name": f"{e.get('name', '首领')}的爪牙",
                "hp": int(e.get("max_hp", 1) * 0.20),
                "max_hp": int(e.get("max_hp", 1) * 0.20),
                "atk": int(e.get("atk", 0) * 0.40),
                "matk": int(e.get("matk", 0) * 0.40),
            }
            self.e_minions.append(m)
            created.append(m)
        return created

    def _damage_player(self, player: dict, dmg: int, logs: list):
        if dmg <= 0:
            return
        # 24 章宠物技能·影袭：替主人挡一次攻击（主动保护优先于自身闪避，拦截后直接结束本次伤害）
        dmg = self._pet_block_check(dmg, logs)
        if dmg <= 0:
            return
        # v105 闪避体系（鱼鱼拍板"闪避改乘算"）：全部来源乘算合成 1-Π(1-dᵢ)，统一 40% 总上限
        # 攻击方精准削减：有效闪避 = 闪避 × (1 - 攻击方精准)，精准上限 60%（PVP 互殴生效，PVE 怪物无精准）
        dodge = min(float(self._player_stats(player).get("dodge", 0) or 0), 0.40)
        # 伪装帷幕（effect=dodge_up 闪避率 +40%）：乘算并入
        if self.p_buffs.get("dodge_up"):
            dodge = 1 - (1 - dodge) * (1 - 0.40)
        # 无声被动——被攻击概率降低 30%：乘算并入
        for _pn, _ps in self._passive_map(player)["proc"].get("dodge_up", []):
            dodge = 1 - (1 - dodge) * (1 - float(_ps.get("mult", 0.3)))
        # 影步药剂 15%：并入乘算（不再独立判定——旧实现独立判定绕过 40% 上限，基础 40%+药水可达 49.7%）
        if self.p_buffs.get("dodge_pot"):
            dodge = 1 - (1 - dodge) * (1 - 0.15)
        # 攻击方精准削减（PVP：对方玩家精准；PVE：怪物无精准=0 不削减）
        atk_hit = self._attacker_precise()
        if atk_hit > 0:
            dodge = dodge * (1 - min(atk_hit, 0.60))
        dodge = min(dodge, 0.40)
        if dodge > 0 and random.random() < dodge:
            logs.append("💨 你闪避了攻击！")
            return
        # v104 R3 P1-1：圣盾被动——10% 概率格挡（减伤 50%，同防御姿态）
        for _pn, _ps in self._passive_map(player)["stat"]:
            if _ps.get("stat") == "block" and random.random() < float(_ps.get("mult", 0.1)):
                block_reduce = max(1, int(dmg * 0.5))
                dmg = max(1, dmg - block_reduce)
                logs.append(f"🛡️ 圣盾格挡！减免 {block_reduce} 点伤害！")
        self._player_hit = True  # v2.1 条件：记录本场受击（未受击增伤判定）
        # v104 R3 P1-1：复仇被动——受击后下次攻击 +30%（挨打反打）
        for _pn, _ps in self._passive_map(player)["proc"].get("counter", []):
            self.p_buffs["revenge_atk"] = max(self.p_buffs.get("revenge_atk", 0), 1)
            break
        # 阶段八：受击词条（减伤/格挡/反击/反伤/腐蚀/坚韧）
        dmg = self._affix_on_taken(player, dmg, logs)
        dmg = self._food_on_taken(player, dmg, logs)
        # v64/v104 被动 proc 结算（按 passive 字段查 learned_skills，替换名字硬匹配）：
        #   dmg_taken → 减伤（铁壁之心/磐石体/磐石之心/磐石之躯/守护姿态）；reflect → 反伤（反震）
        ps_names = E.passive_skills_learned(player.get("class_name", ""), player.get("learned_skills", []))
        reduce_total = 0
        for ps_name in ps_names:
            info = E.skill_info(player.get("class_name", ""), ps_name)
            ps = (info or {}).get("passive") or {}
            proc = ps.get("proc")
            if proc == "dmg_taken":
                rpct = float(ps.get("reduce") or 0)
                if rpct <= 0:
                    continue
                if ps.get("cond") == "hp_low_30" and player.get("hp", 0) / max(1, player.get("max_hp", 1)) >= 0.30:
                    continue
                reduce_total += int(dmg * rpct)
            elif proc == "reflect" and self.enemy.get("hp", 0) > 0:
                rd = int(dmg * float(ps.get("mult") or 0))
                if rd > 0:
                    # v104 M02 P1-5：反伤走 Boss 护盾过滤（扣盾减半/反伤），再结算援军挡刀
                    rd = self._boss_dmg_filter(rd, player, logs)
                    self._damage_enemy(rd, logs)
                    logs.append(f"🪨 {ps_name}：反弹 {rd} 点伤害！")
        if reduce_total:
            dmg = max(1, dmg - reduce_total)
            logs.append(f"🛡️ 被动减伤 {reduce_total} 点")
        # v51 盾牌反击：被攻击时 60% 概率反击 120% 伤害
        if self.p_buffs.get("counter", 0) > 0 and self.enemy.get("hp", 0) > 0:
            if random.random() < C.SHIELD_COUNTER_CHANCE:
                pst2 = self._player_stats(player)
                est2 = self._enemy_stats()
                cd = E.calc_damage(int(pst2["atk"] * 1.2), est2.get("def", 0))
                self._damage_enemy(cd, logs)
                logs.append(f"🛡️ 盾牌反击！对【{self.enemy.get('name', '敌人')}】造成 {cd} 点伤害！")
        # 龙鳞套：被攻击时 25% 概率反弹 25% 伤害
        if "reflect" in E.set_bonus_4(player.get("equipment", {})) and self.enemy.get("hp", 0) > 0:
            if random.random() < C.REFLECT_CHANCE:
                rd = int(dmg * 0.25)
                rd = self._boss_dmg_filter(rd, player, logs)  # v104 M02 P1-5：反伤走 Boss 护盾过滤
                self._damage_enemy(rd, logs)
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
                self._add_shield("rune_barrier", shield_gain, 2)
                logs.append(f"🛡️ 符文壁垒：获得 {shield_gain} 点护盾！")
        thorns_lvl = self._enchant_lvl(effs, "thorns")
        if thorns_lvl and self.enemy.get("hp", 0) > 0:
            rd = int(dmg * C.rune_value("thorns", thorns_lvl))
            rd = self._boss_dmg_filter(rd, player, logs)  # v104 M02 P1-5：反伤走 Boss 护盾过滤
            self._damage_enemy(rd, logs)
            logs.append(f"🌵 符文荆棘：反弹 {rd} 点伤害！")
        # v101.28f 荆棘药剂：受击反弹 30% 伤害（3 回合，必触发）
        if self.p_buffs.get("thorns_pot") and self.enemy.get("hp", 0) > 0:
            rd = int(dmg * 0.30)
            rd = self._boss_dmg_filter(rd, player, logs)  # v104 M02 P1-5：反伤走 Boss 护盾过滤
            self._damage_enemy(rd, logs)
            logs.append(f"🌵 荆棘附体：反弹 {rd} 点伤害！")
        # v29 神恩护盾：优先吸收（v59：护盾存战斗状态；v101.28d：多来源护盾逐个扣，同源叠厚异源并存）
        shields = self.p_shields
        if shields:
            absorb_total = 0
            for key in list(shields):
                s = shields[key]
                absorb = min(s["value"], dmg)
                s["value"] -= absorb
                dmg -= absorb
                absorb_total += absorb
                if s["value"] <= 0:
                    del shields[key]
                if dmg <= 0:
                    break
            if absorb_total > 0:
                left = sum(s["value"] for s in shields.values())
                logs.append(f"✨ 护盾吸收 {absorb_total} 点伤害(剩余 {left})")
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
        if player["hp"] > 0 and "神圣坚韧" in ps_names:
            if random.random() < C.HOLY_TENACITY_CHANCE:
                heal = int(player.get("max_hp", player.get("hp", 1)) * 0.05)
                player["hp"] = min(player.get("max_hp", player["hp"]), player["hp"] + heal)
                logs.append(f"✨ 神圣坚韧：回复 {heal} 点生命！")

    def _enemy_dead(self) -> bool:
        return self.enemy.get("hp", 1) <= 0

    def _player_dead(self, player: dict) -> bool:
        return player.get("hp", 1) <= 0
