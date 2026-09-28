"""Screening: keeping machine-written text out of a model of a person. Optional.

A model of how someone writes should be built from what they wrote. Since late
2022 a share of what people send has been drafted or polished by a language
model, so a corpus can be screened before it is used. There are four tiers, and
what each costs is stated before anything runs:

========  =====================================================================
tier      what it does and what it costs
========  =====================================================================
date      Keeps only texts dated before a cutoff. Free and instant. The most
          reliable of the four, because no detector is involved.
cheap     ``ductus`` deterministic detectors: stock phrases, mechanical traces,
          sentence shapes, rhythm. No model, no network; milliseconds a text.
heavy     ``ductus`` model-based detectors (Fast-DetectGPT, Binoculars) on this
          machine. Needs torch and transformers, downloads small open models on
          first use, and takes processor time that is measured on a sample first.
agent     An agent reads the texts and judges them. Costs model tokens in
          proportion to the corpus. Not run from here; see the penlike-source skill.
========  =====================================================================

No detector is reliable on a single short text, and every one of them accuses
some human writing. A flagged text is excluded from the model, never deleted, and
can be put back. The honest default for a personal model is the ``date`` tier.

>>> sorted(TIERS)
['agent', 'cheap', 'date', 'heavy']
>>> docs = [{"id": "a", "date": "2021-05-01T00:00:00+00:00", "text": "x", "words": 1},
...         {"id": "b", "date": "2024-05-01T00:00:00+00:00", "text": "y", "words": 1}]
>>> screen(docs, tier="date")["flagged"]
['b']
"""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from penlike.base import AI_ERA_START, PenlikeError, parse_date

__all__ = ["TIERS", "screen"]

TIERS: dict[str, dict[str, str]] = {
    "date": {
        "does": "keeps only texts dated before the cutoff; undated texts are reported, not flagged",
        "costs": "nothing: no model, no network, instant",
        "needs": "dates on the documents",
    },
    "cheap": {
        "does": "flags texts whose wording, mechanics, sentence shapes and rhythm lean machine-written",
        "costs": "no model and no network; regular expressions and arithmetic, milliseconds per text",
        "needs": "pip install 'penlike[screen]'",
    },
    "heavy": {
        "does": "adds model-based detectors, which compare passages inside one text and so only help on long texts",
        "costs": "processor time on this machine (timed on a sample first) and a one-time model download; no fee",
        "needs": "pip install 'penlike[screen]' 'ductus[local]'",
    },
    "agent": {
        "does": "an agent reads each text and records a judgment",
        "costs": "model tokens in proportion to the size of the corpus, at your provider's price",
        "needs": "an agent; follow the penlike-source skill, then record with: penlike exclude",
    },
}
_HEAVY_DETECTORS = ("tells", "forensic", "rhetoric", "rhythm", "fast-detect-gpt", "binoculars")
_FLAGGED_LABEL = "leans-machine"


def _ductus_gauge(tier: str) -> Callable[[str], Mapping[str, Any]]:
    try:
        import ductus
        from ductus.detect import DEFAULT_DETECTORS, detectors_from
    except ImportError:
        raise PenlikeError(
            f"the {tier} tier needs the ductus package:\n    {TIERS[tier]['needs']}"
        ) from None
    names = _HEAVY_DETECTORS if tier == "heavy" else DEFAULT_DETECTORS
    detectors, _ = detectors_from(list(names))

    def gauge(text: str) -> Mapping[str, Any]:
        try:
            verdict = ductus.gauge(text, detectors=detectors).document
        except ImportError as error:
            raise PenlikeError(
                f"the heavy tier could not load its models ({error}):\n"
                f"    {TIERS['heavy']['needs']}"
            ) from None
        return {
            "label": verdict.label,
            "lean": round(verdict.lean, 3),
            "strength": round(verdict.strength, 3),
        }

    return gauge


def screen(
    docs: Sequence[Mapping[str, Any]],
    *,
    tier: str = "date",
    cutoff: str = AI_ERA_START,
    run: bool = False,
    sample: int = 5,
    gauge: Callable[[str], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Screen documents at one tier. Without ``run`` it only states the cost.

    For the ``cheap`` and ``heavy`` tiers a plain call times the detector on
    ``sample`` texts and extrapolates, so the length of the full run is known
    before it starts. ``gauge`` replaces the detector (a function from text to a
    mapping with a ``label``); it is how tests run without ductus.

    Returns ``flagged`` (document ids) and ``findings`` (per document) when the
    screening ran, and the ``plan`` in every case.
    """
    if tier not in TIERS:
        raise PenlikeError(f"no tier named {tier!r}; the tiers are: {', '.join(TIERS)}")
    live = [doc for doc in docs if not doc.get("excluded")]
    plan: dict[str, Any] = {
        "tier": tier,
        **TIERS[tier],
        "documents": len(live),
        "words": sum(doc.get("words", 0) for doc in live),
    }
    if tier == "agent":
        return {"plan": plan, "ran": False, "flagged": [], "findings": {}}

    if tier == "date":
        limit = parse_date(cutoff)
        undated = [doc["id"] for doc in live if not doc.get("date")]
        flagged = [doc["id"] for doc in live if doc.get("date") and doc["date"] >= limit]
        plan.update(cutoff=limit, undated=len(undated))
        findings = {doc_id: {"label": f"dated on or after {limit[:10]}"} for doc_id in flagged}
        return {
            "plan": plan,
            "ran": True,
            "flagged": flagged,
            "findings": findings,
            "undated": undated,
        }

    gauge = gauge or _ductus_gauge(tier)
    if not run:
        tried = live[: max(sample, 0)]
        started = time.perf_counter()
        for doc in tried:
            gauge(doc["text"])
        elapsed = time.perf_counter() - started
        if tried:
            words = sum(doc.get("words", 0) for doc in tried) or 1
            plan["sample"] = {"documents": len(tried), "seconds": round(elapsed, 2)}
            plan["estimated_seconds"] = round(elapsed * plan["words"] / words, 1)
        return {"plan": plan, "ran": False, "flagged": [], "findings": {}}

    findings = {doc["id"]: dict(gauge(doc["text"])) for doc in live}
    flagged = [doc_id for doc_id, found in findings.items() if found.get("label") == _FLAGGED_LABEL]
    return {"plan": plan, "ran": True, "flagged": flagged, "findings": findings}
