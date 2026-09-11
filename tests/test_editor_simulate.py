# -*- coding: utf-8 -*-
"""编辑器阶段 2.3 回归：战斗模拟预览（子进程跑引擎）+ 域扩展（skills / affixes）。

覆盖：
- 多域泛化：DOMAIN_DEFS / list_payload / get_entry / validate_entry 对 skills 与 affixes 都成立
- schema 校验：非法条目（bad kind）被拦下
- simulation：`editor/simulate.py` 真跑子进程 → 真技能（挥砍）返回真实伤害 + 日志 + 事件
- HTTP 层：起 ThreadingHTTPServer（端口 0），真发请求验证 /api/domains、/api/domain/affixes、
  /api/simulate 成功路径 + 非法技能 422 友好报错
- 不改盘：模拟前后 editor/.workdir 不存在/无变化；引擎模拟不 import game 进本进程

跑法：python tests/test_editor_simulate.py（exit=0 全绿）
"""
import json
import os
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PLUGIN_DIR, "framework"))  # 引擎框架包（S8 物理分离：framework/ 为引擎 submodule）
EDITOR_DIR = os.path.join(PLUGIN_DIR, "editor")
if EDITOR_DIR not in sys.path:
    sys.path.insert(0, EDITOR_DIR)
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import data_io          # noqa: E402
import simulate         # noqa: E402
import server as srv    # noqa: E402

PASS = 0
FAIL = 0
FAILURES = []


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        FAILURES.append(f"{name}: {detail}")
        print(f"  ❌ {name}  {detail}")


# --------------------------------------------------------------------- data layer
def t_domains():
    print("【1 多域泛化】")
    check("域列表 = skills + affixes", set(data_io.DOMAINS) == {"skills", "affixes"},
          str(data_io.DOMAINS))
    check("每域都有 label/schema/primary/source",
          all(all(k in data_io.DOMAIN_DEFS[d] for k in ("label", "schema", "primary", "source", "tables"))
              for d in data_io.DOMAINS))

    sk = data_io.list_payload("skills")
    check("skills 列表有数据（>= 250 条）", sk["total"] >= 250, f"total={sk['total']}")
    check("skills primary=skill", sk["primary"] == "skill")

    af = data_io.list_payload("affixes")
    check("affixes 列表有数据（76 条）", af["total"] == 76, f"total={af['total']}")
    check("affixes primary=affix", af["primary"] == "affix")
    check("affixes 按 kind 分 2 组", len(af["groups"]) == 2,
          str([g["id"] for g in af["groups"]]))

    entry = af["groups"][0]["entries"][0]
    meta, data = data_io.get_entry("affixes", entry["key"])
    check("affix 单条可读且形状正确",
          isinstance(data, dict) and data.get("name") and meta and meta["id"] == entry["id"],
          str(entry))
    check("affix 单条过 schema", data_io.validate_entry("affixes", data)["ok"])

    bad = dict(data, kind="badkind")
    v = data_io.validate_entry("affixes", bad)
    check("非法 affix kind 被拦下", not v["ok"] and any(e["path"] == "$.kind" for e in v["errors"]),
          str(v["errors"][:1]))

    skill_meta, skill = data_io.get_entry("skills", _find_skill_key("挥砍"))
    check("skills 单条可读（挥砍）", isinstance(skill, dict) and skill.get("name") == "挥砍")
    return skill


def _find_skill_key(name):
    for g in data_io.list_payload("skills")["groups"]:
        for e in g["entries"]:
            if e["name"] == name:
                return e["key"]
    return None


# ---------------------------------------------------------------------- simulate
def t_simulate(skill):
    print("【2 战斗模拟（子进程）】")
    check("simulate worker 存在", simulate.available())
    before = os.path.isdir(os.path.join(EDITOR_DIR, ".workdir"))
    res = simulate.simulate({"skill": skill,
                             "attacker": {"class_name": "战士", "level": 20}})
    check("模拟成功 ok=True", res.get("ok") is True, str(res)[:200])
    check("返回真实伤害（> 0）", isinstance(res.get("damage"), int) and res["damage"] > 0,
          f"damage={res.get('damage')}")
    check("返回战斗日志", isinstance(res.get("logs"), list) and len(res["logs"]) > 0,
          str(res.get("logs")))
    check("返回关键事件（含 skill_hit）",
          any(e.get("event") == "skill_hit" for e in (res.get("events") or [])),
          str([e.get("event") for e in (res.get("events") or [])]))
    check("报告蓝耗 = 技能声明", res.get("mp_used") == skill.get("mp"),
          f"mp_used={res.get('mp_used')} declared={skill.get('mp')}")
    check("主进程未被 import game 污染", "game" not in sys.modules
          or not any(m.startswith("battle2") for m in sys.modules),
          str([m for m in sys.modules if m.startswith('game')][:5]))
    after = os.path.isdir(os.path.join(EDITOR_DIR, ".workdir"))
    check("模拟不改盘（.workdir 状态不变）", before == after)

    # 技能等级可调 → 伤害应随等级变化（exprs 里含 skill_lv）
    res2 = simulate.simulate({"skill": skill, "skill_lv": 5,
                              "attacker": {"class_name": "战士", "level": 20}})
    check("skill_lv=5 仍成功且伤害不同",
          res2.get("ok") and res2.get("damage") != res.get("damage"),
          f"lv1={res.get('damage')} lv5={res2.get('damage')}")
    return res


# ---------------------------------------------------------------------- HTTP
def t_http(skill):
    print("【3 HTTP 层（真起服务 + 真请求）】")
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), srv.Handler)
    port = httpd.server_address[1]
    th = threading.Thread(target=httpd.serve_forever, daemon=True)
    th.start()
    base = f"http://127.0.0.1:{port}"

    def call(path, data=None):
        url = base + path
        body = None
        headers = {}
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=body, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8"))

    try:
        s, b = call("/api/domains")
        check("GET /api/domains 200 + 2 域", s == 200 and len(b["domains"]) == 2, str(s))
        check("/api/domains 报告 simulate 可用", b.get("simulate_available") is True)

        s, b = call("/api/domain/affixes")
        check("GET /api/domain/affixes 200 + 76 条", s == 200 and b["total"] == 76,
              f"{s} total={b.get('total')}")

        s, b = call("/api/schema/affixes")
        check("GET /api/schema/affixes 含 $defs.affix",
              s == 200 and "affix" in b["schema"].get("$defs", {}), str(s))

        s, eb = call("/api/domain/skills/" + urllib.parse.quote(_find_skill_key("挥砍")))
        check("GET 单条 200 且带 primary", s == 200 and eb.get("primary") == "skill", str(s))

        s, b = call("/api/simulate", {"skill": skill,
                                      "attacker": {"class_name": "战士", "level": 20}})
        check("POST /api/simulate 200 + ok", s == 200 and b.get("ok") is True, f"{s} {str(b)[:120]}")
        check("POST /api/simulate 真实伤害 > 0", b.get("damage", 0) > 0, f"damage={b.get('damage')}")
        print(f"     [真实读数] damage={b.get('damage')} logs={b.get('logs')}")

        bad = dict(skill, kind="不存在的职业", name="")
        s, b = call("/api/simulate", {"skill": bad})
        check("非法技能 → 422 友好报错", s == 422 and b.get("ok") is False,
              f"{s} {str(b)[:120]}")
        check("非法技能报错带字段定位",
              any(e.get("path") == "$.kind" for e in (b.get("validation", {}).get("errors") or [])),
              str(b.get("validation", {}).get("errors"))[:160])

        s, b = call("/api/domain/affixes/AFFIXES~does_not_exist")
        check("不存在条目 → 404", s == 404, str(s))
    finally:
        httpd.shutdown()
        httpd.server_close()


def main():
    print("=" * 60)
    print("编辑器阶段 2.3：模拟预览 + 域扩展回归")
    print("=" * 60)
    skill = t_domains()
    if not skill:
        print("❌ 找不到「挥砍」，无法继续模拟测试")
        return 1
    t_simulate(skill)
    t_http(skill)
    print("\n" + "=" * 60)
    print(f"结果：PASS={PASS} FAIL={FAIL}")
    for f in FAILURES:
        print("  ❌ " + f)
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
