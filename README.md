![Security.txt Checker banner](docs/banner.png)

# Security.txt Checker

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests: 17 passing](https://img.shields.io/badge/tests-17%20passing-brightgreen.svg)](#tests)

**Audit any website's `security.txt` file against RFC 9116 in seconds, and get a clear A-F grade with plain-language fixes.**

`security.txt` is the file that tells security researchers how to report a vulnerability safely. If it is missing, expired, or points at a dead inbox, a researcher who finds a flaw has nowhere safe to go: they stay silent, disclose it in public, or sell it. This tool fetches `/.well-known/security.txt` (falling back to `/security.txt`), checks it against the standard, and explains exactly what is wrong and how to fix it.

## Features

- **Zero dependencies** — Python standard library only (`urllib`, `argparse`, `json`). Nothing to install, nothing to update.
- **A-F grading** — a 0-100 score with a clear grade, so a site's disclosure readiness is obvious at a glance.
- **Plain-language findings** — every finding comes with a concrete fix, not just an error code.
- **RFC 9116 checks** — Contact, Expires, Canonical, Content-Type, HTTPS transport, unknown/typo'd fields, and optional Policy and Acknowledgments.
- **Optional link checking** — `--check-links` verifies the URLs inside the file actually answer.
- **CI-ready** — `--json` for machine-readable output and `--fail-on` to fail a build on findings above a severity you choose.
- **Private by design** — no telemetry, nothing is stored. It only sends read-only GET requests and never logs in or submits data.
- **Tested** — 17 tests, including mock-server tests and a live audit of github.com.

## Installation

Python 3.8 or later, no third-party packages:

```bash
git clone https://github.com/sajidhussainraza/security-txt-checker.git
cd security-txt-checker
```

That is the whole install. There is nothing else to set up.

## Quick start

Audit a website's security.txt:

```bash
python3 security_txt_checker.py https://github.com
```

```
Security.txt report: https://github.com
Score: 100/100  Grade: A

  Final URL: https://github.com/.well-known/security.txt
  Status: 200
  Content-Type: text/plain
  Redirects: 0
  Fields: 7

No findings: this security.txt looks good.
```

Also verify the URLs inside the file actually answer:

```bash
python3 security_txt_checker.py https://example.com --check-links
```

Machine-readable output:

```bash
python3 security_txt_checker.py https://example.com --json
```

Use it as a CI gate, failing only on high-severity findings:

```bash
python3 security_txt_checker.py https://example.com --fail-on high
```

### Exit codes

| Code | Meaning |
| --- | --- |
| 0 | No findings at or above `--fail-on` |
| 1 | Findings at or above `--fail-on` were found |
| 2 | Usage error (bad URL, site unreachable) |

### Flags

| Flag | Description |
| --- | --- |
| `url` | Website URL to audit, e.g. `https://example.com` |
| `--json` | Print the report as JSON instead of text |
| `--fail-on {high, medium, low, none}` | Exit 1 when a finding of this severity or worse exists (default: `none`) |
| `--check-links` | Also verify the URLs in Encryption, Policy, Acknowledgments and Hiring answer |
| `--timeout SECONDS` | Request timeout in seconds (default: 10) |

## How scoring works

The score starts at 100 and deducts **25** per high-severity finding, **10** per medium, and **3** per low:

| Score | Grade |
| --- | --- |
| 90-100 | A |
| 75-89 | B |
| 60-74 | C |
| 40-59 | D |
| 0-39 | F |

Findings are graded by severity:

| Severity | Examples |
| --- | --- |
| High | No security.txt at all, served over plain HTTP, no Contact, Expires in the past |
| Medium | Invalid Contact URI, missing or malformed Expires, Canonical mismatch |
| Low | Wrong Content-Type, unknown field, missing Policy or Acknowledgments, Expires more than a year away, broken optional link |

## What it checks

| Check | What a good result looks like |
| --- | --- |
| Availability | A file exists at `/.well-known/security.txt` (or `/security.txt`) and returns HTTP 200 |
| Transport | The file is served over HTTPS, so it cannot be altered in transit |
| Content-Type | Served as `text/plain` |
| Contact | At least one Contact, as a valid `mailto:`, `https:` or `tel:` URI |
| Expires | Present, a valid RFC 3339 date-time, in the future and no more than a year away |
| Canonical | Matches the exact URL the file was fetched from |
| Fields | No unknown or misspelled fields (e.g. `Contract:` instead of `Contact:`) |
| Policy / Acknowledgments | Present, so researchers can see the disclosure rules and how past reports were credited |
| Links (`--check-links`) | The URLs in Encryption, Policy, Acknowledgments and Hiring actually answer |

## Examples

Google scores 97/100: its only finding is a low-severity one, an Expires date more than a year away (2030-04-01). A long-lived file is easy to forget and leave stale, so the checker nudges it to renew yearly. The full output of the GitHub and Google runs is saved in `examples/sample-output-github.com.txt` and `examples/sample-output-google.com.txt` (captured 18 November 2026).

A site with no security.txt at all gets one high finding:

```
$ python3 security_txt_checker.py https://example.com
Security.txt report: https://example.com
Score: 75/100  Grade: B

  Final URL: https://example.com/.well-known/security.txt
  Status: 404
  Content-Type: None
  Redirects: 0
  Fields: 0

Findings (1):
  [HIGH] availability: No security.txt found at
  /.well-known/security.txt or /security.txt (both returned 404).
        Fix: Publish a security.txt at /.well-known/security.txt so
        researchers have a safe way to report vulnerabilities.
```

| Site | Score | Grade |
| --- | --- | --- |
| github.com | 100/100 | A |
| google.com | 97/100 | A |
| example.com | 75/100 | B (no file) |

Scores verified live on 20 November 2026.

## Teaching notes

This tool pairs well with a lesson on coordinated vulnerability disclosure: run it against a deliberately bare demo site, then add one field at a time and watch the grade move. Good discussion points:

- Why a missing security.txt is a security problem: a researcher who finds a flaw and has nowhere safe to report it either stays silent, reports it in public, or sells it.
- Why Expires matters: a stale file points researchers at a dead inbox, so the date is a promise the file is still maintained.
- Why Canonical matters: without it, a copied file on a mirror or a typo-squat domain looks just as official as the real one.
- Why the Contact must be a full URI: `security@example.com` on its own is ambiguous, while `mailto:security@example.com` tells every tool exactly what to do with it.
- Why HTTPS matters for a plain text file: over HTTP, anyone on the path can swap in their own contact address and collect the reports.

Note: the checker only reads the public security.txt file. It cannot audit a file that requires login, and it does not test whether the contact address actually responds to a report; that needs a human to send a test message.

## Tests

```bash
python3 tests/run_tests.py   # 17 tests, including a live audit of github.com
```

The mock-server tests run a local fake site serving good, expired, contact-less and mistyped security.txt variants, so they need no internet. The live test runs a real audit against github.com and is skipped automatically when the network is unreachable. (pytest is also supported if it is installed: `python3 -m pytest tests/ -q`.)

## Contributing

Contributions are welcome. To contribute:

1. Fork the repository and create a branch for your change.
2. Keep the tool dependency-free (standard library only).
3. Add or update tests in `tests/` for any new check or behaviour change.
4. Run `python3 tests/run_tests.py` and make sure all 17 tests pass.
5. Open a pull request describing what changed and why.

Bug reports and feature ideas can also be opened as GitHub issues.

## License

MIT — see [LICENSE](LICENSE).

---

Built by [Cyber Legends](https://cyberlegends.org) — cybersecurity trainings, services and solutions.
