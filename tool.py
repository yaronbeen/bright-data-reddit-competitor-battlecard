"""Build an evidence-linked matrix from user-curated Reddit comparison material."""
import argparse, json, re, sys

SAMPLE=[{"url":"https://www.reddit.com/r/saas/comments/a1/compare/","text":"We switched from Acme to Northstar. Northstar costs less, but Acme has better integrations."},{"url":"https://www.reddit.com/r/startups/comments/b2/tools/","text":"Acme vs Northstar: Northstar is easier to set up; Acme has more reporting."}]
PATTERNS=[("cost","costs less|cheaper|pricing|expensive"),("ease_of_use","easier|simpler|hard to use"),("integrations","integrations|integrates"),("reporting","reporting|analytics")]
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
        if a.live: raise ValueError("Live Reddit collection is not implemented here; supply the curated public URLs and records. No request made.")
        data=SAMPLE if a.sample else json.load(open(a.input,encoding="utf-8"))
        if a.dry_run: print(json.dumps({"records":len(data),"live_calls":0})); return 0
        result={"comparison_matrix":compare(data),"decision":"Review supported claims before updating a sales battlecard.","limits":["Only explicit comparative statements in the curated sample are surfaced.","Not market-wide prevalence, verified product truth, lead discovery, or outreach."]}
        json.dump(result,open(a.output,"w",encoding="utf-8"),indent=2); print(json.dumps({"output":a.output,"rows":len(result["comparison_matrix"])})); return 0
    except (ValueError,OSError,KeyError) as e: print(str(e),file=sys.stderr); return 1
if __name__=="__main__": raise SystemExit(main())
