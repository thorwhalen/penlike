# penlike

Model how an author writes, register by register, and give an agent what it needs to write in that style. The author can be one person (by default: you), a group, or any corpus.

```bash
pip install penlike
```

```bash
penlike new me --me you@example.org
penlike gather me mbox ~/mail/sent.mbox --until 2023-01-01
penlike build me
penlike brief --like me --channel email --to ada@example.org   # what to read before writing
penlike check draft.md --like me --style email.one             # what in the draft is not like you
```

penlike is made to be used by an agent. Its main surface is three skills:

```bash
gh skill install thorwhalen/penlike penlike --agent claude-code
gh skill install thorwhalen/penlike penlike-model --agent claude-code
gh skill install thorwhalen/penlike penlike-source --agent claude-code
```

or, from the installed package, with no network: `penlike install-skills --write`.

| Skill | Use it to |
|---|---|
| `penlike` | write or rewrite a text in an author's style ("write like me", "in my technical register") |
| `penlike-model` | build a model, name its registers, add notes, keep it current |
| `penlike-source` | choose and read the texts, write a custom sourcer, screen for machine-written text |

`gh skill` needs a recent GitHub CLI.

## What a model is

A person does not have one style. They write one way to a close colleague, another to a whole team, another in a technical discussion. penlike calls each of these a **register** and models each one separately.

A model holds:

- the author's **texts**, each filed under a register;
- a **measured profile** of each register: sentence and word lengths, punctuation, contractions, function words, greetings and sign-offs, formatting habits, word sequences the author returns to;
- what sets each register apart from the author's others;
- **notes** on what numbers miss, each with the texts it rests on;
- a way to pick **examples**.

When asked to write, `penlike brief` picks the register that fits the situation, and returns its profile, notes and examples. `penlike check` measures a draft against the same register and lists what differs, with figures.

## Your texts stay private

A model of how you write is private data, and so is everything in it. It is stored under `~/.local/share/penlike` (set `PENLIKE_DATA_DIR` to move it), never in a project folder. Do not commit a model, a profile, or texts it was built from to a repository.

## Use texts written before 2023

Since late 2022 a growing share of what people send has been drafted or polished by a language model. A model of you built from such text learns the machine's habits as yours. The simplest protection is a date:

```bash
penlike gather me github your-login --until 2023-01-01
```

The trade-off is age: older text is cleaner and may be less like how you write now. Whatever you choose, `gather` tells you how many of the texts it kept are dated in the era of language models.

## Sources

```bash
penlike sources
```

| Sourcer | Reads |
|---|---|
| `mbox` | a mailbox archive, such as a webmail export |
| `github` | what one login wrote: discussions, issues, pull requests and the comments on them, not line-by-line review comments (through the `gh` tool) |
| `correspond` | any channel of the [correspond](https://github.com/thorwhalen/correspond) package (`pip install 'penlike[correspond]'`) |
| `files` | text files, folders of them, `.eml` messages |
| `jsonl` | one JSON document per line |
| `claude-sessions` | what you typed to a coding agent, which is rarely how you write to people |

When none fits, a sourcer is a plain function that yields dicts, referenced by where it lives:

```python
def read(*refs, since=None, until=None, limit=None, me=(), **options):
    for path in refs:
        ...
        yield {"text": body, "date": sent, "channel": "chat", "to": readers, "is_self": True}
```

```bash
penlike gather me ~/.config/penlike/sourcers/chat.py:read ~/exports/chat.json
```

Only `text` is required. `to` and `channel` decide the register, `date` allows a cutoff, `is_self` keeps other people's writing out. Quoted replies and forwarded messages are removed from every text by rules over plain text, which can miss an unusual mail program: read a sample of what was gathered (`penlike docs me --full`). The `penlike-source` skill tells an agent how to write one for you.

## Registers

Texts are filed by **situation** first: email by number of readers (`email.one`, `email.few`, `email.many`), GitHub writing by opening or reply, and so on. Then penlike looks inside each for groups written differently, and proposes them:

```bash
penlike propose me
penlike register-add me close-colleagues --proposal email.one#2
```

A proposal is a question: you name the register, or decline. A named register keeps its identifier for good, and later texts join it when they are close enough. Routing, when you ask to write:

| You give | Register chosen |
|---|---|
| `--style close-colleagues` | the one you named |
| `--to ada@example.org` | the one you have used most with that reader |
| `--channel email --audience many` | the one for that situation |
| nothing | the largest, and the brief says it is a guess |

## One person, a group, a corpus

```bash
penlike new me
penlike new house-style --kind group --basis consent
penlike new field-guide --kind corpus --basis public
```

| Kind | Kept | Specific to it |
|---|---|---|
| `person` | only the author's own texts | registers by reader, greetings and sign-offs, how they write to each person |
| `group` | everyone's texts | shared conventions; individual habits average out |
| `corpus` | everything | text types; readers and dates are often unknown |

Measuring and checking are the same in all three. What differs is what is kept, how texts are filed, and what may be claimed.

## Screening for machine-written text (optional)

```bash
penlike screen me --tier cheap          # says what it would cost; changes nothing
penlike screen me --tier cheap --run
```

| Tier | What it does | Cost |
|---|---|---|
| `date` | excludes texts dated on or after a cutoff | none |
| `cheap` | wording, mechanics, sentence shapes, rhythm (`pip install 'penlike[screen]'`) | no model, no network; milliseconds a text |
| `heavy` | adds detectors that run small language models on your machine (`pip install 'ductus[local]'`) | processor time, timed on a sample first; a model download on first use |
| `agent` | an agent reads each text | model tokens, in proportion to the corpus |

Without `--run`, nothing is changed and the cost is stated. Flagged texts are excluded, never deleted: `penlike exclude me <id> --undo` puts one back. No detector is reliable on one short text, and each accuses some human writing. The date is the tier to trust. Screening uses [ductus](https://github.com/thorwhalen/ductus).

## Writing to someone, in your voice

penlike answers "how does the author write?". [acquaint](https://github.com/thorwhalen/acquaint) answers a different question: "what does this reader need?". To write to a known person in your own voice, use both: penlike for the voice, acquaint for the reader. The `penlike` skill does this when acquaint is installed.

## From Python

```python
import penlike

penlike.new("me", me=["you@example.org"])
penlike.gather("me", "mbox", ["sent.mbox"], until="2023-01-01")
penlike.build("me")
brief = penlike.brief(like="me", channel="email", to=["ada@example.org"])
print(brief["text"])
report = penlike.check(draft, like="me", style=brief["register"])
for item in report["discrepancies"]:
    print(item["message"])
```

Every verb returns a JSON-ready dict with `ok`, a `summary` and usually a `text`. The same verbs are served over MCP by `penlike-mcp` (`pip install 'penlike[mcp]'`), except those that reach into the machine: gathering, deleting a model, writing batch files and linking skills stay at the terminal.

## Limits

- Passing `check` means the measurable surface of a draft matches the author. It does not mean a reader who knows them would take the text for theirs.
- Imitation by a language model works best on structured writing and worst on informal, personal writing.
- A register with under about 2000 words is marked provisional; its figures are rough.
- The word lists (function words, hedges, greetings) are English. On other languages the lengths, punctuation and formatting features still hold.
- The thresholds used to propose registers were set on synthetic text. Treat proposals as questions.

## Responsible use

Build a model of your own writing, or of an author who agreed to it. Do not present a text as written by someone who neither wrote nor approved it. Follow the usage policy of the language model you use. Every model records the basis on which it was made.

## Research

The design follows a review of the literature on stylometry, style imitation with language models, and register: [misc/docs/research_report.md](misc/docs/research_report.md). The design record is [misc/docs/design.md](misc/docs/design.md).
