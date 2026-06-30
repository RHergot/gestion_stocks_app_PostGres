# Rapport d'Audit — Gestion de Stock/GMAO (gestion_stocks_app_Postgres)

**Date :** 30 juin 2026
**Stack :** PySide6 + PostgreSQL (psycopg2) · ~20 000 lignes Python
**Méthodologie :** 3 sous-agents en parallèle — couche Core (models/services/utils), couche UI (views/controllers/main), scan sécurité transverse + tools
**Fichiers lus :** 95 fichiers .py + fichiers racine (.env, .gitignore, pyproject.toml, etc.)

---

## Résumé Exécutif

| Sévérité | Nombre | Détail |
|----------|--------|--------|
| 🔴 CRITIQUE | 7 | Bugs bloquants + fuites de secrets |
| 🟠 HAUTE | 19 | Architecture, sécurité, duplication massive |
| 🟡 MOYENNE | 22 | Performance, qualité, tooling |
| 🟢 BASSE | 11 | Cosmétique, documentation |
| **Total** | **59** | |

---

## ✅ Ce qui est bien

- **Pattern MVC** globalement respecté (models → services → controllers → views)
- **Requêtes paramétrées** généralisées — pas d'injection SQL classique (f"SELECT ...")
- **i18n** avec Qt `self.tr()` + dictionnaires FR/EN — système fonctionnel
- **Double langue** FR/EN opérationnelle via `Language` enum + `AppConfig`
- **Cython-ready** via `setup.py` — possibilité de compilation pour la distribution
- **`.gitignore`** présent et correct pour `.env`, `__pycache__`, `venv/`
- **Séparation des responsabilités** globalement comprise (repositories/services distinctes)
- **Gestion FK** avec `get_delete_blockers()` dans `PieceService` — bonne pratique

---

## 🔴 CRITIQUE (7) — Urgence immédiate

### C1 — PieceService cassé : AttributeError garanti à l'exécution
- **Fichier :** `APP/services/piece_service.py:35-38, 60-63`
- `add_piece()` et `update_piece()` appellent `self._get_nom_from_id()` avec `self.parent_unit_list`, `self.parent_category_list`, etc.
- **Ces attributs ne sont JAMAIS initialisés.** Toute création/modification de pièce → `AttributeError`.
- **Correction :** Initialiser ces listes dans `__init__()` ou faire des requêtes SQL ciblées.

### C2 — Injection SQL via noms de colonnes interpolés
- **Fichiers :** `APP/models/commande_repository.py:77,144` · `APP/models/ligne_commande_repository.py:177`
- Construction de requêtes avec f-strings pour les noms de colonnes (`f"UPDATE commande SET {set_clause}"`). Les noms viennent de `cleaned_data.keys()` — potentiellement injectables.
- **Correction :** Whitelist stricte des colonnes autorisées avant interpolation.

### C3 — Mot de passe Admin `admin123` hardcodé EN CLAIR
- **Fichier :** `APP/models/commande_repository.py:305-323`
- `get_default_user_id()` crée automatiquement un Admin avec `'admin123'` stocké tel quel dans `mot_de_passe_hash`. Ni haché, ni salé.
- **Correction :** Supprimer cette fonction. Hacher via bcrypt (déjà dans les dépendances !). Script d'init séparé.

### C4 — Mot de passe PostgreSQL affiché en clair dans stdout
- **Fichiers :** `APP/services/db.py:24-26` · `tools/test_db_connection.py:111-114`
- `for key, value in os.environ.items(): if key.startswith('POSTGRES_'): print(f"{key} = {value}")` — affiche `POSTGRES_PASSWORD=mot_de_passe_fort` dans la console et les logs.
- **Correction :** Masquer `*PASSWORD*` dans l'affichage (`***`).

### C5 — `.env_old` doublon de secrets NON protégé par `.gitignore`
- **Fichier :** `.env_old` (racine)
- Contient les mêmes credentials que `.env` mais n'est PAS dans `.gitignore`. Risque de commit Git accidentel.
- **Correction :** Supprimer `.env_old` immédiatement. Ajouter `*.env_*` au `.gitignore`. Vérifier `git log` pour s'assurer qu'il n'a jamais été commité.

### C6 — Méthodes orphelines dans `mouvement_table_view.py`
- **Fichier :** `APP/views/mouvement_table_view.py:865-925`
- Trois fonctions définies HORS classe avec `self.mouvement_controller` qui n'existe pas dans ce scope. Code mort qui causerait des `NameError` si exécuté. Dupliquent des méthodes déjà dans la classe.
- **Correction :** Supprimer les lignes 865-925.

### C7 — Clé de dictionnaire incorrecte → KeyError
- **Fichier :** `APP/views/mise_en_stock_dialog.py:186`
- `dest_data['id_emplacement']` alors que les données sont stockées avec la clé `'id'` (cf. `load_data()` ligne 152). Provoque `KeyError` à l'exécution.
- **Correction :** Remplacer `'id_emplacement'` par `'id'`.

---

## 🟠 HAUTE (19) — Corriger rapidement

### Architecture

**H1 — Schéma SQLite vs PostgreSQL — incompatibilité fondamentale**
- `database/bu/schemas.py` (554 lignes, 26K) utilise la syntaxe SQLite (`AUTOINCREMENT`, triggers `FOR EACH ROW BEGIN...END`) mais le runtime est PostgreSQL via psycopg2. Soit le schéma est un artéfact, soit il est cassé.
- **Correction :** Réécrire en syntaxe PostgreSQL ou confirmer que `schemas.py` n'est plus utilisé.

**H2 — Duplication complète `i18n.py` / `i18ny.py`**
- `APP/utils/i18n.py` et `APP/utils/i18ny.py` sont identiques à 2 lignes près. Même code dans deux fichiers ≠ source unique de vérité.
- **Correction :** Supprimer `i18ny.py`, ne garder que `i18n.py`.

**H3 — Deux patterns d'accès DB incompatibles**
- Certains repos utilisent `self.db.execute(query, params)`, d'autres `self.db.conn.cursor()` directement. Mélange de `RealDictCursor` vs cursor standard. Incohérence dans la gestion des transactions.
- **Correction :** Uniformiser sur un seul pattern (recommandation : `db.execute()` partout).

**H4 — God Object `commande_view.py` (1116 lignes)**
- 3 responsabilités : modèles de données (TableModel), vue (affichage), logique métier (workflow statuts, copie, numérotation). Violation du principe de responsabilité unique.
- **Correction :** Splitter en `models/commande_table_model.py`, `controllers/commande_controller.py`, vue allégée < 300 lignes.

**H5 — God Object `commande_dialog.py` (949 lignes)**
- Logique métier (`_creer_mouvements_livraison()`, `_changer_statut()`) + DDL SQL (`CREATE TABLE IF NOT EXISTS`) dans un dialog UI.
- **Correction :** Déléguer toute logique métier au contrôleur/service. Supprimer le DDL des vues.

**H6 — Logique métier et SQL direct dans `main_window.py`**
- 6 méthodes (`show_stock_faible`, `show_pieces_by_machine`, etc.) exécutent du SQL avec JOINs directement dans la fenêtre principale.
- **Correction :** Déplacer vers un `RapportService` ou le `MouvementController`.

**H7 — Duplication massive `main_window_selection_menu_patch.py`**
- Duplique intégralement 5 méthodes de `main_window.py` + n'est jamais importé (menu "Selection" inaccessible). Code mort et dangereux (définitions conflictuelles).
- **Correction :** Supprimer le fichier. Intégrer le menu Selection directement dans `MainWindow._create_menu_bar()`.

**H8 — `accueil.py` — point d'entrée Windows-only incompatible**
- Chemins Windows hardcodés (`C:\\Users\\Public\\.vscode\\...`), `subprocess.Popen`, référence un autre projet. Inutilisable sous Linux.
- **Correction :** Supprimer ou déplacer dans `legacy/`.

**H9 — Absence de classe de base CRUD (11 paires dialog/table_view)**
- `fabricant`, `site`, `type_machine`, `fournisseur`, `user`, `piece_unit`, `piece_statut`, `piece_category`, `machine`, `piece`, `emplacement` — toutes implémentent le même pattern sans héritage commun.
- **Correction :** Créer `BaseTableView` et `BaseDialog` avec méthodes génériques.

**H10 — 9 services pass-through sans valeur ajoutée**
- `user_service.py`, `machine_service.py`, `fabricant_service.py`, etc. délèguent 100% au repository sans logique métier. Couche d'indirection pure.
- **Correction :** Ajouter validation/règles métier, ou supprimer ces services et appeler les repos directement.

**H11 — SQL direct dans les vues (bypass couche service)**
- `piece_table_view.py` (5 méthodes), `ligne_commande_dialog.py`, `reception_dialog.py` exécutent du SQL via `self.db.conn.cursor()`.
- **Correction :** Tout doit passer par les services. Les vues ne doivent jamais accéder à `db.conn`.

### Sécurité

**H12 — SHA-256 sans sel pour les mots de passe**
- `APP/views/user_dialog.py:35` — `hashlib.sha256(...).hexdigest()`. Vulnérable aux rainbow tables.
- **Correction :** Utiliser `bcrypt` (déjà dans `requirements.txt` !) ou `hashlib.pbkdf2_hmac`.

**H13 — ID utilisateur hardcodé à 1**
- `APP/views/reception_dialog.py:335` — `utilisateur_id = 1` dans un INSERT SQL. Placeholder.
- **Correction :** Récupérer l'utilisateur connecté depuis le contexte applicatif.

**H14 — Pas de validation des entrées utilisateur**
- Aucun repository/service ne valide types, longueurs, formats (email, téléphone), ou valeurs autorisées.
- **Correction :** Ajouter validation dans les services (types, ranges, whitelists).

**H15 — Pas de SSL/TLS pour PostgreSQL**
- `POSTGRES_OPTIONS=sslmode=require` est commenté dans `.env`. Connexion non chiffrée.
- **Correction :** Activer `sslmode=require` en production.

**H16 — Double chargement `.env` incompatible**
- `db.py` utilise `POSTGRES_*`, `env_loader.py` utilise `DB_*`. Deux systèmes concurrents.
- **Correction :** Unifier sur un seul schéma de variables.

### Qualité

**H17 — `print()` comme mécanisme de logging (46+ occurrences)**
- `db.py` (22), `commande_view.py` (30+), `warehouse_layout_view.py` (30+), `emplacement_ext_service.py` (14), etc.
- **Correction :** Remplacer par le module `logging` avec niveaux appropriés.

**H18 — Configuration logging multiple et incohérente**
- `logging.basicConfig()` appelé dans 2 repositories différents. Configuration écrasée aléatoirement.
- **Correction :** Centraliser la config logging dans `main.py` uniquement.

**H19 — Pas d'internationalisation dans plusieurs fichiers UI**
- `fabricant_dialog.py`, `fabricant_table_view.py`, `ligne_commande_dialog.py`, `reception_dialog.py` — chaînes en dur, pas de `self.tr()`.
- **Correction :** Wrapper toutes les chaînes visibles avec `self.tr()`.

---

## 🟡 MOYENNE (22) — Dette technique

### Bugs potentiels
- **M1** — Suppression commande sans rollback atomique (`commande_repository.py:186-202`)
- **M2** — TODO non implémenté dans `mouvement_service.py:473` (`pass` après `# TODO: Implémenter`)
- **M3** — Try/except nu (`except Exception: pass`) dans `piece_service.py:123-125, 164-166`
- **M4** — Cache `_default_user_id` non invalidé dans `commande_repository.py:13`
- **M5** — Double définition `get_lignes_data()` dans `commande_dialog.py:504, 659` (seconde écrase la première)
- **M6** — Incohérence nombre colonnes dans `piece_table_view.py` (12 puis 13)
- **M7** — `select_commande()` ne fonctionne pas — `Qt.UserRole` non supporté (`commande_view.py:786`)
- **M8** — `Incohérence impact_stock` contrainte CHECK (-1,1) mais code utilise 0 (`schemas.py:243`, `mouvement_service.py:578`)

### Performance
- **M9** — Recherche N+1 : `list_machines()` charge tout puis boucle linéaire (`piece_service.py:42-46`)
- **M10** — `_get_nom_from_id()` scan linéaire O(n) au lieu de dict ou requête ciblée
- **M11** — Sous-requête au lieu de JOIN dans `mouvement_repository.py:42-49`
- **M12** — `_generer_nouveau_numero()` charge toutes les commandes puis max() en Python — O(n)
- **M13** — Pas de pagination dans `mouvement_table_view.py` (charge tout en mémoire)
- **M14** — `CREATE TABLE IF NOT EXISTS` exécuté à chaque ouverture de dialogue (`commande_dialog.py:228`)

### Architecture
- **M15** — `mouvement_controller.py` trop volumineux (679 lignes, 8 types d'opérations + rapports)
- **M16** — Lazy imports dans contrôleurs (`mouvement_controller.py:371,381` — `ReceptionWorkflowService` importé dans les méthodes)
- **M17** — Accès chaîné fragile : `parent.parent().db` (`machine_dialog.py:22`)
- **M18** — Pas de couche DTO/transformation — `RealDictRow` propagé jusqu'aux vues
- **M19** — `env_loader.py` redondant/non utilisé (double de `db.py` avec noms différents)

### Tooling / Sécurité
- **M20** — Pas de framework de tests automatisés (pytest) — 20+ scripts `test_*.py` manuels dans `tools/`
- **M21** — Scripts `tools/` dupliqués (48 fichiers, forte redondance)
- **M22** — Droits RBAC désalignés : `droits_table` accorde à `stock_app`, l'app utilise `gmao_app_user`

---

## 🟢 BASSE (11) — Améliorations continues

- **B1** — `.gitignore` incomplet (manque `.env_old`, `*.dump`)
- **B2** — `pyproject.toml` : scripts d'entrée commentés (`[project.scripts]`)
- **B3** — Dépendances désynchronisées (`requirements.txt` vs `pyproject.toml`)
- **B4** — Pas de lock file (`requirements-lock.txt` ou `poetry.lock`)
- **B5** — `psycopg2-binary` au lieu de `psycopg2` en production
- **B6** — `procedure Git.md` fait référence à un autre projet (Purchasing_Desk, SQLite)
- **B7** — Fichiers `.md` dans `tools/` — devraient être dans `docs/`
- **B8** — Convention de nommage incohérente (méthodes FR/EN mélangées, tables MAJ/min)
- **B9** — Langue des logs mixée français/anglais
- **B10** — Import dupliqué dans `main_window.py:1-3, 6-8`
- **B11** — Boutons d'action non standardisés (OK/Cancel, Validate/Cancel, Save/Close, ...)

---

## Plan d'Action Priorisé

### Phase 1 — CRITIQUE (7 problèmes — ~8h)
Corrections immédiates, une par une avec test entre chaque :

1. **C1** — Initialiser `parent_unit_list`, etc. dans `PieceService.__init__()` → l'app fonctionne
2. **C7** — Corriger `id_emplacement` → `id` dans `mise_en_stock_dialog.py:186`
3. **C6** — Supprimer les méthodes orphelines (l.865-925) de `mouvement_table_view.py`
4. **C3** — Supprimer `get_default_user_id()` + mot de passe `admin123` → script d'init externe
5. **C4** — Masquer `POSTGRES_PASSWORD` dans les logs (`db.py`, `test_db_connection.py`)
6. **C5** — Supprimer `.env_old` + ajouter au `.gitignore` + vérifier `git log`
7. **C2** — Ajouter whitelist de colonnes dans `commande_repository.py` et `ligne_commande_repository.py`

### Phase 2 — HAUTE (19 problèmes — ~20h)

1. Supprimer `main_window_selection_menu_patch.py` + `accueil.py` + `i18ny.py` (H7, H8, H2)
2. Déplacer SQL direct de `main_window.py` vers `RapportService` (H6)
3. Créer `BaseTableView` + `BaseDialog` pour éliminer duplication CRUD (H9)
4. Uniformiser pattern DB : `db.execute()` partout (H3)
5. Remplacer SHA-256 par bcrypt dans `user_dialog.py` (H12)
6. Activer `sslmode=require` PostgreSQL (H15)
7. Remplacer tous les `print()` par `logging` (H17)
8. Centraliser la config logging dans `main.py` (H18)
9. Ajouter `self.tr()` dans les fichiers UI non i18n (H19)
10. Ajouter validation d'entrée dans les services (H14)
11. Corriger ID utilisateur hardcodé → contexte applicatif (H13)
12. Splitter `commande_view.py` et `commande_dialog.py` (H4, H5 — ~6h chacun)

### Phase 3 — MOYENNE (22 problèmes — ~15h)
- Consolider `tools/` (supprimer doublons) → M21
- Mettre en place pytest avec fixtures → M20
- Extraire `ReceptionController` de `mouvement_controller.py` → M15
- Optimiser requêtes N+1 → M9, M10, M11, M12
- Implémenter pagination → M13
- Nettoyer DDL des vues → M14
- Supprimer/consolider `env_loader.py` → M19

### Phase 4 — BASSE (11 problèmes — ~4h)
- Compléter `.gitignore` → B1
- Générer lock file → B4
- Uniformiser conventions de nommage → B8
- Nettoyer imports dupliqués → B10
- Adapter `procedure Git.md` → B6

---

## Structure du Projet avec Marquage des Problèmes

```
gestion_stocks_app_Postgres/
├── .env                          ⚠️ C4 (password loggé), H15 (SSL off)
├── .env_old                      🔴 C5 (secrets non protégés)
├── .gitignore                    ⚠️ B1 (incomplet)
├── requirements.txt              ⚠️ B3, B5 (psycopg2-binary)
├── pyproject.toml                ⚠️ B2, B3
├── setup.py                      ✅ Correct
├── accueil.py                    ❌ H8 (Windows-only, à supprimer)
├── APP/
│   ├── main.py                   ⚠️ H17 (print() debug)
│   ├── main_window.py            ❌ H6 (SQL direct), B10 (imports dupliqués)
│   ├── main_window_selection_menu_patch.py  🔴 C6? ❌ H7 (duplication, jamais appelé)
│   ├── droits_table               ⚠️ M22 (RBAC désaligné)
│   ├── controllers/
│   │   └── mouvement_controller.py  ⚠️ M15 (679 lignes), M16 (lazy imports)
│   ├── models/
│   │   ├── commande_repository.py   🔴 C2 (f-string SQL), 🔴 C3 (admin123), M4 (cache)
│   │   ├── ligne_commande_repository.py  🔴 C2 (f-string SQL), H18 (basicConfig)
│   │   ├── mouvement_repository.py  ⚠️ M5?, M11 (sous-requête), M8 (impact_stock)
│   │   ├── piece_repository.py      ✅ Correct (pattern cible)
│   │   └── ... (13 autres repos)    ⚠️ H10 (6 quasi identiques)
│   ├── services/
│   │   ├── db.py                    🔴 C4 (password stdout), ⚠️ H16 (double .env)
│   │   ├── piece_service.py         🔴 C1 (AttributeError), M3 (bare except), M9, M10
│   │   ├── mouvement_service.py     ⚠️ M2 (TODO), M8 (impact_stock)
│   │   └── ... (14 autres services) ⚠️ H10 (9 pass-through), H17 (print())
│   ├── utils/
│   │   ├── i18n.py                  ✅ Garder
│   │   ├── i18ny.py                 ❌ H2 (doublon parfait, à supprimer)
│   │   └── env_loader.py            ⚠️ M19 (redondant)
│   └── views/
│       ├── commande_view.py         ❌ H4 (God Object 1116 lignes)
│       ├── commande_dialog.py       ❌ H5 (God Object 949 lignes), M5 (double def), M14 (DDL)
│       ├── mouvement_table_view.py  🔴 C6 (méthodes orphelines), M13 (pas pagination)
│       ├── mise_en_stock_dialog.py  🔴 C7 (KeyError id_emplacement→id)
│       ├── reception_dialog.py      ⚠️ H13 (user_id=1), H11 (SQL direct)
│       ├── user_dialog.py           ⚠️ H12 (SHA-256 sans sel)
│       ├── piece_table_view.py      ⚠️ M6 (colonnes 12→13), H11 (SQL direct)
│       ├── warehouse_layout_view.py ⚠️ H17 (30+ print DEBUG)
│       └── ... (23 autres vues)     ⚠️ H9 (pas BaseTableView), H19 (pas i18n)
├── database/
│   ├── bu/
│   │   └── schemas.py               🔴 H1 (SQLite vs PostgreSQL, 26K monolithique)
│   ├── database_complete_consolidated.sql  (61K)
│   └── mon_schema_complet.sql       (319K dump complet)
└── tools/                           ⚠️ M21 (48 fichiers, doublons), M20 (pas pytest)
    └── (48 fichiers test/debug/init)
```

---

## Analyse de Sécurité Globale

| Contrôle | Statut | Détail |
|----------|--------|--------|
| Injection SQL (f-strings) | ⚠️ | Colonnes interpolées sans whitelist (C2) |
| Injection SQL (valeurs) | ✅ | Requêtes paramétrées %s partout |
| Mots de passe hardcodés | 🔴 | `admin123` en clair (C3) |
| Hashage mots de passe | 🔴 | SHA-256 sans sel (H12) — bcrypt dispo mais inutilisé |
| Secrets en stdout | 🔴 | POSTGRES_PASSWORD affiché (C4) |
| Secrets dans .env | ⚠️ | Mot de passe faible + .env_old non protégé (C5) |
| SSL/TLS PostgreSQL | 🔴 | Désactivé — `sslmode` commenté (H15) |
| RBAC | ⚠️ | Script `droits_table` utilisateur incorrect (M22) |
| Validation entrées | ❌ | Aucune validation (H14) |
| Logging | ❌ | `print()` non structuré, config multiple (H17, H18) |
| Tests automatisés | ❌ | Aucun framework, scripts manuels (M20) |
| eval/exec/shell=True | ✅ | Aucun trouvé (les `dialog.exec()` sont Qt) |
| Connection pooling | ❌ | Connexion unique (M24) |

---

*Rapport consolidé généré après fusion de 3 audits parallèles — 95 fichiers Python lus exhaustivement.*
*Les 3 rapports intermédiaires sont disponibles dans `/opt/Projects/gestion_stocks_app_Postgres/audit_core.md`, `audit_ui.md`, `audit_security.md`.*
