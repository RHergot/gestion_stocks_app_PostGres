#!/usr/bin/env python3
"""
Test simple pour isoler le problème des boutons
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QGroupBox, QLabel)

class TestDialog(QDialog):
    def __init__(self, mode_edition=False):
        super().__init__()
        self.mode_edition = mode_edition
        self.setWindowTitle(f"Test Dialog - Mode: {'Edition' if mode_edition else 'Creation'}")
        self.setMinimumWidth(600)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Section normale
        normal_group = QGroupBox("Section normale")
        normal_layout = QVBoxLayout()
        normal_layout.addWidget(QLabel("Cette section est toujours visible"))
        normal_group.setLayout(normal_layout)
        
        # Section de test (équivalent aux boutons de statut)
        self.test_group = QGroupBox("Boutons de test")
        test_layout = QHBoxLayout()
        
        self.btn1 = QPushButton("Bouton 1")
        self.btn2 = QPushButton("Bouton 2")
        self.btn3 = QPushButton("Bouton 3")
        
        test_layout.addWidget(self.btn1)
        test_layout.addWidget(self.btn2)
        test_layout.addWidget(self.btn3)
        
        self.test_group.setLayout(test_layout)
        
        # Boutons de fermeture
        button_box = QHBoxLayout()
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        button_box.addStretch()
        button_box.addWidget(close_btn)
        
        # Assemblage
        layout.addWidget(normal_group)
        layout.addWidget(self.test_group)
        layout.addLayout(button_box)
        
        # Contrôle de visibilité
        if self.mode_edition:
            self.test_group.setVisible(True)
            print(f"Mode édition: groupe visible = {self.test_group.isVisible()}")
        else:
            self.test_group.setVisible(False)
            print(f"Mode création: groupe visible = {self.test_group.isVisible()}")
        
        self.setLayout(layout)

def main():
    app = QApplication(sys.argv)
    
    # Test 1: Mode création
    print("=== Test 1: Mode création ===")
    dialog1 = TestDialog(mode_edition=False)
    dialog1.show()
    print("Dialog création affiché")
    
    # Test 2: Mode édition
    print("\n=== Test 2: Mode édition ===")
    dialog2 = TestDialog(mode_edition=True)
    dialog2.show()
    print("Dialog édition affiché")
    
    # Attendre que l'utilisateur ferme les dialogs
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())