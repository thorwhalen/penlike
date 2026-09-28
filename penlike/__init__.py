"""Model how an author, a group or a corpus writes, and write in that style.

penlike keeps a *model* of a writer: their texts, filed by register (the situation
a text was written in), a measured profile of each register, notes on what numbers
miss, and examples. An agent asks for a brief before writing and checks its draft
afterwards.

>>> import penlike
>>> files = {}
>>> _ = penlike.new("ada", files=files)
>>> penlike.models(files=files)["summary"]
'1 model(s)'

Everything a model holds is private and lives under the user's data folder
(``~/.local/share/penlike`` by default), never in a project.
"""

from penlike.base import AI_ERA_START, PenlikeError, normalize_doc
from penlike.routing import situate
from penlike.sourcers import SOURCERS, resolve_sourcer
from penlike.store import ModelStore, data_dir
from penlike.tools import (
    TOOLS,
    assign,
    batches,
    brief,
    build,
    check,
    docs,
    exclude,
    exemplars,
    gather,
    install_skills,
    measure,
    models,
    new,
    note,
    notes,
    propose,
    register_add,
    register_edit,
    register_merge,
    registers,
    remove,
    route,
    screen,
    show,
    sources,
    use,
)

__all__ = [
    "AI_ERA_START",
    "SOURCERS",
    "TOOLS",
    "ModelStore",
    "PenlikeError",
    "assign",
    "batches",
    "brief",
    "build",
    "check",
    "data_dir",
    "docs",
    "exclude",
    "exemplars",
    "gather",
    "install_skills",
    "measure",
    "models",
    "new",
    "normalize_doc",
    "note",
    "notes",
    "propose",
    "register_add",
    "register_edit",
    "register_merge",
    "registers",
    "remove",
    "resolve_sourcer",
    "route",
    "screen",
    "show",
    "situate",
    "sources",
    "use",
]
