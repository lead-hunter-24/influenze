// YT Insights — frontend logic
const fmt = (n) => n >= 1e6 ? (n / 1e6).toFixed(1) + "M" : n >= 1e3 ? Math.round(n / 1e3) + "K" : Math.round(n);
const $ = (id) => document.getElementById(id);
let charts = {};
let current = null;

const SUGGESTIONS = [
  "Which video has the best momentum right now, and why?",
  "What topic should this channel make more of?",
  "Which videos are hidden gems — high engagement but low reach?",
  "Summarize this channel's strategy in 3 bullets.",
];

async function init() {
  const channels = await fetch("/api/channels").then((r) => r.json());
  const sel = $("channelSelect");
  sel.innerHTML = channels
    .map((c) => `<option value="${c.slug}">${c.title} — ${fmt(c.subscribers)} subs</option>`)
    .join("");
  sel.addEventListener("change", () => loadChannel(sel.value));
  if (channels.length) loadChannel(channels[0].slug);

  $("askForm").addEventListener("submit", onAsk);
  $("suggestions").innerHTML = SUGGESTIONS.map((s) => `<span class="chip">${s}</span>`).join("");
  $("suggestions").querySelectorAll(".chip").forEach((c) =>
    c.addEventListener("click", () => { $("askInput").value = c.textContent; onAsk(new Event("x")); })
  );
}

async function loadChannel(slug) {
  const ch = await fetch(`/api/channels/${slug}`).then((r) => r.json());
  current = ch;
  renderHead(ch);
  renderCards(ch);
  renderCharts(ch);
  renderTable(ch);
  $("answer").classList.add("hidden");
}

function renderHead(ch) {
  $("chTitle").textContent = ch.title;
  $("chAvatar").textContent = (ch.title[0] || "?").toUpperCase();
  $("chMeta").textContent =
    `${ch.handle} · created ${ch.createdAt} (${ch.channelAgeDays} days old) · snapshot ${ch.capturedAt}`;
  const a = ch.aggregates;
  $("chChips").innerHTML = [
    `topics: <b>${ch.topics.join(", ")}</b>`,
    `<b>${ch.uploadsPerMonth}</b> uploads/mo`,
    `top topic: <b>${a.topicAggregates[0].topic}</b>`,
  ].map((t) => `<span class="chip-stat">${t}</span>`).join("");
  $("chLink").href = `https://www.youtube.com/channel/${ch.channelId}`;
}

function renderCards(ch) {
  const a = ch.aggregates;
  const cards = [
    ["Subscribers", fmt(ch.subscribers), `+${fmt(ch.subsGained30d)} / 30d`],
    ["Total views", fmt(ch.totalViews), `+${fmt(ch.viewsGained30d)} / 30d`],
    ["Videos", ch.totalVideos, `${ch.uploadsPerMonth}/month`],
    ["Avg views / video", fmt(ch.avgViewsPerVideo), ""],
    ["Views / subscriber", ch.viewsPerSubscriber, ""],
    ["Median views", fmt(a.medianViews), ""],
    ["Median engagement", a.medianEngagement + "%", ""],
    ["Top-3 view share", a.top3ViewSharePct + "%", "concentration"],
  ];
  $("cards").innerHTML = cards
    .map(([l, v, s]) => `<div class="card"><div class="label">${l}</div><div class="value">${v}</div>${s ? `<div class="sub">${s}</div>` : ""}</div>`)
    .join("");
}

const C = { grid: "rgba(17,24,39,.08)", tick: "#6b7280", coral: "#dc2626", green: "#059669", purple: "#7c3aed" };
Chart.defaults.color = C.tick;
Chart.defaults.font.family = "system-ui, sans-serif";

function destroyCharts() { Object.values(charts).forEach((c) => c.destroy()); charts = {}; }

function renderCharts(ch) {
  destroyCharts();
  const recent = (v) => v.ageDays <= 60;

  const vpd = ch.videos.slice().sort((a, b) => b.viewsPerDay - a.viewsPerDay);
  charts.vpd = new Chart($("vpdChart"), {
    type: "bar",
    data: { labels: vpd.map((v) => short(v.title)), datasets: [{ data: vpd.map((v) => v.viewsPerDay), backgroundColor: vpd.map((v) => recent(v) ? C.coral : "#6b7280"), borderRadius: 3 }] },
    options: barOpts((v, i) => `${fmt(v)} views/day · ${vpd[i].ageDays}d old`),
  });

  const eng = ch.videos.slice().sort((a, b) => b.engagementRate - a.engagementRate);
  charts.eng = new Chart($("engChart"), {
    type: "bar",
    data: { labels: eng.map((v) => short(v.title)), datasets: [{ data: eng.map((v) => v.engagementRate), backgroundColor: C.green, borderRadius: 3 }] },
    options: barOpts((v) => `${v}% engagement`, "%"),
  });

  const t = ch.aggregates.topicAggregates;
  charts.topic = new Chart($("topicChart"), {
    type: "bar",
    data: { labels: t.map((x) => `${x.topic} (${x.count})`), datasets: [{ data: t.map((x) => x.avgViews), backgroundColor: C.purple, borderRadius: 3 }] },
    options: barOpts((v) => `${fmt(v)} avg views/video`),
  });

  charts.scatter = new Chart($("scatterChart"), {
    type: "scatter",
    data: { datasets: [{ data: ch.videos.map((v) => ({ x: v.durationMin, y: v.views, t: v.title })), backgroundColor: C.purple, pointRadius: 6, pointHoverRadius: 8 }] },
    options: {
      responsive: true, maintainAspectRatio: false, layout: { padding: 8 },
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => `${c.raw.t} — ${c.raw.x}min, ${fmt(c.raw.y)} views` } } },
      scales: { x: { title: { display: true, text: "Length (min)" }, grid: { color: C.grid } }, y: { title: { display: true, text: "Views" }, grid: { color: C.grid }, ticks: { callback: fmt } } },
    },
  });
}

function barOpts(labelFn, suffix = "") {
  return {
    indexAxis: "y", responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => labelFn(c.parsed.x, c.dataIndex) } } },
    scales: { x: { grid: { color: C.grid }, ticks: { callback: (v) => suffix ? v + suffix : fmt(v) } }, y: { grid: { display: false }, ticks: { font: { size: 11 } } } },
  };
}

const short = (t) => (t.length > 38 ? t.slice(0, 36) + "…" : t);

function renderTable(ch) {
  const rows = ch.videos.slice().sort((a, b) => b.views - a.views);
  const vc = $("videoCount"); if (vc) vc.textContent = `${rows.length} videos`;
  $("videoTable").querySelector("tbody").innerHTML = rows
    .map((v) => `<tr>
      <td>${v.title}</td><td>${v.publishedAt}</td><td>${v.topic}</td>
      <td class="num">${v.durationMin}m</td><td class="num">${v.views.toLocaleString()}</td>
      <td class="num">${v.viewsPerDay.toLocaleString()}</td><td class="num">${v.engagementRate}%</td>
      <td class="num">${v.outlierMultiple}×</td></tr>`)
    .join("");
}

async function onAsk(e) {
  e.preventDefault();
  const q = $("askInput").value.trim();
  if (!q || !current) return;
  const out = $("answer");
  const btn = $("askBtn");
  btn.disabled = true;
  out.classList.remove("hidden", "err");
  out.innerHTML = `<span class="spinner"></span>Haiku is reading ${current.title}'s data…`;
  try {
    const res = await fetch("/api/ask", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ slug: current.slug, question: q }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "request failed");
    const u = data.usage ? `<div class="usage">Haiku · ${data.usage.input_tokens} in / ${data.usage.output_tokens} out tokens</div>` : "";
    out.innerHTML = mdLite(data.answer) + u;
  } catch (err) {
    out.classList.add("err");
    out.textContent = "⚠ " + err.message;
  } finally {
    btn.disabled = false;
  }
}

// minimal markdown: **bold**, bullets, line breaks
function mdLite(s) {
  return s
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/^[-*]\s+(.*)$/gm, "• $1")
    .replace(/\n/g, "<br>");
}

init();
