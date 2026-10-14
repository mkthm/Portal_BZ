(() => {
  'use strict';

  const MAP = window.METRO_MAP;
  const tg = window.Telegram && window.Telegram.WebApp;
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const SVG_NS = 'http://www.w3.org/2000/svg';
  const FILLER_STEP = /Изучите продемонстрированный|Адаптируйте ключевые принципы/i;
  const FAV_KEY = 'kb_favorites';
  const ZOOM_MIN = 0.7, ZOOM_MAX = 2.2, ZOOM_FOCUS = 1.25;
  const SHEET_HALF = 0.40;

  // ---------- DOM ----------
  const $ = (id) => document.getElementById(id);
  const app = $('app');
  const viewport = $('viewport');
  const svg = $('map');
  const world = $('world');
  const linesLayer = $('linesLayer');
  const glintLayer = $('glintLayer');
  const routeLayer = $('routeLayer');
  const stationsLayer = $('stationsLayer');
  const sheet = $('sheet');
  const sheetBody = $('sheetBody');

  function h(tag, attrs, ...children) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v === null || v === undefined || v === false) continue;
      if (k === 'class') el.className = v;
      else if (k === 'text') el.textContent = v;
      else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
      else el.setAttribute(k, v === true ? '' : v);
    }
    for (const c of children.flat()) if (c !== null && c !== undefined) el.append(c);
    return el;
  }
  function s(tag, attrs) {
    const el = document.createElementNS(SVG_NS, tag);
    for (const [k, v] of Object.entries(attrs || {})) if (v !== null && v !== undefined) el.setAttribute(k, v);
    return el;
  }
  function icon(path, size = 16, fill = 'none') {
    const el = s('svg', { width: size, height: size, viewBox: '0 0 24 24', fill, stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'aria-hidden': 'true' });
    el.append(s('path', { d: path }));
    return el;
  }
  const ICON_SWAP = 'M7 4 3 8l4 4M3 8h14M17 20l4-4-4-4M21 16H7';
  const ICON_BOOKMARK = 'M6 3h12v18l-6-4-6 4z';
  const ICON_EXTERNAL = 'M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5';

  // ---------- Telegram ----------
  function haptic(kind) {
    try {
      if (!tg || !tg.HapticFeedback) return;
      if (kind === 'select') tg.HapticFeedback.selectionChanged();
      else tg.HapticFeedback.impactOccurred(kind);
    } catch (_) { /* старые клиенты Telegram */ }
  }
  function openExternal(url) {
    if (tg && tg.openLink) tg.openLink(url);
    else window.open(url, '_blank', 'noopener');
  }
  if (tg) {
    try {
      tg.ready();
      tg.expand();
      tg.disableVerticalSwipes && tg.disableVerticalSwipes();
      tg.setHeaderColor && tg.setHeaderColor('#080C14');
      tg.setBackgroundColor && tg.setBackgroundColor('#080C14');
      tg.BackButton && tg.BackButton.onClick(() => {
        if (state.sheet.level === 'full' && state.sheet.mode === 'node') setSheetLevel('half');
        else closeSheet();
      });
    } catch (_) { /* вне Telegram */ }
  }

  // ---------- Favorites ----------
  function readFavs() {
    try { return JSON.parse(localStorage.getItem(FAV_KEY) || '[]'); } catch (_) { return []; }
  }
  function writeFavs(list) {
    try { localStorage.setItem(FAV_KEY, JSON.stringify(list)); } catch (_) { /* приватный режим */ }
  }

  // ---------- Data ----------
  const stationIds = Object.keys(MAP.stations);
  const stationLines = {};
  for (const id of stationIds) stationLines[id] = [];
  for (const [line, pts] of Object.entries(MAP.routes)) {
    for (const p of pts) if (typeof p === 'string') stationLines[p].push(line);
  }
  const subToStation = new Map();
  for (const id of stationIds) for (const sub of MAP.stations[id].subs) subToStation.set(sub, id);

  let posts = [];
  const postsByStation = {};

  // Убирает нумерацию из текста, склеивает шаги, разорванные посередине фразы,
  // и возвращает пробел после точки перед заглавной буквой.
  function cleanSteps(list) {
    const out = [];
    for (const raw of list) {
      const st = String(raw).replace(/^\s*(?:Шаг\s*\d+\s*[.):—–-]?|\d+\s*[.)])\s*/i, '')
        .replace(/([.!?])([А-ЯЁA-Z])/g, '$1 $2').trim();
      if (!st) continue;
      if (out.length && /^[а-яёa-z]/.test(st)) out[out.length - 1] += ' ' + st;
      else out.push(st);
    }
    return out;
  }
  function realSteps(post) {
    return (post.action_steps || []).filter((st) => st && !FILLER_STEP.test(st));
  }
  function sortPosts(list) {
    return list.slice().sort((a, b) => {
      const sa = realSteps(a).length > 0 ? 1 : 0;
      const sb = realSteps(b).length > 0 ? 1 : 0;
      if (sa !== sb) return sb - sa;
      return String(b.date).localeCompare(String(a.date));
    });
  }
  function indexPosts(data) {
    posts = data;
    for (const id of stationIds) postsByStation[id] = [];
    for (const p of posts) {
      const id = subToStation.get(p.level3_subcategory);
      if (id) postsByStation[id].push(p);
    }
    for (const id of stationIds) postsByStation[id] = sortPosts(postsByStation[id]);
  }
  const countOf = (id) => (postsByStation[id] || []).length;
  function lineCount(line) {
    return MAP.routes[line].filter((p) => typeof p === 'string').reduce((n, id) => n + countOf(id), 0);
  }
  const pt = (p) => (typeof p === 'string' ? [MAP.stations[p].x, MAP.stations[p].y] : p);
  const plainName = (id) => (MAP.stations[id].title || MAP.stations[id].name.replace(/\n/g, ' '));

  const MONTHS = ['янв', 'фев', 'мар', 'апр', 'мая', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];
  function fmtDate(str) {
    const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(str || '');
    if (!m) return '';
    return `${Number(m[3])} ${MONTHS[Number(m[2]) - 1]} ${m[1]}`;
  }
  function plural(n, one, few, many) {
    const m10 = n % 10, m100 = n % 100;
    if (m10 === 1 && m100 !== 11) return one;
    if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few;
    return many;
  }
  const materials = (n) => `${n} ${plural(n, 'материал', 'материала', 'материалов')}`;

  // ---------- Graph for routes ----------
  const adjacency = {};
  for (const id of stationIds) adjacency[id] = [];
  for (const [line, pts] of Object.entries(MAP.routes)) {
    const ids = pts.filter((p) => typeof p === 'string');
    for (let i = 1; i < ids.length; i++) {
      adjacency[ids[i - 1]].push({ to: ids[i], line });
      adjacency[ids[i]].push({ to: ids[i - 1], line });
    }
  }
  function findRoute(from, to) {
    if (from === to) return [{ id: from, line: stationLines[from][0] }];
    const prev = { [from]: null };
    const queue = [from];
    while (queue.length) {
      const cur = queue.shift();
      if (cur === to) break;
      for (const e of adjacency[cur]) {
        if (!(e.to in prev)) { prev[e.to] = { from: cur, line: e.line }; queue.push(e.to); }
      }
    }
    if (!(to in prev)) return null;
    const path = [];
    for (let cur = to; cur; cur = prev[cur] && prev[cur].from) {
      path.unshift({ id: cur, line: prev[cur] ? prev[cur].line : null });
    }
    path[0].line = path[1] ? path[1].line : stationLines[from][0];
    return path;
  }
  function segmentPoints(line, a, b) {
    const pts = MAP.routes[line];
    let i = pts.indexOf(a), j = pts.indexOf(b);
    const rev = i > j;
    if (rev) [i, j] = [j, i];
    const seg = pts.slice(i, j + 1).map(pt);
    return rev ? seg.reverse() : seg;
  }

  // ---------- Geometry ----------
  function roundedPath(points, radius = 14) {
    let d = `M${points[0][0]} ${points[0][1]}`;
    for (let i = 1; i < points.length - 1; i++) {
      const [px, py] = points[i - 1], [cx, cy] = points[i], [nx, ny] = points[i + 1];
      const v1 = [cx - px, cy - py], v2 = [nx - cx, ny - cy];
      const l1 = Math.hypot(...v1), l2 = Math.hypot(...v2);
      const sameDir = Math.abs(v1[0] / l1 - v2[0] / l2) < 1e-6 && Math.abs(v1[1] / l1 - v2[1] / l2) < 1e-6;
      if (sameDir) { d += ` L${cx} ${cy}`; continue; }
      const r = Math.min(radius, l1 / 2, l2 / 2);
      const ax = cx - (v1[0] / l1) * r, ay = cy - (v1[1] / l1) * r;
      const bx = cx + (v2[0] / l2) * r, by = cy + (v2[1] / l2) * r;
      d += ` L${ax} ${ay} Q${cx} ${cy} ${bx} ${by}`;
    }
    const last = points[points.length - 1];
    return d + ` L${last[0]} ${last[1]}`;
  }

  // ---------- Render map ----------
  const lineEls = {};
  const glintEls = {};
  const stationEls = {};

  function renderMap() {
    linesLayer.replaceChildren();
    glintLayer.replaceChildren();
    stationsLayer.replaceChildren();

    let delay = 0;
    for (const [line, def] of Object.entries(MAP.lines)) {
      const d = roundedPath(MAP.routes[line].map(pt));
      const path = s('path', {
        d, class: 'line-path', stroke: def.color,
        'stroke-width': def.dashed ? 4 : 6,
        'stroke-dasharray': def.dashed ? '8 6' : null
      });
      linesLayer.append(path);
      lineEls[line] = path;

      if (!reduceMotion) {
        const g = s('path', { d, class: 'glint', 'stroke-width': def.dashed ? 2 : 3 });
        glintLayer.append(g);
        const len = path.getTotalLength();
        g.style.strokeDasharray = `40 ${Math.ceil(len) + 40}`;
        g.style.setProperty('--len', `${Math.ceil(len) + 40}`);
        g.style.animationDelay = `${delay}s`;
        delay += 1.3;
        glintEls[line] = g;
      }
    }

    // Обычные станции рисуем раньше пересадок, чтобы узлы были сверху.
    const ordered = stationIds.slice().sort((a, b) => Number(!!MAP.stations[a].interchange) - Number(!!MAP.stations[b].interchange));
    for (const id of ordered) stationsLayer.append(renderStation(id));
  }

  function renderStation(id) {
    const st = MAP.stations[id];
    const lines = stationLines[id];
    const n = countOf(id);
    const lineNames = lines.map((l) => MAP.lines[l].short).join(', ');
    const g = s('g', {
      class: 'station', tabindex: '0', role: 'button', 'data-id': id,
      'aria-label': `${plainName(id)}: ${materials(n)}. ${st.interchange ? 'Пересадка' : 'Линия'}: ${lineNames}`
    });
    g.append(s('circle', { class: 'hit', cx: st.x, cy: st.y, r: 22 }));

    if (st.interchange) {
      const ring = s('g', { class: 'interchange-ring' });
      ring.append(s('circle', { cx: st.x, cy: st.y, r: 12, fill: '#080C14', stroke: '#FFFFFF', 'stroke-width': 3 }));
      const colors = lines.map((l) => MAP.lines[l].color);
      const radii = colors.length >= 3 ? [7.5, 5, 2.5] : [5, 2.5];
      colors.slice(0, radii.length).forEach((c, i) => {
        ring.append(s('circle', { cx: st.x, cy: st.y, r: radii[i], fill: c, stroke: i ? '#080C14' : null, 'stroke-width': i ? 1 : null }));
      });
      g.append(ring);
      g.append(s('circle', { class: 'focus-ring', cx: st.x, cy: st.y, r: 16 }));
    } else {
      const color = MAP.lines[lines[0]].color;
      g.append(s('circle', { cx: st.x, cy: st.y, r: 5, fill: '#080C14', stroke: color, 'stroke-width': 3 }));
      g.append(s('circle', { class: 'focus-ring', cx: st.x, cy: st.y, r: 10 }));
    }

    g.append(renderLabel(st, n));
    stationEls[id] = g;
    return g;
  }

  function renderLabel(st, n) {
    const rows = st.name.split('\n');
    const lh = st.interchange ? 13 : 11.5;
    const off = st.interchange ? 17 : 10;
    const pos = st.label || 'r';
    let x = st.x, y = st.y, anchor = 'start';
    if (pos.includes('r')) { x += off; anchor = 'start'; }
    if (pos.includes('l')) { x -= off; anchor = 'end'; }
    if (pos === 't' || pos === 'b') anchor = 'middle';
    let top;
    if (pos.includes('t')) top = y - off - (rows.length - 1) * lh - 2;
    else if (pos.includes('b')) top = y + off + lh - 2;
    else top = y + 3.5 - ((rows.length - 1) * lh) / 2;
    const text = s('text', { class: `st-label${st.interchange ? ' x' : ''}`, x, y: top, 'text-anchor': anchor, 'aria-hidden': 'true' });
    rows.forEach((row, i) => {
      const t = s('tspan', { x, dy: i === 0 ? 0 : lh });
      t.textContent = row;
      text.append(t);
    });
    const c = s('tspan', { class: 'st-count', dx: 4 });
    c.textContent = String(n);
    text.append(c);
    return text;
  }

  // ---------- Highlight ----------
  const state = {
    filter: null,
    focus: null,
    route: null,
    routeFrom: MAP.routePreset.from,
    routeTo: MAP.routePreset.to,
    view: { x: 0, y: 0, k: 1 },
    fit: { x: 0, y: 0, k: 1 },
    sheet: { mode: null, level: 'closed', id: null }
  };

  function applyHighlight() {
    let activeLines, activeStations = null;
    if (state.route) {
      activeLines = new Set();
      activeStations = new Set(state.route.map((r) => r.id));
    } else if (state.focus) {
      activeLines = new Set(stationLines[state.focus]);
    } else if (state.filter) {
      activeLines = new Set([state.filter]);
    } else {
      activeLines = new Set(Object.keys(MAP.lines));
    }
    for (const [line, el] of Object.entries(lineEls)) {
      const on = activeLines.has(line);
      el.classList.toggle('dim', !on);
      if (glintEls[line]) glintEls[line].style.display = on ? '' : 'none';
    }
    for (const id of stationIds) {
      const on = activeStations ? activeStations.has(id) : stationLines[id].some((l) => activeLines.has(l));
      stationEls[id].classList.toggle('dim', !on);
      stationEls[id].setAttribute('aria-pressed', String(state.focus === id));
    }
    stationsLayer.querySelectorAll('.ping').forEach((p) => p.remove());
    if (state.focus && !reduceMotion) {
      const st = MAP.stations[state.focus];
      const ring = s('circle', { class: 'ping', cx: st.x, cy: st.y, r: st.interchange ? 12 : 7 });
      stationEls[state.focus].prepend(ring);
    }
    renderRouteOverlay();
    renderChips();
  }

  function renderRouteOverlay() {
    routeLayer.replaceChildren();
    if (!state.route || state.route.length < 2) return;
    for (let i = 1; i < state.route.length; i++) {
      const a = state.route[i - 1].id, b = state.route[i].id, line = state.route[i].line;
      const pts = segmentPoints(line, a, b);
      routeLayer.append(s('path', {
        d: roundedPath(pts), class: 'line-path', stroke: MAP.lines[line].color,
        'stroke-width': MAP.lines[line].dashed ? 4 : 6,
        'stroke-dasharray': MAP.lines[line].dashed ? '8 6' : null
      }));
      routeLayer.append(s('path', { d: roundedPath(pts), class: 'route-path' }));
    }
  }

  // ---------- Chips ----------
  const chips = $('chips');
  function renderChips() {
    chips.replaceChildren();
    const all = h('button', { class: 'chip', type: 'button', 'aria-pressed': String(!state.filter), onclick: () => setFilter(null) }, 'Все');
    chips.append(all);
    for (const [line, def] of Object.entries(MAP.lines)) {
      const dot = h('span', { class: 'dot' });
      dot.style.background = def.color;
      chips.append(h('button', {
        class: 'chip', type: 'button', 'aria-pressed': String(state.filter === line),
        'aria-label': `${def.full}: ${materials(lineCount(line))}`,
        onclick: () => setFilter(state.filter === line ? null : line)
      }, dot, def.short));
    }
    chips.classList.toggle('overflow', chips.scrollWidth > chips.clientWidth + 1);
  }
  function setFilter(line) {
    haptic('select');
    state.filter = line;
    state.focus = null;
    state.route = null;
    $('routeBtn').setAttribute('aria-pressed', 'false');
    if (state.sheet.mode === 'node' || state.sheet.mode === 'route') closeSheet(false);
    applyHighlight();
  }

  // ---------- View transform ----------
  let contentBox = null;

  function applyView(animate) {
    world.classList.toggle('no-anim', !animate || reduceMotion);
    const { x, y, k } = state.view;
    world.style.transform = `translate(${x}px, ${y}px) scale(${k})`;
  }

  function reservedBottom() {
    const tab = document.querySelector('.tabbar').getBoundingClientRect().height;
    const ctr = document.querySelector('.controls').getBoundingClientRect().height;
    return tab + ctr + 16;
  }

  function computeFit() {
    const W = viewport.clientWidth, H = viewport.clientHeight;
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    const pad = 24;
    const availH = Math.max(120, H - reservedBottom());
    const box = contentBox;
    const k = Math.min((W - pad * 2) / box.width, (availH - pad * 2) / box.height);
    const x = (W - box.width * k) / 2 - box.x * k;
    const y = pad + (availH - pad * 2 - box.height * k) / 2 - box.y * k;
    state.fit = { x, y, k };
  }

  function fitView(animate = true) {
    state.view = { ...state.fit };
    applyView(animate);
  }

  function clampView() {
    const W = viewport.clientWidth, H = viewport.clientHeight, b = contentBox, v = state.view;
    const margin = 80;
    const left = b.x * v.k + v.x, right = (b.x + b.width) * v.k + v.x;
    const top = b.y * v.k + v.y, bottom = (b.y + b.height) * v.k + v.y;
    if (right < margin) v.x += margin - right;
    if (left > W - margin) v.x -= left - (W - margin);
    if (bottom < margin) v.y += margin - bottom;
    if (top > H - margin) v.y -= top - (H - margin);
  }

  function zoomAt(px, py, factor) {
    const v = state.view, base = state.fit.k;
    const k = Math.min(base * ZOOM_MAX, Math.max(base * ZOOM_MIN, v.k * factor));
    const f = k / v.k;
    v.x = px - (px - v.x) * f;
    v.y = py - (py - v.y) * f;
    v.k = k;
    clampView();
    applyView(false);
  }

  function visibleMapHeight() {
    const H = viewport.clientHeight;
    if (state.sheet.level === 'closed') return H - reservedBottom();
    return Math.max(140, H - sheetOffsetFromBottom());
  }

  function centerOn(x, y, kRel) {
    const W = viewport.clientWidth;
    const k = state.fit.k * kRel;
    const vh = visibleMapHeight();
    state.view = { x: W / 2 - x * k, y: vh / 2 - y * k, k };
    applyView(true);
  }

  // Вписывает станции вместе с подписями: берём рамки их SVG-групп (в координатах схемы).
  function fitToStations(ids) {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const id of ids) {
      const g = stationsLayer.querySelector(`[data-id="${id}"]`);
      const b = g ? g.getBBox() : { x: MAP.stations[id].x, y: MAP.stations[id].y, width: 0, height: 0 };
      minX = Math.min(minX, b.x); minY = Math.min(minY, b.y);
      maxX = Math.max(maxX, b.x + b.width); maxY = Math.max(maxY, b.y + b.height);
    }
    const pad = 24 / state.fit.k;
    minX -= pad; minY -= pad; maxX += pad; maxY += pad;
    const W = viewport.clientWidth, vh = visibleMapHeight();
    const base = state.fit.k;
    const k = Math.min(base * 1.4, Math.max(base * ZOOM_MIN, Math.min(W / (maxX - minX), vh / (maxY - minY))));
    state.view = { x: W / 2 - ((minX + maxX) / 2) * k, y: vh / 2 - ((minY + maxY) / 2) * k, k };
    applyView(true);
  }

  // ---------- Gestures ----------
  const pointers = new Map();
  let gesture = null;
  let lastTap = { t: 0, x: 0, y: 0 };

  function localPoint(e) {
    const r = viewport.getBoundingClientRect();
    return { x: e.clientX - r.left, y: e.clientY - r.top };
  }

  viewport.addEventListener('pointerdown', (e) => {
    if (e.target.closest('.controls, .state')) return;
    viewport.setPointerCapture(e.pointerId);
    pointers.set(e.pointerId, localPoint(e));
    if (pointers.size === 1) {
      const p = localPoint(e);
      gesture = { type: 'pan', start: p, last: p, moved: false, station: e.target.closest('.station') };
    } else if (pointers.size === 2) {
      const [a, b] = [...pointers.values()];
      gesture = { type: 'pinch', dist: Math.hypot(a.x - b.x, a.y - b.y), moved: true };
    }
  });

  viewport.addEventListener('pointermove', (e) => {
    if (!pointers.has(e.pointerId) || !gesture) return;
    const p = localPoint(e);
    pointers.set(e.pointerId, p);
    if (gesture.type === 'pan' && pointers.size === 1) {
      const dx = p.x - gesture.last.x, dy = p.y - gesture.last.y;
      if (!gesture.moved && Math.hypot(p.x - gesture.start.x, p.y - gesture.start.y) < 6) return;
      gesture.moved = true;
      viewport.classList.add('dragging');
      state.view.x += dx;
      state.view.y += dy;
      gesture.last = p;
      clampView();
      applyView(false);
    } else if (gesture.type === 'pinch' && pointers.size === 2) {
      const [a, b] = [...pointers.values()];
      const dist = Math.hypot(a.x - b.x, a.y - b.y);
      if (gesture.dist > 0) zoomAt((a.x + b.x) / 2, (a.y + b.y) / 2, dist / gesture.dist);
      gesture.dist = dist;
    }
  });

  function endPointer(e) {
    if (!pointers.has(e.pointerId)) return;
    pointers.delete(e.pointerId);
    viewport.classList.remove('dragging');
    if (!gesture) return;
    if (gesture.type === 'pan' && !gesture.moved && e.type === 'pointerup') {
      if (gesture.station) {
        selectStation(gesture.station.dataset.id);
      } else {
        const p = localPoint(e), now = Date.now();
        if (now - lastTap.t < 320 && Math.hypot(p.x - lastTap.x, p.y - lastTap.y) < 30) {
          fitView(true);
          lastTap.t = 0;
        } else {
          lastTap = { t: now, x: p.x, y: p.y };
        }
      }
    }
    if (pointers.size === 1) {
      const p = [...pointers.values()][0];
      gesture = { type: 'pan', start: p, last: p, moved: true, station: null };
    } else if (pointers.size === 0) {
      gesture = null;
    }
  }
  viewport.addEventListener('pointerup', endPointer);
  viewport.addEventListener('pointercancel', endPointer);

  viewport.addEventListener('wheel', (e) => {
    e.preventDefault();
    const p = localPoint(e);
    zoomAt(p.x, p.y, Math.exp(-e.deltaY * 0.0015));
  }, { passive: false });

  stationsLayer.addEventListener('keydown', (e) => {
    const g = e.target.closest('.station');
    if (!g) return;
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectStation(g.dataset.id); }
  });

  // ---------- Selection ----------
  function selectStation(id) {
    const st = MAP.stations[id];
    haptic(st.interchange ? 'medium' : 'light');
    if (state.route) {
      state.route = null;
      $('routeBtn').setAttribute('aria-pressed', 'false');
    }
    state.focus = id;
    applyHighlight();
    openSheet('node', id, 'half');
    centerOn(st.x, st.y, ZOOM_FOCUS);
  }

  // ---------- Sheet ----------
  function sheetHeights() {
    const appH = app.clientHeight;
    const sheetH = sheet.getBoundingClientRect().height || appH * 0.85;
    return { appH, sheetH, half: sheetH - appH * SHEET_HALF, full: 0, closed: sheetH };
  }
  function sheetOffsetFromBottom() {
    const { appH } = sheetHeights();
    const viewportBottomGap = app.getBoundingClientRect().bottom - viewport.getBoundingClientRect().bottom;
    const covered = state.sheet.level === 'full' ? appH * 0.85 : appH * SHEET_HALF;
    return covered - viewportBottomGap;
  }
  function placeSheet(level, animate = true) {
    const hts = sheetHeights();
    sheet.classList.toggle('no-anim', !animate || reduceMotion);
    sheet.style.transform = `translateY(${hts[level]}px)`;
  }

  function setSheetLevel(level) {
    state.sheet.level = level;
    placeSheet(level);
    const open = level !== 'closed';
    sheet.setAttribute('aria-hidden', String(!open));
    sheet.toggleAttribute('inert', !open);
    try { if (tg && tg.BackButton) open ? tg.BackButton.show() : tg.BackButton.hide(); } catch (_) {}
    if (open) renderSheet();
  }

  function openSheet(mode, id, level) {
    state.sheet.mode = mode;
    state.sheet.id = id;
    sheetBody.scrollTop = 0;
    setSheetLevel(level);
  }

  function closeSheet(refit = true) {
    const wasNode = state.sheet.mode === 'node';
    const wasRoute = state.sheet.mode === 'route';
    state.sheet.mode = null;
    setSheetLevel('closed');
    if (wasNode) { state.focus = null; applyHighlight(); }
    if (wasRoute) {
      state.route = null;
      $('routeBtn').setAttribute('aria-pressed', 'false');
      applyHighlight();
    }
    if (refit && (wasNode || wasRoute)) fitView(true);
  }

  $('closeBtn').addEventListener('click', () => closeSheet());
  $('handleBtn').addEventListener('click', () => {
    if (handleDragged) return;
    setSheetLevel(state.sheet.level === 'full' ? 'half' : 'full');
  });

  // Перетаскивание шторки за верхнюю часть.
  let sheetDrag = null;
  let handleDragged = false;
  const grab = $('sheetGrab');
  grab.addEventListener('pointerdown', (e) => {
    if (e.target.closest('.close-btn')) return;
    handleDragged = false;
    const hts = sheetHeights();
    sheetDrag = { startY: e.clientY, base: hts[state.sheet.level], last: e.clientY, t: performance.now(), v: 0, pointerId: e.pointerId };
  });
  grab.addEventListener('pointermove', (e) => {
    if (!sheetDrag || e.pointerId !== sheetDrag.pointerId) return;
    const dy = e.clientY - sheetDrag.startY;
    if (!handleDragged && Math.abs(dy) <= 4) return;
    if (!handleDragged) {
      handleDragged = true;
      grab.setPointerCapture(e.pointerId);
      sheet.classList.add('no-anim');
    }
    const now = performance.now();
    sheetDrag.v = (e.clientY - sheetDrag.last) / Math.max(1, now - sheetDrag.t);
    sheetDrag.last = e.clientY; sheetDrag.t = now;
    const hts = sheetHeights();
    const y = Math.min(hts.closed, Math.max(0, sheetDrag.base + dy));
    sheet.style.transform = `translateY(${y}px)`;
  });
  function endSheetDrag(e) {
    if (!sheetDrag || e.pointerId !== sheetDrag.pointerId) return;
    const hts = sheetHeights();
    const y = Math.min(hts.closed, Math.max(0, sheetDrag.base + (e.clientY - sheetDrag.startY)));
    const v = sheetDrag.v;
    sheetDrag = null;
    if (!handleDragged) return;
    let target;
    if (v < -0.5) target = y > hts.half ? 'half' : 'full';
    else if (v > 0.5) target = y < hts.half ? 'half' : 'closed';
    else {
      const opts = [['full', 0], ['half', hts.half], ['closed', hts.closed]];
      target = opts.reduce((best, o) => (Math.abs(o[1] - y) < Math.abs(best[1] - y) ? o : best))[0];
    }
    if (target === 'closed') closeSheet();
    else if (target !== state.sheet.level) setSheetLevel(target);
    else placeSheet(target);
    setTimeout(() => { handleDragged = false; }, 0);
  }
  grab.addEventListener('pointerup', endSheetDrag);
  grab.addEventListener('pointercancel', endSheetDrag);

  function setBadges(lines, label) {
    const box = $('sheetBadges');
    box.replaceChildren();
    box.hidden = !lines.length;
    if (!lines.length) return;
    const b = h('span', { class: 'badge' });
    lines.forEach((l, i) => {
      const dot = h('span', { class: 'dot' });
      dot.style.background = MAP.lines[l].color;
      b.append(dot);
      const t = h('span', { text: MAP.lines[l].short });
      t.style.color = MAP.lines[l].color;
      b.append(t);
      if (i < lines.length - 1) b.append(h('span', { text: '+', 'aria-hidden': 'true' }));
    });
    box.append(b);
  }

  function renderSheet() {
    const { mode, id, level } = state.sheet;
    if (mode === 'node') renderNodeSheet(id, level);
    else if (mode === 'route') renderRouteSheet();
    else if (mode === 'fav') renderFavSheet();
  }

  function compactCard(post) {
    const steps = realSteps(post).length;
    return h('button', {
      class: 'compact', type: 'button',
      onclick: () => {
        setSheetLevel('full');
        requestAnimationFrame(() => {
          const el = document.getElementById(`post-${post.id}`);
          if (el) el.scrollIntoView({ block: 'start', behavior: reduceMotion ? 'auto' : 'smooth' });
        });
      }
    },
    h('span', { class: 'compact-title', text: post.card_title }),
    h('span', { class: 'compact-meta' },
      h('span', { text: `@${post.author_username}` }),
      steps ? h('span', { class: 'steps-flag', text: `${steps} ${plural(steps, 'шаг', 'шага', 'шагов')}` }) : h('span', { text: fmtDate(post.date) })
    ));
  }

  function fullCard(post) {
    const favs = readFavs();
    const saved = favs.includes(post.id);
    const steps = cleanSteps(realSteps(post)).slice(0, 7);
    const saveBtn = h('button', {
      class: 'save-btn', type: 'button', 'aria-pressed': String(saved),
      'aria-label': saved ? 'Убрать из избранного' : 'Сохранить в избранное'
    }, icon(ICON_BOOKMARK, 18, saved ? 'currentColor' : 'none'));
    saveBtn.addEventListener('click', () => {
      const list = readFavs();
      const i = list.indexOf(post.id);
      if (i >= 0) list.splice(i, 1); else list.push(post.id);
      writeFavs(list);
      haptic('light');
      const now = i < 0;
      saveBtn.setAttribute('aria-pressed', String(now));
      saveBtn.setAttribute('aria-label', now ? 'Убрать из избранного' : 'Сохранить в избранное');
      saveBtn.replaceChildren(icon(ICON_BOOKMARK, 18, now ? 'currentColor' : 'none'));
    });
    const tools = (post.tools || []).slice(0, 5);
    return h('li', { class: 'card', id: `post-${post.id}` },
      h('h3', { class: 'card-title', text: post.card_title }),
      h('div', { class: 'card-meta', text: [`@${post.author_username}`, fmtDate(post.date)].filter(Boolean).join(' · ') }),
      tools.length ? h('div', { class: 'tool-badges' }, tools.map((t) => h('span', { class: 'tool', text: t }))) : null,
      steps.length
        ? h('ol', { class: 'steps-list', 'aria-label': 'Шаги' }, steps.map((st) => h('li', { text: st })))
        : h('p', { class: 'no-steps', text: 'Пошаговый разбор ещё не сделан. Суть в оригинале.' }),
      h('div', { class: 'card-actions' },
        h('a', {
          class: 'open-link', href: post.url, target: '_blank', rel: 'noopener',
          onclick: (e) => { if (tg && tg.openLink) { e.preventDefault(); openExternal(post.url); } }
        }, 'Открыть оригинал', icon(ICON_EXTERNAL, 14)),
        saveBtn
      ));
  }

  function renderNodeSheet(id, level) {
    const st = MAP.stations[id];
    const list = postsByStation[id] || [];
    setBadges(stationLines[id]);
    $('sheetTitle').textContent = plainName(id);
    const body = [];
    if (st.about) body.push(h('p', { class: 'about', text: st.about }));
    else body.push(h('p', { class: 'about', text: `Станция линии «${MAP.lines[stationLines[id][0]].full}». Разделы: ${st.subs.join('; ').replace(/ & /g, ' и ')}.` }));
    const withSteps = list.filter((p) => realSteps(p).length > 0).length;
    body.push(h('p', { class: 'count-line' },
      `${st.interchange ? 'В узле' : 'На станции'} `, h('strong', { text: materials(list.length) }),
      withSteps ? `, с пошаговым разбором: ${withSteps}` : ''));

    if (level === 'half') {
      if (!list.length) {
        body.push(h('p', { class: 'no-steps', text: 'Здесь пока нет материалов.' }));
      } else {
        body.push(h('div', { class: 'peek-row', role: 'list' }, list.slice(0, 8).map((p) => h('div', { role: 'listitem' }, compactCard(p)))));
        body.push(h('button', { class: 'expand-hint', type: 'button', onclick: () => setSheetLevel('full') }, `Показать все ${list.length}`));
      }
    } else {
      const ids = list.map((p) => p.id);
      const favs = readFavs();
      const allSaved = ids.length > 0 && ids.every((x) => favs.includes(x));
      const favAll = h('button', { class: 'fav-all', type: 'button', 'data-done': String(allSaved) },
        icon(ICON_BOOKMARK, 18, allSaved ? 'currentColor' : 'none'),
        allSaved ? 'Вся связка в избранном' : `Добавить всю ${st.interchange ? 'связку' : 'станцию'} в избранное`);
      favAll.addEventListener('click', () => {
        const cur = readFavs();
        for (const x of ids) if (!cur.includes(x)) cur.push(x);
        writeFavs(cur);
        haptic('medium');
        toast(`Сохранено: ${materials(ids.length)}`);
        renderSheet();
      });
      if (ids.length) body.push(favAll);
      body.push(h('ul', { class: 'card-list' }, list.map(fullCard)));
    }
    sheetBody.replaceChildren(...body);
  }

  // ---------- Route planner ----------
  function stationSelect(idAttr, value, label) {
    const sel = h('select', { id: idAttr });
    for (const [line, def] of Object.entries(MAP.lines)) {
      const group = h('optgroup', { label: def.full });
      for (const p of MAP.routes[line]) {
        if (typeof p !== 'string' || MAP.stations[p].interchange) continue;
        group.append(h('option', { value: p, selected: p === value }, plainName(p)));
      }
      sel.append(group);
    }
    const xg = h('optgroup', { label: 'Пересадки' });
    for (const id of stationIds) if (MAP.stations[id].interchange) xg.append(h('option', { value: id, selected: id === value }, plainName(id)));
    sel.append(xg);
    return h('label', {}, label, sel);
  }

  function computeRoute() {
    state.route = findRoute(state.routeFrom, state.routeTo);
    applyHighlight();
    if (state.route) fitToStations(state.route.map((r) => r.id));
  }

  function renderRouteSheet() {
    setBadges([]);
    $('sheetTitle').textContent = 'Проложить маршрут';
    const fromL = stationSelect('routeFrom', state.routeFrom, 'У меня есть');
    const toL = stationSelect('routeTo', state.routeTo, 'Хочу прийти к');
    const onChange = () => {
      state.routeFrom = $('routeFrom').value;
      state.routeTo = $('routeTo').value;
      haptic('select');
      computeRoute();
      renderRouteSheet();
    };
    fromL.querySelector('select').addEventListener('change', onChange);
    toL.querySelector('select').addEventListener('change', onChange);
    const swap = h('button', { class: 'swap-btn', type: 'button', onclick: () => {
      [state.routeFrom, state.routeTo] = [state.routeTo, state.routeFrom];
      haptic('light');
      computeRoute();
      renderRouteSheet();
    }, 'aria-label': 'Поменять местами' }, icon(ICON_SWAP, 18));

    const body = [h('div', { class: 'route-form' }, fromL, swap, toL)];
    const route = state.route;
    if (!route) {
      body.push(h('p', { class: 'no-steps', text: 'Между этими станциями нет пути.' }));
    } else if (route.length === 1) {
      body.push(h('p', { class: 'no-steps', text: 'Вы уже на месте: выберите другую конечную станцию.' }));
    } else {
      const changes = route.filter((r, i) => i > 1 && r.line !== route[i - 1].line).length;
      body.push(h('p', { class: 'count-line' },
        h('strong', { text: `${route.length} ${plural(route.length, 'урок', 'урока', 'уроков')}` }),
        changes ? `, ${changes} ${plural(changes, 'пересадка', 'пересадки', 'пересадок')}` : ', без пересадок'));
      const steps = route.map((r, i) => {
        const color = MAP.lines[r.line].color;
        const dot = h('span', { class: 'route-dot' });
        dot.style.borderColor = color;
        const next = route[i + 1];
        let note = MAP.lines[r.line].full;
        if (next && next.line !== r.line && MAP.stations[r.id].interchange) note = `Пересадка: ${MAP.lines[r.line].short} → ${MAP.lines[next.line].short}`;
        const lesson = (postsByStation[r.id] || [])[0];
        return h('li', { class: 'route-step' }, dot, h('div', {},
          h('div', { class: 'route-step-name', text: plainName(r.id) }),
          h('div', { class: 'route-step-note', text: `${note} · ${materials(countOf(r.id))}` }),
          lesson ? h('a', {
            class: 'route-lesson', href: lesson.url, target: '_blank', rel: 'noopener',
            onclick: (e) => { if (tg && tg.openLink) { e.preventDefault(); openExternal(lesson.url); } }
          }, lesson.card_title) : null));
      });
      body.push(h('ol', { class: 'route-steps' }, steps));
    }
    sheetBody.replaceChildren(...body);
  }

  $('routeBtn').addEventListener('click', () => {
    const on = state.sheet.mode !== 'route';
    $('routeBtn').setAttribute('aria-pressed', String(on));
    haptic('light');
    if (!on) { closeSheet(); return; }
    state.focus = null;
    state.filter = null;
    openSheet('route', null, 'half');
    computeRoute();
    renderRouteSheet();
  });

  // ---------- Favorites tab ----------
  function renderFavSheet() {
    setBadges([]);
    $('sheetTitle').textContent = 'Сохранённые материалы';
    const favs = readFavs();
    const list = posts.filter((p) => favs.includes(p.id));
    if (!list.length) {
      sheetBody.replaceChildren(h('p', { class: 'no-steps', text: 'Пока пусто. Сохраняйте материалы кнопкой с закладкой на карточке или целой связкой.' }));
      return;
    }
    sheetBody.replaceChildren(h('p', { class: 'count-line' }, h('strong', { text: materials(list.length) })), h('ul', { class: 'card-list' }, sortPosts(list).map(fullCard)));
  }
  $('favTab').addEventListener('click', () => {
    haptic('light');
    if (state.focus || state.route) {
      state.focus = null; state.route = null;
      $('routeBtn').setAttribute('aria-pressed', 'false');
      applyHighlight();
    }
    openSheet('fav', null, 'full');
  });

  // ---------- Search ----------
  const searchBox = $('search');
  const searchInput = $('searchInput');
  const searchResults = $('searchResults');
  $('searchBtn').addEventListener('click', () => {
    const open = searchBox.hidden;
    searchBox.hidden = !open;
    $('searchBtn').setAttribute('aria-pressed', String(open));
    if (open) { searchInput.value = ''; renderSearch(''); searchInput.focus(); }
  });
  searchInput.addEventListener('input', () => renderSearch(searchInput.value));
  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { searchBox.hidden = true; $('searchBtn').setAttribute('aria-pressed', 'false'); $('searchBtn').focus(); }
  });

  function renderSearch(q) {
    const query = q.trim().toLowerCase();
    searchResults.replaceChildren();
    if (!query) {
      searchResults.append(h('li', { class: 'search-empty', text: 'Например: Ozon, n8n, Reels, VPN, налоги' }));
      return;
    }
    const scored = [];
    for (const id of stationIds) {
      const st = MAP.stations[id];
      const nameHit = plainName(id).toLowerCase().includes(query) || st.subs.some((x) => x.toLowerCase().includes(query));
      const hits = (postsByStation[id] || []).filter((p) =>
        (p.card_title || '').toLowerCase().includes(query) || (p.tools || []).some((t) => t.toLowerCase().includes(query))).length;
      if (nameHit || hits) scored.push({ id, score: (nameHit ? 1000 : 0) + hits, hits });
    }
    scored.sort((a, b) => b.score - a.score);
    if (!scored.length) {
      searchResults.append(h('li', { class: 'search-empty', text: 'Ничего не нашлось. Попробуйте название инструмента или темы.' }));
      return;
    }
    for (const r of scored.slice(0, 7)) {
      const dots = h('span', { 'aria-hidden': 'true', style: 'display:flex;gap:3px' }, stationLines[r.id].map((l) =>
        h('span', { style: `width:8px;height:8px;border-radius:50%;background:${MAP.lines[l].color}` })));
      searchResults.append(h('li', {}, h('button', { type: 'button', onclick: () => {
        searchBox.hidden = true;
        $('searchBtn').setAttribute('aria-pressed', 'false');
        selectStation(r.id);
      } }, dots, h('span', { class: 'res-name', text: plainName(r.id) }),
      h('span', { class: 'res-meta', text: r.hits ? `совпадений: ${r.hits}` : materials(countOf(r.id)) }))));
    }
  }

  // ---------- Toast ----------
  let toastTimer = 0;
  function toast(msg) {
    const el = $('toast');
    el.textContent = msg;
    el.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove('show'), 1800);
  }

  // ---------- Boot ----------
  $('fitBtn').addEventListener('click', () => { haptic('light'); fitView(true); });

  let resizeRaf = 0;
  window.addEventListener('resize', () => {
    cancelAnimationFrame(resizeRaf);
    resizeRaf = requestAnimationFrame(() => {
      if (!contentBox) return;
      computeFit();
      if (state.sheet.level !== 'closed') placeSheet(state.sheet.level, false);
      if (state.focus) { const st = MAP.stations[state.focus]; centerOn(st.x, st.y, ZOOM_FOCUS); }
      else if (state.route) fitToStations(state.route.map((r) => r.id));
      else fitView(false);
    });
  });

  async function load() {
    $('errorState').hidden = true;
    $('loadState').hidden = false;
    try {
      const res = await fetch('posts.json', { cache: 'no-cache' });
      if (!res.ok) throw new Error(String(res.status));
      indexPosts(await res.json());
    } catch (err) {
      $('loadState').hidden = true;
      $('errorState').hidden = false;
      $('totalMeta').textContent = 'Нет связи с базой';
      return;
    }
    $('loadState').hidden = true;
    $('totalMeta').textContent = `${materials(posts.length)}`;
    renderMap();
    applyHighlight(); // рисует чипсы: их высота нужна для расчёта вписывания
    contentBox = world.getBBox();
    computeFit();
    fitView(false);
    placeSheet('closed', false);
  }
  $('retryBtn').addEventListener('click', load);
  load();
})();
