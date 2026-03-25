#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "python-frontmatter>=1.1",
#   "rich>=13.0",
# ]
# ///
"""
Show the current state of the blog at a glance.

Usage:
    uv run scripts/status.py
    uv run scripts/status.py --sort date
"""

import argparse
from datetime import date, datetime
from pathlib import Path

import frontmatter
from rich.console import Console
from rich.table import Table
from rich import box

BLOG_ROOT = Path(__file__).parent.parent
CONTENT_POSTS = BLOG_ROOT / "content" / "posts"

console = Console()


def parse_date(val) -> date | None:
    if val is None:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()
    try:
        return date.fromisoformat(str(val))
    except ValueError:
        return None


def main():
    parser = argparse.ArgumentParser(description="Show blog post status at a glance.")
    parser.add_argument(
        "--sort",
        choices=["date", "title"],
        default="date",
        help="Sort posts by date (default) or title",
    )
    args = parser.parse_args()

    posts_dir = CONTENT_POSTS
    md_files = sorted(posts_dir.glob("*.md"))

    if not md_files:
        console.print("[dim]No posts found in content/posts/[/dim]")
        return

    rows = []
    drafts_in_blog = []

    for f in md_files:
        try:
            post = frontmatter.load(str(f))
        except Exception:
            rows.append({"file": f.name, "title": "[red]parse error[/red]", "date": None, "tags": 0, "draft": False})
            continue

        title = post.metadata.get("title", f.stem)
        raw_date = post.metadata.get("date")
        post_date = parse_date(raw_date)
        tags = post.metadata.get("tags", [])
        tag_count = len(tags) if isinstance(tags, list) else (1 if tags else 0)
        is_draft = post.metadata.get("draft") is True

        rows.append({
            "file": f.name,
            "title": title,
            "date": post_date,
            "tags": tag_count,
            "draft": is_draft,
        })

        if is_draft:
            drafts_in_blog.append(f.name)

    # Sort
    if args.sort == "title":
        rows.sort(key=lambda r: str(r["title"]).lower())
    else:
        rows.sort(key=lambda r: r["date"] or date.min, reverse=True)

    # Build table
    table = Table(box=box.SIMPLE, header_style="bold cyan", show_edge=False)
    table.add_column("Date", style="dim", width=12)
    table.add_column("Title", min_width=30)
    table.add_column("Tags", justify="right", width=6)
    table.add_column("File", style="dim")

    for row in rows:
        date_str = row["date"].isoformat() if row["date"] else "—"
        title_str = f"[yellow]{row['title']} [DRAFT][/yellow]" if row["draft"] else str(row["title"])
        table.add_row(date_str, title_str, str(row["tags"]), row["file"])

    console.print()
    console.print(table)

    # Summary line
    total = len(rows)
    dates_with_values = [r["date"] for r in rows if r["date"]]
    newest = max(dates_with_values).isoformat() if dates_with_values else "—"
    console.print(f"  [bold]{total}[/bold] post(s) · most recent: [bold]{newest}[/bold]")

    if drafts_in_blog:
        console.print()
        console.print("[yellow]Warning:[/yellow] The following posts in content/posts/ have draft: true")
        console.print("[dim](They won't be published by Quartz's RemoveDrafts filter — likely a mistake)[/dim]")
        for d in drafts_in_blog:
            console.print(f"  • {d}")

    console.print()


if __name__ == "__main__":
    main()
