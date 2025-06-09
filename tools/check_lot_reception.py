from APP.services.db import Database

db = Database()
db.connect()

with db.conn.cursor() as cur:
    # Vérifier si la table lot_reception existe
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name = 'lot_reception'
    """)
    result = cur.fetchall()
    print(f"Table lot_reception existe: {len(result) > 0}")
    
    # Lister toutes les tables
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = cur.fetchall()
    print(f"\nTables disponibles ({len(tables)}):")
    for table in tables:
        print(f"  - {table[0]}")

db.close()