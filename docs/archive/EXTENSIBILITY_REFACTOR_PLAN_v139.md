# v139 引擎通用机制实现规格（数据驱动 · 复用优先）

> 版本：v139 ｜ 日期：2026-08-29 ｜ 状态：实现基准（所有子 agent 必须遵守）
> 原则：**加内容=加数据，加行为=注册表**；禁止 if-elif 分发链；魔法数字进 constants.py + core/__init__.py 导出
> 目标：13 份职业方案提炼为 **6 个通用引擎机制**，13 个职业全部是数据配置，引擎零职业特判

---

## 〇、总览：6 个通用机制

| # | 机制 | 覆盖职业 | 数据落点 | 引擎落点 |
|---|---|---|---|---|
| 1 | **dual_form 双形态** | 狂战士狂暴/龙裔龙焰/暮影影舞/淬势者倾泻 | core_resources.py 各职业 dual_form 字段 + battle_config.py DUAL_FORM_CFG | battle.py 通用形态机（进入/维持/受击扣/强制回/免费切换） |
| 2 | **focus 架设态** | 法师元素架设/时咒时间凝滞 | core_resources.py 各职业 focus 字段 + battle_config.py FOCUS_CFG | battle.py 通用专注机（进态/增伤/受击加重/打断保护） |
| 3 | **charge 蓄力三律** | 游侠电荷/弓手/时咒 | skills.py 技能 charge 字段 + battle_config.py CHARGE_CFG | battle.py 通用电荷机（边攒边打/打断-1阶/满阶强制释放） |
| 4 | **vent 排气节流阀** | 游侠凝神屏息/星语猎印满5 | battle_config.py VENT_CFG | battle.py 通用排气机（满值触发/强制排气/泄压渠道） |
| 5 | **enemy_bar 挂敌身条** | 拳师破绽/暗影诅咒/斗士晕眩 | battle_config.py ENEMY_BAR_CFG + enemy.buffs 新键 | battle.py 通用敌身条（积蓄/阈值递增/触发/免疫窗口） |
| 6 | **counter 防御即生产** | 战士守线反击/拳师承伤 | skills.py counter_attack 字段（已有）+ battle_config.py COUNTER_CFG | battle.py 复用已有 counter_attack 段（5476-5498） |

---

## 一、dual_form 双形态（通用形态机）

### 1.1 数据字段（core_resources.py 各职业）

```python
# 例：cls_zhan_shi 攻线狂战士
"dual_form": {
    "enter_requirement": 10,     # 资源 ≥ N 可进入（战前可下调）
    "maintain_cost": 1,          # 形态中每回合 -N
    "hit_cost": 1,               # 形态中受击 -N（P3：不清零，单回合至多 N）
    "hit_cost_cap": 1,           # 单回合受击扣减上限
    "force_return": 4,           # 资源 < N 强制回基础形态
    "return_penalty": "none",    # P1 归零无惩罚（不晕/不空过）
    "form": "fury",              # 形态名（显示/战报用）
    "auto_enter": False,         # 是否满值自动进（暮影影舞 True，其余 False）
    "duration": 3,               # 自动形态持续回合（暮影影舞 3）
    "lock_gain": True,           # 形态中是否锁死资源累积（暮影影舞 True）
    "no_hit_clear": True,        # 形态中受击不清空（暮影影舞 True）
}
```

### 1.2 引擎通用形态机（battle.py 新增 ~80 行）

```python
def _dual_form_state(self, player): -> dict  # 读 player["dual_form"] 序列化态
def _dual_form_enter(self, player, logs):    # 进入形态（检查 enter_requirement）
def _dual_form_tick(self, player, logs):     # 回合开始：maintain_cost + force_return 检查
def _dual_form_hit(self, player, logs):      # 受击：hit_cost（cap）+ lock_gain 检查
def _dual_form_exit(self, player, logs):     # 退出形态（免费/主动/强制）
def _dual_form_mult(self, player): -> float  # 形态增伤倍率（读 dual_form.dmg_bonus）
```

### 1.3 关键规则
- **免费切换是承重墙**：进入/退出不占行动、不耗资源（云海核心）
- 强制回形态无惩罚（P1）：回基础形态继续可攒
- 受击不清零（P3）：单回合至多扣 hit_cost_cap
- 序列化：`dual_form` 状态随战斗 to_state/from_state（同 mech_stacks）

---

## 二、focus 架设态（通用专注机）

### 2.1 数据字段（core_resources.py 各职业）

```python
"focus": {
    "enter_turn": 1,             # 进入占 1 回合（站桩吟唱）
    "enter_gain": 1,             # 进入时资源 +N（预装）
    "gain_per_turn": 1,          # 专注中每回合额外 +N 资源
    "dmg_bonus": 0.40,           # 专注中技能伤害 +40%（乘区挂 pmult）
    "taken_bonus": 0.20,         # 专注中受击 +20%
    "interrupt_rate": 0.30,      # 受击打断概率（P3：打断不清零，资源保留）
    "max_turns": 3,              # 维持回合上限
    "blocked": ["attack", "skill", "swap"],  # 专注中禁止的行动（可防御/道具）
    "free_exit": True,           # 主动解除 = 免费无损（承重墙）
    "no_burst_skills": True,     # 增伤不作用于耗资源大爆发技（防 EQ 超上限）
}
```

### 2.2 引擎通用专注机（battle.py 新增 ~70 行）

```python
def _focus_enter(self, player, logs):        # 进入专注（占 1 回合）
def _focus_tick(self, player, logs):         # 回合开始：gain_per_turn + max_turns 检查
def _focus_hit(self, player, logs):          # 受击：interrupt_rate 打断（资源保留）+ taken_bonus
def _focus_mult(self, player, info): -> float  # 专注增伤（no_burst_skills 判定）
def _focus_block(self, player, action): -> bool  # 行动拦截（blocked 列表）
def _focus_exit(self, player, logs):         # 主动解除（免费无损）
```

### 2.3 关键规则
- 打断不清零（P3）：被打断资源保留，只退出专注
- 增伤不作用于耗资源大爆发（防 EQ 超上限，时咒教训）
- 免费解除（承重墙）

---

## 三、charge 蓄力三律（通用电荷机）

### 3.1 数据字段（skills.py 技能级）

```python
"charge": {
    "max": 3,                    # 电荷上限（阶数 0-3）
    "gain_per_turn": 1,          # 每回合蓄 1 阶（蓄力动作）
    "dmg_per_stage": [0.7, 1.3, 1.9],  # 边攒边打：各阶自动出伤倍率
    "interrupt_penalty": 1,      # 打断仅 -1 阶不清零（P3）
    "force_release": True,       # 满阶强制释放（不占行动）
    "release_power": 2.8,        # 满阶释放威力
    "release_extra": {"pierce": True, "reach": 3},  # 满阶释放附加
}
```

### 3.2 引擎通用电荷机（battle.py 新增 ~60 行）

```python
def _charge_tick(self, player, logs):        # 蓄力回合：+1 阶 + 边攒边打出伤
def _charge_hit(self, player, logs):         # 受击：-interrupt_penalty 阶（不清零）
def _charge_release(self, player, logs):     # 满阶强制释放
def _charge_state(self, player): -> dict     # 电荷状态（序列化）
```

### 3.3 关键规则
- 蓄力也出伤（0.7/1.3/1.9 边攒边打）
- 打断仅 -1 阶不清零（P3）
- 满阶强制释放（不占行动）

---

## 四、vent 排气节流阀（通用排气机）

### 4.1 数据字段（battle_config.py）

```python
VENT_CFG = {
    "trigger": 100,              # 资源 = 上限触发排气
    "auto": True,                # 回合开始自动执行（不占玩家决策）
    "reset": 0,                  # 触发后资源归 N
    "bonus": {"seg_bonus": 1, "low_cost_max": 25},  # 排气后下回合低耗技段数 +1
    "bonus_duration": 1,         # 加成持续回合
    "vent_on_dodge": 15,         # 闪避成功泄压 -15
    "vent_on_move": 15,          # 机动技施放泄压 -15
    "max_delay": 1,              # 最大可推迟回合（深排）
}
```

### 4.2 引擎通用排气机（battle.py 新增 ~40 行）

```python
def _vent_check(self, player, logs):         # 回合开始：资源 ≥ trigger → 强制排气
def _vent_apply(self, player, logs):         # 排气：reset + bonus 生效
def _vent_relief(self, player, amount, logs): # 泄压渠道（闪避/机动成功时调用）
def _vent_delay(self, player, logs):         # 推迟排气（max_delay 内）
```

### 4.3 关键规则
- 满值强制排气（P3 防死锁）
- 位移/闪避泄压（位移从成本变收益）
- 排气后低耗技段数 +1（补偿）

---

## 五、enemy_bar 挂敌身资源条（通用敌身条）

### 5.1 数据字段（battle_config.py）

```python
ENEMY_BAR_CFG = {
    "shaken": {                  # 拳师破绽
        "max": 50, "decay_per_turn": 4,
        "threshold_base": 50, "threshold_inc": 1.35, "threshold_cap": 2.5,
        "auto_trigger": True, "immune_turns": 1, "phase_preserve_pct": 0.5,
        "trigger_effect": "skip_turn",  # 触发：敌方跳过下回合行动
    },
    "curse": {                   # 暗影神谕诅咒
        "max": 1, "decay_per_turn": 0,
        "threshold_base": 1, "threshold_inc": 1.0, "threshold_cap": 1.0,
        "auto_trigger": True, "immune_turns": 0, "phase_preserve_pct": 1.0,
        "trigger_effect": "debuff",  # 触发：全队对目标 +20% 伤害 + 命中 +10%
    },
}
```

### 5.2 引擎通用敌身条（battle.py 新增 ~60 行）

```python
def _enemy_bar_gain(self, enemy, bar_key, amount, logs):  # 积蓄注入
def _enemy_bar_tick(self, enemy, logs):                    # 回合开始：衰减 + 阈值检查
def _enemy_bar_trigger(self, enemy, bar_key, logs):        # 触发效果执行
def _enemy_bar_preserve(self, logs):                       # 阶段转换保留（phase_preserve_pct）
```

### 5.3 关键规则
- 积蓄挂敌身（enemy.buffs 新键），独立于异常免疫
- 阈值递增（×threshold_inc 封顶 threshold_cap）防无限控
- 触发后免疫窗口（immune_turns）防连控锁死 Boss
- 阶段转换保留部分积蓄（进度遗产）

---

## 六、counter 防御即生产（复用已有）

### 6.1 已有实现
- battle.py:5476-5498 counter_attack 段（拳师反击已接线）
- skills.py passive proc="counter_attack"（守护姿态等）
- DEFEND_REDUCE=0.5（_do_defend）

### 6.2 新增（battle_config.py）

```python
COUNTER_CFG = {
    "guard_counter_dmg": 0.40,   # 守护姿态受击自动反击 40%
    "guard_counter_res_gain": 3, # 反击时回怒 3
    "guard_counter_flat": 1,     # 回合末保底回怒 1
    "break_counter_dmg": 0.40,   # 破格自动衔接低伤盾击 40%
    "break_counter_thresh": 3,   # 受击 ≥3 触发破格衔接
}
```

### 6.3 落地
- 复用已有 counter_attack 段，新增数据配置
- 不新增 if-elif 分发

---

## 七、通用引擎落地清单（battle.py 新增函数汇总）

| 函数 | 机制 | 行数估计 |
|---|---|---|
| `_dual_form_state/_enter/_tick/_hit/_exit/_mult` | 双形态 | ~80 |
| `_focus_enter/_tick/_hit/_mult/_block/_exit` | 架设态 | ~70 |
| `_charge_tick/_hit/_release/_state` | 蓄力三律 | ~60 |
| `_vent_check/_apply/_relief/_delay` | 排气阀 | ~40 |
| `_enemy_bar_gain/_tick/_trigger/_preserve` | 敌身条 | ~60 |
| COUNTER_CFG 接线 | 防御即生产 | ~20 |
| **合计** | | **~330 行** |

## 八、数据驱动铁律（子 agent 必须遵守）

1. **禁止在 battle.py 写职业特判**（`if class_name == "cls_zhan_shi"`）——一切走数据字段
2. 新增常量必须进 `core/constants.py` + `core/__init__.py` 导出
3. 新增字段必须兼容旧数据（无字段 = 默认不启用）
4. 序列化：新状态字段必须进 to_state/from_state（同 mech_stacks）
5. 不单开版本号文件，数据并入既有 battle_config.py / core_resources.py / skills.py
6. 每块改完 py_compile + 相关单测；不 commit（主 agent 收尾）
7. 数值改动必须过 run_numeric_tests.py 门禁

---

*本规格是 v139 全职业实现的**引擎基准**。子 agent 按「波次」分工，全部遵循本规格，禁止各自为政。*
