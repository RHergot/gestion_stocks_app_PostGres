# gmao_app/app/data/schemas.py
"""
Contient les requêtes SQL pour définir le schéma de la base de données.
"""
from typing import Dict

# Clé: Nom de la table/objet, Valeur: Requête SQL CREATE
TABLES: Dict[str, str] = {
    # --- Tables de référence (créées en premier) ---
    "SITE": """
        CREATE TABLE IF NOT EXISTS SITE (
            id_site INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE,
            adresse TEXT,
            ville TEXT,
            pays TEXT,
            contact_principal TEXT
            -- created_at, updated_at ? Optionnel pour ces références simples
        );
    """,
    "FABRICANT": """
        CREATE TABLE IF NOT EXISTS FABRICANT (
            id_fabricant INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE,
            contact TEXT,
            site_web TEXT,
            support_technique TEXT
            -- created_at, updated_at ? Optionnel
        );
    """,
    "TYPE_MACHINE": """
        CREATE TABLE IF NOT EXISTS TYPE_MACHINE (
            id_type_machine INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE,
            description TEXT,
            categorie TEXT
            -- created_at, updated_at ? Optionnel
        );
    """,
    "EQUIPE": """
        CREATE TABLE IF NOT EXISTS EQUIPE (
            id_equipe INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE,
            domaine_expertise TEXT,
            responsable_id INTEGER, -- FK vers TECHNICIEN
            FOREIGN KEY (responsable_id) REFERENCES TECHNICIEN(id_technicien) ON DELETE SET NULL
        );
    """,
    "TECHNICIEN": """
        CREATE TABLE IF NOT EXISTS TECHNICIEN (
            id_technicien INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prenom TEXT,
            qualification TEXT,
            contact TEXT,
            cout_horaire REAL DEFAULT 0.0,
            equipe_id INTEGER, -- Nullable
            actif INTEGER DEFAULT 1,
            FOREIGN KEY (equipe_id) REFERENCES EQUIPE(id_equipe) ON DELETE SET NULL
            -- Ajouter contrainte UNIQUE(nom, prenom) ?
        );
    """,

    # --- Table Utilisateur ---
    "UTILISATEUR": """
        CREATE TABLE IF NOT EXISTS UTILISATEUR (
            id_utilisateur INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            mot_de_passe_hash TEXT NOT NULL,
            nom_complet TEXT,
            role TEXT NOT NULL, -- CHECK constraint recommandée
            email TEXT UNIQUE,
            actif INTEGER DEFAULT 1,
            derniere_connexion TEXT, -- ISO timestamp string
            technicien_id INTEGER, -- Nullable
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(technicien_id) REFERENCES TECHNICIEN(id_technicien) ON DELETE SET NULL
        );
    """,

    # --- Table Machine ---
    "MACHINE": """
        CREATE TABLE IF NOT EXISTS MACHINE (
            id_machine INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            serial TEXT UNIQUE, -- Nullable?
            modele TEXT,
            date_installation TEXT, -- ISO Date YYYY-MM-DD
            localisation TEXT,
            etat TEXT DEFAULT 'Inconnu', -- CHECK recommandée
            informations_techniques TEXT,
            type_machine_id INTEGER NOT NULL,
            site_id INTEGER NOT NULL,
            fabricant_id INTEGER NOT NULL,
            parent_machine_id INTEGER, -- Nullable
            criticite TEXT, -- CHECK recommandée (ex: A, B, C)
            garantie_fin TEXT, -- ISO Date YYYY-MM-DD
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (type_machine_id) REFERENCES TYPE_MACHINE(id_type_machine) ON DELETE RESTRICT,
            FOREIGN KEY (site_id) REFERENCES SITE(id_site) ON DELETE RESTRICT,
            FOREIGN KEY (fabricant_id) REFERENCES FABRICANT(id_fabricant) ON DELETE RESTRICT,
            FOREIGN KEY (parent_machine_id) REFERENCES MACHINE(id_machine) ON DELETE SET NULL
        );
    """,

    # --- Table Fournisseur ---
    "FOURNISSEUR": """
        CREATE TABLE IF NOT EXISTS FOURNISSEUR (
            id_fournisseur INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE,
            contact TEXT,
            adresse TEXT,
            telephone TEXT,
            email TEXT,
            delai_livraison_moyen_j INTEGER,
            devise TEXT DEFAULT 'EUR', -- CHECK recommandée
            note_qualite REAL, -- Note sur 5? Nullable
            updated_at TEXT -- Ajout pour le trigger
        );
    """,

    # --- Table Piece ---
    "PIECE": """
        CREATE TABLE IF NOT EXISTS PIECE (
            id_piece INTEGER PRIMARY KEY AUTOINCREMENT,
            reference TEXT NOT NULL UNIQUE,
            nom TEXT NOT NULL,
            fournisseur_pref_id INTEGER, -- Nullable
            prix_unitaire REAL DEFAULT 0.0 CHECK(prix_unitaire >= 0),
            stock_alerte INTEGER DEFAULT 0 CHECK(stock_alerte >= 0),
            stock_actuel INTEGER DEFAULT 0 CHECK(stock_actuel >= 0),
            stock_reserve INTEGER DEFAULT 0 CHECK(stock_reserve >= 0),
            unite TEXT NOT NULL, -- CHECK recommandée
            categorie TEXT,
            emplacement_stockage TEXT,
            statut TEXT DEFAULT 'Actif', -- CHECK recommandée
            updated_at TEXT, -- Ajout pour trigger et suivi modif stock/prix
            FOREIGN KEY (fournisseur_pref_id) REFERENCES FOURNISSEUR(id_fournisseur) ON DELETE SET NULL
            -- CONSTRAINT check_stock CHECK (stock_actuel >= stock_reserve) -- Possible? Vérifie stock >= réservé
        );
    """,

    # --- Tables Maintenance ---
    "ORDRE_TRAVAIL": """
        CREATE TABLE IF NOT EXISTS ORDRE_TRAVAIL (
            id_ot INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_ot TEXT UNIQUE,
            machine_id INTEGER NOT NULL,
            gamme_id INTEGER, -- Sera lié à GAMME_ENTRETIEN plus tard
            type TEXT NOT NULL, -- CHECK recommandée
            description TEXT NOT NULL,
            date_creation TEXT DEFAULT CURRENT_TIMESTAMP,
            date_prevue TEXT, -- ISO Timestamp string
            duree_prevue_min INTEGER,
            priorite TEXT, -- CHECK recommandée
            urgence INTEGER DEFAULT 0,
            statut TEXT NOT NULL, -- CHECK recommandée
            technicien_assigne_id INTEGER,
            utilisateur_createur_id INTEGER NOT NULL,
            notes_planification TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (machine_id) REFERENCES MACHINE(id_machine) ON DELETE CASCADE,
            -- FOREIGN KEY (gamme_id) REFERENCES GAMME_ENTRETIEN(id_gamme) ON DELETE SET NULL, -- Futur
            FOREIGN KEY (technicien_assigne_id) REFERENCES TECHNICIEN(id_technicien) ON DELETE SET NULL,
            FOREIGN KEY (utilisateur_createur_id) REFERENCES UTILISATEUR(id_utilisateur) ON DELETE RESTRICT
        );
    """,
    "MAINTENANCE": """
        CREATE TABLE IF NOT EXISTS MAINTENANCE (
            id_maintenance INTEGER PRIMARY KEY AUTOINCREMENT,
            ot_id INTEGER NOT NULL UNIQUE,
            machine_id INTEGER, -- FK MACHINE (Optionnel)
            technicien_id INTEGER NOT NULL,
            date_debut_reelle TEXT NOT NULL, -- ISO Timestamp string
            date_fin_reelle TEXT NOT NULL, -- ISO Timestamp string
            duree_intervention_h REAL,
            type_reel TEXT NOT NULL, -- CHECK recommandée
            description_travaux TEXT NOT NULL,
            resultat TEXT NOT NULL, -- CHECK recommandée
            cout_manuel_v1 REAL,
            -- Nouveaux champs financiers (Phase 11)
            cout_main_oeuvre REAL DEFAULT 0.0,
            cout_pieces_internes REAL DEFAULT 0.0,
            cout_pieces_externes REAL DEFAULT 0.0,
            cout_autres_frais REAL DEFAULT 0.0,
            cout_total REAL DEFAULT 0.0,
            evaluation_qualite INTEGER,
            impact_production TEXT, -- CHECK recommandée
            notes_technicien TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ot_id) REFERENCES ORDRE_TRAVAIL(id_ot) ON DELETE CASCADE,
            FOREIGN KEY (machine_id) REFERENCES MACHINE(id_machine) ON DELETE SET NULL,
            FOREIGN KEY (technicien_id) REFERENCES TECHNICIEN(id_technicien) ON DELETE RESTRICT
        );
    """,
    "INTERVENTION_PIECE": """
        CREATE TABLE IF NOT EXISTS INTERVENTION_PIECE (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            maintenance_id INTEGER NOT NULL,
            piece_id INTEGER NOT NULL,
            quantite INTEGER NOT NULL CHECK(quantite > 0),
            lot TEXT,
            FOREIGN KEY (maintenance_id) REFERENCES MAINTENANCE(id_maintenance) ON DELETE CASCADE,
            FOREIGN KEY (piece_id) REFERENCES PIECE(id_piece) ON DELETE RESTRICT
        );
    """,
    # --- Table Mouvement Stock ---
    "MOUVEMENT_STOCK": """
        CREATE TABLE IF NOT EXISTS MOUVEMENT_STOCK (
            id_mouvement INTEGER PRIMARY KEY AUTOINCREMENT,
            piece_id INTEGER NOT NULL,
            type_mouvement TEXT NOT NULL CHECK(type_mouvement IN ('ENTREE', 'SORTIE', 'AJUSTEMENT', 'INVENTAIRE', 'TRANSFERT')),
            quantite INTEGER NOT NULL, -- Peut être négatif pour sorties/ajustements
            date_mouvement TEXT DEFAULT CURRENT_TIMESTAMP,
            raison TEXT,
            ot_id INTEGER,  -- FK vers ORDRE_TRAVAIL (pour consommations liées à OT)
            user_id INTEGER, -- Qui a fait l'ajustement manuel / inventaire
            stock_avant INTEGER, -- Stock avant ce mouvement (informatif)
            stock_apres INTEGER, -- Stock après ce mouvement (informatif)
            emplacement_source_id INTEGER, -- Pour les transferts entre emplacements
            emplacement_destination_id INTEGER, -- Pour les transferts entre emplacements
            reference_document TEXT, -- Bon de commande, bon de livraison, etc.
            cout_unitaire REAL, -- Prix unitaire de la pièce pour ce mouvement
            cout_total REAL, -- Prix total pour ce mouvement (quantité * cout_unitaire)
            commentaire TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (piece_id) REFERENCES PIECE(id_piece) ON DELETE RESTRICT,
            FOREIGN KEY (ot_id) REFERENCES ORDRE_TRAVAIL(id_ot) ON DELETE SET NULL,
            FOREIGN KEY (user_id) REFERENCES UTILISATEUR(id_utilisateur) ON DELETE SET NULL
        );
    """,

    # --- Tables de gestion avancée des mouvements (Phase 12) ---
    "TYPE_MOUVEMENT": """
        CREATE TABLE IF NOT EXISTS TYPE_MOUVEMENT (
            id_type_mouvement INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE,
            description TEXT,
            impact_stock INTEGER NOT NULL CHECK (impact_stock IN (-1, 1)), -- -1 pour sortie, 1 pour entrée
            actif INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """,

    # --- Tables Gammes (Phase 6) ---
    "GAMME_ENTRETIEN": """
        CREATE TABLE IF NOT EXISTS GAMME_ENTRETIEN (
            id_gamme INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL UNIQUE, -- Nom/Code de la gamme
            type_entretien TEXT, -- CHECK recommandée
            periodicite_valeur INTEGER,
            periodicite_unite TEXT, -- CHECK recommandée (Jours, Semaines, Mois, Heures...)
            instructions TEXT,
            date_derniere_realisation TEXT, -- ISO Date YYYY-MM-DD
            prochaine_date_calculee TEXT, -- ISO Date YYYY-MM-DD (non normé, mais pratique)
            active INTEGER DEFAULT 1,
            type_machine_id INTEGER, -- Peut être lié à un type de machine
            createur_id INTEGER, -- FK Utilisateur
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            duree_estimee_min INTEGER, -- Durée totale estimée gamme
            qualification_requise TEXT, -- Compétence nécessaire
            priorite TEXT, -- Priorité par défaut pour OT générés? CHECK recommandée
            FOREIGN KEY (type_machine_id) REFERENCES TYPE_MACHINE(id_type_machine) ON DELETE SET NULL,
            FOREIGN KEY (createur_id) REFERENCES UTILISATEUR(id_utilisateur) ON DELETE SET NULL
        );
    """,
    "GAMME_ETAPE": """
        CREATE TABLE IF NOT EXISTS GAMME_ETAPE (
            id_etape INTEGER PRIMARY KEY AUTOINCREMENT,
            gamme_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            ordre INTEGER NOT NULL, -- Ordre d'exécution de l'étape
            instructions_detaillees TEXT,
            duree_estimee_min INTEGER,
            FOREIGN KEY (gamme_id) REFERENCES GAMME_ENTRETIEN(id_gamme) ON DELETE CASCADE -- Si gamme supprimée, supprime étapes
            -- UNIQUE (gamme_id, ordre) -- Assurer ordre unique par gamme
        );
    """,
    "GAMME_PIECE_TYPE": """
        CREATE TABLE IF NOT EXISTS GAMME_PIECE_TYPE (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gamme_id INTEGER NOT NULL,
            piece_id INTEGER NOT NULL,
            quantite_theorique INTEGER DEFAULT 1 CHECK(quantite_theorique >= 0),
            FOREIGN KEY (gamme_id) REFERENCES GAMME_ENTRETIEN(id_gamme) ON DELETE CASCADE,
            FOREIGN KEY (piece_id) REFERENCES PIECE(id_piece) ON DELETE CASCADE, -- Si pièce supprimée, retirer des gammes? CASCADE ou RESTRICT? Discutable. CASCADE ici.
            UNIQUE (gamme_id, piece_id) -- Ne pas lister deux fois la même pièce pour une gamme
        );
    """,


     # --- NOUVELLES TABLES (Phase 7: Achats) ---
    "COMMANDE": """
        CREATE TABLE IF NOT EXISTS COMMANDE (
            id_commande INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_commande TEXT UNIQUE, -- Numéro unique interne ou fournisseur
            fournisseur_id INTEGER NOT NULL,
            createur_id INTEGER NOT NULL, -- Utilisateur qui a créé la commande
            date_commande TEXT NOT NULL, -- ISO Date YYYY-MM-DD
            date_livraison_prevue TEXT, -- ISO Date YYYY-MM-DD
            date_livraison_reelle TEXT, -- ISO Date YYYY-MM-DD (Dernière livraison?)
            statut TEXT NOT NULL CHECK(statut IN ('Brouillon', 'Validee', 'Envoyee', 'Partielle', 'Livree', 'Annulee')) DEFAULT 'Brouillon',
            total_ht REAL DEFAULT 0.0, -- Calculé ou saisi? Mieux si calculé par trigger/service?
            frais_port REAL DEFAULT 0.0,
            -- total_ttc REAL, -- Si besoin TVA
            reference_fournisseur TEXT, -- Réf commande chez le fournisseur
            mode_paiement TEXT,
            notes_commande TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (fournisseur_id) REFERENCES FOURNISSEUR(id_fournisseur) ON DELETE RESTRICT,
            FOREIGN KEY (createur_id) REFERENCES UTILISATEUR(id_utilisateur) ON DELETE RESTRICT
        );
    """,
    "LIGNE_COMMANDE": """
        CREATE TABLE IF NOT EXISTS LIGNE_COMMANDE (
            id_ligne INTEGER PRIMARY KEY AUTOINCREMENT,
            commande_id INTEGER NOT NULL,
            piece_id INTEGER NOT NULL,
            description_libre TEXT, -- Si pièce non cataloguée
            quantite_commandee INTEGER NOT NULL CHECK(quantite_commandee > 0),
            prix_unitaire_ht REAL NOT NULL CHECK(prix_unitaire_ht >= 0),
            quantite_recue INTEGER DEFAULT 0 CHECK(quantite_recue >= 0),
            date_reception TEXT, -- ISO Date YYYY-MM-DD (Dernière réception pour cette ligne)
            statut_ligne TEXT NOT NULL CHECK(statut_ligne IN ('Attente', 'Partielle', 'Recue')) DEFAULT 'Attente',
            FOREIGN KEY (commande_id) REFERENCES COMMANDE(id_commande) ON DELETE CASCADE, -- Si on supprime la commande, on supprime les lignes
            FOREIGN KEY (piece_id) REFERENCES PIECE(id_piece) ON DELETE RESTRICT -- On ne peut pas supprimer une pièce si elle est dans une ligne de commande
            -- UNIQUE (commande_id, piece_id) -- Pour éviter d'avoir deux fois la même pièce sur une commande? Discutable.
        );
    """,

    "COMPTEUR": """
        CREATE TABLE IF NOT EXISTS COMPTEUR (
            id_compteur INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id INTEGER NOT NULL,
            nom TEXT NOT NULL,
            unite TEXT NOT NULL,
            valeur_actuelle REAL DEFAULT 0.0,
            date_dernier_releve TEXT, -- ISO Date YYYY-MM-DD
            seuil_alerte REAL, -- Nullable
            seuil_prev_ot REAL, -- Nullable
            -- actif INTEGER DEFAULT 1, -- Optionnel si vous l'ajoutez au modèle/DB
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (machine_id) REFERENCES MACHINE(id_machine) ON DELETE CASCADE, -- Supprimer compteurs si machine supprimée
            UNIQUE (machine_id, nom) -- Une machine ne peut avoir qu'un seul compteur du même nom/type
        );
    """,
    "HISTORIQUE_COMPTEUR": """
        CREATE TABLE IF NOT EXISTS HISTORIQUE_COMPTEUR (
            id_historique INTEGER PRIMARY KEY AUTOINCREMENT,
            compteur_id INTEGER NOT NULL,
            date_releve TEXT DEFAULT CURRENT_TIMESTAMP, -- ISO Timestamp YYYY-MM-DD HH:MM:SS.sss
            valeur REAL NOT NULL,
            utilisateur_id INTEGER, -- Nullable: qui a fait le relevé manuel?
            maintenance_id INTEGER, -- Nullable: si relevé fait pendant maintenance (lien facultatif)
            FOREIGN KEY (compteur_id) REFERENCES COMPTEUR(id_compteur) ON DELETE CASCADE, -- Supprimer historiques si compteur supprimé
            FOREIGN KEY (utilisateur_id) REFERENCES UTILISATEUR(id_utilisateur) ON DELETE SET NULL,
            FOREIGN KEY (maintenance_id) REFERENCES MAINTENANCE(id_maintenance) ON DELETE SET NULL
        );
    """,

    # --- NOUVELLES TABLES (Phase 11: Gestion Financière) ---
    "MAINTENANCE_INTERVENANT": """
        CREATE TABLE IF NOT EXISTS MAINTENANCE_INTERVENANT (
            id_intervenant INTEGER PRIMARY KEY AUTOINCREMENT,
            maintenance_id INTEGER NOT NULL,
            technicien_id INTEGER, -- NULL si intervenant externe
            nom_intervenant_externe TEXT, -- NULL si technicien_id n'est pas NULL
            heures_travaillees REAL NOT NULL CHECK(heures_travaillees > 0),
            cout_horaire REAL NOT NULL CHECK(cout_horaire >= 0),
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (maintenance_id) REFERENCES MAINTENANCE(id_maintenance) ON DELETE CASCADE,
            FOREIGN KEY (technicien_id) REFERENCES TECHNICIEN(id_technicien) ON DELETE RESTRICT,
            -- Soit technicien_id soit nom_intervenant_externe doit être non NULL
            CHECK ((technicien_id IS NOT NULL) OR (nom_intervenant_externe IS NOT NULL))
        );
    """,
    "MAINTENANCE_FRAIS_EXTERNE": """
        CREATE TABLE IF NOT EXISTS MAINTENANCE_FRAIS_EXTERNE (
            id_frais INTEGER PRIMARY KEY AUTOINCREMENT,
            maintenance_id INTEGER NOT NULL,
            type_frais TEXT NOT NULL CHECK(type_frais IN ('PIECE_EXTERNE', 'DEPLACEMENT', 'SOUS_TRAITANCE', 'AUTRE')),
            description TEXT NOT NULL,
            montant REAL NOT NULL CHECK(montant >= 0),
            quantite INTEGER DEFAULT 1 CHECK(quantite > 0),
            reference_piece TEXT, -- Pour les pièces externes
            fournisseur TEXT, -- Pour les pièces/services externes
            facture_reference TEXT, -- Pour référence comptable
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (maintenance_id) REFERENCES MAINTENANCE(id_maintenance) ON DELETE CASCADE
        );
    """,

    # --- Index pour Phase 6 ---
    "IDX_GAMME_TYPE_MACHINE": """
        CREATE INDEX IF NOT EXISTS idx_gamme_type_machine ON GAMME_ENTRETIEN(type_machine_id);
    """,
    "IDX_GAMME_ETAPE_GAMME": """
        CREATE INDEX IF NOT EXISTS idx_gamme_etape_gamme ON GAMME_ETAPE(gamme_id);
    """,
     "IDX_GAMME_PIECE_GAMME": """
        CREATE INDEX IF NOT EXISTS idx_gamme_piece_gamme ON GAMME_PIECE_TYPE(gamme_id);
    """,
     "IDX_GAMME_PIECE_PIECE": """
        CREATE INDEX IF NOT EXISTS idx_gamme_piece_piece ON GAMME_PIECE_TYPE(piece_id);
    """,

    # --- Index généraux déjà définis ---
    "IDX_INTERVENTION_PIECE_MAINT": """
        CREATE INDEX IF NOT EXISTS idx_intervention_piece_maint ON INTERVENTION_PIECE(maintenance_id);
    """,
    "IDX_INTERVENTION_PIECE_PIECE": """
        CREATE INDEX IF NOT EXISTS idx_intervention_piece_piece ON INTERVENTION_PIECE(piece_id);
    """,

     # --- NOUVEAUX INDEX (Phase 8) ---
    "IDX_COMPTEUR_MACHINE": """
        CREATE INDEX IF NOT EXISTS idx_compteur_machine ON COMPTEUR(machine_id);
    """,
     "IDX_HISTORIQUE_COMPTEUR": """
        CREATE INDEX IF NOT EXISTS idx_historique_compteur ON HISTORIQUE_COMPTEUR(compteur_id);
    """,
     "IDX_HISTORIQUE_UTILISATEUR": """
        CREATE INDEX IF NOT EXISTS idx_historique_utilisateur ON HISTORIQUE_COMPTEUR(utilisateur_id);
    """,
    "IDX_HISTORIQUE_MAINTENANCE": """
        CREATE INDEX IF NOT EXISTS idx_historique_maintenance ON HISTORIQUE_COMPTEUR(maintenance_id);
    """,

    # --- Index pour les mouvements de stock (Phase 12) ---
    "IDX_MOUVEMENT_PIECE": """
        CREATE INDEX IF NOT EXISTS idx_mouvement_piece ON MOUVEMENT_STOCK(piece_id);
    """,
    "IDX_MOUVEMENT_TYPE": """
        CREATE INDEX IF NOT EXISTS idx_mouvement_type ON MOUVEMENT_STOCK(type_mouvement);
    """,
    "IDX_MOUVEMENT_DATE": """
        CREATE INDEX IF NOT EXISTS idx_mouvement_date ON MOUVEMENT_STOCK(date_mouvement);
    """,
    "IDX_MOUVEMENT_UTILISATEUR": """
        CREATE INDEX IF NOT EXISTS idx_mouvement_user ON MOUVEMENT_STOCK(user_id);
    """,
    "IDX_MOUVEMENT_OT": """
        CREATE INDEX IF NOT EXISTS idx_mouvement_ot ON MOUVEMENT_STOCK(ot_id);
    """,

    # --- Ajoutons des indices pour les nouvelles tables ---
    "IDX_MAINTENANCE_INTERVENANT_MAINT": """
        CREATE INDEX IF NOT EXISTS idx_maintenance_intervenant_maint ON MAINTENANCE_INTERVENANT(maintenance_id);
    """,
    "IDX_MAINTENANCE_INTERVENANT_TECH": """
        CREATE INDEX IF NOT EXISTS idx_maintenance_intervenant_tech ON MAINTENANCE_INTERVENANT(technicien_id);
    """,
    "IDX_MAINTENANCE_FRAIS_MAINT": """
        CREATE INDEX IF NOT EXISTS idx_maintenance_frais_maint ON MAINTENANCE_FRAIS_EXTERNE(maintenance_id);
    """,
    "IDX_MAINTENANCE_FRAIS_TYPE": """
        CREATE INDEX IF NOT EXISTS idx_maintenance_frais_type ON MAINTENANCE_FRAIS_EXTERNE(type_frais);
    """,
}

# --- Triggers ---
TRIGGERS: Dict[str, str] = {
    "UTILISATEUR_update_trigger": """
        CREATE TRIGGER IF NOT EXISTS utilisateur_updated_at
        AFTER UPDATE ON UTILISATEUR FOR EACH ROW BEGIN
            UPDATE UTILISATEUR SET updated_at = CURRENT_TIMESTAMP WHERE id_utilisateur = OLD.id_utilisateur;
        END;
    """,
    "MACHINE_update_trigger": """
        CREATE TRIGGER IF NOT EXISTS machine_updated_at
        AFTER UPDATE ON MACHINE FOR EACH ROW BEGIN
            UPDATE MACHINE SET updated_at = CURRENT_TIMESTAMP WHERE id_machine = OLD.id_machine;
        END;
    """,
    "ORDRE_TRAVAIL_update_trigger": """
        CREATE TRIGGER IF NOT EXISTS ot_updated_at
        AFTER UPDATE ON ORDRE_TRAVAIL FOR EACH ROW BEGIN
            UPDATE ORDRE_TRAVAIL SET updated_at = CURRENT_TIMESTAMP WHERE id_ot = OLD.id_ot;
        END;
    """,
    "FOURNISSEUR_update_trigger": """
        CREATE TRIGGER IF NOT EXISTS fournisseur_updated_at
        AFTER UPDATE ON FOURNISSEUR FOR EACH ROW BEGIN
            UPDATE FOURNISSEUR SET updated_at = CURRENT_TIMESTAMP WHERE id_fournisseur = OLD.id_fournisseur;
        END;
    """, # Assure-toi que la colonne updated_at est bien dans la table FOURNISSEUR
    "PIECE_update_trigger": """
        CREATE TRIGGER IF NOT EXISTS piece_updated_at
        AFTER UPDATE ON PIECE FOR EACH ROW BEGIN
            UPDATE PIECE SET updated_at = CURRENT_TIMESTAMP WHERE id_piece = OLD.id_piece;
        END;
    """,
    # Trigger pour GAMME_ENTRETIEN
    "GAMME_ENTRETIEN_update_trigger": """
        CREATE TRIGGER IF NOT EXISTS gamme_updated_at
        AFTER UPDATE ON GAMME_ENTRETIEN FOR EACH ROW BEGIN
            UPDATE GAMME_ENTRETIEN SET updated_at = CURRENT_TIMESTAMP WHERE id_gamme = OLD.id_gamme;
        END;
    """,


     # --- NOUVEAU TRIGGER (Phase 7) ---
    "COMMANDE_update_trigger": """
        CREATE TRIGGER IF NOT EXISTS commande_updated_at
        AFTER UPDATE ON COMMANDE FOR EACH ROW BEGIN
            UPDATE COMMANDE SET updated_at = CURRENT_TIMESTAMP WHERE id_commande = OLD.id_commande;
        END;
    """,
    # Pas de trigger pour MOUVEMENT_STOCK, GAMME_ETAPE, GAMME_PIECE_TYPE a priori

     # --- NOUVEAUX TRIGGERS (Phase 8) ---
     "COMPTEUR_update_trigger": """
        CREATE TRIGGER IF NOT EXISTS compteur_updated_at
        AFTER UPDATE ON COMPTEUR FOR EACH ROW BEGIN
            UPDATE COMPTEUR SET updated_at = CURRENT_TIMESTAMP WHERE id_compteur = OLD.id_compteur;
        END;
    """,
    # Pas de trigger pour HISTORIQUE_COMPTEUR, c'est un log de faits passés.

    # --- NOUVEAUX TRIGGERS (Phase 11) ---
    # Pas de triggers nécessaires pour les tables MAINTENANCE_INTERVENANT et MAINTENANCE_FRAIS_EXTERNE car elles ne sont modifiées que lors de leur création
    
    # --- NOUVEAUX TRIGGERS (Phase 12: Mouvements Stock) ---
    "MOUVEMENT_update_trigger": """
        CREATE TRIGGER IF NOT EXISTS mouvement_updated_at
        AFTER UPDATE ON MOUVEMENT_STOCK FOR EACH ROW BEGIN
            UPDATE MOUVEMENT_STOCK SET updated_at = CURRENT_TIMESTAMP WHERE id_mouvement = OLD.id_mouvement;
        END;
    """
}

# --- Données de base à insérer ---
BASE_DATA: Dict[str, str] = {
    "TYPE_MOUVEMENT_DATA": """
        INSERT INTO TYPE_MOUVEMENT (nom, description, impact_stock) VALUES
        ('ENTREE_ACHAT', 'Entrée suite à un achat', 1),
        ('ENTREE_RETOUR', 'Entrée suite à un retour', 1),
        ('ENTREE_INVENTAIRE', 'Entrée suite à un ajustement d''inventaire', 1),
        ('SORTIE_CONSOMMATION', 'Sortie pour consommation/utilisation', -1),
        ('SORTIE_RETOUR_FOURNISSEUR', 'Sortie pour retour fournisseur', -1),
        ('SORTIE_INVENTAIRE', 'Sortie suite à un ajustement d''inventaire', -1),
        ('TRANSFERT_ENTREE', 'Entrée suite à un transfert', 1),
        ('TRANSFERT_SORTIE', 'Sortie suite à un transfert', -1),
        ('SORTIE_PERTE', 'Sortie pour perte/casse', -1),
        ('SORTIE_OBSOLESCENCE', 'Sortie pour obsolescence', -1);
    """
}