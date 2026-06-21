#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRANS_DIR = ROOT / "research" / "youtube-transcripts"
OUT_SQL = ROOT / "research" / "transcript_inserts.sql"


def load_transcript(path: Path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("# METADATA"):
        raise ValueError(f"Missing metadata header in {path}")
    parts = text.split("# TRANSCRIPT\n", 1)
    if len(parts) != 2:
        raise ValueError(f"Missing transcript section in {path}")
    meta = json.loads(parts[0].split("\n", 1)[1])
    transcript = parts[1].rstrip("\n")
    return meta, transcript


def quote_text(value: str) -> str:
    if value is None:
        return "NULL"
    if "$$" not in value:
        return "$$" + value + "$$"
    tag_index = 0
    while True:
        tag = f"$SQL{tag_index}$"
        if tag not in value:
            return tag + value + tag
        tag_index += 1


def quote_string(value):
    if value is None:
        return "NULL"
    if isinstance(value, str):
        return quote_text(value)
    return quote_text(str(value))


def main():
    rows = []
    for path in sorted(TRANS_DIR.glob("*.txt")):
        meta, transcript = load_transcript(path)
        rows.append({
            "expert": meta.get("expert"),
            "video_id": meta.get("video_id"),
            "source_url": meta.get("source_url"),
            "query": meta.get("query"),
            "fetched_at": meta.get("fetched_at"),
            "transcript": transcript,
            "path": str(path.name),
        })
    with OUT_SQL.open("w", encoding="utf-8") as out:
        out.write("-- Generated INSERT statements for public.transcripts\n")
        out.write("BEGIN;\n")
        out.write("DELETE FROM public.transcripts WHERE video_id IN (\n")
        out.write(",\n".join(quote_string(row["video_id"]) for row in rows))
        out.write("\n);\n")
        for row in rows:
            values = [
                quote_string(row["expert"]),
                quote_string(row["video_id"]),
                quote_string(row["source_url"]),
                quote_string(row["query"]),
                quote_string(row["fetched_at"]),
                quote_string(row["transcript"]),
            ]
            out.write(
                "INSERT INTO public.transcripts (expert, video_id, source_url, query, fetched_at, transcript) VALUES ("
                + ", ".join(values)
                + ");\n"
            )
        out.write("COMMIT;\n")
    print(f"Wrote {OUT_SQL} with {len(rows)} inserts")


if __name__ == "__main__":
    main()
