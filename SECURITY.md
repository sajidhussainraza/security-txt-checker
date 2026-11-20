# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

**Do not open a public issue for a security vulnerability.**

Instead, email **info@cyberlegends.org** with:

- A description of the issue and what it affects
- Steps to reproduce it
- The version you tested against (`python3 security_txt_checker.py --help`
  shows usage; the version is in `VERSION` at the top of
  `security_txt_checker.py`)

You should receive an acknowledgement within 5 working days. If the
issue is confirmed, a fix will be released and credited in
[CHANGELOG.md](CHANGELOG.md) unless you ask to stay anonymous.

## Scope notes

This tool only sends read-only GET requests to the site you name on the
command line, plus optional HEAD requests to the URLs inside a
security.txt file when you pass `--check-links`. It never logs in,
submits data, or stores anything. It does not test whether a contact
address actually responds to a vulnerability report — that needs a human
to send a test message.
