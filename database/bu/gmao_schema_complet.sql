-- Script de création complet de la base de données GMAO
-- Combinaison de schema.sql, mouvement_schema.sql et mouvement_schema_migration.sql
-- Ce script permet d'initialiser complètement la base de données en une seule opération

-- ============================================================================================
-- PARTIE 1: TABLES PRINCIPALES (schema.sql)
-- ============================================================================================

-- Script de création des tables utilisées par l'application GMAO
-- Généré automatiquement à partir des repositories Python
-- Ajout d'index et de triggers pour la cohérence et la performance

CREATE TABLE IF NOT EXISTS inventory_warehouses (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    description TEXT,
    adresse TEXT,
    ville VARCHAR(100),
    pays VARCHAR(100),
    code_postal VARCHAR(20),
    responsable_id INTEGER,
    actif BOOLEAN DEFAULT TRUE,
    max_aisles INTEGER DEFAULT 10 CHECK (max_aisles > 0),
    max_shelves INTEGER DEFAULT 5 CHECK (max_shelves > 0),
    max_levels INTEGER DEFAULT 4 CHECK (max_levels > 0)
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_inventory_warehouse_nom ON inventory_warehouse(nom);


CREATE TABLE IF NOT EXISTS fabricant (
    id_fabricant SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    contact VARCHAR(100),
    site_web VARCHAR(255),
    support_technique VARCHAR(255)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fabricant_nom ON fabricant(nom);

CREATE TABLE IF NOT EXISTS fournisseur (
    id_fournisseur SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    contact VARCHAR(100),
    adresse TEXT,
    telephone VARCHAR(50),
    email VARCHAR(255),
    delai_livraison_moyen_j INTEGER,
    devise VARCHAR(10) DEFAULT 'EUR',
    note_qualite INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fournisseur_nom ON fournisseur(nom);
CREATE INDEX IF NOT EXISTS idx_fournisseur_email ON fournisseur(email);

CREATE TABLE IF NOT EXISTS site (
    id_site SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    adresse TEXT,
    ville VARCHAR(100),
    pays VARCHAR(100),
    contact_principal VARCHAR(100)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_site_nom ON site(nom);

CREATE TABLE IF NOT EXISTS type_machine (
    id_type_machine SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    description TEXT,
    categorie VARCHAR(100)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_type_machine_nom ON type_machine(nom);

CREATE TABLE IF NOT EXISTS machine (
    id_machine SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    serial VARCHAR(100),
    modele VARCHAR(100),
    date_installation DATE,
    localisation VARCHAR(100),
    etat VARCHAR(50),
    informations_techniques TEXT,
    type_machine_id INTEGER REFERENCES type_machine(id_type_machine),
    site_id INTEGER REFERENCES site(id_site),
    fabricant_id INTEGER REFERENCES fabricant(id_fabricant),
    parent_machine_id INTEGER REFERENCES machine(id_machine),
    criticite VARCHAR(50),
    garantie_fin DATE
);

CREATE INDEX IF NOT EXISTS idx_machine_type ON machine(type_machine_id);
CREATE INDEX IF NOT EXISTS idx_machine_site ON machine(site_id);
CREATE INDEX IF NOT EXISTS idx_machine_fabricant ON machine(fabricant_id);
CREATE INDEX IF NOT EXISTS idx_machine_parent ON machine(parent_machine_id);

CREATE TABLE IF NOT EXISTS piece_category (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    description TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_piece_category_nom ON piece_category(nom);

CREATE TABLE IF NOT EXISTS piece_unit (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL,
    description TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_piece_unit_nom ON piece_unit(nom);

CREATE TABLE IF NOT EXISTS piece_statut (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL,
    description TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_piece_statut_nom ON piece_statut(nom);

CREATE TABLE IF NOT EXISTS emplacement (
    id SERIAL PRIMARY KEY,
    magasin_id INTEGER REFERENCES inventory_warehouse(id),
    nom VARCHAR(100) NOT NULL,
    type VARCHAR(50),
    allee VARCHAR(50),
    etagere VARCHAR(50),
    niveau VARCHAR(50)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_emplacement_nom ON emplacement(nom);

CREATE TABLE IF NOT EXISTS piece (
    id_piece SERIAL PRIMARY KEY,
    reference VARCHAR(100) NOT NULL,
    nom VARCHAR(100) NOT NULL,
    fournisseur_pref_id INTEGER REFERENCES fournisseur(id_fournisseur),
    prix_unitaire DECIMAL(10,2),
    stock_alerte INTEGER DEFAULT 0,
    stock_actuel INTEGER DEFAULT 0,
    stock_reserve INTEGER DEFAULT 0,
    unite VARCHAR(50),
    categorie VARCHAR(100),
    emplacement_stockage VARCHAR(100),
    statut VARCHAR(50) DEFAULT 'Actif',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_piece_reference ON piece(reference);
CREATE INDEX IF NOT EXISTS idx_piece_nom ON piece(nom);
CREATE INDEX IF NOT EXISTS idx_piece_fournisseur ON piece(fournisseur_pref_id);

CREATE TABLE IF NOT EXISTS piece_extension (
    id_piece INTEGER PRIMARY KEY REFERENCES piece(id_piece),
    unite_id INTEGER REFERENCES piece_unit(id),
    categorie_id INTEGER REFERENCES piece_category(id),
    emplacement_id INTEGER REFERENCES emplacement(id),
    statut_id INTEGER REFERENCES piece_statut(id),
    machine_id INTEGER REFERENCES machine(id_machine)
);

CREATE INDEX IF NOT EXISTS idx_piece_extension_unite ON piece_extension(unite_id);
CREATE INDEX IF NOT EXISTS idx_piece_extension_categorie ON piece_extension(categorie_id);
CREATE INDEX IF NOT EXISTS idx_piece_extension_emplacement ON piece_extension(emplacement_id);
CREATE INDEX IF NOT EXISTS idx_piece_extension_statut ON piece_extension(statut_id);
CREATE INDEX IF NOT EXISTS idx_piece_extension_machine ON piece_extension(machine_id);

CREATE TABLE IF NOT EXISTS utilisateur (
    id_utilisateur SERIAL PRIMARY KEY,
    login VARCHAR(100) NOT NULL UNIQUE,
    mot_de_passe_hash VARCHAR(255) NOT NULL,
    nom_complet VARCHAR(100),
    role VARCHAR(50),
    email VARCHAR(255),
    actif BOOLEAN DEFAULT TRUE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_utilisateur_login ON utilisateur(login);
CREATE INDEX IF NOT EXISTS idx_utilisateur_email ON utilisateur(email);

-- Trigger pour la mise à jour automatique de updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='fournisseur' AND column_name='updated_at') THEN
        IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='set_updated_at_fournisseur') THEN
            CREATE TRIGGER set_updated_at_fournisseur
            BEFORE UPDATE ON fournisseur
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        END IF;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='piece' AND column_name='updated_at') THEN
        IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='set_updated_at_piece') THEN
            CREATE TRIGGER set_updated_at_piece
            BEFORE UPDATE ON piece
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        END IF;
    END IF;
END$$;

-- ============================================================================================
-- PARTIE 2: TABLES DE MOUVEMENTS (mouvement_schema_migration.sql)
-- ============================================================================================

-- Migration script for mouvement_stock tables

-- Vérifier si la table mouvement_stock existe déjà avec la structure correcte
DO $$
DECLARE
    column_exists BOOLEAN;
BEGIN
    -- Vérifier si la colonne type_mouvement_id existe
    SELECT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'mouvement_stock' 
        AND column_name = 'type_mouvement_id'
    ) INTO column_exists;
    
    -- Si la table existe mais n'a pas la bonne structure, on la supprime
    IF NOT column_exists AND EXISTS (
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_name = 'mouvement_stock'
    ) THEN
        DROP TABLE mouvement_stock CASCADE;
    END IF;
END$$;

-- Create type_mouvement table first
CREATE TABLE IF NOT EXISTS type_mouvement (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    impact_stock INTEGER NOT NULL CHECK (impact_stock IN (-1, 1)), -- -1 pour sortie, 1 pour entrée
    actif BOOLEAN DEFAULT TRUE
);

-- Insert basic movement types
INSERT INTO type_mouvement (nom, description, impact_stock) VALUES
('ENTREE_ACHAT', 'Entrée suite à un achat', 1),
('ENTREE_RETOUR', 'Entrée suite à un retour', 1),
('ENTREE_INVENTAIRE', 'Entrée suite à un ajustement d''inventaire', 1),
('SORTIE_CONSOMMATION', 'Sortie pour consommation/utilisation', -1),
('SORTIE_RETOUR_FOURNISSEUR', 'Sortie pour retour fournisseur', -1),
('SORTIE_INVENTAIRE', 'Sortie suite à un ajustement d''inventaire', -1),
('TRANSFERT_ENTREE', 'Entrée suite à un transfert', 1),
('TRANSFERT_SORTIE', 'Sortie suite à un transfert', -1),
('SORTIE_PERTE', 'Sortie pour perte/casse', -1),
('SORTIE_OBSOLESCENCE', 'Sortie pour obsolescence', -1)
ON CONFLICT (nom) DO NOTHING;

-- Create the new mouvement_stock table with enhanced structure
CREATE TABLE IF NOT EXISTS mouvement_stock (
    id SERIAL PRIMARY KEY,
    piece_id INTEGER NOT NULL REFERENCES piece(id_piece),
    type_mouvement_id INTEGER NOT NULL REFERENCES type_mouvement(id),
    quantite INTEGER NOT NULL CHECK (quantite > 0),
    emplacement_source_id INTEGER REFERENCES emplacement(id),
    emplacement_destination_id INTEGER REFERENCES emplacement(id),
    utilisateur_id INTEGER REFERENCES utilisateur(id_utilisateur),
    date_mouvement TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reference_document VARCHAR(100), -- Bon de commande, bon de livraison, etc.
    commentaire TEXT,
    cout_unitaire DECIMAL(10,2),
    cout_total DECIMAL(10,2),
    stock_avant INTEGER NOT NULL,
    stock_apres INTEGER NOT NULL,
    valide BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour optimiser les performances
CREATE INDEX IF NOT EXISTS idx_mouvement_stock_piece ON mouvement_stock(piece_id);
CREATE INDEX IF NOT EXISTS idx_mouvement_stock_type ON mouvement_stock(type_mouvement_id);
CREATE INDEX IF NOT EXISTS idx_mouvement_stock_date ON mouvement_stock(date_mouvement);
CREATE INDEX IF NOT EXISTS idx_mouvement_stock_utilisateur ON mouvement_stock(utilisateur_id);
CREATE INDEX IF NOT EXISTS idx_mouvement_stock_emplacement_source ON mouvement_stock(emplacement_source_id);
CREATE INDEX IF NOT EXISTS idx_mouvement_stock_emplacement_dest ON mouvement_stock(emplacement_destination_id);

-- Trigger pour la mise à jour automatique de updated_at
DO $$
BEGIN
    -- Vérifier si la fonction existe déjà
    IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'update_mouvement_updated_at') THEN
        CREATE FUNCTION update_mouvement_updated_at()
        RETURNS TRIGGER AS $BODY$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $BODY$ LANGUAGE plpgsql;
    END IF;
    
    -- Vérifier si le trigger existe déjà
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_updated_at_mouvement_stock') THEN
        CREATE TRIGGER set_updated_at_mouvement_stock
            BEFORE UPDATE ON mouvement_stock
            FOR EACH ROW
            EXECUTE FUNCTION update_mouvement_updated_at();
    END IF;
END$$;

-- Fonction pour calculer automatiquement le coût total
DO $$
BEGIN
    -- Vérifier si la fonction existe déjà
    IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'calculate_cout_total') THEN
        CREATE FUNCTION calculate_cout_total()
        RETURNS TRIGGER AS $BODY$
        BEGIN
            IF NEW.cout_unitaire IS NOT NULL AND NEW.quantite IS NOT NULL THEN
                NEW.cout_total = NEW.cout_unitaire * NEW.quantite;
            END IF;
            RETURN NEW;
        END;
        $BODY$ LANGUAGE plpgsql;
    END IF;
    
    -- Vérifier si le trigger existe déjà
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'calculate_cout_total_trigger') THEN
        CREATE TRIGGER calculate_cout_total_trigger
            BEFORE INSERT OR UPDATE ON mouvement_stock
            FOR EACH ROW
            EXECUTE FUNCTION calculate_cout_total();
    END IF;
END$$;

-- Vue pour les statistiques de mouvements
CREATE OR REPLACE VIEW v_mouvement_stats AS
SELECT 
    p.id_piece,
    p.reference,
    p.nom as piece_nom,
    tm.nom as type_mouvement,
    COUNT(*) as nb_mouvements,
    SUM(ms.quantite) as quantite_totale,
    SUM(ms.cout_total) as cout_total,
    MIN(ms.date_mouvement) as premier_mouvement,
    MAX(ms.date_mouvement) as dernier_mouvement
FROM mouvement_stock ms
JOIN piece p ON ms.piece_id = p.id_piece
JOIN type_mouvement tm ON ms.type_mouvement_id = tm.id
WHERE ms.valide = TRUE
GROUP BY p.id_piece, p.reference, p.nom, tm.id, tm.nom;

-- Vue pour l'historique détaillé des mouvements
CREATE OR REPLACE VIEW v_historique_mouvements AS
SELECT 
    ms.id,
    ms.date_mouvement,
    p.reference as piece_reference,
    p.nom as piece_nom,
    tm.nom as type_mouvement,
    tm.impact_stock,
    ms.quantite,
    ms.stock_avant,
    ms.stock_apres,
    es.nom as emplacement_source,
    ed.nom as emplacement_destination,
    u.nom_complet as utilisateur,
    ms.reference_document,
    ms.commentaire,
    ms.cout_unitaire,
    ms.cout_total
FROM mouvement_stock ms
JOIN piece p ON ms.piece_id = p.id_piece
JOIN type_mouvement tm ON ms.type_mouvement_id = tm.id
LEFT JOIN emplacement es ON ms.emplacement_source_id = es.id
LEFT JOIN emplacement ed ON ms.emplacement_destination_id = ed.id
LEFT JOIN utilisateur u ON ms.utilisateur_id = u.id_utilisateur
WHERE ms.valide = TRUE
ORDER BY ms.date_mouvement DESC;

-- ============================================================================================
-- PARTIE 3: ATTRIBUTION DES DROITS
-- ============================================================================================

-- Droits pour l'utilisateur applicatif
DO $$
BEGIN
    -- Attribution des droits standards sur toutes les tables
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO gmao_app_user;
    
    -- Droits spécifiques pour les tables de mouvements
    GRANT SELECT, INSERT, UPDATE, DELETE ON mouvement_stock TO gmao_app_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON type_mouvement TO gmao_app_user;
    GRANT SELECT ON v_mouvement_stats TO gmao_app_user;
    GRANT SELECT ON v_historique_mouvements TO gmao_app_user;
    
    -- Droits sur les séquences
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO gmao_app_user;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Une erreur s''est produite lors de l''attribution des permissions: %', SQLERRM;
END$$;
