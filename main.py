#!/usr/bin/env python3
"""Render the 19 November 2026 front page to $MAKEFUN_OUTPUT_DIR/entry.png.

The drawing lives in gen_image.py (Pillow only; Natural Earth 110m
coastline in coastline.json; 35 stories from Thursday 19 November 2026).
No network, no clock, no random — running it twice writes byte-identical
files. Output is one 1024x1024 PNG under 1 MiB.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gen_image


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "entry.png")
    gen_image.render(dst)
    size = os.path.getsize(dst)
    if size > 1048576:
        print("entry.png over 1 MiB: %d bytes" % size, file=sys.stderr)
        return 1
    print("wrote %s (%d bytes)" % (dst, size))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
