#!/usr/bin/env python3
"""Tests for security_txt_checker.py.

The mock-server tests spin up a local fake site serving different
security.txt variants, so they need no internet. The live test audits
github.com and is skipped automatically when the network is
unreachable.
"""

import socket
import sys
import threading
import unittest
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import security_txt_checker as stc

GOOD = """# Security contact for Example Corp
Contact: mailto:security@example.com
Contact: https://example.com/security
Expires: 2027-06-01T00:00:00Z
Acknowledgments: https://example.com/hall-of-fame
Policy: https://example.com/disclosure-policy
Hiring: https://example.com/careers
Preferred-Languages: en, ur
Canonical: {base}/.well-known/security.txt
"""

NO_CONTACT = """Expires: 2030-01-01T00:00:00Z
Policy: https://example.com/disclosure-policy
"""

EXPIRED = """Contact: mailto:security@example.com
Expires: 2020-01-01T00:00:00Z
"""

BAD_CONTACT_AND_CANONICAL = """Contact: security@example.com
Expires: 2030-01-01T00:00:00Z
Canonical: https://other.example.com/.well-known/security.txt
"""

TYPO_FIELD = """Contact: mailto:security@example.com
Expires: 2030-01-01T00:00:00Z
Contract: mailto:legal@example.com
Policy: https://example.com/disclosure-policy
Acknowledgments: https://example.com/hall-of-fame
"""

BAD_EXPIRES = """Contact: mailto:security@example.com
Expires: next summer
"""

PLAIN_HTTP = GOOD


def make_handler(bodies):
    """Build a handler serving {path: (status, content_type, body)}."""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            entry = bodies.get(self.path)
            if entry is None:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"not found")
                return
            status, content_type, body = entry
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, *args):  # keep test output clean
            pass

    return Handler


class MockServerTestCase(unittest.TestCase):
    def start_server(self, bodies):
        handler = make_handler(bodies)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       daemon=True)
        self.thread.start()
        return "http://127.0.0.1:%d" % self.port

    def tearDown(self):
        server = getattr(self, "server", None)
        if server is not None:
            server.shutdown()
            server.server_close()

    def test_good_file_scores_high(self):
        bodies = {}
        base = self.start_server(bodies)
        bodies["/.well-known/security.txt"] = (
            200, "text/plain", GOOD.format(base=base))
        report = stc.check_security_txt(base)
        self.assertEqual(report["status"], 200)
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["score"], 100)
        self.assertEqual(report["grade"], "A")

    def test_missing_file_is_high(self):
        base = self.start_server({})
        report = stc.check_security_txt(base)
        severities = [f["severity"] for f in report["findings"]]
        self.assertIn("high", severities)
        self.assertTrue(any(f["field"] == "availability"
                            for f in report["findings"]))
        # One high finding: 100 - 25 = 75, grade B.
        self.assertEqual(report["score"], 75)
        self.assertEqual(report["grade"], "B")

    def test_fallback_to_root_security_txt(self):
        bodies = {}
        base = self.start_server(bodies)
        root_good = GOOD.replace(
            "/.well-known/security.txt", "/security.txt")
        bodies["/security.txt"] = (200, "text/plain",
                                   root_good.format(base=base))
        report = stc.check_security_txt(base)
        self.assertEqual(report["status"], 200)
        self.assertTrue(report["final_url"].endswith("/security.txt"))
        self.assertEqual(report["grade"], "A")

    def test_missing_contact_is_high(self):
        base = self.start_server({
            "/.well-known/security.txt": (200, "text/plain", NO_CONTACT),
        })
        report = stc.check_security_txt(base)
        fields = {f["field"]: f["severity"] for f in report["findings"]}
        self.assertEqual(fields.get("contact"), "high")

    def test_expired_file_is_high(self):
        base = self.start_server({
            "/.well-known/security.txt": (200, "text/plain", EXPIRED),
        })
        report = stc.check_security_txt(base)
        fields = {f["field"]: f["severity"] for f in report["findings"]}
        self.assertEqual(fields.get("expires"), "high")

    def test_bad_contact_and_canonical(self):
        base = self.start_server({
            "/.well-known/security.txt": (
                200, "text/plain", BAD_CONTACT_AND_CANONICAL),
        })
        report = stc.check_security_txt(base)
        by_field = {}
        for finding in report["findings"]:
            by_field.setdefault(finding["field"], []).append(
                finding["severity"])
        self.assertIn("medium", by_field.get("contact", []))
        self.assertIn("medium", by_field.get("canonical", []))

    def test_typo_field_flagged(self):
        base = self.start_server({
            "/.well-known/security.txt": (200, "text/plain", TYPO_FIELD),
        })
        report = stc.check_security_txt(base)
        self.assertTrue(any(f["field"] == "contract"
                            for f in report["findings"]))

    def test_bad_expires_format(self):
        base = self.start_server({
            "/.well-known/security.txt": (200, "text/plain", BAD_EXPIRES),
        })
        report = stc.check_security_txt(base)
        self.assertTrue(any(f["field"] == "expires"
                            for f in report["findings"]))

    def test_wrong_content_type_is_low(self):
        bodies = {}
        base = self.start_server(bodies)
        bodies["/.well-known/security.txt"] = (
            200, "text/html", GOOD.format(base=base))
        report = stc.check_security_txt(base)
        by_field = {f["field"]: f["severity"] for f in report["findings"]}
        self.assertEqual(by_field.get("content-type"), "low")

    def test_loopback_http_is_exempt_from_transport_check(self):
        # Local test servers run over plain HTTP by design, so the
        # transport finding must not fire for loopback hosts.
        bodies = {}
        base = self.start_server(bodies)
        bodies["/.well-known/security.txt"] = (
            200, "text/plain", GOOD.format(base=base))
        report = stc.check_security_txt(base)
        self.assertFalse(any(f["field"] == "transport"
                             for f in report["findings"]))
        self.assertEqual(report["grade"], "A")

    def test_missing_policy_and_acknowledgments_are_low(self):
        base = self.start_server({
            "/.well-known/security.txt": (200, "text/plain", EXPIRED),
        })
        report = stc.check_security_txt(base)
        by_field = {f["field"]: f["severity"] for f in report["findings"]}
        self.assertEqual(by_field.get("policy"), "low")
        self.assertEqual(by_field.get("acknowledgments"), "low")

    def test_parse_handles_comments_and_case(self):
        fields, errors = stc.parse_security_txt(
            "# comment\n\nCONTACT: mailto:a@example.com\nExpires: 2030-01-01T00:00:00Z\n")
        self.assertEqual(errors, [])
        self.assertEqual(fields["contact"], ["mailto:a@example.com"])

    def test_parse_flags_line_without_colon(self):
        _, errors = stc.parse_security_txt("Contact mailto security@example.com\n")
        self.assertEqual(len(errors), 1)

    def test_valid_contact_forms(self):
        self.assertTrue(stc.valid_contact("mailto:security@example.com"))
        self.assertTrue(stc.valid_contact("https://example.com/security"))
        self.assertTrue(stc.valid_contact("tel:+92-300-1234567"))
        self.assertFalse(stc.valid_contact("security@example.com"))
        self.assertFalse(stc.valid_contact("mailto:not-an-email"))

    def test_fail_on_exit_code(self):
        base = self.start_server({
            "/.well-known/security.txt": (200, "text/plain", EXPIRED),
        })
        self.assertEqual(stc.main([base, "--fail-on", "high"]), 1)
        self.assertEqual(stc.main([base, "--fail-on", "none"]), 0)

    def test_bad_url_is_usage_error(self):
        self.assertEqual(stc.main(["not-a-url"]), 2)


class LiveTestCase(unittest.TestCase):
    def test_live_github_audit(self):
        try:
            report = stc.check_security_txt("https://github.com")
        except (urllib.error.URLError, socket.timeout, OSError):
            self.skipTest("network unreachable")
        self.assertEqual(report["status"], 200)
        self.assertTrue(report["field_count"] >= 5)
        self.assertGreaterEqual(report["score"], 75)


if __name__ == "__main__":
    unittest.main(verbosity=2)
