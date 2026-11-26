# Deala public website package

Deploy the contents of this directory as a static site (index.html at the root). No backend is required. Use HTTPS or localhost for Ed25519 Web Crypto. For a local preview, run `python -m http.server 8000` here and visit http://localhost:8000. Opening index.html directly also displays the minimal homepage, but local file handling varies by browser.

- `/`: minimal spinning D, Work the trade, quiet navigation.
- `operator.html`: six-section operator pitch and local synthetic demos.
- `verify/`: paste a v1/v2 browser-demo receipt or load a signed sample (`?sample=1`). V2 signs JSON.stringify(subject), including type. Preserve field order; the envelope is not authenticated. Embedded public key is not a trusted identity. No production receipt compatibility claimed.
- `security/`, `status/`, `changelog/`, `press/`: supporting resources.
- `assets/operator-dossier.pdf`: seven-page development datasheet.
- `assets/metal-card-proof.pdf`: 85 x 54 mm two-sided proof, not a production order. Confirm QR destination https://deala.trade/verify/?sample=1 after deploying and test physical samples.

## Validation performed
Offline Chromium DOM rendering: rotation/pause, reduced motion, mobile overflow, six sections, timeline, abstention, preview-only form, fail-closed unavailable crypto. Local file links and unique HTML IDs checked. Actual verifier JavaScript exercised in Node Web Crypto with valid signature, payload tamper, subject type substitution and malformed/unsupported input. PDF pages inspected in raster preview.

## Release limitations
Browser navigation to a test HTTPS host was blocked in the preview environment; HTTPS browser cryptography, full navigation, CDN assets/animations and live Lighthouse performance require deployment staging tests. All data is synthetic; no completed Silent Shift or verified production engine is claimed. Public changelog reflects observed repository commits, not invented release revisions. No verified production contact address, live health monitor, or active cohort claimed. Access form sends no inquiry. Confirm a working inquiry contact before publishing. No GitHub push or deployment performed. Existing core backend is untouched. No manufacturing order placed.

## Final shipping review
- Homepage byte-for-byte unchanged; operator hero and trade cards unchanged, including G-Wagon SVG.
- Signature result immediately follows the banner and precedes JSON. Signature validity and digest consistency are separately reported. Plain-language modal note distinguishes listings and decisions; detailed scope is in Security. Early denial caption explicitly refers to the local demonstration.
- GitHub API confirmed full commits 758abda08714c476c0715b73678731eedb569f0a and 4fd367ae9189fc0433973ea56f4c7cbc062e2132.
- 103 local references (links, assets, fragments) resolved; all HTML IDs unique. All eight main static routes returned HTTP 200 using a local Python static server.
- Actual modal signing and verification functions tested in Node Web Crypto with DOM stubs: allowed and denied records, re-verification, signed-payload tamper, digest-only mismatch. Standalone verifier accepted supplied and modal-generated receipts and rejected payload/type tampering. Offline Chromium checked result order, unavailable-crypto failure, and no horizontal overflow at 1280 and 390 px; no page script errors in that preview.
- Chromium navigation to localhost was blocked by environment policy. Full secure-context browser interaction, public HTTPS navigation, CDN animations, production contact and deployed route checks remain release gates.
- Deploy the complete directory together; do not upload operator.html alone. No remote action performed.

## Investor positioning update
The minimal homepage is unchanged. The operator page now describes a platform with two initial markets, a clearly labeled expansion research roadmap, qualitative market leakage context, and a company/pilot posture plate. The old preview form was removed. A local pilot review brief and dossier are available without collecting contact data. To enable booking, set `data-booking-url` on `#pilot-booking` in operator.html to a verified HTTPS booking URL, then test booking and its privacy disclosures before publication. No endpoint has been supplied; the booking button remains hidden. The status page preserves the true readiness limitations. No market average, active pilot, SOC alignment, market size or production claims have been added. Core demonstration and verifier logic unchanged.

## Runtime / research edition
Uses the investor edition as base. Homepage, original SVG illustrations and all operator JavaScript are unchanged. Operator navigation prioritizes Runtime, Mandates, Research and Reference markets. The research page publishes a methodology summary and downloadable text, not a measured benchmark or production claim. Model independence is an architectural objective; universal MCP/provider integration is not asserted. No acquisition or financing figures from the positioning brief were included or verified. Existing dossier is retained. Booking still requires a verified URL.

## Repository import (2026-11-26)
Imported into `NickAltstein/Deala` under `site/` (deploy `site/` as the web root). Two edits after packaging:
- `operator.html`: the second Section 02 strip (Market leakage) is labeled `MARKET / TICKET SIZE`, `MARKET / CHANNELS`, `MARKET / RECALL GAP` so it no longer repeats the `01 / 02 / 03` numbering of the runtime strip above it.
- `index.html`: footer reads `DEALA / SPEC v0.3` and adds a `Research` link. The homepage is therefore no longer byte-for-byte identical to the packaged version; the spinning D, intro and navigation are unchanged.

Still open before publishing: `data-booking-url` on `#pilot-booking` is empty (button stays hidden) until a verified HTTPS booking URL is supplied; live HTTPS checks of in-browser Ed25519 verification and of `https://deala.trade/verify/?sample=1` (metal card QR). CDN scripts and fonts are version-pinned but have no Subresource Integrity attributes.
