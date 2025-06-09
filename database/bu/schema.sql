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
    actif BOOLEAN DEFAULT TRUE
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
        CREATE TRIGGER set_updated_at_fournisseur
        BEFORE UPDATE ON fournisseur
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='piece' AND column_name='updated_at') THEN
        CREATE TRIGGER set_updated_at_piece
        BEFORE UPDATE ON piece
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
END$$;

-- Droits pour l'utilisateur applicatif
grant select, insert, update, delete on all tables in schema public to gmao_app_user;
-- Généré automatiquement à partir des repositories Python

CREATE TABLE IF NOT EXISTS fabricant (
    id_fabricant SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    contact VARCHAR(100),
    site_web VARCHAR(255),
    support_technique VARCHAR(255)
);

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

CREATE TABLE IF NOT EXISTS site (
    id_site SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    adresse TEXT,
    ville VARCHAR(100),
    pays VARCHAR(100),
    contact_principal VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS type_machine (
    id_type_machine SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    description TEXT,
    categorie VARCHAR(100)
);

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

CREATE TABLE IF NOT EXISTS piece_category (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS piece_unit (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS piece_statut (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS emplacement (
    id SERIAL PRIMARY KEY,
    magasin_id INTEGER REFERENCES inventory_warehouse(id),
    nom VARCHAR(100) NOT NULL,
    type VARCHAR(50),
    allee VARCHAR(50),
    etagere VARCHAR(50),
    niveau VARCHAR(50)
    -- FK magasin_id si la table magasin existe
);

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

CREATE TABLE IF NOT EXISTS piece_extension (
    id_piece INTEGER PRIMARY KEY REFERENCES piece(id_piece),
    unite_id INTEGER REFERENCES piece_unit(id),
    categorie_id INTEGER REFERENCES piece_category(id),
    emplacement_id INTEGER REFERENCES emplacement(id),
    statut_id INTEGER REFERENCES piece_statut(id),
    machine_id INTEGER REFERENCES machine(id_machine)
);

CREATE TABLE IF NOT EXISTS utilisateur (
    id_utilisateur SERIAL PRIMARY KEY,
    login VARCHAR(100) NOT NULL UNIQUE,
    mot_de_passe_hash VARCHAR(255) NOT NULL,
    nom_complet VARCHAR(100),
    role VARCHAR(50),
    email VARCHAR(255),
    actif BOOLEAN DEFAULT TRUE
);

-- Droits pour l'utilisateur applicatif
grant select, insert, update, delete on all tables in schema public to gmao_app_user;
