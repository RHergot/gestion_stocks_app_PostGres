from pathlib import Path
import os
from setuptools import setup, find_packages, Extension

# Note cross-platform build notes:
# - Windows: requires Microsoft C++ Build Tools (matching your Python version)
# - Linux: install build-essential and python3-dev (or distro equivalent)
# - macOS: install Xcode Command Line Tools (xcode-select --install)

# Allow disabling Cythonization by setting environment variable CYTHONIZE=0
CYTHONIZE_ENABLED = os.environ.get("CYTHONIZE", "1") not in ("0", "false", "False")

try:
    from Cython.Build import cythonize  # type: ignore
except Exception:
    # If Cython is not available (e.g., end-user install without build deps),
    # fall back to packaging pure-python modules when CYTHONIZE is disabled.
    if CYTHONIZE_ENABLED:
        raise
    cythonize = None

ROOT = Path(__file__).resolve().parent

# Files to exclude from Cython compilation (e.g., entry points)
EXCLUDE_RELATIVE = {
    "APP/main.py",  # keep as pure Python if you run it as script/entry point
}

# Collecte des sources à compiler
patterns = [
    "APP/*.py",  # main.py, main_window.py, etc. (main.py is excluded below)
    "APP/controllers/**/*.py",
    "APP/models/**/*.py",
    "APP/services/**/*.py",
    "APP/views/**/*.py",
    "APP/utils/**/*.py",
]

extensions_specs = []
for pattern in patterns:
    for p in ROOT.glob(pattern):
        if p.is_file() and p not in {ROOT / rel for rel in EXCLUDE_RELATIVE}:
            # Compute fully-qualified module name, e.g. APP.views.foo
            mod_name = str(p.relative_to(ROOT).with_suffix(""))
            mod_name = mod_name.replace(os.sep, ".")
            extensions_specs.append(Extension(mod_name, [str(p)]))

if CYTHONIZE_ENABLED and cythonize is not None and extensions_specs:
    extensions = cythonize(
        extensions_specs,
        compiler_directives={
            "language_level": 3,
            "boundscheck": False,
            "wraparound": False,
            "embedsignature": True,
        },
        annotate=False,  # Set True to generate HTML reports
    )
else:
    # Build without Cython (pure Python). This eases installs when compilers are absent.
    extensions = []

setup(
    name="gestion_stocks_app",
    version="0.1.0",
    packages=find_packages(where="."),
    include_package_data=True,  # include data declared in pyproject.toml
    ext_modules=extensions,
    zip_safe=False,
)
