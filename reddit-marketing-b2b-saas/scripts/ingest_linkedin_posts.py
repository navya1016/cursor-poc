#!/usr/bin/env python3
"""Load LinkedIn posts from formatted files directly into Supabase.

This script:
1. Reads formatted LinkedIn post files
2. Parses metadata and content
3. Ingests data directly into Supabase via the Python client

Usage:
  python scripts/ingest_linkedin_posts.py

Requires SUPABASE_URL and SUPABASE_KEY environment variables.
"""
import os
import json
from pathlib import Path
from datetime import datetime

# Try to import supabase client
try:
    from supabase import create_client, Client
except ImportError:
    print("Error: supabase package not installed. Install with: pip install supabase")
    exit(1)

ROOT = os.path.dirname(os.path.dirname(__file__))
POSTS_DIR = os.path.join(ROOT, "research", "linkedin-posts-formatted")


def get_supabase_client() -> Client:
    """Create and return a Supabase client."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_KEY environment variables must be set\n"
            "Set them with:\n"
            "  export SUPABASE_URL='https://your-project.supabase.co'\n"
            "  export SUPABASE_KEY='your-anon-key'"
        )
    
    return create_client(url, key)


def load_post(path: Path) -> dict:
    """Load and parse a LinkedIn post file."""
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


def main():
    """Ingest LinkedIn posts into Supabase."""
    if not os.path.exists(POSTS_DIR):
        print(f"Formatted posts directory not found: {POSTS_DIR}")
        print(f"Run fetch_linkedin_posts.py first to format posts")
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
        print("No posts to ingest")
        return
    
    # Connect to Supabase
    print("Connecting to Supabase...")
    try:
        supabase = get_supabase_client()
    except ValueError as e:
        print(f"Error: {e}")
        return
    
    # Clear existing posts
    print("Clearing existing LinkedIn posts...")
    try:
        supabase.table("linkedin_posts").delete().eq("id", -1).execute()
    except:
        pass  # Delete all by clearing (method depends on supabase version)
    
    # Ingest posts
    print(f"Ingesting {len(posts)} posts...")
    inserted = 0
    
    for post in posts:
        try:
            row = {
                "author": post.get("author"),
                "post_id": post.get("post_id"),
                "source_url": post.get("source_url"),
                "date_published": post.get("date_published"),
                "topic": post.get("topic"),
                "content": post.get("content"),
                "collected_at": post.get("collected_at"),
            }
            
            # Insert into Supabase
            supabase.table("linkedin_posts").insert(row).execute()
            inserted += 1
            print(f"  ✓ Inserted: {post.get('author')} - {post.get('topic', 'Untitled')}")
        except Exception as e:
            print(f"  ✗ Error inserting post: {e}")
    
    print(f"\nSuccessfully ingested {inserted}/{len(posts)} LinkedIn posts")
    
    # Verify count
    try:
        result = supabase.table("linkedin_posts").select("COUNT(*)", count="exact").execute()
        count = result.count
        print(f"Total posts in Supabase: {count}")
    except Exception as e:
        print(f"Could not verify count: {e}")


if __name__ == "__main__":
    main()
