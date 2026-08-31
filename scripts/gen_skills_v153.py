# -*- coding: utf-8 -*-
"""v153 技能表生成脚本：从 workspace/skills_v153_parsed.json → skills_v153.py

用法:
    python scripts/gen_skills_v153.py           # 生成 game/data/skills_v153.py
    python scripts/gen_skills_v153.py --dry-run # 只打印统计不写文件

说明:
- 数据源: workspace/skills_v153_parsed.json（主 agent 从 CLASS_MECHANICS_v153.md 解析）
- 输出: game/data/skills_v153.py（新 override 表，替代 skills_v151_overrides.py）
- 机制字段映射在下方 MECH_RULES 表，是"机制文本→引擎字段"的规则库
- 引擎不支持的机制标 TODO_ENGINE，由主 agent 统一接线
- desc 由 DESC_TEMPLATES 模板生成（数值 + 机制文本拼装），保证可读性
"""
import json, re, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SRC = r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/workspace/skills_v153_parsed.json"
OUT = r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/data/skills_v153.py"
DRY = "--dry-run" in sys.argv

data = json.load(open(SRC, encoding="utf-8"))

def pinyin_key(name: str) -> str:
    """中文名 → 拼音 id（与 core/index.py pinyin_id 同构）"""
    try:
        from pypinyin import lazy_pinyin
        parts = []
        for ch in name:
            if '\u4e00' <= ch <= '\u9fff':
                parts.append(lazy_pinyin(ch)[0])
            elif ch.isalnum() or ch == '_':
                parts.append(ch.lower())
        return "_".join(parts)
    except Exception:
        return name

def parse_cd(cd_text: str):
    m = re.match(r'(\d+)', cd_text or "")
    return int(m.group(1)) if m else None

def parse_num(t: str, default=None):
    if not t or t == "—":
        return default
    m = re.match(r'[\d.]+', str(t))
    return float(m.group(0)) if m else default

# ============ desc 骨架生成器（仅数值骨架，文案由子 agent 精写） ============
def gen_desc(name: str, sk: dict) -> str:
    """从 kind/base/hits/机制 生成数值骨架 desc。
    注意：这只是骨架（保证技能结构完整），文案由子 agent 按 v151 风格精写后回填。
    骨架格式 = 数值说明 + 机制说明，不含文学描写。
    """
    kind = sk.get("kind", "")
    base = sk.get("base", "")
    hits = sk.get("hits", "")
    mech = sk.get("机制", "")
    cd = sk.get("cd", "")

    # 数值描述
    num_desc = ""
    if kind in ("物理", "魔法", "真伤", "魔法·火", "魔法·冰", "魔法·雷"):
        pct = int(round(float(base) * 100)) if base not in ("—", "") else None
        if pct:
            hits_txt = f"×{hits}" if hits and hits not in ("—", "", "1") else ""
            kind_txt = "物理" if kind == "物理" else "魔法"
            num_desc = f"{pct}% {kind_txt}伤害{hits_txt}"
        elif mech.startswith("[AOE]"):
            num_desc = "全体伤害"
    elif kind == "治疗":
        num_desc = "治疗"
    elif kind == "增益":
        num_desc = "增益"
    elif kind == "召唤":
        num_desc = "召唤"
    elif kind == "被动":
        num_desc = "被动"
    elif kind == "嘲讽":
        num_desc = "嘲讽"

    # 机制清洗
    mech_desc = mech
    for token in ["**兑现**：", "**结算**", "**终结技**：", "**吟唱**：", "**破防**",
                  "〔真伤签名①〕", "〔真伤签名②〕", "（见 §8）"]:
        mech_desc = mech_desc.replace(token, "")
    mech_desc = re.sub(r'\[AOE\]\s*', '', mech_desc)
    mech_desc = mech_desc.strip("； ")

    parts = [p for p in (num_desc, mech_desc) if p]
    text = "；".join(parts)
    if not text:
        text = mech
    if cd and cd not in ("—", ""):
        text = f"{text}（CD {cd}）"
    return text

# ============ 机制 → 引擎字段 映射规则 ============
# 每条规则: (正则, 添加字段 dict, 移除标记)
MECH_RULES = [
    # ---- 战士 ----
    (r'命中 \+1 战意', {"mech": "zhan_yi", "mech_val": 1}, None),
    (r'每段命中 \+1 战意', {"mech": "zhan_yi", "mech_val": 1}, None),
    (r'每层战意 \+(\d+)% 伤害', {"cond_type": "zhan_yi_dmg", "cond_val": None}, None),
    (r'破防\(pierce\)', {"pierce": True}, None),
    (r'全队攻击 \+(\d+)% 持续 (\d+) 刻，自身 \+(\d+) 战意', {"effect": "atk_all", "mech": "zhan_yi", "mech_val": 3}, None),
    (r'自身减伤 (\d+)%，持续 (\d+) 刻', {"effect": "reduce", "mech_val": 45}, None),
    (r'\[AOE\] 前排', {"aoe": "front"}, None),
    (r'\[AOE\] 全体', {"aoe": "all"}, None),
    (r'位移至前排 \+ 先手压制', {"cond": {"type": "player_first", "mult": 1.15, "label": "先手压制"}}, None),
    (r'\*\*兑现\*\*：花 (\d+) 层战意 → 回 (\d+)% 生命 \+ 清 1 减益', {"mech": "zhan_yi_cash", "mech_val": 5, "heal_pct": 20}, None),
    (r'\*\*兑现\*\*：花 (\d+) 层战意 → 立即进入狂暴（无视 10 层门槛）', {"mech": "zhan_yi_fury", "mech_val": 4}, None),
    (r'自身护盾 \+ 格挡率 \+(\d+)%，持续 (\d+) 刻', {"effect": "shield_block", "block_pct": None}, None),
    (r'吸血 (\d+)%；狂暴中 (\d+)%', {"lifesteal": 0.25, "rage_form": {"lifesteal_mult": 2}}, None),
    (r'真伤 \+ 灼烧 (\d+) 层', {"kind_override": "真伤", "mech": "burn", "mech_val": 2}, None),
    (r'真伤爆发 \+ 灼烧 (\d+) 层', {"kind_override": "真伤", "mech": "burn", "mech_val": 3}, None),
    (r'战意 ≥(\d+) 时附加流血 (\d+) 层', {"mech": "bleed", "mech_val": 2, "cond": {"type": "player_mech_stacks", "mech": "zhan_yi", "stacks": None, "mult": 1.0}}, None),
    (r'流血 (\d+) 层 \+ 减速 (\d+)% 持续 (\d+) 刻', {"mech": "bleed", "mech_val": 2, "mech2": "spd_down", "mech2_val": 30}, None),
    (r'流血 (\d+) 层', {"mech": "bleed", "mech_val": 2}, None),
    (r'战意 ≥(\d+) 时 ×([\d.]+)', {"cond": {"type": "player_mech_stacks", "mech": "zhan_yi", "stacks": None, "mult": None}}, None),
    (r'战意 ≥(\d+) 时扩为全体', {"aoe_cond": True}, None),
    (r'战意 ≥(\d+) 时暴击 \+(\d+)%', {"passive": "zhan_yi_crit"}, None),
    (r'(\d+)% 眩晕 ([\d.]+) 刻', {"mech": "stun", "mech_chance": None, "mech_val": None}, None),
    (r'(\d+)% 眩晕 ([\d.]+) 刻；守护姿态中 \+(\d+)% 伤害', {"mech": "stun", "mech_chance": None, "mech_val": None, "stance_dmg": True}, None),
    (r'姿态：受击反击 (\d+)%，每刻 \+([\d.]+) 战意', {"stance": "counter", "mech": "zhan_yi", "mech_val": 1}, None),
    (r'嘲讽失效时自动衔接（不占行动）', {"auto": "taunt_fail"}, None),
    (r'强制攻击，持续 (\d+) 刻', {"effect": "taunt"}, None),
    (r'为队友挡刀，反伤 (\d+)%，持续 (\d+) 刻', {"effect": "protect", "reflect": None}, None),
    (r'挡刀 \+ 反伤 (\d+)%，持续 (\d+) 刻', {"effect": "protect", "reflect": None}, None),
    (r'全队减伤 (\d+)% 持续 (\d+) 刻', {"effect": "reduce_all"}, None),
    (r'战意满 (\d+) 时减伤 \+(\d+)%、免疫眩晕', {"passive": "zhan_yi_full_reduce"}, None),
    (r'被控时消耗 (\d+) 层战意跳过（每场 (\d+) 次）', {"passive": "tenacity", "mech_val": 2}, None),
    (r'复仇：伤害 = base ×\(1 \+ 已承伤/max_hp ×([\d.]+)\)', {"cond": {"type": "revenge", "mult": 0.8}}, None),
    (r'破防 \+ (\d+)% 眩晕 ([\d.]+) 刻', {"pierce": True, "mech": "stun", "mech_chance": None}, None),
    (r'战意之盾：全队护盾（值随战意层数，每层 \+(\d+)%，不消耗）持续 (\d+) 刻', {"effect": "shield_all", "shield_per_stack": None}, None),
    (r'\*\*兑现\*\*：花 (\d+) 层战意 → 全队护盾（每层 (\d+)% 施法者 max_hp）持续 (\d+) 刻', {"effect": "shield_all", "shield_per_stack": None}, None),
    (r'\*\*兑现\*\*：花满 (\d+) 层 → 全队护盾 \+ 减伤 (\d+)%，持续 (\d+) 刻', {"effect": "shield_all_reduce"}, None),
    (r'战意满 (\d+) 时 ×([\d.]+)', {"cond": {"type": "player_mech_stacks", "mech": "zhan_yi", "stacks": None, "mult": None}}, None),
    (r'狂暴中生命首次归零时，清空战意复活并回 (\d+)%', {"passive": "berserk_revive"}, None),
    (r'进入狂暴时自动追加（不占行动）', {"auto": "fury_append"}, None),
    (r'守护姿态下首次致命伤免疫，清空全部战意', {"passive": "stance_immortal"}, None),
    (r'全队攻击 \+(\d+)% 持续 (\d+) 刻', {"effect": "atk_all"}, None),
    (r'每层战意额外 \+([\d.]+)% 吸血', {"passive": "zhan_yi_lifesteal"}, None),
    (r'三段，每段命中 \+1 战意', {"mech": "zhan_yi", "mech_val": 1, "hits": 3}, None),
    (r'四段，每段命中 \+1 战意', {"mech": "zhan_yi", "mech_val": 1, "hits": 4}, None),
    (r'灼烧清算', {"mech2": "burn_burst"}, None),
    # ---- 法师（印记规则必须在减速规则前：冰锥"挂冰印+减速"会被减速规则抢匹配）----
    (r'挂火印 (\d+) 层', {"mech": "fire_mark", "mech_val": 1}, None),
    (r'挂冰印 (\d+) 层，减速 (\d+)% 持续 (\d+) 刻', {"mech": "ice_mark", "mech_val": 1, "mech2": "spd_down"}, None),
    (r'挂冰印 (\d+) 层', {"mech": "ice_mark", "mech_val": 1}, None),
    (r'挂雷印 (\d+) 层', {"mech": "thunder_mark", "mech_val": 1}, None),
    (r'三段，每段挂雷印 1 层', {"mech": "thunder_mark", "mech_val": 1, "hits": 3}, None),
    (r'\[AOE\] 全体，挂火印 1 层', {"aoe": "all", "mech": "fire_mark", "mech_val": 1}, None),
    (r'挂火印 (\d+) 层', {"mech": "fire_mark", "mech_val": 2}, None),
    (r'减速 (\d+)% 持续 (\d+) 刻', {"mech2": "spd_down"}, None),
    (r'减速 (\d+)%，持续 (\d+) 刻', {"mech": "spd_down", "mech_val": None}, None),
    (r'自身护盾，持续 (\d+) 刻', {"effect": "shield_self"}, None),
    (r'位移至后排 \+ 闪避 \+(\d+)% 持续 (\d+) 刻', {"effect": "dodge_buff", "move": "back"}, None),
    (r'召唤藤蔓守卫（见 §8）', {"summon": "vine_guard"}, None),
    (r'召唤古树守卫（见 §8）', {"summon": "treant"}, None),
    (r'召唤 1 只骷髅（挡刀，上限 3）', {"summon": "skeleton", "count": 1}, None),
    (r'召唤 3 只骷髅', {"summon": "skeleton", "count": 3}, None),
    (r'脱战 \+ 全队闪避 \+(\d+)% 持续 (\d+) 刻', {"effect": "disengage_dodge"}, None),
    (r'\*\*结算\*\*目标印记，触发对应反应', {"mech": "element_burst", "mech_val": 1}, None),
    (r'架设：施法 \+(\d+)%，受伤 \+(\d+)%，不可普攻', {"focus": True, "focus_magic": None}, None),
    (r'两段，各挂不同系印记 1 层', {"hits": 2, "mech": "element_multi_mark"}, None),
    (r'架设中受伤 −(\d+)%，持续 (\d+) 刻', {"focus_reduce": True}, None),
    (r'目标印记总层数 ≥(\d+) 时 ×([\d.]+)', {"cond": {"type": "enemy_marks", "stacks": None, "mult": None}}, None),
    (r'引爆后，下次挂印 \+1 层', {"passive": "element_affinity"}, None),
    (r'切换当前主系（影响下次挂印系别）', {"effect": "element_switch"}, None),
    (r'结算目标全部印记，每层 \+(\d+)% 伤害', {"mech": "element_burst_all", "per_layer": None}, None),
    (r'连续两次同系施法，第二次挂印 \+1 层', {"passive": "element_sync"}, None),
    (r'\[AOE\] 全体挂当前系印记 1 层', {"aoe": "all", "mech": "element_mark_current"}, None),
    (r'单系印记满 3 层时，该系结算暴击 \+(\d+)%', {"passive": "element_core"}, None),
    (r'召唤火元素（见 §8）', {"summon": "fire_elemental"}, None),
    (r'结算三系印记，每系 ×([\d.]+)', {"mech": "element_burst_3", "per_element": None}, None),
    (r'\[AOE\] 全体 \+ 全体结算印记', {"aoe": "all", "mech": "element_burst_all"}, None),
    (r'三系同时 ≥(\d+) 层时，结算伤害 \+(\d+)%（\*\*加算\*\*，不是乘算）', {"passive": "element_origin"}, None),
    (r'召唤雷元素（见 §8）', {"summon": "thunder_elemental"}, None),
    (r'雷系顶点；雷印满 3 层时连击 \+(\d+)', {"mech": "thunder_mark", "mech_val": 1, "cond": {"type": "enemy_mark_full", "mech": "thunder", "stacks": 3, "combo": 2}}, None),
    (r'三段，充能 \+(\d+)；充能 ≥(\d+) 时 ×([\d.]+)', {"mech": "arcane", "mech_val": 1, "hits": 3, "cond": {"type": "player_mech_stacks", "mech": "arcane", "stacks": 2, "mult": 1.15}}, None),
    (r'每刻自动 \+(\d+) 充能（冥想中 \+(\d+)）', {"passive": "arcane_intuition", "rate": 1, "meditate_rate": 2}, None),
    (r'必中力场，充能 \+(\d+)；架设中额外 \+(\d+)', {"mech": "arcane", "mech_val": 1, "accuracy": "true", "focus_extra": 1}, None),
    (r'架设：魔法 \+(\d+)%、受击 \+(\d+)%、每刻充能 \+(\d+)', {"focus": True, "focus_magic": None, "arcane_meditate": True}, None),
    (r'两段，充能 \+(\d+)；充能 ≥(\d+) 时 ×([\d.]+)', {"mech": "arcane", "mech_val": 2, "hits": 2, "cond": {"type": "player_mech_stacks", "mech": "arcane", "stacks": 4, "mult": 1.25}}, None),
    (r'力场护盾：消耗全部充能，每层转 (\d+)% 魔攻护盾', {"effect": "arcane_shield", "per_charge": None}, None),
    (r'燃尽全部充能，每层 \+(\d+)%；架设中只烧一半', {"mech": "arcane_burst", "per_charge": None, "focus_half": True}, None),
    (r'燃尽全部充能，每层 \+(\d+)%；满 5 层时 ×([\d.]+)', {"mech": "arcane_burst", "per_charge": None, "full_mult": None}, None),
    (r'奥术技能伤害 \+(\d+)%', {"passive": "arcane_resonance"}, None),
    (r'沉默 ([\d.]+) 刻（首领 ([\d.]+) 刻）\+ 充能 \+(\d+)', {"mech": "silence", "mech_val": 2, "arcane_gain": 2}, None),
    (r'领域：全队奥术/魔法伤害 \+(\d+)%，持续 (\d+) 刻', {"effect": "arcane_matrix"}, None),
    (r'力场塑形：消耗 (\d+) 充能，选盾（护盾）或刃（下次奥术技 ×([\d.]+)）', {"effect": "arcane_field"}, None),
    (r'\[AOE\] 全体纯能量', {"aoe": "all"}, None),
    (r'单体爆发；充能 ≥(\d+) 时 ×([\d.]+)', {"cond": {"type": "player_mech_stacks", "mech": "arcane", "stacks": 3, "mult": 1.2}}, None),
    (r'充能满 (\d+) 时，奥术暴击 \+(\d+)%', {"passive": "arcane_wisdom"}, None),
    (r'奥术技能耗蓝 −(\d+)%（能量循环）', {"passive": "arcane_constant"}, None),
    (r'顶点：充能满 (\d+) 时 ×([\d.]+)，且本次不耗蓝', {"cond": {"type": "player_mech_stacks", "mech": "arcane", "stacks": 5, "mult": 1.4}, "no_mp": True}, None),
    # ---- 游侠 ----
    (r'双段', {"hits": 2}, None),
    (r'单体', {}, None),
    (r'自身暴击 \+(\d+)%、命中 \+(\d+)%，持续 (\d+) 刻', {"effect": "crit_hit_buff"}, None),
    (r'速度 \+(\d+)% 持续 (\d+) 刻 \+ 位移', {"effect": "spd_buff", "move": "front"}, None),
    (r'对异常状态目标 ×([\d.]+)', {"cond": {"type": "enemy_debuff", "mult": None}}, None),
    (r'挂猎印 (\d+) 层（全队对该目标 \+(\d+)% 伤害/层，上限 3 层）', {"mech": "hunt_mark", "mech_val": 1}, None),
    (r'挂猎印 (\d+) 层', {"mech": "hunt_mark", "mech_val": 2}, None),
    (r'对猎印目标 ×([\d.]+)', {"cond": {"type": "enemy_hunt_mark", "mult": None}}, None),
    (r'毒 (\d+) 层（供荆棘爆引爆），持续 (\d+) 刻', {"mech": "poison", "mech_val": 2}, None),
    (r'毒 (\d+) 层 \+ 定身 ([\d.]+) 刻（首领免疫）', {"mech": "poison", "mech_val": 2, "mech2": "stun", "mech2_val": 1.5}, None),
    (r'引爆毒层，每层 \+(\d+)% 伤害（(\d+) 层上限 → ×([\d.]+)）', {"mech": "poison_burst", "per_layer": None}, None),
    (r'猎印每层增伤 \+(\d+)%（叠加基础 8%）', {"passive": "hunt_mark_up"}, None),
    (r'猎印上限 \+(\d+) 层（至 (\d+) 层）', {"passive": "hunt_mark_cap"}, None),
    (r'对猎印目标 ×([\d.]+) \+ 全队暴击 \+(\d+)% 持续 (\d+) 刻', {"cond": {"type": "enemy_hunt_mark", "mult": None}, "effect": "crit_all"}, None),
    (r'毒层上限 \+(\d+)，毒爆增伤 \+(\d+)%', {"passive": "poison_cap_up"}, None),
    (r'猎印满层时 ×([\d.]+)', {"cond": {"type": "enemy_hunt_full", "mult": None}}, None),
    (r'全队闪避 \+(\d+)%、减伤 (\d+)%，持续 (\d+) 刻', {"effect": "dodge_reduce_all"}, None),
    (r'全队对猎印目标增伤 \+(\d+)%，持续 (\d+) 刻', {"effect": "hunt_team_dmg"}, None),
    (r'四段', {"hits": 4}, None),
    (r'猎印满层 \+ 毒层 ≥(\d+) 时，斩杀生命 <(\d+)% 的目标', {"kill": {"hunt_full": True, "poison": None, "hp_lt": 0.25}}, None),
    (r'召唤物存活时，专注充能 \+(\d+)/s（至 (\d+)/s）', {"passive": "focus_regen_summon"}, None),
    (r'速度比 ≥([\d.]+) 时 ×([\d.]+)', {"cond": {"type": "speed_ratio", "ratio": None, "mult": None}}, None),
    (r'双段', {"hits": 2}, None),
    (r'蓄力 ([\d.]+) 刻；蓄力后 ×([\d.]+)', {"charge": None, "charge_mult": None}, None),
    (r'三段', {"hits": 3}, None),
    (r'锁定，无视站位，全队对其 \+(\d+)% 伤害，持续 (\d+) 刻', {"effect": "star_lock"}, None),
    (r'风行：速度 \+(\d+)%，持续 (\d+) 刻', {"effect": "spd_buff"}, None),
    (r'结余 ≥(\d+) 时，下次技能暴击 \+(\d+)%（强化结余奖励）', {"passive": "focus_surplus_crit"}, None),
    (r'三段；结余 ≥(\d+) 时改为四段', {"hits": 3, "cond": {"type": "focus_surplus", "stacks": None, "extra_hit": True}}, None),
    (r'点名后排 \+ 破防', {"pierce": True, "target": "back"}, None),
    (r'闪避 \+(\d+)%，持续 (\d+) 刻', {"effect": "dodge_buff"}, None),
    (r'破防 \+ 点名，无视 (\d+)% 防御', {"pierce": True, "pene_pct": None, "target": "back"}, None),
    (r'击杀目标后，专注立即回满', {"passive": "focus_full_on_kill"}, None),
    (r'全队速度 \+(\d+)%，持续 (\d+) 刻', {"effect": "spd_all"}, None),
    (r'四段；结余 ≥(\d+) 时暴击 \+(\d+)%', {"hits": 4, "cond": {"type": "focus_surplus", "stacks": None, "crit": None}}, None),
    (r'速度比 ≥([\d.]+) 时，所有伤害 ×([\d.]+)', {"passive": "speed_ratio_dmg"}, None),
    (r'必中 \+ 必暴 \+ 破防；点名后排', {"pierce": True, "accuracy": "true", "crit": "true", "target": "back"}, None),
    # ---- 牧师 ----
    (r'单体治疗', {"kind": "治疗", "heal": True}, None),
    (r'全体小治疗', {"kind": "治疗", "heal": True, "team": True}, None),
    (r'驱散 1 个减益', {"effect": "cleanse"}, None),
    (r'单体护盾，持续 (\d+) 刻', {"effect": "shield_self"}, None),
    (r'单体输出（不增信念）', {}, None),
    (r'全队魔攻 \+(\d+)%，持续 (\d+) 刻', {"effect": "matk_all"}, None),
    (r'主动卸除 (\d+) 点信念，自身回血 (\d+)%', {"mech": "faith_unload", "mech_val": 3, "heal_pct": 15}, None),
    (r'免疫 1 次控制', {"effect": "cc_immune"}, None),
    (r'单体大治疗；信念 <(\d+) 时额外 \+(\d+)%', {"kind": "治疗", "heal": True, "cond": {"type": "faith_lt", "stacks": None, "mult": None}}, None),
    (r'全体治疗', {"kind": "治疗", "heal": True, "team": True}, None),
    (r'单体大治疗；目标生命越低越高', {"kind": "治疗", "heal": True, "cond": {"type": "target_low_hp", "mult": None}}, None),
    (r'全体净化 \+ 解控', {"effect": "cleanse_all"}, None),
    (r'治疗溢出量的 (\d+)% 转为护盾', {"passive": "heal_overflow_shield"}, None),
    (r'持续回血，(\d+) 刻 内每 (\d+) 刻 恢复一次', {"kind": "治疗", "heal": True, "hot": True}, None),
    (r'单体超大治疗', {"kind": "治疗", "heal": True}, None),
    (r'全体持续回血，(\d+) 刻 内每 (\d+) 刻 恢复一次', {"kind": "治疗", "heal": True, "team": True, "hot": True}, None),
    (r'全队减伤 (\d+)% \+ 回血，持续 (\d+) 刻', {"effect": "reduce_all", "heal": True}, None),
    (r'全体大治疗（重技）', {"kind": "治疗", "heal": True, "team": True}, None),
    (r'全队攻击 \+ 魔攻 \+(\d+)%，持续 (\d+) 刻', {"effect": "atk_matk_all"}, None),
    (r'治疗时，目标承伤的 (\d+)% 转移给自己（分担）', {"passive": "faith_share"}, None),
    (r'全体大治疗 \+ 驱散全部减益', {"kind": "治疗", "heal": True, "team": True, "effect": "cleanse_all"}, None),
    (r'复活倒地队友（回 (\d+)% 生命）', {"kind": "治疗", "revive": True, "revive_pct": None}, None),
    (r'圣光单体终结（不增信念）', {"kind": "魔法"}, None),
    (r'过载时不再力竭，改为全队回血 \+(\d+)%', {"passive": "faith_overload_heal"}, None),
    (r'全体治疗 \+ 全队免疫 1 次致命伤，持续 (\d+) 刻', {"kind": "治疗", "heal": True, "team": True, "effect": "fatal_immune"}, None),
    (r'暗蚀 \+ 挂诅咒：全队对目标 \+(\d+)% 伤害持续 (\d+) 刻', {"mech": "curse", "mech_val": 1}, None),
    (r'挂灵魂标记：每层全队 \+(\d+)%（上限 3，随骷髅存活同步）', {"mech": "soul_mark", "mech_val": 1}, None),
    (r'暗蚀 \+ 刷新目标诅咒持续', {"mech": "curse_refresh"}, None),
    (r'献祭 1 骷髅 → 全体暗蚀', {"mech": "sacrifice"}, None),
    (r'骷髅上限 \+(\d+)（至 (\d+)）', {"passive": "skeleton_cap"}, None),
    (r'场上每只亡灵 每刻 \+([\d.]+) 信念', {"passive": "undead_faith"}, None),
    (r'信念 ≥(\d+) 时，致命伤由 1 只骷髅代为承受', {"passive": "death_contract"}, None),
    (r'\[AOE\] 消耗全部骷髅，每只 (\d+)% 全体暗蚀', {"aoe": "all", "mech": "bone_rush"}, None),
    (r'对带诅咒目标 ×([\d.]+)', {"cond": {"type": "enemy_cursed", "mult": None}}, None),
    (r'自身减伤 (\d+)% 持续 (\d+) 刻 \+ 骷髅挡刀', {"effect": "reduce", "summon_block": True}, None),
    (r'召唤 3 只骷髅', {"summon": "骷髅", "count": 3}, None),
    (r'\[AOE\] 全体暗蚀 \+ 沉默 ([\d.]+) 刻', {"aoe": "all", "mech2": "silence"}, None),
    (r'灵魂标记上限 \+(\d+)（至 (\d+)），每层 \+(\d+)%', {"passive": "soul_mark_cap"}, None),
    (r'献祭全部骷髅 → 单体高伤 \+ 沉默 ([\d.]+) 刻', {"mech": "bone_rush_single", "mech2": "silence"}, None),
    (r'顶点：信念满 (\d+) 时 ×([\d.]+)，召唤亡魂大军', {"cond": {"type": "faith_full", "stacks": None, "mult": None}, "summon": "skeleton", "count": 3}, None),
    # ---- 刺客 ----
    (r'命中 \+1 段', {"mech": "lian_duan", "mech_val": 1}, None),
    (r'每段命中 \+1 段', {"mech": "lian_duan", "mech_val": 1}, None),
    (r'背击时 ×([\d.]+)', {"cond": {"type": "backstab", "mult": None}}, None),
    (r'潜行：下次攻击必暴，不涨段', {"effect": "stealth"}, None),
    (r'速度 \+(\d+)%，持续 (\d+) 刻', {"effect": "spd_buff"}, None),
    (r'\*\*终结技\*\*：×\(1\+([\d.]+)×连段\)，结算后归零', {"mech": "finisher", "per_stack": None}, None),
    (r'三段，每段命中 \+1 段', {"mech": "lian_duan", "mech_val": 1, "hits": 3}, None),
    (r'断连时只掉 (\d+) 段（而非减半）', {"passive": "lian_duan_soft"}, None),
    (r'潜行中 ×([\d.]+)', {"cond": {"type": "stealth", "mult": None}}, None),
    (r'目标生命 <(\d+)% 时 ×([\d.]+)', {"cond": {"type": "enemy_low_hp", "hp_lt": None, "mult": None}}, None),
    (r'四段，每段命中 \+1 段', {"mech": "lian_duan", "mech_val": 1, "hits": 4}, None),
    (r'强制潜行 \+ 免控，持续 (\d+) 刻', {"effect": "stealth_cc"}, None),
    (r'影舞态内速度 \+(\d+)%、暴伤 \+(\d+)%', {"passive": "shadow_dance_bonus"}, None),
    (r'影舞态强化：全队暴击 \+(\d+)%，持续 (\d+) 刻', {"effect": "crit_all"}, None),
    (r'四段；影舞态中 ×([\d.]+)', {"hits": 4, "cond": {"type": "shadow_dance", "mult": None}}, None),
    (r'\*\*终结技\*\*：×\(1\+([\d.]+)×连段\)；击杀则连段保留', {"mech": "finisher", "per_stack": None, "keep_on_kill": True}, None),
    (r'影舞态中所有技能 CD −(\d+)%', {"passive": "shadow_dance_cd"}, None),
    (r'连段满 (\d+) 时 ×([\d.]+)', {"cond": {"type": "player_mech_stacks", "mech": "lian_duan", "stacks": None, "mult": None}}, None),
    (r'终结技系数 \+(\d+)%（每段 10% → 16%）', {"passive": "finisher_up", "per_stack": None}, None),
    (r'连段满 (\d+) → 进入影舞态：CD −(\d+)%，受击不清段', {"effect": "shadow_dance", "cd_reduce": None}, None),
    (r'\*\*终结技\*\*：×\(1\+([\d.]+)×连段\)；连段 ≥(\d+) 时必暴', {"mech": "finisher", "per_stack": None, "crit_cond": None}, None),
    (r'毒 (\d+) 层持续 (\d+) 刻；连段 ≥(\d+) 时额外毒 1 层', {"mech": "poison", "mech_val": 2, "cond": {"type": "player_mech_stacks", "mech": "lian_duan", "stacks": None, "extra_poison": True}}, None),
    (r'双段，每段毒 (\d+) 层', {"hits": 2, "mech": "poison", "mech_val": 2}, None),
    (r'毒爆伤害 \+(\d+)%', {"passive": "poison_burst_up"}, None),
    (r'\*\*终结技\*\*：引爆全部毒层，每层 \+(\d+)%；结算后连段归零', {"mech": "poison_burst_finisher", "per_layer": None}, None),
    (r'毒 (\d+) 层持续 (\d+) 刻 \+ \*\*破防\*\*（与毒刃区分：叠毒 vs 破防）', {"mech": "poison", "mech_val": 3, "pierce": True}, None),
    (r'目标易伤 \+(\d+)%，持续 (\d+) 刻', {"effect": "vuln"}, None),
    (r'毒层上限 \+(\d+)（至 (\d+) 层）', {"passive": "poison_cap"}, None),
    (r'\[AOE\] 全体 \+ 毒 (\d+) 层持续 (\d+) 刻', {"aoe": "all", "mech": "poison", "mech_val": 2}, None),
    (r'毒层 ≥(\d+) 时，目标减速 (\d+)%、降防 (\d+)%', {"passive": "poison_weaken"}, None),
    (r'真伤单体 \+ 腐蚀 (\d+) 层〔真伤签名①〕', {"kind_override": "真伤", "mech": "corros", "mech_val": 2}, None),
    (r'目标防御越高伤害越高（最高 ×([\d.]+)）', {"cond": {"type": "enemy_def_high", "mult": None}}, None),
    (r'自身闪避 \+(\d+)%，持续 (\d+) 刻', {"effect": "dodge_buff"}, None),
    (r'全部毒层伤害 \+(\d+)%', {"passive": "poison_all_up"}, None),
    (r'\[AOE\] 全体 \+ 满毒清算（毒 ≥(\d+) 层时 ×([\d.]+)）', {"aoe": "all", "cond": {"type": "enemy_poison_full", "stacks": None, "mult": None}}, None),
    (r'真伤顶点 \+ 腐蚀 (\d+) 层〔真伤签名②〕', {"kind_override": "真伤", "mech": "corros", "mech_val": 4}, None),
    (r'毒爆击杀目标时，毒层扩散给相邻敌人', {"passive": "poison_spread"}, None),
    (r'\[AOE\] 全体；对所有带毒目标 ×([\d.]+)', {"aoe": "all", "cond": {"type": "enemy_poisoned", "mult": None}}, None),
    # ---- 拳师 ----
    (r'清 1 减益 \+ 自身每刻回蓝 (\d+)%（持续 (\d+) 刻）', {"effect": "cleanse", "mp_regen": True}, None),
    (r'对破防状态目标 ×([\d.]+)', {"cond": {"type": "enemy_broken", "mult": None}}, None),
    (r'对破防目标 ×([\d.]+)', {"cond": {"type": "enemy_broken", "mult": None}}, None),
    (r'破防持续 \+([\d.]+) 刻，全队增伤 \+(\d+)%', {"passive": "broken_extend"}, None),
    (r'推条；伤害 = base ×\(1 \+ ([\d.]+) × 磐核数\)', {"shaken_gain": 5, "cond": {"type": "guard_core", "per_core": None}}, None),
    (r'磐核 ≥(\d+) 时，溢出承伤转为护盾', {"passive": "core_overflow"}, None),
    (r'核能爆发：消耗全部磐核：×\(1 \+ ([\d.]+) × 核数\)', {"mech": "guard_core_burst", "per_core": None}, None),
    (r'全队护盾（磐核数 ×(\d+)% 施法者 max_hp）持续 (\d+) 刻', {"effect": "shield_all", "per_core_pct": None}, None),
    (r'磐核满 (\d+) 时，免疫控制 \+ 减伤 \+(\d+)%', {"passive": "core_full"}, None),
    (r'全队减伤 (\d+)-(\d+)%（按磐核数）\+ 护盾，持续 (\d+) 刻', {"effect": "reduce_shield_all"}, None),
    (r'消耗全部磐核：×\(1 \+ ([\d.]+) × 核数\)', {"mech": "guard_core_burst", "per_core": None}, None),
    (r'生命 <(\d+)% 时获得 (\d+) 核 \+ 减伤 (\d+)%（每场 1 次）', {"passive": "core_last_stand"}, None),
    (r'推条；对破防目标 ×([\d.]+)', {"shaken_gain": 15, "cond": {"type": "enemy_broken", "mult": None}}, None),
    (r'推条', {"shaken_gain": 5}, None),
    (r'推条；速度比 ≥([\d.]+) 时额外 \+(\d+)', {"shaken_gain": 5, "cond": {"type": "speed_ratio", "ratio": None, "extra_shaken": None}}, None),
    (r'\[AOE\] 前排推条', {"aoe": "front", "shaken_gain": 5}, None),
    (r'单次大推条', {"shaken_gain": 15}, None),
    (r'伤害 = base ×\(1 \+ 目标破绽/50 × ([\d.]+)\)', {"cond": {"type": "enemy_shaken_ratio", "mult": None}}, None),
    (r'格挡 1 次 \+ 反伤 (\d+)%，持续 (\d+) 刻', {"effect": "block_reflect"}, None),
    (r'敌人破绽 ≥(\d+) 时，自身对其伤害 \+(\d+)%', {"passive": "shaken_awareness"}, None),
    (r'四段推条', {"hits": 4, "shaken_gain": 4}, None),
    (r'三段；破绽 ≥(\d+) 时追加 1 段', {"hits": 3, "cond": {"type": "enemy_shaken", "stacks": None, "extra_hit": True}}, None),
    (r'破绽衰减减半（−([\d.]+)/s → −([\d.]+)/s）', {"passive": "shaken_decay_half"}, None),
    (r'破防触发时，额外眩晕 ([\d.]+) 刻', {"mech2": "stun"}, None),
    (r'破绽越高伤害越高', {"cond": {"type": "enemy_shaken_scale", "mult": 1.0}}, None),
    (r'四段推条', {"hits": 4, "shaken_gain": 3}, None),
    (r'推条；破防时目标眩晕 ([\d.]+) 刻', {"shaken_gain": 18, "mech2": "stun"}, None),
    (r'守御姿态下受击 +1', {"stance": "guard_core_gain"}, None),
    (r'姿态：受伤 −(\d+)%，但推条值 −(\d+)%', {"stance": "defend", "shaken_penalty": None}, None),
    (r'全队减伤 (\d+)%，持续 (\d+) 刻', {"effect": "reduce_all"}, None),
    (r'受击时 (\d+)% 反击（普攻的 (\d+)%）', {"passive": "counter_chance"}, None),
    (r'受击时对攻击者反弹 (\d+)% 伤害 \+ 推条', {"passive": "reflect", "shaken_gain": 3}, None),
    (r'反击概率 \+(\d+)%，反击伤害 \+(\d+)%', {"passive": "counter_up"}, None),
    (r'每核额外减伤 \+(\d+)%（与基础 \+(\d+)% 叠加）', {"passive": "core_reduce"}, None),
    (r'消耗 (\d+) 核 → 自身减伤 (\d+)%，持续 (\d+) 刻', {"effect": "reduce", "core_cost": None}, None),
    # ---- 诗人 ----
    (r'驻留：全队攻击 \+(\d+)%', {"mech": "melody", "melody": "atk"}, None),
    (r'驻留：全队减伤 \+(\d+)%', {"mech": "melody", "melody": "def"}, None),
    (r'驻留：全队速度 \+(\d+)%', {"mech": "melody", "melody": "spd"}, None),
    (r'\*\*吟唱\*\*：当前旋律强度 \+1', {"mech": "melody_chant", "mech_val": 1}, None),
    (r'音波单体输出', {}, None),
    (r'全队小回血', {"kind": "治疗", "heal": True, "team": True}, None),
    (r'全队速度 \+(\d+)%，持续 (\d+) 刻（一次性，非驻留）', {"effect": "spd_all"}, None),
    (r'\*\*吟唱\*\*：强度 \+1，且当前旋律效果翻倍，持续 (\d+) 刻', {"mech": "melody_chant", "mech_val": 1, "melody_double": True}, None),
    (r'驻留：全队攻击 \+(\d+)%。\*\*终章\*\*：全队攻击 \+(\d+)%，持续 (\d+) 刻', {"mech": "melody", "melody": "atk", "finale": "atk"}, None),
    (r'驻留：全队攻击 \+ 魔攻 \+(\d+)%。\*\*终章\*\*：全队暴击 \+(\d+)%，持续 (\d+) 刻', {"mech": "melody", "melody": "atk_matk", "finale": "crit"}, None),
    (r'吟唱时强度额外 \+1 层', {"passive": "melody_duet"}, None),
    (r'音刃输出；当前旋律为增益系时 ×([\d.]+)', {"cond": {"type": "melody_buff", "mult": None}}, None),
    (r'驻留：全队攻击 \+(\d+)%、暴击 \+(\d+)%。\*\*终章\*\*：全队吸血 \+(\d+)%，持续 (\d+) 刻', {"mech": "melody", "melody": "atk_crit", "finale": "lifesteal"}, None),
    (r'全队回血 \+ 攻击 \+(\d+)%，持续 (\d+) 刻', {"kind": "治疗", "heal": True, "team": True, "effect": "atk_all"}, None),
    (r'单体音刃终结（重技）', {"kind": "魔法"}, None),
    (r'驻留：全队攻/魔攻/暴击/速度 \+(\d+)%。\*\*终章\*\*：全队免疫 1 次控制', {"mech": "melody", "melody": "all", "finale": "cc_immune"}, None),
    (r'强度层 ≥(\d+) 时，全队额外 \+(\d+)% 全属性', {"passive": "melody_resonance"}, None),
    (r'全队免疫 1 次控制', {"effect": "cc_immune"}, None),
    (r'当前旋律效果翻倍，持续 (\d+) 刻（\*\*不吃吟唱位\*\*，与和声区分）', {"melody_double": True}, None),
    (r'全队大回血', {"kind": "治疗", "heal": True, "team": True}, None),
    (r'驻留：全队全属性 \+(\d+)%（顶点旋律）。\*\*终章\*\*：全队全属性 \+(\d+)%，持续 (\d+) 刻', {"mech": "melody", "melody": "all", "finale": "all"}, None),
    (r'强度层满 (\d+) 时，全队额外 \+(\d+)% 全属性', {"passive": "melody_full"}, None),
    (r'每强度层 \+(\d+)% 旋律效果（\*\*满层 \+(\d+)%\*\*，基础为 \+(\d+)%）', {"passive": "melody_master"}, None),
    (r'音刃顶点终结；强度层 ≥(\d+) 时 ×([\d.]+)', {"kind": "魔法", "cond": {"type": "melody_stacks", "stacks": None, "mult": None}}, None),
    (r'全队全属性 \+(\d+)%、免疫控制，持续 (\d+) 刻', {"effect": "all_stat_cc"}, None),
    (r'音刃 \+ 目标攻击 −(\d+)%，持续 (\d+) 刻', {"mech2": "atk_down"}, None),
    (r'驻留：敌方全体速度 −(\d+)%。\*\*终章\*\*：敌方全体速度 −(\d+)%，持续 (\d+) 刻', {"mech": "melody", "melody": "e_spd", "finale": "e_spd"}, None),
    (r'单体睡眠：定身 ([\d.]+) 刻（首领 ([\d.]+) 刻）', {"mech": "stun", "mech_val": None, "sleep": True}, None),
    (r'音刃 \+ 目标攻击 −(\d+)%，持续 (\d+) 刻', {"mech2": "atk_down"}, None),
    (r'驻留：敌方全体攻击 −(\d+)%。\*\*终章\*\*：敌方全体攻击 −(\d+)%，持续 (\d+) 刻', {"mech": "melody", "melody": "e_atk", "finale": "e_atk"}, None),
    (r'目标防御 −(\d+)%，持续 (\d+) 刻', {"mech2": "def_down"}, None),
    (r'驻留：敌方全体封印技能（每 (\d+) 刻 至多 1 次）。\*\*终章\*\*：全体沉默 ([\d.]+) 刻', {"mech": "melody", "melody": "e_silence", "finale": "silence"}, None),
    (r'敌方全体睡眠：定身 ([\d.]+) 刻（首领 ([\d.]+) 刻）', {"mech": "stun", "mech_val": None, "sleep": True, "aoe": "all"}, None),
    (r'音刃 \+ 沉默 ([\d.]+) 刻', {"mech2": "silence"}, None),
    (r'挽歌系控制时长 \+([\d.]+) 刻', {"passive": "dirge_ctrl_up"}, None),
    (r'目标全属性 −(\d+)%，持续 (\d+) 刻', {"mech2": "all_down"}, None),
    (r'驻留：敌方全体速度 −(\d+)%、命中 −(\d+)%。\*\*终章\*\*：敌方全体定身 ([\d.]+) 刻', {"mech": "melody", "melody": "e_spd_hit", "finale": "stun"}, None),
    (r'驻留：敌方全体攻/速/命中 −(\d+)%。\*\*终章\*\*：敌方全体全属性 −(\d+)%，持续 (\d+) 刻', {"mech": "melody", "melody": "e_all", "finale": "e_all"}, None),
    (r'音刃终结 \+ 沉默 ([\d.]+) 刻', {"kind": "魔法", "mech2": "silence"}, None),
    (r'敌方每携带 1 个负面，受到伤害 \+(\d+)%（上限 \+(\d+)%）', {"passive": "dirge_debuff_dmg"}, None),
    (r'\[AOE\] 全体音刃 \+ 全体沉默 ([\d.]+) 刻', {"aoe": "all", "mech2": "silence"}, None),
    (r'敌方全体定身 ([\d.]+) 刻 \+ 全属性 −(\d+)%，持续 (\d+) 刻', {"mech": "stun", "mech_val": None, "mech2": "all_down"}, None),
]

def map_mech(mech_text: str) -> dict:
    """机制文本 → 引擎字段（返回 dict，可能含 TODO_ENGINE 标记）"""
    out = {}
    matched = False
    for pat, fields, _ in MECH_RULES:
        m = re.search(pat, mech_text)
        if m:
            matched = True
            # 收集正则捕获组（组1开始）
            groups = [m.group(i) for i in range(1, m.lastindex + 1)] if m.lastindex else []
            gi = 0

            def fill_none(v):
                nonlocal gi
                if isinstance(v, dict):
                    return {k: fill_none(vv) for k, vv in v.items()}
                if v is None:
                    if gi < len(groups) and groups[gi] is not None:
                        gv = groups[gi]
                        gi += 1
                        if re.match(r'^[\d.]+$', gv):
                            return float(gv) if '.' in gv else int(gv)
                        return gv
                    gi += 1
                    return None
                return v

            for k, v in fields.items():
                out[k] = fill_none(v)
            break  # 只匹配第一条
    if not matched:
        out["TODO_ENGINE"] = mech_text
    return out

# ============ 生成技能表 ============
PLAYER_SKILLS = {}
BRANCH_SKILLS = {}

CLS_NAMES = {
    "cls_zhan_shi": "战士",
    "cls_fa_shi": "法师",
    "cls_you_xia": "游侠",
    "cls_mu_shi": "牧师",
    "cls_ci_ke": "刺客",
    "cls_wu_seng": "拳师",
    "cls_shi_ren": "吟游诗人",
}

# 分支线名（v153）
BRANCH_NAMES = {
    "cls_zhan_shi": {"A": "狂战士", "B": "盾卫士"},
    "cls_fa_shi": {"A": "元素使", "B": "奥术学者"},
    "cls_you_xia": {"A": "森语者", "B": "风行者"},
    "cls_mu_shi": {"A": "神谕者", "B": "死灵祭司"},
    "cls_ci_ke": {"A": "影舞者", "B": "毒刃者"},
    "cls_wu_seng": {"A": "格斗士", "B": "磐石行者"},
    "cls_shi_ren": {"A": "咏叹者", "B": "挽歌者"},
}

todo_list = []

for cls, tiers in data.items():
    cls_name = CLS_NAMES.get(cls, cls)
    PLAYER_SKILLS[cls] = {"name": cls_name, "skills": {}}
    BRANCH_SKILLS[cls] = {"name": cls_name, "branches": {1: {}, 2: {}, 3: {}}}

    for tier_key, skills in tiers.items():
        # tier_key: base_base / A_T1 / A_T2 / A_T3 / B_T1 / B_T2 / B_T3
        if tier_key == "base_base":
            target = PLAYER_SKILLS[cls]["skills"]
        else:
            line, t = tier_key.split("_")
            branch_name = BRANCH_NAMES.get(cls, {}).get(line, line)
            tier_num = int(t[1])
            target = BRANCH_SKILLS[cls]["branches"][tier_num].setdefault(branch_name, {})

        for sk in skills:
            name = sk["name"].replace("**", "").strip()  # v153 文档加粗残留清理（**冷静** → 冷静）
            info = {
                "lv": int(parse_num(sk["lv"], 1)),
                "mp": int(parse_num(sk["mp"], 0)),
                "power": parse_num(sk["base"], 1.0),
                "kind": sk["kind"],
                "cast": parse_num(sk["cast"], None),
                "name": name,
                "desc": gen_desc(name, sk),
            }
            cd = parse_cd(sk["cd"])
            if cd:
                info["cd"] = cd
            hits = parse_num(sk["hits"], None)
            if hits and hits > 1:
                info["hits"] = int(hits)
            # 机制映射
            mech_fields = map_mech(sk["机制"])
            for k, v in mech_fields.items():
                info[k] = v
            # 职业专属字段
            if "专注" in sk and sk["专注"] not in ("—", ""):
                # v153：游侠专注消耗 → 引擎 res_cost.energy（focus_cost 是设计字段，引擎消费 res_cost）
                info["res_cost"] = {"energy": int(parse_num(sk["专注"], 0))}
            if "信念" in sk and sk["信念"] not in ("—", ""):
                info["faith"] = int(parse_num(sk["信念"], 0))
            if "推条" in sk and sk["推条"] not in ("—", ""):
                info["shaken_gain"] = int(parse_num(sk["推条"], 0))
            if "TODO_ENGINE" in info:
                todo_list.append((cls, tier_key, name, info["TODO_ENGINE"]))
                # 保留 desc 用机制文本，机制留空待接线
                info["desc"] = sk["机制"]
            # key：基础用 sk_+pinyin，分支用中文名
            if tier_key == "base_base":
                skey = f"sk_{pinyin_key(name)}"
            else:
                skey = name
            target[skey] = info

# ============ 输出 ============
def fmt_info(info: dict, indent: str = "             ") -> str:
    """格式化技能 dict（对齐 v151 紧凑格式）"""
    parts = []
    order = ["lv", "mp", "power", "kind", "cast", "cd", "hits", "mech", "mech_val",
             "shaken_gain", "res_cost", "faith", "effect", "cond", "aoe", "pierce",
             "lifesteal", "summon", "passive", "stance", "auto", "charge", "accuracy",
             "crit", "target", "kill", "no_mp", "kind_override", "mech2", "mech2_val",
             "melody", "finale", "sleep", "TODO_ENGINE", "name", "desc"]
    for k in order:
        if k not in info:
            continue
        v = info[k]
        if k == "desc":
            parts.append(f"{indent}'desc': '{v}'")
        elif isinstance(v, dict):
            # JSON → Python 字面量：null→None, true→True, false→False
            js = json.dumps(v, ensure_ascii=False)
            js = js.replace(": null", ": None").replace(": true", ": True").replace(": false", ": False")
            parts.append(f"{indent}'{k}': {js}")
        elif isinstance(v, bool):
            parts.append(f"{indent}'{k}': {str(v)}")
        elif isinstance(v, (int, float)):
            parts.append(f"{indent}'{k}': {v}")
        else:
            parts.append(f"{indent}'{k}': '{v}'")
    return ",\n".join(parts)

lines_out = []
lines_out.append("# -*- coding: utf-8 -*-")
lines_out.append('"""v153 职业体系重做：7 职业 × 42 技能 = 294 技能（脚本生成，勿手改）')
lines_out.append("")
lines_out.append("来源：docs/CLASS_MECHANICS_v153.md → workspace/skills_v153_parsed.json → 本文件")
lines_out.append("策略（鱼鱼拍板）：v153 重做职业，玩家技能已重置，旧技能直接删。")
lines_out.append("  PLAYER_SKILLS 整体替换；BRANCH_SKILLS 统一 3-key；分支技能 key 中文名。")
lines_out.append("  基础技能 key 用 sk_ ID；分支技能 key 用中文名（v151 惯例）。")
lines_out.append('"""')
lines_out.append("")
lines_out.append("_V153_PLAYER_SKILLS = {")
for cls, cinfo in PLAYER_SKILLS.items():
    lines_out.append(f"    \"{cls}\": {{")
    lines_out.append(f"        \"name\": \"{cinfo['name']}\",")
    lines_out.append(f"        \"skills\": {{")
    for sk_name, info in cinfo["skills"].items():
        lines_out.append(f"            \"{sk_name}\": {{")
        lines_out.append(fmt_info(info))
        lines_out.append("            },")
    lines_out.append("        },")
    lines_out.append("    },")
lines_out.append("}")
lines_out.append("")
lines_out.append("_V153_BRANCH_SKILLS = {")
for cls, cinfo in BRANCH_SKILLS.items():
    lines_out.append(f"    \"{cls}\": {{")
    lines_out.append(f"        \"name\": \"{cinfo['name']}\",")
    lines_out.append(f"        \"branches\": {{")
    for tier_num in (1, 2, 3):
        lines_out.append(f"            {tier_num}: {{")
        for bname, skills in cinfo["branches"][tier_num].items():
            lines_out.append(f"                \"{bname}\": {{")
            for sk_name, info in skills.items():
                lines_out.append(f"                    \"{sk_name}\": {{")
                lines_out.append(fmt_info(info, "                        "))
                lines_out.append("                    },")
            lines_out.append("                },")
        lines_out.append("            },")
    lines_out.append("        },")
    lines_out.append("    },")
lines_out.append("}")

content = "\n".join(lines_out)

if DRY:
    print(f"=== 干跑：将生成 {len(content)} 字符 ===")
    print(f"PLAYER_SKILLS: {sum(len(v['skills']) for v in PLAYER_SKILLS.values())} 技能")
    print(f"BRANCH_SKILLS: {sum(sum(len(b) for b in v['branches'].values()) for v in BRANCH_SKILLS.values())} 技能")
    print(f"\n=== TODO_ENGINE 待接线: {len(todo_list)} ===")
    from collections import Counter
    tc = Counter(t[3] for t in todo_list)
    for txt, cnt in tc.most_common(30):
        print(f"  [{cnt}] {txt[:80]}")
else:
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"已写入 {OUT} ({len(content)} 字符)")
    print(f"TODO_ENGINE: {len(todo_list)} 条待接线")
