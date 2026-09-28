# penlike

Model how an author, a group or a corpus writes, and write in that style.

penlike keeps a *model* of a writer: their texts, filed by register (the situation
a text was written in), a measured profile of each register, notes on what numbers
miss, and examples. An agent asks for a brief before writing and checks its draft
afterwards.

```pycon
>>> import penlike
>>> files = {}
>>> _ = penlike.new("ada", files=files)
>>> penlike.models(files=files)["summary"]
'1 model(s)'
```

Everything a model holds is private and lives under the user’s data folder
(`~/.local/share/penlike` by default), never in a project.

### Functions

| [`assign`](#penlike.assign)(model, register, ids, \*[, data_dir, ...])   | File texts under a register by hand.                                                      |
|------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| [`batches`](#penlike.batches)(model, \*[, register, size, ...])           | Write a register's texts into batch files for reader agents, and return their paths.      |
| [`brief`](#penlike.brief)(\*[, like, style, channel, to, ...])          | Everything needed to write in an author's style, for one piece of writing.                |
| [`build`](#penlike.build)([model, reference, situate, lam, ...])        | File every text under a register and measure each register's profile.                     |
| [`check`](#penlike.check)(text, \*[, like, style, channel, to, ...])    | Measure a draft against the author's register and list what differs.                      |
| [`data_dir`](#penlike.data_dir)([data_dir])                                | The data root: the argument, else `$PENLIKE_DATA_DIR`, else the user data folder.         |
| [`docs`](#penlike.docs)([model, register, excluded, limit, ...])       | List a model's texts: id, date, register and the first words.                             |
| [`exclude`](#penlike.exclude)(model, ids, \*[, reason, undo, ...])        | Keep texts out of the model without deleting them, or put them back with `undo`.          |
| [`exemplars`](#penlike.exemplars)(\*[, like, style, channel, to, ...])      | Pick texts by the author to show as examples, for the register the request routes to.     |
| [`gather`](#penlike.gather)(model, source[, refs, since, until, ...])    | Read texts from a source into a model.                                                    |
| [`install_skills`](#penlike.install_skills)(\*[, target, write])                 | Link the skills and agents shipped with penlike into an agent host's folders.             |
| [`measure`](#penlike.measure)(text)                                       | Measure one text's style, on its own: lengths, punctuation, habits, greeting and closing. |
| [`models`](#penlike.models)(\*[, data_dir, files])                       | List the models in the store, with what each is a model of.                               |
| [`new`](#penlike.new)(model, \*[, kind, description, basis, ...])     | Make an empty model.                                                                      |
| [`normalize_doc`](#penlike.normalize_doc)(raw, \*[, source])                    | Make a well-formed document from whatever a sourcer yielded.                              |
| [`note`](#penlike.note)(model, text, \*[, register, source, ...])      | Record something about how the author writes that numbers do not capture.                 |
| [`notes`](#penlike.notes)([model, register, data_dir, files])           | Read the notes on a model: one register's, or all of them.                                |
| [`propose`](#penlike.propose)([model, lam, min_size, ...])                | Look for registers nobody named yet: groups of texts that are written differently.        |
| [`register_add`](#penlike.register_add)(model, name, \*[, parent, ...])        | Name a register and put texts in it, from a proposal or from a list of text ids.          |
| [`register_edit`](#penlike.register_edit)(model, register, \*[, name, ...])     | Give a register a display name or a description.                                          |
| [`register_merge`](#penlike.register_merge)(model, register, into, \*[, ...])    | Merge one register into another, when the two turn out to be written the same way.        |
| [`registers`](#penlike.registers)([model, data_dir, files])                 | List a model's registers: how much text each rests on, and what it was named.             |
| [`remove`](#penlike.remove)(model, \*[, yes, data_dir, files])           | Delete a model and everything in it.                                                      |
| [`resolve_sourcer`](#penlike.resolve_sourcer)(source)                             | Find the sourcer a name refers to: built-in, `module:function`, or `file.py:function`.    |
| [`route`](#penlike.route)(\*[, like, style, channel, to, ...])          | Choose the register for a piece of writing, and say why it was chosen.                    |
| [`screen`](#penlike.screen)(model, \*[, tier, cutoff, run, ...])         | Screen a model's texts for machine-written content.                                       |
| [`show`](#penlike.show)([model, data_dir, files])                      | Show one model: what it is of, where its texts came from, and its registers.              |
| [`situate`](#penlike.situate)(doc)                                        | The situational register of a document, from its metadata alone.                          |
| [`sources`](#penlike.sources)()                                           | List the built-in sourcers, what each reads, and whether it can run on this machine.      |
| [`use`](#penlike.use)(model, \*[, data_dir, files])                   | Make a model the default, the one meant by "write like me".                               |

### Classes

| [`ModelStore`](#penlike.ModelStore)(name, \*[, data_dir, files])   | One model's files: documents, registers, profiles and notes.   |
|--------------------------------------------------------------------------------------------|----------------------------------------------------------------|

### Exceptions

| [`PenlikeError`](#penlike.PenlikeError)   | An error whose message tells the caller what to do next.   |
|-----------------------------------------------------------------|------------------------------------------------------------|

### *class* penlike.ModelStore(name, , data_dir=None, files=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One model’s files: documents, registers, profiles and notes.

`files` is the seam. The default is a local folder; any `MutableMapping` of
relative path to text works, which is how tests run without touching a disk.

#### delete()

Delete every file of the model. Returns how many were removed.

* **Return type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)

#### require()

Return self, or explain how to make the model when it does not exist.

* **Return type:**
  [`ModelStore`](penlike.store.md#penlike.store.ModelStore)

### *exception* penlike.PenlikeError

Bases: [`Exception`](https://docs.python.org/3/builtins/exceptions.html#Exception)

An error whose message tells the caller what to do next.

### penlike.assign(model, register, ids, , data_dir=None, files=None)

File texts under a register by hand. The choice is kept through every later build.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penlike.batches(model, , register=None, size=30, data_dir=None, files=None)

Write a register’s texts into batch files for reader agents, and return their paths.

The files go under the data root (`work/<model>/`), never into a project
folder. Each holds `size` texts with their ids, so that a note can cite them.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penlike.brief(, like=None, style=None, channel=None, to=None, audience=None, reply=False, n=5, words=None, data_dir=None, files=None)

Everything needed to write in an author’s style, for one piece of writing.

Routes the request to a register, then returns that register’s measured
profile, the notes on it, and examples by the author. Read it before
drafting; check the draft against the same register afterwards.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penlike.build(model=None, , reference=None, situate=None, lam=1.25, data_dir=None, files=None)

File every text under a register and measure each register’s profile.

Texts are filed by situation (`situate`, a `module:function` reference,
replaces the rule). Texts that a person assigned by hand stay where they were
put. Where a register has named finer registers, each new text joins the
nearest one if it is within `lam` of it, and otherwise waits in the parent.

`reference` names another model to contrast with (a population, a sector).
Without it each register is contrasted with the author’s other registers.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penlike.check(text, , like=None, style=None, channel=None, to=None, audience=None, reply=False, threshold=2.0, data_dir=None, files=None)

Measure a draft against the author’s register and list what differs.

Each discrepancy gives the draft’s figure and the author’s usual one, so it can
be acted on. `ok` is true when nothing differs by more than `threshold` of
the author’s own spread. Passing the check means the measurable surface
matches; it does not mean the draft would pass for the author’s.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penlike.data_dir(data_dir=None)

The data root: the argument, else `$PENLIKE_DATA_DIR`, else the user data folder.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

```pycon
>>> data_dir("somewhere").is_absolute()
True
```

### penlike.docs(model=None, , register=None, excluded=False, limit=20, full=False, data_dir=None, files=None)

List a model’s texts: id, date, register and the first words. `full` prints whole texts.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penlike.exclude(model, ids, , reason='by hand', undo=False, data_dir=None, files=None)

Keep texts out of the model without deleting them, or put them back with `undo`.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penlike.exemplars(, like=None, style=None, channel=None, to=None, audience=None, reply=False, n=5, words=None, data_dir=None, files=None)

Pick texts by the author to show as examples, for the register the request routes to.

Texts to the same readers come first, then a spread over readers and dates.
`words` prefers examples near the length of what is to be written.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penlike.gather(model, source, refs=None, , since=None, until=None, limit=None, include_others=False, min_words=5, dry_run=False, option=None, data_dir=None, files=None)

Read texts from a source into a model.

`source` is a built-in sourcer (see `sources`) or a reference to your own.
`since` and `until` bound the dates kept (`until` is exclusive). For a
person model only the author’s own texts are kept unless `include_others`.
Texts already in the model are skipped. `option` passes `key=value`
settings to the sourcer. `dry_run` counts without storing.

The result says how many kept texts are dated in the era of language models,
because those may not be the author’s own words.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penlike.install_skills(, target=None, write=False)

Link the skills and agents shipped with penlike into an agent host’s folders.

The target defaults to `~/.claude`. Without `write` it only says what it would do.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

```pycon
>>> result = install_skills()
>>> result["dry_run"], len(result["skills"]) > 0
(True, True)
```

### penlike.measure(text)

Measure one text’s style, on its own: lengths, punctuation, habits, greeting and closing.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penlike.models(, data_dir=None, files=None)

List the models in the store, with what each is a model of.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penlike.new(model, , kind='person', description='', basis='self', me=None, default=False, data_dir=None, files=None)

Make an empty model.

`kind` is person, group or corpus. `basis` records why the texts may be
imitated: self, consent or public. `me` lists the author’s own addresses and
handles, used to tell their texts from their correspondents’. The first model
made becomes the default.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penlike.normalize_doc(raw, , source='')

Make a well-formed document from whatever a sourcer yielded.

Quoted material is removed, the date is put in ISO form, the audience is derived
when it was not given, and the id is computed from the cleaned text. Unknown keys
are kept under `flags` so that a custom sourcer can carry extra metadata.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

```pycon
>>> doc = normalize_doc({"text": "> quoted\nFine by me.", "date": "2020", "mood": "calm"})
>>> doc["text"], doc["date"][:4], doc["flags"]
('Fine by me.', '2020', {'mood': 'calm'})
```

### penlike.note(model, text, , register='general', source=None, data_dir=None, files=None)

Record something about how the author writes that numbers do not capture.

For example how they open a request, what they explain and what they assume,
how they disagree. `source` says what the note rests on (text ids, such as
`doc:3f2a...`); a note without one is filed as a hypothesis. `register` is
`general` for what holds everywhere.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penlike.notes(model=None, , register=None, data_dir=None, files=None)

Read the notes on a model: one register’s, or all of them.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penlike.propose(model=None, , lam=1.25, min_size=5, min_separation=1.6, data_dir=None, files=None)

Look for registers nobody named yet: groups of texts that are written differently.

Returns proposals, each with the texts in it, what sets it apart and whom the
texts were for. Read a few of its `typical_docs`, then name it with
`register-add --proposal`. Lower `lam` to find finer groups, and
`min_separation` to see groups that stand less clearly apart.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penlike.register_add(model, name, , parent=None, description='', proposal=None, ids=None, lam=1.25, min_size=5, min_separation=1.6, data_dir=None, files=None)

Name a register and put texts in it, from a proposal or from a list of text ids.

The texts are pinned there, and they are what later texts are compared with.
Use the same `lam`, `min_size` and `min_separation` as the `propose` call
the proposal came from.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penlike.register_edit(model, register, , name=None, description=None, data_dir=None, files=None)

Give a register a display name or a description. Its identifier never changes.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penlike.register_merge(model, register, into, , data_dir=None, files=None)

Merge one register into another, when the two turn out to be written the same way.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penlike.registers(model=None, , data_dir=None, files=None)

List a model’s registers: how much text each rests on, and what it was named.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penlike.remove(model, , yes=False, data_dir=None, files=None)

Delete a model and everything in it. Without `yes` it only says what would go.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penlike.resolve_sourcer(source)

Find the sourcer a name refers to: built-in, `module:function`, or `file.py:function`.

* **Return type:**
  [`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)[[`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis), [`Iterable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]]

```pycon
>>> resolve_sourcer("files") is files
True
>>> resolve_sourcer("json:loads").__name__
'loads'
```

### penlike.route(, like=None, style=None, channel=None, to=None, audience=None, reply=False, data_dir=None, files=None)

Choose the register for a piece of writing, and say why it was chosen.

Name a `style`, or describe the situation: the `channel` (email, github,
…), whom it is `to`, the `audience` size (one, few, many, public), and
whether it is a `reply`. With nothing given, the register with the most text
is returned and marked as a fallback.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penlike.screen(model, , tier='date', cutoff='2022-11-30', run=False, sample=5, data_dir=None, files=None)

Screen a model’s texts for machine-written content. States the cost first.

Tiers: date (free), cheap (no model), heavy (local models), agent (tokens).
Without `run` nothing is changed: the call reports what the tier does, what it
costs on this corpus, and for the date tier how many texts it would exclude.
With `run` the flagged texts are excluded (never deleted; `exclude --undo`
puts them back).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penlike.show(model=None, , data_dir=None, files=None)

Show one model: what it is of, where its texts came from, and its registers.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penlike.situate(doc)

The situational register of a document, from its metadata alone.

Email is filed by how many people it was for, GitHub writing by whether it
opens a thread or answers in one, agent prompts and plain documents each under
one key. Any other channel is filed as `<channel>.<audience>`.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### penlike.sources()

List the built-in sourcers, what each reads, and whether it can run on this machine.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### penlike.use(model, , data_dir=None, files=None)

Make a model the default, the one meant by “write like me”.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### Modules

| [`base`](penlike.base.md#module-penlike.base)           | The shared vocabulary: the document record, text cleaning, dates and the error type.      |
|-------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| [`data`](penlike.data.md#module-penlike.data)           | The skills and agents shipped with penlike, as package data.                              |
| [`features`](penlike.features.md#module-penlike.features)   | Measure how a text is written: the cheap tier, standard library only.                     |
| [`mcp`](penlike.mcp.md#module-penlike.mcp)             | MCP over stdio: the same verbs, for local MCP clients.                                    |
| [`profile`](penlike.profile.md#module-penlike.profile)     | Profiles: what a set of texts has in common, and how far a draft is from it.              |
| [`routing`](penlike.routing.md#module-penlike.routing)     | Registers: filing texts by situation, finding new ones, and routing a request to one.     |
| [`screening`](penlike.screening.md#module-penlike.screening) | Screening: keeping machine-written text out of a model of a person.                       |
| [`sourcers`](penlike.sourcers.md#module-penlike.sourcers)   | Sourcers: where the writing comes from.                                                   |
| [`store`](penlike.store.md#module-penlike.store)         | Where models live, and the one object that reads and writes them.                         |
| [`tools`](penlike.tools.md#module-penlike.tools)         | The verbs: every operation penlike offers, as plain functions returning JSON-ready dicts. |
