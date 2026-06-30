# Gestion des Stocks — Module GMAO

Module de **gestion des stocks et pièces détachées** intégré à la suite GMAO Industrielle. Développé avec **PySide6 (Qt)** et **PostgreSQL**.

> ⚠️ **Ce module dépend de l'application principale.**
> Il partage la même base de données PostgreSQL que [`gmao_app_PostGres`](https://github.com/RHergot/gmao_app_PostGres).
> Installez et initialisez d'abord l'app principale avant d'utiliser ce module.

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

## Conventions de code

- **Langue** : Noms de classes/méthodes en anglais ; commentaires et messages utilisateur en français
- **Nommage tables** : snake_case (commande, piece_extension, mouvement_stock)
- **Pattern DB** : Préférer `db.execute(query, params)` à `db.conn.cursor()` directement
- **DTO** : Les données DB (`RealDictRow`) sont propagées jusqu'aux vues. Dans un futur refactoring, introduire des dataclasses/Pydantic pour découpler le schéma DB de l'interface.
- **i18n** : Toutes les chaînes UI via `self.tr()` ; dictionnaires FR/EN dans `APP/utils/i18n.py`
- **Logging** : Module `logging` (config centralisée dans `APP/main.py`), pas de `print()`

## 🗄️ Base de données

Ce module partage la base `gmao_industrie_data` avec l'app principale. Schéma complet dans [`gmao_app_PostGres/docs/database-schema.md`](https://github.com/RHergot/gmao_app_PostGres/blob/main/docs/database-schema.md).

Fichier SQL de référence : [`database/database_complete_consolidated.sql`](database/database_complete_consolidated.sql)
