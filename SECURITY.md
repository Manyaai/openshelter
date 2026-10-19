# Security policy

**OpenShelter is a planning aid, not a safety control system.** Read this before
reporting anything.

## What this project does and does not do

- It reads public hazard data and open building-code profiles and writes a
  plain-language design brief. It does **not** perform structural calculations,
  certify designs, or replace a licensed engineer. A qualified local engineer
  must sign every construction drawing derived from a brief.
- The web demo runs entirely in your browser. No coordinates, site names, or
  inputs are uploaded to any server we operate.
- The CLI has no network access at runtime unless you explicitly configure a
  remote hazard provider.

## Reporting a vulnerability

If you believe you found a security issue (for example, something that could
execute code in the browser demo, or tamper with generated briefs):

1. Email the maintainers privately via GitHub: open a **private security
   advisory** at https://github.com/Manyaai/openshelter/security/advisories/new
2. Do not open a public issue for security matters.
3. We aim to acknowledge within 7 days and ship a fix within 30 for confirmed
   high-severity issues.

## Out-of-scope reports

- Briefs that disagree with a local engineer's judgement (that's expected; see
  the disclaimer above). File a normal issue with citations instead.
- Availability of free hosting services (GitHub Pages) being rate-limited.
- Findings from automated scanners without a demonstrated impact.

## Supply chain

The core package depends only on the Python standard library, and the website
uses vendored, locally-hosted assets (no third-party CDNs, no analytics
cookies). If you find an exception to this in `pyproject.toml` or `site/`,
please report it as a bug.
