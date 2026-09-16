#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""拆仓落点一致性门禁 —— 「包独立成仓」之后，**两处落点必须同一版本**，否则门禁是假绿。

为什么需要它（B16 拆仓的硬约束①/②）
----------------------------------
包独立成仓后，同一份包会在**两个物理落点**出现：

    落点A（引擎仓侧）  $GWEN_FRAMEWORK_DIR/games/<包>        ← 引擎仓记录的是 submodule 指针
    落点B（宿主插件侧） <插件根>/framework/games/<包>          ← framework submodule 里的同一指针
    部署面（真正加载）  <插件根>/config.json 的 package_dir（或 $GWEN_PACKAGE_DIR）

门禁跑的是 A（`--framework` / `$GWEN_FRAMEWORK_DIR`），宿主测试与线上读的是 B/部署面。
**只要两边不在同一个提交/同一份内容上**，「测试全绿」就只是拿另一份树量出来的 —— 假绿。
本门禁把这条钉成牙：三个落点必须 **同一包 id + 同一内容 sha256 + 同一提交**，且落点必须是
**包仓的独立检出**（有 `.git`），不能是引擎树里的**内嵌副本**（内嵌 = 两处实现，拆仓没拆干净）。

口径（不写死任何包名）
--------------------
* 包 = `framework/games/*` 里**声明表最大**的那个（`content/data/commands.json` 条数），
  与 `scripts/run_all_tests.py::_find_package_dir()` / `tests/test_command_registration.py::_find_package_dir()`
  **同一口径**（换包 = 换这棵树，判据与包无关）。
* 部署面 = `$GWEN_PACKAGE_DIR` > `<插件根>/config.json` 的 `package_dir`（相对路径按插件根解析）
  —— 与 `main.resolve_package_dir()` 的 ①②③ 同序（真源在 main.py，本脚本只读同一份配置）。
* 内容 sha256 = 逐文件 sha256（相对路径 + 文件哈希，排序后拼接）——排除 `.git/`、`__pycache__/`、`*.pyc`。
  它量的是**内容**；提交号量的是**历史**。两者都要相等（内容相同但提交不同 = 有人手改过/不是同一版）。

用法 / 退出码
------------
    python scripts/check_package_landings.py                       # 默认：$GWEN_FRAMEWORK_DIR > <插件根>/framework
    python scripts/check_package_landings.py --framework DIR        # 显式指引擎仓（门禁口径）
    python scripts/check_package_landings.py --json out.json
退出码 0 = 三个落点一致且都是独立检出；1 = 任一条不成立（**含「引擎仓里还是内嵌目录」**）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(HERE)

SKIP_DIRS = {"__pycache__", ".pytest_cache", ".git"}
SKIP_SUFFIX = (".pyc", ".pyo")
#: 引擎仓 framework/ 下，包落点相对引擎仓根的路径前缀（与 editor/packages.py::DEFAULT_GAMES_DIR 同源）
GAMES_REL = os.path.join("games")


def _u8(stream):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                    # noqa: BLE001
        pass


def git(repo, *args):
    """跑只读 git 命令：返回 (rc, stdout, stderr)。仓库不是 git 仓/命令不可用时 rc!=0。"""
    try:
        p = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except OSError as exc:                               # noqa: BLE001
        return 127, "", str(exc)


def content_sha(root):
    lines = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in sorted(filenames):
            if name.endswith(SKIP_SUFFIX) or name == ".git":
                continue        # ⚠️ 子模块检出里的 `.git` 是**gitfile**（文件，不是目录）
                                #    ⇒ 只按 SKIP_DIRS 排目录会把它当内容比：两个落点的嵌套深度不同
                                #    （引擎仓 games/X vs 宿主 framework/games/X），gitdir 相对路径
                                #    必然不同 ⇒ 内容 sha 恒报「2 个不同」的假红。它不属于包内容。
            full = os.path.join(dirpath, name)
            h = hashlib.sha256()
            with open(full, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h.update(chunk)
            lines.append("%s\t%s" % (os.path.relpath(full, root).replace("\\", "/"), h.hexdigest()))
    lines.sort()
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest(), len(lines)


def read_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def discover_package(games_dir):
    """包目录：`games/*` 里声明表（content/data/commands.json）最大的那个 —— 不写包名。"""
    best, best_n = None, -1
    if not os.path.isdir(games_dir):
        return None
    for name in sorted(os.listdir(games_dir)):
        decl = os.path.join(games_dir, name, "content", "data", "commands.json")
        if not os.path.isfile(decl):
            continue
        data = read_json(decl)
        if not isinstance(data, dict):
            continue
        if len(data) > best_n:
            best, best_n = os.path.join(games_dir, name), len(data)
    return best


def landmark(label, pkg_dir):
    """一个落点的实测事实：存在性 / 独立检出 / 包 id / 内容 sha / 提交。"""
    info = {"label": label, "dir": pkg_dir, "exists": os.path.isdir(pkg_dir),
            "is_checkout": False, "pkg_id": None, "sha": None, "files": 0, "commit": None}
    if not info["exists"]:
        return info
    info["is_checkout"] = os.path.exists(os.path.join(pkg_dir, ".git"))
    man = read_json(os.path.join(pkg_dir, "game.json"))
    info["pkg_id"] = (man or {}).get("id")
    info["sha"], info["files"] = content_sha(pkg_dir)
    if info["is_checkout"]:
        rc, out, _ = git(pkg_dir, "rev-parse", "HEAD")
        if rc == 0:
            info["commit"] = out
    return info


def resolve_framework(explicit):
    if explicit:
        return os.path.abspath(explicit), "--framework"
    env = str(os.environ.get("GWEN_FRAMEWORK_DIR") or "").strip()
    if env:
        return os.path.abspath(env), "$GWEN_FRAMEWORK_DIR"
    return os.path.join(PLUGIN_ROOT, "framework"), "<插件根>/framework（默认）"


def resolve_deployment_package(plugin_root):
    """部署面实际加载的包目录：$GWEN_PACKAGE_DIR > <插件根>/config.json 的 package_dir。"""
    raw = str(os.environ.get("GWEN_PACKAGE_DIR") or "").strip()
    src = "$GWEN_PACKAGE_DIR"
    if not raw:
        cfg = read_json(os.path.join(plugin_root, "config.json")) or {}
        raw = str(cfg.get("package_dir") or "").strip()
        src = "%s/config.json:package_dir" % plugin_root
    if not raw:
        return None, "（未配置：既无 $GWEN_PACKAGE_DIR 也无 config.json:package_dir）"
    if not os.path.isabs(raw):
        raw = os.path.normpath(os.path.join(plugin_root, raw))
    return raw, src


def main(argv=None):
    _u8(sys.stdout)
    ap = argparse.ArgumentParser(description="拆仓落点一致性门禁（两处落点 + 部署面）")
    ap.add_argument("--plugin-root", default=PLUGIN_ROOT, help="宿主插件仓根（默认本脚本上级）")
    ap.add_argument("--framework", default=None, help="引擎仓根（默认 $GWEN_FRAMEWORK_DIR > <插件根>/framework）")
    ap.add_argument("--json", default=None, help="另存机器可读结果")
    args = ap.parse_args(argv)

    plugin_root = os.path.abspath(args.plugin_root)
    framework, fw_src = resolve_framework(args.framework)
    fw_games = os.path.join(framework, GAMES_REL)
    host_fw = os.path.join(plugin_root, "framework")
    print("=" * 78)
    print("拆仓落点一致性门禁（B16）")
    print("  引擎仓（门禁口径 $GWEN_FRAMEWORK_DIR）: %s   [来源：%s]" % (framework, fw_src))
    print("  宿主根: %s" % plugin_root)

    pkg_a = discover_package(fw_games)
    if not pkg_a:
        print("❌ 引擎仓侧找不到任何包：%s（games/*/content/data/commands.json 一个都没有）" % fw_games)
        return 1
    pkg_name = os.path.basename(pkg_a)
    print("  包名（按声明表最大发现，未写死）: %s" % pkg_name)

    pkg_b = os.path.join(host_fw, GAMES_REL, pkg_name)
    dep, dep_src = resolve_deployment_package(plugin_root)
    if dep and os.path.basename(dep.rstrip("\\/")) != pkg_name:
        print("⚠️ 部署面 package_dir 指向的目录名 ≠ 发现的包名：%s（仍按配置的目录核对）" % dep)
    spots = [landmark("A 引擎仓 $GWEN_FRAMEWORK_DIR", pkg_a),
             landmark("B 宿主 framework submodule", pkg_b)]
    if dep:
        spots.append(landmark("C 部署面（config/env）", dep))

    ok = True
    print("-" * 78)
    for s in spots:
        print("  [%s] %s" % (s["label"], s["dir"]))
        print("      存在=%s  独立检出(.git)=%s  包id=%s  内容sha=%s  文件数=%s  提交=%s"
              % (s["exists"], s["is_checkout"], s["pkg_id"],
                 (s["sha"] or "-")[:16], s["files"], (s["commit"] or "-")[:12]))
        if not s["exists"]:
            print("      ❌ 落点不存在")
            ok = False
        elif not s["is_checkout"]:
            print("      ❌ 不是包仓的独立检出（无 .git）= 引擎树里的内嵌副本 ⇒ 拆仓未完成 / 两处实现")
            ok = False
    print("  部署面来源：%s" % dep_src)

    print("-" * 78)
    ids = {s["pkg_id"] for s in spots if s["exists"]}
    shas = {s["sha"] for s in spots if s["exists"]}
    commits = {s["commit"] for s in spots if s["exists"] and s["commit"]}
    checks = [
        ("全部落点都存在", all(s["exists"] for s in spots)),
        ("全部落点是包仓独立检出（非内嵌副本）", all(s["is_checkout"] for s in spots if s["exists"])),
        ("包 id 一致（%s）" % (",".join(sorted(str(i) for i in ids)) or "-"), len(ids) == 1),
        ("内容 sha256 一致（去重后 %d 个不同的 sha）" % len(shas), len(shas) == 1),
        ("提交一致（%s）" % (",".join(sorted(c[:12] for c in commits)) or "无 git 信息"),
         len(commits) <= 1),
    ]
    # 引擎仓若本身是 git 仓：树里记录的必须是 submodule gitlink（160000），且等于检出提交
    if os.path.isdir(os.path.join(framework, ".git")):
        rel = "%s/%s" % (GAMES_REL.replace("\\", "/"), pkg_name)
        rc, out, _ = git(framework, "ls-tree", "HEAD", rel)
        parts = out.split()
        mode = parts[0] if parts else ""
        recorded = parts[2] if len(parts) > 2 else ""
        spot_a = spots[0]
        checks.append(("引擎仓树里 %s 是 submodule gitlink（160000，实测 %s）" % (rel, mode or "无"),
                       mode == "160000"))
        checks.append(("引擎仓记录的指针 == 落点A 检出提交（%s == %s）"
                       % (recorded[:12] or "-", (spot_a["commit"] or "-")[:12]),
                       bool(recorded) and recorded == spot_a["commit"]))
    else:
        print("  （引擎仓 %s 不是 git 仓 —— 「指针 vs 检出」两条跳过；内容/提交一致性仍然照查）" % framework)

    for title, passed in checks:
        print("  %s %s" % ("✅" if passed else "❌", title))
        ok = ok and bool(passed)
    print("-" * 78)
    print("结论：%s" % ("✅ 落点一致（同一包 id / 同一内容 / 同一提交，且都是独立检出）" if ok
                       else "❌ 落点不一致或不是独立检出 —— 门禁若在此状态下全绿即为**假绿**"))
    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"ok": bool(ok), "framework": framework, "framework_source": fw_src,
                       "plugin_root": plugin_root, "package": pkg_name,
                       "deployment": {"dir": dep, "source": dep_src},
                       "spots": spots,
                       "checks": [{"title": t, "ok": bool(p)} for t, p in checks]},
                      fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print("JSON → %s" % args.json)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
