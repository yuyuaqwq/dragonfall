# N5b4-5a 副本主流程 battle2 化 —— 施工图（字段/函数级）

> 2026-09-08。分支 wt_ebuffs。上一级缺口设计见 `REFACTOR_v181P4_N5B5_instance_gap_design.md`。
> 本批范围：**_instance_act 的"重建 Battle → 行动 → 回写"三明治换成 battle2**，
> 让副本数值战斗主流程跑在 battle2 上。仇恨/团队广播（5b）、Boss 剧本（5c）、
> 宠物（宠物批）不在此批——期间对应能力退化（见 §7 行为差异清单）。

---

## 0. 现状（要替换的段）

`_instance_act`（instance.py 2444-3077）每次玩家行动：
1. `BT.Battle.from_state({50 键 from st})` + `b._focus = snap`（2551-2606）——旧 Battle 重建
2. `b.actor_act(action, skill, snap, enemy_act=True, target)`（2611）——旧 Battle 一次跑完
3. 从 `b.*` 读回 20+ 键写 st（2621-2710）——回写
4. 副本层账务/轮转/通关判定（命令层，保留）

## 1. st ↔ battle2 sides 字段映射（权威）

### 1.1 玩家 actor（sides["player"] = 存活成员，序 = st["members"]）
构造：`BR.player_to_actor(snap)` 后合并 st 顶层 per-player 键：

| battle2 actor 字段 | 来源 |
|---|---|
| 身份/面板（uid/name/side/kind/human_controlled/class_name/level/equipment/skills/learned_skills/class_tier/attributes/evolve_path/race/hp/mp/max_hp/max_mp） | snap（player_to_actor 透传；hp/mp 当前值） |
| `buffs` | st["p_buffs"][k]（旧引擎 Battle 内写回 p_buffs → battle2 actor.buffs） |
| `hot` | st["p_hot"][k] |
| `food_effects` | st["p_food_effects"][k] |
| `shields` | snap["p_shields"]（快照上键） |
| `defending` | st["p_defending"][k] |
| `charging` | st["charging"][k] |
| `cooldown` | st["cooldown"][k] |
| `resources` | st["resources"][k]（职业资源——先透传旧名，battle2 state 翻译后续职业批） |
| `stacks` | st["mech_stacks"][k] |
| `combo_seq` | st["combo_seq"][k] |
| `state` | 缺省 {}（旧副本无 state 容器；dot 迁移见 §7） |
| `ct` | snap["ct"]（绝对时刻，battle2 同语义） |
| `stat_bonus` | 开本时快照 title_bonus 折算（N5b4-4c 通用容器；快照构造处 177 行 title_bonus 键 → 改名 stat_bonus + 塞 actor） |
| `pet`（Battle 参数） | st["pets"][k]（暂不驱动） |
| 装备装配 EP_apply | **决策点**：旧副本 Battle 无 player 构造 → 玩家武器/词条 triggers 从未装配（护盾词条靠 _instance_seed_battle_start_affixes 手工种子）。battle2 化若 EP_apply 会让副本玩家装备特效首度生效（行为变化）。**5a 先不装配**（对齐旧），装配差异列 §7 待鱼鱼拍板 |

### 1.2 敌方 actor（sides["enemy"] = st["enemies"] 全量，含爪牙/增援）
构造：`BR.monster_to_actor(u)`（透传 rank/reach/role/is_boss/is_elite/uid/ct/...；lv→level）。

| 来源键 | battle2 | 备注 |
|---|---|---|
| st["enemies"] 每单位 | enemy actor | uid 保留（任务/压缩/锁定用） |
| 死亡单位 | **不移除**（actor hp=0 留在 sides；st 压缩由命令层做） | 与旧 _remove_unit 差异见 §5 |
| 增援/召唤 | 命令层 append actor 进 sides["enemy"] 且 append st["enemies"]（同一批单位双写） | e_minions 概念退役 |

### 1.3 回写（行动后：st = f(actors)）
| st 目标 | actor 来源 |
|---|---|
| st["players"][k] hp/mp/max_hp/max_mp | 各玩家 actor（sync 标量） |
| st["p_buffs"][k] | actor["buffs"] |
| st["p_hot"][k] / st["p_food_effects"][k] | actor["hot"] / actor["food_effects"] |
| snap["p_shields"] | actor["shields"] |
| st["p_defending"][k] | actor["defending"] |
| st["charging"][k] | actor["charging"] |
| st["cooldown"][k] / st["resources"][k] / st["mech_stacks"][k] / st["combo_seq"][k] | 对应 actor 键 |
| snap["ct"] | actor["ct"]（battle2 _after_act 已推） |
| st["enemies"] | sides["enemy"] actors（hp/buffs/defending/charging/state 写回每单位；**死亡单位不写回 st**——命令层按 actor hp<=0 压缩进 _last_killed） |
| st["now"] | battle._now |
| st["killed_enemies"] | battle.killed_actors uid 并入（去重） |
| （退役）st["tick_effects"] | battle2 无 tick 卡（DOT 随 actor.state；5a 先空） |
| （退役）st["dot_pending"] | battle2 schedule 自结算；5a 副本旧毒未迁前见 §7 |

## 2. 新 helper（instance.py 新增）

### 2.1 `_instance_build_battle2(st, group_id, cur_key)` -> B2
```python
def _instance_build_battle2(self, st, group_id, cur_key):
    """副本每次行动重建 battle2（从 st 组 sides）。
    - player side = 存活成员 actors（合并 st 顶层 per-player 键 + stat_bonus）
    - enemy side = st enemies actors
    - target_picker/on_event = None（5b 注入；此批敌方行动回落默认目标）
    """
    from ..services import battle2_bridge as BR
    from ..battle2 import Battle as B2
    sides = {"player": [], "enemy": []}
    for k in st["members"]:
        if not st.get("alive", {}).get(str(k), True):
            continue
        snap = st["players"][str(k)]
        a = BR.player_to_actor(snap)               # 身份/面板透传
        for frm, key in (("p_buffs","buffs"), ("p_hot","hot"),
                         ("p_food_effects","food_effects"), ("p_defending","defending"),
                         ("charging","charging"), ("cooldown","cooldown"),
                         ("resources","resources"), ("mech_stacks","stacks"),
                         ("combo_seq","combo_seq")):
            v = (st.get(frm) or {}).get(str(k))
            if v is not None and key not in a:
                a[key] = v
        _psh = (snap.get("p_shields") or {})
        if _psh:
            a["shields"] = dict(_psh)
        a["ct"] = float(snap.get("ct", 0) or 0)
        a["stat_bonus"] = dict(snap.get("stat_bonus") or {})   # 5a 起快照带通用增幅
        sides["player"].append(a)
    for u in st.get("enemies") or []:
        sides["enemy"].append(BR.monster_to_actor(u))
    return B2("instance", sides=sides, title_bonus={},
              pet=(st.get("pets") or {}).get(str(cur_key)) or {})
```
- ⚠️ p_defending 现状是 st["p_defending"][k] bool；battle2 actor defending bool 同构 ✓
- hp/mp：snap 是行动权威（行动前 _enter_stage_combat/切怪已刷新）→ player_to_actor 透传 ✓

### 2.2 `_instance_sync_battle_back(st, b, cur_key)` -> None
```python
def _instance_sync_battle_back(self, st, b, cur_key):
    """行动后：battle2 actors → st（每人标量/状态键 + 敌阵列 hp + now + 击杀并入）。"""
    # ① 玩家侧回写（含当前行动者；战斗内引擎可能改任何存活 actor——回血/盾/毒）
    from ..services.battle2_bridge import sync_player_from_actor
    _by_uid = {}   # 敌 uid → actor（压缩用）
    for _a in b.sides_of("enemy"):
        _by_uid[str(_a.get("uid",""))] = _a
    for _a in b.sides_of("player"):
        _k = str(_a.get("qq_id") or "")
        if _k not in (st.get("players") or {}):
            continue
        snap = st["players"][_k]
        sync_player_from_actor(snap, _a)          # hp/mp/max/buffs/defending/charging/...（含 _BACK_SYNC_*）
        st.setdefault("p_buffs", {})[_k] = _a.get("buffs") or {}
        st.setdefault("p_hot", {})[_k] = _a.get("hot") or {}
        st.setdefault("p_food_effects", {})[_k] = _a.get("food_effects") or []
        st.setdefault("p_defending", {})[_k] = bool(_a.get("defending", False))
        st.setdefault("charging", {})[_k] = _a.get("charging")
        st.setdefault("cooldown", {})[_k] = _a.get("cooldown") or {}
        st.setdefault("resources", {})[_k] = _a.get("resources") or {}
        st.setdefault("mech_stacks", {})[_k] = _a.get("stacks") or {}
        st.setdefault("combo_seq", {})[_k] = _a.get("combo_seq") or []
        snap["p_shields"] = _a.get("shields") or {}
        snap["ct"] = float(_a.get("ct", 0) or 0)
        # 倒地标记（O105 语义：行动者自伤/毒发后 hp<=0）
        if snap.get("hp", 0) <= 0 and st.get("alive", {}).get(_k, True):
            st["alive"][_k] = False
    # ② 敌阵列写回（死亡单位不写回——st 压缩在调用方做）
    alive_enemies = []
    for _a in b.sides_of("enemy"):
        if (_a.get("hp") or 0) > 0:
            alive_enemies.append(_a)
        # 死亡：把 battle2 actor 状态并进 st["killed_enemies"]（uid 记账）
    #   命令层调用方用 _by_uid 匹配原 st 单位同步存活者状态（hp/buffs/defending/charging）
    ...
    # ③ 时刻
    st["now"] = float(getattr(b, "_now", 0.0) or 0.0)
```
- 详细"存活敌单位逐字段写回"与"死亡去重入账"在实施时对齐现有 `_instance_enemies_compact` + killed 合并逻辑（保留函数，只改数据来源）。

## 3. `_instance_act` 逐段改法

| 段（现状行） | 改法 |
|---|---|
| 2551-2603 构造 dict | → `b = self._instance_build_battle2(st, group_id, cur_key)` |
| 2604-2606 `b._focus = snap` / `_pct_before` | 删（actor 副本；回写走 helper）；调试变量改读 my actor ct |
| 2611 `b.actor_act(...)` | → `act_logs, ended, _who_next = b.human_act(action, skill_name, actor=<当前玩家 actor>, target=<解析目标 actor 或 None>)` |
| 目标解析 | 保留 `_instance_extract_target`（名字→找 sides actor/`target` 传 actor dict；'a1/b2/编号'→自动） |
| 2621-2710 回写段（p_buffs/.../enemies/killed/tick/pet/ct/now/defending/charging/p_shields） | → `self._instance_sync_battle_back(st, b, cur_key)`；tick_effects 序列化段删；pet 写回段删（Battle pet 只存，写回无意义）；killed 并入 helper 内 |
| 2637 `st["round"] = b._tick_no()` | → 命令层展示轮次（round 递增保留原语义，从 _now 折算或 st 自增） |
| 2688 `st["now"]` | helper 内 |
| 2704-2710 killed_enemies 并入 | helper 内 |
| 2775-2791 team_effects 消费 | 5a 先置空（技能 team 字段效果暂缺 → 列 §7）；taunt 仇恨 5b |
| 2722-2756 dealt/仇恨/防御挑衅 | 保留（dealt 用 enemies_before 现逻辑；battle2 敌 actor hp 读同 st） |
| 2759-2773 O105 倒地 | 保留（snap hp 已由 helper 回写） |
| 其余轮转/通关/肃清分支 | 保留 |

## 4. 连带 helper 改动（旧引擎 API 退役点）

| helper | 现状 | 改法 |
|---|---|---|
| `_instance_reset_player_cts` (1078) | `BT.Battle()._player_stats(snap)` 取 spd | → `E.player_final_stats(...)` 直算（同 join_battle 157 口径，含 title_bonus→stat_bonus 键） |
| `join_battle` (198) `BT.Battle()._ct_cost(_spd)` | 旧 cost | → `from ..battle2.schedule import action_time; cost = action_time(_spd, 1.0)`（对齐 battle2 初值语义） |
| `_instance_build_enemy_array` (1143/1146/1172) `BT._ct_initial_wait(spd)` | 旧敌 ct 播种 | → schedule.action_time 同款（或保留旧值——敌 ct 语义须与 battle2 player ct 同轴） |
| `_enter_stage_combat`/切怪 `_instance_reset_player_cts` | 同上 | 同上 |

## 5. 死亡/压缩语义差异（关键！）

- 旧：Battle 内部 `_remove_unit` 击杀即移出 enemies → 副本压 st + killed 账
- battle2：死亡 actor **留在 sides**（hp=0 + killed_actors）→ 命令层在 `_instance_sync_battle_back` 后
  用现 `_instance_enemies_compact(st)` 压缩 st enemies（数据源 = 写回的存活单位 + 死亡 uid 账）
- st["boss"] 兼容键/多动定位（is_boss/uid）逻辑保留（现 1210-1217 已按 uid 处理）

## 6. 测试计划（tests/test_battle2_n5b4_instance.py）

- 拟真 st 构造（1-2 玩家 + Boss/爪牙）：`_instance_build_battle2` sides 字段断言
- 行动闭环：human_act 后回写（hp/ct/buffs/enemies/now）+ 轮转 min-ct 不变
- 多玩家：A 行动（引擎敌自动打默认目标）→ 写回 → B 轮
- 敌死亡：hp<=0 → compact 移除 → killed 账 → 通关分支
- 增援：sides append + st enemies append → 下一轮参与

## 7. 5a 完成时行为差异清单（转后续批/待鱼鱼拍板）

| 能力 | 5a 状态 | 去向 |
|---|---|---|
| Boss 仇恨/嘲讽选目标 | 回落默认（打首个存活玩家） | 5b target_picker |
| 团队技能广播（群奶/群体 buff/taunt） | 不广播 | 5b on_event 翻译器 |
| 副本旧毒（boss.debuffs.poison δ层） | battle2 不认旧格式 → 毒结算断（内容批迁 state dot 或命令层保留） | 内容/DOT 迁移批 |
| 玩家武器/词条特效 | 不装配（对齐旧副本无装配） | 待拍板（battle2 化后是否启用 EP_apply） |
| Boss mech 剧本（转阶段/召唤/低血） | 不触发 | 5c 导演 |
| 宠物参战 | 只存不驱动 | 宠物批 |
| 副本内 p_defending 每行动前清（2532） | 保留命令层语义（非 defend 行动前清自己 defending——battle2 不清） | 5a 内处理：行动前清当前行动者 defending（对齐旧 2532） |

## 8. 验收

- 副本流程测试绿 + battle2 全套绿
- 手测：2 人开本 → 普通/精英/Boss 数值战斗主线跑通（伤害/死亡/轮转/通关/失败）
- 核心战斗文件 diff（_instance_act 大改）→ 鱼鱼过目再提交
