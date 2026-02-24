#!/usr/bin/env python3
"""
Add og:image meta tags to all area, guide, and blog HTML pages that are missing them.

Inserts after og:url (or last og: meta tag if og:url not found):
  <meta property="og:image" content="https://quads-nurse.com/assets/ogp.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
"""

import os
import re
import glob

OG_IMAGE_URL = "https://quads-nurse.com/assets/ogp.png"
BASE_DIR = os.path.expanduser("~/robby-the-match")

# Directories to process
PATTERNS = [
    os.path.join(BASE_DIR, "lp/job-seeker/area/*.html"),
    os.path.join(BASE_DIR, "lp/job-seeker/guide/*.html"),
    os.path.join(BASE_DIR, "blog/*.html"),
]

OG_IMAGE_TAGS = (
    '    <meta property="og:image" content="{url}">\n'
    '    <meta property="og:image:width" content="1200">\n'
    '    <meta property="og:image:height" content="630">'
).format(url=OG_IMAGE_URL)


def has_og_image(content):
    """Check if the file already has an og:image tag."""
    return bool(re.search(r'<meta\s+property=["\']og:image["\']', content))


def add_og_image(content):
    """Add og:image tags after og:url or the last og: meta tag."""
    lines = content.split('\n')
    insert_index = None

    # Strategy 1: Find og:url line and insert after it
    for i, line in enumerate(lines):
        if re.search(r'<meta\s+property=["\']og:url["\']', line):
            insert_index = i + 1
            break

    # Strategy 2: If no og:url, find the last og: meta tag
    if insert_index is None:
        for i, line in enumerate(lines):
            if re.search(r'<meta\s+property=["\']og:', line):
                insert_index = i + 1

    if insert_index is None:
        return None  # No og: tags found at all, skip

    # Insert the og:image tags
    lines.insert(insert_index, OG_IMAGE_TAGS)
    return '\n'.join(lines)


def main():
    files_found = []
    for pattern in PATTERNS:
        files_found.extend(sorted(glob.glob(pattern)))

    updated = []
    skipped_has_tag = []
    skipped_no_og = []

    for filepath in files_found:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if has_og_image(content):
            skipped_has_tag.append(filepath)
            continue

        new_content = add_og_image(content)
        if new_content is None:
            skipped_no_og.append(filepath)
            continue

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        updated.append(filepath)

    # Report
    print(f"\n{'='*60}")
    print(f"og:image Tag Addition Report")
    print(f"{'='*60}")
    print(f"\nTotal HTML files scanned: {len(files_found)}")
    print(f"Files updated (og:image added): {len(updated)}")
    print(f"Files skipped (already had og:image): {len(skipped_has_tag)}")
    print(f"Files skipped (no og: tags found): {len(skipped_no_og)}")

    if updated:
        print(f"\nUpdated files:")
        for f in updated:
            relpath = os.path.relpath(f, BASE_DIR)
            print(f"  + {relpath}")

    if skipped_has_tag:
        print(f"\nAlready had og:image:")
        for f in skipped_has_tag:
            relpath = os.path.relpath(f, BASE_DIR)
            print(f"  - {relpath}")

    if skipped_no_og:
        print(f"\nNo og: tags found (skipped):")
        for f in skipped_no_og:
            relpath = os.path.relpath(f, BASE_DIR)
            print(f"  ! {relpath}")

    print(f"\n{'='*60}")
    print(f"Done. {len(updated)} files updated.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
