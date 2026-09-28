# penlike.screening

Screening: keeping machine-written text out of a model of a person. Optional.

A model of how someone writes should be built from what they wrote. Since late
2022 a share of what people send has been drafted or polished by a language
model, so a corpus can be screened before it is used. There are four tiers, and
what each costs is stated before anything runs:

| tier   | what it does and what it costs                                                                                                                                                                                            |
|--------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| date   | Keeps only texts dated before a cutoff. Free and instant. The most<br/>reliable of the four, because no detector is involved.                                                                                             |
| cheap  | `ductus` deterministic detectors: stock phrases, mechanical traces,<br/>sentence shapes, rhythm. No model, no network; milliseconds a text.                                                                               |
| heavy  | `ductus` model-based detectors (Fast-DetectGPT, Binoculars) on this<br/>machine. Needs torch and transformers, downloads small open models on<br/>first use, and takes processor time that is measured on a sample first. |
| agent  | An agent reads the texts and judges them. Costs model tokens in<br/>proportion to the corpus. Not run from here; see the penlike-source skill.                                                                            |

No detector is reliable on a single short text, and every one of them accuses
some human writing. A flagged text is excluded from the model, never deleted, and
can be put back. The honest default for a personal model is the `date` tier.

```pycon
>>> sorted(TIERS)
['agent', 'cheap', 'date', 'heavy']
>>> docs = [{"id": "a", "date": "2021-05-01T00:00:00+00:00", "text": "x", "words": 1},
...         {"id": "b", "date": "2024-05-01T00:00:00+00:00", "text": "y", "words": 1}]
>>> screen(docs, tier="date")["flagged"]
['b']
```

### Functions

| [`screen`](#penlike.screening.screen)(docs, \*[, tier, cutoff, run, sample, ...])   | Screen documents at one tier.   |
|-------------------------------------------------------------------------------------------------------|---------------------------------|

### penlike.screening.screen(docs, , tier='date', cutoff='2022-11-30', run=False, sample=5, gauge=None)

Screen documents at one tier. Without `run` it only states the cost.

For the `cheap` and `heavy` tiers a plain call times the detector on
`sample` texts and extrapolates, so the length of the full run is known
before it starts. `gauge` replaces the detector (a function from text to a
mapping with a `label`); it is how tests run without ductus.

Returns `flagged` (document ids) and `findings` (per document) when the
screening ran, and the `plan` in every case.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]
