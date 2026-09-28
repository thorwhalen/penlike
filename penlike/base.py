"""The shared vocabulary: the document record, text cleaning, dates and the error type.

A *document* is one piece of writing plus the situation it was written in. It is a plain
``dict`` so that it round-trips through JSON and so that a custom sourcer can be written
by anyone (or any agent) without importing a class. :func:`normalize_doc` is the one
place that decides what a well-formed document looks like.

>>> doc = normalize_doc({"text": "Hello there.", "channel": "email", "to": ["ada@example.org"]})
>>> doc["audience"], doc["words"], len(doc["id"])
('one', 2, 16)
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

__all__ = [
    "AI_ERA_START",
    "DOC_FIELDS",
    "PenlikeError",
    "audience_of",
    "doc_id",
    "normalize_doc",
    "parse_date",
    "prose_of",
    "strip_quoted",
    "word_count",
]

#: The public release of ChatGPT. Text dated on or after this day may have been written
#: or edited by a language model, so a corpus meant to capture a person is safest when
#: it stops before it. It is a default for warnings, never a silent filter.
AI_ERA_START = "2022-11-30"

#: Every field a document may carry. Only ``text`` is required from a sourcer.
DOC_FIELDS = (
    "id",  # content hash, assigned here
    "text",  # the author's own words, quoted material removed
    "date",  # ISO 8601, UTC, or None when unknown
    "source",  # the sourcer that produced it
    "ref",  # where it came from, in that sourcer's terms
    "channel",  # email, github, chat, document, agent, ...
    "kind",  # post, reply, message, document, ...
    "title",  # subject line or title, if any
    "author",  # who wrote it, in the channel's terms
    "is_self",  # True when the author is the model's subject; None when unknown
    "to",  # direct addressees
    "cc",  # copied readers
    "audience",  # one, few, many, public, unknown
    "reply",  # True for a reply, False for an opening message, None when unknown
    "url",
    "register",  # a register hint from the sourcer, or the assigned register id
    "pinned",  # True when a person assigned the register by hand
    "excluded",  # a reason string when the document is kept out of the model
    "flags",  # findings of optional screening passes
    "words",  # word count of the prose
)

_WORD_RE = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*")


class PenlikeError(Exception):
    """An error whose message tells the caller what to do next."""


def word_count(text: str) -> int:
    """Count words (letters, with inner apostrophes).

    >>> word_count("Don't stop, it's 3pm.")
    4
    """
    return len(_WORD_RE.findall(text))


def doc_id(text: str) -> str:
    """A stable id for a text: the first 16 hex digits of its SHA-256, whitespace-blind.

    >>> doc_id("Hello  there.") == doc_id("Hello there. ")
    True
    """
    canonical = " ".join(text.split())
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def parse_date(value: Any) -> str | None:
    """Turn a date in any common form into ISO 8601 UTC, or ``None``.

    A naive value is read as UTC. A bare year or day is accepted.

    >>> parse_date("2021-03-04")
    '2021-03-04T00:00:00+00:00'
    >>> parse_date("Thu, 4 Mar 2021 10:00:00 +0100")
    '2021-03-04T09:00:00+00:00'
    >>> parse_date("2023")
    '2023-01-01T00:00:00+00:00'
    >>> parse_date("") is None
    True
    """
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        moment = datetime.fromtimestamp(value, tz=timezone.utc)
    elif isinstance(value, datetime):
        moment = value
    else:
        text = str(value).strip()
        if re.fullmatch(r"\d{4}", text):
            text += "-01-01"
        elif re.fullmatch(r"\d{4}-\d{2}", text):
            text += "-01"
        try:
            moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            try:
                moment = parsedate_to_datetime(text)
            except (TypeError, ValueError):
                raise PenlikeError(
                    f"cannot read {value!r} as a date; use ISO 8601, for example 2023-01-01"
                ) from None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).isoformat()


_QUOTE_HEADER_RE = re.compile(
    r"^\s*(?:"
    r"On .{5,200}wrote:\s*$"
    r"|Le .{5,200}a écrit\s*:\s*$"
    r"|-{2,}\s*Original Message\s*-{2,}"
    r"|-{2,}\s*Forwarded message\s*-{2,}"
    r"|_{5,}\s*$"
    r"|From:\s.+$"
    r")",
    re.IGNORECASE,
)


def strip_quoted(text: str) -> str:
    """Remove what the author did not write: quoted replies and forwarded mail.

    A model of an author built from text that includes the messages they were
    answering is a model of their correspondents. Lines starting with ``>`` go, and
    everything from a reply header ("On ... wrote:", "Original Message") onward goes.

    >>> strip_quoted("Sounds good.\\n\\nOn Mon, 1 Feb 2021, Ada wrote:\\n> Shall we?")
    'Sounds good.'
    >>> strip_quoted("> earlier point\\nI agree with this.")
    'I agree with this.'
    """
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    kept: list[str] = []
    for index, line in enumerate(lines):
        if _QUOTE_HEADER_RE.match(line):
            # "From:" only counts as a forwarded header when a header block follows.
            if line.lstrip().lower().startswith("from:") and not any(
                re.match(r"^\s*(Sent|Date|To|Subject):", nxt, re.IGNORECASE)
                for nxt in lines[index + 1 : index + 4]
            ):
                kept.append(line)
                continue
            break
        if line.lstrip().startswith(">"):
            continue
        kept.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()


_FENCE_RE = re.compile(r"(```|~~~).*?(\1|\Z)", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
_URL_RE = re.compile(r"(?:https?://|www\.)\S+")
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")


def prose_of(text: str) -> str:
    """The prose of a text: code blocks, inline code and bare links replaced by placeholders.

    Style is measured on prose. Code and links are somebody else's tokens, and they
    would swamp punctuation and word-length figures in technical writing.

    >>> prose_of("Call `f(x)` then see https://example.org/a for more.")
    'Call CODE then see LINK for more.'
    """
    text = _FENCE_RE.sub("\n", text)
    text = _INLINE_CODE_RE.sub("CODE", text)
    text = _MD_LINK_RE.sub(r"\1", text)
    return _URL_RE.sub("LINK", text)


def audience_of(to: Iterable[str], cc: Iterable[str] = (), *, public: bool = False) -> str:
    """The size of the readership: ``one``, ``few`` (2 to 5), ``many``, ``public`` or ``unknown``.

    Recipient count has a measured effect on how formally people write email, so it
    is part of the situation a text is filed under.

    >>> audience_of(["a@example.org"]), audience_of(["a", "b"], ["c"]), audience_of([])
    ('one', 'few', 'unknown')
    """
    if public:
        return "public"
    n = len(set(to)) + len(set(cc))
    if n == 0:
        return "unknown"
    return "one" if n == 1 else "few" if n <= 5 else "many"


def _as_list(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(item).strip() for item in value if str(item).strip()]


def normalize_doc(raw: Mapping[str, Any], *, source: str = "") -> dict[str, Any]:
    """Make a well-formed document from whatever a sourcer yielded.

    Quoted material is removed, the date is put in ISO form, the audience is derived
    when it was not given, and the id is computed from the cleaned text. Unknown keys
    are kept under ``flags`` so that a custom sourcer can carry extra metadata.

    >>> doc = normalize_doc({"text": "> quoted\\nFine by me.", "date": "2020", "mood": "calm"})
    >>> doc["text"], doc["date"][:4], doc["flags"]
    ('Fine by me.', '2020', {'mood': 'calm'})
    """
    if not isinstance(raw, Mapping) or not str(raw.get("text") or "").strip():
        raise PenlikeError("a document needs a non-empty 'text'")
    text = strip_quoted(str(raw["text"]))
    to, cc = _as_list(raw.get("to")), _as_list(raw.get("cc"))
    channel = str(raw.get("channel") or "document")
    audience = raw.get("audience") or audience_of(to, cc)
    extras = {k: v for k, v in raw.items() if k not in DOC_FIELDS}
    return {
        "id": doc_id(text),
        "text": text,
        "date": parse_date(raw.get("date")),
        "source": str(raw.get("source") or source),
        "ref": str(raw.get("ref") or ""),
        "channel": channel,
        "kind": str(raw.get("kind") or ("message" if to else "document")),
        "title": str(raw.get("title") or ""),
        "author": str(raw.get("author") or ""),
        "is_self": raw.get("is_self"),
        "to": to,
        "cc": cc,
        "audience": str(audience),
        "reply": raw.get("reply"),
        "url": str(raw.get("url") or ""),
        "register": raw.get("register") or None,
        "pinned": bool(raw.get("pinned")) or bool(raw.get("register")),
        "excluded": raw.get("excluded") or None,
        "flags": {**dict(raw.get("flags") or {}), **extras},
        "words": word_count(prose_of(text)),
    }
