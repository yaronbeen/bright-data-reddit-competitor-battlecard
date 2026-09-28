# Reddit Competitor Comparison Battlecard

Turn a marketer-curated set of public Reddit comparison/recommendation URLs and supplied comments into an evidence-linked matrix of explicit product-versus-product claims, tradeoffs, and objections. It helps a team decide which claims to verify before updating a sales battlecard or positioning.

## Who, why, decision

For product marketing and sales enablement teams who already know which competitors and public discussions they want reviewed. Input is curated records with `url`, `text`, and optional explicit `competitors`. Output keeps the quoted source text and URL alongside simple detected comparison dimensions. It does not discover prospects, identify people, mine general pain themes, or draft outreach.

## Workflow and synthetic example

The included two-record synthetic corpus says Northstar costs less and is easier to set up while Acme has better integrations and reporting. Run `python3 tool.py --sample`; the matrix retains the two Reddit source URLs and matched dimensions. Decision: verify the claims against product evidence and decide whether a sales battlecard needs an update. These invented examples are not market findings.

## Quick start

```bash
python3 tool.py --sample
python3 tool.py curated_comparisons.json battlecard.json
python3 -m pytest -q
```

Offline records are JSON objects containing a canonical public Reddit `url`, curated `text`, and optional `competitors` list. For live mode, provide JSON records with the selected post URLs; the CLI collects public comments for those URLs, at most 20 per synchronous request:

```bash
python3 tool.py curated_comparisons.json battlecard.json --live --dry-run
BRIGHT_DATA_API_KEY="your-key" python3 tool.py curated_comparisons.json battlecard.json --live
```

The current [Bright Data Reddit API docs](https://docs.brightdata.com/products/scrapers/reddit/introduction) document Comments dataset `gd_lvzdpsdlw09j6t702`, URL collection, sync requests up to 20 URLs, and pay-per-successful-record pricing. If Bright Data returns `202`, the tool reports the snapshot response rather than treating it as comments. Live collection is opt-in and may incur charges; no live request runs in tests or CI.

## Outputs and caveats

`battlecard.json` contains source-linked comparison rows with competitor names, observed dimensions, and text evidence, plus a human-review decision. Detection is heuristic and can miss paraphrases or misread capitalization. Reddit claims are unverified opinions, not product facts. Curated selection is biased by design; no broad prevalence or sentiment estimate is made.

## Differentiation

This is a narrow battlecard evidence extractor, not `bright-data-reddit-outreach` or `hand-raisers` lead discovery, not `bright-data-reddit-demand-radar` broad pain clustering, and not person identification or outreach. Its unit of analysis is an explicit comparison claim and its decision is whether a sales battlecard statement warrants human verification.

## Safety and FAQ

Use only public material you are authorized to process. No author handles, profiles, lead lists, messaging, or posting are emitted. Live calls are disabled unless an exact request workflow has been verified; no live call occurs in tests. Bright Data account access and current [pricing](https://brightdata.com/pricing/web-scraper) apply when collection is performed separately. `.env` is ignored; never commit keys.

**Can the matrix be pasted directly into battlecards?** Treat it as a review queue; verify every claim with product evidence first.

**Does it find competitors or threads?** No. The comparison set and URLs are user-curated.

MIT License. Independent demonstration; not affiliated with or endorsed by Bright Data.
