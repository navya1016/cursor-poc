#!/usr/bin/env python3
"""Ingest transcripts from research/youtube-transcripts into DuckDB and optionally Supabase.

Usage:
  python scripts/ingest_duckdb_supabase.py

Requires: `duckdb` and `supabase` (optional).
Set SUPABASE_URL and SUPABASE_KEY env vars to enable Supabase upload.
"""
import os
import json
import duckdb
from glob import glob

ROOT = os.path.dirname(os.path.dirname(__file__))
TRANS_DIR = os.path.join(ROOT, "research", "youtube-transcripts")
DB_PATH = os.path.join(ROOT, "research", "data.db")


def parse_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if content.startswith("# METADATA"):
        parts = content.split("# TRANSCRIPT\n", 1)
        meta = json.loads(parts[0].split("\n", 1)[1])
        transcript = parts[1].strip() if len(parts) > 1 else ""
        return meta, transcript
    else:
        return None, content


def ingest_to_duckdb():
    con = duckdb.connect(DB_PATH)
    con.execute("CREATE TABLE IF NOT EXISTS transcripts (expert TEXT, video_id TEXT, source_url TEXT, fetched_at TEXT, transcript TEXT);")
    files = glob(os.path.join(TRANS_DIR, "*.txt"))
    for p in files:
        meta, transcript = parse_file(p)
        if meta is None:
            continue
        con.execute("INSERT INTO transcripts VALUES (?, ?, ?, ?, ?)", [meta.get("expert"), meta.get("video_id"), meta.get("source_url"), meta.get("fetched_at"), transcript])
        print(f"Inserted {p} into DuckDB")
    con.close()


def main():
    ingest_to_duckdb()
    # Optional Supabase push
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if supabase_url and supabase_key:
        try:
            from supabase import create_client
            url = supabase_url
            key = supabase_key
            supa = create_client(url, key)
            # create table if needed (requires SQL via Supabase SQL API or via pg client). We'll attempt a simple insert to a table named 'transcripts'
            con = duckdb.connect(DB_PATH)
            rows = con.execute("SELECT expert, video_id, source_url, fetched_at, transcript FROM transcripts").fetchall()
            for r in rows:
                record = {"expert": r[0], "video_id": r[1], "source_url": r[2], "fetched_at": r[3], "transcript": r[4]}
                supa.table("transcripts").insert(record).execute()
            print("Uploaded transcripts to Supabase (table: transcripts)")
        except Exception as e:
            print("Supabase upload failed or package missing:", e)


if __name__ == "__main__":
    main()
