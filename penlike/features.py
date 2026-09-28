"""Measure how a text is written: the cheap tier, standard library only.

:func:`measure` turns one text into numbers and forms that describe its style and
say little about its topic: sentence and word lengths, punctuation rates, function
words, contractions, greetings and sign-offs, formatting habits, recurring word
sequences. The choice of features follows the stylometry literature (see
``misc/docs/research_report.md``): frequent and function words are the most robust
signal, punctuation and affix habits carry most of what character n-grams know,
and openings and closings are where an individual is most recognisable.

The word lists are English. On other languages the language-neutral features
(lengths, punctuation, formatting) still hold and the word-list rates read low.

>>> m = measure("Hi Ada,\\n\\nI think it's fine. Shall we ship it?\\n\\nCheers,\\nGrace")
>>> m["greeting"], m["signoff"], m["scalars"]["question_per_100w"] > 0
('Hi <name>,', 'Cheers,', True)
"""

from __future__ import annotations

import re
import statistics
from collections import Counter
from typing import Any

from penlike.base import prose_of

__all__ = [
    "FUNCTION_WORDS",
    "PRESENCE_FEATURES",
    "SCALAR_FEATURES",
    "measure",
    "sentences_of",
    "words_of",
]

#: English function words: closed-class words whose rates depend on the writer and the
#: register far more than on the topic.
FUNCTION_WORDS = tuple(
    """a about above after again against all almost also although always am among an and
    another any anyone anything are around as at be because been before being below
    between both but by can cannot could did do does doing done down during each either
    enough even ever every everyone everything few for from further had has have having
    he her here hers herself him himself his how however i if in into is it its itself
    just least less many may me might more most much must my myself neither never no
    nobody none nor not nothing now of off often on once one only onto or other others
    ought our ours ourselves out over own perhaps quite rather same shall she should
    since so some someone something still such than that the their theirs them
    themselves then there these they this those though through thus to too toward under
    until up upon us very was we were what whatever when where whether which while who
    whom whose why will with within without would yet you your yours yourself""".split()
)
_FUNCTION_WORD_SET = frozenset(FUNCTION_WORDS)

_HEDGES = frozenset(
    """maybe perhaps possibly probably apparently seemingly somewhat roughly arguably
    presumably might could guess suppose seems seem appears appear likely unlikely
    sort kind""".split()
)
_INTENSIFIERS = frozenset(
    """very really extremely absolutely totally completely highly incredibly truly
    definitely certainly super so quite utterly deeply hugely""".split()
)
_FIRST_SINGULAR = frozenset("i me my mine myself".split())
_FIRST_PLURAL = frozenset("we us our ours ourselves".split())
_SECOND_PERSON = frozenset("you your yours yourself yourselves".split())

_WORD_RE = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?…])[\"')\]]*\s+(?=[\"'(\[]?[A-Z0-9])|\n+")
_CONTRACTION_RE = re.compile(r"[^\W\d_]+['’](?:s|t|re|ve|ll|d|m)\b", re.IGNORECASE)
_EMOJI_RE = re.compile("[\U0001f300-\U0001faff☀-➿]|(?<![\\w:])[:;=]-?[)(DPp](?!\\w)")
_LIST_LINE_RE = re.compile(r"^\s*(?:[-*+•]|\d+[.)])\s+\S")
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+\S")
_BOLD_RE = re.compile(r"\*\*[^*\n]+\*\*|__[^_\n]+__")
_CODE_RE = re.compile(r"```|~~~|`[^`\n]+`")
_LINK_RE = re.compile(r"https?://|\[[^\]]+\]\([^)]+\)")

_GREETING_RE = re.compile(
    r"^(hi|hello|hey|heya|hiya|dear|greetings|good (?:morning|afternoon|evening|day)"
    r"|bonjour|salut|hola|ciao|yo)\b",
    re.IGNORECASE,
)
_NAME_ONLY_GREETING_RE = re.compile(r"^[A-Z][\w'’-]+(?: [A-Z][\w'’-]+)?\s*[,:\-–—]\s*$")
_SIGNOFF_RE = re.compile(
    r"^(thanks|thank you|thx|many thanks|cheers|best|all the best|best wishes"
    r"|regards|best regards|kind regards|warm regards|warmly|sincerely|yours"
    r"|take care|talk soon|later|ciao|cordialement|bien à vous|a\+|à bientôt"
    r"|looking forward|hope (?:this|that) helps)\b",
    re.IGNORECASE,
)

#: Rates and averages, one number per text. ``None`` when the text is too short for it.
SCALAR_FEATURES = (
    "words",
    "sentence_len_mean",
    "sentence_len_sd",
    "short_sentence_share",
    "long_sentence_share",
    "word_len_mean",
    "long_word_share",
    "paragraph_len_mean",
    "lexical_diversity",
    "function_word_share",
    "comma_per_100w",
    "semicolon_per_100w",
    "colon_per_100w",
    "dash_per_100w",
    "parenthesis_per_100w",
    "ellipsis_per_100w",
    "exclamation_per_100w",
    "question_per_100w",
    "contraction_per_100w",
    "first_singular_per_100w",
    "first_plural_per_100w",
    "second_person_per_100w",
    "hedge_per_100w",
    "intensifier_per_100w",
    "allcaps_per_100w",
    "emoji_per_100w",
    "lowercase_start_share",
)

#: Habits that a text either shows or does not. A profile keeps the share of texts that do.
PRESENCE_FEATURES = (
    "has_greeting",
    "has_signoff",
    "has_list",
    "has_heading",
    "has_bold",
    "has_code",
    "has_link",
    "has_dash",
    "has_semicolon",
    "has_exclamation",
    "has_emoji",
)

_LEXICAL_DIVERSITY_WINDOW = 50
_SHORT_SENTENCE = 5
_LONG_SENTENCE = 30
_LONG_WORD = 7
_NGRAM_SIZES = (3, 4)


def words_of(text: str) -> list[str]:
    """The words of a text, lowercased.

    >>> words_of("Don't Panic, it's fine.")
    ["don't", 'panic', "it's", 'fine']
    """
    return [w.lower().replace("’", "'") for w in _WORD_RE.findall(text)]


def sentences_of(text: str) -> list[str]:
    """Split prose into sentences, treating a line break as a boundary.

    >>> sentences_of("It works. Does it? Yes!")
    ['It works.', 'Does it?', 'Yes!']
    """
    parts = (part.strip() for part in _SENTENCE_SPLIT_RE.split(text))
    return [part for part in parts if _WORD_RE.search(part)]


def _per_100(count: int, n_words: int) -> float:
    return round(100.0 * count / n_words, 3) if n_words else 0.0


def _moving_average_ttr(words: list[str], window: int) -> float | None:
    """Moving-average type-token ratio: lexical diversity that does not depend on length."""
    if len(words) < window:
        return None
    counts = Counter(words[:window])
    total = len(counts) / window
    for start in range(1, len(words) - window + 1):
        gone, new = words[start - 1], words[start + window - 1]
        counts[gone] -= 1
        if not counts[gone]:
            del counts[gone]
        counts[new] += 1
        total += len(counts) / window
    return round(total / (len(words) - window + 1), 4)


def _mask_names(line: str, *, after: int) -> str:
    """Replace the capitalised words after the first ``after`` characters with ``<name>``."""
    head, tail = line[:after], line[after:]
    tail = re.sub(r"[A-Z][\w'’-]+(?:\s+[A-Z][\w'’-]+)*", "<name>", tail)
    return head + tail


def _greeting(lines: list[str]) -> str:
    """The opening line when it greets someone, with the name masked and the punctuation kept."""
    if not lines:
        return ""
    first = lines[0].strip()
    if len(first.split()) > 6:
        return ""
    match = _GREETING_RE.match(first)
    if match:
        return _mask_names(first, after=match.end())
    if _NAME_ONLY_GREETING_RE.match(first) and len(lines) > 1:
        return _mask_names(first, after=0)
    return ""


def _signoff(lines: list[str]) -> tuple[str, str]:
    """The closing formula and the signature form, from the last few lines."""
    tail = [line.strip() for line in lines[-4:]]
    for index, line in enumerate(tail):
        if len(line.split()) <= 5 and _SIGNOFF_RE.match(line):
            after = [x for x in tail[index + 1 :] if x]
            signature = ""
            if after and len(after[0].split()) <= 3 and after[0][:1].isupper():
                signature = after[0]
            return line, signature
    last = tail[-1] if tail else ""
    if last and len(last.split()) <= 2 and last[:1].isupper() and last[-1:].isalpha():
        if len(lines) > 2:
            return "", last
    return "", ""


def measure(text: str) -> dict[str, Any]:
    """Measure one text. Returns scalars, presence flags, forms and counters.

    The result is JSON-ready. ``scalars`` holds one number per name in
    :data:`SCALAR_FEATURES` (or ``None``), ``presence`` one boolean per name in
    :data:`PRESENCE_FEATURES`.

    >>> m = measure("We shipped it; nobody noticed. Odd, really odd!")
    >>> m["n_words"], m["presence"]["has_semicolon"], m["scalars"]["exclamation_per_100w"]
    (8, True, 12.5)
    """
    prose = prose_of(text)
    lines = [line for line in prose.split("\n") if line.strip()]
    words = words_of(prose)
    n = len(words)
    sentences = sentences_of(prose)
    sentence_lengths = [len(words_of(s)) for s in sentences]
    paragraphs = [p for p in re.split(r"\n\s*\n", prose) if _WORD_RE.search(p)]
    greeting = _greeting(lines)
    signoff, signature = _signoff(lines)

    raw_words = _WORD_RE.findall(prose)
    dashes = len(re.findall(r"—|–| -- | - ", prose))
    counts = {
        "comma": prose.count(","),
        "semicolon": prose.count(";"),
        "colon": len(re.findall(r":(?!\w)", prose)),
        "dash": dashes,
        "parenthesis": prose.count("("),
        "ellipsis": len(re.findall(r"\.{3,}|…", prose)),
        "exclamation": prose.count("!"),
        "question": prose.count("?"),
        "contraction": len(_CONTRACTION_RE.findall(prose)),
        "first_singular": sum(w in _FIRST_SINGULAR for w in words),
        "first_plural": sum(w in _FIRST_PLURAL for w in words),
        "second_person": sum(w in _SECOND_PERSON for w in words),
        "hedge": sum(w in _HEDGES for w in words),
        "intensifier": sum(w in _INTENSIFIERS for w in words),
        "allcaps": sum(len(w) > 1 and w.isupper() and w not in ("CODE", "LINK") for w in raw_words),
        "emoji": len(_EMOJI_RE.findall(prose)),
    }
    function_words = Counter(w for w in words if w in _FUNCTION_WORD_SET)

    scalars: dict[str, float | None] = {
        "words": n,
        "sentence_len_mean": None,
        "sentence_len_sd": None,
        "short_sentence_share": None,
        "long_sentence_share": None,
        "word_len_mean": None,
        "long_word_share": None,
        "paragraph_len_mean": None,
        "lexical_diversity": _moving_average_ttr(words, _LEXICAL_DIVERSITY_WINDOW),
        "function_word_share": None,
        "lowercase_start_share": None,
    }
    if sentence_lengths:
        k = len(sentence_lengths)
        scalars["sentence_len_mean"] = round(statistics.fmean(sentence_lengths), 3)
        scalars["sentence_len_sd"] = (
            round(statistics.pstdev(sentence_lengths), 3) if k > 1 else None
        )
        scalars["short_sentence_share"] = round(
            sum(x <= _SHORT_SENTENCE for x in sentence_lengths) / k, 4
        )
        scalars["long_sentence_share"] = round(
            sum(x >= _LONG_SENTENCE for x in sentence_lengths) / k, 4
        )
        starts = [s.lstrip("\"'([*_-•0123456789. ")[:1] for s in sentences]
        starts = [c for c in starts if c.isalpha()]
        if starts:
            scalars["lowercase_start_share"] = round(
                sum(c.islower() for c in starts) / len(starts), 4
            )
    if n:
        lengths = [len(w.replace("'", "")) for w in words]
        scalars["word_len_mean"] = round(statistics.fmean(lengths), 3)
        scalars["long_word_share"] = round(sum(x >= _LONG_WORD for x in lengths) / n, 4)
        scalars["function_word_share"] = round(sum(function_words.values()) / n, 4)
        scalars["paragraph_len_mean"] = round(n / max(len(paragraphs), 1), 3)
    for name, count in counts.items():
        scalars[f"{name}_per_100w"] = _per_100(count, n)

    presence = {
        "has_greeting": bool(greeting),
        "has_signoff": bool(signoff),
        "has_list": any(_LIST_LINE_RE.match(line) for line in text.split("\n")),
        "has_heading": any(_HEADING_RE.match(line) for line in text.split("\n")),
        "has_bold": bool(_BOLD_RE.search(text)),
        "has_code": bool(_CODE_RE.search(text)),
        "has_link": bool(_LINK_RE.search(text)),
        "has_dash": dashes > 0,
        "has_semicolon": counts["semicolon"] > 0,
        "has_exclamation": counts["exclamation"] > 0,
        "has_emoji": counts["emoji"] > 0,
    }

    ngrams: Counter[str] = Counter()
    for sentence in sentences:
        tokens = words_of(sentence)
        for size in _NGRAM_SIZES:
            for start in range(len(tokens) - size + 1):
                gram = tokens[start : start + size]
                if "code" in gram or "link" in gram:
                    continue
                ngrams[" ".join(gram)] += 1
    openers = Counter(" ".join(words_of(s)[:2]) for s in sentences if len(words_of(s)) >= 3)

    return {
        "n_words": n,
        "n_sentences": len(sentences),
        "n_paragraphs": len(paragraphs),
        "scalars": scalars,
        "presence": presence,
        "greeting": greeting,
        "signoff": signoff,
        "signature": signature,
        "function_words": dict(function_words),
        "ngrams": dict(ngrams),
        "openers": dict(openers),
    }
