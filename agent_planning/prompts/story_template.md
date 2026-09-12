# Spanish Sitcom Story — Reusable Writing Template

Use this template in combination with a story configuration file. The config file defines characters, setting, and plot. This file defines all formatting, tone, and quality requirements that apply to every story in the series.

## HOW TO USE
1. Read this template fully
2. Read the accompanying story config file
3. Write according to both — the config takes precedence for story-specific decisions
4. Follow the generation instruction in the prompt that invoked you (full book, or Part 1 only)
5. **Setting is parameterized.** The building name, neighborhood, company name, and other placeholders are all defined by the config — never hardcode a specific building or location in the story body. The config's `Output` path and the production file's voice block (lines 1–22, Fish.Audio voice IDs) are inviolable.

---

## LANGUAGE REQUIREMENTS

- **Latin American Spanish exclusively.** Do not use Castilian vocabulary.
  - ✓ celular, computadora, departamento, carro, ahorita, órale, padre (cool), chido, güey (sparingly)
  - ✗ móvil, ordenador, piso, coche, tío (slang), vosotros, vale (as filler)
- **Register:** Spoken, conversational, intermediate level. Avoid overly formal constructions in dialogue.
- **Vocabulary density:** Natural. Do not simplify to the point of sounding unnatural, but avoid rare vocabulary that wouldn't appear in everyday conversation.
- **Language learning integration:** Embed useful everyday phrases organically in dialogue. Do NOT:
  - Label vocabulary sections or create scene headers that announce a language topic
  - Repeat phrases as if drilling
  - Break narrative flow to explain what a phrase means
  - Create structured "lesson" scenes disguised as story

  DO naturally include across the full story: greetings, apologies, requests for clarification, polite disagreement, ordering food, making small talk, expressing simple emotions, asking for help, excusing yourself from a conversation.

---

## COMEDY STYLE

**Inspired by:** Big Bang Theory (character-driven socially-awkward genius humor), Better Off Ted (absurdist workplace comedy, deadpan), Avenue 5 (ensemble disaster management), Eureka (quirky community solving ordinary problems extraordinarily)

**Use the concept of Extr@ Spanish, not its structure.** Extr@ Spanish had the right premise — sitcom format for language learners, relatable characters in everyday situations. But its scenes were built around vocabulary targets: characters say things because the lesson needs that phrase, not because their character would say it. This produces labeled scenes, unnatural repetition, and characters who exist to USE language rather than BE people.

The language learning in this story should work the way it works when you watch a foreign film you are genuinely engaged with — through immersion, not instruction. Never label a scene by its language topic. Never have a character explain a social phrase to another character. Never repeat a phrase in a way that reads as a drill.

### Core Rules
- Humor must emerge **from character quirks colliding with each other and the outside world** — not from setup/punchline structure
- Each character has **one recurring comedic prop or behavior** defined in the config — play it completely straight, never wink at the audience about it
- Each character's quirk must generate **at least 2 callbacks per part**
- Social anxiety is portrayed with **warmth, never mockery**
- The funniest moments happen when characters apply their technical worldview to ordinary human situations
- Non-technical characters (neighbors, colleagues outside the team) should find the group's behavior charming-strange, not annoying or pathetic

### Tone
- Light, warm, absurdist
- Never mean-spirited
- Characters genuinely like each other even when they drive each other insane
- Emotional stakes are small but real — nobody is in crisis, but things do matter
- The outside world is not hostile; it's just operating on different protocols

---

## STRUCTURE

- **3 parts** per book
- After completing Part 1, **stop and wait for instruction**
- Each part must function as a complete sitcom episode with its own contained arc: setup → escalation → resolution. **Stop when the arc resolves, not when you hit a word count.**
- As a loose guide, aim for **4,000–7,000 words per part**. Err toward longer — rushed scenes with clipped dialogue perform poorly in TTS. Let scenes breathe.
- Use `## Parte Uno`, `## Parte Dos`, `## Parte Tres` as headers
- Use `***` as scene breaks within a part

### Default arc shape (override in config if needed)
- **Part 1:** Establish characters and their quirks through an ordinary day + first contact event with the outside social world
- **Part 2:** Higher-stakes social event + at least one character has an unexpected social success + a supporting character's arc deepens
- **Part 3:** Large event the group organizes for someone else + the group discovers they have grown + emotional payoff from the supporting character arc

---

## RECURRING SUPPORTING CHARACTERS

Every story must include at least one **recurring supporting character outside the main group** who:
- Has their own distinct personality and a slow-burn arc (not just a foil or straight-man)
- Represents the world the main characters are learning to navigate
- Has a genuine emotional reveal in Part 3 — not melodramatic, just honest
- Brings something the main characters genuinely need and cannot provide for themselves
- Is never made to feel inferior to the tech characters

---

## SERIES CONTINUITY

Each book is part of an ongoing series. Requirements for every book:
- **Plant at least two unresolved threads** at the end of Part 3 for the next book
- Do not resolve every storyline — leave some relationships mid-development
- A mentorship or teaching relationship between one main character and a supporting character should carry forward between books
- Each book's emotional arc should stand alone while contributing to a larger character growth arc across the series
- Characters should be demonstrably different at the end of each book from how they were at the start — small changes, but real ones

---

## TTS FORMATTING — MANDATORY

### Voices Header
Begin every story with a Voices section listing all named characters.

**Template format (human-readable, used in this file and config):**
```
Voices:

[Character name] — [voice descriptor]
```

**Production format (Fish.Audio voice block, lines 1–22 of the production file — inviolable):**
```
Voices:

Voices:

 <F-Carmen>  →  Sakura Haruno 🌸 (56ff4449f7f6438c917a6b47542e8aaf)
 <F-Clara>  →  Narradora Clara (73a30a5338f146a09a2dbafab046e776)
 <F-Dana>  →  Rose cuarzo  (633b52ccb8064da295334da9bd00a30d)
 ...
 <Narrator>  →  NANDEZ ESPAÑOL (6af8a8e604ba467b9af5c23f83b9cbdc)
```

The production voice block maps each `<Character>` tag to a Fish.Audio voice ID. The voice descriptors in this template are for human reference; the production file uses actual Fish.Audio voice IDs. When drafting a new book, the voice block is generated by the user based on which Fish.Audio voices are available at production time.

### Character Notation
- Narration: `<Narrator>` (NO colon after — `<Narrator:>` breaks the set_voices script)
- Male character dialogue: `<M-Name>` (NO colon after — `<M-Name:>` breaks the set_voices script)
- Female character dialogue: `<F-Name>` (NO colon after — `<F-Name:>` breaks the set_voices script)
- Tags are **not HTML**. Do not close them.
- Use the character's name exactly as listed in the Voices header
- **Pre-production validation:** Run `python3 validate_story.py <file.txt>` before any production handoff. If it fails, run `python3 fix_story_tags.py <file.txt>` to repair common formatting errors.

### Dialogue Format
```
<M-Name> —[tag] Spoken text here.

<F-Name> —[tag][tag] Text with multiple tags.
```

### Tag Reference

**Voice Style**
| Tag | Effect |
|-----|--------|
| `[whispering]` | Hushed, breathy |
| `[soft voice]` | Quiet and gentle |
| `[loud voice]` | Raised volume |
| `[shouting]` | Full volume |
| `[low voice]` | Deeper register |

**Emotion**
| Tag | Effect |
|-----|--------|
| `[excited]` | High energy, upbeat |
| `[angry]` | Harsh, forceful |
| `[sad]` | Heavy, downcast |

**Breath & Reaction**
| Tag | Effect |
|-----|--------|
| `[sigh]` | Expressive exhale |
| `[inhale]` / `[exhale]` | Audible breath |
| `[gasp]` | Sharp intake |
| `[panting]` | Heavy, rapid breathing |
| `[clears throat]` | Throat-clearing before speaking |

**Vocal**
| Tag | Effect |
|-----|--------|
| `[laughing]` | Full laughter |
| `[chuckling]` | Quiet, contained laugh |
| `[giggle]` | Light, high-pitched |
| `[sobbing]` | Crying with breath |
| `[crying]` | Tears audible in voice |
| `[groan]` | Discomfort or exasperation |

**Pacing**
| Tag | Effect |
|-----|--------|
| `[pause]` | Brief silence |
| `[short pause]` | Shorter beat |
| `[long pause]` | Extended silence |

**Emphasis & Ambient**
| Tag | Effect |
|-----|--------|
| `[emphasis]` | Stress on the word that follows |
| `[rustling sound]` | Background ambient rustling |

### Multiple Tags
Stack left to right with no space between: `[soft voice][excited]`

### Formatting Example

```
<Narrator> Era lunes por la mañana. El café estaba hecho. El internet funcionaba.

<M-Diego> —[soft voice] Buenos días, servidor. Buenos días, red. [pause] Buenos días, humanos. Por ese orden.

<F-Laura> —[soft voice] ¿Por qué los humanos van al último?

<M-Diego> —[low voice] Porque los servidores no me fallan.

<F-Valeria> —[chuckling][whispering] Lleva diciendo eso tres años.
```
