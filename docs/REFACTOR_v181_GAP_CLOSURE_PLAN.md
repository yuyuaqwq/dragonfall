# v181 缺口收口方案（磐核 / 召唤 / 挽歌）——引擎改动审批稿

> 2026-09-10 盘点。范围 = 被动 proc 剩余 18 项中可闭合的 10 项（磐核 4 + 召唤 4 + 挽歌 2）。
> 本文档只写**需要引擎侧决策**的部分；纯装配/数据改动另附。
> 结论先行：**10 项里没有一项必须改引擎内部**；唯一要你拍板的是召唤要不要加一个公开 API。

---

## 0. 现状证据（全部代码核对过，非推测）

| 事实 | 证据 |
|---|---|
| `Battle.sides` 是普通 dict，无隐藏缓存 | `battle2/battle.py:62`——`self.sides = {}` 后直接 `list(acts)` |
| CTB 调度**动态**遍历 sides（中途加 actor 自动获得行动） | `battle2/schedule.py:117/132/191` 三处 `for acts in battle.sides.values()` |
| 序列化遍历 sides（新 actor 自动进存档） | `battle2/serialize.py:44` `"sides": {sn: [...] for sn, acts in battle.sides.items()}` |
| **中途加 actor 已有活代码先例** | `commands/boss_script.py:526` `battle.sides.setdefault("enemy", []).insert(0, m)` |
| `Battle` **没有** add_actor / spawn 公开方法 | `battle.py` def 全集：sides_of/hostile_of/focus/alive_*/human_act/advance/auto_run/actor_auto/act/_do_*/_on_actor_dead/_check_side_end/to_state/from_state |
| `period` 每刻机制完整可用（含 float） | `schedule.py:226-345` 周期跳；`battle2_rules.py:121` focus_cost `{dir:gain,amount:18}` / `:148` faith `{amount:-0.7}` |
| 资源渠道机制声明驱动、零硬编码 | `class_mech_proc.py:175` `class_res_channel_gain`——res/gain 全由声明给 |
| 渠道**不支持条件过滤** | `class_mech_proc.py:1308` `_CHANNEL_EVENTS` extra 只有 `{kind:...}` / `{not_basic:True}` |
| judge 条件谓词求值在**装配层** | `class_mech_proc.py:740` `_res_ge_ok(owner, params.get("judge")...)` |

---

## 1. 磐核 4 项（core_full / core_reduce / core_last_stand / core_overflow）

### 设计权威（v153 §六，勿改数值）
```
磐核 0-5（上限 5）
获取：① 守御姿态下受击 +1   ② 守御姿态下每刻 +0.4   ③ 守线技能命中 +1
消耗：磐岩释能 / 磐核爆发 / 磐岩甲
效果：每核 减伤 +3%、反击伤害 +10%；伤害系数每核 +0.7
衰减：战斗中不衰减；战斗结束清零
```

### 判定：**不需要改引擎**（改动落在 `data/` + `services/`）

| 攒端来源 | 落地方式 | 层级 |
|---|---|---|
| ② 每刻 +0.4 | `EFFECT_RULES["guard_core"].period = {"dir":"gain","interval":1.0,"amount":0.4}` | data ✅ 零改动 |
| ③ 守线技能命中 +1 | `channels: {"skill_hit": 1}`（现成时机） | data ✅ 零改动 |
| ① 守御姿态受击 +1 | `channels: {"taken": 1}` + **姿态条件过滤** ← 唯一缺口 | services ⚠️ 装配层新增 |

**唯一需要新增的能力（装配层，非引擎）**：
`class_res_channel_gain` 支持 `when`/`judge` 条件——复用现成 judge 求值器，加一个
`has_effect` 谓词 kind（判 actor.effects 是否含某 key，即"是否处于守御姿态"）。
装配时把渠道声明的 `when` 透传进 trigger 参数，动作入口求值，不满足直接 return。

**被动读取端**（PASSIVE_PROC 加 4 条 + 复用/新增动作）：
```
core_full        → 复用 passive_taken_reduce（减伤段）+ 复用 passive_cc_clear（免控段）
core_reduce      → 复用 passive_taken_reduce（per_core 每核 ×0.02）
core_last_stand  → 复用 passive_taken_reduce（一次性 flag 常驻减伤 0.40）
core_overflow    → 复用 passive_heal_overflow_shield 或新增 passive_overflow_shield
```
> 4 条的 judge 都读 `res_ge {res: guard_core}`（现成谓词），参数照抄旧 handler
> `core/passive_procs.py:999 _h_dr_cond` 的 D0 回填值（`battle2_rules.py:74` 自述缺口即此处）。

**消耗端**：`MECH_CASH` 加 `guard_core_burst`（读磐核数 → 清核 → dmg_mult ×(1+0.7×n)），
照抄 `arcane_burst` 现成写法（`battle2_rules.py`，per_layer 0.7）。

---

## 2. 召唤 4 项（death_contract / undead_faith / skeleton_cap / focus_regen_summon）

### 判定：**技术上不需要改引擎**，但建议加一个公开 API —— **此项需你审批**

三个必需件：① 生成随从 actor ② 计数（亡灵数/随从数）③ 上限。

| 件 | 现状 |
|---|---|
| ① 生成 actor | 引擎侧 `sides` 可写（boss_script 先例），但**无 actor 工厂**；旧 `battle._spawn_companion` 随 N10 删旧 battle.py 消失（测试在 `tests/_retired_old_engine/`） |
| ② 计数 | 无 helper；旧 `battle._undead_count()` 已消失（`passive_procs.py:1350` 用 `hasattr` 兜底 = 恒 0） |
| ③ 上限 | 无；boss 援军是硬编码上限 3（`boss_script.py:463`） |

### 两个选项

**选项 A：内容层自己拼（零引擎改动）**
```python
# services/ 内照 boss_script 写法
battle.sides.setdefault("player", []).append(actor)   # 或 insert(0) 挡刀位
```
- ✅ 立刻能做，不动引擎
- ❌ 三个真问题：
  1. **新 actor 的 `_skill_index` 不建** —— `_index_skills()` 只在 Battle 构造时跑一次
     （`battle.py:81`），中途加的 actor 技能解析不了（auto_act 技能静默空放）
  2. **ct 不播种** —— 构造期的 `initial_ct` 只覆盖开局 actor（`battle.py:86-99`），
     新 actor `ct` 为空 → CTB 排序异常
  3. **框架契约缺失** —— 插件化可分发目标下，"怎么往战斗里加一个单位"没有稳定入口，
     每个插件作者都要抄一遍 boss_script

### 选项 B：引擎加公开 API（推荐）—— ★ 本稿唯一需审批的引擎改动

**改动文件**：`game/battle2/battle.py`（唯一），纯新增 + 两处抽取，**不碰任何现有行为**。

**B1. 抽出单 actor 版技能索引**（现有 `_index_skills` 的循环体 → 方法）
```python
def _index_one_actor(self, actor: dict) -> None:
    """单 actor 技能索引（构造期与运行期注册共用）。原 _index_skills 循环体逐字搬迁。"""
    idx = actor.setdefault("_skill_index", {})
    for sk in (actor.get("skills") or []):
        if sk in idx:
            continue
        info = None
        if actor.get("class_name"):
            info = E.skill_info(actor["class_name"], sk)
        if not info:
            info = E.skill_by_key(sk)
        if not info:
            try:
                info = (C.MONSTER_SKILLS or {}).get(sk)
            except Exception:
                info = None
        if info:
            idx[info.get("name", sk)] = info
            idx[sk] = info

def _index_skills(self):
    """（改写为）遍历 sides → 逐个调 _index_one_actor。语义不变。"""
    try:
        for _acts in self.sides.values():
            for _a in _acts:
                self._index_one_actor(_a)
    except Exception:
        pass  # 索引失败不阻断构造（N1 原行为保留）
```

**B2. 抽出单 actor 版 ct 播种**（现有 `__init__` 播种体 → 方法，同款口径）
```python
def _seed_ct_one(self, actor: dict) -> None:
    """单 actor 初始 ct 播种（构造期与运行期注册共用）。语义 = __init__ 现循环体：
    已有正 ct 不重播；裸 spd 走 stats.actor_spd 聚合口径。"""
    if actor.get("ct") is not None and float(actor.get("ct") or 0) > 0:
        return
    from .schedule import initial_ct as _ict
    _spd = actor.get("spd", 0) or 0
    try:
        from . import stats as S
        _spd = S.actor_spd(self, actor)
    except Exception:
        pass
    actor["ct"] = _ict(_spd)
```
> `__init__` 里原播种循环改为调 `self._seed_ct_one(_a)`——行为等价（原代码同样判 `ct>0` 跳过）。

**B3. 新增公开方法**（唯一新增 API）
```python
def add_actor(self, actor: dict, side: str, front: bool = False) -> dict:
    """向战斗注册一个新 actor（召唤 / 援军 / 变身）。

    - 入 self.sides[side]；front=True 插队首（前排挡刀，对齐 boss_script M-W2s 口径；
      默认 append 尾部）
    - 建 actor["_skill_index"]（复用 _index_one_actor）
    - 播种 ct（复用 _seed_ct_one）——不播种则 CTB 排序异常（新单位 ct 为空）
    - 返回 actor（调用方拿引用做日志/上限记账）

    引擎零游戏知识：不认识"随从/召唤/亡灵/援军"，只做注册 + 索引 + 排程。
    sides 为普通 dict、调度与序列化均动态遍历（schedule.py:117/132/191、
    serialize.py:44），故新 actor 自动参与行动与存档，无需额外同步。
    """
    acts = self.sides.setdefault(side, [])
    if front:
        acts.insert(0, actor)
    else:
        acts.append(actor)
    self._index_one_actor(actor)
    self._seed_ct_one(actor)
    return actor
```

**为什么需要（而不走选项 A）**：A 的三个坑都是引擎职责——
① `_skill_index` 只在构造期建（`battle.py:81`），A 得让每个内容方自己解析技能表，
   等于把引擎的数据桥逻辑复制到插件里（违反"引擎只留动词执行器"的架构哲学）；
② ct 播种同理（`initial_ct` + `stats.actor_spd` 是引擎内部口径）；
③ 框架契约：插件协议需要一个稳定入口，否则每个作者抄一遍 boss_script。

**风险评估**：
- 现有调用点零改动（纯新增方法；B1/B2 是等价抽取，由现有测试兜底）
- 不引入新状态、不新增字段、不动 EFFECT_RULES/PASSIVE_PROC 结构
- 回归闸：全量测试 + 新增 `test_battle2_add_actor.py`

**验收测试**（`tests/test_battle2_add_actor.py`）：
1. `add_actor(a, "player")` → actor 在 `sides["player"]` 末位
2. `add_actor(a, "enemy", front=True)` → 在 `sides["enemy"]` 首位（挡刀位）
3. 新 actor `_skill_index` 非空（给一个已知技能 key）
4. 新 actor `ct > 0`
5. 新 actor 能被 CTB 调度行动（`auto_run` 若干步后 ct 推进 / 有行动日志）
6. `to_state()` 含新 actor；`from_state` 后仍在（存档往返）

### 实施记录（2026-09-10 已落地）

**引擎改动（鱼鱼批准，做干净不留兼容）**：`game/battle2/battle.py` 唯一文件
- 抽出 `_seed_ct_one(actor)` / `_index_one_actor(actor)`（等价抽取，两个调用方同语义；
  索引失败的 N1 政策收敛到 `_index_one_actor` 内部）
- `__init__` ct 播种循环与 `_index_skills` 改写为调用上述两函数
- 新增公开 API `Battle.add_actor(actor, side, front=False)`

**验收**：`tests/test_battle2_add_actor.py` 20 断言全绿（入队语义/索引/ct/CTB 调度/存档往返）

**顺带修掉一个存量活 bug**：`commands/boss_script.py:526` 原为手工
`battle.sides.setdefault("enemy", []).insert(0, m)` —— 只入容器、**不建
`_skill_index`**（技能索引仅 Battle 构造期建一次），而 22/22 副本援军模板均带
`ms_*` 技能 → **Boss 召唤的援军技能全部静默退化为普攻**（线上全覆盖）。
已改为 `battle.add_actor(m, "enemy", front=True)`（索引补齐 + ct 保留 Boss 自设
的 `now+2.0`，不插队）。A/B 验证：旧写法 `test_boss_script_p3` test_8 exit=1，
新写法 29/29。测试补 `test_8_summon_skill_index`。

**药水召唤死路径已清（不留兼容）**：`core/potion_effects.py` 的 `eff_summon`
原调 `battle._spawn_companion`（旧 battle 方法，N10 随删除消失 → 死调用），
`_SUMMON_FACES` 随之成孤儿——两者一并删除；`eff_summon` 改为显式拒绝
（本文件既有惯例，同 `eff_trap` 魅惑分支「尚未接入」），并注明复活路径。
药水召唤复活 = 随从线的一部分（需随从 actor 工厂：属性缩放 / 守卫 / 上限），
与 §2 召唤 4 项同批处理。


---

## 3. 挽歌 2 项（dirge_ctrl_up / dirge_debuff_dmg）

**判定：不需要改引擎。** 均属装配层：
- `dirge_debuff_dmg`（挽歌·极：减益旋律伤害提升）→ 复用 `passive_dmg_mult` + `judge {mech_prefix: [dirge]}`
- `dirge_ctrl_up`（镇魂安魂：控制延长）→ 复用 `passive_bar_extend` 同族写法（控制已是 effect 条目，加 turns 即可）
- 前置：G1 挽歌者 5 技能数据（e_ 减益旋律）先落地

---

## 4. 建议执行顺序

| 步 | 内容 | 层级 | 是否需审批 |
|---|---|---|---|
| 1 | 磐核：period + channels + 4 条 PASSIVE_PROC + guard_core_burst | data + services | ❌ 装配层自主 |
| 2 | 渠道条件过滤能力（`when`/`has_effect` 谓词） | services | ❌ 装配层自主 |
| 3 | 召唤：按你选的 A/B 实施 | 引擎(仅B) | ⚠️ **需审批（本稿）** |
| 4 | 挽歌：数据 + 2 条 PASSIVE_PROC | data + services | ❌ 装配层自主 |
| 5 | 并行派工：装配层项目拆给子 agent | — | ❌ |

> 铁律遵守：引擎改动主 agent 亲写；装配/数据可拆分派工；
> 数值权威 = `docs/CLASS_MECHANICS_v153.md`（本稿所有数值均引用该文档，未自创）。
