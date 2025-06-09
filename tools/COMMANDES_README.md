# Gestion des Commandes - Workflow et Réception

## Vue d'ensemble

Ce module implémente un système complet de gestion des commandes avec workflow de statuts et gestion automatique des mouvements de stock lors de la réception.

## Workflow des Statuts

### Statuts disponibles
- **Brouillon** : Commande en cours de création/modification
- **Validee** : Commande confirmée et prête à être envoyée
- **Envoyee** : Commande envoyée au fournisseur
- **Partielle** : Livraison partielle reçue
- **Livree** : Commande entièrement livrée
- **Annulee** : Commande annulée

### Transitions possibles
```
Brouillon → Validee → Envoyee → Livree
    ↓         ↓         ↓
  Annulee   Annulee   Annulee
```

## Fonctionnalités

### 1. Gestion des transitions de statut
- **Confirmer** : Brouillon → Validee
- **Envoyer** : Validee → Envoyee  
- **Livrer** : Envoyee → Livree (avec création automatique des mouvements de stock)
- **Annuler** : Tout statut → Annulee

### 2. Actions disponibles
- **Copier** : Crée une nouvelle commande avec les mêmes lignes
- **Modifier** : Édition des détails de la commande
- **Supprimer** : Suppression complète de la commande

### 3. Gestion automatique du stock
Lors du passage au statut "Livree" :
- Création automatique de mouvements d'entrée de type `ENTREE_ACHAT`
- Mise à jour du stock actuel des pièces
- Traçabilité complète avec référence à la commande

## Interface Utilisateur

### Dialog de commande (`commande_dialog.py`)
- **Section informations** : Détails de la commande
- **Section lignes** : Gestion des lignes de commande
- **Section actions** : Boutons de transition de statut (en mode édition uniquement)

### Boutons de statut
Les boutons sont activés/désactivés selon le statut actuel :

| Statut | Confirmer | Envoyer | Livrer | Copier | Annuler |
|--------|-----------|---------|--------|--------|---------|
| Brouillon | ✅ | ❌ | ❌ | ✅ | ✅ |
| Validee | ❌ | ✅ | ❌ | ✅ | ✅ |
| Envoyee | ❌ | ❌ | ✅ | ✅ | ✅ |
| Livree | ❌ | ❌ | ❌ | ✅ | ❌ |
| Annulee | ❌ | ❌ | ❌ | ✅ | ❌ |

## Architecture Technique

### Fichiers modifiés/créés
- `APP/views/commande_dialog.py` : Interface principale avec boutons de gestion
- `APP/views/commande_view.py` : Vue liste avec connexion des signaux
- `test_commande_workflow.py` : Tests automatisés du workflow
- `test_commande_ui.py` : Test de l'interface utilisateur
- `reset_commande_test.py` : Utilitaire pour remettre une commande en test

### Services utilisés
- `CommandeRepository` : Gestion des commandes en base
- `LigneCommandeRepository` : Gestion des lignes de commande
- `MouvementService` : Création des mouvements de stock
- `TypeMouvement` : Types de mouvements (ENTREE_ACHAT, etc.)

### Signaux Qt
- `commande_livree` : Signal émis lors de la livraison pour rafraîchir la vue

## Utilisation

### 1. Créer une nouvelle commande
```python
dialog = CommandeDialog(db, parent=self)
if dialog.exec() == QDialog.Accepted:
    # Traitement des données
```

### 2. Modifier une commande existante
```python
dialog = CommandeDialog(db, commande_data, parent=self)
dialog.commande_livree.connect(self.refresh_data)  # Connexion du signal
if dialog.exec() == QDialog.Accepted:
    # Traitement des modifications
```

### 3. Workflow programmatique
```python
# Transition de statut
repo.update_commande(commande_id, {'statut': 'Validee'})

# Livraison avec mouvements
repo.update_commande(commande_id, {
    'statut': 'Livree',
    'date_livraison_reelle': datetime.now().strftime('%Y-%m-%d')
})

# Création des mouvements de stock
for ligne in lignes_commande:
    mouvement_service.creer_mouvement_entree(
        piece_id=ligne['piece_id'],
        quantite=ligne['quantite_commandee'],
        type_mouvement_id=type_entree_achat['id'],
        reference_document=f"CMD-{numero_commande}",
        commentaire=f"Livraison commande {numero_commande}"
    )
```

## Tests

### Test automatisé du workflow
```bash
python test_commande_workflow.py
```

### Test de l'interface utilisateur
```bash
python test_commande_ui.py
```

### Remise en état pour tests
```bash
python reset_commande_test.py
```

## Sécurité et Validation

### Contraintes de base de données
- Statuts validés par contrainte CHECK
- Clés étrangères pour l'intégrité référentielle
- Transactions pour la cohérence des données

### Validations interface
- Vérification des champs obligatoires
- Confirmation pour les actions critiques (livraison, annulation)
- Gestion des erreurs avec messages utilisateur

### Traçabilité
- Horodatage automatique des modifications
- Référence de document dans les mouvements
- Historique complet des changements de statut

## Évolutions possibles

1. **Livraisons partielles** : Gestion du statut "Partielle"
2. **Notifications** : Alertes automatiques selon les statuts
3. **Workflow configurable** : Personnalisation des transitions
4. **Approbations** : Workflow d'approbation multi-niveaux
5. **Intégration EDI** : Échange automatique avec les fournisseurs

## Dépendances

- PySide6 : Interface utilisateur
- psycopg2 : Connexion PostgreSQL
- python-dotenv : Configuration
- datetime : Gestion des dates