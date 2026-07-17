const $ = (selector) => document.querySelector(selector);
const create = (tag, className, value) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value !== undefined) node.textContent = value;
  return node;
};
const appendText = (parent, tag, className, value) => parent.append(create(tag, className, value));

async function loadManifest() {
  const response = await fetch('data/platform_manifest.json', { cache: 'no-store' });
  if (!response.ok) throw new Error('The generated platform manifest is unavailable. Run the pipeline to refresh it.');
  return response.json();
}

function renderNavigation(manifest) {
  const nav = $('#nav');
  manifest.navigation.forEach((item) => {
    const link = create('a', 'navigation-link', item.label);
    link.href = `#${item.id}`;
    nav.append(link);
  });
}

function renderOverview(manifest) {
  const { overview, run } = manifest;
  $('#run-chip').textContent = `${run.status.toUpperCase()} · ${run.provider}`;
  const grid = $('#overview-kpis');
  overview.kpis.forEach((item) => {
    const card = create('article', 'kpi-card');
    appendText(card, 'span', 'kpi-label', item.label);
    appendText(card, 'strong', 'kpi-value', item.value);
    appendText(card, 'p', 'kpi-detail', item.detail);
    appendText(card, 'small', 'source-note', `Calculated: ${item.source} · n=${item.sample_size}`);
    grid.append(card);
  });
  const lineage = overview.lineage;
  $('#lineage-callout').textContent = `Observed source: ${lineage.raw_source} · ${lineage.observed_rows} rows · run ${lineage.calculation_run_id}. Original provenance remains unspecified; targets and hypotheses are never presented as results.`;
}

function renderContent(manifest) {
  const { plan, plan_counts: counts, asset_root: assets, video_briefs: briefData } = manifest.content_studio;
  $('#plan-summary').textContent = `${counts.post} posts + ${counts.video} videos · ${plan.length} validated items · local assets only`;
  plan.filter((item) => item.format === 'post').forEach((item) => {
    const card = create('article', 'asset-card');
    const image = create('img');
    image.loading = 'lazy'; image.src = `${assets}/posts/${item.asset_filename}`; image.alt = `Day ${item.day}: ${item.hook}`;
    card.append(image);
    const copy = create('div', 'asset-card__copy');
    appendText(copy, 'span', 'eyebrow', `DAY ${item.day} · ${item.content_pillar}`);
    appendText(copy, 'h3', '', item.hook);
    appendText(copy, 'p', '', item.content_idea);
    appendText(copy, 'small', 'metric-tag', item.primary_kpi);
    card.append(copy); $('#post-gallery').append(card);
  });
  const briefs = new Map((briefData.briefs || []).map((brief) => [brief.day, brief]));
  plan.filter((item) => item.format === 'video').forEach((item) => {
    const card = create('article', 'video-card');
    const video = create('video', 'video-card__media');
    video.controls = true; video.muted = true; video.playsInline = true; video.preload = 'metadata';
    const stem = item.asset_filename.replace(/\.mp4$/, '');
    video.poster = `${assets}/video_frames/${stem}_preview.png`;
    const source = create('source'); source.src = `${assets}/videos/${item.asset_filename}`; source.type = 'video/mp4'; video.append(source); card.append(video);
    const copy = create('div', 'video-card__copy');
    appendText(copy, 'span', 'eyebrow eyebrow--lime', `DAY ${item.day} · VIDEO`);
    appendText(copy, 'h3', '', item.hook);
    appendText(copy, 'p', '', item.full_proposed_caption);
    appendText(copy, 'small', 'metric-tag metric-tag--dark', item.reasoned_target_range);
    const brief = briefs.get(item.day);
    if (brief) {
      const rationale = create('details', 'storyboard');
      const summary = create('summary', '', 'Why the video matches the caption'); rationale.append(summary);
      appendText(rationale, 'p', '', brief.creative_director_decision.why);
      const beats = create('ol', 'storyboard__beats');
      brief.beats.forEach((beat) => appendText(beats, 'li', '', `${beat.step}: “${beat.caption_evidence}” — ${beat.takeaway}`));
      rationale.append(beats); copy.append(rationale);
    }
    card.append(copy); $('#video-gallery').append(card);
  });
  const tabs = [...document.querySelectorAll('.tab')];
  tabs.forEach((tab) => tab.addEventListener('click', () => {
    const showVideos = tab.id === 'video-tab';
    tabs.forEach((item) => { const active = item === tab; item.classList.toggle('is-active', active); item.setAttribute('aria-selected', String(active)); });
    $('#post-panel').hidden = showVideos; $('#video-panel').hidden = !showVideos;
  }));
}

function renderPerformance(manifest) {
  const { observed_metrics: metrics, charts, summaries } = manifest.performance;
  metrics.forEach((item) => {
    const card = create('article', 'metric-card'); appendText(card, 'span', '', item.metric); appendText(card, 'strong', '', item.display); appendText(card, 'small', '', `n=${item.n} · ${item.source}`); $('#observed-metrics').append(card);
  });
  charts.forEach((chart) => {
    const figure = create('figure', 'chart-card'); const image = create('img'); image.src = chart.src; image.alt = chart.alt; image.loading = 'lazy'; figure.append(image); appendText(figure, 'figcaption', '', chart.caption); $('#chart-gallery').append(figure);
  });
  [['Format performance', summaries.format, 'format'], ['Pillar performance', summaries.pillar, 'pillar']].forEach(([title, rows, key]) => {
    const panel = create('article', 'summary-card'); appendText(panel, 'h3', '', title);
    const scroll = create('div', 'table-scroll'); const table = create('table'); const head = create('thead'); const headRow = create('tr'); ['Group', 'n', 'Median ER', 'Q1–Q3', 'Mean ER', 'Confidence'].forEach((label) => appendText(headRow, 'th', '', label)); head.append(headRow); table.append(head);
    const body = create('tbody'); rows.forEach((row) => { const tr = create('tr'); [row[key], row.n, `${row.median.toFixed(3)}%`, `${row.q1.toFixed(3)}–${row.q3.toFixed(3)}%`, `${row.mean.toFixed(3)}%`, row.sample_note].forEach((value) => appendText(tr, 'td', '', String(value))); body.append(tr); }); table.append(body); scroll.append(table); panel.append(scroll); $('#summary-tables').append(panel);
  });
}

function renderStrategy(manifest) {
  const { diagnosis, strategy, before_after: comparison } = manifest.strategy;
  appendText($('#diagnosis-card'), 'span', 'eyebrow eyebrow--lime', 'FAILURE DIAGNOSIS'); appendText($('#diagnosis-card'), 'h3', '', diagnosis.selected_diagnosis); appendText($('#diagnosis-card'), 'p', '', diagnosis.outlier_caveat);
  strategy.evidence_linked_changes.forEach((change) => {
    const card = create('article', 'strategy-card'); appendText(card, 'span', 'evidence-id', change.evidence); appendText(card, 'h3', '', change.strategy_change); appendText(card, 'p', '', change.finding); appendText(card, 'small', '', `Success measure: ${change.success_metric}`); appendText(card, 'small', 'source-note', change.confidence_or_limitation); $('#strategy-grid').append(card);
  });
  $('#after-note').textContent = manifest.overview.lineage.after_note;
  comparison.forEach((item) => { const card = create('article', 'comparison-card'); appendText(card, 'span', '', item.dimension); appendText(card, 'small', 'value-kind', item.before_kind.toUpperCase()); appendText(card, 'strong', '', item.before); appendText(card, 'small', 'source-note', item.before_source); appendText(card, 'i', '', '↓'); appendText(card, 'small', 'value-kind', item.after_kind.toUpperCase()); appendText(card, 'b', '', item.after); appendText(card, 'small', 'source-note', item.after_source); $('#comparison-grid').append(card); });
}

function renderWorkflow(manifest) {
  manifest.workflow.trace.forEach((entry) => { const row = create('article', 'trace-row'); appendText(row, 'strong', '', entry.agent); appendText(row, 'p', '', entry.decision_summary); appendText(row, 'span', `trace-status trace-status--${String(entry.status).toLowerCase()}`, entry.status); $('#trace-list').append(row); });
}

function renderValidation(manifest) {
  const validation = manifest.validation; $('#validation-title').textContent = validation.status === 'PASS' ? 'Production gate passed.' : 'Repair gate active.'; $('#validation-score').innerHTML = `<strong>${validation.passed}/${validation.passed + validation.failed}</strong><span>checks passed</span>`;
}

function activateNavigation() {
  const links = [...document.querySelectorAll('.navigation-link')];
  const observer = new IntersectionObserver((entries) => entries.forEach((entry) => { if (entry.isIntersecting) links.forEach((link) => link.classList.toggle('is-active', link.getAttribute('href') === `#${entry.target.id}`)); }), { rootMargin: '-20% 0px -65% 0px' });
  document.querySelectorAll('.view[id]').forEach((section) => observer.observe(section));
}

loadManifest().then((manifest) => { renderNavigation(manifest); renderOverview(manifest); renderContent(manifest); renderPerformance(manifest); renderStrategy(manifest); renderWorkflow(manifest); renderValidation(manifest); activateNavigation(); $('#app-status').remove(); }).catch((error) => { $('#app-status').textContent = error.message; $('#app-status').classList.add('app-status--error'); console.error(error); });
