#!/usr/bin/env python3
"""Direct LinkedIn post processor - inline implementation."""
import os
import json
import re
from pathlib import Path
from datetime import datetime

ROOT = r"c:\Users\91630\Downloads\git\cursor-poc\reddit-marketing-b2b-saas"
POSTS_DIR = os.path.join(ROOT, "research", "linkedin-posts")
FORMATTED_DIR = os.path.join(ROOT, "research", "linkedin-posts-formatted")
OUT_FILE = os.path.join(ROOT, "research", "linkedin_posts_inserts.sql")

os.makedirs(FORMATTED_DIR, exist_ok=True)

print(f"Processing LinkedIn posts from: {POSTS_DIR}")
print(f"Output directory: {FORMATTED_DIR}")

# Process each LinkedIn markdown file
md_files = sorted(Path(POSTS_DIR).glob("*.md"))
md_files = [f for f in md_files if f.name != "README.md"]

print(f"Found {len(md_files)} markdown files\n")

formatted_posts = []

for md_file in md_files:
    print(f"Processing: {md_file.name}")
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract metadata
    source_url = None
    date_published = None
    topic = None
    post_id = None
    
    # Extract URL
    url_match = re.search(r'URL:\s*(https://[^\s\n]+)', content)
    if url_match:
        source_url = url_match.group(1)
        # Extract post_id
        post_match = re.search(r'/posts/([^/?]+)', source_url)
        if post_match:
            post_id = post_match.group(1)
    
    # Extract Date
    date_match = re.search(r'Date:\s*(\d{4}-\d{2}-\d{2})', content)
    if date_match:
        date_published = date_match.group(1)
    
    # Extract Topic
    topic_match = re.search(r'Topic:\s*([^\n]+)', content)
    if topic_match:
        topic = topic_match.group(1).strip()
    
    # Extract content (everything after "## Key insights" or "## Notes")
    content_lines = []
    lines = content.split('\n')
    in_content = False
    
    for line in lines:
        if line.startswith('##'):
            in_content = True
            continue
        if in_content and line.strip():
            content_lines.append(line)
    
    post_content = '\n'.join(content_lines).strip()
    
    if not post_content or len(post_content) < 20:
        print(f"  ⚠ Skipped: minimal content\n")
        continue
    
    # Create metadata
    author = md_file.stem.replace('-', ' ').title()
    post_metadata = {
        "author": author,
        "post_id": post_id,
        "source_url": source_url,
        "date_published": date_published,
        "topic": topic,
        "collected_at": datetime.utcnow().isoformat() + "Z",
    }
    
    # Write formatted file
    safe_author = author.lower().replace(' ', '_')
    post_id_safe = post_id if post_id else md_file.stem
    out_filename = f"{safe_author}_{post_id_safe}.txt"
    out_path = os.path.join(FORMATTED_DIR, out_filename)
    
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("# METADATA\n")
        f.write(json.dumps(post_metadata, ensure_ascii=False, indent=2))
        f.write("\n\n# POST\n")
        f.write(post_content)
    
    formatted_posts.append(post_metadata)
    print(f"  ✓ Created: {out_filename}\n")

print(f"\nFormatted {len(formatted_posts)} posts\n")

# Now generate SQL inserts
print("=" * 60)
print("Generating SQL INSERT statements...")
print("=" * 60)

def escape_sql_string(value):
    """Escape single quotes in string for SQL."""
    if value is None or value == "":
        return "NULL"
    return f"'{value.replace(chr(39), chr(39)+chr(39))}'"

def quote_text(value):
    """Quote text using PostgreSQL dollar-quoting."""
    if value is None or value == "":
        return "$$$$"
    if "$$" not in value:
        return f"$${value}$$"
    tag = "post"
    counter = 0
    while f"${tag}{counter}$" in value:
        counter += 1
    tag = f"{tag}{counter}"
    return f"${tag}${value}${tag}$"

def quote_string(value):
    """Quote a string value, handling NULL."""
    if value is None or value == "":
        return "NULL"
    return f"'{value}'"

# Load all formatted posts
formatted_posts = []
for post_file in Path(FORMATTED_DIR).glob("*.txt"):
    with open(post_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    parts = content.split("# POST\n", 1)
    if len(parts) == 2:
        metadata_block = parts[0].replace("# METADATA\n", "").strip()
        post_content = parts[1].strip()
        try:
            metadata = json.loads(metadata_block)
            metadata["content"] = post_content
            formatted_posts.append(metadata)
        except json.JSONDecodeError as e:
            print(f"Error parsing {post_file.name}: {e}")

print(f"Loaded {len(formatted_posts)} formatted posts\n")

# Generate SQL
sql_lines = [
    "-- LinkedIn posts ingestion",
    "-- Generated from formatted post files",
    "",
    "BEGIN;",
    "",
    "DELETE FROM public.linkedin_posts WHERE id > 0;",
    "",
]

for i, post in enumerate(formatted_posts, 1):
    author = post.get("author", "Unknown")
    post_id = post.get("post_id")
    source_url = post.get("source_url")
    date_published = post.get("date_published")
    topic = post.get("topic")
    content = post.get("content", "")
    
    # Build INSERT statement
    insert = f"INSERT INTO public.linkedin_posts (author, post_id, source_url, date_published, topic, content, collected_at) VALUES ("
    
    # Add quoted values
    values = [
        escape_sql_string(author),
        quote_string(post_id),
        quote_string(source_url),
        quote_string(date_published),
        quote_string(topic),
        quote_text(content),
        "NOW()",
    ]
    
    insert += ", ".join(values) + ");"
    sql_lines.append(insert)
    
    if i < len(formatted_posts):
        sql_lines.append("")

sql_lines.extend(["", "COMMIT;", ""])

# Write SQL file
with open(OUT_FILE, 'w', encoding='utf-8') as f:
    f.write("\n".join(sql_lines))

print(f"✓ Generated SQL with {len(formatted_posts)} inserts")
print(f"  File: {OUT_FILE}")
print(f"  Size: {len(sql_lines)} lines\n")

# Show first few lines
print("First 20 lines of generated SQL:")
print("\n".join(sql_lines[:20]))
