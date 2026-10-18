"""Long-text registers: examples are excerpts, and figures never use scientific notation."""

import json
import re

import pytest

import penlike
from penlike.profile import plain_number
from penlike.routing import excerpt, select_exemplars
from tests.corpus import fictional_essays

WORDS = 120


@pytest.fixture
def essays(tmp_path):
    files = {}
    source = tmp_path / "essays.jsonl"
    source.write_text("\n".join(json.dumps(d) for d in fictional_essays()), encoding="utf-8")
    penlike.new("essayist", kind="corpus", files=files)
    penlike.gather("essayist", "jsonl", [str(source)], files=files)
    penlike.build("essayist", files=files)
    return files


def _doc(paragraphs):
    text = "\n\n".join(paragraphs)
    return {"id": "d1", "text": text, "words": len(text.split()), "date": "2020-01-01"}


def test_brief_offers_excerpts_for_a_register_of_long_texts(essays):
    brief = penlike.brief(like="essayist", style="document", words=WORDS, files=essays)
    text = brief["text"]
    assert "(no example of usable length" not in text
    found = re.findall(r'<example id="([^"]+)"[^>]*excerpt="true" of_words="(\d+)">', text)
    assert 2 <= len(found) <= 3
    assert "excerpts" in text
    lengths = [len(m.split()) for m in re.findall(r"<example[^>]*>\n(.*?)\n</example>", text, re.S)]
    assert all(WORDS / 2 <= n <= WORDS * 2 for n in lengths)
    assert all(int(of_words) > 400 for _, of_words in found)


def test_exemplars_returns_the_same_excerpts(essays):
    found = penlike.exemplars(like="essayist", style="document", words=WORDS, files=essays)
    assert found["ok"] and found["summary"].endswith("document") and "excerpts" in found["summary"]
    assert all(e["excerpt"] and e["of_words"] > e["words"] for e in found["exemplars"])


def test_excerpts_are_whole_paragraphs_from_the_middle():
    paragraphs = [f"p{i} " + "word " * 39 for i in range(20)]
    found = excerpt(_doc(paragraphs), words=80)
    kept = [p for p in found["text"].split("\n\n")]
    assert all(p in [q.strip() for q in paragraphs] for p in kept)
    first = [q.strip() for q in paragraphs].index(kept[0])
    assert 5 <= first and first + len(kept) <= 15  # not the opening, not the end
    assert found["excerpt"] and found["of_words"] == 20 * 40


def test_one_huge_paragraph_is_cut_at_sentences():
    sentence = "This is a sentence of exactly eight words long. "
    found = excerpt(_doc([sentence * 100]), words=40)
    assert found["text"].endswith(".") and 24 <= found["words"] <= 80


def test_a_register_with_short_texts_keeps_showing_only_those():
    short = {"id": "s", "text": "a b c " * 10, "words": 30, "date": "2020-01-01"}
    long = _doc(["word " * 100] * 10)
    assert select_exemplars([short, long], n=5, words=100) == [short]


def test_excerpts_put_the_readers_texts_first():
    mine = {**_doc(["word " * 100] * 10), "id": "mine", "to": ["a@example.org"]}
    other = {**_doc(["word " * 100] * 10), "id": "other", "to": ["b@example.org"]}
    picked = select_exemplars([other, mine], n=1, to=["a@example.org"], words=100)
    assert [d["id"] for d in picked] == ["mine"]


def test_text_without_sentence_ends_is_cut_by_length():
    flat = _doc(["word " * 2000])
    found = excerpt(flat, words=100)
    assert found is not None and 50 <= found["words"] <= 200
    unbroken = _doc([("word " * 400).strip()] * 3)
    assert excerpt(unbroken, words=100)["words"] <= 200


def test_degenerate_arguments_do_not_raise():
    assert excerpt({"id": "x", "text": None}, words=100) is None
    assert excerpt(_doc(["word " * 50] * 10), words=0)["words"] >= 1


def test_a_text_with_nothing_to_cut_gives_no_excerpt():
    assert excerpt(_doc(["just a few words here"]), words=100) is None


@pytest.mark.parametrize(
    ("value", "shown"),
    [(2840.0, "2800"), (0.01234, "0.012"), (12.34, "12"), (0, "0"), (1.5e-05, "0.000015")],
)
def test_plain_number_is_never_scientific(value, shown):
    assert plain_number(value) == shown


def test_no_scientific_notation_in_a_brief(essays):
    text = penlike.brief(like="essayist", style="document", files=essays)["text"]
    assert not re.search(r"\d[eE][+-]\d", text)
    assert re.search(r"length in words: typically \d+ \(usual range \d+ to \d+\)", text)


def test_small_lengths_keep_their_digits():
    from penlike.profile import show_figure

    assert show_figure("words", 2840.3) == "2840"
    assert show_figure("sentence_len_mean", 14.8) == "14.8"
    assert show_figure("sentence_len_sd", 0.4) == "0.4"
    assert show_figure("comma_per_100w", 2.84) == "2.8"
    assert show_figure("long_sentence_share", 0.124) == "12%"


def test_measure_reports_lengths_as_the_summary_does():
    found = penlike.measure("word " * 2840)
    assert "words: 2840" in found["text"]
