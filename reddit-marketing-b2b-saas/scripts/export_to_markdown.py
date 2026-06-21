"""Utilities to export research content into markdown summaries."""

import os


def export_summary(content: str, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    summary = (
        "# Research Summary\n\n"
        "This file can be used to compile key findings from research files into a single markdown report.\n"
    )
    export_summary(summary, "../research/analysis/research-summary.md")
