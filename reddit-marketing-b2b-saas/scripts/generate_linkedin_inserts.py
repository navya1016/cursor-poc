#!/usr/bin/env python3
"""Generate safe SQL INSERT statements for LinkedIn posts to load into Supabase.

This script reads processed LinkedIn post files and generates PostgreSQL INSERT statements
with proper dollar-quoting to safely handle special characters in content.

Usage:
  python scripts/generate_linkedin_inserts.py
"""
import os
import json
import re
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(__file__))
POSTS_DIR = os.path.join(ROOT, "research", "linkedin-posts-formatted")
OUT_FILE = os.path.join(ROOT, "research", "linkedin_posts_inserts.sql")


def load_post(path: Path) -> dict:
    """Load and parse a LinkedIn post file.
    
    Format:
    # METADATA
    { json object }
    
    # POST
    <content>
    """
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by markers
    parts = content.split("# POST\n", 1)
    if len(parts) != 2:
        return None
    
    metadata_block = parts[0].replace("# METADATA\n", "").strip()
    post_content = parts[1].strip()
    
    try:
        metadata = json.loads(metadata_block)
        metadata["content"] = post_content
        return metadata
    except json.JSONDecodeError as e:
        print(f"Error parsing {path.name}: {e}")
        return None


def quote_text(value: str) -> str:
    """Quote text using PostgreSQL dollar-quoting for safe string literals.
    
    Dollar-quoting is safe for any content including quotes, backslashes, etc.
    Format: $$content$$ or $tag$content$tag$ if content contains $$
    """
    if value is None:
        return "NULL"
    
    if not value:
        return "$$$$"
    
    # Check if content contains $$ to avoid conflicts
    if "$$" not in value:
        return f"$${value}$$"
    
    # Use a more specific tag if needed
    tag = "post"
    counter = 0
    while f"${tag}{counter}$" in value:
        counter += 1
    tag = f"{tag}{counter}"
    
    return f"${tag}${value}${tag}$"


def quote_string(value) -> str:
    """Quote a string value, handling NULL."""
    if value is None or value == "":
        return "NULL"
    return f"'{value}'"


def escape_sql_string(value: str) -> str:
    """Escape single quotes in string for standard SQL quoting."""
    if value is None:
        return "NULL"
    return f"'{value.replace(chr(39), chr(39)+chr(39))}'"


def main():
    """Generate SQL INSERT statements from LinkedIn post files."""
    if not os.path.exists(POSTS_DIR):
        print(f"Formatted posts directory not found: {POSTS_DIR}")
        print(f"Run fetch_linkedin_posts.py first")
        return
    
    # Find all formatted post files
    post_files = list(Path(POSTS_DIR).glob("*.txt"))
    
    if not post_files:
        print(f"No post files found in {POSTS_DIR}")
        return
    
    print(f"Found {len(post_files)} formatted LinkedIn posts")
    
    # Load all posts
    posts = []
    for post_file in sorted(post_files):
        post = load_post(post_file)
        if post:
            posts.append(post)
        else:
            print(f"Warning: Could not parse {post_file.name}")
    
    if not posts:
        print("No posts to insert")
        return
    
    # Generate SQL
    sql_lines = [
        "-- LinkedIn posts ingestion",
        "-- Generated from formatted post files",
        "",
        "BEGIN;",
        "",
        "DELETE FROM public.linkedin_posts;",
        "",
    ]
    
    for i, post in enumerate(posts, 1):
        author = post.get("author", "Unknown")
        post_id = post.get("post_id")
        source_url = post.get("source_url")
        date_published = post.get("date_published")
        topic = post.get("topic")
        content = post.get("content", "")
        
        # Build INSERT statement with dollar-quoting for content
        insert = f"INSERT INTO public.linkedin_posts (author, post_id, source_url, date_published, topic, content, collected_at) VALUES ("
        
        # Add quoted values
        values = [
            escape_sql_string(author),
            quote_string(post_id),
            quote_string(source_url),
            quote_string(date_published),
            quote_string(topic),
            quote_text(content),  # Use dollar-quoting for large content
            "NOW()",
        ]
        
        insert += ", ".join(values) + ");"
        sql_lines.append(insert)
        
        if i < len(posts):
            sql_lines.append("")
    
    sql_lines.extend(["", "COMMIT;", ""])
    
    # Write SQL file
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(sql_lines))
    
    print(f"Wrote {len(posts)} inserts to: {OUT_FILE}")
    print(f"Run with: psql -U postgres -d postgres -f {OUT_FILE}")


if __name__ == "__main__":
    main()
