"""Placeholder for LinkedIn post collection guidance.

For a coursework/research project, collect public posts manually and save raw text
in markdown files. Record the URL, date, engagement metrics, and notes.
"""

import os


def save_linkedin_post(author: str, title: str, content: str, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n")
        f.write(f"Author: {author}\n")
        f.write("\n")
        f.write(content)


if __name__ == "__main__":
    example_author = "Amanda Natividad"
    example_title = "Founders in niche communities"
    example_content = (
        "Date: 2026-06-01\n"
        "URL: https://www.linkedin.com/posts/amandanat_example\n"
        "Topic: Why founders should participate in niche communities\n\n"
        "## Key insights\n"
        "- Don't immediately promote.\n"
        "- Build credibility first.\n"
        "- Answer questions consistently.\n"
    )
    save_linkedin_post(example_author, example_title, example_content, "../research/linkedin-posts/example-post.md")
