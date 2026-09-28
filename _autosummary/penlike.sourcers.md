# penlike.sourcers

Sourcers: where the writing comes from. Read-only, by construction.

A *sourcer* is a plain function. It takes references (paths, conversation
references, a login) and yields documents as dicts:

```default
def my_sourcer(*refs, since=None, until=None, limit=None, me=(), **options):
    yield {"text": "...", "date": "2021-03-04", "channel": "chat", "to": ["ada"]}
```

Only `text` is required. Every other field of [`penlike.base.DOC_FIELDS`](penlike.base.md#penlike.base.DOC_FIELDS) is
optional and improves what the model can do: `date` allows a cutoff, `to` and
`channel` decide the register, `is_self` separates the author from the people
they were talking with. `since` and `until` are hints a sourcer may use to
fetch less; the caller applies the window again, so ignoring them is safe.

The source is a seam: [`resolve_sourcer()`](#penlike.sourcers.resolve_sourcer) accepts a built-in name, a
`module:function` reference, or a `path/to/file.py:function` reference, so a
sourcer written for one person’s odd archive needs no change here.

```pycon
>>> sourcer = resolve_sourcer("jsonl")
>>> sourcer.__name__
'jsonl'
>>> sorted(SOURCERS)
['claude-sessions', 'correspond', 'files', 'github', 'jsonl', 'mbox']
```

### Module Attributes

| [`SOURCERS`](#penlike.sourcers.SOURCERS)   | The built-in sourcers, by the name used on the command line.   |
|-------------------------------------------------------------|----------------------------------------------------------------|

### Functions

| [`claude_sessions`](#penlike.sourcers.claude_sessions)(\*refs, \*\*_)                    | What the author typed to a coding agent, from saved Claude Code session logs.          |
|----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| [`correspond`](#penlike.sourcers.correspond)(\*refs[, since, limit, registry])      | Conversations read through `correspond`, the facade over communication channels.       |
| [`files`](#penlike.sourcers.files)(\*refs[, me])                               | Text files and folders of them (`.txt`, `.md`, `.rst`), and `.eml` messages.           |
| [`github`](#penlike.sourcers.github)(\*refs[, since, until, limit, kinds, run]) | What one GitHub user wrote: discussions, issues, pull requests and comments on them.   |
| [`jsonl`](#penlike.sourcers.jsonl)(\*refs, \*\*_)                              | JSON Lines files, one document per line: the interchange format for custom sources.    |
| [`mbox`](#penlike.sourcers.mbox)(\*refs[, me])                                | Mailbox archives in mbox format, such as a mail export from a webmail provider.        |
| [`requirements`](#penlike.sourcers.requirements)()                                    | For each built-in sourcer: what it reads, and whether it can run here.                 |
| [`resolve_sourcer`](#penlike.sourcers.resolve_sourcer)(source)                           | Find the sourcer a name refers to: built-in, `module:function`, or `file.py:function`. |

### penlike.sourcers.SOURCERS *: [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [Callable](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)[[...], [Iterable](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable)[[dict](https://docs.python.org/3/builtins/stdtypes.html#dict)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [Any](https://docs.python.org/3/library/typing.html#typing.Any)]]]]* *= {'claude-sessions': <function claude_sessions>, 'correspond': <function correspond>, 'files': <function files>, 'github': <function github>, 'jsonl': <function jsonl>, 'mbox': <function mbox>}*

The built-in sourcers, by the name used on the command line.

### penlike.sourcers.claude_sessions(\*refs, \*\*\_)

What the author typed to a coding agent, from saved Claude Code session logs.

This is how a person writes to an agent, which is rarely how they write to
people. It gets its own register (`agent`) and should not be the basis of a
model meant for writing to humans.

* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterator)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]

### penlike.sourcers.correspond(\*refs, since=None, limit=None, registry=None, \*\*\_)

Conversations read through `correspond`, the facade over communication channels.

Each reference is a correspond conversation reference, for example
`github:owner/repo#12` or `email:`. Any channel registered with correspond
works, including one you add yourself. Needs `pip install 'penlike[correspond]'`.

* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterator)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]

### penlike.sourcers.files(\*refs, me=(), \*\*\_)

Text files and folders of them (`.txt`, `.md`, `.rst`), and `.eml` messages.

A folder is read recursively. A text file is one document; it has no date (a
file’s modification time says when it was copied, not when it was written) and
no addressee, so it is filed as a `document`.

* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterator)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]

### penlike.sourcers.github(\*refs, since=None, until=None, limit=None, kinds=('discussion', 'issue'), run=<function run>, \*\*_)

What one GitHub user wrote: discussions, issues, pull requests and comments on them.

Each reference is a login, optionally narrowed to a repository or an owner:
`octocat`, `octocat@owner/repo`, `octocat@owner`. It goes through the
`gh` command line tool and its login, so private repositories the login can
read are included.

Limits: GitHub search returns at most 1000 threads per query; the first 100
comments of a thread are read (50 for a discussion, with 50 replies each);
review comments on the lines of a pull request are not read. `kinds` keeps
`discussion`, `issue` (which includes pull requests) or both.

* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterator)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]

### penlike.sourcers.jsonl(\*refs, \*\*\_)

JSON Lines files, one document per line: the interchange format for custom sources.

Anything that can write `{"text": ..., "date": ..., "to": [...]}` lines can feed
a model, in any language and by any means.

* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterator)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]

### penlike.sourcers.mbox(\*refs, me=(), \*\*\_)

Mailbox archives in mbox format, such as a mail export from a webmail provider.

Pass the author’s own addresses as `me` so that only what they sent is kept.
Without it, messages carrying a “Sent” label are taken as the author’s and the
rest are left undecided.

* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterator)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]

### penlike.sourcers.requirements()

For each built-in sourcer: what it reads, and whether it can run here.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]

### penlike.sourcers.resolve_sourcer(source)

Find the sourcer a name refers to: built-in, `module:function`, or `file.py:function`.

* **Return type:**
  [`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)[[`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis), [`Iterable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]]

```pycon
>>> resolve_sourcer("files") is files
True
>>> resolve_sourcer("json:loads").__name__
'loads'
```
