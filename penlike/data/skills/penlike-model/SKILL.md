---
name: penlike-model
description: Build, inspect, change or delete a penlike style model of how an author, a group or a corpus writes. Use when asked to "build a model of how I write", "make a write-like-me model", "model this author's style", "model our house style", "learn my writing style from my emails", "what registers do I have", "name this register", "split or merge these styles", "add notes on how I write", "update my style model with new texts", "show my style model", or "delete the model". Covers making the model, building registers and profiles, finding and naming new registers, recording sourced notes with parallel penlike-reader agents, and how a person, a group and a corpus differ. Use penlike-source to choose and read the texts, and penlike to write with the finished model.
license: MIT
metadata:
  audience: users
---

# penlike-model: build and keep a style model

A model answers one question: how does this author write, in each of the situations they write in? It holds the author's texts, their registers, a measured profile of each, and notes. All of it is private and lives in the user's data folder (`~/.local/share/penlike` unless `PENLIKE_DATA_DIR` says otherwise). Never copy any of it into a repository.

## The whole path

```bash
penlike new me --me quinn@example.org quinn
penlike gather me mbox ~/mail/sent.mbox --until 2023-01-01
penlike build me
penlike show me
```

Then name registers, add notes, and keep it current. Each step is below.

## 1. What is being modelled

Ask before making the model. The answer changes what is kept and what can be done.

| Kind | What it is | What is kept | What it allows |
|---|---|---|---|
| `person` | one author | only texts that author wrote | registers by reader, greetings and sign-offs, how they write to each person, change over time |
| `group` | a team, a sector, a house style | everyone's texts | shared conventions; individual quirks average out |
| `corpus` | any set of texts | everything | style by text type only; no readers, often no dates |

Also record **on what basis** the writer may be imitated: `self` (the model is of the person building it), `consent` (the author agreed) or `public` (a published style, imitated as a style and not attributed to a person). If none applies, do not build the model.

```bash
penlike new me --me quinn@example.org quinn
penlike new house-style --kind group --basis consent --description "how the docs team writes"
penlike new field-guide --kind corpus --basis public
```

`--me` lists the author's own addresses and handles. It is how their texts are told from their correspondents', so ask for every address they have written from.

## 2. Give it texts

Use the `penlike-source` skill. It covers which sources to read, the date cutoff, and screening for machine-written text.

How much text: a register with under about 2000 words is marked `provisional`, and its figures are rough. Greetings and sign-offs settle with a few dozen messages. Tell the user which registers are thin; do not hide it.

## 3. Build

```bash
penlike build me
penlike build me --reference population
```

Building files every text under a register and measures each register. Texts are filed by **situation** first: email by number of readers (`email.one`, `email.few`, `email.many`), GitHub writing by opening or reply (`github.post`, `github.reply`), agent prompts (`agent`), plain documents (`document`). Language describes a register; the situation defines it.

Each register is contrasted with a reference, to find what is characteristic and not only what is frequent. By default the reference is the author's other registers. `--reference <model>` contrasts with another model instead, such as a group the author belongs to.

Rebuild after anything changes. A model that changed since its last build refuses to brief until it is rebuilt.

## 4. Find and name registers

One situation can hide several ways of writing: mail to one reader may be a close colleague or a stranger.

```bash
penlike propose me
penlike docs me --register email.one --full --limit 5
```

Each proposal lists the texts in a group, what sets it apart, whom the texts were mostly for, and how clearly it stands apart (`separation`). A proposal is a question, never a decision:

1. Read the `typical_docs` of the proposal.
2. Decide whether the difference is real and worth a name. Two groups that differ only in length are usually one register.
3. **Ask the user to name it.** They know that these readers are "the board" and those are "friends"; you do not.
4. Record it:

```bash
penlike register-add me close-colleagues --proposal email.one#2 --description "short, no greeting, to people I work with daily"
penlike register-add me board --parent email.few --docs 3f2a9c1b7d4e8a10 9d1aadd22b0aece7
```

A named register keeps its identifier for good. Later texts join the nearest named register when they are close enough, and wait in the parent when they are not, where the next `propose` will find them. That is how a new register shows up over time.

To correct the filing:

```bash
penlike assign me board 3f2a9c1b7d4e8a10
penlike register-edit me email.many --name announcements --description "notices to everyone"
penlike register-merge me github.reply github.post
```

If `propose` finds nothing, lower `--lam` (finer groups) or `--min-separation` (groups that stand less clearly apart). These are settings to try, not truths.

## 5. Notes: what numbers miss

The profile measures lengths, punctuation, habits and forms. It cannot see how the author opens a request, what they explain and what they assume, how they disagree, or what they never say. Notes record those, each with its evidence.

For a register of more than about 30 texts, read in parallel:

```bash
penlike batches me --register email.one --size 30
```

This writes batch files under the data folder and prints their paths. Spawn one `penlike-reader` agent per batch, all with the same instruction, and collect their rows (`dimension | observation | quote | doc id | date`). Then:

1. Keep an observation only when **two or more** texts support it, from different threads.
2. Record it with its sources:

```bash
penlike note me "Opens a request with the problem, then asks in one line." --register email.one --source "doc:3f2a9c1b7d4e8a10, doc:9d1aadd22b0aece7"
penlike note me "Never uses headings in mail." --source "doc:1f67ae22acfbda7d, doc:0615363a24c22f06"
penlike notes me
```

A note without `--source` is filed as a hypothesis and must not be acted on alone. Omit `--register` for what holds in every register.

**Never record** personality traits, mood, health, religion, politics, ethnicity, sexuality or family matters, nor anything about the people the author wrote to. Record what the writing does, not what the writer is.

### Contrast notes

The most useful notes say how the author differs from your own default. To find them:

1. Pick a real text of the register and set it aside. Write down only what it says.
2. With `penlike brief`, write your own version of that content in the register.
3. Compare the two. Record each difference as a note, citing the real text: "Where a default draft thanks the reader first, the author starts with the answer."

Three or four such rounds per register are enough.

## 6. Keep it current

```bash
penlike gather me github quinn --since 2023-01-01
penlike build me
penlike propose me
```

Gathering skips texts the model already has. Registers, names and notes survive every rebuild.

## 7. Inspect and delete

```bash
penlike models
penlike show me
penlike registers me
penlike docs me --excluded
penlike use me
penlike remove old-model
```

`remove` only lists what would go until it is given `--yes`. Deleting is permanent; confirm with the user first.

## What to tell the user when the model is built

- the registers found, with how much text each rests on, and which are provisional;
- how many texts were excluded and why;
- which proposals wait for a name;
- that the model is ready for the `penlike` skill, and what it cannot do (see that skill's limits).
