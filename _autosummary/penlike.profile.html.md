# penlike.profile

Profiles: what a set of texts has in common, and how far a draft is from it.

A profile is built per register, never across registers: an average over a
person’s email and their technical writing describes neither. Every figure keeps
the number of texts it rests on, and a profile built on little text says so
(`provisional`).

Three operations:

- [`build_profile()`](#penlike.profile.build_profile) aggregates the measurements of many texts;
- [`contrast()`](#penlike.profile.contrast) says what sets one profile apart from a reference;
- [`compare()`](#penlike.profile.compare) measures a draft against a profile and lists the discrepancies
  in words a writer can act on.

```pycon
>>> from penlike.features import measure
>>> texts = ["Short one. Very short.", "Another short one. Tiny.", "Small again. Yes."]
>>> profile = build_profile([measure(t) for t in texts], register="notes")
>>> profile["n_docs"], profile["provisional"], profile["scalars"]["sentence_len_mean"]["n"]
(3, True, 3)
```

### Module Attributes

| [`NORM_FORMAT`](#penlike.profile.NORM_FORMAT)     | The version of the stored figures.                                                                                                                     |
|------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`DISTANCE`](#penlike.profile.DISTANCE)        | The distance that style vectors are compared with, recorded next to the figures it produced: thresholds set for one distance mean nothing for another. |
| [`LABELS`](#penlike.profile.LABELS)          | What each feature is called when speaking to a writer.                                                                                                 |
| [`VECTOR_FEATURES`](#penlike.profile.VECTOR_FEATURES) | every scalar but raw length (its logarithm is used, since length otherwise dominates), plus four structural habits.                                    |

### Functions

| [`build_profile`](#penlike.profile.build_profile)(measurements, \*[, register, ...])   | Aggregate the measurements of a register's texts into its profile.                       |
|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| [`compare`](#penlike.profile.compare)(measured, profile, \*[, norm, ...])        | Measure a draft against a register's profile and list what differs.                      |
| [`contrast`](#penlike.profile.contrast)(profile, reference, \*[, top])            | What sets `profile` apart from `reference`: the largest differences, in both directions. |
| [`function_word_vector`](#penlike.profile.function_word_vector)(measured, norm)               | A text's function-word rates as z-scores against `norm`, or `None` if too short.         |
| [`norm_is_current`](#penlike.profile.norm_is_current)(norm)                              | Whether stored figures were made by this version's features, word list and distance.     |
| [`render_profile`](#penlike.profile.render_profile)(profile, \*[, differences])         | A profile as plain lines an agent can follow when writing.                               |
| [`style_vector`](#penlike.profile.style_vector)(measured, norm)                       | A text's style vector: each feature as a clipped z-score against `norm`.                 |
| [`vector_distance`](#penlike.profile.vector_distance)(a, b)                              | Root-mean-square difference between two style vectors.                                   |

### penlike.profile.DISTANCE *= 'features-rms-z'*

The distance that style vectors are compared with, recorded next to the figures it
produced: thresholds set for one distance mean nothing for another.

### penlike.profile.LABELS *= {'allcaps_per_100w': 'all-capital words per 100 words', 'colon_per_100w': 'colons per 100 words', 'comma_per_100w': 'commas per 100 words', 'contraction_per_100w': 'contractions per 100 words', 'dash_per_100w': 'dashes per 100 words', 'ellipsis_per_100w': 'ellipses per 100 words', 'emoji_per_100w': 'emoji and emoticons per 100 words', 'exclamation_per_100w': 'exclamation marks per 100 words', 'first_plural_per_100w': 'we/us/our per 100 words', 'first_singular_per_100w': 'I/me/my per 100 words', 'function_word_share': 'share of function words', 'has_bold': 'bold text', 'has_code': 'code formatting', 'has_dash': 'dashes', 'has_emoji': 'emoji or emoticons', 'has_exclamation': 'exclamation marks', 'has_greeting': 'a greeting line', 'has_heading': 'headings', 'has_link': 'links', 'has_list': 'bulleted or numbered lists', 'has_semicolon': 'semicolons', 'has_signoff': 'a closing formula', 'hedge_per_100w': 'hedging words per 100 words', 'intensifier_per_100w': 'intensifiers per 100 words', 'lexical_diversity': 'variety of vocabulary', 'long_sentence_share': 'share of very long sentences (30 words or more)', 'long_word_share': 'share of long words (7 letters or more)', 'lowercase_start_share': 'share of sentences starting in lower case', 'paragraph_len_mean': 'words per paragraph', 'parenthesis_per_100w': 'parentheses per 100 words', 'question_per_100w': 'question marks per 100 words', 'second_person_per_100w': 'you/your per 100 words', 'semicolon_per_100w': 'semicolons per 100 words', 'sentence_len_mean': 'words per sentence', 'sentence_len_sd': 'spread of sentence lengths', 'short_sentence_share': 'share of very short sentences (5 words or fewer)', 'word_len_mean': 'letters per word', 'words': 'length in words'}*

What each feature is called when speaking to a writer.

### penlike.profile.NORM_FORMAT *= 1*

The version of the stored figures. It changes when their layout does.

### penlike.profile.VECTOR_FEATURES *= ('log_words', 'sentence_len_mean', 'sentence_len_sd', 'short_sentence_share', 'long_sentence_share', 'word_len_mean', 'long_word_share', 'paragraph_len_mean', 'lexical_diversity', 'function_word_share', 'comma_per_100w', 'semicolon_per_100w', 'colon_per_100w', 'dash_per_100w', 'parenthesis_per_100w', 'ellipsis_per_100w', 'exclamation_per_100w', 'question_per_100w', 'contraction_per_100w', 'first_singular_per_100w', 'first_plural_per_100w', 'second_person_per_100w', 'hedge_per_100w', 'intensifier_per_100w', 'allcaps_per_100w', 'emoji_per_100w', 'lowercase_start_share', 'has_greeting', 'has_signoff', 'has_list', 'has_code')*

every scalar but raw length (its
logarithm is used, since length otherwise dominates), plus four structural habits.

* **Type:**
  The features a text’s style vector is made of

### penlike.profile.build_profile(measurements, , register='', norm=None, others=(), min_phrase_docs=3, max_phrases=40)

Aggregate the measurements of a register’s texts into its profile.

`norm` (from `build_norm()`) adds the register’s centroid and the
function-word calibration: how far the register’s own texts sit from it (the
ceiling for a draft) and how far texts of `others` registers sit (the floor).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### penlike.profile.compare(measured, profile, , norm=None, threshold=2.0, min_words_for_rates=30)

Measure a draft against a register’s profile and list what differs.

A discrepancy is reported when the draft sits more than `threshold` of the
author’s own standard deviations from their average, when it shows a habit the
author almost never has, or lacks one they almost always have. Each comes with
the figures, so the next revision has something concrete to change.

The function-word distance, when both the draft and the profile are long enough,
is reported next to two references from the author’s own texts: how far they sit
from each other (`own`) and how far their other registers sit (`others`).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### penlike.profile.contrast(profile, reference, , top=8)

What sets `profile` apart from `reference`: the largest differences, in both directions.

Differences in averages are given in pooled standard deviations, differences in
habits as shares of texts, and function words as a ratio of rates.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]]

### penlike.profile.function_word_vector(measured, norm)

A text’s function-word rates as z-scores against `norm`, or `None` if too short.

This is the vector Cosine Delta compares. `norm` holds the mean and standard
deviation of each word’s rate over a population of texts.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`float`](https://docs.python.org/3/builtins/functions.html#float)] | [`None`](https://docs.python.org/3/builtins/constants.html#None)

### penlike.profile.norm_is_current(norm)

Whether stored figures were made by this version’s features, word list and distance.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### penlike.profile.render_profile(profile, , differences=None)

A profile as plain lines an agent can follow when writing.

Figures are given as the author’s typical value and range, because a target
range is something a draft can be held to and a bare average is not.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### penlike.profile.style_vector(measured, norm)

A text’s style vector: each feature as a clipped z-score against `norm`.

A feature the text is too short to have counts as average (zero).

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]

### penlike.profile.vector_distance(a, b)

Root-mean-square difference between two style vectors.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

```pycon
>>> vector_distance([0.0, 0.0], [3.0, 4.0])
3.5355
```
