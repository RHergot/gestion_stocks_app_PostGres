-- Extension du schéma pour gérer le workflow réception -> mise en stock
-- Auteur: Système GMAO
-- Date: 2024

-- 1. Nouveaux types de mouvements pour la gestion réception/stock
INSERT INTO type_mouvement (nom, description, impact_stock) VALUES
('RECEPTION_ACHAT', 'Réception de marchandises (zone de réception)', 0),  -- Impact 0 = pas d''impact sur stock emplacement
('MISE_EN_STOCK', 'Mise en stock depuis la réception', 1),
('SORTIE_RECEPTION', 'Sortie de la zone de réception', -1),
('RETOUR_RECEPTION', 'Retour vers la zone de réception', 0)
ON CONFLICT (nom) DO NOTHING;

-- 2. Modification de la table type_mouvement pour supporter impact_stock = 0
ALTER TABLE type_mouvement DROP CONSTRAINT IF EXISTS type_mouvement_impact_stock_check;
ALTER TABLE type_mouvement ADD CONSTRAINT type_mouvement_impact_stock_check 
    CHECK (impact_stock IN (-1, 0, 1));

-- 3. Création d'emplacements spéciaux pour la réception
INSERT INTO inventory_warehouse (nom, description, actif) VALUES
('MAGASIN_PRINCIPAL', 'Magasin principal', TRUE)
ON CONFLICT DO NOTHING;

-- Récupérer l'ID du magasin principal
DO $$
DECLARE
    magasin_id INTEGER;
BEGIN
    SELECT id INTO magasin_id FROM inventory_warehouse WHERE nom = 'MAGASIN_PRINCIPAL' LIMIT 1;
    
    IF magasin_id IS NOT NULL THEN
        -- Créer les emplacements de réception
        INSERT INTO emplacement (magasin_id, nom, type, allee, etagere, niveau) VALUES
        (magasin_id, 'RECEPTION', 'Zone_Reception', 'REC', '01', '01'),
        (magasin_id, 'RECEPTION_CONTROLE', 'Zone_Controle', 'REC', '02', '01'),
        (magasin_id, 'RECEPTION_QUARANTAINE', 'Zone_Quarantaine', 'REC', '03', '01')
        ON CONFLICT DO NOTHING;
        
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
    END IF;
END $$;

-- 4. Table pour gérer les lots de réception
CREATE TABLE IF NOT EXISTS lot_reception (
    id SERIAL PRIMARY KEY,
    numero_lot VARCHAR(50) NOT NULL UNIQUE,
    commande_id INTEGER REFERENCES commande(id_commande),
    ligne_commande_id INTEGER REFERENCES ligne_commande(id_ligne),
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

-- Index pour optimiser les performances
CREATE INDEX IF NOT EXISTS idx_lot_reception_piece ON lot_reception(piece_id);
CREATE INDEX IF NOT EXISTS idx_lot_reception_commande ON lot_reception(commande_id);
CREATE INDEX IF NOT EXISTS idx_lot_reception_statut ON lot_reception(statut_lot);
CREATE INDEX IF NOT EXISTS idx_lot_reception_date ON lot_reception(date_reception);

-- 5. Table pour tracer les mouvements de mise en stock
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

-- 6. Triggers pour maintenir la cohérence
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
            WHEN total_stocke > 0 THEN 'PRET_STOCKAGE'
            ELSE statut_lot
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

-- 7. Vues pour le suivi des réceptions et mises en stock
CREATE OR REPLACE VIEW v_lots_reception AS
SELECT 
    lr.id,
    lr.numero_lot,
    lr.commande_id,
    c.numero_commande,
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
LEFT JOIN commande c ON lr.commande_id = c.id_commande
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

-- 8. Fonctions utilitaires
CREATE OR REPLACE FUNCTION generer_numero_lot()
RETURNS TEXT AS $$
BEGIN
    RETURN 'LOT-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(nextval('lot_reception_id_seq')::TEXT, 6, '0');
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_emplacement_reception_defaut()
RETURNS INTEGER AS $$
DECLARE
    emplacement_id INTEGER;
BEGIN
    SELECT id INTO emplacement_id
    FROM emplacement
    WHERE nom = 'RECEPTION'
    LIMIT 1;
    
    RETURN emplacement_id;
END;
$$ LANGUAGE plpgsql;

-- 9. Droits pour l'utilisateur applicatif
GRANT SELECT, INSERT, UPDATE, DELETE ON lot_reception TO gmao_app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON mise_en_stock_detail TO gmao_app_user;
GRANT SELECT ON v_lots_reception TO gmao_app_user;
GRANT SELECT ON v_stock_reception TO gmao_app_user;
GRANT SELECT ON v_mise_en_stock_detail TO gmao_app_user;
GRANT USAGE, SELECT ON SEQUENCE lot_reception_id_seq TO gmao_app_user;
GRANT USAGE, SELECT ON SEQUENCE mise_en_stock_detail_id_seq TO gmao_app_user;
GRANT EXECUTE ON FUNCTION generer_numero_lot() TO gmao_app_user;
GRANT EXECUTE ON FUNCTION get_emplacement_reception_defaut() TO gmao_app_user;

-- Commentaires sur les tables
COMMENT ON TABLE lot_reception IS 'Gestion des lots de réception avant mise en stock';
COMMENT ON TABLE mise_en_stock_detail IS 'Détail des mises en stock depuis la réception';
COMMENT ON COLUMN lot_reception.quantite_restante IS 'Quantité restant à mettre en stock (calculée automatiquement)';
COMMENT ON COLUMN lot_reception.statut_lot IS 'EN_RECEPTION, EN_CONTROLE, PRET_STOCKAGE, STOCKE, QUARANTAINE';
COMMENT ON VIEW v_stock_reception IS 'Vue du stock en attente de mise en stock dans la zone de réception';