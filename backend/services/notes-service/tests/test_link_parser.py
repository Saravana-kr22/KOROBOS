"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Unit tests for the wiki-link parser.
"""

from app.services.link_parser import extract_wiki_links


def test_single_link():
    assert extract_wiki_links("See [[Machine Learning]].") == ["Machine Learning"]


def test_multiple_links():
    result = extract_wiki_links("[[Deep Learning]] builds on [[Machine Learning]].")
    assert result == ["Deep Learning", "Machine Learning"]


def test_deduplication():
    result = extract_wiki_links("[[Python]] and [[Python]] again.")
    assert result == ["Python"]


def test_no_links():
    assert extract_wiki_links("Plain text with no links.") == []


def test_empty_string():
    assert extract_wiki_links("") == []


def test_whitespace_normalisation():
    result = extract_wiki_links("[[  Spaced   Title  ]]")
    assert result == ["Spaced Title"]


def test_nested_brackets_not_matched():
    # [[[deep]]] should not match — outer brackets incomplete
    result = extract_wiki_links("[[[deep]]]")
    assert result == ["deep"]


def test_link_at_start_and_end():
    result = extract_wiki_links("[[Start]] middle [[End]]")
    assert result == ["Start", "End"]


def test_multiline_content():
    content = "# Notes\n\n[[AI]] is interesting.\n\nSee also [[Neural Networks]]."
    result = extract_wiki_links(content)
    assert result == ["AI", "Neural Networks"]


def test_order_preserved():
    result = extract_wiki_links("[[Z]] [[A]] [[M]]")
    assert result == ["Z", "A", "M"]
