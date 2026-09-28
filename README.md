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

Records are JSON objects containing a canonical public Reddit `url`, curated `text`, and optional `competitors` list. The offline tool performs no network calls. `--live` currently fails closed; collect only those curated public URLs using an explicitly reviewed workflow and provide the selected records. Current Bright Data docs document Posts dataset `gd_lvz8ah06191smkebj4`, Comments dataset `gd_lvzdpsdlw09j6t702`, and up to 20 URL inputs for sync collection ([Reddit API](https://docs.brightdata.com/products/scrapers/reddit/introduction)). Comments collection is billable and is intentionally not triggered by this CLI.

## Outputs and caveats

`battlecard.json` contains source-linked comparison rows with competitor names, observed dimensions, and text evidence, plus a human-review decision. Detection is heuristic and can miss paraphrases or misread capitalization. Reddit claims are unverified opinions, not product facts. Curated selection is biased by design; no broad prevalence or sentiment estimate is made.

## Differentiation

This is a narrow battlecard evidence extractor, not `bright-data-reddit-outreach` or `hand-raisers` lead discovery, not `bright-data-reddit-demand-radar` broad pain clustering, and not person identification or outreach. Its unit of analysis is an explicit comparison claim and its decision is whether a sales battlecard statement warrants human verification.

## Safety and FAQ

Use only public material you are authorized to process. No author handles, profiles, lead lists, messaging, or posting are emitted. Live calls are disabled unless an exact request workflow has been verified; no live call occurs in tests. Bright Data account access and current [pricing](https://brightdata.com/pricing/web-scraper) apply when collection is performed separately. `.env` is ignored; never commit keys.

**Can the matrix be pasted directly into battlecards?** Treat it as a review queue; verify every claim with product evidence first.

**Does it find competitors or threads?** No. The comparison set and URLs are user-curated.

MIT License. Independent demonstration; not affiliated with or endorsed by Bright Data.
