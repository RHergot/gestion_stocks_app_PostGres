from PySide6.QtWidgets import QMainWindow, QMenuBar, QMenu, QMessageBox
from PySide6.QtCore import QTranslator
from PySide6.QtGui import QAction


from PySide6.QtWidgets import QMainWindow, QMenuBar, QMenu, QMessageBox, QLabel, QDialog
from PySide6.QtCore import QTranslator, Qt
from PySide6.QtGui import QAction, QFont

from APP.services.user_service import UserService
from APP.views.user_table_view import UserTableView
from APP.services.machine_service import MachineService
from APP.views.machine_table_view import MachineTableView
from APP.services.site_service import SiteService
from APP.views.site_table_view import SiteTableView
from APP.services.fabricant_service import FabricantService
from APP.views.fabricant_table_view import FabricantTableView
from APP.services.type_machine_service import TypeMachineService
from APP.views.type_machine_table_view import TypeMachineTableView
from APP.services.fournisseur_service import FournisseurService
from APP.views.fournisseur_table_view import FournisseurTableView
from APP.services.piece_service import PieceService
from APP.views.piece_table_view import PieceTableView
from APP.services.emplacement_service import EmplacementService
from APP.views.emplacement_table_view import EmplacementTableView
from APP.services.piece_category_service import PieceCategoryService
from APP.views.piece_category_table_view import PieceCategoryTableView
from APP.services.piece_statut_service import PieceStatutService
from APP.views.piece_statut_table_view import PieceStatutTableView
from APP.services.piece_unit_service import PieceUnitService
from APP.views.piece_unit_table_view import PieceUnitTableView
from APP.controllers.mouvement_controller import MouvementController
from APP.views.mouvement_table_view import MouvementTableView
from APP.services.db import Database

class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.user_service = UserService(self.db)
        self.machine_service = MachineService(self.db)
        self.site_service = SiteService(self.db)
        self.fabricant_service = FabricantService(self.db)
        self.type_machine_service = TypeMachineService(self.db)
        self.fournisseur_service = FournisseurService(self.db)
        self.piece_service = PieceService(self.db)
        self.emplacement_service = EmplacementService(self.db)
        self.piece_category_service = PieceCategoryService(self.db)
        self.piece_statut_service = PieceStatutService(self.db)
        self.piece_unit_service = PieceUnitService(self.db)
        self.mouvement_controller = MouvementController(self.db)
        self.setWindowTitle(self.tr("Stock / CMMS Management"))
        self.setGeometry(0, 0, 1920, 1080)
        self._create_menu_bar()
        self.commande_view = None
        self.statusBar().showMessage("")
        # Préparation pour la traduction (anglais par défaut)
        self.translator = QTranslator()
        # Affichage du titre central
        self._show_main_title()
        # Pour changer la langue plus tard :
        # QApplication.instance().installTranslator(self.translator)

    def _show_main_title(self):
        label = QLabel(self.tr("Stock Management"), self)
        font = QFont()
        font.setPointSize(40)
        font.setBold(True)
        label.setFont(font)
        label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(label)

    def show_under_construction(self):
        # Affiche un message "Under construction" (barre de statut et popup)
        self.statusBar().showMessage(self.tr("Under construction"), 3000)
        QMessageBox.information(self, self.tr("Info"), self.tr("Under construction"))

    def show_sites(self):
        self.site_table_view = SiteTableView(self.site_service, parent=None)
        self.site_table_view.show()

    def show_fabricants(self):
        self.fabricant_table_view = FabricantTableView(self.fabricant_service, parent=None)
        self.fabricant_table_view.show()

    def show_type_machines(self):
        self.type_machine_table_view = TypeMachineTableView(self.type_machine_service, parent=None)
        self.type_machine_table_view.show()

    def show_machines(self):
        self.machine_table_view = MachineTableView(self.machine_service, parent=None)
        self.machine_table_view.show()

    def show_fournisseurs(self):
        self.fournisseur_table_view = FournisseurTableView(self.fournisseur_service, parent=None)
        self.fournisseur_table_view.show()

    def show_pieces(self):
        # Pass self as parent so PieceTableView can access services via self.parent()
        self.piece_table_view = PieceTableView(self.piece_service, parent=self)
        self.piece_table_view.show()

    def show_emplacements(self):
        # Pass parent=None to make it a top-level window
        self.emplacement_table_view = EmplacementTableView(self.emplacement_service, self.db, parent=None)
        self.emplacement_table_view.show()

    def show_piece_categories(self):
        self.piece_category_table_view = PieceCategoryTableView(self.piece_category_service, parent=None)
        self.piece_category_table_view.show()

    def show_piece_statuts(self):
        self.piece_statut_table_view = PieceStatutTableView(self.piece_statut_service, parent=None)
        self.piece_statut_table_view.show()

    def show_piece_units(self):
        self.piece_unit_table_view = PieceUnitTableView(self.piece_unit_service, parent=None)
        self.piece_unit_table_view.show()

    def show_commandes(self):
        from APP.views.commande_view import CommandeView
        from APP.services.commande_service import get_all_commandes_clean
        
        commandes = get_all_commandes_clean(self.db)
        self.commande_view = CommandeView(commandes, self.db)
        self.commande_view.show()

    def _create_menu_bar(self):
        menubar = self.menuBar()
        # 1) File menu
        file_menu = menubar.addMenu(self.tr("File"))
        quit_action = QAction(self.tr("Quit"), self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        # 2) General menu and submenus
        general_menu = menubar.addMenu(self.tr("General"))
        users_action = QAction(self.tr("Users"), self)
        users_action.triggered.connect(self.show_users)
        general_menu.addAction(users_action)
        type_machines_action = QAction(self.tr("Type Machines"), self)
        type_machines_action.triggered.connect(self.show_type_machines)
        general_menu.addAction(type_machines_action)
        machines_action = QAction(self.tr("Machines"), self)
        machines_action.triggered.connect(self.show_machines)
        general_menu.addAction(machines_action)

        manufacturers_action = QAction(self.tr("Manufacturers"), self)
        manufacturers_action.triggered.connect(self.show_fabricants)
        general_menu.addAction(manufacturers_action)
        sites_action = QAction(self.tr("Sites"), self)
        sites_action.triggered.connect(self.show_sites)
        general_menu.addAction(sites_action)
        locations_action = QAction(self.tr("Locations"), self)
        locations_action.triggered.connect(self.show_emplacements)
        general_menu.addAction(locations_action)
        # 3) Parts, Orders, Movements menus
        # Menu Orders
        commandes_menu = menubar.addMenu(self.tr("Orders"))
        voir_commandes_action = QAction(self.tr("View orders"), self)
        voir_commandes_action.triggered.connect(self.show_commandes)
        commandes_menu.addAction(voir_commandes_action)
        # Menu Pièces
        parts_menu = menubar.addMenu(self.tr("Parts"))
        suppliers_action = QAction(self.tr("Suppliers"), self)
        suppliers_action.triggered.connect(self.show_fournisseurs)
        parts_menu.addAction(suppliers_action)
        input_parts_action = QAction(self.tr("Input Parts"), self)
        input_parts_action.triggered.connect(self.show_pieces)
        parts_menu.addAction(input_parts_action)
        part_categories_action = QAction(self.tr("Part Categories"), self)
        part_categories_action.triggered.connect(self.show_piece_categories)
        parts_menu.addAction(part_categories_action)
        part_statuts_action = QAction(self.tr("Part Statuses"), self)
        part_statuts_action.triggered.connect(self.show_piece_statuts)
        parts_menu.addAction(part_statuts_action)
        part_units_action = QAction(self.tr("Units of Measure"), self)
        part_units_action.triggered.connect(self.show_piece_units)
        parts_menu.addAction(part_units_action)
        orders_action = QAction(self.tr("Orders"), self)
        orders_action.triggered.connect(self.show_under_construction)
        parts_menu.addAction(orders_action)

        movements_menu = menubar.addMenu(self.tr("Movements"))
        
        # Actions for Movements menu
        view_movements_action = QAction(self.tr("View movements"), self)
        view_movements_action.triggered.connect(self.show_movements)
        movements_menu.addAction(view_movements_action)
        
        movements_menu.addSeparator()
        
        new_entry_action = QAction(self.tr("New entry"), self)
        new_entry_action.triggered.connect(self.show_new_entry)
        movements_menu.addAction(new_entry_action)
        
        new_exit_action = QAction(self.tr("New exit"), self)
        new_exit_action.triggered.connect(self.show_new_exit)
        movements_menu.addAction(new_exit_action)
        
        new_transfer_action = QAction(self.tr("New transfer"), self)
        new_transfer_action.triggered.connect(self.show_new_transfer)
        movements_menu.addAction(new_transfer_action)
        
        inventory_adjustment_action = QAction(self.tr("Inventory adjustment"), self)
        inventory_adjustment_action.triggered.connect(self.show_inventory_adjustment)
        movements_menu.addAction(inventory_adjustment_action)

    def show_users(self):
        self.user_table_view = UserTableView(self.user_service, parent=None)
        self.user_table_view.show()

    def show_stock_faible(self):
        with self.db.conn.cursor() as cur:
            cur.execute("""
                SELECT nom, reference, stock_actuel, stock_alerte
                FROM piece
                WHERE stock_actuel <= stock_alerte
                ORDER BY stock_actuel ASC;
            """)
            rows = cur.fetchall()
        msg = "\n".join([f"{r[0]} ({r[1]}): {r[2]}/{r[3]}" for r in rows]) or "No parts with low stock."
        QMessageBox.information(self, self.tr("Parts with low stock"), msg)

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
        msg = "\n".join([f"{r[0]} ({r[1]}): {r[3]}" for r in rows]) or "No parts linked to a machine."
        QMessageBox.information(self, self.tr("Parts by machine"), msg)

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
        msg = "\n".join([f"{r[0]}: {r[1]} parts, {r[2]} in stock" for r in rows]) or "No category."
        QMessageBox.information(self, self.tr("Inventory by category"), msg)

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
        msg = "\n".join([f"{r[0]}: {r[1]} parts" for r in rows]) or "No underused location."
        QMessageBox.information(self, self.tr("Underused locations"), msg)

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
        msg = "\n".join([f"{r[0]}: {r[1]} parts" for r in rows]) or "No status."
        QMessageBox.information(self, self.tr("Parts by status"), msg)

    # === Méthodes pour les mouvements de stock ===

    def show_movements(self):
        """Affiche la fenêtre de gestion des mouvements"""
        try:
            self.mouvement_table_view = MouvementTableView(self.mouvement_controller, parent=None)
            self.mouvement_table_view.show()
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), 
                               self.tr(f"Error while opening movements: {e}"))

    def show_new_entry(self):
        """Affiche le dialog pour une nouvelle entrée"""
        try:
            from APP.views.mouvement_dialog import MouvementDialog
            
            pieces = self.mouvement_controller.obtenir_pieces_disponibles()
            types_entree = self.mouvement_controller.obtenir_types_mouvement('entree')
            emplacements = self.mouvement_controller.obtenir_emplacements_disponibles()
            
            dialog = MouvementDialog(self, 'entree', pieces, types_entree, emplacements)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                result = self.mouvement_controller.effectuer_entree_stock(**data)
                
                if result['success']:
                    QMessageBox.information(self, self.tr("Success"), result['message'])
                else:
                    QMessageBox.critical(self, self.tr("Error"), result['message'])
                    
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), 
                               self.tr(f"Error while creating entry: {e}"))

    def show_new_exit(self):
        """Affiche le dialog pour une nouvelle sortie"""
        try:
            from APP.views.mouvement_dialog import MouvementDialog
            
            pieces = self.mouvement_controller.obtenir_pieces_disponibles()
            types_sortie = self.mouvement_controller.obtenir_types_mouvement('sortie')
            emplacements = self.mouvement_controller.obtenir_emplacements_disponibles()
            
            dialog = MouvementDialog(self, 'sortie', pieces, types_sortie, emplacements)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                result = self.mouvement_controller.effectuer_sortie_stock(**data)
                
                if result['success']:
                    QMessageBox.information(self, self.tr("Success"), result['message'])
                else:
                    QMessageBox.critical(self, self.tr("Error"), result['message'])
                    
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), 
                               self.tr(f"Error while creating exit: {e}"))

    def show_new_transfer(self):
        """Affiche le dialog pour un nouveau transfert"""
        try:
            from APP.views.mouvement_dialog import MouvementDialog
            
            pieces = self.mouvement_controller.obtenir_pieces_disponibles()
            emplacements = self.mouvement_controller.obtenir_emplacements_disponibles()
            
            dialog = MouvementDialog(self, 'transfert', pieces, [], emplacements)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                result = self.mouvement_controller.effectuer_transfert(**data)
                
                if result['success']:
                    QMessageBox.information(self, self.tr("Success"), result['message'])
                else:
                    QMessageBox.critical(self, self.tr("Error"), result['message'])
                    
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), 
                               self.tr(f"Error while creating transfer: {e}"))

    def show_inventory_adjustment(self):
        """Affiche le dialog pour un ajustement d'inventaire"""
        try:
            from APP.views.mouvement_dialog import MouvementDialog
            
            pieces = self.mouvement_controller.obtenir_pieces_disponibles()
            
            dialog = MouvementDialog(self, 'inventaire', pieces, [], [])
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                result = self.mouvement_controller.effectuer_ajustement_inventaire(**data)
                
                if result['success']:
                    QMessageBox.information(self, self.tr("Success"), result['message'])
                else:
                    QMessageBox.critical(self, self.tr("Error"), result['message'])
                    
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), 
                               self.tr(f"Error while adjusting inventory: {e}"))
