#!/usr/bin/env python3
"""Search YouTube for a query, extract the top video id, and fetch transcript.

This is a lightweight scraper that hits the public YouTube search page and
parses `videoId` occurrences from the initial data. It's not robust but works
for quick collection when no API key is available.
"""
import requests
import re
import time
import json
import os
from youtube_transcript_api import YouTubeTranscriptApi

ROOT = os.path.dirname(os.path.dirname(__file__))
OUT_DIR = os.path.join(ROOT, "research", "youtube-transcripts")
os.makedirs(OUT_DIR, exist_ok=True)


def search_top_video_id(query):
    url = "https://www.youtube.com/results"
    r = requests.get(url, params={"search_query": query}, timeout=15)
    text = r.text
    m = re.search(r'"videoId":"([A-Za-z0-9_-]{11})"', text)
    if m:
        return m.group(1)
    return None


def fetch_transcript_for_query(expert, query):
    vid = search_top_video_id(query)
    if not vid:
        print(f"No video id found for {query}")
        return
    # use instance API for youtube_transcript_api
    api = YouTubeTranscriptApi()
    transcript = None
    try:
        transcript = api.fetch(vid)
    except Exception:
        try:
            tlist = api.list(vid)
            transcript = tlist.find_transcript(["en"]).fetch()
        except Exception as e:
            print(f"Transcript fetch failed for {vid}: {e}")
            return
    parts = []
    for seg in transcript:
        if isinstance(seg, dict):
            parts.append(seg.get("text", ""))
        else:
            parts.append(getattr(seg, "text", str(seg)))
    text = "\n".join(parts)
    fname = f"{expert.replace(' ', '_')}-{vid}.txt"
    path = os.path.join(OUT_DIR, fname)
    meta = {"expert": expert, "video_id": vid, "query": query}
    with open(path, "w", encoding="utf-8") as f:
        f.write("# METADATA\n")
        f.write(json.dumps(meta, ensure_ascii=False, indent=2))
        f.write("\n\n# TRANSCRIPT\n")
        f.write(text)
    print(f"Saved transcript for {expert} -> {path}")


def main():
    # minimal mapping of expert -> search query (tune as needed)
    mapping = {
        "Jason Lemkin": "Jason Lemkin SaaStr interview",
        "Hiten Shah": "Hiten Shah interview",
        "Nathan Latka": "Nathan Latka podcast",
        "Rand Fishkin": "Rand Fishkin talk",
        "Brian Dean": "Brian Dean YouTube SEO",
        "Tim Schmoyer": "Tim Schmoyer YouTube strategy",
        "Roberto Blake": "Roberto Blake YouTube growth",
        "Andrew Chen": "Andrew Chen growth talk",
        "Noah Kagan": "Noah Kagan marketing",
        "Justin Jackson": "Justin Jackson SaaS podcast",
    }
    for expert, query in mapping.items():
        fetch_transcript_for_query(expert, query)
        time.sleep(3)


if __name__ == "__main__":
    main()
