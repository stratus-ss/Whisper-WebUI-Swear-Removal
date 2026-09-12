#!/usr/bin/env python3
"""
Repair common TTS formatting errors in a Spanish story file.

Fixes:
  - <Narrator:> → <Narrator>
  - <M-Name:> → <M-Name>
  - <F-Name:> → <F-Name>
  - Removes any HTML-style closing tags
  - Removes accidental empty brackets []

The script does NOT modify any actual story content. It only fixes
formatting errors that would break the Fish.Audio set_voices script.

Run with: python3 fix_story_tags.py <file.txt>
"""

import re
import sys
from pathlib import Path


def fix_file(path: Path) -> tuple[int, list[str]]:
    text = path.read_text(encoding="utf-8")
    original = text
    fixes = []

    # 1. Fix malformed Narrator tag
    n = len(re.findall(r"<Narrator:>", text))
    if n:
        text = text.replace("<Narrator:>", "<Narrator>")
        fixes.append(f"Fixed {n} <Narrator:> → <Narrator>")

    # 2. Fix malformed character tags
    n = len(re.findall(r"<([MF])-([A-Za-zÁ-Úá-úÑñ]+):>", text))
    if n:
        text = re.sub(r"<([MF])-([A-Za-zÁ-Úá-úÑñ]+):>", r"<\1-\2>", text)
        fixes.append(f"Fixed {n} malformed character tags with colon")

    # 3. Remove HTML closing tags (should not exist)
    n = len(re.findall(r"</[A-Z][^>]*>", text))
    if n:
        text = re.sub(r"</[A-Z][^>]*>", "", text)
        fixes.append(f"Removed {n} HTML closing tags")

    # 4. Remove empty brackets
    n = len(re.findall(r"\[\s*\]", text))
    if n:
        text = re.sub(r"\[\s*\]", "", text)
        fixes.append(f"Removed {n} empty []")

    # 5. Write if changed
    if text != original:
        path.write_text(text, encoding="utf-8")
        return len(fixes), fixes
    else:
        return 0, ["No fixes needed"]


def main():
    if len(sys.argv) < 2:
        print("Usage: fix_story_tags.py <story_file.txt>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    n, fixes = fix_file(path)
    print(f"Fixes applied to {path}:")
    for f in fixes:
        print(f"  - {f}")
    sys.exit(0)


if __name__ == "__main__":
    main()
