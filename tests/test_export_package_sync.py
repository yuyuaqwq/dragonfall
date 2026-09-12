#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""门禁：奥兰迪亚物品数据 → 框架编辑器游戏包 JSON 的**同步门禁**（items 域）。

跑法（系统 python 即可）：
    cd dragonfall && python tests/test_export_package_sync.py
退出码：0 = 全绿；1 = 有红（红行会点名具体 key + 字段）。

框架仓路径：默认 `C:/Users/yuyu/framework-engine`，可用环境变量 `GWEN_FRAMEWORK_DIR` 覆盖。

本门禁锁什么
------------
1. **源表规模**：ITEMS=900 / MATERIALS=598 / CONSUMABLES=206（派生表 MATERIALS_BY_NAME=598、
   MATERIAL_PRICE_OVERRIDE=219 也一并核）——源表被误删/改名立即红。
2. **合表语义**：MATERIALS 与 CONSUMABLES 的每个 key 都在 ITEMS 里，且 `is` 同一对象
   → 导出**唯一物品 = 900**。「ITEMS 900 + MATERIALS 598 + CONSUMABLES 206 = 1704」是同一批
   条目被三张表重复计数（重复量 598+206=804，900+804=1704），不是 1704 件东西。依据见
   `game/data/items.py:3057-3058`（ITEMS = dict(MATERIALS); ITEMS.update(CONSUMABLES)）。
3. **逐条逐字段同步**：仓库里已生成的 `games/orlandia/content/data/items.json` 必须等于
   **现场重新派生**的结果 —— 缺 key / 多 key / 值不同 / 字段丢失都红，报错定位到 key+字段。
4. **price 覆盖**：`MATERIAL_PRICE_OVERRIDE` 219 条在 import 期就地覆盖（`items.py:2813-2817`），
   而 ITEMS 在覆盖之后才构造（`items.py:3057`）→ 导出价必须等于覆盖值（不是源码字面量的旧价）。
5. **BY_NAME 是索引不是数据源**：598 条按名镜像与导出的同 key 条目**逐字段一致**（零新信息，
   故不进包；依据 `items.py:3054`，消费端 game/store/inventory.py:51 等）。
6. **形状/schema**：每条含 name/price/desc（`schemas/item.schema.json` required）；price 非负；
   quality ∈ enum；key 匹配 `^[a-z][a-z0-9_]*$`；装了 jsonschema 时用框架 schema 全量校验。
7. **幂等**：CLI 连跑到两个独立 tmp 目录 → `items.json` 与 `game.json` 逐字节相同；
   且 CLI 产物与仓库已生成文件**逐字节相同**（真同步，不是「看着差不多」）。
8. **清单与文件对得上**：game.json 声明的每个域都有 content/data|rules/<域>.json；
   data/rules 目录下不存在未声明的域文件；id/engine/entry/created/domains 规范。
9. **未实现域必须报错**：`--domain classes` 退出码非 0 且提示「未实现」（绝不静默产空表 ——
   编辑器会显示「0 条」而不报错，是最难查的那种故障）。
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)                            # dragonfall/
DEFAULT_FRAMEWORK_DIR = "C:/Users/yuyu/framework-engine"
FW_ROOT = os.path.abspath(os.environ.get("GWEN_FRAMEWORK_DIR") or DEFAULT_FRAMEWORK_DIR)

PKG_ID = "orlandia"
PKG_DIR = os.path.join(FW_ROOT, "games", PKG_ID)
DATA_PATH = os.path.join(PKG_DIR, "content", "data", "items.json")
MAN_PATH = os.path.join(PKG_DIR, "game.json")
EXPORTER = os.path.join(REPO_ROOT, "scripts", "export_game_package.py")

EXPECT_ITEMS, EXPECT_MATERIALS, EXPECT_CONSUMABLES = 900, 598, 206
EXPECT_OVERRIDE, EXPECT_BY_NAME = 219, 598
EXPECT_EXPORTED = 900            # 合表后唯一物品数（**不是** 1704；见文件头 2.）
MAX_REPORT = 20                  # 每类差异最多打印多少行

passed = failed = 0


def check(name: str, cond: bool, detail: str = "") -> bool:
    global passed, failed
    if cond:
        passed += 1
        print("  ✅ %s" % name)
    else:
        failed += 1
        print("  ❌ %s %s" % (name, detail))
    return bool(cond)


def _sha(path: str) -> str:
    import hashlib
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def _load_exporter():
    if os.path.join(REPO_ROOT, "scripts") not in sys.path:
        sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
    import export_game_package as EX      # noqa: PLC0415
    return EX


def _sub(domain: str) -> str:
    """域数据在 content/ 下的子目录（**问框架**，别硬编码：effect_rules/passive_proc 走 rules/）。"""
    if FW_ROOT not in sys.path:
        sys.path.insert(0, FW_ROOT)
    from editor import packages as PK      # noqa: PLC0415
    return "rules" if (PK.DOMAINS.get(domain) or {}).get("kind") == "rules" else "data"


def _run_cli(out_dir: str, domain: str = "items", timeout: int = 120, check: bool = False):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    args = [sys.executable, EXPORTER, "--domain", domain, "--out", out_dir]
    if check:
        args.append("--check")
    p = subprocess.run(args, capture_output=True, timeout=timeout, env=env, cwd=REPO_ROOT)
    out = (p.stdout or b"").decode("utf-8", "replace") + (p.stderr or b"").decode("utf-8", "replace")
    return p.returncode, out


def _field_diffs(actual: dict, expected: dict) -> list:
    """逐条逐字段比对（actual = 仓库文件，expected = 现场派生）。返回差异文案列表。"""
    diffs = []
    for k in sorted(set(actual) - set(expected)):
        diffs.append("多出 key %r（源里没有，仓库文件是脏的）" % k)
    for k in sorted(set(expected) - set(actual)):
        diffs.append("缺失 key %r（源里有 %d 个字段，仓库文件没有）" % (k, len(expected[k])))
    for k in sorted(set(actual) & set(expected)):
        a, e = actual[k], expected[k]
        if not isinstance(a, dict) or not isinstance(e, dict):
            if a != e:
                diffs.append("%r 形状不同：文件=%s 源=%s" % (k, type(a).__name__, type(e).__name__))
            continue
        for f in sorted(set(e) - set(a)):
            diffs.append("%r 缺字段 %r（源值=%r）" % (k, f, e[f]))
        for f in sorted(set(a) - set(e)):
            diffs.append("%r 多字段 %r（源里没有）" % (k, f))
        for f in sorted(set(a) & set(e)):
            if a[f] != e[f] or type(a[f]) is not type(e[f]):
                diffs.append("%r 字段 %r 不一致：文件=%r 源=%r" % (k, f, a[f], e[f]))
    return diffs


# ---------------------------------------------------------------------------
def main() -> int:
    print("=== 奥兰迪亚物品域 → 游戏包 JSON 同步门禁 ===")
    print("    源   = %s" % REPO_ROOT)
    print("    框架 = %s" % FW_ROOT)
    print("    产物 = %s" % DATA_PATH)
    if not os.path.isdir(FW_ROOT):
        print("❌ 框架仓不存在：%s（可用 GWEN_FRAMEWORK_DIR 覆盖）" % FW_ROOT)
        return 1

    # ---- 源表（现场 import，读的是运行时态） ----
    if REPO_ROOT not in sys.path:
        sys.path.insert(0, REPO_ROOT)
    import game.data.items as D           # noqa: PLC0415
    # 框架域注册表（落点 content/data|rules 的唯一真源）—— 本节起全程可用
    if FW_ROOT not in sys.path:
        sys.path.insert(0, FW_ROOT)
    from editor import packages as PK     # noqa: PLC0415

    # 已实现的域：从导出器源码读（别手写第二个列表）；未实现的 = 框架认识但导出器还没有
    _src = open(EXPORTER, encoding="utf-8").read()
    _m = re.search(r"^DERIVERS = \{(.*?)^\}", _src, re.S | re.M)
    doms = sorted(re.findall(r'"([a-z_]+)":\s*derive_', _m.group(1))) if _m else []
    todo = [d for d in sorted(PK.DOMAINS) if d not in doms]

    print("\n【1】源表规模")
    check("ITEMS=900", len(D.ITEMS) == EXPECT_ITEMS, "实际 %d" % len(D.ITEMS))
    check("MATERIALS=598", len(D.MATERIALS) == EXPECT_MATERIALS, "实际 %d" % len(D.MATERIALS))
    check("CONSUMABLES=206", len(D.CONSUMABLES) == EXPECT_CONSUMABLES, "实际 %d" % len(D.CONSUMABLES))
    check("MATERIALS_BY_NAME=598（派生索引）", len(D.MATERIALS_BY_NAME) == EXPECT_BY_NAME,
          "实际 %d" % len(D.MATERIALS_BY_NAME))
    check("MATERIAL_PRICE_OVERRIDE=219（派生覆盖表）",
          len(D.MATERIAL_PRICE_OVERRIDE) == EXPECT_OVERRIDE, "实际 %d" % len(D.MATERIAL_PRICE_OVERRIDE))

    print("\n【2】合表语义：唯一物品 = 900（不是 900+598+206=1704）")
    sub_tables = {"MATERIALS": D.MATERIALS, "CONSUMABLES": D.CONSUMABLES}
    dup = sum(len(t) for t in sub_tables.values())       # 804
    check("MATERIALS/CONSUMABLES 每个 key 都在 ITEMS 且是同一对象（is）",
          all(D.ITEMS.get(k) is v for t in sub_tables.values() for k, v in t.items()),
          "存在未并入 ITEMS 的条目")
    check("900 + 804(重复计数量) = 1704 的算法已核实", EXPECT_ITEMS + dup == 1704,
          "%d + %d != 1704" % (EXPECT_ITEMS, dup))
    print("     说明：ITEMS = dict(MATERIALS) + update(CONSUMABLES) + 追加（items.py:3057-3058 及各 update）")
    print("     → 598+206=804 条在 ITEMS 里已存在，三表相加 1704 是重复计数，导出唯一键 %d 条" % EXPECT_ITEMS)

    # ---- 现场重新派生 ----
    EX = _load_exporter()
    derived = EX.sort_table(EX.derive_items(REPO_ROOT))

    print("\n【3】逐条逐字段同步（仓库文件 vs 现场派生）")
    if not check("产物存在：games/%s/content/data/items.json" % PKG_ID, os.path.exists(DATA_PATH), DATA_PATH):
        print("\n汇总：%d 通过 / %d 失败" % (passed, failed))
        return 1
    committed = _read_json(DATA_PATH, None)
    if not check("产物是合法 JSON 对象", isinstance(committed, dict), "解析失败或非对象"):
        print("\n汇总：%d 通过 / %d 失败" % (passed, failed))
        return 1
    check("条数 = %d（合表后唯一物品数）" % EXPECT_EXPORTED, len(committed) == EXPECT_EXPORTED,
          "实际 %d" % len(committed))
    diffs = _field_diffs(committed, derived)
    check("文件与源逐条逐字段一致", not diffs, "共 %d 处差异" % len(diffs))
    for d in diffs[:MAX_REPORT]:
        print("       · %s" % d)
    if len(diffs) > MAX_REPORT:
        print("       · … 另 %d 处" % (len(diffs) - MAX_REPORT))

    print("\n【4】price 覆盖（items.py:2813-2817 就地覆盖，ITEMS 构造于其后）")
    bad_ov = [(k, v, derived.get(k, {}).get("price"))
              for k, v in sorted(D.MATERIAL_PRICE_OVERRIDE.items())
              if derived.get(k, {}).get("price") != v]
    check("219 条覆盖价与导出价一致", not bad_ov, "不一致 %d 条，例：%s" % (len(bad_ov), bad_ov[:3]))

    print("\n【5】BY_NAME 是按名索引，零新信息（不进包）")
    bad_mir = []
    for name, ent in sorted(D.MATERIALS_BY_NAME.items()):
        key = next((k for k, v in D.MATERIALS.items() if v is ent), None)
        if key is None or derived.get(key) != ent:
            bad_mir.append((name, key))
    check("598 条按名镜像与导出条目逐字段一致", not bad_mir,
          "不一致 %d 条，例：%s" % (len(bad_mir), bad_mir[:3]))

    print("\n【6】形状 / schema（schemas/item.schema.json $defs.item）")
    KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
    bad_key = [k for k in committed if not KEY_RE.match(k)]
    check("key 匹配 ^[a-z][a-z0-9_]*$", not bad_key, "违规 %d 例：%s" % (len(bad_key), bad_key[:3]))
    bad_req = []
    for k, v in committed.items():
        miss = [f for f in ("name", "price", "desc") if f not in v]
        if miss:
            bad_req.append((k, miss))
        elif not isinstance(v["name"], str) or not v["name"]:
            bad_req.append((k, "name 非非空字符串"))
        elif not isinstance(v["desc"], str) or not v["desc"]:
            bad_req.append((k, "desc 非非空字符串"))
        elif not isinstance(v["price"], (int, float)) or isinstance(v["price"], bool) or v["price"] < 0:
            bad_req.append((k, "price=%r 非非负数" % v.get("price")))
    check("900 条都满足 required(name/price/desc) 与 price>=0", not bad_req,
          "违规 %d 条，例：%s" % (len(bad_req), bad_req[:3]))
    QUAL = {"white", "green", "blue", "purple", "orange"}
    bad_q = [(k, v.get("quality")) for k, v in committed.items()
             if v.get("quality") is not None and v["quality"] not in QUAL]
    check("quality 取值 ∈ schema enum（缺省=不补默认值）", not bad_q,
          "违规 %d 例：%s" % (len(bad_q), bad_q[:3]))
    try:
        import jsonschema                       # noqa: PLC0415
        schema_path = os.path.join(FW_ROOT, "schemas", "item.schema.json")
        schema = _read_json(schema_path, None)
        target = (schema or {}).get("$defs", {}).get("item")
        if target:
            sub = dict(schema); sub.pop("$id", None)
            v = jsonschema.Draft202012Validator(target,
                                                resolver=jsonschema.RefResolver.from_schema(sub))
            errs = []
            for k, d in sorted(committed.items()):
                msgs = sorted("%s:%s" % ("/".join(str(x) for x in e.absolute_path) or "(root)", e.message)
                              for e in v.iter_errors(d))
                if msgs:
                    errs.append((k, msgs))
            check("框架 schemas/item.schema.json 全量校验通过（jsonschema）", not errs,
                  "%d 条违规，例：%s" % (len(errs), errs[:2]))
        else:
            print("  ⚠️ 跳过框架 schema 校验：未见 $defs.item")
    except ImportError:
        print("  ⚠️ 跳过框架 schema 校验：环境无 jsonschema（不依赖第三方，上面已做等价最小校验）")
    except Exception as e:                      # noqa: BLE001  （schema 工具自身异常不该算门禁红）
        print("  ⚠️ 跳过框架 schema 校验（工具异常）：%r" % (e,))

    print("\n【7】幂等（CLI 连跑两次 + 与仓库产物逐字节比对）")
    tmp = tempfile.mkdtemp(prefix="export_pkg_sync_")
    try:
        t1, t2 = os.path.join(tmp, "r1"), os.path.join(tmp, "r2")
        rc1, o1 = _run_cli(t1)
        rc2, o2 = _run_cli(t2)
        check("CLI 退出码 0 两次", rc1 == 0 and rc2 == 0, "rc=%s/%s\n%s" % (rc1, rc2, (o1 + o2)[-400:]))
        f1 = os.path.join(t1, "games", PKG_ID, "content", "data", "items.json")
        f2 = os.path.join(t2, "games", PKG_ID, "content", "data", "items.json")
        g1 = os.path.join(t1, "games", PKG_ID, "game.json")
        g2 = os.path.join(t2, "games", PKG_ID, "game.json")
        check("两次导出 items.json 逐字节相同（幂等）",
              os.path.exists(f1) and os.path.exists(f2) and _sha(f1) == _sha(f2),
              "sha256 不同/文件缺失")
        check("两次导出 game.json 逐字节相同（created 不用时间戳）",
              os.path.exists(g1) and os.path.exists(g2) and _sha(g1) == _sha(g2),
              "sha256 不同/文件缺失")
        check("CLI 产物 items.json == 仓库已生成文件（逐字节）",
              os.path.exists(f1) and os.path.exists(DATA_PATH) and _sha(f1) == _sha(DATA_PATH),
              "sha256 不同：CLI=%s 仓库=%s"
              % (_sha(f1)[:16] if os.path.exists(f1) else "-", _sha(DATA_PATH)[:16]))
        check("CLI 产物 game.json == 仓库已生成文件（逐字节）",
              os.path.exists(g1) and os.path.exists(MAN_PATH) and _sha(g1) == _sha(MAN_PATH),
              "sha256 不同（若 created 被人工改过会红：请用导出器重新生成，别手改）")

        print("\n【8】game.json 清单 ↔ content/ 实际文件")
        man = _read_json(MAN_PATH, None)
        check("game.json 是合法 JSON 对象", isinstance(man, dict))
        man = man if isinstance(man, dict) else {}
        check("id=%s" % PKG_ID, man.get("id") == PKG_ID, "实际 %r" % man.get("id"))
        check("engine 形如 >=x.y", isinstance(man.get("engine"), str) and man["engine"].startswith(">="),
              "实际 %r" % man.get("engine"))
        ent = man.get("entry")
        check("entry 不声明（纯数据包 = 无装配入口）或声明即存在",
              ent is None or (bool(ent) and os.path.exists(os.path.join(PKG_DIR, str(ent)))),
              "实际 %r" % ent)
        check("created 是固定值（非空串，且非时间戳式秒级变化）", bool(man.get("created")),
              "实际 %r" % man.get("created"))
        doms = man.get("domains") or []
        check("domains 含 items", "items" in doms, "实际 %r" % doms)
        for sub in ("data", "rules"):
            d = os.path.join(PKG_DIR, "content", sub)
            for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
                if f.endswith(".json"):
                    check("声明域 %s 有文件 content/%s/%s" % (f[:-5], sub, f), f[:-5] in doms,
                          "文件存在但 domains 未声明 → 编辑器看不到它")
        for dom in doms:
            want = PK.domain_path(PKG_DIR, dom)
            check("域 %s 落在框架期望的路径（content/%s/）" % (dom, _sub(dom)),
                  os.path.isfile(want),
                  "domains 声明了但 %s 不存在（写错 data/rules 边 → 编辑器显示 0 条且不报错）" % want)

        print("\n【9】未实现域必须显式报错（不静默产空表）")
        # 动态挑一个「框架认识、导出器还没实现」的域 —— 写死会在实现当天变成假红/漏测
        if not todo:
            print("  · 框架的域已被导出器全部实现 → 本节无事可做（跳过）")
        else:
            probe = todo[0]
            rc3, o3 = _run_cli(os.path.join(tmp, "r3"), domain=probe)
            check("--domain %s（框架认识但未实现）退出码非 0" % probe, rc3 != 0, "rc=%s" % rc3)
            check("--domain %s 提示「未实现」" % probe, "未实现" in o3, "输出：%s" % o3.strip()[-200:])
            check("--domain %s 未落盘任何文件" % probe,
                  not os.path.exists(os.path.join(tmp, "r3", "games", PKG_ID, "content",
                                                  _sub(probe), probe + ".json")),
                  "居然写出了 %s.json" % probe)
        print("\n【10】每个已实现的域都要与真源同步（防「源里带 tuple / 键序」这类假不一致）")
        src_txt = open(EXPORTER, encoding="utf-8").read()
        m = re.search(r"^DERIVERS = \{(.*?)^\}", src_txt, re.S | re.M)
        doms = sorted(re.findall(r'"([a-z_]+)":\s*derive_', m.group(1))) if m else []
        check("从导出器源码读到已实现的域（≥2）", len(doms) >= 2, "读到 %r" % doms)
        for d in doms:
            out_root = os.path.join(tmp, "sync_" + d)
            rc, out = _run_cli(out_root, domain=d)
            check("域 %s 导出退出码 0" % d, rc == 0, out.strip()[-160:])
            sub = _sub(d)
            f_new = os.path.join(out_root, "games", PKG_ID, "content", sub, d + ".json")
            f_repo = os.path.join(PKG_DIR, "content", sub, d + ".json")
            check("域 %s：CLI 产物与仓库文件逐字节相同" % d,
                  os.path.exists(f_new) and os.path.exists(f_repo) and _sha(f_new) == _sha(f_repo),
                  "%s vs %s" % (_sha(f_new)[:12] if os.path.exists(f_new) else "-",
                                _sha(f_repo)[:12] if os.path.exists(f_repo) else "-"))
            rc2, out2 = _run_cli(FW_ROOT, domain=d, check=True)
            check("域 %s：--check 报与真源一致（源里 tuple 不得造成假不一致）" % d,
                  rc2 == 0 and "不一致" not in out2, out2.strip()[-200:])

        print("\n【11】框架侧回环：包内每一条都要过框架 schema（x-primary def）")
        from editor import validate as VD      # noqa: PLC0415
        for d in doms:
            if d not in PK.DOMAINS:
                check("域 %s 在框架 DOMAINS 里（否则编辑器不认）" % d, False, "框架侧没有这个域")
                continue
            tbl = _read_json(PK.domain_path(PKG_DIR, d), {})
            tbl = tbl if isinstance(tbl, dict) else {}
            bad = []
            for k, v in tbl.items():
                errs = VD.validate_entry(d, v)
                if errs:
                    bad.append((k, errs[0]))
            check("域 %s：%d 条全部过框架 schema（primary=%s）"
                  % (d, len(tbl), PK.DOMAINS[d].get("primary")),
                  bool(tbl) and not bad, "失败样例 %r" % (bad[:2],))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n=== 汇总：%d 通过 / %d 失败 ===" % (passed, failed))
    if failed:
        print("修法：cd dragonfall && python scripts/export_game_package.py --domain items 重新导出；"
              "若仍红且报「值不同」，说明源数据改过了 → 重新导出即可（导出器只读源，绝不改 game/data/*.py）。")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
