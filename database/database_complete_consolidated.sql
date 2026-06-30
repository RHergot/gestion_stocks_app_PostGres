-- ============================================================================================
-- FICHIER SQL CONSOLIDÉ POUR L'INITIALISATION DE LA BASE DE DONNÉES GMAO
-- Ce script combine les fichiers SQL suivants :
-- - gmao_schema_complet.sql (qui inclut schema.sql et mouvement_schema_migration.sql)
-- - emplacement_extension_schema.sql
-- - reception_workflow_schema.sql
-- - mouvement_statut_migration.sql
-- - reception_schema_migration.sql
--
-- ATTENTION : Ce script a des dépendances sur les tables 'commande' et 'ligne_commande'.
--             Assurez-vous que ces tables sont définies avant d'exécuter les sections
--             qui les référencent (marquées par des commentaires).
-- ============================================================================================

-- ============================================================================================
-- PARTIE 1: TABLES PRINCIPALES (Basé sur schema.sql, via gmao_schema_complet.sql)
-- ============================================================================================

-- Script de création des tables utilisées par l'application GMAO
-- Généré automatiquement à partir des repositories Python
-- Ajout d'index et de triggers pour la cohérence et la performance

CREATE TABLE IF NOT EXISTS inventory_warehouse (
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
-- PARTIE 2: EXTENSION DES EMPLACEMENTS (emplacement_extension_schema.sql)
-- ============================================================================================

-- Schema pour l'extension des emplacements avec dimensions et stock détaillé
-- Auteur: Système GMAO
-- Date: 2024

-- Table pour les dimensions et propriétés étendues des emplacements
CREATE TABLE IF NOT EXISTS emplacement_ext (
    emplacement_id INTEGER PRIMARY KEY REFERENCES emplacement(id) ON DELETE CASCADE,
    longueur_cm DECIMAL(8,2) CHECK (longueur_cm > 0),
    hauteur_cm DECIMAL(8,2) CHECK (hauteur_cm > 0), 
    profondeur_cm DECIMAL(8,2) CHECK (profondeur_cm > 0),
    volume_cm3 DECIMAL(15,2) GENERATED ALWAYS AS (longueur_cm * hauteur_cm * profondeur_cm) STORED,
    capacite_max_kg DECIMAL(10,2) CHECK (capacite_max_kg >= 0),
    temperature_min_c DECIMAL(5,2),
    temperature_max_c DECIMAL(5,2),
    humidite_max_pct DECIMAL(5,2) CHECK (humidite_max_pct >= 0 AND humidite_max_pct <= 100),
    conditions_speciales TEXT,
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_temperature CHECK (temperature_max_c IS NULL OR temperature_min_c IS NULL OR temperature_max_c >= temperature_min_c)
);

-- Table pour le stock détaillé par emplacement
CREATE TABLE IF NOT EXISTS emplacement_stock (
    id SERIAL PRIMARY KEY,
    emplacement_id INTEGER NOT NULL REFERENCES emplacement(id) ON DELETE CASCADE,
    piece_id INTEGER NOT NULL REFERENCES piece(id_piece) ON DELETE CASCADE,
    quantite INTEGER NOT NULL DEFAULT 0 CHECK (quantite >= 0),
    date_derniere_entree TIMESTAMP,
    date_derniere_sortie TIMESTAMP,
    date_derniere_maj TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    commentaire TEXT,
    UNIQUE(emplacement_id, piece_id)
);

-- Index pour optimiser les performances
CREATE INDEX IF NOT EXISTS idx_emplacement_ext_volume ON emplacement_ext(volume_cm3);
CREATE INDEX IF NOT EXISTS idx_emplacement_ext_capacite ON emplacement_ext(capacite_max_kg);
CREATE INDEX IF NOT EXISTS idx_emplacement_stock_emplacement ON emplacement_stock(emplacement_id);
CREATE INDEX IF NOT EXISTS idx_emplacement_stock_piece ON emplacement_stock(piece_id);
CREATE INDEX IF NOT EXISTS idx_emplacement_stock_quantite ON emplacement_stock(quantite) WHERE quantite > 0;

-- Trigger pour la mise à jour automatique de updated_at
CREATE OR REPLACE FUNCTION update_emplacement_ext_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at_emplacement_ext
    BEFORE UPDATE ON emplacement_ext
    FOR EACH ROW
    EXECUTE FUNCTION update_emplacement_ext_updated_at();

-- Trigger pour la mise à jour de date_derniere_maj dans emplacement_stock
CREATE OR REPLACE FUNCTION update_emplacement_stock_maj()
RETURNS TRIGGER AS $$
BEGIN
    NEW.date_derniere_maj = NOW();
    
    -- Mettre à jour les dates d'entrée/sortie selon le contexte
    IF NEW.quantite > COALESCE(OLD.quantite, 0) THEN
        NEW.date_derniere_entree = NOW();
    ELSIF NEW.quantite < COALESCE(OLD.quantite, 0) THEN
        NEW.date_derniere_sortie = NOW();
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at_emplacement_stock
    BEFORE UPDATE ON emplacement_stock
    FOR EACH ROW
    EXECUTE FUNCTION update_emplacement_stock_maj();

-- Trigger pour initialiser les dates lors de l'insertion
CREATE OR REPLACE FUNCTION init_emplacement_stock_dates()
RETURNS TRIGGER AS $$
BEGIN
    NEW.date_derniere_maj = NOW();
    IF NEW.quantite > 0 THEN
        NEW.date_derniere_entree = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER init_dates_emplacement_stock
    BEFORE INSERT ON emplacement_stock
    FOR EACH ROW
    EXECUTE FUNCTION init_emplacement_stock_dates();

-- Fonction pour vérifier la cohérence du stock
CREATE OR REPLACE FUNCTION check_stock_coherence()
RETURNS TRIGGER AS $$
DECLARE
    total_emplacement INTEGER;
    stock_piece INTEGER;
    piece_id_check INTEGER;
BEGIN
    -- Déterminer l'ID de la pièce à vérifier
    piece_id_check := COALESCE(NEW.piece_id, OLD.piece_id);
    
    -- Calculer le total dans les emplacements pour cette pièce
    SELECT COALESCE(SUM(quantite), 0) INTO total_emplacement
    FROM emplacement_stock 
    WHERE piece_id = piece_id_check;
    
    -- Récupérer le stock actuel de la pièce
    SELECT stock_actuel INTO stock_piece
    FROM piece 
    WHERE id_piece = piece_id_check;
    
    -- Vérifier la cohérence (avec tolérance pour les opérations en cours)
    IF total_emplacement != COALESCE(stock_piece, 0) THEN
        RAISE WARNING 'Incohérence stock détectée pour pièce %: Total emplacements (%) != Stock pièce (%)', 
                     piece_id_check, total_emplacement, COALESCE(stock_piece, 0);
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger de vérification de cohérence (en mode WARNING pour ne pas bloquer)
CREATE TRIGGER check_coherence_emplacement_stock
    AFTER INSERT OR UPDATE OR DELETE ON emplacement_stock
    FOR EACH ROW
    EXECUTE FUNCTION check_stock_coherence();

-- Vue pour l'état détaillé des emplacements
CREATE OR REPLACE VIEW v_emplacement_detail AS
SELECT 
    e.id,
    e.nom,
    e.type,
    e.allee,
    e.etagere,
    e.niveau,
    ext.longueur_cm,
    ext.hauteur_cm,
    ext.profondeur_cm,
    ext.volume_cm3,
    ext.capacite_max_kg,
    ext.temperature_min_c,
    ext.temperature_max_c,
    ext.humidite_max_pct,
    ext.conditions_speciales,
    COALESCE(stock_info.nb_pieces_differentes, 0) as nb_pieces_differentes,
    COALESCE(stock_info.quantite_totale, 0) as quantite_totale,
    CASE 
        WHEN ext.capacite_max_kg IS NOT NULL AND stock_info.quantite_totale > 0 
        THEN ROUND((stock_info.quantite_totale::DECIMAL / ext.capacite_max_kg) * 100, 2)
        ELSE NULL 
    END as taux_occupation_pct
FROM emplacement e
LEFT JOIN emplacement_ext ext ON e.id = ext.emplacement_id
LEFT JOIN (
    SELECT 
        emplacement_id,
        COUNT(*) as nb_pieces_differentes,
        SUM(quantite) as quantite_totale
    FROM emplacement_stock 
    WHERE quantite > 0
    GROUP BY emplacement_id
) stock_info ON e.id = stock_info.emplacement_id;

-- Vue pour le stock par emplacement avec détails des pièces
CREATE OR REPLACE VIEW v_stock_par_emplacement AS
SELECT 
    e.id as emplacement_id,
    e.nom as emplacement_nom,
    e.type as emplacement_type,
    e.allee,
    e.etagere,
    e.niveau,
    p.id_piece,
    p.reference as piece_reference,
    p.nom as piece_nom,
    p.categorie as piece_categorie,
    es.quantite,
    es.date_derniere_entree,
    es.date_derniere_sortie,
    es.date_derniere_maj,
    es.commentaire,
    p.stock_actuel as stock_total_piece,
    CASE 
        WHEN p.stock_actuel > 0 
        THEN ROUND((es.quantite::DECIMAL / p.stock_actuel) * 100, 2)
        ELSE 0 
    END as pourcentage_piece_dans_emplacement
FROM emplacement e
JOIN emplacement_stock es ON e.id = es.emplacement_id
JOIN piece p ON es.piece_id = p.id_piece
WHERE es.quantite > 0
ORDER BY e.nom, p.reference;

-- Vue pour les emplacements avec leurs capacités
CREATE OR REPLACE VIEW v_emplacement_capacite AS
SELECT 
    e.id,
    e.nom,
    e.type,
    ext.volume_cm3,
    ext.capacite_max_kg,
    COALESCE(SUM(es.quantite), 0) as stock_actuel,
    CASE 
        WHEN ext.capacite_max_kg IS NOT NULL AND ext.capacite_max_kg > 0
        THEN ROUND((COALESCE(SUM(es.quantite), 0)::DECIMAL / ext.capacite_max_kg) * 100, 2)
        ELSE NULL 
    END as taux_remplissage_pct,
    CASE 
        WHEN ext.capacite_max_kg IS NOT NULL 
        THEN ext.capacite_max_kg - COALESCE(SUM(es.quantite), 0)
        ELSE NULL 
    END as capacite_restante
FROM emplacement e
LEFT JOIN emplacement_ext ext ON e.id = ext.emplacement_id
LEFT JOIN emplacement_stock es ON e.id = es.emplacement_id AND es.quantite > 0
GROUP BY e.id, e.nom, e.type, ext.volume_cm3, ext.capacite_max_kg
ORDER BY e.nom;

-- Fonction utilitaire pour nettoyer les stocks à zéro
CREATE OR REPLACE FUNCTION nettoyer_stocks_zero()
RETURNS INTEGER AS $$
DECLARE
    nb_supprime INTEGER;
BEGIN
    DELETE FROM emplacement_stock WHERE quantite = 0;
    GET DIAGNOSTICS nb_supprime = ROW_COUNT;
    RETURN nb_supprime;
END;
$$ LANGUAGE plpgsql;

-- Fonction pour déplacer du stock entre emplacements
CREATE OR REPLACE FUNCTION deplacer_stock(
    p_piece_id INTEGER,
    p_emplacement_source_id INTEGER,
    p_emplacement_destination_id INTEGER,
    p_quantite INTEGER,
    p_commentaire TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    stock_source INTEGER;
BEGIN
    -- Vérifier le stock source
    SELECT quantite INTO stock_source
    FROM emplacement_stock
    WHERE emplacement_id = p_emplacement_source_id AND piece_id = p_piece_id;
    
    IF stock_source IS NULL OR stock_source < p_quantite THEN
        RAISE EXCEPTION 'Stock insuffisant dans l''emplacement source (disponible: %, demandé: %)', 
                       COALESCE(stock_source, 0), p_quantite;
    END IF;
    
    -- Décrémenter le stock source
    UPDATE emplacement_stock 
    SET quantite = quantite - p_quantite,
        commentaire = COALESCE(p_commentaire, commentaire)
    WHERE emplacement_id = p_emplacement_source_id AND piece_id = p_piece_id;
    
    -- Incrémenter le stock destination (ou créer l'enregistrement)
    INSERT INTO emplacement_stock (emplacement_id, piece_id, quantite, commentaire)
    VALUES (p_emplacement_destination_id, p_piece_id, p_quantite, p_commentaire)
    ON CONFLICT (emplacement_id, piece_id)
    DO UPDATE SET 
        quantite = emplacement_stock.quantite + p_quantite,
        commentaire = COALESCE(p_commentaire, emplacement_stock.commentaire);
    
    -- Nettoyer les stocks à zéro
    DELETE FROM emplacement_stock 
    WHERE emplacement_id = p_emplacement_source_id 
      AND piece_id = p_piece_id 
      AND quantite = 0;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Commentaires sur les tables
COMMENT ON TABLE emplacement_ext IS 'Extension des emplacements avec dimensions et propriétés physiques';
COMMENT ON TABLE emplacement_stock IS 'Stock détaillé par emplacement et par pièce';
COMMENT ON COLUMN emplacement_ext.volume_cm3 IS 'Volume calculé automatiquement (L×H×P)';
COMMENT ON COLUMN emplacement_ext.capacite_max_kg IS 'Capacité maximale en poids';
COMMENT ON COLUMN emplacement_stock.quantite IS 'Quantité de la pièce dans cet emplacement';
COMMENT ON FUNCTION deplacer_stock IS 'Fonction pour déplacer du stock entre emplacements de manière atomique';

-- ============================================================================================
-- PARTIE 3: TABLES DE MOUVEMENTS (Basé sur mouvement_schema_migration.sql, via gmao_schema_complet.sql)
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
-- PARTIE 4: WORKFLOW DE RÉCEPTION (reception_workflow_schema.sql)
-- ============================================================================================
-- ATTENTION: Les sections suivantes dépendent des tables 'commande' et 'ligne_commande'.
--            Assurez-vous que ces tables sont définies si vous utilisez ces fonctionnalités.

-- 4.1. Modification de type_mouvement et ajout de nouveaux types
ALTER TABLE type_mouvement DROP CONSTRAINT IF EXISTS type_mouvement_impact_stock_check;
ALTER TABLE type_mouvement ADD CONSTRAINT type_mouvement_impact_stock_check 
    CHECK (impact_stock IN (-1, 0, 1));

INSERT INTO type_mouvement (nom, description, impact_stock) VALUES
('RECEPTION_ACHAT', 'Réception de marchandises (zone de réception)', 0),  -- Impact 0 = pas d''impact sur stock emplacement
('MISE_EN_STOCK', 'Mise en stock depuis la réception', 1),
('SORTIE_RECEPTION', 'Sortie de la zone de réception', -1),
('RETOUR_RECEPTION', 'Retour vers la zone de réception', 0)
ON CONFLICT (nom) DO NOTHING;

-- 4.2. Création d'emplacements spéciaux pour la réception
INSERT INTO inventory_warehouse (nom, description, actif) VALUES
('MAGASIN_PRINCIPAL', 'Magasin principal', TRUE)
ON CONFLICT (nom) DO NOTHING; -- Conflit sur nom au lieu de DO NOTHING simple

DO $$
DECLARE
    v_magasin_id INTEGER;
BEGIN
    SELECT id INTO v_magasin_id FROM inventory_warehouse WHERE nom = 'MAGASIN_PRINCIPAL' LIMIT 1;
    
    IF v_magasin_id IS NOT NULL THEN
        -- Créer les emplacements de réception
        INSERT INTO emplacement (magasin_id, nom, type, allee, etagere, niveau) VALUES
        (v_magasin_id, 'RECEPTION', 'Zone_Reception', 'REC', '01', '01'),
        (v_magasin_id, 'RECEPTION_CONTROLE', 'Zone_Controle', 'REC', '02', '01'),
        (v_magasin_id, 'RECEPTION_QUARANTAINE', 'Zone_Quarantaine', 'REC', '03', '01')
        ON CONFLICT (nom) DO NOTHING; -- Conflit sur nom
        
        -- Ajouter les extensions pour ces emplacements
        INSERT INTO emplacement_ext (
            emplacement_id, longueur_cm, hauteur_cm, profondeur_cm, 
            capacite_max_kg, temperature_min_c, temperature_max_c, 
            humidite_max_pct, conditions_speciales, actif
        )
        SELECT 
            e.id, 500.0, 200.0, 300.0, 
            1000.0, 10.0, 30.0, 
            80.0, 'Zone de réception temporaire', TRUE
        FROM emplacement e 
        WHERE e.nom IN ('RECEPTION', 'RECEPTION_CONTROLE', 'RECEPTION_QUARANTAINE')
        AND NOT EXISTS (
            SELECT 1 FROM emplacement_ext ext WHERE ext.emplacement_id = e.id
        );
    ELSE
        RAISE NOTICE 'Magasin principal non trouvé, les emplacements de réception n'ont pas été créés.';
    END IF;
END $$;

-- 4.3. Table pour gérer les lots de réception
CREATE TABLE IF NOT EXISTS lot_reception (
    id SERIAL PRIMARY KEY,
    numero_lot VARCHAR(50) NOT NULL UNIQUE,
    commande_id INTEGER, -- REFERENCES commande(id_commande) -- Dépendance externe
    ligne_commande_id INTEGER, -- REFERENCES ligne_commande(id_ligne) -- Dépendance externe
    piece_id INTEGER NOT NULL REFERENCES piece(id_piece),
    quantite_recue INTEGER NOT NULL CHECK (quantite_recue > 0),
    quantite_mise_en_stock INTEGER DEFAULT 0 CHECK (quantite_mise_en_stock >= 0),
    quantite_restante INTEGER GENERATED ALWAYS AS (quantite_recue - quantite_mise_en_stock) STORED,
    emplacement_reception_id INTEGER REFERENCES emplacement(id),
    date_reception TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_mise_en_stock TIMESTAMP,
    statut_lot VARCHAR(20) DEFAULT 'EN_RECEPTION' CHECK (statut_lot IN ('EN_RECEPTION', 'EN_CONTROLE', 'PRET_STOCKAGE', 'STOCKE', 'QUARANTAINE')),
    utilisateur_reception_id INTEGER REFERENCES utilisateur(id_utilisateur),
    utilisateur_stockage_id INTEGER REFERENCES utilisateur(id_utilisateur),
    commentaire_reception TEXT,
    commentaire_stockage TEXT,
    bon_etat BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Ajout des contraintes FK pour commande_id et ligne_commande_id si les tables existent
-- ALTER TABLE lot_reception ADD CONSTRAINT fk_lot_reception_commande FOREIGN KEY (commande_id) REFERENCES commande(id_commande);
-- ALTER TABLE lot_reception ADD CONSTRAINT fk_lot_reception_ligne_commande FOREIGN KEY (ligne_commande_id) REFERENCES ligne_commande(id_ligne);


-- Index pour optimiser les performances
CREATE INDEX IF NOT EXISTS idx_lot_reception_piece ON lot_reception(piece_id);
CREATE INDEX IF NOT EXISTS idx_lot_reception_commande ON lot_reception(commande_id);
CREATE INDEX IF NOT EXISTS idx_lot_reception_statut ON lot_reception(statut_lot);
CREATE INDEX IF NOT EXISTS idx_lot_reception_date ON lot_reception(date_reception);

-- 4.4. Table pour tracer les mouvements de mise en stock
CREATE TABLE IF NOT EXISTS mise_en_stock_detail (
    id SERIAL PRIMARY KEY,
    lot_reception_id INTEGER NOT NULL REFERENCES lot_reception(id),
    emplacement_destination_id INTEGER NOT NULL REFERENCES emplacement(id),
    quantite_stockee INTEGER NOT NULL CHECK (quantite_stockee > 0),
    date_stockage TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    utilisateur_id INTEGER REFERENCES utilisateur(id_utilisateur),
    mouvement_stock_id INTEGER REFERENCES mouvement_stock(id),
    commentaire TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour optimiser les performances
CREATE INDEX IF NOT EXISTS idx_mise_en_stock_lot ON mise_en_stock_detail(lot_reception_id);
CREATE INDEX IF NOT EXISTS idx_mise_en_stock_emplacement ON mise_en_stock_detail(emplacement_destination_id);
CREATE INDEX IF NOT EXISTS idx_mise_en_stock_date ON mise_en_stock_detail(date_stockage);

-- 4.5. Triggers pour maintenir la cohérence
CREATE OR REPLACE FUNCTION update_lot_reception_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at_lot_reception
    BEFORE UPDATE ON lot_reception
    FOR EACH ROW
    EXECUTE FUNCTION update_lot_reception_updated_at();

-- Trigger pour mettre à jour le statut du lot après mise en stock
CREATE OR REPLACE FUNCTION update_lot_statut_after_stockage()
RETURNS TRIGGER AS $$
DECLARE
    total_stocke INTEGER;
    quantite_lot INTEGER;
BEGIN
    -- Calculer le total stocké pour ce lot
    SELECT COALESCE(SUM(quantite_stockee), 0) INTO total_stocke
    FROM mise_en_stock_detail
    WHERE lot_reception_id = NEW.lot_reception_id;
    
    -- Récupérer la quantité du lot
    SELECT quantite_recue INTO quantite_lot
    FROM lot_reception
    WHERE id = NEW.lot_reception_id;
    
    -- Mettre à jour le statut et les quantités
    UPDATE lot_reception 
    SET quantite_mise_en_stock = total_stocke,
        statut_lot = CASE 
            WHEN total_stocke >= quantite_lot THEN 'STOCKE'
            WHEN total_stocke > 0 THEN 'PRET_STOCKAGE' -- Ou garder 'EN_RECEPTION' si partiellement stocké mais pas tout
            ELSE statut_lot -- Garder le statut actuel si rien n'est stocké (ex: EN_RECEPTION)
        END,
        date_mise_en_stock = CASE 
            WHEN total_stocke >= quantite_lot THEN NOW()
            ELSE date_mise_en_stock
        END
    WHERE id = NEW.lot_reception_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_lot_after_stockage
    AFTER INSERT OR UPDATE OR DELETE ON mise_en_stock_detail
    FOR EACH ROW
    EXECUTE FUNCTION update_lot_statut_after_stockage();

-- 4.6. Vues pour le suivi des réceptions et mises en stock
CREATE OR REPLACE VIEW v_lots_reception AS
SELECT 
    lr.id,
    lr.numero_lot,
    lr.commande_id,
    -- c.numero_commande, -- Dépend de la table commande
    lr.piece_id,
    p.reference as piece_reference,
    p.nom as piece_nom,
    lr.quantite_recue,
    lr.quantite_mise_en_stock,
    lr.quantite_restante,
    lr.statut_lot,
    lr.date_reception,
    lr.date_mise_en_stock,
    er.nom as emplacement_reception,
    lr.bon_etat,
    lr.commentaire_reception,
    ur.login as utilisateur_reception,
    us.login as utilisateur_stockage
FROM lot_reception lr
JOIN piece p ON lr.piece_id = p.id_piece
-- LEFT JOIN commande c ON lr.commande_id = c.id_commande -- Dépend de la table commande
LEFT JOIN emplacement er ON lr.emplacement_reception_id = er.id
LEFT JOIN utilisateur ur ON lr.utilisateur_reception_id = ur.id_utilisateur
LEFT JOIN utilisateur us ON lr.utilisateur_stockage_id = us.id_utilisateur
ORDER BY lr.date_reception DESC;

CREATE OR REPLACE VIEW v_stock_reception AS
SELECT 
    lr.piece_id,
    p.reference as piece_reference,
    p.nom as piece_nom,
    SUM(lr.quantite_restante) as quantite_en_reception,
    COUNT(*) as nb_lots,
    MIN(lr.date_reception) as plus_ancienne_reception,
    MAX(lr.date_reception) as plus_recente_reception
FROM lot_reception lr
JOIN piece p ON lr.piece_id = p.id_piece
WHERE lr.quantite_restante > 0
GROUP BY lr.piece_id, p.reference, p.nom
ORDER BY plus_ancienne_reception ASC;

CREATE OR REPLACE VIEW v_mise_en_stock_detail AS
SELECT 
    msd.id,
    lr.numero_lot,
    lr.piece_id,
    p.reference as piece_reference,
    p.nom as piece_nom,
    msd.quantite_stockee,
    ed.nom as emplacement_destination,
    msd.date_stockage,
    u.login as utilisateur,
    msd.commentaire,
    ms.id as mouvement_stock_id
FROM mise_en_stock_detail msd
JOIN lot_reception lr ON msd.lot_reception_id = lr.id
JOIN piece p ON lr.piece_id = p.id_piece
JOIN emplacement ed ON msd.emplacement_destination_id = ed.id
LEFT JOIN utilisateur u ON msd.utilisateur_id = u.id_utilisateur
LEFT JOIN mouvement_stock ms ON msd.mouvement_stock_id = ms.id
ORDER BY msd.date_stockage DESC;

-- 4.7. Fonctions utilitaires
CREATE OR REPLACE FUNCTION generer_numero_lot()
RETURNS TEXT AS $$
BEGIN
    RETURN 'LOT-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(nextval('lot_reception_id_seq')::TEXT, 6, '0');
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_emplacement_reception_defaut()
RETURNS INTEGER AS $$
DECLARE
    emplacement_id_val INTEGER; -- Renommé pour éviter conflit avec nom de table
BEGIN
    SELECT id INTO emplacement_id_val
    FROM emplacement
    WHERE nom = 'RECEPTION'
    LIMIT 1;
    
    RETURN emplacement_id_val;
END;
$$ LANGUAGE plpgsql;

-- Commentaires sur les tables
COMMENT ON TABLE lot_reception IS 'Gestion des lots de réception avant mise en stock';
COMMENT ON TABLE mise_en_stock_detail IS 'Détail des mises en stock depuis la réception';
COMMENT ON COLUMN lot_reception.quantite_restante IS 'Quantité restant à mettre en stock (calculée automatiquement)';
COMMENT ON COLUMN lot_reception.statut_lot IS 'EN_RECEPTION, EN_CONTROLE, PRET_STOCKAGE, STOCKE, QUARANTAINE';
COMMENT ON VIEW v_stock_reception IS 'Vue du stock en attente de mise en stock dans la zone de réception';

-- ============================================================================================
-- PARTIE 5: MIGRATION STATUT DES MOUVEMENTS (mouvement_statut_migration.sql)
-- ============================================================================================

-- 1. Ajouter la colonne statut_mouvement à la table mouvement_stock
ALTER TABLE mouvement_stock 
ADD COLUMN IF NOT EXISTS statut_mouvement VARCHAR(20) DEFAULT 'CONFIRME' 
CHECK (statut_mouvement IN ('EN_ATTENTE', 'CONFIRME', 'ANNULE'));

-- 2. Mettre à jour les mouvements existants
UPDATE mouvement_stock 
SET statut_mouvement = 'CONFIRME' 
WHERE statut_mouvement IS NULL;

-- 3. Créer un index pour optimiser les requêtes par statut
CREATE INDEX IF NOT EXISTS idx_mouvement_stock_statut ON mouvement_stock(statut_mouvement);

-- 4. Supprimer et recréer la vue v_historique_mouvements pour inclure le statut
DROP VIEW IF EXISTS v_historique_mouvements;

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
    ms.statut_mouvement,
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

-- 5. Créer une vue spécifique pour les mouvements en attente de confirmation
CREATE OR REPLACE VIEW v_mouvements_en_attente AS
SELECT 
    ms.id,
    ms.date_mouvement,
    p.reference as piece_reference,
    p.nom as piece_nom,
    tm.nom as type_mouvement,
    tm.impact_stock,
    ms.quantite,
    ms.statut_mouvement,
    es.nom as emplacement_source,
    ed.nom as emplacement_destination,
    u.nom_complet as utilisateur,
    ms.reference_document,
    ms.commentaire,
    -- Calculer l'âge du mouvement en attente
    EXTRACT(EPOCH FROM (NOW() - ms.date_mouvement))/3600 as heures_en_attente
FROM mouvement_stock ms
JOIN piece p ON ms.piece_id = p.id_piece
JOIN type_mouvement tm ON ms.type_mouvement_id = tm.id
LEFT JOIN emplacement es ON ms.emplacement_source_id = es.id
LEFT JOIN emplacement ed ON ms.emplacement_destination_id = ed.id
LEFT JOIN utilisateur u ON ms.utilisateur_id = u.id_utilisateur
WHERE ms.valide = TRUE AND ms.statut_mouvement = 'EN_ATTENTE'
ORDER BY ms.date_mouvement ASC;

-- 6. Fonction pour confirmer un mouvement en attente
CREATE OR REPLACE FUNCTION confirmer_mouvement_en_attente(
    p_mouvement_id INTEGER,
    p_utilisateur_id INTEGER DEFAULT NULL, -- Ce paramètre n'est pas utilisé dans la logique actuelle, mais conservé pour la signature
    p_commentaire_confirmation TEXT DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    v_mouvement RECORD;
    v_nouveau_commentaire TEXT;
    v_type_mouvement_record RECORD;
BEGIN
    -- Récupérer le mouvement
    SELECT * INTO v_mouvement 
    FROM mouvement_stock 
    WHERE id = p_mouvement_id AND statut_mouvement = 'EN_ATTENTE';
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Mouvement % non trouvé ou déjà confirmé/annulé', p_mouvement_id;
    END IF;

    -- Récupérer les infos du type de mouvement
    SELECT * INTO v_type_mouvement_record
    FROM type_mouvement
    WHERE id = v_mouvement.type_mouvement_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Type de mouvement % non trouvé pour le mouvement %', v_mouvement.type_mouvement_id, p_mouvement_id;
    END IF;
    
    -- Préparer le nouveau commentaire
    v_nouveau_commentaire := v_mouvement.commentaire;
    IF p_commentaire_confirmation IS NOT NULL THEN
        v_nouveau_commentaire := COALESCE(v_nouveau_commentaire, '') || 
                                ' [CONFIRMÉ: ' || p_commentaire_confirmation || ']';
    END IF;
    
    -- Confirmer le mouvement
    UPDATE mouvement_stock 
    SET statut_mouvement = 'CONFIRME',
        commentaire = v_nouveau_commentaire,
        updated_at = NOW()
    WHERE id = p_mouvement_id;
    
    -- Appliquer l'impact sur le stock UNIQUEMENT si le type de mouvement a un impact
    IF v_type_mouvement_record.impact_stock != 0 THEN
        -- Mettre à jour le stock actuel de la pièce
        -- Le stock_apres a été calculé lors de la création du mouvement (ou devrait l'être)
        -- en se basant sur stock_avant et l'impact.
        -- Si le mouvement était EN_ATTENTE, stock_apres était égal à stock_avant.
        -- Maintenant, nous devons le recalculer et l'appliquer.
        
        DECLARE
            v_stock_final INTEGER;
        BEGIN
            v_stock_final := v_mouvement.stock_avant + (v_mouvement.quantite * v_type_mouvement_record.impact_stock);

            UPDATE piece 
            SET stock_actuel = v_stock_final,
                updated_at = NOW()
            WHERE id_piece = v_mouvement.piece_id;
            
            -- Mettre à jour le stock_apres du mouvement pour refléter le nouveau stock
            UPDATE mouvement_stock
            SET stock_apres = v_stock_final
            WHERE id = p_mouvement_id;
        END;
    END IF;
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Erreur lors de la confirmation du mouvement %: %', p_mouvement_id, SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- 7. Fonction pour annuler un mouvement en attente
CREATE OR REPLACE FUNCTION annuler_mouvement_en_attente(
    p_mouvement_id INTEGER,
    p_utilisateur_id INTEGER DEFAULT NULL, -- Ce paramètre n'est pas utilisé dans la logique actuelle
    p_raison_annulation TEXT DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    v_mouvement RECORD;
    v_nouveau_commentaire TEXT;
BEGIN
    -- Récupérer le mouvement
    SELECT * INTO v_mouvement 
    FROM mouvement_stock 
    WHERE id = p_mouvement_id AND statut_mouvement = 'EN_ATTENTE';
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Mouvement % non trouvé ou déjà traité (confirmé/annulé)', p_mouvement_id;
    END IF;
    
    -- Préparer le nouveau commentaire
    v_nouveau_commentaire := v_mouvement.commentaire;
    IF p_raison_annulation IS NOT NULL THEN
        v_nouveau_commentaire := COALESCE(v_nouveau_commentaire, '') || 
                                ' [ANNULÉ: ' || p_raison_annulation || ']';
    END IF;
    
    -- Annuler le mouvement
    UPDATE mouvement_stock 
    SET statut_mouvement = 'ANNULE',
        commentaire = v_nouveau_commentaire,
        valide = FALSE, -- Un mouvement annulé n'est plus valide pour les calculs de stock
        updated_at = NOW()
    WHERE id = p_mouvement_id;
    
    -- Aucun impact sur le stock de la pièce car le mouvement est annulé avant confirmation.
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Erreur lors de l''annulation du mouvement %: %', p_mouvement_id, SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- 8. Vue pour le tableau de bord des réceptions
CREATE OR REPLACE VIEW v_dashboard_reception AS
SELECT 
    'LOTS_EN_RECEPTION' as indicateur,
    COUNT(*) as valeur,
    'Lots en cours de réception' as description
FROM lot_reception 
WHERE statut_lot = 'EN_RECEPTION'

UNION ALL

SELECT 
    'LOTS_PRET_STOCKAGE' as indicateur,
    COUNT(*) as valeur,
    'Lots prêts pour stockage' as description
FROM lot_reception 
WHERE statut_lot = 'PRET_STOCKAGE'

UNION ALL

SELECT 
    'MOUVEMENTS_EN_ATTENTE' as indicateur,
    COUNT(*) as valeur,
    'Mouvements en attente de confirmation' as description
FROM mouvement_stock 
WHERE statut_mouvement = 'EN_ATTENTE' AND valide = TRUE

UNION ALL

SELECT 
    'QUANTITE_EN_RECEPTION' as indicateur,
    COALESCE(SUM(quantite_restante), 0) as valeur,
    'Quantité totale en attente de stockage' as description
FROM lot_reception 
WHERE quantite_restante > 0;

-- 9. Trigger pour empêcher la modification du stock si le mouvement n'est pas confirmé
CREATE OR REPLACE FUNCTION verifier_statut_avant_impact_stock()
RETURNS TRIGGER AS $$
DECLARE
    v_type_mouvement_impact INTEGER;
BEGIN
    -- Récupérer l'impact du type de mouvement
    SELECT impact_stock INTO v_type_mouvement_impact
    FROM type_mouvement 
    WHERE id = NEW.type_mouvement_id;

    -- Si le mouvement a un impact sur le stock (type_mouvement.impact_stock != 0) 
    -- ET n'est pas confirmé, alors stock_apres doit être égal à stock_avant.
    IF v_type_mouvement_impact != 0 AND NEW.statut_mouvement != 'CONFIRME' THEN
        NEW.stock_apres := NEW.stock_avant;
    ELSIF v_type_mouvement_impact != 0 AND NEW.statut_mouvement = 'CONFIRME' THEN
        -- Si le mouvement est confirmé et a un impact, calculer stock_apres
        NEW.stock_apres := NEW.stock_avant + (NEW.quantite * v_type_mouvement_impact);
    ELSIF v_type_mouvement_impact = 0 THEN
        -- Si le mouvement n'a pas d'impact (ex: RECEPTION_ACHAT), stock_apres = stock_avant
        NEW.stock_apres := NEW.stock_avant;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS verifier_statut_mouvement_avant_stock ON mouvement_stock;

CREATE TRIGGER verifier_statut_mouvement_avant_stock
    BEFORE INSERT OR UPDATE ON mouvement_stock
    FOR EACH ROW
    EXECUTE FUNCTION verifier_statut_avant_impact_stock();

-- 10. Commentaires sur les nouvelles fonctionnalités
COMMENT ON COLUMN mouvement_stock.statut_mouvement IS 'EN_ATTENTE: mouvement créé mais pas encore confirmé, CONFIRME: mouvement validé et impact sur stock, ANNULE: mouvement annulé';
COMMENT ON VIEW v_mouvements_en_attente IS 'Vue des mouvements en attente de confirmation avec calcul du temps d''attente';
COMMENT ON FUNCTION confirmer_mouvement_en_attente IS 'Confirme un mouvement en attente et applique l''impact sur le stock si applicable';
COMMENT ON FUNCTION annuler_mouvement_en_attente IS 'Annule un mouvement en attente sans impact sur le stock';

-- ============================================================================================
-- PARTIE 6: MIGRATION SCHEMA RÉCEPTION (reception_schema_migration.sql)
-- ============================================================================================
-- ATTENTION: Les sections suivantes dépendent des tables 'commande' et 'ligne_commande'.
--            Assurez-vous que ces tables sont définies si vous utilisez ces fonctionnalités.

-- 1. Ajouter les champs manquants à la table ligne_commande (si elle existe)
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ligne_commande') THEN
        ALTER TABLE ligne_commande 
        ADD COLUMN IF NOT EXISTS quantite_defectueuse INTEGER DEFAULT 0,
        ADD COLUMN IF NOT EXISTS date_derniere_reception TIMESTAMP,
        ADD COLUMN IF NOT EXISTS commentaire_reception TEXT;

        -- 2. Modifier le statut_ligne pour inclure les nouveaux statuts
        ALTER TABLE ligne_commande 
        DROP CONSTRAINT IF EXISTS ligne_commande_statut_ligne_check;

        ALTER TABLE ligne_commande 
        ADD CONSTRAINT ligne_commande_statut_ligne_check 
        CHECK (statut_ligne IN ('Attente', 'Partielle', 'Complete', 'Annulee'));

        -- 11. Mettre à jour les données existantes
        UPDATE ligne_commande 
        SET statut_ligne = 'Attente' 
        WHERE statut_ligne IS NULL OR statut_ligne = '';
    ELSE
      RAISE NOTICE 'Table ligne_commande non trouvée, certaines migrations de réception sont ignorées.';
    END IF;
END $$;


-- 3. Créer la table reception_detail pour l'historique des réceptions
CREATE TABLE IF NOT EXISTS reception_detail (
    id_reception SERIAL PRIMARY KEY,
    ligne_commande_id INTEGER NOT NULL, -- REFERENCES ligne_commande(id_ligne) ON DELETE CASCADE, -- Dépendance externe
    date_reception TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    quantite_recue INTEGER NOT NULL CHECK (quantite_recue >= 0),
    quantite_defectueuse INTEGER DEFAULT 0 CHECK (quantite_defectueuse >= 0),
    utilisateur_id INTEGER REFERENCES utilisateur(id_utilisateur),
    commentaire TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- ALTER TABLE reception_detail ADD CONSTRAINT fk_reception_detail_ligne_commande FOREIGN KEY (ligne_commande_id) REFERENCES ligne_commande(id_ligne) ON DELETE CASCADE;


-- 4. Créer les index pour optimiser les performances
CREATE INDEX IF NOT EXISTS idx_reception_detail_ligne_commande ON reception_detail(ligne_commande_id);
CREATE INDEX IF NOT EXISTS idx_reception_detail_date ON reception_detail(date_reception);
CREATE INDEX IF NOT EXISTS idx_reception_detail_utilisateur ON reception_detail(utilisateur_id);

-- 5. Créer ou vérifier l'existence d'un emplacement pour les pièces défectueuses
INSERT INTO emplacement (nom, type, allee, etagere, niveau)
VALUES ('DEFECTUEUX', 'RETOUR', 'RET', '001', '001')
ON CONFLICT (nom) DO NOTHING;

INSERT INTO emplacement (nom, type, allee, etagere, niveau)
VALUES ('RETOUR_FOURNISSEUR', 'RETOUR', 'RET', '002', '001')
ON CONFLICT (nom) DO NOTHING;

-- 6. Créer une vue pour faciliter les requêtes de réception
CREATE OR REPLACE VIEW v_reception_lignes AS
SELECT 
    lc.id_ligne,
    lc.commande_id,
    -- c.numero_commande, -- Dépend de la table commande
    lc.piece_id,
    p.reference as piece_reference,
    p.nom as piece_nom,
    lc.description_libre,
    lc.quantite_commandee,
    lc.quantite_recue,
    lc.quantite_defectueuse,
    lc.prix_unitaire_ht,
    lc.statut_ligne,
    lc.date_derniere_reception,
    lc.commentaire_reception,
    (lc.quantite_commandee - lc.quantite_recue - lc.quantite_defectueuse) as quantite_restante,
    CASE 
        WHEN lc.quantite_recue + lc.quantite_defectueuse >= lc.quantite_commandee THEN 'Complete'
        WHEN lc.quantite_recue + lc.quantite_defectueuse > 0 THEN 'Partielle'
        ELSE 'Attente'
    END as statut_calcule
FROM ligne_commande lc -- Dépend de la table ligne_commande
-- JOIN commande c ON lc.commande_id = c.id_commande -- Dépend de la table commande
LEFT JOIN piece p ON lc.piece_id = p.id_piece;

-- 7. Créer une vue pour l'historique des réceptions
CREATE OR REPLACE VIEW v_historique_receptions AS
SELECT 
    rd.id_reception,
    rd.date_reception,
    lc.commande_id,
    -- c.numero_commande, -- Dépend de la table commande
    lc.piece_id,
    p.reference as piece_reference,
    p.nom as piece_nom,
    rd.quantite_recue,
    rd.quantite_defectueuse,
    rd.commentaire,
    u.nom_complet as receptionnaire
FROM reception_detail rd
JOIN ligne_commande lc ON rd.ligne_commande_id = lc.id_ligne -- Dépend de la table ligne_commande
-- JOIN commande c ON lc.commande_id = c.id_commande -- Dépend de la table commande
LEFT JOIN piece p ON lc.piece_id = p.id_piece
LEFT JOIN utilisateur u ON rd.utilisateur_id = u.id_utilisateur
ORDER BY rd.date_reception DESC;

-- 8. Fonction pour calculer automatiquement le statut d'une ligne
CREATE OR REPLACE FUNCTION update_ligne_statut()
RETURNS TRIGGER AS $$
BEGIN
    -- Vérifier si la table ligne_commande existe avant de continuer
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ligne_commande') THEN
        RETURN NEW; -- Ou OLD selon le contexte du trigger, ou RAISE NOTICE
    END IF;

    -- Calculer le nouveau statut basé sur les quantités
    IF NEW.quantite_recue + NEW.quantite_defectueuse >= NEW.quantite_commandee THEN
        NEW.statut_ligne = 'Complete';
    ELSIF NEW.quantite_recue + NEW.quantite_defectueuse > 0 THEN
        NEW.statut_ligne = 'Partielle';
    ELSE
        NEW.statut_ligne = 'Attente';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 9. Créer le trigger pour mettre à jour automatiquement le statut (si ligne_commande existe)
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ligne_commande') THEN
        DROP TRIGGER IF EXISTS trigger_update_ligne_statut ON ligne_commande;
        CREATE TRIGGER trigger_update_ligne_statut
            BEFORE UPDATE OF quantite_recue, quantite_defectueuse ON ligne_commande
            FOR EACH ROW
            EXECUTE FUNCTION update_ligne_statut();
    END IF;
END $$;

-- 10. Fonction pour calculer le statut global d'une commande
CREATE OR REPLACE FUNCTION update_commande_statut_from_lignes(commande_id_param INTEGER)
RETURNS TEXT AS $$
DECLARE
    total_lignes INTEGER;
    lignes_completes INTEGER;
    lignes_partielles INTEGER;
    nouveau_statut TEXT;
BEGIN
    -- Vérifier si les tables commande et ligne_commande existent
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'commande') OR
       NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ligne_commande') THEN
        RAISE NOTICE 'Tables commande ou ligne_commande non trouvées. Statut de commande non mis à jour.';
        RETURN NULL;
    END IF;

    -- Compter les lignes par statut
    SELECT 
        COUNT(*),
        COUNT(CASE WHEN statut_ligne = 'Complete' THEN 1 END),
        COUNT(CASE WHEN statut_ligne = 'Partielle' THEN 1 END)
    INTO total_lignes, lignes_completes, lignes_partielles
    FROM ligne_commande 
    WHERE commande_id = commande_id_param;
    
    -- Déterminer le nouveau statut
    IF total_lignes = 0 THEN -- Cas où la commande n'a pas de lignes
        nouveau_statut := (SELECT statut FROM commande WHERE id_commande = commande_id_param); -- Garder le statut actuel
    ELSIF lignes_completes = total_lignes THEN
        nouveau_statut = 'Livree';
    ELSIF lignes_completes > 0 OR lignes_partielles > 0 THEN
        nouveau_statut = 'Partielle';
    ELSE
        nouveau_statut = 'Envoyee'; -- Reste en envoyée si rien n'est reçu
    END IF;
    
    -- Mettre à jour la commande
    UPDATE commande 
    SET statut = nouveau_statut,
        updated_at = CURRENT_TIMESTAMP
    WHERE id_commande = commande_id_param;
    
    RETURN nouveau_statut;
END;
$$ LANGUAGE plpgsql;

-- 12. Commentaires pour la documentation
COMMENT ON TABLE reception_detail IS 'Historique détaillé des réceptions pour chaque ligne de commande';
COMMENT ON COLUMN reception_detail.quantite_recue IS 'Quantité reçue en bon état lors de cette réception';
COMMENT ON COLUMN reception_detail.quantite_defectueuse IS 'Quantité reçue défectueuse lors de cette réception';
COMMENT ON VIEW v_reception_lignes IS 'Vue consolidée des lignes de commande avec statut de réception (dépend de ligne_commande et commande)';
COMMENT ON VIEW v_historique_receptions IS 'Historique complet de toutes les réceptions (dépend de ligne_commande et commande)';

-- ============================================================================================
-- PARTIE 7: ATTRIBUTION DES DROITS CONSOLIDÉE
-- ============================================================================================

DO $$
BEGIN
    -- S'assurer que l'utilisateur applicatif existe (sinon, le créer)
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'gmao_app_user') THEN
        CREATE ROLE gmao_app_user LOGIN PASSWORD 'change_this_password'; -- Changez le mot de passe!
        RAISE NOTICE 'Rôle gmao_app_user créé. Changez le mot de passe par défaut.';
    END IF;

    -- Attribution des droits standards sur toutes les tables existantes et futures dans le schéma public
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO gmao_app_user;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO gmao_app_user;
    
    -- Droits sur toutes les séquences existantes et futures
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO gmao_app_user;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO gmao_app_user;

    -- Droits spécifiques pour les vues (SELECT uniquement généralement)
    GRANT SELECT ON v_mouvement_stats TO gmao_app_user;
    GRANT SELECT ON v_historique_mouvements TO gmao_app_user;
    GRANT SELECT ON v_emplacement_detail TO gmao_app_user;
    GRANT SELECT ON v_stock_par_emplacement TO gmao_app_user;
    GRANT SELECT ON v_emplacement_capacite TO gmao_app_user;
    GRANT SELECT ON v_lots_reception TO gmao_app_user; 
    GRANT SELECT ON v_stock_reception TO gmao_app_user;
    GRANT SELECT ON v_mise_en_stock_detail TO gmao_app_user;
    GRANT SELECT ON v_mouvements_en_attente TO gmao_app_user;
    GRANT SELECT ON v_dashboard_reception TO gmao_app_user;
    -- Les vues dépendant de commande/ligne_commande auront besoin de droits si ces tables sont créées
    IF EXISTS (SELECT FROM information_schema.views WHERE table_name = 'v_reception_lignes') THEN
        GRANT SELECT ON v_reception_lignes TO gmao_app_user;
    END IF;
    IF EXISTS (SELECT FROM information_schema.views WHERE table_name = 'v_historique_receptions') THEN
        GRANT SELECT ON v_historique_receptions TO gmao_app_user;
    END IF;

    -- Droits d'exécution sur les fonctions
    GRANT EXECUTE ON FUNCTION update_updated_at_column() TO gmao_app_user;
    GRANT EXECUTE ON FUNCTION update_emplacement_ext_updated_at() TO gmao_app_user;
    GRANT EXECUTE ON FUNCTION update_emplacement_stock_maj() TO gmao_app_user;
    GRANT EXECUTE ON FUNCTION init_emplacement_stock_dates() TO gmao_app_user;
    GRANT EXECUTE ON FUNCTION check_stock_coherence() TO gmao_app_user;
    GRANT EXECUTE ON FUNCTION nettoyer_stocks_zero() TO gmao_app_user;
    GRANT EXECUTE ON FUNCTION deplacer_stock(INTEGER, INTEGER, INTEGER, INTEGER, TEXT) TO gmao_app_user;
    GRANT EXECUTE ON FUNCTION update_mouvement_updated_at() TO gmao_app_user;
    GRANT EXECUTE ON FUNCTION calculate_cout_total() TO gmao_app_user;
    GRANT EXECUTE ON FUNCTION update_lot_reception_updated_at() TO gmao_app_user;
    GRANT EXECUTE ON FUNCTION update_lot_statut_after_stockage() TO gmao_app_user;
    GRANT EXECUTE ON FUNCTION generer_numero_lot() TO gmao_app_user;
    GRANT EXECUTE ON FUNCTION get_emplacement_reception_defaut() TO gmao_app_user;
    GRANT EXECUTE ON FUNCTION confirmer_mouvement_en_attente(INTEGER, INTEGER, TEXT) TO gmao_app_user;
    GRANT EXECUTE ON FUNCTION annuler_mouvement_en_attente(INTEGER, INTEGER, TEXT) TO gmao_app_user;
    GRANT EXECUTE ON FUNCTION verifier_statut_avant_impact_stock() TO gmao_app_user;
    -- Les fonctions dépendant de commande/ligne_commande auront besoin de droits si ces tables sont créées
    IF EXISTS (SELECT FROM information_schema.routines WHERE routine_name = 'update_ligne_statut') THEN
        GRANT EXECUTE ON FUNCTION update_ligne_statut() TO gmao_app_user;
    END IF;
    IF EXISTS (SELECT FROM information_schema.routines WHERE routine_name = 'update_commande_statut_from_lignes') THEN
        GRANT EXECUTE ON FUNCTION update_commande_statut_from_lignes(INTEGER) TO gmao_app_user;
    END IF;

    RAISE NOTICE 'Permissions attribuées à gmao_app_user.';
EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING 'Une erreur s''est produite lors de l''attribution des permissions: %', SQLERRM;
END$$;

-- ============================================================================================
-- FIN DU SCRIPT CONSOLIDÉ
-- ============================================================================================
