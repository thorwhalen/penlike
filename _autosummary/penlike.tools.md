# penlike.tools

The verbs: every operation penlike offers, as plain functions returning JSON-ready dicts.

This module is the single list that the command line, the MCP server and the
shipped skills are all built from ([`TOOLS`](#penlike.tools.TOOLS)). It knows nothing about any of
them. Each verb returns a dict with `ok`, a one-line `summary` and usually a
`text` meant to be read.

The life of a model, in verbs:

```default
new -> gather -> screen (optional) -> build -> propose / register_add -> note
then, for every piece of writing:  brief -> (draft) -> check -> (revise)
```

```pycon
>>> files = {}
>>> new("ada", description="Ada's letters", files=files)["ok"]
True
>>> [m["name"] for m in models(files=files)["models"]]
['ada']
```

### Module Attributes

| [`KINDS`](#penlike.tools.KINDS)             | What a model can be a model of.                                                      |
|--------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| [`BASES`](#penlike.tools.BASES)             | On what basis the texts may be used to imitate their author.                         |
| [`HIDDEN_PARAMETERS`](#penlike.tools.HIDDEN_PARAMETERS) | where the data lives, and `situate`, which loads a function from a module or a file. |
| [`TOOLS`](#penlike.tools.TOOLS)             | The single list every surface is built from.                                         |

### Functions

| [`host_mutating`](#penlike.tools.host_mutating)(fn)       | Mark a verb that reaches into the machine it runs on, beyond the data root.   |
|--------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| [`without`](#penlike.tools.without)(func[, hidden]) | The same verb with `hidden` parameters removed from its signature.            |

### penlike.tools.BASES *= {'consent': 'the author agreed to be modelled', 'public': 'a published style or corpus, imitated as a style and not attributed to a person', 'self': 'the model is of the person building it'}*

On what basis the texts may be used to imitate their author.

### penlike.tools.HIDDEN_PARAMETERS *= ('data_dir', 'files', 'situate')*

where the
data lives, and `situate`, which loads a function from a module or a file.

* **Type:**
  Arguments that belong to the host, not to a caller on a remote surface

### penlike.tools.KINDS *= {'corpus': 'any set of texts, with or without known authors or readers', 'group': "several authors who share a style (a team, a sector, a house style); everyone's texts are kept", 'person': 'one author; only their own texts are kept, and readers and greetings matter'}*

What a model can be a model of. The kind changes what is kept and what is said.

### penlike.tools.TOOLS *= [<function models>, <function new>, <function use>, <function show>, <function remove>, <function sources>, <function gather>, <function docs>, <function exclude>, <function screen>, <function build>, <function registers>, <function propose>, <function register_add>, <function register_edit>, <function register_merge>, <function assign>, <function note>, <function notes>, <function route>, <function exemplars>, <function brief>, <function measure>, <function check>, <function batches>, <function install_skills>]*

The single list every surface is built from.

### penlike.tools.host_mutating(fn)

Mark a verb that reaches into the machine it runs on, beyond the data root.

Reading arbitrary paths, loading a sourcer from a file, deleting a model and
linking into an agent host are things the person at the terminal decides. A
remote surface leaves these verbs out.

### penlike.tools.without(func, hidden=('data_dir', 'files', 'situate'))

The same verb with `hidden` parameters removed from its signature.

A surface builds its arguments from the signature, so this is how the command
line leaves out the in-memory store and how a remote surface leaves out the
data root.

```pycon
>>> "files" in inspect.signature(without(models)).parameters
False
```
