import tool


def test_comments_request_uses_documented_dataset_and_bare_input_array(monkeypatch):
    captured = {}
    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self): return b'[{"url":"https://www.reddit.com/r/saas/comments/a1/x/","body":"Acme is cheaper than Beta"}]'
    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["body"] = req.data
        captured["authorization"] = req.get_header("Authorization")
        return Response()
    monkeypatch.setattr(tool.urllib.request, "urlopen", fake_urlopen)
    rows = tool.collect_comments(["https://www.reddit.com/r/saas/comments/a1/x/"], "secret")
    assert "dataset_id=gd_lvzdpsdlw09j6t702" in captured["url"]
    assert b'[{"url":' in captured["body"]
    assert captured["authorization"] == "Bearer secret"
    assert rows[0]["url"].startswith("https://www.reddit.com/")


def test_extracts_comparative_claims_with_source_links():
    rows = tool.compare(tool.SAMPLE)
    assert rows
    assert all(row["source_url"].startswith("https://www.reddit.com/") for row in rows)
    assert all(row["competitor"] for row in rows)


def test_uncompared_opinion_is_not_claim():
    assert tool.compare([{"url": "https://www.reddit.com/r/x/comments/1/a", "text": "I like this."}]) == []
