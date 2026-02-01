from app.rag_utils import (
    tokenize,
    keyword_score,
    simple_embed,
    cosine_similarity,
    build_context_snippets,
    contains_sensitive_identifiers,
    format_context_prompt,
)


def test_tokenize_filters_tokens():
    assert tokenize("Hello, world!") == ["hello", "world"]


def test_keyword_score_overlap():
    score = keyword_score(["a", "b"], ["b", "c"])
    assert score == 0.5


def test_simple_embed_length():
    vector = simple_embed("test", dim=8)
    assert len(vector) == 8


def test_cosine_similarity_bounds():
    a = [1.0, 0.0]
    b = [1.0, 0.0]
    assert cosine_similarity(a, b) == 1.0


def test_build_context_snippets_respects_limit():
    hits = [
        {"collection": "c1", "id": "1", "content": "alpha"},
        {"collection": "c2", "id": "2", "content": "beta"},
    ]
    snippets = build_context_snippets(hits, max_tokens=2)
    assert len(snippets) == 1


def test_contains_sensitive_identifiers():
    assert contains_sensitive_identifiers("ssn 123456789") is True
    assert contains_sensitive_identifiers("safe text") is False


def test_format_context_prompt():
    prompt = format_context_prompt(["[c:1] text"], "query")
    assert "query" in prompt
