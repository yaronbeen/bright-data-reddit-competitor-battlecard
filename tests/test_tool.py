import tool


def test_extracts_comparative_claims_with_source_links():
    rows = tool.compare(tool.SAMPLE)
    assert rows
    assert all(row["source_url"].startswith("https://www.reddit.com/") for row in rows)
    assert all(row["competitor"] for row in rows)


def test_uncompared_opinion_is_not_claim():
    assert tool.compare([{"url": "https://www.reddit.com/r/x/comments/1/a", "text": "I like this."}]) == []
