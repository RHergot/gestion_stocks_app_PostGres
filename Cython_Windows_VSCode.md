# Compilation complète d'un projet Python (MVC) avec Cython sous Windows + VS Code

Ce guide documente une procédure validée pour compiler l'intégralité d'un dossier applicatif (ici `APP/`) en extensions Cython (`.pyd`) sous Windows, intégrée à VS Code. Le point d'entrée (`APP/main.py`) reste en Python pur pour faciliter le lancement et le debug.

---

## 1) Pré-requis Windows

- Python (même version que votre venv) depuis python.org
- Microsoft Visual C++ Build Tools + Windows 10/11 SDK
  - Télécharger: https://visualstudio.microsoft.com/visual-cpp-build-tools/
  - Dans l'installateur, cocher «Desktop development with C++» ou «C++ build tools», MSVC v14.x et Windows SDK
- VS Code + extension Python

---

## 2) Environnement Python

Dans un terminal VS Code (PowerShell), à la racine du projet:

```powershell
# (Optionnel) créer/activer un venv
python -m venv .venv;
.\.venv\Scripts\activate;

# Mettre à jour outils de build + Cython
python -m pip install -U pip setuptools wheel build Cython;

# Installer les dépendances applicatives
python -m pip install -r requirements.txt;
```

Note: sous PowerShell, l'opérateur `&&` n'est pas valide (utiliser `;` ou exécuter ligne par ligne).

---

## 3) Fichiers de build

Créer à la racine du repo:

- `pyproject.toml`
```toml
[build-system]
requires = ["setuptools>=68", "wheel", "Cython>=3.0"]
build-backend = "setuptools.build_meta"

[project]
name = "gestion_stocks_app"
version = "0.1.0"

[tool.setuptools.packages.find]
where = ["."]
include = ["APP*"]
```

- `setup.py`
```python
from pathlib import Path
from setuptools import setup, find_packages
from Cython.Build import cythonize

ROOT = Path(__file__).resolve().parent

# Fichiers à exclure (point d'entrée...)
EXCLUDE_RELATIVE = {
    Path("APP/main.py"),
}

# Dossiers à compiler en .pyd
patterns = [
    "APP/controllers/**/*.py",
    "APP/models/**/*.py",
    "APP/services/**/*.py",
    "APP/views/**/*.py",
    "APP/utils/**/*.py",
]

sources = []
for pattern in patterns:
    for p in ROOT.glob(pattern):
        if p.is_file() and p not in {ROOT / rel for rel in EXCLUDE_RELATIVE}:
            sources.append(str(p))

extensions = cythonize(
    sources,
    compiler_directives={
        "language_level": 3,
        "boundscheck": False,
        "wraparound": False,
        "embedsignature": True,
    },
    annotate=False,  # passer à True pour générer les rapports HTML
)

setup(
    name="gestion_stocks_app",
    version="0.1.0",
    packages=find_packages(where="."),
    ext_modules=extensions,
    zip_safe=False,
)
```

---

## 4) .gitignore recommandé

Ajouter (si pas déjà présent):

```
build/
dist/
*.egg-info/
**/*.c
**/*.cpp
**/*.html
**/*.so
**/*.pyd
```

Astuce: si vous souhaitez committer les `.c` générés (rarement utile), retirez `**/*.c` de l'ignore.

---

## 5) Compiler (build in-place)

Depuis la racine du projet, venv activé:

```powershell
.\.venv\Scripts\python.exe setup.py build_ext --inplace;
```

- Génère des `.pyd` à côté des `.py` dans `APP/`.
- L'import de vos modules continue de fonctionner normalement.

Lancer l'application:
```powershell
python .\APP\main.py
```

---

## 6) Intégration VS Code (facultatif mais pratique)

Créer `.vscode/tasks.json`:
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Cython build (in-place)",
      "type": "shell",
      "command": ".\\.venv\\Scripts\\python.exe setup.py build_ext --inplace",
      "group": "build",
      "problemMatcher": "$msCompile"
    }
  ]
}
```

Créer `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Run app (Python)",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/APP/main.py",
      "preLaunchTask": "Cython build (in-place)",
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

---

## 7) Dépannage courant

- «Microsoft Visual C++ 14.0 or greater is required» → installer MSVC Build Tools + Windows SDK, puis relancer un nouveau terminal.
- Erreurs Cython sur des noms non définis/indentations: ce sont souvent de vrais bugs Python révélés à la compilation. Corriger le fichier, puis recompiler.
- Si un fichier pose problème (ex: `APP/views/warehouse_layout_view.py`), vous pouvez l'exclure temporairement:
  ```python
  EXCLUDE_RELATIVE = {
      Path("APP/main.py"),
      Path("APP/views/warehouse_layout_view.py"),
  }
  ```
  et conserver `"APP/views/**/*.py"` dans `patterns` pour compiler le reste.

---

## 8) Conseils de performance

- Sans `cdef`/types, le gain est modéré mais réel sur certaines boucles.
- Activez `annotate=True` dans `cythonize(...)` pour générer des rapports `.html` et identifier les hotspots.
- Typage progressif: commencez par les modules `models/` et `services/` contenant des boucles lourdes.

---

## 9) Build de distribution (optionnel)

Pour construire une wheel:

```powershell
python -m build;
# puis installer localement
pip install .\dist\gestion_stocks_app-0.1.0-*.whl;
```

Pour le dev quotidien, préférez le build in-place.

---

## 10) Récapitulatif commandes PowerShell

```powershell
# venv
python -m venv .venv; .\.venv\Scripts\activate;

# outils de build + Cython
python -m pip install -U pip setuptools wheel build Cython;

# deps applicatives
python -m pip install -r requirements.txt;

# build in-place
.\.venv\Scripts\python.exe setup.py build_ext --inplace;

# lancer l'app
python .\APP\main.py
```

---

Ce modèle est réutilisable pour d'autres applications structurées de façon similaire (MVC sous `APP/`). Adaptez simplement les patterns dans `setup.py` et l'exclusion du point d'entrée.
