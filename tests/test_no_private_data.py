"""The guard: nothing in this repository comes from a real writer's private texts.

A model of how a person writes, and everything derived from it, lives in the user's
data folder. This scans every text file in the working tree (tracked or not, so a new
file is covered before it is committed) for the mechanical signs of a leak:

- an email address outside the placeholder domains;
- an absolute home or temporary path, which names a machine or a person;
- a file that looks like part of a model (documents, profiles, notes).

It cannot tell invented prose from real prose; that part is on whoever writes the
text. Strings that must look like leaks inside this file are built by concatenation,
so that the guard does not trip on itself.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

_SKIP_DIRS = {
    ".git", "__pycache__", ".pytest_cache", ".ruff_cache", "dist", "build",
    ".venv", "venv", "node_modules", "handoffs", "htmlcov",
}  # fmt: skip
_TEXT_SUFFIXES = {
    ".py", ".md", ".toml", ".json", ".jsonl", ".txt", ".yml", ".yaml", ".cfg", ".csv", ".eml",
}  # fmt: skip
_MODEL_FILES = {"docs.jsonl", "registers.json", "model.json"}

PLACEHOLDER_DOMAINS = {"example.org", "example.com", "example.net"}
ALLOWED_ADDRESSES = {"git" + "@" + "github.com"}

EMAIL_RE = re.compile(r"[A-Za-z0-9_.+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)")
HOME_PATH_RE = re.compile(
    r"/(?:Users|home)/[A-Za-z0-9_.-]+"
    + r"|(?<![\w.])/"
    + r"root\b"
    + r"|/(?:private/)?var/folders/"
    + r"|/private/"
    + r"tmp/"
    + r"|\b[A-Za-z]:\\Users\\[A-Za-z0-9_.-]+"
)


def _files() -> list[Path]:
    return [
        path
        for path in REPO_ROOT.rglob("*")
        if path.is_file()
        and not path.is_symlink()
        and not any(
            part in _SKIP_DIRS or part.endswith((".egg-info", ".dist-info"))
            for part in path.relative_to(REPO_ROOT).parts
        )
    ]


def _texts() -> list[tuple[str, str]]:
    return [
        (str(path.relative_to(REPO_ROOT)), path.read_text(encoding="utf-8", errors="replace"))
        for path in _files()
        if path.suffix in _TEXT_SUFFIXES
    ]


def emails_outside_placeholders(text: str) -> list[str]:
    return [
        m.group(0)
        for m in EMAIL_RE.finditer(text)
        if m.group(1).lower() not in PLACEHOLDER_DOMAINS and m.group(0) not in ALLOWED_ADDRESSES
    ]


def test_no_email_addresses_outside_placeholder_domains():
    offenders = {
        name: found for name, text in _texts() if (found := emails_outside_placeholders(text))
    }
    assert not offenders, f"address(es) outside {sorted(PLACEHOLDER_DOMAINS)}: {offenders}"


def test_no_absolute_home_paths():
    offenders = {name: found for name, text in _texts() if (found := HOME_PATH_RE.findall(text))}
    assert not offenders, f"absolute home or temporary path(s): {offenders}"


def test_no_model_files_in_the_tree():
    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path in _files()
        if path.name in _MODEL_FILES or "profiles" in path.parts or "notes" in path.parts
    ]
    assert not offenders, (
        f"these look like parts of a style model; they belong in the data folder: {offenders}"
    )


def test_the_guard_actually_catches_leaks():
    """Each detector must fire on a planted leak, or the guard guards nothing."""
    planted = "someone" + "@" + "realmail.test"
    assert emails_outside_placeholders(f"write to {planted}") == [planted]
    assert emails_outside_placeholders("write to ada" + "@" + "example.org") == []
    assert HOME_PATH_RE.search("/" + "Users" + "/someone/mail")
    assert HOME_PATH_RE.search("scp server:/" + "root/archive")
    assert HOME_PATH_RE.search("/" + "var/folders/xy/T/tmp123")
