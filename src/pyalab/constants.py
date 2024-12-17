from pathlib import Path

PATH_TO_PACKAGE_ROOT = Path(__file__).parent
assert str(PATH_TO_PACKAGE_ROOT).endswith(
    "pyalab"
), f"Sanity check failed, path was not to package root, it was: {PATH_TO_PACKAGE_ROOT}"
PATH_TO_INCLUDED_XML_FILES = PATH_TO_PACKAGE_ROOT / "integra_library"
