"""Profiles: what a set of texts has in common, and how far a draft is from it.

A profile is built per register, never across registers: an average over a
person's email and their technical writing describes neither. Every figure keeps
the number of texts it rests on, and a profile built on little text says so
(``provisional``).

Three operations:

- :func:`build_profile` aggregates the measurements of many texts;
- :func:`contrast` says what sets one profile apart from a reference;
- :func:`compare` measures a draft against a profile and lists the discrepancies
  in words a writer can act on.

>>> from penlike.features import measure
>>> texts = ["Short one. Very short.", "Another short one. Tiny.", "Small again. Yes."]
>>> profile = build_profile([measure(t) for t in texts], register="notes")
>>> profile["n_docs"], profile["provisional"], profile["scalars"]["sentence_len_mean"]["n"]
(3, True, 3)
"""

from __future__ import annotations

import math
import statistics
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from penlike.features import FUNCTION_WORDS, PRESENCE_FEATURES, SCALAR_FEATURES

__all__ = [
    "DISTANCE",
    "LABELS",
    "NORM_FORMAT",
    "VECTOR_FEATURES",
    "build_profile",
    "compare",
    "contrast",
    "function_word_vector",
    "norm_is_current",
    "render_profile",
    "style_vector",
    "vector_distance",
]

#: The version of the stored figures. It changes when their layout does.
NORM_FORMAT = 1
#: The distance that style vectors are compared with, recorded next to the figures it
#: produced: thresholds set for one distance mean nothing for another.
DISTANCE = "features-rms-z"


def norm_is_current(norm: Mapping[str, Any] | None) -> bool:
    """Whether stored figures were made by this version's features, word list and distance."""
    return bool(
        norm
        and norm.get("format") == NORM_FORMAT
        and norm.get("distance") == DISTANCE
        and norm.get("features") == list(VECTOR_FEATURES)
        and norm.get("function_word_list") == list(FUNCTION_WORDS)
    )


#: Below this many words a register's distributional figures are provisional. The
#: authorship literature puts the floor for a stable frequency profile at a few
#: thousand words; see the research report.
PROVISIONAL_BELOW_WORDS = 2000
#: A text shorter than this has no usable function-word profile.
FUNCTION_WORD_MIN_WORDS = 100
_Z_CLIP = 3.0
_MIN_DOCS_FOR_SPREAD = 5
_MIN_DOCS_FOR_HABIT = 10
_RARE_SHARE = 0.05
_USUAL_SHARE = 0.9

#: What each feature is called when speaking to a writer.
LABELS = {
    "words": "length in words",
    "sentence_len_mean": "words per sentence",
    "sentence_len_sd": "spread of sentence lengths",
    "short_sentence_share": "share of very short sentences (5 words or fewer)",
    "long_sentence_share": "share of very long sentences (30 words or more)",
    "word_len_mean": "letters per word",
    "long_word_share": "share of long words (7 letters or more)",
    "paragraph_len_mean": "words per paragraph",
    "lexical_diversity": "variety of vocabulary",
    "function_word_share": "share of function words",
    "comma_per_100w": "commas per 100 words",
    "semicolon_per_100w": "semicolons per 100 words",
    "colon_per_100w": "colons per 100 words",
    "dash_per_100w": "dashes per 100 words",
    "parenthesis_per_100w": "parentheses per 100 words",
    "ellipsis_per_100w": "ellipses per 100 words",
    "exclamation_per_100w": "exclamation marks per 100 words",
    "question_per_100w": "question marks per 100 words",
    "contraction_per_100w": "contractions per 100 words",
    "first_singular_per_100w": "I/me/my per 100 words",
    "first_plural_per_100w": "we/us/our per 100 words",
    "second_person_per_100w": "you/your per 100 words",
    "hedge_per_100w": "hedging words per 100 words",
    "intensifier_per_100w": "intensifiers per 100 words",
    "allcaps_per_100w": "all-capital words per 100 words",
    "emoji_per_100w": "emoji and emoticons per 100 words",
    "lowercase_start_share": "share of sentences starting in lower case",
    "has_greeting": "a greeting line",
    "has_signoff": "a closing formula",
    "has_list": "bulleted or numbered lists",
    "has_heading": "headings",
    "has_bold": "bold text",
    "has_code": "code formatting",
    "has_link": "links",
    "has_dash": "dashes",
    "has_semicolon": "semicolons",
    "has_exclamation": "exclamation marks",
    "has_emoji": "emoji or emoticons",
}

#: The features a text's style vector is made of: every scalar but raw length (its
#: logarithm is used, since length otherwise dominates), plus four structural habits.
VECTOR_FEATURES = (
    "log_words",
    *(name for name in SCALAR_FEATURES if name != "words"),
    "has_greeting",
    "has_signoff",
    "has_list",
    "has_code",
)


def _raw_vector(measured: Mapping[str, Any]) -> dict[str, float | None]:
    scalars, presence = measured["scalars"], measured["presence"]
    out: dict[str, float | None] = {}
    for name in VECTOR_FEATURES:
        if name == "log_words":
            out[name] = math.log1p(measured["n_words"])
        elif name in presence:
            out[name] = 1.0 if presence[name] else 0.0
        else:
            out[name] = scalars.get(name)
    return out


def _spread(values: Sequence[float]) -> dict[str, float]:
    return {
        "mean": round(statistics.fmean(values), 4),
        "sd": round(statistics.pstdev(values), 4) if len(values) > 1 else 0.0,
        "median": round(statistics.median(values), 4),
        "n": len(values),
    }


def function_word_vector(
    measured: Mapping[str, Any], norm: Mapping[str, Any] | None
) -> list[float] | None:
    """A text's function-word rates as z-scores against ``norm``, or ``None`` if too short.

    This is the vector Cosine Delta compares. ``norm`` holds the mean and standard
    deviation of each word's rate over a population of texts.
    """
    n = measured["n_words"]
    if not norm or n < FUNCTION_WORD_MIN_WORDS:
        return None
    counts = measured["function_words"]
    vector = []
    for word, mean, sd in zip(FUNCTION_WORDS, norm["mean"], norm["sd"]):
        rate = 1000.0 * counts.get(word, 0) / n
        vector.append(0.0 if sd <= 0 else (rate - mean) / sd)
    return vector


def _cosine_distance(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return 1.0 if norm == 0 else round(1.0 - dot / norm, 4)


def style_vector(
    measured: Mapping[str, Any], norm: Mapping[str, Mapping[str, float]]
) -> list[float]:
    """A text's style vector: each feature as a clipped z-score against ``norm``.

    A feature the text is too short to have counts as average (zero).
    """
    raw = _raw_vector(measured)
    vector = []
    for name in VECTOR_FEATURES:
        value, stats = raw[name], norm.get(name)
        if value is None or not stats or stats["sd"] <= 0:
            vector.append(0.0)
        else:
            z = (value - stats["mean"]) / stats["sd"]
            vector.append(max(-_Z_CLIP, min(_Z_CLIP, z)))
    return vector


def vector_distance(a: Sequence[float], b: Sequence[float]) -> float:
    """Root-mean-square difference between two style vectors.

    >>> vector_distance([0.0, 0.0], [3.0, 4.0])
    3.5355
    """
    return round(math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / max(len(a), 1)), 4)


def _mean_vector(vectors: Sequence[Sequence[float]]) -> list[float]:
    return [round(statistics.fmean(column), 4) for column in zip(*vectors)]


def build_norm(measurements: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """The population figures that style and function-word vectors are scored against."""
    measurements = list(measurements)
    columns: dict[str, list[float]] = {name: [] for name in VECTOR_FEATURES}
    for measured in measurements:
        for name, value in _raw_vector(measured).items():
            if value is not None:
                columns[name].append(value)
    style = {
        name: {k: v for k, v in _spread(values).items() if k in ("mean", "sd")}
        for name, values in columns.items()
        if values
    }
    long_enough = [m for m in measurements if m["n_words"] >= FUNCTION_WORD_MIN_WORDS]
    words = None
    if len(long_enough) >= _MIN_DOCS_FOR_SPREAD:
        rates = [
            [1000.0 * m["function_words"].get(w, 0) / m["n_words"] for m in long_enough]
            for w in FUNCTION_WORDS
        ]
        words = {
            "mean": [round(statistics.fmean(r), 4) for r in rates],
            "sd": [round(statistics.pstdev(r), 4) for r in rates],
            "n": len(long_enough),
        }
    return {
        "format": NORM_FORMAT,
        "distance": DISTANCE,
        "features": list(VECTOR_FEATURES),
        "function_word_list": list(FUNCTION_WORDS),
        "style": style,
        "function_words": words,
    }


def build_profile(
    measurements: Iterable[Mapping[str, Any]],
    *,
    register: str = "",
    norm: Mapping[str, Any] | None = None,
    others: Iterable[Mapping[str, Any]] = (),
    min_phrase_docs: int = 3,
    max_phrases: int = 40,
) -> dict[str, Any]:
    """Aggregate the measurements of a register's texts into its profile.

    ``norm`` (from :func:`build_norm`) adds the register's centroid and the
    function-word calibration: how far the register's own texts sit from it (the
    ceiling for a draft) and how far texts of ``others`` registers sit (the floor).
    """
    measurements = list(measurements)
    n_docs = len(measurements)
    n_words = sum(m["n_words"] for m in measurements)
    scalars = {}
    for name in SCALAR_FEATURES:
        values = [m["scalars"][name] for m in measurements if m["scalars"].get(name) is not None]
        if values:
            scalars[name] = _spread(values)
    presence = (
        {
            name: round(sum(bool(m["presence"][name]) for m in measurements) / n_docs, 4)
            for name in PRESENCE_FEATURES
        }
        if n_docs
        else {}
    )

    def forms(key: str) -> list[list[Any]]:
        counted = Counter(m[key] for m in measurements if m.get(key))
        return [[form, count] for form, count in counted.most_common(12)]

    totals: Counter[str] = Counter()
    phrase_docs: Counter[str] = Counter()
    opener_docs: Counter[str] = Counter()
    for measured in measurements:
        totals.update(measured["function_words"])
        phrase_docs.update(measured["ngrams"].keys())
        opener_docs.update(measured["openers"].keys())
    function_words = {
        word: round(1000.0 * totals[word] / n_words, 3)
        for word in FUNCTION_WORDS
        if n_words and totals[word]
    }
    phrases = _recurrent(phrase_docs, min_docs=min_phrase_docs, limit=max_phrases)
    openers = [
        [form, count] for form, count in opener_docs.most_common(15) if count >= min_phrase_docs
    ]

    profile: dict[str, Any] = {
        "register": register,
        "n_docs": n_docs,
        "n_words": n_words,
        "provisional": n_words < PROVISIONAL_BELOW_WORDS,
        "scalars": scalars,
        "presence": presence,
        "greetings": forms("greeting"),
        "signoffs": forms("signoff"),
        "signatures": forms("signature"),
        "function_words": function_words,
        "phrases": phrases,
        "openers": openers,
    }
    if norm and measurements:
        profile["centroid"] = _mean_vector([style_vector(m, norm["style"]) for m in measurements])
        profile["calibration"] = _calibrate(measurements, list(others), norm["function_words"])
    return profile


def _recurrent(doc_counts: Counter[str], *, min_docs: int, limit: int) -> list[list[Any]]:
    """Word sequences found in several texts, longest first, without their own fragments."""
    kept: list[tuple[str, int]] = []
    candidates = sorted(
        ((g, c) for g, c in doc_counts.items() if c >= min_docs),
        key=lambda item: (-len(item[0].split()), -item[1], item[0]),
    )

    def pairs(gram: str) -> set[tuple[str, str]]:
        tokens = gram.split()
        return set(zip(tokens, tokens[1:]))

    for gram, count in candidates:
        # A sequence that overlaps one already kept, and is seen in about as many
        # texts, is the same habit caught through a shifted window.
        if any(pairs(gram) & pairs(other) and count <= seen + 1 for other, seen in kept):
            continue
        kept.append((gram, count))
    kept.sort(key=lambda item: (-item[1], item[0]))
    return [[gram, count] for gram, count in kept[:limit]]


def _calibrate(
    own: Sequence[Mapping[str, Any]],
    others: Sequence[Mapping[str, Any]],
    norm: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    vectors = [v for v in (function_word_vector(m, norm) for m in own) if v is not None]
    if len(vectors) < _MIN_DOCS_FOR_SPREAD:
        return None
    sums = [sum(column) for column in zip(*vectors)]
    k = len(vectors)
    # Leave-one-out: each text is compared with the centroid of the *other* texts.
    own_distances = [
        _cosine_distance(v, [(s - x) / (k - 1) for s, x in zip(sums, v)]) for v in vectors
    ]
    centroid = [round(s / k, 4) for s in sums]
    other_vectors = [v for v in (function_word_vector(m, norm) for m in others) if v is not None]
    other_distances = [_cosine_distance(v, centroid) for v in other_vectors]
    return {
        "centroid": centroid,
        "own": _spread(own_distances),
        "others": _spread(other_distances)
        if len(other_distances) >= _MIN_DOCS_FOR_SPREAD
        else None,
    }


def contrast(
    profile: Mapping[str, Any], reference: Mapping[str, Any], *, top: int = 8
) -> dict[str, list[dict[str, Any]]]:
    """What sets ``profile`` apart from ``reference``: the largest differences, in both directions.

    Differences in averages are given in pooled standard deviations, differences in
    habits as shares of texts, and function words as a ratio of rates.
    """
    features = []
    for name, stats in profile.get("scalars", {}).items():
        other = reference.get("scalars", {}).get(name)
        if not other or min(stats["n"], other["n"]) < _MIN_DOCS_FOR_SPREAD:
            continue
        pooled = math.sqrt((stats["sd"] ** 2 + other["sd"] ** 2) / 2)
        if pooled <= 0:
            continue
        effect = (stats["mean"] - other["mean"]) / pooled
        if abs(effect) >= 0.5:
            features.append(
                {
                    "feature": name,
                    "label": LABELS[name],
                    "here": stats["mean"],
                    "reference": other["mean"],
                    "effect": round(effect, 2),
                }
            )
    features.sort(key=lambda item: -abs(item["effect"]))

    habits = []
    for name, share in profile.get("presence", {}).items():
        other = reference.get("presence", {}).get(name)
        if other is not None and abs(share - other) >= 0.25:
            habits.append(
                {"feature": name, "label": LABELS[name], "here": share, "reference": other}
            )
    habits.sort(key=lambda item: -abs(item["here"] - item["reference"]))

    words = []
    smoothing = 0.5  # per 1000 words, so that a word absent on one side has a finite ratio
    here, there = profile.get("function_words", {}), reference.get("function_words", {})
    for word in set(here) | set(there):
        a, b = here.get(word, 0.0), there.get(word, 0.0)
        if max(a, b) < 1.0:
            continue
        ratio = math.log2((a + smoothing) / (b + smoothing))
        if abs(ratio) >= 1.0:
            words.append({"word": word, "here": a, "reference": b, "log2_ratio": round(ratio, 2)})
    words.sort(key=lambda item: -abs(item["log2_ratio"]))
    return {"features": features[:top], "habits": habits[:top], "words": words[:top]}


def _show(name: str, value: float) -> str:
    """A figure as a reader wants it: shares as percentages, the rest to three digits."""
    if name.endswith("_share") or name.startswith("has_"):
        return f"{value:.0%}"
    return f"{value:.3g}"


def _describe(name: str, value: float, stats: Mapping[str, float]) -> str:
    direction = "higher" if value > stats["mean"] else "lower"
    return (
        f"{LABELS[name]}: {_show(name, value)} in the draft, {direction} than the author's "
        f"usual {_show(name, stats['mean'])} (spread {_show(name, stats['sd'])}, "
        f"over {stats['n']} texts)"
    )


def compare(
    measured: Mapping[str, Any],
    profile: Mapping[str, Any],
    *,
    norm: Mapping[str, Any] | None = None,
    threshold: float = 2.0,
    min_words_for_rates: int = 30,
) -> dict[str, Any]:
    """Measure a draft against a register's profile and list what differs.

    A discrepancy is reported when the draft sits more than ``threshold`` of the
    author's own standard deviations from their average, when it shows a habit the
    author almost never has, or lacks one they almost always have. Each comes with
    the figures, so the next revision has something concrete to change.

    The function-word distance, when both the draft and the profile are long enough,
    is reported next to two references from the author's own texts: how far they sit
    from each other (``own``) and how far their other registers sit (``others``).
    """
    n_words = measured["n_words"]
    discrepancies: list[dict[str, Any]] = []
    for name, stats in profile.get("scalars", {}).items():
        value = measured["scalars"].get(name)
        if value is None or stats["n"] < _MIN_DOCS_FOR_SPREAD or name == "words":
            continue
        if name.endswith(("_per_100w", "_share")) and n_words < min_words_for_rates:
            continue
        # A floor on the spread, so that a habit the author never varies does not
        # turn a rounding difference into an alarm.
        floor = 0.1 * abs(stats["mean"]) + 0.05
        z = (value - stats["mean"]) / max(stats["sd"], floor)
        if abs(z) >= threshold:
            discrepancies.append(
                {
                    "feature": name,
                    "kind": "level",
                    "z": round(z, 2),
                    "draft": value,
                    "usual": stats["mean"],
                    "message": _describe(name, value, stats),
                }
            )
    n_docs = profile.get("n_docs", 0)
    if n_docs >= _MIN_DOCS_FOR_HABIT:
        for name, share in profile.get("presence", {}).items():
            shown = bool(measured["presence"].get(name))
            if shown and share <= _RARE_SHARE:
                message = f"the draft uses {LABELS[name]}; the author does in {share:.0%} of {n_docs} texts"
            elif not shown and share >= _USUAL_SHARE:
                thing = LABELS[name].removeprefix("a ")
                message = (
                    f"the draft has no {thing}; the author has in {share:.0%} of {n_docs} texts"
                )
            else:
                continue
            discrepancies.append(
                {
                    "feature": name,
                    "kind": "habit",
                    "draft": shown,
                    "usual": share,
                    "message": message,
                }
            )
    for key, label in (("greeting", "greeting"), ("signoff", "closing formula")):
        form, known = measured.get(key), [f for f, _ in profile.get(f"{key}s", [])]
        if form and known and form not in known:
            discrepancies.append(
                {
                    "feature": key,
                    "kind": "form",
                    "draft": form,
                    "usual": known[:3],
                    "message": f"the {label} {form!r} is not one the author uses; theirs: "
                    + ", ".join(repr(f) for f in known[:3]),
                }
            )
    discrepancies.sort(key=lambda d: -abs(d.get("z", threshold + 1)))

    distance = None
    calibration = profile.get("calibration")
    if calibration and norm:
        vector = function_word_vector(measured, norm.get("function_words"))
        if vector is not None:
            value = _cosine_distance(vector, calibration["centroid"])
            own = calibration["own"]
            distance = {
                "value": value,
                "own": own,
                "others": calibration.get("others"),
                "within_own_range": value <= own["mean"] + 2 * own["sd"],
            }
    return {
        "n_words": n_words,
        "discrepancies": discrepancies,
        "function_word_distance": distance,
        "provisional": bool(profile.get("provisional")),
    }


def render_profile(
    profile: Mapping[str, Any], *, differences: Mapping[str, Any] | None = None
) -> str:
    """A profile as plain lines an agent can follow when writing.

    Figures are given as the author's typical value and range, because a target
    range is something a draft can be held to and a bare average is not.
    """
    lines = []
    n_docs, n_words = profile.get("n_docs", 0), profile.get("n_words", 0)
    basis = f"Measured on {n_docs} texts, {n_words} words."
    if profile.get("provisional"):
        basis += (
            f" Provisional: under {PROVISIONAL_BELOW_WORDS} words, so treat the figures as rough."
        )
    lines.append(basis)

    scalars = profile.get("scalars", {})

    def typical(name: str) -> str | None:
        stats = scalars.get(name)
        if not stats:
            return None
        low, high = max(stats["mean"] - stats["sd"], 0), stats["mean"] + stats["sd"]
        return (
            f"{LABELS[name]}: typically {_show(name, stats['median'])} "
            f"(usual range {_show(name, low)} to {_show(name, high)})"
        )

    shape = [
        typical(n)
        for n in (
            "words",
            "sentence_len_mean",
            "paragraph_len_mean",
            "short_sentence_share",
            "long_sentence_share",
        )
    ]
    lines += ["", "Length and shape:"] + [f"- {x}" for x in shape if x]

    marks = []
    for name in SCALAR_FEATURES:
        if not name.endswith("_per_100w") or name not in scalars:
            continue
        stats = scalars[name]
        if stats["mean"] < 0.05:
            marks.append(f"- {LABELS[name]}: almost never")
        else:
            marks.append(f"- {typical(name)}")
    lines += ["", "Punctuation and word habits:"] + marks

    presence = profile.get("presence", {})
    if presence:
        lines += ["", "Habits (share of texts that show them):"]
        lines += [f"- {LABELS[name]}: {share:.0%}" for name, share in presence.items()]

    for key, title in (
        ("greetings", "Greetings"),
        ("signoffs", "Closing formulas"),
        ("signatures", "Signatures"),
    ):
        forms = profile.get(key) or []
        if forms:
            lines += ["", f"{title} (times seen):"]
            lines += [f"- {form!r}: {count}" for form, count in forms[:6]]
    if profile.get("phrases"):
        lines += ["", "Word sequences the author returns to (texts containing them):"]
        lines += [f"- {gram!r}: {count}" for gram, count in profile["phrases"][:15]]

    if differences and any(differences.values()):
        lines += ["", "What sets this register apart from the reference:"]
        for item in differences.get("features", []):
            word = "higher" if item["effect"] > 0 else "lower"
            here, there = (
                _show(item["feature"], item["here"]),
                _show(item["feature"], item["reference"]),
            )
            lines.append(f"- {item['label']}: {here} here, {there} there ({word})")
        for item in differences.get("habits", []):
            lines.append(
                f"- {item['label']}: {item['here']:.0%} of texts here, {item['reference']:.0%} there"
            )
        more = [w["word"] for w in differences.get("words", []) if w["log2_ratio"] > 0]
        less = [w["word"] for w in differences.get("words", []) if w["log2_ratio"] < 0]
        if more:
            lines.append("- function words used more here: " + ", ".join(more))
        if less:
            lines.append("- function words used less here: " + ", ".join(less))
    return "\n".join(lines)
