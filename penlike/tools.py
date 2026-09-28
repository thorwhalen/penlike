"""The verbs: every operation penlike offers, as plain functions returning JSON-ready dicts.

This module is the single list that the command line, the MCP server and the
shipped skills are all built from (:data:`TOOLS`). It knows nothing about any of
them. Each verb returns a dict with ``ok``, a one-line ``summary`` and usually a
``text`` meant to be read.

The life of a model, in verbs::

    new -> gather -> screen (optional) -> build -> propose / register_add -> note
    then, for every piece of writing:  brief -> (draft) -> check -> (revise)

>>> files = {}
>>> new("ada", description="Ada's letters", files=files)["ok"]
True
>>> [m["name"] for m in models(files=files)["models"]]
['ada']
"""

from __future__ import annotations

import functools
import inspect
import json
from collections import Counter
from collections.abc import Mapping, MutableMapping
from datetime import datetime, timezone
from typing import Any

from penlike import routing as _registers
from penlike import screening as _screen
from penlike import sourcers as _sources
from penlike.base import AI_ERA_START, PenlikeError, normalize_doc, parse_date
from penlike.features import measure as _measure
from penlike.profile import (
    build_norm,
    build_profile,
    compare,
    contrast,
    render_profile,
    style_vector,
)
from penlike.store import (
    ModelStore,
    check_name,
    data_dir as _data_dir,
    model_names,
    settings,
    write_settings,
)

__all__ = [
    "HIDDEN_PARAMETERS",
    "KINDS",
    "BASES",
    "TOOLS",
    "host_mutating",
    "without",
]

#: What a model can be a model of. The kind changes what is kept and what is said.
KINDS = {
    "person": "one author; only their own texts are kept, and readers and greetings matter",
    "group": "several authors who share a style (a team, a sector, a house style); everyone's texts are kept",
    "corpus": "any set of texts, with or without known authors or readers",
}
#: On what basis the texts may be used to imitate their author.
BASES = {
    "self": "the model is of the person building it",
    "consent": "the author agreed to be modelled",
    "public": "a published style or corpus, imitated as a style and not attributed to a person",
}
#: Arguments that belong to the host, not to a caller on a remote surface.
HIDDEN_PARAMETERS = ("data_dir", "files")
#: The reserved register for notes that hold in every register.
GENERAL = "general"
_NORM = "_all"
_RESPONSIBLE_USE = (
    "Responsible use: write in this style only for its author or with their agreement. "
    "Do not present the result as written by a person who did not write or approve it, "
    "and follow your model provider's usage policy."
)


def host_mutating(fn):
    """Mark a verb that reaches into the machine it runs on, beyond the data root.

    Reading arbitrary paths, loading a sourcer from a file, deleting a model and
    linking into an agent host are things the person at the terminal decides. A
    remote surface leaves these verbs out.
    """
    fn.mutates_host = True
    return fn


def without(func, hidden=HIDDEN_PARAMETERS):
    """The same verb with ``hidden`` parameters removed from its signature.

    A surface builds its arguments from the signature, so this is how the command
    line leaves out the in-memory store and how a remote surface leaves out the
    data root.

    >>> "files" in inspect.signature(without(models)).parameters
    False
    """
    hidden = set(hidden)
    signature = inspect.signature(func)

    @functools.wraps(func)
    def verb(*args, **kwargs):
        return func(*args, **kwargs)

    verb.__signature__ = signature.replace(
        parameters=[p for p in signature.parameters.values() if p.name not in hidden]
    )
    return verb


def _store(model: str | None, *, data_dir: Any, files: Any) -> ModelStore:
    name = model or settings(data_dir=data_dir, files=files).get("default_model")
    if not name:
        names = model_names(data_dir=data_dir, files=files)
        if len(names) == 1:
            name = names[0]
        elif not names:
            raise PenlikeError("there are no models yet. Make one with: penlike new me")
        else:
            raise PenlikeError(
                f"which model? There are {len(names)}: {', '.join(names)}. Name one, or "
                "set a default with: penlike use <model>"
            )
    return ModelStore(name, data_dir=data_dir, files=files).require()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _live(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [doc for doc in docs if not doc.get("excluded")]


# -- models --------------------------------------------------------------------------


def models(*, data_dir: str | None = None, files: MutableMapping | None = None) -> dict:
    """List the models in the store, with what each is a model of."""
    default = settings(data_dir=data_dir, files=files).get("default_model")
    found = []
    for name in model_names(data_dir=data_dir, files=files):
        store = ModelStore(name, data_dir=data_dir, files=files)
        meta = store.read_model()
        found.append(
            {
                "name": name,
                "kind": meta.get("kind"),
                "description": meta.get("description", ""),
                "documents": meta.get("n_docs", 0),
                "registers": len([r for r in store.read_registers().values() if r.get("n_docs")]),
                "default": name == default,
            }
        )
    lines = [
        f"{'*' if m['default'] else ' '} {m['name']}  ({m['kind']}, {m['documents']} texts, "
        f"{m['registers']} registers)  {m['description']}"
        for m in found
    ]
    text = "\n".join(lines) if lines else "No models yet. Make one with: penlike new me"
    return {"ok": True, "summary": f"{len(found)} model(s)", "models": found, "text": text}


def new(
    name: str,
    *,
    kind: str = "person",
    description: str = "",
    basis: str = "self",
    me: list[str] | None = None,
    default: bool = False,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
) -> dict:
    """Make an empty model.

    ``kind`` is person, group or corpus. ``basis`` records why the texts may be
    imitated: self, consent or public. ``me`` lists the author's own addresses and
    handles, used to tell their texts from their correspondents'. The first model
    made becomes the default.
    """
    if kind not in KINDS:
        raise PenlikeError(f"kind must be one of {', '.join(KINDS)}; got {kind!r}")
    if basis not in BASES:
        raise PenlikeError(
            f"basis must be one of {', '.join(BASES)}; got {basis!r}. It records on what "
            "ground this writer may be imitated"
        )
    check_name(name)
    if name == GENERAL:
        raise PenlikeError(f"{GENERAL!r} is reserved; choose another name")
    store = ModelStore(name, data_dir=data_dir, files=files)
    if store.exists():
        raise PenlikeError(f"a model named {name!r} already exists; see: penlike show {name}")
    store.write_model(
        {
            "name": name,
            "kind": kind,
            "description": description,
            "basis": basis,
            "me": [m.lower() for m in (me or [])],
            "created": _now(),
            "n_docs": 0,
            "gathered": [],
        }
    )
    current = settings(data_dir=data_dir, files=files)
    made_default = default or not current.get("default_model")
    if made_default:
        write_settings({**current, "default_model": name}, data_dir=data_dir, files=files)
    return {
        "ok": True,
        "summary": f"made the {kind} model {name!r}"
        + (" (now the default)" if made_default else ""),
        "model": name,
        "text": f"Made {name!r}. Next, give it texts: penlike gather {name} <source> <references>",
    }


def use(name: str, *, data_dir: str | None = None, files: MutableMapping | None = None) -> dict:
    """Make a model the default, the one meant by "write like me"."""
    ModelStore(name, data_dir=data_dir, files=files).require()
    current = settings(data_dir=data_dir, files=files)
    write_settings({**current, "default_model": name}, data_dir=data_dir, files=files)
    return {"ok": True, "summary": f"{name!r} is now the default model", "model": name}


def show(
    model: str | None = None,
    *,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
) -> dict:
    """Show one model: what it is of, where its texts came from, and its registers."""
    store = _store(model, data_dir=data_dir, files=files)
    meta, records = store.read_model(), store.read_registers()
    docs = store.read_docs()
    excluded = Counter(doc["excluded"] for doc in docs if doc.get("excluded"))
    lines = [
        f"{meta['name']}: a {meta['kind']} model ({KINDS[meta['kind']]})",
        f"basis: {meta.get('basis')} ({BASES.get(meta.get('basis'), '')})",
        f"texts: {len(_live(docs))} in use, {sum(excluded.values())} excluded",
    ]
    if meta.get("description"):
        lines.insert(1, meta["description"])
    for reason, count in excluded.most_common():
        lines.append(f"  excluded, {reason}: {count}")
    if not meta.get("built"):
        lines.append(f"not built yet; run: penlike build {meta['name']}")
    lines += ["", _register_lines(records)]
    return {
        "ok": True,
        "summary": f"{meta['name']}: {len(_live(docs))} texts, {len(records)} registers",
        "model": meta,
        "registers": records,
        "text": "\n".join(lines),
    }


@host_mutating
def remove(
    model: str,
    *,
    yes: bool = False,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
) -> dict:
    """Delete a model and everything in it. Without ``yes`` it only says what would go."""
    store = ModelStore(model, data_dir=data_dir, files=files).require()
    keys = list(store.keys())
    if not yes:
        return {
            "ok": False,
            "summary": f"would delete {len(keys)} files of {model!r}; repeat with --yes to do it",
            "files": keys,
        }
    store.delete()
    current = settings(data_dir=data_dir, files=files)
    if current.get("default_model") == model:
        current.pop("default_model")
        write_settings(current, data_dir=data_dir, files=files)
    return {"ok": True, "summary": f"deleted {model!r} ({len(keys)} files)"}


# -- sources -------------------------------------------------------------------------


def sources() -> dict:
    """List the built-in sourcers, what each reads, and whether it can run on this machine."""
    found = _sources.requirements()
    lines = []
    for name, info in found.items():
        state = "ready" if info["ready"] else f"needs: {info['to_enable']}"
        lines.append(f"{name}: {info['reads']} [{state}]")
    lines.append(
        "custom: any function yielding dicts with a 'text', referenced as "
        "module:function or path/to/file.py:function"
    )
    return {
        "ok": True,
        "summary": f"{len(found)} built-in sourcers",
        "sources": found,
        "text": "\n".join(lines),
    }


def _options(pairs: list[str] | None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for pair in pairs or []:
        key, separator, value = pair.partition("=")
        if not separator:
            raise PenlikeError(f"an option is written key=value; got {pair!r}")
        try:
            out[key] = json.loads(value)
        except json.JSONDecodeError:
            out[key] = value
    return out


@host_mutating
def gather(
    model: str,
    source: str,
    refs: list[str] | None = None,
    *,
    since: str | None = None,
    until: str | None = None,
    limit: int | None = None,
    include_others: bool = False,
    min_words: int = 5,
    dry_run: bool = False,
    option: list[str] | None = None,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
) -> dict:
    """Read texts from a source into a model.

    ``source`` is a built-in sourcer (see ``sources``) or a reference to your own.
    ``since`` and ``until`` bound the dates kept (``until`` is exclusive). For a
    person model only the author's own texts are kept unless ``include_others``.
    Texts already in the model are skipped. ``option`` passes ``key=value``
    settings to the sourcer. ``dry_run`` counts without storing.

    The result says how many kept texts are dated in the era of language models,
    because those may not be the author's own words.
    """
    store = _store(model, data_dir=data_dir, files=files)
    meta = store.read_model()
    sourcer = _sources.resolve_sourcer(source)
    low, high = parse_date(since), parse_date(until)
    existing = store.read_docs()
    known = {doc["id"] for doc in existing}
    person = meta["kind"] == "person"
    counts: Counter[str] = Counter()
    added: list[dict[str, Any]] = []
    refs = list(refs or [])
    produced = sourcer(
        *refs,
        since=since,
        until=until,
        limit=limit,
        me=tuple(meta.get("me", [])),
        **_options(option),
    )
    for raw in produced:
        counts["read"] += 1
        try:
            doc = normalize_doc(raw, source=source if isinstance(source, str) else "custom")
        except PenlikeError:
            counts["empty"] += 1
            continue
        if person and doc["is_self"] is False and not include_others:
            counts["by someone else"] += 1
        elif (low or high) and not doc["date"]:
            counts["undated"] += 1
        elif (low and doc["date"] < low) or (high and doc["date"] >= high):
            counts["outside the dates"] += 1
        elif doc["words"] < min_words:
            counts["too short"] += 1
        elif doc["id"] in known:
            counts["already in the model"] += 1
        else:
            known.add(doc["id"])
            added.append(doc)
            if limit and len(added) >= limit:
                break
    in_ai_era = sum(1 for doc in added if doc["date"] and doc["date"] >= parse_date(AI_ERA_START))
    unverified = sum(1 for doc in added if doc["is_self"] is None) if person else 0
    if added and not dry_run:
        store.write_docs(existing + added)
        meta["n_docs"] = len(_live(existing + added))
        meta.setdefault("gathered", []).append(
            {
                "at": _now(),
                "source": str(source),
                "refs": list(refs),
                "since": low,
                "until": high,
                "added": len(added),
            }
        )
        meta["built"] = None
        store.write_model(meta)
    skipped = {k: v for k, v in counts.items() if k != "read"}
    warnings = []
    if in_ai_era:
        warnings.append(
            f"{in_ai_era} of the texts are dated on or after {AI_ERA_START}, when language "
            "models came into general use; some may not be the author's own words. To keep "
            f"them out: penlike screen {store.name} --tier date --run"
        )
    if unverified:
        warnings.append(
            f"{unverified} texts do not say who wrote them; they were kept on trust. Set the "
            "author's addresses with 'me' when making the model to check authorship"
        )
    verb = "would add" if dry_run else "added"
    lines = [f"{verb} {len(added)} texts to {store.name!r} (read {counts['read']})"]
    lines += [f"  skipped, {reason}: {count}" for reason, count in skipped.items()]
    lines += [f"warning: {w}" for w in warnings]
    if added and not dry_run:
        lines.append(f"next: penlike build {store.name}")
    return {
        "ok": True,
        "summary": lines[0],
        "added": len(added),
        "read": counts["read"],
        "skipped": skipped,
        "in_ai_era": in_ai_era,
        "warnings": warnings,
        "text": "\n".join(lines),
    }


def docs(
    model: str | None = None,
    *,
    register: str | None = None,
    excluded: bool = False,
    limit: int = 20,
    full: bool = False,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
) -> dict:
    """List a model's texts: id, date, register and the first words. ``full`` prints whole texts."""
    store = _store(model, data_dir=data_dir, files=files)
    found = [
        doc
        for doc in store.read_docs()
        if bool(doc.get("excluded")) == excluded
        and (not register or doc.get("register") == register)
    ]
    shown = found[:limit] if limit else found
    lines = []
    for doc in shown:
        head = f"{doc['id']}  {(doc['date'] or 'undated')[:10]}  {doc.get('register') or '-'}  {doc['words']}w"
        if doc.get("excluded"):
            head += f"  [excluded: {doc['excluded']}]"
        body = doc["text"] if full else " ".join(doc["text"].split())[:100]
        lines.append(f"{head}\n{body}\n" if full else f"{head}  {body}")
    return {
        "ok": True,
        "summary": f"{len(found)} texts, showing {len(shown)}",
        "docs": shown
        if full
        else [{k: d[k] for k in ("id", "date", "register", "words", "excluded")} for d in shown],
        "text": "\n".join(lines),
    }


def exclude(
    model: str,
    ids: list[str],
    *,
    reason: str = "by hand",
    undo: bool = False,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
) -> dict:
    """Keep texts out of the model without deleting them, or put them back with ``undo``."""
    store = _store(model, data_dir=data_dir, files=files)
    wanted, all_docs = set(ids), store.read_docs()
    changed = 0
    for doc in all_docs:
        if doc["id"] in wanted and bool(doc.get("excluded")) == undo:
            doc["excluded"] = None if undo else reason
            changed += 1
    missing = wanted - {doc["id"] for doc in all_docs}
    if changed:
        store.write_docs(all_docs)
        meta = store.read_model()
        meta.update(n_docs=len(_live(all_docs)), built=None)
        store.write_model(meta)
    verb = "put back" if undo else "excluded"
    return {
        "ok": not missing,
        "summary": f"{verb} {changed} texts"
        + (f"; not found: {', '.join(sorted(missing))}" if missing else ""),
        "changed": changed,
    }


def screen(
    model: str,
    *,
    tier: str = "date",
    cutoff: str = AI_ERA_START,
    run: bool = False,
    sample: int = 5,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
) -> dict:
    """Screen a model's texts for machine-written content. States the cost first.

    Tiers: date (free), cheap (no model), heavy (local models), agent (tokens).
    Without ``run`` nothing is changed: the call reports what the tier does, what it
    costs on this corpus, and for the date tier how many texts it would exclude.
    With ``run`` the flagged texts are excluded (never deleted; ``exclude --undo``
    puts them back).
    """
    store = _store(model, data_dir=data_dir, files=files)
    all_docs = store.read_docs()
    result = _screen.screen(all_docs, tier=tier, cutoff=cutoff, run=run, sample=sample)
    plan, flagged = result["plan"], set(result["flagged"])
    lines = [
        f"tier {tier}: {plan['does']}",
        f"cost: {plan['costs']}",
        f"needs: {plan['needs']}",
        f"corpus: {plan['documents']} texts, {plan['words']} words",
    ]
    if "estimated_seconds" in plan:
        lines.append(
            f"timed {plan['sample']['documents']} texts in {plan['sample']['seconds']}s; "
            f"the full run should take about {plan['estimated_seconds']}s"
        )
    applied = 0
    if result["ran"] and run:
        for doc in all_docs:
            if doc["id"] in flagged:
                doc["excluded"] = f"screen:{tier}"
                doc.setdefault("flags", {})["screen"] = result["findings"][doc["id"]]
                applied += 1
        if applied:
            store.write_docs(all_docs)
            meta = store.read_model()
            meta.update(n_docs=len(_live(all_docs)), built=None)
            store.write_model(meta)
        lines.append(f"excluded {applied} texts; rebuild with: penlike build {store.name}")
    elif result["ran"]:
        lines.append(f"would exclude {len(flagged)} texts; repeat with --run to do it")
    else:
        lines.append("nothing was run; repeat with --run to screen the whole corpus")
    if result.get("undated"):
        lines.append(f"{len(result['undated'])} texts have no date and were left in")
    if tier in ("cheap", "heavy"):
        lines.append(
            "a detector accuses some human writing and misses some machine writing; "
            "read what it flags before trusting it (penlike docs --excluded)"
        )
    return {
        "ok": True,
        "summary": lines[-1]
        if not result["ran"]
        else f"{tier}: {len(flagged)} flagged, {applied} excluded",
        "plan": plan,
        "flagged": sorted(flagged),
        "excluded": applied,
        "text": "\n".join(lines),
    }


# -- building ------------------------------------------------------------------------


def _register_lines(records: Mapping[str, Mapping[str, Any]]) -> str:
    if not records:
        return "registers: none yet"
    lines = ["registers:"]
    for rid, record in sorted(records.items(), key=lambda item: -item[1].get("n_docs", 0)):
        name = f" ({record['name']})" if record.get("name") and record["name"] != rid else ""
        parent = f", within {record['parent']}" if record.get("parent") else ""
        rough = ", provisional" if record.get("provisional") else ""
        lines.append(
            f"  {rid}{name}: {record.get('n_docs', 0)} texts, {record.get('n_words', 0)} words{parent}{rough}"
        )
        if record.get("description"):
            lines.append(f"      {record['description']}")
    return "\n".join(lines)


def build(
    model: str | None = None,
    *,
    reference: str | None = None,
    situate: str | None = None,
    lam: float = _registers.DEFAULT_LAM,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
) -> dict:
    """File every text under a register and measure each register's profile.

    Texts are filed by situation (``situate``, a ``module:function`` reference,
    replaces the rule). Texts that a person assigned by hand stay where they were
    put. Where a register has named finer registers, each new text joins the
    nearest one if it is within ``lam`` of it, and otherwise waits in the parent.

    ``reference`` names another model to contrast with (a population, a sector).
    Without it each register is contrasted with the author's other registers.
    """
    store = _store(model, data_dir=data_dir, files=files)
    rule = _sources.resolve_sourcer(situate) if situate else _registers.situate
    all_docs = store.read_docs()
    live = _live(all_docs)
    if not live:
        raise PenlikeError(
            f"{store.name!r} has no texts; add some with: penlike gather {store.name} <source> <references>"
        )
    records = store.read_registers()
    for doc in live:
        if not doc.get("pinned"):
            doc["register"] = rule(doc)
    measured = {doc["id"]: _measure(doc["text"]) for doc in live}
    norm = build_norm(measured.values())
    vectors = {doc_id: style_vector(m, norm["style"]) for doc_id, m in measured.items()}

    children: dict[str, list[str]] = {}
    for rid, record in records.items():
        if record.get("parent"):
            children.setdefault(record["parent"], []).append(rid)
    for parent, kids in children.items():
        centroids = {}
        for kid in kids:
            members = [vectors[d["id"]] for d in live if d.get("pinned") and d["register"] == kid]
            if members:
                centroids[kid] = [sum(c) / len(c) for c in zip(*members)]
        for doc in live:
            if doc.get("pinned") or doc["register"] != parent or not centroids:
                continue
            kid, distance = _registers.nearest(vectors[doc["id"]], centroids)
            if kid and distance <= lam:
                doc["register"] = kid

    by_register: dict[str, list[dict[str, Any]]] = {}
    for doc in live:
        by_register.setdefault(doc["register"], []).append(doc)
    reference_profile = None
    if reference:
        other = ModelStore(reference, data_dir=data_dir, files=files).require()
        reference_profile = (other.read_profile(_NORM) or {}).get("profile")
        if not reference_profile:
            raise PenlikeError(
                f"the reference model {reference!r} is not built; run: penlike build {reference}"
            )

    store.clear_profiles()
    for rid, members in by_register.items():
        inside = [measured[d["id"]] for d in members]
        outside = [m for doc_id, m in measured.items() if doc_id not in {d["id"] for d in members}]
        profile = build_profile(inside, register=rid, norm=norm, others=outside)
        against = reference_profile or (build_profile(outside) if outside else None)
        profile["reference"] = reference or ("the author's other registers" if outside else None)
        profile["differences"] = contrast(profile, against) if against else None
        dates = sorted(d["date"] for d in members if d.get("date"))
        profile["dates"] = [dates[0][:10], dates[-1][:10]] if dates else None
        store.write_profile(rid, profile)
        record = records.setdefault(
            rid, {"name": rid, "description": "", "parent": None, "created": _now()}
        )
        record.update(
            n_docs=profile["n_docs"], n_words=profile["n_words"],
            provisional=profile["provisional"], dates=profile["dates"],
        )  # fmt: skip
    for rid, record in records.items():
        if rid not in by_register:
            record.update(n_docs=0, n_words=0)
    store.write_profile(
        _NORM, {"norm": norm, "profile": build_profile(measured.values(), register=_NORM)}
    )
    store.write_registers(records)
    store.write_docs(all_docs)
    meta = store.read_model()
    meta.update(n_docs=len(live), built=_now())
    store.write_model(meta)
    text = f"built {store.name!r} from {len(live)} texts\n" + _register_lines(records)
    rough = [rid for rid, r in records.items() if r.get("provisional") and r.get("n_docs")]
    if rough:
        text += (
            "\nprovisional registers rest on little text; their figures are rough: "
            + ", ".join(rough)
        )
    return {
        "ok": True,
        "summary": f"built {store.name!r}: {len(live)} texts in {len(by_register)} registers",
        "registers": records,
        "text": text,
    }


def _built(store: ModelStore) -> tuple[dict[str, Any], dict[str, Any]]:
    records, norm = store.read_registers(), store.read_profile(_NORM)
    if not norm or not store.read_model().get("built"):
        raise PenlikeError(
            f"{store.name!r} changed since it was last built, or never was; run: penlike build {store.name}"
        )
    return records, norm["norm"]


def registers(
    model: str | None = None,
    *,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
) -> dict:
    """List a model's registers: how much text each rests on, and what it was named."""
    store = _store(model, data_dir=data_dir, files=files)
    records = store.read_registers()
    return {
        "ok": True,
        "summary": f"{len(records)} registers",
        "registers": records,
        "text": _register_lines(records),
    }


def propose(
    model: str | None = None,
    *,
    lam: float = _registers.DEFAULT_LAM,
    min_size: int = 5,
    min_separation: float = _registers.DEFAULT_MIN_SEPARATION,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
) -> dict:
    """Look for registers nobody named yet: groups of texts that are written differently.

    Returns proposals, each with the texts in it, what sets it apart and whom the
    texts were for. Read a few of its ``typical_docs``, then name it with
    ``register-add --proposal``. Lower ``lam`` to find finer groups, and
    ``min_separation`` to see groups that stand less clearly apart.
    """
    store = _store(model, data_dir=data_dir, files=files)
    _, norm = _built(store)
    live = _live(store.read_docs())
    vectors = {doc["id"]: style_vector(_measure(doc["text"]), norm["style"]) for doc in live}
    found = _registers.propose(
        live, vectors, lam=lam, min_size=min_size, min_separation=min_separation
    )
    lines = []
    for p in found:
        lines.append(
            f"{p['proposal']}: {p['n_docs']} texts within {p['parent']} (separation {p['separation']})"
        )
        if p["differs_by"]:
            lines.append("    differs by " + "; ".join(p["differs_by"]))
        if p["mostly_to"]:
            lines.append("    mostly to " + ", ".join(p["mostly_to"]))
        lines.append("    read: penlike docs --full  (ids " + ", ".join(p["typical_docs"]) + ")")
    text = (
        "\n".join(lines)
        if lines
        else (
            "No register splits into separate groups at these settings. Lower --lam for finer groups."
        )
    )
    return {"ok": True, "summary": f"{len(found)} proposal(s)", "proposals": found, "text": text}


def register_add(
    model: str,
    name: str,
    *,
    parent: str | None = None,
    description: str = "",
    proposal: str | None = None,
    docs: list[str] | None = None,
    lam: float = _registers.DEFAULT_LAM,
    min_size: int = 5,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
) -> dict:
    """Name a register and put texts in it, from a proposal or from a list of text ids.

    The texts are pinned there, and they are what later texts are compared with.
    Use the same ``lam`` and ``min_size`` as the ``propose`` call the proposal came from.
    """
    store = _store(model, data_dir=data_dir, files=files)
    check_name(name)
    records = store.read_registers()
    if name in records or name in (GENERAL, _NORM):
        raise PenlikeError(f"a register named {name!r} already exists or is reserved")
    ids = set(docs or [])
    if proposal:
        found = propose(store.name, lam=lam, min_size=min_size, data_dir=data_dir, files=files)
        match = [p for p in found["proposals"] if p["proposal"] == proposal]
        if not match:
            raise PenlikeError(
                f"no proposal {proposal!r} at these settings; run: penlike propose {store.name}"
            )
        ids |= set(match[0]["docs"])
        parent = parent or match[0]["parent"]
    if not ids:
        raise PenlikeError(
            "give the texts of the register: --proposal <id> or --docs <id> <id> ..."
        )
    if parent and parent not in records:
        raise PenlikeError(f"no register named {parent!r} to put it within")
    all_docs = store.read_docs()
    moved = 0
    for doc in all_docs:
        if doc["id"] in ids:
            doc.update(register=name, pinned=True)
            moved += 1
    records[name] = {"name": name, "description": description, "parent": parent, "created": _now()}
    store.write_registers(records)
    store.write_docs(all_docs)
    rebuilt = build(store.name, data_dir=data_dir, files=files)
    return {
        "ok": True,
        "summary": f"added the register {name!r} with {moved} texts",
        "registers": rebuilt["registers"],
        "text": rebuilt["text"],
    }


def register_edit(
    model: str,
    register: str,
    *,
    name: str | None = None,
    description: str | None = None,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
) -> dict:
    """Give a register a display name or a description. Its identifier never changes."""
    store = _store(model, data_dir=data_dir, files=files)
    records = store.read_registers()
    if register not in records:
        raise PenlikeError(f"no register {register!r}; there are: {', '.join(sorted(records))}")
    if name is not None:
        records[register]["name"] = name
    if description is not None:
        records[register]["description"] = description
    store.write_registers(records)
    return {"ok": True, "summary": f"updated {register!r}", "register": records[register]}


def register_merge(
    model: str,
    register: str,
    into: str,
    *,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
) -> dict:
    """Merge one register into another, when the two turn out to be written the same way."""
    store = _store(model, data_dir=data_dir, files=files)
    records = store.read_registers()
    for rid in (register, into):
        if rid not in records:
            raise PenlikeError(f"no register {rid!r}; there are: {', '.join(sorted(records))}")
    all_docs = store.read_docs()
    moved = 0
    for doc in all_docs:
        if doc.get("register") == register:
            doc.update(register=into, pinned=True)
            moved += 1
    del records[register]
    for record in records.values():
        if record.get("parent") == register:
            record["parent"] = into
    notes_text = store.read_notes(register)
    if notes_text:
        store.write_notes(into, (store.read_notes(into) + "\n" + notes_text).strip() + "\n")
        store.write_notes(register, "")
    store.write_registers(records)
    store.write_docs(all_docs)
    rebuilt = build(store.name, data_dir=data_dir, files=files)
    return {
        "ok": True,
        "summary": f"merged {register!r} into {into!r} ({moved} texts)",
        "text": rebuilt["text"],
    }


def assign(
    model: str,
    register: str,
    ids: list[str],
    *,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
) -> dict:
    """File texts under a register by hand. The choice is kept through every later build."""
    store = _store(model, data_dir=data_dir, files=files)
    records = store.read_registers()
    if register not in records:
        raise PenlikeError(f"no register {register!r}; there are: {', '.join(sorted(records))}")
    all_docs, wanted, moved = store.read_docs(), set(ids), 0
    for doc in all_docs:
        if doc["id"] in wanted:
            doc.update(register=register, pinned=True)
            moved += 1
    store.write_docs(all_docs)
    meta = store.read_model()
    meta["built"] = None
    store.write_model(meta)
    return {
        "ok": moved == len(wanted),
        "summary": f"filed {moved} texts under {register!r}; rebuild to update the profiles",
    }


# -- notes ---------------------------------------------------------------------------

_NOTE_SECTIONS = {
    "observation": "## Observations",
    "hypothesis": "## Hypotheses (not yet supported; never act on these alone)",
}


def note(
    model: str,
    text: str,
    *,
    register: str = GENERAL,
    source: str | None = None,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
) -> dict:
    """Record something about how the author writes that numbers do not capture.

    For example how they open a request, what they explain and what they assume,
    how they disagree. ``source`` says what the note rests on (text ids, such as
    ``doc:3f2a...``); a note without one is filed as a hypothesis. ``register`` is
    ``general`` for what holds everywhere.
    """
    store = _store(model, data_dir=data_dir, files=files)
    if register != GENERAL and register not in store.read_registers():
        raise PenlikeError(
            f"no register {register!r}; use one of the model's registers or {GENERAL!r}"
        )
    line = " ".join(text.split())
    if not line:
        raise PenlikeError("the note is empty")
    kind = "observation" if source else "hypothesis"
    entry = f"- {line} [source: {source}]" if source else f"- {line}"
    current = store.read_notes(register) or f"# Notes on {store.name}, register {register}\n"
    heading = _NOTE_SECTIONS[kind]
    if heading in current:
        head, _, tail = current.partition(heading)
        section, separator, rest = tail.partition("\n## ")
        current = (
            head
            + heading
            + section.rstrip("\n")
            + "\n"
            + entry
            + "\n"
            + (("\n## " + rest) if separator else "")
        )
    else:
        current = current.rstrip("\n") + f"\n\n{heading}\n\n{entry}\n"
    store.write_notes(register, current)
    return {"ok": True, "summary": f"recorded one {kind} on {register!r}", "kind": kind}


def notes(
    model: str | None = None,
    *,
    register: str | None = None,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
) -> dict:
    """Read the notes on a model: one register's, or all of them."""
    store = _store(model, data_dir=data_dir, files=files)
    wanted = [register] if register else store.note_registers()
    found = {rid: store.read_notes(rid) for rid in wanted if store.read_notes(rid).strip()}
    text = "\n\n".join(found.values()) if found else "No notes yet. Record one with: penlike note"
    return {
        "ok": True,
        "summary": f"notes on {len(found)} register(s)",
        "notes": found,
        "text": text,
    }


# -- writing -------------------------------------------------------------------------


def route(
    *,
    like: str | None = None,
    style: str | None = None,
    channel: str | None = None,
    to: list[str] | None = None,
    audience: str | None = None,
    reply: bool = False,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
) -> dict:
    """Choose the register for a piece of writing, and say why it was chosen.

    Name a ``style``, or describe the situation: the ``channel`` (email, github,
    ...), whom it is ``to``, the ``audience`` size (one, few, many, public), and
    whether it is a ``reply``. With nothing given, the register with the most text
    is returned and marked as a fallback.
    """
    store = _store(like, data_dir=data_dir, files=files)
    records, _ = _built(store)
    chosen = _registers.route(
        records, store.read_docs(), style=style, channel=channel, to=to or (),
        audience=audience, reply=reply if (reply or channel == "github") else None,
    )  # fmt: skip
    text = f"{chosen['register']} ({chosen['how']}): {chosen['reason']}"
    if chosen["alternatives"]:
        text += "\nother registers: " + ", ".join(chosen["alternatives"])
    return {"ok": True, "summary": text.split("\n")[0], "model": store.name, **chosen, "text": text}


def exemplars(
    *,
    like: str | None = None,
    style: str | None = None,
    channel: str | None = None,
    to: list[str] | None = None,
    audience: str | None = None,
    reply: bool = False,
    n: int = 5,
    words: int | None = None,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
) -> dict:
    """Pick texts by the author to show as examples, for the register the request routes to.

    Texts to the same readers come first, then a spread over readers and dates.
    ``words`` prefers examples near the length of what is to be written.
    """
    chosen = route(
        like=like,
        style=style,
        channel=channel,
        to=to,
        audience=audience,
        reply=reply,
        data_dir=data_dir,
        files=files,
    )
    store = _store(chosen["model"], data_dir=data_dir, files=files)
    members = [d for d in store.read_docs() if d.get("register") == chosen["register"]]
    picked = _registers.select_exemplars(members, n=n, to=to or (), words=words)
    shown = [
        {"id": d["id"], "date": (d["date"] or "")[:10], "words": d["words"], "text": d["text"]}
        for d in picked
    ]
    blocks = [
        f'<example id="{d["id"]}" date="{d["date"] or "undated"}">\n{d["text"]}\n</example>'
        for d in shown
    ]
    return {
        "ok": bool(shown),
        "summary": f"{len(shown)} examples from {chosen['register']}",
        "register": chosen["register"],
        "exemplars": shown,
        "text": "\n\n".join(blocks),
    }


def brief(
    *,
    like: str | None = None,
    style: str | None = None,
    channel: str | None = None,
    to: list[str] | None = None,
    audience: str | None = None,
    reply: bool = False,
    n: int = 5,
    words: int | None = None,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
) -> dict:
    """Everything needed to write in an author's style, for one piece of writing.

    Routes the request to a register, then returns that register's measured
    profile, the notes on it, and examples by the author. Read it before
    drafting; check the draft against the same register afterwards.
    """
    chosen = route(
        like=like,
        style=style,
        channel=channel,
        to=to,
        audience=audience,
        reply=reply,
        data_dir=data_dir,
        files=files,
    )
    store = _store(chosen["model"], data_dir=data_dir, files=files)
    meta = store.read_model()
    rid = chosen["register"]
    record = store.read_registers()[rid]
    profile = store.read_profile(rid) or {}
    found = exemplars(
        like=store.name, style=rid, to=to, n=n, words=words, data_dir=data_dir, files=files
    )
    subject = {"person": "the author", "group": "this group", "corpus": "this corpus"}[meta["kind"]]
    parts = [
        f"# Writing like {store.name} ({meta['kind']}): register {record.get('name') or rid}",
        f"Register chosen: {rid}, by {chosen['how']}. {chosen['reason']}.",
    ]
    if record.get("description"):
        parts.append(record["description"])
    if chosen["how"] in ("fallback", "channel"):
        parts.append(
            "This register is a guess. If the writing is for another situation, ask which of "
            "these fits: " + ", ".join([rid, *chosen["alternatives"]])
        )
    parts += [
        "",
        f"## How {subject} writes here, measured",
        render_profile(profile, differences=profile.get("differences")),
    ]
    for scope in (GENERAL, rid):
        text = store.read_notes(scope).strip()
        if text:
            parts += ["", f"## Notes ({scope})", text]
    parts += [
        "",
        f"## Examples by {subject}",
        "Take the style from these, never the content. They are private: do not quote them in what you write.",
        found["text"] or "(no example of usable length in this register)",
        "",
        "## After drafting",
        f"Check the draft against this register: penlike check <draft> --like {store.name} --style {rid}",
        "Change what it reports, and check once more. Stop after two rounds.",
        "",
        _RESPONSIBLE_USE
        if meta.get("basis") != "self" or meta["kind"] != "person"
        else "This is a model of its own author. What is written with it is theirs to approve before it is sent.",
    ]
    return {
        "ok": True,
        "summary": f"brief for {store.name}, register {rid} ({chosen['how']})",
        "model": store.name,
        "register": rid,
        "how": chosen["how"],
        "provisional": bool(profile.get("provisional")),
        "text": "\n".join(parts),
    }


def measure(text: str) -> dict:
    """Measure one text's style, on its own: lengths, punctuation, habits, greeting and closing."""
    found = _measure(text)
    lean = {
        k: found[k]
        for k in (
            "n_words",
            "n_sentences",
            "scalars",
            "presence",
            "greeting",
            "signoff",
            "signature",
        )
    }
    lines = [f"{found['n_words']} words, {found['n_sentences']} sentences"]
    lines += [f"{name}: {value}" for name, value in found["scalars"].items() if value is not None]
    lines += [f"{name}: yes" for name, value in found["presence"].items() if value]
    return {"ok": True, "summary": lines[0], **lean, "text": "\n".join(lines)}


def check(
    text: str,
    *,
    like: str | None = None,
    style: str | None = None,
    channel: str | None = None,
    to: list[str] | None = None,
    audience: str | None = None,
    reply: bool = False,
    threshold: float = 2.0,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
) -> dict:
    """Measure a draft against the author's register and list what differs.

    Each discrepancy gives the draft's figure and the author's usual one, so it can
    be acted on. ``ok`` is true when nothing differs by more than ``threshold`` of
    the author's own spread. Passing the check means the measurable surface
    matches; it does not mean the draft would pass for the author's.
    """
    chosen = route(
        like=like,
        style=style,
        channel=channel,
        to=to,
        audience=audience,
        reply=reply,
        data_dir=data_dir,
        files=files,
    )
    store = _store(chosen["model"], data_dir=data_dir, files=files)
    _, norm = _built(store)
    profile = store.read_profile(chosen["register"]) or {}
    result = compare(_measure(text), profile, norm=norm, threshold=threshold)
    found = result["discrepancies"]
    lines = [f"checked against {store.name}, register {chosen['register']} ({chosen['how']})"]
    lines += [f"- {d['message']}" for d in found] or [
        "nothing measurable differs from the author's usual"
    ]
    distance = result["function_word_distance"]
    if distance:
        own = distance["own"]
        verdict = "within" if distance["within_own_range"] else "outside"
        lines.append(
            f"function-word distance {distance['value']:g}: {verdict} the range of the author's own "
            f"texts (mean {own['mean']:g}, spread {own['sd']:g}, over {own['n']} texts)"
        )
    else:
        lines.append(
            "function-word distance: not measured (the draft or the register is too short for it)"
        )
    if result["provisional"]:
        lines.append("the register rests on little text, so these figures are rough")
    return {
        "ok": not found,
        "summary": f"{len(found)} discrepancies against {chosen['register']}",
        "model": store.name,
        "register": chosen["register"],
        **result,
        "text": "\n".join(lines),
    }


@host_mutating
def batches(
    model: str,
    *,
    register: str | None = None,
    size: int = 30,
    data_dir: str | None = None,
    files: MutableMapping | None = None,
) -> dict:
    """Write a register's texts into batch files for reader agents, and return their paths.

    The files go under the data root (``work/<model>/``), never into a project
    folder. Each holds ``size`` texts with their ids, so that a note can cite them.
    """
    store = _store(model, data_dir=data_dir, files=files)
    members = [d for d in _live(store.read_docs()) if not register or d.get("register") == register]
    if not members:
        raise PenlikeError("no texts to batch; build the model, or check the register name")
    members.sort(key=lambda d: (d.get("register") or "", d.get("date") or ""))
    prefix = f"work/{store.name}/"
    for key in [k for k in store.files if k.startswith(prefix)]:
        del store.files[key]
    written = []
    for index in range(0, len(members), size):
        chunk = members[index : index + size]
        rid = register or "all"
        key = f"{prefix}{rid}-batch-{index // size + 1:03d}.md"
        blocks = [
            f"## doc:{d['id']}\nregister: {d.get('register')}\ndate: {(d.get('date') or 'undated')[:10]}\n"
            f"readers: {len(d.get('to', []))}\n\n{d['text']}\n"
            for d in chunk
        ]
        store.files[key] = f"# {store.name}, batch {index // size + 1}\n\n" + "\n---\n\n".join(
            blocks
        )
        written.append(key)
    root = _data_dir(data_dir) if files is None else None
    paths = [str(root / key) if root else key for key in written]
    return {
        "ok": True,
        "summary": f"wrote {len(paths)} batch files ({len(members)} texts)",
        "paths": paths,
        "text": "\n".join(paths),
    }


@host_mutating
def install_skills(*, target: str | None = None, write: bool = False) -> dict:
    """Link the skills and agents shipped with penlike into an agent host's folders.

    The target defaults to ``~/.claude``. Without ``write`` it only says what it would do.

    >>> result = install_skills()
    >>> result["dry_run"], len(result["skills"]) > 0
    (True, True)
    """
    from importlib.resources import files as resource_files
    from pathlib import Path

    base = Path(str(resource_files("penlike.data")))
    host = Path(target).expanduser() if target else Path.home() / ".claude"
    actions = []
    for kind, pattern in (("skills", "*/SKILL.md"), ("agents", "*.md")):
        for found in sorted((base / kind).glob(pattern)):
            item = found.parent if kind == "skills" else found
            link = host / kind / item.name
            state = "exists" if link.exists() or link.is_symlink() else "new"
            actions.append({"kind": kind, "name": item.name, "link": str(link), "state": state})
            if write and state == "new":
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(item)
    lines = [f"{a['kind']}/{a['name']}: {a['state']}" for a in actions]
    if not write:
        lines.append("nothing was changed; repeat with --write to link them")
    return {
        "ok": True,
        "summary": f"{len(actions)} skills and agents" + ("" if write else " (dry run)"),
        "dry_run": not write,
        "target": str(host),
        "skills": actions,
        "text": "\n".join(lines),
    }


#: The single list every surface is built from.
TOOLS = [
    models, new, use, show, remove,
    sources, gather, docs, exclude, screen,
    build, registers, propose, register_add, register_edit, register_merge, assign,
    note, notes,
    route, exemplars, brief, measure, check,
    batches, install_skills,
]  # fmt: skip
