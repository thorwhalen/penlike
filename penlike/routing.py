"""Registers: filing texts by situation, finding new ones, and routing a request to one.

A register is defined by the *situation* a text was written in (channel, who it
was for, reply or opening) and only then described by its language. So the first
key is situational and costs nothing to compute (:func:`situate`). Language comes
second, as a check on that key: when the texts filed under one situation fall into
clearly separate groups, :func:`propose` reports the groups so that a person can
name them. Named registers keep their identifier for good; nothing is renumbered
when more text arrives.

>>> situate({"channel": "email", "audience": "one"})
'email.one'
>>> situate({"channel": "github", "reply": True})
'github.reply'
>>> situate({"channel": "document"})
'document'
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from penlike.base import PenlikeError
from penlike.profile import LABELS, VECTOR_FEATURES, vector_distance

__all__ = [
    "DEFAULT_LAM",
    "DEFAULT_MIN_SEPARATION",
    "dp_means",
    "nearest",
    "propose",
    "route",
    "select_exemplars",
    "situate",
]

#: How far (in root-mean-square z-scores) a text must be from every centre to start a group.
DEFAULT_LAM = 1.25
#: How far apart a group must stand, relative to its own spread, to be proposed.
DEFAULT_MIN_SEPARATION = 1.6

_UNSAFE_RE = re.compile(r"[^a-z0-9._-]+")


def situate(doc: Mapping[str, Any]) -> str:
    """The situational register of a document, from its metadata alone.

    Email is filed by how many people it was for, GitHub writing by whether it
    opens a thread or answers in one, agent prompts and plain documents each under
    one key. Any other channel is filed as ``<channel>.<audience>``.
    """
    channel = str(doc.get("channel") or "document").lower()
    audience = str(doc.get("audience") or "unknown").lower()
    if channel == "github":
        key = "github.reply" if doc.get("reply") else "github.post"
    elif channel in ("document", "agent"):
        key = channel
    elif audience in ("unknown", ""):
        key = channel
    else:
        key = f"{channel}.{audience}"
    return _UNSAFE_RE.sub("-", key).strip("-.") or "document"


def dp_means(vectors: Sequence[Sequence[float]], *, lam: float, max_iter: int = 20) -> list[int]:
    """Cluster vectors without fixing the number of clusters (DP-means).

    A vector further than ``lam`` from every centre opens a new cluster; otherwise it
    joins the nearest. One parameter, deterministic, and sequential by nature, which
    is what registers that appear over time need.

    >>> dp_means([[0.0], [0.1], [5.0], [5.1]], lam=1.0)
    [0, 0, 1, 1]
    """
    if not vectors:
        return []
    centres = [list(vectors[0])]
    labels = [0] * len(vectors)
    for _ in range(max_iter):
        changed = False
        for index, vector in enumerate(vectors):
            distances = [vector_distance(vector, centre) for centre in centres]
            best = min(range(len(centres)), key=distances.__getitem__)
            if distances[best] > lam:
                centres.append(list(vector))
                best = len(centres) - 1
            if labels[index] != best:
                labels[index], changed = best, True
        members: dict[int, list[Sequence[float]]] = defaultdict(list)
        for label, vector in zip(labels, vectors):
            members[label].append(vector)
        order = sorted(members)  # drop emptied clusters, keep the order of appearance
        centres = [[sum(c) / len(c) for c in zip(*members[label])] for label in order]
        renumber = {label: position for position, label in enumerate(order)}
        labels = [renumber[label] for label in labels]
        if not changed:
            break
    return labels


def nearest(
    vector: Sequence[float], centroids: Mapping[str, Sequence[float]]
) -> tuple[str | None, float]:
    """The closest centroid to a vector, and the distance to it.

    >>> nearest([0.0, 0.0], {"a": [0.0, 1.0], "b": [3.0, 3.0]})
    ('a', 0.7071)
    """
    best, distance = None, float("inf")
    for name, centroid in centroids.items():
        d = vector_distance(vector, centroid)
        if d < distance:
            best, distance = name, d
    return best, distance


def _top_differences(
    group: Sequence[Sequence[float]], rest: Sequence[Sequence[float]], *, top: int = 4
) -> list[str]:
    """The features on which a group's vectors differ most from the rest, in words."""
    if not group or not rest:
        return []
    found = []
    for position, name in enumerate(VECTOR_FEATURES):
        here = sum(v[position] for v in group) / len(group)
        there = sum(v[position] for v in rest) / len(rest)
        if abs(here - there) >= 0.75:
            label = "length" if name == "log_words" else LABELS[name]
            found.append((abs(here - there), f"{'more' if here > there else 'less'}: {label}"))
    return [text for _, text in sorted(found, reverse=True)[:top]]


def propose(
    docs: Sequence[Mapping[str, Any]],
    vectors: Mapping[str, Sequence[float]],
    *,
    lam: float = DEFAULT_LAM,
    min_size: int = 5,
    min_separation: float = DEFAULT_MIN_SEPARATION,
) -> list[dict[str, Any]]:
    """Look inside each register for separate groups of texts that could be registers.

    Texts a person filed by hand are left alone. A group is proposed only when its
    register holds at least two groups of ``min_size`` texts or more, and when the
    group stands apart: the distance from its centre to the centre of the rest,
    divided by the mean distance of its own texts to its centre, must reach
    ``min_separation``. Any set of texts can be cut in two; that ratio is what
    tells a cut from a difference.

    ``lam`` (how different a text must be to start a group), ``min_size`` and
    ``min_separation`` are settings to adjust, not constants to trust. The defaults
    were set on synthetic text; no published study validates values for personal
    correspondence. A proposal is a question to a person, never a decision.

    Each proposal names the texts, the features that set the group apart and whom
    the texts were mostly for, which is what is needed to give it a name.
    """
    by_register: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for doc in docs:
        if doc.get("excluded") or doc.get("pinned") or doc["id"] not in vectors:
            continue
        by_register[doc["register"]].append(doc)
    proposals = []
    for register, members in sorted(by_register.items()):
        if len(members) < 2 * min_size:
            continue
        member_vectors = [vectors[doc["id"]] for doc in members]
        labels = dp_means(member_vectors, lam=lam)
        sizes = Counter(labels)
        groups = [label for label, size in sizes.most_common() if size >= min_size]
        if len(groups) < 2:
            continue
        for rank, label in enumerate(groups, 1):
            inside = [i for i, l in enumerate(labels) if l == label]
            outside = [i for i, l in enumerate(labels) if l != label]
            group_vectors = [member_vectors[i] for i in inside]
            centre = [sum(c) / len(c) for c in zip(*group_vectors)]
            ranked = sorted(inside, key=lambda i: vector_distance(member_vectors[i], centre))
            rest = [member_vectors[i] for i in outside]
            rest_centre = [sum(c) / len(c) for c in zip(*rest)]
            spread = sum(vector_distance(v, centre) for v in group_vectors) / len(group_vectors)
            separation = round(vector_distance(centre, rest_centre) / max(spread, 1e-9), 2)
            if separation < min_separation:
                continue
            readers = Counter(reader for i in inside for reader in members[i].get("to", []))
            proposals.append(
                {
                    "proposal": f"{register}#{rank}",
                    "parent": register,
                    "n_docs": len(inside),
                    "separation": separation,
                    "differs_by": _top_differences(
                        group_vectors, [member_vectors[i] for i in outside]
                    ),
                    "mostly_to": [reader for reader, _ in readers.most_common(5)],
                    "typical_docs": [members[i]["id"] for i in ranked[:3]],
                    "docs": [members[i]["id"] for i in inside],
                }
            )
    return proposals


def _match_style(style: str, registers: Mapping[str, Mapping[str, Any]]) -> list[str]:
    wanted = style.strip().lower()
    exact = [
        rid
        for rid, record in registers.items()
        if wanted in (rid.lower(), str(record.get("name") or "").lower())
    ]
    if exact:
        return exact
    return [
        rid
        for rid, record in registers.items()
        if wanted in rid.lower()
        or wanted in str(record.get("name") or "").lower()
        or wanted in str(record.get("description") or "").lower()
    ]


def route(
    registers: Mapping[str, Mapping[str, Any]],
    docs: Sequence[Mapping[str, Any]],
    *,
    style: str | None = None,
    channel: str | None = None,
    to: Sequence[str] = (),
    audience: str | None = None,
    reply: bool | None = None,
    situate: Callable[[Mapping[str, Any]], str] = situate,
) -> dict[str, Any]:
    """Choose the register for a piece of writing, and say why.

    In order: the style that was named; the register the author has used most with
    these readers; the register of the situation described (channel, audience,
    reply); and last the register with the most text, reported as a fallback so
    that nobody mistakes a guess for a match.
    """
    usable = {rid: r for rid, r in registers.items() if r.get("n_docs")}
    if not usable:
        raise PenlikeError("the model has no registers yet; run: penlike build <model>")
    listing = sorted(usable, key=lambda rid: -usable[rid]["n_docs"])

    def chosen(rid: str, how: str, reason: str) -> dict[str, Any]:
        return {
            "register": rid,
            "name": usable[rid].get("name") or rid,
            "how": how,
            "reason": reason,
            "alternatives": [r for r in listing if r != rid][:6],
        }

    if style:
        matches = [rid for rid in _match_style(style, registers) if rid in usable]
        if len(matches) == 1:
            return chosen(matches[0], "named", f"the style {style!r} was asked for")
        found = ", ".join(matches) if matches else "none"
        raise PenlikeError(
            f"the style {style!r} matches {found}; the registers are: {', '.join(listing)}"
        )
    readers = {r.lower() for r in to}
    if readers:
        used = Counter(
            doc["register"]
            for doc in docs
            if not doc.get("excluded")
            and doc.get("register") in usable
            and readers & {r.lower() for r in doc.get("to", [])}
            and (not channel or doc.get("channel") == channel)
        )
        if used:
            rid, count = used.most_common(1)[0]
            return chosen(
                rid, "readers", f"{count} earlier texts to these readers are in this register"
            )
    if channel or audience or reply is not None:
        described = {
            "channel": channel or "document",
            "audience": audience
            or (("one" if len(readers) == 1 else "few") if readers else "unknown"),
            "reply": reply,
        }
        key = situate(described)
        if key in usable:
            children = [rid for rid, r in usable.items() if r.get("parent") == key]
            note = (
                f"; it has finer registers you can name instead: {', '.join(children)}"
                if children
                else ""
            )
            return chosen(key, "situation", f"the situation described is {key}{note}")
        same_channel = [rid for rid in listing if rid.split(".")[0] == key.split(".")[0]]
        if same_channel:
            return chosen(
                same_channel[0],
                "channel",
                f"no texts were written in the situation {key}; this is the author's "
                "largest register on the same channel",
            )
    return chosen(
        listing[0],
        "fallback",
        "nothing about the situation was given, or nothing matched; this is the register "
        "with the most text. Name a style or describe the situation for a better match",
    )


def select_exemplars(
    docs: Sequence[Mapping[str, Any]],
    *,
    n: int = 5,
    to: Sequence[str] = (),
    words: int | None = None,
    min_words: int = 15,
    max_words: int = 400,
) -> list[Mapping[str, Any]]:
    """Pick the texts to show as examples of a register.

    Texts to the same readers come first. After that the choice is for *spread*, not
    for similarity of topic to the task: one text per reader or thread in turn,
    newest first, because examples narrow in topic pull the imitation toward their
    content and away from the style. ``words`` prefers texts near a target length.
    """
    readers = {r.lower() for r in to}
    pool = [
        doc
        for doc in docs
        if not doc.get("excluded") and min_words <= doc.get("words", 0) <= max_words
    ]

    def closeness(doc: Mapping[str, Any]) -> float:
        return abs(doc["words"] - words) if words else 0.0

    def group_of(doc: Mapping[str, Any]) -> str:
        return ",".join(sorted(doc.get("to", []))) or doc.get("ref") or doc["id"]

    def spread(candidates: list[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
        groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
        for doc in sorted(
            candidates, key=lambda d: (closeness(d), d.get("date") or ""), reverse=False
        ):
            groups[group_of(doc)].append(doc)
        for members in groups.values():
            members.sort(key=lambda d: (closeness(d), _newest_first(d)))
        ordered, queues = [], [groups[key] for key in sorted(groups)]
        while any(queues):
            for queue in queues:
                if queue:
                    ordered.append(queue.pop(0))
        return ordered

    same = [d for d in pool if readers & {r.lower() for r in d.get("to", [])}]
    rest = [d for d in pool if d not in same]
    return (spread(same) + spread(rest))[:n]


def _newest_first(doc: Mapping[str, Any]) -> str:
    # ISO dates sort as text; invert so that a later date sorts first, undated last.
    date = doc.get("date") or ""
    return "".join(chr(255 - ord(c)) if ord(c) < 255 else c for c in date) if date else "\uffff"
