# penlike.features

Measure how a text is written: the cheap tier, standard library only.

[`measure()`](#penlike.features.measure) turns one text into numbers and forms that describe its style and
say little about its topic: sentence and word lengths, punctuation rates, function
words, contractions, greetings and sign-offs, formatting habits, recurring word
sequences. The choice of features follows the stylometry literature (see
`misc/docs/research_report.md`): frequent and function words are the most robust
signal, punctuation and affix habits carry most of what character n-grams know,
and openings and closings are where an individual is most recognisable.

The word lists are English. On other languages the language-neutral features
(lengths, punctuation, formatting) still hold and the word-list rates read low.

```pycon
>>> m = measure("Hi Ada,\n\nI think it's fine. Shall we ship it?\n\nCheers,\nGrace")
>>> m["greeting"], m["signoff"], m["scalars"]["question_per_100w"] > 0
('Hi <name>,', 'Cheers,', True)
```

### Module Attributes

| [`FUNCTION_WORDS`](#penlike.features.FUNCTION_WORDS)    | closed-class words whose rates depend on the writer and the register far more than on the topic.   |
|--------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| [`SCALAR_FEATURES`](#penlike.features.SCALAR_FEATURES)   | Rates and averages, one number per text.                                                           |
| [`PRESENCE_FEATURES`](#penlike.features.PRESENCE_FEATURES) | Habits that a text either shows or does not.                                                       |

### Functions

| [`measure`](#penlike.features.measure)(text)      | Measure one text.                                                |
|---------------------------------------------------------------------|------------------------------------------------------------------|
| [`sentences_of`](#penlike.features.sentences_of)(text) | Split prose into sentences, treating a line break as a boundary. |
| [`words_of`](#penlike.features.words_of)(text)     | The words of a text, lowercased.                                 |

### penlike.features.FUNCTION_WORDS *= ('a', 'about', 'above', 'after', 'again', 'against', 'all', 'almost', 'also', 'although', 'always', 'am', 'among', 'an', 'and', 'another', 'any', 'anyone', 'anything', 'are', 'around', 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'can', 'cannot', 'could', 'did', 'do', 'does', 'doing', 'done', 'down', 'during', 'each', 'either', 'enough', 'even', 'ever', 'every', 'everyone', 'everything', 'few', 'for', 'from', 'further', 'had', 'has', 'have', 'having', 'he', 'her', 'here', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'however', 'i', 'if', 'in', 'into', 'is', 'it', 'its', 'itself', 'just', 'least', 'less', 'many', 'may', 'me', 'might', 'more', 'most', 'much', 'must', 'my', 'myself', 'neither', 'never', 'no', 'nobody', 'none', 'nor', 'not', 'nothing', 'now', 'of', 'off', 'often', 'on', 'once', 'one', 'only', 'onto', 'or', 'other', 'others', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'perhaps', 'quite', 'rather', 'same', 'shall', 'she', 'should', 'since', 'so', 'some', 'someone', 'something', 'still', 'such', 'than', 'that', 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'these', 'they', 'this', 'those', 'though', 'through', 'thus', 'to', 'too', 'toward', 'under', 'until', 'up', 'upon', 'us', 'very', 'was', 'we', 'were', 'what', 'whatever', 'when', 'where', 'whether', 'which', 'while', 'who', 'whom', 'whose', 'why', 'will', 'with', 'within', 'without', 'would', 'yet', 'you', 'your', 'yours', 'yourself')*

closed-class words whose rates depend on the writer and the
register far more than on the topic.

* **Type:**
  English function words

### penlike.features.PRESENCE_FEATURES *= ('has_greeting', 'has_signoff', 'has_list', 'has_heading', 'has_bold', 'has_code', 'has_link', 'has_dash', 'has_semicolon', 'has_exclamation', 'has_emoji')*

Habits that a text either shows or does not. A profile keeps the share of texts that do.

### penlike.features.SCALAR_FEATURES *= ('words', 'sentence_len_mean', 'sentence_len_sd', 'short_sentence_share', 'long_sentence_share', 'word_len_mean', 'long_word_share', 'paragraph_len_mean', 'lexical_diversity', 'function_word_share', 'comma_per_100w', 'semicolon_per_100w', 'colon_per_100w', 'dash_per_100w', 'parenthesis_per_100w', 'ellipsis_per_100w', 'exclamation_per_100w', 'question_per_100w', 'contraction_per_100w', 'first_singular_per_100w', 'first_plural_per_100w', 'second_person_per_100w', 'hedge_per_100w', 'intensifier_per_100w', 'allcaps_per_100w', 'emoji_per_100w', 'lowercase_start_share')*

Rates and averages, one number per text. `None` when the text is too short for it.

### penlike.features.measure(text)

Measure one text. Returns scalars, presence flags, forms and counters.

The result is JSON-ready. `scalars` holds one number per name in
[`SCALAR_FEATURES`](#penlike.features.SCALAR_FEATURES) (or `None`), `presence` one boolean per name in
[`PRESENCE_FEATURES`](#penlike.features.PRESENCE_FEATURES).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

```pycon
>>> m = measure("We shipped it; nobody noticed. Odd, really odd!")
>>> m["n_words"], m["presence"]["has_semicolon"], m["scalars"]["exclamation_per_100w"]
(8, True, 12.5)
```

### penlike.features.sentences_of(text)

Split prose into sentences, treating a line break as a boundary.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

```pycon
>>> sentences_of("It works. Does it? Yes!")
['It works.', 'Does it?', 'Yes!']
```

### penlike.features.words_of(text)

The words of a text, lowercased.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

```pycon
>>> words_of("Don't Panic, it's fine.")
["don't", 'panic', "it's", 'fine']
```
