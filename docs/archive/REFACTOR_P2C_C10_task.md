# P2C-C10 任务书：P2C 收尾（删旧 handler 死代码 + buff 显示修复 + DEFAULT 清理）

> 权威文档：docs/archive/REFACTOR_P2C_weapon_executors.md（§4.1 目标注册表 + C10 行 + §6 风险表）
> 工作分支：wt_p2cc10（worktree w10）｜ 完成后 commit，不 merge master

## 背景
C1-C9 已完成：79 key 全路由进 13 个族执行器（_WE_EXEC_KEYS 72 key + 7 纯辅助）。C9 刚迁完保命族。
**现在 weapon_effects.py 里所有旧 `_we_*` handler 都是死代码**——proc() 分发器命中 _WE_EXEC_KEYS 后 continue，永不 fallback 到旧 handler（除非有 key 漏路由）。

## 目标（行为零变化）
1. **删旧 handler 死代码**：weapon_effects.py L431 之后所有 `@register(...)` + `def _we_*`（旧 handler）删除
2. **删 wd.get DEFAULT**：旧 handler 删光后，残余的 `wd.get("xxx", 0.xx)` 默认值兜底一并清理
3. **保留**：L1-430 基建（_we_defaults/_we_family/weapon_effect_ids/effect_data/has_effect/_pstats/_estats/_true_dmg/_extra_phys/_extra_magi/_slow_enemy/_freeze_enemy/_apply_dot/_heal_player/_boss_enemy/_hp_ratio/WEAPON_EFFECTS+register/proc/_we_executors/_WE_EXEC_KEYS/_we_key_event_family/_we_panel_apply）——这些被 battle.py/_we_executors.py 依赖
4. **buff 显示修复（combat.py _status_line）**：玩家/敌方 buff "剩X刻" 按 _now 折算（见下）

## 关键判断（先做侦察再动手！）
- **WEAPON_EFFECTS 注册表**：register() 还在往 WEAPON_EFFECTS 装 key。全 key 路由后，proc() fallback 永不触发——但要确认：
  - 有没有**漏路由 key**？跑：`python - <<EOF` 对比数据表 79 key vs _WE_EXEC_KEYS 72 key vs WEAPON_EFFECTS 注册 key，确认 7 个差额 = 纯辅助 key（*_p 后缀等）
  - 漏了 → 不能删（会静默失效）！
- **register() 装饰器**：旧 handler 删光后 register 还有没有用？如果 WEAPON_EFFECTS 最终空，register 可留（proc 兼容层可能读）或删（谨慎）
- **_apply_dot 等共享动作**：_we_executors.py 里 `from .weapon_effects import _apply_dot, _boss_enemy` 等 import——**必须保留这些共享函数**！别误删
- **battle.py 直读点**：C6-C9 已把 battle.py 直读点改查表（_we_panel_apply/_we_proc/effect_data）——确认没有 battle.py 还在直调 `_we_*` 旧 handler（应该全清了）

## buff 显示修复（combat.py game/commands/combat.py）
现状（v152 时刻制改革遗漏）：L1630-1632 玩家 buff 直接 `剩{v}刻`（v=到期绝对刻号不递减），L1679 敌方 buff 同样。
修复（参考同文件 L1646-1661 护盾折算样板）：
```python
# 玩家 buff
_now_t = float(getattr(b, "_now", 0.0) or 0.0)  # 已在 shields 段定义过就复用
for k, v in (b._p_buffs_bag() or {}).items():
    if v and v > 0 and k in self._P_BUFF_NAMES:
        _left = float(v) * ACT_TICK - _now_t  # v=绝对到期刻号
        _turns = max(1, int(round(_left / (ACT_TICK or 1.0)))) if _left > 0 else None
        pbuf.append(f"{self._P_BUFF_NAMES[k]}(剩{_turns}刻)" if _turns else f"{self._P_BUFF_NAMES[k]}")
# 敌方 buff 同理（L1679）
```
注意：v 可能是 int（旧格式剩余刻）或 dict（新 expire_at）——兼容处理参考 _decay_buff_table L9467-9479 三种形态。
注意：**不是所有 buff 都是"到期删"语义**——一次性键（next_atk_up/stealth/we_oath 等 _decay_buff_table 跳过的）显示原始值合理（它们攻击消费）；盾/元素印记已特判。

## 验证清单（全绿才算完成）
```
python -m py_compile game/core/weapon_effects.py game/commands/combat.py game/battle.py game/core/_we_executors.py
python tests/test_p2cc2_we_family_semantics.py      # 33
python tests/test_p2cc3_we_shield_semantics.py      # 40
python tests/test_p2cc5_control_semantics.py        # 35
python tests/test_p2cc6_panel_buff_probe.py         # 33
python tests/test_p2cc6_panel_buff_semantics.py     # 34
python tests/test_p2cc7_marks_probe.py              # 35
python tests/test_p2cc7_marks_semantics.py          # 41
python tests/test_p2cc8_passive_stack_semantics.py  # 34
python tests/test_p2cc9_lifesave_probe.py           # 37
python tests/test_p2cc9_lifesave_semantics.py       # 43
python tests/test_v140_weapon_effects.py            # 12
python tests/test_v140_novice_effects.py            # 20
python tests/test_v59_battle_status.py              # buff 显示
scripts/run_numeric_tests.py                        # 52 全绿
# grep 断言：battle.py 无 _we_ 旧 handler 直调
grep -n 'from .core.weapon_effects import _we_\|_we_[a-z].*(battle' game/battle.py  # 应空
```

## 测试环境（坑）
- worktree 直接跑不行（conftest 需 data/plugins 父链）——复制到沙盒跑：
```
rm -rf /c/Users/yuyu/AppData/Local/Temp/df_wt_copy10/data/plugins/dragonfall
mkdir -p /c/Users/yuyu/AppData/Local/Temp/df_wt_copy10/data/plugins
cp -r /c/Users/yuyu/AppData/Local/Temp/df_wt_v181f/w10/. /c/Users/yuyu/AppData/Local/Temp/df_wt_copy10/data/plugins/dragonfall/
cd /c/Users/yuyu/AppData/Local/Temp/df_wt_copy10/data/plugins/dragonfall
"C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe" tests/xxx.py
```
- worktree 物理路径：C:/c/Users/yuyu/AppData/Local/Temp/df_wt_v181f/w10

## 完成条件
- [ ] weapon_effects.py 旧 handler 全删（L431 后 @register/def _we_* 清零），共享动作保留
- [ ] 无漏路由 key（79=72+7 验证）
- [ ] buff 显示修复（玩家+敌方两处折算）
- [ ] 全部测试 + numeric 52 全绿
- [ ] git status 干净，commit 到 wt_p2cc10 分支（v181.P2C-C10 收尾）
