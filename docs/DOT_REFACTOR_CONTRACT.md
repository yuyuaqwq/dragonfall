# DOT/减益重构——接口契约 v1（所有实施 agent 必须遵守）

仓库根：`C:\Users\yuyu\qqbot\data\plugins\dragonfall`（基线 commit `00eee84`）。

## 0. 目标

1. 敌方持续减益（毒/灼烧/标记/流血）从"每玩家 mech_stacks"迁为**目标级状态** `enemy["debuffs"]`，副本/世界 Boss 全局共享单份。
2. 结算频率：单机每玩家行动一次（现状不变）；副本**每轮（全队各行动一次）结算一次**；世界 Boss 全局每 N 次行动结算一次。
3. 层数=剩余回合：每次结算后层数 -1，归零消散；叠层即刷新。
4. 抗性属性 `dot_res`：普通怪 0 / 精英 0.8 / boss 0.9（cap 0.95），结算时乘 (1-dot_res)；`immune_dots` 列表支持完全免疫某类。
5. dot 结算纳入 `_boss_dmg_filter`（护盾 -50%/吸收对 dot 生效）。
6. 毒爆等爆发段保持不吃 dot_res（魔法直伤，受 mdef 约束）。

## 1. 数据结构

```python
# 敌方单位 dict 新增（随 enemy dict 序列化/持久化）
enemy["debuffs"] = {
    "poison": {"n": int, "mult": float},   # n=层数=剩余结算次数；mult=叠毒者被动倍率（刷新取 max）
    "burn":   {"n": int, "mult": float},
    "mark":   {"n": int, "mult": float},
    "bleed":  {"n": int, "mult": float},   # mult 恒 1.0
}
enemy["dot_res"] = float        # 0~0.95，缺失=0（普通怪不设键）
enemy["immune_dots"] = list     # 可选，如 ["burn"]，缺失=[]
```

- 层数 cap：poison/burn/mark 均 5；bleed cap 3（词条来源回合数）。
- 多怪场景：**dot 状态与结算都只挂主目标 `self.enemy`**（不挂爪牙；与现状"伤害按主目标 max_hp 算"一致）。

## 2. Battle 层（game/battle.py）

### 2.1 `_dot_pending` 结算闸门
- `__init__`：`self._dot_pending = True`（单机每次玩家行动=一回合，结算一次；与现状频率一致）
- `from_state`：`self._dot_pending = bool(state.get("dot_pending", True))`
- `to_state`：包含 `"dot_pending": self._dot_pending`
- `player_turn` → `_turn_start` 内（原灼烧/毒/流血三段结算处）：
  ```python
  if getattr(self, "_dot_pending", True):
      self._dot_pending = False
      logs += self._tick_dots(player, logs)
  ```
  删除原 2815-2823（灼烧）、2824-2848（毒）、2849-2859（流血）三段旧结算块。

### 2.2 `_tick_dots(self, player, logs, force=False) -> list`
```python
def _tick_dots(self, player, logs, force=False):
    if not force:
        if not getattr(self, "_dot_pending", True):
            return logs
        self._dot_pending = False
    e = self.enemy or {}
    deb = e.get("debuffs") or {}
    if not deb:
        return logs
    max_hp = int(e.get("max_hp", 1) or 1)
    res = min(float(e.get("dot_res", 0) or 0), 0.95)
    for k, pct in (("poison", 0.05), ("burn", 0.03), ("bleed", 0.05)):
        d = deb.get(k)
        if not d: continue
        n = int(d.get("n", 0) or 0)
        if n <= 0: deb.pop(k, None); continue
        mult = float(d.get("mult", 1.0) or 1.0)
        p = int(max_hp * pct * n * mult * (1 - res))
        # 伤害段：毒/灼烧=magi；灼烧吃火元素抗；流血=phys 吃物免
        if k == "burn":
            p, _ = self._enemy_mitigate(p, p, "fire", logs, kind="魔法", dot=True); dt = "magi"
        elif k == "poison":
            p, _ = self._enemy_mitigate(p, p, None, logs, kind="魔法", dot=True); dt = "magi"
        else:
            p, _ = self._enemy_mitigate(p, 0, None, logs, kind="物理", dot=True); dt = "phys"
        p = self._boss_dmg_filter(p, player, logs, dmg_type=dt)   # 护盾减半/吸收生效
        if p > 0:
            self._damage_enemy(p, logs, wake_sleep=False)
        logs.append(f"☠️/🔥/🩸 【{e.get('name','敌人')}】{毒/灼烧/流血}发作，损失 {p} 点生命！(剩余 {n-1} 层)")
        n -= 1
        if n <= 0:
            deb.pop(k, None)
            logs.append(f"💨 【{e.get('name','敌人')}】的{毒/灼烧/流血}消散了！")
        else:
            d["n"] = n
        if self._enemy_dead():
            self.result = "victory"
            logs.append(f"🎉 你击败了【{e.get('name','敌人')}】！(毒发身亡)")
            break
    return logs
```
（文案按 k 区分：毒发身亡/灼烧致死/失血过多，沿用旧文案；死亡后 break。）

### 2.3 老存档迁移
`from_state` 内：若 `enemy` 无 `debuffs` 且 `state["mech_stacks"]` 含 `poison/burn/mark` 键 → 迁移为 `enemy["debuffs"][k] = {"n": v, "mult": 1.0}` 并从 mech_stacks 删除该键。

### 2.4 常量集中
`battle.py` 模块级：
```python
POISON_PCT = 0.05      # 毒：每层每回合 5% 敌方最大生命（保留旧名兼容外部引用）
BURN_PCT = 0.03        # 灼烧：每层每回合 3%
BLEED_PCT = 0.05       # 流血：每回合 5%（词条 2~3 回合）
DEBUFF_TURNS = 2       # 保留
```
`_tick_dots` 内引用这些常量（不再写死 0.03/0.05）。

### 2.5 其他
- 删除 `_turn_start` 中 `elif "poison" in self.e_buffs:` 老布尔路径（并轨，e_buffs 不再承载毒）。
- `_boss_dmg_filter` 逻辑本身不动（dot 现在会经过它）。

## 3. 机制层（game/core/battle_mech.py）

### 3.1 叠层 handler 改道（写 enemy debuffs，不再写 p_mech）
- `_m_poison(battle, mval, p_mech, total, logs, skill_name, is_crit, info)`：
  - 免疫检查：`"poison" in (battle.enemy.get("immune_dots") or [])` → 提示"免疫中毒"，不叠层、直接 return。
  - `deb = battle.enemy.setdefault("debuffs", {})`；`cur = deb.get("poison") or {"n":0,"mult":1.0}`；
  - `mult`：用 `battle._passive_map(battle._last_player)["proc"].get("poison", [])` 乘算（取 max(旧, 新)）；`cur["n"] = min(5, cur["n"] + mval)`；写回。
  - 日志：`☠️ 毒层 {n}(每回合 {n*5}% 生命，{n} 回合后消散)`。
  - mech_chance 概率逻辑保留（v113.1）。
- `_m_burn` 同理（cap 5，无被动 mult 则 1.0；免疫键 "burn"）。
- `_m_mark`：写 `debuffs["mark"]`（cap 5）+ **保留** `battle.e_buffs["mark"] = DEBUFF_TURNS`（+30% 易伤计时，不动现有 _apply_mark）。
- `_m_poison_burst`（毒爆）：读 `battle.enemy["debuffs"]["poison"]["n"]`；n≥3 引爆（伤害=matk×0.15×n 魔法段吃 mdef，**不吃 dot_res**，现状公式不动）；引爆后清 `debuffs["poison"]`（并 `e_buffs.pop("poison", None)` 保留）。n<3 提示。
- `_m_burn_burst`：读/清 `debuffs["burn"]`。
- `_m_mark_burst`：读/清 `debuffs["mark"]`。
- `_m_cleanse`：**扩展**——保留原"清敌方增益"逻辑，新增：清空 `battle.enemy["debuffs"]`（提示"✨ 净化！敌人的中毒/灼烧/标记被驱散！"）。
- `_stack`/`mech_stack_gain` 不再用于敌方键（engine 函数保留给玩家资源）。

### 3.2 玩家侧不变
rage/shadow/chi/judge/arcane/spellblade/wind/iron/bless/shield 等玩家资源仍写 `p_mech`（mech_stacks），逻辑不动。

## 4. 数据层

### 4.1 game/core/stats.py `monster_stats()`
- role == "boss" → `stats["dot_res"] = 0.9`
- role == "elite" → `stats["dot_res"] = 0.8`
- 其他 role 不设（缺失=0）。
（`game/data/stat_templates.py` 的 MONSTER_ROLE_BASE 不需要加键，直接 stats.py 里加，避免模板表全量改动。）

### 4.2 game/core/affix_effects.py
- `_sp_burn`（烈焰之力，现 L280 写 `e_buffs["poison"]`——**bug**）：改为对 `battle.enemy` 挂灼烧：
  ```python
  deb = battle.enemy.setdefault("debuffs", {})
  cur = deb.get("burn") or {"n": 0, "mult": 1.0}
  cur["n"] = min(5, cur["n"] + 1)
  deb["burn"] = cur
  logs.append("🔥 烈焰之力！敌人被灼烧！")
  ```
- 其他 SET_PROC_EFFECTS 不动（frost 走 e_buffs spd_down 保留）。

### 4.3 game/engine.py
- `MECH_STACK_MAX`：poison/burn/mark 键**保留**（cap 语义仍被 mech_stack_gain 引用，且 test_v59_stack_cap 依赖）；注释修正：
  - `"poison": 5,   # 毒层：5 层 = 每回合 25% 生命（结算后逐层衰减消散）`
  - `"burn": 5,     # 灼烧：5 层 = 每回合 15% 生命（结算后逐层衰减消散）`
- 不改 mech_stack_gain 逻辑。

## 5. 副本层（game/commands/instance.py）

- 构造 from_state（L1409-1436 区域）新增：`"dot_pending": st.get("dot_pending", True)`；enemy 传 `st["boss"]`（已含 debuffs/dot_res）。
- 行动后写回（L1445-1446 区域）：`st["dot_pending"] = False`（本轮已结算）。
- **轮次推进**：在玩家行动后检测"所有存活玩家本轮均已行动"（现有 CTB 逻辑里找挂点；若没有现成集合，新增 `st["round_acted"]` 集合，行动后 add(cur_key)，覆盖全部存活成员时清空并置 `st["dot_pending"] = True`）。
- 切怪/换 Boss（L1563-1596 区域，现 L1577 `st["e_buffs"] = {}` 处）：追加
  ```python
  st["dot_pending"] = True
  st["boss"].pop("debuffs", None)     # 新怪无减益
  for _m in st["members"]: st["mech_stacks"][_m] = {}   # 玩家资源不跨怪
  ```
- 进层/新战斗初始化（L977-1043 区域）：初始化 `st["dot_pending"] = True`。
- poison_all 团队技能（L1731-1737）：改为对**共享** Boss 挂毒：
  ```python
  if kind == "poison_all":
      boss = st.get("boss")
      if boss:
          deb = boss.setdefault("debuffs", {})
          cur = deb.get("poison") or {"n": 0, "mult": 1.0}
          cur["n"] = min(5, cur["n"] + 2)
          deb["poison"] = cur
          logs.append("☠️ 全队武器淬毒！(毒层共享)")
  ```
- **注意**：L1421 `"mech_stacks": st["mech_stacks"].get(cur_key, {})` 保留（玩家资源）；敌方键不再写入其中。

## 6. 世界 Boss 层（game/commands/combat.py）

- 常量：`WORLD_BOSS_DOT_INTERVAL = 4`（全局每 4 次玩家行动结算一次 dot，模拟"一队一轮"）。
- 全局事件数据 `gboss` 增加：`gboss.setdefault("debuffs", {})`、`gboss.setdefault("dot_act", 0)`、`gboss.setdefault("dot_res", 0.9)`（世界 Boss 默认 90% 抗，事件数据可覆写）、`immune_dots` 可选。
- 创建 battle（L2405 区域）：enemy 构建时透传 debuffs/dot_res（`b` 的 enemies 各单位的 debuffs 从 gboss 拷入）。
- `_worldboss_act`（L2435-2480 区域）：
  - 行动前：全局 `gboss["debuffs"]` → 本地 `b.enemy["debuffs"]` 同步（与 hp 同步同处）。
  - 行动后：`gboss["dot_act"] = gboss.get("dot_act", 0) + 1`；若 `gboss["dot_act"] % WORLD_BOSS_DOT_INTERVAL == 0` → `logs += b._tick_dots(player, logs, force=True)`（结算后伤害已写进 b.enemies，随既有 hp 写回全局）。
  - 写回：`gboss["debuffs"] = b.enemy.get("debuffs", {})`（与 hp 写回同处）。
  - 删除 L2465 的 `"毒发身亡" not in x` 过滤（恢复文案）。
- 贡献计算（dealt=before-after）**不动**（dot 已计入，线性正确）。

## 7. 面板显示（game/commands/combat.py）

- 敌方状态栏（L1560-1630 区域）：从 `b.enemy.get("debuffs", {})` 渲染 `☠️毒×N 🔥灼烧×N 🎯标记×N 🩸流血×N`；`dot_res > 0` 时显示 `🛡️毒抗{int(dot_res*100)}%`（或按类型"异常抗性"）。
- `_MECH_CN`/`_ENEMY_MECH_STACKS` 相关键位同步调整（burn/poison/mark 从 mech_stacks 显示逻辑移除，改读 debuffs）。

## 8. 测试（由测试 agent E 第二批统一处理）

- 预期会改的现有测试（E 负责，实施 agent 不要改测试）：
  - `tests/test_commands_battle.py` L104-119（淬毒挂层 → enemy debuffs；e_buffs poison 老路径删除 → 改为 debuffs 毒层递减断言）、L145-152（毒爆）
  - `tests/test_v59_stack_cap.py` L57-63（`_apply_mech_effect("burn",...)` 断言 mech_stacks → 改读 enemy debuffs）
  - `tests/test_v107_mech.py` L109-125（毒爆：`b.mech_stacks["poison"]=3` → `b.enemy.setdefault("debuffs",{})["poison"]={"n":3,"mult":1.0}`）
  - `tests/test_v109_2_combat_mech.py`（灼烧 dot 断言——无抗性怪首 tick 数值不变，层数衰减若有跨回合断言需核对）
  - `tests/test_v59_battle_status.py` L31/41（burn/poison 显示归属）
  - `tests/test_v114_formation.py` L402-412（e_buffs poison 序列化——老键删除后需迁移兼容）
- 新增测试（E 负责）：
  - dot 衰减（5 层→5 回合→消散）；抗性（elite 0.8/boss 0.9 数值）；immune_dots；dot 过护盾（shield boss dot 减半）；副本每轮一次（dot_pending 流转）；切怪清层；poison_all 共享；毒爆不吃 dot_res；老存档迁移。

## 9. 文件职责划分（实施 agent 只改自己的文件）

| Agent | 文件 |
|---|---|
| A（战斗核心） | `game/battle.py` |
| B（机制与数据） | `game/core/battle_mech.py`、`game/core/affix_effects.py`、`game/engine.py`、`game/core/stats.py` |
| C（副本） | `game/commands/instance.py` |
| D（世界Boss+面板） | `game/commands/combat.py` |
| E（测试，第二批） | `tests/` 全部 |

**禁止**：改其他 agent 的文件；改测试（E 专属）；改设计文档（最后统一）。
