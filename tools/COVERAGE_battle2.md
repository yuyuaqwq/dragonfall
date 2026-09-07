# battle2 覆盖率说明

## 三层覆盖

| 层级 | 工具 | 当前 | 说明 |
|---|---|---|---|
| 函数级 | `tools/cov_func_battle2.py` | 100%（0 未调用） | 每个函数是否被调用过 |
| 行级（真可执行行） | `tools/cov_branch_battle2.py` | 90.4% | 排除 def/docstring 后的代码行 |
| 分支/路径 | 行级近似 + 人工甄别 | 真业务全覆盖 | 见下方豁免清单 |

## 剩余未覆盖行甄别（90.4% → 全为防御代码）

逐行人工核对过，剩余 ~61 行全部是**防御性代码**（异常兜底/参数保护/理论边界），
正常业务路径不可能走到，价值是"出错不崩"，不强求测试覆盖：

| 类别 | 典型 | 行 |
|---|---|---|
| except 兜底 | formation 异常回落 / heal_power 异常 / 索引失败 | actions 40-41,166-167,310-311；effects 109,111 |
| 参数/空保护 | amount<=0 / target None / 无 hp 容器 / 无玩家 / 已结束 | landing 33,37,70,143；battle 150,152,201,203 |
| 索引 fallback | skill_by_key 找不到 / _skill_index 异常 | battle 87,94,98-99 |
| 理论边界 | guard 耗尽 / result 中断 / 空返回 | schedule 92,99,106,180；effects 170,174,197,201 |
| 死路径 | _skill_usable 恒 true（73 行） | actions 73（可删但保留语义钩子） |

**判定标准**：若某行是"异常处理/输入保护/永不触发的兜底" → 豁免合理。
若某行是"正常输入会走的业务分支" → 必须补测试（当前已 0 遗漏）。

## 跑法

```bash
# 函数级（快，质量门禁用）
python tools/cov_func_battle2.py

# 行级（慢，~2min，全部测试跑一遍）
python tools/cov_branch_battle2.py
```

## 测试文件

- tests/test_battle2_coverage.py（73 断言）：查询 API/helper/defend/cleanse/schedule
  工具/serialize 便捷/stats 便捷/landing 边界/effects 分支/actions 分支/AOE falloff
- 各 N 阶段测试：N1(8) N2(10) N2b(8) N3(28) N4(14) N5(14) landing(13) coverage(73)
