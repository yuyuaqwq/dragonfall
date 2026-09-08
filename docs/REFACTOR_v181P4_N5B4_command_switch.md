# N5b-4 命令层切换详细设计（字段/函数级施工图 v2）

> 2026-09-08 鱼鱼要求详细设计方案文档（具体到字段/函数）。本文档取代 N5B_调用映射表
> 的零散映射，给出**可逐行执行的施工图**：每个文件怎么改、每个函数签名、字段去向。
> 分支 wt_ebuffs（worktree df_wt_ebuffs/w1），HEAD b276bdd。baseline：battle2 12 测试全绿。
> 前置产物已就绪：battle2_bridge（N5b-1）/ cmdflow 测试（N5b-3）/ 开战仪式（N5b-2）
> / EP.apply_to_actor 装备装配（N9）/ act_done 事件（N9A-2）。

---

## 0. 目标与红线

- **目标**：命令层 9 文件从 `from .. import battle as BT` 切到 `game.battle2`，
  `BT.Battle` → `B2.Battle(sides=...)`，battle2 引擎零改动（鱼鱼拍板选项 B/A 混合：
  引擎干净，适配在命令层+桥）。
- **红线 1**：battle2 引擎文件（game/battle2/*.py）不改——适配全在命令层/桥。
- **红线 2**：存量旧档（无 sides）作废清档重开（migrate 代码已删，不复活）。
- **红线 3**：每步独立验证（cmdflow 测试 + battle2 全套绿），分批 commit v181.N5b4.X。
- **北极星**：战斗级元数据（map/name/hp/dot_res/adapt）不进引擎对象——存 battle_state
  外壳（state 的顶层兄弟键）。

---

## 1. 命令层要切的总账（9 文件 → 实际动 6）

| 文件 | 改动程度 | 说明 |
|---|---|---|
| game/commands/combat.py | 🔴 大 | 野外/野王/世界Boss/PVP 构造+行动+展示 |
| game/commands/instance.py | 🔴 大 | 副本战斗状态机（最复杂） |
| game/commands/economy.py | 🟡 中 | 约战/比试战斗构造+恢复 |
| game/commands/player.py | 🟢 小 | 战斗内实时面板（读 actor stats） |
| game/commands/tower.py | 🟢 小 | 塔层战斗构造+存盘 |
| game/commands/world.py / base.py / misc.py / social.py | ⬜ 0 | 仅 import 未实际用 → 删 import 即可 |

---

## 2. 构造/恢复/存盘统一改法（所有文件共用）

### 2.1 开战构造（替换 `BT.Battle(btype, enemy, tb, player=..., pet=..., enemies=...)`）

```python
# 新（命令层统一走桥，禁止手拼 sides）：
from ..services import battle2_bridge as BR
from ..services.battle2_equip_proc import apply_to_actor as EP_apply   # N9 装备装配

# ① 开战仪式（player dict 侧，纯数据搬运；效果执行 N5b 增量）
BR.prepare_player_for_battle(player, self._title_bonus(group_id, qq_id), db)

# ② 组 sides（player + 怪组 + pet）
sides = BR.build_sides(player=player, enemies=group, allies=None)

# ③ 装备装配（weapon_effect + affix → actor.triggers；N9.7 已支持 42 affix）
for _a in sides.get("player", []):
    EP_apply(_a)

# ④ 构造
b = B2.Battle("monster", sides=sides, title_bonus=tb, pet=db.pet_get(qq_id))
```
> ⚠️ **pet 处理**：旧引擎 pet 是玩家侧跟随者参与战斗；battle2 Battle 构造 pet 参数
> 目前只存不驱动（N5b-1 桥现状）。**N5b-4 首批不驱动宠物战斗**（宠物技能/普攻后续
> 单独批），pet 参数照传保持构造兼容，展示照旧。

### 2.2 恢复（替换 `BT.Battle.from_state(battle["state"])`）

```python
b = B2.Battle.from_state(battle["state"])   # 同签名！新档直用
```
- 无 sides 的旧档 → 命令层清档重开：`db.clear_battle` + 提示重新遭遇
- from_state 后不需要设 `b._focus`——battle2 focus() 返回 human_controlled actor

### 2.3 存盘（不变）
```python
db.save_battle(gid, qid, b.to_state())
```
- battle2 to_state 已是 sides 结构（serialize.py），DB 层无改动

### 2.4 ⚠️ 玩家回写（battle2 actor 是副本，旧引擎引用传递自动同步已失效）

旧 Battle 构造时把 player dict 当 `_focus` 引用，行动后 `player["hp"]` 自动是最新值；
battle2 的 player actor 是 make_actor 副本。**每次 human_act 后必须回写**：
```python
logs, ended, who = b.human_act("attack", None, b.focus(), target=_target)
BR.sync_player_from_actor(player, b.focus())   # actor → player dict（hp/mp/buffs/shields/...）
```
- sync 字段全量见 bridge `_BACK_SYNC_SCALARS`（hp/mp/max_hp/max_mp）+ `_BACK_SYNC_BAGS`
  （buffs/debuffs/shields/cooldown/hot/charging/defending/ct/state/resources/stacks/eff/...）
- 时机：① 每次行动后 db.update_player 前 ② 战斗结束结算前 ③ 展示面板前
- 胜利/失败/逃跑后玩家 buffs/叠层也回写（旧档战斗中带状态逃跑=下场携带，语义保留）

### 2.5 展示辅助读取（battle2 actor 直读，替代 b._p_*）

| 旧调用 | battle2 等价 | 位置 |
|---|---|---|
| `b._p_buffs_bag()` | `b.focus().get("buffs") or {}` | _status_line |
| `b._p_stacks()` / `b.mech_stacks` | `b.focus().get("state") or {}` | _status_line（**stacks→state 语义需核对**） |
| `b._p_shields_bag()` | `b.focus().get("shields") or {}` | _status_line |
| `b._p_res()` | `b.focus().get("state") or {}`（旧 resources→state 映射见 §4） | _resource_line |
| `b._p_poi_buff()` | `b.focus().get("poi_buff")` | 战斗读祝福 |
| `b.enemies` | `b.sides_of("enemy")` | 各展示 |
| `b.enemy`（主目标） | `_b_enemy` 改读 `b.sides_of("enemy")[0]` 存活 | 展示/结算 |
| `b._enemy_dead()` | `not any(alive in sides["enemy"])` | 结果判断 |
| `b.e_defending` | 敌 actor `["defending"]` | PVP |
| `b._focus["charging"]` | `b.focus()["charging"]` | 施法打断 |
| `b._p_poi_buff` / `b._p_buffs_bag` 内 `stealth` | `b.focus().get("buffs", {}).get("stealth")` | 潜行消散提示 |

---

## 3. combat.py 逐函数改造表（9 处构造 + 行动 + 展示）

| 行区 | 函数/位置 | 现状（BT） | 改法（B2） |
|---|---|---|---|
| 191 | 野王遭遇 | `BT.Battle(...)` | §2.1 构造 |
| 346/415 | 普通探索遇怪 | `BT.Battle(...)` | §2.1 构造 |
| 925 | attack 命令恢复 | `BT.Battle.from_state` + `b._focus = player` | §2.2 恢复 + 删 _focus 行 |
| 942 | attack 行动 | `b.actor_act("attack", ...)` | `b.human_act(...)`（签名一致）+ §2.4 回写 |
| 946-950 | attack 后 db.update_player | 读 player dict | 回写后照旧 |
| 962-990 | victory/defeat/fled 结算 | `b._p_buffs_bag().get("stealth")` / `_origin_enemy` / `killed_enemies` | `b.focus().get("buffs",{}).get("stealth")`；击杀列表 `b.killed_actors`；主怪引用见 §5 |
| 998-1000 | 战斗后展示 | `_battle_footer(player, b, monster)` | 同签名（内部改读） |
| 1165 | skill 命令恢复 | `BT.Battle.from_state` | §2.2 |
| 1187 | skill 行动 | `b.actor_act("skill", ...)` | `b.human_act(...)` + 回写 |
| 1505/1562 | defend/flee 恢复+行动 | `BT.Battle.from_state` / `actor_act` | §2.2 + human_act |
| 2095 | 世界Boss 构造 | `BT.Battle("worldboss", ..., dmg_mult=...)` | §2.1 构造 + `hostile_map` 缺省；dmg_mult 传 B2 构造（签名有） |
| 2526 | PVP 构造 | `BT.Battle("pvp", ..., enemies=[dict(opp...)])` | §2.1 构造（opp 做 enemy side，human_controlled=True 由 PVP 流控制） |

### 3.1 世界Boss 分支（特殊：血量同步/战斗级元数据）

现状（worldboss_act ~2060-2079）：`b.setdefault("map"/"name"/"hp"/...)`、`b["name"]=...`
——把战斗级字段直接塞 Battle dict。battle2 Battle 不是 dict，不能塞。

**外壳方案（§0 北极星）——用 to_state 顶层 meta 键（不加 db 列）**：
```python
# 构造后存盘前：命令层把战斗级元数据塞 to_state 顶层（serialize 只认已知键，
# from_state 忽略多余键 → meta 只给命令层读，不污染引擎）
st = b.to_state()
st["meta"] = {
    "btype": "worldboss", "name": boss_name, "map": cur_map_id,
    "hp": boss_hp, "dot_res": 0.0, "adapt": 0.0,
    "uid": boss_uid, "_player_hit": False,
    "stamina_charged": False,   # ⚠️ 旧实现防重复扣体力的标记也进 meta（见下）
}
db.save_battle(gid, qid, st)
# 恢复/展示读：
meta = (battle["state"].get("meta") or {})
```
- 恢复行动后再次 to_state 时 **meta 保留**：命令层每次行动取 `battle["state"].get("meta")`
  塞回新 st["meta"]（battle2 to_state 本身不带 meta——命令层封装一个
  `_battle_to_state(b) -> dict`：`st = b.to_state(); st["meta"] = 当前 meta; return st`）
- ⚠️ **db.save_battle 的 monster 列**（展示宿主昵称）读 `state["enemies"]`——battle2
  to_state 只有 sides！两处处理：
  1. `game/store/battle_state.py _monster_display_name` 兼容 sides：
     ```python
     enemies = state.get("enemies")
     if not isinstance(enemies, list) or not enemies:
         sides = state.get("sides") or {}
         eacts = sides.get("enemy") or []
         if eacts:
             return eacts[0].get("name", "") or ""
     ```
  2. 命令层可主动在 st 塞 `st["enemies"] = [敌 actor 展示 dict]` 兼容旧列（备选）
- ⚠️ **体力防重复标记**：旧 save_battle 从旧 state 继承 `stamina_charged` 防战斗内
  第二击重复扣体力——battle2 无此字段，命令层在 attack/skill 里自己判
  `meta.get("stamina_charged")`（首击扣体力后置 True，续存继承）
- 世界Boss 全局血量同步：battle2 敌 actor 死亡不从 sides 移除（只进 killed_actors）
  → 同步读 `sides_of("enemy")[0]["hp"]` 照旧；同步逻辑在命令层不在引擎

### 3.2 展示辅助函数改造（combat 内 6 个方法）

| 方法 | 现依赖 | 改法 |
|---|---|---|
| `_b_enemy(b)`（已 sides 化 ✅） | 读 b.sides_of("enemy") | 不动（但确认返回存活） |
| `_status_line(player, b)` | `_p_buffs_bag/_p_stacks/_p_shields_bag` + ACT_TICK 折算 | 全改 `b.focus()` 直读；**buff 形态差异见 §4.2** |
| `_resource_line(player, b)` | `_p_res()`（旧 resources） | `b.focus().get("state")` 按 core_resource_def 读（映射见 §4.3） |
| `_battle_formation_panel(player, b)` | b.enemies | `b.sides_of("enemy")` 只读存活 |
| `_battle_footer(player, b, monster)` | monster dict 入参 + b._now | 入参不变；b._now battle2 有 |
| `pet_battle_status_note(pet)` | 纯 pet dict | 不动（pet 未驱动，照旧显示） |

### 3.3 `_status_line` 详细改法（最难，字段级）

battle2 buffs 条目形态（N7.1 定稿）：`buffs[key] = {"expire": 绝对时刻, "stat", "op", "mult"}`
旧展示按 `int 刻号/特殊键/绝对到期` 三形态判断——battle2 只有绝对到期形态。

```python
def _status_line(self, player, b):
    pbuf = []
    actor = b.focus()
    _now_t = float(getattr(b, "_now", 0.0) or 0.0)
    bf = actor.get("buffs") or {}
    for k, e in bf.items():
        if not isinstance(e, dict):           # 旧 int 残留/异常 → 跳过（N7.1 后不再写）
            continue
        nm = self._P_BUFF_NAMES.get(k)
        if not nm:
            continue
        # 显示折算：expire 绝对时刻 → 剩余刻
        exp = e.get("expire")
        if exp is None:
            pbuf.append(nm)                    # 永久 buff（无到期）
        else:
            left = float(exp) - _now_t
            if left > 0:
                pbuf.append(f"{nm}(剩{max(1, int(round(left / ACT_TICK)))}刻)")
            else:
                pbuf.append(nm)
    # 盾：expire_at 同款折算（保留原逻辑只换数据源）
    for sname, s in (actor.get("shields") or {}).items():
        if (s or {}).get("value", 0) > 0:
            ...  # 同旧逻辑（expire_at - now 折算刻）
    # 敌方 buffs：b.sides_of("enemy")[0] actor 的 buffs 同款
    ...
```
- ⚠️ `_P_BUFF_NAMES` 键表对齐：battle2 buff key 沿用旧名（atk_up/spd_down/stealth/...）
  → 名字表不改；但**控制/元素印记等 battle2 存 state 容器**（不是 buffs）→ 敌方
  debuffs/state 折算另加段落（读 enemy `state` dot 层/`shields`）。
- 具体差异表（旧→battle2 读法）：
  | 旧形态 | battle2 容器 | 显示 |
  |---|---|---|
  | p_buffs int/浮点到期 | actor.buffs[key].expire | 剩余刻 |
  | 控制 stun/freeze | actor.buffs[tag]（control 动词写） | 剩余刻 |
  | 叠层 stacks | actor.state[key]（层数 int） | ×n |
  | 护盾 shields {expire_at,value} | 同构 | 盾值+剩余刻 |
  | debuffs DOT | enemy.state[key]（dot 层） | ×n |
  | dot_res/adapt 战斗级 | meta 外壳 | 读 meta |

---

## 4. 语义映射表（旧 → battle2，字段级权威）

### 4.1 结果/行动
| 旧 | battle2 | 备注 |
|---|---|---|
| b.result "victory"/"defeat"/"fled" | 同字段 | battle2 `_check_side_end` 写 |
| b.actor_act(action, skill, player, target) | b.human_act(action, skill, actor, target) → (logs, ended, who) | 签名顺序一致 |
| b.actor_turn(action, skill, player, enemy_act=) | 无直接等价 → human_act + 手动控 actor_auto | PVP 每回合驱动改命令层（§6） |
| b.btype | 构造传入，同字段 | — |
| ACT_TICK（combat import from battle） | **保留**（battle.py 常量导出，N10 删旧前不动） | — |

### 4.2 buffs 形态（最重要差异）
- 旧：`player["buffs"]["atk_up"] = 12`（int 到期刻号）或 dict 混合
- battle2：`actor["buffs"]["atk_up"] = {"expire": 123.4, "stat": "atk", "op": "mul", "mult": 1.3}`
- 命令层凡是 `if b._p_buffs_bag().get("stealth")` 这种**只查存在性**的判断 → 改
  `if b.focus().get("buffs", {}).get("stealth")`（真值判断兼容 dict）
- 凡是读数值折算刻 → 按 §3.3 统一改
- ⚠️ battle2 无 `debuffs` 概念（N7 收口进 state 容器）——敌方减益读 `enemy.state` + 声明表

### 4.3 resources/stacks → state 容器（职业资源映射）
- 旧双轨：`player["resources"]["rage"]`、`player["stacks"]["combo"]`
- battle2：`actor["state"]["rage"]`（资源 = 数值层，cap 由 STATE_EFFECTS 声明）
- 桥 `player_to_actor` 不隐式迁移（防错误灌入）；命令层在开战仪式后、战斗前调用
  **职业模块翻译**（N5b 后续批：core_resource_def 声明 → state 层）——N5b-4 首批
  若职业资源展示错乱可接受（等职业模块，`_resource_line` 返回空串不崩即可）

### 4.4 玩家 actor vs player dict 的字段差异（桥已处理）
| 字段 | 桥处理 |
|---|---|
| class_name/level/equipment/skills/learned_skills | make_actor 透传 |
| class_tier/attributes/evolve_path/race | 透传（stats 重算用） |
| lv（怪） | monster_to_actor 转 level |
| auto_act（怪 AI） | 透传（battle2 actor_auto 读） |
| 战斗级标签（rank/role/is_boss/exp/gold/drops/...） | 透传未知 key |
| player buffs/shields/cooldown/hot/charging/defending | 同构透传 |
| player stacks/resources | **不自动迁**（需职业模块翻译） |

---

## 5. 击杀/结算处理（胜利结算要主怪引用）

旧：`b._origin_enemy`（v126.7 修）/ `b.killed_enemies` / `self._b_enemy(b)` 兜底。
battle2：
- **死亡不移除**（已核实 battle.py `_on_actor_dead` 只 append 到 `killed_actors`，
  不 pop 出 sides）→ `sides_of("enemy")` 始终含尸体（hp=0）→ 读存活必须过滤
  `actor_alive`；主怪引用 = 构造时命令层保存的 `_origin_enemy = sides["enemy"][0]`
  引用（victory 结算读 exp/gold/drops，hp 0 不影响）
- 击杀列表：`b.killed_actors`（list of actor dict；serialize 存 uid 列表恢复时重挂）——
  副本任务/extra_kills 用它
- 展示过滤：`_b_enemy(b)` 改 = `next((a for a in sides_of("enemy") if actor_alive(a)), None)`

---

## 6. PVP 分支（最难之一）

现状（_pvp_start/_pvp_act ~2311-2600）：`b.actor_turn(..., enemy_act=False)` 真人轮流、
`b._pvp_snapshot`、超时判定、`e_defending`、敌方 charging。

battle2 方案：
- 构造：sides={"player": [玩家, 对手(敌侧 human_controlled=True)]} + hostile_map 双向
- 行动：`b.human_act(action, skill, actor=当前行动者, target=对方)`——battle2 act() 已支持
  任意 actor 决策（focus() 返回第一个 human_controlled——PVP 双方都是，focus 语义要处理）
- ⚠️ focus() 只返回第一个 human_controlled → PVP 命令层要显式拿"当前该行动的人"
  （battle2 无 p_ct 概念单焦点；PVP 真人轮流由命令层驱动，交替传 actor）
- 超时/快照：读 `sides_of("player")[0]` / `[1]` 的 actor 状态
- 敌方 charging/defending → 敌 actor 字段直读
- 具体分步：PVP 放最后切（等野外/世界Boss 稳定）

---

## 7. instance.py 副本（最复杂，单独批次）

现状：副本状态机 _instance_act ~1000+ 行：怪组增援（e_minions）、_tick_actor_dots 强制
结算、p_ct/行动点、killed_enemies 计数、from_state 后按 ct 排 enemy_act 事件。

battle2 方案：
- 构造/行动同 §2；`battle._instance_act` 改调 `b.human_act`（副本真人输入同野外）
- **怪组增援**：battle2 sides["enemy"] append actor（命令层持有 sides 引用）→ 新怪
  进 battle；`b.sides_of("enemy")` 展示含增援
- DOT 强制结算：battle2 schedule 在 advance 自动结算 → 命令层不需要 `_tick_actor_dots`
  （删）；跨刻推进由 human_act 内 advance 完成
- p_ct/行动点：battle2 CTB 用 `actor["ct"]` + schedule.advance——命令层"轮到谁"看
  human_act 返回 who
- killed 计数：b.killed_actors（副本任务/结算读 uid）
- 副本"每场限时/行动点"类规则：命令层用 battle._now 折算（battle2 _now 同语义）
- instance 单独验证（副本流程测试——需拟真 DB + 队伍状态）

---

## 8. 轻文件改造

### economy.py（约战/比试，3 处 BT.Battle）
- 构造：§2.1（对手做 enemy side；比试可无装备/宠物参数照传）
- 恢复：§2.2；行动后 §2.4 回写
- 胜利结算：读 sides + killed_actors（约战奖品看 result）

### player.py（战斗内实时面板 1 处）
- `b._player_stats(player)` → battle2 读 `b.focus()` 后 `stats.actor_stats(b, actor)`，
  或桥 `BR.player_stats(player)`（= E.player_final_stats 薄封装）

### tower.py（1 处构造+存盘）
- §2.1 构造 + to_state 存盘（无行动命令，纯开战）

### world/base/misc/social
- 删 `from .. import battle as BT` import（无实际用点）；如报错引用补查一次

---

## 9. 批次计划（每批验证 + commit）

| 批 | 内容 | 验证 |
|---|---|---|
| N5b4-1 | combat.py 展示辅助改造（_status_line/_resource_line/面板——**纯读函数先切**，不依赖引擎构造） | battle2 全套 + cmdflow |
| N5b4-2 | combat.py 探索/野王/普通遇怪构造切 B2 + attack/skill/defend/flee 行动切 B2 + 回写 | cmdflow + 手测战斗闭环 |
| N5b4-3 | 世界Boss 分支（meta 外壳 + db.save_battle meta 列 + 血量同步） | 世界Boss 手测 |
| N5b4-4 | PVP 分支（focus 处理/轮流行动/超时） | PVP 手测 |
| N5b4-5 | instance.py 副本（增援/DOT 自动/killed） | 副本流程测试 |
| N5b4-6 | economy/player/tower 轻文件 + 删 4 文件 import | 全量回归 |
| N5b4-7 | 全命令层回归（服务测试 + 真实 DB 探针）+ 汇报鱼鱼过目 diff | run_all |

依赖：db.save_battle 加 meta 参数（第 3.1 节）建议在 N5b4-3 前置单独小 commit。

---

## 10. 风险与对策

| 风险 | 对策 |
|---|---|
| 玩家战斗核心改错 = 玩家打不了架 | 每批手测闭环 + 服务测试；PVP/instance 最后切 |
| battle2 buff 形态差异导致展示错乱 | §3.3 展示先切（纯读），语义差异测试锁定 |
| stacks/resources 未迁 state | 首批只保证展示不崩（空串），职业模块补翻译 |
| pet 未驱动 | 首批照传不驱动，pet 展示不动；单独后续批 |
| from_state 后 focus 返回 None（无 human_controlled） | 恢复路径断言 + 兜底 kind=player 首个存活（battle2 focus 已有） |
| 击杀后 sides 移除语义不清 | §5 NOTE：实施时读 landing/battle 确认后写测试 |
