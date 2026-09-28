# penlike.base

The shared vocabulary: the document record, text cleaning, dates and the error type.

A *document* is one piece of writing plus the situation it was written in. It is a plain
`dict` so that it round-trips through JSON and so that a custom sourcer can be written
by anyone (or any agent) without importing a class. [`normalize_doc()`](#penlike.base.normalize_doc) is the one
place that decides what a well-formed document looks like.

```pycon
>>> doc = normalize_doc({"text": "Hello there.", "channel": "email", "to": ["ada@example.org"]})
>>> doc["audience"], doc["words"], len(doc["id"])
('one', 2, 16)
```

### Module Attributes

| [`AI_ERA_START`](#penlike.base.AI_ERA_START)   | The public release of ChatGPT.                 |
|-----------------------------------------------------------------|------------------------------------------------|
| [`DOC_FIELDS`](#penlike.base.DOC_FIELDS)     | Every field a document may carry.              |
| [`RESERVED_NAMES`](#penlike.base.RESERVED_NAMES) | Names that a model or a register may not take. |

### Functions

| [`audience_of`](#penlike.base.audience_of)(to[, cc, public])    | The size of the readership: `one`, `few` (2 to 5), `many`, `public` or `unknown`.      |
|-----------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| [`check_name`](#penlike.base.check_name)(name)                 | Validate the name of a model or a register, which is also the name of its files.       |
| [`doc_id`](#penlike.base.doc_id)(text)                     | A stable id for a text: the first 16 hex digits of its SHA-256, whitespace-blind.      |
| [`normalize_doc`](#penlike.base.normalize_doc)(raw, \*[, source]) | Make a well-formed document from whatever a sourcer yielded.                           |
| [`parse_date`](#penlike.base.parse_date)(value)                | Turn a date in any common form into ISO 8601 UTC, or `None`.                           |
| [`prose_of`](#penlike.base.prose_of)(text)                   | The prose of a text: code blocks, inline code and bare links replaced by placeholders. |
| [`strip_quoted`](#penlike.base.strip_quoted)(text)               | Remove what the author did not write: quoted replies and forwarded mail.               |
| [`word_count`](#penlike.base.word_count)(text)                 | Count words (letters, with inner apostrophes).                                         |

### Exceptions

| [`PenlikeError`](#penlike.base.PenlikeError)   | An error whose message tells the caller what to do next.   |
|-----------------------------------------------------------------|------------------------------------------------------------|

### penlike.base.AI_ERA_START *= '2022-11-30'*

The public release of ChatGPT. Text dated on or after this day may have been written
or edited by a language model, so a corpus meant to capture a person is safest when
it stops before it. It is a default for warnings, never a silent filter.

### penlike.base.DOC_FIELDS *= ('id', 'text', 'date', 'source', 'ref', 'channel', 'kind', 'title', 'author', 'is_self', 'to', 'cc', 'audience', 'reply', 'url', 'register', 'pinned', 'excluded', 'flags', 'words')*

Every field a document may carry. Only `text` is required from a sourcer.

### *exception* penlike.base.PenlikeError

Bases: [`Exception`](https://docs.python.org/3/builtins/exceptions.html#Exception)

An error whose message tells the caller what to do next.

### penlike.base.RESERVED_NAMES *= ('general',)*

Names that a model or a register may not take.

### penlike.base.audience_of(to, cc=(), , public=False)

The size of the readership: `one`, `few` (2 to 5), `many`, `public` or `unknown`.

Recipient count has a measured effect on how formally people write email, so it
is part of the situation a text is filed under.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

```pycon
>>> audience_of(["a@example.org"]), audience_of(["a", "b"], ["c"]), audience_of([])
('one', 'few', 'unknown')
```

### penlike.base.check_name(name)

Validate the name of a model or a register, which is also the name of its files.

Lowercase letters, digits, `.`, `_` and `-`, starting with a letter or a
digit, with no `..`. Anything else could name a file outside the data folder.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

```pycon
>>> check_name("me"), check_name("email.one")
('me', 'email.one')
>>> check_name("../outside")
Traceback (most recent call last):
    ...
penlike.base.PenlikeError: '../outside' is not a usable name: use lowercase ...
```

### penlike.base.doc_id(text)

A stable id for a text: the first 16 hex digits of its SHA-256, whitespace-blind.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

```pycon
>>> doc_id("Hello  there.") == doc_id("Hello there. ")
True
```

### penlike.base.normalize_doc(raw, , source='')

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

### penlike.base.parse_date(value)

Turn a date in any common form into ISO 8601 UTC, or `None`.

A naive value is read as UTC. A bare year or day is accepted.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)

```pycon
>>> parse_date("2021-03-04")
'2021-03-04T00:00:00+00:00'
>>> parse_date("Thu, 4 Mar 2021 10:00:00 +0100")
'2021-03-04T09:00:00+00:00'
>>> parse_date("2023")
'2023-01-01T00:00:00+00:00'
>>> parse_date("") is None
True
```

### penlike.base.prose_of(text)

The prose of a text: code blocks, inline code and bare links replaced by placeholders.

Style is measured on prose. Code and links are somebody else’s tokens, and they
would swamp punctuation and word-length figures in technical writing.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

```pycon
>>> prose_of("Call `f(x)` then see https://example.org/a for more.")
'Call CODE then see LINK for more.'
```

### penlike.base.strip_quoted(text)

Remove what the author did not write: quoted replies and forwarded mail.

A model of an author built from text that includes the messages they were
answering is a model of their correspondents. Lines starting with `>` go, and
everything from a reply header (“On <date>, <someone> wrote:”, “Original
Message”, a block of mail headers) onward goes. This is a heuristic over
plain text: check a sample of what was gathered.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

```pycon
>>> strip_quoted("Sounds good.\n\nOn Mon, 1 Feb 2021, Ada wrote:\n> Shall we?")
'Sounds good.'
>>> strip_quoted("> earlier point\nI agree with this.")
'I agree with this.'
>>> strip_quoted("Here is the plan.\n\nOn Monday I wrote:\nship it")
'Here is the plan.\n\nOn Monday I wrote:\nship it'
```

### penlike.base.word_count(text)

Count words (letters, with inner apostrophes).

* **Return type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)

```pycon
>>> word_count("Don't stop, it's 3pm.")
4
```
