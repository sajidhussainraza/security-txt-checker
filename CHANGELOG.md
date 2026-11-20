# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Professional README: badges, quick start, scoring guide, FAQ, roadmap,
  contributing and architecture sections.
- Original visual assets: `assets/banner.svg`, `assets/logo.svg`, and a
  static terminal-output preview (`assets/demo.svg`).
- Repository files: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`,
  `SECURITY.md`, `.gitignore`, `.editorconfig`, issue and pull request
  templates, and a CI workflow (`.github/workflows/ci.yml`).
- PNG banner (`docs/banner.png`) and social preview
  (`assets/social-preview.png`) prepared locally for upload via the
  GitHub web UI (PNG files cannot be pushed through the connector).

## [1.0.0] - 2026-11-19

### Added

- Initial release: dependency-free Python CLI auditing a website's
  `security.txt` file against RFC 9116.
- A-F grading (score starts at 100; high -25, medium -10, low -3).
- Checks: availability, HTTPS transport, Content-Type, Contact, Expires,
  Canonical, unknown fields, Policy, Acknowledgments, and optional link
  checking with `--check-links`.
- `--json` output and `--fail-on` CI gate (exit codes 0/1/2).
- 17 tests (mock-server tests plus a live audit of github.com).
- Example outputs for github.com and google.com in `examples/`.
- MIT license.

[Unreleased]: https://github.com/sajidhussainraza/security-txt-checker/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/sajidhussainraza/security-txt-checker/releases/tag/v1.0.0
