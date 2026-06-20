# YT Insights

Open a webpage, **pick any YouTube channel**, see its full statistics and charts, and **ask Claude Haiku questions** about it in plain English. Haiku reads the selected channel's data and answers with real numbers.

## What's inside

```
yt-insights/
  server.js                 Express server: serves the page + 3 APIs
  generate_channel_data.py  Builds the universal-schema JSON from raw data
  data/
    index.json              List of available channels
    channels/<slug>.json    One universal-schema file per channel
  public/
    index.html  app.js  styles.css   The dashboard (channel picker, charts, Ask-AI box)
  .env.example              Copy to .env and add your Anthropic API key
```

## The universal variables (work for ANY channel)

**Channel:** subscribers, total views, videos, channel age, topics, avg views/video,
views/subscriber, uploads/month, 30-day subs/views/video growth.
**Per video:** views, likes, comments, engagement rate, like rate, comment rate,
**views/day** (age-normalized momentum), **outlier multiple** (views ÷ channel median),
duration, title word-count, topic.
**Aggregates:** median views, median engagement, top-3 view share, per-topic avg views.

These are what the charts plot and what Haiku reasons over.

## Run it

```bash
cd yt-insights
npm install
cp .env.example .env          # then edit .env and paste your ANTHROPIC_API_KEY
npm start                     # → http://localhost:3000
```

Open http://localhost:3000, pick a channel from the dropdown, and use the **Ask the data** box.

> Get an API key at https://console.anthropic.com/settings/keys
> The stats and charts work with **no** key — only the Ask-AI box needs one.

## APIs

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/channels` | List channels in the dropdown |
| GET | `/api/channels/:slug` | Full universal-schema data for one channel |
| POST | `/api/ask` | `{slug, question}` → natural-language insight from Claude Haiku |

The AI call is a single Messages API request to **`claude-haiku-4-5`**: the channel's
stats are packed into the system/user context and Haiku answers the question. It is
instructed to use only the supplied data and never invent numbers.

## Add another channel

1. Pull the channel + video data (e.g. via vidiq) and add it to `RAW_CHANNELS` in
   `generate_channel_data.py` (same shape as `crayon_capital`).
2. `python generate_channel_data.py` — regenerates the JSON and `index.json`.
3. Refresh the page; the new channel appears in the dropdown automatically.

## Deploy

It's a standard Node app. Set `ANTHROPIC_API_KEY` (and optional `PORT`) in the host's
environment and run `node server.js`. Works on any Node 18+ host (Render, Railway,
Fly, a VPS, etc.). Keep `.env` out of git (already in `.gitignore`).
