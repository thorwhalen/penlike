"""The whole path on a fictional corpus, every seam on its default.

This is the definition of v1: make a model, give it texts, build it, ask for a
brief, check a draft. It must keep passing after any seam is swapped.
"""

import json

import pytest

import penlike
from tests.corpus import FRIEND, fictional_corpus

OFF_STYLE = (
    "Dear Mira,\n\nI hope this message finds you well. It is important to note that the "
    "deployment, which was undertaken yesterday afternoon following considerable deliberation "
    "among the various stakeholders, has unfortunately encountered a number of significant "
    "difficulties — difficulties which, in all likelihood, will necessitate a comprehensive "
    "and thorough re-examination of the underlying architectural assumptions.\n\n"
    "Kind regards,\nQuinn"
)
IN_STYLE = (
    "Hi Mira,\n\nok so I looked at the log. it's the cache, I think. can you restart it? "
    "I'll check again tonight. don't worry about the rest.\n\nCheers,\nQuinn"
)


@pytest.fixture
def model(tmp_path):
    files = {}
    source = tmp_path / "corpus.jsonl"
    source.write_text("\n".join(json.dumps(d) for d in fictional_corpus()), encoding="utf-8")
    penlike.new("quinn", me=["quinn@example.org"], files=files)
    gathered = penlike.gather("quinn", "jsonl", [str(source)], files=files)
    assert gathered["added"] == 42 and gathered["in_ai_era"] == 0
    penlike.build("quinn", files=files)
    return files


def test_registers_are_situational(model):
    found = penlike.registers("quinn", files=model)["registers"]
    assert {"email.one", "email.many", "github.post", "github.reply"} <= set(found)
    assert found["email.one"]["n_docs"] == 14


def test_gathering_twice_adds_nothing(model, tmp_path):
    again = penlike.gather("quinn", "jsonl", [str(tmp_path / "corpus.jsonl")], files=model)
    assert again["added"] == 0 and again["skipped"] == {"already in the model": 42}


def test_routing(model):
    assert penlike.route(like="quinn", style="email.many", files=model)["how"] == "named"
    by_reader = penlike.route(like="quinn", to=[FRIEND], files=model)
    assert (by_reader["register"], by_reader["how"]) == ("email.one", "readers")
    by_situation = penlike.route(like="quinn", channel="email", audience="many", files=model)
    assert (by_situation["register"], by_situation["how"]) == (
        "email.many",
        "situation",
    )
    assert penlike.route(files=model)["how"] == "fallback"
    with pytest.raises(penlike.PenlikeError, match="registers are"):
        penlike.route(like="quinn", style="sonnet", files=model)


def test_brief_carries_profile_examples_and_next_step(model):
    brief = penlike.brief(like="quinn", to=[FRIEND], files=model)
    assert brief["register"] == "email.one"
    assert "'Hi <name>,'" in brief["text"] and "<example id=" in brief["text"]
    assert "penlike check" in brief["text"]
    # Readers' addresses stay out of what an agent is handed.
    assert FRIEND not in brief["text"]


def test_check_tells_a_foreign_draft_from_a_native_one(model):
    off = penlike.check(OFF_STYLE, like="quinn", style="email.one", files=model)
    near = penlike.check(IN_STYLE, like="quinn", style="email.one", files=model)
    assert not off["ok"] and len(off["discrepancies"]) > len(near["discrepancies"])
    features = {d["feature"] for d in off["discrepancies"]}
    assert {"sentence_len_mean", "greeting", "signoff"} <= features


def test_registers_differ_where_they_should(model):
    store = penlike.ModelStore("quinn", files=model)
    casual = store.read_profile("email.one")
    formal = store.read_profile("email.many")
    for feature, casual_is_lower in (
        ("sentence_len_mean", True),
        ("contraction_per_100w", False),
    ):
        a = casual["scalars"][feature]["mean"]
        b = formal["scalars"][feature]["mean"]
        assert (a < b) == casual_is_lower
    assert casual["greetings"][0][0] == "Hi <name>,"
    assert formal["greetings"][0][0] == "Dear all,"


def test_screening_by_date_excludes_and_restores(model, tmp_path):
    late = tmp_path / "late.jsonl"
    late.write_text(
        json.dumps(
            {
                "text": "A text written well after the cutoff, for the test.",
                "date": "2024-02-01",
                "channel": "email",
                "to": [FRIEND],
                "is_self": True,
            }
        )
    )
    gathered = penlike.gather("quinn", "jsonl", [str(late)], files=model)
    assert gathered["in_ai_era"] == 1 and gathered["warnings"]
    plan = penlike.screen("quinn", tier="date", files=model)
    assert len(plan["flagged"]) == 1 and plan["excluded"] == 0
    done = penlike.screen("quinn", tier="date", run=True, files=model)
    assert done["excluded"] == 1
    restored = penlike.exclude("quinn", done["flagged"], undo=True, files=model)
    assert restored["changed"] == 1


def test_screening_states_its_cost_before_running(model):
    calls = []

    def gauge(text):
        calls.append(text)
        return {"label": "leans-machine" if "committee" in text else "leans-human"}

    from penlike.screening import screen

    docs = penlike.ModelStore("quinn", files=model).read_docs()
    plan = screen(docs, tier="cheap", sample=3, gauge=gauge)
    assert not plan["ran"] and len(calls) == 3
    assert "estimated_seconds" in plan["plan"] and plan["plan"]["costs"]
    ran = screen(docs, tier="cheap", run=True, gauge=gauge)
    assert ran["ran"] and ran["flagged"] and len(ran["flagged"]) < len(docs)


def test_a_named_register_keeps_its_texts(model):
    docs = penlike.ModelStore("quinn", files=model).read_docs()
    ids = [d["id"] for d in docs if d["register"] == "email.many"]
    penlike.register_add(
        "quinn",
        "announcements",
        parent="email.many",
        ids=ids[:10],
        description="formal notices to the whole team",
        files=model,
    )
    found = penlike.registers("quinn", files=model)["registers"]
    assert found["announcements"]["parent"] == "email.many"
    assert found["announcements"]["n_docs"] >= 10
    routed = penlike.route(like="quinn", style="announcements", files=model)
    assert routed["register"] == "announcements"
    # A rebuild never renames or renumbers what a person named.
    penlike.build("quinn", files=model)
    assert "announcements" in penlike.registers("quinn", files=model)["registers"]


def test_proposals_find_the_two_ways_of_writing_filed_together(model, tmp_path):
    def one_register(doc):
        return "everything"

    files = {}
    source = tmp_path / "corpus.jsonl"
    penlike.new("quinn", files=files)
    penlike.gather("quinn", "jsonl", [str(source)], files=files)
    import tests.test_smoke as here

    here.one_register = one_register
    penlike.build("quinn", situate="tests.test_smoke:one_register", files=files)
    assert set(penlike.registers("quinn", files=files)["registers"]) == {"everything"}
    found = penlike.propose("quinn", files=files)["proposals"]
    assert len(found) >= 2 and all(p["parent"] == "everything" for p in found)


def test_notes_need_a_source_to_count_as_observations(model):
    seen = penlike.note(
        "quinn",
        "Opens requests with the problem, then asks.",
        register="email.one",
        source="doc:abc, doc:def",
        files=model,
    )
    guessed = penlike.note("quinn", "May avoid headings on purpose.", files=model)
    assert (seen["kind"], guessed["kind"]) == ("observation", "hypothesis")
    text = penlike.notes("quinn", files=model)["text"]
    assert "[source: doc:abc, doc:def]" in text and "Hypotheses" in text
    brief = penlike.brief(like="quinn", style="email.one", files=model)
    assert "Opens requests" in brief["text"]


def test_only_the_authors_own_texts_are_kept(tmp_path):
    files = {}
    source = tmp_path / "thread.jsonl"
    source.write_text(
        "\n".join(
            json.dumps(d)
            for d in [
                {"text": "This one was written by the author of the model.", "is_self": True},
                {"text": "This one was written by a correspondent instead.", "is_self": False},
            ]
        )
    )
    penlike.new("quinn", files=files)
    kept = penlike.gather("quinn", "jsonl", [str(source)], files=files)
    assert kept["skipped"] == {"by someone else": 1}
    penlike.new("team", kind="group", basis="consent", files=files)
    assert penlike.gather("team", "jsonl", [str(source)], files=files)["added"] == 2


# -- what an independent review found before the first release ------------------------


def test_a_register_name_cannot_leave_the_data_folder(tmp_path):
    def hostile(*refs, **_):
        yield {"text": "A text whose sourcer names a register.", "register": "../../outside"}

    files = {}
    penlike.new("quinn", files=files)
    assert penlike.gather("quinn", hostile, files=files)["skipped"] == {"not usable": 1}

    def up(doc):
        return "../outside"

    import tests.test_smoke as here

    here.up = up
    source = tmp_path / "one.jsonl"
    source.write_text(json.dumps({"text": "One plain text, long enough to be kept."}))
    penlike.gather("quinn", "jsonl", [str(source)], files=files)
    with pytest.raises(penlike.PenlikeError, match="not a usable name"):
        penlike.build("quinn", situate="tests.test_smoke:up", files=files)
    assert all(key.startswith(("models/quinn/", "config/")) for key in files)


def test_naming_a_finer_register_does_not_empty_its_parent(model):
    docs = penlike.ModelStore("quinn", files=model).read_docs()
    ids = [d["id"] for d in docs if d["register"] == "email.one"][:2]
    penlike.register_add("quinn", "board", parent="email.one", ids=ids, files=model)
    found = penlike.registers("quinn", files=model)["registers"]
    assert found["board"]["n_docs"] >= 2 and found["email.one"]["n_docs"] >= 1


def test_register_changes_refuse_what_would_lose_data(model):
    penlike.note("quinn", "Keeps it short.", register="email.one", source="doc:abc", files=model)
    with pytest.raises(penlike.PenlikeError, match="into itself"):
        penlike.register_merge("quinn", "email.one", "email.one", files=model)
    assert "Keeps it short." in penlike.notes("quinn", files=model)["text"]
    with pytest.raises(penlike.PenlikeError, match="no such texts"):
        penlike.register_add("quinn", "ghost", ids=["nope"], files=model)
    assert "ghost" not in penlike.registers("quinn", files=model)["registers"]


def test_figures_from_another_version_ask_for_a_rebuild(model):
    store = penlike.ModelStore("quinn", files=model)
    stored = store.read_profile("_all")
    stored["norm"]["features"] = stored["norm"]["features"][:-1]
    store.write_profile("_all", stored)
    with pytest.raises(penlike.PenlikeError, match="penlike build quinn"):
        penlike.brief(like="quinn", style="email.one", files=model)


def test_a_named_channel_is_not_overridden_by_the_reader(model):
    routed = penlike.route(like="quinn", channel="github", to=[FRIEND], reply=True, files=model)
    assert routed["register"] == "github.reply"


def test_show_keeps_addresses_and_paths_to_itself(model):
    shown = penlike.show("quinn", files=model)
    assert "quinn@example.org" not in json.dumps(shown)
