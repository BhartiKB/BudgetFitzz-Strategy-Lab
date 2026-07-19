const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const state = {
  manifest: null,
  route: 'home',
  selectedDay: 1,
  planFormat: 'all',
  studioFormat: 'all',
};

const icons = {
  home: '<path d="M3 11.5 12 4l9 7.5v8a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
  chart: '<path d="M4 20V10m6 10V4m6 16v-7m4 7H2"/>',
  search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/>',
  strategy: '<path d="M4 19V5m0 3h9l-2.5 3L13 14H4m9 5 3-3 4 4"/>',
  calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M8 3v4m8-4v4M3 10h18M8 14h3m3 0h3m-9 3h3"/>',
  studio: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="m4 18 5-5 3 3 3-4 5 6"/>',
  agents: '<circle cx="9" cy="8" r="3"/><circle cx="17" cy="10" r="2.5"/><path d="M3 20c.5-4 2.5-6 6-6s5.5 2 6 6m0-5c3 0 5 1.5 5.5 5"/>',
  architecture: '<rect x="3" y="4" width="5" height="5" rx="1"/><rect x="16" y="4" width="5" height="5" rx="1"/><rect x="9.5" y="15" width="5" height="5" rx="1"/><path d="M8 6.5h8M12 9v6"/>',
  check: '<circle cx="12" cy="12" r="9"/><path d="m8 12 2.5 2.5L16 9"/>',
  send: '<path d="m3 4 18 8-18 8 3-8zm3 8h15"/>',
  more: '<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>',
  arrow: '<path d="M5 12h14m-5-5 5 5-5 5"/>',
  play: '<path d="m9 7 8 5-8 5z"/>',
  file: '<path d="M6 3h8l4 4v14H6zM14 3v5h5M9 13h6m-6 4h6"/>',
};

function icon(name, className = '') {
  return `<svg class="icon ${className}" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${icons[name] || icons.strategy}</svg>`;
}

function el(tag, className = '', text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function append(parent, tag, className, text) {
  const node = el(tag, className, text);
  parent.append(node);
  return node;
}

function formatBytes(bytes) {
  if (!bytes) return 'Not generated';
  const units = ['B', 'KB', 'MB', 'GB'];
  let value = bytes;
  let index = 0;
  while (value >= 1024 && index < units.length - 1) { value /= 1024; index += 1; }
  return `${value.toFixed(index ? 1 : 0)} ${units[index]}`;
}

function formatDate(value, options = { weekday: 'short', month: 'short', day: 'numeric' }) {
  const parsed = new Date(`${value}T00:00:00`);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleDateString('en-IN', options);
}

function valueKind(kind, text = kind) {
  return `<span class="value-kind value-kind--${kind}">${text}</span>`;
}

function routeHeader({ eyebrow, title, summary, aside = '' }) {
  const header = el('header', 'route-header');
  const copy = el('div', 'route-header__copy');
  append(copy, 'span', 'overline', eyebrow);
  const heading = append(copy, 'h1', '', title);
  heading.id = 'route-title';
  if (summary) append(copy, 'p', 'route-summary', summary);
  header.append(copy);
  if (aside) { const meta = el('div', 'route-header__aside'); meta.innerHTML = aside; header.append(meta); }
  return header;
}

function sourceNote(text, sampleSize) {
  const note = el('small', 'source-note');
  note.textContent = sampleSize === undefined ? text : `${text} · n=${sampleSize}`;
  return note;
}

function emptyState(title, detail) {
  const box = el('div', 'empty-state');
  append(box, 'strong', '', title);
  append(box, 'p', '', detail);
  return box;
}

async function loadManifest() {
  const response = await fetch('data/platform_manifest.json', { cache: 'no-store' });
  if (!response.ok) throw new Error(`Manifest request failed (${response.status}).`);
  const manifest = await response.json();
  const required = ['navigation', 'overview', 'performance', 'strategy', 'content_studio', 'workflow', 'architecture', 'validation'];
  const missing = required.filter((key) => !manifest[key]);
  if (missing.length) throw new Error(`Generated manifest is missing: ${missing.join(', ')}.`);
  return manifest;
}

function renderChrome(manifest) {
  const makeLink = (item, mobile = false) => {
    const link = el('a', mobile ? 'mobile-nav__link' : 'route-link');
    link.href = `#${item.id}`;
    link.dataset.route = item.id;
    link.innerHTML = `${icon(item.icon || item.id)}<span>${item.label}</span>`;
    return link;
  };

  manifest.navigation.forEach((item) => {
    $('#desktop-nav').append(makeLink(item));
    $('#sheet-nav').append(makeLink(item));
  });

  const primaryMobile = ['home', 'insights', 'content-plan', 'studio'];
  manifest.navigation.filter((item) => primaryMobile.includes(item.id)).forEach((item) => $('#mobile-nav').append(makeLink(item, true)));
  const more = el('button', 'mobile-nav__link');
  more.type = 'button';
  more.innerHTML = `${icon('more')}<span>More</span>`;
  more.addEventListener('click', () => $('#route-sheet').showModal());
  $('#mobile-nav').append(more);

  const validation = manifest.validation;
  const spend = manifest.operations?.spend?.paid_generation_total_inr ?? 0;
  $('#topbar-status').innerHTML = `${valueKind(validation.status === 'PASS' ? 'validated' : 'error', `${validation.status === 'PASS' ? '✓' : '!'} Validation ${validation.status}`)}${valueKind('neutral', `₹${Number(spend).toFixed(0)} paid spend`)}`;
  $('#rail-status').innerHTML = `<span class="status-dot" aria-hidden="true"></span><div><strong>${validation.passed}/${validation.passed + validation.failed} checks passed</strong><small>Run ${manifest.run.run_id}</small></div>`;

  $$('[data-close-dialog]').forEach((button) => button.addEventListener('click', () => $(`#${button.dataset.closeDialog}`).close()));
  $$('dialog').forEach((dialog) => dialog.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); }));
  $('#sheet-nav').addEventListener('click', () => $('#route-sheet').close());
}

function signalCard(item, index) {
  const card = el('article', `signal-card signal-card--${index + 1}`);
  card.innerHTML = valueKind(index === 2 ? 'directional' : 'observed', index === 2 ? 'Derived comparison' : 'Observed');
  append(card, 'strong', 'signal-card__value', item.value);
  append(card, 'span', 'signal-card__label', item.label);
  append(card, 'p', '', item.detail);
  card.append(sourceNote(item.source, item.sample_size));
  return card;
}

function planMedia(item, compact = false) {
  const root = state.manifest.content_studio.asset_root;
  const wrap = el('div', `plan-media ${compact ? 'plan-media--compact' : ''} plan-media--${item.format}`);
  if (item.format === 'video') {
    const video = el('video');
    video.controls = !compact;
    video.muted = true;
    video.playsInline = true;
    video.preload = 'metadata';
    video.poster = `${root}/video_frames/${item.asset_filename.replace(/\.mp4$/, '')}_preview.png`;
    const source = el('source'); source.src = `${root}/videos/${item.asset_filename}`; source.type = 'video/mp4'; video.append(source);
    wrap.append(video);
    if (compact) { const badge = el('span', 'video-badge'); badge.innerHTML = `${icon('play')} Video`; wrap.append(badge); }
  } else {
    const image = el('img');
    image.src = `${root}/posts/${item.asset_filename}`;
    image.alt = `Day ${item.day} creative: ${item.hook}`;
    image.loading = 'lazy';
    wrap.append(image);
  }
  return wrap;
}

function contentCard(item, { interactive = false, compact = false } = {}) {
  const card = el(interactive ? 'button' : 'article', `content-card content-card--${item.format}`);
  if (interactive) { card.type = 'button'; card.dataset.day = item.day; card.setAttribute('aria-label', `Preview day ${item.day}: ${item.hook}`); }
  card.append(planMedia(item, compact));
  const copy = el('div', 'content-card__copy');
  copy.innerHTML = `${valueKind(item.format === 'video' ? 'directional' : 'neutral', `Day ${item.day} · ${item.format}`)}`;
  append(copy, 'h3', '', item.hook);
  append(copy, 'p', '', item.content_pillar);
  card.append(copy);
  return card;
}

function renderHome() {
  const manifest = state.manifest;
  const view = el('div', 'route route--home');
  const hero = el('section', 'home-hero');
  const copy = el('div', 'home-hero__copy');
  copy.innerHTML = `${valueKind('observed', 'Observed baseline')}<span class="issue-no">ISSUE 01 / STRATEGY INTELLIGENCE</span>`;
  append(copy, 'h1', '', 'Baseline: Overwhelmingly Promotional').id = 'route-title';
  append(copy, 'p', 'hero-deck', manifest.strategy.diagnosis.selected_diagnosis);
  const actions = el('div', 'button-row');
  const primary = el('a', 'button button--primary'); primary.href = '#strategy'; primary.innerHTML = `Review revised strategy ${icon('arrow')}`;
  const secondary = el('a', 'button button--secondary', 'Open seven-day plan'); secondary.href = '#content-plan';
  actions.append(primary, secondary); copy.append(actions);
  const note = el('aside', 'hero-note');
  append(note, 'span', 'overline', 'EDITORIAL POSITION');
  append(note, 'p', '', manifest.strategy.diagnosis.outlier_caveat);
  note.append(sourceNote(manifest.overview.lineage.analysis_source));
  hero.append(copy, note); view.append(hero);

  const signals = el('section', 'signal-grid');
  signals.setAttribute('aria-label', 'Observed strategy signals');
  manifest.overview.kpis.forEach((item, index) => signals.append(signalCard(item, index)));
  view.append(signals);

  const connection = el('section', 'connection-card');
  const connectionCopy = el('div');
  append(connectionCopy, 'span', 'overline', 'PLATFORM ARCHITECTURE');
  append(connectionCopy, 'h2', '', 'How the platform connects.');
  append(connectionCopy, 'p', '', 'The frontend is driven by outputs generated by the analytical and agent pipeline, not by manually copied dashboard values.');
  const connectionLink = el('a', 'button button--secondary');
  connectionLink.href = '#agents';
  connectionLink.innerHTML = `View the connection ${icon('arrow')}`;
  connection.append(connectionCopy, connectionLink);
  view.append(connection);

  const section = el('section', 'editorial-section');
  const head = el('div', 'section-head');
  head.innerHTML = '<div><span class="overline">THIS WEEK IN THE ATELIER</span><h2>Seven useful reasons to publish.</h2></div>';
  const all = el('a', 'text-link'); all.href = '#content-plan'; all.innerHTML = `View content plan ${icon('arrow')}`; head.append(all); section.append(head);
  const strip = el('div', 'home-plan-strip');
  manifest.content_studio.plan.forEach((item) => strip.append(contentCard(item, { compact: true })));
  section.append(strip); view.append(section);

  const provenance = el('aside', 'provenance-band');
  provenance.innerHTML = `<div><span class="overline">DATA LINEAGE</span><strong>${manifest.overview.lineage.observed_rows} observed rows · ${manifest.overview.audit.span_days} days</strong></div><p>${manifest.overview.lineage.after_note}</p>`;
  view.append(provenance);
  return view;
}

function metricCard(item) {
  const card = el('article', 'metric-card');
  card.innerHTML = valueKind('observed', 'Observed');
  append(card, 'strong', '', item.display);
  append(card, 'h3', '', item.metric);
  card.append(sourceNote(item.source, item.n));
  return card;
}

function summaryTable(title, rows, key) {
  const card = el('article', 'table-card');
  append(card, 'h2', '', title);
  const scroll = el('div', 'table-scroll');
  const table = el('table');
  table.innerHTML = '<thead><tr><th>Group</th><th>n</th><th>Median ER</th><th>Q1–Q3</th><th>Mean ER</th><th>Confidence</th></tr></thead>';
  const body = el('tbody');
  rows.forEach((row) => {
    const tr = el('tr');
    [row[key], row.n, `${row.median.toFixed(3)}%`, `${row.q1.toFixed(3)}–${row.q3.toFixed(3)}%`, `${row.mean.toFixed(3)}%`, row.sample_note].forEach((value) => append(tr, 'td', '', String(value)));
    body.append(tr);
  });
  table.append(body); scroll.append(table); card.append(scroll); return card;
}

function renderInsights() {
  const { overview, performance } = state.manifest;
  const view = el('div', 'route');
  view.append(routeHeader({ eyebrow: 'INSIGHTS / OBSERVED EVIDENCE', title: 'Read the baseline without flattening its limits.', summary: 'Every number below is calculated by the analytical pipeline. Robust summaries sit beside means so one extreme video cannot silently define the story.', aside: valueKind('observed', 'Observed values only') }));

  const audit = overview.audit;
  const quality = el('section', 'quality-strip');
  [
    ['Rows analysed', audit.rows, `${audit.date_min} to ${audit.date_max}`],
    ['Duplicate IDs', audit.duplicate_ids, 'No removals or hidden deduplication'],
    ['Invalid dates', audit.invalid_dates, `${audit.span_days}-day observed window`],
    ['Missing CTAs', audit.missing_by_column.cta, 'Retained and reported as missing'],
  ].forEach(([label, value, detail]) => { const card = el('article', 'quality-card'); append(card, 'span', '', label); append(card, 'strong', '', String(value)); append(card, 'small', '', detail); quality.append(card); });
  view.append(quality);

  const metrics = el('section', 'metric-grid');
  performance.observed_metrics.forEach((item) => metrics.append(metricCard(item)));
  view.append(metrics);

  const charts = el('section', 'chart-grid');
  performance.charts.forEach((chart) => {
    const figure = el('figure', 'chart-card');
    const image = el('img'); image.src = chart.src; image.alt = chart.alt; image.loading = 'lazy';
    const caption = el('figcaption'); append(caption, 'span', 'overline', 'INTERPRETATION'); append(caption, 'strong', '', chart.caption);
    figure.append(image, caption); charts.append(figure);
  });
  view.append(charts);

  const tables = el('section', 'table-grid');
  tables.append(summaryTable('Format performance', performance.summaries.format, 'format'), summaryTable('Pillar performance', performance.summaries.pillar, 'pillar'));
  view.append(tables);
  return view;
}

function renderDiagnosis() {
  const { diagnosis } = state.manifest.strategy;
  const view = el('div', 'route');
  view.append(routeHeader({ eyebrow: 'DIAGNOSIS / EVIDENCE TEST', title: 'The failure is the content system, not one bad post.', summary: 'The diagnosis retains counterevidence and outliers. It identifies a mix problem to test, not a causal result to claim.', aside: valueKind('directional', diagnosis.hypothesis_result) }));
  const lead = el('section', 'diagnosis-layout');
  const statement = el('article', 'diagnosis-statement');
  statement.innerHTML = valueKind('observed', 'Supported by observed evidence');
  append(statement, 'h2', '', diagnosis.selected_diagnosis);
  const evidence = el('div', 'evidence-list'); diagnosis.support.forEach((item) => append(evidence, 'span', 'evidence-chip', item)); statement.append(evidence);
  const caveat = el('aside', 'caveat-card'); append(caveat, 'span', 'overline', 'OUTLIER CHECK'); append(caveat, 'p', '', diagnosis.outlier_caveat);
  lead.append(statement, caveat); view.append(lead);
  const counter = el('section', 'counter-section');
  const head = el('div', 'section-head'); head.innerHTML = '<div><span class="overline">COUNTEREVIDENCE</span><h2>What the data does not prove.</h2></div>'; counter.append(head);
  const list = el('ol', 'counter-list'); diagnosis.counterevidence.forEach((item) => append(list, 'li', '', item)); counter.append(list); view.append(counter);
  return view;
}

function renderStrategy() {
  const { strategy, before_after: comparison } = state.manifest.strategy;
  const view = el('div', 'route');
  view.append(routeHeader({ eyebrow: 'STRATEGY / REVISED TEST DESIGN', title: 'Change the publishing behavior, then measure the response.', summary: 'Each revision links to evidence, a success measure, and a limitation. Proposed ranges remain labelled targets.', aside: valueKind('target', 'Plan, not results') }));
  const changes = el('section', 'strategy-grid');
  strategy.evidence_linked_changes.forEach((change, index) => {
    const card = el('article', 'strategy-card'); append(card, 'span', 'strategy-card__no', String(index + 1).padStart(2, '0')); append(card, 'span', 'evidence-chip', change.evidence); append(card, 'h2', '', change.strategy_change); append(card, 'p', '', change.finding);
    const measure = el('div', 'strategy-measure'); measure.innerHTML = valueKind('target', 'Success measure'); append(measure, 'p', '', change.success_metric); card.append(measure, sourceNote(change.confidence_or_limitation)); changes.append(card);
  });
  view.append(changes);
  const beforeAfter = el('section', 'before-after');
  const head = el('div', 'section-head'); head.innerHTML = '<div><span class="overline">BEFORE / REVISED PILOT</span><h2>Observed baseline beside the proposed test.</h2></div>'; beforeAfter.append(head);
  const grid = el('div', 'comparison-grid');
  comparison.forEach((item) => { const card = el('article', 'comparison-card'); append(card, 'span', 'overline', item.dimension); const before = el('div'); before.innerHTML = valueKind(item.before_kind, item.before_kind); append(before, 'strong', '', item.before); before.append(sourceNote(item.before_source)); const after = el('div'); after.innerHTML = valueKind(item.after_kind, item.after_kind); append(after, 'strong', '', item.after); after.append(sourceNote(item.after_source)); card.append(before, after); grid.append(card); });
  beforeAfter.append(grid); view.append(beforeAfter); return view;
}

function filterBar(active, items, handler) {
  const group = el('div', 'filter-bar'); group.setAttribute('role', 'group'); group.setAttribute('aria-label', 'Content format');
  items.forEach(([value, label]) => { const button = el('button', `filter-chip ${active === value ? 'is-active' : ''}`, label); button.type = 'button'; button.setAttribute('aria-pressed', String(active === value)); button.addEventListener('click', () => handler(value)); group.append(button); });
  return group;
}

function selectedPlanItem() {
  return state.manifest.content_studio.plan.find((item) => item.day === state.selectedDay) || state.manifest.content_studio.plan[0];
}

function planDetail(item) {
  const detail = el('article', 'plan-detail');
  detail.append(planMedia(item));
  const copy = el('div', 'plan-detail__copy');
  copy.innerHTML = `${valueKind(item.format === 'video' ? 'directional' : 'neutral', `Day ${item.day} · ${item.format}`)}${valueKind('target', 'Pilot target')}`;
  append(copy, 'span', 'overline plan-time', `${formatDate(item.date)} · ${item.recommended_publication_time}`);
  append(copy, 'h2', '', item.hook);
  append(copy, 'p', 'plan-idea', item.content_idea);
  const caption = el('div', 'caption-block'); append(caption, 'span', 'overline', 'PROPOSED CAPTION'); append(caption, 'p', '', item.full_proposed_caption); copy.append(caption);
  const facts = el('dl', 'detail-list');
  [['CTA', item.cta], ['Primary KPI', item.primary_kpi], ['Target range', item.reasoned_target_range], ['Evidence link', item.baseline_insight]].forEach(([term, value]) => { append(facts, 'dt', '', term); append(facts, 'dd', '', value); }); copy.append(facts);
  detail.append(copy, generationPromptPanel(item)); return detail;
}

function assetId(item) { return String(item.asset_filename).replace(/\.[^.]+$/, ''); }

function copyGenerationText(text, button) {
  navigator.clipboard?.writeText(text).then(() => { const label = button.textContent; button.textContent = 'Copied'; setTimeout(() => { button.textContent = label; }, 1200); }).catch(() => { button.textContent = 'Copy unavailable'; });
}

function generationPromptPanel(item) {
  const generation = state.manifest.content_studio.generation || {};
  const prompt = (generation.prompts || []).find((entry) => entry.asset_id === assetId(item));
  if (!prompt) return el('div');
  const panel = el('section', 'generation-prompt');
  panel.setAttribute('aria-label', `Generation prompt for Day ${item.day}`);
  panel.innerHTML = `<span class="overline">GENERATION PROMPT</span><h3>Generation Prompt</h3><p class="generation-prompt__meta">Prompt generated by the BudgetFitzz content workflow · ${prompt.recommended_provider} · ${prompt.recommended_model} · ${prompt.width}×${prompt.height}${prompt.duration_seconds ? ` · ${prompt.duration_seconds}s` : ''}</p>`;
  const promptBlock = el('pre', 'generation-prompt__text'); promptBlock.textContent = prompt.prompt;
  const negative = el('pre', 'generation-prompt__text generation-prompt__text--negative'); negative.textContent = prompt.negative_prompt;
  panel.append(promptBlock, negative);
  const actions = el('div', 'generation-actions');
  const copy = el('button', 'button button--secondary', 'Copy prompt'); copy.type = 'button'; copy.addEventListener('click', () => copyGenerationText(prompt.prompt, copy));
  const copyNegative = el('button', 'button button--secondary', 'Copy negative prompt'); copyNegative.type = 'button'; copyNegative.addEventListener('click', () => copyGenerationText(prompt.negative_prompt, copyNegative));
  const packageLink = el('a', 'button button--secondary', 'Export JSON'); packageLink.href = `../analysis/generation_packages/${prompt.asset_id}.json`; packageLink.download = `${prompt.asset_id}.json`;
  const markdownLink = el('a', 'button button--secondary', 'Export Markdown'); markdownLink.href = `../analysis/generation_packages/${prompt.asset_id}.md`; markdownLink.download = `${prompt.asset_id}.md`;
  const referenceLink = el('a', 'button button--secondary', 'Download reference files'); referenceLink.href = prompt.reference_files?.[0] ? `../${prompt.reference_files[0]}` : '#'; if (!prompt.reference_files?.length) { referenceLink.setAttribute('aria-disabled', 'true'); referenceLink.classList.add('is-disabled'); }
  const flow = el('a', 'button', 'Open Google Flow'); flow.href = 'https://labs.google/fx/tools/flow/'; flow.target = '_blank'; flow.rel = 'noopener noreferrer';
  actions.append(copy, copyNegative, packageLink, markdownLink, referenceLink, flow); panel.append(actions);
  if (prompt.storyboard_beats?.length) { const beats = el('ul', 'generation-beats'); prompt.storyboard_beats.forEach((beat) => append(beats, 'li', '', `${beat.step}: ${beat.caption_evidence} → ${beat.takeaway}`)); panel.append(beats); }
  return panel;
}

function renderContentPlan() {
  const { plan, plan_counts: counts } = state.manifest.content_studio;
  const view = el('div', 'route');
  view.append(routeHeader({ eyebrow: 'CONTENT PLAN / SEVEN-DAY PILOT', title: 'One week. Seven useful reasons to return.', summary: 'The plan is generated by ContentPlannerAgent and refined by CreativeDirectorAgent. Select a day to inspect its media, caption, CTA, KPI, and evidence link.', aside: `${valueKind('validated', `${counts.post} posts`)}${valueKind('directional', `${counts.video} videos`)}` }));
  view.append(filterBar(state.planFormat, [['all', 'All 7'], ['post', 'Posts'], ['video', 'Videos']], (value) => {
    state.planFormat = value;
    const selected = selectedPlanItem();
    if (value !== 'all' && selected.format !== value) {
      state.selectedDay = plan.find((item) => item.format === value)?.day || selected.day;
    }
    renderRoute(false);
  }));
  const calendar = el('section', 'week-strip'); calendar.setAttribute('aria-label', 'Seven-day content plan');
  plan.forEach((item) => { const hidden = state.planFormat !== 'all' && item.format !== state.planFormat; const button = el('button', `day-card ${state.selectedDay === item.day ? 'is-active' : ''} ${hidden ? 'is-muted' : ''}`); button.type = 'button'; button.dataset.day = item.day; button.setAttribute('aria-pressed', String(state.selectedDay === item.day)); button.innerHTML = `<span>Day ${item.day}</span><strong>${formatDate(item.date, { weekday: 'short' })}</strong><small>${item.format}</small>`; button.addEventListener('click', () => { state.selectedDay = item.day; renderRoute(false); }); calendar.append(button); });
  view.append(calendar, planDetail(selectedPlanItem()));
  return view;
}

function openPreview(day) {
  const item = state.manifest.content_studio.plan.find((candidate) => candidate.day === Number(day));
  if (!item) return;
  const briefs = state.manifest.content_studio.video_briefs.briefs || [];
  const brief = briefs.find((candidate) => candidate.day === item.day);
  const content = $('#preview-content'); content.replaceChildren();
  const head = el('div', 'dialog-head'); const heading = el('div'); heading.innerHTML = `<span class="overline">DAY ${item.day} · ${item.format.toUpperCase()}</span>`; append(heading, 'h2', '', item.hook).id = 'preview-title'; const close = el('button', 'icon-button', '×'); close.type = 'button'; close.setAttribute('aria-label', 'Close preview'); close.addEventListener('click', () => $('#preview-modal').close()); head.append(heading, close); content.append(head);
  const body = el('div', 'preview-body'); body.append(planMedia(item)); const copy = el('div', 'preview-copy'); append(copy, 'p', 'plan-idea', item.full_proposed_caption); const cta = el('div', 'cta-note'); cta.innerHTML = valueKind('target', 'CTA'); append(cta, 'strong', '', item.cta); copy.append(cta);
  if (brief) { const details = el('details', 'agent-rationale'); const summary = el('summary', '', 'Agent rationale and storyboard'); details.append(summary); append(details, 'p', '', brief.creative_director_decision.why); const list = el('ol'); brief.beats.forEach((beat) => append(list, 'li', '', `${beat.step}: “${beat.caption_evidence}” — ${beat.takeaway}`)); details.append(list); copy.append(details); }
  body.append(copy); content.append(body); $('#preview-modal').showModal();
}

function renderStudio() {
  const { plan, generation = {} } = state.manifest.content_studio;
  const view = el('div', 'route');
  view.append(routeHeader({ eyebrow: 'STUDIO / FINISHED MEDIA', title: 'Review the visual and the reason together.', summary: 'Every preview stays paired with its proposed caption, CTA, KPI, target and agent rationale. Nothing in this gallery is an unsupported standalone asset.', aside: valueKind('validated', '7 finished assets') }));
  view.append(providerStatusPanel(generation), importMediaPanel(plan, generation), generationHistoryPanel(generation));
  view.append(filterBar(state.studioFormat, [['all', 'All'], ['post', 'Posts 4:5'], ['video', 'Videos 9:16']], (value) => { state.studioFormat = value; renderRoute(false); }));
  const filtered = plan.filter((item) => state.studioFormat === 'all' || item.format === state.studioFormat);
  const gallery = el('section', 'studio-gallery');
  if (!filtered.length) gallery.append(emptyState('No assets in this view', 'Choose a different format to review generated media.'));
  filtered.forEach((item) => gallery.append(contentCard(item, { interactive: true })));
  gallery.addEventListener('click', (event) => { const card = event.target.closest('[data-day]'); if (card) openPreview(card.dataset.day); });
  view.append(gallery); return view;
}

function providerStatusPanel(generation) {
  const section = el('section', 'provider-status'); append(section, 'span', 'overline', 'HYBRID GENERATION STATUS'); append(section, 'h2', '', 'Choose how the next version is made.'); append(section, 'p', '', generation.provider_status?.claim || 'Provider state is unavailable.');
  const grid = el('div', 'provider-status__grid'); (generation.provider_status?.providers || []).forEach((provider) => { const card = el('article', 'provider-status__card'); append(card, 'h3', '', provider.label); append(card, 'p', '', `API: ${provider.api_state} · Manual: ${provider.manual_state}`); append(card, 'small', '', provider.api_tested ? 'Local path tested' : 'API mode not tested'); grid.append(card); }); section.append(grid); return section;
}

function importMediaPanel(plan, generation) {
  const section = el('section', 'media-import'); append(section, 'span', 'overline', 'MANUAL PROVIDER WORKFLOW'); append(section, 'h2', '', 'Import Generated Media'); append(section, 'p', '', 'Import a file generated manually in Google Flow / Veo or another provider. The original is quarantined, validated, post-processed and kept as a candidate until you approve it.');
  const form = el('form', 'media-import__form'); form.enctype = 'multipart/form-data';
  const select = (name, label, values) => { const group = el('label', 'media-import__field'); append(group, 'span', '', label); const control = el('select'); control.name = name; values.forEach(([value, text]) => { const option = el('option', '', text); option.value = value; control.append(option); }); group.append(control); return group; };
  form.append(select('asset_id', 'Related asset', plan.map((item) => [assetId(item), `Day ${item.day} · ${item.hook}`])));
  form.append(select('provider', 'Provider', ['Google Flow / Veo','Hugging Face','FAL','Runway','Higgsfield','Kling','Stock media','Local generation','Other'].map((value) => [value, value])));
  form.append(select('access_method', 'Access method', ['Manual web interface','API','Free website credits','Promotional credits','Paid website generation','Licensed stock media','Local'].map((value) => [value, value])));
  form.append(select('credit_type', 'Credit type', ['Free website credits','Promotional credits','Paid INR','Licensed stock','Not applicable'].map((value) => [value, value])));
  const model = el('label', 'media-import__field'); append(model, 'span', '', 'Provider model (optional)'); const modelInput = el('input'); modelInput.name = 'model'; modelInput.placeholder = 'e.g. Veo'; model.append(modelInput); form.append(model);
  const attempts = el('label', 'media-import__field'); append(attempts, 'span', '', 'Generation attempts'); const attemptsInput = el('input'); attemptsInput.name = 'attempts'; attemptsInput.type = 'number'; attemptsInput.min = '1'; attemptsInput.value = '1'; attempts.append(attemptsInput); form.append(attempts);
  const cost = el('label', 'media-import__field'); append(cost, 'span', '', 'Actual paid cost (INR)'); const costInput = el('input'); costInput.name = 'actual_cost_inr'; costInput.type = 'number'; costInput.min = '0'; costInput.value = '0'; cost.append(costInput); form.append(cost);
  const date = el('label', 'media-import__field'); append(date, 'span', '', 'Generation date'); const dateInput = el('input'); dateInput.name = 'generation_date'; dateInput.type = 'datetime-local'; date.append(dateInput); form.append(date);
  const requestId = el('label', 'media-import__field'); append(requestId, 'span', '', 'Provider request ID (optional)'); const requestIdInput = el('input'); requestIdInput.name = 'provider_request_id'; requestId.append(requestIdInput); form.append(requestId);
  const media = el('label', 'media-import__field media-import__field--wide'); append(media, 'span', '', 'Media file'); const mediaInput = el('input'); mediaInput.name = 'media_file'; mediaInput.type = 'file'; mediaInput.accept = 'image/png,image/jpeg,image/webp,video/mp4'; mediaInput.required = true; media.append(mediaInput); form.append(media);
  const mappings = el('label', 'media-import__field media-import__field--wide'); append(mappings, 'span', '', 'Caption-to-beat mapping (optional)'); const mappingsInput = el('textarea'); mappingsInput.name = 'beat_mappings'; mappingsInput.placeholder = 'For video: source 00:00–00:03 | caption phrase | visual beat | crop/callout'; mappings.append(mappingsInput); form.append(mappings);
  const notes = el('label', 'media-import__field media-import__field--wide'); append(notes, 'span', '', 'Notes (optional)'); const notesInput = el('textarea'); notesInput.name = 'notes'; notes.append(notesInput); form.append(notes);
  const permission = el('label', 'media-import__consent'); const box = el('input'); box.type = 'checkbox'; box.name = 'permission_confirmed'; box.required = true; permission.append(box); append(permission, 'span', '', 'I have permission to use this media and want it validated as a new version.'); form.append(permission);
  const submit = el('button', 'button', 'Validate and create candidate'); submit.type = 'submit'; const result = el('p', 'media-import__result'); result.setAttribute('aria-live', 'polite'); form.append(submit, result);
  form.addEventListener('submit', async (event) => { event.preventDefault(); const selected = (generation.prompts || []).find((entry) => entry.asset_id === form.elements.asset_id.value); const data = new FormData(form); data.set('prompt_version', String(selected?.prompt_version || 1)); data.set('generation_date', form.elements.generation_date.value ? new Date(form.elements.generation_date.value).toISOString() : new Date().toISOString()); data.set('permission_confirmed', form.elements.permission_confirmed.checked ? 'true' : 'false'); submit.disabled = true; result.textContent = 'Validating imported media…'; try { const response = await fetch('/api/generation/import', { method: 'POST', body: data }); const payload = await response.json(); if (!response.ok) throw new Error(payload.message || 'Import failed'); result.textContent = `Candidate ${payload.result.version} created. It is awaiting human approval.`; } catch (error) { result.textContent = error.message; } finally { submit.disabled = false; } });
  section.append(form); return section;
}

function generationHistoryPanel(generation) {
  const section = el('section', 'generation-history'); append(section, 'span', 'overline', 'ASSET VERSIONING & PROVENANCE'); append(section, 'h2', '', 'Approved media stays active until you approve a candidate.');
  const versions = generation.versions || {}; const pendingJobs = (generation.jobs || []).filter((job) => job.status === 'AWAITING_REVIEW');
  const notice = el('aside', 'generation-history__notice');
  if (!pendingJobs.length) {
    append(notice, 'strong', '', 'No imported candidate is awaiting approval.');
    append(notice, 'p', '', 'Upload a file above and select “Validate and create candidate”. The approval action will then appear on the matching asset card below.');
    const disabled = el('button', 'button button--secondary', 'Approve imported candidate'); disabled.type = 'button'; disabled.disabled = true; disabled.title = 'Available after a media candidate passes validation'; notice.append(disabled);
  } else {
    append(notice, 'strong', '', `${pendingJobs.length} candidate${pendingJobs.length === 1 ? '' : 's'} awaiting approval.`);
    append(notice, 'p', '', 'Use the approval action on the matching asset card below to make the candidate active.');
    if (pendingJobs.length === 1) {
      const pending = pendingJobs[0]; const approveNow = el('button', 'button button--primary', `Approve ${pending.asset_id} now`); approveNow.type = 'button';
      approveNow.addEventListener('click', async () => { approveNow.disabled = true; try { const response = await fetch('/api/generation/approve', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({job_id: pending.job_id}) }); const payload = await response.json(); if (!response.ok) throw new Error(payload.message || 'Approval failed'); window.location.reload(); } catch (error) { approveNow.textContent = error.message; approveNow.disabled = false; } });
      notice.append(approveNow);
    }
  }
  section.append(notice);
  const list = el('div', 'generation-history__list');
  Object.entries(versions).forEach(([asset, record]) => { const card = el('article', 'generation-history__card'); append(card, 'h3', '', asset); append(card, 'p', '', `Active version: ${record.active_version || 'None'} · ${record.versions?.length || 0} recorded version(s)`); const pending = (generation.jobs || []).find((job) => job.asset_id === asset && job.status === 'AWAITING_REVIEW'); if (pending) { const approve = el('button', 'button button--secondary', `Approve ${pending.job_id}`); approve.type = 'button'; approve.addEventListener('click', async () => { approve.disabled = true; try { const response = await fetch('/api/generation/approve', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({job_id: pending.job_id}) }); const payload = await response.json(); if (!response.ok) throw new Error(payload.message || 'Approval failed'); window.location.reload(); } catch (error) { approve.textContent = error.message; approve.disabled = false; } }); card.append(approve); } list.append(card); }); section.append(list); return section;
}

function finalTraceEntries(trace) {
  const byAgent = new Map();
  trace.forEach((entry) => { const previous = byAgent.get(entry.agent); if (!previous || entry.status !== 'started') byAgent.set(entry.agent, entry); });
  return [...byAgent.values()];
}

function renderArchitectureExplainer() {
  const architecture = state.manifest.architecture;
  const details = architecture.technical_details;
  const section = el('section', 'architecture-explainer');
  section.id = 'how-platform-connects';
  section.setAttribute('aria-labelledby', 'architecture-title');
  const head = el('div', 'architecture-explainer__head');
  append(head, 'span', 'overline', 'PLATFORM ARCHITECTURE');
  const title = append(head, 'h2', '', 'How the platform connects');
  title.id = 'architecture-title';
  append(head, 'p', '', architecture.summary);
  section.append(head);

  const flow = el('ol', 'architecture-flow');
  flow.setAttribute('aria-label', 'Backend-to-frontend data flow');
  architecture.flow.forEach((stage, index) => {
    const item = el('li', 'architecture-stage');
    const badge = el('span', 'architecture-stage__icon');
    badge.innerHTML = icon(stage.icon || 'architecture');
    const copy = el('div');
    append(copy, 'span', 'architecture-stage__number', String(index + 1).padStart(2, '0'));
    append(copy, 'h3', '', stage.label);
    append(copy, 'p', '', stage.description);
    item.append(badge, copy);
    if (index < architecture.flow.length - 1) {
      const connector = el('span', 'architecture-stage__connector', '→');
      connector.setAttribute('aria-hidden', 'true');
      item.append(connector);
    }
    flow.append(item);
  });
  section.append(flow);

  const technical = el('details', 'architecture-details');
  const summary = el('summary', '', 'View technical details');
  technical.append(summary);
  const detailGrid = el('dl', 'architecture-details__grid');
  const detailItems = [
    ['Manifest path', details.manifest_path],
    ['Backend entry point', details.backend_entry],
    ['Frontend data-loading entry point', details.frontend_entry],
    ['Health endpoint', details.health_endpoint],
    ['Current API-status response', JSON.stringify(details.health_response)],
  ];
  detailItems.forEach(([term, value]) => {
    const row = el('div', 'architecture-detail');
    append(row, 'dt', '', term);
    append(row, 'dd', '', value);
    detailGrid.append(row);
  });
  const outputRow = el('div', 'architecture-detail architecture-detail--outputs');
  append(outputRow, 'dt', '', 'Generated-output categories');
  const categories = el('ul');
  details.output_categories.forEach((category) => append(categories, 'li', '', category));
  outputRow.append(categories);
  detailGrid.append(outputRow);
  technical.append(detailGrid);
  section.append(technical);
  return section;
}

function renderAgents() {
  const workflow = state.manifest.workflow;
  const entries = finalTraceEntries(workflow.trace);
  const totalDuration = Object.values(workflow.timings_sec || {}).reduce((sum, value) => sum + Number(value || 0), 0);
  const view = el('div', 'route');
  view.append(routeHeader({ eyebrow: 'AGENTS / DECISION TRACE', title: 'The content has a recorded reason for existing.', summary: 'The trace exposes concise decisions, evidence references, tools, durations and retries. It intentionally stores no hidden chain-of-thought.', aside: `${valueKind('validated', `${entries.length} agents`)}${valueKind('neutral', `${totalDuration.toFixed(2)}s recorded`)}` }));
  view.append(renderArchitectureExplainer());
  const flow = el('section', 'agent-flow');
  entries.forEach((entry, index) => { const node = el('article', 'agent-node'); append(node, 'span', 'agent-node__index', String(index + 1).padStart(2, '0')); const copy = el('div'); append(copy, 'h2', '', entry.agent.replace(/Agent$/, ' Agent')); append(copy, 'p', '', entry.decision_summary); const meta = el('div', 'agent-meta'); meta.innerHTML = `${valueKind(entry.status === 'completed' || entry.status === 'approved' ? 'validated' : 'neutral', entry.status)}<span>${entry.provider_or_tool}</span><span>${Number(entry.duration_sec || workflow.timings_sec?.[entry.agent] || 0).toFixed(3)}s</span><span>retry ${entry.retry_number ?? workflow.retry_counts?.[entry.agent] ?? 0}</span>`; copy.append(meta); if (entry.evidence_ids?.length) { const evidence = el('div', 'evidence-list'); entry.evidence_ids.forEach((id) => append(evidence, 'span', 'evidence-chip', id)); copy.append(evidence); } node.append(copy); flow.append(node); });
  view.append(flow); return view;
}

function validationCategory(name) {
  if (/CSV|DOCX|Checksum|Dataset|Raw|Metric|Analysis|Sample|Outlier/i.test(name)) return 'Data & analysis';
  if (/plan|post|video|asset|caption|placeholder|Before|Target/i.test(name)) return 'Content & media';
  if (/Agent|workflow|Retry|GPU|trace|checkpoint/i.test(name)) return 'Agents & operations';
  return 'Application & package';
}

function renderValidation() {
  const validation = state.manifest.validation;
  const view = el('div', 'route');
  view.append(routeHeader({ eyebrow: 'VALIDATION / PRODUCTION GATE', title: validation.status === 'PASS' ? 'The production gate is clear.' : 'The production gate needs attention.', summary: 'Raw preservation, calculations, plan counts, media dimensions, captions, spend, application paths and packaging are checked before export.', aside: valueKind(validation.status === 'PASS' ? 'validated' : 'error', validation.status) }));
  const score = el('section', 'validation-score'); score.innerHTML = `<strong>${validation.passed}</strong><span>of ${validation.passed + validation.failed}<br>checks passed</span><div class="score-track"><i style="width:${(validation.passed / Math.max(1, validation.passed + validation.failed)) * 100}%"></i></div>`; view.append(score);
  const groups = new Map();
  (validation.checks || []).forEach((check) => { const category = validationCategory(check.check); if (!groups.has(category)) groups.set(category, []); groups.get(category).push(check); });
  const grid = el('section', 'validation-groups');
  groups.forEach((checks, category) => { const card = el('article', 'validation-group'); const head = el('div', 'validation-group__head'); append(head, 'h2', '', category); append(head, 'span', 'count-badge', `${checks.filter((item) => item.passed).length}/${checks.length}`); card.append(head); const list = el('ul'); checks.forEach((check) => { const li = el('li'); li.innerHTML = `<span class="check-mark ${check.passed ? 'is-pass' : 'is-fail'}" aria-hidden="true">${check.passed ? '✓' : '!'}</span><div><strong>${check.check}</strong><small>${check.evidence}</small></div>`; list.append(li); }); card.append(list); grid.append(card); });
  view.append(grid); return view;
}

function renderSubmission() {
  const { submission, operations, validation } = state.manifest;
  const view = el('div', 'route');
  view.append(routeHeader({ eyebrow: 'SUBMISSION / FILE SHELF', title: submission?.ready ? 'Ready for handoff.' : 'Handoff files are being assembled.', summary: 'The shelf reports filesystem availability and file metadata from the generated manifest. The self-referential ZIP size is verified separately by the package validator.', aside: valueKind(submission?.ready ? 'validated' : 'target', submission?.ready ? 'Package ready' : 'Build pending') }));
  const band = el('section', 'submission-band');
  band.innerHTML = `<div><span class="overline">FINAL STATUS</span><strong>${validation.status}</strong><small>${validation.passed}/${validation.passed + validation.failed} checks</small></div><div><span class="overline">DIRECT PAID SPEND</span><strong>₹${Number(operations?.spend?.paid_generation_total_inr || 0).toFixed(0)}</strong><small>${operations?.spend?.within_cap ? 'Within documented cap' : 'Review required'}</small></div><div><span class="overline">VIDEO ENCODER</span><strong>${operations?.hardware?.selected_video_encoder || 'Unavailable'}</strong><small>${operations?.hardware?.gpu_name || 'Hardware not reported'}</small></div>`;
  view.append(band);
  const shelf = el('section', 'file-shelf');
  (submission?.files || []).forEach((file) => { const card = el('article', `file-card ${file.available ? '' : 'is-missing'}`); card.innerHTML = `<span class="file-icon">${icon('file')}</span>`; const copy = el('div'); copy.innerHTML = `${valueKind(file.available ? 'validated' : 'error', file.available ? 'Available' : 'Missing')}<h2>${file.label}</h2>`; append(copy, 'p', '', file.path); append(copy, 'small', '', `${file.type} · ${file.size_note || formatBytes(file.bytes)}`); card.append(copy); if (file.available) { const link = el('a', 'button button--secondary', file.type === 'ZIP' ? 'Download' : 'Open'); link.href = file.href; if (file.type === 'ZIP') link.setAttribute('download', ''); card.append(link); } shelf.append(card); });
  if (!submission?.files?.length) shelf.append(emptyState('No file shelf in this run', 'Run the pipeline and finalizer to regenerate submission metadata.'));
  view.append(shelf); return view;
}

const routeRenderers = {
  home: renderHome,
  insights: renderInsights,
  diagnosis: renderDiagnosis,
  strategy: renderStrategy,
  'content-plan': renderContentPlan,
  studio: renderStudio,
  agents: renderAgents,
  validation: renderValidation,
  submission: renderSubmission,
};

function currentRoute() {
  const requested = window.location.hash.replace(/^#/, '') || 'home';
  return routeRenderers[requested] ? requested : 'home';
}

function renderRoute(focus = true) {
  state.route = currentRoute();
  const stage = $('#main-content');
  stage.replaceChildren(routeRenderers[state.route]());
  $$('[data-route]').forEach((link) => { const active = link.dataset.route === state.route; link.classList.toggle('is-active', active); if (active) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current'); });
  const label = state.manifest.navigation.find((item) => item.id === state.route)?.label || 'Home';
  $('#route-context').textContent = `${label} / BudgetFitzz Editorial Atelier`;
  document.title = `${label} — BudgetFitzz Atelier`;
  if (focus) { stage.focus({ preventScroll: true }); window.scrollTo({ top: 0, behavior: 'instant' }); }
}

function renderError(error) {
  const stage = $('#main-content');
  const box = el('div', 'error-state');
  append(box, 'span', 'overline', 'MANIFEST ERROR');
  append(box, 'h1', '', 'The atelier could not open.').id = 'route-title';
  append(box, 'p', '', error.message);
  append(box, 'code', '', 'PYTHONPATH=src .venv\\Scripts\\python.exe scripts\\run_pipeline.py');
  const button = el('button', 'button button--primary', 'Retry loading'); button.type = 'button'; button.addEventListener('click', () => window.location.reload()); box.append(button); stage.replaceChildren(box);
}

window.addEventListener('hashchange', () => { if (state.manifest) renderRoute(); });

loadManifest().then((manifest) => {
  state.manifest = manifest;
  renderChrome(manifest);
  renderRoute(false);
}).catch((error) => {
  console.error('BudgetFitzz manifest load failed:', error);
  renderError(error);
});
