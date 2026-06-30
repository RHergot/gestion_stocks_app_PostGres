# Extension des Emplacements - Documentation

## Vue d'ensemble

Cette extension ajoute des fonctionnalités avancées de gestion des emplacements au système GMAO, incluant :

1. **Dimensions physiques** (Longueur × Hauteur × Profondeur)
2. **Gestion détaillée du stock par emplacement**
3. **Transferts entre emplacements**
4. **Vérification de cohérence des stocks**
5. **Conditions de stockage spécialisées**

## 🏗️ Architecture

### Nouvelles Tables

#### `emplacement_ext`
Extension des emplacements avec propriétés physiques :
- `longueur_cm`, `hauteur_cm`, `profondeur_cm` : Dimensions en centimètres
- `volume_cm3` : Volume calculé automatiquement (L×H×P)
- `capacite_max_kg` : Capacité maximale en poids
- `temperature_min_c`, `temperature_max_c` : Plage de température
- `humidite_max_pct` : Humidité maximale
- `conditions_speciales` : Conditions particulières de stockage

#### `emplacement_stock`
Stock détaillé par emplacement et par pièce :
- `emplacement_id`, `piece_id` : Clés de liaison
- `quantite` : Quantité stockée
- `date_derniere_entree`, `date_derniere_sortie` : Traçabilité
- `commentaire` : Notes sur le stockage

### Vues Créées

#### `v_emplacement_detail`
Vue complète des emplacements avec leurs propriétés étendues et statistiques de stock.

#### `v_stock_par_emplacement`
Vue détaillée du stock par emplacement avec informations des pièces.

#### `v_emplacement_capacite`
Vue des capacités et taux d'occupation des emplacements.

### Fonctions Utilitaires

#### `deplacer_stock(piece_id, source_id, dest_id, quantite, commentaire)`
Fonction atomique pour déplacer du stock entre emplacements.

#### `nettoyer_stocks_zero()`
Supprime les enregistrements de stock à quantité zéro.

## 🚀 Installation

### 1. Exécuter le script d'initialisation
```bash
python init_emplacement_extension.py
```

### 2. Vérifier l'installation
```bash
python test_emplacement_extension.py
```

## 💻 Utilisation

### Dialogue d'Emplacement Étendu

Le dialogue d'emplacement a été enrichi avec 3 onglets :

#### Onglet 1 : Informations de Base
- ID Magasin
- Nom (généré automatiquement)
- Type d'emplacement
- Coordonnées (Allée, Étagère, Niveau)

#### Onglet 2 : Dimensions Physiques
- Longueur, Hauteur, Profondeur (en cm)
- Volume calculé automatiquement
- Capacité maximale (en kg)

#### Onglet 3 : Conditions de Stockage
- Plage de température
- Humidité maximale
- Conditions spéciales

### Services Disponibles

#### EmplacementExtService
```python
from APP.services.emplacement_ext_service import EmplacementExtService

service = EmplacementExtService(db)

# Récupérer un emplacement complet
emplacement = service.get_emplacement_complet(emplacement_id)

# Ajouter du stock
service.ajouter_stock_piece(emplacement_id, piece_id, quantite, commentaire)

# Transférer du stock
service.transferer_stock(piece_id, source_id, dest_id, quantite, commentaire)

# Vérifier la cohérence
incoherences = service.verifier_coherence_stock_global()
```

#### MouvementService Étendu
```python
from APP.services.mouvement_service import MouvementService

service = MouvementService(db)

# Créer un mouvement avec emplacement
service.creer_mouvement_entree(
    piece_id=1,
    quantite=10,
    type_mouvement_id=1,
    emplacement_destination_id=5,
    commentaire="Réception commande"
)

# Transfert entre emplacements
service.creer_mouvement_transfert(
    piece_id=1,
    quantite=5,
    emplacement_source_id=5,
    emplacement_destination_id=6
)
```

## 🔄 Intégration avec les Mouvements

### Entrées de Stock
Lors d'une entrée de stock avec emplacement spécifié :
1. Le stock global de la pièce est mis à jour
2. Le stock dans l'emplacement est incrémenté
3. Un mouvement est enregistré avec l'emplacement destination

### Sorties de Stock
Lors d'une sortie de stock avec emplacement spécifié :
1. Vérification du stock disponible dans l'emplacement
2. Le stock global de la pièce est mis à jour
3. Le stock dans l'emplacement est décrémenté
4. Un mouvement est enregistré avec l'emplacement source

### Transferts
Les transferts entre emplacements :
1. Utilisent une fonction atomique pour garantir la cohérence
2. N'affectent pas le stock global de la pièce
3. Créent deux mouvements (sortie + entrée) pour la traçabilité

## 📊 Cohérence des Données

### Principe
**Le stock total d'une pièce doit toujours égaler la somme des quantités dans tous les emplacements.**

### Vérification
```python
# Vérifier les incohérences
incoherences = service.verifier_coherence_stock_global()

for inc in incoherences:
    print(f"Pièce {inc['reference']}: "
          f"Global={inc['stock_global']}, "
          f"Emplacements={inc['total_emplacements']}")
```

### Correction
```python
# Corriger en recalculant le stock global
service.corriger_incoherence_stock(piece_id, forcer_stock_global=True)
```

## 🔍 Requêtes Utiles

### Stock par emplacement
```sql
SELECT * FROM v_stock_par_emplacement 
WHERE emplacement_id = 1 
ORDER BY piece_reference;
```

### Emplacements avec capacité libre
```sql
SELECT * FROM v_emplacement_capacite 
WHERE capacite_restante > 10 
ORDER BY capacite_restante DESC;
```

### Recherche de pièces
```sql
SELECT * FROM v_stock_par_emplacement 
WHERE piece_reference ILIKE '%ABC%' 
   OR piece_nom ILIKE '%ABC%';
```

## 🛠️ Maintenance

### Nettoyage des stocks vides
```python
# Supprimer les enregistrements à quantité zéro
nb_nettoyes = service.nettoyer_stocks_vides()
```

### Statistiques d'emplacement
```python
# Obtenir les statistiques détaillées
stats = service.get_statistiques_emplacement(emplacement_id)
print(f"Pièces différentes: {stats['nb_pieces_differentes']}")
print(f"Quantité totale: {stats['quantite_totale']}")
```

## 🚨 Points d'Attention

### 1. Cohérence des Données
- Toujours vérifier la cohérence après des opérations manuelles
- Utiliser les fonctions de service plutôt que des requêtes SQL directes

### 2. Performance
- Les vues sont optimisées avec des index
- Nettoyer régulièrement les stocks à zéro

### 3. Sécurité
- Les transferts utilisent des transactions atomiques
- Les vérifications de stock sont effectuées avant chaque opération

## 📈 Évolutions Futures

### Fonctionnalités Prévues
- [ ] Gestion des zones de stockage (température contrôlée, etc.)
- [ ] Optimisation automatique des emplacements
- [ ] Alertes de capacité
- [ ] Historique détaillé des mouvements par emplacement
- [ ] Interface graphique pour la visualisation des emplacements

### Améliorations Possibles
- [ ] Calcul automatique du poids total par emplacement
- [ ] Gestion des dimensions des pièces pour optimisation
- [ ] Intégration avec un système de codes-barres
- [ ] Rapports de rotation des stocks par emplacement

## 🆘 Dépannage

### Problème : Incohérences de stock
**Solution :** Exécuter la vérification et correction :
```python
incoherences = service.verifier_coherence_stock_global()
for inc in incoherences:
    service.corriger_incoherence_stock(inc['piece_id'])
```

### Problème : Transfert impossible
**Causes possibles :**
- Stock insuffisant dans l'emplacement source
- Emplacements source et destination identiques
- Pièce inexistante

### Problème : Dialogue d'emplacement ne s'affiche pas
**Solution :** Vérifier que la base de données contient les tables d'extension :
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_name IN ('emplacement_ext', 'emplacement_stock');
```

## 📞 Support

Pour toute question ou problème :
1. Vérifier les logs d'erreur
2. Exécuter les scripts de test
3. Consulter cette documentation
4. Vérifier la cohérence des données

---

*Documentation générée automatiquement - Version 1.0*