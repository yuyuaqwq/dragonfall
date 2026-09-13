# design/ 已被清空 —— 策划案仓已移出本仓（2026-09-13）

本目录（原 `design/new_world/`，849 文件 / 10.0 MB）在 **2026-09-13 的 B1 清场**中**整体移出游戏仓**（移出 ≠ 删除）。

## 为什么移

`design/new_world/` 是一个**独立的 git 仓库**（内含自己的 `.git`，独占 7.2 MB）。
外挂仓混进插件目录会让代码仓状态混乱（`docs/ENGINE_CONTENT_SPLIT_PLAN.md` 的 R10 记的就是这个隐患，`.gitignore` 里也只能靠 `design/` 整目录排除）。
鱼鱼拍板 **A 案：保持移出**，并把「策划案同步铁律」改为已退役 —— 见 `DEVELOPMENT.md` §6。

## 现在在哪 / 怎么找回

- **现址**：`C:\Users\yuyu\AppData\Local\hermes\workspace\_retired\20260913\design\new_world\`
- **回滚**：同目录 `README.md` 里有一段反向 `shutil.move` 脚本；`MANIFEST.json` 存了 1,978 条的 `path / dst / bytes / sha256`，可逐字节核对还原。

## 源码里的 `design/new_world/...` 引用怎么理解

仓内约 10 处**注释**把 `design/new_world/32_数值设计.md` 等当「数值/设计权威」引用
（如 `game/data/battle_rules.py`、`game/data/classes.py`、`game/store/professions.py`、
`game/commands/combat.py`、`tests/test_v181_batch_d_dot_formula.py`）。
这些注释**沿用旧写法未逐条改** —— 按本文件跳转即可：路径前缀 `design/new_world/` 一律替换为
`<workspace>\_retired\20260913\design\new_world\`。

## 待定（会影响这里的写法）

设计/数值改动的**同步对象待定**：外挂仓（在仓外继续独立提交）/ 并入 `docs/` / 重建独立仓，三选一。
**定案前**：涉及数值·新内容·机制的改动，请在提交说明里写清设计依据并知会鱼鱼（`DEVELOPMENT.md` §6 有完整口径）。
定案后请回来更新本文件与 `DEVELOPMENT.md` §6。

> 本文件是仓内**唯一**被跟踪的 `design/` 文件（`.gitignore` 用 `design/*` + `!design/README.md` 实现），
> 作用是让所有指向 `design/` 的旧路径不再悬空。
