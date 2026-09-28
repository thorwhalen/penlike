---
name: penlike-source
description: Choose, read and filter the texts a penlike style model is built from, including writing a custom sourcer for an archive penlike cannot read yet. Use when asked "where should my style model get its texts", "use my sent emails", "use my GitHub discussions", "use my old blog posts", "only texts from before 2023", "read this mailbox export", "import this Slack or chat export", "make a sourcer for X", "filter out AI-written text from my sources", "screen my corpus for AI text", "how much would it cost to screen", or when penlike gather needs a source. Covers the built-in sourcers (files, jsonl, mbox, correspond, github, claude-sessions), the date cutoff that keeps machine-written text out, the custom sourcer contract, and optional screening with its cost tiers stated before anything runs.
license: MIT
metadata:
  audience: users
---

# penlike-source: where the writing comes from

A model is as good as its texts. This skill is about getting the right ones in and the wrong ones out. It only reads: nothing here sends, posts or edits anything.

The texts are private. They go into the model in the user's data folder. Never copy them, or anything derived from them, into a repository, a test, a documentation example, an issue or a commit message.

## Ask the user three things first

1. **Which sources?** Where is writing that is really theirs, and written for people? Sent mail, posts and comments, reports, messages.
2. **Which dates?** See the cutoff below.
3. **Which registers matter?** If they mostly want to write mail, a corpus of technical posts will not help much.

Do not start reading a mailbox or an account before the user has named it.

## The date cutoff: say this to every user

Since late 2022 a growing share of what people send was drafted or polished by a language model. A model of a person built from such text learns the machine's habits and calls them the person's.

The simplest and most reliable protection is a date: **use texts written before 2023.**

```bash
penlike gather me mbox ~/mail/sent.mbox --until 2023-01-01
```

`--until` is exclusive. State the trade-off to the user: older text is cleaner but may be stale, since people's writing drifts over the years. If they did not use a language model for some later writing, that writing is fine to include; they are the only one who knows.

`gather` always reports how many of the texts it kept are dated in the era of language models, whatever flags were given.

## The built-in sourcers

```bash
penlike sources
```

| Sourcer | Reads | Example |
|---|---|---|
| `mbox` | a mailbox archive, such as a webmail export | `penlike gather me mbox ~/mail/sent.mbox --until 2023-01-01` |
| `github` | what one login wrote: discussions, issues, pull requests, comments | `penlike gather me github quinn --until 2023-01-01` |
| `correspond` | any channel of the `correspond` package | `penlike gather me correspond github:example/loader#12` |
| `files` | text files, folders of them, `.eml` messages | `penlike gather me files ~/writing/essays` |
| `jsonl` | one JSON document per line | `penlike gather me jsonl ~/exports/chat.jsonl` |
| `claude-sessions` | what the user typed to a coding agent | `penlike gather me claude-sessions` |

Useful flags: `--since`, `--until`, `--limit`, `--dry-run` (count without storing), `--min-words`, `--option key=value` (passed to the sourcer). Always run with `--dry-run` first on a large source and show the user the counts.

Notes on each:

- **mbox.** The author's addresses must be on the model (`penlike new me --me ...`), or mail received is indistinguishable from mail sent. Quoted replies and forwarded messages are removed, so only the author's own words are kept.
- **github.** Narrow it with `login@owner/repo` or `login@owner`. It uses the `gh` login, so private repositories that login can read are included; say so to the user. `--option 'kinds=["discussion"]'` keeps discussions only.
- **correspond.** Reads one conversation per reference. Its email channel reads a single folder, so point it at the sent folder to read what the user wrote.
- **claude-sessions.** How a person writes to an agent is rarely how they write to people. These texts get their own register, `agent`, and should not be the basis for writing to humans. Offer it; do not default to it.

## When no sourcer fits: write one

A sourcer is a plain function that yields dicts. Only `text` is required.

```python
"""Read my chat export."""

import json


def read(*refs, since=None, until=None, limit=None, me=(), **options):
    for path in refs:
        with open(path, encoding="utf-8") as lines:
            for line in lines:
                row = json.loads(line)
                yield {
                    "text": row["body"],
                    "date": row["sent"],  # any common date form
                    "channel": "chat",
                    "to": row["recipients"],  # decides the register
                    "is_self": row["from"] in me,  # True, False, or None if unknown
                    "reply": bool(row.get("in_reply_to")),
                    "url": row.get("link", ""),
                }
```

```bash
penlike gather me ~/.config/penlike/sourcers/chat_export.py:read ~/exports/chat.json --dry-run
```

Rules for a custom sourcer:

1. **Read only.** It never sends, deletes or marks anything as read.
2. **Put it outside any repository**, for example under `~/.config/penlike/sourcers/`. A sourcer written for one person's archive tends to contain their paths and account names.
3. Fill in what the source knows. `to` and `channel` decide the register; `date` allows the cutoff; `is_self` keeps other people's writing out. A field the source does not have is left out, never invented.
4. `since` and `until` are hints for fetching less. penlike applies the dates again, so ignoring them is safe.
5. Set `register` on a document only when the source itself says what kind of writing it is (a folder named `newsletters`); that text is then filed there for good.
6. Any extra key is kept with the document under `flags`.

The alternative with no Python at all: write the texts as JSON lines by any means and use the `jsonl` sourcer.

If the source is a communication channel others would want (a chat service, a forum), the better home for the reader is a channel in `correspond`, which every tool built on it then shares. Suggest that to the user.

## Screening for machine-written text (optional)

Screening is a second line of defence after the date cutoff. It is optional and imperfect. **Always show the cost before running anything**, and ask before the `heavy` and `agent` tiers.

```bash
penlike screen me --tier date
penlike screen me --tier cheap
penlike screen me --tier heavy --sample 10
```

Without `--run`, `screen` changes nothing: it states what the tier does, what it costs on this corpus, and for the model tiers it times a small sample and estimates the full run.

| Tier | What it does | Cost | Needs |
|---|---|---|---|
| `date` | excludes texts dated on or after a cutoff (`--cutoff`) | none | dates on the texts |
| `cheap` | wording, mechanics, sentence shapes, rhythm | no model, no network; milliseconds a text | `pip install 'penlike[screen]'` |
| `heavy` | adds detectors that run small language models on this machine | processor time, plus a model download on first use; no fee | also `pip install 'ductus[local]'` |
| `agent` | an agent reads each text and judges it | model tokens in proportion to the corpus | an agent and the user's go-ahead |

What to tell the user before they choose:

- No detector is reliable on one short text. Every detector accuses some human writing, and formal, fluent prose is accused most. A careful writer's own mail can be flagged.
- The `heavy` detectors compare passages inside one text. They help on long documents and add little on short messages.
- The `date` tier involves no detector, which is why it is the one to trust.

Then run it, and look at what it caught:

```bash
penlike screen me --tier cheap --run
penlike docs me --excluded --full --limit 10
```

Flagged texts are excluded from the model, never deleted. Read a sample with the user. Put back what was wrongly flagged, and rebuild:

```bash
penlike exclude me 3f2a9c1b7d4e8a10 --undo
penlike build me
```

For the `agent` tier, estimate the cost first: `penlike show me` gives the number of texts and words. Tell the user the size, get their go-ahead, read the texts in batches (the `ductus-gauge` skill describes what to look for, when installed), and record each judgment:

```bash
penlike exclude me 3f2a9c1b7d4e8a10 --reason "agent: reads as machine-written"
```

## After gathering

Report to the user: how many texts were read and kept, what was skipped and why, how many are dated in the era of language models, and how many have no known author. Then go on with the `penlike-model` skill (`penlike build`).
