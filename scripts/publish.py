#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "python-frontmatter>=1.1",
#   "rich>=13.0",
# ]
# ///
"""
Publish a post from the private Obsidian vault to the blog content directory.

Usage:
    uv run scripts/publish.py path/to/post.md
    uv run scripts/publish.py path/to/post.md --force
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

import frontmatter
from rich.console import Console
from rich.panel import Panel

VAULT_ROOT = Path("/Users/peter/Documents/Obsidian/Vault")
BLOG_ROOT = Path(__file__).parent.parent
CONTENT_POSTS = BLOG_ROOT / "content" / "posts"
CONTENT_ASSETS = BLOG_ROOT / "content" / "assets"

REQUIRED_FIELDS = ["title", "date", "tags"]
WARN_FIELDS = ["description"]

console = Console()


def resolve_source(path_arg: str) -> Path:
    """Resolve the source path — absolute or relative to vault root."""
    p = Path(path_arg)
    if p.is_absolute():
        return p
    candidate = VAULT_ROOT / p
    if candidate.exists():
        return candidate
    # Try as-is from cwd
    if p.exists():
        return p.absolute()
    console.print(f"[red]Error:[/red] Cannot find '{path_arg}' — tried absolute and relative to vault root.")
    sys.exit(1)


def validate_frontmatter(post) -> list[str]:
    """Check required fields. Returns list of warnings."""
    warnings = []
    missing_required = [f for f in REQUIRED_FIELDS if f not in post.metadata]
    if missing_required:
        console.print(f"[red]Error:[/red] Missing required frontmatter fields: {', '.join(missing_required)}")
        sys.exit(1)

    for field in WARN_FIELDS:
        if field not in post.metadata or not post.metadata[field]:
            warnings.append(f"Missing recommended frontmatter field: '{field}'")

    if post.metadata.get("draft") is True:
        warnings.append("Post has 'draft: true' — publishing anyway, but consider removing it.")

    return warnings


def find_image_refs(body: str) -> list[str]:
    """Extract all image filenames from wikilink and standard markdown image syntax."""
    images = []
    # ![[filename.ext]] or ![[filename.ext|alias]]
    wikilink_imgs = re.findall(r"!\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]", body)
    images.extend(wikilink_imgs)
    # ![alt](path/to/image.ext) — only local (no http)
    md_imgs = re.findall(r"!\[[^\]]*\]\((?!https?://)([^)]+)\)", body)
    images.extend(md_imgs)
    return images


def find_wikilinks(body: str) -> list[str]:
    """Find all non-image wikilinks."""
    return re.findall(r"(?<!!)\[\[([^\]|#]+?)(?:[|#][^\]]*)?\]\]", body)


def copy_images(image_refs: list[str], source: Path, force: bool) -> dict[str, Path]:
    """
    Look for each image in the attachments subfolder adjacent to the source file.
    Returns a dict mapping original ref -> destination path.
    """
    attachments_dir = source.parent / "attachments"
    copied = {}
    missing = []

    for ref in image_refs:
        filename = Path(ref).name
        src_path = attachments_dir / filename
        if not src_path.exists():
            # Fallback: search recursively in vault
            matches = list(VAULT_ROOT.rglob(filename))
            if matches:
                src_path = matches[0]
            else:
                missing.append(ref)
                continue

        dest_path = CONTENT_ASSETS / filename
        if dest_path.exists() and not force:
            console.print(f"  [yellow]Skip[/yellow] (already exists): {filename} — use --force to overwrite")
        else:
            shutil.copy2(src_path, dest_path)
        copied[ref] = dest_path

    if missing:
        console.print(f"\n[yellow]Warning:[/yellow] Could not find image(s) in vault:")
        for m in missing:
            console.print(f"  • {m}")

    return copied


def rewrite_image_paths(body: str, copied: dict[str, Path]) -> str:
    """Rewrite image references to point to ../assets/filename."""
    for original_ref, dest_path in copied.items():
        filename = dest_path.name
        # Rewrite ![[filename]] → ![filename](../assets/filename)
        body = re.sub(
            r"!\[\[" + re.escape(original_ref) + r"(?:\|[^\]]*)?\]\]",
            f"![{filename}](../assets/{filename})",
            body,
        )
        # Rewrite ![alt](old/path/filename) → ![alt](../assets/filename)
        body = re.sub(
            r"(!\[[^\]]*\]\()(?!https?://)[^)]*" + re.escape(Path(original_ref).name) + r"(\))",
            rf"\1../assets/{filename}\2",
            body,
        )
    return body


def check_wikilinks(wikilinks: list[str]) -> list[str]:
    """Warn about wikilinks that won't resolve in content/."""
    unresolved = []
    for link in wikilinks:
        # Search for a matching .md file in content/
        target = link.strip()
        matches = list(CONTENT_POSTS.rglob(f"{target}.md")) + list((BLOG_ROOT / "content").rglob(f"{target}.md"))
        if not matches:
            unresolved.append(link)
    return unresolved


def main():
    parser = argparse.ArgumentParser(
        description="Publish a post from the private Obsidian vault to the blog."
    )
    parser.add_argument("path", help="Path to the post (absolute, or relative to vault root)")
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing images in content/assets/"
    )
    args = parser.parse_args()

    source = resolve_source(args.path)

    if not source.suffix == ".md":
        console.print("[red]Error:[/red] Source file must be a .md file.")
        sys.exit(1)

    console.rule(f"[bold]Publishing[/bold]: {source.name}")

    post = frontmatter.load(str(source))

    # Validate frontmatter
    warnings = validate_frontmatter(post)

    # Find and copy images
    image_refs = find_image_refs(post.content)
    copied_images: dict[str, Path] = {}
    if image_refs:
        console.print(f"\n[cyan]Images found:[/cyan] {len(image_refs)}")
        copied_images = copy_images(image_refs, source, args.force)

    # Rewrite image paths in body
    new_body = rewrite_image_paths(post.content, copied_images)
    post.content = new_body

    # Check wikilinks
    wikilinks = find_wikilinks(new_body)
    unresolved = check_wikilinks(wikilinks)

    # Write post to content/posts/
    dest = CONTENT_POSTS / source.name
    with open(dest, "w", encoding="utf-8") as f:
        f.write(frontmatter.dumps(post))

    # Summary
    console.print()
    console.print(Panel.fit(
        f"[green]✓[/green] Written to: [bold]{dest.relative_to(BLOG_ROOT)}[/bold]\n"
        + (f"[green]✓[/green] Images copied: {', '.join(Path(p).name for p in copied_images)}\n" if copied_images else "")
        + (f"[yellow]⚠[/yellow] Warnings:\n" + "\n".join(f"  • {w}" for w in warnings) + "\n" if warnings else "")
        + (f"[yellow]⚠[/yellow] Unresolved wikilinks (won't render as links):\n"
           + "\n".join(f"  • [[{l}]]" for l in unresolved) if unresolved else ""),
        title="Publish Summary",
        border_style="green" if not warnings and not unresolved else "yellow",
    ))

    if unresolved:
        console.print("[dim]Tip: copy the linked pages to content/ or remove the wikilinks before pushing.[/dim]")


if __name__ == "__main__":
    main()
