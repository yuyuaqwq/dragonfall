# audit_T5.md — 意见#6『采集有 bug，采集后没有东西』排查报告

- 意见：zerc「采集好像有 bug，采集后没有东西」（群 1095961596，status=new）
- 排查人/日期：T5 子代理，2026-08-27 上午
- 结论：**真 bug，已定位根因并最小修复（economy.py 单文件 15 行），复现 + 回归全绿**

---

## 一、排查过程（采集指令全链路）

链路：`采集` 指令 handler → 体力 → 成功判定 → 产出表 → 入包 → 提示语。
全部在 `game/commands/economy.py`。

| 环节 | 位置 | 排查结果 |
|---|---|---|
| 指令入口 | economy.py:1082 `def gather` | 城镇/副本正确拦截并提示；`_prof_active_check` 拜师拦截正常 |
| 体力 | economy.py:1113 `_spend_stamina` 5 点 | 先开等待轮后扣，不足回滚+播报，正常 |
| 等待轮 | economy.py:1101-1119 `_prof_wait_flow` → `_prof_wait_begin`(:615) | v127.5 起挂通用懒计时引擎 `set_timed(key="prof_wait")`，到点由 `_prof_delayed_push`(:638) 结算入包 |
| 产出表 | `_gather_roll`(:466) + `data/gather_pools.py` | **数据完整**：61 图池 + 8 条件池全部材料 ID 存在、权重>0；全地图 roll 恒有产出（脚本实证） |
| 入包 | `_settle_gather`(:874) → `db.add_item` | store/inventory.py:183 无静默跳过（无背包上限）；物品实入 |
| 提示语 | economy.py:942「🌿 采集完成！…采到了…」 | 提示与入包同源（同一个 `got` dict），无“成功但没提示/没入包”错位 |
| 条件产出 | `_gather_cond_roll`(:502) | v125.2 fail-closed 条件词注册表，无未注册词 |

**排除项**：产出表空/权重 0/条件不满足但判定成功 → 不存在（Part 1 脚本实证）；失败提示误导 → 不存在（采集无随机失败，等待制恒定产出）；体力不足静默失败 → 不存在（体力不足有明确播报且回滚等待轮）。

**真正的洞在「结算/交付」环节**（v127.5 惰性结算设计）：

1. 『采集』开轮后，结算只依赖进程内 `_prof_delayed_push`（`asyncio.sleep(wait)` 后结算+推送）。
2. **若进程重启或推送任务异常被吞**（`except Exception: pass`，economy.py:650-651），事件留在引擎存储 `timed_events_{qq_id}` 且已过期，**从未结算**。
3. 玩家之后发**任意**游戏指令（如『背包』查看、『前往』、任何指令）→ `_maint_gate`（base.py:195，priority=100 先于一切 handler）→ `refresh_timed`（timed_events.py:164）→ **物理删除过期 `prof_wait` 事件**。该事件注册时 `on_expire=None`（economy.py 旧 :30），**无任何回调** → 结算数据（finish/type/spot_map）永久丢失。
4. 之后哪怕再『采集』，`_prof_wait_flow` 的残留兜底（`_prof_wait_residual`）也读不到任何数据 → 直接开新轮。玩家视角＝「采集后没有东西」，且永远没有提示。
5. 唯一幸存路径：到点后玩家的**下一条指令恰好是副业指令**（采集/挖掘/垂钓/遗忘），`_prof_wait_flow` 先读 residual 再触 `get_timed`，可结算出旧轮（2C 实证）。

**触发现实性**：框架环境注明 "AstrBot 在线（重启中）"；开服第 2 天玩家采集 → 等待 45~75 秒 → 服务器重启/推送失败 → 任意指令清数据 → 符合玩家报告。

---

## 二、复现验证（workspace/feedback_fix/verify_T5.py，16 断言全绿）

复现手法：真实 `Main(None)` + FakeEvent 全链路跑『采集』→ 把引擎事件 expire/data.finish 改写为过去（等价进程重启后到点）→ 触发 `refresh_timed`（等价玩家发任意指令）→ 查背包/residual。

- **修复前实录**（首轮运行）：
  - `refresh_timed 清掉过期事件` ✅ n=1
  - `BUG 复现：结算数据被物理删除（residual 为空）` ✅
  - `BUG 复现：背包无新增材料（采集=空气）` ✅
  - `>>> 复现成功：『采集后没有东西』＝到点未结算 + 任意指令刷新清数据`
- **修复后**（同脚本）：
  - `on_expire 把结算数据保全到遗留键（residual 可读）` ✅
  - `修复后：旧轮产出入包（1~2 份）` ✅
  - `修复后：旧轮提示语带出（采集=有东西）` ✅
  - `修复后：无双结算（结算后遗留键已清空）` ✅
- 正常主路径（推送结算）不受影响：`背包 +1~2 份` `提示语含物品名` ✅

---

## 三、根因

**v127.5『等待型副业收编懒计时引擎』的结算兜底假设被 `refresh_timed` 破坏**：
注释声称 "on_expire 不需要：结算走 _prof_delayed_push + 惰性结算兜底（_prof_wait_residual 非破坏读引擎存储残留，防『到点但未结算』吞掉奖励）"（economy.py 旧 28-29 行），但：
- `refresh_timed`（timed_events.py:164-194）对过期事件**无回调即物理删除**（pop + _save）；
- `_maint_gate`（base.py:203-205）在**每条指令**先执行 refresh；
- 于是「残留非破坏读」只在下一指令恰好是副业指令时才来得及；其余情况数据先被删。

一句话：**到点未结算的副业轮次，会被任意一条后续指令静默清掉，物品与提示全丢。**

---

## 四、最小修复（game/commands/economy.py:25-51）

利用引擎官方 `on_expire` 回调钩子（timed_events.py:49，wild.py 同款机制），给 `prof_wait` 注册数据保全回调：引擎物理删除前，把 `{finish,type,spot_map}` 平移到历史遗留键 `prof_wait_{qq_id}`（`_prof_wait_residual` 第二顺位读取源，v127.5 迁移兜底键），由既有的 `_prof_wait_flow` 残留路径在下次副业指令时惰性结算（物品入包 + 提示语一并带出）。

```python
def _prof_wait_expire_cb(group_id, qq_id, data):
    try:
        st = dict(data or {})
        if st.get("finish") and st.get("type") in ("gather", "fishing", "mining"):
            db.set_event_state(f"prof_wait_{qq_id}", json.dumps(st, ensure_ascii=False))
    except Exception:
        pass

_te.register_timed("prof_wait", duration_sec=None, on_expire=_prof_wait_expire_cb)
```

幂等性论证：
- 结算后 `_prof_wait_clear`（economy.py:602-605）清空遗留键 + 引擎事件 → 无双结算；
- `_prof_wait_begin` 开新轮时也清遗留键 → 不串台；
- 重复触发仅覆盖同结构数据（finish 一致）；
- 正常推送路径（进程存活）不经过回调，行为零变化；
- 只动 economy.py，未碰引擎/base/共享设施（框架铁律）。

**修复边界**：物品在「下一条副业指令」时送达+播报（与 v127.5 开轮文案『完成会自动入包～』的惰性语义一致）。修复前是**永久丢失**；修复后至多延迟到下次副业动作。更强的「任意指令即结算+推送」需要 base.py 门面改动与跨指令文本暂存，超出最小修复范围（见遗留建议）。

---

## 五、回归测试（相关采集/副业测试文件，全绿）

| 测试文件 | 结果 |
|---|---|
| test_v1275_prof_wait.py（v127.5 等待型副业引擎，最直接） | 26 通过, 0 失败 |
| test_v1275_timed_engine.py（懒计时引擎） | 22 通过, 0 失败 |
| test_v1275_limited_wild.py（refresh_timed/on_expire 引擎同路径） | 29 通过, 0 失败 |
| test_commands_world.py（垂钓/采集） | 43 通过, 0 失败 |
| test_commands_profession.py（副业体系） | 26 通过, 0 失败 |
| test_commands_fishing.py | 24 通过, 0 失败 |
| test_r3_m15_fishing.py（等待型副业等待流/体力） | 30 通过, 0 失败 |
| test_v1023_life_prof.py（采集限定物/深矿） | 15 通过, 0 失败 |

未做全量回归（框架铁律）；未 git commit。

---

## 六、遗留建议（非本卡范围）

1. `_prof_settle`（economy.py:653）首行 `_prof_wait_clear` 先清状态再结算——若 `_settle_gather/_settle_fishing` 内部抛异常（如未来数据脏），推送路径同样会静默吞掉（`except Exception: pass`）。建议后续把 clear 移到结算成功后，或给 `_prof_delayed_push` 加错误日志。
2. 更强 UX：在 `_maint_gate` 对残留做即时代结算（物品任意指令即到），结算文本暂存 `event_state` 并在下一指令头部带出；需动 base.py，属产品拍板项。
3. 生产库中已被吞的旧轮无法追回（数据已删），无需补发逻辑；修复自生效起不再丢。