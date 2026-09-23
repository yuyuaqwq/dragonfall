# -*- coding: utf-8 -*-
"""全量回归（**宿主侧**）：枚举 = 「宿主自留件」 + 「包仓那份 tests」（T8 测试单源化）。

口径（T8 作业书）
-----------------
内容侧测试的**唯一真源 = 包仓 `tests/`**（编辑器里的 `framework/games/*/tests` 就是它经
`sync.sh` 部署出来的那一份）。宿主侧 `tests/` 只保留**宿主专属**的门禁（编辑器 / 宿主存储 /
平台桥接 / 跑器自检 …），同名片副本一律删除。

```
枚举  = <plugin>/tests/test_*.py                          ← 宿主自留件
      + <plugin>/framework/games/*/tests/test_*.py        ← 包仓那份（不写死包名）
```

两侧出现同名文件 = **单源被破**：直接醒目报错、退非零（不许默默跑两份 / 只跑一份）。
包仓 tests 目录缺失 / 为空 = 同上（反证③：绝不当成「0 个测试=全绿」）。

用法：
  python scripts/run_all_tests.py [--file=<名|路径>] [--fail-fast] [--jobs=N] [--serial]
                                  [--skip=test_xxx.py[,test_yyy.py]] [--real-astrbot]
                                  [--pkg-only] [--pkg-root=<包仓根>]

包仓入口（`pkg/scripts/run_all_tests.py`）是**薄壳**：只做「发现宿主壳根 → 转调本文件」，
跑器真源唯一在本文件（T8 终态）。薄壳带 `--pkg-only --pkg-root=<源仓根>` 过来：
  - `--pkg-only`    只枚举「包仓那份 tests」，不跑宿主自留件（枚举面之外一切不变）；
  - `--pkg-root=<d>` 指定包仓根 ⇒ 枚举面 = `<d>/tests` —— 是**源仓那份**，不是部署副本
                    `framework/games/<pkg>/tests`（两者由 `sync.sh` 保持一致）；worker 模板库
                    也按该包建。缺 `content/data/commands.json` ⇒ 醒目报错（不当 0 个测试跑绿）。

v117 全量提速（默认并行 + shim astrbot）能力**逐条保留**：
  - 每个测试文件 = 独立子进程 + 独立 GWEN_GAME_DB 私有库（tests/.run_all_workers_<pid>_<ts>/）
  - 每轮跑先建一次空白 schema 模板库，各文件复制一份 → 表结构齐全且零残留
  - 默认 --jobs 按核数自适应（4~16）；--serial 恢复纯串行共享库行为
  - --skip= 跳过；--file= 单文件走旧逻辑（共享库）
  - 默认注入包仓那份的 `tests/shim_astrbot`；--real-astrbot 退回真实 astrbot
  - 硬编码共享 test_game_data.db 的文件自动进「串行槽」先跑

路径装配（T8 去宿主常量）
------------------------
  - 引擎部署面   = `<plugin>/framework`（环境变量 `GWEN_FRAMEWORK_DIR` 覆盖）
  - 宿主壳根     = `<plugin>`（`GWEN_HOST_DIR` 覆盖）
  - 包目录       = `GWEN_PACKAGE_DIR` 优先，否则 `framework/games/*` 里**声明表最大**的那个
                   （`--pkg-root=<根>` 直接指定：枚举面 + worker 模板库都用它）
  - qqbot 根     = 发现（`GWEN_QQBOT_DIR` 优先 → 找「谁家 `data/plugins/<x>` 与插件目录同一
                   实体」的祖先 / 其一见子目录）——只为本仓「平台插件名面」
                   （`data.plugins.<pkg>`）可 import 而给 PYTHONPATH；找不到不报错（多数测试不需要）
  - 子进程解释器 = 本运行器的 `sys.executable`（用哪个 python 跑本器，子进程就用哪个）

注意：
  - 必须用带 pypinyin 的 python 启动（宿主的 uv astrbot python 或同依赖的 python）
  - 跑全量期间不要改动任何源文件（避免中间态误判）
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

# P1-1：子进程强制 UTF-8（否则测试打印 ✅/中文在 GBK 控制台崩溃（UnicodeEncodeError）
# → 假红）。先 setdefault 再在 subprocess 环境里也显式传递，双保险。
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
# v110 审计修复：父进程 stdout 同样强制 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

_BASE_TIMEOUT = 300   # 独占单跑基线（秒）
_TIMEOUT_CAP = 900    # 上限（最慢文件 247s 单跑 ×2.5 并发放大 ≈ 620s，留足余量）
# ★ 2026-09-18 修复「并行假红」——阈值必须随**并发度**放宽：
#   实测（24 核机、默认 16 路并发）最慢文件墙钟被 CPU/IO/内存争用放大 1.5–2×：
#     test_texts_table 单跑 164s → 并发 >300s · u1i2 205s → >300s · u1i4 247s → >300s
#   ⇒ 三个门禁恒报 TIMEOUT（单跑全绿），真回归被假红淹掉、还逼人手工单跑复核。
#   现在：基线 × 「每 4 路并发一档」，并设上限（防真 hang 无限拖全量）。


def _test_timeout(jobs: int) -> int:
    """单文件超时秒数：基线 × 并发档位（每 4 路一档），不超过上限。"""
    slots = max(1, (int(jobs) + 3) // 4)
    return min(_TIMEOUT_CAP, _BASE_TIMEOUT * slots)

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # <plugin>/
HOST_TESTS_DIR = os.path.join(PLUGIN_DIR, "tests")                        # 宿主自留件
FRAMEWORK_DIR = os.path.join(PLUGIN_DIR, "framework")                     # 引擎部署面
GAMES_DIR = os.path.join(FRAMEWORK_DIR, "games")                          # 包部署面（games/*）
PYTHON = sys.executable

# 串行槽：直接赋值 os.environ["GWEN_GAME_DB"] 指向共享 test_game_data.db 的文件
# （不认外层 env，无法用私有库隔离）→ 必须与并行主体错开，保持旧行为先跑。
SERIAL_SLOT = {
    "test_v101_28_food_hot.py",
    "test_v1023_life_prof.py",
    # ★ T8：**写包内磁盘真源**的文件必须与「读同一份真源」的文件错开 ——
    #   `test_gm_reload.py` 会改写 `content/rules/effect_rules.json` 再 `finally` 还原
    #   （它就是测「改盘 → 重载」）。并行跑时 `test_export_package_sync.py` 的落盘规范
    #   检查会读到**写了一半**的文件 ⇒ 偶发红
    #   （实测：本入口 `❌ content/rules/effect_rules.json:['无末尾换行','JSON 坏']`，
    #    单跑 3/3 绿）。
    "test_gm_reload.py",
}

# 退役探针：P2C 族化迁移期 OLD==NEW 差分验证工具；迁移完成后恒 KeyError，run_all 不再纳入。
RETIRED_PROBES = {
    "test_p2cc2_we_family_probe.py",
    "test_p2cc3_we_shield_probe.py",
    "test_p2cc4_extra_dmg_probe.py",
    "test_p2cc5_control_probe.py",
    "test_p2cc6_panel_buff_probe.py",
    "test_p2cc7_marks_probe.py",
    "test_p2cc8_passive_stack_probe.py",
    "test_p2cc9_lifesave_probe.py",
    "test_p2cc10_aux_probe.py",
}

# 探测未来新增的同款硬编码共享库文件（忽略注释行），命中自动进串行槽
_SHARED_DB_RE = re.compile(
    r'os\.environ\[["\']GWEN_GAME_DB["\']\]\s*=\s*[^\n]*test_game_data\.db'
)

# 并行 worker 库的空白 schema 模板初始化（每轮跑只执行一次）。
#   argv[1] = 私有库路径 · argv[2] = 插件根 · argv[3] = 引擎部署面 · argv[4] = 包目录
# ★ T8：`host.store_factory` 是**宿主里能 import 到的那只**（`<plugin>/host/store_factory.py`）；
#   旧写法 `data.plugins.dragonfall.host.store_factory` 要求 qqbot 名面在位（本工作副本的
#   `<ws>/host` 布局下取不到 ⇒ 模板初始化当场 ModuleNotFoundError ⇒ 全量跑器零结果中止，实测）。
_TPL_INIT = (
    "import os,sys;"
    "os.environ['GWEN_GAME_DB']=sys.argv[1];"
    "sys.path.insert(0,sys.argv[2]);"
    "sys.path.insert(0,sys.argv[3]);"
    "from host import store_factory as _sf;"
    "from saintess_engine.package import load_stack;"
    "_pkg=load_stack(sys.argv[4], inject=_sf.inject_handles());"
    "_sf.bind_store(_pkg).init()"
)


def _find_package_dirs():
    """`framework/games/*` 里的**包目录**（含 `content/data/commands.json`），按名排序。

    不写死包名：判据 = 「是不是一个内容包」，不是「叫什么」。
    """
    out = []
    if not os.path.isdir(GAMES_DIR):
        return out
    for name in sorted(os.listdir(GAMES_DIR)):
        pkg = os.path.join(GAMES_DIR, name)
        if os.path.isfile(os.path.join(pkg, "content", "data", "commands.json")):
            out.append(pkg)
    return out


def _pick_package_dir(pkgs):
    """包目录：`GWEN_PACKAGE_DIR` 优先；否则声明表**最大**的那个（与注册门禁同口径）。"""
    env = str(os.environ.get("GWEN_PACKAGE_DIR") or "").strip()
    if env and os.path.isfile(os.path.join(env, "content", "data", "commands.json")):
        return env
    best, best_n = None, -1
    for pkg in pkgs:
        decl = os.path.join(pkg, "content", "data", "commands.json")
        try:
            with open(decl, encoding="utf-8") as fh:
                n = len(json.load(fh) or {})
        except (OSError, ValueError):
            continue
        if n > best_n:
            best, best_n = pkg, n
    return best


def _find_qqbot_dir():
    """qqbot 部署根（`<qqbot>/data/plugins/<插件>` 的 `data` 的父目录）——只为平台名面可 import。

    旧口径 `dirname³(PLUGIN_DIR)` 只在**部署布局**成立；本工作副本里插件目录是 `<ws>/host`，
    qqbot 名面在**兄弟目录** `<ws>/_run_home`（目录联接 → `<ws>/host`）⇒ 死算落空。
    发现顺序：env → 插件目录的各级祖先及其一级子目录里「谁家 data/plugins/<x> 与本插件
    同一实体」（samefile 认联接/软链）→ 找不到返回 ""（不报错：多数测试不碰平台名面）。
    """
    env = (os.environ.get("GWEN_QQBOT_DIR") or "").strip()
    if env and os.path.isdir(env):
        return os.path.abspath(env)
    plugin_abs = os.path.abspath(PLUGIN_DIR)

    def _hit(root):
        plugins = os.path.join(root, "data", "plugins")
        if not os.path.isdir(plugins):
            return False
        try:
            names = sorted(os.listdir(plugins))
        except OSError:
            return False
        for name in names:
            cand = os.path.join(plugins, name)
            try:
                if os.path.isdir(cand) and os.path.samefile(cand, plugin_abs):
                    return True
            except OSError:
                continue
        return False

    home = os.path.dirname(plugin_abs)
    for _ in range(6):
        if _hit(home):
            return home
        try:
            children = sorted(os.listdir(home))
        except OSError:
            children = []
        for name in children:
            child = os.path.join(home, name)
            try:
                if os.path.isdir(child) and _hit(child):
                    return child
            except OSError:
                continue
        parent = os.path.dirname(home)
        if parent == home:
            break
        home = parent
    return ""


def _parse_args(argv):
    fail_fast = "--fail-fast" in argv
    serial = "--serial" in argv
    real_astrbot = "--real-astrbot" in argv
    pkg_only = "--pkg-only" in argv
    pkg_root = None
    jobs = max(4, min(8, os.cpu_count() or 8))  # 默认按核数自适应（4~16）
    only = None
    skips = []
    for a in argv:
        if a.startswith("--file="):
            only = a.split("=", 1)[1]
        elif a.startswith("--jobs="):
            jobs = int(a.split("=", 1)[1])
        elif a.startswith("--skip="):
            for s in a.split("=", 1)[1].split(","):
                s = s.strip()
                if s:
                    skips.append(s if s.endswith(".py") else s + ".py")
        elif a.startswith("--pkg-root="):
            pkg_root = (a.split("=", 1)[1] or "").strip() or None
    return fail_fast, serial, real_astrbot, jobs, only, skips, pkg_only, pkg_root


def _iter_tests(directory):
    """目录下 `test_*.py` 的文件名（排序；目录不存在 → 空）。"""
    try:
        return sorted(f for f in os.listdir(directory)
                      if f.startswith("test_") and f.endswith(".py"))
    except OSError:
        return []


def _collect_files(only, skips, host_names, pkg_sources, search_dirs):
    """返回 (串行槽文件列表, 并行文件列表)。

    `pkg_sources` = [(tests_dir, [文件名…]), …]，顺序即优先级（同名以**先出现**者为准，
    但同名在两侧同时出现时调用方已判定为「单源被破」并中止，正常态不会重叠）。
    `search_dirs` = `--file=<名>` 的解析面（宿主自留件 + 包仓那份；`--pkg-only` 时只有后者）
    —— 传参而不现算，正是为了让包仓入口**不会**误跑宿主侧同名文件。
    """
    if only:
        base = os.path.basename(only if only.endswith(".py") else only + ".py")
        if os.path.isabs(only):
            return [only], []
        for d in search_dirs:
            cand = os.path.join(d, base)
            if os.path.isfile(cand):
                return [cand], []
        return [os.path.join(search_dirs[0], base)], []   # 不存在 → 子进程报错，不静默跳过

    def _want(name):
        return name not in skips and name not in RETIRED_PROBES

    all_files = [os.path.join(HOST_TESTS_DIR, n) for n in host_names]
    for d, names in pkg_sources:
        all_files += [os.path.join(d, n) for n in names]

    serial, parallel = [], []
    for path in all_files:
        name = os.path.basename(path)
        if not _want(name):
            continue
        if name in SERIAL_SLOT:
            serial.append(path)
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                code_lines = [ln for ln in fh.read().splitlines()
                              if not ln.lstrip().startswith("#")]
                if _SHARED_DB_RE.search("\n".join(code_lines)):
                    serial.append(path)
                    continue
        except OSError:
            pass
        parallel.append(path)
    return serial, parallel


def _run_one(f, env, seed_db=None, timeout=None):
    if seed_db is not None:
        shutil.copy2(seed_db, env["GWEN_GAME_DB"])
    ts = time.time()
    try:
        proc = subprocess.run(
            [PYTHON, f], capture_output=True, text=True, encoding="utf-8",
            errors="replace", env=env,
            timeout=timeout if timeout is not None else _BASE_TIMEOUT,
        )
        timed_out, ok = False, proc.returncode == 0
    except subprocess.TimeoutExpired as te:
        proc, timed_out, ok = te, True, False
    return os.path.basename(f), ok, proc, time.time() - ts, timed_out


def _report(name, ok, proc, dt, timed_out, source=""):
    flag = "✅" if ok else ("⏱️" if timed_out else "❌")
    tail = (" [%s]" % source) if source else ""
    print(f"{flag} {name} ({dt:.1f}s, exit={'TIMEOUT' if timed_out else proc.returncode}){tail}",
          flush=True)
    if not ok:
        out_lines = (proc.stdout or "").strip().splitlines() if hasattr(proc, "stdout") else []
        err_lines = (proc.stderr or "").strip().splitlines() if hasattr(proc, "stderr") else []
        for label, lines in (("stdout:", out_lines), ("--- stderr ---", err_lines)):
            tail_lines = lines[-30:] if lines else []
            if tail_lines:
                print(label, flush=True)
                print("\n".join(tail_lines), flush=True)
        print("-" * 60, flush=True)


def _summary(results, t0, n_host, n_pkg, pkg_dirs):
    print("\n" + "=" * 60)
    passed = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]
    print(f"文件: {len(results)} 个，通过 {len(passed)}，失败 {len(failed)}，总耗时 {time.time()-t0:.0f}s")
    print(f"  其中：宿主自留件 {n_host} 个 · 包仓那份 {n_pkg} 个")
    print("【新口径 T8】内容侧测试真源 = 包仓 tests（经 `sync.sh` 部署到"
          " `<plugin>/framework/games/<pkg>/tests`）：")
    for d in pkg_dirs:
        print(f"  · 包仓那份：{d}")
    if failed:
        print("失败文件:")
        for name, _ in failed:
            print(f"  ❌ {name}")
    return 1 if failed else 0


def _run_framework_tests(base_env):
    """前置：跑引擎框架仓自带测试（S8 拆仓后的双轨）。

    引擎已物理分离（`framework/` submodule）——它的纯度门禁 / 中性兜底 / 示例冒烟是本仓
    回归的**前置依赖**。返回 True=通过；框架目录不存在（submodule 未初始化）时跳过并提示。
    """
    runner = os.path.join(FRAMEWORK_DIR, "tests", "run_all.py")
    if not os.path.exists(runner):
        print("⚠️ 跳过引擎框架仓测试：framework/tests/run_all.py 不存在"
              "（submodule 未初始化？`git submodule update --init`）", flush=True)
        return True
    print("── 前置：引擎框架仓测试（framework/tests/run_all.py）──", flush=True)
    try:
        proc = subprocess.run([PYTHON, runner], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", env=base_env,
                              timeout=_BASE_TIMEOUT)
        ok = proc.returncode == 0
    except subprocess.TimeoutExpired:
        ok = False
        proc = None
    tail = (proc.stdout or proc.stderr or "").strip().splitlines()[-12:] if proc else []
    for ln in tail:
        print("   " + ln, flush=True)
    print(f"{'✅' if ok else '❌'} 引擎框架仓测试", flush=True)
    return ok


def _abort(msg):
    print("!" * 78, flush=True)
    print("!! " + msg, flush=True)
    print("!" * 78, flush=True)
    return 1


def main():
    (fail_fast, serial_mode, real_astrbot, jobs, only, skips,
     pkg_only, pkg_root) = _parse_args(sys.argv[1:])

    # ---- 枚举两侧（单源被破 / 包仓那份缺失都**醒目报错**，不许当 0 个测试跑绿）----
    if not os.path.isdir(HOST_TESTS_DIR):
        return _abort("宿主 tests 目录不存在：%s" % HOST_TESTS_DIR)
    # `--pkg-only`（包仓入口薄壳）：宿主自留件不进枚举面 —— 它们归宿主自己的全量跑。
    host_names = [] if pkg_only else _iter_tests(HOST_TESTS_DIR)

    if pkg_root:
        _pr = os.path.abspath(pkg_root)
        if not os.path.isfile(os.path.join(_pr, "content", "data", "commands.json")):
            return _abort("--pkg-root 指向的不是包目录（缺 content/data/commands.json）：%s" % _pr)
        pkgs = [_pr]
    else:
        pkgs = _find_package_dirs()
    pkg_dirs = [os.path.join(p, "tests") for p in pkgs if os.path.isdir(os.path.join(p, "tests"))]
    if not pkg_dirs:
        if pkg_root:
            return _abort(
                ("找不到**包仓那份 tests**（--pkg-root=%s 下没有 tests/）——" + "\n"
                 "!! 内容侧测试真源缺失 = 全量入口不可信（绝不当「0 个测试=全绿」）。") % pkg_root)
        return _abort(
            "找不到**包仓那份 tests**（扫过 %s 下的每个包目录的 tests/）——\n"
            "!! 内容侧测试真源缺失 = 全量入口不可信（绝不当「0 个测试=全绿」）。\n"
            "!! 修法：确认 `framework/games/<包名>/tests/` 在位（`bash sync.sh`）。" % GAMES_DIR)

    pkg_sources = []
    pkg_names = set()
    for d in pkg_dirs:
        names = _iter_tests(d)
        pkg_sources.append((d, names))
        pkg_names.update(names)

    dup = sorted(set(host_names) & pkg_names)
    if dup:
        return _abort(
            "单源被破：以下 %d 个文件**两侧同名**（宿主 tests/ 与包仓那份 tests/）：\n"
            "!!   %s\n"
            "!! T8 口径 = 内容侧真源唯一在包仓；宿主侧同名副本必须删除，"
            "本跑器拒绝在双源态下继续。" % (len(dup), ", ".join(dup[:20])
                                            + (" …" if len(dup) > 20 else "")))

    if not host_names and not pkg_names:
        return _abort("两侧都没枚举到 test_*.py —— 入口不可信，拒绝当全绿。")

    search_dirs = ([] if pkg_only else [HOST_TESTS_DIR]) + [d for d, _ in pkg_sources]
    serial_files, parallel_files = _collect_files(only, skips, host_names, pkg_sources,
                                                  search_dirs)
    if serial_mode:
        parallel_files, serial_files = [], serial_files + parallel_files
    if pkg_only:
        print(f"枚举（--pkg-only · 包仓入口）：包仓那份 {len(pkg_names)} 个"
              f"（来自 {len(pkg_dirs)} 个包 tests 目录；宿主自留件不进枚举面）", flush=True)
    else:
        print(f"枚举：宿主自留件 {len(host_names)} 个 · 包仓那份 {len(pkg_names)} 个"
              f"（来自 {len(pkg_dirs)} 个包 tests 目录）", flush=True)
    for d in pkg_dirs:
        print(f"  · 包仓那份：{d}", flush=True)
    if skips:
        print(f"跳过 {len(skips)} 个文件: {', '.join(skips)}", flush=True)
    if real_astrbot:
        print("使用真实 astrbot（对照模式，较慢）", flush=True)

    # ---- 环境：路径三件套 + shim + 平台名面 ----
    base_env = {**os.environ, "PYTHONIOENCODING": "utf-8",
                "GWEN_SQLITE_SYNC": os.environ.get("GWEN_SQLITE_SYNC", "NORMAL")}
    base_env["GWEN_FRAMEWORK_DIR"] = FRAMEWORK_DIR
    base_env["GWEN_HOST_DIR"] = PLUGIN_DIR
    pkg_dir = _pick_package_dir(pkgs)   # `--pkg-root=` 时 pkgs = [该根] ⇒ 直接命中
    if pkg_dir:
        base_env["GWEN_PACKAGE_DIR"] = pkg_dir
    _pp_parts = []
    # shim astrbot（包仓那份的 `tests/shim_astrbot`；宿主侧不再自留一份）
    for d in pkg_dirs:
        shim = os.path.join(d, "shim_astrbot")
        if not real_astrbot and os.path.isdir(shim):
            _pp_parts.append(shim)
            break
    qqbot = _find_qqbot_dir()
    if qqbot:
        _pp_parts.append(qqbot)
        print(f"平台名面根（data.plugins.*）：{qqbot}", flush=True)
    else:
        print("⚠️ 未发现 qqbot 部署根（data.plugins.* 名面不可 import）——"
              "仅影响依赖该名面的测试；可设 GWEN_QQBOT_DIR", flush=True)
    _pp_parts += [PLUGIN_DIR, FRAMEWORK_DIR] + list(pkg_dirs)
    # ★ T9（2026-09-24）：**扩展包搜索根**也要进 PYTHONPATH。
    #   2026-09-23/24 的包栈重构把一批游戏形状搬进 `<引擎根>/extends/ext_*`，
    #   包内实现（`content/**`）与门禁会直接 `import ext_combat` / `ext_world` …；
    #   原先只有 PLUGIN_DIR / FRAMEWORK_DIR 两根 ⇒ 子进程（含 `schema/validate.py`）
    #   报 `No module named 'ext_combat'` = 整片假红，只能靠外部 PYTHONPATH 兜着。
    for _d in (FRAMEWORK_DIR, os.path.join(PLUGIN_DIR, "framework")):
        _ext = os.path.join(_d, "extends")
        if os.path.isdir(_ext) and _ext not in _pp_parts:
            _pp_parts.append(_ext)
    _old_pp = base_env.get("PYTHONPATH", "")
    base_env["PYTHONPATH"] = os.pathsep.join(
        _pp_parts + ([_old_pp] if _old_pp else []))

    # ---- worker 私有库模板 ----
    worker_dir = os.path.join(HOST_TESTS_DIR, f".run_all_workers_{os.getpid()}_{int(time.time())}")
    tpl_db = None
    if parallel_files:
        shutil.rmtree(worker_dir, ignore_errors=True)
        os.makedirs(worker_dir, exist_ok=True)
        tpl_db = os.path.join(worker_dir, "template.db")
        if not pkg_dir:
            print("❌ 找不到包目录（framework/games/*/content/data/commands.json）"
                  "——worker 模板库无法初始化", flush=True)
            shutil.rmtree(worker_dir, ignore_errors=True)
            return 1
        try:
            subprocess.run(
                [PYTHON, "-B", "-c", _TPL_INIT, tpl_db, PLUGIN_DIR, FRAMEWORK_DIR, pkg_dir],
                check=True, timeout=120, capture_output=True, env=base_env,
                text=True, encoding="utf-8", errors="replace",
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as _e:
            print(f"❌ worker 模板库初始化失败: {_e}", flush=True)
            if isinstance(_e, subprocess.CalledProcessError):
                print("--- 模板初始化 stderr ---\n%s" % (_e.stderr or "")[-2000:], flush=True)
            shutil.rmtree(worker_dir, ignore_errors=True)
            return 1

    results = []
    t0 = time.time()
    # 并行主体按并发档放宽超时；串行槽/引擎前置是独占跑 ⇒ 用基线（更严格）
    par_timeout = _test_timeout(jobs)
    if parallel_files and par_timeout != _BASE_TIMEOUT:
        print(f"单文件超时：串行 {_BASE_TIMEOUT}s ｜ 并行 {par_timeout}s（{jobs} 路并发）",
              flush=True)

    # 0) 前置：引擎框架仓测试
    framework_ok = _run_framework_tests(base_env)

    pkg_source_dirs = {d for d, _names in pkg_sources}

    def _source_of(path):
        return "包仓那份" if os.path.dirname(path) in pkg_source_dirs else "宿主自留"

    # 1) 串行槽
    for f in serial_files:
        name, ok, proc, dt, timed_out = _run_one(f, base_env, timeout=_BASE_TIMEOUT)
        results.append((name, ok))
        _report(name, ok, proc, dt, timed_out, _source_of(f))
        if fail_fast and not ok:
            break

    # 2) 并行主体（每文件独立私有库）
    if parallel_files:
        def make_env(i):
            return {**base_env, "GWEN_GAME_DB": os.path.join(worker_dir, f"test_game_data_w{i}.db")}

        jobs = max(1, min(jobs, len(parallel_files)))
        queue = iter(enumerate(parallel_files))
        executor = ThreadPoolExecutor(max_workers=jobs)
        pending = {}
        fail_seen = False

        def submit_next():
            nonlocal fail_seen
            if fail_fast and fail_seen:
                return False
            try:
                i, f = next(queue)
            except StopIteration:
                return False
            pending[executor.submit(_run_one, f, make_env(i), tpl_db, par_timeout)] = f
            return True

        for _ in range(jobs):
            if not submit_next():
                break
        while pending:
            done, _ = wait(pending, return_when=FIRST_COMPLETED)
            for fut in done:
                f = pending.pop(fut)
                name, ok, proc, dt, timed_out = fut.result()
                results.append((name, ok))
                _report(name, ok, proc, dt, timed_out, _source_of(f))
                if not ok:
                    fail_seen = True
                submit_next()
        executor.shutdown(wait=True)

    shutil.rmtree(worker_dir, ignore_errors=True)
    n_host = sum(1 for n, _ in results if n in set(host_names))
    n_pkg = len(results) - n_host
    rc = _summary(results, t0, n_host, n_pkg, pkg_dirs)
    if not framework_ok:
        print("❌ 引擎框架仓测试未通过（前置门禁）——游戏侧结果仅供参考")
        return 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
