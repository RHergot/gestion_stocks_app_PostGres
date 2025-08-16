from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QMessageBox
from PySide6.QtCore import Qt

class PieceDeleteDialog(QDialog):
    """
    Dialog to manage part deletion workflow.
    - Shows blockers (referencing records) if any.
    - Offers Archive (set statut to Inactif) or Delete.
    - Delete is only enabled when there are no blockers.
    """
    def __init__(self, parent, piece_service, piece: dict):
        super().__init__(parent)
        self.piece_service = piece_service
        self.piece = piece
        self.setWindowTitle(self.tr("Delete or archive part"))
        layout = QVBoxLayout(self)

        # Load blockers
        try:
            self.blockers = self.piece_service.get_delete_blockers(self.piece["id_piece"])
        except Exception as e:
            self.blockers = None
            QMessageBox.warning(self, self.tr("Warning"), self.tr(f"Pre-check failed: {e}"))

        self.info = QLabel(self)
        self.info.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._update_info()
        layout.addWidget(self.info)

        buttons = QDialogButtonBox(self)
        self.btn_archive = buttons.addButton(self.tr("Archive"), QDialogButtonBox.AcceptRole)
        self.btn_empty_stock = buttons.addButton(self.tr("Empty stock from locations"), QDialogButtonBox.ActionRole)
        self.btn_delete = buttons.addButton(self.tr("Delete"), QDialogButtonBox.DestructiveRole)
        self.btn_cancel = buttons.addButton(self.tr("Cancel"), QDialogButtonBox.RejectRole)

        # Delete enabled only if there are no blockers
        can_delete = (self.blockers is not None and sum(self.blockers.values()) == 0)
        self.btn_delete.setEnabled(can_delete)

        buttons.accepted.connect(self.on_archive)
        buttons.rejected.connect(self.reject)
        self.btn_delete.clicked.connect(self.on_delete)
        self.btn_empty_stock.clicked.connect(self.on_empty_stock)
        layout.addWidget(buttons)

    def _update_info(self):
        """Refresh the info label and delete button state based on current blockers."""
        if self.blockers is None:
            self.info.setText(self.tr("Unable to compute blockers. You can still archive the part."))
        else:
            total = sum(self.blockers.values())
            if total == 0:
                self.info.setText(self.tr(f"No referencing records found. You can safely delete part '{self.piece.get('nom','')}'."))
            else:
                details = self.piece_service.format_blockers_message(self.blockers)
                self.info.setText(details)
        # Delete enabled only if there are no blockers
        can_delete = (self.blockers is not None and sum(self.blockers.values()) == 0)
        if hasattr(self, 'btn_delete'):
            self.btn_delete.setEnabled(can_delete)

    def on_archive(self):
        try:
            self.piece_service.archive_piece(self.piece["id_piece"])
            QMessageBox.information(self, self.tr("Archived"), self.tr("The part has been archived (status set to Inactive)."))
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), self.tr(f"Failed to archive: {e}"))

    def on_delete(self):
        # Only called if enabled (no blockers). Additional safety: re-check.
        try:
            blockers = self.piece_service.get_delete_blockers(self.piece["id_piece"])
            if sum(blockers.values()) > 0:
                QMessageBox.warning(self, self.tr("Delete blocked"), self.piece_service.format_blockers_message(blockers))
                return
            # Confirm delete
            from PySide6.QtWidgets import QMessageBox as _QMB
            confirm = _QMB.question(self, self.tr("Confirm deletion"), self.tr(f"Delete part '{self.piece.get('nom','')}'?"), _QMB.Yes | _QMB.No)
            if confirm == _QMB.Yes:
                self.piece_service.delete_piece(self.piece["id_piece"])
                self.accept()
        except RuntimeError as e:
            QMessageBox.critical(self, self.tr("Error"), str(e))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), self.tr(f"Unexpected error while deleting: {e}"))

    def on_empty_stock(self):
        """Attempt to empty the piece from all locations to lift blockers related to stock movements/emplacements."""
        try:
            from PySide6.QtWidgets import QMessageBox as _QMB
            confirm = _QMB.question(
                self,
                self.tr("Confirm emptying stock"),
                self.tr(f"This will create inventory-out movements to empty all locations for part '{self.piece.get('nom','')}'. Continue?"),
                _QMB.Yes | _QMB.No
            )
            if confirm != _QMB.Yes:
                return

            nb = self.piece_service.clear_piece_stocks(self.piece["id_piece"], None, "Vidage pour suppression")
            QMessageBox.information(self, self.tr("Stock cleared"), self.tr(f"Created {nb} movement(s)."))

            # Refresh blockers after action
            self.blockers = self.piece_service.get_delete_blockers(self.piece["id_piece"])
            self._update_info()
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), self.tr(f"Failed to empty stock: {e}"))
