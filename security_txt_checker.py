#!/usr/bin/env python3
"""Security.txt Checker - audit a website's security.txt file (RFC 9116).

A small, dependency-free Python CLI that fetches a site's
``/.well-known/security.txt`` (falling back to ``/security.txt``) and
checks it against the RFC 9116 rules: a reachable Contact, a valid
Expires date, a matching Canonical URL, and sensible optional fields.
It grades the site A-F and explains each finding in plain language,
so students and small teams can see exactly where researchers are
left without a safe way to report a vulnerability, and how to fix it.

Standard library only. No third-party packages, no telemetry, nothing
is stored. The checker only sends read-only GET requests and never
logs in or submits data.
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

VERSION = "1.0.0"

# Fields defined by RFC 9116. Anything else is flagged as unknown,
# which usually means a typo (e.g. "Contract:" instead of "Contact:").
KNOWN_FIELDS = {
    "acknowledgments",
    "canonical",
    "contact",
    "encryption",
    "expires",
    "hiring",
    "policy",
    "preferred-languages",
}

SEVERITY_RANK = {"high": 3, "medium": 2, "low": 1}
DEDUCTIONS = {"high": 25, "medium": 10, "low": 3}
GRADE_BANDS = [(90, "A"), (75, "B"), (60, "C"), (40, "D"), (0, "F")]


class Finding:
    """One problem found in a security.txt file."""

    def __init__(self, severity, field, message, fix):
        self.severity = severity
        self.field = field
        self.message = message
        self.fix = fix

    def as_dict(self):
        return {
            "severity": self.severity,
            "field": self.field,
            "message": self.message,
            "fix": self.fix,
        }


def grade(score):
    for threshold, letter in GRADE_BANDS:
        if score >= threshold:
            return letter
    return "F"


def fetch(url, timeout=10, max_redirects=5):
    """GET a URL without following redirects automatically.

    Returns (status, final_url, content_type, body, redirect_count).
    Raises URLError / HTTPError (for 4xx/5xx) with the status attached.
    """
    redirects = 0
    current = url
    while True:
        request = urllib.request.Request(
            current, headers={"User-Agent": "security-txt-checker/" + VERSION}
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return (
                    response.status,
                    current,
                    response.headers.get_content_type(),
                    response.read().decode("utf-8", errors="replace"),
                    redirects,
                )
        except urllib.error.HTTPError as exc:
            if exc.code in (301, 302, 303, 307, 308) and redirects < max_redirects:
                location = exc.headers.get("Location")
                if location:
                    current = urllib.parse.urljoin(current, location)
                    redirects += 1
                    continue
            raise
        except urllib.error.URLError:
            raise


def head_ok(url, timeout=10):
    """Best-effort check that a URL answers with a 2xx/3xx status."""
    try:
        request = urllib.request.Request(
            url,
            method="HEAD",
            headers={"User-Agent": "security-txt-checker/" + VERSION},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return 200 <= response.status < 400
    except urllib.error.HTTPError as exc:
        # Some servers reject HEAD; a GET that returns anything at all
        # still proves the link is alive.
        return 200 <= exc.code < 400
    except Exception:
        return False


def parse_security_txt(body):
    """Parse a security.txt body into {field: [values]} plus line errors.

    Field names are case-insensitive per RFC 9116. Comment lines
    (starting with '#') and blank lines are ignored.
    """
    fields = {}
    errors = []
    for lineno, raw_line in enumerate(body.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            errors.append(
                "Line %d has no ':' separator, so it is not a field: %r"
                % (lineno, raw_line.strip())
            )
            continue
        name, value = line.split(":", 1)
        name = name.strip().lower()
        value = value.strip()
        if not name:
            errors.append("Line %d has an empty field name." % lineno)
            continue
        fields.setdefault(name, []).append(value)
    return fields, errors


def parse_expires(value):
    """Parse an RFC 9116 Expires value (RFC 3339 date-time)."""
    text = value.strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        # No offset given; RFC 3339 requires one, but treat a bare
        # date-time as UTC rather than rejecting it outright.
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def valid_contact(value):
    """A Contact must be a mailto:, https: or tel: URI (RFC 9116)."""
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme == "mailto":
        return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", parsed.path or ""))
    if parsed.scheme in ("https", "http"):
        return bool(parsed.netloc)
    if parsed.scheme == "tel":
        return bool(re.match(r"^\+?[0-9][0-9\-(). ]+$", parsed.path or ""))
    return False


def check_security_txt(url, timeout=10, check_links=False):
    """Audit the security.txt of the site at ``url``.

    Returns a report dict: url, final_url, status, content_type,
    redirects, findings, score, grade, field_count.
    """
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("URL must start with http:// or https://")
    base = "%s://%s" % (parsed.scheme, parsed.netloc)
    findings = []

    body = None
    final_url = None
    status = None
    content_type = None
    redirects = 0
    tried = []

    for path in ("/.well-known/security.txt", "/security.txt"):
        candidate = base + path
        tried.append(candidate)
        try:
            status, final_url, content_type, body, redirects = fetch(
                candidate, timeout=timeout
            )
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                continue
            findings.append(
                Finding(
                    "high",
                    "availability",
                    "security.txt request failed with HTTP %d." % exc.code,
                    "Make security.txt return HTTP 200 at "
                    "/.well-known/security.txt.",
                )
            )
            return _report(url, final_url or candidate, status or exc.code,
                           content_type, redirects, findings)
        except urllib.error.URLError as exc:
            findings.append(
                Finding(
                    "high",
                    "availability",
                    "Could not reach the site: %s." % exc.reason,
                    "Check the site is online and the URL is correct.",
                )
            )
            return _report(url, candidate, None, None, 0, findings)

    if body is None:
        findings.append(
            Finding(
                "high",
                "availability",
                "No security.txt found at /.well-known/security.txt or "
                "/security.txt (both returned 404).",
                "Publish a security.txt at /.well-known/security.txt so "
                "researchers have a safe way to report vulnerabilities.",
            )
        )
        return _report(url, tried[0], 404, None, 0, findings)

    # Local test servers run over plain HTTP by design; only flag
    # transport for real hosts.
    host = urllib.parse.urlparse(final_url).hostname or ""
    is_loopback = host in ("localhost", "127.0.0.1", "::1") or (
        host.endswith(".localhost")
    )
    if not final_url.startswith("https://") and not is_loopback:
        findings.append(
            Finding(
                "high",
                "transport",
                "security.txt is served over plain HTTP, so it can be "
                "altered in transit and a researcher may report to an "
                "attacker.",
                "Serve security.txt over HTTPS.",
            )
        )

    if content_type and content_type != "text/plain":
        findings.append(
            Finding(
                "low",
                "content-type",
                "security.txt is served as %s instead of text/plain."
                % content_type,
                "Serve security.txt with Content-Type: text/plain.",
            )
        )

    fields, line_errors = parse_security_txt(body)
    for error in line_errors:
        findings.append(
            Finding("low", "syntax", error,
                    "Fix the line so it reads 'Field: value'.")
        )

    for name in fields:
        if name not in KNOWN_FIELDS:
            findings.append(
                Finding(
                    "low",
                    name,
                    "Unknown field %r is not defined by RFC 9116; it is "
                    "probably a typo." % name,
                    "Check the spelling against the RFC 9116 field list: "
                    "Contact, Expires, Encryption, Acknowledgments, "
                    "Policy, Hiring, Preferred-Languages, Canonical.",
                )
            )

    # Contact: the one field RFC 9116 requires.
    contacts = fields.get("contact", [])
    if not contacts:
        findings.append(
            Finding(
                "high",
                "contact",
                "No Contact field: researchers have no address to report "
                "a vulnerability to.",
                "Add at least one Contact, e.g. "
                "'Contact: mailto:security@example.com' or a link to a "
                "bug-bounty page.",
            )
        )
    else:
        for contact in contacts:
            if not valid_contact(contact):
                findings.append(
                    Finding(
                        "medium",
                        "contact",
                        "Contact value %r is not a valid mailto:, https: "
                        "or tel: URI." % contact,
                        "Use a full URI, e.g. "
                        "'Contact: mailto:security@example.com'.",
                    )
                )

    # Expires: required in practice; an expired file misleads researchers.
    expires_values = fields.get("expires", [])
    if not expires_values:
        findings.append(
            Finding(
                "medium",
                "expires",
                "No Expires field: researchers cannot tell whether this "
                "file is still current.",
                "Add an Expires date in RFC 3339 format, e.g. "
                "'Expires: 2027-06-01T00:00:00Z', and renew it regularly.",
            )
        )
    else:
        for value in expires_values:
            try:
                expires = parse_expires(value)
            except ValueError:
                findings.append(
                    Finding(
                        "medium",
                        "expires",
                        "Expires value %r is not a valid RFC 3339 "
                        "date-time." % value,
                        "Use a date like 'Expires: 2027-06-01T00:00:00Z'.",
                    )
                )
                continue
            now = datetime.now(timezone.utc)
            if expires < now:
                findings.append(
                    Finding(
                        "high",
                        "expires",
                        "Expires date %s is in the past, so the file "
                        "looks abandoned." % value,
                        "Renew the Expires date and keep it up to date.",
                    )
                )
            elif (expires - now).days > 365:
                findings.append(
                    Finding(
                        "low",
                        "expires",
                        "Expires date %s is more than a year away; a "
                        "long-lived file is easy to forget and leave "
                        "stale." % value,
                        "Set Expires no more than a year ahead and "
                        "review the file when it renews.",
                    )
                )

    # Canonical: must match the URL the file was fetched from.
    canonicals = fields.get("canonical", [])
    if canonicals:
        for canonical in canonicals:
            if canonical.rstrip("/") != final_url.rstrip("/"):
                findings.append(
                    Finding(
                        "medium",
                        "canonical",
                        "Canonical %r does not match the URL this file "
                        "was fetched from (%s)." % (canonical, final_url),
                        "Set Canonical to the exact URL where the file "
                        "lives.",
                    )
                )

    # Optional fields: useful, but their absence is only a nudge.
    if "policy" not in fields:
        findings.append(
            Finding(
                "low",
                "policy",
                "No Policy field: researchers cannot see the rules for "
                "testing and disclosure.",
                "Add a Policy link to the vulnerability disclosure or "
                "bug-bounty policy.",
            )
        )
    if "acknowledgments" not in fields:
        findings.append(
            Finding(
                "low",
                "acknowledgments",
                "No Acknowledgments field: researchers cannot see how "
                "past reports were credited.",
                "Add an Acknowledgments link to a hall of fame or "
                "disclosure log.",
            )
        )

    # Optional link check: only when the user asks, so a slow or
    # offline target does not make the default run crawl.
    if check_links:
        for field in ("encryption", "policy", "acknowledgments", "hiring"):
            for value in fields.get(field, []):
                if value.startswith(("http://", "https://")) and not head_ok(
                    value, timeout=timeout
                ):
                    findings.append(
                        Finding(
                            "low",
                            field,
                            "%s link %r does not answer." % (field.title(), value),
                            "Fix or remove the broken link.",
                        )
                    )

    return _report(url, final_url, status, content_type, redirects,
                   findings, field_count=len(fields))


def _report(url, final_url, status, content_type, redirects, findings,
            field_count=0):
    score = max(0, 100 - sum(DEDUCTIONS[f.severity] for f in findings))
    return {
        "url": url,
        "final_url": final_url,
        "status": status,
        "content_type": content_type,
        "redirects": redirects,
        "field_count": field_count,
        "findings": [f.as_dict() for f in findings],
        "score": score,
        "grade": grade(score),
    }


def format_text(report):
    lines = [
        "Security.txt report: %s" % report["url"],
        "Score: %d/100  Grade: %s" % (report["score"], report["grade"]),
        "",
        "  Final URL: %s" % report["final_url"],
        "  Status: %s" % report["status"],
        "  Content-Type: %s" % report["content_type"],
        "  Redirects: %d" % report["redirects"],
        "  Fields: %d" % report["field_count"],
    ]
    findings = report["findings"]
    if not findings:
        lines.append("")
        lines.append("No findings: this security.txt looks good.")
    else:
        lines.append("")
        lines.append("Findings (%d):" % len(findings))
        for finding in findings:
            lines.append(
                "  [%s] %s: %s"
                % (finding["severity"].upper(), finding["field"],
                   finding["message"])
            )
            lines.append("        Fix: %s" % finding["fix"])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Audit a website's security.txt file (RFC 9116)."
    )
    parser.add_argument("url", help="Website URL, e.g. https://example.com")
    parser.add_argument("--json", action="store_true",
                        help="Print the report as JSON")
    parser.add_argument(
        "--fail-on", choices=["high", "medium", "low", "none"],
        default="none",
        help="Exit 1 when a finding of this severity or worse exists",
    )
    parser.add_argument("--check-links", action="store_true",
                        help="Also verify the URLs in optional fields answer")
    parser.add_argument("--timeout", type=int, default=10,
                        help="Request timeout in seconds (default 10)")
    args = parser.parse_args(argv)

    try:
        report = check_security_txt(
            args.url, timeout=args.timeout, check_links=args.check_links
        )
    except ValueError as exc:
        print("Error: %s" % exc, file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(format_text(report))

    if args.fail_on != "none":
        threshold = SEVERITY_RANK[args.fail_on]
        if any(
            SEVERITY_RANK[f["severity"]] >= threshold
            for f in report["findings"]
        ):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
