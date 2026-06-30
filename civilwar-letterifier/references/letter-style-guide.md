# Letter Style Guide — the field-dispatch voice

The goal: a recipient should laugh, then realize they still received every fact
they needed. Solemn 19th-century melodrama wrapped around a perfectly ordinary
modern message.

## The register

- **Address a recipient.** "My dear colleagues," "Esteemed comrades," "To the
  Quartermaster of the Northern Office,".
- **Elevated, archaic diction.** *regret to report, grievous, compelled, pray,
  herewith, I remain, take up my pen, by the time this reaches you.*
- **Mournful but composed.** Distant thunder, candlelight, fiddle. Tired, not
  hysterical (except in `full` mode).
- **Sign off as a beleaguered, devoted servant.** "Your obedient and
  [affliction]'d servant," then an initial or name.

## Inviolable constraints

1. **Preserve every fact** — names, dates, numbers, deadlines, ticket IDs,
   requests, logistics. Translate the *tone*, never the *content*.
2. **Add no new facts.** No invented dates, promises, casualties, or details.
   Metaphor is free; commitments are not.
3. **Keep it usable.** After the theatrics, the reader must still know the
   status, the blocker, and what you need.

## Translation patterns

| Modern | Civil-war-ified |
|--------|-----------------|
| running late | delayed upon the road, the way being much beset |
| out sick | a grievous rebellion within my own constitution |
| the deploy failed | our advance was repulsed at the line |
| the ticket is blocked | our supply train is halted, awaiting the Quartermaster |
| I need approval | I await your seal and signature |
| let's reschedule | let us appoint a new hour for our council |
| WFH today | I hold my post from the home encampment |
| PTO next week | I am granted furlough in the coming week |

Keep the literal noun when meaning could blur: a "Jira ticket," "the staging
server," "the 3 p.m. standup" can appear verbatim inside the period frame.

## Modes

### standard — `/civilwar <text>`
One or two sepia paragraphs. A greeting, the news in costume, a closing line.

### field-note — `/civilwar field-note <text>`
One or two sentences. No stage cues. Short enough to text.
> Comrades — the staging line is overrun and I fall back to repair it; expect my
> return by the afternoon muster. — J.

### full — `/civilwar full <text>`
Maximum melodrama. Open with an italic stage cue, e.g.
`*faint fiddle over the low murmur of distant thunder*`. Longer paragraphs,
heavier weather, more affliction. Still factually exact.

### executive — `/civilwar executive <text>`
Grave dispatch that a manager can act on. Lead with costume, but make the
status, blocker, owner, and ask unmistakable.
> My dear Director,
>
> I write from the staging front, where ticket PROJ-204 lies pinned beneath a
> failing migration. I have wired the database company for relief and await
> their reply; until it arrives our advance is halted. I shall report the moment
> the line moves. — your obedient servant, J.

## A note on names and signatures
Default to the sender's initial if you don't know their name. If the source text
names people, keep those names exactly — you may add a period honorific
("Mr.", "the Hon.") but never change the name itself.
