# P3 e_buffs/enemy 兼容层全删——actor 化收口任务书（wt_ebuffs）

> 鱼鱼 2026-09-08 拍板：**全部 actor 化，大改动，一并删干净**。不留兼容代码、不考虑旧档兼容、不搞风险规避。
> 触发：古王+王冠核心多怪时敌方 debuff 挂错人/状态栏不可见（probe 已复现）。
> 铁律：行为零变化是底线——但**收口不是纯寻址**，多怪语义本来错，改后多怪正确、单怪不变。

## 北极星（本次收口目标态）

1. **敌方 buffs 一律在 actor dict 自己的 `buffs` 字段**（怪/玩家/随从同构，无共享敌方 buffs）。
2. **删 `e_buffs` property**（battle.py L1119-1126，指向 enemy.setdefault("buffs") 的共享别名）。
3. **删 `e_defending` property**（L1128-1135）——defending 本来就在 actor dict 上，多余包装。
4. **删 `enemy` property 的"主怪"语义依赖**——凡"敌方目标"一律用具体 actor 引用
   （`_active_target` = 玩家当前选中怪 / 显式传入的 u / `enemies[i]`）。
5. core 执行器不再写 `battle.e_buffs`——按语义写**目标 actor** 或**施法 actor** 的 buffs。

## 访问器设计（battle.py 先落，其他文件依赖）

```python
# —— v181 P3：actor 一视同仁 buffs 访问器（替代 e_buffs 共享别名）——
def _actor_buffs(self, actor: dict) -> dict:
    """目标 actor 的 buffs（玩家/怪/随从同构；actor 缺省 None 由调用方保证）。"""
    return actor.setdefault("buffs", {})

def _hit_tgt(self) -> dict:
    """当前受击/被作用目标 actor：玩家当前选中怪；无活跃目标回退第一存活怪。"""
    t = getattr(self, "_active_target", None)
    if t is not None and t.get("hp", 0) > 0:
        return t
    for u in self.enemies:
        if u.get("hp", 0) > 0:
            return u
    return self.enemies[0] if self.enemies else {}
```

## 引用语义分类（199 处全量清单见 docs/ebuffs_all_refs.txt）

| 类别 | 语义 | 改法 |
|---|---|---|
| A 玩家技能/攻击/宠物 → 目标怪 debuff | 对当前被打怪施加 freeze/sleep/def_down/mark 等 | `battle.e_buffs[X]=N` → `battle._actor_buffs(battle._hit_tgt())[X]=N` |
| B 怪给自己加 buff | mon_atk_up/def_up/spd_up 等（施法怪自身） | → `battle._actor_buffs(施法怪actor)`（handler 内 battle._cast_ctx 或 e 参数） |
| C 读目标是否带某 debuff | "mark" in e_buffs / freeze 判定 | → 按判定目标 actor 读 |
| D 序列化/存档 | st["e_buffs"] 存取 | 弃用（enemies[] 每怪自带 buffs）；读旧键路径删（不做旧档兼容） |
| E 命令层显示 | combat.py 敌方状态栏 | → 读当前显示怪 actor 的 buffs |
| F 衰减/回合逻辑 | e_buffs 控制减益逐刻衰减 | → 扫每怪 actor buffs（已有 v180G B4 部分修正） |

## 分批（每批独立 commit + 测试）

- **B0（battle.py 地基）**：加 _actor_buffs/_hit_tgt 访问器；删 e_buffs/e_defending property；
  battle.py 内 45 处引用收口（含序列化 L1269 弃用 e_buffs 键、恢复 L1513 旧档并入删、
  _tgt 退化点 L1828 改 _hit_tgt、6 个直写点、L7480 控制缩短、L10100 宠物破甲等）。
- **B1（battle_mech 46 处）**：A 类写 `battle._actor_buffs(battle._hit_tgt())`，B 类写施法怪自身。
- **B2（affix_effects 31 + weapon_effects 6 + food_effects 1 + _we_executors 17）**：同上语义分类。
- **B3（battle_conds 11 + passive_procs 8）**：读点按判定目标改。
- **B4（commands combat 10 + instance 16 + store battle_state 6 + engine 1）**：显示/存档/恢复收口。
- **B5（收尾）**：grep 全仓 e_buffs/e_defending 零残留（白名单注释除外）；多怪专项测试；
  全量 numeric + run_all。

## 验证
- 每批 py_compile + 相关测试（战斗族 + numeric）
- 多怪专项 probe（tests/probe_ebuffs_multienemy.py 已落盘）：断言副怪中 debuff → 副怪 buffs 有、
  主怪无、状态栏显示正确
- 全量 run_all 对照基线（11 固定红 = pre-existing probe 类）
