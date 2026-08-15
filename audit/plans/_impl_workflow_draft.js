// ============ Dragonfall 审计修复 · 批次2：实施工作流（协调者 + 文件独占分组实施） ============
const ROOT = 'C:/Users/yuyu/qqbot/data/plugins/dragonfall';
const REP = ROOT + '/audit/reports';
const PLAN_DIR = ROOT + '/audit/plans';

// ---------------- 8 项从 risky 提升为直接实施的任务 ----------------
const PROMOTIONS = [
  { id:'H0-S1-honor', domain:'H0', sev:'S', verdict:'confirmed', title:'荣誉可无限对刷：PVP 袭击 CD 加对称（victim 也有 CD）',
    files:['game/commands/combat.py','tests/test_v85_pvp_honor.py'],
    fix_summary:'在 PVP 战斗结算处（combat.py 约 L2901 _set_pvp_cd 目前只写攻击方）对败方 loser 也写入同样的 PVP 袭击 CD（同机制同时长），使两账号交替互刷被 CD 阻断；同步检查 tests/test_v85_pvp_honor.py 相关断言：若现有断言依赖原无 CD 行为，改为验证败方同样进入 CD（第二次交替攻击应被拒）。不改变单次 PVP 荣誉数值。',
    test_impact:'tests/test_v85_pvp_honor.py' },
  { id:'N0-S1-roads-archive', domain:'N0', sev:'S', verdict:'confirmed', title:'必经之路旧脚本族归档 + 禁跑守卫（防误删合法城镇直连）',
    files:['scripts/apply_roads.py','scripts/gen_roads.py','scripts/fix_roads_insert.py','scripts/audit_roads.py','scripts/audit_roads2.py','scripts/fix_connections.py','scripts/fix_connections2.py'],
    fix_summary:'先用 grep 确认这些脚本无任何 import/引用（除互相之间）；然后用 pwsh 的 Move-Item 把它们移入 scripts/_archive/（目录已存在）；每个文件头部加醒目注释块"⚠️ 已废弃（13.4.6 起城镇直连为合法设计，本族脚本前提失效），禁止运行"；并在模块主逻辑入口前加运行时守卫：print("已废弃，禁止运行", file=sys.stderr) 后 sys.exit(1)，防止误跑改库/改 maps.py。原 N0-B1（gen_roads 死循环）与 N0-B2（apply_roads 死代码）两条 confirmed 任务即被本归档覆盖，无需再单独改逻辑。',
    test_impact:'无（脚本零引用，归档前 grep 验证）' },
  { id:'N0-S2-rollback-archive', domain:'N0', sev:'S', verdict:'confirmed', title:'rollback_plus / fix_formatting 全角替换族归档（防误跑破坏文案）',
    files:['scripts/rollback_plus.py','scripts/fix_formatting.py','scripts/fix_formatting2.py','scripts/fix_formatting3.py','scripts/fix_formatting4.py'],
    fix_summary:'同族处理：grep 验证零引用后移入 scripts/_archive/，头部加"⚠️ 一次性迁移已内化，勿重跑：全库无差别全角↔半角替换会破坏合法文案"，主逻辑入口前加 print(stderr)+sys.exit(1) 守卫。',
    test_impact:'无' },
  { id:'G0-A1-craftcost', domain:'G0', sev:'A', verdict:'confirmed', title:'炼金/烹饪产物 craft_cost 注入，堵卖店净正收益（逼近 S 防刷）',
    files:['game/commands/economy.py','game/data/craft.py','game/data/alchemy.py','game/data/cooking.py'],
    fix_summary:'对齐锻造路径：在炼金/烹饪成功产出的分发链路（economy.py 约 L1055-1064 及 craft 分发处）为产物写入 craft_cost=材料总成本，使 _sell_one 卖店封顶（售价≤成本）生效；随后核对强化石、高效治疗药水、金鲤盛宴、御膳汤等产物：若注入后卖价仍>0.9×成本（售价数据高于成本），把对应产物售价下调至 ≤0.9×成本。不改变产物自身效果与正常消耗体验。',
    test_impact:'建议在 test_v60_craft_enhance_index.py 或经济相关测试补"炼制产物卖店价≤成本"断言（若测试文件不在你的专属清单则跳过，仅实现）' },
  { id:'H0-A2-market-sell-atomic', domain:'H0', sev:'A', verdict:'confirmed', title:'上架 market_sell 原子化（防崩溃致物品复制/少货得金）',
    files:['game/store/social.py','game/commands/social.py'],
    fix_summary:'仿照 store/social.py 内 market_buy_atomic（约 L259-285）的 atomic() 单事务模式：新增 market_sell_atomic（上架插入 + 背包扣减同一事务，任一步失败整体回滚），命令层 market_sell handler（social.py 约 L85-86 目前两次独立 commit）改调它。消除崩溃窗口。',
    test_impact:'现有 test_v104_shop_auction_mount.py / test_commands_stall.py 应仍通过' },
  { id:'M0-A3-index-empty', domain:'M0', sev:'A', verdict:'confirmed', title:'data/index.py 死空壳 dict 清理 + ARCHITECTURE.md 归位说明',
    files:['game/data/index.py','ARCHITECTURE.md'],
    fix_summary:'先用 grep 验证 data/index.py 内 5 个空 dict（SKILL_FLAT/_MONSTER_INDEX/_FISH_INDEX/_NPC_INDEX/_SHOP_W_INDEX）确无消费者（_assembly.py 已重新声明）；确认后删除这些死空 dict（保留模块注释说明归属），并修正 ARCHITECTURE.md 中关于 index 归属的描述（约 L40）。注意 _INDEXES 是活共享容器，绝不能删。',
    test_impact:'test_data_registry.py / test_core_index.py 应仍通过' },
  { id:'L0-A1-cmd-config-copies', domain:'L0', sev:'A', verdict:'confirmed', title:'cmd_config.json 漂移副本清除（仓库内明文密码副本）',
    files:['game/data/cmd_config.json','scripts/data/cmd_config.json','tests/data/cmd_config.json'],
    fix_summary:'已 grep 验证全库 py 仅 gm.py:30 注释提及 cmd_config（无代码读取）。用 pwsh Remove-Item 删除这三份漂移副本；根目录 data/cmd_config.json（真实 AstrBot 配置）保留不动。若删除时发现某份确有引用，跳过该份并在报告说明。',
    test_impact:'无' },
  { id:'S3-lootmult-impl', domain:'O0', sev:'S', verdict:'confirmed', title:'每日奇遇 loot_mult/pref_mats 死效果落地实现（跨域合并根因）',
    files:['game/core/event_templates.py','game/commands/combat.py','game/commands/world.py'],
    fix_summary:'1) event_templates.py 的 EventContext.__init__ 增加可选参数 loot_mult=None, pref_mats=None 并存为 self.loot_mult / self.pref_mats；2) 在 tpl_loot_gold、tpl_loot_gold_mats、tpl_loot_materials（及文件内其他产出金币/材料的模板，若有）中应用：金币 gold = int(gold * (ctx.loot_mult or 1.0))；材料抽取时若 ctx.pref_mats 非空则优先从 pref_mats∩材料池 抽取（交集为空回退原池）；3) combat.py L694-700 的 TypeError 回退分支删除（EventContext 已支持这两个参数）；4) world.py L619 面板展示保留（现在为真）。不改 daily_events.py 数据。',
    test_impact:'可选：在现有事件/每日测试文件中补一条"EventContext(loot_mult=2) 后 tpl_loot_gold 金币×2"断言（测试文件若不在专属清单则跳过）' },
];

// ---------------- Schema ----------------
const COORD_SCHEMA = { type:'object', additionalProperties:false, properties:{
  task_count:{type:'number'},
  per_domain_counts:{type:'object'},
  tasks:{ type:'array', items:{ type:'object', additionalProperties:false, properties:{
    id:{type:'string'}, domain:{type:'string'}, sev:{type:'string'}, verdict:{type:'string'},
    title:{type:'string'}, fix_summary:{type:'string'}, files:{type:'array', items:{type:'string'}}
  }, required:['id','domain','sev','verdict','title','fix_summary','files'] } }
}, required:['task_count','per_domain_counts','tasks'] };

const IMPL_SCHEMA = { type:'object', additionalProperties:false, properties:{
  owner:{type:'string'},
  files_done:{ type:'array', items:{ type:'object', additionalProperties:false, properties:{
    file:{type:'string'}, changed:{type:'boolean'}, summary:{type:'string'}
  }, required:['file','changed','summary'] } },
  skipped:{ type:'array', items:{ type:'object', additionalProperties:false, properties:{
    id:{type:'string'}, reason:{type:'string'}
  }, required:['id','reason'] } },
  syntax_ok:{type:'boolean'},
  notes:{type:'string'}
}, required:['owner','files_done','skipped','syntax_ok','notes'] };

// ---------------- 协调者 ----------------
const coordPrompt = `你是「Dragonfall 审计修复」协调者。工作目录：${ROOT}。只读任务：不修改任何文件。
【任务】读取 audit/plans/ 下全部 16 个 *_fixplan.json（用 read 工具，JSON 格式），提取其中 verdict 为 "confirmed" 或 "doc_only" 的全部 findings，逐条原样收录：
- id / sev / title / files / fix_summary / test_impact（如有），domain 用所属计划文件里的 domain 字段。
不得遗漏任何一条、不得改写 fix_summary 内容。
另外把下面 8 条提升任务（verdict 已是 confirmed）一并收录进同一 tasks 数组：
${PROMOTIONS.map(p => `- [${p.id}] (${p.sev}) ${p.title} :: files=${p.files.join('|')}`).join('\n')}
（提升任务的完整 fix_summary 以你 read 到的本提示词为准——它们不在计划文件里，必须按上面 id 对应的 fix_summary 完整收录。为节省输出，你可以在返回时对提升任务保留完整 fix_summary，对计划文件任务保留原文 fix_summary。）
【输出】纯 JSON（无 markdown 代码块）：
{"task_count":<总数>,"per_domain_counts":{"A0":n,...},"tasks":[{"id","domain","sev","verdict","title","fix_summary","files":[...]}...]}
task_count 必须等于各计划文件 confirmed+doc_only 之和加 8。files 必须是相对路径。`;

// ---------------- 实施 Agent ----------------
function implPrompt(bucket) {
  const tasks = bucket.tasks.map(t =>
    `- [${t.id}] (${t.sev}, 来源领域 ${t.domain}, verdict=${t.verdict}) ${t.title}\n  涉及文件: ${t.files.join(', ')}\n  修复方案: ${t.fix_summary}`
  ).join('\n');
  const files = bucket.files.map(f => '- ' + f).join('\n');
  return `你是「Dragonfall 审计修复」实施 Agent（owner=${bucket.owner}，负责 ${bucket.srcDomains.join('/')} 等领域派出的任务）。
项目根目录（你的工作目录）：${ROOT}

【铁律】
- 只允许修改下面【你的专属文件】清单中的文件。禁止修改任何其他文件（包括 audit/ 目录、未列出的游戏文件）。
- 禁止运行游戏本体、禁止运行任何测试（pytest / run_all_tests / 单测脚本）、禁止运行任何写库命令、禁止执行任何会 import 游戏模块的 python 命令（import 会触发 DB 初始化）。
- 验证手段：read / glob / grep 静态检查；编辑后可用 pwsh 运行语法校验：& 'C:/Users/yuyu/AppData/Local/Programs/Python/Python312/python.exe' -m py_compile <文件1> <文件2> ...（只编译不执行；若沙箱禁止则改用 ast.parse 只读校验并注明）。
- 最小 diff，遵循现有代码风格与注释习惯，不引入新依赖，不改变无关行为。

【你的专属文件】（独占，其他 Agent 不会修改它们；同一处修改被多个任务指向时合并为一次编辑）
${files}

【任务清单】
${tasks}

【执行要求】
1. 逐条任务：先 read 相关代码，确认（a）缺陷在当前代码仍存在、（b）fix_summary 仍适用。若代码已迭代导致方案不适用或缺陷已消失，跳过并在报告说明原因。
2. 实现修复：只改专属文件；若某修复必须改非专属文件才能完成，跳过该修复并在报告说明（不要越权改文件）。
3. 涉及测试文件的任务：仅当测试文件属于你的专属文件时才修改它；补回归测试时遵循该测试文件既有风格（conftest 的 FakeEvent/run 模式）。
4. 全部完成后对每个改动文件跑 py_compile 语法校验；确保 syntax_ok。
5. 报告里逐文件给出 changed 与改动摘要；skipped 列表给出 id 与原因。

【输出】最终回复为纯 JSON（无 markdown 代码块）：
{"owner":"${bucket.owner}","files_done":[{"file":"相对路径","changed":true,"summary":"改动摘要"}],"skipped":[{"id":"..","reason":".."}],"syntax_ok":true,"notes":"..."}`;
}

// ---------------- 任务-文件图分组（连通分量） ----------------
function groupTasks(tasks) {
  const sevRank = { S:4, A:3, B:2, C:1 };
  // union-find over nodes (tasks + files)
  const parent = new Map();
  const find = x => { if (!parent.has(x)) parent.set(x, x); while (parent.get(x) !== x) { parent.set(x, parent.get(parent.get(x))); x = parent.get(x); } return x; };
  const union = (a, b) => { const ra = find(a), rb = find(b); if (ra !== rb) parent.set(ra, rb); };
  tasks.forEach((t, i) => {
    const tn = 'T' + i;
    (t.files || []).forEach(f => union(tn, 'F:' + f));
  });
  // group
  const comps = new Map(); // root -> {tasks:[], files:Set}
  tasks.forEach((t, i) => {
    const root = find('T' + i);
    if (!comps.has(root)) comps.set(root, { tasks: [], files: new Set() });
    comps.get(root).tasks.push(t);
    (t.files || []).forEach(f => comps.get(root).files.add(f));
  });
  // owner: domain of highest-sev task (tie: more tasks, then alpha)
  const buckets = [...comps.values()].map(c => {
    let best = null;
    for (const t of c.tasks) {
      const r = sevRank[t.sev] || 1;
      if (!best || r > best.rank || (r === best.rank && t.domain < best.domain)) best = { rank: r, domain: t.domain };
    }
    return {
      owner: best.domain,
      srcDomains: [...new Set(c.tasks.map(t => t.domain))].sort(),
      files: [...c.files].sort(),
      tasks: c.tasks,
    };
  });
  buckets.sort((a, b) => a.owner.localeCompare(b.owner));
  return buckets;
}

// ---------------- 并发池 ----------------
async function poolRun(items, limit, fn) {
  const results = new Array(items.length);
  let idx = 0;
  async function worker() {
    while (idx < items.length) {
      const i = idx++;
      results[i] = await fn(items[i], i);
    }
  }
  const workers = [];
  for (let w = 0; w < Math.min(limit, items.length); w++) workers.push(worker());
  await Promise.all(workers);
  return results;
}

async function runWithRetry(make, label) {
  for (let i = 1; i <= 2; i++) {
    try {
      const r = await make();
      if (r) return r;
      log(label + ' 第' + i + '次返回 null');
    } catch (e) { log(label + ' 第' + i + '次异常: ' + String(e && e.message || e)); }
  }
  return null;
}

// ============ 1. 协调者 ============
phase('实施: 协调者聚合任务');
let coord = null;
for (let i = 1; i <= 3 && !coord; i++) {
  try { coord = await agent(coordPrompt, { schema: COORD_SCHEMA, label: 'COORD', phase: '实施: 协调者聚合任务' }); }
  catch (e) { log('COORD 第' + i + '次异常: ' + String(e && e.message || e)); }
}
if (!coord) return { error: '协调者失败' };
log('协调者任务数: ' + coord.task_count + '，各域: ' + JSON.stringify(coord.per_domain_counts));

// ============ 2. 分组 ============
const buckets = groupTasks(coord.tasks);
log('分组数: ' + buckets.length + '，owner 列表: ' + buckets.map(b => b.owner + '(' + b.tasks.length + ')').join(' '));

// ============ 3. 实施（并发 12） ============
phase('实施: 按文件独占分组并行修复');
const implResults = await poolRun(buckets, 12, (b, i) =>
  runWithRetry(() => agent(implPrompt(b), { schema: IMPL_SCHEMA, label: 'IMP-' + b.owner + '-' + i, phase: '实施: 按文件独占分组并行修复' }), 'IMP-' + b.owner)
);
const okImpl = implResults.filter(Boolean);
const failImpl = buckets.map((b, i) => ({ owner: b.owner, ok: !!implResults[i] })).filter(x => !x.ok);
log('实施完成: ' + okImpl.length + '/' + buckets.length + '，失败: ' + (failImpl.map(f => f.owner).join(',') || '无'));

// ============ 4. 汇总 ============
const changedFiles = [];
const skippedAll = [];
for (const r of okImpl) {
  for (const f of r.files_done || []) changedFiles.push({ owner: r.owner, file: f.file, changed: f.changed, summary: f.summary });
  for (const s of r.skipped || []) skippedAll.push({ owner: r.owner, id: s.id, reason: s.reason });
}
return {
  task_total: coord.task_count,
  per_domain_counts: coord.per_domain_counts,
  buckets: buckets.length,
  implemented: okImpl.map(r => ({ owner: r.owner, files: (r.files_done || []).filter(f => f.changed).map(f => f.file), syntax_ok: r.syntax_ok })),
  changed_files: changedFiles.filter(f => f.changed),
  skipped: skippedAll,
  failed_owners: failImpl.map(f => f.owner),
  notes: okImpl.map(r => r.notes).filter(Boolean)
};
