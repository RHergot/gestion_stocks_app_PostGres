# Gestion des Stocks — Module GMAO

Module de **gestion des stocks et pièces détachées** intégré à la suite GMAO Industrielle. Développé avec **PySide6 (Qt)** et **PostgreSQL**.

## Fonctionnalités

- 📦 **Catalogue pièces** — Références, catégories, statuts, unités
- 🏬 **Emplacements** — Gestion des emplacements physiques, extensions
- 📥 **Réception** — Workflow complet de réception des commandes
- 🔄 **Mouvements** — Suivi des mouvements de stock (entrées/sorties/transferts)
- 🏢 **Multi-sites** — Gestion par site, fabricants, fournisseurs
- 📊 **Vue entrepôt** — Layout visuel des emplacements

## Architecture

```
APP/
├── controllers/    # Logique métier
├── models/         # Repositories PostgreSQL (pattern repository)
├── services/       # Couche service (CRUD, workflow réception)
├── views/          # Dialogues et vues Qt (PySide6)
└── utils/          # i18n, chargement .env
```

## Stack

| Composant | Technologie |
|-----------|-------------|
| Interface | PySide6 (Qt) |
| Base de données | PostgreSQL |
| Packaging | pyproject.toml + setup.py |

## Installation

```bash
pip install -r requirements.txt
python tools/init_db.py
python APP/main.py
```

## Licence

MIT — voir [LICENSE](LICENSE)
