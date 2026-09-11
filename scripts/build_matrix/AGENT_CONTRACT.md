# v175 职业×流派平衡矩阵 — Agent 接口契约（冻结版）

> 状态：**冻结**（2026-09-04，格温主 agent 定稿，所有子 agent 照此执行）
> 铁律：任务卡写死怎么做禁全量读；同文件并行=独立新文件+主 agent 合并；引擎主 agent 亲写

## 0. 工程目标（一句话）

7 基础职业 × 3 流派（=转职线）× 42-45 技能 × 5 阶段 → 期望模型全矩阵 + 真引擎抽验 → 门禁断言。
产出 6 个新 `tests/test_numeric_*.py` + `docs/BALANCE_MATRIX_v175.md` 报告。

## 1. 数据事实（已核实，勿重复探索）

| 事实 | 值 | 证据 |
|---|---|---|
| 职业 | 7：战士/法师/游侠/牧师/刺客/拳师/诗人（无隐藏职业） | classes.py CLASSES |
| 技能总数 | **299**（基础 61 + 转职 238），无重名 | skills.py 实测 |
| 每职业技能 | base 8-11 + branch 34 = 42-45 | 实测 |
| BRANCH 结构 | `BRANCH_SKILLS[cid].branches[tier]{线名: {技能名: {...}}}`，tier 1/2/3，每职业2线 | skills.py |
| BUILDS 流派 | 每职业 3 流派，**每流派=1条转职线**（技能从 base 起，跨 tier1→tier3） | builds.py |
| 转职档 | 30/60/90 级（numeric_lib tier 1/2/3；TIER_GROWTH ×1.15/1.30/1.50） | classes.py |
| 技能字段 | lv/mp/power/kind/cast/cd/exprs/mech/mech_val/effect/buff_turns/res_cost/cond/passive/hits/heal_formula/aoe/... | skills.py 299 实测 |
| 资源系统 | job_guide CORE_RESOURCE_GUIDE（cid→key/desc）+ EFFECT_RULES（name/cap 单源；原 core_resources.py 已随 v181.M-R2c 退役）：战士 rage、法师 element(基础无)、游侠 energy(period 18/刻)、牧师 faith、刺客 cp、拳师 chi、诗人 resonance+echo | job_guide.py + battle_rules.py |
| 阶段 | P1(10)/P2(24)/P3(45)/P4(75)/P5(95)；装备档 loadout 见 numeric_lib STAGES | constants.py |
| 副本 | 22 本；单人可进 12 本（min_players=1），多人 10 本（min>=2） | instances.py |
| 技能升级 | SKILL_UP 每技能 max 3-5，p=每级+x% | skill_up.py |

## 2. 文件布局（全部新文件，不碰既有文件）

```
scripts/build_matrix/
  __init__.py
  skill_scan.py      ✅ 已完成（格温）：全技能效率扫描器（skill_efficiency_table）
  schema.py          ⬅️ 本契约落地：字段定义 / 常量 / 校验器
  build_matrix.py    [A1 期望引擎] 主 agent 亲写（依赖各职业 JSON）
  boss_matrix.py     [C2] Boss 侧提取 + 档位表
  rotations.py       读取各职业 JSON 流派循环 → 期望循环模拟
scripts/balance_data/
  cls_zhan_shi.json   [B1-1] 每职业 agent 产出一个（纯数据，无代码）
  cls_fa_shi.json     [B1-2]
  ...（7 个）
```

## 3. 职业 agent 产出 schema（scripts/balance_data/cls_<职业>.json）

每个职业 agent **只产出一个 JSON 文件**（纯数据），包含三块：

```jsonc
{
  "class_id": "cls_zhan_shi",
  "class_name": "战士",
  "resource": "rage",              // 资源 key：rage/element/energy/faith/cp/chi/resonance（单源 EFFECT_RULES/job_guide CORE_RESOURCE_GUIDE）
  "resource_max": 10,              // EFFECT_RULES[key].cap（= 旧 core_resources max）
  "resource_regen_per_tick": 0,    // energy=18 等；无=0
  "builds": {                      // 3 流派，键名与 BUILDS 一致
    "狂战流": {
      "line": "狂战士",             // 对应 BRANCH tier1 线名（BUILDS 内技能同线）
      "role": "dps",               // 定位：dps/tank/heal/support/control
      "attr_preset": {"str": "full"},  // 推荐加点：full主属性 / 或显式 dict
      "rotation": [                 // 流派循环：期望引擎按此模拟（技能名，必须 PLAYER_SKILLS/BRANCH 内）
        {"skill": "挥砍", "cond": "always", "prio": 1, "note": "攒战意"},
        {"skill": "破甲斩", "cond": "always", "prio": 2, "note": "破防+攒意"},
        {"skill": "怒斩", "cond": "rage>=5", "prio": 3, "note": "高怒增伤"},
        {"skill": "嗜血斩", "cond": "cd_ready", "prio": 4, "note": "吸血"},
        {"skill": "战争化身", "cond": "rage==10", "prio": 0, "note": "满怒终结"}
      ],
      "fight_len": 60,             // 模拟战斗长度（轮，与门禁一致）
      "self_heal": true,           // 流派是否有自愈（决定单刷生存）
      "desc": "挥砍/破甲攒战意 → 怒斩战意增伤 → 嗜血斩吸血 → 战争化身真伤终结"
    }
  },
  "attr_presets": {                // 加点预设（每职业 3-4 套，覆盖"不同加点组合"）
    "full_str": {"str": "all"},    // all = 全部自由点投主属性
    "balanced": {"str": 0.4, "agi": 0.3, "vit": 0.3},   // 比例（引擎按比例分点）
    "full_agi": {"agi": "all"},
    "crit": {"str": 0.7, "agi": 0.3}
  },
  "notes": "agent 备注：发现的失衡点/缺口/疑问"
}
```

### rotation cond 支持语法（期望引擎实现，职业 agent 只声明意图）
| cond | 含义 |
|---|---|
| always | 永远可用（无 CD 限制时） |
| cd_ready | 该技能 CD 转好 |
| cd_ready_any | 任选一个 CD 转好的技能（低优先级填充） |
| rage>=N / cp>=N / chi>=N / faith>=N / energy>=N | 资源阈值 |
| resource_full | 资源满（战士 10 怒/刺客 5 点/拳师 10 气等） |
| resource_low | 资源不足（防攒点技空转） |
| enemy_hp_pct<N | 敌人血量低于 N% |
| buff_active:X | 自身有 X buff |
| combo_ready | 连击点≥3 |
| always_after:X | 在 X 技能后紧跟（连招） |

职业 agent **不确定某技能怎么循环就写 always + 低 prio**，宁保守勿瞎编。

### 期望引擎的循环近似规则（agent 须知，勿重复设计）
1. 按 prio 从高到低（0 最高=终结）逐技能看 cond，满足则放，否则看下一技能
2. 技能 CD 未好 / MP 不足 / 资源不足 → 跳过（引擎 _skill_cast_blocked 同语义）
3. 所有技能都不满足 → 普攻（cast_atk）
4. 每行动步进 tick：玩家 ct += (cast+recover)×spd_factor；资源 regen 每 tick +regen
5. 模拟到 fight_len 轮（= tick 数），统计总伤害 / 击杀轮 / 空蓝 / 生存
6. **技能等级按阶段算**：skill_lv = min(SKILL_UP.max, 1+(玩家lv-技能lv)//4)，0=未解锁

## 4. A1 期望引擎接口（主 agent 亲写，子 agent 只产出 JSON）

```python
# scripts/build_matrix/build_matrix.py
def build_panel(cls_id: str, lv: int, loadout: str, attr: dict) -> dict
    # 真实引擎面板（E.player_final_stats + gear_loadout + 属性点分配）

def class_skill_pool(cls_id: str, lv: int) -> dict[str, dict]
    # 该等级可学全部技能（base + 已解锁转职线技能；lv<=玩家lv）
    # 返回 {技能名: info}

def rotation_dps(cls_id: str, lv: int, loadout: str, attr: dict,
                 rotation: list[dict], fight_len: float, target: dict) -> dict
    # 期望循环模拟：{dps, kill_rounds, survive_rounds, empty_mp_rounds, ...}

def build_vs_boss(cls_id: str, lv: int, loadout: str, attr: dict,
                  rotation: list[dict], boss_def: dict, boss_lv: int) -> dict
    # 对 Boss 的击杀轮/生存轮/胜率预估

def full_matrix() -> dict
    # 全职业×流派×阶段×加点×装备 → 大表
```

## 5. A2 真引擎接口（子 agent 产出，主 agent 验收）

```python
# scripts/numeric_lib/battle2.py （或同族）
def battle_rotation(cls_id: str, lv: int, loadout: str, attr: dict,
                    rotation: list[str], boss_def: dict, boss_lv: int,
                    seeds: int = 8) -> dict
    # 真实 BT.Battle 多技能循环：{wins, avg_rounds, avg_survive}
    # 玩家 dict 构造对齐 numeric_sim.player_panel + learned_skills=rotation 全技能
    # 每回合按 rotation 顺序试技能，CD/蓝/资源拦截转普攻（对齐 numeric_sim）

def expect_vs_actual(cls_id, lv, loadout, attr, rotation, boss_def, boss_lv,
                     seeds=8) -> dict
    # 期望模型 vs 真引擎：{expect_kill, actual_kill, delta, verdict}
```

## 6. 阶段 × Boss 匹配（C2 boss_matrix.py）

每职业流派打「该阶段能进的本」——按玩家 lv 对齐 Boss lv：
| 阶段 | 玩家 lv | 装备档 | 单人可进主线 Boss（示例） |
|---|---|---|---|
| P1 | 10 | solo_low 蓝+0 | 哥布林(15/20) |
| P2 | 24 | solo_mid 蓝+5 | 海蚀(22/27) |
| P3 | 45 | team_purple9 紫+9 | 老王(35/40)、圣堂(42/47 需3人) |
| P4 | 75 | team_purple9 紫+9 | 精灵废墟(58/63)、烬山(82/87 偏高) |
| P5 | 95 | team_orange9 橙+9 | 深渊裂隙(90/95)、龙墓(90/95) |

单人职业流派矩阵只打 **min_players=1 的 12 本**（用对应阶段档位）；
10 个多人本沿用既有 team_comp 队伍口径（test_numeric_team_comp），不硬塞单人。
**Boss 侧提取**：读 instances.py，展开 boss_def → C.build_monster 真实面板（boss role 自带 lv/def/mdef/hp）。

## 7. 门禁测试 6 文件（主 agent 组装）

| 文件 | 断言 |
|---|---|
| test_numeric_build_matrix.py | 流派×加点×装备全矩阵期望 DPS 一致性 + 击杀轮带 |
| test_numeric_skill_efficiency.py | 全 299 技能效率审计（无废技 DPE<普攻0.8 / 无超模>4×） |
| test_numeric_build_vs_boss.py | 流派 vs Boss 期望击杀轮带 + 生存≥击杀×0.9 |
| test_numeric_boss_engine_verify.py | 真引擎抽验关键格胜率≥6/8 + 期望vs实测≤1.5轮 |
| test_numeric_attr_sensitivity.py | 加点敏感性（主属性 vs 次优 ≤15%） |
| test_numeric_combo_chain.py | 流派连招正收益（联动>单技能） |

断言先跑基线打印实测 → 审视 → 锁定（铁律：不先跑就写断言 = 拍脑袋）。
**新测试与既有 26 个并存**；run_numeric_tests.py 自动纳入新文件（discover 按文件名前缀）。

## 8. 子 agent 分工（第一波 9 个并行）

| ID | 任务 | 产出 | 依赖 |
|---|---|---|---|
| A1 | 期望引擎 build_matrix.py（**主 agent 亲写**） | 代码 | schema + JSON |
| A2 | 真引擎 battle2.py | 代码 | schema |
| B1 | 战士 JSON | scripts/balance_data/cls_zhan_shi.json | 本契约 |
| B2 | 法师 JSON | cls_fa_shi.json | 本契约 |
| B3 | 游侠 JSON | cls_you_xia.json | 本契约 |
| B4 | 牧师 JSON | cls_mu_shi.json | 本契约 |
| B5 | 刺客 JSON | cls_ci_ke.json | 本契约 |
| B6 | 拳师 JSON | cls_wu_seng.json | 本契约 |
| B7 | 诗人 JSON | cls_shi_ren.json | 本契约 |

**每个 B 类 agent 任务卡（写死，禁全量读）**：
1. 读本职业 PLAYER_SKILLS[cid].skills + BRANCH_SKILLS[cid].branches 全部技能
2. 跑 `python scripts/build_matrix/skill_scan.py <cls_id> 45` 拿到 Lv45 效率基线（口径已定，勿改）
3. 按 schema 产出 JSON：3 流派循环（=3 转职线，技能名必须与 BUILDS/BRANCH 精确一致）
4. 每流派给 role/attr_preset/fight_len/self_heal；4 套加点预设
5. 审一遍自己职业的技能：标出废技能（DPE 明显低）/超模技能/空转 mech（对照 v153 缺口清单）
6. **只写自己的 JSON，禁动任何 .py / 其它 JSON**
7. 校验：`python -c "import json; json.load(open('scripts/balance_data/cls_xxx.json'))"` 合法

## 9. 铁律（所有 agent）

- 禁改 game/ 源码、禁改既有测试、禁 commit（主 agent 统一收尾）
- 不确定就写 note 到 JSON，不瞎编
- 输出中文；报进度只报状态（主 agent 不催）
- 真实数据源：engine skill_info / skill_expr_preview 是唯一伤害口径；不手算倍率

## 10. 变更记录
- 2026-09-04 v1 冻结（格温，含 299 技能全量核实 / BUILDS=转职线映射 / 单人12本决策）
