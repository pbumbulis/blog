#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "python-frontmatter>=1.1",
#   "rich>=13.0",
# ]
# ///
"""
Pre-publish validation for a post in the private Obsidian vault.

Exits with code 0 on success, code 1 on any failure.

Usage:
    uv run scripts/check.py path/to/post.md
"""

import argparse
import re
import sys
from pathlib import Path

import frontmatter
from rich.console import Console

VAULT_ROOT = Path("/Users/peter/Documents/Obsidian/Vault")
BLOG_ROOT = Path(__file__).parent.parent
CONTENT_DIR = BLOG_ROOT / "content"

REQUIRED_FIELDS = ["title", "date", "tags"]
WARN_FIELDS = ["description"]

# Patterns that suggest Obsidian-specific syntax that won't render in Quartz
TEMPLATER_PATTERN = re.compile(r"<%[-_]?\s*(tp\.|tR|tP)")
DATAVIEW_PATTERN = re.compile(r"```dataview|`=\s*this\.|dv\.")

console = Console()


def resolve_source(path_arg: str) -> Path:
    p = Path(path_arg)
    if p.is_absolute() and p.exists():
        return p
    candidate = VAULT_ROOT / p
    if candidate.exists():
        return candidate
    if p.exists():
        return p.absolute()
    console.print(f"[red]✗[/red] Cannot find '{path_arg}'")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Validate a post before publishing. Exits 1 if anything fails."
    )
    parser.add_argument("path", help="Path to the post (absolute or relative to vault root)")
    args = parser.parse_args()

    source = resolve_source(args.path)
    errors: list[str] = []
    warnings: list[str] = []

    try:
        post = frontmatter.load(str(source))
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to parse frontmatter: {e}")
        sys.exit(1)

    # 1. Required frontmatter fields
    missing = [f for f in REQUIRED_FIELDS if f not in post.metadata]
    if missing:
        errors.append(f"Missing required frontmatter fields: {', '.join(missing)}")

    for field in WARN_FIELDS:
        if field not in post.metadata or not post.metadata[field]:
            warnings.append(f"Missing recommended field: '{field}'")

    # 2. publish: true must be set
    if not post.metadata.get("publish"):
        errors.append("'publish: true' is not set — post is not marked as ready")

    # 3. draft: true should not be set
    if post.metadata.get("draft") is True:
        warnings.append("'draft: true' is set — it will be stripped by Quartz's RemoveDrafts filter")

    # 4. No Templater syntax
    if TEMPLATER_PATTERN.search(post.content):
        errors.append("Templater syntax detected (<%...%> or tp.) — remove before publishing")

    # 5. No Dataview syntax
    if DATAVIEW_PATTERN.search(post.content):
        errors.append("Dataview syntax detected — remove before publishing")

    # 6. Image references resolvable
    wikilink_imgs = re.findall(r"!\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]", post.content)
    md_imgs = re.findall(r"!\[[^\]]*\]\((?!https?://)([^)]+)\)", post.content)
    all_imgs = wikilink_imgs + md_imgs
    attachments_dir = source.parent / "attachments"
    for img in all_imgs:
        filename = Path(img).name
        local = attachments_dir / filename
        if not local.exists():
            vault_matches = list(VAULT_ROOT.rglob(filename))
            if not vault_matches:
                errors.append(f"Image not found anywhere in vault: '{filename}'")

    # 7. Wikilinks to private-only pages
    wikilinks = re.findall(r"(?<!!)\[\[([^\]|#]+?)(?:[|#][^\]]*)?\]\]", post.content)
    for link in wikilinks:
        target = link.strip()
        matches = list(CONTENT_DIR.rglob(f"{target}.md"))
        if not matches:
            warnings.append(f"Wikilink [[{target}]] has no matching page in content/ (will render as plain text)")

    # Report
    console.rule(f"[bold]Checking[/bold]: {source.name}")

    if warnings:
        for w in warnings:
            console.print(f"  [yellow]⚠[/yellow]  {w}")

    if errors:
        console.print()
        for e in errors:
            console.print(f"  [red]✗[/red]  {e}")
        console.print(f"\n[red]Check failed[/red] — {len(errors)} error(s), {len(warnings)} warning(s).")
        sys.exit(1)

    if warnings:
        console.print(f"\n[green]✓ Check passed[/green] — {len(warnings)} warning(s). Ready to publish.")
    else:
        console.print(f"\n[green]✓ Check passed[/green] — no issues found.")


if __name__ == "__main__":
    main()
