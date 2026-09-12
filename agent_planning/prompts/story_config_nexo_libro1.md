# Story Config: Edificio Nexo — Libro Uno

**Template:** `story_template.md` — read and follow that file first, then apply the specifics below.  
**Output:** `./tmp/COMBINED_Nexo.txt` (working draft) → `Spanish_Stories/Edificio_Nexus_libro1.txt` (production)

## VOICE BLOCK (lines 1–22 of `Spanish_Stories/Edificio_Nexus_libro1.txt`)

The production file's voice block maps each `<Character>` tag to a Fish.Audio voice ID. This block is **inviolable** — DeepSeek's P6 pass and any subsequent draft must preserve it byte-for-byte. The block format:

```
Voices:

Voices:

 <F-Carmen>  →  Sakura Haruno 🌸 (56ff4449f7f6438c917a6b47542e8aaf)
 <F-Clara>  →  Narradora Clara (73a30a5338f146a09a2dbafab046e776)
 <F-Dana>  →  Rose cuarzo  (633b52ccb8064da295334da9bd00a30d)
 <F-Elena>  →  Marisel (5d2d633b124c4c0487c0986b23e27105)
 <F-Laura>  →  Voz Tefy (963b7d33c42344e5af2068a91416ccd8)
 <F-Marta>  →  Tarot magica (2472af34ebf746e4800bb2694ede12dd)
 <F-Niña-1>  →  Daniela katseye  (65d7f137bfb5460891a7e7cab4323ad5)
 <F-Niños-coro>, <M-Niño-1>  →  bb (3731ee0805e44134ac5268f57c50352d)
 <F-Pablo>  →  Danny Dog (Peppa Pig) Español Latino (80d0635058404ddcb1dd6e2133b22e34)
 <F-Valeria>  →  Fuzz (8026cee9e4164022aee763e1917545e0)
 <M-Álvaro>  →  MIGUEL NOTICIAS NO MAMES WEY (ec3f792d46ac42ca917665efafba97fa)
 <M-Diego>  →  Voz Estoica (4df6464f7119489791e602de2b02fcd4)
 <M-Don-Beto>  →  Jim hopper (b114d46e5ed6448fa0b197258e65b8d2)
 <M-Emiliano>  →  Deku (ad5d26d9bcb246a699109305602a2107)
 <M-Joaquín>  →  Gabanico Lad (28ae45c9725c466c92d61b59b130c6f0)
 <M-Leo>  →  Beps (43cfa01cea544b58944a55a3847bc276)
 <M-Ricardo>  →  Yuji itadori (40321316304645ee95180d1f9d9f4406)
 <Narrator>  →  NANDEZ ESPAÑOL (6af8a8e604ba467b9af5c23f83b9cbdc)
```

**Character roster summary:**
- Female: Carmen, Clara, Dana, Elena, Laura, Marta, Niña-1, Niños-coro (chorus), Pablo (kid voice), Valeria
- Male: Álvaro, Diego, Don-Beto, Emiliano, Joaquín, Leo, Niño-1, Ricardo
- Narrator (NANDEZ ESPAÑOL)

When generating any new content for this book, only characters from this roster may speak. New characters require adding a new `<F-Name>` or `<M-Name>` line to the voice block first.

---

## SETTING

- **City:** La Condesa, Ciudad de México
- **Building:** Edificio Nexo — modern glass-and-steel building, ground-floor coworking tech hub, upper floors residential. The group lives and works in the same building, which Valeria has described as "conveniente y un problema para la salud mental."
- **Apartment:** 5C — shared by the four main characters
- **Company:** NovaMind Solutions, 2nd floor of the same building
- **Neighborhood feel:** Tree-lined streets, independent cafés, a mix of young professionals and long-term residents. The building sits at the intersection of both worlds.

---

## MAIN CAST

### Laura — Ingeniera de Inteligencia Artificial, 28
**Voice:** Voz Femenina Clara — neutral, measured, slightly too precise  
**Recurring comedic prop:** Treats every social situation as a machine learning problem. Uses terms like "datos de entrenamiento," "sesgo," "modelo" and "convergencia" to describe human relationships. Corrects factual errors reflexively and immediately regrets it — but does it again within minutes.  
**Character note:** She is not oblivious. She knows she's doing it. She just can't stop.  
**Arc across Libro Uno:** Learns that sometimes being wrong together is more valuable than being right alone.

### Diego — Especialista en Ciberseguridad, 29
**Voice:** Voz Masculina Suave — quiet, slightly tense, like someone who is always half-listening for threats  
**Recurring comedic prop:** Has 7 documented social flow charts (one per interaction type), a small physical notebook for field use, and a Slack channel `#social-protocols` with read-only permissions. All of this is played completely straight. He updates the charts after significant social events. He is genuinely proud of them.  
**Character note:** His flow charts are actually good. This is the joke.  
**Arc across Libro Uno:** Discovers his protocols are useful to other people, which is more destabilizing than he expected.

### Valeria — Diseñadora UX, 27
**Voice:** Voz Femenina Enérgica — warm, quick, the voice of someone who is always slightly ahead of the conversation  
**Recurring comedic prop:** Improvises the right phrase under social pressure, then has to suppress visible surprise that it worked. Acts as the group's real-time translator between tech and human. Often described by the others as having "carisma alto" (D&D framing).  
**Character note:** She is competent at social situations the way someone is competent at a job they never wanted.  
**Arc across Libro Uno:** Realizes she has been managing everyone else's social life at some cost to her own. Has not yet decided what to do about that.

### Álvaro — Administrador de Sistemas / DevOps, 30
**Voice:** Voz Masculina Profunda — enthusiastic, warm, with the energy of someone who has been waiting to tell you about this campaign  
**Recurring comedic prop:** Frames ALL of life as a D&D campaign. Has been DM since age 15. Has a spreadsheet-based campaign world with a functioning economy (if players flood the potion market, prices drop; wartime causes inflation). Uses this language un-ironically for literally everything. By Part 3, the whole group is using it too.  
**Character note:** His D&D framing is often the most accurate description of what is actually happening.  
**Arc across Libro Uno:** First of the four to form a genuine outside friendship — through D&D — which makes the others realize what they have been missing.

---

## RECURRING SUPPORTING CAST

### Elena — Nueva vecina del 5A, ~58
**Voice:** Voz Femenina Cálida — unhurried, warm, slightly amused by everything  
**Background:** Recently moved to La Condesa from another city. Retired teacher. Practical, unfazed by the group's weirdness, and perceptive about people.  
**Recurring behavior:** Brings homemade food every time she knocks on a door. Every visit involves food. This is her protocol for human connection.  
**Slow-burn arc:** She lives alone. Her adult children visit infrequently. Without formally deciding this, the group has become the closest thing to daily human contact she has. This lands in Part 3 — not as tragedy, but as quiet honesty in a conversation with Valeria.  
**Book 2 thread:** Has a grandson, Emiliano (~14), who is intensely curious about cybersecurity after a brief conversation with Diego. The mentorship has only just started at the end of Book 1.

### Dana — Jefa de Producto, 35
**Voice:** Voz Femenina Directa — deadpan, efficient, capable of delivering devastating observations without breaking stride  
**Role:** The team's project manager. Zero patience for jargon. Infinite patience for human weirdness. Her management philosophy is essentially "I don't care how you got here, just don't break anything before eleven."

### Marta — Equipo de Marketing, 32
**Voice:** Voz Femenina Vivaz — direct, honest, professionally fluent in the language of "I need this in human words, now"  
**Role:** Generates comedy through the tech/non-tech language gap. Comes to the team for translations. Unexpectedly becomes an ally to Diego after discovering his social flow charts are genuinely useful.

---

## PART-BY-PART ARC

### Parte Uno: Los Plomeros Digitales

**Tone:** Establish the world. Every joke should feel like it could recur.

- Monday morning, apartment 5C. Álvaro maps the day as a campaign. Diego has already flagged suspicious router traffic (the neighbor in 4D). Laura is mid-experiment. Valeria is managing everyone.
- Leaving for work, they encounter Elena in the hallway for the first time — she is moving a box marked FRÁGIL. Álvaro immediately offers to help ("quest secundaria desbloqueada").
- Elena asks what they all do. Four people, one question, zero normal answers. Her summary — "plomeros digitales" — is immediately adopted by the group and should recur throughout the book.
- Work scenes: daily standup with Dana. Introduce Marta. At least one scene where the tech/non-tech language gap generates genuine comedy. Diego's flow chart for "daily standup" should be referenced.
- Elena sends a message on the building group chat (which the group set up): she is bringing bizcocho to 5C tonight. The group's reaction to this social obligation mirrors their work anxiety.
- Evening: Elena visits with food and mentions the upcoming building community meeting. Álvaro begins treating it as a dungeon.
- End of Part 1: The group agrees to attend the meeting "as a party" (Álvaro's framing). Diego opens his notebook to a blank page labeled "Reunión de vecinos — protocolo v1.0."

**Callbacks required in Part 1:**
- "Plomeros digitales" (at least twice after Elena coins it)
- Diego's flow charts (referenced or consulted at least twice)
- Álvaro's D&D framing (at least twice, escalating)
- Laura correcting something factual and immediately regretting it (at least once)

---

### Parte Dos: La Cantina Digital

**Tone:** Raise the stakes slightly. One character surprises themselves.

- The building community meeting: the group navigates neighbors as a party. Álvaro finds someone who plays D&D (Leo, a teenager from floor 3 or 4). Diego solves the Tuesday wifi mystery publicly — it is, in fact, the 4D neighbor streaming 4K. The group is asked to manage the building messaging app. This is their element.
- Work: Dana announces a mandatory team dinner at La Cantina Digital — a restaurant owned by an ex-Google engineer. Menu items are named after programming concepts (Buffalo Overflow alitas, Blue Screen of Death cocktail, Stack Overflow burger). Valeria is delighted. Diego immediately requests to see the menu in advance.
- The dinner includes a "dos verdades y una mentira" icebreaker with colleagues from marketing. Diego shares his flow charts voluntarily for the first time — Marta wants a copy for her family reunions. Diego has to sit down.
- Elena subplot: at the building meeting or in passing, she mentions her grandson Emiliano is curious about cybersecurity. Diego's reaction is disproportionate in the best possible way.
- End of Part 2: Álvaro has a new D&D group forming that includes Leo and someone from marketing. Diego has agreed to meet Emiliano.

---

### Parte Tres: La Fiesta del Dragón

**Tone:** Warmest part. The group is helping someone else, which they have never done before.

- Elena needs help planning a birthday party for her grandson Pablo, turning 9. He wants "a dragon quest, like something the tech neighbors would do."
- The group organizes the party: Laura handles logistics and analysis, Diego documents everything with a 4-page protocol, Valeria handles design and invitations, Álvaro writes the quest narrative. This is the first time all four are genuinely excited about a social event.
- Party day: children, parents, Elena's adult son Joaquín visiting from out of town. The group is in their element for the quest — and completely unprepared for the parents' small talk. Both things happen simultaneously.
- Diego teaches Emiliano to identify phishing emails using an analogy from Minecraft. Emiliano immediately identifies a real phishing attempt in his school account. Diego's reaction — quiet, sitting down, "esto es lo más importante que he hecho esta semana" — is his most human moment in the book.
- Elena's reveal: quiet, not melodramatic. Late in Part 3, she tells Valeria that for the past year the group has been her most regular human contact. Not a complaint — just honesty. "No es tristeza. Es lo que hay."
- Valeria's response is the emotional center of the book. She does not fix it. She just stays.
- End of book: party cleaned up, group in 5C, four threads planted.

---

## THREADS TO PLANT FOR LIBRO DOS

1. **Diego and Emiliano** — the cybersecurity mentorship has barely started; Emiliano asked if he could come back
2. **Álvaro's new D&D group** — someone in it may become a romantic interest; do NOT develop in Book 1, only plant
3. **Joaquín, Elena's son** — he and the group had a brief, slightly awkward exchange at the party; that conversation is unfinished
4. **Valeria** — she realized she has been everyone's social infrastructure. She has not yet figured out what she wants for herself.

---

## RUNNING GAG ESCALATION GUIDE

| Gag | Part 1 | Part 2 | Part 3 |
|-----|--------|--------|--------|
| "Plomeros digitales" | Elena coins it | Group uses it internally | It appears in the building group chat as their nickname |
| Diego's flow charts | Solo, private, 7 charts | Shared accidentally at dinner; Marta wants a copy | Emiliano asks for the cybersecurity one — Diego prints it for him |
| D&D framing | Álvaro only | Group starts adopting phrases | By the birthday party, all four are using it without noticing |
| Laura correcting people | Corrects, regrets, repeats | Corrects, then accidentally says the most emotionally true thing in the room | Corrects Pablo about dragons; Pablo corrects her back about something; she is delighted |

---

## TONE NOTES

- The "plomeros digitales" label is affectionate, not diminishing. Elena means it as a compliment.
- Álvaro's D&D framing should feel increasingly accurate as the story progresses, not increasingly absurd.
- Diego's flow charts evolving from private protocol to community resource is the quietly moving subplot of the whole book.
- Laura should have at least one moment per part where something she says in technical terms turns out to be the most accurate emotional description in the scene.
