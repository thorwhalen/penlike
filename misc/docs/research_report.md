# Modelling how an author writes, and writing like them: research report

Compiled 2026-09-28 for the first version of penlike. It has three parts, each researched separately and each stating at its head how far its sources were verified: stylometry and the libraries that measure style (Part A), style transfer and emulation with language models (Part B), and register, genre and the discovery of registers (Part C). References are numbered once for the whole report and listed at the end. A source cited in more than one part appears once per part in the list.

This report is about published research and public software. It contains no text from anyone's correspondence, and no figure in it was computed from private data.

## Summary

What to measure. The most robust classical signal of who wrote a text is the profile of its most frequent words, function words above all, compared as a whole and normalised [1] [4]. Punctuation and affix habits carry most of what character n-grams know [10]. Vocabulary richness depends on length and is only usable in windowed form [11]. An individual is most recognisable in small co-selected forms: in the Enron mail, a greeting or a farewell, down to its punctuation, could be hundreds of times likelier for its author than for others [21].

How much text. Attribution studies put the floor for a stable frequency profile between about 1,500 and 5,000 words [3] [6] [7]. No study gives a floor for *describing* a style for generation, so penlike marks a register with under 2,000 words as provisional and says so wherever its figures are used.

One person has several styles. A general average describes no register [117]. In a study of 112 people individual style was weakly stable across genres [157], while within one register idiolects are consistent [156]. The consequence is the central design rule: model each register separately, never the person as a whole.

What a register is. The literature defines a register by the situation of use and then describes it by its language [110] [111]. The addressee is the main driver of style shift [114], and the effects are measured on exactly the metadata a mail client exposes: in Enron, informality was 56.0% in personal against 21.3% in business mail, and fell as the number of recipients rose [131]. So the register key is situational, and language is the check on it.

Finding new registers. For hundreds to low thousands of short texts nothing needs to be online in the algorithmic sense; what must be incremental is the *identity* of the registers [147]. A distance threshold that opens a new group (DP-means [141]), a person who names it, and identifiers that are never renumbered is the pipeline adopted. It is a synthesis: no source evaluates it on personal correspondence.

What works for imitation. Examples are necessary and not sufficient: few-shot beats zero-shot, and going from 2 to 10 examples changes little [67]. Imitation of everyday authors works on structured genres (news, email) and fails on informal ones (blogs, forums) [67]. Output drifts to a generic register with measurable features [74], which is what makes a contrastive description possible. Selecting examples by similarity of topic hurt style in one study [67]. The best-supported prompt design adds the model's own failed attempt and an explanation of how it differs from the real text [76]. Prompted imitation has a ceiling below fine-tuning for expert readers [73].

How to check. No single automatic metric of style match is reliable; ensembles do better, and scores should be calibrated per author against the author's own variation and against other writing [90] [71]. A revise loop driven by measured discrepancies is a reasoned design without direct published validation [98].

Why before 2023. Population studies find that a substantial share of text attributed to people has been processed by language models since late 2022: 6.5% to 16.9% of review text at four AI conferences [103], up to 17.5% of computer-science papers [104], at least 13.5% of 2024 biomedical abstracts [106]. These are corpus-level estimates; they support a cutoff by date and do not support trusting a detector on one short text. No study tests whether a personal model built on older text imitates better, and older text may be stale.

## What changes with what is being modelled

| | One person | A group, sector or house style | Any corpus |
|---|---|---|---|
| What the model captures | idiolect, within registers | shared conventions | text types |
| Data | small, rich in metadata | larger | any size, often no metadata |
| Register key | situation: channel, readers, reply | document type and purpose | inferred from the text |
| Possible only here | registers by reader, greetings and sign-offs, drift over time, how they write to one person | a fresh dimensional analysis, a population baseline, enough text to fine-tune | nothing specific |
| Not possible | new factor analysis (too little text) | reader-conditioned registers | reader-conditioned registers, drift without dates |
| Individual variation | the signal | noise to average out | unknown |
| Basis for imitation | self, or consent | consent of the group | a published style |

The collapse the request asked about ("maybe all these cases are: write like this corpus") holds for the measuring and the checking, which are the same code in all three cases. It does not hold for the register key, for which texts are kept, or for what may be claimed: a person's model knows who each text was for, and a corpus does not.

## What penlike v1 does with this, and what it leaves

| Finding | In v1 | Left for later |
|---|---|---|
| Function words, punctuation, lengths, forms are the robust cheap signals | measured with the standard library | syntactic features through spaCy; Biber features through `pybiber` or `biberplus` |
| Model per register | profiles are per register; there is no whole-person profile used for writing | |
| Register is situational first | texts are filed by channel, audience size and reply | tie strength and hierarchy as continuous variables |
| New registers appear over time | threshold clustering proposes, a person names, identifiers are permanent | style embeddings as the distance |
| Examples are needed, about five, chosen for spread | examples by reader first, then spread over readers and dates | a retrieval strategy tested against alternatives |
| Contrast against a reference shows what is characteristic | each register is contrasted with the author's other registers, or with another model | a shipped population baseline |
| Notes should be contrastive and sourced | notes carry their sources; unsourced notes are hypotheses | automated trial-error-explain |
| Verification should be several calibrated scores | per-feature discrepancies, and a function-word distance calibrated on the author's own texts | authorship and style embeddings (LUAR, StyleDistance) as further scores |
| Machine-written text contaminates recent corpora | a date cutoff, warnings on every gather, optional screening in cost tiers | |
| Imitation is dual-use | a recorded basis per model, responsible-use text in every brief and skill | |

The research on detecting machine-written text is not repeated here. It was done for the `ductus` package, which penlike uses for optional screening, and is kept in that project's `misc/docs/research/detection-methods.md` [159].

## Part A: Stylometry, style features and libraries

*Stylometry and style features for an author-style model: literature and Python tooling*

Research date: 2026-09-28. Scope: the measurement side (what to measure about how someone writes, and what to wrap), not the generation side.

### How to read this report

Every numbered source was opened during this research unless the reference entry says otherwise. Where only a bibliographic page or an abstract was reachable (paywall, bot wall), the reference entry says so and the text leans on it only for what that page showed. Library facts (version, date, licence, size, dependencies) were read from the PyPI JSON API and the GitHub API on 2026-09-28. "Size" means the download size of the package artefact on PyPI, not the installed footprint with dependencies and models.

### Executive summary

- The most dependable classical signal is the relative frequency of very frequent words (mostly function words), compared as a profile rather than word by word. Character n-grams are the strongest single low-level feature family in the comparisons the surveys report, but they also carry topic [1], [2], [4].
- Reliable attribution from frequency profiles needs thousands of words: about 5,000 words per sample in most corpora Eder tested, 2,500 for Latin prose [6]; a later abstract by the same author lowers this to under 2,000 words for texts with a clear authorial signal, with a warning that some texts need much more [7]. A style card built from a few hundred words must therefore be treated as a low-confidence sketch.
- Content words leak topic. The remedies with evidence behind them are: restrict to frequent words, mask everything else (Stamatatos's text distortion), or use POS-based features [15], [16].
- The forensic-linguistics literature locates individuality in habitual co-selections: recurring word sequences, greetings, sign-offs and their punctuation. Low-frequency variants are often the most distinctive [21], [23].
- Neural style embeddings (LUAR, Wegmann's Style-Embedding, StyleDistance, mStyleDistance) are all RoBERTa-base-sized models on Hugging Face under permissive licences where a licence is stated. They are useful as a similarity check on generated text, not as a description an LLM can read [26]–[35].
- For a Python package: `spaCy` plus a thin in-house layer covers most of the inventory. `textdescriptives`, `lexicalrichness`, `textstat`, `biberplus` and `pybiber` are alive and permissively licensed. `LFTK` (CC BY-NC) and StyloMetrix (GPL-3.0) have licence constraints. `writeprints-static`, `cophi`, `pystyl` and `pydelta` are stale or not on PyPI.

### 1. Classical stylometry

#### 1.1 Feature families

Stamatatos's survey groups stylometric features into lexical, character, syntactic, semantic and application-specific types, and records that by the late 1990s close to 1,000 different measures had been proposed (citing Rudman) [1]. The families that matter for a style model are below.

**Function words and most-frequent-word (MFW) profiles.** The survey's argument for function words is that they "are used in a largely unconscious manner by the authors, and they are topic-independent" [1]. Published English lists range widely: the survey lists sets of 150, 303, 365, 480 and 675 function words from different studies, and notes that selection criteria are usually arbitrary [1]. Koppel, Schler and Argamon report that typical modern English studies use lists of a few hundred words and that results across different lists have been similar, so the precise choice of list is not critical [2]. The alternative to a curated list is simply the most frequent words of the corpus; earlier studies regarded sets of at most 100 frequent words as adequate [1]. Kestemont's position paper reviews why this word category is attractive and relates it to character n-grams, proposing the term "functor" instead of "function word" [9].

**Burrows's Delta and its variants.** Delta compares z-scored frequencies of the most frequent words between a text and candidate authors. According to the abstract of the original paper, the method gives comparatively accurate results for texts exceeding about 1,500 words, can still narrow the field of candidates for texts as short as 100 words, and works least well for texts in a genre uncharacteristic of their author [3]. Evert and colleagues separated the method into feature selection, feature scaling and distance measure, and tested Manhattan, Euclidean and cosine distances under several scalings. Their finding is that normalising the feature vector to length 1, which is implicit in the cosine measure, "is the decisive factor for the improvement of Delta", and that the authorial information lies "in the profile of deviation across the most frequent words rather than in the extent of the deviation or in the deviation of specific words only" [4]. For a style card this means the useful object is the shape of the whole frequency profile relative to a reference norm, not a list of three favourite words. Rybicki and Eder tested many word-vector configurations across languages and genres and found that Delta works best for English and German prose and less well for highly inflected languages such as Polish and Latin [5].

**Character n-grams.** The survey reports that in Grieve's comparison on a common corpus, character n-grams were the most effective measures, outperformed only by a combination of frequent words and punctuation marks [1]. Grieve's own abstract says he compared thirty-nine types of textual measurement on the same data and proposes combining many measurements [8]. The survey also states the cost: a large n captures thematic information as well as lexical and contextual information, and for short English texts the best results were obtained with sequences of up to 4-grams [1]. Koppel and colleagues observe that character n-grams performed almost identically to content words on two of their corpora, which suggests that they act partly as proxies for content words [2]. Sapkota and colleagues split character n-grams into affix, word and punctuation categories and conclude that n-grams capturing affixes and punctuation "account for almost all of the power of character n-grams as features" [10]. This is a practical result: a punctuation-and-affix n-gram profile keeps the style signal and drops most of the topic signal.

**Syntactic features (POS n-grams, rewrite rules).** The survey regards syntactic information as potentially more reliable than lexical information because authors use syntactic patterns unconsciously, but notes that extraction depends on parser accuracy and introduces noise, and concludes that syntactic and semantic features are best used as a complement to lexical and character features [1].

**Sentence length, word length, punctuation.** These are among the oldest measures [1]. The survey warns that sentence-boundary detection is itself noisy in domains with heavy abbreviation, naming e-mail explicitly [1].

**Vocabulary richness.** Type-token ratio and hapax counts depend heavily on text length. The survey says functions proposed to be length-stable, such as Yule's K and Honoré's R, gave "questionable results" (citing Tweedie and Baayen) and that such measures "are considered unreliable to be used alone" [1], [11]. If a style card includes a richness figure it should be a length-controlled measure (for example a moving-average TTR or MTLD, both implemented in `lexicalrichness` [47]) computed on a fixed window, and it should be compared only with figures computed the same way.

**Idiosyncrasies.** Koppel and Schler's writing-error measures (spelling errors, formatting errors such as all-caps words) are described in the survey, which adds that human experts mainly use observations of this kind [1].

**Writeprints.** Abbasi and Chen combine lexical, syntactic, structural, content-specific and idiosyncratic features, with structural features described as especially useful for online text, and report accuracy as high as 94% when differentiating between 100 authors [12]. Writeprints-Static is the fixed feature subset used by Brennan, Afroz and Greenstadt in their adversarial stylometry work [13], which is the set the `writeprints-static` package reproduces [57].

#### 1.2 What is most robust

Reading the sources together: (a) frequent-word profiles, normalised and compared as a whole [4]; (b) character n-grams restricted to affix and punctuation types [10]; (c) combinations of many feature types rather than any single one [8], [12]. Koppel and colleagues' "in the wild" setting (many thousands of candidate authors, the true author possibly absent) is the reminder that results on small closed candidate sets do not transfer to open settings [14]; I could open only the bibliographic record of that paper, so I report its framing and no figures from it.

#### 1.3 How much text is needed

- Eder 2015: the minimal sample length for stable attribution "varied from 2,500 words (Latin prose) to 5,000 or so words (in most cases, including English, German, Polish, and Hungarian novels)" [6]. A search snippet of the same paper says that randomly excerpted bags of words did better than contiguous passages, but I did not see that sentence in the abstract I opened, so treat it as unverified.
- Eder 2017: the minimum can be lowered "from ca. 5,000 running words ... to less than 2,000 words", but only for texts with a clear authorial signal; for others the risk of severe misclassification appears, and the minimum differs per text [7].
- Burrows 2002: about 1,500 words for attribution, 100 words to narrow candidates [3].
- Stamatatos 2009: studies report promising results on texts under 1,000 words, but "it is not yet possible to define such a text-length threshold" [1].
- Wright 2017, e-mail: with samples of 2% of an author's e-mails no n-gram length achieved more than 40% accuracy, while four-grams reached 94% with 20% samples; across all sample sizes the overall success rate was 64% [23].
- Zhu and Jurgens 2021: their neural model finds idiolectal variation evident and consistent in texts as short as 100 tokens [25].

These numbers answer the attribution question (which of N authors), which is not the same as the description question a style card asks. The safe reading is that distributional features need a few thousand words per author per register to stabilise, while categorical habits (does this person open e-mails with "Hi Name," or with nothing) can be observed from a few dozen messages. I found no source that gives a minimum sample size for descriptive style profiling as such.

### 2. Topic versus style

**Why content words leak topic.** Word n-grams and long character n-grams capture content-specific information [1]. Character n-grams behave like content words on some corpora [2]. Even function words are not clean: the survey notes that stylometric features applied to topic identification have shown they can indicate content too [1].

**Text distortion (Stamatatos 2018).** Every word outside the k most frequent words of the language is masked, leaving the frequent words and the punctuation in place. Variants: DV-MA replaces each character of a masked word with an asterisk (keeping word length), DV-SA replaces the whole word with one asterisk, DV-EX keeps the first and last characters; digits are replaced by `#`. The frequent-word list came from the British National Corpus [15]. In the cross-topic experiment, a character-3-gram SVM went from 39.55% average accuracy to 64.81% with DV-MA, and a compression model (PPM5) from 47.35% to 53.31%; the best previously published result on that corpus was 45.05% [15]. Low values of k suited cross-topic attribution, whereas cross-genre attribution improved only with k above 2,500, so the two problems need different settings [15]. The method needs nothing beyond a frequency list and a regex, which makes it a cheap default for a style package.

**POS-based features.** In the topic-confusion task of Altakrori and colleagues, where author-topic pairings are switched between training and test, stylometric features with POS tags were the least susceptible to topic variation, and word n-grams outperformed BERT and RoBERTa [16].

**Shared-task evidence.** PAN 2021 evaluated open-set verification on fan fiction where the two texts of a pair come from different fandoms and test authors and fandoms are unseen; it received 13 submissions from 10 teams, and the baselines were character-n-gram TF-IDF, compression, and a short-text variant of unmasking [17]. PAN 2022 moved to cross-discourse-type verification on a corpus drawn from the Aston 100 Idiolects Corpus, with 112 individuals writing essays, e-mails, text messages and business memos. The overview states that it is "very challenging to distinguish authorial characteristics that remain intact across discourse types" and that, surprisingly, a naive baseline achieved the best overall score [18]. For this project that is the strongest published evidence that style must be modelled per register: a person's text messages predict their essays poorly.

**Neural confirmation.** Wegmann and colleagues show that representations trained on authorship verification can encode content rather than style, and that controlling for conversation during training gives representations that are better at representing style independently of content than controlling for domain or not controlling at all [29]. Zhu and Jurgens masked either content or function words and found either alone is a reliable cue; with one of their two encoders, content words carried slightly more idiolectal signal despite topic variation [25]. So content words are not purely noise, but they are not safe to use without a topic control.

### 3. Idiolect: the forensic-linguistics view

Coulthard states the theoretical position that every native speaker has their own idiolect, which shows in "distinctive and idiosyncratic choices", and that speakers "make typical and individuating co-selections of preferred words". He also rejects the fingerprint metaphor: any linguistic sample gives only partial information about an idiolect, and many forensic texts are under 200 words [19]. His evidence is that short sequences of ordinary words quickly become rare; one six-word sequence he checked occurred 7,770 times on the web and adding a seventh word made it far rarer [19].

Grant's SMS case study frames the analysis in terms of consistency (does the author do this repeatedly) and distinctiveness (do others not do it) [20]. I could open only the bibliographic record, so I take from it the two criteria named in its title and nothing else. They are the right two columns for any style-card entry.

Wright's Enron work gives the numbers.

- Greetings and farewells [21]: in a four-author corpus he found 19 greeting forms and 12 farewell forms that were individuating or used far more consistently by one author. The distinguishing detail was often punctuation and capitalisation: a name followed by a colon, a name followed by a comma with the next word not capitalised, a name with no punctuation. Tested against a 126-author reference corpus of 40,236 e-mails and 1,669,197 words, four variants lost their distinctiveness, while some forms were 60, 230 and 500 times more likely to appear in the author's e-mail than in another writer's. Two forms with likelihood ratios of 10 and 9 combined to 90 when they co-occurred. He concludes that less frequent variants were often the most distinctive at population level.
- Word n-grams [23]: on the 176-author, 2.5-million-word Enron corpus, with twelve test authors, four-grams were the best single length (70.50% of 600 samples), followed closely by five-grams (70%). Per-author accuracy ranged from 87.20% to 8.40%, so some people are far more formulaic than others. One author's distinctive five-grams included "a clean and redlined version" and "please review and let's discuss".
- Johnson and Wright [22]: one Enron employee's habitual politely encoded directives allowed n-gram "textbites" to attribute anonymised samples to him with success rates as high as 100%.

Nini's Theory of Linguistic Individuality grounds this in cognitive linguistics and the likelihood-ratio framework [24]. Wright explains recurrence through entrenchment: sequences a person uses repeatedly become stored units [23].

Implications for a style card: record openings, closings and their exact punctuation; record recurrent 3- to 5-word sequences that are frequent for the author and rare in a reference population; record how directives and requests are phrased; keep per-feature consistency and distinctiveness scores; and expect large differences between authors in how much of this signal exists at all.

### 4. Neural style representations

| Model | Paper | What it is | Hugging Face id | Licence | Size |
|---|---|---|---|---|---|
| LUAR | Rivera-Soto et al., EMNLP 2021 [26] | Author embedding computed from an "episode" of several short texts by one author; trained on Reddit (MUD) or on Reddit, Amazon and fan fiction | `rrivera1849/LUAR-MUD`, `rrivera1849/LUAR-CRUD` [27] | Apache-2.0 [27] | 82.5M parameters; 512-dimensional output [27] |
| Style-Embedding | Wegmann, Schraagen, Nguyen, RepL4NLP 2022 [29] | RoBERTa-base fine-tuned with a triplet loss on an authorship task with conversation-level content control | `AnnaWegmann/Style-Embedding` [30] | No licence stated on the model card; the code repository `nlpsoc/Style-Embeddings` is MIT on GitHub [30] | 499 MB weights file; 768 dimensions [30] |
| StyleDistance | Patel et al., NAACL 2025 [32] | RoBERTa-base trained contrastively on synthetic near-paraphrases that differ in one of 40 style features | `StyleDistance/styledistance` [33] | MIT [33] | 124.6M parameters [33] |
| mStyleDistance | Qiu et al., 2025 [34] | Multilingual version, XLM-RoBERTa-base, nine training languages | `StyleDistance/mstyledistance` [35] | MIT [35] | 278.0M parameters [35] |
| LISA | Patel et al., Findings of EMNLP 2023 [31] | 768 interpretable dimensions, each the probability of a named style attribute, distilled from LLM annotations (StyleGenome) | Not found by me on the Hub | Unverified | Unverified |
| Neurobiber | Alkiek et al., 2025 [36] | RoBERTa tagger predicting presence of 96 Biber-style features | `Blablablab/neurobiber` [37] | No licence tag on the model repository; `biberplus` code is MIT [37], [52] | 124.7M parameters [37] |

Notes on each.

- **LUAR.** The paper is the first large-scale study of cross-domain transfer for authorship verification, over Amazon reviews, fan fiction and Reddit comments; transfer worked between some domains and not others [26]. Training inputs are excerpts of 32 sub-word tokens from up to 16 documents per author [26]. The Hub model needs `trust_remote_code=True` and a 3-D input (batch, episode length, sequence length) [27]. A community conversion to the sentence-transformers format exists (`gabrielloiseau/LUAR-MUD-sentence-transformers`, Apache-2.0, 82.1M parameters) [27].
- **STEL and STEL-or-Content.** STEL is a modular, content-controlled evaluation framework for style measures, covering formal/informal and simple/complex plus contraction and number-substitution characteristics; in it, BERT-based methods outperformed simple character 3-gram, punctuation-frequency and LIWC-based measures [28]. The 2022 paper adds a variant that tests whether a representation prefers style over content [29].
- **StyleDistance** is motivated by content leakage in contrastive training on real authorship data; the synthetic pairs hold content nearly fixed while varying one style feature [32]. The model card says the training data also included real Reddit authorship data [33].
- **LISA** is the only one of these whose output is readable by a person or an LLM. The authors say they release the dataset and models [31], but I did not locate a Hub repository, so availability and licence are unverified.
- **Neurobiber** reports macro-F1 0.97 and micro-F1 0.98 against the rule-based tagger, about 117,000 tokens per second, and up to 56 times the speed of the fastest open-source alternative [36]. It predicts presence of a feature per chunk, not a count.
- **Benchmark.** STEB (2026) covers 96 datasets in 7 languages and finds that semantic embeddings consistently fail at stylistic tasks and that no style embedding is best across all tasks [38]. There is therefore no single model to standardise on; the embedding should be a replaceable component.

**Relevance to generation.** Wang and colleagues evaluated few-shot style imitation by LLMs, with over 40,000 generations per model and more than 400 real authors across news, e-mail, forums and blogs. LLMs approximate style in structured formats such as news and e-mail, struggle with informal blog and forum writing, tend towards an average generic tone, and gain little from more demonstrations [39]. This supports giving the LLM an explicit, measured style description rather than examples alone, and using an embedding or classifier as an independent check on the output. That inference is mine, not a claim of the paper.

### 5. Python libraries

Data as of 2026-09-28.

| Library | PyPI name | Licence | Latest release | Status | Computes | Weight |
|---|---|---|---|---|---|---|
| faststylometry [40] | `faststylometry` | MIT | 1.0.15, 2025-07-21 | Alive, slow cadence | Burrows's Delta, plus calibrated same-author probability | 19 KB wheel; needs numpy, pandas, scikit-learn. Declares Python `>=3.12,<=3.13.3`, which is restrictive |
| stylo (R) [41] | not a Python package | GPL-3 | GitHub pushed 2026-06-19 | Alive | Delta variants, classifiers, rolling stylometry, verification | Needs R. The PyPI name `stylo` is an unrelated image-drawing library [41] |
| pydelta [42] | not on PyPI (the PyPI name `pydelta` is an unrelated taxonomy library) | Licence file present, terms not checked | GitHub pushed 2021-10-01 | Stale | Delta measures; install from Git, branch `next` | numpy, pandas, scipy, scikit-learn |
| PyStyl [43] | not on PyPI | Not a standard licence per GitHub | GitHub pushed 2021-03-30 | Stale; README calls it early-stage | Stylo-like analyses | Source install |
| textstat [44] | `textstat` | MIT | 0.7.13, 2026-02-18 | Alive | Readability formulas, syllable, word and sentence counts | 177 KB wheel; pyphen, nltk |
| spaCy [45] | `spacy` | MIT | 3.8.16, 2026-08-24 | Alive | Tokens, sentences, POS, morphology, dependencies, entities | About 7 MB wheel plus a language model downloaded separately |
| TextDescriptives [46] | `textdescriptives` | Apache-2.0 | 2.8.4, 2024-12-16 (GitHub pushed 2026-05-05) | Alive, but no PyPI release for 21 months | Descriptive statistics, readability, dependency distance, POS proportions, coherence, quality, information theory | 254 KB wheel; spaCy, pandas; pins `numpy<2.0.0` |
| LexicalRichness [47] | `lexicalrichness` | MIT | 0.5.1, 2023-08-27 (GitHub pushed 2026-05-02) | Maintained, feature-complete | TTR, RTTR, CTTR, Herdan, Summer, Dugast, Maas, Yule's K and I, MSTTR, MATTR, MTLD, HD-D, vocd-D | 98 KB sdist; TextBlob |
| LFTK [48] | `lftk` | CC BY-NC 4.0 | 1.0.9, 2023-04-27 | Dormant | Over 220 handcrafted features on spaCy | 2.3 MB sdist. Non-commercial licence: do not make it a dependency of a permissively licensed package |
| StyloMetrix [49] | `stylo-metrix` (not `stylometrix`) | GPL-3.0 | 0.1.9.1, 2024-03-19 (GitHub pushed 2026-06-09) | Repository alive, PyPI release old | 196 English metrics in grammatical, lexical, syntactic and statistical groups; also Polish, German, Ukrainian, Russian | 214 KB wheel; pins `spacy==3.7.2` and requires `morfeusz2`. Copyleft |
| pybiber [50] | `pybiber` | MIT | 0.3.1, 2026-03-06 | Alive | 67 Biber (1988) features, Multi-Dimensional Analysis, PCA | 1.8 MB wheel; spaCy, polars |
| biberplus [52] | `biberplus` | MIT | 0.4.0, 2025-02-21 (GitHub pushed 2026-07-07) | Alive | 96 Biber-style features, function-word tagger, PCA and factor analysis; optional `[neural]` extra for Neurobiber | 112 KB wheel; spaCy, pandas, factor_analyzer, matplotlib, seaborn |
| neurobiber [36], [37] | no PyPI package of that name; shipped as `biberplus[neural]` | see above | Hub model updated 2026-06-30 | Alive | Presence of 96 features | Needs torch and the 124.7M-parameter model |
| cophi [53] | `cophi` | Apache-2.0 | 1.3.2, 2019-04-25 | Dead | Corpus preprocessing, not stylometry | 17 KB wheel |
| PAN baselines [54] | not packaged | MIT | GitHub pushed 2026-07-02 | Alive as a code archive | Character-n-gram TF-IDF and compression verification baselines, evaluators [17] | Scripts, not a library |
| sentence-transformers [55] | `sentence-transformers` | Apache-2.0 | 6.1.0, 2026-09-18 | Alive | Loads Style-Embedding, StyleDistance, mStyleDistance and the LUAR conversion | 741 KB wheel, but requires torch and transformers |
| writeprints-static [57] | `writeprints-static` | ISC | 0.0.2, 2022-05-06 | Dead; the homepage repository returns 404 | Writeprints-Static feature set | 10 KB wheel; pins `spacy==3.0.8`, `numpy<2` |
| pystylometry [56] | `pystylometry` | MIT | 1.4.3, 2026-02-07 | New (first release 2026-01-22), single maintainer | Claims 50+ metrics in 11 modules: lexical diversity, function words, readability, syntactic | Core needs only `rich`; extras pull spaCy. Not evaluated by me beyond its PyPI description |

Other findings: the PyPI name `stylometry` is a single 2015 release with no stated licence, and `stylometry-utils` (2023) depends on TensorFlow; neither is a candidate. `biberpy` is a GPL-3.0 multilingual Biber feature script, not a PyPI package [51].

**Recommendation.** Make the core dependency-free (stdlib `re`, `collections`, `statistics`) for the cheap tier, put `spaCy` behind an optional extra for the medium tier, and put `sentence-transformers` behind a second optional extra for the heavy tier. Implement Delta and Cosine Delta in-house: they are a z-score and a distance over a frequency table [4], and `faststylometry`'s Python pin would constrain users [40]. Wrap `lexicalrichness` or reimplement MATTR and MTLD; wrap `biberplus` or `pybiber` for register features; treat `textdescriptives` as an optional provider because of its numpy pin. Do not depend on `lftk`, `stylo-metrix` or `writeprints-static`.

### 6. Recommended feature inventory for a style card

Each entry should be stored per author and per register (e-mail, chat, issue comment, long-form), since cross-register transfer is weak [18]. Each should carry the sample size it was computed from, a consistency score (how often the author does it) and, where a reference population exists, a distinctiveness score (how much more often than others) [20], [21]. Cost tiers: **C** cheap (stdlib and regex), **M** medium (spaCy or similar), **H** heavy (neural model).

#### Lexical

| Dimension | Tier | Basis |
|---|---|---|
| Relative frequencies of the top 100 to 500 frequent words, z-scored against a reference corpus | C | [1], [3], [4] |
| Function-word profile from a fixed list | C | [1], [2] |
| Word-length distribution (mean, spread, share of long words) | C | [1] |
| Length-controlled lexical diversity (MATTR, MTLD) on a fixed window | C | [1], [11], [47] |
| Contractions rate, number style (digits or words) | C | [28] |
| Recurrent 3- to 5-word sequences, frequent for the author and rare in the reference | C | [19], [23] |
| Preferred intensifiers and their collocates | C to M | [23] |
| Character n-grams of affix and punctuation type | C | [10] |
| Idiosyncratic spellings, abbreviations, consistent errors | C | [1], [12] |

#### Syntactic

| Dimension | Tier | Basis |
|---|---|---|
| Sentence-length distribution (median, spread, share of very short and very long) | C, more accurate with M | [1] |
| POS unigram and n-gram proportions | M | [1], [16] |
| Dependency distance, subordination and coordination rates | M | [46] |
| Voice, tense and person distribution | M | [49] |
| Biber-style register features | M, or H through Neurobiber | [36], [50], [52] |
| Masked-text (text distortion) n-gram profile | C | [15] |

#### Punctuation and orthography

| Dimension | Tier | Basis |
|---|---|---|
| Rate per 1,000 tokens of each punctuation mark, including dashes, semicolons, parentheses, ellipses, exclamation and question marks | C | [1], [10] |
| Quote style, spacing habits, serial comma | C | [10] |
| Capitalisation habits (all-caps words, lower-case sentence starts) | C | [1], [21] |
| Emoji and emoticon use | C | [10] |

#### Discourse and structure

| Dimension | Tier | Basis |
|---|---|---|
| Message and paragraph length distributions, sentences per paragraph | C | [12] |
| Opening move (context first, request first, answer first) | M to H; needs a classifier or an LLM annotator | my proposal, not from a cited source |
| Connective and discourse-marker inventory | C | my proposal, not from a cited source |
| Coherence between adjacent sentences | M to H | [46] |

#### Pragmatic

| Dimension | Tier | Basis |
|---|---|---|
| Greeting form, including exact punctuation and capitalisation, and the no-greeting rate | C | [21] |
| Sign-off form, name form (full, first, initials, none) | C | [21] |
| Greeting and sign-off co-selection | C | [21] |
| Phrasing of directives and requests (imperative, "please" plus verb, modal question) | C to M | [22], [23] |
| Hedging and emphatic markers, by word list (both are Biber-style features) | C | [36] |
| Formality | H (embedding or classifier) or M (Biber dimensions) | [28], [52] |

#### Formatting

| Dimension | Tier | Basis |
|---|---|---|
| Use of lists, headings, bold, inline code, links; line-break habits | C | [12] |
| Quoting and reply style in threads | C | [12] |

#### Whole-text representations

| Dimension | Tier | Basis |
|---|---|---|
| Style embedding centroid and spread per author and register, used to score generated drafts | H | [27], [30], [33], [38] |
| Interpretable attribute vector in the manner of LISA | H | [31] |

#### Design consequences

1. Store distributions and rates, not single values, and store n with every figure. Below roughly 2,000 words per author-register cell, mark distributional features as provisional [6], [7].
2. Keep a reference corpus per register. Both Delta [4] and likelihood-ratio distinctiveness [21] are defined relative to a norm; without one, a card records what is frequent but not what is characteristic.
3. Do not discard rare features. Low-frequency variants were often the most distinctive in Wright's data [21].
4. Separate what the card tells the LLM (interpretable features, exemplar phrases) from what verifies the output (embedding similarity, feature re-measurement on the draft). The second use tolerates opaque models; the first does not.

### Limits of this research

- Not opened in full: Burrows 2002, Eder 2015, Evert 2017, Rybicki and Eder 2011 and Grieve 2007 (abstract pages only); Koppel 2011 and Grant 2013 (bibliographic records only); Tweedie and Baayen 1998 and Brennan 2012 (publisher pages refused automated access; known to me only through search-result summaries and through citing papers).
- Abstract pages were read through a summarising fetch tool. Quotations from those pages are short and were returned by that tool as verbatim, but I could not compare them with the page source. Quotations from papers I downloaded as PDF ([1], [7], [10], [15], [18], [19], [21], [23], [36], [38], [39]) were read directly.
- I did not install or run any library. Status is inferred from release and push dates.
- LIWC, a common style-feature tool, is proprietary and was not examined.
- The literature is overwhelmingly about attribution and verification. Its use for describing style for generation is my extrapolation throughout section 6.

## Part B: Style transfer and emulation with language models

*Style transfer and author emulation with hosted LLMs: what the literature supports*

Research report, compiled 2026-09-28. Scope: how to model an author's (or a corpus's) writing so that a frontier hosted LLM, without fine-tuning, can write or rewrite text that reads as that author's.

### How to read this report

Every source in the REFERENCES section was opened during this research. Three levels of verification apply, and they matter for how far to trust a number. (a) Figures from Wang et al. [67] were read directly from the tables in the PDF. (b) The evaluation triad and the "tightly coupled" remark in Jin et al. [58] were read from the extracted text of the paper, and the Anthropic usage-policy clauses [102] were read from the page text. (c) All other figures come from the arXiv or publisher abstract page, or from the full text as read through an automated page reader; these are reported as retrieved, and any figure that will be quoted in public documentation should be spot-checked against the paper first. Where a claim could not be verified it is said so in place.

### 1. Text style transfer: background

Text style transfer (TST) is the task of changing the stylistic properties of a text while keeping its style-independent content [59]. The two standard surveys are Jin et al., which covers more than 100 papers from the first neural work in 2017 onward [58], and Hu et al., which adds a reproducibility study benchmarking 19 TST algorithms on two public datasets [59].

Two definitions of style run through the field. Jin et al. separate a linguistic definition (the manner in which something is said) from a data-driven definition, in which "style" is whatever distinguishes two corpora; they state that most deep-learning work adopts the data-driven definition [58]. This matters for an author model, because whatever distinguishes an author's corpus from a reference corpus includes their topics, not only their manner.

Attribute transfer and authorial transfer are different problems. Most TST work transfers a coarse attribute such as sentiment, formality or politeness [58]. Krishna et al. argue that much of that work is not style transfer at all, because changing sentiment changes meaning; they reformulate style transfer as controlled paraphrase generation (the STRAP method) and release a dataset of 15 million sentences in 11 styles [60]. Authorship transfer is harder: Jin et al. list it among the open challenges precisely because it "has tightly coupled style and content" [58].

The evaluation triad is standard. Jin et al. name the three criteria as transferred style strength, semantic preservation and fluency, measured automatically by, respectively, a separately trained style classifier, BLEU/ROUGE-type overlap, and perplexity under a separately trained language model [58]. The automatic metrics are known to be weak: Krishna et al. surveyed 23 style transfer papers and found the usual automatic metrics can be gamed [60].

Large language models changed the method but not the triad. Reif et al. showed that an LLM can perform arbitrary style rewrites from a natural-language instruction alone, which they call augmented zero-shot learning [61]. Suzgun et al. generate several candidates by zero- or few-shot prompting and then rerank them by textual similarity, target style strength and fluency, the same triad used as a selection criterion rather than only as a score [62]. That generate-then-rerank pattern is directly reusable with a hosted LLM.

### 2. Authorship style transfer and personal style imitation

#### 2.1 Pre-LLM and small-model methods

Patel et al. define low-resource authorship style transfer: imitate a non-famous author from about 16 Reddit posts (about 500 words), where earlier work had needed more than 100,000 words per author [63]. Their method, STYLL, is a three-step prompt chain: paraphrase the texts into a neutral style, ask the model for adjectives that describe the target author's style, then rewrite the neutralised source using few-shot pairs of (neutral paraphrase, target original) together with the style descriptors [63]. They also introduce the evaluation now standard in this sub-field: Away (distance from the source author's style), Towards (movement toward the target author's style), Sim (meaning preservation) and Joint (a geometric-mean combination), with the style measurements computed from authorship embeddings [63]. Their own conclusion is that current approaches "do not yet achieve mastery" of the task [63].

ParaGuide uses a paraphrase-conditioned diffusion model guided at inference time by off-the-shelf classifiers and style embedders, and reports results on formality, sentiment and authorship transfer [64]. TinyStyler conditions a small model (800M parameters) on pre-trained authorship embeddings, training it to reconstruct texts from their paraphrases; its abstract reports that it outperforms GPT-4 on authorship style transfer under automatic evaluation [65]. Its authors note a limitation that applies equally to any embedding-based judge: the system is bottlenecked by what the authorship embedding can represent [65]. Liu et al. (ASTRAPOP) combine transfer learning with policy optimisation for the low-resource case [66]. All of these need model weights and training; they are relevant here mainly as sources of evaluation practice and as optional local back ends.

#### 2.2 What frontier LLMs do when asked to imitate a person

The most useful single study is Wang et al. (Findings of EMNLP 2025) [67]. They test GPT-4o, GPT-4o-mini, Gemini-2.0-Flash, Gemma-3-27B, DeepSeek-V3 and Llama-4-Maverick on four corpora covering 400 authors: Enron emails, blogs, CCAT50 news articles and Reddit posts. The model receives five randomly chosen writing samples by the author plus a content summary of a held-out text, and must write that text. No style description is given; the study is explicitly about implicit imitation [67].

Their findings, with the numbers read from the paper's tables [67]:

- Examples help. Five-shot prompting beats zero-shot on every dataset and metric, which the authors read as confirmation that without examples LLMs default to a generic style.
- Genre decides almost everything. Authorship-verification accuracy for five-shot generations was 94.68 to 97.46% on news and 95.65 to 96.64% on email across the six models, but 49.97 to 65.88% on Reddit and only 16.72 to 21.25% on blogs. Structured, formal genres are imitated well; informal, stylistically diverse ones are not.
- More examples do not fix it. Varying the number of examples over 2, 4, 6, 8 and 10 changed the metrics very little.
- Output remains detectable as machine text. The share of generations classified as human by GPTZero was always below 55% and often below 20%. The authors caution that the detector may itself be biased toward detecting GPT-family output.
- Choosing examples by topic similarity hurt style. Selecting the five examples from the same topic cluster as the target reduced attribution performance, for example top-5 attribution accuracy on Enron fell from 69.33% to 36.00%. The authors' reading is that a narrow topical cluster reduces the stylistic diversity the model sees.
- Seeding with the author's own words helped human-likeness. Supplying the first 50 words or 20% of the target text raised the share classified as human, for example from 9.00% to 21.70% on blogs, with mixed effects on attribution.

Other studies agree on direction. Bhandarkar et al. tested 12 off-the-shelf LLMs and concluded they fall short of effective author style emulation [68]. Jemama and Kumar report that prompting strategy matters more than model size, that few-shot prompting gives up to 23.5 times higher style-matching accuracy than zero-shot, and that text-completion prompting reaches 99.9% agreement with the original author's style; but matched outputs stay statistically distinguishable, with average perplexity of 15.2 against 29.5 for human essays [69]. Mikros finds by stylometric analysis that GPT-4o captures surface elements of Hemingway and Mary Shelley, improves moderately with in-context examples, and still remains clearly separated from the originals; the simpler style (Hemingway) was easier [70].

#### 2.3 Examples, descriptions, or both

Direct comparisons are few and I found no study that settles the question with human judges. Sawant's PersonalBench compares four inference-time methods on 50 blog authors and 1,000 generations: no personalisation, five-shot examples, a two-stage extracted style profile used without examples, and examples plus contrastive examples from other authors plus stylometric measurements [71]. On LUAR similarity to the real author the four methods score 0.484, 0.508, 0.502 and 0.494, a spread of 0.024, all below the 0.626 similarity observed between different human authors [71]. On an LLM judge's trait-match rate the profile method scores highest (0.542 against 0.433 for few-shot) [71]. The three metric families in the companion paper correlate at near zero (|r| < 0.07), so the choice of metric determines the conclusion [72]. These are single-author preprints and a workshop paper, on one domain, with two open-weight generator families and no human validation, as the author states [71]; treat them as a warning about evaluation rather than as a ranking of methods.

The practical reading is that a style description moves what an LLM judge can see, examples move what an authorship model can see, and neither closes the gap alone. STYLL used both together [63].

#### 2.4 The ceiling of prompting

Chakrabarty et al. ran a preregistered study in which MFA-trained writers and three frontier models emulated 50 award-winning authors. With in-context prompting, expert readers strongly disfavoured the AI text for stylistic fidelity (odds ratio 0.16); after fine-tuning on the authors' complete works the experts preferred the AI text (odds ratio 8.16), and detection by commercial detectors fell from 97% to 3% [73]. This is literary fiction by famous authors, not everyday prose, but it is the clearest evidence that prompting has a ceiling which fine-tuning passes. A package that promises parity with fine-tuning from prompts alone would be overclaiming.

#### 2.5 Why the output collapses to a generic register

Reinhart et al. compare human and LLM text written from the same prompts using Biber's feature set. Instruction-tuned models differ from humans more than base models do; GPT-4o uses present participial clauses at 5.3 times the human rate and nominalisations at 2.1 times, and overuses specific words by large factors [74]. Padmakumar and He found that writing with an instruction-tuned model, but not with a base model, produced a statistically significant reduction in diversity across authors [75]. Cho et al. attribute the generic register to training for aggregate preference and observe that models produce connectives such as "additionally" and "therefore" more often than the users they imitate [76]. The default register is therefore a measurable, describable thing, which is what makes contrastive description possible (section 5).

### 3. Personalised generation: benchmarks and retrieval

LaMP is the reference benchmark: seven personalised tasks (three classification, four generation), each user having a profile of past items, with retrieval used to choose which items go into the prompt [77]. LongLaMP extends this to long-form output with four tasks: email completion, abstract generation, review writing and topic (Reddit post) writing [78]. PersonalLLM is a different kind of benchmark: it simulates users with heterogeneous preferences over responses, and is about what a user prefers to receive rather than how a user writes [83]. It is of limited use for author emulation.

What retrieval strategy works best, according to these sources:

- Selection beats inclusion. LaMP compares random selection, BM25, Contriever and recency, and concludes that choosing the most relevant or most recent profile items matters, rather than including any profile items at all [77].
- No retriever wins everywhere. In LaMP the dense retriever was best on most classification tasks, while BM25 was best on generation tasks such as email subject and scholarly title generation [77]. Salemi et al. later train a selector that picks a retriever per input and report significant improvements on six of seven LaMP datasets [82].
- Small k. In LongLaMP the best number of retrieved items was small and task-dependent: 4 for abstracts, 1 for topic writing, 2 to 4 for reviews [78].
- Retrieval tuned to the generator. PEARL trains the retriever against the downstream generation quality and uses the retriever score to predict when a generation will be poor, which triggers revision [79].
- Summary plus retrieval. Richardson et al. add an offline LLM-written user summary to retrieved items and match or beat retrieval alone with 75% less retrieved user data [80]. Li et al. use a five-stage pipeline of retrieval, ranking, summarisation, synthesis and generation [81].

One caveat governs all of the above. These benchmarks score with ROUGE and similar overlap measures against the user's real text [77] [78], and overlap measures reward getting the content and vocabulary right. Wang et al. measured style directly and found topic-similar example selection made style imitation worse [67]. The two results are compatible: retrieval by topic improves what the text says, and can narrow what the model learns about how the author writes. I found no study that isolates the best retrieval strategy for style specifically; the recommendation in the last section is an inference from these two results, not a published finding.

Fine-tuning remains an option for users who want it. Panza fine-tunes a local model and adds retrieval, and reports that under 100 emails are enough to imitate a user convincingly; its authors also name the resulting impersonation risk [84].

### 4. Measuring style match without human judges

#### 4.1 Available judges

- Authorship embeddings. LUAR learns author representations from sets of documents and was studied for transfer across Amazon reviews, fanfiction and Reddit; transfer is good between some domains and poor between others [85]. The public LUAR-MUD checkpoint is trained on Reddit, takes an "episode" of texts per author (16 in the usage example), outputs 512-dimensional embeddings and is Apache-2.0 licensed [86]. It is the basis of the Away/Towards metrics [63] [65].
- Content-independent style embeddings. Wegmann et al. show that good authorship-verification performance does not guarantee a good style representation, because authors keep to their topics; controlling for conversation during training gives representations more independent of content [87]. StyleDistance trains on synthetic near-paraphrases that differ in one of 40 style features, to reduce content leakage further [88].
- Interpretable style features. LISA produces human-readable style attributes by distilling LLM stylometric annotations, which suits a system that must explain why a draft fails [89].
- Classical stylometry. Burrows's Delta compares the relative frequencies of very common words; it works best on texts over 1,500 words and is less reliable across genres or across distant periods of a career [96]. Evert et al. show that the improvement of cosine Delta comes from vector normalisation, and that the authorial signal lies in the profile of deviation across the frequent words [97]. Wang et al. build per-author style models from LIWC and WritePrints features and score by Mahalanobis distance [67].
- LLM as judge. Huang et al. report that LLMs can do zero-shot authorship verification and attribution among 10 to 20 candidates and can explain their decisions in linguistic terms [92]. Cho et al. report about 97% accuracy for their LLM judge on the top authors of two datasets [76].

#### 4.2 How reliable each is

Jangra et al. (accepted at EMNLP 2026 according to the arXiv record) test the metrics on eight writing tasks in three settings of increasing difficulty [90]. The hardest setting, telling a personalised generation from a non-personalised one by the same model, is the one that corresponds to a verification loop. Mean accuracies across settings as retrieved: GPT-4.1 as judge 0.815, BLEU 0.733, StyleDistance 0.722, ROUGE-1 0.722, Wegmann embeddings 0.713; small LLM judges were near random; style-embedding metrics lost the most accuracy moving to the LLM-generated setting (38.3%) and the strong LLM judge lost the least (11.3%) [90]. A performance-weighted ensemble of BLEU, ROUGE-1, StyleDistance and GPT-4.1 scored 0.821, and ensembles generally beat their members [90]. Human agreement on style preference was only 0.641 [90]. Abbas finds neither style embeddings nor an LLM judge uniformly better at telling human from machine continuations, with the advantage varying by generator and domain [91].

#### 4.3 Known failure modes

- Topic leakage. Authorship models use content as well as style. In Wang et al. the zero-shot generations, written with no examples at all, still achieved non-trivial attribution accuracy, which the authors attribute to topical overlap [67]. Sawatphol et al. show that topic leakage in test data inflates authorship-verification results and destabilises model rankings, and propose a sampling method and benchmark to control it [95]. A style score computed between a draft and exemplars on the same topic is therefore inflated.
- Domain mismatch. An embedding trained on Reddit is being used out of domain on email or long-form prose [85] [71].
- Judge bias toward machine text. LLM evaluators recognise and favour their own generations, with self-preference correlated with self-recognition [93]. Wataoka et al. trace the bias to familiarity: LLM judges rate lower-perplexity text higher than humans do [94]. Since LLM imitations have lower perplexity than the human text they imitate [69], an LLM judge is biased in exactly the direction that hides the failure.
- Circularity. If the style profile was written by an LLM and the judge is an LLM checking traits from that profile, the judge measures compliance with the description, not resemblance to the author. PersonalBench shows the profile method winning on the LLM judge while being indistinguishable on LUAR, and reports unstable trait extraction (mean Jaccard similarity 0.22) [71].
- Metrics that disagree. Near-zero correlation between an authorship model, an LLM judge and function-word stylometry [72] means a single number is not evidence.
- Short texts. Delta needs length [96], and the weakest datasets in Jangra et al. were those with short reference texts [90].

### 5. Prompt designs with support

Each design below is labelled by the strength of its support. None has been validated by human judges on everyday authors with a frontier model in a study I could find.

- Describe, then imitate. Supported as a component. STYLL generates style descriptors and uses them with examples [63]; Richardson et al. and Li et al. show LLM-written profile summaries help on personalisation benchmarks [80] [81]. Used alone, a profile is not shown to beat examples on an authorship model [71]. Anthropic ships this as a product feature (custom styles built from uploaded writing samples); I could not open the current help article, which returned an error after a redirect, so this is reported from search results only and is not in the reference list.
- Examples, selected and structured. Well supported: few-shot beats zero-shot consistently [67] [69]. Anthropic's prompting guide asks for examples that are relevant, diverse enough that the model does not pick up unintended patterns, and wrapped in example tags [99]. The diversity requirement matches the finding that topic-narrow example sets hurt [67].
- Contrastive description and negative examples. Supported by one strong method paper. TICL generates the model's own attempt, compares it with the author's real text, and adds the failed attempt plus an explanation of how it differs to the prompt, using fewer than 10 examples per user; it reports win rates up to 91.5% against the prior state of the art under an LLM judge [76]. Its ablation attributes up to 77% of the gain over plain in-context learning to the explanations [76]. The evaluation is an LLM judge, so the caveats of section 4.3 apply. Describing the author relative to the model's default register is further motivated by the measurable features of that register [74].
- Negative constraints. Supported by descriptive evidence, not by an imitation experiment. The overused constructions and words are documented [74] [106], and Wikipedia's editor-maintained field guide catalogues them, noting that the characteristic vocabulary shifts between model generations and that the signs are not proof [100]. A fixed banned-word list will therefore go stale; the list should be data. A constraint is only legitimate if the author does not themselves use the feature, which is checkable against the corpus.
- Two-step content-then-style rewriting. Supported by STYLL's neutralise-then-restyle chain [63] and by the paraphrase formulation [60]. Wang et al. fix content with a summary for the same reason: it separates what is said from how [67].
- Generate several, rerank by measured style. Supported by Prompt-and-Rerank [62] and by TinyStyler's filtering and reranking of candidates [65].
- Iterative critique and revise. Self-Refine reports about 20% absolute average improvement across 7 tasks from a generate, critique, refine loop [98], and PEARL uses a score to trigger revision [79]. I found no study that runs such a loop against a measured style distance for author imitation, so this is a reasoned design, not a tested one. The critic should be given the measured discrepancies (for example function-word deviations) rather than asked for an opinion.
- Seeding with the author's words. Providing the opening of the text raised human-likeness in Wang et al. [67], and completion-style prompting scored highest in Jemama and Kumar [69]. For rewriting tasks the user's own draft serves this role.

### 6. Ethics, and the case for a pre-2023 corpus

#### 6.1 Impersonation, consent, disclosure

The papers treat style imitation as dual-use. TinyStyler's ethics statement says efficient style transfer can aid malicious actors with impersonation, and calls for AI-text detection and media literacy [65]. Patel et al. present the protective use: style transfer as a defence against automated author identification, for people such as political dissidents [63]. Nguyen et al. describe LLMs as double-edged for authorship privacy and note that public writing leaves identifying traces even without explicit identifiers [101]. Panza names the attack directly: a convincing imitation can be built from a small sample of someone's writing [84].

Provider terms bind users of a hosted model regardless of what a package says. Anthropic's usage policy prohibits impersonating a human by presenting results as human-generated or using results to convince a person they are communicating with a natural person when they are not, and prohibits impersonating real entities or creating fake personas to falsely attribute content or mislead others about its origin without consent or legal right [102]. I did not review other providers' policies.

I did not find a published standard wording for responsible use of text style imitation tools. The elements that recur in the sources are: consent of the person imitated, no false attribution, disclosure where a reader would otherwise be misled, and acknowledgement that detection is unreliable [65] [101] [102].

#### 6.2 Why build the model from text written before 2023

The evidence that human-attributed text has been increasingly LLM-processed since ChatGPT's release in November 2022 is strong at the population level.

- Peer reviews: between 6.5% and 16.9% of review text at four AI conferences (ICLR 2024, NeurIPS 2023, CoRL 2023, EMNLP 2023) could have been substantially modified by LLMs [103].
- Papers: across nearly 1 million papers from January 2020 to February 2024, the LLM-modified share rose steadily, reaching up to 17.5% in computer science and up to 6.3% in mathematics and Nature-portfolio papers [104].
- Society at large: roughly 18% of consumer complaint text, up to 24% of corporate press releases, nearly 10% of job postings at small firms and about 14% of UN press releases by late 2024, with growth appearing to stabilise by 2024 [105].
- Vocabulary: Kobak et al. find an abrupt rise in certain style words and estimate that at least 13.5% of 2024 PubMed abstracts were processed with LLMs, up to 40% in some subfields, from more than 15 million abstracts (2010 to 2024) in the Science Advances version; the first arXiv version gave at least 10% from 14.2 million abstracts, with frequency ratios of 25.2 for "delves", 9.2 for "showcasing" and 9.1 for "underscores" [106].

These estimates are corpus-level. Liang et al. say the trends may be too subtle to detect in an individual document [103], so they support a cutoff by date and do not support trying to filter a person's post-2022 text with a detector. Two caveats. First, I found no study that tests whether a personal model built from pre-2023 text imitates better than one built from later text; the advice is a precaution derived from contamination rates. Second, styles drift over a career, and Delta is known to weaken across distant periods [96], so an old corpus trades contamination for staleness. A search result also suggested some of the marker words were already rising before 2022; I did not verify that source and do not rely on it.

### Implications for design

1. Model an author as three artefacts, not one: a structured style description, a pool of exemplars with metadata, and a measured stylometric profile (function-word and feature distributions). The literature shows each is visible to a different judge [71] [72].
2. Always send exemplars. Default to about five, since gains from 2 to 10 were small [67] and the best k in long-form retrieval was 1 to 4 [78]. Make the count a keyword argument.
3. Select exemplars by genre, register and length first, then for diversity; do not default to pure semantic similarity to the task, which hurt style [67]. Keep the selector an injectable strategy, because no retriever wins everywhere [77] [82]. Treat this default as an inference to be tested, not an established result.
4. Write the style description contrastively: how this author differs from the model's default register and from a reference corpus, with quoted evidence. Generate it by the trial-error-explain procedure (model attempts, comparison with the real text, explanation of the difference) and store the failed attempts and explanations as data [76].
5. Keep negative constraints as versioned data, derived per author by checking which default-register features [74] [100] the author does not use. Never ship a fixed universal banned-word list.
6. Rewrite in two steps where content fidelity matters: fix the content (summary or neutral paraphrase), then restyle [63] [67]. When the user supplies a draft, keep their words as the seed [67] [69].
7. Generate several candidates and rerank on the triad of style, content preservation and fluency [58] [62].
8. Make verification an ensemble with separate, reported scores: an authorship embedding (LUAR), a content-independent style embedding (StyleDistance or Wegmann), a function-word measure (cosine Delta) and optionally an LLM judge [90]. Do not collapse to one number by default; report disagreement [72].
9. Calibrate every score per author against two baselines computed from held-out text: the author against themselves (ceiling) and the author against other humans (floor). A draft that scores below the cross-author floor has not been personalised in any meaningful sense [71].
10. Control for topic when scoring: compare the draft with held-out author text on different topics, and report a same-topic score separately [87] [95].
11. If an LLM judge is used, use a different model family from the generator, ask decoupled trait questions rather than a holistic one, and never let it be the only gate, because its bias favours low-perplexity machine text [93] [94] [71].
12. Feed the critique step with measured discrepancies, and cap iterations. State in the documentation that the loop is a reasoned design without direct published validation [98].
13. Warn by genre. Informal, personal writing (blogs, forum posts) is where imitation fails; news and business email are where it works [67]. Surface an expected-difficulty note from the corpus's genre.
14. Enforce minimum text lengths for the stylometric checks and say so in the error message; Delta needs long texts [96].
15. Do not claim undetectability or parity with fine-tuning. Prompted imitations remain detectable [67] [69] and fall short of fine-tuned ones for expert readers [73]. Leave a seam for a fine-tuned or local back end [65] [84].
16. Default the corpus builder to text dated before 2023 when dates are available, warn when later text is included, and allow override with a recency option, documenting the staleness trade-off [103] [104] [105] [106] [96].
17. Ship responsible-use terms with the package and the skill: build a model only of your own writing or with the author's consent; do not attribute generated text to a real person without their agreement; disclose where a reader would be misled; comply with the model provider's usage policy [102]. Record provenance (source, date, consent basis) for every corpus, and keep private corpora out of public repositories.

## Part C: Register, genre and the discovery of registers

*Register and genre: literature and methods for a style-modelling package*

Research date: 2026-09-28. Scope: what the register / genre literature says, and which methods and Python tools are usable, for a package that sorts an author's texts into registers, tracks style per register, discovers new registers as text arrives, and routes a writing request to the right one.

### How to read this report

Every source in the REFERENCES section was opened during this research (publisher page, abstract page, PDF, model card, PyPI JSON record or GitHub API record). Where only an abstract or a secondary description could be opened, the text says so. Numbers are quoted only from the source cited next to them. Package metadata was read from the PyPI JSON API and the GitHub API on 2026-09-28 and will go stale.

### 1. Foundations

#### 1.1 Biber's multidimensional analysis (MDA)

Biber's 1988 book analysed twenty-three spoken and written genres and used factor analysis over linguistic co-occurrence patterns to identify six dimensions of variation [107]. The feature set is 67 linguistic features, and the tagging rules are documented in the book's appendix, which is what made later re-implementations possible [108]. The corpus combined the Lancaster-Oslo-Bergen corpus of written British English, the London-Lund corpus of spoken English, and a collection of professional and personal letters [109].

The six dimensions, with the features that load on them, are summarised by Nini [108]: (1) Involved vs Informational Discourse, where private verbs, contractions, present tense, first and second person pronouns, hedges, amplifiers and wh-questions mark the involved pole, and nouns, word length, prepositions, type/token ratio and attributive adjectives mark the informational pole; (2) Narrative vs Non-Narrative Concerns (past tense, third person pronouns, perfect aspect, public verbs); (3) Context-Independent vs Context-Dependent Discourse, called "explicit vs situation-dependent reference" in other summaries [109]; (4) Overt Expression of Persuasion (infinitives, prediction and necessity modals, suasive verbs, conditional subordination); (5) Abstract vs Non-Abstract Information (passives, conjuncts); (6) On-Line Informational Elaboration.

Three points matter for design. First, the dimensions are continuous: a register is a region in the space, not a box, and genres that separate on one dimension often overlap on another [109]. Second, Biber (1989) followed up with cluster analysis over the dimension scores and obtained eight "text types" that cut across the situationally named genres [108]; this is the direct ancestor of "cluster the feature vectors to find registers". Third, the dimensions were only obtainable because the corpus was deliberately sampled across registers and was large enough for factor analysis; for a small or unstratified corpus Nini recommends projecting texts onto the existing 1988 dimensions instead of running a new factor analysis [108]. Passonneau et al. built samples of 1,000 tokens, motivated by Biber's observation that even rare features are relatively stable at that size [109], which is a warning for short emails and comments.

#### 1.2 Register, genre and style (Biber & Conrad)

Biber and Conrad define a register as a language variety associated with a particular situation of use and with pervasive linguistic features that serve functions within that situation [110]. Argamon, quoting the 2009 edition, draws out the consequence: register is "primarily defined by the situations in which it is used and only secondarily by the linguistic features by which it is recognized", and he notes that this view is not universally adopted in computational work, where "register", "genre" and "text type" are often used interchangeably [111]. Argamon also reports the distinction that register is realised through lexico-grammatical variation while genre is largely realised through discourse structure [111]. In search-result summaries of the book, genre is described as concerning conventional structure and format; I could not open the chapter text itself, so the precise three-way wording (register = pervasive functional features, genre = conventional structures of complete texts, style = aesthetic or author-preference features not functionally motivated) should be checked against the book before it is quoted in documentation.

The situational analysis framework has seven headings: participants, relations among participants, channel, production circumstances, setting, communicative purposes, and topic. I verified the list only through a secondary slide summary of chapter 2 [112] and the chapter abstract [110], not the chapter body.

#### 1.3 Halliday: field, tenor, mode

In systemic functional linguistics a register is "a variety of language, corresponding to a variety of situation", with the situation described by field (the activity and subject matter), tenor (the role relations among participants) and mode (the channel and the part language plays) [113]. Argamon notes that this formulation dominates register synthesis (text generation), because field, tenor and mode can be set by hand as generation parameters, whereas the Biber tradition dominates analysis [111]. A style package does both, so it benefits from both: MDA-like features to describe, field/tenor/mode-like parameters to prompt.

#### 1.4 Why style shifts by addressee: audience design and accommodation

Bell's audience design theory holds that style is essentially the speaker's response to the audience: speakers accommodate primarily to the addressee, with third parties (auditors, overhearers) having lesser effects, and non-audience factors such as topic deriving their effect by association with addressee types [114]. Bell also distinguishes responsive shifts from initiative shifts toward a reference group ("referee design") [114]. For email this maps naturally to To (addressee), Cc (auditor) and a public thread (overhearers).

Communication accommodation theory, developed by Howard Giles from 1970s speech accommodation theory, describes convergence toward and divergence from an interlocutor's style [115]. I could open only an encyclopedia overview of the theory [115]; the primary sources (Giles, Coupland and Coupland 1991) were not accessible. Computational support comes from Danescu-Niculescu-Mizil et al., who derive from the theory the principle that the lower the speaker's power relative to the target, the more the speaker coordinates linguistically, and test it on Wikipedia talk pages and Supreme Court arguments [116].

### 2. Newer work

#### 2.1 Text-linguistic variation

Biber contrasts two corpus research designs: the variationist design, which gives primacy to each linguistic token, and the text-linguistic design, which gives primacy to each text. He argues that average descriptions from a general corpus "do not accurately describe any register" [117]. The design consequence is direct: one averaged style profile per author describes none of that author's registers. The unit of observation should be the text, with rates of features per text.

#### 2.2 Web registers and the CORE corpus

Egbert, Biber and Davies built a bottom-up method in which end users of the web coded situational characteristics of documents through a decision-tree survey, and applied it to 53,000 web documents [118]. Biber and Egbert then ran MDA over that corpus [119]. Ehret and Taboada report that the labelling produced general register types plus sub-registers, many of them hybrid, and that the first dimension found was "oral-involved vs literate" [120], which echoes Dimension 1 of 1988. Hybrids are therefore a normal outcome of situational coding, not an error.

#### 2.3 Register classification with transformers

Laippala et al. released CORE openly and report a 68% F1 score with BERT; they also found that the beginning of a document gave the best classification accuracy [121]. Henriksson et al. extended this to multilingual CORE corpora with over 72,000 documents and a 25-register hierarchical taxonomy across 16 languages; models hit a ceiling at 79% F1, which rose above 90% when ambiguously labelled documents were removed, and the authors attribute the ceiling to inherent ambiguity in web registers and not to model limits [122]. The corresponding model on Hugging Face is fine-tuned from XLM-RoBERTa-large under Apache 2.0 [123].

The X-GENRE classifier (Kuzman, Mozetič, Ljubešić) is fine-tuned from XLM-RoBERTa-base with nine labels (Information/Explanation, News, Instruction, Opinion/Argumentation, Forum, Prose/Lyrical, Legal, Promotion, Other); its card reports macro F1 0.687 on the EN-GINCO test set and recommends applying it to texts of at least 75 words and discarding predictions below 0.8 confidence [124]. The same authors found zero-shot ChatGPT outperformed the fine-tuned model on a dataset unseen by both [125].

Limitation for this project: these taxonomies describe the public web. "Email to a close colleague" vs "email to a stranger" is not a distinction they encode; at best they separate forum-like interactive discussion from informational description. They are useful as a coarse prior on an arbitrary corpus, not as the register model of a person.

#### 2.4 Short-text MDA

Clarke and Grieve analysed 21,739 tweets from one account using multiple correspondence analysis over the presence or absence of 63 grammatical features, instead of factor analysis over relative frequencies, because frequencies are unreliable in very short texts [126]. Dimension 1 correlated strongly with tweet length (r = 0.87) and the other dimensions only weakly, so length was isolated in one dimension; the remaining dimensions were interpreted as conversational, campaigning, engaged and advisory styles, and their use was tracked over time [126]. This is the closest published precedent for the project: one account, short texts, several styles, diachronic drift.

#### 2.5 Register vs dialect in language models

Grieve et al. argue that language models inherently model varieties of language, defining a variety as a population of texts delimited by external factors; dialects are varieties defined by the social background of the producers, registers are varieties defined by the communicative context, and periods by time [127]. They recast domain adaptation as adapting a base model to a more narrowly defined variety and recommend defining the target variety with sociolinguistic care [127]. For this package, a per-register exemplar set is the corpus that defines the target variety for in-context adaptation. I did not find, in the sources opened, a claim by Grieve that register outweighs dialect inside language models; I leave that unasserted.

#### 2.6 Embedding and geometric approaches

I found no verified paper that studies register specifically as geometry in embedding space; searches returned general representation-geometry work only. What does exist is style embedding work. Wegmann et al. show that authorship-verification training leaks topic into "style" representations and that controlling for content with conversation labels gives better style representations [128]. StyleDistance trains on synthetic near-paraphrases varying 40 style features to reduce content leakage and is released under MIT on Hugging Face [129]. Neurobiber is the bridge between the two traditions: a RoBERTa-based tagger that predicts 96 Biber-style features, reported as up to 56 times faster than parsing-based systems while replicating MDA results on CORE [130]. Interpretable features and opaque embeddings are complements: cluster on either, explain with the former.

### 3. Email and workplace registers

Peterson, Hohensee and Xia tested Brown and Levinson's factors (social distance, relative power, weight of imposition) on Enron [131]. Using a classifier trained on 400 hand-labelled emails (80.6% accuracy), they found: personal emails were informal at a rate of 56.0% against 21.3% for business emails; informality rose with the amount of prior contact, from 24.4% for pairs with 1 to 10 emails to 37.5% for pairs with 101 or more; emails to a recipient four or more ranks higher were informal 15.6% of the time against 31.6% for four or more ranks lower; emails containing a request were informal 19.0% of the time against 28.6%; and informality fell from 32.0% with one recipient to 16.5% with three to five, rising slightly again for eleven or more [131]. Two cautions from the same paper: human agreement on a four-level formality scale was only 43.5%, and the classifier's informality features were surface cues (informal words, punctuation, casing) [131]. Formality is a fuzzy label even for humans.

Gilbert modelled whether an Enron email goes up the hierarchy from its phrases, using 2,044 messages and 7,222 candidate phrases; an SVM reached 70.7% accuracy against a 60.5% majority baseline, and "thought you would" signalled an upward message while "let's discuss" signalled the opposite [132]. Notably, a model that knew only the sender's identity already had considerable explanatory power [132], a reminder that idiolect and addressee effects are confounded unless the sender is held fixed, which a personal corpus does by construction. Prabhakaran and Rambow predict hierarchical power relations between participants from a single thread [133]; I verified the citation and task only, not the feature findings.

On formality measures: Heylighen and Dewaele define "deep" formality as avoidance of ambiguity by minimising context-dependence, and propose the F-score, F = (noun + adjective + preposition + article frequencies minus pronoun, verb, adverb and interjection frequencies + 100) / 2, with frequencies as percentages of words; they propose that formality rises with the distance in space, time or background between interlocutors [134]. That is an addressee-distance theory of formality and only needs a part-of-speech tagger. Pavlick and Tetreault studied human perception of formality in four genres and built a predictive model [135]; GYAFC is a formality style-transfer corpus [136]. The `s-nlp/roberta-base-formality-ranker` model was trained on both and its card reports 0.9087 accuracy on the GYAFC test set and a Spearman correlation of 0.7606 on the email subset of the Pavlick-Tetreault data [137].

On politeness: Danescu-Niculescu-Mizil et al. built a classifier from features operationalising indirection, deference, impersonalisation and modality, and found that Wikipedia editors become less polite after being elevated in status and that high-reputation Stack Exchange users are less polite [138]. ConvoKit ships these strategies as a `PolitenessStrategies` transformer [139].

Taken together, the workplace literature supports a small set of addressee variables as drivers of style: tie strength (volume of prior contact), relative power, audience size, personal vs business purpose, and whether the message imposes a request.

### 4. Dynamic and unsupervised register discovery

#### 4.1 Candidate algorithms

Incremental clustering. scikit-learn's BIRCH and MiniBatchKMeans both support `partial_fit`; the documentation advises that BIRCH does not scale well to high-dimensional data and that above roughly twenty features MiniBatchKMeans is generally the better choice [140]. MiniBatchKMeans requires the number of clusters in advance, so it cannot discover a new register.

DP-means. Kulis and Jordan show that a Dirichlet-process mixture's Gibbs sampler approaches a hard clustering algorithm in the limit, giving a k-means-like objective with a penalty on the number of clusters [141]. In practice a point whose distance to every centroid exceeds a threshold λ opens a new cluster. It is a few dozen lines of code, has one interpretable parameter, and is naturally sequential. I did not verify a maintained Python package for it; plan to implement it.

Dirichlet-process mixtures. scikit-learn's `BayesianGaussianMixture` with a Dirichlet process prior needs only an upper bound on components and drives unneeded weights toward zero; the documentation lists slower inference and sensitivity to `weight_concentration_prior` as costs [142]. It is a batch method, so it means periodic refits.

HDBSCAN. `approximate_predict` places new points in an existing condensed tree, can label them as noise, and explicitly cannot create, split or merge clusters; the documentation advises caching data and retraining periodically to avoid drift [143]. The noise label is a free novelty signal.

BERTopic as an analogue. Its online mode uses IncrementalPCA, MiniBatchKMeans and an online vectoriser with decay, and the documentation shows the `river` package's DBSTREAM as a clusterer that can create clusters as data arrives [144]. Its `merge_models` route compares topic embeddings between an old and a new model, treats topics above `min_similarity` (default 0.7) as the same, appends the rest as new, and keeps the original topics' order [145]. That is a ready-made recipe for identity-preserving refits.

Novelty detection. scikit-learn separates outlier detection from novelty detection (clean training data, new observation tested) and offers `OneClassSVM`, `SGDOneClassSVM` and `LocalOutlierFactor(novelty=True)` for the latter [146].

#### 4.2 Keeping identities stable

Chakrabarti, Kumar and Tomkins formalise the trade-off: an evolutionary clustering should stay faithful to current data (snapshot quality) while not shifting dramatically from the previous clustering (history cost), and they list consistency, noise removal, smoothing and cluster correspondence as the benefits [147]. For a user-facing tool the history cost dominates: a user who named a register "close colleagues" must find it unchanged next week.

#### 4.3 LLM-assisted labelling and open-ended categorisation

TnT-LLM generates and iteratively refines a label taxonomy with an LLM, then uses LLM labels to train lightweight classifiers for scale [148]. GoalEx takes a corpus plus a natural-language goal and returns clusters each with a description, by proposing explanations, assigning texts to them, and selecting a subset by integer linear programming [149]. ClusterLLM uses LLM answers to triplet questions to fine-tune a small embedder and pairwise questions to set granularity, at an average cost of about $0.6 per dataset over 14 datasets [150]. Ziems et al. found that zero-shot LLMs do not beat the best fine-tuned classifiers on taxonomic labelling but reach fair agreement with humans, and that they are best used in partnership with people [151].

#### 4.4 Pragmatic recommendation for hundreds to low thousands of short texts

At this size nothing needs to be online in the algorithmic sense; refitting on everything takes seconds. What needs to be incremental is the identity of the registers. Recommended pipeline:

1. Partition by situational metadata first (section 5). This yields the top-level registers with stable, human-readable keys and zero clustering.
2. Inside each situational cell with enough texts, represent each text by an interpretable feature vector (Biber-style features as presence/absence for short texts [126], formality, politeness strategies, length, greeting and sign-off forms) and optionally a style embedding [128, 129]. Treat length as its own variable, since it can dominate the first dimension [126].
3. Assign each arriving text to the nearest register centroid; if its distance exceeds a threshold, hold it in a "pending" pool (DP-means rule [141], or HDBSCAN noise [143]).
4. When the pending pool contains a dense group above a minimum size, propose a new register. Have an LLM write a name and a description from exemplars and contrast exemplars (GoalEx-style [149]), and ask the user to confirm, since LLM labelling is good but not authoritative [151].
5. Refit in batch on a schedule, then map new clusters to old by centroid similarity and keep old identifiers, appending only unmatched clusters [145, 147]. Never renumber.
6. Store the assignment with a confidence, and allow a text to belong to two registers, because hybrids are normal [120, 122].

Uncertainty: no source opened here evaluates this exact pipeline on personal correspondence. The thresholds (distance, minimum cluster size) are parameters to expose, not constants to trust.

### 5. Situational metadata first, linguistic features second

The support for a situational-first definition is strong and consistent. Biber and Conrad define register by situation of use [110]; Argamon states the primary/secondary ordering explicitly [111]; Halliday's register corresponds to a situation type described by field, tenor and mode [113]; Grieve et al. define all varieties by external factors [127]; and the CORE annotation was performed by coding situational characteristics, not by inspecting grammar [118]. Audience design adds that the addressee is the primary situational driver [114], and the Enron studies show measurable effects for exactly the metadata an email client exposes: recipient count, prior contact volume, relative rank, and request vs no request [131, 132].

A workable mapping from available metadata to the seven headings [112]: participants = recipient identity and recipient count; relations among participants = tie strength (message count and recency with that recipient), internal vs external domain, known hierarchy; channel = platform (email, GitHub issue, chat, document); production circumstances = reply vs initiate, thread position, latency, length; setting = public vs private, work vs personal account; communicative purpose = request, report, review, thanks, which must be inferred from text; topic = inferred from text or repository.

The counter-argument should be stated. The MDA tradition is methodologically text-internal, treating linguistic features as primary irrespective of external variables [111], and Biber's text types deliberately cut across situational genres [108]. So the situational key is the primary index, and linguistic clustering is the check on it: two situational cells with indistinguishable feature profiles should be merged, and one cell with two clear linguistic modes should be split. This two-way check is a design inference from the sources, not something a single source prescribes.

### 6. Python tools

| Tool | Where | Licence | Status (2026-09-28) | Weight and notes |
|---|---|---|---|---|
| `pybiber` [152] | PyPI `pybiber` 0.3.1 | MIT (PyPI classifier and README; GitHub API reports no detected licence) | Last release 2026-03-06; 5 releases since 2025-01 | Requires spaCy >= 3.7, polars, adjustText; Python >= 3.10; 67 features; includes MDA and PCA via `BiberAnalyzer`; warns that accuracy depends on tagger quality and degrades on non-standard text |
| `biberplus` [153] | PyPI `biberplus` 0.4.0 | MIT | PyPI release 2025-02-21; repository pushed 2026-07-07 | spaCy, pandas, numpy, factor_analyzer, matplotlib, seaborn; 96 features; windowed counts (default 100 tokens) with mean, min, max, range, standard deviation; PCA and factor analysis |
| Neurobiber [130] | Hugging Face `Blablablab/neurobiber`; no PyPI project found under that name | Not stated on the model card as fetched; the paper is CC BY 4.0 | Paper February 2025 | RoBERTa-based, about 0.1B parameters, 512-token input; needs `transformers` and PyTorch; 96 features predicted as present/absent |
| MAT [154] | GitHub `andreanini/multidimensionalanalysistagger`, v1.3.3 | GPL-3.0 | Last push 2023-12-06 | Perl program for Windows using the Stanford Tagger (Java); 67 features, dimension scores and closest text type; not a Python dependency candidate, and GPL matters for redistribution |
| `textdescriptives` [155] | PyPI `textdescriptives` 2.8.4 | Apache-2.0 | Last release 2024-12-16; repository pushed 2026-05-05 | spaCy, numpy < 2.0, pandas, pyphen, ftfy, pydantic; readability, part-of-speech proportions, dependency distance, coherence, descriptive statistics; the numpy < 2 pin can conflict with newer stacks |
| X-GENRE classifier [124] | Hugging Face `classla/xlm-roberta-base-multilingual-text-genre-classifier` | CC-BY-SA-4.0 | Card last updated 2024-10-07 | XLM-RoBERTa-base; 9 web genres; advised minimum 75 words |
| TurkuNLP register model [123] | Hugging Face `TurkuNLP/web-register-classification-multilingual` | Apache-2.0 | Published 2024-06-28 | XLM-RoBERTa-large (heavy); multilabel CORE taxonomy; English test F1 0.75 |
| Formality ranker [137] | Hugging Face `s-nlp/roberta-base-formality-ranker` | CC BY-NC-SA 4.0 (non-commercial) | Not dated in the fetch | RoBERTa-base; sentence-level formal/informal; the licence restricts commercial users of a public package |
| `convokit` [139] | PyPI `convokit` 4.1.2 | MIT (GitHub; PyPI metadata has no licence field) | Last release 2026-06-28; 76 releases | Heavy: spaCy, sentence-transformers, datasets, pymongo, nltk, scikit-learn, pinned h5py; use only if politeness strategies justify it, or re-implement the markers |
| StyleDistance [129] | Hugging Face `StyleDistance/styledistance` | MIT | NAACL 2025 | RoBERTa-base via `sentence-transformers` |
| Style-Embedding [128] | Hugging Face `AnnaWegmann/Style-Embedding` | Not stated on the card as fetched | 2022 | RoBERTa-base, 768 dimensions, `sentence-transformers` |
| Clustering | PyPI `scikit-learn` 1.9.1, `hdbscan` 0.8.44, `river` 0.26.1, `bertopic` 0.17.4 | BSD-3-Clause, BSD, BSD-3-Clause, MIT | All released within the last ten months | scikit-learn alone covers BIRCH, MiniBatchKMeans, DP mixtures and novelty detection [140, 142, 146] |

Install weight was judged from declared dependencies in the PyPI records, not measured by installing.

### 7. How the unit of analysis changes the method

One person (idiolect). Data is small but metadata is rich and the author is constant, so author and addressee effects are not confounded as they are in Enron-wide models [132]. Zhu and Jurgens found idiolects in online registers to be distinctive yet consistent [156], but Kredens, Heini and Pęzik, studying 112 people across emails, text messages, essays, interviews and other tasks (over one million words), report very low individual stability across genres [157]. The conflict resolves in favour of per-register modelling: a person is recognisable within a register and not reliably across them. For one person the package can do things that are impossible for a corpus: recipient-conditioned registers [114, 131], tie-strength and hierarchy effects [131, 132], diachronic drift tracking per register [126], accommodation to a specific correspondent [116], and contrast against a population baseline to find what is distinctive, which is what projecting a text onto an existing multidimensional model provides [108]. The constraint is statistical: no new factor analysis, presence/absence features, pooled estimates with shrinkage toward the person's overall profile for sparse registers. The shrinkage suggestion is my inference, not a cited finding.

A group, sector or house style. More data averages out idiosyncrasy, so a fresh MDA or clustering is statistically possible, and the target is convention: genre structure, required sections, style-guide rules. Genre in Biber and Conrad's sense (conventional structure of complete texts [111]) matters more here than for a person. Addressee metadata is less useful because the audience is often generic; the relevant situational variables are document type and purpose. Per-author variance should be measured and discarded, not modelled, though the sender-identity effect in Gilbert's model shows it will be large [132].

An arbitrary corpus. No situational metadata, so the situation must be inferred from text, which reverses the natural order of section 5. Options: pretrained register or genre classifiers as a coarse prior [123, 124], subject to the ambiguity ceiling [122]; linguistic clustering in the manner of Biber's text types [108]; and LLM-proposed taxonomies [148, 149]. What cannot be done: recipient-conditioned registers, tie strength, drift (without dates), and any claim that a cluster is a register in the strict sense, since it is only a text type until a situation is attached to it.

What a corpus allows that a person does not: stable dimension estimates, enough data to fine-tune, and a population baseline. The package should therefore ship or compute a reference baseline so that a person's profile can be expressed as deviations.

A caution for all three: Wang et al. evaluated LLM imitation of everyday authors from a few samples (over 40,000 generations per model, more than 400 authors) and found models approximate style in structured formats like news and email but struggle with informal writing in blogs and forums [158]. The informal, close-colleague register is where explicit feature descriptions and carefully chosen exemplars are most needed.

### Implications for design

1. Make the register key situational. Compute a `Situation` record from metadata (channel, recipient set and count, internal/external, reply/initiate, thread position, tie strength) and let that be the primary index; linguistic features describe and validate the register but do not define it [110, 111, 118].
2. Make the situational extractor a seam. Email, GitHub and chat expose different metadata; a corpus exposes none. One keyword argument supplying a `text -> Situation` function, defaulting to metadata when present and to a text-based inference when absent, covers the person, group and corpus cases.
3. Model the addressee explicitly, with Bell's roles: addressee (To), auditor (Cc), overhearer (public thread) [114]. Keep tie strength and relative power as continuous variables, not register names [131].
4. Use the text as the unit and never average across registers into one profile [117, 157].
5. For short texts use presence/absence features and treat length separately [126]; prefer projection onto a reference baseline over per-user factor analysis [108].
6. Keep two representations: interpretable features (what to tell the LLM) and a style embedding (what to measure distance with) [128, 129, 130].
7. Discover registers with a threshold rule plus a pending pool, confirm with the user, and name with an LLM; refit in batch and preserve identifiers by matching centroids [141, 143, 145, 147, 149].
8. Allow hybrid and low-confidence assignments; the literature says the ambiguity is in the data [122].
9. Route a request in this order: named style if given; otherwise the situational key of the request (who is it to, on what channel, reply or new); otherwise the nearest register by the content of the thread being replied to; otherwise the author's most populous register, stated as a fallback.
10. Keep the core dependency light: spaCy-based features and scikit-learn. Put transformer models and ConvoKit behind optional extras. Avoid bundling the CC BY-NC-SA formality model or GPL MAT in a permissively licensed public package [137, 154]; the F-score needs only a tagger [134].
11. Record dates on every text so that per-register drift can be reported and old exemplars can be down-weighted [126].

## REFERENCES

[1] Stamatatos E. A survey of modern authorship attribution methods. J Am Soc Inf Sci Technol. 2009;60(3):538-556. doi:10.1002/asi.21001. [A Survey of Modern Authorship Attribution Methods (PDF)](https://www.clips.uantwerpen.be/~walter/educational/material/Stamatatos_survey2009.pdf)

[2] Koppel M, Schler J, Argamon S. Computational methods in authorship attribution. J Am Soc Inf Sci Technol. 2009;60(1):9-26. doi:10.1002/asi.20961. [Computational Methods in Authorship Attribution (author PDF)](https://u.cs.biu.ac.il/~koppel/papers/authorship-JASIST-final.pdf)

[3] Burrows J. 'Delta': a measure of stylistic difference and a guide to likely authorship. Lit Linguist Comput. 2002;17(3):267-287. Abstract page only. ['Delta': a Measure of Stylistic Difference and a Guide to Likely Authorship](https://academic.oup.com/dsh/article-abstract/17/3/267/929277)

[4] Evert S, Proisl T, Jannidis F, Reger I, Pielström S, Schöch C, Vitt T. Understanding and explaining Delta measures for authorship attribution. Digit Scholarsh Humanit. 2017;32(suppl_2):ii4-ii16. doi:10.1093/llc/fqx023. [Understanding and explaining Delta measures for authorship attribution](https://academic.oup.com/dsh/article/32/suppl_2/ii4/3865676)

[5] Rybicki J, Eder M. Deeper Delta across genres and languages: do we really need the most frequent words? Lit Linguist Comput. 2011;26(3):315-321. Abstract page only. [Deeper Delta across genres and languages](https://academic.oup.com/dsh/article-abstract/26/3/315/1149353)

[6] Eder M. Does size matter? Authorship attribution, small samples, big problem. Digit Scholarsh Humanit. 2015;30(2):167-182. doi:10.1093/llc/fqt066. Abstract page only. [Does size matter? Authorship attribution, small samples, big problem](https://academic.oup.com/dsh/article-abstract/30/2/167/390738)

[7] Eder M. Short samples in authorship attribution: a new approach. Digital Humanities 2017 conference abstracts. [Short samples in authorship attribution: a new approach (PDF)](https://dh2017.adho.org/abstracts/341/341.pdf)

[8] Grieve J. Quantitative authorship attribution: an evaluation of techniques. Lit Linguist Comput. 2007;22(3):251-270. doi:10.1093/llc/fqm020. Abstract page only. [Quantitative Authorship Attribution: An Evaluation of Techniques](https://academic.oup.com/dsh/article-abstract/22/3/251/951481)

[9] Kestemont M. Function words in authorship attribution: from black magic to theory? In: Proceedings of the 3rd Workshop on Computational Linguistics for Literature (CLfL); 2014; Gothenburg. [Function Words in Authorship Attribution. From Black Magic to Theory?](https://aclanthology.org/W14-0908/)

[10] Sapkota U, Bethard S, Montes M, Solorio T. Not all character n-grams are created equal: a study in authorship attribution. In: Proceedings of NAACL-HLT 2015. p. 93-102. [Not All Character N-grams Are Created Equal](https://aclanthology.org/N15-1010/)

[11] Tweedie FJ, Baayen RH. How variable may a constant be? Measures of lexical richness in perspective. Comput Humanit. 1998;32:323-352. Not opened (publisher refused automated access); cited as reported in [1]. [How Variable May a Constant be?](https://link.springer.com/article/10.1023/A:1001749303137)

[12] Abbasi A, Chen H. Writeprints: a stylometric approach to identity-level identification and similarity detection in cyberspace. ACM Trans Inf Syst. 2008;26(2):article 7. [Writeprints (PDF copy)](https://www.scss.tcd.ie/Khurshid.Ahmad/Research/Sentiments/K_Teams_Buchraest/a7-abbasi.pdf)

[13] Brennan M, Afroz S, Greenstadt R. Adversarial stylometry: circumventing authorship recognition to preserve privacy and anonymity. ACM Trans Inf Syst Secur. 2012;15(3). Not opened; citation as given by the `writeprints-static` package description and search results. [Adversarial stylometry](https://dl.acm.org/doi/10.1145/2382448.2382450)

[14] Koppel M, Schler J, Argamon S. Authorship attribution in the wild. Lang Resour Eval. 2011;45(1):83-94. doi:10.1007/s10579-009-9111-2. Bibliographic record only. [Authorship Attribution in the Wild (repository record)](https://touroscholar.touro.edu/president_pubs/281/)

[15] Stamatatos E. Masking topic-related information to enhance authorship attribution. J Assoc Inf Sci Technol. 2018;69(3):461-473. doi:10.1002/asi.23968. Author preprint read. [Masking Topic-related Information to Enhance Authorship Attribution (preprint PDF)](https://icsdweb.aegean.gr/stamatatos/papers/jasist-2018-preprint.pdf)

[16] Altakrori MH, Cheung JCK, Fung BCM. The topic confusion task: a novel scenario for authorship attribution. In: Findings of EMNLP 2021. [The Topic Confusion Task](https://arxiv.org/abs/2104.08530)

[17] Kestemont M, Manjavacas E, Markov I, Bevendorff J, Wiegmann M, Stamatatos E, Stein B, Potthast M. Overview of the cross-domain authorship verification task at PAN 2021. CLEF 2021 Working Notes, CEUR-WS vol. 2936. [Overview of the Cross-Domain Authorship Verification Task at PAN 2021 (PDF)](https://ceur-ws.org/Vol-2936/paper-147.pdf); task page: [Authorship Verification, PAN at CLEF 2021](https://pan.webis.de/clef21/pan21-web/author-identification.html)

[18] Stamatatos E, Kestemont M, Kredens K, Pezik P, Heini A, Bevendorff J, Stein B, Potthast M. Overview of the authorship verification task at PAN 2022. CLEF 2022 Working Notes, CEUR-WS vol. 3180. [Overview of the Authorship Verification Task at PAN 2022 (PDF)](https://ceur-ws.org/Vol-3180/paper-184.pdf)

[19] Coulthard M. Author identification, idiolect, and linguistic uniqueness. Appl Linguist. 2004;25(4):431-447. doi:10.1093/applin/25.4.431. Author's final manuscript read. [Author Identification, Idiolect and Linguistic Uniqueness (Aston record)](https://research.aston.ac.uk/en/publications/author-identification-idiolect-and-linguistic-uniqueness/); [manuscript](https://publications.aston.ac.uk/id/eprint/1928/1/A_AppLing.art.final.doc)

[20] Grant T. TXT 4N6: method, consistency, and distinctiveness in the analysis of SMS text messages. J Law Policy. 2013;21(2):467-494. Bibliographic record only. [TXT 4N6 (Brooklyn Law School repository)](https://brooklynworks.brooklaw.edu/jlp/vol21/iss2/9/)

[21] Wright D. Stylistic variation within genre conventions in the Enron email corpus: developing a text-sensitive methodology for authorship research. Int J Speech Lang Law. 2013;20(1):45-75. Post-print read. [Stylistic variation within genre conventions in the Enron email corpus (post-print PDF)](https://david-wright.net/wp-content/uploads/2021/04/wright-2013-postprint.pdf)

[22] Johnson A, Wright D. Identifying idiolect in forensic authorship attribution: an n-gram textbite approach. Lang Law / Linguagem e Direito. 2014;1(1):37-69. Repository abstract read. [Identifying idiolect in forensic authorship attribution](https://eprints.whiterose.ac.uk/90461)

[23] Wright D. Using word n-grams to identify authors and idiolects: a corpus approach to a forensic linguistic problem. Int J Corpus Linguist. 2017;22(2):212-241. Post-print read. [Using word n-grams to identify authors and idiolects (post-print PDF)](https://irep.ntu.ac.uk/id/eprint/31377/1/PubSub8891_Wright.pdf)

[24] Nini A. A theory of linguistic individuality for authorship analysis. Cambridge: Cambridge University Press; 2023. (Elements in Forensic Linguistics). doi:10.1017/9781108974851. University record read, not the book. [A Theory of Linguistic Individuality for Authorship Analysis](https://research.manchester.ac.uk/en/publications/a-theory-of-linguistic-individuality-for-authorship-analysis/)

[25] Zhu J, Jurgens D. Idiosyncratic but not arbitrary: learning idiolects in online registers reveals distinctive yet consistent individual styles. In: Proceedings of EMNLP 2021. [Idiosyncratic but not Arbitrary](https://arxiv.org/abs/2109.03158)

[26] Rivera-Soto RA, Miano OE, Ordonez J, Chen BY, Khan A, Bishop M, Andrews N. Learning universal authorship representations. In: Proceedings of EMNLP 2021. p. 913-919. [Learning Universal Authorship Representations](https://aclanthology.org/2021.emnlp-main.70/)

[27] Hugging Face model cards: [rrivera1849/LUAR-MUD](https://huggingface.co/rrivera1849/LUAR-MUD), [rrivera1849/LUAR-CRUD](https://huggingface.co/rrivera1849/LUAR-CRUD), [gabrielloiseau/LUAR-MUD-sentence-transformers](https://huggingface.co/gabrielloiseau/LUAR-MUD-sentence-transformers). Accessed 2026-09-28.

[28] Wegmann A, Nguyen D. Does it capture STEL? A modular, similarity-based linguistic style evaluation framework. In: Proceedings of EMNLP 2021. p. 7109-7130. [Does It Capture STEL?](https://aclanthology.org/2021.emnlp-main.569/)

[29] Wegmann A, Schraagen M, Nguyen D. Same author or just same topic? Towards content-independent style representations. In: Proceedings of the 7th Workshop on Representation Learning for NLP; 2022. p. 249-268. [Same Author or Just Same Topic?](https://aclanthology.org/2022.repl4nlp-1.26/)

[30] Hugging Face model card: [AnnaWegmann/Style-Embedding](https://huggingface.co/AnnaWegmann/Style-Embedding); code: [nlpsoc/Style-Embeddings](https://github.com/nlpsoc/Style-Embeddings). Accessed 2026-09-28.

[31] Patel A, Rao D, Kothary A, McKeown K, Callison-Burch C. Learning interpretable style embeddings via prompting LLMs. In: Findings of EMNLP 2023. p. 15270-15290. [Learning Interpretable Style Embeddings via Prompting LLMs](https://aclanthology.org/2023.findings-emnlp.1020/)

[32] Patel A, Zhu J, Qiu J, Horvitz Z, Apidianaki M, McKeown K, Callison-Burch C. StyleDistance: stronger content-independent style embeddings with synthetic parallel examples. NAACL 2025. arXiv:2410.12757. [StyleDistance](https://arxiv.org/abs/2410.12757)

[33] Hugging Face model card: [StyleDistance/styledistance](https://huggingface.co/StyleDistance/styledistance). Accessed 2026-09-28.

[34] Qiu J, Zhu J, Patel A, Apidianaki M, Callison-Burch C. mStyleDistance: multilingual style embeddings and their evaluation. arXiv:2502.15168; 2025. [mStyleDistance](https://arxiv.org/abs/2502.15168)

[35] Hugging Face model card: [StyleDistance/mstyledistance](https://huggingface.co/StyleDistance/mstyledistance). Accessed 2026-09-28.

[36] Alkiek K, Wegmann A, Zhu J, Jurgens D. Neurobiber: fast and interpretable stylistic feature extraction. arXiv:2502.18590; 2025. [Neurobiber](https://arxiv.org/abs/2502.18590)

[37] Hugging Face model: [Blablablab/neurobiber](https://huggingface.co/Blablablab/neurobiber). Accessed 2026-09-28.

[38] Rivera Soto R, Wegmann A, Aggazzotti C. STEB: Style Text Embedding Benchmark. arXiv:2606.31741; 2026. [STEB: Style Text Embedding Benchmark](https://arxiv.org/abs/2606.31741)

[39] Wang Z, Tripto NI, Park S, Li Z, Zhou J. Catch me if you can? Not yet: LLMs still struggle to imitate the implicit writing styles of everyday authors. arXiv:2509.14543; 2025. [Catch Me If You Can? Not Yet](https://arxiv.org/abs/2509.14543)

[40] faststylometry. [PyPI](https://pypi.org/project/faststylometry/); [GitHub](https://github.com/fastdatascience/faststylometry). Accessed 2026-09-28.

[41] stylo (R package). [GitHub](https://github.com/computationalstylistics/stylo). Unrelated PyPI project of the same name: [stylo on PyPI](https://pypi.org/project/stylo/). Accessed 2026-09-28.

[42] pydelta. [GitHub](https://github.com/cophi-wue/pydelta). Accessed 2026-09-28.

[43] PyStyl. [GitHub](https://github.com/mikekestemont/pystyl). Accessed 2026-09-28.

[44] textstat. [PyPI](https://pypi.org/project/textstat/); [GitHub](https://github.com/textstat/textstat). Accessed 2026-09-28.

[45] spaCy. [PyPI](https://pypi.org/project/spacy/). Accessed 2026-09-28.

[46] TextDescriptives. [PyPI](https://pypi.org/project/textdescriptives/); [documentation](https://hlasse.github.io/TextDescriptives/). Accessed 2026-09-28.

[47] LexicalRichness. [PyPI](https://pypi.org/project/lexicalrichness/); [GitHub](https://github.com/LSYS/LexicalRichness). Accessed 2026-09-28.

[48] Lee BW, Lee JH-J. LFTK: handcrafted features in computational linguistics. BEA workshop at ACL 2023. arXiv:2305.15878. [LFTK paper](https://arxiv.org/abs/2305.15878); [PyPI](https://pypi.org/project/lftk/); [GitHub](https://github.com/brucewlee/lftk). Accessed 2026-09-28.

[49] Okulska I, Stetsenko D, Kołos A, Karlińska A, Głąbińska K, Nowakowski A. StyloMetrix: an open-source multilingual tool for representing stylometric vectors. arXiv:2309.12810; 2023. [StyloMetrix paper](https://arxiv.org/abs/2309.12810); [PyPI: stylo-metrix](https://pypi.org/project/stylo-metrix/); [GitHub](https://github.com/NASK-NLP/StyloMetrix); [English metrics list](https://github.com/NASK-NLP/StyloMetrix/blob/main/resources/metrics_list_en.md). Accessed 2026-09-28.

[50] pybiber. [PyPI](https://pypi.org/project/pybiber/); [GitHub](https://github.com/browndw/pybiber). Accessed 2026-09-28.

[51] biberpy. [GitHub](https://github.com/ssharoff/biberpy). Accessed 2026-09-28.

[52] biberplus. [PyPI](https://pypi.org/project/biberplus/); [GitHub](https://github.com/davidjurgens/biberplus). Accessed 2026-09-28.

[53] cophi. [PyPI](https://pypi.org/project/cophi/); [GitHub](https://github.com/cophi-wue/cophi-toolbox). Accessed 2026-09-28.

[54] PAN shared-task code. [GitHub](https://github.com/pan-webis-de/pan-code). Accessed 2026-09-28.

[55] sentence-transformers. [PyPI](https://pypi.org/project/sentence-transformers/). Accessed 2026-09-28.

[56] pystylometry. [PyPI](https://pypi.org/project/pystylometry/). Accessed 2026-09-28.

[57] writeprints-static. [PyPI](https://pypi.org/project/writeprints-static/). Accessed 2026-09-28.

[58] Jin D, Jin Z, Hu Z, Vechtomova O, Mihalcea R. Deep learning for text style transfer: a survey. Computational Linguistics. 2022;48(1):155-205. [Deep Learning for Text Style Transfer: A Survey](https://aclanthology.org/2022.cl-1.6/) (preprint: [arXiv:2011.00416](https://arxiv.org/abs/2011.00416))

[59] Hu Z, Lee RKW, Aggarwal CC, Zhang A. Text style transfer: a review and experimental evaluation. SIGKDD Explorations. 2022;24:14-45. [Text Style Transfer: A Review and Experimental Evaluation](https://arxiv.org/abs/2010.12742)

[60] Krishna K, Wieting J, Iyyer M. Reformulating unsupervised style transfer as paraphrase generation. EMNLP 2020. [Reformulating Unsupervised Style Transfer as Paraphrase Generation](https://arxiv.org/abs/2010.05700)

[61] Reif E, Ippolito D, Yuan A, Coenen A, Callison-Burch C, Wei J. A recipe for arbitrary text style transfer with large language models. arXiv:2109.03910; 2021 (revised 2022). [A Recipe For Arbitrary Text Style Transfer with Large Language Models](https://arxiv.org/abs/2109.03910)

[62] Suzgun M, Melas-Kyriazi L, Jurafsky D. Prompt-and-rerank: a method for zero-shot and few-shot arbitrary textual style transfer with small language models. arXiv:2205.11503; 2022. [Prompt-and-Rerank](https://arxiv.org/abs/2205.11503)

[63] Patel A, Andrews N, Callison-Burch C. Low-resource authorship style transfer: can non-famous authors be imitated? arXiv:2212.08986; 2022 (revised 2024). [Low-Resource Authorship Style Transfer: Can Non-Famous Authors Be Imitated?](https://arxiv.org/abs/2212.08986)

[64] Horvitz Z, Patel A, Callison-Burch C, Yu Z, McKeown K. ParaGuide: guided diffusion paraphrasers for plug-and-play textual style transfer. arXiv:2308.15459; 2023 (revised 2024). [ParaGuide](https://arxiv.org/abs/2308.15459)

[65] Horvitz Z, Patel A, Singh K, Callison-Burch C, McKeown K, Yu Z. TinyStyler: efficient few-shot text style transfer with authorship embeddings. arXiv:2406.15586; 2024. [TinyStyler](https://arxiv.org/abs/2406.15586)

[66] Liu S, Agarwal S, May J. Authorship style transfer with policy optimization. arXiv:2403.08043; 2024. [Authorship Style Transfer with Policy Optimization](https://arxiv.org/abs/2403.08043)

[67] Wang Z, Tripto NI, Park S, Li Z, Zhou J. Catch me if you can? Not yet: LLMs still struggle to imitate the implicit writing styles of everyday authors. Findings of EMNLP 2025. arXiv:2509.14543. [Catch Me If You Can? Not Yet](https://arxiv.org/abs/2509.14543)

[68] Bhandarkar A, Wilson R, Swarup A, Woodard D. Emulating author style: a feasibility study of prompt-enabled text stylization with off-the-shelf LLMs. Proceedings of the 1st Workshop on Personalization of Generative AI Systems (PERSONALIZE 2024); p. 76-82. [Emulating Author Style](https://aclanthology.org/2024.personalize-1.6/)

[69] Jemama R, Kumar R. How well do LLMs imitate human writing style? IEEE UEMCON 2025. arXiv:2509.24930. [How Well Do LLMs Imitate Human Writing Style?](https://arxiv.org/abs/2509.24930)

[70] Mikros G. Beyond the surface: stylometric analysis of GPT-4o's capacity for literary style imitation. Digital Scholarship in the Humanities. 2025;40(2):587. [Beyond the surface](https://academic.oup.com/dsh/article/40/2/587/8118784)

[71] Sawant YG. PersonalBench: measuring the authorship gap in LLM personalization. arXiv:2608.19746; 2026. [PersonalBench](https://arxiv.org/abs/2608.19746)

[72] Sawant YG. Theory-grounded evaluation exposes the authorship gap in LLM personalization. CTB Workshop, ICML 2026. arXiv:2604.26460. [Theory-Grounded Evaluation Exposes the Authorship Gap in LLM Personalization](https://arxiv.org/abs/2604.26460)

[73] Chakrabarty T, Ginsburg JC, Dhillon P. Readers prefer outputs of AI trained on copyrighted books over expert human writers. arXiv:2510.13939; 2025 (revised 2026). [Readers Prefer Outputs of AI Trained on Copyrighted Books over Expert Human Writers](https://arxiv.org/abs/2510.13939)

[74] Reinhart A, Markey B, Laudenbach M, Pantusen K, Yurko R, Weinberg G, Brown DW. Do LLMs write like humans? Variation in grammatical and rhetorical styles. Proceedings of the National Academy of Sciences. 2025;122. arXiv:2410.16107. [Do LLMs write like humans?](https://arxiv.org/abs/2410.16107)

[75] Padmakumar V, He H. Does writing with language models reduce content diversity? ICLR 2024. [Does Writing with Language Models Reduce Content Diversity?](https://arxiv.org/abs/2309.05196)

[76] Cho H, Sharma K, Jedema N, Ribeiro LFR, Moschitti A, Krishnan R, May J. Tuning-free personalized alignment via trial-error-explain in-context learning. Findings of NAACL 2025. arXiv:2502.08972. [Trial-Error-Explain In-Context Learning](https://arxiv.org/abs/2502.08972)

[77] Salemi A, Mysore S, Bendersky M, Zamani H. LaMP: when large language models meet personalization. arXiv:2304.11406; 2023 (revised 2024). [LaMP](https://arxiv.org/abs/2304.11406)

[78] Kumar I, Viswanathan S, Yerra S, Salemi A, Rossi RA, Dernoncourt F, et al. LongLaMP: a benchmark for personalized long-form text generation. arXiv:2407.11016; 2024. [LongLaMP](https://arxiv.org/abs/2407.11016)

[79] Mysore S, Lu Z, Wan M, Yang L, Sarrafzadeh B, Menezes S, et al. Pearl: personalizing large language model writing assistants with generation-calibrated retrievers. Workshop on Customizable NLP at EMNLP 2024. arXiv:2311.09180. [Pearl](https://arxiv.org/abs/2311.09180)

[80] Richardson C, Zhang Y, Gillespie K, Kar S, Singh A, Raeesy Z, et al. Integrating summarization and retrieval for enhanced personalization via large language models. International Workshop on Personalized Generative AI at CIKM 2023. arXiv:2310.20081. [Integrating Summarization and Retrieval for Enhanced Personalization](https://arxiv.org/abs/2310.20081)

[81] Li C, Zhang M, Mei Q, Wang Y, Hombaiah SA, Liang Y, Bendersky M. Teach LLMs to personalize: an approach inspired by writing education. arXiv:2308.07968; 2023. [Teach LLMs to Personalize](https://arxiv.org/abs/2308.07968)

[82] Salemi A, Kallumadi S, Zamani H. Optimization methods for personalizing large language models through retrieval augmentation. arXiv:2404.05970; 2024. [Optimization Methods for Personalizing LLMs through Retrieval Augmentation](https://arxiv.org/abs/2404.05970)

[83] Zollo TP, Siah AWT, Ye N, Li A, Namkoong H. PersonalLLM: tailoring LLMs to individual preferences. arXiv:2409.20296; 2024 (revised 2025). [PersonalLLM](https://arxiv.org/abs/2409.20296)

[84] Nicolicioiu A, Iofinova E, Jovanovic A, Kurtic E, Nikdan M, Panferov A, et al. Panza: design and analysis of a fully-local personalized text writing assistant. arXiv:2407.10994; 2024 (revised 2025). [Panza](https://arxiv.org/abs/2407.10994)

[85] Rivera-Soto RA, Miano OE, Ordonez J, Chen BY, Khan A, Bishop M, Andrews N. Learning universal authorship representations. EMNLP 2021. [Learning Universal Authorship Representations](https://aclanthology.org/2021.emnlp-main.70/)

[86] Rivera-Soto RA. LUAR-MUD model card. Hugging Face. [rrivera1849/LUAR-MUD](https://huggingface.co/rrivera1849/LUAR-MUD)

[87] Wegmann A, Schraagen M, Nguyen D. Same author or just same topic? Towards content-independent style representations. 7th Workshop on Representation Learning for NLP (RepL4NLP), ACL 2022. [Same Author or Just Same Topic?](https://arxiv.org/abs/2204.04907)

[88] Patel A, Zhu J, Qiu J, Horvitz Z, Apidianaki M, McKeown K, Callison-Burch C. StyleDistance: stronger content-independent style embeddings with synthetic parallel examples. NAACL 2025. arXiv:2410.12757. [StyleDistance](https://arxiv.org/abs/2410.12757)

[89] Patel A, Rao D, Kothary A, McKeown K, Callison-Burch C. Learning interpretable style embeddings via prompting LLMs. arXiv:2305.12696; 2023. [Learning Interpretable Style Embeddings via Prompting LLMs](https://arxiv.org/abs/2305.12696)

[90] Jangra A, Sarrafzadeh B, Cucerzan S, de Wynter A, Jauhar SK. Evaluating style-personalized text generation: challenges and directions. arXiv:2508.06374; 2025 (revised 2026; listed as accepted to EMNLP 2026). [Evaluating Style-Personalized Text Generation](https://arxiv.org/abs/2508.06374)

[91] Abbas M. Attribution quality in AI-generated content: benchmarking style embeddings and LLM judges. IEEE ICDM 2025 workshop. arXiv:2510.13898. [Attribution Quality in AI-Generated Content](https://arxiv.org/abs/2510.13898)

[92] Huang B, Chen C, Shu K. Can large language models identify authorship? Findings of EMNLP 2024. arXiv:2403.08213. [Can Large Language Models Identify Authorship?](https://arxiv.org/abs/2403.08213)

[93] Panickssery A, Bowman SR, Feng S. LLM evaluators recognize and favor their own generations. arXiv:2404.13076; 2024. [LLM Evaluators Recognize and Favor Their Own Generations](https://arxiv.org/abs/2404.13076)

[94] Wataoka K, Takahashi T, Ri R. Self-preference bias in LLM-as-a-judge. NeurIPS 2024 Safe Generative AI Workshop. arXiv:2410.21819. [Self-Preference Bias in LLM-as-a-Judge](https://arxiv.org/abs/2410.21819)

[95] Sawatphol J, Udomcharoenchaikit C, Nutanong S. Addressing topic leakage in cross-topic evaluation for authorship verification. Transactions of the Association for Computational Linguistics. 2024. arXiv:2407.19164. [Addressing Topic Leakage in Cross-Topic Evaluation for Authorship Verification](https://arxiv.org/abs/2407.19164)

[96] Burrows J. 'Delta': a measure of stylistic difference and a guide to likely authorship. Literary and Linguistic Computing. 2002;17(3):267-287. ['Delta': a Measure of Stylistic Difference and a Guide to Likely Authorship](https://academic.oup.com/dsh/article-abstract/17/3/267/929277)

[97] Evert S, Proisl T, Jannidis F, Reger I, Pielström S, Schöch C, Vitt T. Understanding and explaining Delta measures for authorship attribution. Digital Scholarship in the Humanities. 2017;32(suppl 2):ii4-ii16. [Understanding and explaining Delta measures for authorship attribution](https://academic.oup.com/dsh/article/32/suppl_2/ii4/3865676)

[98] Madaan A, et al. Self-Refine: iterative refinement with self-feedback. arXiv:2303.17651; 2023. [Self-Refine](https://arxiv.org/abs/2303.17651)

[99] Anthropic. Prompting best practices (section on using examples). Claude developer documentation. Accessed 2026-09-28. [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)

[100] Wikipedia contributors. Wikipedia: Signs of AI writing. WikiProject AI Cleanup advice page. Accessed 2026-09-28. [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)

[101] Nguyen T, Hu Y, Le T. Unraveling interwoven roles of large language models in authorship privacy: obfuscation, mimicking, and verification. arXiv:2505.14195; 2025. [Unraveling Interwoven Roles of LLMs in Authorship Privacy](https://arxiv.org/abs/2505.14195)

[102] Anthropic. Usage policy. Accessed 2026-09-28. [Anthropic Usage Policy](https://www.anthropic.com/legal/aup)

[103] Liang W, Izzo Z, Zhang Y, Lepp H, Cao H, Zhao X, et al. Monitoring AI-modified content at scale: a case study on the impact of ChatGPT on AI conference peer reviews. ICML 2024. arXiv:2403.07183. [Monitoring AI-Modified Content at Scale](https://arxiv.org/abs/2403.07183)

[104] Liang W, Zhang Y, Wu Z, et al. Mapping the increasing use of LLMs in scientific papers. arXiv:2404.01268; 2024. [Mapping the Increasing Use of LLMs in Scientific Papers](https://arxiv.org/abs/2404.01268)

[105] Liang W, Zhang Y, Codreanu M, Wang J, Cao H, Zou J. The widespread adoption of large language model-assisted writing across society. arXiv:2502.09747; 2025. [The Widespread Adoption of LLM-Assisted Writing Across Society](https://arxiv.org/abs/2502.09747)

[106] Kobak D, González-Márquez R, Horvát EÁ, Lause J. Delving into LLM-assisted writing in biomedical publications through excess vocabulary. Science Advances. 2025. arXiv:2406.07016 (first version titled "Delving into ChatGPT usage in academic writing through excess vocabulary"). [Delving into LLM-assisted writing in biomedical publications through excess vocabulary](https://arxiv.org/abs/2406.07016)

[107] Biber D. Variation across Speech and Writing. Cambridge: Cambridge University Press; 1988 (paperback 1991). [Variation across Speech and Writing (Google Books record)](https://books.google.com/books/about/Variation_Across_Speech_and_Writing.html?id=CVTPaSSYEroC)

[108] Nini A. The Multi-Dimensional Analysis Tagger. In: Berber Sardinha T, Veirano Pinto M, editors. Multi-Dimensional Analysis: Research Methods and Current Issues. London: Bloomsbury Academic; 2019. p. 67-94. [The Multidimensional Analysis Tagger (pre-print)](https://andreanini.com/wp-content/uploads/2019/06/pre-print-the-multidimensional-analysis-tagger.pdf)

[109] Passonneau RJ, Ide N, Su S, Stuart J. Biber Redux: Reconsidering Dimensions of Variation in American English. In: Proceedings of COLING 2014; 2014. p. 565-576. [Biber Redux](https://aclanthology.org/C14-1054.pdf)

[110] Biber D, Conrad S. Describing the situational characteristics of registers and genres. In: Register, Genre, and Style. Cambridge: Cambridge University Press; 2009. p. 31-49. doi:10.1017/CBO9780511814358.002. [Register, Genre, and Style, chapter 2](https://www.cambridge.org/core/books/abs/register-genre-and-style/describing-the-situational-characteristics-of-registers-and-genres/1E2EC0EBA5AC86A1407FCC3539052F51)

[111] Argamon SE. Computational Register Analysis and Synthesis. Pre-print of an article for Register Studies; 2019. arXiv:1901.02543. [Computational Register Analysis and Synthesis](https://arxiv.org/pdf/1901.02543)

[112] Describing the Situational Characteristics of Registers and Genres (slide summary of Biber and Conrad, chapter 2; secondary source). [Slide summary](https://www.slideshare.net/slideshow/describing-the-situational-characteristics-of-registers-and-genres/53165370)

[113] Lukin A, Moore A, Herke M, Wegener R, Wu C. Halliday's model of register revisited and explored. Linguistics and the Human Sciences. 2008;4(2):187-213. [Halliday's model of register revisited and explored](https://researchers.mq.edu.au/en/publications/hallidays-model-of-register-revisited-and-explored/)

[114] Bell A. Language style as audience design. Language in Society. 1984;13(2):145-204. doi:10.1017/S004740450001037X. [Language style as audience design](https://www.cambridge.org/core/journals/language-in-society/article/abs/language-style-as-audience-design/35677FBB8C9B7602DC20FDD354DB2ADD)

[115] Wikipedia contributors. Communication accommodation theory (encyclopedia overview; primary sources not accessed). [Communication accommodation theory](https://en.wikipedia.org/wiki/Communication_accommodation_theory)

[116] Danescu-Niculescu-Mizil C, Lee L, Pang B, Kleinberg J. Echoes of Power: Language Effects and Power Differences in Social Interaction. In: Proceedings of WWW 2012; 2012. [Echoes of Power](https://www.cs.cornell.edu/~cristian/Echoes_of_power_files/echoes_of_power.pdf)

[117] Biber D. Register as a predictor of linguistic variation. Corpus Linguistics and Linguistic Theory. 2012;8(1):9-37. doi:10.1515/cllt-2012-0002. [Register as a predictor of linguistic variation](https://doi.org/10.1515/cllt-2012-0002)

[118] Egbert J, Biber D, Davies M. Developing a bottom-up, user-based method of web register classification. Journal of the Association for Information Science and Technology. 2015;66(9):1817-1831. doi:10.1002/asi.23308. [Developing a bottom-up, user-based method of web register classification](https://experts.nau.edu/en/publications/developing-a-bottom-up-user-based-method-of-web-register-classifi)

[119] Biber D, Egbert J. Register Variation Online. Cambridge: Cambridge University Press; 2018. doi:10.1017/9781316388228. [Register Variation Online](https://www.cambridge.org/core/books/register-variation-online/D1D0F0E0BFEA077107F4686C357AA66B)

[120] Ehret K, Taboada M. Characterising Online News Comments: A Multi-Dimensional Cruise Through Online Registers. Frontiers in Artificial Intelligence. 2021;4:643770. doi:10.3389/frai.2021.643770. [Characterising Online News Comments](https://pmc.ncbi.nlm.nih.gov/articles/PMC8238081/)

[121] Laippala V, Rönnqvist S, Oinonen M, Kyröläinen AJ, Salmela A, Biber D, Egbert J, Pyysalo S. Register identification from the unrestricted open Web using the Corpus of Online Registers of English. Language Resources and Evaluation. 2023;57(3):1045-1079. [Register identification from the unrestricted open Web](https://experts.nau.edu/en/publications/register-identification-from-the-unrestricted-open-web-using-the-/)

[122] Henriksson E, Myntti A, Hellström S, Eskelinen A, Erten-Johansson S, Laippala V. Automatic register identification for the open web using multilingual deep learning. arXiv:2406.19892; 2024. [Automatic register identification for the open web](https://arxiv.org/abs/2406.19892)

[123] TurkuNLP. Web register classification (multilingual model). Hugging Face model card. [TurkuNLP/web-register-classification-multilingual](https://huggingface.co/TurkuNLP/web-register-classification-multilingual)

[124] CLASSLA. X-GENRE classifier: multilingual text genre classifier. Hugging Face model card (cites Kuzman T, Mozetič I, Ljubešić N. Machine Learning and Knowledge Extraction. 2023;5(3):1149-1175; the journal page itself could not be opened). [classla/xlm-roberta-base-multilingual-text-genre-classifier](https://huggingface.co/classla/xlm-roberta-base-multilingual-text-genre-classifier)

[125] Kuzman T, Mozetič I, Ljubešić N. ChatGPT: Beginning of an End of Manual Linguistic Data Annotation? Use Case of Automatic Genre Identification. arXiv:2303.03953; 2023. [ChatGPT: Beginning of an End of Manual Linguistic Data Annotation?](https://arxiv.org/abs/2303.03953)

[126] Clarke I, Grieve J. Stylistic variation on the Donald Trump Twitter account: A linguistic analysis of tweets posted between 2009 and 2018. PLoS ONE. 2019;14(9):e0222062. [Stylistic variation on the Donald Trump Twitter account](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0222062)

[127] Grieve J, Bartl S, Fuoli M, Grafmiller J, Huang W, Jawerbaum A, Murakami A, Perlman M, Roemling D, Winter B. The sociolinguistic foundations of language modeling. Frontiers in Artificial Intelligence. 2025. [The sociolinguistic foundations of language modeling](https://pmc.ncbi.nlm.nih.gov/articles/PMC11770026/)

[128] Wegmann A, Schraagen M, Nguyen D. Same Author or Just Same Topic? Towards Content-Independent Style Representations. In: Proceedings of the 7th Workshop on Representation Learning for NLP; 2022. p. 249-268. [Same Author or Just Same Topic?](https://aclanthology.org/2022.repl4nlp-1.26/) Model: [AnnaWegmann/Style-Embedding](https://huggingface.co/AnnaWegmann/Style-Embedding)

[129] Patel A, Zhu J, Qiu J, Horvitz Z, Apidianaki M, McKeown K, Callison-Burch C. StyleDistance: Stronger Content-Independent Style Embeddings with Synthetic Parallel Examples. NAACL 2025. arXiv:2410.12757. [StyleDistance](https://arxiv.org/abs/2410.12757) Model: [StyleDistance/styledistance](https://huggingface.co/StyleDistance/styledistance)

[130] Alkiek K, Wegmann A, Zhu J, Jurgens D. Neurobiber: Fast and Interpretable Stylistic Feature Extraction. arXiv:2502.18590; 2025. [Neurobiber](https://arxiv.org/abs/2502.18590) Model: [Blablablab/neurobiber](https://huggingface.co/Blablablab/neurobiber)

[131] Peterson K, Hohensee M, Xia F. Email Formality in the Workplace: A Case Study on the Enron Corpus. In: Proceedings of the Workshop on Language in Social Media (LSM 2011); 2011. p. 86-95. [Email Formality in the Workplace](https://aclanthology.org/W11-0711.pdf)

[132] Gilbert E. Phrases That Signal Workplace Hierarchy. In: Proceedings of CSCW 2012; 2012. [Phrases That Signal Workplace Hierarchy](http://eegilbert.org/papers/cscw12.hierarchy.gilbert.pdf)

[133] Prabhakaran V, Rambow O. Predicting Power Relations between Participants in Written Dialog from a Single Thread. In: Proceedings of ACL 2014 (Short Papers); 2014. p. 339-344. [Predicting Power Relations](https://aclanthology.org/P14-2056/)

[134] Heylighen F, Dewaele JM. Formality of Language: definition, measurement and behavioral determinants. Internal Report, Center "Leo Apostel", Free University of Brussels; 1999. [Formality of Language](http://pespmc1.vub.ac.be/Papers/Formality.pdf)

[135] Pavlick E, Tetreault J. An Empirical Analysis of Formality in Online Communication. Transactions of the Association for Computational Linguistics. 2016;4:61-74. doi:10.1162/tacl_a_00083. [An Empirical Analysis of Formality in Online Communication](https://aclanthology.org/Q16-1005/)

[136] Rao S, Tetreault J. Dear Sir or Madam, May I Introduce the GYAFC Dataset: Corpus, Benchmarks and Metrics for Formality Style Transfer. In: Proceedings of NAACL-HLT 2018; 2018. p. 129-140. [GYAFC](https://aclanthology.org/N18-1012/)

[137] s-nlp. roberta-base-formality-ranker. Hugging Face model card. [s-nlp/roberta-base-formality-ranker](https://huggingface.co/s-nlp/roberta-base-formality-ranker)

[138] Danescu-Niculescu-Mizil C, Sudhof M, Jurafsky D, Leskovec J, Potts C. A computational approach to politeness with application to social factors. In: Proceedings of ACL 2013; 2013. p. 250-259. arXiv:1306.6078. [A computational approach to politeness](https://arxiv.org/abs/1306.6078)

[139] Cornell NLP. ConvoKit: PolitenessStrategies documentation, and PyPI record for convokit 4.1.2. [ConvoKit PolitenessStrategies](https://convokit.cornell.edu/documentation/politenessStrategies.html) and [convokit on PyPI](https://pypi.org/project/convokit/)

[140] scikit-learn developers. Clustering (user guide). [scikit-learn: Clustering](https://scikit-learn.org/stable/modules/clustering.html)

[141] Kulis B, Jordan MI. Revisiting k-means: New Algorithms via Bayesian Nonparametrics. ICML 2012. arXiv:1111.0352. [Revisiting k-means](https://arxiv.org/abs/1111.0352)

[142] scikit-learn developers. Gaussian mixture models (user guide). [scikit-learn: Mixture models](https://scikit-learn.org/stable/modules/mixture.html)

[143] hdbscan developers. Predicting clusters for new points. [hdbscan prediction tutorial](https://hdbscan.readthedocs.io/en/latest/prediction_tutorial.html)

[144] Grootendorst M. BERTopic documentation: Online Topic Modeling. [BERTopic: Online Topic Modeling](https://maartengr.github.io/BERTopic/getting_started/online/online.html)

[145] Grootendorst M. BERTopic documentation: Merge Multiple Models. [BERTopic: Merge Multiple Models](https://maartengr.github.io/BERTopic/getting_started/merge/merge.html)

[146] scikit-learn developers. Novelty and Outlier Detection (user guide). [scikit-learn: Novelty and Outlier Detection](https://scikit-learn.org/stable/modules/outlier_detection.html)

[147] Chakrabarti D, Kumar R, Tomkins A. Evolutionary Clustering. In: Proceedings of KDD 2006; 2006. [Evolutionary Clustering](https://faculty.mccombs.utexas.edu/deepayan.chakrabarti/mywww/papers/kdd06-evolutionary.pdf)

[148] Wan M, Safavi T, Jauhar SK, et al. TnT-LLM: Text Mining at Scale with Large Language Models. arXiv:2403.12173; 2024. [TnT-LLM](https://arxiv.org/abs/2403.12173)

[149] Wang Z, Shang J, Zhong R. Goal-Driven Explainable Clustering via Language Descriptions. In: Proceedings of EMNLP 2023; 2023. p. 10626-10649. [GoalEx](https://aclanthology.org/2023.emnlp-main.657/)

[150] Zhang Y, Wang Z, Shang J. ClusterLLM: Large Language Models as a Guide for Text Clustering. In: Proceedings of EMNLP 2023; 2023. p. 13903-13920. [ClusterLLM](https://aclanthology.org/2023.emnlp-main.858/)

[151] Ziems C, Held W, Shaikh O, Chen J, Zhang Z, Yang D. Can Large Language Models Transform Computational Social Science? Computational Linguistics. 2024;50(1):237-291. doi:10.1162/coli_a_00502. [Can Large Language Models Transform Computational Social Science?](https://aclanthology.org/2024.cl-1.8/)

[152] Brown DW. pybiber. [pybiber on GitHub](https://github.com/browndw/pybiber) and [pybiber on PyPI](https://pypi.org/project/pybiber/)

[153] Jurgens D, et al. biberplus. [biberplus on GitHub](https://github.com/davidjurgens/biberplus) and [biberplus on PyPI](https://pypi.org/project/biberplus/)

[154] Nini A. Multidimensional Analysis Tagger (MAT), v1.3.3. [MAT on GitHub](https://github.com/andreanini/multidimensionalanalysistagger) and [MAT website](https://sites.google.com/site/multidimensionaltagger)

[155] Hansen L, et al. TextDescriptives. [textdescriptives on PyPI](https://pypi.org/project/textdescriptives/) and [TextDescriptives on GitHub](https://github.com/HLasse/textdescriptives)

[156] Zhu J, Jurgens D. Idiosyncratic but not Arbitrary: Learning Idiolects in Online Registers Reveals Distinctive yet Consistent Individual Styles. In: Proceedings of EMNLP 2021; 2021. p. 279-297. [Idiosyncratic but not Arbitrary](https://aclanthology.org/2021.emnlp-main.25/)

[157] Kredens K, Heini A, Pęzik P. Cross-genre individual variation in language use: A study of 112 idiolects. Fourth European Conference of the International Association of Forensic and Legal Linguistics, Porto; 2022. [Cross-genre individual variation in language use](https://research.aston.ac.uk/en/publications/cross-genre-individual-variation-in-language-use-a-study-of-112-i/)

[158] Wang Z, Tripto NI, Park S, Li Z, Zhou J. Catch Me If You Can? Not Yet: LLMs Still Struggle to Imitate the Implicit Writing Styles of Everyday Authors. Findings of EMNLP 2025. arXiv:2509.14543. [Catch Me If You Can? Not Yet](https://arxiv.org/abs/2509.14543)

[159] ductus project. Detecting AI-Generated Text: State of the Art (2026). Research notes; 2026. [detection-methods.md](https://github.com/thorwhalen/ductus/blob/main/misc/docs/research/detection-methods.md)
