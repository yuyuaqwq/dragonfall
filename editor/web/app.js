/* app.js —— 域切换 / 条目列表 / 按 kind 定制表单 / 原始 JSON / 差异预览 / 保存 / 战斗模拟预览
 * 原生 JS，零依赖。API 契约见 editor/README.md。 */
'use strict';

const D = {
  domain: 'skills',
  domainDef: null,       // {id,label,primary,flat,capabilities}
  list: null,
  info: {},
  key: null,
  meta: null,
  original: null,
  current: null,
  schema: null,
  primary: null,
  filter: '',
  dirty: false,
  formHandle: null,
  compact: true,         // 「按 kind 精简显示」开关
};

const $ = (id) => document.getElementById(id);

async function api(url, opts) {
  const r = await fetch(url, opts);
  let body = null;
  try { body = await r.json(); } catch (e) { body = { ok: false, message: '响应不是 JSON' }; }
  return { status: r.status, body: body };
}

function setStatus(msg) { $('statusbar').textContent = msg; }
function deepCopy(o) { return JSON.parse(JSON.stringify(o)); }
function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined && text !== null) e.textContent = String(text);
  return e;
}

/* --------------------------------------------------------------- diff */
function diff(before, after, path) {
  path = path || '';
  const out = [];
  if (Array.isArray(before) && Array.isArray(after)) {
    if (before.length !== after.length) return [{ path: path, before: before, after: after }];
    before.forEach((b, i) => { out.push(...diff(b, after[i], path + '[' + i + ']')); });
    return out;
  }
  if (before && after && typeof before === 'object' && typeof after === 'object') {
    const keys = Array.from(new Set([...Object.keys(before), ...Object.keys(after)]));
    keys.sort();
    keys.forEach((k) => {
      const sub = path ? path + '.' + k : k;
      if (!(k in before)) out.push({ path: sub, before: undefined, after: after[k] });
      else if (!(k in after)) out.push({ path: sub, before: before[k], after: undefined });
      else out.push(...diff(before[k], after[k], sub));
    });
    return out;
  }
  if (before !== after) out.push({ path: path, before: before, after: after });
  return out;
}
function fmt(v) {
  if (v === undefined) return '（不存在）';
  return JSON.stringify(v);
}

/* ------------------------------------------------- 按 kind 定制的表单档位 */
/* 只改前端渲染，不动 schema：kind 决定「高亮哪些字段 / 精简时隐藏哪些字段」 */
const SKILL_PROFILES = [
  { id: 'dmg', label: '伤害型',
    kinds: ['物理', '魔法', '魔法·火', '魔法·冰', '魔法·雷', '真伤'],
    hl: ['power', 'exprs', 'formula', 'mp', 'cast', 'cd', 'hits', 'aoe', 'element', 'crit',
         'pierce', 'accuracy', 'mech', 'mech_val', 'mech_chance', 'cond', 'lifesteal', 'charge',
         'kind_override', 'pene'],
    dim: ['effect', 'buff_turns', 'team', 'summon', 'heal_formula', 'passive', 'melody',
          'melody_pct', 'finale', 'hate_mult', 'hate_taunt_mult', 'hate_lock_turns'] },
  { id: 'heal', label: '治疗型', kinds: ['治疗'],
    hl: ['heal_formula', 'power', 'mp', 'cast', 'cd', 'team', 'cond', 'buff_turns', 'hp_pct'],
    dim: ['exprs', 'formula', 'hits', 'aoe', 'element', 'mech', 'mech_val', 'mech2'] },
  { id: 'buff', label: '增益 / 防御型', kinds: ['增益', '嘲讽'],
    hl: ['effect', 'buff_turns', 'mp', 'cast', 'cd', 'cond', 'auto', 'stance', 'hate_mult',
         'hate_taunt_mult', 'hate_lock_turns', 'reduce_all', 'reduce_pct'],
    dim: ['exprs', 'formula', 'hits', 'aoe', 'element', 'mech_val', 'lifesteal'] },
  { id: 'passive', label: '被动型', kinds: ['被动'],
    hl: ['passive', 'cond'],
    dim: ['mp', 'cast', 'cd', 'hits', 'aoe', 'element', 'mech', 'mech_val', 'summon'] },
  { id: 'summon', label: '召唤型', kinds: ['召唤'],
    hl: ['summon', 'mp', 'cast', 'cd', 'cond'],
    dim: ['exprs', 'hits', 'aoe', 'element', 'lifesteal'] },
];
const AFFIX_PROFILES = [
  { id: 'stat', label: '常驻属性型', triggers: ['stat'], hl: ['effect'], dim: [] },
  { id: 'onhit', label: '命中触发型', triggers: ['on_hit', 'on_taken'],
    hl: ['effect', 'chance'], dim: [] },
  { id: 'passive', label: '被动判定型', triggers: ['passive'], hl: ['effect', 'chance'], dim: [] },
  { id: 'timed', label: '时序触发型', triggers: ['turn_start', 'battle_start'],
    hl: ['effect', 'chance', 'tiers'], dim: [] },
];

function currentProfile() {
  if (D.domain === 'skills') {
    const k = D.current && D.current.kind;
    return SKILL_PROFILES.find((p) => p.kinds.indexOf(k) >= 0) || null;
  }
  if (D.domain === 'affixes') {
    const t = D.current && D.current.trigger;
    return AFFIX_PROFILES.find((p) => p.triggers.indexOf(t) >= 0) || null;
  }
  return null;
}

function applyKindProfile(box) {
  box.querySelectorAll('.field.kind-hl,.field.kind-dim').forEach((e) => e.classList.remove('kind-hl', 'kind-dim'));
  const prof = currentProfile();
  const bar = $('kprofile');
  if (!bar) return;
  bar.innerHTML = '';
  if (!prof) { bar.hidden = true; return; }
  bar.hidden = false;
  bar.appendChild(el('span', 'kp-tag', '按 kind 定制：' + prof.label));
  if (prof.hl.length) bar.appendChild(el('span', 'kp-hint', '高亮 ' + prof.hl.length + ' 个关键字段'));
  const lbl = el('label', 'kp-toggle');
  const cb = el('input');
  cb.type = 'checkbox';
  cb.checked = D.compact;
  cb.addEventListener('change', () => { D.compact = cb.checked; applyKindProfile(box); });
  lbl.appendChild(cb);
  lbl.appendChild(document.createTextNode(' 精简显示（隐藏无关字段）'));
  bar.appendChild(lbl);

  prof.hl.forEach((p) => {
    box.querySelectorAll('.field[data-path="' + p + '"]').forEach((e) => e.classList.add('kind-hl'));
  });
  if (D.compact) {
    prof.dim.forEach((p) => {
      box.querySelectorAll('.field[data-path="' + p + '"]').forEach((e) => e.classList.add('kind-dim'));
    });
  }
}

/* ------------------------------------------------------------ boot */
async function boot() {
  setStatus('加载域列表…');
  const res = await api('/api/domains');
  if (!res.body.ok) { setStatus('❌ /api/domains 失败: ' + res.body.message); return; }
  const info = res.body;
  D.info = info;
  D.domainDef = (info.domains || []).find((d) => d.id === D.domain) || (info.domains || [])[0] || null;
  if (D.domainDef) D.domain = D.domainDef.id;
  const box = $('domains');
  box.innerHTML = '';
  info.domains.forEach((d) => {
    const b = document.createElement('button');
    b.textContent = d.label;
    b.className = d.id === D.domain ? 'active' : '';
    b.addEventListener('click', () => {
      if (d.id === D.domain) return;
      if (D.dirty && !confirm('当前有未保存改动，确定丢弃并切换域？')) return;
      D.domain = d.id;
      D.key = null; D.original = null; D.current = null; D.list = null;
      $('editor').hidden = true; $('empty').hidden = false;
      closeSim();
      boot();
    });
    box.appendChild(b);
  });
  const badge = $('badge-source');
  badge.textContent = info.source === 'workcopy' ? '数据来源：工作副本' : '数据来源：py 源文件（只读）';
  badge.className = 'badge ' + (info.source === 'workcopy' ? 'workcopy' : 'source');
  $('notice').textContent = '⚠ ' + info.note +
    '　·　校验器: ' + info.validator + '　·　副本路径: ' + info.copy_path +
    '　·　模拟: ' + (info.simulate_available ? '可用' : '不可用');
  await loadList();
  // 深链：index.html#<urlencoded key> 直接打开某条
  const h = decodeURIComponent((location.hash || '').replace(/^#/, ''));
  if (h && h.indexOf('~') >= 0) await selectEntry(h);
}

window.addEventListener('DOMContentLoaded', () => {
  bindUi();
  boot().catch((e) => setStatus('❌ 初始化异常: ' + e));
});

/* ------------------------------------------------------------ list */
async function loadList() {
  setStatus('加载列表…');
  const res = await api('/api/domain/' + D.domain);
  if (!res.body.ok) { setStatus('❌ 列表失败: ' + res.body.message); return; }
  D.list = res.body;
  renderTree();
  setStatus('共 ' + D.list.total + ' 条（' + D.list.groups.length + ' 个分组）');
}

function renderTree() {
  const q = D.filter.trim().toLowerCase();
  const tree = $('tree');
  tree.innerHTML = '';
  let shown = 0;
  D.list.groups.forEach((g) => {
    const hit = g.entries.filter((e) => {
      if (!q) return true;
      return [e.name, e.id, e.kind, g.cls_name, g.label, e.group, e.trigger]
        .join(' ').toLowerCase().indexOf(q) >= 0;
    });
    if (!hit.length) return;
    shown += hit.length;
    const gh = document.createElement('div');
    gh.className = 'group';
    gh.textContent = g.label + '  (' + hit.length + ')';
    tree.appendChild(gh);
    hit.forEach((e) => {
      const it = document.createElement('div');
      it.className = 'item' + (e.key === D.key ? ' active' : '');
      const nm = document.createElement('span');
      nm.className = 'nm';
      nm.textContent = (e.name || e.id) + '  ';
      const id = document.createElement('span');
      id.style.color = 'var(--fg2)';
      id.style.fontSize = '11px';
      id.textContent = e.id;
      nm.appendChild(id);
      const kd = document.createElement('span');
      kd.className = 'kd k-' + e.kind;
      kd.textContent = (e.kind || '') + (e.lv ? ' Lv' + e.lv : '');
      it.appendChild(nm); it.appendChild(kd);
      it.title = e.key;
      it.addEventListener('click', () => selectEntry(e.key));
      tree.appendChild(it);
    });
  });
  $('list-count').textContent = q ? ('匹配 ' + shown + ' / ' + D.list.total) : ('共 ' + D.list.total + ' 条');
}

/* ------------------------------------------------------- selection */
async function selectEntry(key) {
  if (D.dirty && !confirm('当前有未保存改动，确定丢弃并切换？')) return;
  const res = await api('/api/domain/' + D.domain + '/' + encodeURIComponent(key));
  if (!res.body.ok) { setStatus('❌ 读取失败: ' + res.body.message); return; }
  D.key = key;
  D.meta = res.body.meta;
  D.original = res.body.data;
  D.current = deepCopy(res.body.data);
  D.schema = res.body.schema;
  D.primary = res.body.primary || (D.schema.$defs ? Object.keys(D.schema.$defs)[0] : 'skill');
  D.capabilities = res.body.capabilities || {};
  $('empty').hidden = true;
  $('editor').hidden = false;
  $('sk-title').textContent = (D.meta.name || '') + '　' + (D.meta.id || D.meta.sk_id || '');
  const bits = [D.meta.table];
  if (D.meta.cls_name || D.meta.cls_id) bits.push(D.meta.cls_name || D.meta.cls_id);
  if (D.meta.group) bits.push(D.meta.group + (D.meta.branch_lv ? '（Lv' + D.meta.branch_lv + '）' : ''));
  if (D.meta.trigger) bits.push('trigger=' + D.meta.trigger);
  if (D.meta.kind) bits.push('kind=' + D.meta.kind);
  $('sk-meta').textContent = bits.join(' · ');
  $('btn-simulate').disabled = !(D.capabilities && D.capabilities.simulate);
  $('btn-simulate').title = (D.capabilities && D.capabilities.simulate)
    ? '在子进程里跑一场最小战斗，看伤害数值与战斗日志'
    : '该域不支持战斗模拟（仅技能域）';
  renderTree();
  renderForm();
  renderDiff();
  syncJson();
  setDirty(false);
  savebar(null);
  const v = res.body.validation || {};
  setStatus('已载入 ' + key + (v.ok ? '　·　当前值 schema 校验 ✅' : '　·　当前值有 ' + v.errors.length + ' 处违规'));
}

function renderForm() {
  const box = $('tab-form');
  box.innerHTML = '';
  const kp = el('div', 'kprofile');
  kp.id = 'kprofile';
  kp.hidden = true;
  box.appendChild(kp);
  const rootSchema = D.schema.$defs[D.primary];
  if (!rootSchema) {
    box.appendChild(el('div', 'help', '未在 schema 里找到主 def「' + D.primary + '」'));
    return;
  }
  D.formHandle = SchemaForm.render(rootSchema, D.current, {
    onChange: onModelChange,
    onRerender: () => { renderForm(); },
  });
  box.appendChild(D.formHandle.el);
  if (D.saveErrors) SchemaForm.markErrors(box, D.saveErrors);
  applyKindProfile(box);
}

function onModelChange() {
  renderDiff();
  syncJson();
  setDirty(true);
  // kind / trigger 变了 → 重算定制档位（不整体重渲染，避免丢焦点）
  applyKindProfile($('tab-form'));
}

function setDirty(b) {
  D.dirty = b;
  $('dirty-flag').hidden = !b;
  $('btn-save').disabled = !b;
  $('btn-reset').disabled = !b;
}

/* ----------------------------------------------------------- diff tab */
function renderDiff() {
  if (!D.original) return;
  const changes = diff(D.original, D.current);
  const pill = $('diff-count');
  pill.textContent = changes.length;
  pill.className = 'pill' + (changes.length ? ' nz' : '');
  const body = $('diff-body');
  body.innerHTML = '';
  if (!changes.length) {
    body.appendChild(el('div', 'diff-none', '暂无改动。'));
    return;
  }
  const t = document.createElement('table');
  t.className = 'diff';
  t.innerHTML = '<thead><tr><th>字段</th><th>改前</th><th>改后</th></tr></thead>';
  const tb = document.createElement('tbody');
  changes.forEach((c) => {
    const tr = document.createElement('tr');
    [c.path, c.before, c.after].forEach((v, i) => {
      const td = document.createElement('td');
      if (i === 0) { td.textContent = v; td.style.color = 'var(--accent)'; }
      else { td.className = i === 1 ? 'before' : 'after'; td.textContent = fmt(v); }
      tr.appendChild(td);
    });
    tb.appendChild(tr);
  });
  t.appendChild(tb);
  body.appendChild(t);
}

/* ------------------------------------------------------------ json tab */
function syncJson() { $('json-area').value = JSON.stringify(D.current, null, 2); }

function applyJson() {
  try {
    const parsed = JSON.parse($('json-area').value);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error('条目必须是 JSON 对象');
    D.current = parsed;
    $('json-area').classList.remove('bad');
    renderForm(); renderDiff(); setDirty(true);
    setStatus('已从 JSON 同步到表单');
  } catch (e) {
    $('json-area').classList.add('bad');
    setStatus('❌ JSON 解析失败: ' + e.message);
  }
}

/* -------------------------------------------------------------- save */
function savebar(kind, msg, errors) {
  const bar = $('savebar');
  if (!kind) { bar.hidden = true; bar.textContent = ''; return; }
  bar.hidden = false;
  bar.className = 'savebar ' + kind;
  bar.textContent = msg;
  if (errors && errors.length) {
    const ul = document.createElement('ul');
    ul.className = 'err-list';
    errors.slice(0, 40).forEach((e) => {
      ul.appendChild(el('li', null, e.path + '  →  ' + e.message));
    });
    bar.appendChild(ul);
  }
}

async function save() {
  D.saveErrors = null;
  const res = await api('/api/domain/' + D.domain + '/' + encodeURIComponent(D.key), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data: D.current }),
  });
  if (res.status === 200 && res.body.ok) {
    D.original = deepCopy(D.current);
    setDirty(false);
    renderDiff(); syncJson();
    const n = (res.body.changed || []).length;
    savebar('ok', '✅ 保存成功（' + (res.body.created ? '新建' : '更新 ' + n + ' 个字段') +
      '）→ ' + res.body.saved_to);
    setStatus('已写入 ' + res.body.saved_to + '　·　schema 校验 ✅ (' + res.body.validation.engine + ')');
    await loadList();
  } else {
    const v = (res.body.validation || {});
    D.saveErrors = v.errors || [];
    renderForm();
    savebar('err', '❌ ' + (res.body.message || '保存失败') + '（未写盘）', D.saveErrors);
    const first = (D.saveErrors[0] || {});
    if (first.path) {
      const el2 = document.querySelector('#tab-form .field[data-path="' + first.path.replace(/^\$\.?/, '') + '"]');
      if (el2) el2.scrollIntoView({ block: 'center', behavior: 'smooth' });
    }
    setStatus('校验拦截：' + D.saveErrors.length + ' 处违规，数据未写入');
  }
}

function reset() {
  D.current = deepCopy(D.original);
  D.saveErrors = null;
  renderForm(); renderDiff(); syncJson(); setDirty(false); savebar(null);
  setStatus('已还原为载入时的值');
}

async function cloneEntry() {
  if (!D.key) return;
  const parts = D.key.split('~');
  const old = parts[parts.length - 1];
  const nid = prompt('新条目 id（将作为 key 的最后一段）', old + '_copy');
  if (!nid) return;
  parts[parts.length - 1] = nid.trim();
  const newKey = parts.join('~');
  const exists = D.list.groups.some((g) => g.entries.some((e) => e.key === newKey));
  if (exists) { alert('已存在同名 key：' + newKey); return; }
  const res = await api('/api/domain/' + D.domain + '/' + encodeURIComponent(newKey), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data: D.current }),
  });
  if (res.status === 200 && res.body.ok) {
    setStatus('已新建 ' + newKey);
    await loadList();
    selectEntry(newKey);
  } else {
    savebar('err', '❌ 新建失败（未写盘）', (res.body.validation || {}).errors || []);
  }
}

/* ----------------------------------------------------- 战斗模拟预览 */
function openSim() {
  $('sim-panel').hidden = false;
  document.body.classList.add('sim-open');
  if (D.domain === 'skills' && D.meta && D.meta.cls_name) {
    $('sim-class').value = D.meta.cls_name;
  }
}
function closeSim() {
  $('sim-panel').hidden = true;
  document.body.classList.remove('sim-open');
}

async function runSim() {
  if (!D.current) return;
  const body = {
    skill: D.current,
    skill_lv: Number($('sim-skilllv').value) || 1,
    attacker: { class_name: $('sim-class').value.trim() || '战士',
                level: Number($('sim-level').value) || 20 },
    defender: { def: Number($('sim-def').value) || 0,
                mdef: Number($('sim-mdef').value) || 0 },
  };
  const out = $('sim-body');
  out.innerHTML = '';
  out.appendChild(el('div', 'sim-idle', '⏳ 正在子进程里跑引擎…'));
  setStatus('模拟中…（子进程装配引擎，首次约 1-3 秒）');
  const res = await api('/api/simulate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  renderSim(res.body, res.status);
}

function renderSim(b, status) {
  const out = $('sim-body');
  out.innerHTML = '';
  $('sim-sub').textContent = (D.current && D.current.name ? D.current.name + ' · ' : '') +
    'kind=' + ((D.current && D.current.kind) || '—');
  if (!b || b.ok !== true) {
    const box = el('div', 'sim-err');
    box.appendChild(el('div', 'sim-err-msg', '❌ ' + ((b && b.message) || '模拟失败')));
    const v = b && b.validation;
    if (v && v.errors && v.errors.length) {
      const ul = el('ul', 'err-list');
      v.errors.slice(0, 20).forEach((e) => ul.appendChild(el('li', null, e.path + '  →  ' + e.message)));
      box.appendChild(ul);
    }
    if (b && b.traceback) {
      const pre = el('pre', 'sim-tb', b.traceback);
      box.appendChild(el('div', 'sim-sec', '引擎异常摘要'));
      box.appendChild(pre);
    }
    out.appendChild(box);
    setStatus('模拟未成功：' + ((b && b.message) || ('HTTP ' + status)));
    return;
  }
  // 伤害大数字
  const hero = el('div', 'sim-hero');
  hero.appendChild(el('div', 'sim-dmg', String(b.damage)));
  hero.appendChild(el('div', 'sim-dmg-cap', '对目标伤害'));
  if (b.self_heal) hero.appendChild(el('div', 'sim-heal', '自身回复 ' + b.self_heal));
  out.appendChild(hero);

  const grid = el('div', 'sim-grid');
  const rows = [
    ['技能等级', b.skill ? b.skill.lv : '—'],
    ['蓝耗', b.mp_used],
    ['施法者', b.attacker ? (b.attacker.class_name + ' Lv' + b.attacker.level) : '—'],
    ['目标', b.defender ? (b.defender.name + ' Lv' + b.defender.level) : '—'],
    ['目标血量', b.hp ? (b.hp.target_before + ' → ' + b.hp.target_after) : '—'],
    ['战斗结果', b.result || '未结束（单次施放）'],
    ['随机种子', b.seed],
  ];
  rows.forEach((r) => {
    grid.appendChild(el('div', 'sim-k', r[0]));
    grid.appendChild(el('div', 'sim-v', String(r[1])));
  });
  out.appendChild(grid);

  (b.warnings || []).forEach((w) => out.appendChild(el('div', 'sim-warn', '⚠ ' + w)));

  out.appendChild(el('div', 'sim-sec', '战斗日志（' + (b.logs || []).length + '）'));
  const lg = el('div', 'sim-logs');
  (b.logs || []).forEach((l) => lg.appendChild(el('div', 'sim-log', l)));
  if (!(b.logs || []).length) lg.appendChild(el('div', 'sim-idle', '（空）'));
  out.appendChild(lg);

  const det = el('details', 'sim-events');
  det.appendChild(el('summary', null, '关键事件（' + (b.events || []).length + '）'));
  (b.events || []).forEach((ev) => {
    det.appendChild(el('div', 'sim-ev', '• ' + ev.event + '　' + JSON.stringify(ev.ctx)));
  });
  out.appendChild(det);
  setStatus('模拟完成：伤害 ' + b.damage +
    '　·　日志 ' + (b.logs || []).length + ' 条　·　事件 ' + (b.events || []).length + ' 个');
}

/* --------------------------------------------------------------- ui */
function bindUi() {
  $('search').addEventListener('input', (e) => { D.filter = e.target.value; if (D.list) renderTree(); });
  $('btn-save').addEventListener('click', save);
  $('btn-reset').addEventListener('click', reset);
  $('btn-json-apply').addEventListener('click', applyJson);
  $('btn-clone').addEventListener('click', cloneEntry);
  $('btn-simulate').addEventListener('click', () => { openSim(); runSim(); });
  $('btn-sim-run').addEventListener('click', runSim);
  $('btn-sim-close').addEventListener('click', closeSim);
  $('tabs').addEventListener('click', (e) => {
    const b = e.target.closest('button[data-tab]');
    if (!b) return;
    document.querySelectorAll('#tabs button[data-tab]').forEach((x) => x.classList.toggle('active', x === b));
    ['form', 'json', 'diff'].forEach((t) => { $('tab-' + t).hidden = (t !== b.dataset.tab); });
  });
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !$('sim-panel').hidden) { closeSim(); return; }
    if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); if (D.dirty) save(); }
  });
  window.addEventListener('beforeunload', (e) => {
    if (D.dirty) { e.preventDefault(); e.returnValue = ''; }
  });
}
