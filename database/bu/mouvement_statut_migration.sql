-- Migration pour ajouter un statut aux mouvements
-- Objectif: Différencier les mouvements de réception des mouvements de mise en stock effective
-- Date: 2024

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

CREATE VIEW v_historique_mouvements AS
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
    p_utilisateur_id INTEGER DEFAULT NULL,
    p_commentaire_confirmation TEXT DEFAULT NULL
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
        RAISE EXCEPTION 'Mouvement % non trouvé ou déjà confirmé', p_mouvement_id;
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
    
    -- Pour les mouvements de réception (impact_stock = 0), on doit quand même mettre à jour le stock
    -- car la confirmation transforme la réception en entrée effective
    IF v_mouvement.type_mouvement_id IN (
        SELECT id FROM type_mouvement WHERE nom = 'RECEPTION_ACHAT'
    ) THEN
        -- Pour une réception, on ajoute la quantité au stock actuel
        UPDATE piece 
        SET stock_actuel = stock_actuel + v_mouvement.quantite,
            updated_at = NOW()
        WHERE id_piece = v_mouvement.piece_id;
        
        -- Mettre à jour le stock_apres du mouvement pour refléter le nouveau stock
        UPDATE mouvement_stock
        SET stock_apres = (SELECT stock_actuel FROM piece WHERE id_piece = v_mouvement.piece_id)
        WHERE id = p_mouvement_id;
        
    ELSIF v_mouvement.type_mouvement_id IN (
        SELECT id FROM type_mouvement WHERE impact_stock != 0
    ) THEN
        -- Pour les autres mouvements, utiliser le stock_apres calculé
        UPDATE piece 
        SET stock_actuel = v_mouvement.stock_apres,
            updated_at = NOW()
        WHERE id_piece = v_mouvement.piece_id;
    END IF;
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Erreur lors de la confirmation du mouvement: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- 7. Fonction pour annuler un mouvement en attente
CREATE OR REPLACE FUNCTION annuler_mouvement_en_attente(
    p_mouvement_id INTEGER,
    p_utilisateur_id INTEGER DEFAULT NULL,
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
        RAISE EXCEPTION 'Mouvement % non trouvé ou déjà traité', p_mouvement_id;
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
        valide = FALSE,
        updated_at = NOW()
    WHERE id = p_mouvement_id;
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Erreur lors de l''annulation du mouvement: %', SQLERRM;
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
BEGIN
    -- Si le mouvement a un impact sur le stock et n'est pas confirmé, ne pas modifier le stock
    IF NEW.statut_mouvement != 'CONFIRME' AND EXISTS (
        SELECT 1 FROM type_mouvement 
        WHERE id = NEW.type_mouvement_id AND impact_stock != 0
    ) THEN
        -- Pour les mouvements en attente, on garde le stock_avant = stock_apres
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
COMMENT ON FUNCTION confirmer_mouvement_en_attente IS 'Confirme un mouvement en attente et applique l''impact sur le stock';
COMMENT ON FUNCTION annuler_mouvement_en_attente IS 'Annule un mouvement en attente sans impact sur le stock';

-- 11. Droits pour l'utilisateur applicatif
GRANT SELECT ON v_mouvements_en_attente TO gmao_app_user;
GRANT SELECT ON v_dashboard_reception TO gmao_app_user;
GRANT EXECUTE ON FUNCTION confirmer_mouvement_en_attente TO gmao_app_user;
GRANT EXECUTE ON FUNCTION annuler_mouvement_en_attente TO gmao_app_user;

-- 12. Données de test pour valider le système
-- Insérer quelques mouvements en attente pour tester
-- (Ces données seront supprimées en production)
/*
INSERT INTO mouvement_stock (
    piece_id, type_mouvement_id, quantite, 
    emplacement_destination_id, utilisateur_id, 
    reference_document, commentaire, 
    stock_avant, stock_apres, statut_mouvement
) 
SELECT 
    1, -- piece_id (à adapter selon vos données)
    (SELECT id FROM type_mouvement WHERE nom = 'RECEPTION_ACHAT' LIMIT 1),
    10, -- quantite
    (SELECT id FROM emplacement WHERE nom = 'RECEPTION' LIMIT 1),
    1, -- utilisateur_id (à adapter)
    'TEST-RECEPTION-001',
    'Test de réception en attente de confirmation',
    0, -- stock_avant
    0, -- stock_apres (sera égal à stock_avant car EN_ATTENTE)
    'EN_ATTENTE'
WHERE EXISTS (SELECT 1 FROM piece WHERE id_piece = 1)
AND EXISTS (SELECT 1 FROM type_mouvement WHERE nom = 'RECEPTION_ACHAT')
AND EXISTS (SELECT 1 FROM emplacement WHERE nom = 'RECEPTION');
*/