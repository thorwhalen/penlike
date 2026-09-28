"""A fictional corpus for the tests: one invented author, three ways of writing.

Every sentence here was made up for the tests. No text in this repository comes
from a real person's correspondence, and none may: a model of a real writer is
private data and lives in the user's data folder.
"""

from __future__ import annotations

import random

AUTHOR = "quinn@example.org"
FRIEND = "mira@example.org"
TEAM = [
    "tomas@example.org",
    "ines@example.org",
    "pavel@example.org",
    "lena@example.org",
    "omar@example.org",
    "yuki@example.org",
]

_CASUAL = [
    "ok so I tried it and it broke again.",
    "no idea why, honestly.",
    "can you take a look?",
    "I think it's the cache.",
    "works on my side though!",
    "let's talk tomorrow.",
    "that's odd, isn't it?",
    "I'll push a fix tonight.",
    "don't worry about the tests yet.",
    "it's fine, really.",
    "did you see the log?",
    "we're close I think.",
    "I can't reproduce it anymore.",
    "so that's that.",
    "want me to ping Tomas?",
]
_FORMAL = [
    "Please find below the summary of the quarterly planning session.",
    "The committee reviewed the proposed schedule and approved it without amendment.",
    "We would be grateful if every team could confirm its attendance before Friday.",
    "The revised budget will be circulated once the figures have been verified.",
    "Any objection should be addressed to the coordination office in writing.",
    "The next session will take place in the main building on the second floor.",
    "Participants are reminded that the agenda is fixed two weeks in advance.",
    "A detailed report will follow as soon as the minutes have been validated.",
    "We thank all contributors for the considerable effort invested in this work.",
    "The deadline for submissions remains unchanged despite the recent delays.",
]
_TECHNICAL = [
    "The loader reads the whole file before it parses the header.",
    "Calling `load(path)` twice returns the same object, which hides the bug.",
    "I would rather pass the store as an argument than import it.",
    "The failing case is an empty mapping; see the traceback below.",
    "We could cache the result, but then invalidation becomes our problem.",
    "This changes the public signature, so it needs a deprecation step.",
    "The test passes locally and fails on the runner with the older version.",
    "A generator would avoid holding every record in memory.",
    "What should happen when the key is missing: raise, or return the default?",
    "I checked the three callers and none of them relies on the order.",
]


def fictional_corpus(*, seed: int = 7, per_register: int = 14) -> list[dict]:
    """Documents by one invented author: casual mail, formal mail, technical posts."""
    rng = random.Random(seed)
    docs = []
    for index in range(per_register):
        day = f"2019-{1 + index % 12:02d}-{1 + index:02d}"
        casual = " ".join(rng.sample(_CASUAL, rng.randint(3, 6)))
        docs.append(
            {
                "text": f"Hi Mira,\n\n{casual}\n\nCheers,\nQuinn",
                "date": day,
                "channel": "email",
                "to": [FRIEND],
                "author": AUTHOR,
                "is_self": True,
            }
        )
        formal = " ".join(rng.sample(_FORMAL, rng.randint(4, 7)))
        docs.append(
            {
                "text": f"Dear all,\n\n{formal}\n\nBest regards,\nQuinn Avery",
                "date": day,
                "channel": "email",
                "to": TEAM,
                "author": AUTHOR,
                "is_self": True,
            }
        )
        technical = rng.sample(_TECHNICAL, rng.randint(4, 7))
        body = " ".join(technical[:3]) + "\n\n- " + "\n- ".join(technical[3:])
        docs.append(
            {
                "text": body,
                "date": day,
                "channel": "github",
                "audience": "public",
                "reply": index % 2 == 0,
                "author": "quinn",
                "is_self": True,
                "url": f"https://example.org/threads/{index}",
            }
        )
    return docs
