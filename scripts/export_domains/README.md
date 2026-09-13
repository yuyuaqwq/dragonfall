# scripts/export_domains/ —— 域插件目录（并行加域的零冲突扩展面）

**一句话**：一个域插件 = 本目录下一个 `.py`，暴露 `DOMAINS = {"<域>": derive_<域>, ...}`，
即被 `scripts/export_game_package.py` 自动并入注册表 —— **不必改那个 2,900 行的宿主文件**。

## 为什么要有它（2026-09-13 加）

原做法是「在 `export_game_package.py` 里加 `derive_<域>` + 在字面量 `DERIVERS = {...}` 里加一行」。
单路开发没问题，但**多路并行加域**时，5 路会在同一处字面量上互相覆盖 ——
而「域悄悄消失」在包侧是**静默失效**（game.json 少一个域、编辑器少一个页签，不报错）。
改成「加一个文件」后，每路各写各的文件，零冲突。

## 契约（写插件前必读）

```python
# scripts/export_domains/<你的线>.py
from _helpers import import_game_data, sort_table, as_table   # ⚠️ 同目录相对导入走 sys.path，见下

DOMAINS = {"<域>": derive_<域>}          # 域名单必须全局唯一（重名 → 导出器直接抛错，不静默覆盖）

def derive_<域>(src_root: str = None) -> dict:
    """真源 → 内存表。条目**原样**进 JSON：不补默认值、不改类型、不展开引用字符串。"""
```

规则：
1. **不许 import `export_game_package`**（宿主会扫描本目录 → 循环导入）。公用小工具用 `_helpers.py`。
2. 派生函数**只读真源**，不写任何文件（落盘由宿主统一做：UTF-8/LF/indent=2/原子替换）。
3. 域数据落点由包侧 `<pkg>/editor/domains.json` 的 `kind` 决定（`data` → `content/data/`，
   `rules` → `content/rules/`）——**域必须先在包里声明**，否则 `domain_path` 抛 KeyError。
4. 一个插件文件里放**同一线**的多个域（如 NPC 线的 dialogues/quests/events…），
   便于一个 agent 独占一个文件。
5. 加载失败**不静默**：坏模块被记为 `DOMAIN_PLUGIN_ERRORS`（宿主 CLI 打警告、
   `scripts/verify_package_coverage.py` 计入失败），但**只跳过坏模块**，不阻塞其它路。

## 怎么用

```bash
cd <游戏仓>
PYTHONIOENCODING=utf-8 python scripts/export_game_package.py --domain <域>          # 导出落盘
PYTHONIOENCODING=utf-8 python scripts/export_game_package.py --domain <域> --check  # 与真源比对（必须 ✅）
PYTHONIOENCODING=utf-8 python scripts/verify_package_coverage.py --check           # 全包覆盖门禁
```

`game.json` 的 `domains` 由 `sorted(DERIVERS)` 派生（含插件域）→ 不用手写第二份名单。
