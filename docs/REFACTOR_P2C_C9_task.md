# P2C-C9 任务书：保命/特殊族（proc_dr_revive + proc_special）迁族执行器

> 权威文档：docs/REFACTOR_P2C_weapon_executors.md §3.11（保命/特殊族）+ §4.1（族 12/13）
> 工作分支：wt_p2cc9（worktree w7）｜ 完成后在 wt_p2cc9 分支 commit，不要 merge 到 master

## 目标（行为零变化，数值零变化）

把 weapon_effects.py 里保命/特殊族 5 个 key 从旧 handler 迁入 _we_executors.py 族执行器：

| key | family(表已标) | 表 event | handler 注册事件 | 行为 |
|---|---|---|---|---|
| undying_will | proc_dr_revive | [battle_start, threshold] | @register("battle_start") + @register("undying_will","threshold") | 每场1次 hp<20% 免疫致死 + 回 10% |
| death_dance_armor | proc_dr_revive | (无 event) | @register("passive") | passive taken 减伤 8% |
| death_dance | proc_special | [battle_start, turn_start] | @register("death_dance","battle_start") + @register("turn_start") | 缓伤池 35%→每刻 10% |
| novice_first_turn_guard | proc_special | [battle_start] | @register("battle_start") | 首刻减伤 10%（battle 消费） |
| novice_first_turn_dodge | proc_special | [battle_start] | @register("battle_start") | 首刻闪避 +5%（battle 消费） |

数据表 game/data/weapon_effect_data.py 已标 family/event/参数，C1 已核与 handler 硬编码零差异。

## 要改的文件

1. **game/core/_we_executors.py**：
   - 新增 `proc_dr_revive` 执行器（undying_will 双事件 + death_dance_armor passive 段）
   - 新增 `proc_special` 执行器（death_dance battle_start+turn_start 双事件 + novice 首刻标记 2 key battle_start）
   - WE_EXECUTORS 注册表加 2 族（现有 11 族 → 13 族）
   - **签名**：fn(battle, player, ctx, logs, wd, key, event)——照抄现有族执行器格式

2. **game/core/weapon_effects.py**：
   - `_WE_EXEC_KEYS` 路由表加 5 key：undying_will→proc_dr_revive、death_dance_armor→proc_dr_revive、death_dance→proc_special、novice_first_turn_guard→proc_special、novice_first_turn_dodge→proc_special
   - 原 5 key 的旧 handler **保留但不再被触发**（proc() 分发器先查路由表，命中族执行器后 continue）——不要删旧 handler！C10 才删死代码
   - 注意：`_we_undying_will` 是 @register("battle_start") 单 key，`_we_undying_will_t` 是 @register("undying_will","threshold") 双 key——两个都迁

3. **game/battle.py 消费点改查表（关键！）**：
   - L10976-10980 `_post_hp_lethal`：`EFF.get("we_undying_immune")` → 改读 undying_will 表 immune_key（we_undying_immune）——**0.10 回拉 → 表 hp_pct 读**
   - L10982-10983 `_post_hp_lethal`：`EFF.get("we_death_pool")` + `dmg * 0.35` → 改读 death_dance 表 pool_key/pool_pct（0.35→表读）
   - L10574-10581 `_mitigate_chain`：`EFF.get("novice_guard_active")` → 改读 novice_first_turn_guard 表 mark_key（novice_guard_active）；reduce_pct 已查表（L10577）
   - L10403 `_skill_dodge` 附近：`EFF.get("novice_dodge_active")` → 改读 novice_first_turn_dodge 表 mark_key
   - **铁律**：表驱动，缺字段=无此行为，绝不补默认值

## 行为零变化探针（必须写）

照抄 C6/C7 的探针模式（tests/test_p2cc6_panel_buff_probe.py 为模板）：
1. OLD 路径（绕过路由直接调旧 handler）vs NEW 路径（走 proc() 路由）逐语句等价差分：
   - undying_will：hp<20% 触发 → 免疫标记 + 回血；hp≥20% 不触发；每场 1 次（used 后不再触发）
   - death_dance：battle_start 初始化 pool；受击填充 pool；turn_start 结算 pay
   - death_dance_armor：passive taken 减伤 8%
   - novice_first_turn_guard/dodge：battle_start 置标记；tick>1 后不消费
2. battle 消费点差分：构造玩家濒死场景，OLD（battle 直读硬编码）vs NEW（查表）行为一致
3. **死亡链端到端**：玩家带 undying_will 被一击打死 → 免死回拉不死亡；带 death_dance → 缓伤池正确填充

## 验证清单（全部绿才算完成）

```
python -m py_compile game/core/_we_executors.py game/core/weapon_effects.py game/battle.py
python tests/test_p2cc9_lifesave_probe.py        # 新增探针，OLD==NEW
python tests/test_p2cc9_lifesave_semantics.py    # 新增语义测试（硬断言）
python tests/test_p2cc3_we_shield_semantics.py   # 相关回归（改未族化代表）
python tests/test_v140_weapon_effects.py         # 武器特效回归 12
python tests/test_v140_novice_effects.py         # 新手特效回归（novice 族关键！）
scripts/run_numeric_tests.py                     # 数值门禁 52 全绿
```

## 测试环境（坑！）

- worktree 直接跑测试不行（conftest 需要 data/plugins 父链）——把 worktree 复制到沙盒跑：
  ```
  rm -rf /c/Users/yuyu/AppData/Local/Temp/df_wt_copy9/data/plugins/dragonfall
  mkdir -p /c/Users/yuyu/AppData/Local/Temp/df_wt_copy9/data/plugins
  cp -r <worktree路径>/ /c/Users/yuyu/AppData/Local/Temp/df_wt_copy9/data/plugins/dragonfall
  cd /c/Users/yuyu/AppData/Local/Temp/df_wt_copy9/data/plugins/dragonfall
  "C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe" tests/xxx.py
  ```
- worktree 物理路径：主仓 git worktree list 输出为准（可能是 C:/c/c/... 或 C:/c/...）

## 完成条件

- [ ] 5 key 全部进路由表，走新族执行器
- [ ] battle.py 4 处消费点改查表（0.35 硬编码清零）
- [ ] 探针 + 语义测试新增全绿（含死亡链端到端）
- [ ] test_p2cc3 等回归绿（未族化代表更新为真实未迁 key）
- [ ] numeric 52 全绿
- [ ] git status 干净，commit 到 wt_p2cc9 分支
