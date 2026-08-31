# R1 任务卡：battle.py 修复（预检口径 + 硬编码入表 + 日志规范化）

## 背景
v130.2c/d 审计发现（详见 6 审计汇总，本卡只列你要做的）：
- P1：`_skill_cast_blocked`（预检）与 `_do_player_skill`（扣减）消耗口径分裂
- P2：5 处消费端硬编码阈值未读数据表
- P3：战斗日志泄漏资源内部 key、echo 日志丢失、满资源误报

## 修复清单（全部在 game/battle.py，CRLF 文件——多行替换用 python io.open(newline='') 精确 needle，patch 工具仅限单行）

### 1. 预检口径统一（P1×2，最重要）
- **P1-1 精力刀刃折扣**：预检（约 1800 行 `_skill_cast_blocked` 内 energy 分支未应用 energy_blade 词条折扣，只应用 `_energy_cost_after_sets` 套装折扣）；扣减路径（约 1871 行）两者都应用 → 玩家持精力刀刃时施放被预检误拦「精力不足！需要 50，当前 48」。修法：提取统一折算函数（如 `_energy_cost_reduce(player, info, base_cost)` 先词条折扣再套装折扣），预检与扣减共用（预检用折算后值校验、扣减用同一函数）。
- **P1-2 双声明技能**：skills.py 数据侧无畏冲击（res_cost {rage:10} + consume_all）与神恩降临（res_cost {faith:10} + consume_all）双声明 → 预检 consume_all 分支通过后**继续落入 res_cost 满额校验**，持 4 怒被拦「需要 10，当前 4」。修法二选一（**推荐：引擎侧 else 分叉**，不动 skills.py 数据以免影响其他机制）：预检与施放的 consume_all 分支处理后 `else` 跳过 res_cost 校验（`if consume_all: ... else: res_cost 校验`）。同时确认施放侧（约 1842-1864）逻辑一致。
- 修完自查：`_skill_cast_blocked` 与 `_do_player_skill` 两处消耗语义完全同源。

### 2. 硬编码阈值入表（P2×5，读 sets.py 12 套 effect dict 确认字段名）
- **套装全耗减免「留 1 点」**：`_left = 1 if cur >= 2 else 0`（约 1858/1860）→ 改 `_left = int(eff.get("value", 1))`（接住 `_set_eff` 返回值；元素使徒/余烬军团的 effect value=1）。
- **猎首 50/100 档阈值**：`_base >= 50`（约 2476）→ sets.py 猎首条目 effect 增 `"min_cost": 50`，消费端读数据。
- **日冕二档判定**：`faith >= 5`（约 2490）→ sets.py 日冕 effect 增 `"miracle_min": 5`，消费端读数据。
- **影纱 5 件 cap**：`cap = per * 8`（约 1064）→ 数据增 `"max_layers": 8`（sets.py 影纱 bonus_5），消费端读；读不到 fallback 8。
- **势不可挡判定过宽**（约 2509-2511）：`cls_wu_seng 或 任意 res_cost/consume_all 物理技` → 收窄为 **chi 资源相关**（res_cost.chi / consume_all key=="chi" 或 cls_wu_seng），与词条 burst_break（battle.py:818 同款）口径一致。
- **暗夜圣典 elegy_dmg 满档判定**（约 2505）：desc 说「满档」但无条件生效 → sets.py 暗夜圣典 effect 增 `"cond": "canticle_full"`，消费端 `_res_read("canticle") >= _res_max(player,"canticle")` 才加成。
- 以上 sets.py 字段由 R2 同步添加（见 R2 卡），你只改 battle.py 消费端（读不到新字段用旧值 fallback，保证先行编译/测试通过）。

### 3. 战斗日志与显示规范化（P3）
- **套装日志资源 key 泄漏**（约 2448）：`f"⚔️ 套装回响：{eff['res']} +{gain}！"` → 用资源显示名（`E.core_resource_def_by_key(rk) or E.core_resource_def(...)` 取 name，参照同文件 1848-1849 行写法）。
- **echo 生产日志丢失**（约 579 `_echo_add(player, [], ...)`）：透传 logs（改 `_res_gain` 的 echo 分支接收 logs 参数或由调用方记录）；至少让歌者玩家施放时有「🎵 回声驻留 +N」反馈。
- **满资源误报**（`_affix_res_proc`/`_set_res_proc` 的 `added > 0` 判定，约 792/1244）：改真实增量判定（_res_gain 返回新值，对比调用前值）。

### 4. 顺手小修
- `_res_gain_class`（约 605-608）上限加 `self._set_res_max_bonus(self.player, k)`（与 `_res_max` 口径统一；self.player 为 None 时守卫）。
- 印记铭刻多件叠加无帽：battle.py `_elem_mark_max` 读 affixes max_total 帽（R2 会给 sigil_engrave 加 `"max_total": 1`，你按词条 effect 的 max_total 字段封顶）。
- battle.py:111 区「31 哑词条」注释更新为「31 词条接线」。
- `_res_gain_class` 无 player 时 None 守卫（约 608）。

## 铁律
- 只改 game/battle.py（+ battle_config.py 如需）；禁改 skills.py/sets.py/affixes.py（R2/R4 负责）。
- 禁 git commit、禁重启 AstrBot、禁跑 scripts/run_all_tests.py 全量回归。
- 最小 diff 禁整文件重写；改完 py_compile + 跑 tests/test_v130_resources.py、tests/_smoke_v130_engine.py、tests/test_v1252_audit_closure.py（私有临时库姿势参照 conftest）。
- 写 1 个验证脚本（GWEN_GAME_DB 私有临时库，用完删）验证：① 精力 48 持精力刀刃放 50 档终结技可施放 ② 持 4 怒施放无畏冲击成功（EQ 动态）③ 套装日志显示中文资源名。

## 报告（中文）
修复清单表（问题 | 改动位置 | 验证证据）+ 测试结果 + git status 清单 + 留给主 agent 的注意事项（sets.py 新字段依赖项清单）。