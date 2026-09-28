"""Each sourcer on invented input. Nothing here reads a real mailbox, account or session."""

import functools
import json
import mailbox
from email.message import EmailMessage
from types import SimpleNamespace

import pytest

import penlike
from penlike import sourcers

ME = "quinn@example.org"


def _mail(sender, to, body, *, date="Mon, 04 Mar 2019 10:00:00 +0000", reply=False):
    message = EmailMessage()
    message["From"], message["To"], message["Date"] = sender, to, date
    message["Subject"] = "About the release"
    if reply:
        message["In-Reply-To"] = "<earlier@example.org>"
    message.set_content(body)
    return message


def test_mbox_keeps_metadata_and_tells_the_author_from_the_others(tmp_path):
    path = tmp_path / "archive.mbox"
    box = mailbox.mbox(str(path))
    box.add(_mail(ME, "mira@example.org, tomas@example.org", "Shipping on Friday.\n"))
    box.add(_mail("mira@example.org", ME, "Fine by me.\n", reply=True))
    box.close()
    found = list(sourcers.mbox(str(path), me=[ME]))
    assert [d["is_self"] for d in found] == [True, False]
    assert found[0]["to"] == ["mira@example.org", "tomas@example.org"]
    assert found[0]["date"].startswith("2019-03-04") and found[1]["reply"] is True


def test_quoted_replies_are_not_the_authors_words(tmp_path):
    path = tmp_path / "archive.mbox"
    box = mailbox.mbox(str(path))
    body = "Agreed, go ahead.\n\nOn Mon, 4 Mar 2019, Mira wrote:\n> Shall we ship on Friday?\n"
    box.add(_mail(ME, "mira@example.org", body))
    box.close()
    files = {}
    penlike.new("quinn", me=[ME], files=files)
    penlike.gather("quinn", "mbox", [str(path)], min_words=1, files=files)
    (doc,) = penlike.ModelStore("quinn", files=files).read_docs()
    assert doc["text"] == "Agreed, go ahead."


def test_files_reads_folders_and_single_messages(tmp_path):
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes" / "one.md").write_text("A short note about the loader.")
    (tmp_path / "notes" / "skip.bin").write_text("not text")
    (tmp_path / "one.eml").write_bytes(bytes(_mail(ME, "mira@example.org", "See you there.\n")))
    found = list(sourcers.files(str(tmp_path / "notes"), str(tmp_path / "one.eml"), me=[ME]))
    assert [d["channel"] for d in found] == ["document", "email"]
    assert "date" not in found[0]  # a file's modification time is not when it was written


def test_a_missing_path_says_so(tmp_path):
    with pytest.raises(penlike.PenlikeError, match="no such file or folder"):
        list(sourcers.files(str(tmp_path / "nowhere")))


def _github_run(pages):
    calls = []

    def run(command, **_):
        calls.append(command)
        query = next(a for a in command if a.startswith("q="))[2:]
        kind = "DISCUSSION" if "type: DISCUSSION" in command[4] else "ISSUE"
        nodes = pages.get((kind, query.split(":")[0]), [])
        payload = {
            "data": {
                "search": {"pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": nodes}
            }
        }
        return SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")

    run.calls = calls
    return run


def test_github_keeps_only_what_the_login_wrote():
    def item(login, body, url, **more):
        return {
            "body": body,
            "createdAt": "2020-05-01T00:00:00Z",
            "url": url,
            "author": {"login": login},
            **more,
        }

    thread = item(
        "quinn",
        "How should the loader treat an empty mapping?",
        "https://example.org/d/1",
        __typename="Discussion",
        title="Empty mappings",
        repository={"nameWithOwner": "example/loader", "isPrivate": False},
        comments={
            "nodes": [
                item(
                    "mira",
                    "Raise, I would say.",
                    "https://example.org/d/1#c1",
                    replies={
                        "nodes": [item("quinn", "Agreed, raising.", "https://example.org/d/1#c2")]
                    },
                )
            ]
        },
    )
    run = _github_run({("DISCUSSION", "author"): [thread], ("DISCUSSION", "commenter"): [thread]})
    found = list(sourcers.github("quinn", until="2023-01-01", kinds=["discussion"], run=run))
    assert [d["kind"] for d in found] == ["discussion", "discussion-reply"]
    assert all(d["is_self"] and d["audience"] == "public" for d in found)
    assert any("created:*..2023-01-01" in a for a in run.calls[0])


def test_correspond_is_the_source_seam():
    correspond = pytest.importorskip("correspond")
    testing = pytest.importorskip("correspond.testing")
    fake = testing.demo_channel()
    found = list(sourcers.correspond(f"fake:{testing.DEMO_CONVERSATION}", registry={"fake": fake}))
    assert len(found) == 2 and all(d["channel"] == "fake" for d in found)
    assert {type(d["is_self"]) for d in found} == {bool}
    assert correspond.__name__ == "correspond"


def test_claude_sessions_keeps_what_the_person_typed(tmp_path):
    lines = [
        {"type": "user", "message": {"content": "please rename the loader module"}},
        {"type": "user", "message": {"content": "<system-reminder>ignore</system-reminder>"}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "content": "x"}]}},
        {"type": "assistant", "message": {"content": "Done."}},
    ]
    path = tmp_path / "session.jsonl"
    path.write_text("\n".join(json.dumps(line) for line in lines))
    found = list(sourcers.claude_sessions(str(tmp_path)))
    assert [d["text"] for d in found] == ["please rename the loader module"]
    assert penlike.situate(penlike.normalize_doc(found[0])) == "agent"


def test_a_custom_sourcer_is_a_function_in_a_file(tmp_path):
    (tmp_path / "my_source.py").write_text(
        "def read(*refs, since=None, until=None, limit=None, me=(), **options):\n"
        "    for ref in refs:\n"
        "        yield {'text': f'A line about {ref}, written for the test.',\n"
        "               'channel': 'chat', 'to': ['mira'], 'date': '2018-06-01',\n"
        "               'shout': options.get('shout')}\n"
    )
    files = {}
    penlike.new("quinn", files=files)
    source = f"{tmp_path / 'my_source.py'}:read"
    result = penlike.gather(
        "quinn", source, ["parsers", "stores"], option=["shout=true"], files=files
    )
    assert result["added"] == 2
    docs = penlike.ModelStore("quinn", files=files).read_docs()
    assert {d["flags"]["shout"] for d in docs} == {True}
    penlike.build("quinn", files=files)
    assert set(penlike.registers("quinn", files=files)["registers"]) == {"chat.one"}


def test_a_callable_is_a_sourcer_too():
    def lines(*refs, **_):
        yield {"text": "One text from a function, long enough to keep."}

    files = {}
    penlike.new("notes", kind="corpus", basis="public", files=files)
    assert penlike.gather("notes", functools.partial(lines), files=files)["added"] == 1


def test_dates_bound_what_is_kept(tmp_path):
    path = tmp_path / "dated.jsonl"
    rows = [
        {"text": f"A text dated in {year}, long enough to keep.", "date": f"{year}-06-01"}
        for year in (2015, 2019, 2024)
    ] + [{"text": "A text with no date at all, long enough to keep."}]
    path.write_text("\n".join(json.dumps(r) for r in rows))
    files = {}
    penlike.new("quinn", files=files)
    result = penlike.gather(
        "quinn", "jsonl", [str(path)], since="2016", until="2023-01-01", files=files
    )
    assert result["added"] == 1
    assert result["skipped"] == {"outside the dates": 2, "undated": 1}


def test_what_the_author_did_not_write_is_removed():
    from penlike.base import strip_quoted

    wrapped = (
        "Fine.\n\nOn Mon, 4 Mar 2019 at 10:00, Mira Example <mira@example.org>\nwrote:\n> Shall we?"
    )
    assert strip_quoted(wrapped) == "Fine."
    assert strip_quoted("Gut.\n\nAm 04.03.2019 um 10:00 schrieb Mira:\n> Ja?") == "Gut."
    outlook = "Agreed.\n\nFrom: Mira\nSent: Monday\nTo: Quinn\nSubject: Release\n\nShall we?"
    assert strip_quoted(outlook) == "Agreed."


def test_the_authors_own_prose_is_kept():
    from penlike.base import strip_quoted

    for prose in (
        "Here is the plan.\n\nOn Monday I wrote:\nship it",
        "Two fields matter.\nFrom: the sender\nThat is all.",
        "Above the line.\n_____\nBelow the line.",
    ):
        assert strip_quoted(prose) == prose


def test_html_mail_and_attached_messages(tmp_path):
    from email.message import EmailMessage

    rich = EmailMessage()
    rich["From"], rich["To"] = ME, "mira@example.org"
    rich.set_content(
        "<div>I&#39;m here&nbsp;now &amp; ready.</div>"
        '<div class="gmail_quote">On Monday Mira wrote:<blockquote>secret</blockquote></div>',
        subtype="html",
    )
    assert sourcers._message_text(rich).strip() == "I'm here now & ready."

    inner = _mail("mira@example.org", ME, "Words that the author never wrote.\n")
    outer = _mail(ME, "tomas@example.org", "See the attached note.\n")
    outer.add_attachment(inner)
    assert sourcers._message_text(outer).strip() == "See the attached note."


def test_github_kinds_are_checked():
    run = _github_run({})
    assert list(sourcers.github("quinn", kinds="issue", run=run)) == []
    assert len(run.calls) == 2
    with pytest.raises(penlike.PenlikeError, match="kinds must be"):
        list(sourcers.github("quinn", kinds=["wiki"], run=run))
    list(sourcers.github("quinn", since="2019-01-01", kinds="issue", run=run))
    assert not any("created:" in a for call in run.calls for a in call)


def test_a_sourcer_with_the_wrong_signature_is_explained():
    def bare(path):
        yield {"text": "never reached"}

    files = {}
    penlike.new("quinn", files=files)
    with pytest.raises(penlike.PenlikeError, match="A sourcer is"):
        penlike.gather("quinn", bare, ["x"], files=files)
