#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "python-frontmatter>=1.1",
#   "rich>=13.0",
# ]
# ///
"""
Create a new post skeleton in the private Obsidian vault.

Usage:
    uv run scripts/new_post.py "My Post Title"
    uv run scripts/new_post.py "My Post Title" --drafts-folder drafts/
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

import frontmatter
from rich.console import Console

VAULT_ROOT = Path("/Users/peter/Documents/Obsidian/Vault")

console = Console()


def slugify(title: str) -> str:
    """Convert a title to a URL-safe filename slug."""
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def main():
    parser = argparse.ArgumentParser(
        description="Create a new post skeleton in the private Obsidian vault."
    )
    parser.add_argument("title", help="Post title (quoted string)")
    parser.add_argument(
        "--drafts-folder",
        default="",
        help="Subfolder within vault to write the draft (default: vault root)",
    )
    args = parser.parse_args()

    today = date.today().isoformat()
    slug = slugify(args.title)
    filename = f"{today}-{slug}.md"

    if args.drafts_folder:
        dest_dir = VAULT_ROOT / args.drafts_folder.strip("/")
    else:
        dest_dir = VAULT_ROOT

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename

    if dest.exists():
        console.print(f"[red]Error:[/red] File already exists: {dest}")
        sys.exit(1)

    metadata = {
        "title": args.title,
        "date": today,
        "lastmod": today,
        "tags": [],
        "description": "",
        "draft": True,
        "publish": False,
    }

    body = """
## Notes

_Write your notes here._

## References

-
"""

    post = frontmatter.Post(body, **metadata)

    with open(dest, "w", encoding="utf-8") as f:
        f.write(frontmatter.dumps(post))

    console.print(f"[green]✓[/green] Created: [bold]{dest}[/bold]")
    console.print(f"[dim]Open it in Obsidian and start writing. Set 'publish: true' when ready.[/dim]")


if __name__ == "__main__":
    main()
