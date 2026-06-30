# Système de Statuts de Mouvement - Gestion de Stock

## 🎯 Objectif

Résoudre le problème de double encodage lors de la réception de marchandises en introduisant un système de statuts pour les mouvements de stock. Cela permet de différencier clairement les étapes de réception et de mise en stock effective.

## 🔄 Problème Résolu

**Avant :** 
- La réception créait immédiatement un mouvement avec impact sur le stock
- Quand le magasinier déplaçait physiquement les pièces, il y avait risque de double comptage
- Pas de distinction entre "reçu" et "en stock"

**Après :**
- La réception crée un mouvement EN_ATTENTE (sans impact stock)
- La confirmation applique l'impact sur le stock
- La mise en stock physique gère les emplacements
- Traçabilité complète du processus

## 📊 Nouveaux Statuts de Mouvement

### 1. EN_ATTENTE
- **Usage :** Mouvement créé mais pas encore confirmé
- **Impact stock :** Aucun (stock_avant = stock_après)
- **Cas d'usage :** Réception de marchandises en attente de validation

### 2. CONFIRME
- **Usage :** Mouvement validé et appliqué
- **Impact stock :** Selon le type de mouvement (entrée/sortie)
- **Cas d'usage :** Mouvement standard, réception confirmée

### 3. ANNULE
- **Usage :** Mouvement annulé
- **Impact stock :** Aucun
- **Cas d'usage :** Erreur de saisie, réception refusée

## 🔧 Workflow de Réception Amélioré

### Étape 1 : Réception Initiale
```python
# Création d'un lot de réception
lot_id = reception_service.creer_lot_reception(
    piece_id=piece_id,
    quantite_recue=10,
    utilisateur_id=user_id,
    commentaire="Livraison fournisseur XYZ"
)
```

**Résultat :**
- ✅ Lot créé avec statut `EN_RECEPTION`
- ✅ Mouvement tracé avec statut `EN_ATTENTE`
- ✅ Stock de la pièce **inchangé**
- ✅ Quantité visible dans "stock en réception"

### Étape 2 : Confirmation de Réception
```python
# Confirmation par le magasinier
success = reception_service.confirmer_reception_lot(
    lot_id=lot_id,
    utilisateur_id=user_id,
    commentaire_confirmation="Contrôle qualité OK"
)
```

**Résultat :**
- ✅ Mouvement passe en statut `CONFIRME`
- ✅ Stock de la pièce **mis à jour** (+10)
- ✅ Lot passe en statut `PRET_STOCKAGE`
- ✅ Prêt pour mise en stock physique

### Étape 3 : Mise en Stock Physique
```python
# Déplacement vers l'emplacement final
success = reception_service.mettre_en_stock(
    lot_id=lot_id,
    emplacement_destination_id=emplacement_id,
    quantite_a_stocker=10,
    utilisateur_id=user_id
)
```

**Résultat :**
- ✅ Transfert de la zone réception vers l'emplacement
- ✅ Stock par emplacement mis à jour
- ✅ Lot passe en statut `STOCKE`
- ✅ Processus terminé

## 🛠️ Nouvelles Fonctionnalités

### Gestion des Mouvements en Attente

```python
# Récupérer les mouvements en attente
mouvements_attente = mouvement_service.get_mouvements_en_attente()

# Confirmer un mouvement
success = mouvement_service.confirmer_mouvement_reception(
    mouvement_id=mouvement_id,
    utilisateur_id=user_id,
    commentaire_confirmation="Validation manuelle"
)

# Annuler un mouvement
success = mouvement_service.annuler_mouvement_reception(
    mouvement_id=mouvement_id,
    utilisateur_id=user_id,
    raison_annulation="Erreur de saisie"
)
```

### Dashboard de Réception

```python
# Tableau de bord détaillé
dashboard = reception_service.get_dashboard_reception_detaille()

# Indicateurs disponibles :
# - LOTS_EN_RECEPTION : Nombre de lots en cours
# - LOTS_PRET_STOCKAGE : Lots prêts pour stockage
# - MOUVEMENTS_EN_ATTENTE : Mouvements à confirmer
# - QUANTITE_EN_RECEPTION : Quantité totale en attente
# - LOTS_EN_ATTENTE_CONFIRMATION : Lots à valider
# - TEMPS_MOYEN_ATTENTE : Temps moyen en heures
```

### Lots en Attente de Confirmation

```python
# Récupérer les lots nécessitant une action
lots_attente = reception_service.get_lots_en_attente_confirmation()

# Chaque lot contient :
# - Informations du lot (numéro, pièce, quantité)
# - Temps d'attente en heures
# - Statut du mouvement associé
```

## 📋 Nouvelles Vues SQL

### v_mouvements_en_attente
Affiche tous les mouvements en attente de confirmation avec le temps d'attente.

### v_dashboard_reception
Fournit les indicateurs clés pour le tableau de bord de réception.

### v_historique_mouvements (mise à jour)
Inclut maintenant le statut du mouvement dans l'historique.

## 🔧 Nouvelles Fonctions SQL

### confirmer_mouvement_en_attente()
```sql
SELECT confirmer_mouvement_en_attente(
    mouvement_id, 
    utilisateur_id, 
    commentaire_confirmation
);
```

### annuler_mouvement_en_attente()
```sql
SELECT annuler_mouvement_en_attente(
    mouvement_id, 
    utilisateur_id, 
    raison_annulation
);
```

## 🚀 Migration et Déploiement

### 1. Appliquer la Migration
```bash
python apply_mouvement_statut_migration.py
```

### 2. Vérifications Post-Migration
- ✅ Colonne `statut_mouvement` ajoutée à `mouvement_stock`
- ✅ Nouvelles vues créées
- ✅ Nouvelles fonctions disponibles
- ✅ Triggers configurés
- ✅ Index optimisés

### 3. Test du Workflow
Le script de migration inclut un test complet qui :
- Crée un lot de réception
- Vérifie que le stock n'est pas impacté
- Confirme la réception
- Vérifie la mise à jour du stock
- Teste l'annulation

## 📊 Avantages du Nouveau Système

### ✅ Évite le Double Encodage
- Réception et stockage sont des étapes distinctes
- Pas de risque de compter deux fois la même quantité

### ✅ Traçabilité Complète
- Chaque étape est tracée avec son statut
- Historique complet des actions

### ✅ Contrôle de Qualité
- Possibilité de valider avant impact stock
- Annulation possible en cas d'erreur

### ✅ Visibilité Opérationnelle
- Dashboard temps réel
- Indicateurs de performance
- Suivi des temps d'attente

### ✅ Flexibilité
- Workflow adaptable selon les besoins
- Possibilité de réception partielle
- Gestion des quarantaines

## 🔍 Cas d'Usage Typiques

### Réception Standard
1. Livraison arrive → Création lot (EN_ATTENTE)
2. Contr��le qualité → Confirmation (CONFIRME)
3. Rangement → Mise en stock (STOCKE)

### Réception avec Problème
1. Livraison arrive → Création lot (EN_ATTENTE)
2. Problème détecté → Annulation (ANNULE)
3. Lot en quarantaine → Traitement spécial

### Réception Partielle
1. Livraison partielle → Création lot (EN_ATTENTE)
2. Validation partielle → Confirmation (CONFIRME)
3. Stockage progressif → Mise en stock par lots

## 🔧 Configuration et Personnalisation

### Types de Mouvement Supportés
- `RECEPTION_ACHAT` : impact_stock = 0 (réception)
- `MISE_EN_STOCK` : impact_stock = 1 (stockage)
- `ENTREE_ACHAT` : impact_stock = 1 (entrée directe)
- `SORTIE_CONSOMMATION` : impact_stock = -1 (sortie)

### Statuts de Lot
- `EN_RECEPTION` : Lot créé, en attente de validation
- `PRET_STOCKAGE` : Lot validé, prêt pour stockage
- `STOCKE` : Lot complètement stocké
- `QUARANTAINE` : Lot en quarantaine

## 📞 Support et Maintenance

### Surveillance
- Surveiller les mouvements en attente trop longtemps
- Vérifier la cohérence des stocks régulièrement
- Analyser les temps de traitement

### Maintenance
- Archiver les anciens mouvements annulés
- Optimiser les index selon l'usage
- Ajuster les seuils d'alerte

### Dépannage
- Vérifier les logs pour les erreurs de confirmation
- Contrôler la cohérence stock global vs emplacements
- Valider les triggers et contraintes

---

*Ce système améliore significativement la gestion des réceptions en évitant les erreurs de double comptage tout en maintenant une traçabilité complète du processus.*