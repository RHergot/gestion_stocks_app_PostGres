from APP.models.commande_repository import CommandeRepository

# Liste ordonnée des clés attendues (doit correspondre à HEADER_LABELS du modèle)
COMMANDE_HEADER_KEYS = [
    "id_commande",
    "numero_commande",
    "fournisseur_nom",
    "createur_nom",
    "date_commande",
    "date_livraison_prevue",
    "date_livraison_reelle",
    "statut",
    "total_ht",
    "frais_port",
    "reference_fournisseur",
    "mode_paiement",
    "notes_commande",
    "created_at",
    "updated_at"
]

def get_all_commandes_clean(db):
    print("\n[DEBUG] Retrieval des commandes depuis la base de données...")
    repo = CommandeRepository(db)
    commandes = repo.get_all_commandes()
    
    if not commandes:
        print("[DEBUG] Aucune commande trouvée dans la base de données.")
        return []
        
    print(f"[DEBUG] {len(commandes)} commandes récupérées.")
    print("[DEBUG] Première commande :", commandes[0])
    
    # Nettoie chaque dict pour garantir la présence et l'ordre des clés
    cleaned = []
    for cmd in commandes:
        row = {k: cmd.get(k, "") for k in COMMANDE_HEADER_KEYS}
        cleaned.append(row)
    
    print("[DEBUG] Données nettoyées. Première ligne :", cleaned[0] if cleaned else "Aucune donnée")
    return cleaned
