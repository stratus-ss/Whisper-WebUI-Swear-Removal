# Discovery Ladders — Wiki Page Template

Use this template for every Discovery Ladder wiki page. Fill in `<!-- -->`
placeholders with the session's actual data. After filling, publish via
GraphQL `pages.update` (or `pages.create` for the first session).

**Format established:** 2026-07-04, V10 (descriptive V/M/D tiers, per-area
sections, collapsed extraction details).

## Structure

```
# Archive Discovery Ladders

**Status key:** 📖 Available · 🔒 Blocked · ⚫ Dead end · ✅ Found

---

## 🏛️ <Area Name> (if multiple floors/zones)

### Quick reference

| Quad | Item | Status |

<details>
<summary>Anchor detail table (click to expand)</summary>

| Quad | Anchor | Visible | Mid | Deep | Extraction | DC |

</details>

<details>
<summary>Extraction details — <Area Name> (click to expand)</summary>

- **[Item](...</en/D&D/Osteria/Players/Loot/Item_Name>):** <method>.
  **Reckless:** <consequence>.

</details>

---   ← horizontal rule between every area

... repeat for each area

## Discovery Tips (always include at bottom)
```

## Emoji key (choose per area)

| Emoji | Use for |
|-------|---------|
| 🏛️ | Archives, libraries, study areas |
| 📚 | Upper floors, book-heavy zones |
| 🚪 | Entrances, transitions, corridors |
| 🏗️ | Under construction, undercrofts, rough areas |
| ⚔️ | Climax / high-stakes zones, combat areas |
| 🌿 | Natural / wilderness areas |
| 💧 | Water / flooded zones |
| 🔥 | Forge / heat / fire areas |

## Rules

### Status key (Quick Reference)
- `📖 Available` — still left, not yet found
- `🔒 Blocked` — gated behind a condition/quest
- `⚫ Dead end` — narrative dead end (always a row, never struck-through)
- `✅ Found` — already claimed by a player + their name in parens

### Anchor detail table
- Only **one** of V/M/D columns is populated per row
- **Visible** = DM narrates without a roll (descriptive text)
- **Mid** = DC 12–14 to discover (descriptive text)
- **Deep** = DC 14–16 to discover (descriptive text)
- **DC** must include check type + number, e.g. `Sleight of Hand 12`
- **Extraction** = method description, e.g. `Reach under fallen shelf`
- ✅ (Found) rows: leave V/M/D blank, put "Already FOUND (<player>)." in Extraction
- ⚫ (Dead end) rows: only Visible populated, Extraction/DC both `—`
- Item names that are loot → link to `/en/D&D/Osteria/Players/Loot/<Item_Name>`

### Extraction details (collapsed)
- One bullet per loot item
- Format: `**[Item](/en/D&D/Osteria/Players/Loot/Item_Name):** <method>. **Reckless:** <consequence>.`
- Include alt methods if applicable: `Alt: Nature 13.`
- Add sprite / environmental modifiers as a final line

### Discovery Tips (always at bottom)
Copy verbatim from the published page — this is DM-facing operational guidance.

### Section separators
- `---` horizontal rule between every area section
- Emoji prefix per area for fast vertical scanning

### Dead ends
- Always regular text (never struck-through)
- Always in **Visible** column (DM announces, player investigates and finds nothing)
- Extraction/DC = `—`

## Publishing

Use the GraphQL `pages.update` mutation with:
- `editor: "markdown"`
- `isPublished: true`, `isPrivate: false`
- `locale: "en"`
- Tags: session numbers as strings (e.g. `["32", "33", "43"]`)

See `knowledge/services/dnd-workflow.md` §12 for the full publishing workflow.
