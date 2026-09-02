# v163 副本战斗修复：敌方伤害丢失 + Boss 打不死（一套代码定稿）

> 日期：2026-09-02
> 触发：鱼鱼实测哥布林营地 Boss 房"怪物 0 伤害 + Boss 打不死"（round 63、召唤 9+ 爪牙）
> 范围：game/battle.py + game/commands/instance.py + game/core/battle_mech.py + game/data/instances.py
> 状态：✅ 已落地（全量回归 + 数值门禁 + 本地打通验证）

## 1. 三个根因

### 1.1 敌方读条伤害跨消息丢失（引擎级 bug，野外同样中招）

v154 读条命中制后：敌方出手瞬间只排 `cast_done` 事件，读条结束才结算伤害。
玩家读条状态有持久化（`_player_casting`/`_pending_player_cast` 在 to_state/from_state），
**敌方读条没有对称物** → 敌方每次"挥爪扑向你(1.5s)"排的 cast_done 一旦跨消息存档即丢。

**复现**：`scripts/repro_enemy_cast_loss.py`（纯引擎，野外单怪同样丢失敌方伤害）：
```
敌方出手日志: ['⚔️ 【哥布林守卫】挥爪扑向你！(出招 2.7s)']
出手后事件队列: [(2.67, enemy_act), (12.67, cast_done e)]  ← 命中在 12.67s
恢复后事件队列: [(12.67, enemy_act)]                        ← cast_done 丢了！
玩家 hp: 500 → 500（敌方造成伤害: 0）                      ← 伤害蒸发
```

**修复**（引擎层，野外/副本一套代码）：
- `_enemy_turn` 出手（技能/普攻）时把命中参数写入单位 dict `e["_cast"] = {hit_at, kind, skill, power_mult}`——随 enemies JSON 序列化自动持久化
- `Battle.from_state` 恢复时：对读条中的敌方（`_cast` 存在且 `hit_at > now`）补排 cast_done 事件
- cast_done 结算后清 `e["_cast"]`（防重复补排）

### 1.2 instance.py v158 合并残留旧轮转敌方段（副本双重行动）

v158 把 `player_turn` 改成 `enemy_act=True`（battle 队列驱动敌方），但 `_instance_act`
玩家行动后仍残留调 `_instance_enemy_ct_acts`（旧手动轮转）→ **敌方双重行动** + 旧轮转
用瞬态 Battle 排 cast_done 从不结算 → 大量"挥爪"日志但伤害蒸发。

**修复**：删除 `_instance_act` 里 2628-2649 残留的 `_instance_enemy_ct_acts` 调用段，
改为纯玩家侧收尾（倒地失败检测 + 下一行动玩家 = 存活玩家 ct 最小者）。
敌方行动统一由 `player_turn(enemy_act=True)` 的 battle 事件队列驱动。

### 1.3 Boss 召唤无 CD/无上限/召唤物=Boss 比例（策划案缺陷）

鱼鱼拍板三层：
1. **召唤 CD 5 刻**（原每 3 刻 1-2 只，频率爆炸）
2. **场上援军上限 3 只**（含开怪自带爪牙；机制召唤/技能召唤同走 `_summon_minions` 统一生效）
3. **召唤物 = 同图小怪模板**（原 Boss×0.2：咕噜 9482 血 vs 同图小怪 564 血，量级错 16 倍）

## 2. 代码改动

| 文件 | 改动 |
|---|---|
| game/battle.py | ① 敌方读条持久化（`_enemy_turn` 写 `e["_cast"]` + from_state 补排 cast_done + 结算后清）② `_summon_minions` 场上上限 3（`SUMMON_MINION_CAP`）+ 优先从副本 inst.minions[].monster 模板 build_monster 构建（同图小怪数值），无配置回落 Boss×0.2 兜底 |
| game/commands/instance.py | ① 删 v158 残留旧轮转敌方段（`_instance_enemy_ct_acts` 调用）② `_instance_build_enemy_array` 从副本 inst.minions[].monster 模板构建开怪爪牙（`_mark_minion_copy` 新方法），旧 name/role 配置兜底 ×0.5 |
| game/core/battle_mech.py | ① `SUMMON_MINION_CAP=3`/`SUMMON_MINION_CD=5` 常量 ② `_b_summon` CD 5 刻、单次 1 只、满员跳过 |
| game/data/instances.py | 两副本 minions 配置改为 monster 模板引用：哥布林营地=哥布林守卫 lv15×2、海蚀洞窟=海史莱姆 lv22×2（同图小怪） |

## 3. 验证

- ✅ `repro_enemy_cast_loss.py`：敌方伤害从 0 恢复为正常结算（跨两次存档恢复）
- ✅ Boss 房模拟：开怪爪牙 20840 → **564 血**（小怪档）；召唤受控 2-4 只；Boss 血量稳定下降
- ✅ **真实打通**（sim_mech_clear.py）：35 级战士真实战斗 157 轮击杀咕噜 → `cleared=True` + 首通成就
- ✅ test_commands_battle / test_v116 / test_v137_dungeon / test_v104_battle_skills 全绿
- ✅ 数值门禁 17/17 全绿

## 4. 策划案同步

- 27 章 §2.5：野外 Boss 爪牙注明 ×0.5 相对 ×0.7 主怪；副本 Boss 编成单独规则
- 27 章 §2.6：敌方援军数值 = 独立小怪模板（v163 定稿）+ CD 5/上限 3
- 27 章 §2.7：副本 Boss 队伍 minions = 引用同图怪池小怪模板（非 Boss×0.5）
- 04 章 机制表召唤行：CD 5 刻、同图小怪模板、上限 3

## 5. 遗留

- 生产库鱼鱼/散人 round 63 卡住的旧存档仍存在（旧爪牙 20840 血残留），修复后再次行动会以旧 enemies 阵列继续——建议鱼鱼撤退重开本（旧存档爪牙是 Boss×0.5 的过时数据，不会自动修复）
- 模拟器脚本保留在 scripts/（repro_enemy_cast_loss.py / sim_mech_clear.py / sim_boss_verify.py 等），供后续副本回归复用
