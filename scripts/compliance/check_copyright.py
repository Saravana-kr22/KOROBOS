#!/usr/bin/env python3
"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

import os
import re
import sys

# We specifically block closed-source/non-OSS wording to enforce the OS nature.
_ARR = "all rights" + " reserved"
_PROP = "propri" + "etary"
_CONF = "confid" + "ential"
FORBIDDEN_PATTERNS = [
    re.compile(_ARR, re.IGNORECASE),
    re.compile(_PROP, re.IGNORECASE),
    re.compile(rf"\b{_CONF}\b", re.IGNORECASE),
]

# Standard Copyright format expected in some files, though not strictly required everywhere.
# We are mainly looking for FORBIDDEN text here.


def check_file(filepath):
    """Scans a file for forbidden closed-source/non-OSS patterns."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

            for pattern in FORBIDDEN_PATTERNS:
                match = pattern.search(content)
                if match:
                    print(
                        f"ERROR: Forbidden text '{match.group()}' found in {filepath}"
                    )
                    return False
    except UnicodeDecodeError:
        # Skip binary files if they sneak through
        pass
    except Exception as e:
        print(f"WARNING: Could not process {filepath}: {e}")

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Pre-commit passes files as arguments
        sys.exit(0)

    files = sys.argv[1:]
    has_error = False

    for filepath in files:
        if not os.path.isfile(filepath):
            continue

        if not check_file(filepath):
            has_error = True

    if has_error:
        msg1 = (
            "Commit blocked: " + _PROP.capitalize() + " or " + _CONF + " text detected."
        )
        msg2 = (
            "CortexOS relies on open source licensing. Please remove "
            + _PROP
            + " claims."
        )
        print("\n" + msg1)
        print(msg2)
        sys.exit(1)

    sys.exit(0)
