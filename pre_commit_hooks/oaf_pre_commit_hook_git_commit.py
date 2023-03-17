#!/usr/bin/env python3
"""Helper script to be used as a pre-commit hook."""
import argparse
import os
import re
import ssl
import subprocess
import sys
import warnings
from typing import Sequence
from urllib.request import urlopen


def is_hook_installed(hook) -> bool:
    """Determine if the pre-commit hook is installed and enabled."""
    exit_code = os.WEXITSTATUS(os.system("git config --bool " + hook))
    out = subprocess.getoutput("git config --bool " + hook)
    return exit_code == 0 and out == "false"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="", help="check README.md")
    parser.add_argument("--forced", default=True, help="check README.md")
    args = parser.parse_args(argv)

    if (
        args.forced == False
        and is_hook_installed("hooks.oaf-pre-commit-hook-git-commit") == False
    ):
        warnings.warn(
            "Hook is not installed or disabled:(enable with 'git config hooks.oaf-pre-commit-hook-git-commit true')"
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
