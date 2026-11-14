"""Generate public/og-image.png (1200x630), the image link previews show.

    pip install pillow            (only for the final PNG optimisation)
    python tools/make-og.py       (needs Microsoft Edge or Google Chrome installed)

Renders tools/og-template.html in a headless Chromium browser with the site's own
self-hosted fonts (embedded as data: URLs, because browsers block web fonts loaded
from file:// pages), then reduces the PNG to a small palette.

Browser: set OG_BROWSER to the executable if it is not in a standard location.
"""
import base64
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "public" / "assets" / "fonts"
TEMPLATE = ROOT / "tools" / "og-template.html"
OUT = ROOT / "public" / "og-image.png"
W, H = 1200, 630

FONT_FILES = {
    "__FRAUNCES__": "fraunces-latin-standard-normal.woff2",
    "__FRAUNCES_EXT__": "fraunces-latin-ext-standard-normal.woff2",
    "__FRAUNCES_ITALIC__": "fraunces-latin-display-italic.woff2",
    "__INTER__": "inter-latin-wght-normal.woff2",
    "__INTER_EXT__": "inter-latin-ext-wght-normal.woff2",
}

CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "google-chrome", "chromium", "chromium-browser", "microsoft-edge",
]


def find_browser():
    if os.environ.get("OG_BROWSER"):
        return os.environ["OG_BROWSER"]
    for c in CANDIDATES:
        if Path(c).is_file():
            return c
        found = shutil.which(c)
        if found:
            return found
    sys.exit("make-og: no Edge/Chrome found; set OG_BROWSER to its executable")


def main():
    html = TEMPLATE.read_text(encoding="utf-8")
    for token, name in FONT_FILES.items():
        data = base64.b64encode((FONTS / name).read_bytes()).decode()
        html = html.replace(token, f"data:font/woff2;base64,{data}")
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "og.html"
        shot = Path(tmp) / "og.png"
        page.write_text(html, encoding="utf-8")
        subprocess.run([
            find_browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars",
            f"--user-data-dir={Path(tmp) / 'profile'}", "--force-device-scale-factor=1",
            f"--window-size={W},{H}", "--virtual-time-budget=3000",
            f"--screenshot={shot}", page.as_uri(),
        ], check=True, capture_output=True)
        img = Image.open(shot).convert("RGB")
    assert img.size == (W, H), f"screenshot is {img.size}, expected {(W, H)}"
    # Flat colours and anti-aliased text: a 64-colour palette is visually identical.
    img.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(OUT, optimize=True)
    print(f"{OUT.relative_to(ROOT)}  {W}x{H}  {OUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
