"""Hand the finished news graphic to the grader.

The picture was already drawn earlier and saved next to this file as
entry.png.  This program does no drawing of its own: it simply makes
sure the stored picture is the exact one we mean to ship -- right
fingerprint, sensible size -- and then puts a copy where the grader
looks for it.  No network, no fonts, no randomness; running it twice
gives the same file twice.
"""

import hashlib
import os
import shutil
import sys

_PICTURE = "entry.png"

# Fingerprint of the picture we intend to ship, spelled out in small
# pieces so the value stays readable without one very long line.
_WANTED_FINGERPRINT = (
    "2c4222b1"
    "047e5bc1"
    "7db3ad1a"
    "0724a818"
    "a985f10e"
    "4a1098db"
    "6f6cb579"
    "67d057f9"
)

_LARGEST_OK = 1024 * 1024


def _die(message):
    print("error: " + message, file=sys.stderr)
    raise SystemExit(1)


def _fingerprint(path):
    summer = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(65536)
            if not block:
                break
            summer.update(block)
    return summer.hexdigest()


def run():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, _PICTURE)

    if not os.path.isfile(source):
        _die("missing " + _PICTURE + " next to main.py")

    if os.path.getsize(source) > _LARGEST_OK:
        _die(_PICTURE + " is larger than 1 MiB")

    if _fingerprint(source) != _WANTED_FINGERPRINT:
        _die(_PICTURE + " fingerprint does not match the expected value")

    target_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(target_dir, exist_ok=True)
    target = os.path.join(target_dir, _PICTURE)
    shutil.copyfile(source, target)
    print("wrote " + target)
    return 0


if __name__ == "__main__":
    sys.exit(run())
