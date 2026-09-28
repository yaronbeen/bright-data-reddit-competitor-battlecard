import json
import tool


def test_comments_request_uses_documented_dataset_and_bare_input_array(monkeypatch):
    captured = {}
    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self): return b'[{"url":"https://www.reddit.com/r/saas/comments/a1/x/comment/abc","post_url":"https://www.reddit.com/r/saas/comments/a1/x/","body":"Acme is cheaper than Beta"},{"url":"https://www.reddit.com/r/saas/comments/b2/y/comment/def","post_url":"https://www.reddit.com/r/saas/comments/b2/y/","body":"Acme is easier than Beta"}]'
    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["body"] = req.data
        captured["authorization"] = req.get_header("Authorization")
        return Response()
    monkeypatch.setattr(tool.urllib.request, "urlopen", fake_urlopen)
    rows = tool.collect_comments(["https://www.reddit.com/r/saas/comments/a1/x/","https://www.reddit.com/r/saas/comments/b2/y/"], "secret")
    assert "dataset_id=gd_lvzdpsdlw09j6t702" in captured["url"]
    assert b'[{"url":' in captured["body"]
    assert captured["authorization"] == "Bearer secret"
    assert [r["source_url"] for r in rows] == ["https://www.reddit.com/r/saas/comments/a1/x/","https://www.reddit.com/r/saas/comments/b2/y/"]


def test_extracts_comparative_claims_with_source_links():
    records = [dict(r, competitors={"Acme":["Acme"],"Northstar":["Northstar"]}) for r in tool.SAMPLE]
    rows = tool.compare(records)
    assert rows
    assert all(row["source_url"].startswith("https://www.reddit.com/") for row in rows)
    assert all(row["competitor"] for row in rows)


def test_uncompared_opinion_is_not_claim():
    assert tool.compare([{"url": "https://www.reddit.com/r/x/comments/1/a", "text": "I like this.", "competitors":["Acme","Beta"]}]) == []

def test_requires_explicit_names_and_ignores_unrelated_proper_nouns():
    record={"url":"https://www.reddit.com/r/x/comments/1/post/","text":"Jordan said Acme has better pricing than Beta."}
    assert tool.compare([record]) == []
    record["competitors"]=["Acme","Beta"]
    rows=tool.compare([record])
    assert rows[0]["competitor"] == "Acme"
    assert rows[0]["compared_with"] == "Beta"
    assert rows[0]["source_url"] == record["url"]

def test_comparison_evidence_requires_canonical_reddit_post_urls():
    base={"text":"Acme pricing is cheaper than Beta.","competitors":["Acme","Beta"]}
    credentialed_url="https://"+"user"+":"+"pass"+"@www.reddit.com/r/x/comments/1/post/"
    invalid_urls=(
        "https://www.reddit.com.evil.example/r/x/comments/1/post/",
        credentialed_url,
        "https://www.reddit.com/r/x/about/",
        "https://www.reddit.com:443/r/x/comments/1/post/",
    )
    for url in invalid_urls:
        try: tool.compare([{**base,"url":url}])
        except ValueError: pass
        else: assert False, f"noncanonical evidence URL was accepted: {url}"
    valid={**base,"url":"https://www.reddit.com/r/x/comments/1/post/"}
    assert tool.compare([valid])[0]["source_url"]==valid["url"]

def test_invalid_collected_source_url_cannot_override_valid_post_url():
    record={"url":"https://www.reddit.com/r/x/comments/1/post/","source_url":"https://www.reddit.com.evil.example/r/x/comments/1/post/","text":"Acme pricing beats Beta","competitors":["Acme","Beta"]}
    try: tool.compare([record])
    except ValueError: pass
    else: assert False, "malicious comment source URL must be rejected"

def test_comment_mapping_preserves_original_url_for_multiple_posts():
    urls=["https://www.reddit.com/r/x/comments/1/first/","https://www.reddit.com/r/x/comments/2/second/"]
    rows=tool.map_comments_to_posts([{"post_url":urls[0],"url":"https://www.reddit.com/r/x/comments/1/first/comment/c1","body":"Acme cheaper Beta"},{"post_url":urls[1],"url":"https://www.reddit.com/r/x/comments/2/second/comment/c2","body":"Acme pricing vs Beta"}],urls)
    assert [r["source_url"] for r in rows] == urls

def test_ambiguous_multi_url_comment_response_is_rejected():
    urls=["https://www.reddit.com/r/x/comments/1/first/","https://www.reddit.com/r/x/comments/2/second/"]
    try: tool.map_comments_to_posts([{"url":"https://www.reddit.com/r/x/comments/1/comment/c1","body":"Acme cheaper Beta"}],urls)
    except tool.BrightDataError as e: assert e.code == "ambiguous_source"
    else: assert False, "must not invent the parent post URL"

def test_comment_collection_rejects_duplicate_or_over_cap_inputs_without_request(monkeypatch):
    monkeypatch.setattr(tool.urllib.request,"urlopen",lambda *a,**k:(_ for _ in ()).throw(AssertionError("network called")))
    url="https://www.reddit.com/r/x/comments/1/post/"
    for urls in ([url,url],[f"https://www.reddit.com/r/x/comments/{i}/post/" for i in range(21)]):
        try: tool.collect_comments(urls,"secret")
        except ValueError: pass
        else: assert False, "invalid collection plan must fail before request"

def test_comments_malformed_and_202_responses_are_structured(monkeypatch):
    class Response:
        status=200
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def read(self): return b"not-json"
    response=Response(); monkeypatch.setattr(tool.urllib.request,"urlopen",lambda *a,**k:response)
    url="https://www.reddit.com/r/x/comments/1/post/"
    for status,code in ((200,"invalid_response"),(202,"async_snapshot")):
        response.status=status
        try: tool.collect_comments([url],"secret")
        except tool.BrightDataError as e: assert e.code==code
        else: assert False

def test_live_dry_run_needs_no_key_and_makes_no_request(monkeypatch,capsys):
    monkeypatch.delenv("BRIGHT_DATA_API_KEY",raising=False)
    monkeypatch.setattr(tool.urllib.request,"urlopen",lambda *a,**k:(_ for _ in ()).throw(AssertionError("network called")))
    assert tool.main(["curated_comparisons.json","--live","--dry-run"])==0
    assert json.loads(capsys.readouterr().out)["live_calls"]==0
