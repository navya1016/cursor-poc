#!/usr/bin/env python3
"""Wrapper to run LinkedIn post processing and capture output."""
import subprocess
import sys
import os

os.chdir(r"c:\Users\91630\Downloads\git\cursor-poc")

# Step 1: Format posts
print("=" * 60)
print("STEP 1: Formatting LinkedIn posts...")
print("=" * 60)
result1 = subprocess.run(
    [sys.executable, r"reddit-marketing-b2b-saas\scripts\fetch_linkedin_posts.py"],
    capture_output=True,
    text=True
)
print(result1.stdout)
if result1.stderr:
    print("STDERR:", result1.stderr)
print(f"Return code: {result1.returncode}\n")

# Step 2: Generate SQL inserts
print("=" * 60)
print("STEP 2: Generating SQL inserts...")
print("=" * 60)
result2 = subprocess.run(
    [sys.executable, r"reddit-marketing-b2b-saas\scripts\generate_linkedin_inserts.py"],
    capture_output=True,
    text=True
)
print(result2.stdout)
if result2.stderr:
    print("STDERR:", result2.stderr)
print(f"Return code: {result2.returncode}\n")

# Check if SQL file was created
sql_file = r"reddit-marketing-b2b-saas\research\linkedin_posts_inserts.sql"
if os.path.exists(sql_file):
    print(f"✓ SQL file created: {sql_file}")
    with open(sql_file, 'r') as f:
        lines = f.readlines()
    print(f"  File size: {len(lines)} lines")
    print("\nFirst 30 lines of SQL:")
    print("".join(lines[:30]))
else:
    print(f"✗ SQL file not found: {sql_file}")
