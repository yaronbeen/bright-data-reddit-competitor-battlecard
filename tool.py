"""Build an evidence-linked matrix from user-curated Reddit comparison material."""
import argparse, json, os, re, sys, urllib.error, urllib.parse, urllib.request

SAMPLE=[{"url":"https://www.reddit.com/r/saas/comments/a1/compare/","text":"We switched from Acme to Northstar. Northstar costs less, but Acme has better integrations."},{"url":"https://www.reddit.com/r/startups/comments/b2/tools/","text":"Acme vs Northstar: Northstar is easier to set up; Acme has more reporting."}]
PATTERNS=[("cost","costs less|cheaper|pricing|expensive"),("ease_of_use","easier|simpler|hard to use"),("integrations","integrations|integrates"),("reporting","reporting|analytics")]
def collect_comments(urls, key):
    if not 1 <= len(urls) <= 20: raise ValueError("Comments collection accepts 1-20 post URLs per sync request")
    if any(not u.startswith("https://www.reddit.com/") for u in urls): raise ValueError("Only canonical public Reddit URLs are accepted")
    query=urllib.parse.urlencode({"dataset_id":"gd_lvzdpsdlw09j6t702","format":"json"})
    req=urllib.request.Request("https://api.brightdata.com/datasets/v3/scrape?"+query,data=json.dumps([{"url":u} for u in urls]).encode(),headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=75) as response:
        payload=response.read().decode()
        if response.status==202: raise RuntimeError("Bright Data returned async snapshot; comments sync call returned no comment records")
        result=json.loads(payload)
        for row in result:
            row["source_url"]=row.get("post_url") or row.get("url") or urls[0]
            row["text"]=row.get("body") or row.get("comment_text") or row.get("text") or row.get("description") or ""
        return result
def compare(records):
    rows=[]
    for r in records:
        text=r.get("text",""); names=r.get("competitors",[])
        if not names: names=re.findall(r"\b[A-Z][A-Za-z0-9_-]{2,}\b",text)
        names=list(dict.fromkeys(n for n in names if n.lower() not in {"we","from","northstar"} or n=="Northstar"))
        matched=[label for label,pattern in PATTERNS if re.search(pattern,text,re.I)]
        if len(names)>=2 and matched:
            rows.append({"competitor":names[0],"compared_with":names[1],"observed_dimensions":matched,"quoted_evidence":text,"source_url":r.get("url","")})
    return rows
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("input",nargs="?"); p.add_argument("output",nargs="?",default="battlecard.json"); p.add_argument("--sample",action="store_true"); p.add_argument("--live",action="store_true"); p.add_argument("--dry-run",action="store_true"); a=p.parse_args()
    try:
        data=SAMPLE if a.sample else json.load(open(a.input,encoding="utf-8"))
        if a.dry_run: print(json.dumps({"records":len(data),"live_calls":0,"dataset_id":"gd_lvzdpsdlw09j6t702" if a.live else None})); return 0
        if a.live:
            key=os.environ.get("BRIGHT_DATA_API_KEY")
            if not key: raise ValueError("Set BRIGHT_DATA_API_KEY in the environment")
            data=collect_comments([r["url"] for r in data],key)
        result={"comparison_matrix":compare(data),"decision":"Review supported claims before updating a sales battlecard.","limits":["Only explicit comparative statements in the curated sample are surfaced.","Not market-wide prevalence, verified product truth, lead discovery, or outreach."]}
        json.dump(result,open(a.output,"w",encoding="utf-8"),indent=2); print(json.dumps({"output":a.output,"rows":len(result["comparison_matrix"])})); return 0
    except (ValueError,OSError,KeyError,urllib.error.URLError,RuntimeError) as e: print(str(e),file=sys.stderr); return 1
if __name__=="__main__": raise SystemExit(main())
