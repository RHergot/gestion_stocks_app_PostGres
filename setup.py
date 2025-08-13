from pathlib import Path
import os
from setuptools import setup, find_packages, Extension
from Cython.Build import cythonize

ROOT = Path(__file__).resolve().parent

# Fichiers à exclure de la compilation (par ex. point d'entrée)
EXCLUDE_RELATIVE = {
}

# Collecte des sources à compiler
patterns = [
    "APP/*.py",  # main.py, main_window.py, etc.
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

extensions = cythonize(
    extensions_specs,
    compiler_directives={
        "language_level": 3,
        "boundscheck": False,
        "wraparound": False,
        "embedsignature": True,
    },
    annotate=False,  # Passez à True pour générer les rapports HTML
)

setup(
    name="gestion_stocks_app",
    version="0.1.0",
    packages=find_packages(where="."),
    ext_modules=extensions,
    zip_safe=False,
)
