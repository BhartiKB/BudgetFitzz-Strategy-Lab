async function loadData() {
  const response = await fetch('data/dashboard.json', { cache: 'no-store' });
  if (!response.ok) throw new Error('dashboard data missing');
  return response.json();
}

const el = (tag, className, text) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
};

const addText = (parent, tag, className, text) => {
  const node = el(tag, className, text);
  parent.append(node);
  return node;
};

function renderKpis(data) {
  const grid = document.querySelector('#kpis');
  data.overview_kpis.forEach((item) => {
    const card = el('div', 'kpi');
    addText(card, 'strong', '', item.value);
    addText(card, 'span', '', item.label);
    addText(card, 'small', '', `${item.detail} · n=${item.sample_size}`);
    addText(card, 'div', 'source-note', `Calculated: ${item.source}`);
    grid.append(card);
  });
}

function renderAudit(data) {
  const auditRows = [
    ['Rows', data.audit.rows],
    ['Columns', data.audit.columns],
    ['Missing CTAs', data.audit.missing_by_column.cta],
    ['Wrong-handle rows', data.audit.aristostyling_rows],
    ['Video plays > reach', data.facts.video_views_exceed_reach_count],
    ['Duplicate rows', data.audit.duplicate_rows],
    ['Duplicate IDs', data.audit.duplicate_ids],
    ['Invalid dates', data.audit.invalid_dates],
    ['Negative numeric values', data.audit.negative_numeric_values],
    ['Date span', `${data.audit.date_min} → ${data.audit.date_max} (${data.audit.span_days} days)`],
  ];
  const list = document.querySelector('#audit-list');
  auditRows.forEach(([label, value]) => {
    const row = el('div');
    addText(row, 'span', '', label);
    addText(row, 'b', '', String(value));
    list.append(row);
  });
  document.querySelector('#quality-record-count').textContent = `${data.audit.rows} calculated records`;
  document.querySelector('#audit-source').textContent = `Source: ${data.data_lineage.raw_source} · SHA-256 ${data.data_lineage.raw_sha256.slice(0, 16)}…`;
}

function renderMetrics(data) {
  const observed = document.querySelector('#observed-metric-grid');
  data.observed_metrics.forEach((item) => {
    const card = el('article', 'observed-metric');
    addText(card, 'small', '', item.metric);
    addText(card, 'strong', '', item.display);
    addText(card, 'span', '', `n=${item.n}`);
    addText(card, 'code', '', item.source);
    observed.append(card);
  });

  const formulas = document.querySelector('#metric-grid');
  Object.entries(data.metric_contract.metrics).forEach(([name, formula]) => {
    const card = el('div', 'metric');
    addText(card, 'b', '', name.replaceAll('_', ' '));
    addText(card, 'code', '', formula);
    formulas.append(card);
  });
}

function summaryTable(title, rows, labelKey, source) {
  const panel = el('section', 'summary-panel');
  addText(panel, 'h3', '', title);
  addText(panel, 'div', 'source-note', `Calculated source: ${source}`);
  const wrapper = el('div', 'table-scroll');
  const table = el('table', 'data-table');
  const head = el('thead');
  const headRow = el('tr');
  ['Group', 'n', 'Median ER', 'Q1–Q3', 'Mean ER', 'Confidence'].forEach((value) => addText(headRow, 'th', '', value));
  head.append(headRow);
  table.append(head);
  const body = el('tbody');
  rows.forEach((row) => {
    const tr = el('tr');
    const values = [
      row[labelKey],
      row.n,
      `${row.median.toFixed(3)}%`,
      `${row.q1.toFixed(3)}–${row.q3.toFixed(3)}%`,
      `${row.mean.toFixed(3)}%`,
      row.sample_note,
    ];
    values.forEach((value) => addText(tr, 'td', '', String(value)));
    body.append(tr);
  });
  table.append(body);
  wrapper.append(table);
  panel.append(wrapper);
  return panel;
}

function renderPerformance(data) {
  const container = document.querySelector('#performance-tables');
  container.append(summaryTable('Format performance', data.summaries.format, 'format', 'analysis/tables/format_summary.csv'));
  container.append(summaryTable('Pillar performance', data.summaries.pillar, 'pillar', 'analysis/tables/pillar_summary.csv'));
}

function renderStrategyAndPlan(data) {
  const pillarCounts = data.plan.reduce((counts, item) => {
    counts[item.content_pillar] = (counts[item.content_pillar] || 0) + 1;
    return counts;
  }, {});
  const mix = document.querySelector('#strategy-mix');
  Object.entries(pillarCounts).forEach(([name, count]) => {
    const segment = addText(mix, 'span', '', `${count} ${name}`);
    segment.style.setProperty('--w', `${count / data.plan.length * 100}%`);
  });

  const strategyGrid = document.querySelector('#strategy-cards');
  data.strategy.evidence_linked_changes.forEach((change) => {
    const card = el('article', 'strategy-card');
    addText(card, 'span', 'id', change.evidence);
    addText(card, 'h3', '', change.strategy_change);
    addText(card, 'p', '', change.finding);
    addText(card, 'small', '', change.confidence_or_limitation);
    strategyGrid.append(card);
  });

  const formatCounts = data.plan.reduce((counts, item) => {
    counts[item.format] = (counts[item.format] || 0) + 1;
    return counts;
  }, {});
  document.querySelector('#plan-count-heading').textContent = `${formatCounts.post || 0} posts + ${formatCounts.video || 0} videos from ${data.plan.length} validated items`;
  const planGrid = document.querySelector('#plan-cards');
  data.plan.forEach((item) => {
    const card = el('article', `plan-card ${item.format}`);
    const day = el('div', 'day');
    addText(day, 'span', '', `DAY ${item.day}`);
    addText(day, 'span', '', item.format.toUpperCase());
    card.append(day);
    addText(card, 'h3', '', item.hook);
    addText(card, 'p', '', item.content_idea);
    addText(card, 'span', 'kpi-chip', item.primary_kpi);
    planGrid.append(card);
  });
}

function renderAssets(data) {
  const creatives = document.querySelector('#creative-gallery');
  data.plan.filter((item) => item.format === 'post').forEach((item) => {
    const card = el('article', 'creative-card');
    const image = el('img');
    image.src = `../assets/posts/${item.asset_filename}`;
    image.alt = item.hook;
    card.append(image);
    addText(card, 'div', '', `DAY ${item.day} • ${item.topic}`);
    creatives.append(card);
  });

  const videos = document.querySelector('#video-gallery');
  data.plan.filter((item) => item.format === 'video').forEach((item) => {
    const stem = item.asset_filename.replace(/\.mp4$/, '');
    const card = el('article', 'video-card');
    const video = el('video');
    video.controls = true;
    video.muted = true;
    video.playsInline = true;
    video.preload = 'metadata';
    video.poster = `../assets/video_frames/${stem}_preview.png`;
    const source = el('source');
    source.src = `../assets/videos/${item.asset_filename}`;
    source.type = 'video/mp4';
    video.append(source);
    card.append(video);
    const copy = el('div');
    addText(copy, 'div', 'eyebrow lime', `DAY ${item.day} • VIDEO`);
    addText(copy, 'h3', '', item.hook);
    addText(copy, 'p', '', item.full_proposed_caption);
    addText(copy, 'span', 'badge dark-badge', item.reasoned_target_range);
    card.append(copy);
    videos.append(card);
  });
}

function renderComparison(data) {
  document.querySelector('#after-note').textContent = data.data_lineage.after_note;
  const grid = document.querySelector('#comparison-grid');
  data.before_after.forEach((item) => {
    const card = el('article', 'comparison-card');
    addText(card, 'small', '', item.dimension);
    addText(card, 'span', 'value-kind observed', item.before_kind.toUpperCase());
    addText(card, 'h3', '', item.before);
    addText(card, 'div', 'source-note', item.before_source);
    addText(card, 'div', 'arrow', '↓');
    addText(card, 'span', 'value-kind planned', item.after_kind.toUpperCase());
    addText(card, 'b', '', item.after);
    addText(card, 'div', 'source-note', item.after_source);
    grid.append(card);
  });
}

function render(data) {
  document.querySelector('#run-status').textContent = data.run.status.toUpperCase();
  document.querySelector('#provider').textContent = data.run.provider;
  document.querySelector('#validation-status').textContent = data.validation.status;
  document.querySelector('#lineage-note').textContent = `Source: ${data.data_lineage.raw_source} · ${data.data_lineage.observed_rows} observed rows · calculated by run ${data.data_lineage.calculation_run_id}. Original provenance remains unspecified.`;
  renderKpis(data);
  renderAudit(data);
  renderMetrics(data);
  renderPerformance(data);
  document.querySelector('#diagnosis-text').textContent = data.diagnosis.selected_diagnosis;
  document.querySelector('#diagnosis-caveat').textContent = data.diagnosis.outlier_caveat;
  renderStrategyAndPlan(data);
  renderAssets(data);
  renderComparison(data);
  const trace = document.querySelector('#trace');
  data.trace.slice(-11).forEach((entry) => {
    const row = el('div', 'trace-row');
    addText(row, 'b', '', entry.agent);
    addText(row, 'span', '', entry.decision_summary);
    addText(row, 'span', '', entry.status);
    trace.append(row);
  });
  document.querySelector('#validation-score').textContent = `${data.validation.passed}/${data.validation.passed + data.validation.failed}`;
  document.querySelector('#validation-heading').textContent = data.validation.status === 'PASS' ? 'Production gate passed.' : 'Repair gate active.';
}

loadData().then(render).catch((error) => {
  document.querySelector('#validation-heading').textContent = error.message;
  console.error(error);
});

const sections = [...document.querySelectorAll('main section[id]')];
const links = [...document.querySelectorAll('#nav a')];
const observer = new IntersectionObserver((entries) => entries.forEach((entry) => {
  if (entry.isIntersecting) {
    links.forEach((link) => link.classList.toggle('active', link.getAttribute('href') === `#${entry.target.id}`));
  }
}), { rootMargin: '-20% 0px -65% 0px' });
sections.forEach((section) => observer.observe(section));
