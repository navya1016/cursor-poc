#!/usr/bin/env python3
"""Fetch YouTube transcripts for a list of videos and save to research/youtube-transcripts.

Usage:
  python scripts/fetch_youtube_transcripts.py --sources-file research/sources_videos.json

The `sources_videos.json` should be a JSON map of expert -> list of video URLs.
"""
import os
import re
import json
from datetime import datetime

from youtube_transcript_api import YouTubeTranscriptApi

ROOT = os.path.dirname(os.path.dirname(__file__))
OUT_DIR = os.path.join(ROOT, "research", "youtube-transcripts")
os.makedirs(OUT_DIR, exist_ok=True)


def video_id_from_url(url):
    m = re.search(r"v=([A-Za-z0-9_-]{11})", url)
    if m:
        return m.group(1)
    m = re.search(r"youtu\.be/([A-Za-z0-9_-]{11})", url)
    if m:
        return m.group(1)
    return None


def fetch_and_save(expert, url):
    vid = video_id_from_url(url)
    if not vid:
        print(f"Skipping invalid URL: {url}")
        return
    # use instance API (supports modern package versions)
    api = YouTubeTranscriptApi()
    transcript = None
    try:
        transcript = api.fetch(vid)
    except Exception:
        try:
            tlist = api.list(vid)
            transcript = tlist.find_transcript(["en"]).fetch()
        except Exception as e:
            print(f"Could not fetch transcript for {vid}: {e}")
            return
    # join text
    text = "\n".join([seg.get("text", "") for seg in transcript])
    fname = f"{expert.replace(' ', '_')}-{vid}.txt"
    path = os.path.join(OUT_DIR, fname)
    meta = {
        "expert": expert,
        "video_id": vid,
        "source_url": url,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
    }
    parts = []
    for seg in transcript:
        if isinstance(seg, dict):
            parts.append(seg.get("text", ""))
        else:
            parts.append(getattr(seg, "text", str(seg)))
    text = "\n".join(parts)
    with open(path, "w", encoding="utf-8") as f:
        f.write("# METADATA\n")
        f.write(json.dumps(meta, ensure_ascii=False, indent=2))
        f.write("\n\n# TRANSCRIPT\n")
        f.write(text)
    print(f"Wrote transcript: {path}")


def main():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--sources-file", default="research/sources_videos.json")
    args = p.parse_args()

    if not os.path.exists(args.sources_file):
        print(f"Sources file not found: {args.sources_file}")
        return
    with open(args.sources_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    for expert, urls in data.items():
        for url in urls:
            fetch_and_save(expert, url)


if __name__ == "__main__":
    main()
