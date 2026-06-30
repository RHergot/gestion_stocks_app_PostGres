# Audit de Sécurité — Projet gestion_stocks_app_Postgres

**Date :** 30 juin 2026  
**Périmètre :** Tous les fichiers `.py` (APP/, tools/, database/), fichiers racine (.env, .env_old, .gitignore, pyproject.toml, setup.py, requirements.txt), APP/droits_table, tools/ (48 fichiers)  
**Méthodologie :** Scan transverse automatisé + lecture manuelle des fichiers critiques

---

## Résumé Exécutif

| Sévérité | Nombre |
|----------|--------|
| 🔴 CRITIQUE | 6 |
| 🟠 HAUTE | 4 |
| 🟡 MOYENNE | 7 |
| 🟢 BASSE | 8 |

---

## 🔴 CRITIQUE

### 1. Credentials en clair dans `.env`
- **Chemin :** `/opt/Projects/gestion_stocks_app_Postgres/.env`
- **Sévérité :** 🔴 CRITIQUE
- **Description :** Le fichier `.env` contient `POSTGRES_PASSWORD=mot_de_passe_fort` en clair. Même si `.env` est dans `.gitignore`, le mot de passe est faible et stocké en clair sur le disque. Le fichier est présent physiquement sur le serveur.
- **Correction :** 
  1. Remplacer par un mot de passe fort généré aléatoirement (≥ 32 caractères)
  2. Utiliser un gestionnaire de secrets (Vault, Doppler, ou variables d'environnement système)
  3. Créer un `.env.example` sans secrets comme modèle

### 2. `.env_old` non protégé
- **Chemin :** `/opt/Projects/gestion_stocks_app_Postgres/.env_old`
- **Sévérité :** 🔴 CRITIQUE
- **Description :** Fichier `.env_old` contient les mêmes secrets que `.env` mais n'est PAS dans `.gitignore`. Risque élevé de commit accidentel des credentials dans Git. Le fichier est redondant et ne devrait pas exister.
- **Correction :** 
  1. Supprimer immédiatement `.env_old`
  2. Ajouter `.env_old` et `*.env_*` au `.gitignore`
  3. Vérifier l'historique Git (`git log --all --full-history -- .env_old`) pour s'assurer qu'il n'a jamais été commité

### 3. Password loggé en stdout — `APP/services/db.py`
- **Chemin :** `/opt/Projects/gestion_stocks_app_Postgres/APP/services/db.py` (lignes 24-26)
- **Sévérité :** 🔴 CRITIQUE
- **Description :** La méthode `__init__` de la classe `Database` affiche TOUTES les variables `POSTGRES_*` incluant `POSTGRES_PASSWORD` dans stdout :
  ```python
  for key, value in os.environ.items():
      if key.startswith('POSTGRES_'):
          print(f"{key} = {value}")  # AFFICHE LE MOT DE PASSE EN CLAIR
  ```
  Le mot de passe est visible dans les logs, les sorties de terminal, et potentiellement dans les systèmes de monitoring.
- **Correction :** 
  ```python
  for key, value in os.environ.items():
      if key.startswith('POSTGRES_'):
          if key.endswith('PASSWORD'):
              print(f"{key} = ***")
          else:
              print(f"{key} = {value}")
  ```

### 4. Password loggé en stdout — `tools/test_db_connection.py`
- **Chemin :** `/opt/Projects/gestion_stocks_app_Postgres/tools/test_db_connection.py` (lignes 111-114)
- **Sévérité :** 🔴 CRITIQUE
- **Description :** Même problème que ci-dessus — toutes les variables `POSTGRES_*` affichées en clair, y compris `POSTGRES_PASSWORD`.
- **Correction :** Appliquer le même masquage que pour `db.py`.

### 5. Mot de passe Admin hardcodé dans le code source
- **Chemin :** `/opt/Projects/gestion_stocks_app_Postgres/APP/models/commande_repository.py` (lignes 305-323)
- **Sévérité :** 🔴 CRITIQUE
- **Description :** La méthode `get_default_user_id()` crée automatiquement un utilisateur Admin avec le mot de passe **en clair** `'admin123'` :
  ```python
  cur.execute("""
      INSERT INTO utilisateur (login, email, mot_de_passe_hash, role, actif, nom_complet)
      VALUES ('Admin', 'admin@example.com', 'admin123', ...)
  """)
  ```
  Le champ s'appelle `mot_de_passe_hash` mais le mot de passe est stocké en clair, sans aucun hachage. De plus, le compte Admin est créé automatiquement sans demande explicite.
- **Correction :** 
  1. Ne jamais créer d'utilisateur automatiquement
  2. Hacher le mot de passe avec `bcrypt` (déjà dans les dépendances !)
  3. Utiliser `hashlib` ou `bcrypt` pour stocker un hash, pas le mot de passe en clair
  4. Utiliser un script d'initialisation séparé (`tools/init_admin.py`) qui demande le mot de passe en interactif

### 6. `.env_old` doublon de secrets
- **Chemin :** `/opt/Projects/gestion_stocks_app_Postgres/.env_old`
- **Sévérité :** 🔴 CRITIQUE
- **Description :** Le fichier `.env_old` est un copié-collé de `.env` contenant les mêmes credentials. Pourquoi existe-t-il ? Ancienne version ? Backup ? Ce fichier double la surface d'attaque sans raison.
- **Correction :** Supprimer `.env_old` et documenter pourquoi il existait (procédure Git ? migration ?).

---

## 🟠 HAUTE

### 7. Absence de fichier `.env.example`
- **Chemin :** Racine du projet
- **Sévérité :** 🟠 HAUTE
- **Description :** Aucun fichier `.env.example` ou `.env.template` n'existe. Les développeurs ne savent pas quelles variables sont nécessaires ni leur format attendu.
- **Correction :** Créer `.env.example` :
  ```
  POSTGRES_HOST=localhost
  POSTGRES_PORT=5432
  POSTGRES_DB=your_database_name
  POSTGRES_USER=your_user
  POSTGRES_PASSWORD=your_secure_password_here
  # POSTGRES_OPTIONS=sslmode=require
  ```

### 8. Désalignement RBAC — `APP/droits_table`
- **Chemin :** `/opt/Projects/gestion_stocks_app_Postgres/APP/droits_table`
- **Sévérité :** 🟠 HAUTE
- **Description :** Le script SQL accorde les droits à l'utilisateur `stock_app` mais l'application utilise `gmao_app_user`. Les permissions RBAC ne sont donc pas appliquées au bon utilisateur.
- **Correction :** Remplacer `stock_app` par `gmao_app_user` dans le script, ou documenter clairement le mapping.

### 9. Debug `print()` exposant la config DB
- **Chemin :** Multiples fichiers
  - `/opt/Projects/gestion_stocks_app_Postgres/APP/services/db.py` (lignes 40-46, paramètres sauf password affichés)
  - `/opt/Projects/gestion_stocks_app_Postgres/tools/init_mouvement_tables.py` (lignes 30-33)
  - `/opt/Projects/gestion_stocks_app_Postgres/tools/check_db.py` (paramètres de connexion exposés)
  - `/opt/Projects/gestion_stocks_app_Postgres/tools/init_db.py` (lignes 19-21)
- **Sévérité :** 🟠 HAUTE
- **Description :** De nombreux scripts affichent la configuration de connexion (host, database, user) dans la sortie standard. En environnement de production, ces informations ne devraient pas être loggées sans nécessité.
- **Correction :** Utiliser le module `logging` avec niveaux DEBUG/INFO appropriés. Désactiver les logs de configuration en production.

### 10. SSL/TLS désactivé pour PostgreSQL
- **Chemin :** `/opt/Projects/gestion_stocks_app_Postgres/.env` (dernière ligne commentée)
- **Sévérité :** 🟠 HAUTE
- **Description :** `POSTGRES_OPTIONS=sslmode=require` est commenté. La connexion à PostgreSQL se fait sans chiffrement SSL, exposant les données (et le mot de passe) en clair sur le réseau.
- **Correction :** Décommenter et activer `sslmode=require` (ou `verify-full` en production).

---

## 🟡 MOYENNE

### 11. Absence de framework de tests automatisés
- **Chemin :** `tools/` (20+ scripts `test_*.py`)
- **Sévérité :** 🟡 MOYENNE
- **Description :** Aucun framework de test (pytest, unittest) n'est utilisé. Tous les "tests" sont des scripts manuels dans `tools/` qui nécessitent une base de données réelle et une intervention humaine. Pas de `conftest.py`, pas de `pytest.ini`, pas de CI/CD configurable.
- **Correction :** 
  1. Créer un dossier `tests/` avec pytest
  2. Mocker la base de données pour les tests unitaires
  3. Intégrer pytest dans `pyproject.toml`
  4. Ajouter `pytest` aux dépendances de dev

### 12. Scripts outils dupliqués et redondants
- **Chemin :** `tools/` (48 fichiers)
- **Sévérité :** 🟡 MOYENNE
- **Description :** De nombreux scripts ont des fonctionnalités qui se chevauchent :
  - `test_commande_ui.py` / `test_commande_view_buttons.py` / `test_commande_workflow.py`
  - `test_reception_system.py` / `test_reception_ui.py` / `test_reception_ui_fixed.py` / `test_reception_complete.py` / `test_reception_workflow.py` / `test_reception_dialog_logic.py` / `test_integration_reception.py`
  - `prepare_test_reception.py` / `reset_commande_for_reception.py` / `reset_commande_test.py` (fonctionnalités très similaires)
  - `check_db.py` / `check_structure.py` / `check_mouvement_structure.py` / `check_mouvement_data.py` / `check_commande_structure.py` / `check_ligne_commande_structure.py` / `check_lot_reception.py` (7 scripts de vérification)
- **Correction :** Consolider en scripts génériques paramétrables. Supprimer les doublons (`test_reception_ui_fixed.py` semble être une version corrigée de `test_reception_ui.py`).

### 13. Token GitHub dans la documentation
- **Chemin :** `/opt/Projects/gestion_stocks_app_Postgres/procedure Git.md` (lignes 42-43)
- **Sévérité :** 🟡 MOYENNE
- **Description :** La documentation contient un exemple de clone Git avec token :
  ```
  git clone https://RHergot:ghp...@github.com/RHergot/Purchasing_Desk.git
  ```
  Bien que partiellement masqué, ce pattern expose la méthode d'authentification et le nom du repo.
- **Correction :** Remplacer par une référence générique sans nom d'utilisateur ni token.

### 14. Pas de gestion de sessions DB (connection pooling)
- **Chemin :** `/opt/Projects/gestion_stocks_app_Postgres/APP/services/db.py`
- **Sévérité :** 🟡 MOYENNE
- **Description :** La classe `Database` utilise une connexion unique sans pool. En environnement multi-utilisateurs, cela peut causer des problèmes de performance et de concurrence. Pas de `psycopg2.pool` utilisé.
- **Correction :** Implémenter `psycopg2.pool.SimpleConnectionPool` ou `ThreadedConnectionPool` pour les accès concurrents.

### 15. Fichier patch dans le code applicatif
- **Chemin :** `/opt/Projects/gestion_stocks_app_Postgres/APP/main_window_selection_menu_patch.py`
- **Sévérité :** 🟡 MOYENNE
- **Description :** Un fichier de "patch" est présent directement dans `APP/`. Cela suggère que le code n'a pas été correctement intégré ou que ce fichier est un résidu de développement. Contient des requêtes SQL qui devraient être dans les repositories.
- **Correction :** Intégrer les fonctionnalités dans le code principal ou déplacer dans `tools/`.

### 16. `psycopg2-binary` en production
- **Chemin :** `/opt/Projects/gestion_stocks_app_Postgres/requirements.txt` (ligne 9)
- **Sévérité :** 🟡 MOYENNE
- **Description :** `psycopg2-binary` est utilisé au lieu de `psycopg2`. La version binaire est conçue pour le développement, pas la production. Selon la doc psycopg2 : "The binary package is a practical choice for development and testing but in production it is advised to use the package built from sources."
- **Correction :** Remplacer par `psycopg2>=2.9.9` (compilation depuis les sources, nécessite `libpq-dev`).

### 17. Point d'entrée dupliqué
- **Chemin :** `/opt/Projects/gestion_stocks_app_Postgres/accueil.py`
- **Sévérité :** 🟡 MOYENNE
- **Description :** `accueil.py` à la racine est un point d'entrée alternatif qui importe et exécute l'application. Cela crée une ambiguïté sur le point d'entrée officiel (`APP/main.py`).
- **Correction :** Documenter ou supprimer. Un seul point d'entrée (`APP/main.py`) est préférable.

---

## 🟢 BASSE

### 18. `.gitignore` incomplet
- **Chemin :** `/opt/Projects/gestion_stocks_app_Postgres/.gitignore`
- **Sévérité :** 🟢 BASSE
- **Description :** Le `.gitignore` n'exclut pas :
  - `.env_old` et autres variantes de `.env*`
  - `*.dump` (fichiers de dump PostgreSQL)
  - `tests/` (si créé)
  - `tools/` (optionnel — contient des scripts de dev)
- **Correction :** Ajouter les patterns manquants.

### 19. `pyproject.toml` — scripts d'entrée commentés
- **Chemin :** `/opt/Projects/gestion_stocks_app_Postgres/pyproject.toml` (lignes 37-38)
- **Sévérité :** 🟢 BASSE
- **Description :** La section `[project.scripts]` est commentée. L'application n'a pas de commande CLI installable.
- **Correction :** Décommenter et activer `gestion-stocks = "APP.main:main"` quand `main()` sera prête.

### 20. Dépendances manquantes dans `pyproject.toml`
- **Chemin :** `/opt/Projects/gestion_stocks_app_Postgres/pyproject.toml`
- **Sévérité :** 🟢 BASSE
- **Description :** `requirements.txt` et `pyproject.toml` sont des sources de vérité séparées pour les dépendances — risque de désynchronisation.
- **Correction :** Utiliser uniquement `pyproject.toml` pour les dépendances (standard PEP 621) et supprimer `requirements.txt` ou le générer automatiquement.

### 21. Pas de gestion de version des dépendances
- **Chemin :** `/opt/Projects/gestion_stocks_app_Postgres/requirements.txt`
- **Sévérité :** 🟢 BASSE
- **Description :** Les dépendances utilisent `>=` sans limite supérieure, ce qui peut introduire des breaking changes. Pas de fichier `requirements-lock.txt` ou `poetry.lock`.
- **Correction :** Utiliser `pip freeze` pour générer un lock file, ou adopter Poetry/PDM.

### 22. `procedure Git.md` — procédure pour un autre projet
- **Chemin :** `/opt/Projects/gestion_stocks_app_Postgres/procedure Git.md`
- **Sévérité :** 🟢 BASSE
- **Description :** La documentation Git fait référence à `Purchasing_Desk`, `db.sqlite3`, `manage.py`, `web_sales` — des noms qui ne correspondent pas au projet actuel. Contenu copié d'un autre projet sans adaptation.
- **Correction :** Adapter au projet `gestion_stocks_app` ou supprimer.

### 23. `database/extraction db.md` — documentation pg_dump générique
- **Chemin :** `/opt/Projects/gestion_stocks_app_Postgres/database/extraction db.md`
- **Sévérité :** 🟢 BASSE
- **Description :** Documentation générique sur `pg_dump`. Utile mais non spécifique au projet.
- **Correction :** Adapter avec les paramètres réels de connexion du projet.

### 24. Fichiers `.md` dans `tools/`
- **Chemin :** `tools/*.md` (7 fichiers)
- **Sévérité :** 🟢 BASSE
- **Description :** Documentation de développement mélangée avec les scripts outils. Devrait être dans un dossier `docs/`.
- **Correction :** Déplacer dans `docs/` ou `tools/docs/`.

### 25. Aucun fichier `.env` dans `database/bu/`
- **Chemin :** `/opt/Projects/gestion_stocks_app_Postgres/database/bu/`
- **Sévérité :** 🟢 BASSE
- **Description :** Le dossier `database/bu/` contient des schémas SQL et un fichier `schemas.py`. L'organisation est confuse.
- **Correction :** Réorganiser en `database/schemas/` et `database/migrations/`.

---

## Analyse SQL Injection

**✅ RAS — Aucune vulnérabilité d'injection SQL détectée.**

Détails :
- Tous les fichiers APP utilisent des **requêtes paramétrées** avec `%s` (style psycopg2)
- `commande_repository.py` utilise `%(name)s` (named parameters) de manière sécurisée
- La méthode `db.execute(query, params)` délègue correctement à `cursor.execute(query, params)`
- Aucun `f"SELECT..."`, `f"INSERT..."`, `f"UPDATE..."` ou `f"DELETE..."` trouvé
- Aucun `.format()` utilisé pour construire des requêtes SQL (uniquement pour l'UI/traductions)
- Aucun `eval()`, `exec()`, `__import__()` trouvé (les `dialog.exec()` sont des appels Qt légitimes)
- Aucun `shell=True` dans les appels `subprocess`

---

## Analyse des Tests

**État : ❌ Pas de vrais tests automatisés.**

Le projet contient 20+ scripts `test_*.py` dans `tools/` mais :
- Pas de framework pytest/unittest
- Pas de `conftest.py`
- Pas de fixtures
- Pas de mocking — dépendance directe à PostgreSQL
- Pas d'intégration CI/CD possible sans base de données réelle
- Tests manuels uniquement (interaction utilisateur requise)

Certains scripts (`fix_reception_logic.py`, `test_reception_dialog_logic.py`) contiennent de la logique de test unitaire théorique mais sans assertions formelles.

---

## Analyse des Fichiers Racine

| Fichier | État | Commentaire |
|---------|------|-------------|
| `.env` | ⚠️ | Contient credentials en clair + mot de passe faible |
| `.env_old` | 🔴 | À SUPPRIMER — doublon non protégé |
| `.gitignore` | ⚠️ | Incomplet (manque `.env_old`, `*.dump`) |
| `pyproject.toml` | ✅ | Structure correcte, scripts à décommenter |
| `setup.py` | ✅ | Build Cython correct, fallback sans Cython |
| `requirements.txt` | ⚠️ | Utilise `psycopg2-binary` (dev, pas prod) |
| `accueil.py` | ⚠️ | Point d'entrée dupliqué |

---

## Recommandations Prioritaires

1. **IMMÉDIAT** : Supprimer `.env_old` et vérifier l'historique Git
2. **IMMÉDIAT** : Masquer le mot de passe dans les logs (`db.py`, `test_db_connection.py`)
3. **IMMÉDIAT** : Hacher le mot de passe Admin dans `commande_repository.py` avec bcrypt
4. **IMMÉDIAT** : Ajouter `.env_old`, `*.env_*` au `.gitignore`
5. **COURT TERME** : Créer `.env.example`, remplacer le mot de passe `.env` par un mot de passe fort
6. **COURT TERME** : Activer `sslmode=require` pour PostgreSQL
7. **COURT TERME** : Corriger le script `droits_table` (utilisateur `stock_app` → `gmao_app_user`)
8. **MOYEN TERME** : Mettre en place pytest avec fixtures et mocking DB
9. **MOYEN TERME** : Nettoyer `tools/` (supprimer doublons, consolider)
10. **MOYEN TERME** : Remplacer `psycopg2-binary` par `psycopg2` en production

---

*Audit généré automatiquement par scan transverse — 30 juin 2026*
