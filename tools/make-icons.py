"""Generate the favicon set from the self-hosted Fraunces font.

    pip install fonttools brotli pymupdf pillow
    python tools/make-icons.py

Writes into public/:
  favicon.svg            light + dark (prefers-color-scheme) variants, glyph as outlines
  favicon.ico            16, 32 and 48 px (16 px has a bigger dot so it stays visible)
  apple-touch-icon.png   180 px, full-bleed square (iOS rounds the corners itself)
  icon-192.png, icon-512.png       rounded square, transparent corners ("any")
  icon-maskable-512.png  full-bleed square, monogram inside the central 80% safe zone

Design: a rounded square in paper colour with a Fraunces 600 "O" in ink and a
small rust dot at the baseline to its right (the rust full stop of the headline).
"""
import io
import struct
from pathlib import Path

import pymupdf
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
FONT = PUBLIC / "assets" / "fonts" / "fraunces-latin-standard-normal.woff2"

LIGHT = {"paper": "#f6f1e7", "ink": "#1b1a17", "accent": "#9c2f17"}
DARK = {"paper": "#16140f", "ink": "#f1ebde", "accent": "#e8805a"}

VIEW = 64  # SVG units


def glyph_path(char="O", wght=600, opsz=14):
    """The glyph as an SVG path in font units (y up), plus its bounds and the UPM."""
    font = instancer.instantiateVariableFont(TTFont(FONT), {"wght": wght, "opsz": opsz})
    gs = font.getGlyphSet()
    name = font.getBestCmap()[ord(char)]
    bp = BoundsPen(gs)
    gs[name].draw(bp)
    return gs, name, bp.bounds, font["head"].unitsPerEm


GS, NAME, (XMIN, YMIN, XMAX, YMAX), UPM = glyph_path()


def monogram(scale_to, dot_r, cx=VIEW / 2, cy=VIEW / 2):
    """Path data for the "O" and the dot centre/radius, fitted so that the glyph is
    scale_to units tall and the O + dot group is centred on (cx, cy)."""
    s = scale_to / (YMAX - YMIN)
    gw = (XMAX - XMIN) * s
    gap = dot_r * 0.9
    group_w = gw + gap + 2 * dot_r
    x0 = cx - group_w / 2 - XMIN * s          # left edge of the group
    base = cy + (YMAX + YMIN) / 2 * s         # baseline (SVG y down)
    pen = SVGPathPen(GS, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
    GS[NAME].draw(TransformPen(pen, (s, 0, 0, -s, x0, base)))
    dot_x = x0 + XMAX * s + gap + dot_r
    dot_y = base - YMIN * s - dot_r           # sits on the glyph's bottom (overshoot) line
    return pen.getCommands(), dot_x, dot_y


def svg(colors, *, rounded=True, glyph_h=40, dot_r=4.2, dark=None):
    d, dx, dy = monogram(glyph_h, dot_r)
    rx = 14 if rounded else 0
    style = ""
    if dark:
        style = (f"<style>.bg{{fill:{colors['paper']}}}.fg{{fill:{colors['ink']}}}.dot{{fill:{colors['accent']}}}"
                 f"@media (prefers-color-scheme: dark){{.bg{{fill:{dark['paper']}}}.fg{{fill:{dark['ink']}}}.dot{{fill:{dark['accent']}}}}}</style>")
        fills = ("", "", "")
    else:
        fills = tuple(f' fill="{colors[k]}"' for k in ("paper", "ink", "accent"))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEW} {VIEW}">{style}'
            f'<rect class="bg" width="{VIEW}" height="{VIEW}" rx="{rx}"{fills[0]}/>'
            f'<path class="fg" d="{d}"{fills[1]}/>'
            f'<circle class="dot" cx="{dx:.2f}" cy="{dy:.2f}" r="{dot_r}"{fills[2]}/></svg>')


def png(svg_text, size):
    doc = pymupdf.open(stream=svg_text.encode(), filetype="svg")
    page = doc[0]
    z = size / page.rect.width
    pix = page.get_pixmap(matrix=pymupdf.Matrix(z, z), alpha=True)
    return Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGBA")


def save_png(img, path):
    img.save(path, optimize=True)
    print(f"{path.relative_to(ROOT)}  {img.size[0]}x{img.size[1]}  {path.stat().st_size:,} bytes")


def save_ico(images, path):
    """ICO with PNG-compressed entries (supported by every current browser and Windows)."""
    blobs = []
    for im in images:
        b = io.BytesIO(); im.save(b, "PNG", optimize=True); blobs.append(b.getvalue())
    out = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    for im, blob in zip(images, blobs):
        w, h = im.size
        out += struct.pack("<BBBBHHII", w % 256, h % 256, 0, 0, 1, 32, len(blob), offset)
        offset += len(blob)
    path.write_bytes(out + b"".join(blobs))
    print(f"{path.relative_to(ROOT)}  {[im.size[0] for im in images]}  {path.stat().st_size:,} bytes")


def main():
    fav = svg(LIGHT, dark=DARK)
    (PUBLIC / "favicon.svg").write_text(fav, encoding="utf-8")
    print(f"public/favicon.svg  {len(fav):,} bytes")

    rounded = svg(LIGHT)
    small = svg(LIGHT, glyph_h=42, dot_r=6.5)   # 16 px: a 4.2-unit dot would be ~1 px of mush
    save_ico([png(small, 16), png(rounded, 32), png(rounded, 48)], PUBLIC / "favicon.ico")

    square = svg(LIGHT, rounded=False, glyph_h=34, dot_r=3.6)
    save_png(png(square, 180).convert("RGB"), PUBLIC / "apple-touch-icon.png")
    save_png(png(rounded, 192), PUBLIC / "icon-192.png")
    save_png(png(rounded, 512), PUBLIC / "icon-512.png")
    # Maskable: the O + dot group must fit the central 80% circle (radius 25.6 units).
    save_png(png(svg(LIGHT, rounded=False, glyph_h=28, dot_r=3), 512).convert("RGB"), PUBLIC / "icon-maskable-512.png")


if __name__ == "__main__":
    main()
