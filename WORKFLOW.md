# Cluster Notes — Workflow Guide

## Prerequisites

- **Node.js 22+** — check with `node --version`
- **uv** — install with `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **gh CLI** — install with `brew install gh`, then `gh auth login`

## One-time setup

### 1. Shell functions

Add this line to your `~/.zshrc` (or `~/.bashrc`):

```bash
source ~/Code/blog/blog.sh
```

Then reload: `source ~/.zshrc`

### 2. Verify the build locally

```bash
cd ~/Code/blog
npm ci           # install Node deps (already done if you ran setup)
npx quartz build --serve
```

Open http://localhost:8080 — you should see the Cluster Notes homepage.

### 3. GitHub Pages settings (already configured)

The repo is at https://github.com/pbumbulis/blog and Pages is enabled with
GitHub Actions as the build source. After every push to `main`, the
`.github/workflows/deploy.yml` workflow builds the site and deploys it to
https://pbumbulis.github.io/blog/.

To verify: go to **Settings → Pages** in the GitHub repo — "Source" should
read "GitHub Actions".

---

## Daily workflow

### Create a new post

```bash
blog-new "Understanding etcd Raft Consensus"
```

This creates a skeleton `.md` file in your Obsidian vault
(`/Users/peter/Documents/Obsidian/Vault/`) with today's date, a slug-based
filename, and stub frontmatter. The full path is printed so you can open it
immediately in Obsidian.

### Write the post

Open the file in Obsidian and write. The frontmatter template:

```yaml
---
title: "Understanding etcd Raft Consensus"
date: 2026-03-25
lastmod: 2026-03-25
tags: []
description: ""
draft: true
publish: false
---
```

When the post is ready to publish:

1. Set `publish: true`
2. Remove or set `draft: false`
3. Fill in `description` and `tags`

### Validate the post

```bash
blog-publish /Users/peter/Documents/Obsidian/Vault/2026-03-25-understanding-etcd-raft-consensus.md
```

`blog-publish` runs `check.py` first. If there are errors (missing frontmatter,
Templater/Dataview syntax, missing images), it stops and prints them. Fix the
errors, then re-run.

### Preview locally

```bash
blog-preview
```

Starts the Quartz dev server at http://localhost:8080 with live reload.

### Push to production

```bash
blog-push "publish: etcd raft post"
```

This stages all changes in `content/`, commits with your message, and pushes to
`main`. GitHub Actions then builds and deploys the site. The deploy usually
takes 1–2 minutes.

Check the deploy: https://github.com/pbumbulis/blog/actions

---

## All commands

| Command | What it does |
|---|---|
| `blog-new "Title"` | Create post skeleton in Obsidian vault |
| `blog-publish path/to/post.md` | Validate + copy post to blog |
| `blog-publish path/to/post.md --force` | Same, overwrite existing images |
| `blog-preview` | Start local dev server |
| `blog-status` | List all published posts |
| `blog-push` | Commit all content/ changes and push |
| `blog-push "message"` | Same with a custom commit message |

### Running scripts directly

```bash
uv run scripts/new_post.py --help
uv run scripts/publish.py --help
uv run scripts/check.py --help
uv run scripts/status.py --help
```

---

## Updating Quartz from upstream

Quartz is vendored directly into this repo (no git submodule). To pull in
upstream changes:

```bash
# Download the latest Quartz release
curl -sL https://github.com/jackyzha0/quartz/archive/refs/heads/v4.tar.gz | tar xz

# Preview what changed in Quartz's core files
diff -rq --exclude='content' --exclude='quartz.config.ts' \
  quartz-v4/quartz/ quartz/

# Selectively copy changed files — never overwrite:
#   quartz.config.ts   (your site config)
#   content/           (your posts)
#   blog.sh            (your scripts)
#   scripts/           (your scripts)
#   WORKFLOW.md        (this file)

# Clean up
rm -rf quartz-v4/

# Update npm dependencies
npm ci

# Verify nothing broke
npx quartz build

git add -A
git commit -m "chore: update Quartz to latest v4"
git push
```

---

## Troubleshooting

### Broken image paths

**Symptom:** Images show as broken links on the published site.

**Cause:** The image wasn't copied to `content/assets/`, or the path in the
markdown wasn't rewritten correctly.

**Fix:**
1. Run `blog-publish` again (it will re-copy images if `--force` is passed).
2. Check that `content/assets/yourimage.png` exists.
3. Check that the post references `../assets/yourimage.png` (relative path
   from `content/posts/`).

### Wikilink warnings

**Symptom:** `check.py` or `publish.py` warns about unresolved wikilinks.

**Cause:** The linked page exists in your private vault but hasn't been
published to `content/`.

**Options:**
- Publish the linked page too: `blog-publish path/to/linked-page.md`
- Replace the wikilink with plain text or remove it
- Leave it: Quartz renders unresolved wikilinks as plain text (not a crash)

### Failed GitHub Actions build

**Symptom:** The deploy workflow fails after a push.

**Check the logs:** https://github.com/pbumbulis/blog/actions

**Common causes:**

| Error | Fix |
|---|---|
| `npm ci` fails | Run `npm ci` locally, fix any issues, commit `package-lock.json` |
| TypeScript errors in `quartz.config.ts` | Run `npx tsc --noEmit` locally to see the error |
| Build output empty | Check `content/` wasn't accidentally emptied |
| Actions permission denied | Go to Settings → Actions → General → Workflow permissions → set to "Read and write" |

### Unpublishing a post

To remove a post from the live site:

```bash
rm ~/Code/blog/content/posts/your-post.md
blog-push "remove: your-post"
```

The file is removed from `content/` but your draft in the Obsidian vault is
untouched.

### Post appears in build but shouldn't (draft: true)

Quartz's `RemoveDrafts` filter removes any page with `draft: true` in
frontmatter. If you see a draft in the build output, check that the filter is
still present in `quartz.config.ts`:

```typescript
filters: [Plugin.RemoveDrafts()],
```

---

## Content structure

```
content/
├── index.md          homepage
├── posts/            all published posts
│   └── YYYY-MM-DD-slug.md
└── assets/           images referenced by posts
    └── image.png
```

Posts in `content/posts/` are accessible at
`https://pbumbulis.github.io/blog/posts/your-post-slug`.
