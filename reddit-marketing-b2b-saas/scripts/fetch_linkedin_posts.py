#!/usr/bin/env python3
"""Format and organize LinkedIn posts from markdown files into structured format.

This script reads markdown files from research/linkedin-posts/ and reformats them
with metadata into a consistent structure similar to YouTube transcripts.

Usage:
  python scripts/fetch_linkedin_posts.py
"""
import os
import json
import re
from pathlib import Path
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
POSTS_DIR = os.path.join(ROOT, "research", "linkedin-posts")
OUT_DIR = os.path.join(ROOT, "research", "linkedin-posts-formatted")
os.makedirs(OUT_DIR, exist_ok=True)


def extract_metadata_from_markdown(content: str) -> dict:
    """Extract URL, date, and other metadata from markdown content."""
    metadata = {
        "source_url": None,
        "date_published": None,
        "topic": None,
        "post_id": None,
    }
    
    # Extract URL
    url_match = re.search(r'URL:\s*(https://[^\s\n]+)', content)
    if url_match:
        url = url_match.group(1)
        metadata["source_url"] = url
        # Extract post_id from LinkedIn URL (the part after /posts/)
        post_match = re.search(r'/posts/([^/?]+)', url)
        if post_match:
            metadata["post_id"] = post_match.group(1)
    
    # Extract Date
    date_match = re.search(r'Date:\s*(\d{4}-\d{2}-\d{2})', content)
    if date_match:
        metadata["date_published"] = date_match.group(1)
    
    # Extract Topic
    topic_match = re.search(r'Topic:\s*([^\n]+)', content)
    if topic_match:
        metadata["topic"] = topic_match.group(1).strip()
    
    return metadata


def extract_content(content: str) -> str:
    """Extract the main content, removing metadata lines."""
    lines = content.split('\n')
    content_lines = []
    skip_until_blank = False
    
    for line in lines:
        # Skip header and metadata lines
        if line.startswith('#') or line.startswith('Author:'):
            continue
        if line.startswith('Date:') or line.startswith('URL:') or line.startswith('Topic:'):
            continue
        # Skip "Posts collected:" and similar headers
        if 'placeholder' in line.lower() or 'posts collected' in line.lower():
            skip_until_blank = True
            continue
        if skip_until_blank:
            if line.strip() == '':
                skip_until_blank = False
            continue
        
        content_lines.append(line)
    
    # Join and clean up
    result = '\n'.join(content_lines).strip()
    return result


def process_linkedin_post(filepath: Path, author: str) -> None:
    """Process a single LinkedIn post markdown file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract metadata
    metadata = extract_metadata_from_markdown(content)
    extracted_content = extract_content(content)
    
    # Skip if no real content
    if not extracted_content or len(extracted_content) < 50:
        print(f"Skipping {filepath.name}: minimal content")
        return
    
    # Create output filename
    safe_author = author.lower().replace(' ', '_')
    post_id = metadata["post_id"] or filepath.stem
    out_filename = f"{safe_author}_{post_id}.txt"
    out_path = os.path.join(OUT_DIR, out_filename)
    
    # Prepare metadata JSON
    post_metadata = {
        "author": author,
        "post_id": metadata["post_id"],
        "source_url": metadata["source_url"],
        "date_published": metadata["date_published"],
        "topic": metadata["topic"],
        "collected_at": datetime.utcnow().isoformat() + "Z",
    }
    
    # Write formatted file
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("# METADATA\n")
        f.write(json.dumps(post_metadata, ensure_ascii=False, indent=2))
        f.write("\n\n# POST\n")
        f.write(extracted_content)
    
    print(f"Processed: {filepath.name} -> {out_filename}")


def main():
    """Process all LinkedIn post markdown files."""
    if not os.path.exists(POSTS_DIR):
        print(f"LinkedIn posts directory not found: {POSTS_DIR}")
        return
    
    # Get all markdown files
    md_files = list(Path(POSTS_DIR).glob("*.md"))
    
    if not md_files:
        print(f"No markdown files found in {POSTS_DIR}")
        return
    
    print(f"Found {len(md_files)} LinkedIn post files")
    processed = 0
    
    for md_file in sorted(md_files):
        # Skip README
        if md_file.name == "README.md":
            continue
        
        # Extract author name from filename
        author = md_file.stem.replace('-', ' ').title()
        
        try:
            process_linkedin_post(md_file, author)
            processed += 1
        except Exception as e:
            print(f"Error processing {md_file.name}: {e}")
    
    print(f"\nProcessed {processed} LinkedIn posts")
    print(f"Output: {OUT_DIR}")


if __name__ == "__main__":
    main()
