# -*- coding: utf-8 -*-
"""数值回归运行器：串行逐个执行 tests/test_numeric_*.py（规格见 docs/NUMERIC_TEST.md）。

⚠️ 使用场景：改动任何数值后必须跑这个 —— 技能 / 怪物 / 装备 / 属性加点 / CTB /
掉落 / 伤害公式 / 成长公式 / 数据表数值，任何一项动过都必须跑本脚本全绿才能提交。

用法：
  python scripts/run_numeric_tests.py            # 全量：串行跑全部 tests/test_numeric_*.py
  python scripts/run_numeric_tests.py --fast     # 只跑胜率矩阵（最耗时项），日常开发快检
  python scripts/run_numeric_tests.py --list     # 只列出当前发现/缺失的数值测试文件，不运行

行为：
  - 串行 subprocess 逐个执行（复用 scripts/run_all_tests.py 的子进程模式，简化版）
  - 每文件一份**独立私有库**（tests/.numeric_workers/ 下，空白 schema 模板复制）——
    与 run_all_tests.py 同款隔离，消除多份门禁并发时的同一 DB 文件竞争（2026-09-11 修）
  - 子进程强制 UTF-8（PYTHONIOENCODING + PYTHONUTF8=1），与手工 `-X utf8` 行为对齐
  - 每文件打印 ✅/❌/⏱️（超时）+ 耗时（秒）；失败分支补打 stdout/stderr 尾部各 30 行
  - 末尾汇总：文件数 / 通过 / 失败 / 跳过 / 总耗时
  - 有任何失败（含超时、崩溃、断言红）→ exit 1（数值门禁不过）
  - 容忍缺失文件：尚未建全的 test_numeric_*.py（并行建设中）只提示跳过、不算失败；
    全部缺失时打印警告并 exit 0（此时无门禁意义，等待测试文件就绪后重跑）
  - 必须用 AstrBot 的 uv python（带项目依赖）：
    C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe

注意：跑数值测试期间不要改动任何源文件/数据表（避免中间态误判）。
"""
import os
import shutil
import subprocess
import sys
import time

# P1：子进程 + 父进程强制 UTF-8，否则 ✅/中文在 GBK(CP936) 控制台 UnicodeEncodeError 崩溃（假红）
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS_DIR = os.path.join(PLUGIN_DIR, "tests")                   # 宿主自留件（T8 前唯一目录）
FRAMEWORK_DIR = os.path.join(PLUGIN_DIR, "framework")            # 引擎部署面
GAMES_DIR = os.path.join(FRAMEWORK_DIR, "games")


def _numeric_search_dirs():
    """★ T8（2026-09-19）：数值测试枚举面 = **宿主自留件** ∪ **包仓那份**。

    内容侧测试真源 = 包仓 `tests/`（经 sync.sh 部署到 `<plugin>/framework/games/<pkg>/tests`）。
    旧版只看宿主 `tests/` ⇒ 包仓那 12 个 test_numeric_* 全被判「缺失」→ 报「跳过 6 个」，
    而它们其实活着。判据 = 「是不是内容包目录」（含 content/），不写死包名。
    """
    dirs = [TESTS_DIR]
    if os.path.isdir(GAMES_DIR):
        for name in sorted(os.listdir(GAMES_DIR)):
            d = os.path.join(GAMES_DIR, name)
            if os.path.isdir(os.path.join(d, "content")) and os.path.isdir(os.path.join(d, "tests")):
                dirs.append(os.path.join(d, "tests"))
    return dirs


def _pkg_dir():
    """包目录：`GWEN_PACKAGE_DIR` 优先；否则 `framework/games/*` 里声明表最大的那个。"""
    env = str(os.environ.get("GWEN_PACKAGE_DIR") or "").strip()
    if env and os.path.isdir(env):
        return env
    best, best_n = None, -1
    if os.path.isdir(GAMES_DIR):
        for name in sorted(os.listdir(GAMES_DIR)):
            decl = os.path.join(GAMES_DIR, name, "content", "data", "commands.json")
            if os.path.isfile(decl) and os.path.getsize(decl) > best_n:
                best, best_n = os.path.join(GAMES_DIR, name), os.path.getsize(decl)
    return best or os.path.join(GAMES_DIR, "orlandia")
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))  # dragonfall/→plugins/→data/→qqbot/
# 项目 Python：与 run_all_tests.py 一致（带 pypinyin 等依赖）
PYTHON = r"C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe"

# 隔离修复（2026-09-11）：此前子进程**不预置** GWEN_GAME_DB → 各文件自己的
# os.environ.setdefault(...) 生效，其中 3 个文件都指向同一个 tests/test_game_data.db
# （drop_unify / instance_reward / reward_unify）。串行时靠顺序侥幸不脏，但一旦与
# run_all_tests.py / 另一份数值跑**并发**，就是同一 DB 文件的竞争 → 门禁偶发红。
# 修法：对齐 run_all_tests.py 的私有库机制——每轮建一份空白 schema 模板，
# 每个文件复制一份独立库并把 GWEN_GAME_DB 预置进去（setdefault 不再覆盖）。
_TPL_INIT = (
    "import os,sys;"
    "os.environ['GWEN_GAME_DB']=sys.argv[1];"
    "sys.path.insert(0,sys.argv[2]);"      # 插件根
    "sys.path.insert(0,sys.argv[3]);"      # 引擎部署面
    "from host import store_factory as _sf;"
    "from saintess_engine.host import load_package;"
    "_pkg=load_package(sys.argv[4], inject=_sf.inject_handles());"
    "_sf.bind_store(_pkg).init()"
)
WORKER_DIR = os.path.join(
    TESTS_DIR, f".numeric_workers_{os.getpid()}_{int(time.time())}"
)   # 按调用唯一：并发跑两份数值门禁时，`tests/` 下同名 worker 库会互相覆盖
    # （run_all_tests 同款固定名目录有一样的隐患，见其 worker_dir）


# 单文件超时（秒）：胜率矩阵最重（24 格 × 8 seeds 战斗），给足余量；可用环境变量 TEST_TIMEOUT 覆盖
FILE_TIMEOUT = int(os.environ.get("TEST_TIMEOUT", "600"))

# 已知测试清单（任务卡 N01~N03 规划，用于缺失提示；缺失不阻塞）
# 实际运行集合 = tests/ 下所有 test_numeric_*.py，新增文件自动纳入（不受此清单限制）
EXPECTED = [
    "test_numeric_battle_matrix.py",     # N01 跨级胜率矩阵 —— --fast 只跑它（最耗时项）
    "test_numeric_ctb_freq.py",          # N02 CTB 行动频率
    "test_numeric_panel_snapshot.py",    # N02 面板快照
    "test_numeric_equip_dependency.py",  # N03 装备依赖
    "test_numeric_monster_curve.py",     # N03 怪物成长曲线
    "test_numeric_skill_power.py",       # N03 技能倍率快照
]
FAST_ONLY = "test_numeric_battle_matrix.py"


def discover(fast):
    """返回 (可运行文件列表, 缺失文件列表)。缺失 = 清单内未找到（跳过提示用）。"""
    present = {}                                     # 名字 → 绝对路径（跨目录，名字可能撞）
    for d in _numeric_search_dirs():
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.startswith("test_numeric_") and f.endswith(".py"):
                    present.setdefault(f, os.path.join(d, f))
    if fast:
        present = {f: p for f, p in present.items() if f == FAST_ONLY}
    files, missing = [], []
    for name in EXPECTED:
        if name in present:
            files.append(present[name])              # ★ 路径（跨两目录）
        else:
            missing.append(name)
    for name in sorted(present):  # 新增/未知的数值测试文件也纳入运行
        if present[name] not in files:
            files.append(present[name])              # ★ 路径（与 EXPECTED 分支一致；漏改过 ⇒ 拼宿主目录报 Errno 2）
    return files, missing


def _report_failure(name, ok, proc, dt, timed_out):
    flag = "✅" if ok else ("⏱️" if timed_out else "❌")
    print(f"{flag} {name} ({dt:.1f}s, exit={'TIMEOUT' if timed_out else proc.returncode})",
          flush=True)
    if not ok:
        # 失败分支补打 stdout + stderr 尾（各 30 行），便于定位子进程崩溃/断言红
        out = (proc.stdout or "").strip().splitlines() if hasattr(proc, "stdout") else []
        err = (proc.stderr or "").strip().splitlines() if hasattr(proc, "stderr") else []
        for label, lines in (("stdout:", out), ("--- stderr ---", err)):
            tail = lines[-30:]
            if tail:
                print(label, flush=True)
                print("\n".join(tail), flush=True)
        print("-" * 60, flush=True)


def main(argv):
    fast = "--fast" in argv
    want_list = "--list" in argv

    files, missing = discover(fast)
    if want_list:
        print("将运行:" if files else "当前没有任何可运行的数值测试文件")
        for f in files:
            print(f"  {f}")
        if missing:
            print("缺失（未找到，可能仍在建设中）:")
            for f in missing:
                print(f"  ⚠️ {f}")
        return 0

    if missing:
        print(f"⚠️ 跳过缺失文件 {len(missing)} 个: {', '.join(missing)}（可能仍在建设中）", flush=True)
    if not files:
        print("⚠️ 未发现任何 tests/test_numeric_*.py —— 数值测试文件尚未就绪（并行建设中？）。", flush=True)
        print("   本次运行无门禁意义，跳过；待测试文件建好后重新运行。", flush=True)
        return 0
    if fast:
        print(f"⚡ --fast 模式：只跑 {FAST_ONLY}（胜率矩阵，最耗时项）", flush=True)
    if not os.path.exists(PYTHON):
        print(f"❌ 找不到项目 Python: {PYTHON}", flush=True)
        return 1

    results = []  # (name, ok, proc, dt, timed_out)
    # P1：强制子进程 UTF-8（与 run_all_tests.py 及手工 `-X utf8` 行为对齐，
    # 消除 locale(cp936) 依赖的文件读写差异）
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}

    # P1 隔离：空白 schema 模板库（建失败则回落旧共享库行为，不阻塞门禁）
    tpl_db = None
    try:
        shutil.rmtree(WORKER_DIR, ignore_errors=True)
        os.makedirs(WORKER_DIR, exist_ok=True)
        tpl_db = os.path.join(WORKER_DIR, "template.db")
        subprocess.run(
            [PYTHON, "-B", "-c", _TPL_INIT, tpl_db, PLUGIN_DIR, FRAMEWORK_DIR, _pkg_dir()],
            check=True, timeout=120, capture_output=True,
            text=True, encoding="utf-8", errors="replace", env=env,
        )
    except Exception as _e:                                     # noqa: BLE001
        print(f"⚠️ 私有库模板初始化失败，回落共享库行为: {_e}", flush=True)
        shutil.rmtree(WORKER_DIR, ignore_errors=True)
        tpl_db = None

    t0 = time.time()
    for i, name in enumerate(files):
        path = name if os.path.isabs(name) else os.path.join(TESTS_DIR, name)
        fenv = dict(env)
        if tpl_db:
            fenv["GWEN_GAME_DB"] = os.path.join(WORKER_DIR, f"num_{i}.db")
            shutil.copy2(tpl_db, fenv["GWEN_GAME_DB"])
        ts = time.time()
        timed_out = False
        try:
            proc = subprocess.run(
                [PYTHON, path], capture_output=True, text=True,
                encoding="utf-8", errors="replace", env=fenv, timeout=FILE_TIMEOUT,
            )
            ok = proc.returncode == 0
        except subprocess.TimeoutExpired as te:
            proc, timed_out, ok = te, True, False
        dt = time.time() - ts
        results.append((name, ok, proc, dt, timed_out))
        _report_failure(name, ok, proc, dt, timed_out)

    shutil.rmtree(WORKER_DIR, ignore_errors=True)

    print("\n" + "=" * 60)
    passed = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]
    summary = (f"数值测试汇总: 共 {len(results)} 个文件, ✅ {len(passed)}, "
               f"❌ {len(failed)}, 总耗时 {time.time() - t0:.0f}s")
    if missing:
        summary += f", 跳过 {len(missing)} 个"
    print(summary, flush=True)
    if failed:
        print("失败文件:")
        for name, _, _, _, timed_out in failed:
            print(f"  {'⏱️' if timed_out else '❌'} {name}")
        print("→ 数值门禁未通过：任何数值改动必须本脚本全绿。若失败是数值设计调整所致，"
              "按 docs/NUMERIC_TEST.md 的基线更新流程处理（禁止不更新断言直接改数值）。")
        return 1
    if missing:
        print("→ 数值门禁通过 ✅（跳过项不代表已验证，测试文件补齐后请跑全量复核）", flush=True)
    else:
        print("→ 数值门禁通过 ✅", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))