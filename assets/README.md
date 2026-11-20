# Assets

Original artwork for Security.txt Checker. Everything here is original
work (SVG) or generated for this project — no copyrighted images or logos.

## Files

| File | What it is | Pushed to GitHub? |
| --- | --- | --- |
| `banner.svg` | README hero banner, 1280x640 | Yes (SVG is text, pushes fine) |
| `logo.svg` | Square logo, works at 64px | Yes |
| `demo.svg` | Static preview of real terminal output | Yes |
| `demo.tape` | VHS script to record a real `demo.gif` | Yes |
| `social-preview.png` | Social preview, 1280x640, 40px safe margins | **No — PNG, upload via the GitHub web UI** (repo Settings → Social preview) |
| `../docs/banner.png` | PNG version of the banner, 1600x533 | **No — PNG, upload via the GitHub web UI if needed** |

PNG files cannot be pushed through the GitHub connector used for this
repo (it accepts UTF-8 text snapshots only), so they live in the local
source directory and must be uploaded in a browser.

## Palette

| Role | Colour | HEX | WCAG AA check |
| --- | --- | --- | --- |
| Primary (background) | Deep navy | `#0B1220` | White text on it: 18.72:1 (AAA) |
| Accent | Teal | `#2DD4BF` | On navy: 10.06:1 (AAA). **Never use on white: 1.86:1 (fails)** |
| Neutral light | Light grey | `#E5E7EB` | On navy: 15.12:1 (AAA) |
| Neutral muted | Slate | `#64748B` | On white: 4.76:1 (AA); on navy as `#94A3B8`: 7.30:1 (AAA) |

All text/background combinations used in the SVGs pass WCAG AA
(4.5:1 for normal text). Teal is a dark-background-only accent.

## Recording the demo GIF

No demo GIF exists yet — `demo.svg` is a static preview of the real
output, labelled as such in the README. To record a real one:

1. Install [VHS](https://github.com/charmbracelet/vhs).
2. Run `vhs assets/demo.tape` from the repo root (terminal 100x28,
   dark theme, under 15 seconds).
3. Optimise under 5 MB: `gifsicle -O3 --colors 128 assets/demo.gif -o assets/demo.gif`
4. Upload `assets/demo.gif` via the GitHub web UI (PNG/GIF files cannot
   be pushed through the connector), then reference it in the README.
