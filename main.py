#!/usr/bin/env python3
"""Copy the 19 November 2026 world-news front page to the output dir.

The image is drawn by gen_image.py (Pillow, Natural Earth 110m coastline,
35 real stories reported on Thursday 19 November 2026) and shipped in this
repository as entry.png. This program only copies it, verifies the bytes,
and writes them to $MAKEFUN_OUTPUT_DIR/entry.png (default /output).
Standard library only, no network, deterministic — it needs neither
Pillow nor any system font at run time, so it runs in a bare Python
image where the live renderer cannot.
"""
import hashlib
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXPECTED_SHA256 = "2c4222b1047e5bc17db3ad1a0724a818a985f10e4a1098db6f6cb57967d057f9"


def main():
    src = os.path.join(HERE, "entry.png")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "entry.png")
    with open(src, "rb") as fh:
        data = fh.read()
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256:
        print("entry.png sha256 mismatch: %s" % digest, file=sys.stderr)
        return 1
    if len(data) > 1048576:
        print("entry.png over 1 MiB: %d bytes" % len(data), file=sys.stderr)
        return 1
    shutil.copyfile(src, dst)
    print("wrote %s (%d bytes, sha256 %s)" % (dst, len(data), digest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
