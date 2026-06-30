#!/usr/bin/env python3
"""
Test script for the new reception workflow UI components.
This script tests the new dialogs and functionality without needing the full GUI.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'APP'))

from PySide6.QtWidgets import QApplication
from views.reception_workflow_dialog import ReceptionWorkflowDialog
from views.mise_en_stock_dialog import MiseEnStockDialog
from APP.services.db import Database

def test_dialogs():
    """Test the new reception workflow dialogs."""
    app = QApplication(sys.argv)
    
    try:        # Test database connection
        print("Testing database connection...")
        db = Database()
        conn = db.connect()
        if conn:
            print("✓ Database connection successful")
            db.close()
        else:
            print("✗ Database connection failed")
            return False
        
        # Test ReceptionWorkflowDialog
        print("\nTesting ReceptionWorkflowDialog...")
        try:
            dialog = ReceptionWorkflowDialog()
            print("✓ ReceptionWorkflowDialog created successfully")
              # Test dialog components
            if hasattr(dialog, 'piece_combo') and hasattr(dialog, 'quantity_spin'):
                print("✓ Dialog has required components")
            else:
                print("✗ Dialog missing required components")
                return False
                
        except Exception as e:
            print(f"✗ Error creating ReceptionWorkflowDialog: {e}")
            return False
        
        # Test MiseEnStockDialog
        print("\nTesting MiseEnStockDialog...")
        try:
            dialog = MiseEnStockDialog()
            print("✓ MiseEnStockDialog created successfully")
              # Test dialog components
            if hasattr(dialog, 'piece_combo') and hasattr(dialog, 'location_combo'):
                print("✓ Dialog has required components")
            else:
                print("✗ Dialog missing required components")
                return False
                  except Exception as e:
            print(f"✗ Error creating MiseEnStockDialog: {e}")
            return False
        
        print("\n✓ All dialog tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        return False
    finally:
        app.quit()

def test_mouvement_table_view_imports():
    """Test that MouvementTableView can import the new dialogs."""
    print("\nTesting MouvementTableView imports...")
    try:
        from views.mouvement_table_view import MouvementTableView
        print("✓ MouvementTableView imported successfully")
        
        # Check if new methods exist
        if hasattr(MouvementTableView, 'new_reception') and hasattr(MouvementTableView, 'mise_en_stock'):
            print("✓ New reception workflow methods found")
        else:
            print("✗ New reception workflow methods not found")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ Error importing MouvementTableView: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Reception Workflow UI Components ===")
    
    # Test imports first
    import_test = test_mouvement_table_view_imports()
    
    # Test dialogs
    dialog_test = test_dialogs()
    
    if import_test and dialog_test:
        print("\n🎉 All tests passed! The reception workflow UI is ready.")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
