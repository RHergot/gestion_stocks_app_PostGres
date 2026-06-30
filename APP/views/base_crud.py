"""Classes de base pour les vues CRUD simples (dialog + table).

Élimine la duplication massive entre les 8 paires dialog/table_view identiques :
fabricant, site, type_machine, fournisseur, user, piece_unit, piece_statut, piece_category.
"""
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPushButton, QHBoxLayout,
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox,
)
from PySide6.QtCore import Qt


class BaseCRUDDialog(QDialog):
    """Dialog CRUD générique avec formulaire et boutons OK/Cancel.

    Sous-classes : définir FIELDS, WINDOW_TITLE, ENTITY_NAME, REQUIRED_FIELD.
    """

    # À surcharger dans les sous-classes
    FIELDS = []          # [(attr_name, label, widget_cls, widget_kwargs), ...]
    WINDOW_TITLE = ""    # self.tr("Add/Edit ...")
    ENTITY_NAME = ""     # self.tr("entity") — pour les messages
    REQUIRED_FIELD = "nom"  # champ obligatoire (attr_name)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr(self.WINDOW_TITLE))
        layout = QFormLayout(self)
        self._widgets = {}

        for attr_name, label, widget_cls, kwargs in self.FIELDS:
            w = widget_cls(self, **kwargs)
            self._widgets[attr_name] = w
            setattr(self, attr_name, w)
            layout.addRow(self.tr(label), w)

        btns = QHBoxLayout()
        self.ok_btn = QPushButton(self.tr("OK"), self)
        self.cancel_btn = QPushButton(self.tr("Cancel"), self)
        btns.addWidget(self.ok_btn)
        btns.addWidget(self.cancel_btn)
        layout.addRow(btns)

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def get_data(self):
        """Retourne un dict {attr_name: value} ou None si validation échoue."""
        if self.REQUIRED_FIELD:
            w = self._widgets.get(self.REQUIRED_FIELD)
            if w and hasattr(w, 'text') and not w.text().strip():
                QMessageBox.warning(
                    self, self.tr("Input error"),
                    self.tr("%s name is required.") % self.tr(self.ENTITY_NAME)
                )
                return None
        data = {}
        for attr_name, _label, _cls, kwargs in self.FIELDS:
            w = self._widgets[attr_name]
            if hasattr(w, 'value') and callable(w.value):
                # QSpinBox, QDoubleSpinBox
                data[attr_name] = w.value()
            elif hasattr(w, 'text'):
                data[attr_name] = w.text()
            elif hasattr(w, 'currentText'):
                data[attr_name] = w.currentText()
            else:
                data[attr_name] = ""
        return data

    def set_data(self, data):
        """Remplit le formulaire à partir d'un dict."""
        for attr_name, _label, _cls, kwargs in self.FIELDS:
            w = self._widgets.get(attr_name)
            if w and attr_name in data and data[attr_name] is not None:
                if hasattr(w, 'setValue') and callable(w.setValue):
                    try:
                        w.setValue(float(data[attr_name]))
                    except (ValueError, TypeError):
                        w.setValue(0)
                elif isinstance(w, QLineEdit):
                    w.setText(str(data[attr_name] or ""))

    # Méthodes de service — à surcharger dans BaseCRUDTableView.subclass
    # (utilisées pour le dispatch Add/Edit/Delete)


class BaseCRUDTableView(QWidget):
    """Table view CRUD générique avec boutons Add/Edit/Delete/Refresh/Close.

    Sous-classes : définir COLUMNS, SERVICE_ATTR, DIALOG_CLASS, WINDOW_TITLE,
    ENTITY_NAME, ID_FIELD.
    """

    # À surcharger dans les sous-classes
    COLUMNS = []          # [(key, header), ...]
    SERVICE_ATTR = None   # Nom de l'attribut de service (ex: "site_service")
    DIALOG_CLASS = None   # Classe de dialog (sous-classe de BaseCRUDDialog)
    WINDOW_TITLE = ""     # self.tr("...")
    ENTITY_NAME = ""      # self.tr("entity")
    ENTITY_NAME_CAP = ""  # self.tr("Entity") — majuscule pour messages
    ID_FIELD = "id"       # Nom du champ ID dans les données

    def __init__(self, service, parent=None):
        super().__init__(parent)
        self.service = service
        self.setWindowTitle(self.tr(self.WINDOW_TITLE))
        self.resize(800, 600)
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()
        self.table = QTableWidget(self)
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels([self.tr(h) for _k, h in self.COLUMNS])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton(self.tr("Add"), self)
        self.edit_btn = QPushButton(self.tr("Edit"), self)
        self.delete_btn = QPushButton(self.tr("Delete"), self)
        self.refresh_btn = QPushButton(self.tr("Refresh"), self)
        self.close_btn = QPushButton(self.tr("Close"), self)
        for btn in [self.add_btn, self.edit_btn, self.delete_btn, self.refresh_btn, self.close_btn]:
            btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self.add_btn.clicked.connect(self._add)
        self.edit_btn.clicked.connect(self._edit)
        self.delete_btn.clicked.connect(self._delete)
        self.refresh_btn.clicked.connect(self.refresh)
        self.close_btn.clicked.connect(self.close)

        self.refresh()

    # === Méthodes à surcharger ===

    def _list(self):
        """Appelle service.list_<entity>() — par convention."""
        return getattr(self.service, f"list_{self.SERVICE_ATTR}s")()

    def _create(self, data):
        return getattr(self.service, f"create_{self.SERVICE_ATTR}")(data)

    def _update(self, data):
        return getattr(self.service, f"update_{self.SERVICE_ATTR}")(data)

    def _delete_entity(self, id_val):
        return getattr(self.service, f"delete_{self.SERVICE_ATTR}")(id_val)

    # === Implémentation générique ===

    def refresh(self):
        items = self._list()
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            for col, (key, _header) in enumerate(self.COLUMNS):
                self.table.setItem(row, col, QTableWidgetItem(str(item.get(key, ""))))

    def _get_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        data = {}
        for col, (key, _header) in enumerate(self.COLUMNS):
            item = self.table.item(row, col)
            data[key] = item.text() if item else ""
        return data

    def _add(self):
        dialog = self.DIALOG_CLASS(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data is None:
                return
            self._create(data)
            self.refresh()

    def _edit(self):
        entity = self._get_selected()
        if not entity:
            QMessageBox.warning(self, self.tr("No %s selected") % self.tr(self.ENTITY_NAME),
                              self.tr("Please select a %s to edit.") % self.tr(self.ENTITY_NAME))
            return
        dialog = self.DIALOG_CLASS(self)
        dialog.set_data(entity)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data is None:
                return
            data[self.ID_FIELD] = entity[self.ID_FIELD]
            self._update(data)
            self.refresh()

    def _delete(self):
        entity = self._get_selected()
        if not entity:
            QMessageBox.warning(self, self.tr("No %s selected") % self.tr(self.ENTITY_NAME),
                              self.tr("Please select a %s to delete.") % self.tr(self.ENTITY_NAME))
            return
        confirm = QMessageBox.question(
            self, self.tr("Confirm deletion"),
            self.tr("Delete %s '%s'?") % (self.tr(self.ENTITY_NAME), entity.get('nom', '')),
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self._delete_entity(entity[self.ID_FIELD])
            self.refresh()
