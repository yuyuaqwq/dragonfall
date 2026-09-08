# N5b4-5a 副本战斗重写版施工图 v2（battle2 原生，鱼鱼 2026-09-08 拍板）

> 取代 v1（补丁版）。鱼鱼拍板：**不在 4005 行老 instance.py 上打洞**——副本战斗
> 直接用 battle2 原生重写（新控制器文件），旧战斗代码整段删除，不留镜像/兼容壳。
> 上一级缺口设计见 `REFACTOR_v181P4_N5B5_instance_gap_design.md`（5E 钩子已落地）。

---

## 0. 目标架构

```
玩法壳（instance.py 保留 ~2000 行）            新控制器（instance_battle.py 新文件）
  开本/组队/地图/探索/调查/宝箱/撤退/任务   →   战斗 = battle2 原生
  命令路由到控制器
        │  st["players"] 视图（只读，控制器同步）      │
        └──────────────  st（副本实例状态） ───────────┘
                              st["battle"] = battle2 to_state（战斗权威，sides actors）
```

- **战斗权威** = `st["battle"]`（battle2 to_state：sides 全员 actors + now + killed）
- **无镜像**：旧 p_buffs/p_hot/p_defending/mech_stacks/enemies/boss/enemy/charging/
  cooldown 战斗键全删（actors 内）
- **视图垫片**（唯一双写点）：每刻落盘时把 actors 状态同步回 st["players"] +
  st["boss"]/st["enemies"]（玩法壳只读旧键不炸）——集中在控制器一个函数
- **DB 同步**：战斗每刻把存活玩家 hp/mp 写回 DB（保留现行为 _sync_players_db）

## 1. 新文件 `game/commands/instance_battle.py`

### 1.1 `build_battle(st, group_id) -> B2`
遭遇/切怪/Boss 战入口（替换 `_enter_stage_combat`/切怪段的 Battle 构造）：
```python
def build_battle(st, group_id):
    sides = {"player": [], "enemy": []}
    for k in st["members"]:
        if not st.get("alive", {}).get(str(k), True):
            continue
        snap = st["players"][str(k)]
        sides["player"].append(_player_actor(snap, st, k))
    for u in st.get("enemies") or []:
        sides["enemy"].append(BR.monster_to_actor(u))
    b = B2("instance", sides=sides, title_bonus={},
           target_picker=<5b>, on_event=<5b>)      # 5a 先 None
    st["battle"] = b.to_state()                     # battle2 state 落 st
    return b
```
`_player_actor(snap, st, k)`：player_to_actor(snap) + 合并 p_buffs→buffs /
p_hot→hot / p_food_effects→food_effects / p_defending→defending /
charging / cooldown / resources / mech_stacks→stacks / p_shields→shields /
ct / stat_bonus（全字段映射见 v1 §1.1，此处 actors 是权威后这些 st 键在建战斗时
一次性搬入，之后只从 actors 回读视图）。

### 1.2 `act(st, group_id, qq_id, action, skill_name, target) -> (logs, ended, who_key)`
真人行动入口（替换 `_instance_act` 战斗段）：
```python
def act(st, group_id, qq_id, action, skill_name, target):
    b = B2.from_state(st["battle"])
    my = <player side 中 qq_id 匹配 actor>（副本轮转已由命令层确认轮到）
    tgt = <目标 actor 或 None>（heal/buff → None 防奶敌，同 PVP）
    logs, ended, who = b.human_act(action, skill_name, actor=my, target=tgt)
    st["battle"] = b.to_state()
    return logs, ended, who
```
### 1.3 `sync_views(st, group_id)` —— 唯一视图/DB 同步点
每刻行动落盘后调：actors → st["players"]（hp/mp/max/buffs 视图）+ st["boss"]/
st["enemies"]（存活敌视图 + 死亡入 killed 账 + 压缩语义由命令层保留 compact）+
st["now"] + DB 血量同步。详细逐字段 = 控制器内 `_BACK_SYNC_*` 同款。

### 1.4 命令层薄壳保留（instance.py 内，读 actors 结果）
- 轮转：下一行动者 = sides player actors ct 最小存活（battle2 schedule 语义，读
  st["battle"] sides）；超时自动防御（薄壳现有逻辑，改读 actors）
- 账务：贡献 dealt/仇恨表 = 命令层自算（现有 hp 差逻辑）
- 通关/失败/肃清/切怪：现有分支保留，改调 build_battle/act

## 2. instance.py 删除清单（被新控制器替代，整段删）

| 函数/段 | 去向 |
|---|---|
| `_instance_act`（2444-3077 战斗主体） | 删（路由改调控制器 act） |
| `_instance_battle_cb`（2395） | 删（5b on_event） |
| `_apply_team_effect`（3078）+ taunt 消费段 | 删（5b on_event 翻译器） |
| CT helpers 全家（3155-3230）：living_player_cts/min_*_ct/next_actor/auto_defend_player/ct_queue/next_player_name | 删或按 §1.4 薄壳重建 |
| `_sync_enemy_unit`（3277） | 删（actors 权威） |
| `_find_skill_cfg`（3233） | 保留（技能数据查询，账务/5b 用） |
| `_instance_seed_*`/`_instance_affix_ids`（1000-1063） | 5a 先保留调用（词条种子行为待拍板）或删（装配批）——见 §5 |
| `_instance_reset_player_cts`（1064） | 删（battle2 ct 由 actors 带）——遭遇重建时 actors 初始 ct 由 build 播种 |
| `_instance_enemies_compact`（1184） | 保留（命令层压缩 st 视图）但简化 |
| `_instance_build_enemy_array`（1132）/`_scale_enemy_copy`/`_mark_minion_copy` | 保留（敌组构造——build_battle 用） |
| `_instance_enemies_alive/_enemy_units/_player_units/_ensure_player_fields` | 保留（视图判定用）或改读 actors |
| 战斗展示 `_instance_battle_footer`（1458） | 保留（改读 actors/st 视图） |

## 3. 路由改造（instance.py 命令层）

| 命令 | 改法 |
|---|---|
| attack/skill/defend（combat.py 内路由 `type==instance` → `_instance_act`） | 改调 `instance_battle.act`（保留 instance.py 入口薄壳做轮转/超时判定） |
| `_enter_stage_combat`（914） | 保留玩法初始化（mode/alive/lock/宠物窗口重置），Battle 构造段 → `build_battle` |
| 肃清/切怪/通关分支（_instance_act 尾段 2793-3045） | 移入命令层新流程函数（act 返回后判定） |

## 4. 测试（tests/test_battle2_n5b4_instance.py）
- build_battle：sides 字段断言（成员 actor 合并 p_*、敌 actor、stat_bonus、ct）
- act 闭环：human_act 后 st["battle"] 更新 + sync_views 后 st["players"] hp 正确
- 多玩家轮转：A 行动 → who/ct → B 轮（min-ct 语义）
- 死亡：敌死 → killed 账 → compact 视图 → 通关/切怪分支
- 增援：sides append（5b/剧本批）
- 回归：battle2 全套

## 5. 边界（随批次补，5a 完成时差异清单）
- 仇恨/嘲讽 → 5b target_picker；团队广播 → 5b on_event
- 旧毒（boss.debuffs.poison δ层）→ battle2 state 不认 → 内容批迁 actor.state dot
- Boss 剧本（mech）→ 5c 导演；宠物 → 宠物批
- 玩家武器词条特效：旧副本 Battle 无 player 装配 → **5a 不装配对齐旧**；是否启用 EP_apply 待鱼鱼拍板
- 词条种子护盾（_instance_seed_battle_start_affixes）：保留调用（行为不变）直到装配拍板

## 6. 验收
- 副本流程测试绿 + battle2 全套绿
- grep 验证：instance.py 与 instance_battle.py 无 `BT.Battle` / 无被删函数残留调用
- 手测：2 人开本 → 普通/精英/Boss 数值战斗主线跑通
- 核心 diff（新控制器 + instance.py 删除 + 路由）→ 鱼鱼过目
