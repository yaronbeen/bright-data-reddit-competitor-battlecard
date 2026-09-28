# Reddit Competitor Comparison Battlecard

Turn a marketer-curated set of public Reddit comparison/recommendation URLs and supplied comments into an evidence-linked matrix of explicit product-versus-product claims, tradeoffs, and objections. It helps a team decide which claims to verify before updating a sales battlecard or positioning.

## Who, why, decision

For product marketing and sales enablement teams who already know which competitors and public discussions they want reviewed. Input records use `url`, `text`, and an explicit `competitors` list (names or `{name, aliases}` records). Name matching uses only those supplied names/aliases; capitalization is never used to guess companies. Source links must be HTTPS `www.reddit.com/r/<subreddit>/comments/<post-id>/<slug>` permalinks with a valid subreddit, alphanumeric post ID, and nonempty URL-safe title slug. The exact host is required; credentials, ports, query strings, and fragments are rejected. The same validation applies to offline input and collected comment evidence; invalid links fail closed. Each comparison row retains the validated source post URL.

## Workflow and synthetic example

The included two-record synthetic corpus says Northstar costs less and is easier to set up while Acme has better integrations and reporting. Run `python3 tool.py --sample`; the matrix retains the two Reddit source URLs and matched dimensions. Decision: verify the claims against product evidence and decide whether a sales battlecard needs an update. These invented examples are not market findings.

## Quick start

```bash
python3 tool.py --sample
python3 tool.py curated_comparisons.json battlecard.json
python3 -m pytest -q
```

Offline JSON is an array of records with a canonical public Reddit `url`, curated `text`, and explicit `competitors` list. Live JSON may instead be an object with a `competitors` list and a `posts` array of selected post URLs, or each record may carry the same competitor list. The CLI validates the whole set before making one bounded Comments dataset request (maximum 20 URLs):

```bash
python3 tool.py curated_comparisons.json battlecard.json --live --dry-run
BRIGHT_DATA_API_KEY="your-key" python3 tool.py curated_comparisons.json battlecard.json --live
```

The current [Bright Data Reddit API docs](https://docs.brightdata.com/products/scrapers/reddit/introduction) document Comments dataset `gd_lvzdpsdlw09j6t702`, URL collection, sync requests up to 20 URLs, and pay-per-successful-record pricing. User-supplied post URLs must be unique in offline and live input; duplicates fail before a request or output. Provider comments are deduplicated by comment ID and permalink, or by a documented-in-output content key from parent post URL, normalized body, and timestamp when IDs/links are absent. Duplicate identities or records lacking a stable identity fail closed. When multi-URL comment records lack a parent post URL that maps to a requested URL, the CLI rejects the response instead of assigning an uncertain source. A `202` snapshot is reported as structured error; no retries occur. Live collection is opt-in and may incur charges; no live request runs in tests or CI.

## Outputs and caveats

`battlecard.json` contains source-linked comparison rows with explicitly supplied competitor names, observed dimensions, and text evidence, plus a human-review decision. Phrase detection is heuristic and can miss paraphrases. Reddit claims are unverified opinions, not product facts. Curated selection is biased by design; no broad prevalence or sentiment estimate is made.

## Differentiation

This is a narrow battlecard evidence extractor, not `bright-data-reddit-outreach` or `hand-raisers` lead discovery, not `bright-data-reddit-demand-radar` broad pain clustering, and not person identification or outreach. Its unit of analysis is an explicit comparison claim and its decision is whether a sales battlecard statement warrants human verification.

## Safety and FAQ

Use only public material you are authorized to process. No author handles, profiles, lead lists, messaging, or posting are emitted. `--live` is required for collection; dry-run makes no request and requires no key. API errors are sanitized/structured and billable requests are never retried automatically. Check Bright Data account access and current [pricing](https://brightdata.com/pricing/web-scraper). `.env` is ignored; never commit keys.

**Can the matrix be pasted directly into battlecards?** Treat it as a review queue; verify every claim with product evidence first.

**Does it find competitors or threads?** No. The comparison set and URLs are user-curated.

MIT License. Independent demonstration; not affiliated with or endorsed by Bright Data.
