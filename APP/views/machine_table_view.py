from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QHBoxLayout, QMessageBox, QDialog
from PySide6.QtCore import Qt, QDate
from APP.views.machine_dialog import MachineDialog

class MachineTableView(QWidget):
    def __init__(self, machine_service, parent=None):
        super().__init__(parent)
        self.machine_service = machine_service
        self.setWindowTitle(self.tr("Machines"))
        self.resize(800, 600)
        layout = QVBoxLayout()
        self.setGeometry(100, 100, 800, 600)
        self.table = QTableWidget(self)
        self.table.setColumnCount(14)
        self.table.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Nom"), self.tr("Série"), self.tr("Modèle"), self.tr("Date installation"), self.tr("Localisation"), self.tr("État"), self.tr("Infos techniques"), self.tr("Type"), self.tr("Site"), self.tr("Fabricant"), self.tr("Parent"), self.tr("Criticité"), self.tr("Fin garantie"), self.tr("Date garantie")
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton(self.tr("Ajouter"), self)
        self.edit_btn = QPushButton(self.tr("Modifier"), self)
        self.delete_btn = QPushButton(self.tr("Supprimer"), self)
        self.refresh_btn = QPushButton(self.tr("Rafraîchir"), self)
        self.close_btn = QPushButton(self.tr("Fermer"), self)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self.add_btn.clicked.connect(self.add_machine)
        self.edit_btn.clicked.connect(self.edit_machine)
        self.delete_btn.clicked.connect(self.delete_machine)
        self.refresh_btn.clicked.connect(self.refresh)
        self.close_btn.clicked.connect(self.close)

        self.refresh()

    def refresh(self):
        machines = self.machine_service.list_machines()
        self.table.setRowCount(len(machines))
        for row, m in enumerate(machines):
            self.table.setItem(row, 0, QTableWidgetItem(str(m.get("id_machine", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(m.get("nom", "")))
            self.table.setItem(row, 2, QTableWidgetItem(m.get("serial", "")))
            self.table.setItem(row, 3, QTableWidgetItem(m.get("modele", "")))
            self.table.setItem(row, 4, QTableWidgetItem(m.get("date_installation", "")))
            self.table.setItem(row, 5, QTableWidgetItem(m.get("localisation", "")))
            self.table.setItem(row, 6, QTableWidgetItem(m.get("etat", "")))
            self.table.setItem(row, 7, QTableWidgetItem(m.get("informations_techniques", "")))
            self.table.setItem(row, 8, QTableWidgetItem(str(m.get("type_machine_id", ""))))
            self.table.setItem(row, 9, QTableWidgetItem(str(m.get("site_id", ""))))
            self.table.setItem(row, 10, QTableWidgetItem(str(m.get("fabricant_id", ""))))
            self.table.setItem(row, 11, QTableWidgetItem(str(m.get("parent_machine_id", ""))))
            self.table.setItem(row, 12, QTableWidgetItem(m.get("criticite", "")))
            self.table.setItem(row, 13, QTableWidgetItem(m.get("garantie_fin", "")))
            self.table.setItem(row, 14, QTableWidgetItem(m.get("date_garantie", "")))

    def get_selected_machine(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        def get_val(col):
            item = self.table.item(row, col)
            return item.text() if item else ""
        return {
            "id_machine": get_val(0),
            "nom": get_val(1),
            "serial": get_val(2),
            "modele": get_val(3),
            "date_installation": get_val(4),
            "localisation": get_val(5),
            "etat": get_val(6),
            "informations_techniques": get_val(7),
            "type_machine_id": get_val(8),
            "site_id": get_val(9),
            "fabricant_id": get_val(10),
            "parent_machine_id": get_val(11),
            "criticite": get_val(12),
            "garantie_fin": get_val(13),
        }

    def add_machine(self):
        dialog = MachineDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data is None:
                return
            data["parent_machine_id"] = 0  # Champ par défaut car la table n'existe pas
            self.machine_service.create_machine(data)
            self.refresh()

    def edit_machine(self):
        machine = self.get_selected_machine()
        if not machine:
            QMessageBox.warning(self, self.tr("Aucune machine sélectionnée"), self.tr("Veuillez sélectionner une machine à modifier."))
            return
        dialog = MachineDialog(self)
        dialog.nom.setText(machine["nom"])
        dialog.serial.setText(machine["serial"])
        dialog.modele.setText(machine["modele"])
        dialog.date_installation.setDate(QDate.fromString(machine["date_installation"], "yyyy-MM-dd"))
        dialog.localisation.setText(machine["localisation"])
        dialog.etat.setText(machine["etat"])
        dialog.informations_techniques.setPlainText(machine["informations_techniques"])
        # Sélectionner la bonne valeur dans les QComboBox par data (ID)
        def set_combo_by_data(combo, value):
            idx = combo.findData(value)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            else:
                combo.setCurrentIndex(0)
        set_combo_by_data(dialog.type_machine_id, int(machine["type_machine_id"]) if machine["type_machine_id"] else None)
        set_combo_by_data(dialog.site_id, int(machine["site_id"]) if machine["site_id"] else None)
        set_combo_by_data(dialog.fabricant_id, int(machine["fabricant_id"]) if machine["fabricant_id"] else None)
        dialog.parent_machine_id.setText(machine["parent_machine_id"])
        dialog.criticite.setText(machine["criticite"])
        # Vérification du format de date avant setDate
        def safe_set_date(date_edit, value):
            if value:
                d = QDate.fromString(value, "yyyy-MM-dd")
                if d.isValid():
                    date_edit.setDate(d)
        safe_set_date(dialog.garantie_fin, machine["garantie_fin"])
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            data["id_machine"] = machine["id_machine"]
            self.machine_service.update_machine(data)
            self.refresh()

    def delete_machine(self):
        machine = self.get_selected_machine()
        if not machine:
            QMessageBox.warning(self, self.tr("Aucune machine sélectionnée"), self.tr("Veuillez sélectionner une machine à supprimer."))
            return
        confirm = QMessageBox.question(self, self.tr("Confirmer la suppression"), self.tr(f"Supprimer la machine '{machine['nom']}' ?"), QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.machine_service.delete_machine(machine["id_machine"])
            self.refresh()
