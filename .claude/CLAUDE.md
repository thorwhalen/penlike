# penlike: map for the agent working on this repository

penlike models how an author writes (voice). It does not model readers (that is acquaint) and it is not a detector (that is ductus). Design record: `misc/docs/design.md`. Research: `misc/docs/research_report.md`.

## Seams and surfaces

| Seam | Default | Where |
|---|---|---|
| source | six built-in sourcers | `penlike/sourcers.py`, `gather(source=)` |
| store | `dol` files under the user data folder | `penlike/store.py`, `files=` on every verb |
| situate | channel, audience, reply | `penlike/routing.py`, `build(situate=)` |
| screening | date cutoff | `penlike/screening.py`, `screen(gauge=)` |
| reference | the author's other registers | `build(reference=)` |

Surfaces built: shipped skills (primary), command line, MCP. All three come from `penlike.tools.TOOLS`. Never write a second list of verbs.

## Rules

1. **No private data in this repository.** Tests use the invented author in `tests/corpus.py`. `tests/test_no_private_data.py` enforces the mechanical part. Examples in docstrings, docs and skills use invented text and `example.org` addresses.
2. A module must not share its name with a verb (`penlike.measure` the function would shadow `penlike.measure` the module). That is why the modules are `features`, `routing`, `screening`, `sourcers`.
3. Verbs take and return JSON-ready values, take no `*args`, and hold no state between calls.
4. The core imports no surface library. `cw`, `py2mcp`, `ductus` and `correspond` are imported where they are used.
5. Skills live in `penlike/data/skills/`, agents in `penlike/data/agents/`. `.claude/skills/<name>` and `.claude/agents/<name>.md` are relative symlinks to them. A command named in a skill must be a verb: `tests/test_surfaces.py` checks it.
6. A merge to `main` publishes to PyPI.
