import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont


current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
sys.path.insert(0, src_path)

try:
    from gui.main_window import MainWindow
except ImportError as e:
    print(f"Erreur d'import: {e}")
    print("Structure des dossiers détectée:")
    print("Tentative de chargement alternatif...")

    try:
        sys.path.insert(0, os.path.join(current_dir, 'src', 'gui'))
        from main_window import MainWindow
        print("✅ Chargement réussi depuis src/gui/")
    except ImportError as e2:
        print(f"Échec du chargement alternatif: {e2}")
        print("Création d'une fenêtre de secours...")
        

        from PyQt5.QtWidgets import QMainWindow, QLabel
        class MainWindow(QMainWindow):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("SecureVault - Mode Secours")
                self.setGeometry(100, 100, 600, 400)
                label = QLabel("Interface principale non chargée.\nStructure: src/gui/")
                label.setStyleSheet("font-size: 14px; padding: 20px; color: red;")
                self.setCentralWidget(label)

def main():
    app = QApplication(sys.argv)
    
    app.setFont(QFont("Segoe UI", 10))
    

    app.setStyleSheet("""
        QMessageBox {
            background-color: #1a2942;
        }
        QMessageBox QLabel {
            color: #e0e7ff;
            font-size: 14px;
        }
        QMessageBox QPushButton {
            background-color: #3b82f6;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 20px;
            min-width: 80px;
        }
        QMessageBox QPushButton:hover {
            background-color: #2563eb;
        }
    """)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()