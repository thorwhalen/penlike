# penlike v1: design record

Written 2026-09-28, before the first release. The research behind the choices is in [research_report.md](research_report.md).

## Objective

penlike models **how an author writes** so that an agent can write in that style. The author may be one person, a group or a corpus. The default author is the user.

It does one thing: style emulation. It is not a detector of machine-written text, not a tool for removing machine-writing tells, and not a model of readers.

## penlike and acquaint: two questions, composed

| | acquaint | penlike |
|---|---|---|
| Question | how to talk **to** X | how to talk **like** Y |
| Models | the audience | the author |
| Its record says | what to say and avoid, how this reader wants to be addressed | how this writer sounds, in each situation they write in |

Neither absorbs the other. They meet in one case, "write to X, like Y": Y's voice, adjusted for X as a reader. There penlike supplies the voice and acquaint the audience adjustment. The rule when they disagree: the reader's needs decide what is said and how much; the author's model decides how it sounds. The `penlike` skill states this and hands over to the `acquaint-write` skill when acquaint is installed. penlike does not import acquaint.

What each existing package is used for:

| Package | Relation | How |
|---|---|---|
| acquaint | composed with, at the skill level | the `penlike` skill routes to `acquaint-write` for the reader; no code dependency |
| correspond | the source seam for communication channels | the `correspond` sourcer wraps `correspond.read`; optional extra |
| ductus | optional screening of a corpus for machine-written text | the `cheap` and `heavy` tiers call `ductus.gauge`; optional extra |
| py2mcp | the MCP surface | `penlike.mcp`, optional extra |
| dol | the store | models are read and written through a `MutableMapping` |
| cw | the command line | built from the one list of verbs |

The method of acquaint's profile extraction (parallel readers, one shared brief, evidence rows, no personality labels) is reused as a method: the `penlike-reader` agent follows the same discipline, pointed at the author's own writing.

## The seam table

| # | Seam | v1 default | Replacement that exists |
|---|---|---|---|
| 1 | where texts come from: `source` in `gather` | six sourcers on the standard library and the `gh` tool | `correspond` (in the fleet); any `module:function` or `file.py:function` |
| 2 | where models live: `files` on every verb | a `dol` files store under the user data folder | any `MutableMapping`, such as `s3dol` |
| 3 | how a text is filed: `situate` in `build` | channel, audience size and reply, from metadata | register classifiers on Hugging Face (X-GENRE, TurkuNLP), an agent |
| 4 | how a corpus is screened: `gauge` in `screening.screen` | the date cutoff, which needs no detector | `ductus` (in the fleet) |
| 5 | what a register is contrasted with: `reference` in `build` | the author's other registers | another penlike model (a group, a population) |

```
Surface for v1: shipped skills, over the command line. MCP is built as well, since it is one short module over the same list.
NOT seams:      feature extraction, example selection, profile rendering, the clustering rule. Written directly, on purpose.
```

Seam candidates, left as direct code until a replacement is wanted: syntactic features through spaCy, a style embedding as the distance and as a further check, a fine-tuned or local generation back end.

## Would each surface need the core to change?

| Surface | Answer |
|---|---|
| Command line | built. It forced list arguments in place of variadic ones. |
| MCP | built. It forced the same, and hiding `data_dir`. Verbs that reach into the host (`gather`, `remove`, `batches`, `install_skills`) are left out. |
| Skills | built; the primary surface. Every verb has a name and a sentence that says when to use it. |
| HTTP | no change needed: verbs take and return JSON, and hold no state between calls. Not built. |
| Frontend | no change needed for the same reason. Not built. |

## What v1 is

```
penlike new me && penlike gather me jsonl corpus.jsonl && penlike build me \
  && penlike brief --like me --channel email --to ada@example.org \
  && penlike check draft.md --like me --style email.one
```

returns a brief with a measured profile and examples, and a list of what in the draft differs from the author. This command is `tests/test_surfaces.py::test_the_one_command_path`.

## Decisions and their reasons

1. **A model is three things**: a measured profile, notes, and examples. The literature finds that each is visible to a different judge, and that examples alone let the output drift to a generic register.
2. **Profiles are per register.** There is no whole-person profile used for writing, because an average over registers describes none of them.
3. **The register key is situational.** Language is used to describe a register and to question the filing, not to define it.
4. **A proposal is a question.** The clustering proposes; a person names. Named registers keep their identifiers through every rebuild.
5. **Examples are chosen for spread**, readers first, and not for similarity of topic to the task.
6. **`check` reports discrepancies with figures**, and one distance calibrated on the author's own texts. It returns no single score and makes no claim that a text would pass for the author's.
7. **No cutoff is applied silently.** Every `gather` reports how many texts are dated in the era of language models; the user decides.
8. **Screening states its cost first** and excludes texts without deleting them.
9. **Every model records its basis** (self, consent, public), and the brief carries the responsible-use text.
10. **The word lists are English.** On other languages the language-neutral features hold and the word-list rates read low. Stated in the module and the README.

## Privacy

A model of a real writer is private data, and so is everything derived from it. It lives under the user data folder. The repository holds only invented text: `tests/corpus.py` is a fictional author, and `tests/test_no_private_data.py` fails the build on an address outside the placeholder domains, a home path, or a model file in the tree. The sdist is built from an allowlist.

## Cut from v1, by name

- Syntactic and Biber-style features (spaCy, `pybiber`, `biberplus`).
- Style and authorship embeddings as a distance and as a check (StyleDistance, LUAR).
- Tie strength and hierarchy as continuous variables in the register key.
- A shipped population baseline.
- Automated trial-error-explain note generation.
- Sourcers for chat services: better placed in `correspond` as channels.
- Languages other than English for the word lists.
