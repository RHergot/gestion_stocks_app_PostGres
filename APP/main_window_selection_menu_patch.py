from PySide6.QtWidgets import QAction, QMessageBox

def patch_selection_menu(self):
    menubar = self.menuBar()
    selection_menu = menubar.addMenu(self.tr("Selection"))
    # 1. Pièces en stock faible
    stock_faible_action = QAction(self.tr("Parts with Low Stock"), self)
    stock_faible_action.triggered.connect(self.show_stock_faible)
    selection_menu.addAction(stock_faible_action)
    # 2. Pièces par machine
    par_machine_action = QAction(self.tr("Parts by Machine"), self)
    par_machine_action.triggered.connect(self.show_pieces_by_machine)
    selection_menu.addAction(par_machine_action)
    # 3. Inventaire par catégorie
    inventaire_categorie_action = QAction(self.tr("Inventory by Category"), self)
    inventaire_categorie_action.triggered.connect(self.show_inventaire_categorie)
    selection_menu.addAction(inventaire_categorie_action)
    # 4. Emplacements sous-utilisés
    emplacements_vides_action = QAction(self.tr("Underutilized Locations"), self)
    emplacements_vides_action.triggered.connect(self.show_emplacements_vides)
    selection_menu.addAction(emplacements_vides_action)
    # 5. Pièces par statut
    par_statut_action = QAction(self.tr("Parts by Status"), self)
    par_statut_action.triggered.connect(self.show_pieces_by_statut)
    selection_menu.addAction(par_statut_action)

def show_stock_faible(self):
    with self.db.conn.cursor() as cur:
        cur.execute("""
            SELECT nom, reference, stock_actuel, stock_alerte
            FROM piece
            WHERE stock_actuel <= stock_alerte
            ORDER BY stock_actuel ASC;
        """)
        rows = cur.fetchall()
    msg = "\n".join([f"{r[0]} ({r[1]}): {r[2]}/{r[3]}" for r in rows]) or self.tr("No low-stock parts.")
    QMessageBox.information(self, self.tr("Parts with Low Stock"), msg)

def show_pieces_by_machine(self):
    with self.db.conn.cursor() as cur:
        cur.execute("""
            SELECT p.nom, p.reference, pe.machine_id, m.nom AS machine
            FROM piece p
            JOIN piece_extension pe ON p.id_piece = pe.id_piece
            JOIN machine m ON pe.machine_id = m.id_machine
            ORDER BY m.nom, p.nom;
        """)
        rows = cur.fetchall()
    msg = "\n".join([f"{r[0]} ({r[1]}): {r[3]}" for r in rows]) or self.tr("No parts linked to a machine.")
    QMessageBox.information(self, self.tr("Parts by Machine"), msg)

def show_inventaire_categorie(self):
    with self.db.conn.cursor() as cur:
        cur.execute("""
            SELECT c.nom, COUNT(*), SUM(p.stock_actuel)
            FROM piece p
            JOIN piece_extension pe ON p.id_piece = pe.id_piece
            JOIN piece_category c ON pe.categorie_id = c.id
            GROUP BY c.nom
            ORDER BY COUNT(*) DESC;
        """)
        rows = cur.fetchall()
    msg = "\n".join([f"{r[0]}: {r[1]} parts, {r[2]} in stock" for r in rows]) or self.tr("No categories.")
    QMessageBox.information(self, self.tr("Inventory by Category"), msg)

def show_emplacements_vides(self):
    with self.db.conn.cursor() as cur:
        cur.execute("""
            SELECT e.nom, COUNT(p.id_piece) AS nb_pieces
            FROM emplacement e
            LEFT JOIN piece_extension pe ON pe.emplacement_id = e.id
            LEFT JOIN piece p ON pe.id_piece = p.id_piece
            GROUP BY e.nom
            HAVING COUNT(p.id_piece) < 5
            ORDER BY nb_pieces ASC;
        """)
        rows = cur.fetchall()
    msg = "\n".join([f"{r[0]}: {r[1]} parts" for r in rows]) or self.tr("No underutilized locations.")
    QMessageBox.information(self, self.tr("Underutilized Locations"), msg)

def show_pieces_by_statut(self):
    with self.db.conn.cursor() as cur:
        cur.execute("""
            SELECT s.nom, COUNT(*)
            FROM piece p
            JOIN piece_extension pe ON p.id_piece = pe.id_piece
            JOIN piece_statut s ON pe.statut_id = s.id
            GROUP BY s.nom
            ORDER BY COUNT(*) DESC;
        """)
        rows = cur.fetchall()
    msg = "\n".join([f"{r[0]}: {r[1]} parts" for r in rows]) or self.tr("No statuses.")
    QMessageBox.information(self, self.tr("Parts by Status"), msg)
