#!/usr/bin/env python3
"""Render brand PNGs (OG image, apple-touch-icon) from SVG sources. Run: python tools/gen_og_image.py"""
import cairosvg, pathlib
root = pathlib.Path(__file__).resolve().parents[1]
og_svg = root / "site/og-image.png.svg"
if og_svg.exists():
    cairosvg.svg2png(url=str(og_svg), write_to=str(root / "site/og-image.png"), output_width=1200, output_height=630)
    print("wrote site/og-image.png")
cairosvg.svg2png(url=str(root / "site/favicon.svg"), write_to=str(root / "site/assets/apple-touch-icon.png"), output_width=180, output_height=180)
print("wrote site/assets/apple-touch-icon.png")
