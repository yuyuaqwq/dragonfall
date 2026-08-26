# -*- coding: utf-8 -*-
"""v130.2g 新功能固化测试（test_v1302g_job_guide.py）：『职业』/『职业 <名称>』指令

落地玩家意见 #1（zerc）「增加查看职业信息的功能」。覆盖：
  ① 数据一致性：job_guide 表与 classes.py / core_resources.py 全字段交叉核对
     （desc/name 逐字相等、position 为 desc 子串、资源字段逐字相等、基础档位门槛与
     EVOLVE_LEVELS 同源、任务链名/种族血缘自动派生且与 desc 一致）
  ② 『职业』一览：12 职业（基础六 + 隐藏六）全名出现 + 分组标题
  ③ 『职业 <名称>』详情：12 职业名逐一可解析（resolve_job + 指令直跑），
     详情含核心机制字段（资源名 + 上限 + 机制 desc）
  ④ 别名解析：武僧/苦修士 → 淬势者、歌者/牧师攻线歌者 → 牧师（详情含 歌者/吟游诗人）
  ⑤ 未知职业友好提示（未找到 + 『职业』看列表指引）；模糊多命中提示
  ⑥ 注册一致性：_registry 静态表含 job_guide，正则命中 无参/带参/At 前缀

运行：python tests/test_v1302g_job_guide.py（exit=0 全绿）
设计：纯数据 + 纯信息指令，不依赖玩家存档；独立私有临时库（绝不触碰生产库）。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 独立私有临时库（与 conftest 默认隔离，防残留影响）
_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_v1302g_job_guide.db")
os.environ["GWEN_GAME_DB"] = _DB

from conftest import C, run, FakeEvent, clean_db  # noqa: E402

from data.plugins.dragonfall.game.data.job_guide import (  # noqa: E402
    JOB_GUIDE, BASE_ORDER, HIDDEN_ORDER, HIDDEN_SUCCESSORS,
    JOB_ALIASES, EXTRA_RESOURCES, resolve_job,
)
from data.plugins.dragonfall.game.commands.job_guide import JobGuideCmds  # noqa: E402
from data.plugins.dragonfall.game.commands._registry import COMMAND_REGEX  # noqa: E402

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")
    return cond


async def job_cmd(msg, jc):
    """直跑 『职业』handler，返回拼接文本"""
    msgs = await run(jc.job_guide, FakeEvent("g1", "u1", msg))
    return "".join(str(x) for x in msgs)


async def main():
    clean_db()  # 建独立测试库（handler 不读档，仅保环境干净）
    jc = JobGuideCmds()
    ok = True

    # ===== ① 数据一致性（classes.py / core_resources.py 交叉核对） =====
    print("【① 数据一致性】")
    ok &= check("12 职业全量（基础六 + 隐藏六）",
                len(JOB_GUIDE) == 12 and len(BASE_ORDER) == 6 and len(HIDDEN_ORDER) == 6,
                f"实际 {len(JOB_GUIDE)}/{len(BASE_ORDER)}/{len(HIDDEN_ORDER)}")
    for cid, g in JOB_GUIDE.items():
        cls = C.CLASSES[cid]
        res = C.CORE_RESOURCES.get(cid, {})
        ok &= check(f"[{cid}] name 与 classes.py 一致", g["name"] == cls.get("name"), g["name"])
        ok &= check(f"[{cid}] desc 与 classes.py 逐字一致", g["desc"] == cls.get("desc"))
        ok &= check(f"[{cid}] position 为 desc 子串", g["position"] in g["desc"])
        ok &= check(f"[{cid}] 资源字段与 core_resources.py 一致",
                    (g["resource_name"], g["resource_max"], g["resource_desc"])
                    == (res.get("name", ""), res.get("max", 0), res.get("desc", "")))
        if g["hidden"]:
            want_tlv = cls.get("tier_levels") or {1: 40, 2: 60, 3: 90}
            ok &= check(f"[{cid}] 隐藏线档位门槛 40/60/90",
                        g["tier_levels"] == want_tlv, str(g["tier_levels"]))
            ok &= check(f"[{cid}] 任务链名自动派生且与 desc 一致",
                        bool(g["task_name"]) and f"需完成{g['task_name']}任务链" in g["desc"],
                        g["task_name"])
            if g["src_race"]:
                ok &= check(f"[{cid}] 种族限制与 RACES 名一致",
                            g["race_name"] == (C.RACES.get(g["src_race"]) or {}).get("name", ""),
                            g["race_name"])
            ok &= check(f"[{cid}] 血缘 src_base 有效", g["src_base"] in JOB_GUIDE)
            ok &= check(f"[{cid}] 隐藏线在基础线继承表中", cid in HIDDEN_SUCCESSORS.get(g["src_base"], []))
        else:
            ok &= check(f"[{cid}] 基础档位门槛与 EVOLVE_LEVELS 同源",
                        g["tier_levels"] == C.EVOLVE_LEVELS, str(g["tier_levels"]))
            ok &= check(f"[{cid}] 攻/守双线（T1 两个分支）",
                        len(g.get("tiers", {}).get(1, [])) == 2, str(g.get("tiers", {}).get(1)))

    # ===== ② 『职业』一览 =====
    print("【② 『职业』一览】")
    txt = await job_cmd("职业", jc)
    ok &= check("一览含 12 职业全名", all(g["name"] in txt for g in JOB_GUIDE.values()))
    ok &= check("一览分组标题（基础六/隐藏六）", "基础六职业" in txt and "隐藏六职业" in txt)
    ok &= check("一览带使用指引", "『职业 <名称>』" in txt or "看详情" in txt)

    # ===== ③ 单职业详情：12 职业名逐一解析 + 核心机制字段 =====
    print("【③ 单职业详情】")
    for cid, g in JOB_GUIDE.items():
        ok &= check(f"resolve_job('{g['name']}') → {cid}", resolve_job(g["name"]) == cid)
        d = await job_cmd(f"职业 {g['name']}", jc)
        ok &= check(f"『职业 {g['name']}』详情可出", g["name"] in d and "核心资源" in d)
        ok &= check(f"『职业 {g['name']}』含资源机制字段",
                    g["resource_name"] in d and str(g["resource_max"]) in d and g["resource_desc"] in d)
        if g["hidden"]:
            ok &= check(f"『职业 {g['name']}』含解锁方式",
                        "解锁" in d and (g["task_name"] in d or "试炼" in d))
        else:
            # 基础职业：详情应标注隐藏传承（若其下有隐藏线）
            if HIDDEN_SUCCESSORS.get(cid):
                ok &= check(f"『职业 {g['name']}』含隐藏传承提示", "隐藏传承" in d)

    # ===== ④ 别名解析 =====
    print("【④ 别名解析】")
    ok &= check("别名 武僧 → 淬势者线", resolve_job("武僧") == "cls_wu_sheng")
    ok &= check("别名 苦修士 → 淬势者线", resolve_job("苦修士") == "cls_wu_sheng")
    ok &= check("别名 苦修 → 淬势者线", resolve_job("苦修") == "cls_wu_sheng")
    d = await job_cmd("职业 武僧", jc)
    ok &= check("『职业 武僧』详情展示新名 淬势者", "淬势者" in d and "核心资源" in d, d[:80])
    d = await job_cmd("职业 苦修士", jc)
    ok &= check("『职业 苦修士』详情展示新名 淬势者", "淬势者" in d)
    ok &= check("别名 歌者 → 牧师", resolve_job("歌者") == "cls_mu_shi")
    d = await job_cmd("职业 牧师攻线歌者", jc)
    ok &= check("『职业 牧师攻线歌者』→ 牧师详情（攻线·歌者）",
                "牧师" in d and "歌者" in d and "吟游诗人" in d, d[:120])
    ok &= check("别名 龙血 → 龙裔誓约线", resolve_job("龙血") == "cls_dragon_oath")
    ok &= check("显示名 id 直查", resolve_job("cls_chronomancer") == "cls_chronomancer")
    # 牧师攻线·歌者双资源（共鸣+回声）在详情中展示
    d = await job_cmd("职业 牧师", jc)
    ok &= check("牧师详情含歌者双资源（共鸣+回声）", "共鸣" in d and "回声" in d)

    # ===== ⑤ 未知/模糊 =====
    print("【⑤ 未知/模糊】")
    d = await job_cmd("职业 龙傲天", jc)
    ok &= check("未知职业友好提示", "未找到" in d and "『职业』" in d, d[:80])
    d = await job_cmd("职业 行者", jc)
    ok &= check("模糊多命中→候选提示", "匹配到多个职业" in d, d[:80])

    # ===== ⑥ 注册一致性 =====
    print("【⑥ 注册一致性】")
    pat = COMMAND_REGEX.get("job_guide")
    ok &= check("_registry 静态表含 job_guide", pat is not None)
    if pat:
        rx = re.compile(pat)
        ok &= check("『职业』命中", bool(rx.match("职业")))
        ok &= check("『职业 战士』命中", bool(rx.match("职业 战士")))
        ok &= check("『[At:1] 职业 淬势者』命中", bool(rx.match("[At:1] 职业 淬势者")))
        ok &= check("『职业重置』不命中（与转职重置无冲突）", not rx.match("职业重置"))
        # 正则与命令层装饰器同源（防矩阵测试漂移）
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "game", "commands", "job_guide.py"),
                   encoding="utf-8").read()
        ok &= check("装饰器正则与静态表逐字一致", f'r"{pat}"' in src)

    print("\n结果: %d 通过, %d 失败" % (passed, failed))
    return 0 if not failed else 1


if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()) or (1 if failed else 0))