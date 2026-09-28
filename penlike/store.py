"""Where models live, and the one object that reads and writes them.

Everything penlike learns about a writer is private: the documents, the measured
profiles, the notes. None of it belongs in a repository. It lives under the data
root, one folder per kind of data::

    <data root>/
        config/settings.json            the default model
        models/<name>/model.json        what the model is of, and on what basis
        models/<name>/docs.jsonl        the documents, one per line
        models/<name>/registers.json    the registers and their names
        models/<name>/profiles/<register>.json
        models/<name>/notes/<register>.md
        work/<name>/...                 batch files handed to reader agents

The data root is the ``data_dir`` argument, else ``$PENLIKE_DATA_DIR``, else
``~/.local/share/penlike`` (``$XDG_DATA_HOME`` and ``%LOCALAPPDATA%`` are honoured).

Code reaches files through a ``MutableMapping`` of relative path to text, so the local
folder can be swapped for any other store without touching the rest:

>>> store = ModelStore("ada", files={})
>>> store.write_model({"name": "ada", "kind": "person"})
>>> store.write_docs([{"id": "1", "text": "Hello."}])
>>> store.read_model()["kind"], [d["id"] for d in store.read_docs()]
('person', ['1'])
>>> sorted(store.files)
['models/ada/docs.jsonl', 'models/ada/model.json']
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Iterable, Iterator, MutableMapping
from pathlib import Path
from typing import Any

from penlike.base import PenlikeError

__all__ = [
    "APP_NAME",
    "DATA_DIR_ENVVAR",
    "ModelStore",
    "data_dir",
    "model_names",
    "settings",
    "text_files",
    "write_settings",
]

APP_NAME = "penlike"
DATA_DIR_ENVVAR = "PENLIKE_DATA_DIR"
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_SETTINGS_KEY = "config/settings.json"


def data_dir(data_dir: str | os.PathLike | None = None) -> Path:
    """The data root: the argument, else ``$PENLIKE_DATA_DIR``, else the user data folder.

    >>> data_dir("somewhere").is_absolute()
    True
    """
    if data_dir:
        return Path(os.path.abspath(os.path.expanduser(str(data_dir))))
    configured = os.environ.get(DATA_DIR_ENVVAR)
    if configured:
        path = Path(os.path.expanduser(configured))
        if not path.is_absolute():
            raise PenlikeError(f"${DATA_DIR_ENVVAR} must be an absolute path, got {configured!r}")
        return path
    if os.name == "nt":  # pragma: no cover - exercised on Windows CI only
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / APP_NAME
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / APP_NAME


def text_files(root: str | os.PathLike) -> MutableMapping[str, str]:
    """A ``dol`` files store under ``root``: ``/``-separated keys, UTF-8 text values.

    Folders are made on write and never on read, and a delete is permanent.
    """
    from dol import Files, mk_dirs_if_missing, wrap_kvs

    files = mk_dirs_if_missing(Files(str(root), delete_func=os.remove))
    return wrap_kvs(
        files,
        key_of_id=lambda k: k.replace(os.sep, "/"),
        id_of_key=lambda k: k.replace("/", os.sep),
        obj_of_data=lambda b: b.decode("utf-8", errors="replace"),
        data_of_obj=lambda s: s.encode("utf-8"),
    )


def _files(files: MutableMapping[str, str] | None, root: Any) -> MutableMapping[str, str]:
    return text_files(data_dir(root)) if files is None else files


def check_name(name: str) -> str:
    """Validate a model or register name: lowercase letters, digits, ``.``, ``_``, ``-``.

    >>> check_name("me"), check_name("tech-writing")
    ('me', 'tech-writing')
    """
    if not _NAME_RE.match(name or ""):
        raise PenlikeError(
            f"{name!r} is not a usable name: use lowercase letters, digits, '.', '_' "
            "or '-', starting with a letter or digit (for example 'me' or 'house-style')"
        )
    return name


def settings(
    *, data_dir: Any = None, files: MutableMapping[str, str] | None = None
) -> dict[str, Any]:
    """The settings, ``{}`` when none were ever written."""
    files = _files(files, data_dir)
    return json.loads(files[_SETTINGS_KEY]) if _SETTINGS_KEY in files else {}


def write_settings(
    values: dict[str, Any],
    *,
    data_dir: Any = None,
    files: MutableMapping[str, str] | None = None,
) -> None:
    """Replace the settings."""
    _files(files, data_dir)[_SETTINGS_KEY] = json.dumps(values, indent=2) + "\n"


def model_names(
    *, data_dir: Any = None, files: MutableMapping[str, str] | None = None
) -> list[str]:
    """The names of the models in the store, sorted."""
    files = _files(files, data_dir)
    found = {
        key.split("/")[1]
        for key in files
        if key.startswith("models/") and key.endswith("/model.json")
    }
    return sorted(found)


class ModelStore:
    """One model's files: documents, registers, profiles and notes.

    ``files`` is the seam. The default is a local folder; any ``MutableMapping`` of
    relative path to text works, which is how tests run without touching a disk.
    """

    def __init__(
        self,
        name: str,
        *,
        data_dir: str | os.PathLike | None = None,
        files: MutableMapping[str, str] | None = None,
    ):
        self.name = check_name(name)
        self.files = _files(files, data_dir)
        self.prefix = f"models/{name}/"

    def _key(self, *parts: str) -> str:
        return self.prefix + "/".join(parts)

    def exists(self) -> bool:
        return self._key("model.json") in self.files

    def require(self) -> ModelStore:
        """Return self, or explain how to make the model when it does not exist."""
        if not self.exists():
            known = model_names(files=self.files)
            listing = ", ".join(known) if known else "none yet"
            raise PenlikeError(
                f"there is no model named {self.name!r} (models: {listing}). "
                f"Make it with: penlike new {self.name}"
            )
        return self

    # -- JSON records ------------------------------------------------------------
    def _read_json(self, key: str, default: Any) -> Any:
        return json.loads(self.files[key]) if key in self.files else default

    def _write_json(self, key: str, value: Any) -> None:
        self.files[key] = json.dumps(value, indent=2, ensure_ascii=False) + "\n"

    def read_model(self) -> dict[str, Any]:
        return self._read_json(self._key("model.json"), {})

    def write_model(self, model: dict[str, Any]) -> None:
        self._write_json(self._key("model.json"), model)

    def read_registers(self) -> dict[str, dict[str, Any]]:
        return self._read_json(self._key("registers.json"), {})

    def write_registers(self, registers: dict[str, dict[str, Any]]) -> None:
        self._write_json(self._key("registers.json"), registers)

    def read_profile(self, register: str) -> dict[str, Any] | None:
        return self._read_json(self._key("profiles", f"{register}.json"), None)

    def write_profile(self, register: str, profile: dict[str, Any]) -> None:
        self._write_json(self._key("profiles", f"{register}.json"), profile)

    def clear_profiles(self) -> None:
        for key in [k for k in self.files if k.startswith(self._key("profiles") + "/")]:
            del self.files[key]

    # -- documents ---------------------------------------------------------------
    def read_docs(self) -> list[dict[str, Any]]:
        key = self._key("docs.jsonl")
        if key not in self.files:
            return []
        return [json.loads(line) for line in self.files[key].splitlines() if line.strip()]

    def write_docs(self, docs: Iterable[dict[str, Any]]) -> None:
        lines = [json.dumps(doc, ensure_ascii=False) for doc in docs]
        self.files[self._key("docs.jsonl")] = "\n".join(lines) + ("\n" if lines else "")

    # -- notes -------------------------------------------------------------------
    def read_notes(self, register: str) -> str:
        key = self._key("notes", f"{register}.md")
        return self.files[key] if key in self.files else ""

    def write_notes(self, register: str, text: str) -> None:
        self.files[self._key("notes", f"{register}.md")] = text

    def note_registers(self) -> list[str]:
        prefix = self._key("notes") + "/"
        return sorted(k[len(prefix) : -3] for k in self.files if k.startswith(prefix))

    # -- whole model -------------------------------------------------------------
    def keys(self) -> Iterator[str]:
        return (k for k in list(self.files) if k.startswith(self.prefix))

    def delete(self) -> int:
        """Delete every file of the model. Returns how many were removed."""
        keys = list(self.keys())
        for key in keys:
            del self.files[key]
        return len(keys)
