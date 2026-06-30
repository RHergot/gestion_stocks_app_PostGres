# Rapport d'Audit — Couche UI (Views, Controllers, MainWindow)

**Projet :** Gestion de Stock/GMAO (PySide6 + PostgreSQL)  
**Date :** 30 juin 2026  
**Périmètre :** `APP/main.py`, `APP/main_window.py`, `APP/main_window_selection_menu_patch.py`, `accueil.py`, `APP/controllers/mouvement_controller.py`, tous les fichiers `APP/views/*.py`  
**Total fichiers lus :** 37 fichiers `.py`

---

## Résumé

| Sévérité | Nombre |
|----------|--------|
| CRITIQUE | 6 |
| HAUTE    | 10 |
| MOYENNE  | 14 |
| BASSE    | 5 |
| **Total** | **35** |

---

## 1. BUGS

### 1.1 [CRITIQUE] Méthodes dupliquées/orphelines dans `mouvement_table_view.py`

- **Fichier :** `APP/views/mouvement_table_view.py`, lignes 865–925
- **Description :** La classe `MoveToWasteDialog` se termine à la ligne 863. Les méthodes `show_low_stock` (l.865), `new_reception` (l.882) et `mise_en_stock` (l.905) sont définies **hors de toute classe** mais utilisent `self.mouvement_controller` qui n'existe pas dans ce scope. Elles ne sont jamais appelées et génèrent des erreurs si le module est importé avec vérification stricte. De plus, `MouvementTableView` a déjà `new_reception` (l.722) et `mise_en_stock` (l.746) correctement définies.
- **Correction :** Supprimer les lignes 865–925 (fonctions orphelines).

### 1.2 [CRITIQUE] Clé de dictionnaire incorrecte dans `mise_en_stock_dialog.py`

- **Fichier :** `APP/views/mise_en_stock_dialog.py`, ligne 186
- **Description :** `get_data()` utilise `dest_data['id_emplacement']` mais les données d'emplacement sont stockées avec la clé `'id'` (cf. `load_data()` ligne 152 qui ajoute `emplacement` comme `userData`). Cela provoquera une `KeyError` à l'exécution.
- **Correction :** Remplacer `dest_data['id_emplacement']` par `dest_data['id']`.

### 1.3 [HAUTE] Double définition de `get_lignes_data()` dans `commande_dialog.py`

- **Fichier :** `APP/views/commande_dialog.py`, lignes 504–532 et 659–684
- **Description :** La méthode `get_lignes_data()` est définie deux fois. La seconde définition (l.659) écrase la première. Les deux extraient les données différemment, ce qui peut causer des incohérences selon le code appelant. La première extrait `piece_id` en gérant le cas dict, la seconde parse le texte des cellules du tableau.
- **Correction :** Fusionner en une seule méthode robuste avec gestion des deux cas.

### 1.4 [MOYENNE] Menu "Selection" jamais ajouté à la barre de menu

- **Fichier :** `APP/main_window.py` et `APP/main_window_selection_menu_patch.py`
- **Description :** Le fichier `main_window_selection_menu_patch.py` définit `patch_selection_menu(self)` mais cette fonction n'est **jamais importée ni appelée** dans `MainWindow.__init__` ou `_create_menu_bar()`. Le menu "Selection" et ses 5 entrées (Low Stock, Parts by Machine, etc.) sont inaccessibles via les menus.
- **Correction :** Importer `patch_selection_menu` dans `main_window.py` et l'appeler dans `_create_menu_bar()`, ou intégrer directement son contenu dans `_create_menu_bar()`.

### 1.5 [MOYENNE] Incohérence de nombre de colonnes dans `piece_table_view.py`

- **Fichier :** `APP/views/piece_table_view.py`, lignes 42 et 77
- **Description :** Le constructeur initialise `self.table.setColumnCount(12)` avec 12 en-têtes. La méthode `set_pieces_table()` redéfinit `setColumnCount(13)` avec 13 en-têtes (ajout de "Machine"). Le tableau change donc de structure entre l'initialisation et le premier `refresh()`.
- **Correction :** Uniformiser à 13 colonnes dès le constructeur.

### 1.6 [BASSE] `select_commande()` ne fonctionne pas — `UserRole` non supporté

- **Fichier :** `APP/views/commande_view.py`, ligne 786
- **Description :** `select_commande()` compare `self.model.data(idx, Qt.UserRole)` avec `commande_id`, mais `CommandeTableModel.data()` ne gère que `Qt.DisplayRole` et `Qt.EditRole`. `Qt.UserRole` retournera toujours `None`, empêchant toute sélection automatique.
- **Correction :** Soit indexer par une colonne connue (ex: ID en colonne 0), soit ajouter le support de `Qt.UserRole` dans le modèle avec `id_commande` comme valeur.

---

## 2. SÉCURITÉ

### 2.1 [HAUTE] SQL direct dans les vues — bypass de la couche service

- **Fichiers :**
  - `APP/views/piece_table_view.py`, lignes 117–188 (5 méthodes avec SQL direct)
  - `APP/main_window.py`, lignes 213–277 (5 méthodes avec SQL direct)
  - `APP/main_window_selection_menu_patch.py`, lignes 27–93 (5 fonctions avec SQL direct)
  - `APP/views/ligne_commande_dialog.py`, lignes 71–122 (SQL direct)
  - `APP/views/commande_dialog.py`, lignes 228–289 (SQL direct + DDL CREATE TABLE)
- **Description :** Les vues exécutent des requêtes SQL directement via `self.db.conn.cursor()` au lieu de passer par les services. Cela contourne les validations, la gestion des transactions et les droits d'accès. Violation du pattern MVC.
- **Correction :** Déplacer toute la logique de requêtage vers les services. Les vues ne doivent appeler que des méthodes de service.

### 2.2 [MOYENNE] Hashage de mot de passe sans sel (SHA-256 brut)

- **Fichier :** `APP/views/user_dialog.py`, ligne 35
- **Description :** `hashlib.sha256(self.mot_de_passe.text().encode('utf-8')).hexdigest()` — pas de sel (salt). Vulnérable aux attaques par dictionnaire/rainbow table.
- **Correction :** Utiliser `hashlib.pbkdf2_hmac` ou `bcrypt`/`argon2` avec un sel aléatoire.

### 2.3 [MOYENNE] ID utilisateur hardcodé

- **Fichier :** `APP/views/reception_dialog.py`, ligne 335
- **Description :** `utilisateur_id` est hardcodé à `1` dans l'INSERT SQL. TODO commenté l.335 confirme que c'est un placeholder.
- **Correction :** Récupérer l'utilisateur connecté depuis le contexte applicatif.

### 2.4 [BASSE] Exposition de la connexion DB aux vues

- **Fichiers :** Tous les dialogs et vues recevant `db` en paramètre
- **Description :** Plusieurs vues reçoivent l'objet `db` directement et accèdent à `db.conn`, exposant la connexion brute et permettant l'exécution de SQL arbitraire.
- **Correction :** Les vues ne devraient recevoir que les services nécessaires, jamais l'objet `Database` directement.

---

## 3. ARCHITECTURE

### 3.1 [CRITIQUE] God Object : `commande_view.py` (1116 lignes)

- **Fichier :** `APP/views/commande_view.py`
- **Description :** Ce module cumule trois responsabilités distinctes :
  1. **Modèles de données** : `CommandeTableModel` (l.22), `LigneCommandeTableModel` (l.133) — devraient être dans `APP/models/`
  2. **Vue** : `CommandeView` — affichage, toolbar, tableaux
  3. **Logique métier** : création/édition/suppression commandes, workflow de statuts (Brouillon→Validee→Envoyee→Livree), copie de commande, génération de numéro, création de mouvements de stock — devraient être dans un `CommandeController` ou `CommandeService`
- **Correction :** Splitter en 3 fichiers : modèles dans `APP/models/`, contrôleur dans `APP/controllers/`, vue allégée (~300 lignes max).

### 3.2 [CRITIQUE] God Object : `commande_dialog.py` (949 lignes)

- **Fichier :** `APP/views/commande_dialog.py`
- **Description :** Le dialog contient de la logique métier importante :
  - `_creer_mouvements_livraison()` (l.836) : création de mouvements de stock
  - `_creer_copie_commande()` (l.872) : duplication de commande
  - `_changer_statut()` (l.803) : mise à jour statut en base
  - `_generer_nouveau_numero()` (l.921) : logique de numérotation
  - `load_fournisseurs()` (l.225) : exécute même `CREATE TABLE IF NOT EXISTS` (!)
- **Correction :** Déléguer toute la logique métier au `MouvementController` ou à un `CommandeService`. Le dialog ne devrait gérer que l'UI.

### 3.3 [CRITIQUE] Logique métier dans `main_window.py`

- **Fichier :** `APP/main_window.py`, lignes 212–278
- **Description :** Six méthodes (`show_stock_faible`, `show_pieces_by_machine`, `show_inventaire_categorie`, `show_emplacements_vides`, `show_pieces_by_statut`, `show_stock_faible` dupliquée) exécutent du SQL direct avec des requêtes complexes de jointure. La fenêtre principale ne devrait coordonner que l'affichage.
- **Correction :** Créer un `RapportService` ou passer par `MouvementController` pour ces requêtes.

### 3.4 [CRITIQUE] Duplication massive : `main_window_selection_menu_patch.py`

- **Fichier :** `APP/main_window_selection_menu_patch.py`
- **Description :** Ce fichier duplique intégralement 5 méthodes déjà présentes dans `main_window.py` (lignes 27–93) avec le même code SQL. C'est un anti-pattern de "monkey-patching" qui n'est même pas appliqué (le patch n'est jamais importé). Si importé, il y aurait des définitions conflictuelles.
- **Correction :** Supprimer ce fichier. Le menu Selection devrait être intégré directement dans `MainWindow._create_menu_bar()`.

### 3.5 [CRITIQUE] `accueil.py` — point d'entrée orphelin incompatible

- **Fichier :** `accueil.py`
- **Description :** Point d'entrée alternatif standalone avec des chemins Windows hardcodés (`C:\\Users\\Public\\.vscode\\...`) et un lanceur `subprocess.Popen`. Inutilisable sous Linux, incompatible avec `APP/main.py`, et référence un autre projet (`gmao_app_PostGres`). Semble être un vestige d'une version antérieure.
- **Correction :** Supprimer ou déplacer dans un dossier `legacy/`. Le vrai point d'entrée est `APP/main.py`.

### 3.6 [HAUTE] Logique métier dans `reception_dialog.py`

- **Fichier :** `APP/views/reception_dialog.py`, lignes 243–396
- **Description :** La méthode `process_reception()` (l.243) exécute des mises à jour de base de données, crée des mouvements de stock, met à jour les statuts de commande. Tout cela est de la logique métier qui devrait être dans un service.
- **Correction :** Déléguer à `MouvementController` ou créer `ReceptionService.process_reception()`.

### 3.7 [HAUTE] Absence de classe de base CRUD — duplication massive de patterns

- **Fichiers :** 11 paires dialog/table_view : `fabricant`, `site`, `type_machine`, `fournisseur`, `user`, `piece_unit`, `piece_statut`, `piece_category`, `machine`, `piece`, `emplacement`
- **Description :** Chaque paire implémente le même pattern CRUD (tableau + boutons Add/Edit/Delete/Refresh/Close + dialog avec OK/Cancel) sans héritage commun. La duplication est massive : `get_data()`, `set_data()`, `refresh()`, `get_selected_*()`, `add_*()`, `edit_*()`, `delete_*()` sont recopiés avec des variations minimes.
- **Correction :** Créer une classe `BaseTableView` et `BaseDialog` avec des méthodes génériques. Les sous-classes ne surchargent que les champs spécifiques.

### 3.8 [HAUTE] Lazy imports dans les contrôleurs

- **Fichier :** `APP/controllers/mouvement_controller.py`, lignes 371 et 381
- **Description :** `ReceptionWorkflowService` est importé dans `get_pieces_en_reception()` et `get_reception_stock_summary()` plutôt qu'au niveau du module ou injecté au constructeur. Cela masque les dépendances et rend le code plus difficile à tester.
- **Correction :** Injecter `ReceptionWorkflowService` dans le constructeur de `MouvementController`.

### 3.9 [MOYENNE] Accès chaîné fragile aux dépendances

- **Fichier :** `APP/views/machine_dialog.py`, ligne 22
- **Description :** `db = parent.parent().db if parent and hasattr(parent, 'parent') and hasattr(parent.parent(), 'db') else None` — chaîne de dépendance fragile basée sur la hiérarchie des widgets.
- **Correction :** Passer `db` explicitement en paramètre du constructeur.

### 3.10 [MOYENNE] Lazy import dans `emplacement_dialog.py`

- **Fichier :** `APP/views/emplacement_dialog.py`, lignes 212, 409
- **Description :** `EmplacementExtService` est importé à l'intérieur des méthodes `load_stock_data()` et `load_emplacement_complet()` plutôt qu'en haut du module.
- **Correction :** Importer en haut du fichier, ou injecter l'instance du service.

### 3.11 [MOYENNE] Controller `mouvement_controller.py` trop volumineux (679 lignes)

- **Fichier :** `APP/controllers/mouvement_controller.py`
- **Description :** Le contrôleur gère 8 types d'opérations de mouvement + le workflow de réception + les rapports + les validations + les données de référence. La classe dépasse 650 lignes.
- **Correction :** Extraire la partie "workflow de réception" dans un `ReceptionController` dédié. Séparer les méthodes de rapport dans `RapportController`.

---

## 4. PERFORMANCE

### 4.1 [MOYENNE] Génération de numéro de commande en O(n)

- **Fichier :** `APP/views/commande_view.py`, ligne 1090 ; `APP/views/commande_dialog.py`, ligne 921
- **Description :** `_generer_nouveau_numero()` charge **toutes** les commandes (`get_all_commandes()`) puis parcourt la liste entière pour trouver le max numérique. Pour 10 000 commandes, c'est inacceptable.
- **Correction :** Utiliser `SELECT MAX(CAST(numero_commande AS INTEGER)) FROM commande` directement en SQL.

### 4.2 [MOYENNE] Pas de pagination dans `mouvement_table_view.py`

- **Fichier :** `APP/views/mouvement_table_view.py`
- **Description :** La table charge tous les mouvements en mémoire sans limite. Si la table contient des centaines de milliers de mouvements, l'UI deviendra inutilisable (mémoire + temps de rendu).
- **Correction :** Implémenter une pagination (LIMIT/OFFSET) avec navigation entre pages.

### 4.3 [MOYENNE] Vérification et création de table à chaque ouverture de dialog

- **Fichier :** `APP/views/commande_dialog.py`, lignes 228–262
- **Description :** `load_fournisseurs()` vérifie l'existence de la table `fournisseur` et exécute un `CREATE TABLE IF NOT EXISTS` + INSERT à **chaque ouverture** du dialog de commande. C'est du code de migration qui n'a rien à faire dans une vue.
- **Correction :** Supprimer ce code DDL. La création de tables doit être gérée par un système de migration (Alembic, script SQL initial).

### 4.4 [BASSE] Requêtes superflues dans `ligne_commande_dialog.py`

- **Fichier :** `APP/views/ligne_commande_dialog.py`, lignes 67–122
- **Description :** `load_pieces()` exécute 4 requêtes : `COUNT(*)`, `LIMIT 5` (debug), `EXISTS` (vérification table), puis la requête principale. Les 3 premières sont du code de debug inutile en production.
- **Correction :** Supprimer les requêtes de debug. Utiliser un logger plutôt que `print()`.

---

## 5. QUALITÉ

### 5.1 [HAUTE] Absence d'internationalisation (i18n) dans plusieurs fichiers

- **Fichiers :**
  - `APP/views/fabricant_dialog.py` — toutes les chaînes en dur, pas de `self.tr()`
  - `APP/views/fabricant_table_view.py` — idem
  - `APP/views/ligne_commande_dialog.py` — chaînes en dur
  - `APP/views/reception_dialog.py` — chaînes en dur
  - `APP/views/commande_view.py` — partiellement i18n ; QMessageBox utilisent des chaînes en dur
  - `APP/views/commande_dialog.py` — partiellement i18n
- **Description :** Ces fichiers n'utilisent pas `self.tr()` pour les chaînes visibles, rendant l'application non traduisible. Incohérence avec `main_window.py` qui utilise `self.tr()` systématiquement.
- **Correction :** Wrapper toutes les chaînes visibles avec `self.tr()`.

### 5.2 [HAUTE] Utilisation abusive de `print()` pour le debug

- **Fichiers :**
  - `APP/views/commande_view.py` : 30+ `print("[DEBUG]...")`
  - `APP/views/commande_dialog.py` : 10+ `print("[DEBUG]...")`
  - `APP/views/ligne_commande_dialog.py` : 15+ `print(...)`
  - `APP/views/warehouse_layout_view.py` : 30+ `print("DEBUG:...")`
  - `APP/views/mouvement_table_view.py` : quelques `print()`
  - `APP/main.py` : `print()` pour les traductions
- **Description :** Les `print()` polluent la sortie standard et ne sont pas filtrables. Aucun mécanisme de niveau de log.
- **Correction :** Remplacer par le module `logging` avec des niveaux appropriés (DEBUG, INFO, ERROR). `mouvement_controller.py` le fait déjà correctement.

### 5.3 [MOYENNE] Code mort et commentaires inutiles

- **Fichier :** `APP/views/machine_table_view.py`, ligne 93
  - `data["parent_machine_id"] = 0  # Champ par défaut car la table n'existe pas` — code incohérent, le champ parent existe ailleurs.
- **Fichier :** `APP/views/warehouse_layout_view.py`
  - Références à `self.aisle_selector` commentées avec "Removed" (l.89, 114, 123) — nettoyage incomplet.
  - La méthode `on_piece_changed` dans `MiseEnStockDialog` (l.153) et `ReceptionWorkflowDialog` (l.152) est un stub vide (`pass`).
- **Correction :** Nettoyer le code mort, implémenter ou supprimer les stubs.

### 5.4 [MOYENNE] Gestion d'erreur incohérente

- **Description :** Certains dialogs captent les exceptions et affichent `QMessageBox.critical`, d'autres laissent l'exception remonter sans capture. `commande_view.py` mélange `print()` et `QMessageBox` pour le même type d'erreur.
- **Correction :** Définir une stratégie uniforme de gestion d'erreur UI (ex: décorateur `@handle_errors` ou méthode `_show_error()`).

### 5.5 [MOYENNE] Incohérence des boutons d'action

- **Fichiers :** Tous les dialogs
- **Description :** Certains dialogs utilisent `OK`/`Cancel`, d'autres `Validate`/`Cancel`, d'autres `Save`/`Close`. Aucune convention n'est respectée :
  - `PieceDialog` : OK / Cancel
  - `MouvementDialog` : Validate / Cancel
  - `CommandeDialog` : Save / Close
  - `EmplacementDialog` : OK / Cancel
  - `MiseEnStockDialog` : Confirm Putaway / Cancel
  - `ReceptionDialog` : Validate reception / Cancel
- **Correction :** Standardiser les libellés (ex: "Save" / "Cancel" ou utiliser `QDialogButtonBox` standard).

### 5.6 [BASSE] `setGeometry` appelé deux fois

- **Fichier :** `APP/views/fournisseur_table_view.py`, ligne 12
- **Description :** `self.resize(800, 600)` et `self.setGeometry(100, 100, 800, 600)` sont appelés tous les deux, le second écrasant le premier.
- **Correction :** Supprimer le `resize()` redondant.

### 5.7 [BASSE] Import dupliqué

- **Fichier :** `APP/main_window.py`, lignes 1–3 et 6–8
- **Description :** `QMainWindow`, `QMenuBar`, `QMenu`, `QMessageBox`, `QTranslator`, `QAction` sont importés deux fois.
- **Correction :** Fusionner les imports en un seul bloc.

### 5.8 [BASSE] `EmplacementDialog.set_data()` — méthode `accept()` non connectée pour validation

- **Fichier :** `APP/views/emplacement_dialog.py`
- **Description :** Le dialog a une méthode `validate_data()` bien écrite, mais `set_data()` remplit le formulaire sans revalider. Si des données incohérentes sont chargées, l'utilisateur peut cliquer OK sans voir les erreurs.
- **Correction :** Appeler `validate_data()` après `set_data()`, ou désactiver le bouton OK tant que les données ne sont pas valides.

---

## 6. Recommandations Globales

### 6.1 Refactoring prioritaire (court terme)

1. **Supprimer `main_window_selection_menu_patch.py`** et intégrer le menu Selection dans `MainWindow`.
2. **Supprimer ou déplacer `accueil.py`** (fichier Windows-only orphelin).
3. **Fusionner les deux `get_lignes_data()`** de `commande_dialog.py`.
4. **Supprimer les définitions de méthodes orphelines** dans `mouvement_table_view.py` (l.865–925).
5. **Corriger la clé `id_emplacement` → `id`** dans `mise_en_stock_dialog.py:186`.
6. **Corriger `select_commande()`** dans `commande_view.py:786`.

### 6.2 Refactoring structurel (moyen terme)

1. **Extraire la logique métier des vues** (`commande_view.py`, `commande_dialog.py`, `reception_dialog.py`, `main_window.py`) vers des contrôleurs/services.
2. **Créer une classe de base pour les vues CRUD** (`BaseTableView`, `BaseDialog`) pour éliminer la duplication des 11 paires dialog/view.
3. **Supprimer l'accès direct à `db` depuis les vues** — passer uniquement des services.
4. **Standardiser l'i18n** sur tous les fichiers UI avec `self.tr()`.

### 6.3 Améliorations de sécurité (moyen terme)

1. **Saler les mots de passe** (bcrypt/argon2 au lieu de SHA-256 brut).
2. **Supprimer le SQL direct des vues** — tout doit passer par les services.
3. **Supprimer le DDL des vues** (`CREATE TABLE` dans `commande_dialog.py`).

### 6.4 Dette technique

1. **Nettoyer tous les `print()` de debug** — utiliser le module `logging`.
2. **Nettoyer le code mort** (commentaires "Removed", stubs vides).
3. **Standardiser les libellés des boutons**.
4. **Implémenter la pagination** pour les tables à fort volume (mouvements, pièces, commandes).
