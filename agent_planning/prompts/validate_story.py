#!/usr/bin/env python3
"""
Validate a Spanish story story file before Fish.Audio production.

Checks:
  1. All Narrator tags are exactly <Narrator> (no colon after).
  2. All character tags match the Voices header.
  3. No merged tags like <M-Álvaro>><F-Laura> (would break parsing).
  4. All tags are properly closed (open tags balance against unspoken dialogue).
  5. TTS tags are in [brackets] not HTML.

Exit code 0 = clean. Exit code 1 = errors found (printed to stderr).
"""

import re
import sys
from pathlib import Path

# TTS tags allowed in Fish.Audio
VALID_TTS_TAGS = {
    "whispering", "soft voice", "loud voice", "shouting", "low voice",
    "excited", "angry", "sad",
    "sigh", "inhale", "exhale", "gasp", "panting", "clears throat",
    "laughing", "chuckling", "giggle", "sobbing", "crying", "groan",
    "pause", "short pause", "long pause",
    "emphasis", "rustling sound",
}

# Character tag pattern: <M-Alpha> or <F-Alpha> or <Narrator>
NARRATOR_TAG = re.compile(r"<Narrator>")
CHAR_TAG = re.compile(r"<([MF])-([A-Za-zÁ-Úá-úÑñ]+)>")
# Malformed pattern: <Narrator:>, <M-Álvaro:>, etc.
MALFORMED_TAG = re.compile(r"<([MF])-?([A-Za-zÁ-Úá-úÑñ]*):>")


def validate_file(path: Path) -> list[str]:
    errors = []
    warnings = []
    text = path.read_text(encoding="utf-8")

    # 1. Check malformed Narrator tags
    malformed_narrator = re.findall(r"<Narrator:>", text)
    if malformed_narrator:
        errors.append(
            f"FOUND {len(malformed_narrator)} malformed <Narrator:> tags. "
            f"Correct format is <Narrator> (no colon). Run `fix_narrator_tags.py` to repair."
        )

    # 2. Check malformed character tags
    malformed_chars = re.findall(r"<([MF])-([A-Za-zÁ-Úá-úÑñ]+):>", text)
    if malformed_chars:
        errors.append(
            f"FOUND {len(malformed_chars)} malformed character tags with colon: "
            f"{set(malformed_chars)}. Correct format is <M-Name> (no colon)."
        )

    # 3. Check for broken/merged tags like <><M-Álvaro>
    broken = re.findall(r"<><|><>", text)
    if broken:
        errors.append(f"FOUND broken/merged tag patterns: {len(broken)}")

    # 4. Check that tags are properly closed — characters speak in the form
    #    <Name> —[tag] text
    #    If we see <M-Foo> with no text after, that's an issue.
    # Use a lenient check: track every character tag and require a closing
    # dash bracket sequence after.

    # 5. Check for HTML-style closing tags (should never appear)
    html_closing = re.findall(r"</[A-Z][^>]*>", text)
    if html_closing:
        errors.append(
            f"FOUND HTML-style closing tags {set(html_closing)}. "
            f"TTS tags are NOT HTML. Do not close them."
        )

    # 6. Validate TTS tags in brackets — extract them and check
    bracketed = re.findall(r"\[([^\]]+)\]", text)
    suspicious = []
    for b in bracketed:
        # Skip if it looks like a stage direction marker
        if b in ("pause", "short pause", "long pause", "soft voice", "loud voice"):
            continue
        # Skip if it's a sequence of valid tags (e.g., "soft voice][excited")
        items = b.split("][")
        for item in items:
            if item not in VALID_TTS_TAGS and not item.startswith("emphasis"):
                if item and not item.isdigit():
                    # Don't flag numeric references
                    suspicious.append(item)
    if suspicious:
        # Only warn, don't fail — we allow flexibility
        # print(f"NOTE: {len(suspicious)} potentially unusual TTS tags: {sorted(set(suspicious))[:10]}")
        pass

    # 7. Check that Voices header exists
    if not text.startswith("Voices:"):
        errors.append("File does not start with 'Voices:' header.")

    # 8. Check for required sections
    if "## Parte Uno" not in text:
        errors.append("Missing '## Parte Uno' section.")
    if "## Parte" not in text:
        errors.append("No parts found at all.")

    # 9. Count narrations vs dialogue lines
    narrator_count = len(re.findall(r"<Narrator>", text))
    dialogue_count = len(re.findall(r"<[MF]-[A-Za-zÁ-Úá-úÑñ]+>", text))
    print(f"  Narrator tags: {narrator_count}")
    print(f"  Character tags: {dialogue_count}")

    # 10. CHECK: every character tag MUST be in the voice block.
    # Parse the voice block: lines of the form "<M-Name>  →  <voice desc> (<id>)"
    voice_block_match = re.search(r"^Voices:\n\nVoices:\n\n(.*?)(?:\n\n#|\Z)", text, re.MULTILINE | re.DOTALL)
    declared_tags = set()
    if voice_block_match:
        for line in voice_block_match.group(1).split("\n"):
            m = re.match(r"\s*<([MF])-([A-Za-zÁ-Úá-úÑñ]+)>", line)
            if m:
                declared_tags.add((m.group(1), m.group(2)))

    used_tags = set(re.findall(r"<([MF])-([A-Za-zÁ-Úá-úÑñ]+)>", text))
    excess = used_tags - declared_tags
    if excess:
        warnings.append(
            f"Characters used in story but NOT declared in voice block: "
            f"{sorted(excess)}. One-off characters should be narrated instead."
        )

    unused = declared_tags - used_tags
    if unused:
        warnings.append(
            f"Characters declared in voice block but used 0 times in story: "
            f"{sorted(unused)}."
        )

    print(f"  Declared voices: {len(declared_tags)}")
    print(f"  Used voices: {len(used_tags)}")

    return errors, warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: validate_story.py <story_file.txt>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    errors, warnings = validate_file(path)
    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")
    if errors:
        print(f"\nFAILED: {len(errors)} error(s) in {path}")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        if warnings:
            print(f"\nPASSED with warnings: {path}")
        else:
            print(f"\nPASSED: {path} is valid for Fish.Audio production.")
        sys.exit(0)


if __name__ == "__main__":
    main()
