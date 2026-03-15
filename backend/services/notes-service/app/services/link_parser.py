"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Wiki-link parser — detects [[Note Title]] patterns in markdown content.
"""

import re

# Matches [[Any Note Title]] — greedy inside, no nested brackets
_WIKI_LINK_RE = re.compile(r"\[\[([^\[\]]+?)\]\]")


def extract_wiki_links(content_md: str) -> list[str]:
    """Return a deduplicated list of note titles found in [[...]] wiki-links.

    Example:
        >>> extract_wiki_links("See [[Machine Learning]] and [[Deep Learning]].")
        ['Machine Learning', 'Deep Learning']
    """
    titles = _WIKI_LINK_RE.findall(content_md)
    # Normalise whitespace and deduplicate while preserving first-seen order
    seen: set[str] = set()
    result: list[str] = []
    for raw in titles:
        title = " ".join(raw.split())
        if title and title not in seen:
            seen.add(title)
            result.append(title)
    return result
