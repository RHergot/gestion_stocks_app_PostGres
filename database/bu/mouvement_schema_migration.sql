-- Migration script for mouvement_stock tables
-- This script handles the existing table structure and migrates to the new schema

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

-- Droits pour l'utilisateur applicatif
DO $$
BEGIN
    GRANT SELECT, INSERT, UPDATE, DELETE ON mouvement_stock TO gmao_app_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON type_mouvement TO gmao_app_user;
    GRANT SELECT ON v_mouvement_stats TO gmao_app_user;
    GRANT SELECT ON v_historique_mouvements TO gmao_app_user;
    GRANT USAGE, SELECT ON SEQUENCE mouvement_stock_id_seq TO gmao_app_user;
    GRANT USAGE, SELECT ON SEQUENCE type_mouvement_id_seq TO gmao_app_user;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Une erreur s''est produite lors de l''attribution des permissions: %', SQLERRM;
END$$;
