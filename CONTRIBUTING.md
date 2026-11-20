# Contributing to Security.txt Checker

Thanks for helping improve the checker. This is a small, dependency-free
project, so contributions stay simple on purpose.

## Quick steps

1. Fork the repository and create a branch for your change.
2. Keep the tool **dependency-free** (Python standard library only).
3. Add or update tests in `tests/` for any new check or behaviour change.
4. Run the test suite and make sure all 17 tests pass:

   ```bash
   python3 tests/run_tests.py
   ```

   (pytest also works if installed: `python3 -m pytest tests/ -q`.)
5. Check your code compiles on the oldest supported Python (3.8):

   ```bash
   python3 -m py_compile security_txt_checker.py tests/*.py
   ```

6. Open a pull request describing what changed and why. Link any
   related issue.

## Ground rules

- **Truth first.** Document only behaviour that exists in the code.
  If a claim needs checking, mark it `TODO: verify` instead of guessing.
- **No invented data.** No fake scores, benchmarks, testimonials, or
  download counts anywhere in docs or code.
- **Copy-paste safe.** Every command in docs must work on a clean
  machine with Python 3.8+ and no extra packages.
- **Keep it readable.** The tool is also a teaching aid: plain
  language in findings, comments, and docs beats cleverness.
- **One change per PR** where possible, so reviews stay quick.

## Reporting bugs

Open a [bug report](../../issues/new?template=bug_report.yml) with the
command you ran, the full output, your Python version
(`python3 --version`), and your operating system.

## Code of Conduct

Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Be kind, be
specific, and assume good intent.
