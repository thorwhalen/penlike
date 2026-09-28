# penlike.routing

Registers: filing texts by situation, finding new ones, and routing a request to one.

A register is defined by the *situation* a text was written in (channel, who it
was for, reply or opening) and only then described by its language. So the first
key is situational and costs nothing to compute ([`situate()`](#penlike.routing.situate)). Language comes
second, as a check on that key: when the texts filed under one situation fall into
clearly separate groups, [`propose()`](#penlike.routing.propose) reports the groups so that a person can
name them. Named registers keep their identifier for good; nothing is renumbered
when more text arrives.

```pycon
>>> situate({"channel": "email", "audience": "one"})
'email.one'
>>> situate({"channel": "github", "reply": True})
'github.reply'
>>> situate({"channel": "document"})
'document'
```

### Module Attributes

| [`DEFAULT_LAM`](#penlike.routing.DEFAULT_LAM)            | How far (in root-mean-square z-scores) a text must be from every centre to start a group.   |
|-------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| [`DEFAULT_MIN_SEPARATION`](#penlike.routing.DEFAULT_MIN_SEPARATION) | How far apart a group must stand, relative to its own spread, to be proposed.               |

### Functions

| [`dp_means`](#penlike.routing.dp_means)(vectors, \*, lam[, max_iter])            | Cluster vectors without fixing the number of clusters (DP-means).               |
|----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| [`nearest`](#penlike.routing.nearest)(vector, centroids)                        | The closest centroid to a vector, and the distance to it.                       |
| [`propose`](#penlike.routing.propose)(docs, vectors, \*[, lam, min_size, ...])  | Look inside each register for separate groups of texts that could be registers. |
| [`route`](#penlike.routing.route)(registers, docs, \*[, style, channel, ...]) | Choose the register for a piece of writing, and say why.                        |
| [`select_exemplars`](#penlike.routing.select_exemplars)(docs, \*[, n, to, words, ...])   | Pick the texts to show as examples of a register.                               |
| [`situate`](#penlike.routing.situate)(doc)                                      | The situational register of a document, from its metadata alone.                |

### penlike.routing.DEFAULT_LAM *= 1.25*

How far (in root-mean-square z-scores) a text must be from every centre to start a group.

### penlike.routing.DEFAULT_MIN_SEPARATION *= 1.6*

How far apart a group must stand, relative to its own spread, to be proposed.

### penlike.routing.dp_means(vectors, , lam, max_iter=20)

Cluster vectors without fixing the number of clusters (DP-means).

A vector further than `lam` from every centre opens a new cluster; otherwise it
joins the nearest. One parameter, deterministic, and sequential by nature, which
is what registers that appear over time need.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`int`](https://docs.python.org/3/builtins/functions.html#int)]

```pycon
>>> dp_means([[0.0], [0.1], [5.0], [5.1]], lam=1.0)
[0, 0, 1, 1]
```

### penlike.routing.nearest(vector, centroids)

The closest centroid to a vector, and the distance to it.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None), [`float`](https://docs.python.org/3/builtins/functions.html#float)]

```pycon
>>> nearest([0.0, 0.0], {"a": [0.0, 1.0], "b": [3.0, 3.0]})
('a', 0.7071)
```

### penlike.routing.propose(docs, vectors, , lam=1.25, min_size=5, min_separation=1.6)

Look inside each register for separate groups of texts that could be registers.

Texts a person filed by hand are left alone. A group is proposed only when its
register holds at least two groups of `min_size` texts or more, and when the
group stands apart: the distance from its centre to the centre of the rest,
divided by the mean distance of its own texts to its centre, must reach
`min_separation`. Any set of texts can be cut in two; that ratio is what
tells a cut from a difference.

`lam` (how different a text must be to start a group), `min_size` and
`min_separation` are settings to adjust, not constants to trust. The defaults
were set on synthetic text; no published study validates values for personal
correspondence. A proposal is a question to a person, never a decision.

Each proposal names the texts, the features that set the group apart and whom
the texts were mostly for, which is what is needed to give it a name.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]

### penlike.routing.route(registers, docs, \*, style=None, channel=None, to=(), audience=None, reply=None, situate=<function situate>)

Choose the register for a piece of writing, and say why.

In order: the style that was named; the register the author has used most with
these readers; the register of the situation described (channel, audience,
reply); and last the register with the most text, reported as a fallback so
that nobody mistakes a guess for a match.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### penlike.routing.select_exemplars(docs, , n=5, to=(), words=None, min_words=15, max_words=400)

Pick the texts to show as examples of a register.

Texts to the same readers come first. After that the choice is for *spread*, not
for similarity of topic to the task: one text per reader or thread in turn,
newest first, because examples narrow in topic pull the imitation toward their
content and away from the style. `words` prefers texts near a target length.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]

### penlike.routing.situate(doc)

The situational register of a document, from its metadata alone.

Email is filed by how many people it was for, GitHub writing by whether it
opens a thread or answers in one, agent prompts and plain documents each under
one key. Any other channel is filed as `<channel>.<audience>`.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
