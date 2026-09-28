"""Sourcers: where the writing comes from. Read-only, by construction.

A *sourcer* is a plain function. It takes references (paths, conversation
references, a login) and yields documents as dicts::

    def my_sourcer(*refs, since=None, until=None, limit=None, me=(), **options):
        yield {"text": "...", "date": "2021-03-04", "channel": "chat", "to": ["ada"]}

Only ``text`` is required. Every other field of :data:`penlike.base.DOC_FIELDS` is
optional and improves what the model can do: ``date`` allows a cutoff, ``to`` and
``channel`` decide the register, ``is_self`` separates the author from the people
they were talking with. ``since`` and ``until`` are hints a sourcer may use to
fetch less; the caller applies the window again, so ignoring them is safe.

The source is a seam: :func:`resolve_sourcer` accepts a built-in name, a
``module:function`` reference, or a ``path/to/file.py:function`` reference, so a
sourcer written for one person's odd archive needs no change here.

>>> sourcer = resolve_sourcer("jsonl")
>>> sourcer.__name__
'jsonl'
>>> sorted(SOURCERS)
['claude-sessions', 'correspond', 'files', 'github', 'jsonl', 'mbox']
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path
from typing import Any

from penlike.base import PenlikeError, audience_of, parse_date

__all__ = [
    "SOURCERS",
    "claude_sessions",
    "correspond",
    "files",
    "github",
    "jsonl",
    "mbox",
    "requirements",
    "resolve_sourcer",
]

_TEXT_SUFFIXES = (".txt", ".md", ".markdown", ".rst", ".text")
_DEFAULT_SESSIONS_DIR = "~/.claude/projects"
_GITHUB_PAGE_SIZE = 25


def _paths(refs: Iterable[str], suffixes: tuple[str, ...]) -> Iterator[Path]:
    for ref in refs:
        path = Path(os.path.expanduser(ref))
        if path.is_dir():
            yield from sorted(
                p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in suffixes
            )
        elif path.is_file():
            yield path
        else:
            raise PenlikeError(f"{ref}: no such file or folder")


def _addresses(value: Any) -> list[str]:
    from email.utils import getaddresses

    return [addr.lower() for _, addr in getaddresses([str(value or "")]) if addr]


def _message_text(message: Any) -> str:
    """The plain-text body of an email message; HTML-only mail is reduced to its text."""
    plain, html = [], []
    parts = message.walk() if message.is_multipart() else [message]
    for part in parts:
        if part.get_content_maintype() != "text" or part.get_filename():
            continue
        payload = part.get_payload(decode=True)
        if payload is None:
            continue
        charset = part.get_content_charset() or "utf-8"
        try:
            body = payload.decode(charset, errors="replace")
        except LookupError:
            body = payload.decode("utf-8", errors="replace")
        (plain if part.get_content_subtype() == "plain" else html).append(body)
    if plain:
        return "\n".join(plain)
    text = re.sub(r"(?is)<(script|style|blockquote).*?</\1>", " ", "\n".join(html))
    text = re.sub(r"(?i)<br\s*/?>|</p>|</div>", "\n", text)
    return re.sub(r"<[^>]+>", "", text)


def _email_doc(message: Any, *, me: Iterable[str], ref: str) -> dict[str, Any] | None:
    sender = _addresses(message.get("From"))
    labels = str(message.get("X-Gmail-Labels") or "")
    mine = {m.lower() for m in me}
    is_self: bool | None = None
    if mine:
        is_self = bool(sender) and sender[0] in mine
    elif re.search(r"(?i)\bsent\b", labels):
        is_self = True
    text = _message_text(message)
    if not text.strip():
        return None
    try:
        date = parse_date(message.get("Date"))
    except PenlikeError:
        date = None
    return {
        "text": text,
        "date": date,
        "channel": "email",
        "kind": "message",
        "title": str(message.get("Subject") or ""),
        "author": sender[0] if sender else "",
        "is_self": is_self,
        "to": _addresses(message.get("To")),
        "cc": _addresses(message.get("Cc")),
        "reply": bool(message.get("In-Reply-To")),
        "ref": ref,
    }


def files(*refs: str, me: Iterable[str] = (), **_: Any) -> Iterator[dict[str, Any]]:
    """Text files and folders of them (``.txt``, ``.md``, ``.rst``), and ``.eml`` messages.

    A folder is read recursively. A text file is one document; it has no date (a
    file's modification time says when it was copied, not when it was written) and
    no addressee, so it is filed as a ``document``.
    """
    from email import message_from_bytes

    for path in _paths(refs, (*_TEXT_SUFFIXES, ".eml")):
        if path.suffix.lower() == ".eml":
            doc = _email_doc(message_from_bytes(path.read_bytes()), me=me, ref=str(path))
            if doc:
                yield doc
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if text.strip():
            yield {
                "text": text,
                "channel": "document",
                "kind": "document",
                "title": path.stem,
                "ref": str(path),
            }


def jsonl(*refs: str, **_: Any) -> Iterator[dict[str, Any]]:
    """JSON Lines files, one document per line: the interchange format for custom sources.

    Anything that can write ``{"text": ..., "date": ..., "to": [...]}`` lines can feed
    a model, in any language and by any means.
    """
    for path in _paths(refs, (".jsonl", ".ndjson")):
        with path.open(encoding="utf-8") as lines:
            for number, line in enumerate(lines, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as error:
                    raise PenlikeError(f"{path}:{number}: not JSON ({error.msg})") from None
                record.setdefault("ref", f"{path}:{number}")
                yield record


def mbox(*refs: str, me: Iterable[str] = (), **_: Any) -> Iterator[dict[str, Any]]:
    """Mailbox archives in mbox format, such as a mail export from a webmail provider.

    Pass the author's own addresses as ``me`` so that only what they sent is kept.
    Without it, messages carrying a "Sent" label are taken as the author's and the
    rest are left undecided.
    """
    import mailbox

    for path in _paths(refs, (".mbox", "")):
        box = mailbox.mbox(str(path), create=False)
        try:
            for index, message in enumerate(box):
                doc = _email_doc(message, me=me, ref=f"{path}#{index}")
                if doc:
                    yield doc
        finally:
            box.close()


def correspond(
    *refs: str,
    since: str | None = None,
    limit: int | None = None,
    registry: Any = None,
    **_: Any,
) -> Iterator[dict[str, Any]]:
    """Conversations read through ``correspond``, the facade over communication channels.

    Each reference is a correspond conversation reference, for example
    ``github:owner/repo#12`` or ``email:``. Any channel registered with correspond
    works, including one you add yourself. Needs ``pip install 'penlike[correspond]'``.
    """
    try:
        import correspond as _correspond
    except ImportError:
        raise PenlikeError(
            "the correspond sourcer needs the correspond package:\n"
            "    pip install 'penlike[correspond]'"
        ) from None
    if not refs:
        raise PenlikeError(
            "give at least one conversation reference, for example github:owner/repo#12"
        )
    for ref in refs:
        for message in _correspond.read(ref, since=since, limit=limit, registry=registry):
            native = dict(message.native or {})
            channel = message.conversation.channel
            yield {
                "text": message.text,
                "date": message.sent_at,
                "channel": channel,
                "kind": "reply" if message.reply_to else "message",
                "title": str(native.get("subject") or native.get("title") or ""),
                "author": message.author.handle or message.author.native_id,
                "is_self": bool(message.author.is_self),
                "to": native.get("to") or [],
                "cc": native.get("cc") or [],
                "audience": "public" if channel == "github" else None,
                "reply": message.reply_to is not None,
                "url": message.url or "",
                "ref": str(ref),
            }


_GITHUB_FIELDS = "body createdAt url author { login }"
_GITHUB_THREAD = "__typename title " + _GITHUB_FIELDS + " repository { nameWithOwner isPrivate }"
_GITHUB_QUERIES = {
    "ISSUE": """
query($q: String!, $n: Int!, $after: String) {
  search(query: $q, type: ISSUE, first: $n, after: $after) {
    pageInfo { hasNextPage endCursor }
    nodes {
      ... on Issue { %(thread)s comments(first: 100) { nodes { %(fields)s } } }
      ... on PullRequest { %(thread)s comments(first: 100) { nodes { %(fields)s } } }
    }
  }
}"""
    % {"thread": _GITHUB_THREAD, "fields": _GITHUB_FIELDS},
    "DISCUSSION": """
query($q: String!, $n: Int!, $after: String) {
  search(query: $q, type: DISCUSSION, first: $n, after: $after) {
    pageInfo { hasNextPage endCursor }
    nodes {
      ... on Discussion { %(thread)s comments(first: 50) { nodes { %(fields)s
        replies(first: 50) { nodes { %(fields)s } } } } }
    }
  }
}"""
    % {"thread": _GITHUB_THREAD, "fields": _GITHUB_FIELDS},
}
_GITHUB_KINDS = {"Issue": "issue", "PullRequest": "pull-request", "Discussion": "discussion"}


def _github_docs(node: dict[str, Any], login: str) -> Iterator[dict[str, Any]]:
    repo = node.get("repository") or {}
    thread = _GITHUB_KINDS.get(node.get("__typename", ""), "thread")
    common = {
        "channel": "github",
        "audience": "few" if repo.get("isPrivate") else "public",
        "title": node.get("title") or "",
        "ref": repo.get("nameWithOwner") or "",
    }

    def doc(item: dict[str, Any], *, reply: bool) -> dict[str, Any] | None:
        author = ((item.get("author") or {}).get("login") or "").lower()
        if author != login.lower() or not (item.get("body") or "").strip():
            return None
        return {
            **common,
            "text": item["body"],
            "date": item.get("createdAt"),
            "url": item.get("url") or "",
            "author": author,
            "is_self": True,
            "reply": reply,
            "kind": f"{thread}-reply" if reply else thread,
        }

    first = doc(node, reply=False)
    if first:
        yield first
    for comment in ((node.get("comments") or {}).get("nodes")) or []:
        found = doc(comment, reply=True)
        if found:
            yield found
        for reply in ((comment.get("replies") or {}).get("nodes")) or []:
            found = doc(reply, reply=True)
            if found:
                yield found


def github(
    *refs: str,
    since: str | None = None,
    until: str | None = None,
    limit: int | None = None,
    kinds: Iterable[str] = ("discussion", "issue"),
    run: Callable[..., Any] = subprocess.run,
    **_: Any,
) -> Iterator[dict[str, Any]]:
    """What one GitHub user wrote: discussions, issues, pull requests and comments on them.

    Each reference is a login, optionally narrowed to a repository or an owner:
    ``octocat``, ``octocat@owner/repo``, ``octocat@owner``. It goes through the
    ``gh`` command line tool and its login, so private repositories the login can
    read are included. GitHub search returns at most 1000 threads per query.
    """
    if not shutil.which("gh") and run is subprocess.run:
        raise PenlikeError("the github sourcer needs the GitHub CLI: https://cli.github.com")
    if not refs:
        raise PenlikeError("give the login to collect, for example: github octocat")
    window = ""
    if since or until:
        low = (parse_date(since) or "")[:10] or "*"
        high = (parse_date(until) or "")[:10] or "*"
        window = f" created:{low}..{high}"
    types = [t for t in ("DISCUSSION", "ISSUE") if t.lower() in set(kinds)]
    seen: set[str] = set()
    produced = 0
    for ref in refs:
        login, _, scope = ref.partition("@")
        scoped = ""
        if scope:
            scoped = f" repo:{scope}" if "/" in scope else f" user:{scope}"
        for search_type in types:
            for role in ("author", "commenter"):
                query = f"{role}:{login}{scoped}{window}"
                after = None
                while True:
                    command = [
                        "gh", "api", "graphql",
                        "-f", f"query={_GITHUB_QUERIES[search_type]}",
                        "-f", f"q={query}",
                        "-F", f"n={_GITHUB_PAGE_SIZE}",
                    ]  # fmt: skip
                    if after:
                        command += ["-f", f"after={after}"]
                    done = run(command, capture_output=True, text=True)
                    if done.returncode:
                        raise PenlikeError(
                            f"gh failed on {query!r}: {(done.stderr or '').strip()[:300]}"
                        )
                    search = json.loads(done.stdout)["data"]["search"]
                    for node in search["nodes"]:
                        for doc in _github_docs(node or {}, login):
                            if doc["url"] in seen:
                                continue
                            seen.add(doc["url"])
                            yield doc
                            produced += 1
                            if limit and produced >= limit:
                                return
                    if not search["pageInfo"]["hasNextPage"]:
                        break
                    after = search["pageInfo"]["endCursor"]


def claude_sessions(*refs: str, **_: Any) -> Iterator[dict[str, Any]]:
    """What the author typed to a coding agent, from saved Claude Code session logs.

    This is how a person writes to an agent, which is rarely how they write to
    people. It gets its own register (``agent``) and should not be the basis of a
    model meant for writing to humans.
    """
    roots = refs or (_DEFAULT_SESSIONS_DIR,)
    for path in _paths(roots, (".jsonl",)):
        with path.open(encoding="utf-8", errors="replace") as lines:
            for line in lines:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if record.get("type") != "user" or record.get("isMeta"):
                    continue
                if record.get("isSidechain"):
                    continue
                content = (record.get("message") or {}).get("content")
                if isinstance(content, list):
                    content = "\n".join(
                        block.get("text", "")
                        for block in content
                        if isinstance(block, dict) and block.get("type") == "text"
                    )
                if not isinstance(content, str) or not content.strip():
                    continue
                if content.lstrip().startswith(("<", "[")) or "<system-reminder>" in content:
                    continue  # harness wrappers, pasted tool output, interruptions
                yield {
                    "text": content,
                    "date": record.get("timestamp"),
                    "channel": "agent",
                    "kind": "prompt",
                    "audience": "agent",
                    "is_self": True,
                    "ref": str(path),
                }


#: The built-in sourcers, by the name used on the command line.
SOURCERS: dict[str, Callable[..., Iterable[dict[str, Any]]]] = {
    "files": files,
    "jsonl": jsonl,
    "mbox": mbox,
    "correspond": correspond,
    "github": github,
    "claude-sessions": claude_sessions,
}


def resolve_sourcer(source: str | Callable) -> Callable[..., Iterable[dict[str, Any]]]:
    """Find the sourcer a name refers to: built-in, ``module:function``, or ``file.py:function``.

    >>> resolve_sourcer("files") is files
    True
    >>> resolve_sourcer("json:loads").__name__
    'loads'
    """
    if callable(source):
        return source
    if source in SOURCERS:
        return SOURCERS[source]
    if ":" not in source:
        raise PenlikeError(
            f"no sourcer named {source!r}. Built in: {', '.join(sorted(SOURCERS))}. "
            "A custom one is referenced as module:function or path/to/file.py:function"
        )
    location, _, attribute = source.rpartition(":")
    try:
        if location.endswith(".py"):
            path = Path(os.path.expanduser(location))
            spec = importlib.util.spec_from_file_location(path.stem, path)
            if spec is None or spec.loader is None:
                raise ImportError(f"cannot load {path}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        else:
            module = importlib.import_module(location)
        return getattr(module, attribute)
    except (ImportError, AttributeError, OSError) as error:
        raise PenlikeError(f"cannot load the sourcer {source!r}: {error}") from None


def requirements() -> dict[str, dict[str, Any]]:
    """For each built-in sourcer: what it reads, and whether it can run here."""
    have_correspond = importlib.util.find_spec("correspond") is not None
    have_gh = shutil.which("gh") is not None
    ready = {
        "correspond": (have_correspond, "pip install 'penlike[correspond]'"),
        "github": (
            have_gh,
            "install the GitHub CLI (https://cli.github.com) and run: gh auth login",
        ),
    }
    out = {}
    for name, function in SOURCERS.items():
        ok, fix = ready.get(name, (True, ""))
        out[name] = {
            "reads": (function.__doc__ or "").strip().split("\n")[0],
            "ready": ok,
            **({} if ok else {"to_enable": fix}),
        }
    return out
