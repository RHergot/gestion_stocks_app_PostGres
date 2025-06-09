# Module de Gestion des Mouvements de Stock

## Vue d'ensemble

Ce module implémente un système complet de gestion des mouvements de stock suivant l'architecture MVC de votre application. Il permet de tracer tous les mouvements d'entrée, de sortie, de transfert et d'ajustement d'inventaire.

## Architecture

### 1. Modèle (Model)
- **`mouvement_repository.py`** : Repository pour l'accès aux données des mouvements
- **`type_mouvement_repository.py`** : Repository pour les types de mouvements (intégré dans mouvement_repository.py)

### 2. Service (Business Logic)
- **`mouvement_service.py`** : Logique métier pour la gestion des mouvements

### 3. Contrôleur (Controller)
- **`mouvement_controller.py`** : Contrôleur pour orchestrer les opérations de mouvements

### 4. Vue (View)
- **`mouvement_table_view.py`** : Interface principale pour visualiser et gérer les mouvements
- **`mouvement_dialog.py`** : Dialogs pour créer/modifier les mouvements

## Base de données

### Tables créées

#### `type_mouvement`
- Types de mouvements prédéfinis (entrée, sortie, transfert, inventaire)
- Impact sur le stock (+1 pour entrée, -1 pour sortie)

#### `mouvement_stock`
- Enregistrement de tous les mouvements
- Traçabilité complète avec stock avant/après
- Référence aux emplacements source/destination
- Coûts et références documentaires

### Vues créées

#### `v_historique_mouvements`
- Vue complète des mouvements avec toutes les informations jointes

#### `v_mouvement_stats`
- Statistiques par pièce et type de mouvement

## Fonctionnalités

### Types de mouvements supportés

1. **Entrées de stock**
   - Achat
   - Retour
   - Ajustement d'inventaire (positif)

2. **Sorties de stock**
   - Consommation/utilisation
   - Retour fournisseur
   - Perte/casse
   - Obsolescence
   - Ajustement d'inventaire (négatif)

3. **Transferts**
   - Déplacement entre emplacements
   - Créé automatiquement une sortie et une entrée

4. **Ajustements d'inventaire**
   - Correction du stock réel
   - Calcul automatique de la différence

### Interface utilisateur

#### Fenêtre principale (`MouvementTableView`)
- Liste de tous les mouvements avec filtres
- Panneau de détails du mouvement sélectionné
- Actions rapides pour les opérations courantes
- Statistiques en temps réel
- Menus contextuels pour différentes vues

#### Dialogs de saisie (`MouvementDialog`)
- Formulaires adaptés selon le type de mouvement
- Validation des données en temps réel
- Calcul automatique des impacts sur le stock

## Installation et configuration

### 1. Initialisation des tables

```bash
python init_mouvement_tables.py
```

Ce script :
- Crée les tables nécessaires
- Insère les types de mouvements de base
- Crée les vues et index
- Génère des mouvements d'exemple

### 2. Intégration dans l'application

Le module est déjà intégré dans `main_window.py` avec :
- Menu "Mouvements" dans la barre de menu
- Actions pour créer rapidement des mouvements
- Accès à la vue complète des mouvements

## Utilisation

### Depuis l'interface

1. **Menu Mouvements > Voir les mouvements** : Ouvre la fenêtre principale
2. **Menu Mouvements > Nouvelle entrée** : Crée une entrée de stock
3. **Menu Mouvements > Nouvelle sortie** : Crée une sortie de stock
4. **Menu Mouvements > Nouveau transfert** : Crée un transfert
5. **Menu Mouvements > Ajustement inventaire** : Ajuste le stock

### Depuis le code

```python
# Créer une entrée de stock
result = mouvement_controller.effectuer_entree_stock(
    piece_id=1,
    quantite=10,
    type_mouvement='ENTREE_ACHAT',
    emplacement_id=1,
    cout_unitaire=15.50,
    commentaire='Livraison fournisseur'
)

# Créer une sortie de stock
result = mouvement_controller.effectuer_sortie_stock(
    piece_id=1,
    quantite=5,
    type_mouvement='SORTIE_CONSOMMATION',
    emplacement_id=1,
    commentaire='Maintenance machine A'
)

# Effectuer un transfert
result = mouvement_controller.effectuer_transfert(
    piece_id=1,
    quantite=3,
    emplacement_source_id=1,
    emplacement_destination_id=2,
    commentaire='Réorganisation magasin'
)

# Ajustement d'inventaire
result = mouvement_controller.effectuer_ajustement_inventaire(
    piece_id=1,
    nouveau_stock=25,
    commentaire='Inventaire physique'
)
```

## Sécurité et validation

### Validations automatiques
- Vérification de l'existence des pièces et emplacements
- Contrôle du stock suffisant pour les sorties
- Validation des quantités positives
- Cohérence des types de mouvements

### Traçabilité
- Tous les mouvements sont horodatés
- Utilisateur responsable enregistré
- Stock avant/après calculé automatiquement
- Possibilité d'annulation avec mouvement inverse

## Rapports et statistiques

### Rapports disponibles
- Historique complet par pièce
- Rapport d'activité par période
- Pièces en stock faible
- Statistiques par type de mouvement

### Filtres et recherches
- Par pièce
- Par type de mouvement
- Par période
- Par emplacement
- Par utilisateur

## Extension et personnalisation

### Ajouter un nouveau type de mouvement

```sql
INSERT INTO type_mouvement (nom, description, impact_stock) 
VALUES ('NOUVEAU_TYPE', 'Description', 1); -- 1 pour entrée, -1 pour sortie
```

### Personnaliser les validations

Modifier les méthodes de validation dans `MouvementController` :
- `_valider_piece_existe()`
- `_valider_stock_suffisant()`
- `_valider_quantite_positive()`

### Ajouter des champs personnalisés

1. Modifier le schéma de la table `mouvement_stock`
2. Adapter les repositories et services
3. Mettre à jour les interfaces utilisateur

## Maintenance

### Nettoyage des données
- Les mouvements annulés sont marqués comme `valide = FALSE`
- Possibilité de purger les anciens mouvements
- Archivage recommandé pour les données historiques

### Performance
- Index créés sur les colonnes fréquemment utilisées
- Pagination dans les listes de mouvements
- Vues optimisées pour les rapports

## Dépannage

### Problèmes courants

1. **Erreur de stock insuffisant** : Vérifier le stock actuel de la pièce
2. **Type de mouvement non trouvé** : Vérifier que les types sont bien initialisés
3. **Emplacement non trouvé** : Vérifier l'existence des emplacements référencés

### Logs et debugging

Les erreurs sont loggées dans le service et le contrôleur. Activer le logging pour plus de détails :

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Évolutions futures

### Fonctionnalités prévues
- Import/export de mouvements en masse
- Notifications automatiques pour stock faible
- Intégration avec les commandes fournisseurs
- Workflow d'approbation pour certains mouvements
- API REST pour intégration externe

### Améliorations techniques
- Cache pour les requêtes fréquentes
- Optimisation des performances pour gros volumes
- Interface mobile/web
- Synchronisation multi-sites