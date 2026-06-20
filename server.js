// YT Insights — Express server
// Serves the dashboard + exposes two APIs:
//   GET  /api/channels            -> list of available channels
//   GET  /api/channels/:slug      -> full universal-schema data for one channel
//   POST /api/ask {slug, question}-> natural-language insight from Claude Haiku
import express from "express";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import Anthropic from "@anthropic-ai/sdk";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DATA = path.join(__dirname, "data");
const PORT = process.env.PORT || 3000;

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

const readJSON = (p) => JSON.parse(fs.readFileSync(p, "utf-8"));

// --- Data APIs ---
app.get("/api/channels", (_req, res) => {
  res.json(readJSON(path.join(DATA, "index.json")));
});

app.get("/api/channels/:slug", (req, res) => {
  const slug = req.params.slug.replace(/[^a-z0-9_]/gi, ""); // sanitize
  const file = path.join(DATA, "channels", `${slug}.json`);
  if (!fs.existsSync(file)) return res.status(404).json({ error: "channel not found" });
  res.json(readJSON(file));
});

// --- Claude Haiku insight API ---
const anthropic = new Anthropic(); // reads ANTHROPIC_API_KEY from env

// Build a compact, token-efficient context block from the channel data.
function buildContext(ch) {
  const a = ch.aggregates;
  const lines = ch.videos
    .slice()
    .sort((x, y) => y.views - x.views)
    .map(
      (v) =>
        `- "${v.title}" | published ${v.publishedAt} (${v.ageDays}d old) | ${v.topic} | ${v.durationMin}min | ` +
        `${v.views.toLocaleString()} views | ${v.likes.toLocaleString()} likes | ${v.comments} comments | ` +
        `eng ${v.engagementRate}% | ${v.viewsPerDay.toLocaleString()} views/day | ${v.outlierMultiple}x median`
    )
    .join("\n");
  const topics = a.topicAggregates
    .map((t) => `${t.topic}: ${t.count} videos, avg ${t.avgViews.toLocaleString()} views`)
    .join("; ");
  return `CHANNEL: ${ch.title} (${ch.handle})
Created ${ch.createdAt} (${ch.channelAgeDays} days old). Topics: ${ch.topics.join(", ")}.
Subscribers: ${ch.subscribers.toLocaleString()} | Total views: ${ch.totalViews.toLocaleString()} | Videos: ${ch.totalVideos}
Avg views/video: ${ch.avgViewsPerVideo.toLocaleString()} | Views per subscriber: ${ch.viewsPerSubscriber} | Uploads/month: ${ch.uploadsPerMonth}
Last 30 days: +${ch.subsGained30d.toLocaleString()} subs, +${ch.viewsGained30d.toLocaleString()} views, ${ch.videosPublished30d} new videos
Median views: ${a.medianViews.toLocaleString()} | Median engagement: ${a.medianEngagement}% | Median views/day: ${a.medianViewsPerDay.toLocaleString()}
Top-3 videos = ${a.top3ViewSharePct}% of all views.
Topic performance (avg views/video): ${topics}
Data captured: ${ch.capturedAt}

ALL VIDEOS (sorted by views):
${lines}`;
}

const SYSTEM = `You are a YouTube channel analytics expert. You answer questions about a single channel using ONLY the data provided in the user's message. Be concrete and quantitative: cite real numbers, video titles, and dates from the data. Lead with the answer, then 2-4 supporting points. Use views/day to compare videos of different ages fairly, and engagement rate to compare audience reaction independent of reach. If the data does not contain something asked, say so plainly. Keep responses under ~180 words and use short markdown bullets where helpful. Never invent numbers.`;

app.post("/api/ask", async (req, res) => {
  try {
    const { slug, question } = req.body || {};
    if (!slug || !question) return res.status(400).json({ error: "slug and question are required" });
    if (!process.env.ANTHROPIC_API_KEY)
      return res.status(401).json({ error: "ANTHROPIC_API_KEY is not set. Copy .env.example to .env, add your key, and restart." });
    const file = path.join(DATA, "channels", `${String(slug).replace(/[^a-z0-9_]/gi, "")}.json`);
    if (!fs.existsSync(file)) return res.status(404).json({ error: "channel not found" });

    const ch = readJSON(file);
    const context = buildContext(ch);

    const message = await anthropic.messages.create({
      model: "claude-haiku-4-5",
      max_tokens: 700,
      system: SYSTEM,
      messages: [
        { role: "user", content: `${context}\n\n---\nQUESTION: ${question}` },
      ],
    });

    const text = message.content.filter((b) => b.type === "text").map((b) => b.text).join("");
    res.json({ answer: text, usage: message.usage });
  } catch (err) {
    if (err instanceof Anthropic.AuthenticationError)
      return res.status(401).json({ error: "Invalid or missing ANTHROPIC_API_KEY. Set it in .env" });
    if (err instanceof Anthropic.RateLimitError)
      return res.status(429).json({ error: "Rate limited — try again in a moment." });
    console.error(err);
    res.status(500).json({ error: err.message || "insight generation failed" });
  }
});

app.listen(PORT, () => {
  console.log(`\n  YT Insights running →  http://localhost:${PORT}\n`);
  if (!process.env.ANTHROPIC_API_KEY)
    console.log("  ⚠  ANTHROPIC_API_KEY not set — the Ask-AI box will return 401 until you add it to .env\n");
});
