"""Build an evidence-linked matrix from user-curated Reddit comparison material."""
import argparse, hashlib, json, os, re, sys, urllib.error, urllib.parse, urllib.request

SAMPLE=[{"url":"https://www.reddit.com/r/saas/comments/a1/compare/","text":"We switched from Acme to Northstar. Northstar costs less, but Acme has better integrations.","competitors":["Acme","Northstar"]},{"url":"https://www.reddit.com/r/startups/comments/b2/tools/","text":"Acme vs Northstar: Northstar is easier to set up; Acme has more reporting.","competitors":["Acme","Northstar"]}]
PATTERNS=[("cost","costs less|cheaper|pricing|expensive"),("ease_of_use","easier|simpler|hard to use"),("integrations","integrations|integrates"),("reporting","reporting|analytics")]
class BrightDataError(Exception):
    def __init__(self,code,message): self.code=code; super().__init__(message)

def map_comments_to_posts(rows, requested_urls):
    mapped=[]; seen=set()
    for row in rows:
        parent=row.get("post_url") or row.get("parent_post_url") or row.get("source_url")
        if parent not in requested_urls:
            if not parent and row.get("url") in requested_urls: parent=row["url"]
            elif not parent and len(requested_urls)==1: parent=requested_urls[0]
            else: raise BrightDataError("ambiguous_source","Comment response lacked a matching parent post URL")
        text=row.get("body") or row.get("comment_text") or row.get("text") or row.get("description") or ""
        comment_id=row.get("comment_id") or row.get("id")
        comment_url=row.get("comment_url") or row.get("permalink") or row.get("link") or row.get("url")
        if comment_url==parent: comment_url=None
        keys=[]
        if comment_id not in (None,""): keys.append(("id",str(comment_id)))
        if isinstance(comment_url,str) and comment_url: keys.append(("url",comment_url))
        if keys:
            if any(key in seen for key in keys): raise BrightDataError("duplicate_comment","Bright Data returned duplicate comment evidence")
            seen.update(keys)
            identity="|".join(f"{kind}:{value}" for kind,value in keys)
        else:
            created_at=row.get("created_at") or row.get("date_posted") or row.get("timestamp") or row.get("created_utc")
            if not isinstance(text,str) or not text.strip() or not created_at: raise BrightDataError("unstable_comment","Comment record lacked an ID, permalink, or body/timestamp content key")
            normalized_text=" ".join(text.split())
            digest=hashlib.sha256((parent+"\0"+normalized_text+"\0"+str(created_at)).encode()).hexdigest()
            identity="content:"+digest; key=("content",parent,digest)
            if key in seen: raise BrightDataError("duplicate_comment","Bright Data returned duplicate comment evidence")
            seen.add(key)
        mapped.append({**row,"comment_id":str(comment_id) if comment_id not in (None,"") else None,"comment_url":comment_url,"comment_identity":identity,"source_url":parent,"text":text})
    return mapped

def collect_comments(urls, key):
    if not 1 <= len(urls) <= 20: raise ValueError("Comments collection accepts 1-20 post URLs per sync request")
    if not isinstance(key,str) or not key: raise ValueError("Bright Data API key is required")
    if any(not isinstance(u,str) for u in urls): raise ValueError("Post URLs must be strings")
    if len(set(urls))!=len(urls): raise ValueError("Post URL inputs must be unique to avoid duplicate billable records")
    if any(not valid_post_url(u) for u in urls): raise ValueError("Only canonical public Reddit post URLs are accepted")
    query=urllib.parse.urlencode({"dataset_id":"gd_lvzdpsdlw09j6t702","format":"json"})
    req=urllib.request.Request("https://api.brightdata.com/datasets/v3/scrape?"+query,data=json.dumps([{"url":u} for u in urls]).encode(),headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=75) as response:
        payload=response.read().decode()
        if response.status==202: raise BrightDataError("async_snapshot","Bright Data returned an async snapshot; no comments were treated as returned")
        try: result=json.loads(payload)
        except json.JSONDecodeError as e: raise BrightDataError("invalid_response","Bright Data response was not valid JSON") from e
        if not isinstance(result,list) or any(not isinstance(row,dict) for row in result): raise BrightDataError("invalid_response","Bright Data response did not match the expected record array")
        return map_comments_to_posts(result,urls)

def valid_post_url(url):
    if not isinstance(url,str) or "?" in url or "#" in url: return False
    try: parts=urllib.parse.urlsplit(url)
    except (TypeError,ValueError): return False
    match=re.fullmatch(r"/r/[A-Za-z0-9_]+/comments/[A-Za-z0-9]+/((?:[A-Za-z0-9._~-]|%[0-9A-Fa-f]{2})+)/?",parts.path)
    return parts.scheme=="https" and parts.netloc=="www.reddit.com" and bool(match) and match.group(1) not in (".","..")

def aliases_for(competitors):
    if isinstance(competitors,dict): competitors=[{"name":name,"aliases":aliases if isinstance(aliases,list) else []} for name,aliases in competitors.items()]
    if not isinstance(competitors,list): raise ValueError("Competitors must be an explicit list or name-to-alias mapping")
    result=[]
    for item in competitors:
        spec={"name":item,"aliases":[]} if isinstance(item,str) else item
        if not isinstance(spec,dict) or not isinstance(spec.get("name"),str) or not spec["name"].strip(): raise ValueError("Each competitor needs an explicit name")
        aliases=spec.get("aliases",[])
        if not isinstance(aliases,list): raise ValueError("Competitor aliases must be an array of strings")
        result.append({"name":spec["name"].strip(),"aliases":[spec["name"].strip(),*[a for a in aliases if isinstance(a,str) and a.strip()]]})
    return result
def compare(records, allow_multiple_comments=False):
    rows=[]; seen_sources=set(); seen_identities=set()
    for r in records:
        source=r.get("source_url") or r.get("url")
        if not valid_post_url(source): raise ValueError("Every comparison record requires a canonical Reddit post evidence URL")
        if not allow_multiple_comments and source in seen_sources: raise ValueError("Duplicate post evidence URL in comparison input")
        seen_sources.add(source)
        identity=r.get("comment_identity") or r.get("comment_id") or r.get("comment_url")
        if allow_multiple_comments:
            if not identity: raise ValueError("Collected comparison record lacks a stable comment identity")
            if identity in seen_identities: raise BrightDataError("duplicate_comment","Duplicate comment identity reached comparison output")
            seen_identities.add(identity)
        text=r.get("text",""); found=[]
        for competitor in aliases_for(r.get("competitors",[])):
            if any(re.search(r"(?<!\w)"+re.escape(alias)+r"(?!\w)",text,re.I) for alias in competitor["aliases"]): found.append(competitor["name"])
        matched=[label for label,pattern in PATTERNS if re.search(pattern,text,re.I)]
        if len(found)>=2 and matched:
            row={"competitor":found[0],"compared_with":found[1],"observed_dimensions":matched,"quoted_evidence":text,"source_url":source}
            if identity: row["comment_identity"]=identity
            if r.get("comment_id"): row["comment_id"]=r["comment_id"]
            if r.get("comment_url"): row["comment_url"]=r["comment_url"]
            rows.append(row)
    return rows
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("input",nargs="?"); p.add_argument("output",nargs="?",default="battlecard.json"); p.add_argument("--sample",action="store_true"); p.add_argument("--live",action="store_true"); p.add_argument("--dry-run",action="store_true"); p.add_argument("--competitors",help="Comma-separated explicit names for live collection"); a=p.parse_args(argv)
    try:
        if a.sample and a.live: raise ValueError("--sample is offline-only and cannot be combined with --live")
        if a.sample: data=SAMPLE
        elif a.input: data=json.load(open(a.input,encoding="utf-8"))
        else: p.error("Supply curated JSON input or use --sample")
        if isinstance(data,dict): records=data.get("posts",[]); competitors=data.get("competitors",[])
        else: records=data; competitors=[]
        if not isinstance(records,list) or any(not isinstance(r,dict) or not isinstance(r.get("url"),str) for r in records): raise ValueError("Input must contain an array of records with Reddit post URLs")
        if a.competitors: competitors=[v.strip() for v in a.competitors.split(",") if v.strip()]
        if not competitors and records: competitors=records[0].get("competitors",[])
        if a.live and records and any(r.get("competitors",competitors)!=records[0].get("competitors",competitors) for r in records): raise ValueError("Competitor names/aliases must be consistent across selected records")
        urls=[r["url"] for r in records]
        if len(set(urls))!=len(urls): raise ValueError("Input post URLs must be unique to prevent duplicate evidence")
        if a.live:
            if not 1<=len(urls)<=20 or any(not valid_post_url(u) for u in urls): raise ValueError("Live mode accepts 1-20 unique canonical Reddit post URLs")
            if len(aliases_for(competitors))<2: raise ValueError("Provide at least two explicit competitors with --competitors or in input JSON")
        for record in records:
            if competitors: record["competitors"]=competitors
        if a.dry_run: print(json.dumps({"records":len(records),"live_calls":0,"dataset_id":"gd_lvzdpsdlw09j6t702" if a.live else None})); return 0
        if a.live:
            key=os.environ.get("BRIGHT_DATA_API_KEY")
            if not key: raise ValueError("Set BRIGHT_DATA_API_KEY in the environment")
            fetched=collect_comments(urls,key)
            data=[]
            for row in fetched:
                original=next((r for r in records if r["url"]==row["source_url"]),{})
                data.append({**row,"competitors":original.get("competitors",competitors)})
        result={"comparison_matrix":compare(data if a.live else records,allow_multiple_comments=a.live),"decision":"Review supported claims before updating a sales battlecard.","limits":["Only explicit comparative statements among user-named competitors in the curated sample are surfaced.","Not market-wide prevalence, verified product truth, lead discovery, or outreach."]}
        json.dump(result,open(a.output,"w",encoding="utf-8"),indent=2); print(json.dumps({"output":a.output,"rows":len(result["comparison_matrix"])})); return 0
    except BrightDataError as e: print(json.dumps({"error":{"code":e.code,"message":str(e),"retryable":False}}),file=sys.stderr); return 1
    except urllib.error.HTTPError as e: print(json.dumps({"error":{"code":"http_error","message":f"Bright Data returned HTTP {e.code}","retryable":False}}),file=sys.stderr); return 1
    except urllib.error.URLError: print(json.dumps({"error":{"code":"transport_error","message":"Bright Data request failed at transport level","retryable":False}}),file=sys.stderr); return 1
    except (ValueError,OSError,KeyError,RuntimeError) as e: print(json.dumps({"error":{"code":"input_error","message":str(e),"retryable":False}}),file=sys.stderr); return 1
if __name__=="__main__": raise SystemExit(main())
