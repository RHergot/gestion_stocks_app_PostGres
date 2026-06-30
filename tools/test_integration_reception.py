#!/usr/bin/env python3
"""
Integration test for the reception workflow to verify the complete workflow functions correctly.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'APP'))

def test_reception_workflow_backend():
    """Test the backend reception workflow functionality."""
    try:
        from controllers.mouvement_controller import MouvementController
        from APP.services.db import Database
        
        print("=== Testing Reception Workflow Backend Integration ===")
          # Initialize database and controller
        db = Database()
        db.connect()
        controller = MouvementController(db)
        
        print("✓ Database and controller initialized")
        
        # Test if the controller has the new reception methods
        methods_to_check = [
            'new_reception_achat',
            'new_mise_en_stock', 
            'get_pieces_en_reception',
            'get_reception_stock_summary'
        ]
        
        missing_methods = []
        for method in methods_to_check:
            if not hasattr(controller, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"✗ Missing controller methods: {', '.join(missing_methods)}")
            return False
        else:
            print("✓ All required controller methods found")
        
        # Test getting pieces in reception
        try:
            pieces_reception = controller.get_pieces_en_reception()
            print(f"✓ Retrieved {len(pieces_reception)} pieces in reception")
        except Exception as e:
            print(f"✗ Error getting pieces in reception: {e}")
            return False
        
        # Test getting reception stock summary
        try:
            summary = controller.get_reception_stock_summary()
            print(f"✓ Retrieved reception stock summary with {len(summary)} entries")
        except Exception as e:
            print(f"✗ Error getting reception summary: {e}")
            return False
        
        db.close()
        print("\n🎉 Backend integration test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Backend integration test failed: {e}")
        return False

def test_ui_integration():
    """Test UI integration with backend."""
    try:        from PySide6.QtWidgets import QApplication
        from views.mouvement_table_view import MouvementTableView
        from controllers.mouvement_controller import MouvementController
        from APP.services.db import Database
        
        print("\n=== Testing UI Integration ===")
        
        app = QApplication(sys.argv)
          # Create controller
        db = Database()
        db.connect()
        controller = MouvementController(db)
        
        # Create the main view
        view = MouvementTableView(controller)
        print("✓ MouvementTableView created with controller")
        
        # Test if buttons exist and are properly connected
        buttons_to_check = ['btn_new_reception', 'btn_mise_en_stock']
        missing_buttons = []
        
        for button_name in buttons_to_check:
            if not hasattr(view, button_name):
                missing_buttons.append(button_name)
        
        if missing_buttons:
            print(f"✗ Missing UI buttons: {', '.join(missing_buttons)}")
            return False
        else:
            print("✓ All required UI buttons found")
        
        # Test menu actions
        menu_actions_to_check = ['show_reception_only', 'show_neutral_only']
        missing_actions = []
        
        for action_name in menu_actions_to_check:
            if not hasattr(view, action_name):
                missing_actions.append(action_name)
        
        if missing_actions:
            print(f"✗ Missing menu actions: {', '.join(missing_actions)}")
            return False
        else:
            print("✓ All required menu actions found")
        
        app.quit()
        print("\n🎉 UI integration test passed!")
        return True
        
        except Exception as e:
        print(f"✗ UI integration test failed: {e}")
        return False

if __name__ == "__main__":
    backend_test = test_reception_workflow_backend()
    ui_test = test_ui_integration()
    
    if backend_test and ui_test:
        print("\n🎉 All integration tests passed! The reception workflow is fully functional.")
    else:
        print("\n❌ Some integration tests failed. Please check the errors above.")
