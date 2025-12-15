import argparse
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

UV_VERSION = "0.9.17"
PNPM_VERSION = "10.25.0"
COPIER_VERSION = "9.11.0"
COPIER_TEMPLATE_EXTENSIONS_VERSION = "0.3.3"
PRE_COMMIT_VERSION = "4.5.0"
GITHUB_WINDOWS_RUNNER_BIN_PATH = r"C:\Users\runneradmin\.local\bin"
INSTALL_SSM_PLUGIN_BY_DEFAULT = False
parser = argparse.ArgumentParser(description="Install CI tooling for the repo")
_ = parser.add_argument(
    "--no-python",
    default=False,
    action="store_true",
    help="Do not process any environments using python package managers",
)
_ = parser.add_argument(
    "--python-version",
    default=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    type=str,
    help="What version to install.",
)
_ = parser.add_argument(
    "--no-node", action="store_true", default=False, help="Do not process any environments using node package managers"
)
_ = parser.add_argument(
    "--skip-installing-ssm-plugin",
    action="store_true",
    default=False,
    help="Skip installing the SSM plugin for AWS CLI",
)


def main():
    args = parser.parse_args(sys.argv[1:])
    is_windows = platform.system() == "Windows"
    uv_env = dict(os.environ)
    uv_env.update({"UV_PYTHON": args.python_version, "UV_PYTHON_PREFERENCE": "only-system"})
    uv_path = ((GITHUB_WINDOWS_RUNNER_BIN_PATH + "\\") if is_windows else "") + "uv"
    if is_windows:
        pwsh = shutil.which("pwsh") or shutil.which("powershell")
        if not pwsh:
            raise FileNotFoundError("Neither 'pwsh' nor 'powershell' found on PATH")
    if not args.no_python:
        if is_windows:
            uv_env.update({"PATH": rf"{GITHUB_WINDOWS_RUNNER_BIN_PATH};{uv_env['PATH']}"})
            # invoke installer in a pwsh process
            _ = subprocess.run(
                [
                    pwsh,  # type: ignore[reportPossiblyUnboundVariable] # this matches the conditional above that defines pwsh
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    f"irm https://astral.sh/uv/{UV_VERSION}/install.ps1 | iex",
                ],
                check=True,
                env=uv_env,
            )
        else:
            _ = subprocess.run(
                f"curl -fsSL --connect-timeout 20 --max-time 40 --retry 3 --retry-delay 5 --retry-connrefused --proto '=https' https://astral.sh/uv/{UV_VERSION}/install.sh | sh",
                check=True,
                shell=True,
                env=uv_env,
            )
            # TODO: add uv autocompletion to the shell https://docs.astral.sh/uv/getting-started/installation/#shell-autocompletion
        _ = subprocess.run(
            [
                uv_path,
                "tool",
                "install",
                f"copier=={COPIER_VERSION}",
                "--with",
                f"copier-template-extensions=={COPIER_TEMPLATE_EXTENSIONS_VERSION}",
            ],
            check=True,
            env=uv_env,
        )
        _ = subprocess.run(
            [
                uv_path,
                "tool",
                "install",
                f"pre-commit=={PRE_COMMIT_VERSION}",
            ],
            check=True,
            env=uv_env,
        )
        _ = subprocess.run(
            [
                uv_path,
                "tool",
                "list",
            ],
            check=True,
            env=uv_env,
        )
    if not args.no_node:
        pnpm_install_sequence = ["npm -v", f"npm install -g pnpm@{PNPM_VERSION}", "pnpm -v"]
        for cmd in pnpm_install_sequence:
            cmd = (
                [
                    pwsh,  # type: ignore[reportPossiblyUnboundVariable] # this matches the conditional above that defines pwsh
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    cmd,
                ]
                if is_windows
                else [cmd]
            )
            _ = subprocess.run(cmd, shell=True, check=True)
    if INSTALL_SSM_PLUGIN_BY_DEFAULT and not args.skip_installing_ssm_plugin:
        with tempfile.TemporaryDirectory() as tmp_dir:
            if is_windows:
                local_package_path = Path(tmp_dir) / "SessionManagerPluginSetup.exe"
                # Based on https://docs.aws.amazon.com/systems-manager/latest/userguide/install-plugin-windows.html
                # no specific reason for that version, just pinning it for best practice
                _ = subprocess.run(
                    [
                        "curl",
                        "https://s3.amazonaws.com/session-manager-downloads/plugin/1.2.707.0/windows/SessionManagerPluginSetup.exe",
                        "-o",
                        f"{local_package_path}",
                    ],
                    check=True,
                )
                _ = subprocess.run(
                    [str(local_package_path), "/quiet"],
                    check=True,
                )
            else:
                local_package_path = Path(tmp_dir) / "session-manager-plugin.deb"
                # Based on https://docs.aws.amazon.com/systems-manager/latest/userguide/install-plugin-debian-and-ubuntu.html
                # no specific reason for that version, just pinning it for best practice
                _ = subprocess.run(
                    [
                        "curl",
                        "https://s3.amazonaws.com/session-manager-downloads/plugin/1.2.707.0/ubuntu_64bit/session-manager-plugin.deb",
                        "-o",
                        f"{local_package_path}",
                    ],
                    check=True,
                )
                _ = subprocess.run(
                    ["sudo", "dpkg", "-i", str(local_package_path)],
                    check=True,
                )
            print("SSM Plugin Manager Version: ")
            _ = subprocess.run(
                ["session-manager-plugin", "--version"],
                check=True,
            )


if __name__ == "__main__":
    main()
