import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Chargement du .env
print("Chargement des variables d'environnement depuis .env...")
load_dotenv()

DB_PARAMS = {
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT', 5432),
    'dbname': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
}

print("Paramètres de connexion:")
for k, v in DB_PARAMS.items():
    if k != 'password':
        print(f"  {k}: {v}")

# Requêtes de création de tables (à compléter/étendre si besoin)
CREATE_TABLE_QUERIES = [
    ("inventory_warehouse", '''
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
    '''),
    ("fabricant", '''
        CREATE TABLE IF NOT EXISTS fabricant (
            id_fabricant SERIAL PRIMARY KEY,
            nom VARCHAR(100) NOT NULL,
            contact VARCHAR(100),
            site_web VARCHAR(255),
            support_technique VARCHAR(255)
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_fabricant_nom ON fabricant(nom);
    '''),
    ("fournisseur", '''
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
    '''),
    ("site", '''
        CREATE TABLE IF NOT EXISTS site (
            id_site SERIAL PRIMARY KEY,
            nom VARCHAR(100) NOT NULL,
            adresse TEXT,
            ville VARCHAR(100),
            pays VARCHAR(100),
            contact_principal VARCHAR(100)
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_site_nom ON site(nom);
    '''),
    ("type_machine", '''
        CREATE TABLE IF NOT EXISTS type_machine (
            id_type_machine SERIAL PRIMARY KEY,
            nom VARCHAR(100) NOT NULL,
            description TEXT,
            categorie VARCHAR(100)
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_type_machine_nom ON type_machine(nom);
    '''),
    ("machine", '''
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
    '''),
    ("piece_category", '''
        CREATE TABLE IF NOT EXISTS piece_category (
            id SERIAL PRIMARY KEY,
            nom VARCHAR(100) NOT NULL,
            description TEXT
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_piece_category_nom ON piece_category(nom);
    '''),
    ("piece_unit", '''
        CREATE TABLE IF NOT EXISTS piece_unit (
            id SERIAL PRIMARY KEY,
            nom VARCHAR(50) NOT NULL,
            description TEXT
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_piece_unit_nom ON piece_unit(nom);
    '''),
    ("piece_statut", '''
        CREATE TABLE IF NOT EXISTS piece_statut (
            id SERIAL PRIMARY KEY,
            nom VARCHAR(50) NOT NULL,
            description TEXT
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_piece_statut_nom ON piece_statut(nom);
    '''),
    ("emplacement", '''
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
    '''),
    ("piece", '''
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
    '''),
    ("piece_extension", '''
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
    '''),
    ("utilisateur", '''
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
    '''),
]

try:
    print("Connexion à la base de données...")
    conn = psycopg2.connect(**DB_PARAMS)
    print("Connexion réussie!")
except Exception as e:
    print("Erreur lors de la connexion à PostgreSQL:", e)
    exit(1)

with conn:
    with conn.cursor() as cur:
        for table_name, query in CREATE_TABLE_QUERIES:
            try:
                print(f"\nCréation de la table '{table_name}'...")
                cur.execute(query)
                print(f"Table '{table_name}' OK.")
            except Exception as err:
                print(f"Erreur lors de la création de '{table_name}':", err)
                conn.rollback()
        print("\nToutes les tables principales sont créées (ou déjà existantes).")

conn.close()
print("Connexion fermée.")
