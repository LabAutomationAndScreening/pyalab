import argparse
import enum
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT_DIR = Path(__file__).parent.parent.resolve()
ENVS_CONFIG = REPO_ROOT_DIR / ".devcontainer" / "envs.json"
parser = argparse.ArgumentParser(description="Manual setup for dependencies in the repo")
_ = parser.add_argument(
    "--python-version",
    type=str,
    default=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    help="What version to install.",
)
_ = parser.add_argument("--skip-check-lock", action="store_true", default=False, help="Skip the lock file check step")
_ = parser.add_argument(
    "--optionally-check-lock", action="store_true", default=False, help="Check the lock file IFF it exists"
)
_ = parser.add_argument(
    "--only-create-lock", action="store_true", default=False, help="Only create the lock file, do not install"
)
_ = parser.add_argument(
    "--no-python",
    action="store_true",
    default=False,
    help="Do not process any environments using python package managers",
)
_ = parser.add_argument(
    "--no-node", action="store_true", default=False, help="Do not process any environments using node package managers"
)


class PackageManager(str, enum.Enum):
    UV = "uv"
    PNPM = "pnpm"


class EnvConfig:
    def __init__(self, json_dict: dict[str, Any]):
        super().__init__()
        self.package_manager = PackageManager(json_dict["package_manager"])
        self.path = REPO_ROOT_DIR
        if "relative_directory" in json_dict:
            self.path = REPO_ROOT_DIR / json_dict["relative_directory"]
        if self.package_manager == PackageManager.UV:
            self.lock_file = self.path / "uv.lock"
        elif self.package_manager == PackageManager.PNPM:
            self.lock_file = self.path / "pnpm-lock.yaml"
        else:
            raise NotImplementedError(f"Package manager {self.package_manager} is not supported")


def main():
    args = parser.parse_args(sys.argv[1:])
    is_windows = platform.system() == "Windows"
    uv_env = dict(os.environ)
    uv_env.update({"UV_PYTHON_PREFERENCE": "only-system", "UV_PYTHON": args.python_version})
    generate_lock_file_only = args.only_create_lock
    check_lock_file = not (args.skip_check_lock or args.optionally_check_lock or generate_lock_file_only)
    if args.skip_check_lock and args.optionally_check_lock:
        print("Cannot skip and optionally check the lock file at the same time.")
        sys.exit(1)

    with ENVS_CONFIG.open("r") as f:
        envs = json.load(f)

    for env_dict in envs:
        env = EnvConfig(env_dict)
        if args.no_python and env.package_manager == PackageManager.UV:
            print(f"Skipping environment {env.path} as it uses a Python package manager and --no-python is set")
            continue
        if args.no_node and env.package_manager == PackageManager.PNPM:
            print(f"Skipping environment {env.path} as it uses a Node package manager and --no-node is set")
            continue
        env_check_lock = check_lock_file
        if args.optionally_check_lock and env.lock_file.exists():
            env_check_lock = True
        if env_check_lock or generate_lock_file_only:
            if env.package_manager == PackageManager.UV:
                uv_args = [
                    "uv",
                    "lock",
                ]
                if not generate_lock_file_only:
                    uv_args.append("--check")
                uv_args.extend(["--directory", str(env.path)])
                _ = subprocess.run(uv_args, check=True, env=uv_env)
            elif env.package_manager == PackageManager.PNPM:
                pass  # doesn't seem to be a way to do this https://github.com/orgs/pnpm/discussions/3202
            else:
                raise NotImplementedError(f"Package manager {env.package_manager} does not support lock file checking")
        if env.package_manager == PackageManager.UV:
            sync_command = ["uv", "sync", "--directory", str(env.path)]
            if env_check_lock:
                sync_command.append("--frozen")
            if not generate_lock_file_only:
                _ = subprocess.run(
                    sync_command,
                    check=True,
                    env=uv_env,
                )
        elif env.package_manager == PackageManager.PNPM:
            pnpm_command = ["pnpm", "install", "--dir", str(env.path)]
            if env_check_lock:
                pnpm_command.append("--frozen-lockfile")
            if is_windows:
                pwsh = shutil.which("pwsh") or shutil.which("powershell")
                if not pwsh:
                    raise FileNotFoundError("Neither 'pwsh' nor 'powershell' found on PATH")
                pnpm_command = [
                    pwsh,
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    " ".join(pnpm_command),
                ]
            _ = subprocess.run(
                pnpm_command,
                check=True,
            )
        else:
            raise NotImplementedError(f"Package manager {env.package_manager} is not supported for installation")


if __name__ == "__main__":
    main()
