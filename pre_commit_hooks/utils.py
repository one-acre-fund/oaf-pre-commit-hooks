import json
import os
import ssl
import subprocess
import warnings
from urllib.request import urlopen


def load_config() -> dict:
    CONFIG_URL = "https://raw.githubusercontent.com/one-acre-fund/oaf-pre-commit-hooks/main/config.json"
    pre_commit_home = os.getenv("PRE_COMMIT_HOME")
    cache_dir = ""
    if pre_commit_home is None or os.path.exists(pre_commit_home) == False:
        pre_commit_home = (
            "" if os.getenv("XDG_CACHE_HOME") is None else os.getenv("XDG_CACHE_HOME")
        )
        cache_dir = pre_commit_home + "/pre-commit"
        if os.path.exists(cache_dir) == False:
            user_home = os.path.expanduser("~")
            cache_dir = user_home + "/.cache/pre-commit"
            if os.path.exists(cache_dir) == False:
                os.makedirs(cache_dir)

    config_file_path = cache_dir + "/oaf_pre-commit_config.json"
    config = {}

    if os.path.exists(config_file_path):
        with open(config_file_path) as json_file:
            config = json.load(json_file)
    if len(config) < 1:
        try:
            ssl._create_default_https_context = ssl._create_unverified_context
            with urlopen(CONFIG_URL) as f:
                config = json.load(f)
                print(" from %s %o", CONFIG_URL, config)
                if len(config) > 1:
                    with open(config_file_path, "w") as fp:
                        json.dump(config, fp)
        except Exception as e:
            warnings.warn(e)

    if len(config) < 1:
        config = {
            "OAF_GIT_BRANCH_NAME_REGEX": "^((release\/[0-9]+\.[0-9]+\.[0-9])|((feature|feat|cleanup|bugfix|hotfix|fix|devops)\/[A-Z]+-[0-9]+(-[A-z0-9]+)+)|(umuganda|chore)\/[a-zA-Z0-9+\-]+)$",
            "OAF_GIT_BRANCH_NAME_EXCEPTION": ["develop", "main", "master"],
            "OAF_GIT_COMMIT_TYPES": [
                "feat",
                "fix",
                "style",
                "refactor",
                "docs",
                "perf",
                "test",
                "chore",
                "build",
            ],
        }
    return config


def is_hook_installed(hook) -> bool:
    """Determine if the pre-commit hook is installed and enabled."""
    exit_code = os.WEXITSTATUS(os.system("git config --bool " + hook))
    out = subprocess.getoutput("git config --bool " + hook)
    return exit_code == 0 and out == "false"
