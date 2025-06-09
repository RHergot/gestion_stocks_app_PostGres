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

-- Droits pour l'utilisateur applicatif
GRANT SELECT, INSERT, UPDATE, DELETE ON emplacement_ext TO gmao_app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON emplacement_stock TO gmao_app_user;
GRANT SELECT ON v_emplacement_detail TO gmao_app_user;
GRANT SELECT ON v_stock_par_emplacement TO gmao_app_user;
GRANT SELECT ON v_emplacement_capacite TO gmao_app_user;
GRANT USAGE, SELECT ON SEQUENCE emplacement_stock_id_seq TO gmao_app_user;
GRANT EXECUTE ON FUNCTION nettoyer_stocks_zero() TO gmao_app_user;
GRANT EXECUTE ON FUNCTION deplacer_stock(INTEGER, INTEGER, INTEGER, INTEGER, TEXT) TO gmao_app_user;

-- Commentaires sur les tables
COMMENT ON TABLE emplacement_ext IS 'Extension des emplacements avec dimensions et propriétés physiques';
COMMENT ON TABLE emplacement_stock IS 'Stock détaillé par emplacement et par pièce';
COMMENT ON COLUMN emplacement_ext.volume_cm3 IS 'Volume calculé automatiquement (L×H×P)';
COMMENT ON COLUMN emplacement_ext.capacite_max_kg IS 'Capacité maximale en poids';
COMMENT ON COLUMN emplacement_stock.quantite IS 'Quantité de la pièce dans cet emplacement';
COMMENT ON FUNCTION deplacer_stock IS 'Fonction pour déplacer du stock entre emplacements de manière atomique';