# Self-hosted fonts

All fonts are under the SIL Open Font License 1.1 (`LICENSE-Fraunces.txt`,
`LICENSE-Inter.txt`). Nothing is loaded from Google Fonts or any other host.

| File | Source | Axes | Used for |
|---|---|---|---|
| `fraunces-latin-standard-normal.woff2`, `fraunces-latin-ext-standard-normal.woff2` | npm `@fontsource-variable/fraunces` 5.3.0, `files/` | wght, opsz | headings, big numbers, the name in the header |
| `fraunces-latin-display-italic.woff2`, `fraunces-latin-ext-display-italic.woff2` | same package (`*-standard-italic.woff2`), opsz pinned at 72 with fontTools (about half the size) | wght | the italic accent word in the home headline (display sizes only) |
| `inter-latin-wght-normal.woff2`, `inter-latin-ext-wght-normal.woff2` | npm `@fontsource-variable/inter` 5.3.0, `files/` | wght | body text and UI |
| `inter-arrows-wght-normal.woff2` | subset of `Inter[opsz,wght].ttf` from github.com/google/fonts (`ofl/inter`), U+2190-2193 only, opsz pinned at 32 | wght | arrows (`→`): Fraunces has no arrow glyphs and the Fontsource subsets leave them out |

Only the `latin` and `latin-ext` subsets are shipped (latin-ext covers Turkish:
İ, ı, ş, ğ). The `@font-face` rules, with the matching `unicode-range` values from
the Fontsource CSS, are at the top of `/assets/css/style.css`. The two files used
above the fold (Fraunces normal latin, Inter latin) are preloaded in every page's
`<head>`.

Fallback metrics: `Fraunces Fallback` (Georgia) and `Inter Fallback` (Arial) use
`size-adjust` and `ascent-/descent-/line-gap-override` values computed with
fontTools from the shipped files (Fraunces at wght 400, opsz 48; Inter at wght 400),
so the swap from the system font to the web font barely moves the layout.

To rebuild the display italic: `instancer.instantiateVariableFont(TTFont("fraunces-latin-standard-italic.woff2"), {"opsz": 72})`, saved as woff2.

To rebuild the arrow subset (needs `pip install fonttools brotli`):

```python
from fontTools.ttLib import TTFont
from fontTools import subset
from fontTools.varLib import instancer
t = TTFont("Inter[opsz,wght].ttf", lazy=False)
o = subset.Options(); o.layout_features = []; o.name_IDs = ["*"]; o.notdef_outline = True
s = subset.Subsetter(o); s.populate(unicodes=[0x2190, 0x2191, 0x2192, 0x2193]); s.subset(t)
t = instancer.instantiateVariableFont(t, {"opsz": 32})
t.flavor = "woff2"; t.save("inter-arrows-wght-normal.woff2")
```
