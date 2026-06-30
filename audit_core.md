# Rapport d'Audit — Couche CORE
**Projet**: `gestion_stocks_app_Postgres`  
**Date**: 30 juin 2026  
**Périmètre**: `APP/models/` (17 repositories), `APP/services/` (17 services + `db.py`), `APP/utils/` (3 fichiers), `database/bu/schemas.py`  
**Méthodologie**: Lecture exhaustive de chaque fichier `.py` dans le périmètre défini

---

## Résumé

| Catégorie    | CRITIQUE | HAUTE | MOYENNE | BASSE | Total |
|-------------|----------|-------|---------|-------|-------|
| Bugs         | 3        | 2     | 1       | 0     | 6     |
| Sécurité     | 2        | 4     | 2       | 1     | 9     |
| Architecture | 2        | 4     | 2       | 2     | 10    |
| Performance  | 0        | 2     | 2       | 1     | 5     |
| Qualité      | 0        | 2     | 4       | 3     | 9     |

---

## 1. BUGS

### BUG-001 — CRITIQUE: Attributs non initialisés dans PieceService (AttributeError à l'exécution)

- **Fichier**: `APP/services/piece_service.py`
- **Lignes**: 35-38, 60-63
- **Description**: Les méthodes `add_piece()` et `update_piece()` appellent `self._get_nom_from_id()` en passant `self.parent_unit_list`, `self.parent_category_list`, `self.parent_emplacement_list` et `self.parent_statut_list`. Ces attributs **ne sont jamais initialisés** dans `__init__()` (lignes 11-16). Toute création ou mise à jour de pièce lèvera une `AttributeError` à l'exécution.
- **Correction**: 
  - Soit initialiser ces listes dans `__init__()` en interrogeant les repositories appropriés (ex: `self.parent_unit_list = PieceUnitRepository(db).get_all_units()`)
  - Soit refactoriser pour charger les noms via des requêtes SQL ciblées plutôt que des listes complètes

### BUG-002 — CRITIQUE: Injection SQL par f-string dans les requêtes dynamiques

- **Fichiers**:
  - `APP/models/commande_repository.py` — lignes 77, 144
  - `APP/models/ligne_commande_repository.py` — ligne 177
- **Description**: Construction de requêtes SQL avec f-strings où les noms de colonnes (issus de `fields`, `set_clause`, `cleaned_data.keys()`) sont interpolés directement dans la requête. Bien que les valeurs soient passées via paramètres `%(name)s`, les noms de colonnes proviennent de données potentiellement contaminées (input utilisateur via `commande_data` et `ligne_data`). Un attaquant pourrait injecter des noms de colonnes malveillants.
- **Correction**:
  - Valider les noms de champs contre une liste blanche (whitelist) avant interpolation
  - Utiliser une liste fixe et exhaustive de colonnes autorisées
  ```python
  ALLOWED_COLUMNS = {'numero_commande', 'fournisseur_id', ...}
  for f in fields:
      if f not in ALLOWED_COLUMNS:
          raise ValueError(f"Colonne non autorisée: {f}")
  ```

### BUG-003 — CRITIQUE: Schéma SQLite utilisé avec PostgreSQL

- **Fichier**: `database/bu/schemas.py`
- **Lignes**: 1-554 (tout le fichier)
- **Description**: Le dictionnaire `TABLES` contient des instructions SQL utilisant la syntaxe SQLite (`INTEGER PRIMARY KEY AUTOINCREMENT`, `TEXT`, `CURRENT_TIMESTAMP`, triggers avec `FOR EACH ROW BEGIN...END`). Le projet utilise PostgreSQL via `psycopg2`. Ces schémas ne fonctionneront pas sur PostgreSQL, ou produiront des tables avec des types incorrects.
- **Correction**:
  - Remplacer `INTEGER PRIMARY KEY AUTOINCREMENT` par `SERIAL PRIMARY KEY` ou `INTEGER GENERATED ALWAYS AS IDENTITY`
  - Remplacer `TEXT` par `VARCHAR(n)` ou `TEXT` (PostgreSQL accepte TEXT mais le typage doit être vérifié)
  - Remplacer `CURRENT_TIMESTAMP` par `NOW()` ou `CURRENT_TIMESTAMP` (fonctionne mais le format diffère)
  - Remplacer la syntaxe de trigger SQLite par la syntaxe PL/pgSQL (`CREATE OR REPLACE FUNCTION ... RETURNS TRIGGER`)

### BUG-004 — HAUTE: Incohérence impact_stock dans TYPE_MOUVEMENT

- **Fichier**: `database/bu/schemas.py`, ligne 243
- **Description**: La colonne `impact_stock` a une contrainte `CHECK (impact_stock IN (-1, 1))` mais le code métier dans `mouvement_service.py` (lignes 578, 44-45) utilise `impact_stock = 0` pour les types de mouvement de réception (RECEPTION_ACHAT). La contrainte CHECK empêcherait d'insérer ces types de mouvement.
- **Correction**: Modifier la contrainte en `CHECK (impact_stock IN (-1, 0, 1))` pour accepter les mouvements neutres.

### BUG-005 — HAUTE: Fichier mouvements_repository.py tronqué

- **Fichier**: `APP/models/mouvement_repository.py`
- **Ligne**: 270
- **Description**: La méthode `delete_type_mouvement` s'arrête brutalement à la ligne 270 (`self.db.conn.commit()` sans `return` ni fermeture de méthode). Le fichier semble tronqué — la méthode de la classe `TypeMouvementRepository` n'est pas correctement terminée.
- **Correction**: Ajouter la fermeture de la méthode et vérifier l'intégralité du fichier.

### BUG-006 — MOYENNE: Suppression de commande sans rollback sur échec partiel

- **Fichier**: `APP/models/commande_repository.py`, lignes 186-202
- **Description**: `delete_commande()` supprime d'abord les lignes (`DELETE FROM ligne_commande`) puis la commande. Si la suppression des lignes réussit mais que celle de la commande échoue, les lignes sont déjà supprimées sans rollback. La transaction n'est commitée qu'après les deux opérations, donc en théorie ça devrait être atomique (merci psycopg2 en mode transaction), **mais** il n'y a pas de `BEGIN` explicite et le `rollback` en cas d'exception ne restaurera pas les lignes déjà supprimées si la connexion n'est pas en mode transactionnel.
- **Correction**: Encapsuler dans un bloc `try/except` avec `rollback()` explicite.

---

## 2. SÉCURITÉ

### SEC-001 — CRITIQUE: Mot de passe admin hardcodé en clair

- **Fichier**: `APP/models/commande_repository.py`, ligne 317
- **Description**: La méthode `get_default_user_id()` crée un utilisateur Admin avec le mot de passe `'admin123'` stocké **en clair** dans le champ `mot_de_passe_hash`. Commentaire dit "À remplacer par un vrai hash en production" mais le code est déployable.
- **Correction**:
  - Ne jamais créer d'utilisateur par défaut avec mot de passe hardcodé
  - Utiliser un mécanisme de seeding sécurisé (ex: script d'initialisation séparé)
  - Hasher le mot de passe avec bcrypt/scrypt/argon2 avant insertion
  - Supprimer cette fonction du repository (violation du principe de responsabilité unique)

### SEC-002 — CRITIQUE: Fuite d'informations de connexion DB dans les logs/print

- **Fichier**: `APP/services/db.py`, lignes 10-27, 41-47
- **Description**: La classe `Database` affiche via `print()` le chemin du fichier `.env`, toutes les variables d'environnement `POSTGRES_*`, et les paramètres de connexion (hôte, port, dbname, user). Ces informations sensibles sont visibles dans la sortie standard, les logs applicatifs, et potentiellement dans les logs système.
- **Correction**:
  - Remplacer tous les `print()` par un logger avec niveau DEBUG
  - Ne jamais logger les variables d'environnement
  - Masquer les informations sensibles (user) dans les logs de production

### SEC-003 — HAUTE: Absence de validation des entrées utilisateur dans les repositories

- **Fichiers**: Tous les repositories dans `APP/models/`
- **Description**: Aucun repository ne valide les données entrantes avant insertion SQL. Les valeurs sont passées directement comme paramètres de requête. Bien que les requêtes paramétrées protègent contre l'injection SQL, il n'y a pas de validation de type, longueur, format, ou valeurs autorisées (ex: email, téléphone).
- **Correction**: Ajouter une couche de validation dans les services (ou repositories) avec:
  - Validation de types (int, float, str)
  - Validation de longueurs maximales
  - Validation de formats (email, téléphone)
  - Validation de valeurs autorisées (statuts, rôles)

### SEC-004 — HAUTE: Mot de passe DB par défaut vide

- **Fichier**: `APP/services/db.py`, ligne 35
- **Description**: La valeur par défaut pour `POSTGRES_PASSWORD` est une chaîne vide `''`. Si le fichier `.env` est absent, la connexion tente de s'établir sans mot de passe.
- **Correction**: Ne pas fournir de valeur par défaut pour le mot de passe, ou lever une exception explicite si `POSTGRES_PASSWORD` n'est pas défini.

### SEC-005 — HAUTE: Double chargement .env avec variables différentes

- **Fichiers**: `APP/services/db.py` (lignes 20, 30-36) vs `APP/utils/env_loader.py` (lignes 10-14)
- **Description**: Deux mécanismes incompatibles de chargement de configuration DB:
  - `db.py` utilise les variables `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
  - `env_loader.py` utilise `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
  
  Si les deux sont utilisés, un seul jeu de variables sera chargé. Risque de connexion avec de mauvais paramètres.
- **Correction**: Unifier sur un seul jeu de variables d'environnement et un seul point de chargement.

### SEC-006 — HAUTE: Logging de données sensibles

- **Fichier**: `APP/models/commande_repository.py`, lignes 85-86
- **Description**: `logger.debug()` affiche la requête SQL complète et les données utilisateur, incluant potentiellement des informations sensibles.
- **Correction**: Ne logger que les métadonnées (ID, timestamps), pas le contenu complet des données.

### SEC-007 — MOYENNE: Pas de gestion de sessions ou timeouts de connexion

- **Fichier**: `APP/services/db.py`
- **Description**: La connexion DB est établie sans paramètres de timeout, keepalive, ou reconnexion automatique. Une connexion idle peut être coupée par le serveur PostgreSQL sans que l'application ne le détecte.
- **Correction**: Configurer `keepalives`, `connect_timeout`, et implémenter un mécanisme de reconnexion ou un pool de connexions.

### SEC-008 — MOYENNE: Pas de chiffrement de la connexion DB

- **Fichier**: `APP/services/db.py`, ligne 49
- **Description**: La connexion PostgreSQL est établie sans `sslmode`. Selon la configuration réseau, les données transitent potentiellement en clair.
- **Correction**: Ajouter `sslmode='require'` (ou `verify-full`) dans les paramètres de connexion.

### SEC-009 — BASSE: Commentaire indiquant des validations manquantes

- **Fichier**: `APP/services/user_service.py`, ligne 11
- **Description**: Le commentaire `# Ici, on pourrait ajouter des validations` confirme l'absence intentionnelle de validation.
- **Correction**: Ajouter les validations ou supprimer le commentaire.

---

## 3. ARCHITECTURE

### ARCH-001 — CRITIQUE: Schéma SQL dans un seul fichier monolithique de 26K

- **Fichier**: `database/bu/schemas.py`
- **Lignes**: 1-554
- **Description**: 26K de code SQL dans un seul dictionnaire Python. Mélange tables (15+), indexes (15+), triggers (10+), et données de seed. Impossible à maintenir. La moindre modification de schéma nécessite de naviguer dans 554 lignes.
- **Correction**:
  - Diviser en fichiers séparés: `tables.sql`, `indexes.sql`, `triggers.sql`, `seed_data.sql`
  - Ou utiliser un outil de migration (Alembic, Flyway)
  - Regrouper par domaine fonctionnel: `stock/`, `maintenance/`, `achats/`

### ARCH-002 — CRITIQUE: Incompatibilité schéma SQLite vs PostgreSQL

- **Fichier**: `database/bu/schemas.py`
- **Description**: Voir BUG-003. Le schéma entier est écrit en syntaxe SQLite alors que le runtime utilise psycopg2 → PostgreSQL. Soit le projet a migré de SQLite vers PostgreSQL sans mettre à jour les schémas, soit schemas.py est un artéfact.
- **Correction**: Réécrire tous les schémas en syntaxe PostgreSQL (SERIAL, VARCHAR, PL/pgSQL triggers, etc.) ou confirmer que `schemas.py` n'est plus utilisé.

### ARCH-003 — HAUTE: Duplication complète i18n.py / i18ny.py

- **Fichiers**: `APP/utils/i18n.py` et `APP/utils/i18ny.py`
- **Description**: Les deux fichiers sont quasi-identiques (199 vs 201 lignes). Différence unique: `i18ny.py` a 2 lignes blanches supplémentaires. C'est une duplication à 100% du code. Import ambigu selon le fichier référencé.
- **Correction**: Supprimer `i18ny.py` et n'utiliser que `i18n.py`. Vérifier tous les imports.

### ARCH-004 — HAUTE: Deux patterns d'accès DB incompatibles

- **Fichiers**: Plusieurs repositories
- **Description**: Deux modèles d'accès à la base coexistent sans cohérence:
  1. Via `self.db.execute(query, params)` — utilisé par `UserRepository`, `SiteRepository`, `FabricantRepository`, `TypeMachineRepository`, `MachineRepository`
  2. Via `self.db.conn.cursor()` directement — utilisé par `PieceRepository`, `FournisseurRepository`, `EmplacementRepository`, `MouvementRepository`, `CommandeRepository`, etc.
  
  Les repositories du modèle 1 délèguent la gestion de transaction à `Database.execute()`, ceux du modèle 2 gèrent `commit()` et `rollback()` manuellement. Certains utilisent `RealDictCursor`, d'autres non.
- **Correction**: Uniformiser sur un seul pattern. Recommandation: toujours utiliser `db.execute()` ou créer un contexte `db.transaction()`.

### ARCH-005 — HAUTE: Services pass-through sans valeur ajoutée

- **Fichiers**: `APP/services/` — `user_service.py`, `machine_service.py`, `fabricant_service.py`, `site_service.py`, `type_machine_service.py`, `piece_unit_service.py`, `piece_statut_service.py`, `piece_category_service.py`, `piece_extension_service.py`
- **Description**: 9 services sur 17 sont de simples wrappers qui déléguent 100% de leurs appels au repository sans aucune logique métier, validation, transformation, ou gestion d'erreur. Ces classes ajoutent une couche d'indirection sans valeur.
- **Correction**:
  - Soit ajouter de la logique métier (validation, règles, orchestration)
  - Soit supprimer ces services et appeler les repositories directement si le pattern MVC ne nécessite pas cette couche

### ARCH-006 — HAUTE: Duplication de code dans les repositories CRUD

- **Fichiers**: `APP/models/` — `site_repository.py`, `fabricant_repository.py`, `type_machine_repository.py`, `piece_unit_repository.py`, `piece_statut_repository.py`, `piece_category_repository.py`
- **Description**: Les repositories simples suivent tous le même pattern CRUD avec un code quasi identique (get_all, add, update, delete). Différence principale: noms de tables et colonnes. ~6 repositories pourraient être remplacés par une classe générique paramétrée.
- **Correction**: Créer une classe `BaseRepository` avec des méthodes CRUD génériques utilisant la métaclasse ou la composition.

### ARCH-007 — MOYENNE: env_loader.py non utilisé ou redondant

- **Fichier**: `APP/utils/env_loader.py`
- **Description**: `load_env()` retourne un dictionnaire avec `DB_HOST`, `DB_NAME`, etc., mais la classe `Database` dans `db.py` fait son propre chargement avec des noms de variables différents (`POSTGRES_*`). Soit `env_loader.py` n'est pas utilisé, soit il est utilisé ailleurs de manière incohérente.
- **Correction**: Supprimer `env_loader.py` ou l'unifier avec le chargement de `db.py`.

### ARCH-008 — MOYENNE: Dépendance circulaire potentielle

- **Fichier**: `APP/services/piece_service.py` (lignes 3-4)
- **Description**: `PieceService` importe `MachineService` et `MouvementService`. `MouvementService` importe `EmplacementExtService`. `EmplacementExtService` importe `EmplacementRepository`. Si à l'avenir `MachineService` ou `MouvementService` importent `PieceService`, cela créera une dépendance circulaire.
- **Correction**: Utiliser l'injection de dépendance ou le pattern médiateur pour briser les dépendances circulaires potentielles.

### ARCH-009 — BASSE: Pas de couche DTO/transformation

- **Fichiers**: Tous les repositories et services
- **Description**: Les données brutes de la DB (dict, RealDictRow) sont propagées jusqu'aux vues sans transformation. Aucune séparation entre le schéma DB et le modèle d'interface.
- **Correction**: Introduire des dataclasses ou modèles Pydantic pour représenter les entités métier.

### ARCH-010 — BASSE: schemas.py dans database/bu/ — nommage obscur

- **Fichier**: `database/bu/schemas.py`
- **Description**: Le répertoire `bu/` n'est pas explicite. "bu" pourrait signifier "backup" — suggère que c'est un artéfact.
- **Correction**: Renommer en `database/schemas/` ou `database/migrations/` avec un nommage explicite.

---

## 4. PERFORMANCE

### PERF-001 — HAUTE: Requête N+1 et chargement complet pour lookup simple

- **Fichier**: `APP/services/piece_service.py`, lignes 42-46, 66-70
- **Description**: À chaque création/mise à jour de pièce, `list_machines()` charge **toutes** les machines, puis fait une boucle de recherche linéaire pour trouver la machine correspondante. Si 1000 machines existent, chaque opération pièce charge 1000 machines.
- **Correction**: Ajouter une méthode `get_machine_by_id()` dans `MachineService`/`MachineRepository` et l'utiliser directement.

### PERF-002 — HAUTE: Recherche linéaire dans _get_nom_from_id

- **Fichier**: `APP/services/piece_service.py`, ligne 144-150
- **Description**: `_get_nom_from_id()` parcourt linéairement des listes entières pour trouver un nom par ID. Appelé 4-5 fois par opération pièce.
- **Correction**: Utiliser un dictionnaire `{id: nom}` ou faire une requête SQL ciblée `SELECT nom FROM table WHERE id = %s`.

### PERF-003 — MOYENNE: Sous-requête au lieu de JOIN

- **Fichier**: `APP/models/mouvement_repository.py`, lignes 42-49
- **Description**: `get_mouvements_by_piece()` utilise une sous-requête `WHERE piece_reference IN (SELECT reference FROM piece WHERE id_piece = %s)` au lieu d'un JOIN direct, moins performant.
- **Correction**: Utiliser `JOIN piece ON ... WHERE piece.id_piece = %s` directement.

### PERF-004 — MOYENNE: Appels redondants à get_emplacement_reception_defaut()

- **Fichier**: `APP/services/reception_workflow_service.py`, lignes 47-49, 100-102
- **Description**: La fonction stockée `get_emplacement_reception_defaut()` est appelée deux fois dans le même workflow (création de lot puis mise en stock). La valeur ne change pas entre les appels.
- **Correction**: Appeler une fois dans `__init__()` ou au début du workflow et passer la valeur en paramètre.

### PERF-005 — BASSE: Pas de pool de connexions

- **Fichier**: `APP/services/db.py`
- **Description**: Une seule connexion `psycopg2` est partagée. En environnement multi-utilisateurs ou multi-thread, cela deviendra un goulot d'étranglement.
- **Correction**: Utiliser `psycopg2.pool.SimpleConnectionPool` ou `SQLAlchemy` avec pool de connexions.

---

## 5. QUALITÉ

### QUAL-001 — HAUTE: print() comme mécanisme de logging en production

- **Fichiers**: `APP/services/db.py` (22 occurrences), `APP/services/emplacement_ext_service.py` (14 occurrences), `APP/services/emplacement_service.py` (5 occurrences), `APP/services/commande_service.py` (5 occurrences), `APP/models/fournisseur_repository.py`, `APP/models/ligne_commande_repository.py`
- **Description**: Utilisation intensive de `print()` pour les logs, erreurs et debug. Mélange de `print()`, `logger.info()`, `logger.error()` sans cohérence. Les `print()` ne peuvent pas être filtrés, redirigés, ou désactivés en production.
- **Correction**: Remplacer TOUS les `print()` par des appels `logging` avec le niveau approprié (DEBUG, INFO, WARNING, ERROR).

### QUAL-002 — HAUTE: Configuration du logging multiple et incohérente

- **Fichiers**: `APP/models/ligne_commande_repository.py` (ligne 6), `APP/models/commande_repository.py` (ligne 6)
- **Description**: `logging.basicConfig(level=logging.INFO)` est appelé dans deux repositories différents. Si un autre module configure le logging avant, cet appel sera ignoré. La configuration du logging doit être centralisée au point d'entrée de l'application.
- **Correction**: Supprimer tous les `basicConfig()` des modules et configurer le logging une seule fois dans `main.py` ou `__init__.py`.

### QUAL-003 — MOYENNE: Gestion d'erreurs incohérente

- **Fichiers**: Plusieurs
- **Description**: Trois patterns de gestion d'erreur coexistent:
  1. Exception propagée (la plupart des repos)
  2. Exception interceptée, loggée, puis `return False` ou `[]` (ex: `emplacement_ext_service.py`)
  3. Exception interceptée avec `rollback()`, loggée, puis `raise` (ex: `commande_repository.py`)
  
  Le pattern 2 masque les erreurs et rend le debugging difficile.
- **Correction**: Uniformiser sur le pattern 3 (log + raise) et laisser la couche supérieure (controllers) décider de l'interface utilisateur.

### QUAL-004 — MOYENNE: TODO et code incomplet

- **Fichier**: `APP/services/mouvement_service.py`, lignes 473-474
- **Description**: `# TODO: Implémenter la logique de répartition` suivi de `pass` — fonctionnalité incomplète qui pourrait causer des comportements inattendus.
- **Correction**: Implémenter la logique ou lever `NotImplementedError`.

### QUAL-005 — MOYENNE: Try/except nu (bare except)

- **Fichier**: `APP/services/piece_service.py`, lignes 8, 123-125, 164-166
- **Description**: 
  - Ligne 8: `except Exception: pg_errors = None` attrape silencieusement toute erreur d'import
  - Lignes 123-125, 164-166: `except Exception: pass` dans les blocs de rollback — masque les erreurs de rollback
- **Correction**:
  - Ligne 8: N'attraper que `ImportError`
  - Lignes 123-125, 164-166: Logger l'exception avant de `pass`

### QUAL-006 — MOYENNE: Cache non invalidé

- **Fichier**: `APP/models/commande_repository.py`, ligne 13
- **Description**: `_default_user_id` est mis en cache sans mécanisme d'invalidation. Si l'utilisateur Admin est supprimé, le cache contiendra un ID invalide.
- **Correction**: Ajouter une méthode `invalidate_cache()` ou ne pas cacher.

### QUAL-007 — BASSE: Incohérence de langue dans les logs

- **Description**: Mélange de français et anglais dans les messages de log:
  - Français: `"Erreur lors de..."`, `"Commande créée avec succès"`
  - Anglais: `"Cannot delete this part because..."`
- **Correction**: Uniformiser sur une langue (recommandation: anglais pour le code et les logs techniques).

### QUAL-008 — BASSE: Lignes de commentaires morts

- **Fichiers**: `APP/models/piece_service.py` (lignes 80-81, 92-98)
- **Description**: Plusieurs blocs de code commenté qui ne sont ni supprimés ni documentés.
- **Correction**: Supprimer le code mort ou le documenter avec une justification.

### QUAL-009 — BASSE: Convention de nommage incohérente

- **Description**: 
  - Méthodes parfois en anglais (`get_all_pieces`), parfois en français (`ajouter_stock_emplacement`)
  - Tables parfois en MAJUSCULES (`UTILISATEUR`, `PIECE`), parfois en minuscules (`emplacement`, `piece_unit`)
  - Colonnes parfois avec préfixe table (`id_piece`), parfois sans (`id`)
- **Correction**: Adopter une convention unique (recommandation: anglais pour le code, snake_case partout, noms de tables cohérents).

---

## 6. SYNTHÈSE ET RECOMMANDATIONS PRIORITAIRES

### Actions immédiates (CRITIQUE)
1. **Corriger BUG-001**: Initialiser les attributs manquants dans `PieceService` — l'application est **cassée** pour la création/modification de pièces
2. **Corriger BUG-002**: Ajouter une whitelist de colonnes dans les requêtes dynamiques de `commande_repository.py` et `ligne_commande_repository.py`
3. **Corriger SEC-001**: Supprimer le mot de passe hardcodé `admin123` et la création automatique d'utilisateur
4. **Clarifier BUG-003**: Déterminer si le schéma doit être PostgreSQL (comme le runtime) ou SQLite, et aligner

### Actions court terme (HAUTE)
5. Supprimer les `print()` de `db.py` qui fuient des informations de connexion (SEC-002)
6. Unifier le pattern d'accès DB (ARCH-004)
7. Supprimer la duplication `i18n.py`/`i18ny.py` (ARCH-003)
8. Diviser `schemas.py` en fichiers séparés (ARCH-001)
9. Remplacer les recherches linéaires par des dictionnaires (PERF-001, PERF-002)

### Améliorations continues (MOYENNE/BASSE)
10. Remplacer tous les `print()` par `logging` (QUAL-001)
11. Centraliser la configuration du logging (QUAL-002)
12. Uniformiser la gestion d'erreurs (QUAL-003)
13. Introduire une validation d'entrée dans les services (SEC-003)
14. Mettre en place un pool de connexions (PERF-005)
15. Ajouter le support SSL pour la connexion DB (SEC-008)

---

*Rapport généré automatiquement après lecture exhaustive de 38 fichiers Python (~38,500 LOC analysées).*
