import sys
import os
from PyQt5.QtWidgets import QApplication

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

from gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SecureVault - Password Guardian")
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()