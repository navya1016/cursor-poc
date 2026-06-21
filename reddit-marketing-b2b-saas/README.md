# YouTube Content Strategy for B2B SaaS

## Objective
Research how top creators and practitioners use YouTube to grow B2B SaaS brands and build a reproducible content pipeline.

## Why This Topic
YouTube is a high-leverage channel for B2B SaaS when used to educate buyers, showcase product value, and scale creator-led marketing.

## Chosen Experts (sample — full list in `research/sources.md`)
1. Jason Lemkin (SaaStr) — SaaS founder/VC, talks growth and scaling
2. Hiten Shah — SaaS product and growth practitioner
3. Nathan Latka — SaaS interviews and monetization
4. Rand Fishkin — audience-driven marketing and content strategy
5. Brian Dean — video SEO and content promotion
6. Tim Schmoyer — YouTube growth strategy for creators
7. Roberto Blake — video growth and creator monetization
8. Andrew Chen — growth at startups, YouTube appearances
9. Noah Kagan — product marketing and content experiments
10. Justin Jackson — indie SaaS and content-first growth

## Materials to Collect
- YouTube transcripts (via API / transcript libraries)
- LinkedIn posts and threads from the same experts (manual or scraped)
- Other resources (podcasts, blog posts, talks)

## Outcome
This repository will hold collected materials and scripts to fetch, ingest, and analyze transcripts and posts to enable building a YouTube content playbook.

## Structure
- `research/`
  - `sources.md` — experts, links, annotations
  - `linkedin-posts/` — posts organized by author
  - `youtube-transcripts/` — transcripts organized by video
  - `other/` — additional materials
  - `analysis/`
- `scripts/` — collection and ingestion helpers
- `requirements.txt` — Python dependencies for collection and ingestion

## Notes
Scripts use `youtube-transcript-api` and `duckdb` locally. Optional Supabase integration is available via environment variables (`SUPABASE_URL`, `SUPABASE_KEY`).
