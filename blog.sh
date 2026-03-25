#!/usr/bin/env bash
# Blog convenience functions — source this in your shell config:
#   source ~/Code/blog/blog.sh

BLOG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create a new post skeleton in the private vault.
# Usage: blog-new "My Post Title"
blog-new() {
    if [[ -z "$1" ]]; then
        echo "Usage: blog-new \"Post Title\"" >&2
        return 1
    fi
    uv run "$BLOG_DIR/scripts/new_post.py" "$1"
}

# Run check.py then publish.py if check passes.
# Usage: blog-publish path/to/post.md [--force]
blog-publish() {
    if [[ -z "$1" ]]; then
        echo "Usage: blog-publish path/to/post.md [--force]" >&2
        return 1
    fi
    uv run "$BLOG_DIR/scripts/check.py" "$1" || return 1
    uv run "$BLOG_DIR/scripts/publish.py" "${@}"
}

# Start the Quartz dev server with live reload.
# Usage: blog-preview
blog-preview() {
    (cd "$BLOG_DIR" && npx quartz build --serve)
}

# Show blog post status at a glance.
# Usage: blog-status
blog-status() {
    uv run "$BLOG_DIR/scripts/status.py"
}

# Stage all content/ changes, commit, and push.
# Usage: blog-push ["optional commit message"]
blog-push() {
    local msg="${1:-publish: update posts}"
    (
        cd "$BLOG_DIR" || return 1
        git add content/
        git commit -m "$msg"
        git push
    )
}
