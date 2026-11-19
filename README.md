# Security.txt Checker

A small, dependency-free Python CLI that audits a website's
`security.txt` file (RFC 9116): the file that tells security
researchers how to report a vulnerability safely. It fetches
`/.well-known/security.txt` (falling back to `/security.txt`) and
checks it against the standard rules: a reachable Contact, a valid
Expires date, a matching Canonical URL, and sensible optional
fields. It grades the site A-F and explains each finding in plain
language, so students and small teams can see exactly where
researchers are left without a safe way to report a problem, and how
to fix it.

Standard library only (`urllib`, `argparse`, `json`). No
third-party packages, no telemetry, nothing is stored. The checker
only sends read-only GET requests and never logs in or submits data.

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

Findings are graded by severity:

| Severity | Examples |
| --- | --- |
| High | No security.txt at all, served over plain HTTP, no Contact, Expires in the past |
| Medium | Invalid Contact URI, missing or malformed Expires, Canonical mismatch |
| Low | Wrong Content-Type, unknown field, missing Policy or Acknowledgments, Expires more than a year away, broken optional link |

Score starts at 100 and deducts 25 / 10 / 3 per high / medium / low
finding: 90+ is A, 75+ B, 60+ C, 40+ D, below that F.

## Install

No installation needed. Python 3.8+ only, standard library only:

```bash
git clone https://github.com/sajidhussainraza/security-txt-checker.git
cd security-txt-checker
```

## Usage

Audit a website's security.txt:

```bash
python3 security_txt_checker.py https://example.com
```

Also verify the URLs inside the file actually answer:

```bash
python3 security_txt_checker.py https://example.com --check-links
```

Machine-readable output:

```bash
python3 security_txt_checker.py https://example.com --json
```

Use it as a CI gate (fail only on high-severity findings):

```bash
python3 security_txt_checker.py https://example.com --fail-on high
```

### Exit codes

| Code | Meaning |
| --- | --- |
| 0 | No findings at/above `--fail-on` |
| 1 | Findings at/above `--fail-on` were found |
| 2 | Usage error (bad URL, site unreachable) |

Note: the checker only reads the public security.txt file. It cannot
audit a file that requires login, and it does not test whether the
contact address actually responds to a report; that needs a human
to send a test message.

## Examples

GitHub publishes a textbook security.txt:

```
$ python3 security_txt_checker.py https://github.com
Security.txt report: https://github.com
Score: 100/100  Grade: A

  Final URL: https://github.com/.well-known/security.txt
  Status: 200
  Content-Type: text/plain
  Redirects: 0
  Fields: 7

No findings: this security.txt looks good.
```

Google scores 97/100: its only finding is a low-severity one, an
Expires date more than a year away (2030-04-01). A long-lived file
is easy to forget and leave stale, so the checker nudges it to
renew yearly. The full output of both runs is saved in
`examples/sample-output-github.com.txt` and
`examples/sample-output-google.com.txt` (captured 18 November 2026).

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

## Teaching notes

This tool pairs well with a lesson on coordinated vulnerability
disclosure: run it against a deliberately bare demo site, then add
one field at a time and watch the grade move. Good discussion
points:

- Why a missing security.txt is a security problem: a researcher
  who finds a flaw and has nowhere safe to report it either stays
  silent, reports it in public, or sells it.
- Why Expires matters: a stale file points researchers at a dead
  inbox, so the date is a promise the file is still maintained.
- Why Canonical matters: without it, a copied file on a mirror or
  a typo-squat domain looks just as official as the real one.
- Why the Contact must be a full URI: `security@example.com` on
  its own is ambiguous, while `mailto:security@example.com` tells
  every tool exactly what to do with it.
- Why HTTPS matters for a plain text file: over HTTP, anyone on
  the path can swap in their own contact address and collect the
  reports.

## Tests

```bash
python3 tests/run_tests.py   # 17 tests, including a live audit of github.com
```

The mock-server tests run a local fake site serving good, expired,
contact-less and mistyped security.txt variants, so they need no
internet. The live test runs a real audit against github.com and is
skipped automatically when the network is unreachable. (pytest is
also supported if it is installed:
`python3 -m pytest tests/ -q`.)

## License

MIT
