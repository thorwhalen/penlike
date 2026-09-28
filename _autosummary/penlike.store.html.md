# penlike.store

Where models live, and the one object that reads and writes them.

Everything penlike learns about a writer is private: the documents, the measured
profiles, the notes. None of it belongs in a repository. It lives under the data
root, one folder per kind of data:

```default
<data root>/
    config/settings.json            the default model
    models/<name>/model.json        what the model is of, and on what basis
    models/<name>/docs.jsonl        the documents, one per line
    models/<name>/registers.json    the registers and their names
    models/<name>/profiles/<register>.json
    models/<name>/notes/<register>.md
    work/<name>/...                 batch files handed to reader agents
```

The data root is the `data_dir` argument, else `$PENLIKE_DATA_DIR`, else
`~/.local/share/penlike` (`$XDG_DATA_HOME` and `%LOCALAPPDATA%` are honoured).

Code reaches files through a `MutableMapping` of relative path to text, so the local
folder can be swapped for any other store without touching the rest:

```pycon
>>> store = ModelStore("ada", files={})
>>> store.write_model({"name": "ada", "kind": "person"})
>>> store.write_docs([{"id": "1", "text": "Hello."}])
>>> store.read_model()["kind"], [d["id"] for d in store.read_docs()]
('person', ['1'])
>>> sorted(store.files)
['models/ada/docs.jsonl', 'models/ada/model.json']
```

### Functions

| [`data_dir`](#penlike.store.data_dir)([data_dir])                          | The data root: the argument, else `$PENLIKE_DATA_DIR`, else the user data folder.   |
|------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| [`model_names`](#penlike.store.model_names)(\*[, data_dir, files])            | The names of the models in the store, sorted.                                       |
| [`settings`](#penlike.store.settings)(\*[, data_dir, files])               | The settings, `{}` when none were ever written.                                     |
| [`text_files`](#penlike.store.text_files)(root)                              | A `dol` files store under `root`: `/`-separated keys, UTF-8 text values.            |
| [`write_settings`](#penlike.store.write_settings)(values, \*[, data_dir, files]) | Replace the settings.                                                               |

### Classes

| [`ModelStore`](#penlike.store.ModelStore)(name, \*[, data_dir, files])   | One model's files: documents, registers, profiles and notes.   |
|--------------------------------------------------------------------------------------------|----------------------------------------------------------------|

### *class* penlike.store.ModelStore(name, , data_dir=None, files=None)

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
  [`ModelStore`](#penlike.store.ModelStore)

### penlike.store.data_dir(data_dir=None)

The data root: the argument, else `$PENLIKE_DATA_DIR`, else the user data folder.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

```pycon
>>> data_dir("somewhere").is_absolute()
True
```

### penlike.store.model_names(, data_dir=None, files=None)

The names of the models in the store, sorted.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### penlike.store.settings(, data_dir=None, files=None)

The settings, `{}` when none were ever written.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### penlike.store.text_files(root)

A `dol` files store under `root`: `/`-separated keys, UTF-8 text values.

Folders are made on write and never on read, and a delete is permanent.

* **Return type:**
  [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### penlike.store.write_settings(values, , data_dir=None, files=None)

Replace the settings.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)
