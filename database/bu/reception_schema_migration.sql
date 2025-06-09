-- Migration pour ajouter la gestion des réceptions détaillées
-- Ce script ajoute les champs nécessaires pour gérer les réceptions partielles et multiples

-- 1. Ajouter les champs manquants à la table ligne_commande
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

-- 3. Créer la table reception_detail pour l'historique des réceptions
CREATE TABLE IF NOT EXISTS reception_detail (
    id_reception SERIAL PRIMARY KEY,
    ligne_commande_id INTEGER NOT NULL REFERENCES ligne_commande(id_ligne) ON DELETE CASCADE,
    date_reception TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    quantite_recue INTEGER NOT NULL CHECK (quantite_recue >= 0),
    quantite_defectueuse INTEGER DEFAULT 0 CHECK (quantite_defectueuse >= 0),
    utilisateur_id INTEGER REFERENCES utilisateur(id_utilisateur),
    commentaire TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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
    c.numero_commande,
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
FROM ligne_commande lc
JOIN commande c ON lc.commande_id = c.id_commande
LEFT JOIN piece p ON lc.piece_id = p.id_piece;

-- 7. Créer une vue pour l'historique des réceptions
CREATE OR REPLACE VIEW v_historique_receptions AS
SELECT 
    rd.id_reception,
    rd.date_reception,
    lc.commande_id,
    c.numero_commande,
    lc.piece_id,
    p.reference as piece_reference,
    p.nom as piece_nom,
    rd.quantite_recue,
    rd.quantite_defectueuse,
    rd.commentaire,
    u.nom_complet as receptionnaire
FROM reception_detail rd
JOIN ligne_commande lc ON rd.ligne_commande_id = lc.id_ligne
JOIN commande c ON lc.commande_id = c.id_commande
LEFT JOIN piece p ON lc.piece_id = p.id_piece
LEFT JOIN utilisateur u ON rd.utilisateur_id = u.id_utilisateur
ORDER BY rd.date_reception DESC;

-- 8. Fonction pour calculer automatiquement le statut d'une ligne
CREATE OR REPLACE FUNCTION update_ligne_statut()
RETURNS TRIGGER AS $$
BEGIN
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

-- 9. Créer le trigger pour mettre à jour automatiquement le statut
DROP TRIGGER IF EXISTS trigger_update_ligne_statut ON ligne_commande;
CREATE TRIGGER trigger_update_ligne_statut
    BEFORE UPDATE OF quantite_recue, quantite_defectueuse ON ligne_commande
    FOR EACH ROW
    EXECUTE FUNCTION update_ligne_statut();

-- 10. Fonction pour calculer le statut global d'une commande
CREATE OR REPLACE FUNCTION update_commande_statut_from_lignes(commande_id_param INTEGER)
RETURNS TEXT AS $$
DECLARE
    total_lignes INTEGER;
    lignes_completes INTEGER;
    lignes_partielles INTEGER;
    nouveau_statut TEXT;
BEGIN
    -- Compter les lignes par statut
    SELECT 
        COUNT(*),
        COUNT(CASE WHEN statut_ligne = 'Complete' THEN 1 END),
        COUNT(CASE WHEN statut_ligne = 'Partielle' THEN 1 END)
    INTO total_lignes, lignes_completes, lignes_partielles
    FROM ligne_commande 
    WHERE commande_id = commande_id_param;
    
    -- Déterminer le nouveau statut
    IF lignes_completes = total_lignes THEN
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

-- 11. Mettre à jour les données existantes
UPDATE ligne_commande 
SET statut_ligne = 'Attente' 
WHERE statut_ligne IS NULL OR statut_ligne = '';

-- 12. Commentaires pour la documentation
COMMENT ON TABLE reception_detail IS 'Historique détaillé des réceptions pour chaque ligne de commande';
COMMENT ON COLUMN reception_detail.quantite_recue IS 'Quantité reçue en bon état lors de cette réception';
COMMENT ON COLUMN reception_detail.quantite_defectueuse IS 'Quantité reçue défectueuse lors de cette réception';
COMMENT ON VIEW v_reception_lignes IS 'Vue consolidée des lignes de commande avec statut de réception';
COMMENT ON VIEW v_historique_receptions IS 'Historique complet de toutes les réceptions';

PRINT 'Migration de la gestion des réceptions terminée avec succès';