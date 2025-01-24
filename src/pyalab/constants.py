from pathlib import Path

PATH_TO_PACKAGE_ROOT = Path(__file__).absolute().resolve().parent
assert str(PATH_TO_PACKAGE_ROOT).endswith("pyalab"), (
    f"Sanity check failed, path was not to package root, it was: {PATH_TO_PACKAGE_ROOT}"
)
PATH_TO_INCLUDED_XML_FILES = PATH_TO_PACKAGE_ROOT / "vendor_files" / "integra_library"
