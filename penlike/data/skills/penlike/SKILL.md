---
name: penlike
description: Write or rewrite text so that it reads as a given author, group or corpus writes, using a penlike style model. Use when asked to "write like me", "write this in my voice", "make this sound like me", "rewrite this the way I write", "write like <author>", "write this in <style> style", "in my technical-writing register", "translate this into my style", or when a draft should match a house style or a corpus. Picks the right register for the situation (who it is for, which channel, reply or not), gets the measured profile, notes and examples with penlike brief, drafts, then checks the draft with penlike check and revises. The default model is the user's own. For building or changing a model use penlike-model; for choosing and reading sources use penlike-source.
license: MIT
metadata:
  audience: users
---

# penlike: write the way an author writes

penlike holds *models* of how someone writes. A model is a set of the author's own texts filed by **register** (the situation a text was written in: a quick mail to one colleague, a notice to a whole team, a technical post), a measured profile of each register, notes on what numbers miss, and examples. Your job with this skill is to write one text in one register.

Everything in a model is private. Read it, use it, and never copy it into a repository, an issue, a commit message or anything published.

## Before you start

```bash
penlike models
```

- No model at all: stop and offer to build one (skill `penlike-model`). Do not imitate a person from memory or from a guess.
- "Like me" means the default model (marked `*`). "Like <name>" or "in <style>" names a model or a register.
- A model marked `provisional` rests on little text. Say so when you hand over the result.

## Step 1: say what the situation is

A person does not have one style. Work out, from the request and the thread you are answering:

| Question | Flag |
|---|---|
| Did they name a style or register? | `--style <name>` |
| Which channel is it for? | `--channel email` (or `github`, `chat`, ...) |
| Who will read it? | `--to <address or handle> ...` |
| How many readers, if no addresses are known? | `--audience one` (or `few`, `many`, `public`) |
| Is it a reply? | `--reply` |

## Step 2: get the brief

```bash
penlike brief --like me --channel email --to ada@example.org
penlike brief --like me --style tech-writing --words 300
```

The first line of the brief says which register was chosen and **how**:

| How | Meaning | What you do |
|---|---|---|
| `named` | the style you asked for | proceed |
| `readers` | the author has written to these readers before | proceed |
| `situation` | the register of this channel and audience | proceed |
| `channel` | nothing matches the situation; nearest on the same channel | say so, and ask if the stakes are high |
| `fallback` | nothing was known; the largest register | ask which register fits, listing the alternatives |

Do not write from a `fallback` brief without telling the user that the register was a guess.

## Step 3: settle the content, then the style

Keep these apart. Style imitation that also invents content produces confident text nobody meant.

1. Write down what the text must say, in plain short statements. If the user gave you a draft, their draft *is* the content, and their own wording is the best seed: keep as much of it as the register allows.
2. Never add a fact, a promise, a date or a feeling that the content does not contain. A missing piece becomes a question to the user, written `[ASK: ...]`.

## Step 4: draft

Write the text in the register's style, using the brief in this order of authority:

1. **The notes**, which record what the author does on purpose.
2. **The measured profile**: lengths, punctuation, greeting and closing forms, habits. Treat the "usual range" as the target. "Almost never" means do not use it.
3. **The examples**: read them for rhythm, order and tone. Take nothing else from them: no sentence, no fact, no name.

Expect your own default to pull the draft toward longer sentences, more hedging, tidy three-part lists and a polite opening. The section "What sets this register apart" and the "almost never" lines are there to resist that pull.

## Step 5: check, revise, stop

```bash
penlike check draft.md --like me --style email.one
penlike check - --like me --style email.one < draft.md
```

Use the same `--style` as the register the brief chose. Each discrepancy gives the draft's figure and the author's usual one. Revise for those, then check once more. **Stop after two rounds.** Past that, fitting numbers starts to damage meaning.

Not every discrepancy deserves a fix. A long word that is the right word stays. Say which discrepancies you left and why.

## Writing to a known person, in the author's voice

Two different questions are in play, and two different tools answer them:

| Question | Tool |
|---|---|
| How does the **author** write? (voice) | penlike |
| What does the **reader** need, expect and dislike? (audience) | acquaint, when installed |

Use both when the reader is someone acquaint knows: `penlike brief` for the voice, then the `acquaint-write` skill for the reader. Where they disagree, the reader's stated needs decide **what is said and how much** (length, what to explain, what never to mention); the author's model decides **how it sounds** (greeting, rhythm, punctuation, wording). If a style check flags as machine-like something the author demonstrably does, it is voice: keep it.

## Hand over

Give the user the text, the register used and how it was chosen, what `check` still reports, and any `[ASK: ...]` left open. The author approves what goes out under their name; you do not send it.

## Limits to state plainly

- Passing `check` means the measurable surface matches. It does not mean a reader who knows the author would be fooled, and you must not claim it.
- Imitation works best on structured writing (business mail, reports) and worst on informal, personal writing. Be more careful there, and lean harder on the examples.
- A register built on a few hundred words gives rough figures.

## Responsible use

Write in a person's style only for that person or with their agreement. Do not present a text as written by someone who neither wrote nor approved it. Follow the usage policy of the model you run on.

## Commands used here

```bash
penlike models
penlike registers me
penlike route --like me --channel email --to ada@example.org
penlike brief --like me --style email.one
penlike exemplars --like me --style email.one -n 3
penlike check draft.md --like me --style email.one
penlike measure draft.md
```

Add `--json` to any command for the full result.
